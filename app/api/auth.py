from flask import Blueprint, request
from flask_jwt_extended import create_access_token
from werkzeug.security import check_password_hash
from app.models import User

api_auth = Blueprint("api_auth", __name__)

@api_auth.route("/login", methods=["POST"])
def login():
    data = request.json
    user = User.query.filter_by(email=data["email"]).first()

    if not user or not check_password_hash(user.password, data["password"]):
        return {"error": "Invalid credentials"}, 401

    token = create_access_token(
        identity=user.id,
        additional_claims={"role": user.role}
    )

    return {"access_token": token}
