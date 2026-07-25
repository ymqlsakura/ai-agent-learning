# 记忆文件索引

> 按重要度从高到低排列。🔴 = 新会话必须读完才能开口。🟠 = 应该读。🟡 = 有空读。🟢 = 用到时再读。

---

## 🔴 致命级（不读会出事）

- [樱漫清澜·学习者画像](learner-profile.md) — 🔴 她是谁、驱动力工作假设（看清楚+赚钱）、学习障碍、认知演变历史、🆕 2026-07-20 代码素养校准
- [AI 导师教学哲学](teaching-philosophy.md) — 🔴 七条法则（含🆕骨架加零件）、危险信号、绝对不做的（含🆕不用HANDOFF术语）、核心开发流程

## 🟠 重要（每次会话很可能用到）

- [五步分析框架](five-step-framework.md) — 🟠 她的原文前三步（已入库）；第四五步系小樱生成补完版（曾误判丢失，2026-07-17 找回）
- [完整交接提示词](complete-handoff-prompt.md) — 🟠 会话结束时的交接模板：8 维度 + 验证 + 保存转录（2026-07-17 她要求固化第五步）
- [AI 论文检测方法论](ai-paper-detection.md) — 🟠 五步核查法、AI 签名词汇库、引用阶层分化规律（2026-07-19 提炼）
- [论文AI检测市场调研](paper-ai-detection-market-research.md) — 🟠 用户五大痛点+竞品格局+市场空白+产品定位"学术写作辅助工具"（2026-07-21 Serper调研）

## 🟡 中等（了解即可）

- [学习路线](learning-path.md) — 🟡 真实需求驱动的学习路线；三条路径（聊天分析/变现/新工具）
- [主动上下文检索](proactive-context-discovery.md) — 🟡 新会话第一条行动不是说话，是自动搜读全部上下文文件（已通过 BOOT.md 步骤 1 + SessionStart hook 实现；原第八节已随 HANDOFF 瘦身删除）
- [Agent 开发基础·三分材料综合](agent-dev-foundation.md) — 🟡 技术栈优先级 + 6 MCP + 四步闭环，双视角评估（未来70%/当前30%）（2026-07-20）
- [MCP 工具配置备忘](.claude-mcp-setup.md) — 🟠 🆕 Serper 联网搜索+网页读取配置、测试结果、备选方案评估（2026-07-21）
- [Claude Code 技能配置备忘](.claude-skills-setup.md) — 🟠 🆕 agent-browser 浏览器自动化 + 3 战略思维 skill（assumption-audit/strategic-options/war-gaming）+ 选型理由（2026-07-21）

## 🟢 参考（用到时再查）

_（当前无文件归入此级）_

---

## 项目关键文件（非 memory，但新会话必须读）

| 文件 | 重要度 | 说明 |
|------|--------|------|
| [../STATUS.md](../STATUS.md) | 🔴 **最优先** | 🆕 当前状态（≤30 行）——新会话先读这个，再读 QUICKSTART。告诉你上次做到哪了、这次第一件事做什么 |
| [../QUICKSTART.md](../QUICKSTART.md) | 🔴 | 操作指令——环境、怎么跑三个工具、铁律（≤40 行） |
| [../HANDOFF.md](../HANDOFF.md) | 🔴 | 🆕 含接力信号块 + 三振出局规则（2026-07-20）——入口文件。STATUS 不存在或任务已完成时读。按需跳读 |
| [../DECISIONS.md](../DECISIONS.md) | 🔴 **🆕** | 🆕 结构化决策日志（v3.0，2026-07-23 第 36 轮）——每条决策一行：日期+主题+决定+准确表述+我的动作+触发条件。对抗压缩算法扭曲意图。17 活跃+7 历史。SessionStart hook 自动注入 |
| [../.claude/settings.local.json](../../.claude/settings.local.json) | 🔴 | 🆕 SessionStart hook（2026-07-20 配置）——自动注入接力信号 + STATUS。新会话启动即生效，不需要手动读 |
| [../../.mcp.json](../../.mcp.json) | 🔴 | 🆕 MCP 联网工具配置（2026-07-21）——Serper search + scrape。新会话自动加载 |
| [../../.claude/skills/](../../.claude/skills/) | 🔴 | 🆕 Claude Code 技能目录（2026-07-21）——3 战略 skill（assumption-audit/strategic-options/war-gaming）——新会话自动发现 |
| [../PRIORITY-REPORT.md](../PRIORITY-REPORT.md) | 🟡 | 优先级快照（Day 11 生成；会随进度过时） |
| [../session-logs/README.md](../session-logs/README.md) | 🟢 | 原始转录审计流程 |

---

## 工具文件（在 stage-5-document-assistant/）

| 文件 | 重要度 | 说明 |
|------|--------|------|
| `chat_analyzer.py` | 🔴 | 聊天分析器 v2.0（分片处理）——万能代码模板 |
| `论文降重.py` | 🔴 | 🆕 学术写作辅助工具 v2.8——全文直出覆盖 5 万字以下，分片-合并路径已删除。AI率评分+AI指纹诊断+翻译腔检测（6维）+HTML对比报告+引用核查+Word(.docx)/PDF读写。v2.7.1 功能完整：粘贴/剪贴板/文件拖入+API重试+输入验证+输出质量守卫+法律防护。notegpt_baseline.json 含 7 个基准样本+维护检查清单 |
| `论文降重.bat` | 🔴 | 🆕 v2.7 拖拽启动器——支持 .txt/.docx/.pdf，检测到无 Python 时自动降级到 exe |
| `产品单页.html` | 🟠 | 🆕 v2.7 产品介绍单页——可分享链接或本地打开，含效果数据+使用步骤+FAQ |
| `用户测试包/` | 🟠 | 🆕 v2.7 种子用户测试包——exe + .env + 示例论文 + 使用说明，解压即用 |
| `论文分析报告.html` | 🟠 | 🆕 交互式 AI 论文查重分析报告（Day 12）——教学用 |
| `doc_assistant.py` | 🟠 | 文档总结——代码模板 B |
| `file_tools.py` | 🟡 | 被以上工具导入的公共模块（报告中心登记函数已于第 30 轮随三振出局移除） |
| `../images/` | 🟢 | 🆕 图片文件夹——供樱漫清澜导入图片分析（2026-07-21）。⚠️ 注意：当前文件夹名为 `images（picture）/` 含全角括号会导致图片渲染失败（→ 坑 30），建议重命名为纯 ASCII `images/` |
| `../images（picture）/` | 🟢 | 🆕 checkjie 竞品分析材料（2026-07-21）——含 AIGC检测报告 PDF、查重检测报告 PDF、两张 checkjie 界面截图（.doc 文件中的 PNG） |
| `示例聊天_商品图用.txt` | 🟢 | 虚构聊天，闲鱼商品图素材（一次性） |
| `测试论文_AI味.txt` | 🟢 | 🆕 v2.1 测试素材（554字，12种AI指纹）——演示降重效果用 |
| `测试论文_AI味_降重对比报告.html` | 🟢 | 🆕 v2.1 产出样例——可当商品展示 |
| `测试论文_带引用.txt` | 🟢 | 🆕 v2.2 测试素材（8个显式引用，中英混合）——演示引用核查用 |
| `测试论文_带引用_引用核查结果.json` | 🟢 | 🆕 v2.4 引用核查结果示例（5条，4已确认含访问指南/1疑似虚构） |

---

*最后更新：2026-07-23（第 42 轮——HANDOFF 第二轮精修 + CALIBRATE/BOOT 开场修正。memory/ 3文件过期引用已修复。坑 44：CALIBRATE 开场模板制造框架豁免区。三振出局「听新方向」第 2 个周期。零新代码。）*
