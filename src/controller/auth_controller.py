from flask import Blueprint, request, jsonify
from src.data.dao.users_dao import UsersDAO
from src.data.model.user_model import UserModel
from src.util.user_util import user_to_dict

auth_api = Blueprint("auth_api", __name__)


@auth_api.route("/signup", methods=["POST"])
def signup():
    data = request.json
    required_fields = ["username", "email", "password", "role"]
    for field in required_fields:
        if not data.get(field):
            return (
                jsonify(
                    {
                        "error_code": 400,
                        "error_message": f"Missing required field: {field}",
                    }
                ),
                400,
            )

    if UsersDAO.get_user_by_username(data.get("username")):
        return (
            jsonify({"error_code": 409, "error_message": "Username already exists"}),
            409,
        )
    if UsersDAO.get_user_by_email(data.get("email")):
        return (
            jsonify({"error_code": 409, "error_message": "Email already exists"}),
            409,
        )

    user = UserModel(
        id=None,
        username=data.get("username"),
        email=data.get("email"),
        password=data.get("password"),
        first_name=data.get("first_name"),
        last_name=data.get("last_name"),
        date_of_birth=data.get("date_of_birth"),
        gender=data.get("gender"),
        phone=data.get("phone"),
        address=data.get("address"),
        current_latitude=data.get("current_latitude"),
        current_longitude=data.get("current_longitude"),
        current_diseases=data.get("current_diseases"),
        role=data.get("role"),
        is_active=True,
    )
    try:
        user = UsersDAO.create_user(user)
        return jsonify(user_to_dict(user)), 201
    except Exception as e:
        return jsonify({"error_code": 500, "error_message": str(e)}), 500


@auth_api.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return (
            jsonify(
                {
                    "error_code": 400,
                    "error_message": "Missing username or password",
                }
            ),
            400,
        )

    user = UsersDAO.get_user_by_username(username)
    if not user:
        return jsonify({"error_code": 404, "error_message": "User not found"}), 404

    if user.password != password:
        return jsonify({"error_code": 401, "error_message": "Invalid credentials"}), 401

    return jsonify(user_to_dict(user)), 200
