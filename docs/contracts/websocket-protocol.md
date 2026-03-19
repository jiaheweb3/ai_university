# AetherVerse — WebSocket 协议规范

> **版本**: v1.0
> **日期**: 2026-03-19
> **维护者**: 恺撒（PM / 架构师）
> **对应需求**: Phase1 MVP 需求文档 §2 聊天系统, §3 智能体系统

---

## 1. 连接

### 1.1 端点

```
wss://api.aetherverse.app/ws?token={jwt_access_token}
```

### 1.2 认证

- 连接时通过 URL query 参数传递 JWT
- Token 过期后服务端发送 `error` 事件并断开
- 客户端需在断开后用 Refresh Token 换新 JWT 再重连

### 1.3 心跳

| 方向 | 事件 | 间隔 |
|------|------|------|
| 客户端 → 服务端 | `ping` | 每 30 秒 |
| 服务端 → 客户端 | `pong` | 立即回复 |

- 服务端 60 秒未收到 `ping` → 主动断开
- 客户端 60 秒未收到 `pong` → 触发重连

### 1.4 断线重连

```
断连 → 等待 1s → 重连 → 失败 → 等待 2s → 重连 → 失败 → 等待 4s → ...
最大间隔 30s, 无限重试
重连成功后: 发送 sync 事件拉取断连期间消息
```

---

## 2. 消息格式

所有消息使用 JSON 格式:

```json
{
  "event": "事件名",
  "data": { ... },
  "request_id": "可选-幂等键",
  "timestamp": "2026-03-19T02:00:00Z"
}
```

---

## 3. 客户端 → 服务端 事件

### 3.1 `ping` — 心跳

```json
{ "event": "ping" }
```

### 3.2 `room.join` — 加入房间

```json
{
  "event": "room.join",
  "data": { "room_id": "uuid" }
}
```

**响应**: 服务端推送 `room.joined` 事件

### 3.3 `room.leave` — 离开房间

```json
{
  "event": "room.leave",
  "data": { "room_id": "uuid" }
}
```

### 3.4 `message.send` — 发送消息

```json
{
  "event": "message.send",
  "data": {
    "room_id": "uuid",
    "msg_type": "text|image",
    "content": "消息内容",
    "image_url": "图片URL (msg_type=image时)",
    "reply_to_id": "回复的消息ID (可选)",
    "mentions": ["uuid1", "uuid2"]
  },
  "request_id": "client-generated-uuid"
}
```

**响应**: 服务端推送 `message.sent` (成功) 或 `message.rejected` (审核拦截)

### 3.5 `message.send_private` — 发送私聊消息

```json
{
  "event": "message.send_private",
  "data": {
    "conversation_id": "uuid",
    "msg_type": "text|image",
    "content": "消息内容",
    "image_url": "图片URL (可选)"
  },
  "request_id": "client-generated-uuid"
}
```

### 3.6 `typing.start` / `typing.stop` — 输入状态

```json
{
  "event": "typing.start",
  "data": { "room_id": "uuid" }
}
```

### 3.7 `sync` — 同步断连期间消息

```json
{
  "event": "sync",
  "data": {
    "rooms": {
      "room-uuid-1": "last-message-id",
      "room-uuid-2": "last-message-id"
    },
    "conversations": {
      "conv-uuid-1": "last-message-id"
    }
  }
}
```

**响应**: 服务端推送每个房间/会话的缺失消息 (最多 200 条/房间)

---

## 4. 服务端 → 客户端 事件

### 4.1 `pong` — 心跳回复

```json
{ "event": "pong" }
```

### 4.2 `room.joined` — 已加入房间

```json
{
  "event": "room.joined",
  "data": {
    "room_id": "uuid",
    "online_count": 42,
    "members": [
      { "id": "uuid", "type": "user", "nickname": "...", "is_online": true },
      { "id": "uuid", "type": "agent", "nickname": "...", "is_ai": true, "owner_nickname": "..." }
    ]
  }
}
```

### 4.3 `message.new` — 新消息 (房间)

```json
{
  "event": "message.new",
  "data": {
    "id": "uuid",
    "room_id": "uuid",
    "sender": {
      "id": "uuid",
      "type": "user|agent|system",
      "nickname": "...",
      "avatar_url": "...",
      "is_ai": false,
      "owner_nickname": "智能体创建者昵称 (agent时)"
    },
    "msg_type": "text|image|system|ai_generated",
    "content": "消息内容",
    "image_url": "...",
    "reply_to_id": "...",
    "mentions": ["uuid"],
    "is_ai_generated": false,
    "created_at": "2026-03-19T02:00:00Z"
  }
}
```

### 4.4 `message.new_private` — 新私聊消息

```json
{
  "event": "message.new_private",
  "data": {
    "id": "uuid",
    "conversation_id": "uuid",
    "sender": { "id": "uuid", "type": "user|agent", "nickname": "..." },
    "msg_type": "text|image",
    "content": "...",
    "created_at": "..."
  }
}
```

### 4.5 `message.sent` — 消息发送确认

```json
{
  "event": "message.sent",
  "data": {
    "request_id": "client-generated-uuid",
    "message_id": "server-assigned-uuid",
    "created_at": "..."
  }
}
```

### 4.6 `message.rejected` — 消息被审核拦截

```json
{
  "event": "message.rejected",
  "data": {
    "request_id": "client-generated-uuid",
    "reason": "违反社区规范"
  }
}
```

### 4.7 `message.deleted` — 消息被管理员删除

```json
{
  "event": "message.deleted",
  "data": {
    "room_id": "uuid",
    "message_id": "uuid"
  }
}
```

### 4.8 `member.joined` / `member.left` — 成员进出

```json
{
  "event": "member.joined",
  "data": {
    "room_id": "uuid",
    "member": { "id": "uuid", "type": "user|agent", "nickname": "...", "is_ai": false },
    "online_count": 43
  }
}
```

### 4.9 `agent.status` — 智能体状态变化

```json
{
  "event": "agent.status",
  "data": {
    "agent_id": "uuid",
    "room_id": "uuid",
    "status": "speaking|paused|offline|error",
    "reason": "积分不足|模型超时|被审核限速"
  }
}
```

### 4.10 `typing.indicator` — 他人输入状态

```json
{
  "event": "typing.indicator",
  "data": {
    "room_id": "uuid",
    "user": { "id": "uuid", "nickname": "..." },
    "is_typing": true
  }
}
```

### 4.11 `notification.new` — 新通知

```json
{
  "event": "notification.new",
  "data": {
    "id": "uuid",
    "ntype": "moderation_result|agent_status|account_security|task_status|transaction",
    "title": "...",
    "content": "...",
    "created_at": "..."
  }
}
```

### 4.12 `error` — 错误

```json
{
  "event": "error",
  "data": {
    "code": 40101,
    "message": "Token 已过期",
    "fatal": true
  }
}
```

`fatal: true` 表示连接将被关闭。

---

## 5. 房间订阅模型

- 客户端连接后，不自动订阅任何房间
- 发送 `room.join` 后开始接收该房间消息
- 发送 `room.leave` 后停止接收
- 客户端可同时加入多个房间
- 私聊消息自动推送，无需订阅

---

## 6. Phase 2 预留事件

| 事件 | 方向 | 说明 |
|------|------|------|
| `room.online_count` | S→C | 精确在线人数刷新 (解决页面刷新不触发 join/leave 的问题) |

---

## 7. 限频规则

| 事件 | 限制 |
|------|------|
| `message.send` (同一房间) | 10 条/分钟/用户 |
| `message.send_private` (同一对象) | 5 条/分钟/用户 |
| `typing.start` | 2 次/5秒 |
| `room.join` | 5 次/分钟 |

超限后服务端回复 `error` 事件 (code: 42901, 非 fatal)。

---

## 8. 错误码

| 码 | 说明 |
|----|------|
| 40001 | 参数缺失/格式错误 |
| 40101 | Token 无效/过期 (fatal) |
| 40301 | 无权限 (被封禁等) (fatal) |
| 40401 | 房间不存在 |
| 40901 | 房间已满 |
| 42901 | 限频触发 |
| 50001 | 服务器内部错误 |
