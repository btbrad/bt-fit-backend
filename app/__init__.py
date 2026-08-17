from flask import Flask


def create_app(config_name="default"):
    """应用工厂函数"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # 初始化扩展
    db.init_app(app)
    CORS(app)

    # 注册路由
    from .routes import main_bp

    app.register_blueprint(main_bp)

    # 注册 CLI 命令
    from .cli import register_cli

    register_cli(app)

    return app


from .config import config
from .extensions import db, CORS
