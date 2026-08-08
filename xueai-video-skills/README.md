# XueAI 视频 Skills

这是学习 AI 1000 天系列视频方法论的 Git 管理源。工作区实际加载的 Skill 安装在 `D:\video\.codex\skills`。

## 当前 Skills

- `xueai-video-production`：从文案讨论到归档的总控生产流程。自动收集可合法获取的素材，并对缺失的本人真实证据生成阻断式素材申请。成片和可复用动效系统都使用不可覆盖的版本，方便直接观看筛选。
- `check-video-audio`：录音、处理后口播和最终成片的严格音频门禁。
- `check-video-visual-experience`：完整成片的过程覆盖、口播同步和视觉体验门禁。
- `video-cover-gen`：系列封面生成，横版 1600x1200 加竖版 1080x1440，改 config 即换集。
- `thousand-day-opener`：系列固定片头独立渲染，依赖 `D:\video\_系统\remotion-base`。

`produce-xueai-douyin-video` 已迁移为 `xueai-video-production`。旧版本只保留在 Git 历史中，避免两个总控入口产生分叉。

## 作用域

这些 Skill 全部只在 `D:\video` 项目内有意义，因此挂在项目级 Skill 目录，不再放进全局：

- Claude Code 入口：`D:\video\.claude\skills`
- Codex 入口：`D:\video\.codex\skills`

两个入口都用目录联接指向本仓库，改一处两边同时生效。通用能力例如 `video-shotcraft`、
`video-use`、`remotion-*` 仍然留在全局，因为换个项目照样能用。

判断标准只有一条：换一个项目还用不用得上。用得上放全局，用不上放项目。

## 安装约定

先在本仓库完成功能修改和验证，再把对应目录同步到工作区：

```powershell
Copy-Item -LiteralPath "D:\video\xueai-video-skills\xueai-video-production" `
  -Destination "D:\video\.codex\skills" -Recurse -Force

Copy-Item -LiteralPath "D:\video\xueai-video-skills\check-video-visual-experience" `
  -Destination "D:\video\.codex\skills" -Recurse -Force
```

安装后使用技能创建器的 `quick_validate.py` 验证源目录和安装目录。不要直接在安装副本里长期维护改动。

## 代码边界

Skill 只负责流程、判断、模板和门禁。可执行的 Remotion 代码、通用命令、测试和设计原语放在 `D:\video\_系统\remotion-base`，每期素材和产物放在 `D:\video\dayXX`。
