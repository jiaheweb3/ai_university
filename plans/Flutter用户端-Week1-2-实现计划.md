# Apollo (Agent C) — Flutter 用户端 Week 1-2 实现计划

Phase 1 MVP Flutter 用户端初始化 + 网络层 + 认证 + 首页。

## 前置问题

1. **Flutter SDK 未安装**：当前系统未检测到 Flutter。需要先安装。
2. **状态管理选型**：`coding_conventions.md` 标注待定，启动指令要求 Riverpod。需确认。

## 技术架构

| 层 | 选型 | 版本 |
|---|---|---|
| 框架 | Flutter | 3.22+ |
| 语言 | Dart | 3.4+ |
| 状态管理 | flutter_riverpod | ^2.5.0 |
| HTTP | Dio | ^5.4.0 |
| WebSocket | web_socket_channel | ^2.4.0 |
| 路由 | GoRouter | ^14.0.0 |
| 本地存储 | shared_preferences | ^2.2.0 |
| 图片缓存 | cached_network_image | ^3.3.0 |
| 图片选择 | image_picker | ^1.0.0 |

## Week 1-2 交付范围

### 项目初始化
- `flutter create --org com.aetherverse --project-name aetherverse_app .`
- 配置依赖、复制共享类型、搭建目录结构

### Core 层 (lib/core/)
- `app.dart` — MaterialApp + ProviderScope 入口
- `theme.dart` — Material 3 主题 (浅色+深色, 品牌色: 深空蓝 #1E3A5F + 科技紫 #7C3AED)
- `router.dart` — GoRouter 路由定义 + 认证守卫
- `constants.dart` — API/WS Base URL, 分页参数

### 网络层 (lib/services/)
- `api_client.dart` — Dio 封装 (JWT 自刷新, 401→refresh→重试, 统一错误处理)
- `ws_client.dart` — WebSocket (30s 心跳, 指数退避重连, sync 补拉, 事件分发)
- `auth_service.dart` — 7 个认证 API 封装
- `storage_service.dart` — Token 持久化

### 认证页面 (lib/screens/auth/)
- 登录 (密码/验证码双模式)、注册、忘记密码

### 首页 (lib/screens/home/)
- 底部导航 (首页/消息/创作/我的)
- 房间列表 (分类筛选+搜索+下拉刷新+Cursor分页)

### Providers
- `auth_provider.dart` — 登录/注册/登出状态
- `room_provider.dart` — 房间列表/详情

## 目录结构

```
app/lib/
├── main.dart
├── core/          (app/theme/router/constants)
├── models/        (shared_types.dart)
├── services/      (api_client/ws_client/auth_service/storage_service)
├── providers/     (auth/room)
├── screens/       (auth/home)
└── widgets/       (room_card/loading_indicator)
```

## 验证方案
1. `flutter pub get` — 0 error
2. `flutter analyze` — 0 issues
3. `flutter run -d chrome` — Web 版运行验证 UI
4. 路由: 闪屏→未登录→登录页 | 登录→首页
5. Mock 数据房间列表展示
