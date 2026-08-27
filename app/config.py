import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)


def _sqlite_uri(filename):
    """返回指向 data/ 目录的 sqlite URI（目录不存在时自动创建）"""
    return "sqlite:///" + os.path.join(DATA_DIR, filename).replace("\\", "/")


def _cors_origins():
    """解析 CORS_ORIGINS 环境变量为列表。

    - 未设置：返回 None（交由各环境配置类决定默认行为）
    - 设置为 *：返回 "*"，允许所有来源（等价于 CORS(app) 的默认行为）
    - 逗号分隔多个域名：返回域名列表
    """
    raw = os.environ.get("CORS_ORIGINS")
    if raw is None:
        return None
    raw = raw.strip()
    if not raw:
        return None
    if raw == "*":
        return "*"
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


class Config:
    """基础配置"""
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
    CORS_ORIGINS = _cors_origins()  # None 表示未配置
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_AS_ASCII = False


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    # 开发环境默认允许所有来源，方便本地联调
    CORS_ORIGINS = _cors_origins() or "*"
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DEV_DATABASE_URL"
    ) or _sqlite_uri("dev.db")


class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProductionConfig(Config):
    """生产环境配置"""
    # 生产环境未显式配置 CORS_ORIGINS 时不放行任何跨域来源
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL"
    ) or _sqlite_uri("app.db")


config = {
    "default": DevelopmentConfig,
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
