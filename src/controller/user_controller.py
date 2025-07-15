import datetime
from flask import Blueprint, request, jsonify
from src.data.dao.users_dao import UsersDAO
from src.data.model.user_model import UserModel
from src.util.user_util import user_to_dict

user_api = Blueprint("user_api", __name__)


@user_api.route("/users", methods=["GET"])
def get_all_users():
    users = UsersDAO.get_all_users()
    return jsonify([user_to_dict(user) for user in users])


@user_api.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    user = UsersDAO.get_user_by_id(user_id)
    if user:
        return jsonify(user_to_dict(user))
    return jsonify({"error": "User not found"}), 404


@user_api.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    data = request.json
    user = UsersDAO.get_user_by_id(user_id)
    if not user:
        return jsonify({"error_code": 404, "error_message": "User not found"}), 404

    # Các trường required không được update
    required_fields = {
        "id",
        "username",
        "email",
        "password",
        "role",
        "is_active",
    }
    for key, value in data.items():
        if key in required_fields:
            continue
        if hasattr(user, key):
            setattr(user, key, value)

    UsersDAO.update_user(user)
    return jsonify(user_to_dict(user))


@user_api.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    success = UsersDAO.delete_user(user_id)
    if success:
        return jsonify({"success": True})
    return jsonify({"error": "User not found"}), 404
