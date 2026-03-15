---
description: 上下文管理工作流 - 防止跨对话上下文丢失
---

# 上下文管理工作流

## 对话开始时
1. 检查 `context_memory/` 目录是否存在
2. 如果存在，读取以下文件：
   - `context_memory/project_decisions.md` — 项目决策记录
   - `context_memory/coding_conventions.md` — 编码规范
   - `context_memory/session_checkpoints.md` — 对话检查点
3. 简要确认已加载上下文

## 对话中
1. 遇到新的设计决策时，即时记录到 `project_decisions.md`
2. 遇到新的编码规范时，即时记录到 `coding_conventions.md`
3. 完成重要任务后，更新 `session_checkpoints.md`

## 对话结束时
1. 更新 `session_checkpoints.md`，记录本次对话的关键进展
2. 如有新决策，更新 `project_decisions.md`
3. 如有新规范，更新 `coding_conventions.md`

## 质量保证
1. 对话超过 15 轮时，主动提醒是否需要开新对话
2. 复杂任务中，定期重新读取 `coding_conventions.md` 确保一致性
3. 发现可能遗忘早期约定时，主动告知并重新确认
