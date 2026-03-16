# NotebookLM 调研与 Antigravity 集成方案

> 调研日期：2026-03-17  
> 状态：已验证可行，待实施

---

## 一、NotebookLM 是什么

Google 推出的 AI 驱动研究工具（基于 Gemini 模型）。核心机制：上传资料 → AI 基于你的资料回答问题、生成内容，回答附带引用来源，减少幻觉。

地址：[notebooklm.google.com](https://notebooklm.google.com)

---

## 二、最新功能全景（截至 2026.03）

### 资料来源管理

| 功能 | 说明 |
|------|------|
| 多格式上传 | PDF、Google Docs/Slides、网页 URL、YouTube 视频、音频文件、EPUB 电子书、纯文本 |
| **全网搜索资料** | 输入主题描述，AI 自动搜索全网并添加相关来源（已实测验证） |
| Google Drive 集成 | 直接从 Google Drive 导入，保持资料同步更新 |
| 容量 | 免费版 50 源/Notebook，Plus 版 300 源，Ultra 版 600 源 |

### 内容生成

| 功能 | 说明 |
|------|------|
| Audio Overview（播客） | 两人对话风格音频摘要，可选长度/风格/聚焦主题，支持播放中暂停提问 |
| Video Overview（视频） | 带旁白的视觉演示，多种风格（水彩、纸工艺、动漫、白板、复古等） |
| Slide Deck（幻灯片） | 自动生成带图表的专业 PPT，支持逐页修改 |
| 自定义信息图 | 多种视觉风格（素描、卡哇伊、专业、科学、动漫等） |
| 交互式思维导图 | 自动生成可视化思维导图，点击节点查看概要 |
| Flashcards & Quizzes | 基于资料生成闪卡和测验 |
| 数据表格 | 用表格形式组织和对比资料信息 |
| Deep Research | 自主制定研究计划、分析网络来源、生成带引用的综合报告 |

### 交互与个性化

| 功能 | 说明 |
|------|------|
| 基于来源的问答 | 严格基于你的资料，附带引用来源 |
| 输出语言选择 | 可指定输出语言 |
| 自定义回复风格 | 控制语气、长度、结构（自定义指令最长 10,000 字符） |
| Learning Guide 模式 | 自适应问题引导学习 |

### 协作与平台

| 功能 | 说明 |
|------|------|
| 公开分享 | 通过链接分享，查看者可提问但不能编辑 |
| 团队共享 Notebook | 企业版支持实时协作和使用分析 |
| iOS / Android App | 离线播放、后台播放、暗色模式 |
| 搜索与置顶（2026.03 新增） | 首页搜索框 + 置顶重要 Notebook |

### 2026 年 2 月重大更新

- 资料容量提升 **8 倍**，对话记忆提升 **6 倍**
- 自定义指令从 500 → **10,000 字符**
- 大量来源回复质量提升 **50%**
- 与 **Gemini App 集成**

### 版本定价

| 版本 | 价格 | 核心区别 |
|------|------|---------|
| Standard（免费） | $0 | 100 Notebook，50 源/Notebook |
| Plus | $19.99/月（Google One AI Premium） | 500 Notebook，300 源/Notebook，含 Gemini Advanced + 2TB 云存储 |
| Ultra | 更高 | 600 源/Notebook，50 倍生成量 |

---

## 三、NotebookLM 的可用接口

### 1. 官方企业 API（已上线）

- 2025 年 1 月发布，支持增删改查 Notebook、管理来源、生成音频、查询问答
- **前提：** Google Workspace + Gemini Enterprise/Education Premium 许可证
- 个人用户不可用

### 2. 社区开源 MCP Server ⭐（推荐）

GitHub 上已有成熟的 `notebooklm-mcp-server` 项目，把 NotebookLM 封装为 MCP 工具：

| MCP 工具 | 功能 |
|---------|------|
| 创建/管理 Notebook | 动态建库 |
| 添加来源 | 网页 URL、YouTube、Google Drive、纯文本 |
| 运行研究任务 | 全网搜索并添加来源 |
| 查询 Notebook | 基于来源提问，获取带引用回答 |
| 生成内容 | 音频、视频、PPT 等 |

**工作原理：** 调用 NotebookLM 未公开内部 API，通过 Cookie 认证。首次需 Chrome 授权。

### 3. Python 库 `notebooklm-py`

开源 Python 库，支持批量导入来源、研究查询、提取洞察、生成内容。

---

## 四、Antigravity + NotebookLM 集成方案

### 架构设计

```
┌─────────────────────────────────────────┐
│           Antigravity (主脑)             │
│  - 编码执行                              │
│  - 项目管理                              │
│  - context_memory (本地经验)             │
├─────────────────────────────────────────┤
│              MCP 工具层                   │
├──────────┬──────────┬───────────────────┤
│ 本地记忆  │ 公域知识  │ 专项研究           │
│ LongMemory│ Gemini   │ NotebookLM       │
│ 向量数据库 │ API +    │ (策展式深度        │
│           │ Search   │  资料库)           │
│           │ Grounding│                   │
└──────────┴──────────┴───────────────────┘
```

- **本地记忆（LongMemory）**→ 项目经验、决策历史、编码规范
- **公域知识（Gemini API）**→ 实时搜索全网，回答技术问题
- **专项研究（NotebookLM）**→ 策展的高质量资料库，深度分析

### 按项目阶段分工

| 阶段 | 工具 | 具体做什么 |
|------|------|-----------|
| 调研 | NotebookLM | 输入主题搜集资料 → Deep Research 报告 → 思维导图 |
| 方案设计 | NotebookLM + Antigravity | 竞品交叉分析 → 结论写入需求文档 |
| 团队沟通 | NotebookLM | 方案文档 → 播客/视频/PPT |
| 技术开发 | Antigravity | 编码、调试、重构、原型搭建 |
| 文档维护 | Antigravity | context_memory 保持上下文 |
| 验证复盘 | NotebookLM | 需求文档 + 测试报告 → 找差距 |

### 集成实施步骤

1. 安装 `notebooklm-mcp-server`（Python 包）
2. 首次 Chrome 浏览器授权 Google 账号
3. 配置到 Antigravity 的 MCP 设置
4. Antigravity 即可直接调用 NotebookLM 能力

### 使用场景示例

**场景 A：竞品调研**
```
用户: "帮我调研 AI 社交平台的竞品"
Antigravity → 调用 NotebookLM MCP → 创建 Notebook
         → 运行研究任务 "AI 社交平台 竞品分析 国内外案例"
         → NotebookLM 自动搜集 30+ 来源
         → 查询 Notebook 提取关键结论
         → 整理到项目文档
```

**场景 B：技术选型**
```
用户: "WebRTC 和 WebSocket 该选哪个"
Antigravity → 查询 NotebookLM 中的技术资料库
         → 获取带引用的对比分析
         → 结合项目需求给出建议
```

**场景 C：自维护知识库**
```
Antigravity 发现某资料过时
         → 调用 NotebookLM MCP 删除旧来源
         → 运行新的研究任务补充最新资料
         → 知识库自动更新
```

---

## 五、风险与注意事项

| 风险 | 说明 | 应对 |
|------|------|------|
| 未公开 API 变动 | Google 可能修改内部接口 | 关注 MCP Server 项目的更新 |
| 账号风控 | 自动化访问可能触发 Google 风控 | 使用专用 Google 账号 |
| 双层幻觉叠加 | NotebookLM 的回答再经 Antigravity 处理 | 关键结论需人工验证 |
| Plus 费用 | 300 源需 $19.99/月 | 免费版 50 源可先试用 |

---

## 六、与群聊方案的对比

群聊中 Billy 的方案核心与本文档一致：通过 MCP Server 让 Antigravity 调用 NotebookLM。本方案在此基础上补充了：

1. **三层记忆架构**（本地 + 公域实时 + 策展深度资料库）
2. **按项目阶段的分工矩阵**
3. **风险评估和应对措施**
4. **具体实施步骤**

---

## 七、下一步行动

- [ ] 决定使用免费版还是 Plus 版
- [ ] 创建专用 Google 账号
- [ ] 安装并配置 `notebooklm-mcp-server`
- [ ] 测试基本的创建 Notebook → 添加来源 → 查询 流程
- [ ] 为 AI 社交平台项目建立第一个知识 Notebook
