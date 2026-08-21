from datetime import datetime
from functools import wraps

from flask import Blueprint, g, jsonify, request

from .extensions import db
from .models import User, WeightRecord

main_bp = Blueprint("main", __name__)


def auth_required(view):
    """从 Authorization: Bearer <token> 解析当前用户的装饰器"""

    @wraps(view)
    def wrapped(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return jsonify({"error": "缺少 token，请先登录"}), 401
        user = User.verify_token(parts[1])
        if user is None:
            return jsonify({"error": "token 无效或已过期"}), 401
        g.user = user
        return view(*args, **kwargs)

    return wrapped


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


@main_bp.post("/api/register")
def register():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")
    confirm_password = data.get("confirm_password", "")

    if not username or not password or not confirm_password:
        return jsonify({"error": "username、password 和 confirm_password 为必填项"}), 400

    if password != confirm_password:
        return jsonify({"error": "两次输入的密码不一致"}), 400

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


@main_bp.post("/api/weight-records")
@auth_required
def create_weight_record():
    data = request.get_json(silent=True) or {}
    weight = data.get("weight")
    note = data.get("note", "")
    recorded_at = data.get("recorded_at")

    if weight is None:
        return jsonify({"error": "weight 为必填项"}), 400

    try:
        weight = float(weight)
    except (TypeError, ValueError):
        return jsonify({"error": "weight 必须是数字"}), 400

    if not (20 <= weight <= 300):
        return jsonify({"error": "weight 需在 20 ~ 300 kg 之间"}), 400

    # recorded_at 可选，支持补录；格式 YYYY-MM-DDTHH:MM:SS
    if recorded_at:
        try:
            recorded_at = datetime.fromisoformat(recorded_at)
        except (TypeError, ValueError):
            return jsonify({"error": "recorded_at 格式应为 YYYY-MM-DDTHH:MM:SS"}), 400

    record = WeightRecord(user_id=g.user.id, weight=weight, note=note or None)
    if recorded_at:
        record.recorded_at = recorded_at
    db.session.add(record)
    db.session.commit()
    return jsonify(record.to_dict()), 201


@main_bp.get("/api/weight-records")
@auth_required
def list_weight_records():
    query = g.user.weight_records.order_by(WeightRecord.recorded_at.desc())

    # 可选时间范围筛选: ?start=2026-08-01&end=2026-08-21
    start = request.args.get("start")
    end = request.args.get("end")
    try:
        if start:
            query = query.filter(WeightRecord.recorded_at >= datetime.fromisoformat(start))
        if end:
            query = query.filter(WeightRecord.recorded_at <= datetime.fromisoformat(end))
    except ValueError:
        return jsonify({"error": "start/end 格式应为 YYYY-MM-DD 或 YYYY-MM-DDTHH:MM:SS"}), 400

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    per_page = min(per_page, 100)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify(
        {
            "items": [r.to_dict() for r in pagination.items],
            "total": pagination.total,
            "page": pagination.page,
            "per_page": pagination.per_page,
        }
    )


@main_bp.delete("/api/weight-records/<int:record_id>")
@auth_required
def delete_weight_record(record_id):
    record = WeightRecord.query.filter_by(id=record_id, user_id=g.user.id).first()
    if record is None:
        return jsonify({"error": "记录不存在"}), 404
    db.session.delete(record)
    db.session.commit()
    return "", 204


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
