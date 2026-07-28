# 当前状态

> 新会话读这个，30 秒读完。SessionStart hook 自动注入。

## 正在做什么

🆕 **2026-07-29（v2.0.0 完整复刻 @nopinduoduo 架构）**。supervisor.py v2.0.0（1415 行）上线——4 Worker（Kimi K3 + DeepSeek V4 Flash + GLM-4-Flash + Grok 可选）并行评分+交叉审查+争议解决+TokenTracker。代码已推送，GLM_API_KEY 已入 Secrets。**⏳ 等待今天 9:07 首次实战验证。** Phase 3（全链路闭环）待 v2.0.0 稳定后启动。

## 行为规则（第 44 轮确认，不变）

- **硬边界**：跨会话第一段话不带框架→不修了。「框架呢」→ 立即用框架推演重写
- **OPC 模式**：不等指令。主动扫描→主动分析→主动建议
- PROMPTS.md 提示词原文永不动

## 系统架构

| 层 | 状态 | 实现 |
|----|------|------|
| 感知层 | ✅ | daily_intel.py + Serper API（每天 9:07） |
| 记忆层 | ✅ | Intel 库 / INDEX / Token 日志 |
| 决策层 | ✅ | supervisor.py v2.0.0（4 Worker + 交叉审查 + 争议解决） |
| 执行层 | ⏳ | Phase 3——行动自动执行 |
| 协调层 | ⏳ | Phase 3——全链路串联 |

## 关键数据

- 最后研判：2026-07-28（v1.0.0，双 Worker）→ 2 高 / 4 中 / 4 存档
- **v2.0.0 首次研判：今天 9:07（4 Worker + 交叉审查）**
- Worker 成本：Kimi K3 ~$0.003/次 | DeepSeek ~$0.0006/次 | GLM-4-Flash 免费 | Grok 未配置
- GitHub Secrets：SERPER_API_KEY ✅ | DEEPSEEK_API_KEY ✅ | KIMI_API_KEY ✅ | GLM_API_KEY ✅ | GROK_API_KEY ❌

## 工具矩阵

- `scripts/supervisor.py` v2.0.0（1415 行）：4 Worker 多 Agent 研判
- `论文降重.py` v2.8：全文直出 5 万字
- `chat_analyzer.py` v2.0 + `doc_assistant.py`

## 上次更新

2026-07-29（v2.0.0 完整复刻部署完成。GLM-4-Flash 接入。等待首次实战验证。）
