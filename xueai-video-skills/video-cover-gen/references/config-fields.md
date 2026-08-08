# CONFIG 全字段说明

## 必填字段

| 字段 | 类型 | 示例 | 说明 |
|---|---|---|---|
| `series_label` | str | `"AI · 1000 DAYS"` | 顶部识别带文字（系列英文标） |
| `series_subtag` | str | `"学习 AI · 1000 天"` | 副标（中文 · 顶部副标 + 计数器小标） |
| `day_number` | int | `29` | 第几天 1-1000 · 自动 zfill 3 位（029） |
| `total_days` | int | `1000` | 系列总天数 · 显示 `/1000` |
| `date` | str | `"2026·04·28"` | 发布日期（点分隔） |
| `hook_main` | str | `"AI Agent"` | 钩子大字（巨字 · 60-130px） |
| `title_line1` | str | `"底层原理"` | 主标题第一行（米白 · 大） |
| `title_line2` | str | `"一口气讲完"` | 主标题第二行（白 · 略小） |
| `tiles` | list | `[["01","messages"], ...]` | tiles 网格 · 每项 `[编号, 名字]` · 6-12 个 |
| `cta_main` | str | `"看完 · Agent 在你眼里再没黑盒"` | 底部金句（白色加粗） |
| `cta_sub` | str | `"完整代码 + 笔记 · 粉丝群免费领"` | 副标（灰色） |

## 可选字段（留空跳过）

| 字段 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `hook_sub` | str | `""` | 红色钩子横幅文字 · 留空 = 不画 |
| `episode_label` | str | `""` | EP.XX 标识 · 留空 = 不画 |
| `tiles_section_title` | str | `""` | tiles 上方小标 · 如「12 个原理 · 一个不少」 |

## 输出控制

| 字段 | 默认 | 说明 |
|---|---|---|
| `out_dir` | `"."` | 输出目录（也可命令行 `--out` 覆盖） |
| `horizontal_filename` | `cover-横版-1600x1200.png` | 横版文件名 |
| `vertical_filename` | `cover-竖版-1080x1440.png` | 竖版文件名 |

## 字段长度建议

| 字段 | 建议长度 |
|---|---|
| `hook_main` | 2-6 字（再多会换行/超出） |
| `hook_sub` | 6-10 字（横幅高度固定） |
| `title_line1` / `title_line2` | 4-6 字 / 行 |
| `cta_main` | 12-16 字 |
| `cta_sub` | 14-20 字 |
| tiles 项 `name` | 2-8 字（单 tile 宽 290 / 200px） |

## 命令行参数

```bash
# 标准用法
python generate_covers.py --config cover-config.json

# 覆盖输出目录
python generate_covers.py --config cover-config.json --out D:/video/day30/封面

# 只出横版
python generate_covers.py --config cover-config.json --horizontal-only

# 只出竖版
python generate_covers.py --config cover-config.json --vertical-only
```

## 配置示例（Day29 实际用过的）

```json
{
  "out_dir": "D:/video/day29/封面",
  "series_label":  "AI · 1000 DAYS",
  "series_subtag": "学习 AI · 1000 天",
  "day_number":    29,
  "total_days":    1000,
  "date":          "2026·04·28",
  "episode_label": "",
  "hook_main":     "AI Agent",
  "hook_sub":      "",
  "title_line1":   "底层原理",
  "title_line2":   "一口气讲完",
  "tiles": [
    ["01", "messages"],
    ["02", "上下文"],
    ["03", "system"],
    ["04", "思维链"],
    ["05", "Few-Shot"],
    ["06", "预填充"],
    ["07", "停止序列"],
    ["08", "Tool Use"],
    ["09", "RAG"],
    ["10", "ReAct"],
    ["11", "幻觉"],
    ["12", "Multi-Agent"]
  ],
  "tiles_section_title": "12 个原理 · 一个不少",
  "cta_main": "看完 · Agent 在你眼里再没黑盒",
  "cta_sub":  "完整代码 + 笔记 + 图解 · 粉丝群免费领"
}
```
