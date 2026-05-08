from flask import jsonify
from flask_jwt_extended import get_jwt_identity

from src.database import db
from src.models.reading_goal import ReadingGoal
from src.models.user import User
from src.models.user_book import UserBook, BookStatus


def _get_current_user():
    return User.query.filter_by(user_id=int(get_jwt_identity())).first()


def _goal_to_dict(goal: ReadingGoal) -> dict:
    data = goal.to_dict()
    finished_count = UserBook.query.filter_by(
        user_id=goal.user_id, status=BookStatus.FINISHED
    ).filter(
        db.func.extract("year", UserBook.last_updated) == goal.year
    ).count()
    data["books_finished"] = finished_count
    return data


def get_me_goals():
    user = _get_current_user()
    if not user:
        return jsonify({"error": "User not found"}), 404
    goals = ReadingGoal.query.filter_by(user_id=user.user_id).order_by(ReadingGoal.year.desc()).all()
    return jsonify([_goal_to_dict(g) for g in goals]), 200


def get_me_goal(year: int):
    user = _get_current_user()
    if not user:
        return jsonify({"error": "User not found"}), 404
    goal = ReadingGoal.query.filter_by(user_id=user.user_id, year=year).first()
    if not goal:
        return jsonify({"error": "Goal not found"}), 404
    return jsonify(_goal_to_dict(goal)), 200


def create_me_goal(year: int, goal: int):
    user = _get_current_user()
    if not user:
        return jsonify({"error": "User not found"}), 404
    existing = ReadingGoal.query.filter_by(user_id=user.user_id, year=year).first()
    if existing:
        return jsonify({"error": f"Goal for {year} already exists"}), 409
    new_goal = ReadingGoal(user_id=user.user_id, year=year, goal=goal)
    db.session.add(new_goal)
    db.session.commit()
    return jsonify(_goal_to_dict(new_goal)), 201


def update_me_goal(year: int, data: dict):
    user = _get_current_user()
    if not user:
        return jsonify({"error": "User not found"}), 404
    goal = ReadingGoal.query.filter_by(user_id=user.user_id, year=year).first()
    if not goal:
        return jsonify({"error": "Goal not found"}), 404
    if "goal" in data:
        goal.goal = data["goal"]
    db.session.commit()
    return jsonify(_goal_to_dict(goal)), 200


def delete_me_goal(year: int):
    user = _get_current_user()
    if not user:
        return jsonify({"error": "User not found"}), 404
    goal = ReadingGoal.query.filter_by(user_id=user.user_id, year=year).first()
    if not goal:
        return jsonify({"error": "Goal not found"}), 404
    db.session.delete(goal)
    db.session.commit()
    return jsonify({"message": f"Goal for {year} deleted"}), 200
