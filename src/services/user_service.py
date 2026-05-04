from flask import jsonify

from src.bcrypt import bcrypt
from src.database import db
from src.models.user import User
from flask_jwt_extended import create_access_token, get_current_user, get_jwt_identity

_users: list[User] = []
_next_id = 1

def create_user(user_email: str, user_password:str, is_admin: bool):
    user = User.query.filter_by(email=user_email).first()
    if user is not None:
        return jsonify({"description": f"user '{user_email}' already exists in database"}), 409

    hasted_password = bcrypt.generate_password_hash(user_password).decode()
    new_user = User(
        user_email=user_email,
        user_password=hasted_password,
        is_admin=is_admin
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify(new_user.to_dict()), 201


def login_user(user_email: str, user_password: str):
    user = User.query.filter_by(email=user_email).first()
    if user and bcrypt.check_password_hash(user.user_password, user_password):
        access_token = create_access_token(identity=str(user.user.id))
        return jsonify({"message": "Login Success", "access_token": access_token, "user_name": user.user_name,
                        "user_email": user_email})
    return jsonify({"description": "Access Denied: bad login or password"}), 401

def get_current_user():
    current_user = get_jwt_identity()
    user = User.query.filter_by(user_id=current_user).first()
    return user

def get_all_users():
    logged_user = get_current_user()
    if not logged_user:
        return jsonify({"description": "not user found"})
    if not logged_user.is_administrator():
        return jsonify({"description": "Unauthorized"}), 401
    users = User.query.all()
    user_dict = [user.to_dict() for user in users]
    return jsonify(user_dict), 200

def get_single_user(user_id):
    logged_user = get_current_user()
    checked_user = User.query.get(user_id)
    if not logged_user:
        return jsonify({"description": "not user found"})
    if not logged_user.is_administrator():
        return jsonify({"description": "Unauthorized"}), 401
    if checked_user is None:
        return jsonify({"description": "User not found"}, 404)
    return jsonify(checked_user.to_dict(), 200)

def get_me_user():
    logged_user = get_current_user()
    if not logged_user:
        return jsonify({"description": "not user found"}, 404)
    return jsonify(logged_user.to_dict(), 200)

def change_single_user(data, user_id):
    logged_user = get_current_user()
    changed_user = User.query.get(user_id)

    if not logged_user:
        return jsonify({"description": "not user found"})
    if not logged_user.is_administrator():
        return jsonify({"description": "Unauthorized"}), 401

    try:
        print(data, "data from user service")

        if "user_email" in data.keys():
            changed_user.user_email = data["user_email"]
        if "user_password" in data.keys():
            changed_user.user_password = data["user_password"]
        if "user_name" in data.keys():
            changed_user.user_password = data["user_name"]

        db.session.commit()

        return jsonify(changed_user.to_dict(), 200)

    except:
        return jsonify({"description": "Unauthorized, try another email"})

def change_me_user(data):
    logged_user = get_current_user()

    if not logged_user:
        return jsonify({"description": "not user found"})

    try:
        if "user_email" in data.keys():
            logged_user.user_email = data["user_email"]
        if "user_name" in data.keys():
            logged_user.user_name = data["user_name"]
        if "user_password" in data.keys():
            logged_user.user_password = data["user_password"]

        db.session.commit()

        return jsonify(logged_user.to_dict(), 200)

    except:
        return jsonify({"description": "Unauthorized, try another email"})

def delete_single_user(user_id):
    logged_user = get_current_user()
    deleted_user = User.query.get(user_id)

    if not logged_user:
        return jsonify({"description": "not user found"})
    if not logged_user.is_administrator():
        return jsonify({"description": "unauthorized"}), 401

    db.session.delete(deleted_user)
    db.session.commit()

    return jsonify({"description": f"user {user_id} deleted"}), 200
