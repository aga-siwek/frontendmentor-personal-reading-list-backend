from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from src.services import user_service

user_app = Blueprint("users", __name__, url_prefix="/users")

@user_app.post("/register/")
def register():
    post_data = request.get_json
    user_email = post_data["user_email"]
    user_password = post_data["user_password"]
    is_admin = False
    return user_service.create_user(user_email, user_password, is_admin)

@user_app.post("/login/")
def login():
    post_data = request.get_json
    user_email = post_data["user_email"]
    user_password = post_data["user_password"]
    return user_service.login(user_email, user_password)

#for admin
@user_app.route("/users/", methods=["GET"])
@jwt_required()
def all_users():
    return user_service.get_all_users()

#for admin
@user_app.route("/users/<user_id>", methods=["GET"])
@jwt_required()
def single_user(user_id):
    return user_service.get_single_user(user_id)

#for user
@user_app.route("/users/me", methods=["GET"])
@jwt_required()
def me_user():
    return user_service.get_me_user()

#for admin
@user_app.route("/users/<user_id>", methods=["PUT"])
@jwt_required()
def change_single_user(user_id):
    put_request = request.json
    return user_service.change_single_user(put_request, user_id)

#for user
@user_app.route("/users/me", methods=["PUT"])
@jwt_required()
def change_me_user():
    put_request = request.json
    return user_service.change_me_user(put_request)

#for admin
@user_app.route("/users/<user_id>", methods=["DELETE"])
@jwt_required()
def delete_single_user(user_id):
    return user_service.delete_single_user(user_id)

#for user
@user_app.route("/users/me", methods=["DELETE"])
@jwt_required()
def delete_me_user():
    return user_service.delete_me_user()