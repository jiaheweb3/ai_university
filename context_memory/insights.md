# 灵感与创新记录

> 项目：AetherVerse（AI × 元宇宙社交平台）
> 创建时间：2026-03-19

## 2026-03-19

### 洞察
- **WsClient 单例 vs Provider 注入的取舍**：代码审查中发现 WsClient 没做单例，修复时选择了与 ApiClient 一致的静态单例模式。但 Riverpod 生态更推崇 Provider 注入（可测试性更好）。Phase 2 如果需要多租户或多 WS 连接场景，应考虑迁移到 `Provider<WsClient>` 注入模式，同时可用 `overrideWithValue` 在测试中替换为 mock。
- **i18n 架构的演进路径**：当前 `strings.dart` 用纯 Dart 常量实现，零依赖、零配置。但国际化扩展时需要迁移到 `flutter_localizations` + ARB 文件。建议在 Phase 2 启动多语言时，写一个脚本自动从 `S.xxx` 提取 key 生成 ARB，保证迁移平滑。
- **乐观更新的通用模式**：S-4 审查反馈让我意识到，项目中所有写操作（创建/更新/删除）都应该统一采用"乐观更新 → API 确认 → 失败回滚"模式。可以抽象成一个 `optimisticUpdate<T>()` 工具函数，减少每个 Provider 重复实现。
