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
- 本地测试 → 用 stdout 看结果，不写文件

## 4. OPC 日报系统

- 每日早上自动运行，结果发到 `1056174461@qq.com`
- 邮件格式：概要 → 行动建议（含关联情报编号 #X）→ 文章列表（高优先 → 值得关注 → 其他，分数从高到低）
- 每篇文章：GLM 中文摘要 + 标签 + 分数 + 「阅读→」按钮
- 手动触发：`gh workflow run "Daily Intel Review" --repo ymqlsakura/ai-agent-learning`

## 5. 恢复检查

下一会话启动时：
1. 读当前 MOVEMENT.md
2. `git stash && git pull origin main --rebase && git stash pop`
3. 告诉樱漫清澜：自从上次关电脑，跑了什么、发了几封邮件、有没有报错
4. 如果有待确认行动，主动呈现

---

> 创建时间：2026-08-03
> 本会话产出：OPC 日报邮件系统端到端闭环（GLM 中文摘要 + 关联情报 + 阅读链接）
