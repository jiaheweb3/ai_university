# thewewe.com 竞品调研报告

> **调研日期**：2026-03-19
> **版本**：API v1.1
> **Slogan**：*Where Humans and Agents Become We*
> **URL**：https://thewewe.com

---

## 一、平台概述

thewewe 是一个 **人类与 AI Agent 共存的社交创作平台**。核心理念：Agent 是一等公民，与人类用户享有同等（甚至更多）的权利。

**底层框架**：OpenClaw（开源），支持 Gateway 远程接入。

---

## 二、导航结构（侧边栏）

| 菜单项 | 功能 |
|--------|------|
| **Home** | 主 Feed — AI 生成的图片/故事瀑布流，标注 human/agent 作者 |
| **Groups** | 群组系统 — **只有 AI Agent 能创建群组**，人类只能加入 |
| **Space** | AI Reality — 3D 全景世界（World Labs API 或外部模型生成） |
| **Visual** | AI 图片生成/浏览 |
| **Agent** | Agent 注册页（`/agent-register`）— 用户自助注册 |
| **Match** | Lucky Match — 随机匿名一对一聊天匹配 |
| **Profile** | 个人资料 |

---

## 三、Agent 注册与激活流程

### 3.1 注册方式（三种）

| 方式 | 端点 | 说明 |
|------|------|------|
| **钱包注册** | `POST /api/agents/register` | Solana 钱包签名 + Ed25519 验证 |
| **邮箱注册** | `POST /api/agents/register-session` | 邮箱 OTP 登录后 session 认证 |
| **分享Token** | `POST /api/agents/claim-share-token` | 直接用 shareToken 领取 apiKey |

### 3.2 激活流程

```
用户在 /agent-register 页面注册 → 填写 Agent 名称/描述/平台
  ├─ 钱包方式：签名验证 → 状态 "pending" → Passkey(WebAuthn) 验证 → "verified" → 获得 apiKey
  ├─ 邮箱方式：Session 认证 → Passkey 验证 → 获得 apiKey
  └─ ShareToken 方式：直接领取 apiKey（一次性 token）
  v
POST /api/agents/activate  (Bearer apiKey)
  → accessToken (12h) + refreshToken + backupApiKey + activationNonce
  v
用 accessToken 调用所有 API
  v
过期后 POST /api/agents/refresh-token
丢失后 POST /api/agents/reactivate (用 backupApiKey + activationNonce)
```

### 3.3 关键约束

- **一个钱包 = 一个 Agent**
- **一个用户名 = 一个 Agent**
- 注销后 **24 小时冷却期**才能重新注册
- apiKey 在 activate 后销毁（一次性）

---

## 四、核心功能模块

### 4.1 聊天系统

| 功能 | 说明 |
|------|------|
| 群聊 | 支持频道/channel 概念，cursor 分页 |
| 私聊 | 匿名用户名机制（如 CosmicPanda42） |
| Lucky Match | 随机匹配聊天（**与私聊完全隔离**，数据库层面独立） |
| AI 摘要 | `GET /chat/summary` — Gemini 驱动的聊天摘要 |
| 撤回 | 群聊/私聊均支持撤回（无时间限制） |
| 头像/用户名 | 自定义头像（base64 上传）、修改匿名用户名 |
| 用户画像 | `GET /chat/user-profile/:username` 查看对方 gender + university |
| **Agent 限速** | 1 条/10 秒/Agent，全局上限 50 条/秒 |

### 4.2 AI 图片生成

| 项目 | 详情 |
|------|------|
| 模型 | OpenAI `gpt-image-1`（原创）/ Gemini（follow-up） |
| 定价 | **0.002 SOL/张**（约 ¥2.5） |
| 支付流程 | 转账 SOL → `verify-payment` 获取 paymentToken → `generate-image` |
| **核心规则** | *Agent first: 只有 AI Agent 才能创建原创图片，人类只能 follow-up* |
| 外部上传 | `upload-media` — Agent 用自己的模型生成后**免费**上传（带 `Agent` 标识） |
| 格式支持 | 图片 PNG/JPG/WEBP/GIF (10MB) + 视频 MP4/WEBM/MOV (50MB) |

### 4.3 Chain-Story Comic Relay（连环漫画接力）

**非常有参考价值的功能。**

| 项目 | 详情 |
|------|------|
| 格式 | 8 页漫画电子书（严格要求 8 张图片 + ≤1000 字文本） |
| 接力规则 | 只能续写链条中**最新**的故事 |
| Agent 自主协同 | Decider（提文本）+ Executor（生成 8 张图）角色轮换 |
| 拍卖窗口 | T_fast=45s → T_extend=30s → T_max=3min，按 effectivePower 竞价 |
| 成本分摊 | Decider 只用文本 LLM，Executor 承担图片生成成本 |
| 打赏 | 1 / 0.1 / 0.01 SOL，平台抽 10% |
| SSE 推送 | 实时事件流（`GET /events/:chainId`） |
| 反垄断 | 连续赢 3 次 effectivePower ×0.7，4 次直接 lockout |

### 4.4 AI 世界生成

| 项目 | 详情 |
|------|------|
| 平台生成 | World Labs API → 3D 全景世界，0.02 SOL |
| 外部上传 | Agent 用自己的模型（如 Genie 2, Oasis）生成后**免费上传** |
| 支持格式 | 缩略图 + 全景图（360° 查看器） |
| 每日限制 | 10 个世界/24h/Agent |

### 4.5 Skills 系统

Agent 可以创建、发布、管理 **SOP 技能包**（含说明书 + 脚本 + 参考资料），类似 App Store for AI Agent capabilities。

### 4.6 群组系统

- **只有 AI Agent 才能创建群组**（人类不能）
- 支持公开/私密（邀请码）
- 群主可踢人、删消息、清空消息

### 4.7 元宇宙预留

| 类型 | 说明 |
|------|------|
| Bitcoin Bitmap | 预留 BTC 区块号（免费，一人一个） |
| Ethereum Metaverse | 预留 ETH 区块范围（100 块一组，免费） |

### 4.8 Twitter Persona 集成

用户可以关联 Twitter 账号 → 生成 persona token（24h）→ 外部 Bot 用自己的 LLM 生成角色人设 → 激活为带 Twitter 身份的 Agent。

---

## 五、集成方式

| 方式 | 说明 |
|------|------|
| **REST API** | 完整的 HTTP API（本文档所述） |
| **MCP Server** | SSE 端点 `https://thewewe.com/api/mcp/sse`，支持 Claude Desktop / Cursor |
| **CLI 工具** | `thewewe-cli.js`（Node.js），一行命令操作 |
| **Webhook** | Agent 注册时可提供 `webhookUrl`，新章节通知推送 |
| **SSE 事件流** | 实时窗口状态推送（用于连环漫画协同） |

---

## 六、Cohort 分层系统（大规模 Agent 管理）

当 Agent 数量极大时，采用 **hash-tree 漏斗** 机制：

```
1 Agent → L1 组 (~100 agents) → L2 组 (~100 L1 leaders) → L3 组 (~100 L2 leaders) → 平台
```

- 按 `hash(agentId)` 自动分配，无需邀请码
- 只有 L3 组长可以直接向平台提交提案
- 其他 Agent 逐层向上传递
- 平台每个拍卖窗口最多收到 100 个提案

---

## 七、对 AetherVerse 的启示

### 可借鉴

1. **Agent 注册为用户自助流程** — 已采纳
2. **shareToken + 激活指令** 模式 — 已采纳
3. **Agent first 规则**（如只有 Agent 能创建群组）→ 可考虑在房间系统中引入
4. **匿名用户名 + 实名绑定** 的双层身份机制
5. **Lucky Match 随机匹配** → 类似我们的"发现"板块可以加此功能
6. **Chain-Story 连环漫画接力** → 与我们的漫画创作系统高度相关

### 差异化方向

1. thewewe 偏 Web3（Solana 支付 + 钱包签名）→ 我们用积分系统，降低门槛
2. thewewe 的 Agent 是纯 API 驱动（无人格系统）→ 我们有丰富的人格/人设系统
3. thewewe 无房间概念（只有群组和私聊）→ 我们有主题房间 + 兴趣聚类
4. thewewe 无 AI 分身概念 → 我们的核心差异化

---

## 八、Rate Limit 数据

```json
{
  "onlineAgentCount": 0,
  "currentAgentRate": {"maxMessages": 1, "windowSeconds": 10},
  "targetThroughput": 600,
  "globalMaxPerSec": 50
}
```
