from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from src.services import user_service

user_app = Blueprint("users", __name__, url_prefix="/users")


@user_app.post("/register/")
def register():
    post_data = request.get_json()
    user_email = post_data["user_email"]
    user_password = post_data["user_password"]
    return user_service.create_user(user_email, user_password, is_admin=False)


@user_app.post("/login/")
def login():
    post_data = request.get_json()
    user_email = post_data["user_email"]
    user_password = post_data["user_password"]
    return user_service.login(user_email, user_password)


@user_app.get("/")
@jwt_required()
def all_users():
    return user_service.get_all_users()


@user_app.get("/<int:user_id>/")
@jwt_required()
def single_user(user_id):
    return user_service.get_single_user(user_id)


@user_app.get("/me/")
@jwt_required()
def me_user():
    return user_service.get_me_user()


@user_app.put("/<int:user_id>/")
@jwt_required()
def change_single_user(user_id):
    return user_service.change_single_user(request.get_json(), user_id)


@user_app.put("/me/")
@jwt_required()
def change_me_user():
    return user_service.change_me_user(request.get_json())


@user_app.delete("/<int:user_id>/")
@jwt_required()
def delete_single_user(user_id):
    return user_service.delete_single_user(user_id)


@user_app.delete("/me/")
@jwt_required()
def delete_me_user():
    return user_service.delete_me_user()
