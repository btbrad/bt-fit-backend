"""应用入口: python wsgi.py（开发）/ wsgi:app（gunicorn 等部署方式）"""
import os

from dotenv import load_dotenv

# 在导入 app 之前加载 .env，使配置类读取到环境变量
load_dotenv()

from app import create_app

app = create_app(os.getenv("FLASK_CONFIG") or "default")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT") or 5000))
