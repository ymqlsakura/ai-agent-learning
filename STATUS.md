# 当前状态

> 新会话读这个，30 秒读完。SessionStart hook 自动注入。

## 正在做什么

🆕 **2026-07-28（OPC Phase 2——v2.0.0 完整复刻 @nopinduoduo 架构）**。supervisor.py v2.0.0 上线——Kimi K3 + DeepSeek + Grok（可选）三 Worker，新增交叉审查协议（Worker 互相挑战/提问/调整评分）+ 争议解决（多数投票）+ Token 追踪（per-run 费用日志）。Grok Worker 可选——有 GROK_API_KEY 自动激活。supervisor-daily.yml 已部署。

## 行为规则（第 44 轮确认，不变）

- **硬边界**：跨会话第一段话不带框架→不修了。「框架呢」→ 立即用框架推演重写
- **OPC 模式**：不等指令。主动扫描→主动分析→主动建议
- PROMPTS.md 提示词原文永不动

## 系统架构

| 层 | 状态 | 实现 |
|----|------|------|
| 感知层 | ✅ | daily_intel.py + Serper API（每天 9:07） |
| 记忆层 | ✅ | Intel 库 / INDEX / 摘要 |
| **决策层** | **✅** | **supervisor.py（Kimi K3 + DeepSeek 双 Worker）** |
| 执行层 | ⏳ | Phase 3——行动自动执行 |
| 协调层 | ⏳ | Phase 3——全链路串联 |

## 关键数据

- 最后一次研判：2026-07-28 21:11（Kimi+Kimi K3）→ 2 条高优先级 / 4 条中优先级 / 4 条存档
- API 成本：Kimi K3 ¥0.4/次（10 条），DeepSeek ~¥0.02/次
- GitHub Secrets：SERPER_API_KEY ✅ / DEEPSEEK_API_KEY ✅ / KIMI_API_KEY ✅

## 工具矩阵

- `scripts/supervisor.py`：多 Agent 研判（~750 行，纯 stdlib）
- `论文降重.py` v2.8：全文直出 5 万字
- `chat_analyzer.py` v2.0 + `doc_assistant.py`

## 上次更新

2026-07-28（OPC Phase 2 部署完成。3 轮调优验证。workflow + Secrets 就绪。Git SOCKS 代理配通。）
