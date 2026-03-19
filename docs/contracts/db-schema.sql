-- =============================================================================
-- AetherVerse — Phase 1 MVP 数据库 Schema
-- 数据库: PostgreSQL 16+
-- 编码: UTF-8
-- 版本: v1.0
-- 维护者: 恺撒（PM / 架构师）
-- 日期: 2026-03-19
--
-- 使用约定:
--   - 主键统一使用 UUID (gen_random_uuid())
--   - 时间戳统一 TIMESTAMPTZ, 默认 NOW()
--   - 软删除使用 deleted_at 字段
--   - 所有金额/积分使用 INTEGER (最小单位)
--   - 枚举使用 PostgreSQL ENUM 类型
--   - 索引命名: idx_{table}_{column(s)}
--   - 外键命名: fk_{table}_{ref_table}
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 0. 扩展 & 枚举
-- ---------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS "pgcrypto";     -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS "pg_trgm";      -- 三字母组索引，用于模糊搜索

-- 用户状态
CREATE TYPE user_status AS ENUM ('active', 'banned_temp', 'banned_perm', 'deleted');

-- 消息类型
CREATE TYPE message_type AS ENUM ('text', 'image', 'system', 'ai_generated');

-- 消息发送者类型
CREATE TYPE sender_type AS ENUM ('user', 'agent', 'system');

-- 审核状态
CREATE TYPE moderation_status AS ENUM ('pending', 'approved', 'rejected', 'appealed', 'appeal_approved', 'appeal_rejected');

-- 审核触发类型
CREATE TYPE moderation_trigger AS ENUM ('auto_block', 'auto_suspect', 'manual_report', 'appeal');

-- 智能体等级
CREATE TYPE agent_level AS ENUM ('L1', 'L2');

-- 智能体状态
CREATE TYPE agent_status AS ENUM ('active', 'paused', 'suspended', 'deleted');

-- 智能体拥有者类型
CREATE TYPE agent_owner_type AS ENUM ('user', 'system');

-- 房间状态
CREATE TYPE room_status AS ENUM ('active', 'archived');

-- 话题状态
CREATE TYPE topic_status AS ENUM ('draft', 'active', 'ended', 'archived');

-- 作品状态
CREATE TYPE artwork_status AS ENUM ('generating', 'pending_review', 'approved', 'rejected', 'failed');

-- 积分交易类型
CREATE TYPE point_tx_type AS ENUM (
    'recharge',           -- 充值
    'create_agent',       -- 创建智能体
    'agent_speak',        -- 智能体发言
    'image_generate',     -- 图片生成
    'free_daily',         -- 每日免费额度
    'refund',             -- 退款/回退
    'admin_adjust'        -- 管理员调整
);

-- 积分交易状态
CREATE TYPE point_tx_status AS ENUM ('frozen', 'confirmed', 'refunded', 'expired');

-- 充值订单状态
CREATE TYPE order_status AS ENUM ('pending', 'paid', 'failed', 'refunded', 'reconciling');

-- 支付渠道
CREATE TYPE payment_channel AS ENUM ('wechat', 'alipay');

-- 通知类型
CREATE TYPE notification_type AS ENUM (
    'moderation_result',  -- 审核结果
    'agent_status',       -- 智能体状态变化
    'account_security',   -- 账号安全
    'task_status',        -- 创作任务状态
    'transaction'         -- 交易记录
);

-- 封禁类型
CREATE TYPE ban_type AS ENUM ('temp', 'perm');

-- 敏感词等级
CREATE TYPE sensitive_level AS ENUM ('block', 'suspect', 'observe');

-- 风控处置动作
CREATE TYPE risk_action AS ENUM ('warn', 'rate_limit', 'pause', 'ban');

-- AI 供应商状态
CREATE TYPE provider_status AS ENUM ('active', 'disabled', 'degraded');

-- AI 调用场景
CREATE TYPE ai_scene AS ENUM ('chat', 'image_gen', 'moderation', 'listen_eval', 'memory_summary');

-- 管理员角色
CREATE TYPE admin_role AS ENUM ('super_admin', 'ops_admin', 'reviewer');

-- 会话类型 (私聊)
CREATE TYPE conversation_type AS ENUM ('user_to_user', 'user_to_agent');

-- ---------------------------------------------------------------------------
-- 1. 用户系统
-- ---------------------------------------------------------------------------

-- 1.1 用户表
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_hash      VARCHAR(64)   NOT NULL,            -- 手机号 SHA-256 哈希 (查重)
    phone_encrypted BYTEA         NOT NULL,            -- 手机号 AES 加密存储
    password_hash   VARCHAR(128)  NOT NULL,            -- bcrypt 哈希
    nickname        VARCHAR(32)   NOT NULL,
    avatar_url      VARCHAR(512),
    bio             VARCHAR(400),                      -- 个人简介 <=200字(UTF-8 最多 400 bytes)
    status          user_status   NOT NULL DEFAULT 'active',
    points_balance  INTEGER       NOT NULL DEFAULT 0,  -- 可用积分余额
    points_frozen   INTEGER       NOT NULL DEFAULT 0,  -- 冻结中积分
    free_chat_remaining   SMALLINT NOT NULL DEFAULT 20,  -- 当日免费对话剩余
    free_image_remaining  SMALLINT NOT NULL DEFAULT 2,   -- 当日免费图片剩余
    free_quota_date       DATE,                          -- 免费额度所属日期
    agent_count     SMALLINT      NOT NULL DEFAULT 0,  -- 已创建智能体数 (上限 3)
    last_active_at  TIMESTAMPTZ,
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ,

    CONSTRAINT ck_users_points_balance CHECK (points_balance >= 0),
    CONSTRAINT ck_users_points_frozen  CHECK (points_frozen >= 0),
    CONSTRAINT ck_users_agent_count    CHECK (agent_count >= 0 AND agent_count <= 3)
);

CREATE UNIQUE INDEX idx_users_phone_hash ON users (phone_hash) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_status ON users (status);
CREATE INDEX idx_users_nickname_trgm ON users USING gin (nickname gin_trgm_ops);
CREATE INDEX idx_users_created_at ON users (created_at);

-- 1.2 DID 绑定表
CREATE TABLE user_dids (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID         NOT NULL REFERENCES users(id),
    did_value   VARCHAR(256) NOT NULL UNIQUE,   -- DID 标识符
    did_method  VARCHAR(32)  NOT NULL DEFAULT 'aetherverse',
    is_verified BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_user_dids_user FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_user_dids_user ON user_dids (user_id);

-- 1.3 用户设置
CREATE TABLE user_settings (
    user_id                UUID PRIMARY KEY REFERENCES users(id),
    notification_enabled   BOOLEAN NOT NULL DEFAULT TRUE,    -- 非安全类通知开关
    privacy_show_agents    BOOLEAN NOT NULL DEFAULT TRUE,    -- 是否公开智能体列表
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 1.4 用户屏蔽关系
CREATE TABLE user_blocks (
    blocker_id  UUID NOT NULL REFERENCES users(id),
    blocked_id  UUID NOT NULL,         -- 可以是 users.id 或 agents.id
    blocked_type sender_type NOT NULL,  -- 'user' 或 'agent'
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (blocker_id, blocked_id)
);

-- 1.5 用户登录/安全日志
CREATE TABLE login_attempts (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_hash  VARCHAR(64) NOT NULL,
    ip_address  INET        NOT NULL,
    device_info VARCHAR(512),
    success     BOOLEAN     NOT NULL,
    failure_reason VARCHAR(64),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_login_attempts_phone ON login_attempts (phone_hash, created_at);
CREATE INDEX idx_login_attempts_ip ON login_attempts (ip_address, created_at);

-- ---------------------------------------------------------------------------
-- 2. 房间系统
-- ---------------------------------------------------------------------------

-- 2.1 房间表
CREATE TABLE rooms (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(64)  NOT NULL,
    description     VARCHAR(500),
    category        VARCHAR(32)  NOT NULL DEFAULT 'general', -- 主题房/兴趣房
    tags            VARCHAR(256)[],                          -- 标签数组
    cover_url       VARCHAR(512),
    status          room_status  NOT NULL DEFAULT 'active',
    max_members     SMALLINT     NOT NULL DEFAULT 200,
    online_count    INTEGER      NOT NULL DEFAULT 0,          -- 缓存字段, 真实值在 Redis
    message_count   BIGINT       NOT NULL DEFAULT 0,          -- 累计消息数
    created_by      UUID         REFERENCES users(id),        -- 管理员创建 (NULL = 系统)
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    archived_at     TIMESTAMPTZ
);

CREATE INDEX idx_rooms_status ON rooms (status);
CREATE INDEX idx_rooms_category ON rooms (category);

-- 2.2 房间成员 (含智能体)
CREATE TABLE room_members (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_id     UUID        NOT NULL REFERENCES rooms(id),
    member_id   UUID        NOT NULL,  -- users.id 或 agents.id
    member_type sender_type NOT NULL,  -- 'user' 或 'agent'
    is_online   BOOLEAN     NOT NULL DEFAULT FALSE,
    joined_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    left_at     TIMESTAMPTZ,

    CONSTRAINT uq_room_members UNIQUE (room_id, member_id, member_type)
);

CREATE INDEX idx_room_members_room ON room_members (room_id) WHERE left_at IS NULL;
CREATE INDEX idx_room_members_member ON room_members (member_id, member_type);

-- ---------------------------------------------------------------------------
-- 3. 消息 & 聊天系统
-- ---------------------------------------------------------------------------

-- 3.1 消息表 (房间消息 + 私聊消息统一存储)
CREATE TABLE messages (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_id         UUID,                                     -- 房间消息时不为 NULL
    conversation_id UUID,                                     -- 私聊消息时不为 NULL
    sender_id       UUID         NOT NULL,                    -- users.id 或 agents.id
    sender_type     sender_type  NOT NULL,
    msg_type        message_type NOT NULL DEFAULT 'text',
    content         TEXT,                                     -- 文本内容
    image_url       VARCHAR(512),                             -- 图片 URL
    reply_to_id     UUID,                                     -- 回复的消息 ID
    mentions        UUID[],                                   -- @提及的 ID 列表

    -- AIGC 标识 (内联, 避免额外 JOIN)
    is_ai_generated BOOLEAN      NOT NULL DEFAULT FALSE,
    aigc_model      VARCHAR(64),                              -- 生成用的模型版本
    aigc_provider   VARCHAR(64),                              -- 服务提供者

    -- 审核
    moderation_status moderation_status DEFAULT 'approved',   -- 默认通过(未触发审核)
    moderation_code   VARCHAR(32),                            -- 审核结果码

    -- 元数据
    client_info     JSONB,                                    -- 客户端信息
    request_id      VARCHAR(64),                              -- 幂等键
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ,

    CONSTRAINT ck_messages_target CHECK (
        (room_id IS NOT NULL AND conversation_id IS NULL) OR
        (room_id IS NULL AND conversation_id IS NOT NULL)
    )
);

-- 房间消息按时间分区性能索引
CREATE INDEX idx_messages_room_time ON messages (room_id, created_at) WHERE room_id IS NOT NULL;
-- 私聊消息索引
CREATE INDEX idx_messages_conv_time ON messages (conversation_id, created_at) WHERE conversation_id IS NOT NULL;
-- 发送者索引
CREATE INDEX idx_messages_sender ON messages (sender_id, sender_type, created_at);
-- 幂等键唯一索引
CREATE UNIQUE INDEX idx_messages_request_id ON messages (request_id) WHERE request_id IS NOT NULL;
-- 审核状态索引
CREATE INDEX idx_messages_moderation ON messages (moderation_status) WHERE moderation_status != 'approved';
-- 全文搜索 (管理后台消息检索)
CREATE INDEX idx_messages_content_search ON messages USING gin (to_tsvector('simple', content)) WHERE content IS NOT NULL;

-- 3.2 私聊会话表
CREATE TABLE conversations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conv_type       conversation_type NOT NULL,
    participant_a   UUID NOT NULL,              -- 发起方 (总是 user)
    participant_b   UUID NOT NULL,              -- 对方 (user 或 agent)
    participant_b_type sender_type NOT NULL,    -- 'user' 或 'agent'
    last_message_id UUID,
    last_message_at TIMESTAMPTZ,

    -- 未读计数 (双方各自)
    unread_count_a  INTEGER NOT NULL DEFAULT 0,
    unread_count_b  INTEGER NOT NULL DEFAULT 0,

    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_conversations UNIQUE (participant_a, participant_b, participant_b_type)
);

CREATE INDEX idx_conversations_a ON conversations (participant_a, last_message_at DESC);
CREATE INDEX idx_conversations_b ON conversations (participant_b, participant_b_type, last_message_at DESC);

-- ---------------------------------------------------------------------------
-- 4. 智能体系统
-- ---------------------------------------------------------------------------

-- 4.1 智能体表
CREATE TABLE agents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id        UUID,                                     -- users.id, NULL 表示系统智能体
    owner_type      agent_owner_type NOT NULL DEFAULT 'user',
    name            VARCHAR(24)  NOT NULL,                    -- 2-12 字符
    avatar_url      VARCHAR(512),
    bio             VARCHAR(500),
    level           agent_level  NOT NULL DEFAULT 'L1',
    status          agent_status NOT NULL DEFAULT 'active',
    persona_config  JSONB        NOT NULL,                    -- 人格设定 (角色/口吻/特长/禁止事项)
    system_prompt   TEXT,                                     -- 完整系统提示词 (由 AI 引擎生成)
    knowledge_base  JSONB,                                    -- 知识背景 (系统智能体)

    -- 运行时状态
    current_room_id UUID REFERENCES rooms(id),                -- 当前活跃房间 (只能在一个房间)
    is_speaking     BOOLEAN NOT NULL DEFAULT FALSE,           -- 是否正在发言模式
    last_speak_at   TIMESTAMPTZ,
    speak_count_today INTEGER NOT NULL DEFAULT 0,             -- 今日发言计数
    task_count_today  SMALLINT NOT NULL DEFAULT 0,            -- 今日创作任务计数 (上限3)

    -- 暖场配置 (系统智能体)
    fallback_timeout_sec SMALLINT DEFAULT 30,                 -- 兜底响应超时秒数
    daily_topic_schedule JSONB,                               -- 每日话题计划

    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ,

    CONSTRAINT ck_agents_task_count CHECK (task_count_today >= 0 AND task_count_today <= 3)
);

CREATE INDEX idx_agents_owner ON agents (owner_id, owner_type) WHERE deleted_at IS NULL;
CREATE INDEX idx_agents_status ON agents (status);
CREATE INDEX idx_agents_room ON agents (current_room_id) WHERE current_room_id IS NOT NULL;

-- 4.2 智能体记忆
CREATE TABLE agent_memories (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id    UUID        NOT NULL REFERENCES agents(id),
    content     TEXT        NOT NULL,              -- 记忆内容
    is_summary  BOOLEAN     NOT NULL DEFAULT FALSE,-- 是否为系统摘要
    token_count INTEGER,                           -- 占用 token 数
    expires_at  TIMESTAMPTZ,                       -- TTL (30天)
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at  TIMESTAMPTZ                        -- 用户手动删除
);

CREATE INDEX idx_agent_memories_agent ON agent_memories (agent_id, created_at) WHERE deleted_at IS NULL;

-- 4.3 智能体 - 房间分配 (系统智能体暖场)
CREATE TABLE agent_room_assignments (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id    UUID NOT NULL REFERENCES agents(id),
    room_id     UUID NOT NULL REFERENCES rooms(id),
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    removed_at  TIMESTAMPTZ,

    CONSTRAINT uq_agent_room UNIQUE (agent_id, room_id)
);

CREATE INDEX idx_agent_room_active ON agent_room_assignments (room_id) WHERE is_active = TRUE;

-- 4.4 人格模板库 (新用户引导 + 管理后台)
CREATE TABLE persona_templates (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(24)  NOT NULL,
    description VARCHAR(200),
    avatar_url  VARCHAR(512),
    persona_config JSONB     NOT NULL,       -- 预设人格配置
    is_onboarding BOOLEAN   NOT NULL DEFAULT FALSE,  -- 是否用于新用户引导
    sort_order  SMALLINT    NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ---------------------------------------------------------------------------
-- 5. 创作系统 (话题 & 作品)
-- ---------------------------------------------------------------------------

-- 5.1 话题/创作任务
CREATE TABLE topics (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title           VARCHAR(128)  NOT NULL,
    description     TEXT,
    keywords        VARCHAR(64)[],           -- 关键词数组
    reference_url   VARCHAR(512),            -- 参考图 URL
    status          topic_status  NOT NULL DEFAULT 'draft',
    room_id         UUID          REFERENCES rooms(id),  -- 关联房间 (可选)
    deadline        TIMESTAMPTZ,
    participant_count INTEGER NOT NULL DEFAULT 0,
    artwork_count     INTEGER NOT NULL DEFAULT 0,
    created_by      UUID          REFERENCES users(id),  -- 管理员
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    ended_at        TIMESTAMPTZ
);

CREATE INDEX idx_topics_status ON topics (status, deadline);

-- 5.2 作品
CREATE TABLE artworks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topic_id        UUID         NOT NULL REFERENCES topics(id),
    agent_id        UUID         NOT NULL REFERENCES agents(id),
    owner_id        UUID         NOT NULL REFERENCES users(id),  -- 智能体的主人
    image_url       VARCHAR(512),
    thumbnail_url   VARCHAR(512),
    status          artwork_status NOT NULL DEFAULT 'generating',

    -- AIGC 标识
    aigc_model      VARCHAR(64),
    aigc_provider   VARCHAR(64),
    aigc_watermark  BOOLEAN     NOT NULL DEFAULT FALSE,   -- 是否已写入数字水印

    -- 创作过程元数据 (需求 §3.3 要求必须落库)
    creative_process JSONB NOT NULL DEFAULT '{}',
    -- 结构: { prompt, negative_prompt, model_version, parameters, steps[], timestamps }

    points_cost     INTEGER     NOT NULL DEFAULT 0,   -- 消耗积分
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reviewed_at     TIMESTAMPTZ,
    reviewed_by     UUID        REFERENCES users(id)  -- 审核员 (admin)
);

CREATE INDEX idx_artworks_topic ON artworks (topic_id, status);
CREATE INDEX idx_artworks_agent ON artworks (agent_id);
CREATE INDEX idx_artworks_owner ON artworks (owner_id);
CREATE INDEX idx_artworks_review ON artworks (status) WHERE status = 'pending_review';

-- ---------------------------------------------------------------------------
-- 6. 积分与计费系统
-- ---------------------------------------------------------------------------

-- 6.1 积分交易流水 (核心账本)
CREATE TABLE point_transactions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID          NOT NULL REFERENCES users(id),
    tx_type         point_tx_type NOT NULL,
    status          point_tx_status NOT NULL DEFAULT 'frozen',
    amount          INTEGER       NOT NULL,            -- 正数=收入, 负数=支出
    frozen_amount   INTEGER       NOT NULL DEFAULT 0,  -- 冻结金额 (预扣阶段)
    balance_after   INTEGER,                           -- 交易后余额快照
    related_id      UUID,                              -- 关联实体 ID (message/artwork/order 等)
    related_type    VARCHAR(32),                        -- 关联实体类型
    request_id      VARCHAR(64),                       -- 幂等键
    description     VARCHAR(200),                      -- 人可读描述
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    confirmed_at    TIMESTAMPTZ,
    expired_at      TIMESTAMPTZ                        -- 预扣超时自动回退时间
);

CREATE INDEX idx_point_tx_user ON point_transactions (user_id, created_at DESC);
CREATE INDEX idx_point_tx_status ON point_transactions (status) WHERE status = 'frozen';
CREATE UNIQUE INDEX idx_point_tx_request ON point_transactions (request_id) WHERE request_id IS NOT NULL;

-- 6.2 充值订单
CREATE TABLE recharge_orders (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID           NOT NULL REFERENCES users(id),
    order_no        VARCHAR(64)    NOT NULL UNIQUE,     -- 业务订单号
    channel         payment_channel NOT NULL,
    channel_order_no VARCHAR(128),                      -- 第三方支付单号
    amount_yuan     DECIMAL(10,2)  NOT NULL,            -- 充值金额 (元)
    points_amount   INTEGER        NOT NULL,            -- 到账积分
    status          order_status   NOT NULL DEFAULT 'pending',
    paid_at         TIMESTAMPTZ,
    created_at      TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ    NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_recharge_orders_user ON recharge_orders (user_id, created_at DESC);
CREATE INDEX idx_recharge_orders_status ON recharge_orders (status) WHERE status = 'pending';

-- ---------------------------------------------------------------------------
-- 7. 通知系统
-- ---------------------------------------------------------------------------

CREATE TABLE notifications (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID              NOT NULL REFERENCES users(id),
    ntype           notification_type NOT NULL,
    title           VARCHAR(128)      NOT NULL,
    content         VARCHAR(500)      NOT NULL,
    related_id      UUID,                              -- 关联实体 ID
    related_type    VARCHAR(32),                        -- 'message', 'agent', 'order' 等
    is_read         BOOLEAN           NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ       NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_notifications_user ON notifications (user_id, is_read, created_at DESC);

-- 通知限频计数 (Redis 更适合, 此表用于持久化审计)
-- 实际限频逻辑在 Redis 中用 sliding window 实现

-- ---------------------------------------------------------------------------
-- 8. 审核系统
-- ---------------------------------------------------------------------------

-- 8.1 审核队列
CREATE TABLE moderation_queue (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_id      UUID              NOT NULL,         -- messages.id 或 artworks.id 或 agents.id
    content_type    VARCHAR(32)       NOT NULL,         -- 'message', 'artwork', 'agent_persona'
    content_snapshot TEXT,                               -- 内容快照 (防篡改)
    trigger_type    moderation_trigger NOT NULL,
    trigger_detail  JSONB,                              -- 触发规则详情 (命中了哪条规则)
    status          moderation_status NOT NULL DEFAULT 'pending',
    priority        SMALLINT         NOT NULL DEFAULT 5, -- 1=最高, 10=最低

    -- 上下文 (前后5条消息)
    context_messages JSONB,

    -- 审核结果
    reviewer_id     UUID             REFERENCES users(id),  -- admin user
    review_result   VARCHAR(32),     -- 'pass', 'reject', 'false_positive', 'escalate'
    review_note     VARCHAR(500),
    reviewed_at     TIMESTAMPTZ,

    -- 申诉
    appeal_reason   VARCHAR(500),
    appeal_at       TIMESTAMPTZ,

    created_at      TIMESTAMPTZ      NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_moderation_status ON moderation_queue (status, priority, created_at);
CREATE INDEX idx_moderation_content ON moderation_queue (content_id, content_type);
CREATE INDEX idx_moderation_reviewer ON moderation_queue (reviewer_id) WHERE reviewer_id IS NOT NULL;

-- 8.2 敏感词库
CREATE TABLE sensitive_words (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    word        VARCHAR(128) NOT NULL,
    category    VARCHAR(32)  NOT NULL,          -- '涉政', '暴恐', '色情', '网暴', '违法交易', '引导转账'
    level       sensitive_level NOT NULL,
    variants    VARCHAR(256)[],                 -- 变体列表 (谐音/拆字/拼音等)
    is_active   BOOLEAN      NOT NULL DEFAULT TRUE,
    created_by  UUID         REFERENCES users(id),
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_sensitive_words_active ON sensitive_words (is_active, category);
CREATE INDEX idx_sensitive_words_word ON sensitive_words USING gin (word gin_trgm_ops);

-- ---------------------------------------------------------------------------
-- 9. 风控系统
-- ---------------------------------------------------------------------------

-- 9.1 风控规则配置
CREATE TABLE risk_rules (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(64)  NOT NULL,
    description     VARCHAR(500),
    category        VARCHAR(32)  NOT NULL,     -- 'rate_limit', 'spam', 'social_engineering', 'impersonation', 'harassment'
    rule_config     JSONB        NOT NULL,     -- 规则参数 (阈值/时间窗口/匹配模式等)
    action          risk_action  NOT NULL,
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_by      UUID         REFERENCES users(id),
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- 9.2 风控事件记录
CREATE TABLE risk_events (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_id         UUID        REFERENCES risk_rules(id),
    target_id       UUID        NOT NULL,                -- 触发者 ID (user/agent)
    target_type     sender_type NOT NULL,
    action_taken    risk_action NOT NULL,
    detail          JSONB,                               -- 事件详情
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_risk_events_target ON risk_events (target_id, target_type, created_at);

-- 9.3 用户封禁记录
CREATE TABLE user_bans (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID     NOT NULL REFERENCES users(id),
    ban_type    ban_type NOT NULL,
    reason      VARCHAR(500) NOT NULL,
    banned_by   UUID     NOT NULL REFERENCES users(id),   -- 管理员
    expires_at  TIMESTAMPTZ,                               -- 临时封禁到期时间
    unbanned_by UUID     REFERENCES users(id),
    unbanned_at TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_user_bans_user ON user_bans (user_id, created_at DESC);

-- 9.4 举报记录
CREATE TABLE reports (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reporter_id     UUID        NOT NULL REFERENCES users(id),
    target_id       UUID        NOT NULL,     -- 被举报实体 ID
    target_type     VARCHAR(32) NOT NULL,     -- 'user', 'agent', 'message'
    reason          VARCHAR(500) NOT NULL,
    status          moderation_status NOT NULL DEFAULT 'pending',
    moderation_id   UUID        REFERENCES moderation_queue(id),  -- 关联审核队列
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_reports_target ON reports (target_id, target_type);
CREATE INDEX idx_reports_status ON reports (status) WHERE status = 'pending';

-- ---------------------------------------------------------------------------
-- 10. AI 网关管理
-- ---------------------------------------------------------------------------

-- 10.1 AI 模型供应商
CREATE TABLE ai_providers (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(64)     NOT NULL UNIQUE,    -- 'deepseek', 'qianwen', 'doubao'
    display_name    VARCHAR(64)     NOT NULL,
    base_url        VARCHAR(512)    NOT NULL,
    status          provider_status NOT NULL DEFAULT 'active',
    health_check_url VARCHAR(512),
    latency_ms      INTEGER,                             -- 最近一次延迟
    success_rate    DECIMAL(5,2),                         -- 成功率 %
    last_health_check TIMESTAMPTZ,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

-- 10.2 API Key 管理
CREATE TABLE ai_api_keys (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_id     UUID        NOT NULL REFERENCES ai_providers(id),
    key_encrypted   BYTEA       NOT NULL,                -- AES 加密存储
    key_hint        VARCHAR(16) NOT NULL,                -- 脱敏显示 (sk-****abcd)
    is_active       BOOLEAN     NOT NULL DEFAULT TRUE,
    daily_limit     INTEGER,                             -- 每日调用上限
    daily_used      INTEGER     NOT NULL DEFAULT 0,
    reset_date      DATE,                                -- 计数重置日期
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ai_keys_provider ON ai_api_keys (provider_id, is_active);

-- 10.3 路由策略配置
CREATE TABLE ai_routing_rules (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scene           ai_scene    NOT NULL,                -- 使用场景
    priority        SMALLINT    NOT NULL DEFAULT 1,      -- 优先级 (1=最高)
    provider_id     UUID        NOT NULL REFERENCES ai_providers(id),
    model_name      VARCHAR(64) NOT NULL,                -- 具体模型名
    is_fallback     BOOLEAN     NOT NULL DEFAULT FALSE,  -- 是否为降级备选
    timeout_ms      INTEGER     NOT NULL DEFAULT 10000,  -- 超时阈值
    max_retries     SMALLINT    NOT NULL DEFAULT 1,
    is_active       BOOLEAN     NOT NULL DEFAULT TRUE,
    created_by      UUID        REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_routing_scene ON ai_routing_rules (scene, priority) WHERE is_active = TRUE;

-- 10.4 AI 调用日志
CREATE TABLE ai_usage_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_id     UUID        NOT NULL REFERENCES ai_providers(id),
    model_name      VARCHAR(64) NOT NULL,
    scene           ai_scene    NOT NULL,
    user_id         UUID,                                 -- 触发用户 (NULL = 平台内部)
    agent_id        UUID,                                 -- 关联智能体
    request_id      VARCHAR(64),                          -- 幂等键
    input_tokens    INTEGER     NOT NULL DEFAULT 0,
    output_tokens   INTEGER     NOT NULL DEFAULT 0,
    cost_yuan       DECIMAL(10,6) NOT NULL DEFAULT 0,     -- 实际花费 (元)
    latency_ms      INTEGER,
    success         BOOLEAN     NOT NULL,
    error_message   VARCHAR(500),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 按时间分区友好的索引
CREATE INDEX idx_ai_usage_time ON ai_usage_logs (created_at);
CREATE INDEX idx_ai_usage_provider ON ai_usage_logs (provider_id, created_at);
CREATE INDEX idx_ai_usage_user ON ai_usage_logs (user_id, created_at) WHERE user_id IS NOT NULL;
CREATE INDEX idx_ai_usage_scene ON ai_usage_logs (scene, created_at);

-- 10.5 日预算配置
CREATE TABLE ai_budget_config (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    daily_limit_yuan DECIMAL(10,2) NOT NULL,       -- 每日预算上限 (元)
    alert_threshold  DECIMAL(3,2) NOT NULL DEFAULT 0.80, -- 告警阈值 (80%)
    alert_webhook    VARCHAR(512),                  -- 告警通知 URL (钉钉/WeChat)
    is_active        BOOLEAN NOT NULL DEFAULT TRUE,
    updated_by       UUID REFERENCES users(id),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ---------------------------------------------------------------------------
-- 11. 管理后台
-- ---------------------------------------------------------------------------

-- 11.1 管理员用户 (与 users 分离, 安全隔离)
CREATE TABLE admin_users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username        VARCHAR(32)  NOT NULL UNIQUE,
    password_hash   VARCHAR(128) NOT NULL,
    display_name    VARCHAR(32)  NOT NULL,
    role            admin_role   NOT NULL,
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    last_login_at   TIMESTAMPTZ,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- 11.2 管理操作日志
CREATE TABLE admin_operation_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_id        UUID        NOT NULL REFERENCES admin_users(id),
    action          VARCHAR(64) NOT NULL,      -- 'ban_user', 'update_routing', 'update_budget' 等
    target_type     VARCHAR(32),               -- 操作目标类型
    target_id       UUID,                      -- 操作目标 ID
    detail          JSONB,                     -- 操作详情 (变更前/后)
    ip_address      INET,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_admin_logs_admin ON admin_operation_logs (admin_id, created_at DESC);
CREATE INDEX idx_admin_logs_action ON admin_operation_logs (action, created_at DESC);
CREATE INDEX idx_admin_logs_target ON admin_operation_logs (target_id, target_type);

-- ---------------------------------------------------------------------------
-- 12. 数据看板 (T+1 聚合表)
-- ---------------------------------------------------------------------------

-- 12.1 每日指标聚合
CREATE TABLE daily_metrics (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_date     DATE NOT NULL,
    dau             INTEGER NOT NULL DEFAULT 0,
    mau             INTEGER NOT NULL DEFAULT 0,    -- 当月累计
    new_users       INTEGER NOT NULL DEFAULT 0,
    d1_retention    DECIMAL(5,2),                  -- D1 留存率 %
    d3_retention    DECIMAL(5,2),
    d7_retention    DECIMAL(5,2),
    d14_retention   DECIMAL(5,2),
    d30_retention   DECIMAL(5,2),
    speak_rate      DECIMAL(5,2),                  -- 发言率 %
    agent_usage_rate DECIMAL(5,2),                 -- 智能体使用率 %
    total_messages  INTEGER NOT NULL DEFAULT 0,
    recharge_yuan   DECIMAL(10,2) NOT NULL DEFAULT 0,
    recharge_users  INTEGER NOT NULL DEFAULT 0,
    points_consumed INTEGER NOT NULL DEFAULT 0,
    ai_cost_yuan    DECIMAL(10,2) NOT NULL DEFAULT 0,
    arpu_yuan       DECIMAL(10,2),
    pay_conversion  DECIMAL(5,2),                  -- 付费转化率 %
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_daily_metrics_date ON daily_metrics (metric_date);

-- 12.2 房间每日活跃度
CREATE TABLE daily_room_metrics (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_date     DATE NOT NULL,
    room_id         UUID NOT NULL REFERENCES rooms(id),
    message_count   INTEGER NOT NULL DEFAULT 0,
    active_users    INTEGER NOT NULL DEFAULT 0,
    avg_messages_per_user DECIMAL(8,2),
    peak_online     INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_daily_room_date ON daily_room_metrics (metric_date, room_id);

-- ---------------------------------------------------------------------------
-- 13. 外部 Agent 接入 (Phase 1B 预留命名空间)
-- ---------------------------------------------------------------------------

-- 13.1 外部 Agent 注册 (Phase 1B 邀请制)
CREATE TABLE external_agents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    developer_name  VARCHAR(64) NOT NULL,
    app_id          VARCHAR(64) NOT NULL UNIQUE,       -- 应用标识
    app_secret_hash VARCHAR(128) NOT NULL,             -- 密钥哈希
    jwt_secret_encrypted BYTEA,                        -- JWT 签名密钥 (AES 加密)
    display_name    VARCHAR(64) NOT NULL,
    description     VARCHAR(500),
    callback_url    VARCHAR(512),                      -- 回调地址
    allowed_scopes  VARCHAR(64)[] NOT NULL DEFAULT '{}', -- 权限范围
    rate_limit_rpm  INTEGER NOT NULL DEFAULT 60,       -- 每分钟请求限制
    is_active       BOOLEAN NOT NULL DEFAULT FALSE,    -- 邀请制, 默认关闭
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 13.2 外部 Agent 调用日志
CREATE TABLE external_agent_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_app_id    VARCHAR(64) NOT NULL,
    endpoint        VARCHAR(128) NOT NULL,
    method          VARCHAR(8) NOT NULL,
    status_code     SMALLINT NOT NULL,
    latency_ms      INTEGER,
    ip_address      INET,
    request_body_size INTEGER,
    error_message   VARCHAR(500),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ext_agent_logs_app ON external_agent_logs (agent_app_id, created_at);

-- ---------------------------------------------------------------------------
-- 14. 辅助与配置
-- ---------------------------------------------------------------------------

-- 14.1 短信验证码 (有 TTL, 配合 Redis 做限频)
CREATE TABLE sms_codes (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_hash  VARCHAR(64) NOT NULL,
    code        VARCHAR(6)  NOT NULL,
    purpose     VARCHAR(16) NOT NULL DEFAULT 'login',  -- 'login', 'register', 'reset_password'
    is_used     BOOLEAN     NOT NULL DEFAULT FALSE,
    expires_at  TIMESTAMPTZ NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_sms_codes_phone ON sms_codes (phone_hash, purpose, created_at DESC);

-- 14.2 文件上传记录
CREATE TABLE file_uploads (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    uploader_id     UUID        NOT NULL,               -- users.id
    file_name       VARCHAR(256) NOT NULL,
    file_size       INTEGER     NOT NULL,               -- bytes
    content_type    VARCHAR(64) NOT NULL,                -- MIME type
    storage_path    VARCHAR(512) NOT NULL,               -- MinIO/OSS path
    thumbnail_path  VARCHAR(512),
    is_reviewed     BOOLEAN     NOT NULL DEFAULT FALSE,
    review_result   VARCHAR(16),                         -- 'pass', 'reject'
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_uploads_uploader ON file_uploads (uploader_id, created_at DESC);

-- 14.3 全局配置 (Key-Value)
CREATE TABLE global_config (
    key         VARCHAR(64)  PRIMARY KEY,
    value       JSONB        NOT NULL,
    description VARCHAR(200),
    updated_by  UUID         REFERENCES admin_users(id),
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- 预插入关键配置
INSERT INTO global_config (key, value, description) VALUES
    ('free_daily_chat', '20', '每日免费对话额度'),
    ('free_daily_image', '2', '每日免费图片额度'),
    ('agent_create_cost', '50', '创建智能体积分消耗'),
    ('agent_speak_cost_min', '2', '智能体单次发言最低积分'),
    ('agent_speak_cost_max', '3', '智能体单次发言最高积分'),
    ('image_gen_cost_min', '20', '图片生成最低积分'),
    ('image_gen_cost_max', '30', '图片生成最高积分'),
    ('max_agents_per_user', '3', '用户最大智能体数'),
    ('recharge_daily_limit_yuan', '500', '单日充值上限(元)'),
    ('recharge_monthly_limit_yuan', '5000', '月充值上限(元)'),
    ('room_max_members', '200', '房间最大人数'),
    ('message_max_length', '500', '单条消息最大字符数'),
    ('notification_retention_days', '30', '通知保留天数');

-- ---------------------------------------------------------------------------
-- 完成
-- ---------------------------------------------------------------------------
-- 表总计: 31 张
-- 枚举总计: 22 个
-- 覆盖模块: 用户(4) + 房间(2) + 消息(2) + 智能体(4) + 创作(2) + 积分(2) +
--           通知(1) + 审核(2) + 风控(4) + AI网关(5) + 管理后台(2) + 看板(2) +
--           外部Agent(2) + 辅助(3)
