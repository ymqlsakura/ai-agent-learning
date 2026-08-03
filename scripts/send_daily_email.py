"""邮件发送脚本 v2——日报格式重写。

每条文章生成中文摘要（标题翻译 + 标签说明 + 一句话概要），
按分数从高到低排列。行动建议放顶部，标注基于哪几条情报。
"""

import smtplib
import sys
import os
import re
import json
from datetime import datetime, timezone, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

TZ = timezone(timedelta(hours=8))
INTEL_DIR = Path("memory/intel")
REPO_URL = "https://github.com/ymqlsakura/ai-agent-learning/blob/main"
DRY_RUN = "--dry-run" in sys.argv

today = datetime.now(TZ).strftime("%Y-%m-%d")

daily_path = INTEL_DIR / f"daily-{today}.md"
actions_path = INTEL_DIR / f"actions-{today}.md"
json_path = INTEL_DIR / f"daily-{today}.json"

if not daily_path.exists():
    print(f"[x] 日报不存在: {daily_path}")
    sys.exit(0)

raw = daily_path.read_text(encoding="utf-8")

# ── 1. 解析文章（标题 + 链接 + 摘要 + 标签）──
articles = {}
article_blocks = re.split(r'\n(?=### \d+\.\s)', raw)
for block in article_blocks:
    m = re.match(r'### (\d+)\.\s+\[(.+?)\]\((.+?)\)', block)
    if not m:
        continue
    num = int(m.group(1))
    title_en = m.group(2).strip()
    link = m.group(3).strip()
    # 提取英文 snippet
    snippet_en = ""
    sm = re.search(r'\n\n(.+?)\n\n\s*-', block, re.DOTALL)
    if sm:
        snippet_en = sm.group(1).strip()[:300]
    tags = re.findall(r'标签:\s*(.+)', block)
    tag_str = tags[0].strip() if tags else ""
    # 提取关键词
    kw = re.findall(r'关键词:\s*`(.+?)`', block)
    kw_str = kw[0] if kw else ""
    articles[num] = {
        "title_en": title_en,
        "link": link,
        "snippet_en": snippet_en,
        "tags": tag_str,
        "keywords": kw_str,
    }

# ── 2. 解析研判表格 ──
scored = []
table_start = raw.find("| # |")
if table_start >= 0:
    for line in raw[table_start:].split("\n"):
        if not line.startswith("|") or "---" in line:
            continue
        cells = [c.strip() for c in line.split("|") if c.strip()]
        if len(cells) < 6:
            continue
        if cells[0] in ("#", "编号"):
            continue
        if "相关性" in str(cells):
            continue
        try:
            num = int(cells[0])
        except ValueError:
            continue
        try:
            total = int(cells[4])
        except ValueError:
            total = 0
        scored.append({
            "num": num,
            "relevance": cells[1],
            "feasibility": cells[2],
            "leverage": cells[3],
            "total": total,
            "action_raw": cells[5],
        })

# 按总分从高到低
scored.sort(key=lambda s: s["total"], reverse=True)

# ── 3. 读取 JSON per-worker 分数 ──
worker_scores = {}
if json_path.exists():
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
        for s in data.get("scores", []):
            num = s.get("num") or s.get("#")
            if num:
                worker_scores[num] = s.get("worker_scores", {})
    except Exception:
        pass

# ── 4. 解析行动建议，提取关联情报编号 ──
action_items = []
if actions_path.exists():
    actions_raw = actions_path.read_text(encoding="utf-8")
    # 提取每个行动块
    act_blocks = re.split(r'\n(?=### 行动 \d+)', actions_raw)
    for block in act_blocks:
        title_m = re.match(r'### 行动 \d+：(.+)', block)
        if not title_m:
            continue
        title = title_m.group(1).strip()
        # 提取「做什么」
        what_m = re.search(r'\*\*做什么\*\*：(.+)', block)
        what = what_m.group(1).strip() if what_m else title
        # 提取关联情报
        refs = re.findall(r'#(\d+)', block)
        ref_nums = [int(r) for r in refs if r.isdigit()]
        action_items.append({
            "title": title,
            "what": what,
            "refs": ref_nums,
        })

# ── 5. 为每篇文章生成中文摘要行 ──
def make_chinese_summary(num: int, art: dict, s: dict) -> str:
    """根据文章标题、标签、摘要生成一条中文描述。"""
    title = art.get("title_en", "")
    snippet = art.get("snippet_en", "")
    tags = art.get("tags", "")
    action = s.get("action_raw", "")

    # 清理 action 中的内部标记
    action_clean = re.sub(r'\[.*?\]', '', action).strip()

    # 基于标签和标题做关键词映射，生成一个中文概要
    # 核心逻辑：tag 说明领域 + snippet 前几个词说明内容
    tag_cn_map = {
        "OPC": "一人公司",
        "AI-agent": "AI Agent",
        "Claude": "Claude",
        "new-tool": "新工具",
    }

    # 翻译标签
    cn_tags = []
    for t in tags.replace("#", "").split():
        t = t.strip()
        if t:
            cn_tags.append(tag_cn_map.get(t, t))
    tag_display = " · ".join(cn_tags) if cn_tags else ""

    # 生成概要：优先用 action_clean，其次用 snippet 的前 100 字符
    if action_clean and len(action_clean) > 3:
        summary = action_clean
    elif snippet:
        # 截取 snippet 第一句
        first_sentence = snippet.split(".")[0].strip()
        summary = first_sentence[:150]
    else:
        summary = title[:150]

    # 如果 summary 全是英文，尝试用 action_clean（中文）
    if action_clean and len(action_clean) > 3 and not re.search(r'[一-鿿]', summary):
        summary = action_clean

    return summary, tag_display


# ── 6. 分组：高优先级（≥7）、中优先级（5-6）、低优先级（<5）──
high_items = [s for s in scored if s["total"] >= 7]
mid_items = [s for s in scored if 5 <= s["total"] <= 6]
low_items = [s for s in scored if s["total"] < 5]

# ── 7. 生成开头概要 ──
top_themes = set()
for s in high_items:
    art = articles.get(s["num"], {})
    for t in art.get("tags", "").replace("#", "").split():
        if t.strip():
            top_themes.add(t.strip())

intro_lines = []
if high_items:
    h = high_items[0]
    art_h = articles.get(h["num"], {})
    intro_lines.append(f"今日头条：{art_h.get('title_en', '')[:60]}……（{h['total']} 分）")
intro_lines.append(f"共审查 {len(articles)} 篇文章，{len(high_items)} 篇高优先级，{len(mid_items)} 篇值得关注。")

intro_text = "\n".join(intro_lines)


# ── 8. 构建 HTML ──
def build_article_row(s: dict, show_score_detail: bool = True, compact: bool = False) -> str:
    num = s["num"]
    art = articles.get(num, {})
    link = art.get("link", "#")
    summary, tag_display = make_chinese_summary(num, art, s)

    # 分数明细
    ws = worker_scores.get(num, {})
    if ws and show_score_detail:
        parts = []
        for wname in ["kimi", "deepseek", "glm"]:
            if wname in ws:
                d = ws[wname]
                parts.append(
                    f'<span style="display:inline-block;min-width:65px;font-size:11px">'
                    f'<b>{wname.upper()}</b> {d["relevance"]}+{d["feasibility"]}+{d["leverage"]}=<b>{d["total"]}</b>'
                    f'</span>'
                )
        score_detail = "<br>".join(parts)
    else:
        score_detail = f'<span style="font-size:11px;color:#888">R{s["relevance"]}+F{s["feasibility"]}+L{s["leverage"]}</span>'

    total = s["total"]
    if total >= 7:
        total_color = "#d93025"
    elif total >= 5:
        total_color = "#e37400"
    else:
        total_color = "#999"

    # 紧凑模式（用于左右分栏里的条目）
    if compact:
        return f"""
            <div style="border-bottom:1px solid #eee;padding:10px 0">
              <div style="margin-bottom:4px">
                <span style="font-weight:bold;color:#222;font-size:14px">#{num}</span>
                <a href="{link}" style="color:#1a73e8;text-decoration:none;font-size:13px;margin-left:4px">原文→</a>
              </div>
              <div style="font-size:13px;color:#333;line-height:1.5;margin-bottom:3px">{summary}</div>
              <div style="font-size:11px;color:#888">{tag_display}</div>
              <div style="margin-top:4px">
                <span style="font-size:16px;font-weight:bold;color:{total_color}">{total}</span>
                <span style="font-size:10px;color:#aaa;margin-left:4px">{score_detail.replace('<br>', ' · ')}</span>
              </div>
            </div>"""

    return f"""
            <tr>
              <td style="padding:12px 10px;border-bottom:1px solid #eee;vertical-align:top">
                <div style="font-size:15px;font-weight:bold;color:#222;margin-bottom:4px">
                  #{num} {summary}
                </div>
                <div style="font-size:12px;color:#888;margin-bottom:4px">{tag_display}</div>
              </td>
              <td style="padding:12px 10px;border-bottom:1px solid #eee;text-align:center;white-space:nowrap;vertical-align:top;min-width:80px">
                <span style="font-size:20px;font-weight:bold;color:{total_color}">{total}</span>
                <div style="margin-top:3px">{score_detail}</div>
              </td>
              <td style="padding:12px 10px;border-bottom:1px solid #eee;text-align:center;vertical-align:top;width:60px">
                <a href="{link}" style="display:inline-block;background:#1a73e8;color:#fff;text-decoration:none;padding:6px 12px;border-radius:4px;font-size:12px;white-space:nowrap">阅读→</a>
              </td>
            </tr>"""


# ── 9. 构建单列垂直布局 ──
# 高优先级 → 值得关注 → 其他，从上往下

all_rows = ""
if high_items:
    all_rows += ('<tr><td colspan="3" style="padding:14px 10px 6px;font-size:14px;font-weight:bold;color:#d93025">'
                 f'🔥 高优先级（{len(high_items)} 篇）</td></tr>')
    for s in high_items:
        all_rows += build_article_row(s, show_score_detail=True, compact=False)

if mid_items:
    all_rows += ('<tr><td colspan="3" style="padding:20px 10px 6px;font-size:14px;font-weight:bold;color:#e37400">'
                 f'📌 值得关注（{len(mid_items)} 篇）</td></tr>')
    for s in mid_items:
        all_rows += build_article_row(s, show_score_detail=True, compact=False)

if not high_items and not mid_items:
    # 没有重点也没有关注，直接从其他开始
    all_rows += ('<tr><td colspan="3" style="padding:10px 10px 6px;font-size:14px;color:#666">'
                 f'今天没有≥5分的文章，以下是全部 {len(low_items)} 篇：</td></tr>')

if low_items:
    if high_items or mid_items:
        all_rows += ('<tr><td colspan="3" style="padding:20px 10px 6px;font-size:14px;font-weight:bold;color:#999">'
                     f'📎 其他（{len(low_items)} 篇）</td></tr>')
    for s in low_items:
        all_rows += build_article_row(s, show_score_detail=False, compact=False)

article_table = f"""
<table style="width:100%;border-collapse:collapse;margin:10px 0">
<tr style="background:#f5f5f5">
  <th style="padding:8px 10px;text-align:left;font-size:13px">文章</th>
  <th style="padding:8px 10px;text-align:center;width:85px;font-size:13px">评分</th>
  <th style="padding:8px 10px;text-align:center;width:65px;font-size:13px">原文</th>
</tr>
{all_rows}
</table>"""

# 行动建议 HTML
action_html = ""
if action_items:
    action_lines = []
    for i, act in enumerate(action_items, 1):
        ref_str = "、".join(f"#{r}" for r in act["refs"]) if act["refs"] else "—"
        action_lines.append(
            f'<li style="margin-bottom:10px">'
            f'<strong>{act["title"]}</strong>'
            f'<div style="font-size:12px;color:#888;margin-top:2px">📎 基于情报 {ref_str}</div>'
            f'</li>'
        )
    action_html = f"""
        <div style="background:#fff3cd;border-radius:8px;padding:18px;margin:20px 0;border-left:4px solid #f9ab00">
          <strong style="font-size:15px">💡 今日行动建议</strong>
          <ol style="margin-top:10px;line-height:1.8;padding-left:20px">{''.join(action_lines)}</ol>
        </div>"""

# ── 9. 拼装完整 HTML ──
body = f"""
<html><body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif;max-width:620px;margin:0 auto;padding:20px;background:#fff">

<h2 style="margin-bottom:2px">☀️ 小樱日报</h2>
<div style="font-size:13px;color:#999;margin-bottom:16px">{today} · 4 个 AI 交叉审查 · {len(articles)} 篇文章</div>

<div style="background:#f0f7ff;border-radius:8px;padding:15px;margin-bottom:20px;font-size:14px;line-height:1.7;color:#333">
  <strong>📊 今日概要</strong>
  <div style="margin-top:6px;white-space:pre-line">{intro_text}</div>
</div>

{action_html}

{article_table}

<div style="background:#f5f5f5;border-radius:8px;padding:12px 15px;margin-top:16px;font-size:13px;color:#555">
  <strong>🔗 完整日报</strong>
  &nbsp;<a href="{REPO_URL}/memory/intel/daily-{today}.md" style="color:#1a73e8">查看原始 Markdown（GitHub）</a>
  &nbsp;|&nbsp;
  <a href="{REPO_URL}/memory/intel/actions-{today}.md" style="color:#1a73e8">行动建议详情</a>
  <span style="float:right;color:#999;font-size:11px">🤖 全自动 · 每日成本约 ¥0.07</span>
</div>

</body></html>"""

# ── 10. 发送 ──
if DRY_RUN:
    preview_path = INTEL_DIR / "_email_preview.html"
    preview_path.write_text(body, encoding="utf-8")
    print(f"[DRY-RUN] Preview saved: {preview_path}")
    print(f"[DRY-RUN] Subject: {today} AI日报 - {len(high_items)}篇重点 + {len(mid_items)}篇关注")
    print(f"[DRY-RUN] Articles: {len(articles)} / Scored: {len(scored)} / Actions: {len(action_items)}")
    print(f"[DRY-RUN] High: {len(high_items)} / Mid: {len(mid_items)} / Low: {len(low_items)}")
    sys.exit(0)

msg = MIMEMultipart()
msg["From"] = os.environ["QQ_EMAIL"]
msg["To"] = os.environ["QQ_EMAIL"]
msg["Subject"] = f"{today} AI日报 · {len(high_items)}篇重点 + {len(mid_items)}篇关注"
msg.attach(MIMEText(body, "html", "utf-8"))

server = smtplib.SMTP_SSL("smtp.qq.com", 465)
server.login(os.environ["QQ_EMAIL"], os.environ["QQ_SMTP_AUTH"])
server.send_message(msg)
server.quit()
print(f"[OK] Daily report sent: {len(scored)} articles / {len(action_items)} actions")
