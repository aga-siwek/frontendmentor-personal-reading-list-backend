from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from src.services import book_service

book_app = Blueprint("books", __name__, url_prefix="/books")

@book_app.route("/search/", methods=["GET"])
@jwt_required()
def search_book():
    title = request.args.get("title", "").strip()
    if not title:
        return {"error": "title query parameter is required"}, 400
    return book_service.search_books(title)


# for admin
@book_app.route("/", methods=["GET"])
@jwt_required()
def get_all_user_books():
    return book_service.get_all_user_books()


# for admin
@book_app.route("/users/<int:user_id>/", methods=["GET"])
@jwt_required()
def get_user_books(user_id):
    return book_service.get_user_books(user_id)


@book_app.route("/me/", methods=["GET"])
@jwt_required()
def get_me_books():
    return book_service.get_me_books()


@book_app.route("/<string:isbn>/", methods=["GET"])
@jwt_required()
def get_book(isbn):
    return book_service.get_book_details(isbn)


@book_app.route("/<string:isbn>/", methods=["POST"])
@jwt_required()
def add_book(isbn):
    data = request.get_json() or {}
    status = data.get("status")
    is_favourite = data.get("is_favourite", False)
    notes = data.get("notes")
    return book_service.add_book(isbn, status, is_favourite, notes)


@book_app.route("/<string:isbn>/", methods=["PATCH"])
@jwt_required()
def update_book(isbn):
    data = request.get_json() or {}
    return book_service.update_user_book(isbn, data)
