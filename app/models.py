from datetime import datetime, timedelta, timezone

import jwt
from werkzeug.security import check_password_hash, generate_password_hash

from flask import current_app

from .extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def set_password(self, password):
        """将明文密码哈希后存储"""
        self.password = generate_password_hash(password)

    def check_password(self, password):
        """校验明文密码是否与存储的哈希匹配"""
        return check_password_hash(self.password, password)

    def generate_token(self, expires_in=3600 * 24 * 7):
        """生成 JWT token，默认7天有效"""
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(self.id),
            "username": self.username,
            "iat": now,
            "exp": now + timedelta(seconds=expires_in),
        }
        return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")

    @staticmethod
    def verify_token(token):
        """校验 JWT token，有效则返回对应的 User，否则返回 None"""
        try:
            payload = jwt.decode(
                token, current_app.config["SECRET_KEY"], algorithms=["HS256"]
            )
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        return db.session.get(User, int(payload["sub"]))

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<User {self.username}>"


class UserProfile(db.Model):
    """用户信息表，与 users 一对一关联"""

    __tablename__ = "user_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    nickname = db.Column(db.String(50))  # 昵称
    avatar = db.Column(db.String(255))  # 头像 URL
    gender = db.Column(db.String(10))  # male / female / other
    height = db.Column(db.Numeric(5, 2))  # 身高，单位: cm
    initial_weight = db.Column(db.Numeric(5, 2))  # 初始体重，单位: kg
    birthday = db.Column(db.Date)  # 生日，可选
    updated_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )

    user = db.relationship(
        "User",
        backref=db.backref("profile", uselist=False, cascade="all, delete-orphan"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "nickname": self.nickname,
            "avatar": self.avatar,
            "gender": self.gender,
            "height": float(self.height) if self.height is not None else None,
            "initial_weight": (
                float(self.initial_weight) if self.initial_weight is not None else None
            ),
            "birthday": self.birthday.isoformat() if self.birthday else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<UserProfile user_id={self.user_id}>"


class WeightRecord(db.Model):
    __tablename__ = "weight_records"
    __table_args__ = (
        db.Index("ix_weight_records_user_recorded", "user_id", "recorded_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    weight = db.Column(db.Numeric(5, 2), nullable=False)  # 单位: kg
    recorded_at = db.Column(
        db.DateTime, nullable=False, default=db.func.current_timestamp()
    )
    note = db.Column(db.String(200))  # 备注，如"晨起空腹"
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    user = db.relationship(
        "User",
        backref=db.backref(
            "weight_records",
            lazy="dynamic",
            order_by="WeightRecord.recorded_at",
            cascade="all, delete-orphan",
        ),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "weight": float(self.weight),
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
            "note": self.note,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<WeightRecord {self.user_id} {self.weight}kg {self.recorded_at}>"
