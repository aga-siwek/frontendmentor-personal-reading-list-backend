from datetime import datetime
from flask import jsonify
from flask_jwt_extended import get_jwt_identity

from src.clients import book_api_client
from src.database import db
from src.models.book import Book
from src.models.category import Category
from src.models.user import User
from src.models.user_book import UserBook, BookStatus
from src.models.reading_progress import ReadingProgress


def _get_current_user():
    return User.query.filter_by(user_id=int(get_jwt_identity())).first()


def _user_book_to_dict(user_book: UserBook) -> dict:
    data = user_book.book.to_dict() if user_book.book else {}
    user_book_dict = user_book.to_dict()
    total_pages = user_book.book.number_of_pages if user_book.book else None
    user_book_dict["percentage"] = round(user_book.current_page / total_pages * 100, 1) if total_pages else None
    data["user_book"] = user_book_dict
    return data


def get_all_user_books():
    logged_user = _get_current_user()
    if not logged_user:
        return jsonify({"error": "User not found"}), 404
    if not logged_user.is_administrator():
        return jsonify({"error": "Unauthorized"}), 401
    user_books = UserBook.query.all()
    return jsonify([_user_book_to_dict(ub) for ub in user_books]), 200


def get_user_books(user_id: int):
    logged_user = _get_current_user()
    if not logged_user:
        return jsonify({"error": "User not found"}), 404
    if not logged_user.is_administrator():
        return jsonify({"error": "Unauthorized"}), 401
    user_books = UserBook.query.filter_by(user_id=user_id).all()
    return jsonify([_user_book_to_dict(ub) for ub in user_books]), 200


def get_me_books():
    logged_user = _get_current_user()
    if not logged_user:
        return jsonify({"error": "User not found"}), 404
    user_books = UserBook.query.filter_by(user_id=logged_user.user_id).all()
    return jsonify([_user_book_to_dict(ub) for ub in user_books]), 200


def search_books(query: str):
    results = book_api_client.search_books(query)
    return jsonify(results), 200


def get_book_details(isbn: str):
    user_id = int(get_jwt_identity())

    book = Book.query.get(isbn)
    if not book:
        data = book_api_client.get_book_details(isbn)
        if not data.get("title"):
            return jsonify({"error": "Book not found"}), 404

        cover = data.get("cover", {})
        book = Book(
            isbn=isbn,
            title=data["title"],
            author=data.get("author"),
            cover_small=cover.get("small"),
            cover_medium=cover.get("medium"),
            cover_large=cover.get("large"),
            description=data.get("description"),
            number_of_pages=data.get("number_of_pages"),
            publish_date=data.get("publish_date"),
            publisher=data.get("publisher"),
            source_api_id=data.get("source_api_id"),
        )
        for name in data.get("categories", []):
            category = Category.query.filter_by(name=name).first()
            if not category:
                category = Category(name=name)
                db.session.add(category)
            book.categories.append(category)
        db.session.add(book)
        db.session.commit()

    user_book = UserBook.query.filter_by(user_id=user_id, isbn=isbn).first()
    response = book.to_dict()
    response["user_book"] = _user_book_to_dict(user_book)["user_book"] if user_book else None

    return jsonify(response), 200


def add_book(isbn: str, status: str, is_favourite: bool = False, notes: str = None, rating: int = None):
    user_id = int(get_jwt_identity())
    existing_user_book = UserBook.query.filter_by(user_id=user_id, isbn=isbn).first()
    if existing_user_book:
        return jsonify({"error": "Book already on your list"}), 409

    book = Book.query.get(isbn)
    if not book:
        return jsonify({"error": "Book not found. Fetch book details first."}), 404
    try:
        book_status = BookStatus(status) if status else BookStatus.WANT_TO_READ
    except ValueError:
        return jsonify({"error": f"Invalid status. Valid values: {[s.value for s in BookStatus]}"}), 400

    if book_status == BookStatus.FINISHED:
        current_page = book.number_of_pages or 0
        last_updated = datetime.utcnow()
    else:
        current_page = 0
        last_updated = None

    user_book = UserBook(
        user_id=user_id,
        isbn=isbn,
        status=book_status,
        is_favourite=is_favourite,
        current_page=current_page,
        notes=notes,
        rating=rating,
        last_updated=last_updated,
    )
    db.session.add(user_book)
    db.session.commit()

    return jsonify(user_book.to_dict()), 201


def add_reading_progress(isbn: str, data: dict):
    user_id = int(get_jwt_identity())
    user_book = UserBook.query.filter_by(user_id=user_id, isbn=isbn).first()
    if not user_book:
        return jsonify({"error": "Book not on your list"}), 404
    current_page = data.get("current_page")
    if current_page is None:
        return jsonify({"error": "current_page is required"}), 400

    total_pages = user_book.book.number_of_pages if user_book.book else None
    if total_pages and current_page > total_pages:
        current_page = total_pages
    progress = ReadingProgress(user_id=user_id, isbn=isbn, current_page=current_page)
    user_book.current_page = current_page
    user_book.last_updated = progress.date
    if total_pages and current_page >= total_pages:
        user_book.status = BookStatus.FINISHED
    elif user_book.status == BookStatus.WANT_TO_READ and current_page > 0:
        user_book.status = BookStatus.CURRENTLY_READING
    db.session.add(progress)
    db.session.commit()
    return jsonify(progress.to_dict()), 201


def get_reading_progress(isbn: str):
    user_id = int(get_jwt_identity())
    user_book = UserBook.query.filter_by(user_id=user_id, isbn=isbn).first()
    if not user_book:
        return jsonify({"error": "Book not on your list"}), 404
    progress = ReadingProgress.query.filter_by(user_id=user_id, isbn=isbn).order_by(ReadingProgress.date).all()
    return jsonify([p.to_dict() for p in progress]), 200


def update_user_book(isbn: str, data: dict):
    user_id = int(get_jwt_identity())
    user_book = UserBook.query.filter_by(user_id=user_id, isbn=isbn).first()
    if not user_book:
        return jsonify({"error": "Book not on your list"}), 404

    if "status" in data:
        try:
            new_status = BookStatus(data["status"])
            user_book.status = new_status
            if new_status == BookStatus.FINISHED:
                user_book.last_updated = datetime.utcnow()
                if user_book.book and user_book.book.number_of_pages:
                    user_book.current_page = user_book.book.number_of_pages
        except ValueError:
            return jsonify({"error": f"Invalid status. Valid values: {[s.value for s in BookStatus]}"}), 400
    if "is_favourite" in data:
        user_book.is_favourite = data["is_favourite"]
    if "current_page" in data:
        total_pages = user_book.book.number_of_pages if user_book.book else None
        user_book.current_page = min(data["current_page"], total_pages) if total_pages else data["current_page"]
    if "notes" in data:
        user_book.notes = data["notes"]
    if "rating" in data:
        user_book.rating = data["rating"]

    db.session.commit()
    return jsonify(user_book.to_dict()), 200
