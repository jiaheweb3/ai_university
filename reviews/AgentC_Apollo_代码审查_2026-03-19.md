# Apollo (Agent C) 代码审查报告

> **审查人**: 恺撒 | **日期**: 2026-03-19  
> **审查范围**: `app/lib/` 全部文件（41 files）  
> **总体评价**: ⭐⭐⭐⭐ **良好** — 架构清晰，契约对齐度高，代码可读性好。有 3 个 Bug 需修复，4 个建议可后续跟进。

---

## ❌ Bug（必须修复）

### BUG-1: `MessageSender` 类重复定义

`MessageSender` 在两个文件里各定义了一次：
- [shared_types.dart#L128-155](file:///c:/projects/ai_university/app/lib/models/shared_types.dart#L128-L155)
- [message.dart#L5-32](file:///c:/projects/ai_university/app/lib/models/message.dart#L5-L32)

同一个类两份定义，修改一个忘改另一个就会出数据解析错误。**`message.dart` 应删除 `MessageSender`，统一从 `shared_types.dart` 导入。**

同理，`shared_types.dart` 里还有 `MessageModel`（L157）和 `AgentModel`（L234）。而 `message.dart` 里有 `Message`、`agent.dart` 里有 `Agent`。这造成了**两套平行的数据模型**。需要统一：要么只用 `shared_types.dart`，要么让 `shared_types.dart` 只放枚举和工具类，models 放具体业务模型（推荐后者，当前 `message.dart` 的定义更完整）。

> **修复方案**: 从 `shared_types.dart` 删除 `MessageModel`、`MessageSender`、`AgentModel`、`PersonaConfig`（保留枚举和 `ApiResponse`/`PaginatedData`/`WsEvents`/`UserProfile*`）。各 service 和 provider 统一引用 `models/*.dart`。

---

### BUG-2: WebSocket 事件名格式不匹配协议

[message_provider.dart#L130-136](file:///c:/projects/ai_university/app/lib/providers/message_provider.dart#L130-L136):

```dart
case 'message:new':    // ❌ 用了冒号
case 'typing:start':   // ❌
case 'typing:stop':    // ❌
```

但 WebSocket 协议和 `WsEvents` 常量用的是**点号**分隔：

```dart
// shared_types.dart L296-306
static const messageNew = 'message.new';      // ✅ 点号
static const typingStart = 'typing.start';    // ✅
```

**Provider 里的事件名全部写错了**，导致消息实时推送不会触发任何处理。

> **修复**: 改为 `case WsEvents.messageNew:` / `WsEvents.typingStart` / `WsEvents.typingStop`，直接引用常量。

---

### BUG-3: `WsClient` 是新实例不是全局单例

[message_provider.dart#L65](file:///c:/projects/ai_university/app/lib/providers/message_provider.dart#L65):

```dart
final WsClient _ws = WsClient();  // 每个 Notifier 都 new WsClient()
```

但 `WsClient` 没有 singleton 工厂构造函数。每个 `RoomMessageNotifier` 都会创建独立的 `WsClient` 实例，各自建立独立 WebSocket 连接。

对比 `ApiClient` 做了单例：
```dart
static final ApiClient _instance = ApiClient._internal();
factory ApiClient() => _instance;
```

**`WsClient` 缺少同样的单例模式。**

> **修复**: 给 `WsClient` 加上与 `ApiClient` 相同的 singleton 工厂，或者通过 Riverpod Provider 注入一个全局实例。

---

## ⚠️ 建议优化（不阻塞，后续迭代改进）

### S-1: `AuthNotifier` 登录时丢弃了加载态的用户数据

[auth_provider.dart#L64](file:///c:/projects/ai_university/app/lib/providers/auth_provider.dart#L64):

```dart
state = const AsyncValue.data(AuthState(isLoading: true));
// ↑ 如果用户在此期间查看 state.value.user，会拿到 null
```

改善：设 `isLoading: true` 时保留旧 `user` 数据，避免 UI 闪烁。

---

### S-2: `toggleSpeaking` 乐观更新写法太冗长

[agent_provider.dart#L128-143](file:///c:/projects/ai_university/app/lib/providers/agent_provider.dart#L128-L143) — 手动构造 `Agent()` 只为改一个字段。建议给 `Agent` 模型加 `copyWith` 方法。

---

### S-3: 路由 `/topics` Tab 名应为"发现"

[router.dart#L77](file:///c:/projects/ai_university/app/lib/core/router.dart#L77) — Tab 路径仍然叫 `/topics`、title 叫"创作"。根据原型图更新计划 M7，已改为"发现"（房间广场/推荐）。路径建议改为 `/discover`。

---

### S-4: `delete()` 应先乐观删除再调 API

[agent_provider.dart#L102-107](file:///c:/projects/ai_university/app/lib/providers/agent_provider.dart#L102-L107) — 当前是先 `await _service.deleteAgent()` 成功后才从列表移除。如果 API 慢，UI 会有明显延迟。建议先乐观移除，API 失败再回滚。

---

## ✅ 做得好的地方

| 项目 | 说明 |
|------|------|
| **JWT 自动刷新** | `api_client.dart` 用独立 Dio 实例刷新 Token，避免循环拦截——标准做法 ✅ |
| **WS 心跳/重连** | `ws_client.dart` 完整实现了协议规定的 30s ping / 60s pong timeout / 指数退避 ✅ |
| **WS sync 事件** | 重连后自动发送 `sync` 拉取断连期间消息——比大多数实现考虑得周全 ✅ |
| **枚举对齐** | `shared_types.dart` 的 14 个枚举与 DB Schema 一一对应 ✅ |
| **WsEvents 常量** | 全部 20 个事件名集中管理，与 `websocket-protocol.md` 完全匹配 ✅ |
| **环境变量注入** | `constants.dart` 用 `String.fromEnvironment` 支持编译时注入 API URL ✅ |
| **分页设计** | cursor-based 分页正确对齐 API 契约 ✅ |
| **错误处理** | `ApiException` + `_handleDioError` 完整覆盖超时/断网/业务错误 ✅ |
| **测试覆盖** | 51 个测试覆盖模型序列化、Provider 状态流转、WS 消息——Week 1-2 够用 ✅ |

---

## 修复优先级

| 优先级 | 项目 | 预计工时 |
|--------|------|---------|
| **P0** | BUG-2: WS 事件名格式错误 | 5 分钟 |
| **P0** | BUG-3: WsClient 缺少单例 | 10 分钟 |
| **P1** | BUG-1: 模型类重复定义 | 30 分钟（需要全局替换引用） |
| **P2** | S-1 ~ S-4 | 下次迭代 |
