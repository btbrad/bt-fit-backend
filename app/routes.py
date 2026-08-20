from flask import Blueprint, jsonify, request

from .extensions import db
from .models import User

main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def index():
    return jsonify({"message": "Welcome to BT-Fit API", "status": "running"})


@main_bp.get("/health")
def health():
    return jsonify({"status": "ok"})


@main_bp.get("/api/users")
def list_users():
    users = User.query.all()
    return jsonify([u.to_dict() for u in users])


@main_bp.post("/api/users")
def create_user():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify({"error": "username 和 password 为必填项"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "用户名已存在"}), 409

    user = User(username=username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201


@main_bp.post("/api/login")
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "username 和 password 为必填项"}), 400

    user = User.query.filter_by(username=username).first()
    if user is None or not user.check_password(password):
        return jsonify({"error": "用户名或密码错误"}), 401

    token = user.generate_token()
    return jsonify({"token": token, "user": user.to_dict()})


@main_bp.get("/api/users/<int:user_id>")
def get_user(user_id):
    user = db.get_or_404(User, user_id)
    return jsonify(user.to_dict())


@main_bp.delete("/api/users/<int:user_id>")
def delete_user(user_id):
    user = db.get_or_404(User, user_id)
    db.session.delete(user)
    db.session.commit()
    return "", 204
