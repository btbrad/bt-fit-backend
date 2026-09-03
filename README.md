# BT-Fit Backend

基于 **Flask** 的后端 API 服务，采用应用工厂（Application Factory）模式组织代码，提供用户管理相关的 RESTful 接口。

## 技术栈

| 组件 | 版本 | 说明 |
|------|------|------|
| Python | 3.14+ | 运行环境 |
| Flask | 3.1.3 | Web 框架 |
| Flask-SQLAlchemy | 3.1.1 | ORM（基于 SQLAlchemy 2.x） |
| Flask-CORS | 6.0.5 | 跨域支持 |
| PyJWT | 2.13.0 | 登录 token 生成与校验（JWT / HS256） |
| SQLite | — | 默认数据库，可通过配置切换 PostgreSQL / MySQL 等 |

## 项目结构

```
bt-fit-backend/
├── app/
│   ├── __init__.py      # 应用工厂 create_app()，注册蓝图与扩展
│   ├── config.py        # 多环境配置（development / testing / production）
│   ├── extensions.py    # 扩展实例：db (SQLAlchemy)、CORS
│   ├── models.py        # 数据模型：User、WeightRecord
│   ├── routes.py        # 蓝图路由：健康检查 + 用户 CRUD + 体重记录
│   └── cli.py           # 自定义 CLI 命令：flask init-db
├── data/                # SQLite 数据库文件目录（首次运行自动创建）
├── wsgi.py              # 应用入口（开发服务器 / WSGI 部署均使用）
├── requirements.txt     # Python 依赖清单
├── .env.example         # 环境变量示例
└── .gitignore
```

## 环境准备

### 前置要求

- Python 3.14 或更高版本
- 已存在的虚拟环境 `bt-fit`（位于 `D:\python3__env\bt-fit`）

### 激活虚拟环境

```bash
# Git Bash / Linux / macOS
source /d/python3__env/bt-fit/Scripts/activate

# Windows CMD
D:\python3__env\bt-fit\Scripts\activate.bat

# Windows PowerShell
D:\python3__env\bt-fit\Scripts\Activate.ps1
```

### 安装依赖

```bash
pip install -r requirements.txt
```

## 快速开始

```bash
cd D:\code\bt-fit-backend

# 1. 初始化数据库（创建 data/dev.db 及所有表）
flask --app wsgi init-db

# 2. 启动开发服务器
python wsgi.py
```

服务默认运行在 <http://127.0.0.1:5000>，验证：

```bash
curl http://127.0.0.1:5000/health
# {"status":"ok"}
```

> 开发模式默认开启 `DEBUG=True`，代码修改后自动重载。

## 配置说明

配置通过 `FLASK_CONFIG` 环境变量选择，默认为 `development`。三种环境对应 `app/config.py` 中的配置类：

| 环境名 | 配置类 | DEBUG | 数据库 |
|--------|--------|-------|--------|
| `development`（默认） | `DevelopmentConfig` | ✅ | `data/dev.db` |
| `testing` | `TestingConfig` | — | SQLite 内存库 |
| `production` | `ProductionConfig` | ❌ | `data/app.db`（建议用 `DATABASE_URL` 覆盖） |

### 环境变量

配置通过项目根目录的 `.env` 文件加载（由 `python-dotenv` 提供，`wsgi.py` 启动时自动读取，优先级低于已存在的系统环境变量）。参考 `.env.example`：

| 变量 | 作用 | 默认值 |
|------|------|--------|
| `FLASK_CONFIG` | 选择环境：`development` / `testing` / `production` | `default`（即 development） |
| `SECRET_KEY` | JWT / 会话签名密钥，生产环境必须为强随机值 | `dev-secret-key-change-me` |
| `DATABASE_URL` | 覆盖生产环境数据库 URI | `sqlite:///data/app.db` |
| `DEV_DATABASE_URL` | 覆盖开发环境数据库 URI | `sqlite:///data/dev.db` |
| `CORS_ORIGINS` | 允许跨域的前端来源，逗号分隔多个；`*` 为全部放行 | 开发环境默认 `*`；**生产环境默认不放行任何跨域** |
| `PORT` | 开发服务器端口（仅 `python wsgi.py` 生效） | `5000` |

首次部署时复制模板生成本地配置：

```bash
cp .env.example .env
# 生成强随机密钥填入 SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"
```

`.env` 已加入 `.gitignore`，不会提交到仓库；上传服务器时可单独拷贝（scp）到服务器项目根目录。

切换到 PostgreSQL 示例：

```bash
set FLASK_CONFIG=production
set DATABASE_URL=postgresql://user:pass@localhost:5432/btfit
python wsgi.py
```

## API 文档

所有响应均为 JSON 格式。基础地址：`http://127.0.0.1:5000`

### 统一响应格式

每个接口的响应体均包含 `code`、`message`、`data` 三个字段：

```json
{
  "code": 200,
  "message": "success",
  "data": { }
}
```

| 字段 | 说明 |
|------|------|
| `code` | 业务码。`200` 表示请求成功；非 `200` 表示业务失败（如 `400` 参数错误、`404` 不存在、`409` 重复） |
| `message` | 提示信息，成功为 `success`，失败为具体错误原因 |
| `data` | 业务数据，失败时为 `null` |

HTTP 状态码约定：

- **`200`** — 正常处理完毕（含业务失败，此时看 body 中的 `code`）。登录接口的用户名/密码错误属于业务校验失败，返回 HTTP 200 + 非 200 的 `code`。
- **`401`** — 仅表示无权限或权限过期：请求头缺少 token、token 无效或已过期。

### 根路径与健康检查

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 欢迎信息 |
| GET | `/health` | 健康检查 |

```bash
curl http://127.0.0.1:5000/
# {"code":200,"message":"success","data":{"message":"Welcome to BT-Fit API","status":"running"}}
```

### 用户管理

#### 获取用户列表

```
GET /api/users
```

**响应 `200`（`code: 200`）：**

```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": 1,
      "username": "alice",
      "created_at": "2026-08-17T13:48:46"
    }
  ]
}
```

#### 创建用户

```
POST /api/users
Content-Type: application/json
```

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `username` | string | ✅ | 用户名，唯一 |
| `password` | string | ✅ | 密码（存储时使用 `generate_password_hash` 哈希，不会明文保存） |

```bash
curl -X POST http://127.0.0.1:5000/api/users \
  -H "Content-Type: application/json" \
  -d '{"username":"bob","password":"secret123"}'
```

**响应 `200`（`code: 200`）：** `data` 为创建的用户对象。

**错误响应（HTTP 200，`code` 非 200）：**

- `code: 400` — `username` 或 `password` 缺失 / 为空
- `code: 409` — 用户名已存在

#### 用户登录

```
POST /api/login
Content-Type: application/json
```

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `username` | string | ✅ | 用户名 |
| `password` | string | ✅ | 密码 |

```bash
curl -X POST http://127.0.0.1:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"secret123"}'
```

**响应 `200`（`code: 200`）：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "user": { "id": 1, "username": "alice", "created_at": "2026-08-17T13:48:46" }
  }
}
```

token 为 JWT（HS256），默认 1 小时有效。

**错误响应（HTTP 200，`code` 非 200）：**

- `code: 400` — `username` 或 `password` 缺失 / 为空
- `code: 400` — 用户名或密码错误（用户不存在与密码错误返回相同提示，避免枚举用户名；登录不涉及权限校验，因此**不返回 HTTP 401**）

#### 退出登录

```
POST /api/logout
```

需携带 `Authorization: Bearer <token>`。JWT 无状态，服务端校验 token 有效后直接返回成功，由客户端删除本地 token 完成退出登录；未携带或 token 无效 / 过期返回 HTTP `401`。

```bash
curl -X POST http://127.0.0.1:5000/api/logout \
  -H "Authorization: Bearer <token>"
# {"code":200,"message":"success","data":null}
```

#### 修改密码

```
POST /api/change-password
Content-Type: application/json
```

需携带 `Authorization: Bearer <token>`；未携带或 token 无效 / 过期返回 HTTP `401`。

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `old_password` | string | ✅ | 原密码 |
| `new_password` | string | ✅ | 新密码 |
| `confirm_password` | string | ✅ | 确认新密码，需与 `new_password` 一致 |

```bash
curl -X POST http://127.0.0.1:5000/api/change-password \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"old_password":"secret123","new_password":"newpass456","confirm_password":"newpass456"}'
# {"code":200,"message":"success","data":null}
```

修改成功后当前 token 仍然有效，可直接用新密码继续使用；下次登录时使用新密码。

**错误响应（HTTP 200，`code` 非 200）：**

- `code: 400` — 字段缺失 / 为空
- `code: 400` — 原密码错误
- `code: 400` — 两次输入的新密码不一致
- `code: 400` — 新密码与原密码相同

#### 查询单个用户

```
GET /api/users/<id>
```

**响应 `200`：** `data` 为用户对象；用户不存在时返回 `code: 404`。

#### 删除用户

```
DELETE /api/users/<id>
```

**响应 `200`（`code: 200`）：** 删除成功；用户不存在时返回 `code: 404`。

### 体重记录

> 以下接口均需登录，请求头携带 `Authorization: Bearer <token>`（登录接口返回的 JWT）。未携带或 token 无效 / 过期返回 **HTTP `401`**；只能操作自己的记录。

#### 记录体重

```
POST /api/weight-records
Content-Type: application/json
```

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `weight` | number | ✅ | 体重（kg），需在 20 ~ 300 之间 |
| `recorded_at` | string | ❌ | 测量时间，ISO 格式 `YYYY-MM-DDTHH:MM:SS`，缺省为当前时间（支持补录） |
| `note` | string | ❌ | 备注，最长 200 字符 |

```bash
curl -X POST http://127.0.0.1:5000/api/weight-records \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"weight": 75.5, "note": "晨起空腹"}'
```

**响应 `200`（`code: 200`）：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "user_id": 1,
    "weight": 75.5,
    "recorded_at": "2026-08-21T13:38:11",
    "note": "晨起空腹",
    "created_at": "2026-08-21T13:38:11"
  }
}
```

#### 查询体重记录

```
GET /api/weight-records?page=1&per_page=20&start=2026-08-01&end=2026-08-21
```

查询参数均可选：`page` / `per_page`（默认 20，最大 100）分页；`start` / `end`（ISO 日期或日期时间）筛选测量时间范围。结果按 `recorded_at` 倒序。

**响应 `200`（`code: 200`）：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [ { "id": 2, "user_id": 1, "weight": 76.2, "recorded_at": "2026-08-20T08:00:00", "note": null, "created_at": "2026-08-21T13:38:11" } ],
    "total": 1,
    "page": 1,
    "per_page": 20
  }
}
```

#### 删除体重记录

```
DELETE /api/weight-records/<id>
```

**响应 `200`（`code: 200`）：** 删除成功；记录不存在或不属于当前用户返回 `code: 404`。

## 数据模型

### User（`users` 表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | Integer | 主键，自增 | 用户 ID |
| `username` | String(80) | 唯一、非空、索引 | 用户名 |
| `password` | String(255) | 非空 | 密码哈希（`werkzeug` `generate_password_hash`，默认 scrypt） |
| `created_at` | DateTime | 默认当前时间 | 创建时间 |

### WeightRecord（`weight_records` 表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | Integer | 主键，自增 | 记录 ID |
| `user_id` | Integer | 外键 → `users.id`，`ON DELETE CASCADE`，非空 | 所属用户 |
| `weight` | Numeric(5,2) | 非空 | 体重（kg），范围校验 20 ~ 300 |
| `recorded_at` | DateTime | 非空 | 测量时间（支持补录历史记录） |
| `note` | String(200) | 可空 | 备注，如"晨起空腹" |
| `created_at` | DateTime | 默认当前时间 | 入库时间 |

索引：`(user_id, recorded_at)` 复合索引，覆盖"按用户查时间线"的查询。

## CLI 命令

| 命令 | 说明 |
|------|------|
| `flask --app wsgi init-db` | 创建所有数据库表（幂等，已有表不会重建） |

## 生产部署

开发服务器（`python wsgi.py`）不适用于生产环境。`requirements.txt` 已包含 gunicorn（Linux），Windows 本地调试可用 waitress：

```bash
# Linux（gunicorn，已包含在 requirements.txt）
gunicorn -w 4 -b 127.0.0.1:8000 wsgi:app

# Windows 本地（waitress）
pip install waitress
waitress-serve --host 127.0.0.1 --port 8000 wsgi:app
```

### 服务器部署步骤（Linux）

`deploy/` 目录下已提供 systemd 和 Nginx 配置模板：

```bash
# 1. 拉取代码
git clone <仓库地址> /opt/bt-fit-backend && cd /opt/bt-fit-backend

# 2. 虚拟环境 + 依赖
python3 -m venv venv
./venv/bin/pip install -r requirements.txt

# 3. 配置环境（生成 .env，填入强随机 SECRET_KEY 与 CORS_ORIGINS）
cp .env.example .env
python -c "import secrets; print(secrets.token_hex(32))"

# 4. 初始化数据库
./venv/bin/flask --app wsgi init-db

# 5. 安装 systemd 服务（先按实际路径修改 deploy/bt-fit.service 中的 /opt/bt-fit-backend）
sudo cp deploy/bt-fit.service /etc/systemd/system/bt-fit.service
sudo systemctl daemon-reload
sudo systemctl enable --now bt-fit
journalctl -u bt-fit -f          # 查看日志

# 6. Nginx 反代 + HTTPS（将 deploy/nginx.conf 中域名替换为实际域名）
sudo cp deploy/nginx.conf /etc/nginx/sites-available/bt-fit
sudo ln -s /etc/nginx/sites-available/bt-fit /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d api.your-domain.com
```

gunicorn 只绑定 `127.0.0.1:8000`，由 Nginx 对外提供 80/443；防火墙只需开放 80/443。

### 部署前检查清单

- [x] 设置强随机的 `SECRET_KEY`（写入服务器 `.env`）
- [x] CORS 已默认收紧：生产环境需在 `.env` 显式配置 `CORS_ORIGINS`，否则不放行任何跨域来源
- [ ] 通过 `DATABASE_URL` 指向生产级数据库（如 PostgreSQL），多 worker 并发下比 SQLite 更稳
- [ ] SQLite 备份：cron 定时备份 `data/app.db`
- [ ] 验证：`curl http://<服务器IP>/health` 返回 `{"status":"ok"}`

## 服务器运维常用命令

以下命令在**服务器上**执行。路径按当前生产环境实际部署标注（项目 `/var/www/bt-fit/bt-fit-backend`，虚拟环境 `/var/www/bt-fit/bt-fit`，应用 systemd 服务名 `bt-fit`）；若部署在其他目录请相应替换。

### 应用服务（bt-fit / gunicorn）

```bash
sudo systemctl status bt-fit     # 运行状态（active 与否、worker 数、内存占用）
sudo systemctl restart bt-fit    # 重启应用
sudo systemctl stop bt-fit       # 停止应用

# 实时看日志（Ctrl+C 退出）
journalctl -u bt-fit -f
# 最近 200 行日志
journalctl -u bt-fit -n 200 --no-pager
# 只看今天的报错
journalctl -u bt-fit --since today -p err --no-pager
```

### 发布更新（最常用流程）

```bash
cd /var/www/bt-fit/bt-fit-backend
git pull                                                  # 1. 拉最新代码
/var/www/bt-fit/bt-fit/bin/pip install -r requirements.txt    # 2. 依赖有变动时
/var/www/bt-fit/bt-fit/bin/flask --app wsgi init-db           # 3. 模型有变动时（只补建缺失的表）
sudo chown -R www-data:www-data data                       # 4. init-db 用非 www-data 用户跑过后必须执行，
                                                           #    否则服务用户写不了库，所有写接口 500
sudo systemctl restart bt-fit                             # 5. 重启生效
curl http://127.0.0.1/health                              # 6. 验证 {"status":"ok"}
```

### Nginx

```bash
sudo nginx -t                                # 改完配置先做语法检查
sudo systemctl reload nginx                  # 平滑重载（不断开现有连接）
sudo systemctl restart nginx                 # 重启
sudo tail -n 50 /var/log/nginx/error.log     # 502/504 排查
sudo tail -n 50 /var/log/nginx/access.log    # 查看请求来源、路径、状态码
```

### 数据库备份与恢复（SQLite）

```bash
# 手动备份（.backup 为在线备份接口，比直接 cp 安全；-readonly 以只读打开源库，避免备份进程影响源库；需已安装 sqlite3）
sqlite3 -readonly /var/www/bt-fit/bt-fit-backend/data/app.db ".backup '/bt/backup/app-$(date +%F).db'"

# 恢复：停应用 → 覆盖库文件 → 起应用
sudo systemctl stop bt-fit
sudo cp /bt/backup/app-2026-08-27.db /var/www/bt-fit/bt-fit-backend/data/app.db
sudo chown www-data:www-data /var/www/bt-fit/bt-fit-backend/data/app.db
sudo systemctl start bt-fit

# 每天凌晨 3 点自动备份（crontab -e 添加，% 在 crontab 中需转义）
0 3 * * * sqlite3 -readonly /var/www/bt-fit/bt-fit-backend/data/app.db ".backup '/bt/backup/app-$(date +\%F).db'"
# 顺带清理 30 天前的旧备份，防止磁盘占满
10 3 * * * find /bt/backup -name "app-*.db" -mtime +30 -delete
```

设置步骤：① `sudo apt install -y sqlite3` 并 `sudo mkdir -p /bt/backup && sudo chown bt:bt /bt/backup`；② 手动执行一次上面的 `.backup` 命令确认成功；③ `crontab -e` 添加两行定时任务；④ `crontab -l` 确认已写入。注意备份与数据库同盘，重要数据应定期 `scp` 拉到本地异地保存（`scp bt@121.199.20.161:/bt/backup/app-2026-08-27.db D:/backup/`）。

### 资源与端口

```bash
df -h                # 磁盘剩余空间
free -h              # 内存
ss -tlnp             # 端口监听：应看到 :80(nginx) 和 127.0.0.1:8000(gunicorn)
ps aux | grep gunicorn    # worker 进程是否都在
```

### 故障速查

| 现象 | 排查顺序 |
|------|----------|
| 访问 502 | ① `systemctl status bt-fit` 是否 active → ② `journalctl -u bt-fit -n 50` 看崩溃原因 → ③ `/var/log/nginx/error.log` |
| 访问 404（Nginx 页面） | `ls /etc/nginx/sites-enabled/`——只应有 `bt-fit`；Ubuntu 的 `default` 站点回来了会抢占流量，且与 `default_server` 冲突导致 nginx 起不来 |
| 连接超时 / 打不开 | 云控制台**安全组**是否放行 80/443 端口 |
| 改了配置没生效 | `sudo nginx -t && sudo systemctl reload nginx`，确认 reload 成功执行过 |
| 服务器重启后服务没了 | `systemctl is-enabled bt-fit nginx` 应均为 `enabled` |

## 常见问题

**`sqlite3.OperationalError: unable to open database file`**
`data/` 目录缺失。当前版本会在导入配置时自动创建目录，若仍出现请手动创建 `data/` 目录。

**修改了模型后如何更新表结构？**
`init-db` 只创建缺失的表，不会迁移已有表。建议引入 [Flask-Migrate](https://flask-migrate.readthedocs.io/)（Alembic）管理 schema 变更：

```bash
pip install flask-migrate
flask --app wsgi db init
flask --app wsgi db migrate -m "your message"
flask --app wsgi db upgrade
```
