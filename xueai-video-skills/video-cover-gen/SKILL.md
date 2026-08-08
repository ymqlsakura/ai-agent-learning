---
name: video-cover-gen
description: >
  生成「学习 AI · 1000 天」系列视频封面 · 横版 4:3 (1600×1200) + 竖版 3:4 (1080×1440) 一键出。
  当用户说「做封面」「生成封面」「day29 封面」「day30 封面」「抖音封面」「视频号封面」「小红书封面」「1000 天封面」时触发。
  改 CONFIG 字段就能套用到下一集（day_number / hook / 标题 / tiles / CTA）· 黑底 + 橙色钩子 + 米白数字的统一品牌风格。
---

# video-cover-gen

> 视频封面批量生成器 · 横竖两版一键出 · 模板化 · 改 CONFIG 即换集

## 触发场景

- 「day30 封面」「day31 封面」每集换数字 + 标题
- 「做封面」「生成封面」「抖音封面」「视频号封面」「小红书封面」
- 已有视频后做封面：先看视频内容（标题 / 关键点 / 12 件事 之类）→ 填进 CONFIG → 跑脚本

## 输出尺寸（抖音规范）

| 版型 | 尺寸 | 比例 | 用途 |
|---|---|---|---|
| 横版 | 1600×1200 | 4:3 | 抖音横屏视频封面 / B站封面 / 视频号横版 |
| 竖版 | 1080×1440 | 3:4 | 抖音竖屏视频封面 / 小红书 / 视频号竖版 |

## 用法（3 步）

### Step 1 · 准备配置 JSON

把这一集的关键信息写到一个 `cover-config.json`：

```json
{
  "out_dir": "D:/video/day30/封面",
  "series_label":  "AI · 1000 DAYS",
  "series_subtag": "学习 AI · 1000 天",
  "day_number":    30,
  "total_days":    1000,
  "date":          "2026·05·06",
  "episode_label": "",
  "hook_main":     "龙虾",
  "hook_sub":      "",
  "title_line1":   "一键安装",
  "title_line2":   "接入微信",
  "tiles": [
    ["01", "下载"],
    ["02", "解压"],
    ["03", "配置"],
    ["04", "启动"],
    ["05", "扫码"],
    ["06", "对话"]
  ],
  "tiles_section_title": "6 步搞定 · 小白也能跑",
  "cta_main": "看完 · 你的微信也有 AI Agent",
  "cta_sub":  "完整教程 + 配置文件 · 粉丝群免费领",
  "horizontal_filename": "cover-横版-1600x1200.png",
  "vertical_filename":   "cover-竖版-1080x1440.png"
}
```

### Step 2 · 跑脚本

```bash
PYTHONIOENCODING=utf-8 PYTHONUTF8=1 python ~/.claude/skills/video-cover-gen/scripts/generate_covers.py --config cover-config.json
```

### Step 3 · 拿图

`out_dir` 下出现 2 张 PNG · 直接传抖音 / 视频号 / 小红书。

## CONFIG 字段说明

详见 [`references/config-fields.md`](references/config-fields.md)。

**最常用的 6 个字段**（每集必改）：

| 字段 | 说明 |
|---|---|
| `day_number` | 第几天（1-1000）· 自动 zfill 3 位显示成 `029` |
| `date` | 发布日期 · 显示成 `2026·05·06` 格式 |
| `hook_main` | 钩子大字（一行）· 如「AI Agent」「Prompt」「龙虾」 |
| `title_line1` / `title_line2` | 主标题双行 · 如「底层原理 / 一口气讲完」 |
| `tiles` | tiles 网格内容 · 列表元素 `[编号, 名字]` · 6-12 个最佳 |
| `cta_main` / `cta_sub` | 底部金句 + 副标 |

**留空跳过的字段**：
- `hook_sub` 留空 = 不画红色横幅
- `episode_label` 留空 = 不画 EP 标识

## 设计风格（不要改的）

- **底色**：BG `#0c0c0e`（近黑）
- **主色**：ACCENT `#ff5a1f`（橙）
- **数字色**：PAPER `#f2e6c3`（米白）
- **字体**：微软雅黑 + 微软雅黑粗体（Windows 自带）
- **角落**：径向橙色光晕（Gaussian blur）

如果要改风格 token，编辑 `scripts/generate_covers.py` 顶部的 `# 设计 token` 块。

## 已知坑位

| 坑 | 解 |
|---|---|
| 中文标题溢出钩子框 | 缩短 `hook_sub` 文字到 8 字以内，或留空跳过 |
| `029` 数字盖到上方副标 | 默认值已调过 · 别动 `make_vertical` 里的 y 坐标 |
| Emoji 显示成 □ | 不用 emoji · PIL 不支持彩色 emoji 渲染 · 用 `01` `02` 编号代替 |
| 字体找不到 | Windows 路径 `C:/Windows/Fonts/msyhbd.ttc` · 其他系统改 `FONT_BOLD` 路径 |

## 相关文件

- [`scripts/generate_covers.py`](scripts/generate_covers.py) — 主脚本（modular · 接收 --config / --out）
- [`references/config-fields.md`](references/config-fields.md) — CONFIG 全字段说明
