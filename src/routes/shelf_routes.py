from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from src.services import shelf_service

shelf_app = Blueprint("shelves", __name__, url_prefix="/shelves")


@shelf_app.route("/me/", methods=["GET"])
@jwt_required()
def get_my_shelves():
    return shelf_service.get_my_shelves()


@shelf_app.route("/me/", methods=["POST"])
@jwt_required()
def create_shelf():
    data = request.get_json() or {}
    return shelf_service.create_shelf(data)


@shelf_app.route("/<int:shelf_id>/", methods=["GET"])
@jwt_required()
def get_shelf(shelf_id):
    return shelf_service.get_shelf(shelf_id)


@shelf_app.route("/<int:shelf_id>/", methods=["PATCH"])
@jwt_required()
def update_shelf(shelf_id):
    data = request.get_json() or {}
    return shelf_service.update_shelf(shelf_id, data)


@shelf_app.route("/<int:shelf_id>/", methods=["DELETE"])
@jwt_required()
def delete_shelf(shelf_id):
    return shelf_service.delete_shelf(shelf_id)


@shelf_app.route("/<int:shelf_id>/books/<string:isbn>/", methods=["POST"])
@jwt_required()
def add_book_to_shelf(shelf_id, isbn):
    return shelf_service.add_book_to_shelf(shelf_id, isbn)


@shelf_app.route("/<int:shelf_id>/books/<string:isbn>/", methods=["DELETE"])
@jwt_required()
def remove_book_from_shelf(shelf_id, isbn):
    return shelf_service.remove_book_from_shelf(shelf_id, isbn)
