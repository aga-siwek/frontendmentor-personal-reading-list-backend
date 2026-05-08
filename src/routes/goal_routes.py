from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from src.services import goal_service

goal_app = Blueprint("goals", __name__, url_prefix="/goals")


@goal_app.route("/me/", methods=["GET"])
@jwt_required()
def get_me_goals():
    return goal_service.get_me_goals()


@goal_app.route("/me/<int:year>/", methods=["GET"])
@jwt_required()
def get_me_goal(year):
    return goal_service.get_me_goal(year)


@goal_app.route("/me/", methods=["POST"])
@jwt_required()
def create_me_goal():
    data = request.get_json() or {}
    year = data.get("year")
    goal = data.get("goal")
    if year is None or goal is None:
        return {"error": "year and goal are required"}, 400
    return goal_service.create_me_goal(year, goal)


@goal_app.route("/me/<int:year>/", methods=["PATCH"])
@jwt_required()
def update_me_goal(year):
    data = request.get_json() or {}
    return goal_service.update_me_goal(year, data)


@goal_app.route("/me/<int:year>/", methods=["DELETE"])
@jwt_required()
def delete_me_goal(year):
    return goal_service.delete_me_goal(year)
