项目结构

  bt-fit-backend/
  ├── app/
  │   ├── __init__.py      # 应用工厂 (create_app)
  │   ├── config.py        # 多环境配置（dev/test/prod，SQLite 存放在 data/）
  │   ├── extensions.py    # db, CORS 扩展实例
  │   ├── models.py        # User 模型
  │   ├── routes.py        # 蓝图路由（含 RESTful 用户 CRUD）
  │   └── cli.py           # flask init-db 命令
  ├── data/                # SQLite 数据库目录（自动创建）
  ├── wsgi.py              # 入口：python wsgi.py
  ├── requirements.txt     # flask 3.1.3 / flask-cors 6.0.5 / flask-sqlalchemy 3.1.1
  ├── .env.example
  └── .gitignore

  已验证的端点

  ┌────────────┬─────────────────┬────────────────────────────┐
  │    方法    │      路径       │            说明            │
  ├────────────┼─────────────────┼────────────────────────────┤
  │ GET        │ /health         │ 健康检查                   │
  虚拟环境（D:\python3__env\bt-fit），并且端点已通过实际运行验证。

  项目结构

  bt-fit-backend/
  ├── app/
  │   ├── __init__.py      # 应用工厂 (create_app)
  │   ├── config.py        # 多环境配置（dev/test/prod，SQLite 存放在 data/）
  │   ├── extensions.py    # db, CORS 扩展实例
  │   ├── models.py        # User 模型
  │   ├── routes.py        # 蓝图路由（含 RESTful 用户 CRUD）
  │   └── cli.py           # flask init-db 命令
  ├── data/                # SQLite 数据库目录（自动创建）
  ├── wsgi.py              # 入口：python wsgi.py
  ├── requirements.txt     # flask 3.1.3 / flask-cors 6.0.5 / flask-sqlalchemy 3.1.1
  ├── .env.example
  └── .gitignore

  已验证的端点

  ┌────────────┬─────────────────┬────────────────────────────┐

  ┌────────────┬─────────────────┬────────────────────────────┐
  │    方法    │      路径       │            说明            │
  ├────────────┼─────────────────┼────────────────────────────┤
  │ GET        │ /health         │ 健康检查                   │
  ├────────────┼─────────────────┼────────────────────────────┤
  │ GET        │ /api/users      │ 用户列表                   │
  ├────────────┼─────────────────┼────────────────────────────┤
  │ POST       │ /api/users      │ 创建用户（含重复校验 409） │
  ├────────────┼─────────────────┼────────────────────────────┤
  │ GET/DELETE │ /api/users/<id> │ 查询/删除用户              │
  └────────────┴─────────────────┴────────────────────────────┘

  使用方式

  # 激活虚拟环境
  D:\python3__env\bt-fit\Scripts\activate

  cd D:\code\bt-fit-backend
  flask --app wsgi init-db     # 首次初始化数据库
  python wsgi.py               # 启动开发服务器 (http://127.0.0.1:5000)

  切换环境可通过环境变量 FLASK_CONFIG=production，数据库可用 DATABASE_URL 覆盖（如 PostgreSQL）。测试服务器已停止，data/dev.db 中保留了一条测试数据（alice），可随时删除。