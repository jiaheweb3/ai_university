# Week 1-2: 后端基础设施 + 用户系统 + 房间系统

> **Agent**: Marcus (Agent A)
> **排期**: Week 1-2
> **交付目标**: SQLAlchemy 模型全量 + 用户系统 + 房间系统

---

## 1. 目标

建立 AetherVerse 后端的完整基础，包括：
- **基础设施层**: 数据库连接池、Redis 连接、配置管理、JWT 认证、异常处理中间件
- **ORM 模型全量**: 从 `db-schema.sql` 的 31 张表映射到 SQLAlchemy 2.0 async 模型
- **用户系统 API**: 注册/登录/Token刷新/密码重置/个人资料/注销/屏蔽
- **房间系统 API**: 列表/详情/加入/离开/成员列表

---

## 2. 架构设计

```
server/app/
├── core/                    # 基础设施
│   ├── config.py           # pydantic-settings 配置
│   ├── database.py         # SQLAlchemy async engine & session
│   ├── redis.py            # Redis 连接池
│   ├── security.py         # JWT 签发/验证、密码哈希、手机号加密
│   └── deps.py             # FastAPI 依赖注入 (get_db, get_current_user)
│
├── models/                  # SQLAlchemy ORM
│   ├── base.py             # Base 类 + 公共 mixin (TimestampMixin, UUIDMixin)
│   ├── user.py             # users, user_dids, user_settings, user_blocks, login_attempts
│   ├── room.py             # rooms, room_members
│   ├── message.py          # messages, conversations
│   ├── agent.py            # agents, agent_memories, agent_room_assignments, persona_templates
│   ├── creation.py         # topics, artworks
│   ├── point.py            # point_transactions, recharge_orders
│   ├── notification.py     # notifications
│   ├── moderation.py       # moderation_queue, sensitive_words
│   ├── risk.py             # risk_rules, risk_events, user_bans, reports
│   ├── ai_gateway.py       # ai_providers, ai_api_keys, ai_routing_rules, ai_usage_logs, ai_budget_config
│   ├── admin.py            # admin_users, admin_operation_logs
│   ├── metrics.py          # daily_metrics, daily_room_metrics
│   ├── external.py         # external_agents, external_agent_logs
│   └── auxiliary.py        # sms_codes, file_uploads, global_config
│
├── api/                     # REST 路由
│   ├── auth.py             # /auth/* (7 端点)
│   ├── users.py            # /users/* (7 端点)
│   └── rooms.py            # /rooms/* (5 端点)
│
├── services/                # 业务逻辑
│   ├── auth_service.py     # 注册/登录/Token/密码
│   ├── user_service.py     # 个人资料/设置/屏蔽/注销
│   └── room_service.py     # 房间 CRUD/加入/离开
│
└── main.py                  # 路由注册 + 中间件 + 生命周期
```

---

## 3. 具体变更

### 3.1 Core — 基础设施

#### [NEW] `server/app/core/config.py`
- `Settings(BaseSettings)` 从环境变量 / `.env` 加载配置
- 字段: `DATABASE_URL`, `REDIS_URL`, `RABBITMQ_URL`, `JWT_SECRET`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS`, `PHONE_AES_KEY`, `AI_ENGINE_URL`, `INTERNAL_API_KEY`
- `@lru_cache` 单例

#### [NEW] `server/app/core/database.py`
- `create_async_engine` + `async_sessionmaker`
- `get_db()` async generator for FastAPI `Depends`
- `init_db()` / `close_db()` for lifespan events

#### [NEW] `server/app/core/redis.py`
- `redis.asyncio.Redis` 连接池
- `get_redis()` for FastAPI `Depends`
- `init_redis()` / `close_redis()`

#### [NEW] `server/app/core/security.py`
- `create_access_token()` / `create_refresh_token()` — JWT 签发 (python-jose)
- `verify_password()` / `hash_password()` — bcrypt (passlib)
- `encrypt_phone()` / `decrypt_phone()` — AES 加密手机号
- `hash_phone()` — SHA-256 手机号哈希

#### [NEW] `server/app/core/deps.py`
- `get_current_user()` — 从 Authorization header 解析 JWT，查 DB 获取 user
- `get_current_active_user()` — 额外检查 `status == 'active'`
- `get_db()` — re-export from database.py

---

### 3.2 Models — SQLAlchemy ORM (全量)

#### [NEW] `server/app/models/base.py`
- `Base = declarative_base()` with mapped column defaults
- `UUIDMixin` — `id: UUID = Column(UUID, primary_key=True, server_default=text("gen_random_uuid()"))`
- `TimestampMixin` — `created_at`, `updated_at`
- `SoftDeleteMixin` — `deleted_at`

#### [NEW] `server/app/models/user.py`
5 张表: `users`, `user_dids`, `user_settings`, `user_blocks`, `login_attempts`
- 所有 CHECK 约束映射 (`ck_users_points_balance` 等)
- 关系: `User.dids`, `User.settings`, `User.blocks`

#### [NEW] 其余 11 个 model 文件
按上述架构逐一映射，所有字段、索引、约束与 `db-schema.sql` 保持 1:1。

---

### 3.3 API + Services — 用户系统

#### [NEW] `server/app/api/auth.py` — 7 端点
| 端点 | 方法 | 说明 |
|------|------|------|
| `/auth/sms/send` | POST | 发送短信验证码 (Phase 1 mock) |
| `/auth/register` | POST | 手机号注册 |
| `/auth/login/password` | POST | 密码登录 |
| `/auth/login/sms` | POST | 验证码登录 |
| `/auth/token/refresh` | POST | 刷新 Token |
| `/auth/password/reset` | POST | 重置密码 |
| `/auth/logout` | POST | 退出登录 |

#### [NEW] `server/app/api/users.py` — 7 端点
| 端点 | 方法 | 说明 |
|------|------|------|
| `/users/me` | GET | 获取当前用户 |
| `/users/me` | PATCH | 更新个人资料 |
| `/users/me` | DELETE | 注销账号 |
| `/users/me/password` | PUT | 修改密码 |
| `/users/me/settings` | GET/PATCH | 获取/更新设置 |
| `/users/{user_id}` | GET | 查看他人主页 |
| `/users/{user_id}/block` | POST/DELETE | 屏蔽/取消 |

#### [NEW] `server/app/services/auth_service.py`
- `send_sms_code()` — 写入 `sms_codes` + Redis 限频 (1 分钟内不重发)
- `register()` — 验证码校验 → 创建用户 → 生成 DID → 签发 JWT
- `login_password()` / `login_sms()` — 校验凭据 → 记录 `login_attempts` → 签发 JWT
- `refresh_token()` — 验证 refresh_token → 签发新 pair
- `reset_password()` — 验证码校验 → 更新密码
- `logout()` — JWT 加入 Redis 黑名单 (剩余有效期内)

#### [NEW] `server/app/services/user_service.py`
- `get_profile()` / `update_profile()` / `delete_account()`
- `get_settings()` / `update_settings()`
- `block_user()` / `unblock_user()`

---

### 3.4 API + Services — 房间系统

#### [NEW] `server/app/api/rooms.py` — 5 端点
| 端点 | 方法 | 说明 |
|------|------|------|
| `/rooms` | GET | 房间列表 (分页/搜索/排序) |
| `/rooms/{room_id}` | GET | 房间详情 |
| `/rooms/{room_id}/join` | POST | 加入房间 |
| `/rooms/{room_id}/leave` | POST | 离开房间 |
| `/rooms/{room_id}/members` | GET | 成员列表 |

#### [NEW] `server/app/services/room_service.py`
- `list_rooms()` — cursor 分页 + 分类筛选 + 模糊搜索 + 排序 (hot/new/joined)
- `get_room_detail()` — 含成员列表 + 当前话题
- `join_room()` — 检查上限 → 插入 room_members → Redis 在线计数 +1
- `leave_room()` — 标记 left_at → Redis 在线计数 -1
- `get_members()` — 合并 user/agent 信息

---

### 3.5 main.py 改造

- 添加 `lifespan` context manager: `init_db`, `init_redis`, `close_db`, `close_redis`
- 注册全局异常处理器 → `AppException` → `{ code, message, detail }`
- 注册路由: `auth.router`, `users.router`, `rooms.router`
- 添加 `structlog` 中间件注入 `request_id`

---

## 4. 关键设计决策

1. **cursor 分页**: 基于 `created_at + id` 双字段排序，避免 offset 性能问题
2. **JWT 黑名单**: 用 Redis SET 存 token jti，TTL = token 剩余有效期
3. **手机号存储**: SHA-256 哈希查重 + XOR 简化加密 (Phase 1)，生产环境切换 AES-256-GCM
4. **SMS 验证码**: Phase 1 开发阶段用固定码 `123456`，预留短信服务接口
5. **枚举一致性**: 所有 model 的 Enum 列直接引用 `shared.constants` 的 StrEnum

---

## 5. 验证方案

### 5.1 自动化测试

Week 1-2 先写 API 级集成测试，后续补 unit test。

```bash
# 安装依赖
cd server && pip install -e "../shared" && pip install -e ".[dev]"

# 运行测试
pytest tests/ -v --tb=short
```

测试组织:
```
server/tests/
├── conftest.py          # testcontainers PG + test client + 认证 fixture
├── test_auth.py         # 注册/登录/Token 刷新/密码重置/注销
├── test_users.py        # 个人资料/设置/屏蔽
└── test_rooms.py        # 列表/详情/加入/离开/成员
```

每个端点至少 1 happy path + 1 error case (如 schema 要求)。

### 5.2 手动验证

启动后访问 `http://localhost:8000/docs` 在 Swagger UI 手动测试:
1. 注册 → 拿到 Token → 用 Token 调用 `/users/me`
2. 创建房间 (管理后台) → 加入 → 查看成员 → 离开

---

## 6. 执行顺序

1. ✅ `core/config.py` + `core/database.py` + `core/redis.py`
2. ✅ `core/security.py` + `core/deps.py`
3. ✅ `models/base.py` + 全量 model 文件 (15 个)
4. ✅ `main.py` 改造 (lifespan + 异常处理)
5. ✅ `services/auth_service.py` + `api/auth.py`
6. ✅ `services/user_service.py` + `api/users.py`
7. ✅ `services/room_service.py` + `api/rooms.py`
8. ✅ `tests/conftest.py` + 测试文件
9. ✅ Alembic 初始化迁移
