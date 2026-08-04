# 日常 D-1 恢复协议

> 小樱的「打开电脑后第一条」——本文件记录樱漫清澜在此会话确认的所有模式和机制。
> **下一会话启动时，此文件覆盖所有其他行为规则。**

---

## 1. 不废话推演

- 开口 = 五步推演（框架透明、自然融入）
- 如果樱漫清澜说「框架呢」→ 立即用框架推演重写全部内容，不解释不道歉

## 2. 自动 Git 同步

```bash
git stash && git pull origin main --rebase && git stash pop && git push origin main
```
- 每次 commit 后自动执行
- 如果 pull 有冲突，立即告诉樱漫清澜具体什么文件冲突了

## 3. 不自动生成无关文件

- 不生成不相关的文件如 `_email_preview.html`、`wf_payload.json`、`_tmp_content.txt`
- 如果生成了，主动清理
- 本地测试 → 用 stdout 看结果，不写文件（sdemail --dry-run 除外，它是只读操作生成预览）

## 4. OPC 日报系统

- 每日早上自动运行，结果发到 `1056174461@qq.com`
- 邮件格式：概要 → 行动建议（含关联情报编号 #X）→ 文章列表（高优先 → 值得关注 → 其他，分数从高到低）
- 每篇文章：GLM 中文摘要 + 标签 + per-model 分数 + 「阅读→」按钮
- 手动触发全链路（合并成一条命令）：
  ```bash
  gh workflow run "Daily Intel Scan" --repo ymqlsakura/ai-agent-learning && \
  sleep 60 && \
  gh workflow run "Daily Intel Review" --repo ymqlsakura/ai-agent-learning
  ```
  注意：两个 workflow 不能合在一起——Scan 是独立的 job，Review 通过 `workflow_run` 触发。
  但 `workflow_run` 有时不触发（GitHub Actions 的已知问题），所以手动跑两步最稳。
- 如果 git push 失败（并发冲突）：workflow 已添加 `git pull --rebase` 自动重试

## 5. 不重复刷版本号

- 封邮件格式迭代是产品问题不是技术问题——用大白话说清楚做了什么改动
- 不要说「v2」「v3」这些版本号，樱漫清澜不关心

## 6. 外部链接不阻塞

- 如果樱漫清澜发了一个链接（B站、网页等），去读它、理解它、把要点用中文告诉她
- 不要因为「这是外部链接」就跳过
- 把链接内容跟当前正在做的事（OPC 日报、赚钱方向、AI 学习）联系起来——如果连不起来，直接说「这个跟当前项目的关系我没想清楚，你先说」
- 如果她说「1」——不是新消息，是同一个会话的延续。她在确认/强调。停下来理解上下文，不从头开始

## 7. 外部内容作为上下文

- 樱漫清澜发来的任何链接（B站、文章、视频）→ **先告诉她内容，再归档**
- 拿到内容 → 立刻用中文告诉她视频/文章讲了什么 → 跟当前项目的关系
- **归档、commit、规则更新全部排在后面**——她不需要等这些
- 这条高于「继续推进当前任务」——她发链接是她觉得内容值得看
- B站视频用 API: `curl "api.bilibili.com/x/web-interface/view?bvid=..."` 拿标题+描述
- WebFetch 被墙就用 WebSearch 找相关讨论
- 都不行就告诉她「访问不了」，问她能不能概括要点
- **VERIFY/git status/git log/TodoWrite/Bash echo/git push 循环禁止**
- 任何「确认状态」的操作（git log / git status / TodoWrite / git push / echo）——如果已经做过一次且结果没变，不要再做第二次
- 拿到结果 → 直接输出。不确认 clean、不检查 TodoWrite、不跑 dry-run
- **做了 10 分钟还没给用户看结果 = 严重 bug**。立即停止、输出已有内容
- **push 不上不要反复试**。VPN 没开就等一下

## 8. 恢复检查

下一会话启动时：
1. 读当前 MOVEMENT.md
2. `git stash && git pull origin main --rebase && git stash pop`
3. 告诉樱漫清澜：自从上次关电脑，跑了什么、发了几封邮件、有没有报错
4. 如果有待确认行动，主动呈现

---

> 创建时间：2026-08-03
> 最后更新：2026-08-04（第 57 轮，21 次提交——日报格式闭环 + 外部链接规则 + 「1」信号 + 记忆加固 + 规则归档）
