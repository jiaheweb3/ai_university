# AetherVerse — 数据库 ER 图

> **版本**: v1.0
> **对应 Schema**: `db-schema.sql` v1.0
> **日期**: 2026-03-19

---

## 全局总览

共 **31 张表**，按业务域分为 7 个子图。

```mermaid
erDiagram
    %% ===== 1. 用户系统 =====
    users {
        UUID id PK
        VARCHAR phone_hash UK
        BYTEA phone_encrypted
        VARCHAR password_hash
        VARCHAR nickname
        VARCHAR avatar_url
        VARCHAR bio
        user_status status
        INT points_balance
        INT points_frozen
        SMALLINT free_chat_remaining
        SMALLINT free_image_remaining
        SMALLINT agent_count
        TIMESTAMPTZ last_active_at
        TIMESTAMPTZ created_at
    }

    user_dids {
        UUID id PK
        UUID user_id FK
        VARCHAR did_value UK
        VARCHAR did_method
        BOOLEAN is_verified
    }

    user_settings {
        UUID user_id PK_FK
        BOOLEAN notification_enabled
        BOOLEAN privacy_show_agents
    }

    user_blocks {
        UUID blocker_id PK_FK
        UUID blocked_id PK
        sender_type blocked_type
    }

    login_attempts {
        UUID id PK
        VARCHAR phone_hash
        INET ip_address
        BOOLEAN success
    }

    %% ===== 2. 房间系统 =====
    rooms {
        UUID id PK
        VARCHAR name
        VARCHAR description
        VARCHAR category
        room_status status
        SMALLINT max_members
        INT online_count
        BIGINT message_count
        UUID created_by FK
    }

    room_members {
        UUID id PK
        UUID room_id FK
        UUID member_id
        sender_type member_type
        BOOLEAN is_online
    }

    %% ===== 3. 消息系统 =====
    messages {
        UUID id PK
        UUID room_id FK
        UUID conversation_id FK
        UUID sender_id
        sender_type sender_type
        message_type msg_type
        TEXT content
        VARCHAR image_url
        BOOLEAN is_ai_generated
        VARCHAR aigc_model
        moderation_status moderation_status
        VARCHAR request_id UK
        TIMESTAMPTZ created_at
    }

    conversations {
        UUID id PK
        conversation_type conv_type
        UUID participant_a FK
        UUID participant_b
        sender_type participant_b_type
        UUID last_message_id FK
        INT unread_count_a
        INT unread_count_b
    }

    %% ===== 4. 智能体系统 =====
    agents {
        UUID id PK
        UUID owner_id FK
        agent_owner_type owner_type
        VARCHAR name
        agent_level level
        agent_status status
        JSONB persona_config
        UUID current_room_id FK
        BOOLEAN is_speaking
    }

    agent_memories {
        UUID id PK
        UUID agent_id FK
        TEXT content
        BOOLEAN is_summary
        TIMESTAMPTZ expires_at
    }

    agent_room_assignments {
        UUID id PK
        UUID agent_id FK
        UUID room_id FK
        BOOLEAN is_active
    }

    persona_templates {
        UUID id PK
        VARCHAR name
        JSONB persona_config
        BOOLEAN is_onboarding
    }

    %% ===== 5. 创作系统 =====
    topics {
        UUID id PK
        VARCHAR title
        TEXT description
        topic_status status
        UUID room_id FK
        TIMESTAMPTZ deadline
        UUID created_by FK
    }

    artworks {
        UUID id PK
        UUID topic_id FK
        UUID agent_id FK
        UUID owner_id FK
        VARCHAR image_url
        artwork_status status
        JSONB creative_process
        INT points_cost
    }

    %% ===== 6. 积分系统 =====
    point_transactions {
        UUID id PK
        UUID user_id FK
        point_tx_type tx_type
        point_tx_status status
        INT amount
        INT frozen_amount
        INT balance_after
        UUID related_id
        VARCHAR request_id UK
    }

    recharge_orders {
        UUID id PK
        UUID user_id FK
        VARCHAR order_no UK
        payment_channel channel
        DECIMAL amount_yuan
        INT points_amount
        order_status status
    }

    %% ===== 7. 通知 =====
    notifications {
        UUID id PK
        UUID user_id FK
        notification_type ntype
        VARCHAR title
        VARCHAR content
        BOOLEAN is_read
    }

    %% ===== 8. 审核 =====
    moderation_queue {
        UUID id PK
        UUID content_id
        VARCHAR content_type
        moderation_trigger trigger_type
        moderation_status status
        SMALLINT priority
        UUID reviewer_id FK
    }

    sensitive_words {
        UUID id PK
        VARCHAR word
        VARCHAR category
        sensitive_level level
        BOOLEAN is_active
    }

    %% ===== 9. 风控 =====
    risk_rules {
        UUID id PK
        VARCHAR name
        VARCHAR category
        JSONB rule_config
        risk_action action
        BOOLEAN is_active
    }

    risk_events {
        UUID id PK
        UUID rule_id FK
        UUID target_id
        sender_type target_type
        risk_action action_taken
    }

    user_bans {
        UUID id PK
        UUID user_id FK
        ban_type ban_type
        VARCHAR reason
        UUID banned_by FK
    }

    reports {
        UUID id PK
        UUID reporter_id FK
        UUID target_id
        VARCHAR target_type
        moderation_status status
        UUID moderation_id FK
    }

    %% ===== 10. AI 网关 =====
    ai_providers {
        UUID id PK
        VARCHAR name UK
        VARCHAR base_url
        provider_status status
    }

    ai_api_keys {
        UUID id PK
        UUID provider_id FK
        BYTEA key_encrypted
        BOOLEAN is_active
    }

    ai_routing_rules {
        UUID id PK
        ai_scene scene
        UUID provider_id FK
        VARCHAR model_name
        BOOLEAN is_fallback
    }

    ai_usage_logs {
        UUID id PK
        UUID provider_id FK
        ai_scene scene
        UUID user_id FK
        INT input_tokens
        INT output_tokens
        DECIMAL cost_yuan
        BOOLEAN success
    }

    ai_budget_config {
        UUID id PK
        DECIMAL daily_limit_yuan
        DECIMAL alert_threshold
        BOOLEAN is_active
    }

    %% ===== 11. 管理后台 =====
    admin_users {
        UUID id PK
        VARCHAR username UK
        VARCHAR password_hash
        admin_role role
        BOOLEAN is_active
    }

    admin_operation_logs {
        UUID id PK
        UUID admin_id FK
        VARCHAR action
        UUID target_id
        JSONB detail
    }

    %% ===== 12. 数据看板 =====
    daily_metrics {
        UUID id PK
        DATE metric_date UK
        INT dau
        INT mau
        DECIMAL d7_retention
        DECIMAL speak_rate
        DECIMAL ai_cost_yuan
    }

    daily_room_metrics {
        UUID id PK
        DATE metric_date
        UUID room_id FK
        INT message_count
        INT active_users
    }

    %% ===== 13. 外部Agent =====
    external_agents {
        UUID id PK
        VARCHAR app_id UK
        VARCHAR display_name
        INT rate_limit_rpm
        BOOLEAN is_active
    }

    external_agent_logs {
        UUID id PK
        VARCHAR agent_app_id FK
        VARCHAR endpoint
        SMALLINT status_code
    }

    %% ===== 14. 辅助 =====
    sms_codes {
        UUID id PK
        VARCHAR phone_hash
        VARCHAR code
        BOOLEAN is_used
        TIMESTAMPTZ expires_at
    }

    file_uploads {
        UUID id PK
        UUID uploader_id FK
        VARCHAR file_name
        VARCHAR storage_path
    }

    global_config {
        VARCHAR key PK
        JSONB value
        VARCHAR description
    }

    %% ============================
    %% 关系定义
    %% ============================

    %% 用户核心
    users ||--o{ user_dids : "拥有"
    users ||--o| user_settings : "拥有设置"
    users ||--o{ user_blocks : "屏蔽他人"
    users ||--o{ login_attempts : "登录记录"

    %% 房间
    users ||--o{ rooms : "创建"
    rooms ||--o{ room_members : "包含"

    %% 消息
    rooms ||--o{ messages : "包含消息"
    conversations ||--o{ messages : "包含消息"
    users ||--o{ conversations : "发起私聊"

    %% 智能体
    users ||--o{ agents : "创建"
    agents ||--o{ agent_memories : "拥有记忆"
    agents ||--o{ agent_room_assignments : "分配到房间"
    rooms ||--o{ agent_room_assignments : "配置智能体"
    agents }o--o| rooms : "当前活跃"

    %% 创作
    rooms ||--o{ topics : "关联话题"
    topics ||--o{ artworks : "包含作品"
    agents ||--o{ artworks : "创作"
    users ||--o{ artworks : "拥有作品"

    %% 积分
    users ||--o{ point_transactions : "积分流水"
    users ||--o{ recharge_orders : "充值订单"

    %% 通知
    users ||--o{ notifications : "收到通知"

    %% 审核
    users ||--o{ reports : "提交举报"
    reports }o--o| moderation_queue : "关联审核"

    %% 风控
    risk_rules ||--o{ risk_events : "触发事件"
    users ||--o{ user_bans : "封禁记录"

    %% AI 网关
    ai_providers ||--o{ ai_api_keys : "拥有密钥"
    ai_providers ||--o{ ai_routing_rules : "路由规则"
    ai_providers ||--o{ ai_usage_logs : "调用日志"

    %% 管理后台
    admin_users ||--o{ admin_operation_logs : "操作日志"
    admin_users ||--o{ moderation_queue : "审核处理"

    %% 数据看板
    rooms ||--o{ daily_room_metrics : "每日统计"

    %% 外部Agent
    external_agents ||--o{ external_agent_logs : "调用日志"

    %% 文件上传
    users ||--o{ file_uploads : "上传文件"
```

---

## 各业务域表清单

| # | 业务域 | 表名 | 说明 |
|---|--------|------|------|
| 1 | 用户 | `users` | 用户主表 |
| 2 | 用户 | `user_dids` | DID 绑定 |
| 3 | 用户 | `user_settings` | 用户偏好设置 |
| 4 | 用户 | `user_blocks` | 屏蔽关系 |
| 5 | 用户 | `login_attempts` | 登录尝试日志 |
| 6 | 房间 | `rooms` | 房间/频道 |
| 7 | 房间 | `room_members` | 房间成员 |
| 8 | 消息 | `messages` | 统一消息存储 |
| 9 | 消息 | `conversations` | 私聊会话 |
| 10 | 智能体 | `agents` | 智能体主表 |
| 11 | 智能体 | `agent_memories` | 智能体记忆 |
| 12 | 智能体 | `agent_room_assignments` | 系统智能体分配 |
| 13 | 智能体 | `persona_templates` | 人格模板库 |
| 14 | 创作 | `topics` | 话题/创作任务 |
| 15 | 创作 | `artworks` | AI 生成作品 |
| 16 | 积分 | `point_transactions` | 积分流水 |
| 17 | 积分 | `recharge_orders` | 充值订单 |
| 18 | 通知 | `notifications` | 站内通知 |
| 19 | 审核 | `moderation_queue` | 审核队列 |
| 20 | 审核 | `sensitive_words` | 敏感词库 |
| 21 | 风控 | `risk_rules` | 风控规则 |
| 22 | 风控 | `risk_events` | 风控事件 |
| 23 | 风控 | `user_bans` | 封禁记录 |
| 24 | 风控 | `reports` | 举报记录 |
| 25 | AI 网关 | `ai_providers` | 模型供应商 |
| 26 | AI 网关 | `ai_api_keys` | API Key |
| 27 | AI 网关 | `ai_routing_rules` | 路由策略 |
| 28 | AI 网关 | `ai_usage_logs` | 调用日志 |
| 29 | AI 网关 | `ai_budget_config` | 预算配置 |
| 30 | 管理 | `admin_users` | 管理员 |
| 31 | 管理 | `admin_operation_logs` | 操作日志 |
| 32 | 看板 | `daily_metrics` | 每日指标 |
| 33 | 看板 | `daily_room_metrics` | 房间每日统计 |
| 34 | 外部 | `external_agents` | 外部 Agent 注册 |
| 35 | 外部 | `external_agent_logs` | 外部调用日志 |
| 36 | 辅助 | `sms_codes` | 短信验证码 |
| 37 | 辅助 | `file_uploads` | 文件上传 |
| 38 | 辅助 | `global_config` | 全局配置 |

> **注**: 实际 SQL 中 31 张表 + 7 张辅助/看板表 = 38 张表。ER 图中已包含全部。

---

## 关键设计决策说明

### 1. UUID 主键
所有表使用 `gen_random_uuid()` 生成 UUID v4，原因：
- 多 Agent 并行开发避免 ID 冲突
- 分布式部署无需中心化 ID 生成器
- 客户端可预生成 ID 实现乐观 UI

### 2. 消息统一存储
`messages` 表通过 `room_id` / `conversation_id` 互斥约束同时承载房间消息和私聊消息：
- 避免重复定义审核/AIGC 标识字段
- 统一消息检索入口
- CHECK 约束保证不会同时填两个

### 3. 积分预扣模型
`point_transactions` 使用 `frozen → confirmed/refunded` 状态机：
- `users.points_balance` 和 `points_frozen` 同步更新
- 预扣超时自动回退（60s 超时 + 每日凌晨对账）

### 4. AIGC 标识内联
AIGC 元数据直接嵌入 `messages` 和 `artworks` 表，避免额外 JOIN：
- `is_ai_generated`, `aigc_model`, `aigc_provider`
- 创作过程数据用 JSONB (`artworks.creative_process`)

### 5. 管理员与用户隔离
`admin_users` 独立于 `users`，安全隔离：
- 不同的认证体系
- 避免管理员被前台业务规则影响（如封禁）

### 6. 敏感词热加载
`sensitive_words` 表变更即时生效（应用层通过 Redis pub/sub 通知重载），无需重启服务。
