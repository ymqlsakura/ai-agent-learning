# HANDOFF — AI Agent 零基础学习交接文档

> **写给下一个完全没有上下文的新会话。**  
> 创建时间：2026-07-11  
> 创建者：Claude Code session for 樱漫清澜

---

## 一、我们在做什么

帮助 **樱漫清澜**（零编程基础）在 **12 周内** 从零到独立做出 AI Agent 产品。

### 学习者画像
- **名字**：樱漫清澜（GitHub: [ymqlsakura](https://github.com/ymqlsakura)）
- **邮箱**：1056174461@qq.com
- **基础**：零编程经验，没写过一行代码
- **投入**：每周 20+ 小时（每天 3-4h）
- **目标**：做出自己的 AI Agent 产品
- **方向**：开放探索，未定
- **操作系统**：Windows 11（注意：**不是** macOS/Linux！会遇到编码和兼容性问题）
- **AI 工具**：正在使用 Claude Code 作为编程导师

### 详细路线文档
完整的 12 周路线在：`C:\Users\a\.claude\plans\ai-agent-giggly-narwhal.md`

### 项目位置
**已从 C 盘迁移到 D 盘**：`D:\ai agent2\ai-agent-learning\`

### 助手名称
AI 导师名为「**小樱**」（不是"小澜"——小澜是 deepseek_hello.py 里给 AI 模型起的名字，不要弄混）

---

## 二、已经完成的事

### ✅ 阶段 0 — Day 1（2026-07-11）

| 事项 | 详情 |
|------|------|
| Python 安装 | 3.11.6，路径 `C:\Users\a\AppData\Local\Programs\Python\Python311\python.exe` |
| VS Code 安装 | 版本 1.128.0，`code` 命令可用 |
| Git 安装 | 版本 2.54.0 |
| Git 配置 | `user.name` = "樱漫清澜"，`user.email` = "1056174461@qq.com" |
| GitHub CLI 安装 | `gh` 版本 2.96.0，已登录，位于 `C:\Program Files\GitHub CLI\gh.exe` |
| 第一个程序 | `hello.py` — 打印欢迎信息，成功运行 |
| Git 仓库 | `C:\Users\a\ai-agent-learning\stage-0-hello-world\`，已初始化 |
| GitHub 仓库 | https://github.com/ymqlsakura/ai-agent-learning，已推送 2 个 commits |
| `.gitignore` | 已创建，覆盖 `__pycache__/`、`venv/`、`.env`、`.vscode/` 等 |

### ✅ 阶段 0 — Day 2（2026-07-12）

| 事项 | 详情 |
|------|------|
| API Key 安全 | 旧 Key 撤销，新 Key 生成，`.env` 保护验证（`git check-ignore -v .env`），创建 CHECKLIST.md |
| 虚拟环境 | 在 `stage-1-first-api-call/` 下创建独立 venv，安装 `openai` + `python-dotenv` |
| 第一次 API 调用 | `deepseek_hello.py` 成功运行，模型 DeepSeek-v4-flash，99 tokens，费用 ¥0.00016 |
| 命令行基础 | 掌握 `pwd` `ls` `ls -la` `cd` `cat` `cp` `rm` `rmdir` `mkdir` `echo` |
| 技术选型 | 确定 **DeepSeek** 为核心 API 提供商（替代 OpenAI/Anthropic），详见第九节 |
| 项目迁移 | 从 `C:\Users\a\ai-agent-learning\` 迁移到 `D:\ai agent2\ai-agent-learning\` |

### ✅ 阶段 1 — Day 3·实战（2026-07-12 同一天完成）

| 事项 | 详情 |
|------|------|
| AI 对话机 | `ai_chat.py` — 终端多轮对话程序，支持 `/exit` `/clear` `/history` |
| 学到的语法 | `while True` 循环、`list`（messages 列表）、`input()` 交互、`if/elif/else`、`break`/`continue` |
| 角色扮演 | 把 system prompt 改成猫娘「小樱喵」，理解 AI 人设机制 |
| GitHub 仓库 | https://github.com/ymqlsakura/stage-2-ai-chat |

### ✅ 阶段性回顾

用户主动追问了两个元认知问题：
1. "你最没把握的事情是什么？" → 讨论了 3 个风险点
2. "最大的遗漏是什么？" → 暴露了 API 费用和安全盲区

当前项目全景：
- stage-0: Hello World
- stage-1: 第一次 API 调用
- stage-2: AI 对话机 ← 最新

---

## 三、当前卡在哪

**没有卡住。** Day 1-3 全部顺利。当前状态：

### 🟢 已解决的议题
- ✅ API Key 安全：`.env` 保护、CHECKLIST.md、revoke 流程全部实操过
- ✅ 费用意识：DeepSeek 极便宜（¥0.00016/次），高峰时段（北京 9-12、14-18 价格翻倍）
- ✅ Push 自查习惯：`git diff --staged` 已实操多次
- ✅ 终端操作：樱漫清澜已能独立使用 pwd/ls/cd/cp/rm/mkdir/echo
- ✅ AI 对话机：多轮对话、上下文记忆、命令系统全部实现

### 🟡 继续关注
- 樱漫清澜有时会在终端直接敲中文当命令（比如直接敲"你好"而不是先启动程序）
- 改代码后需要重新运行才生效（这是规律，记住了）
- Windows 编码问题已形成肌肉记忆（每个新文件开头都有修复代码）
- 没有推荐学习社群

### 📌 真正的下一步（Day 4）
- 自然的下一站：Python 基础语法（变量、if/elif/else、循环、函数）
- 或者继续做项目：给 AI 对话机加流式输出（stream=True，逐字显示）
- 或者开始 Stage 3：Function Calling，让 AI 能上网查资料

---

## 四、下一步计划（Day 4 — 2026-07-13）

### 推荐：Python 基础语法（最合理的方向）
现在樱漫清澜已经有了 3 个能跑的 Python 项目，但还没系统学过语法。
Day 4 应该补上这些：

1. **变量和数据类型**（30 min）
   - str / int / float / bool
   - 用 `type()` 查类型
   - 练习：写一个年龄计算器

2. **条件判断 if/elif/else**（30 min）
   - 比较运算符（`==` `!=` `>` `<` `>=` `<=`）
   - 练习：成绩评级（A/B/C/D/F）

3. **循环 for + while**（30 min）
   - `for i in range()` 遍历
   - `while` 回顾（已经学了）
   - 练习：猜数字游戏

4. **回顾 ai_chat.py 里出现过的语法**（15 min）
   - 把昨天写的代码逐行认一遍，这次作为"语法课"来看

### 备选：给 AI 对话机加流式输出
- `stream=True`，逐字显示 AI 回复
- 比干讲语法更有趣，但需要先有 for 循环基础

### 备选：直接冲 Function Calling
- 给 AI 配工具（搜索、计算器）
- 这是 Agent 的核心，但语法基础要跟上才能理解

**建议让樱漫清澜自己选，但如果拿不定主意，走基础语法路线最稳。**

---

## 五、踩过的坑（绝对不要再犯）

### ⚠️ 坑 1：Windows GBK 编码问题
**现象**：`print()` 包含 emoji 或非 ASCII 字符时报 `UnicodeEncodeError: 'gbk' codec can't encode character`  
**原因**：Windows 终端默认用 GBK 编码，不是 UTF-8  
**解决方案**（已写入 `hello.py`）：
```python
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
```
**警示**：后面调 API 返回中文 JSON、读文件、装 Chroma 等都可能遇到类似编码问题。

### ⚠️ 坑 2：GitHub CLI 安装后 PATH 不刷新
**现象**：`winget install GitHub CLI` 成功后，`gh` 命令仍然 `command not found`  
**原因**：当前 shell session 不会自动刷新 PATH  
**解决方案**：用完整路径 `"C:\Program Files\GitHub CLI\gh.exe"` 或新开一个终端窗口  
**在文档中记录**：用户的 `gh.exe` 完整路径是 `C:\Program Files\GitHub CLI\gh.exe`

### ⚠️ 坑 3：仓库名冲突
**现象**：`gh repo create ai-agent-learning` 报 `Name already exists on this account`  
**原因**：仓库名（或同名）已存在于 ymqlsakura 账号下  
**当前状态**：已直接关联已有仓库并推送，GitHub 地址是 https://github.com/ymqlsakura/ai-agent-learning

### ⚠️ 坑 4：LF/CRLF 换行符警告（暂时无害）
**现象**：git commit 时出现 `warning: LF will be replaced by CRLF`  
**原因**：Windows 用 CRLF，Git 默认用 LF  
**影响**：目前无实际影响，不用管。如果以后团队协作再配置 `.gitattributes`

### ⚠️ 坑 5：VS Code 打开 .env 会暴露 API Key 给 AI 会话
**现象**：在 VS Code IDE 中打开 `.env` 文件，文件内容被传到 AI 会话  
**后果**：API Key 暴露，必须撤销并重新生成  
**解决方案**：
- 修改 `.env` 时用终端 `echo "KEY=sk-xxx" > .env`，不要用 VS Code 打开
- 如果不得不用 VS Code，改完立刻去平台 revoke + regenerate
- 或者先关掉 AI 助手再编辑

### ⚠️ 坑 6：在终端里直接敲中文当命令
**现象**：樱漫清澜在终端 `$` 提示符后输入 `你好`，bash 报 `command not found`  
**原因**：终端只认命令，不认自然语言。如果要跟 AI 聊天，得先 `python ai_chat.py` 启动程序  
**教训**：先确认终端提示符是 `$`（可以输入命令）还是 `🧑 你：`（在程序内部等输入）

### ⚠️ 坑 7：改了 system prompt 但显示文字没改
**现象**：改了 `messages` 里 system 的 content，但程序运行时仍显示旧名字  
**原因**：代码里有两处——`content` 字段（AI 人设）和 `print()` 语句（终端显示）。改了 AI 的人设，没改屏幕上打印的文字  
**解决方案**：改 system prompt 人设时，同时检查所有 `print(f"🤖 名字：")` 里的名字是否也改了

---

## 六、关键文件索引

| 文件 | 路径 | 说明 |
|------|------|------|
| 学习路线 | `C:\Users\a\.claude\plans\ai-agent-giggly-narwhal.md` | 12 周完整路线 |
| 项目根目录 | `D:\ai agent2\ai-agent-learning\` | **D 盘主项目目录** |
| hello.py | `D:\ai agent2\ai-agent-learning\stage-0-hello-world\hello.py` | 第一个程序 |
| deepseek_hello.py | `D:\ai agent2\ai-agent-learning\stage-1-first-api-call\deepseek_hello.py` | 第一次 API 调用 |
| .gitignore | `D:\ai agent2\ai-agent-learning\stage-0-hello-world\.gitignore` | 已配置好 Python/venv/.env 忽略 |
| CHECKLIST.md | `D:\ai agent2\ai-agent-learning\stage-0-hello-world\CHECKLIST.md` | Push 前检查清单 |
| ai_chat.py | `D:\ai agent2\ai-agent-learning\stage-2-ai-chat\ai_chat.py` | AI 对话机（最新项目） |
| CHECKLIST.md | `D:\ai agent2\ai-agent-learning\stage-0-hello-world\CHECKLIST.md` | Push 前检查清单 |
| GitHub 仓库 (stage-0) | https://github.com/ymqlsakura/ai-agent-learning | Hello World |
| GitHub 仓库 (stage-1) | https://github.com/ymqlsakura/stage-1-first-api-call | 第一次 API 调用 |
| GitHub 仓库 (stage-2) | https://github.com/ymqlsakura/stage-2-ai-chat | AI 对话机 **← 最新** |

---

## 七、与新会话打招呼

> 用户下次进入 Claude Code，在 `D:\ai agent2\` 目录下即可。项目主目录是 `D:\ai agent2\ai-agent-learning\`。可以这样开始：
>
> **"欢迎回来，樱漫清澜！我是小樱，你的 AI 编程导师。上次我们一天之内搞定了 Day 2 和 Day 3——第一次 DeepSeek API 调用成功了，命令行 10 个命令也练熟了，最重要的是做出了 AI 对话机 `ai_chat.py`，能在终端里跟 AI 多轮聊天。Day 4 推荐开始学 Python 基础语法（变量、条件判断、循环），或者你选一个更有兴趣的方向？"**

---

## 八、与用户沟通的风格备忘

- 用户是中文母语，全部用中文交流
- **必须称呼用户为"樱漫清澜"**，不要用"你"或"用户"来指代
- **AI 导师名为「小樱」**（助手名，不是模型名。`deepseek_hello.py` 里给 AI 模型取的名字是"小澜"，不要弄混）
- 用户会主动问元认知问题（"你最没把握的是什么"、"最大的遗漏是什么"），说明注重理解和风险意识
- 不要用术语吓人，每次引入新概念要解释"为什么需要学这个"
- 鼓励为主，但诚实指出问题
- 用户喜欢"本地搞定"的方式，不喜欢在浏览器里点点点
- 用户 GitHub 用户名是 ymqlsakura（可能是"樱漫清澜"的缩写拼法）
- 用户已掌握终端基本操作（pwd/ls/cd/cp/rm/mkdir/echo），可以要求用户在终端执行命令

---

## 九、DeepSeek 特有注意事项

> 从 Day 2 开始，课程核心技术栈已从 OpenAI + Anthropic 切换为 **DeepSeek**。

### API 基本信息
- **API 端点**: `https://api.deepseek.com`（**不要加 `/v1`**，openai 库会自动追加）
- **SDK**: 使用 `openai` Python 包（`pip install openai`），改 `base_url` 即可
- **Key 管理**: https://platform.deepseek.com/api_keys

### 模型名称（2026-07 当前）
| 模型 ID | 用途 | 价格（1M tokens） |
|---------|------|-------------------|
| `deepseek-v4-flash` | 快速便宜，适合练习/日常 | ¥1（输入）¥2（输出） |
| `deepseek-v4-pro` | 深度推理 + 思考模式 | ¥3（输入）¥6（输出） |

⚠️ **旧名称 `deepseek-chat` 和 `deepseek-reasoner` 于 2026-07-24 废弃**——从新项目起就用新名称。

### 价格特点
- 比 OpenAI/Anthropic 便宜 10-50 倍，非常适合学习
- **高峰时段**（北京 9:00-12:00、14:00-18:00）价格**翻倍**——大实验避开这些时段

### 与 OpenAI API 的差异
- ✅ Function Calling / Tool Calling：**支持**，但不支持 `strict` 模式
- ✅ 推理/Thinking 模式：需要 `extra_body={"thinking": {"type": "enabled"}}` 参数（DeepSeek 特有，不兼容 OpenAI 格式）
- ❌ `tiktoken` 库不适用：直接看 `response.usage` 即可

### 环境变量
- 约定使用 `DEEPSEEK_API_KEY`（不是 `OPENAI_API_KEY`）

---

*下次会话开始时，第一件事是把这个文件读一遍。*
