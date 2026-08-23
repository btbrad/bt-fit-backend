from datetime import datetime
from functools import wraps

from flask import Blueprint, g, jsonify, request

from .extensions import db
from .models import User, WeightRecord

main_bp = Blueprint("main", __name__)


def ok(data=None, message="success"):
    """统一成功响应：HTTP 200，业务码 200"""
    return jsonify({"code": 200, "message": message, "data": data})


def fail(code, message):
    """统一业务失败响应：HTTP 200，业务码为非 200"""
    return jsonify({"code": code, "message": message, "data": None}), 200


def unauthorized(message):
    """认证失败响应：HTTP 401，仅用于 token 缺失 / 无效 / 过期"""
    return jsonify({"code": 401, "message": message, "data": None}), 401


def auth_required(view):
    """从 Authorization: Bearer <token> 解析当前用户的装饰器"""

    @wraps(view)
    def wrapped(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return unauthorized("缺少 token，请先登录")
        user = User.verify_token(parts[1])
        if user is None:
            return unauthorized("token 无效或已过期")
        g.user = user
        return view(*args, **kwargs)

    return wrapped


@main_bp.get("/")
def index():
    return ok({"message": "Welcome to BT-Fit API", "status": "running"})


@main_bp.get("/health")
def health():
    return ok({"status": "ok"})


@main_bp.get("/api/users")
def list_users():
    users = User.query.all()
    return ok([u.to_dict() for u in users])


@main_bp.post("/api/users")
def create_user():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return fail(400, "username 和 password 为必填项")

    if User.query.filter_by(username=username).first():
        return fail(409, "用户名已存在")

    user = User(username=username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return ok(user.to_dict())


@main_bp.post("/api/register")
def register():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")
    confirm_password = data.get("confirm_password", "")

    if not username or not password or not confirm_password:
        return fail(400, "username、password 和 confirm_password 为必填项")

    if password != confirm_password:
        return fail(400, "两次输入的密码不一致")

    if User.query.filter_by(username=username).first():
        return fail(409, "用户名已存在")

    user = User(username=username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return ok(user.to_dict())


@main_bp.post("/api/login")
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return fail(400, "username 和 password 为必填项")

    user = User.query.filter_by(username=username).first()
    if user is None or not user.check_password(password):
        # 用户名/密码错误属于业务校验失败，不是权限问题：
        # 返回 HTTP 200 + 非 200 业务码，HTTP 401 仅保留给 token 失效
        return fail(400, "用户名或密码错误")

    token = user.generate_token()
    return ok({"token": token, "user": user.to_dict()})


@main_bp.post("/api/weight-records")
@auth_required
def create_weight_record():
    data = request.get_json(silent=True) or {}
    weight = data.get("weight")
    note = data.get("note", "")
    recorded_at = data.get("recorded_at")

    if weight is None:
        return fail(400, "weight 为必填项")

    try:
        weight = float(weight)
    except (TypeError, ValueError):
        return fail(400, "weight 必须是数字")

    if not (20 <= weight <= 300):
        return fail(400, "weight 需在 20 ~ 300 kg 之间")

    # recorded_at 可选，支持补录；格式 YYYY-MM-DDTHH:MM:SS
    if recorded_at:
        try:
            recorded_at = datetime.fromisoformat(recorded_at)
        except (TypeError, ValueError):
            return fail(400, "recorded_at 格式应为 YYYY-MM-DDTHH:MM:SS")

    record = WeightRecord(user_id=g.user.id, weight=weight, note=note or None)
    if recorded_at:
        record.recorded_at = recorded_at
    db.session.add(record)
    db.session.commit()
    return ok(record.to_dict())


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
        return fail(400, "start/end 格式应为 YYYY-MM-DD 或 YYYY-MM-DDTHH:MM:SS")

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    per_page = min(per_page, 100)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return ok(
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
        return fail(404, "记录不存在")
    db.session.delete(record)
    db.session.commit()
    return ok()


@main_bp.get("/api/users/<int:user_id>")
def get_user(user_id):
    user = User.query.get(user_id)
    if user is None:
        return fail(404, "用户不存在")
    return ok(user.to_dict())


@main_bp.delete("/api/users/<int:user_id>")
def delete_user(user_id):
    user = User.query.get(user_id)
    if user is None:
        return fail(404, "用户不存在")
    db.session.delete(user)
    db.session.commit()
    return ok()
