"""邮件发送脚本 v3——真正的日报格式。

每条文章有 GLM 生成的中文摘要（而非内部评分备注），
行动建议放在顶部并标注关联情报编号，
高优先→值得关注→其他 单列垂直布局，分数从高到低。
"""

import smtplib
import sys
import os
import re
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

TZ = timezone(timedelta(hours=8))
INTEL_DIR = Path("memory/intel")
REPO_URL = "https://github.com/ymqlsakura/ai-agent-learning/blob/main"
DRY_RUN = "--dry-run" in sys.argv
GLM_API_KEY = os.environ.get("GLM_API_KEY", "")
GLM_API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"


# ── GLM 中文摘要生成 ──

def generate_chinese_summaries(articles: dict) -> dict[int, str]:
    """调用 GLM-4-Flash（免费）把每篇文章生成中文摘要。

    返回 {num: "中文摘要"} 字典。失败时返回空 dict，调用方降级。
    """
    if not GLM_API_KEY:
        print("[!] GLM_API_KEY 未设置，跳过中文摘要生成")
        return {}

    items_text = ""
    for num, art in sorted(articles.items()):
        items_text += (
            f"#{num}: {art['title_en']}\n"
            f"  摘要: {art['snippet_en'][:200]}\n"
            f"  标签: {art['tags']}\n\n"
        )

    prompt = (
        "你是一个AI日报编辑。以下是从今天AI行业新闻中筛选出的文章，"
        "请为每篇文章写一句中文摘要（20-40字），概括核心内容。\n\n"
        "要求：\n"
        "- 只输出JSON格式：{\"1\": \"摘要\", \"2\": \"摘要\", ...}\n"
        "- 摘要要让人一眼看懂这篇文章在讲什么，不要翻译腔\n"
        "- 如果原文是英文标题+snippet，用自然的中文表达\n\n"
        f"{items_text}"
    )

    payload = json.dumps({
        "model": "glm-4-flash",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 2048,
    }).encode()

    try:
        req = urllib.request.Request(
            GLM_API_URL,
            data=payload,
            headers={
                "Authorization": f"Bearer {GLM_API_KEY}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            content = data["choices"][0]["message"]["content"]

        json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
        if json_match:
            summaries = json.loads(json_match.group())
            result = {}
            for k, v in summaries.items():
                result[int(k)] = v.strip()
            print(f"[*] GLM 生成了 {len(result)} 条中文摘要")
            return result
        else:
            print(f"[!] GLM 返回格式无法解析: {content[:200]}")
            return {}
    except Exception as e:
        print(f"[!] GLM 摘要生成失败: {e}")
        return {}


# ── 主流程 ──

today = datetime.now(TZ).strftime("%Y-%m-%d")

daily_path = INTEL_DIR / f"daily-{today}.md"
actions_path = INTEL_DIR / f"actions-{today}.md"
json_path = INTEL_DIR / f"daily-{today}.json"

if not daily_path.exists():
    print(f"[x] 日报不存在: {daily_path}")
    sys.exit(0)

raw = daily_path.read_text(encoding="utf-8")

# ── 1. 解析文章 ──
articles = {}
article_blocks = re.split(r'\n(?=### \d+\.\s)', raw)
for block in article_blocks:
    m = re.match(r'### (\d+)\.\s+\[(.+?)\]\((.+?)\)', block)
    if not m:
        continue
    num = int(m.group(1))
    title_en = m.group(2).strip()
    link = m.group(3).strip()
    snippet_en = ""
    sm = re.search(r'\n\n(.+?)\n\n\s*-', block, re.DOTALL)
    if sm:
        snippet_en = sm.group(1).strip()[:300]
    tags = re.findall(r'标签:\s*(.+)', block)
    tag_str = tags[0].strip() if tags else ""
    articles[num] = {
        "title_en": title_en,
        "link": link,
        "snippet_en": snippet_en,
        "tags": tag_str,
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
            total = int(cells[4])
        except ValueError:
            continue
        scored.append({
            "num": num,
            "relevance": cells[1],
            "feasibility": cells[2],
            "leverage": cells[3],
            "total": total,
            "action_raw": cells[5],
        })

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

# ── 4. 解析行动建议 ──
action_items = []
if actions_path.exists():
    actions_raw = actions_path.read_text(encoding="utf-8")

    # 提取全局关联情报
    global_refs = []
    refs_section_start = actions_raw.find("## 📊")
    if refs_section_start < 0:
        refs_section_start = actions_raw.find("## 关联情报")
    if refs_section_start >= 0:
        refs_section = actions_raw[refs_section_start:]
        global_refs = list(set(
            int(m.group(1)) for m in re.finditer(r'\[#(\d+)', refs_section)
        ))
        global_refs.sort()

    # 提取每个行动块
    act_blocks = re.split(r'\n(?=### 行动 \d+)', actions_raw)
    for block in act_blocks:
        title_m = re.match(r'### 行动 \d+：(.+)', block)
        if not title_m:
            continue
        title = title_m.group(1).strip()

        # Per-action 关联情报
        refs = []
        ref_match = re.search(r'\*\*关联情报\*\*：(.+)', block)
        if ref_match:
            ref_raw = ref_match.group(1).strip()
            refs = list(set(
                int(r) for r in re.findall(r'#(\d+)', ref_raw) if 1 <= int(r) <= 99
            ))
            refs.sort()
        if not refs:
            refs = global_refs

        action_items.append({"title": title, "refs": refs})

# ── 5. 用 GLM 生成中文摘要 ──
cn_summaries = generate_chinese_summaries(articles)


# ── 6. 辅助函数 ──

def get_summary(art: dict, s: dict) -> str:
    """获取文章的中文描述——只用 GLM 摘要，不做降级。"""
    num = s["num"]
    # 1. GLM 摘要优先
    if num in cn_summaries and cn_summaries[num]:
        return cn_summaries[num]
    # 2. 没有 GLM 摘要时：action_clean 作为底
    action_clean = re.sub(r'\[.*?\]', '', s.get("action_raw", "")).strip()
    if action_clean and len(action_clean) > 3 and re.search(r'[一-鿿]', action_clean):
        return action_clean
    # 3. 全是英文 → 用英文标题（现实：GLM 应该不会失败）
    return art.get("title_en", "")[:150]


def get_tag_display(art: dict) -> str:
    """生成中文标签显示。"""
    tags = art.get("tags", "")
    tag_cn_map = {
        "OPC": "一人公司",
        "AI-agent": "AI Agent",
        "Claude": "Claude",
        "new-tool": "新工具",
    }
    cn_tags = []
    for t in tags.replace("#", "").split():
        t = t.strip()
        if t:
            cn_tags.append(tag_cn_map.get(t, t))
    return " · ".join(cn_tags) if cn_tags else ""


# ── 7. 分组 ──
high_items = [s for s in scored if s["total"] >= 7]
mid_items = [s for s in scored if 5 <= s["total"] <= 6]
low_items = [s for s in scored if s["total"] < 5]


# ── 8. 构建一条文章行 ──

def build_row(s: dict, show_score_detail: bool = True) -> str:
    num = s["num"]
    art = articles.get(num, {})
    link = art.get("link", "#")
    summary = get_summary(art, s)
    tag_display = get_tag_display(art)

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


# ── 9. 构建文章表格 ──

all_rows = ""
if high_items:
    all_rows += ('<tr><td colspan="3" style="padding:14px 10px 6px;font-size:14px;font-weight:bold;color:#d93025">'
                 f'🔥 高优先级（{len(high_items)} 篇）</td></tr>')
    for s in high_items:
        all_rows += build_row(s, show_score_detail=True)

if mid_items:
    all_rows += ('<tr><td colspan="3" style="padding:20px 10px 6px;font-size:14px;font-weight:bold;color:#e37400">'
                 f'📌 值得关注（{len(mid_items)} 篇）</td></tr>')
    for s in mid_items:
        all_rows += build_row(s, show_score_detail=True)

if low_items:
    if high_items or mid_items:
        all_rows += ('<tr><td colspan="3" style="padding:20px 10px 6px;font-size:14px;font-weight:bold;color:#999">'
                     f'📎 其他（{len(low_items)} 篇）</td></tr>')
    for s in low_items:
        all_rows += build_row(s, show_score_detail=False)

article_table = f"""
<table style="width:100%;border-collapse:collapse;margin:10px 0">
<tr style="background:#f5f5f5">
  <th style="padding:8px 10px;text-align:left;font-size:13px">文章</th>
  <th style="padding:8px 10px;text-align:center;width:85px;font-size:13px">评分</th>
  <th style="padding:8px 10px;text-align:center;width:65px;font-size:13px">原文</th>
</tr>
{all_rows}
</table>"""


# ── 10. 构建行动建议 ──

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


# ── 11. 拼装完整 HTML ──

# 今日概要
intro = f"今日共审查 {len(articles)} 篇文章，{len(high_items)} 篇高优先级"
if high_items:
    top_article = articles.get(high_items[0]["num"], {})
    intro += f"，头条是关于 {top_article.get('title_en', 'AI')[:60]}"
intro += "。"

body = f"""
<html><body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif;max-width:620px;margin:0 auto;padding:20px;background:#fff">

<h2 style="margin-bottom:2px">☀️ 小樱日报</h2>
<div style="font-size:13px;color:#999;margin-bottom:16px">{today} · 4 个 AI 交叉审查 · {len(articles)} 篇文章</div>

<div style="background:#f0f7ff;border-radius:8px;padding:15px;margin-bottom:20px;font-size:14px;line-height:1.7;color:#333">
  <strong>📊 今日概要</strong>
  <div style="margin-top:6px">{intro}</div>
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

# ── 12. 发送 ──
if DRY_RUN:
    preview_path = INTEL_DIR / "_email_preview.html"
    preview_path.write_text(body, encoding="utf-8")
    print(f"[DRY-RUN] Preview saved: {preview_path}")
    print(f"[DRY-RUN] Subject: {today} AI日报 - {len(high_items)}重点 + {len(mid_items)}关注")
    print(f"[DRY-RUN] Articles: {len(articles)} / Scored: {len(scored)} / Actions: {len(action_items)}")
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
