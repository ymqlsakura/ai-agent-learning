---
name: thousand-day-opener
description: >
  渲染「学习 AI · 1000 天 · Day XXX · 今天学 XXX」开场片段（5 秒视频或单帧 PNG）。
  基于本地 Remotion 项目 D:/video/_系统/remotion-base 的 Opener01_SeriesCounter 组件。
  当用户说「1000 天 opener」「计数开场」「片头」「day29 片头」「day30 片头」「opener 片段」「学习 AI 开场」时触发。
  输出可用作每集视频开头嵌入剪映 / Remotion / Final Cut · 也能渲单帧 PNG 当做封面用。
---

# thousand-day-opener

> 「学习 AI · 1000 天 · Day XXX · 今天学 XXX」5 秒开场片段独立渲染器
> 基于 Remotion · 复用现有 `Opener01_SeriesCounter` 组件

## 触发场景

- 「day30 片头」「day31 opener」每集换数字 + 主题
- 「单独渲一段开场」不想渲整片
- 「截一帧 1000 天计数器图」做封面
- 「学习 AI 1000 天 开场视频」

## 输出

- **视频**：mp4 · 1920×1080 @ 30fps · **5 秒**（150 帧）
- **单帧**：PNG · 1920×1080 · 任意指定帧（默认中间帧 75）

## 前置要求

本机要有 Remotion 项目（默认路径 `D:/video/_系统/remotion-base`）· 已经装好 Node 22+ 和依赖。

如果路径不一样，改 `scripts/render_opener.py` 顶部的 `REMOTION_DIR`。

## 用法（一键命令）

### 渲染 5 秒视频

```bash
python ~/.claude/skills/thousand-day-opener/scripts/render_opener.py \
    --day 30 \
    --topic "今天学：龙虾接微信" \
    --date "2026·05·06" \
    --out D:/video/day30/opener.mp4
```

### 渲染单帧 PNG（默认第 75 帧 · 数字+标题完全显示）

```bash
python ~/.claude/skills/thousand-day-opener/scripts/render_opener.py \
    --day 30 \
    --topic "今天学：龙虾接微信" \
    --date "2026·05·06" \
    --still \
    --out D:/video/day30/opener.png
```

## 参数（命令行）

| 参数 | 必填 | 说明 |
|---|---|---|
| `--day N` | ✓ | 第几天 1-1000 · 视频里显示成 `029` |
| `--topic "今天学：xxx"` | ✓ | 副标题 · 一句话讲这集学啥 |
| `--date "YYYY·MM·DD"` |  | 日期点分隔 · 默认今天 |
| `--total-days 1000` |  | 系列总天数 · 默认 1000 |
| `--episode-label ""` |  | EP.XX 标识 · 默认空（已无 EP 概念） |
| `--still` |  | 渲单帧 PNG 而不是视频 |
| `--frame N` |  | `--still` 时指定第 N 帧 · 默认 75 |
| `--out PATH` | ✓ | 输出文件路径（.mp4 或 .png） |
| `--remotion-dir PATH` |  | Remotion 项目路径 · 默认 `D:/video/_系统/remotion-base` |

## 常见用法

### 把片头嵌进剪映

视频拍好后剪映里：先放 `opener.mp4`（5 秒）→ 然后接你的主体录制内容。

### 用作封面（PNG）

```bash
python .../render_opener.py --day 30 --topic "..." --still --frame 90 --out cover.png
```

第 90 帧时数字+主题都站定了，适合做静态封面。

### 一次出本期 opener + 下期预告（2 个）

写 shell loop：

```bash
for day in 30 31; do
    python .../render_opener.py --day $day --topic "..." --out day$day-opener.mp4
done
```

## 如何调样式

样式都在 Remotion 项目的 `src/openers/Opener01_SeriesCounter.tsx` 里：

- 字号：搜索 `fontSize`
- 颜色：`src/theme/colors.ts`
- 时长（默认 5 秒 = 150 帧）：改 `Root.tsx` 里 `durationInFrames={150}`

## 已知坑位

| 坑 | 解 |
|---|---|
| `cd: ... no such directory` | 路径含中文 + Git Bash · 在 PowerShell 跑 · 或用绝对路径 |
| 渲染失败 sfx 404 | Opener 不依赖 sfx · 跟整片渲染那个坑无关 |
| 字体显示成方框 | Remotion 项目要装 SimHei / 微软雅黑 · 检查 `src/theme/typography.ts` |
| `--out` 父目录不存在 | 脚本会自动创建 · 不用手工 mkdir |

## 相关文件

- [`scripts/render_opener.py`](scripts/render_opener.py) — 主调用脚本（包装 npx remotion render/still）
- [`references/composition-id.md`](references/composition-id.md) — Remotion Composition 注册说明
