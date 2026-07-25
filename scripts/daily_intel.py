#!/usr/bin/env python3
"""每日情报扫描——调用 Serper API 搜索 AI 动态，写入 Intel 库。

设计原则：
- 纯 Python 标准库，零依赖（GitHub Actions 的 python 直接跑）
- 只做搜索+写文件，不做分析和决策（留给小樱在 Claude Code 里做）
- 失败不阻塞：单个关键词搜索失败不影响其他关键词

环境变量：
    SERPER_API_KEY: Serper API key（通过 GitHub Secrets 注入）

输出：
    memory/intel/daily-YYYY-MM-DD.md  每日简报
    memory/intel/INDEX.md             更新索引
"""

import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from pathlib import Path


# ── 配置 ───────────────────────────────────────────────

# 北京时间 (UTC+8)
TZ = timezone(timedelta(hours=8))

# 搜索关键词（时间敏感的主题加 tbs 参数过滤最近一周）
QUERIES = [
    # (query, language, region, tbs)
    ("AI industry breaking news highlights this week", "en", "us", "qdr:w"),
    ("new AI agent tools frameworks released 2026", "en", "us", None),
    ("solo founder one person business AI startup 2026", "en", "us", None),
    ("Claude Code new features updates 2026", "en", "us", None),
    ("China AI policy regulation 2026", "en", "us", None),
    ("一人公司 AI 创业 新工具 2026", "zh-cn", "cn", None),
]

# Serper API
API_URL = "https://google.serper.dev/search"
MAX_PER_QUERY = 3  # 每个关键词最多取几条（查询多，每条少取，保多样性）

# 路径（相对于仓库根目录）
REPO_ROOT = Path(__file__).resolve().parent.parent
INTEL_DIR = REPO_ROOT / "memory" / "intel"
INDEX_PATH = INTEL_DIR / "INDEX.md"

# DeepSeek API（用于每日摘要——可选，不设则跳过）
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"

# 已知主题标签（用于自动标注）
TOPIC_TAGS = {
    "agent": "#AI-agent",
    "framework": "#AI-agent",
    "claude": "#Claude",
    "anthropic": "#Claude",
    "solo founder": "#OPC",
    "一人公司": "#OPC",
    "one person": "#OPC",
    "opc": "#OPC",
    "china": "#China-AI",
    "中国": "#China-AI",
    "low code": "#vibe-coding",
    "no code": "#vibe-coding",
    "vibe cod": "#vibe-coding",
    "无代码": "#vibe-coding",
    "paper detect": "#paper-detection",
    "论文检测": "#paper-detection",
    "ai detection": "#paper-detection",
    "tool": "#new-tool",
    "platform": "#new-tool",
    "新工具": "#new-tool",
}


# ── 工具函数 ───────────────────────────────────────────

def search(query: str, gl: str, hl: str, tbs: str | None = None) -> list[dict]:
    """调用 Serper API 搜索，返回 organic results 列表。"""
    payload_dict: dict = {
        "q": query,
        "gl": gl,
        "hl": hl,
        "num": MAX_PER_QUERY,
    }
    if tbs:
        payload_dict["tbs"] = tbs
    payload = json.dumps(payload_dict).encode("utf-8")

    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={
            "X-API-KEY": os.environ["SERPER_API_KEY"],
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data.get("organic", [])
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"  HTTP {e.code} for '{query}': {body[:200]}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"  Error for '{query}': {e}", file=sys.stderr)
        return []


def guess_tags(title: str, snippet: str) -> list[str]:
    """根据标题和摘要自动匹配主题标签。"""
    text = (title + " " + snippet).lower()
    tags = []
    for keyword, tag in TOPIC_TAGS.items():
        if keyword in text and tag not in tags:
            tags.append(tag)
    return tags


def domain_from(url: str) -> str:
    """从 URL 提取域名。"""
    try:
        return url.split("/")[2]
    except (IndexError, AttributeError):
        return ""


def write_brief(date_str: str, findings: list[dict]) -> Path:
    """写入每日简报文件。"""
    INTEL_DIR.mkdir(parents=True, exist_ok=True)
    path = INTEL_DIR / f"daily-{date_str}.md"

    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# 每日情报简报 — {date_str}\n\n")
        f.write(f"> 自动扫描时间：{datetime.now(TZ).strftime('%Y-%m-%d %H:%M')}（北京时间）\n")
        f.write(f"> 状态：⏳ 待小樱研判\n")
        f.write(f"> 来源：GitHub Actions + Serper API\n\n")
        f.write("---\n\n")

        if not findings:
            f.write("⚠️ 本次扫描未获取到结果。可能原因：API 配额用尽 / 网络异常。\n\n")
            return path

        f.write(f"## 搜索结果（{len(findings)} 条）\n\n")

        for i, item in enumerate(findings, 1):
            title = item.get("title", "无标题")
            link = item.get("link", "")
            snippet = item.get("snippet", "")
            src_query = item.get("query", "")
            tags = item.get("tags", [])

            f.write(f"### {i}. [{title}]({link})\n\n")
            f.write(f"{snippet}\n\n")
            tag_str = " ".join(tags) if tags else ""
            f.write(f"- 关键词: `{src_query}`\n")
            if tag_str:
                f.write(f"- 标签: {tag_str}\n")
            f.write(f"- 来源: {domain_from(link)}\n")
            f.write(f"- 研判: ⏳ 待小樱评分\n\n")

        # 评分区（供小樱填充）
        f.write("---\n\n")
        f.write("## 研判区（小樱填充）\n\n")
        f.write("| # | 相关性(0-3) | 可行性(0-3) | 杠杆率(0-3) | 总分 | 行动建议 |\n")
        f.write("|---|------------|------------|------------|------|--------|\n")
        for i in range(1, len(findings) + 1):
            f.write(f"| {i} | — | — | — | — | — |\n")
        f.write("\n")
        f.write("**研判结论**：（小樱写）\n\n")

    return path


def update_index(date_str: str, findings: list[dict]):
    """更新 Intel 库索引。"""
    # 提取本次简报的关键主题
    tags_set = set()
    for item in findings:
        for tag in item.get("tags", []):
            tags_set.add(tag)

    # 读取现有索引
    if INDEX_PATH.exists():
        old_lines = INDEX_PATH.read_text(encoding="utf-8").splitlines()
    else:
        old_lines = [
            "# Intel 库索引",
            "",
            "> 每日情报简报存档。按日期索引。",
            "",
            "## 简报列表",
            "",
            "| 日期 | 条数 | 关键标签 | 是否已研判 |",
            "|------|------|---------|-----------|",
            "",
            "---",
            "",
            "## 主题标签索引",
            "",
            "按关键词快速检索历史简报：",
            "- `#AI-agent` — AI Agent 相关",
            "- `#new-tool` — 新工具/平台",
            "- `#OPC` — 一人公司相关",
            "- `#Claude` — Claude/Anthropic 相关",
            "- `#China-AI` — 中国 AI 政策/市场",
            "- `#paper-detection` — 论文检测技术",
            "- `#vibe-coding` — 零代码开发",
            "",
            "---",
            "",
            "> 小樱维护——每次简报写入后更新此索引",
            "",
        ]

    # 找到表格末尾（"---" 行之后是标签索引区）
    new_lines = []
    inserted = False
    for i, line in enumerate(old_lines):
        new_lines.append(line)
        # 在表格最后一行之后、空行之前插入新行
        if not inserted and line.startswith("|") and i > 0:
            # 检查下一行是不是分隔线或空行
            pass

    # 简化方式：重建索引
    table_start = -1
    table_end = -1
    for i, line in enumerate(old_lines):
        if line.startswith("| 日期 |"):
            table_start = i
        if table_start > 0 and line.startswith("---") and i > table_start + 2:
            # 这可能是表格后面的分隔线
            pass

    # 最简单的方式：在第一个表格行之后插入
    output = []
    in_table = False
    row_inserted = False
    for i, line in enumerate(old_lines):
        output.append(line)
        if line.startswith("| 日期 |") and not in_table:
            in_table = True
            continue
        if in_table and line.startswith("|------|") and not row_inserted:
            # 分隔线后插入新行
            tag_str = " ".join(sorted(tags_set)[:5]) if tags_set else "—"
            output.append(f"| {date_str} | {len(findings)} | {tag_str} | ⏳ 待研判 |")
            row_inserted = True

    if not row_inserted:
        # fallback：在第一个 --- 后插入
        pass  # unlikely path for existing index

    INDEX_PATH.write_text("\n".join(output), encoding="utf-8")


def summarize_with_llm(findings: list[dict]) -> str | None:
    """调用 DeepSeek API，从 10 条情报中选 Top 3 + 一句话理由。

    返回 Markdown 格式的摘要文本，失败返回 None。
    """
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        print("  (无 DEEPSEEK_API_KEY，跳过摘要)")
        return None

    # 构造候选列表
    items = []
    for i, f in enumerate(findings, 1):
        tags = " ".join(f.get("tags", []))
        items.append(
            f"{i}. [{f['title']}]({f['link']})\n"
            f"   摘要：{f['snippet']}\n"
            f"   标签：{tags}\n"
            f"   来源：{f['link'].split('/')[2] if f['link'] else '—'}"
        )
    candidates = "\n\n".join(items)

    system_prompt = (
        "你是为一人公司（OPC）创业者筛选情报的 AI 分析师。"
        "关注领域：AI Agent 工具/框架、一人公司创业案例、Claude/Anthropic 更新、中国 AI 政策、零代码开发。"
        "从候选列表中选出最值得关注的前 3 条，每条附一句话理由（≤30 字），说明为什么对一人公司创业者有用。"
        "输出格式：\n"
        "### 🔥 今日 Top 3\n"
        "1. **[标题]** — 一句话理由\n"
        "2. **[标题]** — 一句话理由\n"
        "3. **[标题]** — 一句话理由"
    )

    payload = json.dumps({
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"今日情报候选（共 {len(findings)} 条）：\n\n{candidates}"},
        ],
        "temperature": 0.3,
        "max_tokens": 512,
    }).encode("utf-8")

    req = urllib.request.Request(
        DEEPSEEK_API_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"  LLM 摘要失败: {e}", file=sys.stderr)
        return None


def write_summary(date_str: str, summary: str) -> Path:
    """写入每日摘要文件。"""
    path = INTEL_DIR / f"daily-summary-{date_str}.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# 每日情报精选 — {date_str}\n\n")
        f.write(f"> 🤖 LLM 自动精选 | 原始简报：[daily-{date_str}.md](daily-{date_str}.md)\n\n")
        f.write(summary)
        f.write("\n\n---\n\n")
        f.write("> ⚠️ AI 自动筛选，未经人工核查。建议阅读原文确认。\n")
    return path


# ── 主流程 ──────────────────────────────────────────────

def main():
    api_key = os.environ.get("SERPER_API_KEY", "")
    if not api_key:
        print("FATAL: SERPER_API_KEY environment variable not set.", file=sys.stderr)
        sys.exit(1)

    now = datetime.now(TZ)
    date_str = now.strftime("%Y-%m-%d")
    print(f"=== 每日情报扫描 {date_str} ===\n")

    # 逐关键词搜索
    all_findings = []
    for query, hl, gl, tbs in QUERIES:
        print(f"搜索: {query} (gl={gl}, hl={hl})")
        results = search(query, gl, hl, tbs)
        for r in results:
            title = r.get("title", "")
            snippet = r.get("snippet", "")
            tags = guess_tags(title, snippet)
            all_findings.append({
                "title": title,
                "link": r.get("link", ""),
                "snippet": snippet,
                "query": query,
                "tags": tags,
            })
        print(f"  → {len(results)} 条")

    # 按链接去重
    seen = set()
    unique = []
    for f in all_findings:
        if f["link"] and f["link"] not in seen:
            seen.add(f["link"])
            unique.append(f)

    # 取前 10 条
    unique = unique[:10]
    print(f"\n去重后 {len(unique)} 条（展示 ≤10）")

    # 写入简报
    brief_path = write_brief(date_str, unique)
    print(f"\n简报已写入: {brief_path}")

    # LLM 摘要（可选——需要 DEEPSEEK_API_KEY 环境变量）
    print(f"\n尝试 LLM 摘要...")
    summary = summarize_with_llm(unique)
    if summary:
        summary_path = write_summary(date_str, summary)
        print(f"摘要已写入: {summary_path}")
    else:
        print("  跳过摘要（无 API key 或调用失败）")

    # 更新索引
    update_index(date_str, unique)
    print(f"索引已更新: {INDEX_PATH}")

    print("\n完成。")


if __name__ == "__main__":
    main()
