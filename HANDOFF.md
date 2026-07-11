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

### ✅ 阶段性回顾

用户主动追问了两个元认知问题：
1. "你最没把握的事情是什么？" → 讨论了 3 个风险点
2. "最大的遗漏是什么？" → 暴露了 API 费用和安全盲区

---

## 三、当前卡在哪

**没有卡住。** Day 1 顺利完成。但有以下待解决的隐患：

### 🔴 最高优先级：API Key 安全 + 费用控制（Day 2 必须先做）

路线里遗漏了以下内容，**必须在下一次调 API 之前补上**：

1. **还没教用户怎么验证 `.env` 真的被 gitignore 了**
   - 用 `git status` 确认 `.env` 不在 staged files 里
   - 用 `git check-ignore -v .env` 验证规则生效

2. **还没设置 API 费用硬上限**
   - OpenAI：去 platform.openai.com → Billing → Usage limits → 设 $5/月硬上限
   - Anthropic：去 console.anthropic.com → Plans & Billing → 设置 spending limit

3. **还没讲模型选择省钱策略**
   - 练习/测试：用 GPT-4o-mini 或 Claude Haiku（便宜 50 倍）
   - 真正需要质量时：再用 GPT-4o 或 Claude Sonnet

4. **还没建立 push 前自查习惯**
   - 每次 `git push` 前跑 `git diff --staged` 确认没有敏感文件
   - 如果误 push 了 API Key：立刻去 GitHub revoke + 去平台重新生成 key

### 🟡 其他盲区
- 用户不知道 Debug 怎么做（等着遇到 bug 时现场教）
- 没有推荐学习社群（12 周一个人学可能孤独）
- Windows 编码问题会反复出现（已修复一次 GBK/UTF-8 问题）

---

## 四、下一步计划（Day 2 — 2026-07-12）

### 第一优先级（30 分钟）：API 安全补课
1. 帮用户注册 OpenAI 账号 + 设置 $5 硬上限
2. 帮用户生成第一个 API Key
3. 创建 `.env` 文件，写入 key
4. 验证 `.env` 被 gitignore 保护
5. 教 `git diff --staged` 自查习惯

### 第二优先级（2 小时）：命令行基础
1. 终端导航：`cd`、`ls`、`pwd`、`mkdir`
2. 文件操作：创建、复制、移动文件
3. `pip install` 实战：安装第一个第三方库（建议用 `requests`）
4. 练习：完全在终端里创建并运行一个简单的 Python 文件

### 可以考虑的延续
- 如果用户精力好，可以继续讲虚拟环境（`python -m venv`）
- 或者让用户自由探索，用 pip 装几个有趣的库玩玩

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

---

## 六、关键文件索引

| 文件 | 路径 | 说明 |
|------|------|------|
| 学习路线 | `C:\Users\a\.claude\plans\ai-agent-giggly-narwhal.md` | 12 周完整路线 |
| hello.py | `C:\Users\a\ai-agent-learning\stage-0-hello-world\hello.py` | 第一个程序 |
| .gitignore | `C:\Users\a\ai-agent-learning\stage-0-hello-world\.gitignore` | 已配置好 Python/venv/.env 忽略 |
| README.md | `C:\Users\a\ai-agent-learning\stage-0-hello-world\README.md` | 项目说明 |
| GitHub 仓库 | https://github.com/ymqlsakura/ai-agent-learning | 远程仓库 |

---

## 七、与新会话打招呼

> 用户下次进入 Claude Code，会在 `C:\Users\a\ai-agent-learning\` 目录下。可以这样开始：
>
> **"欢迎回来，樱漫清澜！上次我们完成了 Day 1——你的第一个 Python 程序已经跑通，GitHub 仓库也推送好了。今天按计划是 Day 2：先花 30 分钟把 API 费用和安全配置好，然后学命令行基础。你准备好了吗？"**

---

## 八、与用户沟通的风格备忘

- 用户是中文母语，全部用中文交流
- 用户会主动问元认知问题（"你最没把握的是什么"、"最大的遗漏是什么"），说明注重理解和风险意识
- 不要用术语吓人，每次引入新概念要解释"为什么需要学这个"
- 鼓励为主，但诚实指出问题
- 用户喜欢"本地搞定"的方式，不喜欢在浏览器里点点点
- 用户 GitHub 用户名是 ymqlsakura（可能是"樱漫清澜"的缩写拼法）

---

*下次会话开始时，第一件事是把这个文件读一遍。*
