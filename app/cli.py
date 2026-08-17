"""Flask CLI 命令: flask init-db"""
import click
from flask.cli import with_appcontext

from .extensions import db


def register_cli(app):
    """注册自定义 CLI 命令"""
    @app.cli.command("init-db")
    def init_db_command():
        """创建所有数据库表"""
        db.create_all()
        click.echo("数据库表已创建。")
