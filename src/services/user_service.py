from flask import jsonify
from flask_jwt_extended import create_access_token, get_jwt_identity

from src.bcrypt import bcrypt
from src.database import db
from src.models.user import User


def create_user(user_email: str, user_password: str, is_admin: bool):
    user = User.query.filter_by(user_email=user_email).first()
    if user is not None:
        return jsonify({"description": f"user '{user_email}' already exists in database"}), 409

    hashed_password = bcrypt.generate_password_hash(user_password).decode()
    new_user = User(
        user_email=user_email,
        user_password=hashed_password,
        is_admin=is_admin,
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify(new_user.to_dict()), 201


def login(user_email: str, user_password: str):
    user = User.query.filter_by(user_email=user_email).first()
    if user and bcrypt.check_password_hash(user.user_password, user_password):
        access_token = create_access_token(identity=str(user.user_id))
        return jsonify({
            "message": "Login Success",
            "access_token": access_token,
            "user_name": user.user_name,
            "user_email": user.user_email,
        })
    return jsonify({"description": "Access Denied: bad login or password"}), 401


def _get_current_user():
    current_user_id = get_jwt_identity()
    return User.query.filter_by(user_id=current_user_id).first()


def get_all_users():
    logged_user = _get_current_user()
    if not logged_user:
        return jsonify({"description": "user not found"}), 404
    if not logged_user.is_administrator():
        return jsonify({"description": "Unauthorized"}), 401
    users = User.query.all()
    return jsonify([user.to_dict() for user in users]), 200


def get_single_user(user_id):
    logged_user = _get_current_user()
    if not logged_user:
        return jsonify({"description": "user not found"}), 404
    if not logged_user.is_administrator():
        return jsonify({"description": "Unauthorized"}), 401
    checked_user = User.query.get(user_id)
    if checked_user is None:
        return jsonify({"description": "User not found"}), 404
    return jsonify(checked_user.to_dict()), 200


def get_me_user():
    logged_user = _get_current_user()
    if not logged_user:
        return jsonify({"description": "user not found"}), 404
    return jsonify(logged_user.to_dict()), 200


def change_single_user(data, user_id):
    logged_user = _get_current_user()
    if not logged_user:
        return jsonify({"description": "user not found"}), 404
    if not logged_user.is_administrator():
        return jsonify({"description": "Unauthorized"}), 401
    changed_user = User.query.get(user_id)
    if changed_user is None:
        return jsonify({"description": "User not found"}), 404

    if "user_email" in data:
        changed_user.user_email = data["user_email"]
    if "user_name" in data:
        changed_user.user_name = data["user_name"]
    if "user_password" in data:
        changed_user.user_password = bcrypt.generate_password_hash(data["user_password"]).decode()

    db.session.commit()
    return jsonify(changed_user.to_dict()), 200


def change_me_user(data):
    logged_user = _get_current_user()
    if not logged_user:
        return jsonify({"description": "user not found"}), 404

    if "user_email" in data:
        logged_user.user_email = data["user_email"]
    if "user_name" in data:
        logged_user.user_name = data["user_name"]
    if "user_password" in data:
        logged_user.user_password = bcrypt.generate_password_hash(data["user_password"]).decode()

    db.session.commit()
    return jsonify(logged_user.to_dict()), 200


def delete_single_user(user_id):
    logged_user = _get_current_user()
    if not logged_user:
        return jsonify({"description": "user not found"}), 404
    if not logged_user.is_administrator():
        return jsonify({"description": "Unauthorized"}), 401
    deleted_user = User.query.get(user_id)
    if deleted_user is None:
        return jsonify({"description": "User not found"}), 404
    db.session.delete(deleted_user)
    db.session.commit()
    return jsonify({"description": f"user {user_id} deleted"}), 200


def delete_me_user():
    logged_user = _get_current_user()
    if not logged_user:
        return jsonify({"description": "user not found"}), 404
    db.session.delete(logged_user)
    db.session.commit()
    return jsonify({"description": "account deleted"}), 200
