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


@book_app.route("/<string:isbn>/", methods=["GET"])
@jwt_required()
def get_book(isbn):
    return book_service.get_book_details(isbn)


@book_app.route("/", methods=["POST"])
@jwt_required()
def add_book():
    data = request.get_json()
    isbn = data.get("isbn", "").strip()
    if not isbn:
        return {"error": "isbn is required"}, 400
    status = data.get("status")
    is_favourite = data.get("is_favourite", False)
    return book_service.add_book(isbn, status, is_favourite)
