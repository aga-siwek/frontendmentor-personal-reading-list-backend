from flask import jsonify
from flask_jwt_extended import get_jwt_identity

from src.clients import book_api_client
from src.database import db
from src.models.book import Book
from src.models.category import Category
from src.models.user_book import UserBook, BookStatus


def search_books(title: str):
    results = book_api_client.search_books_by_title(title)
    return jsonify(results), 200


def get_book_details(isbn: str):
    user_id = get_jwt_identity()

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
    response["user_book"] = user_book.to_dict() if user_book else None

    return jsonify(response), 200


def add_book(isbn: str, status: str, is_favourite: bool = False):
    user_id = get_jwt_identity()

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

    if book_status == BookStatus.WANT_TO_READ:
        current_page = 0
    elif book_status == BookStatus.FINISHED:
        current_page = book.number_of_pages or 0
    else:
        current_page = 0

    user_book = UserBook(
        user_id=user_id,
        isbn=isbn,
        status=book_status,
        is_favourite=is_favourite,
        current_page=current_page,
    )
    db.session.add(user_book)
    db.session.commit()

    return jsonify(user_book.to_dict()), 201
