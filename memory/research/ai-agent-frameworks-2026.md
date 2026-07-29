# AI 代理框架选型参考 — 2026

> 来源：[Top AI Agent Frameworks in 2026: A Production-Ready Comparison](https://pub.towardsai.net/top-ai-agent-frameworks-in-2026-a-production-ready-comparison-7ba5e39ad56d)（Pratik K Rupareliya, Towards AI, 2026-07-17）
> 行动 #1 产出 | 2026-07-29

## 核心结论

**框架选择只占生产成功因素的 20%。** 另外 80%：检索质量、工具定义清晰度、失败处理、部署前评估、成本监控。

**最重要的选择标准**：故障容忍度 → 可观测性需求 → 团队调试能力。

## 8 个框架速览

| 框架 | 定位 | 最适合 | 关键风险 |
|------|------|--------|---------|
| **LangGraph** | 生产标准 | 合规/金融/医疗，需审计追踪 | 学习曲线陡，简单场景杀鸡用牛刀 |
| **CrewAI** | 最快出 demo | 内容生成/研究/分析，3 天出原型 | 生产约束紧时可能需要 LangGraph 重写 |
| **AutoGen 2.0** | 企业异步引擎 | Azure 生态，代码生成+审查，高并发 | 对话循环 token 消耗不可预测（10× 超支） |
| **OpenAI Agents SDK** | GPT 原生 | 已用 OpenAI API 的团队，简单 agent 场景 | 模型锁定——换模型迁移成本高 |
| **Anthropic Agent SDK** | 准确性优先 | 安全关键决策、代码 agent、复杂推理 | token 成本高，社区比 LangGraph 小 |
| **Google ADK** | 多模态原生 | 图像/视频/文档+文本混合场景 | GCP 锁定，文本场景不如 LangGraph 灵活 |
| **LlamaIndex Workflows** | RAG 专家 | 大规模文档检索+推理 | 编排能力不如 LangGraph，非 RAG 场景弱 |
| **Intuz（托管）** | 全托管企业级 | 无 ML 团队但需要生产级 agent | 供应商锁定，灵活性不如开源 |

## 生产中最有效的混用模式

```
CrewAI（研究/分析） → LangGraph（执行/合规审查）
LlamaIndex（检索） → LangGraph（编排/人工审核）
```

**教训**：不要忠诚于单一框架。生产系统通常用 2-3 个框架，各管最擅长的层。

## 与我们（OPC）的关系

| 框架 | OPC 适用性 |
|------|-----------|
| **Anthropic Agent SDK** | ✅ 已在用——Claude Code 就是基于它的。MCP 生态是我们工具集成的基础设施 |
| **LangGraph** | 🟡 当前不需要——supervisor.py 是单层 Python 脚本，还没到需要图编排的复杂度 |
| **CrewAI** | 🟡 不需要——但它的「角色分工」思路和我们的 4 Worker 架构同构 |
| **LlamaIndex** | ❌ 不需要——我们不处理大规模文档检索 |

**当前状态**：supervisor.py 的单层架构够用。何时升级到 LangGraph：当 agent 流程需要合规检查点、人工审核节点、或跨会话状态持久化时。

## 五个 2026 趋势

1. **图编排是收敛点**——所有框架都在向图基状态管理靠拢
2. **MCP 成为工具集成标准**——Anthropic 主导，Linux Foundation 治理，50+ 企业支持
3. **多 agent 专业化替代单一大 agent**——检索 agent + 分析 agent + 执行 agent + 轻量协调器
4. **成本优化成为选型标准**——推理占 AI 云支出 55%，agent 循环单任务 10-20 次 LLM 调用
5. **托管 vs 开源分化**——有 ML 团队的用 LangGraph，没有的选托管平台。中间地带是 95% 失败率的来源

## 决策建议

**目前不换框架。** supervisor.py + 4 Worker 架构匹配当前需求。当以下信号出现时重新评估：
- 需要人工审核节点（合规/发布前检查）
- 单次研判成本超过 $0.05
- Worker 协调逻辑复杂到需要显式状态图
- 需要跨会话持久化 agent 状态
