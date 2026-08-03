"""邮件发送脚本——解析日报 markdown + JSON 生成 HTML 邮件。

在 GitHub Actions 中由 supervisor-daily.yml 调用。
需要环境变量: QQ_EMAIL, QQ_SMTP_AUTH
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

# ── 配置 ──
TZ = timezone(timedelta(hours=8))
INTEL_DIR = Path("memory/intel")
REPO_URL = "https://github.com/ymqlsakura/ai-agent-learning/blob/main"
DRY_RUN = "--dry-run" in sys.argv

# ── 获取今天日期 ──
today = datetime.now(TZ).strftime("%Y-%m-%d")

daily_path = INTEL_DIR / f"daily-{today}.md"
actions_path = INTEL_DIR / f"actions-{today}.md"
json_path = INTEL_DIR / f"daily-{today}.json"

if not daily_path.exists():
    print(f"[x] 日报不存在: {daily_path}")
    sys.exit(0)

raw = daily_path.read_text(encoding="utf-8")

# ── 1. 解析每篇文章（含链接）──
articles = []
# 用 "### N. " 模式分割
article_blocks = re.split(r'\n(?=### \d+\.\s)', raw)
for block in article_blocks:
    m = re.match(r'### \d+\.\s+\[(.+?)\]\((.+?)\)', block)
    if not m:
        continue
    tags = re.findall(r'标签:\s*(.+)', block)
    tag_str = tags[0].strip() if tags else ""
    articles.append({
        "title": m.group(1).strip(),
        "link": m.group(2).strip(),
        "tags": tag_str,
    })

# ── 2. 读取 JSON 获取 per-worker 打分明细 ──
worker_scores = {}
if json_path.exists():
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
        for s in data.get("scores", []):
            num = s.get("num") or s.get("#")
            if num:
                worker_scores[num] = s.get("worker_scores", {})
        if worker_scores:
            print(f"[*] 从 JSON 读取到 {len(worker_scores)} 条 per-worker 分数")
        else:
            print("[*] JSON 存在但无 worker_scores（旧版数据），降级到解析 markdown 表格")
    except Exception as e:
        print(f"[!] JSON 解析失败: {e}")

# ── 3. 解析研判表格（从 markdown）──
scored = []
table_start = raw.find("| # |")
if table_start < 0:
    # 兼容：有些文件用的中文表头
    table_start = raw.find("| # | 相关性")

if table_start >= 0:
    for line in raw[table_start:].split("\n"):
        if not line.startswith("|") or "---" in line:
            continue
        cells = [c.strip() for c in line.split("|") if c.strip()]
        if len(cells) < 6:
            continue
        # 跳过表头行
        if cells[0] in ("#", "编号"):
            continue
        if "相关性" in cells[0] or "可行性" in cells[1] or "杠杆" in cells[2]:
            continue
        try:
            num = int(cells[0])
        except ValueError:
            continue
        scored.append({
            "num": num,
            "relevance": cells[1],
            "feasibility": cells[2],
            "leverage": cells[3],
            "total": cells[4],
            "action": cells[5],
        })

# ── 4. 解析行动建议 ──
action_items = []
if actions_path.exists():
    actions_raw = actions_path.read_text(encoding="utf-8")
    act_titles = re.findall(r'### 行动 \d+：(.+)', actions_raw)
    action_items = act_titles

# ── 5. 构建 HTML 表格行 ──
score_rows = ""
for s in scored:
    num = s["num"]
    art = articles[num - 1] if num <= len(articles) else {}
    title = art.get("title", "?")
    link = art.get("link", "#")
    tags = art.get("tags", "")

    # Per-worker 分维度明细
    ws = worker_scores.get(num, {})
    if ws:
        ws_lines = []
        for wname in ["kimi", "deepseek", "glm"]:
            if wname in ws:
                d = ws[wname]
                ws_lines.append(
                    f'<span style="display:inline-block;min-width:75px">'
                    f'<b>{wname.upper()}</b> {d["relevance"]}+{d["feasibility"]}+{d["leverage"]}=<b>{d["total"]}</b>'
                    f'</span>'
                )
        ws_detail = "<br>".join(ws_lines) if ws_lines else ""
    else:
        ws_detail = ""

    total_val = s["total"]
    total_display = f'<span style="font-size:18px;font-weight:bold;color:#222">{total_val}</span>'

    score_rows += f"""
            <tr>
              <td style="padding:8px 10px;border-bottom:1px solid #eee;vertical-align:top">
                <a href="{link}" style="color:#1a73e8;text-decoration:none;font-weight:bold">#{num} {title}</a>
                <div style="font-size:11px;color:#999">{tags}</div>
              </td>
              <td style="padding:8px 10px;border-bottom:1px solid #eee;text-align:center;white-space:nowrap;vertical-align:top">
                {total_display}
                <div style="font-size:11px;color:#666;margin-top:2px">{ws_detail if ws_detail else f"R{s['relevance']}+F{s['feasibility']}+L{s['leverage']}"}</div>
              </td>
              <td style="padding:8px 10px;border-bottom:1px solid #eee;font-size:13px;color:#555;vertical-align:top">
                {s['action']}
              </td>
            </tr>"""

# ── 6. 拼装完整 HTML ──
body = f"""<html><body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;max-width:600px;margin:0 auto;padding:20px">
        <h2>☀️ 小樱日报 {today}</h2>
        <p style="color:#666">4 个 AI 交叉审查 · {len(articles)} 篇文章 · {len(scored)} 条已评分</p>

        <table style="width:100%;border-collapse:collapse;margin:15px 0">
        <tr style="background:#f5f5f5">
          <th style="padding:8px 10px;text-align:left">文章</th>
          <th style="padding:8px 10px;text-align:center;width:90px">总分</th>
          <th style="padding:8px 10px;text-align:left">建议</th>
        </tr>
        {score_rows}
        </table>"""

if action_items:
    action_list = "".join(f"<li>{t}</li>" for t in action_items)
    body += f"""
        <div style="background:#f9f9f9;border-radius:8px;padding:15px;margin:15px 0">
          <strong>💡 今日行动建议</strong>
          <ol style="margin-top:8px;line-height:1.8;padding-left:20px">{action_list}</ol>
        </div>"""

body += f"""
        <div style="background:#e8f0fe;border-radius:8px;padding:15px;margin:15px 0">
          <strong>🔗 完整日报</strong><br>
          <a href="{REPO_URL}/memory/intel/daily-{today}.md" style="color:#1a73e8">查看原文（GitHub）</a>
          &nbsp;|&nbsp;
          <a href="{REPO_URL}/memory/intel/actions-{today}.md" style="color:#1a73e8">行动建议详情</a>
        </div>

        <hr>
        <p style="color:#999;font-size:11px">🤖 全自动 AI 情报研判系统 · Kimi K3 + DeepSeek V4 Flash + GLM-4-Flash 交叉审查 · 每日成本约 ¥0.07</p>
        </body></html>"""

# ── 7. 发送 ──
if DRY_RUN:
    preview_path = INTEL_DIR / "_email_preview.html"
    preview_path.write_text(body, encoding="utf-8")
    print(f"[DRY-RUN] 预览已保存: {preview_path}")
    print(f"[DRY-RUN] 邮件主题: 📰 小樱日报 {today} — {len(scored)} 条情报")
    print(f"[DRY-RUN] 文章 {len(articles)} 篇 / 评分 {len(scored)} 条 / 行动 {len(action_items)} 条")
    sys.exit(0)

msg = MIMEMultipart()
msg["From"] = os.environ["QQ_EMAIL"]
msg["To"] = os.environ["QQ_EMAIL"]
msg["Subject"] = f"📰 小樱日报 {today} — {len(scored)} 条情报"
msg.attach(MIMEText(body, "html", "utf-8"))

server = smtplib.SMTP_SSL("smtp.qq.com", 465)
server.login(os.environ["QQ_EMAIL"], os.environ["QQ_SMTP_AUTH"])
server.send_message(msg)
server.quit()
print(f"[OK] 日报已发送——{len(scored)} 篇文章 / {len(action_items)} 条行动建议")
