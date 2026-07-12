# Push 前检查清单

每次执行 `git push` 之前，逐条确认：

- [ ] `git status` — 有没有不该提交的文件？
- [ ] `git diff --staged` — 具体改了哪些内容？有没有 API Key、密码、个人信息？
- [ ] `git check-ignore -v .env` — .env 确认被保护？
- [ ] 如果有任何不确定的文件，先问导师再 push
