from flask import jsonify
from flask_jwt_extended import get_jwt_identity

from src.database import db
from src.models.book import Book
from src.models.shelf import Shelf, ShelfBook
from src.models.user import User


def _get_current_user():
    return User.query.filter_by(user_id=int(get_jwt_identity())).first()


def get_my_shelves():
    logged_user = _get_current_user()
    if not logged_user:
        return jsonify({"error": "User not found"}), 404
    shelves = Shelf.query.filter_by(user_id=logged_user.user_id).order_by(Shelf.position).all()
    result = []
    for shelf in shelves:
        shelf_dict = shelf.to_dict()
        shelf_dict["books"] = [sb.isbn for sb in shelf.books]
        result.append(shelf_dict)
    return jsonify(result), 200


def get_shelf(shelf_id: int):
    logged_user = _get_current_user()
    if not logged_user:
        return jsonify({"error": "User not found"}), 404
    shelf = Shelf.query.filter_by(id=shelf_id, user_id=logged_user.user_id).first()
    if not shelf:
        return jsonify({"error": "Shelf not found"}), 404
    shelf_dict = shelf.to_dict()
    shelf_dict["books"] = [sb.isbn for sb in shelf.books]
    return jsonify(shelf_dict), 200


def create_shelf(data: dict):
    logged_user = _get_current_user()
    if not logged_user:
        return jsonify({"error": "User not found"}), 404
    name = data.get("name")
    if not name:
        return jsonify({"error": "name is required"}), 400
    position = data.get("position", 0)
    is_default = data.get("is_default", False)

    if is_default:
        Shelf.query.filter_by(user_id=logged_user.user_id, is_default=True).update({"is_default": False})

    shelf = Shelf(user_id=logged_user.user_id, name=name, position=position, is_default=is_default)
    db.session.add(shelf)
    db.session.commit()
    return jsonify(shelf.to_dict()), 201


def update_shelf(shelf_id: int, data: dict):
    logged_user = _get_current_user()
    if not logged_user:
        return jsonify({"error": "User not found"}), 404
    shelf = Shelf.query.filter_by(id=shelf_id, user_id=logged_user.user_id).first()
    if not shelf:
        return jsonify({"error": "Shelf not found"}), 404

    if "name" in data:
        shelf.name = data["name"]
    if "position" in data:
        shelf.position = data["position"]
    if "is_default" in data and data["is_default"]:
        Shelf.query.filter_by(user_id=logged_user.user_id, is_default=True).update({"is_default": False})
        shelf.is_default = True

    db.session.commit()
    return jsonify(shelf.to_dict()), 200


def delete_shelf(shelf_id: int):
    logged_user = _get_current_user()
    if not logged_user:
        return jsonify({"error": "User not found"}), 404
    shelf = Shelf.query.filter_by(id=shelf_id, user_id=logged_user.user_id).first()
    if not shelf:
        return jsonify({"error": "Shelf not found"}), 404
    if shelf.is_default:
        return jsonify({"error": "Cannot delete default shelf"}), 400
    db.session.delete(shelf)
    db.session.commit()
    return jsonify({"message": f"Shelf '{shelf.name}' deleted"}), 200


def add_book_to_shelf(shelf_id: int, isbn: str):
    logged_user = _get_current_user()
    if not logged_user:
        return jsonify({"error": "User not found"}), 404
    shelf = Shelf.query.filter_by(id=shelf_id, user_id=logged_user.user_id).first()
    if not shelf:
        return jsonify({"error": "Shelf not found"}), 404
    book = Book.query.get(isbn)
    if not book:
        return jsonify({"error": "Book not found"}), 404
    existing = ShelfBook.query.filter_by(shelf_id=shelf_id, isbn=isbn).first()
    if existing:
        return jsonify({"error": "Book already on this shelf"}), 409

    shelf_book = ShelfBook(shelf_id=shelf_id, isbn=isbn)
    db.session.add(shelf_book)
    db.session.commit()
    return jsonify(shelf_book.to_dict()), 201


def remove_book_from_shelf(shelf_id: int, isbn: str):
    logged_user = _get_current_user()
    if not logged_user:
        return jsonify({"error": "User not found"}), 404
    shelf = Shelf.query.filter_by(id=shelf_id, user_id=logged_user.user_id).first()
    if not shelf:
        return jsonify({"error": "Shelf not found"}), 404
    shelf_book = ShelfBook.query.filter_by(shelf_id=shelf_id, isbn=isbn).first()
    if not shelf_book:
        return jsonify({"error": "Book not on this shelf"}), 404
    db.session.delete(shelf_book)
    db.session.commit()
    return jsonify({"message": "Book removed from shelf"}), 200
