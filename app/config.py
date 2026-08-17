import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)


def _sqlite_uri(filename):
    """返回指向 data/ 目录的 sqlite URI（目录不存在时自动创建）"""
    return "sqlite:///" + os.path.join(DATA_DIR, filename).replace("\\", "/")



class Config:
    """基础配置"""
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_AS_ASCII = False


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DEV_DATABASE_URL"
    ) or _sqlite_uri("dev.db")


class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProductionConfig(Config):
    """生产环境配置"""
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL"
    ) or _sqlite_uri("app.db")


config = {
    "default": DevelopmentConfig,
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
