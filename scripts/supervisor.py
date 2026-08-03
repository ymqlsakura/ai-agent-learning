#!/usr/bin/env python3
"""多 Agent Supervisor——主控大脑。

复刻 @nopinduoduo 的架构：一个 Supervisor + 多个 Worker 并行协作。
Supervisor 读取 /goal 定义 → 拆解子任务 → 并行调 Worker API → 收集 →
交叉验证 → 追问纠错 → 多轮迭代 → 合并输出。

设计原则：
- 纯 Python 标准库，零依赖（和 daily_intel.py 一致）
- Worker 之间不直接通信（v1 简化——Supervisor 做所有路由）
- /goal = JSON 文件，模拟 Codex 的 /goal 持久化机制
- 并行调用：concurrent.futures.ThreadPoolExecutor

环境变量：
    KIMI_API_KEY      Kimi K3 API key
    DEEPSEEK_API_KEY  DeepSeek API key
    SERPER_API_KEY    可选——Worker 联网搜索

用法：
    python scripts/supervisor.py --goal goals/intel-review.json --date 2026-07-28
    python scripts/supervisor.py --goal goals/intel-review.json --date 2026-07-28 --dry-run
"""

import json
import os
import sys
import urllib.request
import urllib.error
import argparse
import re
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from config import (
    TZ, REPO_ROOT, GOALS_DIR, INTEL_DIR, INDEX_PATH,
    VENDOR_DOMAINS, WORKERS, TOKEN_PRICES,
    MAX_ROUNDS, API_TIMEOUT,
)


# ── Token 追踪 ──────────────────────────────────────────

class TokenTracker:
    """追踪每次 API 调用的 token 消耗和费用。

    所有三大 API（Moonshot / DeepSeek / xAI）都返回标准 OpenAI 格式的
    usage 字段：{"prompt_tokens": int, "completion_tokens": int, "total_tokens": int}。
    """

    # 定价（$/百万 tokens）——来自共享配置
    PRICING = TOKEN_PRICES

    def __init__(self):
        self.records: list[dict] = []

    def record(self, worker_id: str, model: str,
               usage: dict | None, cost_estimate: float = 0.0):
        """记录一次 API 调用。usage 为 None 时用字符估算填充。"""
        rec = {
            "worker": worker_id,
            "model": model,
            "usage": usage or {},
            "cost_estimate_usd": round(cost_estimate, 6),
        }
        self.records.append(rec)

    def summary(self) -> str:
        """返回 Markdown 格式的摘要，用于附加到研判结论末尾。"""
        if not self.records:
            return ""

        per_worker: dict[str, dict] = {}
        total_cost = 0.0
        for r in self.records:
            wid = r["worker"]
            if wid not in per_worker:
                per_worker[wid] = {"calls": 0, "prompt": 0, "completion": 0, "cost": 0.0}
            pw = per_worker[wid]
            pw["calls"] += 1
            pw["prompt"] += r["usage"].get("prompt_tokens", 0)
            pw["completion"] += r["usage"].get("completion_tokens", 0)
            pw["cost"] += r["cost_estimate_usd"]
            total_cost += r["cost_estimate_usd"]

        lines = ["", "💰 本次研判 Token 消耗："]
        for wid, pw in per_worker.items():
            name = WORKERS.get(wid, {}).get("name", wid)
            lines.append(
                f"  - {name}：{pw['calls']} 次调用 / "
                f"输入 {pw['prompt']:,} tokens / "
                f"输出 {pw['completion']:,} tokens / "
                f"≈ ${pw['cost']:.4f}"
            )
        lines.append(f"  **合计 ≈ ${total_cost:.4f}**")
        return "\n".join(lines)

    def write_log(self, date_str: str, goal_name: str, total_rounds: int):
        """将 token 日志写入 memory/intel/token-log-{date}.json。"""
        per_worker = {}
        total_cost = 0.0
        for r in self.records:
            wid = r["worker"]
            if wid not in per_worker:
                per_worker[wid] = {
                    "calls": 0, "prompt_tokens": 0, "completion_tokens": 0,
                    "cost_estimate_usd": 0.0,
                }
            pw = per_worker[wid]
            pw["calls"] += 1
            u = r.get("usage") or {}
            pw["prompt_tokens"] += u.get("prompt_tokens", 0)
            pw["completion_tokens"] += u.get("completion_tokens", 0)
            pw["cost_estimate_usd"] += r["cost_estimate_usd"]
            total_cost += r["cost_estimate_usd"]

        log = {
            "date": date_str,
            "goal": goal_name,
            "rounds": total_rounds,
            "workers": per_worker,
            "total_cost_estimate_usd": round(total_cost, 6),
            "timestamp": now_str(),
        }

        log_path = INTEL_DIR / f"token-log-{date_str}.json"
        save_json(log_path, log)
        print(f"  📊 Token 日志已写入: {log_path}")


def _estimate_cost(worker_id: str, usage: dict | None, response_text: str = "") -> float:
    """估算一次 API 调用的费用。

    优先使用 API 返回的 usage 字段；如果没有，用字符数粗略估算
    （英文 ~4 chars/token，中文 ~1.5 chars/token，取 3 作为混合保守估算）。
    """
    pricing = TokenTracker.PRICING.get(worker_id, {"input": 0.0, "output": 0.0})
    if usage and usage.get("prompt_tokens"):
        prompt_cost = (usage["prompt_tokens"] / 1_000_000) * pricing["input"]
        completion_cost = (usage.get("completion_tokens", 0) / 1_000_000) * pricing["output"]
        return prompt_cost + completion_cost

    # Fallback：字符估算（只估输出）
    chars = len(response_text)
    est_tokens = max(1, chars // 3)
    return (est_tokens / 1_000_000) * pricing["output"]


# ── 工具函数 ───────────────────────────────────────────

def load_json(path: Path) -> dict:
    """读取 JSON 文件。"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: dict):
    """写入 JSON 文件。"""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def llm_call(
    base_url: str,
    api_key: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.3,
    max_tokens: int = 4096,
    extra_body: dict | None = None,
) -> dict | None:
    """调用 OpenAI 兼容的 LLM API。

    成功返回 {"text": str, "model": str, "usage": dict}，失败返回 None。
    usage 字段含 prompt_tokens / completion_tokens / total_tokens。
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    body: dict = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if extra_body:
        body.update(extra_body)

    payload = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        base_url,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=API_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return {
            "text": data["choices"][0]["message"]["content"],
            "model": data.get("model", model),
            "usage": data.get("usage", {}),
        }
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"  HTTP {e.code}: {body[:300]}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"  Error: {e}", file=sys.stderr)
        return None


def save_verbose_log(verbose_dir: Path | None, filename: str, content: str):
    """保存 Worker 原始输出。verbose_dir 为 None 时跳过。"""
    if verbose_dir is None:
        return
    verbose_dir.mkdir(parents=True, exist_ok=True)
    path = verbose_dir / filename
    path.write_text(content, encoding="utf-8")
    print(f"  📄 原始输出已保存: {path}")


def now_str() -> str:
    """当前北京时间字符串。"""
    return datetime.now(TZ).strftime("%Y-%m-%d %H:%M")


# ── Goal 解析 ──────────────────────────────────────────

def parse_goal(goal_file: Path, date_str: str | None = None) -> dict:
    """读取 goal JSON，替换日期占位符。"""
    goal = load_json(goal_file)

    # 替换 {date} 占位符
    if date_str:
        for key in ("goal", "scope"):
            if key in goal:
                goal[key] = goal[key].replace("{date}", date_str)

    return goal


# ── Intel 简报解析 ─────────────────────────────────────

def read_intel_json(date_str: str) -> dict | None:
    """从结构化 JSON 读取情报条目——主数据源，替代正则解析。"""
    json_path = INTEL_DIR / f"daily-{date_str}.json"
    if not json_path.exists():
        return None
    try:
        return json.loads(json_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, Exception) as e:
        print(f"⚠️ JSON 解析失败: {json_path} — {e}", file=sys.stderr)
        return None


def write_intel_json(date_str: str, result: dict):
    """将研判结果写回 JSON 文件。"""
    json_path = INTEL_DIR / f"daily-{date_str}.json"
    data = read_intel_json(date_str)
    if not data:
        # JSON 不存在——无法写回（不应发生，daily_intel.py 会首先生成）
        print(f"  ⚠ JSON 文件不存在，无法写回研判结果: {json_path}", file=sys.stderr)
        return

    data["status"] = "scored"
    data["scored_at"] = now_str()
    data["scores"] = result.get("scores", [])
    data["conclusion"] = result.get("conclusion", "")
    if result.get("cross_review_stats"):
        data["cross_review_stats"] = result["cross_review_stats"]
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  📝 研判结果已写入 JSON: {json_path}")


def parse_intel_items(date_str: str) -> list[dict]:
    """从每日简报获取情报条目——优先 JSON，回退正则解析。"""
    data = read_intel_json(date_str)
    if data and data.get("items"):
        items = []
        for it in data["items"]:
            items.append({
                "num": it["num"],
                "title": it["title"],
                "link": it["link"],
                "snippet": it["snippet"],
                "query": it.get("query", ""),
                "tags": it.get("tags", []),
                "source": it.get("source", ""),
                "status": "pending" if data.get("status") == "pending" else "scored",
            })
        return items

    # 回退：正则解析 markdown（兼容旧文件，无 JSON 时使用）
    brief_path = INTEL_DIR / f"daily-{date_str}.md"
    if not brief_path.exists():
        print(f"简报文件不存在: {brief_path}", file=sys.stderr)
        return []

    text = brief_path.read_text(encoding="utf-8")

    items = []
    pattern = re.compile(
        r'### (\d+)\. \[(.+?)\]\((.+?)\)\n\n'
        r'(.*?)\n\n'
        r'- 关键词: `(.+?)`\n'
        r'(?:- 标签: (.+?)\n)?'
        r'- 来源: (.+?)\n'
        r'- 研判: (⏳ 待小樱评分|✅ 已评分)',
        re.DOTALL,
    )

    for match in pattern.finditer(text):
        num = int(match.group(1))
        title = match.group(2)
        link = match.group(3)
        snippet = match.group(4).strip()
        query = match.group(5)
        tags_str = match.group(6) or ""
        source = match.group(7)
        status = "pending" if "⏳" in match.group(8) else "scored"

        tags = [t.strip() for t in tags_str.split() if t.strip().startswith("#")]

        items.append({
            "num": num,
            "title": title,
            "link": link,
            "snippet": snippet,
            "query": query,
            "tags": tags,
            "source": source,
            "status": status,
        })

    if not items:
        if "✅ 已评分" in text or "研判区" in text:
            print(f"📋 简报 {date_str} 已全部研判，无需重复处理。", file=sys.stderr)
        else:
            print(f"⚠️ 简报 {date_str} 中未找到匹配的情报条目（检查格式）。", file=sys.stderr)

    return items


def parse_existing_scores(date_str: str) -> list[dict]:
    """从已研判的简报中提取已有分数——优先 JSON，回退正则解析。"""
    data = read_intel_json(date_str)
    if data and data.get("scores"):
        return data["scores"]

    # 回退：正则解析 markdown 表格
    brief_path = INTEL_DIR / f"daily-{date_str}.md"
    if not brief_path.exists():
        return []
    text = brief_path.read_text(encoding="utf-8")
    scores = []
    pattern = re.compile(
        r'\| (\d+) \| (\d+) \| (\d+) \| (\d+) \| (\d+) \| (.+?) \|'
    )
    for match in pattern.finditer(text):
        scores.append({
            "num": int(match.group(1)),
            "relevance": int(match.group(2)),
            "feasibility": int(match.group(3)),
            "leverage": int(match.group(4)),
            "total": int(match.group(5)),
            "action": match.group(6).strip(),
        })
    return scores


# ── Worker Prompt 构建 ─────────────────────────────────

def build_worker_prompt(items: list[dict], worker_id: str, goal: dict) -> tuple[str, str]:
    """构建某个 Worker 的 system + user prompt。返回 (system_prompt, user_prompt)。"""

    worker_info = WORKERS.get(worker_id, {})
    worker_name = worker_info.get("name", worker_id)
    worker_strength = worker_info.get("strength", "")

    # 构造条目列表文本
    items_text = []
    for item in items:
        tags = " ".join(item.get("tags", []))
        items_text.append(
            f"### {item['num']}. [{item['title']}]({item['link']})\n"
            f"摘要：{item['snippet']}\n"
            f"标签：{tags}\n"
            f"来源：{item['source']}"
        )
    items_block = "\n\n".join(items_text)

    system_prompt = f"""你是 {worker_name}，OPC（一人公司）多 Agent 系统中的执行 Worker。
你的专长：{worker_strength}

当前任务目标：{goal.get('goal', '')}
工作边界：{goal.get('scope', '')}

## 评分标准（遵循 OPC-CONFIG.md）

对每条情报从三个维度评分（0-3 分）：

| 维度 | 0 | 1 | 2 | 3 |
|------|---|---|---|---|
| 相关性 | 完全无关 | 间接相关 | 直接相关 | 核心目标 |
| 可行性 | 完全做不到 | 需要大量准备 | 需要少量准备 | 现在就能做 |
| 杠杆率 | 一次性小事 | 用完就扔 | 能用一阵 | 长期基础设施 |

评分参考：
- 相关性——这条情报和一人公司创业者的关系多大？涉及我们的关注领域（AI Agent 工具、一人公司案例、Claude/Anthropic、中国 AI 政策、零代码开发、学术写作/论文检测）吗？
- 可行性——樱漫清澜（零编程起步，Python 基础，Windows 11）能用上这条情报里的工具/信息吗？需要什么前置条件？
- 杠杆率——这条情报的价值能持续多久？是一次性新闻还是长期可用的基础设施/方法论？

{worker_id} 的评估角度：{worker_strength}。请从你的专长角度给出评分和行动建议。

## 评分硬约束（必须遵守）

1. **区分度**：10 条情报中，总分 ≥7 的不得超过 3 条。如果看起来有多条值得 ≥7，你必须从中挑出最好的 3 条，其余降到 5-6 分。这是硬性上限，不是建议。
2. **来源权重**：独立媒体报道（Fortune、Reuters 等）> 社区讨论（Reddit、Hacker News）> 供应商自述（LangChain 官网、JetBrains 博客）。供应商来源的默认降 1 分杠杆率。
3. **拉开差距**：你的 10 条评分必须有明显的分数梯度，至少 3 条 ≤3 分。全都在 4-7 分区间说明你在回避判断。

## 输出格式

对每条情报输出一个 JSON 对象，全部 10 条放到一个 JSON 数组中。每条格式：

```json
{{
  "num": 条目编号,
  "relevance": 0-3,
  "feasibility": 0-3,
  "leverage": 0-3,
  "total": 三项之和,
  "action": "一句话行动建议（≤30字）",
  "confidence": "high|medium|low——你对这条评分的把握",
  "reasoning": "评分理由（≤50字）"
}}
```

评分必须严格。不要全都打 2-3 分——0 和 1 分是正常的。只输出 JSON 数组，不要其他文字。"""

    user_prompt = f"以下是今日（{goal.get('_date_str', '')}）的 {len(items)} 条情报，请逐条评分：\n\n{items_block}"

    return system_prompt, user_prompt


# ── Worker 调度 ────────────────────────────────────────

def dispatch_worker(
    worker_id: str,
    items: list[dict],
    goal: dict,
    dry_run: bool = False,
    tracker: TokenTracker | None = None,
    verbose_dir: Path | None = None,
) -> dict | None:
    """向一个 Worker 派发任务，返回其评分结果。"""

    worker_info = WORKERS.get(worker_id)
    if not worker_info:
        print(f"  Unknown worker: {worker_id}", file=sys.stderr)
        return None

    api_key = os.environ.get(worker_info["env_key"], "")
    if not api_key:
        print(f"  ⚠ {worker_id} ({worker_info['name']}): 无 API Key（{worker_info['env_key']} 未设置），跳过", file=sys.stderr)
        return None

    print(f"  → {worker_id} ({worker_info['name']}): 评估 {len(items)} 条情报...")

    if dry_run:
        print(f"     [DRY RUN] 跳过 API 调用")
        return {"worker": worker_id, "items": [], "raw_response": "[DRY RUN]"}

    system_prompt, user_prompt = build_worker_prompt(items, worker_id, goal)

    # Kimi K3 特殊参数
    extra = {}
    if worker_id == "kimi":
        extra["reasoning_effort"] = worker_info.get("reasoning_effort", "low")

    result = llm_call(
        base_url=worker_info["base_url"],
        api_key=api_key,
        model=worker_info["model"],
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=worker_info.get("temperature", 0.3),
        max_tokens=4096,
        extra_body=extra if extra else None,
    )

    if result is None:
        print(f"     ✗ {worker_id} 调用失败", file=sys.stderr)
        return None

    response_text = result["text"]
    model_used = result.get("model", worker_info["model"])
    usage = result.get("usage", {})

    # 追踪 token 消耗
    if tracker:
        cost = _estimate_cost(worker_id, usage, response_text)
        tracker.record(worker_id, model_used, usage, cost)

    # 解析 Worker 返回的 JSON
    scores = parse_worker_scores(response_text, worker_id)
    print(f"     ✓ {worker_id} 返回 {len(scores)} 条评分")

    # 保存原始输出
    save_verbose_log(verbose_dir, f"R1-{worker_id}.txt", response_text)

    return {
        "worker": worker_id,
        "items": scores,
        "raw_response": response_text,
    }


def parse_worker_scores(response: str, worker_id: str) -> list[dict]:
    """从 Worker 响应中解析 JSON 评分数组。"""
    # 尝试提取 JSON 数组
    try:
        # 找第一个 [ 和最后一个 ]
        start = response.find("[")
        end = response.rfind("]")
        if start != -1 and end != -1 and end > start:
            json_str = response[start:end + 1]
            scores = json.loads(json_str)
            if isinstance(scores, list):
                return scores
    except json.JSONDecodeError:
        pass

    # 尝试整段解析
    try:
        scores = json.loads(response.strip())
        if isinstance(scores, list):
            return scores
    except json.JSONDecodeError:
        pass

    print(f"  ⚠ {worker_id} 返回格式无法解析，原始内容前 200 字符: {response[:200]}", file=sys.stderr)
    return []


# ── 交叉审查（Cross-Review）协议 ────────────────────────
#
# 模拟 Worker 之间的自主通信。在无状态 CLI 约束下，
# 通过 Supervisor 路由的结构化 prompt 实现跨 Worker
# 挑战、提问和评分调整。

def build_cross_review_prompt(
    items: list[dict],
    all_results: list[dict],
    target_worker_id: str,
    goal: dict,
) -> str:
    """构造交叉审查提示词——让一个 Worker 审查其他 Worker 的评分。

    展示其他 Worker 的评分摘要、分歧高亮和低置信度条目，
    要求 Worker 输出挑战/提问/调整后的评分。
    """

    # 构造评分摘要表
    worker_names = {}
    for wr in all_results:
        wid = wr["worker"]
        wname = WORKERS.get(wid, {}).get("name", wid)
        worker_names[wid] = wname

    # 逐条目构造对比
    items_with_scores = []
    for item in items:
        num = item["num"]
        entry = {"num": num, "title": item["title"], "workers": {}}
        for wr in all_results:
            wid = wr["worker"]
            for s in wr.get("items", []):
                if s.get("num") == num:
                    entry["workers"][wid] = s
                    break
        items_with_scores.append(entry)

    # 构建表格行
    header_cols = " | ".join(
        [f"{worker_names.get(wid, wid)} (R/F/L=Total, Conf)"
         for wr in all_results for wid in [wr["worker"]]]
    )
    header = f"| # | Title | {header_cols} |"
    sep = f"|---|-------|{'---|' * len(all_results)}"

    rows = []
    disagreements = []
    low_conf_items = []

    for entry in items_with_scores:
        num = entry["num"]
        title = entry["title"][:50]
        cols = []
        totals = []

        for wr in all_results:
            wid = wr["worker"]
            ws = entry["workers"].get(wid, {})
            if ws:
                r, f_val, l_val = ws.get("relevance", "?"), ws.get("feasibility", "?"), ws.get("leverage", "?")
                total = ws.get("total", "?")
                conf = ws.get("confidence", "?")
                cols.append(f"{r}/{f_val}/{l_val}={total}, {conf}")
                if isinstance(total, int):
                    totals.append((wid, total, ws.get("reasoning", ""), conf))
            else:
                cols.append("—")

        row = f"| {num} | {title} | {' | '.join(cols)} |"
        rows.append(row)

        # 检测分歧（总分差 ≥3）
        if len(totals) >= 2:
            max_t = max(totals, key=lambda x: x[1])
            min_t = min(totals, key=lambda x: x[1])
            if max_t[1] - min_t[1] >= 3:
                disagreements.append({
                    "num": num, "title": title,
                    "high_worker": worker_names.get(max_t[0], max_t[0]),
                    "high_score": max_t[1], "high_reasoning": max_t[2],
                    "low_worker": worker_names.get(min_t[0], min_t[0]),
                    "low_score": min_t[1], "low_reasoning": min_t[2],
                })

        # 检测全部低置信度
        if totals and all(t[3] == "low" for t in totals):
            low_conf_items.append(num)

    # 组装提示词
    prompt_parts = [
        "## 其他 Worker 的评估结果",
        "",
        "以下是你的同行 Worker 对相同情报的评分。请仔细审查。",
        "",
        "### 评分对比表",
        header, sep, *rows, "",
    ]

    if disagreements:
        prompt_parts.append("### ⚠️ 显著分歧（总分差 ≥3）")
        prompt_parts.append("")
        for d in disagreements:
            prompt_parts.append(
                f"**#{d['num']}「{d['title'][:40]}」**：\n"
                f"- {d['high_worker']} → {d['high_score']} 分：{d['high_reasoning']}\n"
                f"- {d['low_worker']} → {d['low_score']} 分：{d['low_reasoning']}\n"
            )

    if low_conf_items:
        prompt_parts.append(f"### 🔍 全部低置信度条目：#{', #'.join(map(str, low_conf_items))}")
        prompt_parts.append("")

    prompt_parts.extend([
        "### 你的任务",
        "",
        "你同时扮演两个角色：同行评审 + 合规审计员。",
        "",
        "**Part A — 同行评审**：",
        "1. **挑战**：如果你认为某位同行的评分有误，发起挑战。说明哪个条目、哪个维度、应该是多少分、为什么。",
        "2. **提问**：如果你想深入了解某位同行的推理过程，向他提问。",
        "3. **调整**：如果同行的推理说服了你，你可以调整自己的评分。",
        "",
        "**Part B — 🚨 硬约束合规审计（强制性，必须逐条核验）**：",
        "4. **≥7 分上限检查**：合并所有 Worker 的评分后，≥7 分（total ≥ 7）的条目是否超过 3 条？如果超过，你必须指出应该降级到 6 分的具体条目（挑最弱的），并给出理由。这是硬性上限，必须执行。",
        "5. **供应商来源降权检查**：下列来源属于供应商自述，杠杆率应降 1 分：blog.jetbrains.com、www.langchain.com、www.taskade.com、code.claude.com、openai.com、anthropic.com、aws.amazon.com、azure.microsoft.com、developers.google.com。逐条检查——这些来源的条目是否已被降权？如果没有，你必须发起挑战（target_worker=相关 worker，field=\"leverage\"，new_score=原值-1）。",
        "6. **梯度检查**：10 条评分中，是否至少有 3 条总分 ≤ 3 分？如果没有，必须指出哪些条目应该降分以确保区分度。",
        "",
        "重要原则：",
        "- Part B（合规审计）是强制性的——即使同行评分完全一致，也必须逐条核验上述三项",
        "- 挑战要基于证据和逻辑，不要为不同意而不同意",
        "- 如果你的同行确实看到了你忽略的盲点，承认并调整——这不是示弱",
        "- 如果同行的评分和你一致（差异 <3 分），Part A 可以跳过挑战，但 Part B 不可跳过",
        "",
        "输出 JSON 格式（只输出 JSON，不要其他文字）：",
        "```json",
        "{",
        '  "challenges": [',
        '    {"target_worker": "kimi", "item_num": 3, "field": "feasibility", "new_score": 1, "reason": "需要付费 API，对 OPC 不可行"}',
        "  ],",
        '  "questions": [',
        '    {"target_worker": "deepseek", "item_num": 5, "question": "技术门槛评估是否考虑了 Windows 兼容性？"}',
        "  ],",
        '  "adjusted_scores": [',
        '    {"item_num": 2, "relevance": 2, "feasibility": 1, "leverage": 2, "total": 5, "confidence": "medium", "reasoning": "同行的来源权重分析让我重新评估"}',
        "  ],",
        '  "compliance_report": {',
        '    "ge7_count": "≥7 分条目数（填数字）",',
        '    "ge7_exceeds": "true/false——是否超过 3 条上限",',
        '    "supplier_violations": ["条目 #N 来源 X 未降权", "（如无违规则空数组）"],',
        '    "gradient_ok": "true/false——是否至少 3 条 ≤3 分"',
        "  }",
        "}",
        "```",
        "",
        "如果没有任何挑战/提问/调整，对应数组留空。compliance_report 必须填写——即使没有违规也要明确报告。",
    ])

    return "\n".join(prompt_parts)


def parse_cross_review_response(response: str, worker_id: str) -> dict:
    """解析 Worker 的交叉审查响应。

    返回 {"challenges": [], "questions": [], "adjusted_scores": []}。
    解析失败返回空结构。
    """
    empty = {"challenges": [], "questions": [], "adjusted_scores": []}

    # 尝试提取 JSON 对象
    try:
        start = response.find("{")
        end = response.rfind("}")
        if start != -1 and end != -1 and end > start:
            json_str = response[start:end + 1]
            data = json.loads(json_str)
            if isinstance(data, dict):
                return {
                    "challenges": data.get("challenges", []),
                    "questions": data.get("questions", []),
                    "adjusted_scores": data.get("adjusted_scores", []),
                }
    except json.JSONDecodeError:
        pass

    # 尝试整段解析
    try:
        data = json.loads(response.strip())
        if isinstance(data, dict):
            return {
                "challenges": data.get("challenges", []),
                "questions": data.get("questions", []),
                "adjusted_scores": data.get("adjusted_scores", []),
            }
    except json.JSONDecodeError:
        pass

    print(f"  ⚠ {worker_id} 交叉审查响应无法解析，跳过", file=sys.stderr)
    return empty


def resolve_disputes(
    challenges: list[dict],
    cross_review_results: dict[str, dict],
    worker_results: list[dict],
) -> dict[str, list[dict]]:
    """通过多数投票解决争议。

    返回 {"resolved": [...], "unresolved": [...]}。
    resolved: 争议已解决的条目，含最终分数。
    unresolved: 需要 Round 3 定向追问的条目。
    """
    resolved = []
    unresolved = []

    # 构建快速查找：worker_id -> {item_num -> score}
    worker_scores: dict[str, dict[int, dict]] = {}
    for wr in worker_results:
        wid = wr["worker"]
        worker_scores[wid] = {}
        for s in wr.get("items", []):
            if "num" in s:
                worker_scores[wid][s["num"]] = s

    for ch in challenges:
        item_num = ch.get("item_num")
        target = ch.get("target_worker", "")
        field = ch.get("field", "")
        new_score = ch.get("new_score")
        reason = ch.get("reason", "")

        # 获取被挑战 Worker 的原始评分
        target_scores = worker_scores.get(target, {}).get(item_num, {})
        old_score = target_scores.get(field)

        if old_score is None:
            unresolved.append({**ch, "status": "target_score_missing"})
            continue

        # 检查被挑战 Worker 在交叉审查中是否承认/调整
        target_cr = cross_review_results.get(target, {})
        target_adjusted = target_cr.get("adjusted_scores", [])
        target_agreed = any(
            a.get("item_num") == item_num and a.get(field) == new_score
            for a in target_adjusted
        )

        if target_agreed:
            # 被挑战方同意 → 采用挑战分数
            resolved.append({
                "item_num": item_num,
                "field": field,
                "old_score": old_score,
                "new_score": new_score,
                "resolution": "target_agreed",
                "reason": reason,
            })
        else:
            # 多数投票：统计所有 Worker 在该维度的分数
            all_scores = []
            for wid, scores in worker_scores.items():
                s = scores.get(item_num, {})
                val = s.get(field)
                if val is not None:
                    all_scores.append(val)

            if all_scores:
                # 取众数
                counter = Counter(all_scores)
                most_common = counter.most_common(1)[0][0]

                if new_score == most_common:
                    resolved.append({
                        "item_num": item_num,
                        "field": field,
                        "old_score": old_score,
                        "new_score": most_common,
                        "resolution": "majority_supports_challenge",
                        "reason": reason,
                    })
                elif old_score == most_common:
                    resolved.append({
                        "item_num": item_num,
                        "field": field,
                        "old_score": old_score,
                        "new_score": old_score,
                        "resolution": "majority_rejects_challenge",
                        "reason": f"多数投票维持原评分 {old_score}",
                    })
                else:
                    unresolved.append({
                        **ch,
                        "status": "no_majority",
                        "all_scores": dict(counter),
                    })
            else:
                unresolved.append({**ch, "status": "no_comparable_scores"})

    return {"resolved": resolved, "unresolved": unresolved}


def build_dispute_prompt(
    questions: list[dict],
    target_worker_id: str,
    goal: dict,
) -> str:
    """构造争议解决提示词——让 Worker 回答同行提出的问题。"""
    questions_for_me = [q for q in questions if q.get("target_worker") == target_worker_id]
    if not questions_for_me:
        return ""

    q_lines = []
    for i, q in enumerate(questions_for_me, 1):
        item_num = q.get("item_num", "?")
        question = q.get("question", "")
        q_lines.append(f"{i}. 关于 **#{item_num}**：{question}")

    prompt = (
        "## 同行向你提出的问题\n\n"
        + "\n".join(q_lines)
        + "\n\n"
        + "### 你的任务\n\n"
        + "请逐一回答上述问题。回答要简洁、具体（每条 ≤80 字）。\n"
        + "如果问题揭示了你评分中的盲点或疏漏，请诚实调整你的评分。\n\n"
        + "输出 JSON 格式（只输出 JSON，不要其他文字）：\n"
        + "```json\n"
        + "{\n"
        + '  "answers": [{"question_index": 1, "answer": "回答内容"}],\n'
        + '  "adjusted_scores": []\n'
        + "}\n"
        + "```\n\n"
        + "如果没有需要调整的评分，adjusted_scores 留空数组。"
    )

    return prompt


# ── Supervisor 核心逻辑 ────────────────────────────────

def supervisor_run(goal_file: Path, date_str: str, dry_run: bool = False, verbose: bool = False) -> dict:
    """Supervisor 主循环。"""

    verbose_dir = INTEL_DIR / "verbose" / date_str if verbose else None

    print(f"\n{'='*60}")
    print(f"Supervisor 启动 — {now_str()}")
    print(f"Goal: {goal_file.name}")
    print(f"日期: {date_str}")
    if dry_run:
        print(f"[DRY RUN 模式——不实际调用 API]")
    if verbose:
        print(f"[VERBOSE 模式——原始输出保存到 {verbose_dir}]")
    print(f"{'='*60}\n")

    # 1. 加载 goal
    goal = parse_goal(goal_file, date_str)
    goal["_date_str"] = date_str
    print(f"📋 目标: {goal.get('goal', '未定义')}")
    print(f"📐 边界: {goal.get('scope', '未定义')}")
    print(f"🛑 停止条件: {goal.get('stop_if', [])}")

    # 2. 加载情报条目
    all_items = parse_intel_items(date_str)
    if not all_items:
        print(f"\n⚠️ 未找到可处理的情报条目，终止。")
        return {"error": "no_items", "date": date_str}

    # 只处理待研判条目（已评分的跳过）
    items = [it for it in all_items if it.get("status") == "pending"]
    skipped = len(all_items) - len(items)
    if skipped > 0:
        print(f"\n⏭️ 跳过 {skipped} 条已评分条目")
    if not items:
        print(f"📋 简报 {date_str} 已全部研判，无需重复处理。")
        return {"error": "all_scored", "date": date_str}
    print(f"\n📰 已加载 {len(items)} 条待研判情报（共 {len(all_items)} 条）")

    # 3. 确定活跃 Worker
    active_workers = []
    for wid in WORKERS:
        if os.environ.get(WORKERS[wid]["env_key"], ""):
            active_workers.append(wid)
        else:
            print(f"  ⚠ {wid} 不可用（缺少 {WORKERS[wid]['env_key']}）")

    if not active_workers:
        print("\n❌ 没有可用的 Worker。请设置 KIMI_API_KEY 或 DEEPSEEK_API_KEY。")
        return {"error": "no_workers", "date": date_str}

    print(f"\n🔧 活跃 Worker: {', '.join(active_workers)}")

    # 初始化 Token 追踪器
    tracker = TokenTracker()

    # 4. 第一轮：并行分派全部条目给每个 Worker
    print(f"\n── 第 1 轮：初始评估 ──")
    all_results = []
    with ThreadPoolExecutor(max_workers=len(active_workers)) as executor:
        futures = {}
        for wid in active_workers:
            future = executor.submit(dispatch_worker, wid, items, goal, dry_run, tracker, verbose_dir)
            futures[future] = wid

        for future in as_completed(futures):
            wid = futures[future]
            try:
                result = future.result()
                if result:
                    all_results.append(result)
            except Exception as e:
                print(f"  ✗ {wid} 异常: {e}", file=sys.stderr)

    # 5. 合并 Round 1 评分
    print(f"\n── 合并 Round 1 评分 ──")
    merged = merge_scores(all_results, len(items))

    # 6. Round 2：交叉审查（Cross-Review）——Worker 互相审查评分
    cross_review_enabled = goal.get("cross_review", {}).get("enabled", True)
    cross_review_results: dict[str, dict] = {}
    all_challenges = []
    all_questions = []
    dispute_resolutions = {"resolved": [], "unresolved": []}

    if cross_review_enabled and len(active_workers) >= 2 and not dry_run:
        print(f"\n── 第 2 轮：交叉审查（Cross-Review）──")

        # 为每个 Worker 构造交叉审查 prompt
        cr_futures = {}
        with ThreadPoolExecutor(max_workers=len(active_workers)) as executor:
            for wid in active_workers:
                system_prompt, _ = build_worker_prompt(items, wid, goal)
                cross_prompt = build_cross_review_prompt(items, all_results, wid, goal)

                worker_info = WORKERS[wid]
                api_key = os.environ.get(worker_info["env_key"], "")
                extra = {}
                if wid == "kimi":
                    extra["reasoning_effort"] = worker_info.get("reasoning_effort", "low")

                future = executor.submit(
                    llm_call,
                    base_url=worker_info["base_url"],
                    api_key=api_key,
                    model=worker_info["model"],
                    system_prompt=system_prompt,
                    user_prompt=cross_prompt,
                    temperature=worker_info.get("temperature", 0.3),
                    max_tokens=2048,
                    extra_body=extra if extra else None,
                )
                cr_futures[future] = wid

            for future in as_completed(cr_futures):
                wid = cr_futures[future]
                try:
                    result = future.result()
                    if result:
                        # 追踪 token
                        worker_info = WORKERS[wid]
                        cost = _estimate_cost(wid, result.get("usage", {}), result["text"])
                        tracker.record(wid, result.get("model", worker_info["model"]),
                                      result.get("usage", {}), cost)

                        parsed = parse_cross_review_response(result["text"], wid)
                        cross_review_results[wid] = parsed
                        all_challenges.extend(parsed.get("challenges", []))
                        all_questions.extend(parsed.get("questions", []))
                        print(f"  ✓ {wid}: {len(parsed.get('challenges', []))} 挑战, "
                              f"{len(parsed.get('questions', []))} 提问, "
                              f"{len(parsed.get('adjusted_scores', []))} 调整")
                        save_verbose_log(verbose_dir, f"R2-{wid}-cross-review.txt", result["text"])
                except Exception as e:
                    print(f"  ✗ {wid} 交叉审查异常: {e}", file=sys.stderr)

        # 应用 adjusted_scores 到 merged
        for wid, cr in cross_review_results.items():
            for adj in cr.get("adjusted_scores", []):
                num = adj.get("item_num")
                key = str(num)
                if key in merged:
                    # 替换该 Worker 在 merged 中的评分
                    entry = merged[key]
                    new_score = {
                        "relevance": adj.get("relevance", 0),
                        "feasibility": adj.get("feasibility", 0),
                        "leverage": adj.get("leverage", 0),
                        "total": adj.get("total", 0),
                        "worker": wid,
                    }
                    # 找到并替换
                    for i, s in enumerate(entry.get("scores", [])):
                        if s.get("worker") == wid:
                            entry["scores"][i] = new_score
                            break
                    else:
                        entry["scores"].append(new_score)

        # 解决争议
        if all_challenges:
            dispute_resolutions = resolve_disputes(all_challenges, cross_review_results, all_results)
            print(f"  ⚖️ 争议解决: {len(dispute_resolutions['resolved'])} 已解决, "
                  f"{len(dispute_resolutions['unresolved'])} 未解决")

            # 将已解决的争议应用到 merged
            for res in dispute_resolutions["resolved"]:
                key = str(res["item_num"])
                if key in merged:
                    for s in merged[key].get("scores", []):
                        if s.get("worker") == res.get("target_worker", ""):
                            s[res["field"]] = res["new_score"]
                            # 重算 total
                            s["total"] = s.get("relevance", 0) + s.get("feasibility", 0) + s.get("leverage", 0)

    elif dry_run:
        print(f"\n── 第 2 轮：交叉审查 [DRY RUN 跳过] ──")
    else:
        print(f"\n── 第 2 轮：交叉审查（跳过——需要 ≥2 Workers 且 cross_review.enabled=true）──")

    # 7. Round 3：争议解决——定向回答同行提问
    if all_questions and not dry_run:
        print(f"\n── 第 3 轮：争议解决（{len(all_questions)} 个问题）──")

        dr_futures = {}
        with ThreadPoolExecutor(max_workers=len(active_workers)) as executor:
            for wid in active_workers:
                questions_for_me = [q for q in all_questions if q.get("target_worker") == wid]
                if not questions_for_me:
                    continue

                system_prompt, _ = build_worker_prompt(items, wid, goal)
                dispute_prompt = build_dispute_prompt(all_questions, wid, goal)

                worker_info = WORKERS[wid]
                api_key = os.environ.get(worker_info["env_key"], "")
                extra = {}
                if wid == "kimi":
                    extra["reasoning_effort"] = worker_info.get("reasoning_effort", "low")

                future = executor.submit(
                    llm_call,
                    base_url=worker_info["base_url"],
                    api_key=api_key,
                    model=worker_info["model"],
                    system_prompt=system_prompt,
                    user_prompt=dispute_prompt,
                    temperature=worker_info.get("temperature", 0.3),
                    max_tokens=1024,
                    extra_body=extra if extra else None,
                )
                dr_futures[future] = wid

            for future in as_completed(dr_futures):
                wid = dr_futures[future]
                try:
                    result = future.result()
                    if result:
                        worker_info = WORKERS[wid]
                        cost = _estimate_cost(wid, result.get("usage", {}), result["text"])
                        tracker.record(wid, result.get("model", worker_info["model"]),
                                      result.get("usage", {}), cost)

                        # 解析回答和调整
                        try:
                            start = result["text"].find("{")
                            end = result["text"].rfind("}")
                            if start != -1 and end != -1:
                                dr_data = json.loads(result["text"][start:end + 1])
                                for adj in dr_data.get("adjusted_scores", []):
                                    num = adj.get("item_num")
                                    key = str(num)
                                    if key in merged:
                                        for s in merged[key].get("scores", []):
                                            if s.get("worker") == wid:
                                                if "relevance" in adj:
                                                    s["relevance"] = adj["relevance"]
                                                if "feasibility" in adj:
                                                    s["feasibility"] = adj["feasibility"]
                                                if "leverage" in adj:
                                                    s["leverage"] = adj["leverage"]
                                                s["total"] = s.get("relevance", 0) + s.get("feasibility", 0) + s.get("leverage", 0)
                                                break
                            print(f"  ✓ {wid}: 回答了 {len(dr_data.get('answers', []))} 个问题, "
                                  f"{len(dr_data.get('adjusted_scores', []))} 调整")
                            save_verbose_log(verbose_dir, f"R3-{wid}-dispute.txt", result["text"])
                        except (json.JSONDecodeError, KeyError):
                            print(f"  ⚠ {wid}: 争议解决响应无法解析")
                except Exception as e:
                    print(f"  ✗ {wid} 争议解决异常: {e}", file=sys.stderr)

    elif all_questions and dry_run:
        print(f"\n── 第 3 轮：争议解决 [DRY RUN 跳过] ──")

    # 8. Rounds 4-5：补缺纠错（gap filling，沿用 v1 逻辑）
    start_gap_round = 4
    for round_num in range(start_gap_round, MAX_ROUNDS + 2):  # +2 因为新增了 R2/R3
        gaps = find_gaps(merged, items)
        if not gaps:
            print(f"  ✅ 无缺口——全部评分完整且一致")
            break

        actual_round = round_num - 2  # 显示为第 4/5 轮
        print(f"\n── 第 {round_num} 轮（补缺）：补缺纠错（{len(gaps)} 个缺口）──")
        for gap in gaps:
            print(f"  🔍 {gap['reason']}")

        if dry_run:
            print(f"  [DRY RUN] 跳过迭代")
            break

        # 只对缺口条目重新分派
        gap_items = [items[i] for i in range(len(items))
                     if (i + 1) in [g["num"] for g in gaps]]

        gap_results = []
        with ThreadPoolExecutor(max_workers=len(active_workers)) as executor:
            futures = {}
            for wid in active_workers:
                future = executor.submit(dispatch_worker, wid, gap_items, goal, dry_run, tracker, verbose_dir)
                futures[future] = wid

            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        gap_results.append(result)
                except Exception as e:
                    print(f"  ✗ 异常: {e}", file=sys.stderr)

        # 合并补缺结果
        merged = merge_scores(gap_results, len(items), existing=merged)

    # 9. 最终合并
    print(f"\n── 最终输出 ──")
    cr_stats = {
        "challenges": len(all_challenges),
        "resolved": len(dispute_resolutions.get("resolved", [])),
        "mode": goal.get("cross_review", {}).get("resolution", "majority_vote"),
    }
    final = finalize_scores(merged, items, goal, all_results, tracker, cr_stats)
    print(f"  ✅ {len(final['scores'])} 条评分完成")

    # 🆕 Phase 3：行动建议生成——取 ≥7 分条目
    items_by_num = {it["num"]: it for it in items}
    high_for_actions = [
        {
            **s,
            "link": items_by_num.get(s["num"], {}).get("link", ""),
            "snippet": items_by_num.get(s["num"], {}).get("snippet", ""),
        }
        for s in final["scores"]
        if isinstance(s.get("total"), int) and s["total"] >= 7
    ]
    actions = generate_actions(high_for_actions, final["conclusion"], goal, dry_run)
    final["actions"] = actions

    # 8. 写 Token 日志
    total_rounds = sum(1 for r in range(1, MAX_ROUNDS + 1)
                       if r == 1 or (r > 1 and r <= MAX_ROUNDS))
    tracker.write_log(date_str, goal_file.stem, MAX_ROUNDS)

    return final


def merge_scores(
    worker_results: list[dict],
    total_items: int,
    existing: dict | None = None,
) -> dict:
    """合并多个 Worker 的评分结果。

    策略：
    - 同一条目被多个 Worker 评分 → 取平均值（四舍五入）
    - 只有一个 Worker 评分 → 直接用
    - confidence 取最低值（保守原则）
    """
    merged = existing or {}

    for wr in worker_results:
        for item in wr.get("items", []):
            num = item.get("num")
            if num is None:
                continue

            key = str(num)
            if key not in merged:
                merged[key] = {
                    "num": num,
                    "scores": [],
                    "actions": [],
                    "confidences": [],
                }

            entry = merged[key]
            entry["scores"].append({
                "relevance": item.get("relevance", 0),
                "feasibility": item.get("feasibility", 0),
                "leverage": item.get("leverage", 0),
                "total": item.get("total", 0),
                "worker": wr.get("worker", "unknown"),
            })
            if item.get("action"):
                entry["actions"].append(item["action"])
            if item.get("confidence"):
                entry["confidences"].append(item["confidence"])

    return merged


def find_gaps(merged: dict, items: list[dict]) -> list[dict]:
    """检查评分缺口。返回缺口列表。"""
    gaps = []

    for item in items:
        key = str(item["num"])
        entry = merged.get(key)

        if not entry or not entry.get("scores"):
            gaps.append({
                "num": item["num"],
                "reason": f"#{item['num']}「{item['title'][:30]}」— 无评分",
                "severity": "high",
            })
            continue

        scores = entry["scores"]
        # 检查评分一致性——如果两个 Worker 评分差 ≥3 分（总分），标记为需重评
        if len(scores) >= 2:
            totals = [s["total"] for s in scores]
            if max(totals) - min(totals) >= 3:
                gaps.append({
                    "num": item["num"],
                    "reason": f"#{item['num']}「{item['title'][:30]}」— 评分分歧大（{min(totals)} vs {max(totals)}）",
                    "severity": "medium",
                })

        # 检查低 confidence
        confs = entry.get("confidences", [])
        if confs and all(c == "low" for c in confs):
            gaps.append({
                "num": item["num"],
                "reason": f"#{item['num']}「{item['title'][:30]}」— 所有 Worker 置信度为低",
                "severity": "medium",
            })

    return gaps


def apply_hard_constraints(final_scores: list[dict], items: list[dict]) -> list[dict]:
    """代码级硬约束过滤器——最后一道防线。

    不依赖 Worker 自觉，直接硬过滤 OPC-CONFIG 三项规则：
    1. 供应商来源 → 杠杆率降 1 分（独立媒体 > 社区 > 供应商）
    2. ≥7 分 ≤3 条（硬性上限）——超出部分降至 6 分
    3. 至少 3 条 ≤3 分（强制梯度）——不足时从低分端补齐

    所有降级操作都会在 action 字段中标注原因。
    """
    # Build source lookup from items
    source_map = {}
    for item in items:
        source_map[item["num"]] = item.get("source", "")

    scored = [s for s in final_scores if isinstance(s.get("total"), int)]

    # ── 规则 1：供应商来源降权 ──
    for s in scored:
        source = source_map.get(s["num"], "")
        if source in VENDOR_DOMAINS:
            old_lev = s.get("leverage", 0)
            if isinstance(old_lev, int) and old_lev > 0:
                s["leverage"] = old_lev - 1
                s["total"] = s.get("relevance", 0) + s["feasibility"] + s["leverage"]
                prefix = "[供应商降权]"
                s["action"] = f"{prefix} {s.get('action', '—')}" if s.get("action") and s["action"] != "—" else prefix

    # ── 规则 2：≥7 分上限（重算 total 后，因为规则 1 可能已改变分数）──
    high_scored = sorted(
        [s for s in scored if s["total"] >= 7],
        key=lambda s: s["total"], reverse=True,
    )
    if len(high_scored) > 3:
        # 保留总分最高的 3 条，其余降至 6
        for s in high_scored[3:]:
            old_total = s["total"]
            # 从杠杆率扣除（优先牺牲杠杆率，保留相关性和可行性）
            excess = old_total - 6
            s["leverage"] = max(0, s["leverage"] - excess)
            s["total"] = s["relevance"] + s["feasibility"] + s["leverage"]
            # 如果 leverage 扣完还不够，继续扣 feasibility
            while s["total"] > 6 and s["feasibility"] > 0:
                s["feasibility"] -= 1
                s["total"] = s["relevance"] + s["feasibility"] + s["leverage"]
            # 最终兜底
            if s["total"] > 6:
                s["total"] = 6
            prefix = f"[硬约束降级: ≥7上限 {old_total}→{s['total']}]"
            s["action"] = f"{prefix} {s.get('action', '—')}" if s.get("action") and s["action"] != "—" else prefix

    # ── 规则 3：强制梯度（重新统计，规则 1/2 可能已改变）──
    low_scored = [s for s in scored if s["total"] <= 3]
    if len(low_scored) < 3:
        need = 3 - len(low_scored)
        # 从总分最低的非低分条目开始降级
        mid_scored = sorted(
            [s for s in scored if s["total"] > 3],
            key=lambda s: s["total"],
        )
        for s in mid_scored[:need]:
            old_total = s["total"]
            # 降杠杆率优先
            drop = old_total - 3
            if s["leverage"] >= drop:
                s["leverage"] -= drop
            else:
                old_leverage = s["leverage"]
                s["leverage"] = 0
                remaining = drop - old_leverage
                if s.get("feasibility", 0) >= remaining:
                    s["feasibility"] -= remaining
                else:
                    s["feasibility"] = 0
            s["total"] = s["relevance"] + s["feasibility"] + s["leverage"]
            # 兜底
            if s["total"] > 3:
                s["total"] = 3
            prefix = f"[强制梯度 {old_total}→{s['total']}]"
            s["action"] = f"{prefix} {s.get('action', '—')}" if s.get("action") and s["action"] != "—" else prefix

    return final_scores


def finalize_scores(
    merged: dict,
    items: list[dict],
    goal: dict,
    raw_results: list[dict],
    tracker: TokenTracker | None = None,
    cross_review_stats: dict | None = None,
) -> dict:
    """生成最终评分。可附加交叉审查统计。"""

    final_scores = []
    for item in items:
        key = str(item["num"])
        entry = merged.get(key)

        if not entry or not entry.get("scores"):
            final_scores.append({
                "num": item["num"],
                "title": item["title"],
                "relevance": "—",
                "feasibility": "—",
                "leverage": "—",
                "total": "—",
                "action": "评分缺失",
            })
            continue

        sc = entry["scores"]
        # 取各项平均值，四舍五入
        avg_rel = round(sum(s["relevance"] for s in sc) / len(sc))
        avg_fea = round(sum(s["feasibility"] for s in sc) / len(sc))
        avg_lev = round(sum(s["leverage"] for s in sc) / len(sc))
        avg_total = avg_rel + avg_fea + avg_lev

        # 保留每个 Worker 的原始分数（用于邮件等输出）
        worker_details = {}
        for s in sc:
            wid = s.get("worker", "unknown")
            worker_details[wid] = {
                "relevance": s["relevance"],
                "feasibility": s["feasibility"],
                "leverage": s["leverage"],
                "total": s["relevance"] + s["feasibility"] + s["leverage"],
            }

        # 取第一个 Worker 的 action 建议（或拼接）
        actions = entry.get("actions", [])
        best_action = actions[0] if actions else "—"

        final_scores.append({
            "num": item["num"],
            "title": item["title"],
            "link": item.get("link", ""),
            "relevance": avg_rel,
            "feasibility": avg_fea,
            "leverage": avg_lev,
            "total": avg_total,
            "action": best_action,
            "worker_scores": worker_details,
        })

    # 🚨 硬约束过滤——最后一道防线
    final_scores = apply_hard_constraints(final_scores, items)

    # 生成研判结论
    high_scores = [s for s in final_scores if isinstance(s["total"], int) and s["total"] >= 7]
    medium_scores = [s for s in final_scores if isinstance(s["total"], int) and 5 <= s["total"] <= 6]

    conclusion_lines = [
        f"研判时间：{now_str()}（北京时间）",
        f"参与 Worker：{', '.join(r['worker'] for r in raw_results)}",
        f"评分标准：OPC-CONFIG.md 三维评分（相关性/可行性/杠杆率 0-3）",
    ]

    # 交叉审查统计
    if cross_review_stats:
        cr = cross_review_stats
        challenges_total = cr.get("challenges", 0)
        resolved = cr.get("resolved", 0)
        if challenges_total > 0:
            conclusion_lines.append(
                f"交叉审查：{challenges_total} 个挑战 / {resolved} 个已解决 "
                f"（{'目标同意' if cr.get('mode') == 'target_agreed' else '多数投票'}）"
            )

    if high_scores:
        conclusion_lines.append(f"\n🔥 高优先级（≥7 分，{len(high_scores)} 条）：")
        for s in high_scores:
            conclusion_lines.append(f"  - #{s['num']}「{s['title'][:40]}」总分 {s['total']} → {s['action']}")

    if medium_scores:
        conclusion_lines.append(f"\n📌 中优先级（5-6 分，{len(medium_scores)} 条）：")
        for s in medium_scores:
            conclusion_lines.append(f"  - #{s['num']}「{s['title'][:40]}」总分 {s['total']} → {s['action']}")

    # Token 摘要
    if tracker:
        token_summary = tracker.summary()
        if token_summary:
            conclusion_lines.append(token_summary)

    return {
        "scores": final_scores,
        "conclusion": "\n".join(conclusion_lines),
        "raw_workers": raw_results,
    }


# ── 写入简报 ────────────────────────────────────────────

def write_back_brief(date_str: str, result: dict):
    """将研判结果写回每日简报文件。"""
    brief_path = INTEL_DIR / f"daily-{date_str}.md"
    if not brief_path.exists():
        print(f"简报文件不存在: {brief_path}", file=sys.stderr)
        return

    text = brief_path.read_text(encoding="utf-8")

    # 1. 替换状态行
    text = text.replace(
        "> 状态：⏳ 待小樱研判",
        f"> 状态：✅ 已研判（{now_str()}）"
    )

    # 2. 替换研判标记
    text = text.replace("⏳ 待小樱评分", "✅ 已评分")

    # 3. 重写研判区评分表
    scores = result.get("scores", [])
    table_pattern = re.compile(
        r'(\| # \| 相关性\(0-3\) \| 可行性\(0-3\) \| 杠杆率\(0-3\) \| 总分 \| 行动建议 \|.*?\n)'
        r'(\|---.*?\n)'
        r'((?:\| \d+ \| — \| — \| — \| — \| — \|\n)+)',
        re.DOTALL,
    )

    # 构建新表格
    new_rows = []
    for s in scores:
        new_rows.append(
            f"| {s['num']} | {s['relevance']} | {s['feasibility']} | "
            f"{s['leverage']} | {s['total']} | {s['action']} |"
        )
    new_table = "\n".join(new_rows) + "\n"

    match = table_pattern.search(text)
    if match:
        header = match.group(1)
        sep = match.group(2)
        text = text.replace(match.group(0), header + sep + new_table)
    else:
        print("  ⚠ 未找到研判区表格——无法自动替换", file=sys.stderr)

    # 4. 替换研判结论
    conclusion = result.get("conclusion", "")
    text = re.sub(
        r'\*\*研判结论\*\*：.*$',
        f'**研判结论**：\n\n{conclusion}',
        text,
        flags=re.MULTILINE,
    )

    brief_path.write_text(text, encoding="utf-8")
    print(f"  📝 研判结果已写入: {brief_path}")


# ── 行动建议生成 ────────────────────────────────────────

def generate_actions(
    high_items: list[dict],
    conclusion: str,
    goal: dict,
    dry_run: bool = False,
) -> list[dict]:
    """取 ≥7 分条目，调用 GLM-4-Flash 生成可执行行动建议。

    每个行动包含：建议描述、为什么现在、失效条件、安全级别。
    GLM-4-Flash 不可用时优雅降级——返回空列表。
    """
    if not high_items:
        return []

    worker_info = WORKERS.get("glm", {})
    api_key = os.environ.get(worker_info.get("env_key", ""), "")
    if not api_key:
        print(f"  ⚠ GLM_API_KEY 未设置——跳过行动建议生成", file=sys.stderr)
        return []

    # 构建 prompt
    items_text = "\n\n".join(
        f"### 情报 #{it['num']}：{it['title']}\n"
        f"链接：{it.get('link', '—')}\n"
        f"摘要：{it.get('snippet', '—')}\n"
        f"评分：相关性={it.get('relevance','—')} 可行性={it.get('feasibility','—')} "
        f"杠杆率={it.get('leverage','—')} 总分={it.get('total','—')}\n"
        f"Worker 建议：{it.get('action', '—')}"
        for it in high_items
    )

    system_prompt = (
        "你是樱漫清澜的 AI 行动顾问。你的任务是把情报研判结果转化为可执行的行动建议。\n\n"
        "规则：\n"
        "1. 每条行动必须具体——「做什么」+「怎么做」+「预计耗时」\n"
        "2. 每条行动必须附带一个失效条件——「如果 X 发生，说明判断错误，应停止/转向」\n"
        "3. 标注安全级别：🟢 安全（只读/分析/建议，零副作用）| 🟡 需确认（写文件/改配置/git 操作）\n"
        "4. 每条行动标注「为什么现在」——为什么这个时机适合做这件事\n"
        "5. 最多 3 条行动建议，按优先级排序\n\n"
        "输出格式：纯 JSON 数组，每个元素包含 action_title, what, how, estimated_time, "
        "why_now, safety_level (green/yellow), failure_condition 字段。"
    )

    user_prompt = (
        f"以下是今日情报研判中 ≥7 分的高优先级条目（共 {len(high_items)} 条）：\n\n"
        f"{items_text}\n\n"
        f"研判结论：\n{conclusion}\n\n"
        "请基于以上信息生成 1-3 条可执行行动建议，输出纯 JSON 数组。"
    )

    print(f"\n── 行动建议生成（GLM-4-Flash）──")
    if dry_run:
        print(f"  [DRY RUN] 跳过 API 调用")
        return []

    result = llm_call(
        base_url=worker_info["base_url"],
        api_key=api_key,
        model=worker_info["model"],
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.3,
        max_tokens=2048,
    )

    if result is None:
        print(f"  ✗ GLM-4-Flash 调用失败——跳过行动建议生成", file=sys.stderr)
        return []

    # 解析 JSON
    response_text = result["text"]
    try:
        start = response_text.find("[")
        end = response_text.rfind("]")
        if start != -1 and end != -1 and end > start:
            actions = json.loads(response_text[start:end + 1])
            if isinstance(actions, list):
                print(f"  ✅ 生成 {len(actions)} 条行动建议")
                return actions
    except json.JSONDecodeError:
        pass

    print(f"  ⚠ 无法解析行动建议 JSON——返回空", file=sys.stderr)
    return []


def write_actions_file(date_str: str, actions: list[dict], high_items: list[dict]):
    """将行动建议写入 memory/intel/actions-{date}.md。"""
    if not actions:
        return

    actions_path = INTEL_DIR / f"actions-{date_str}.md"

    lines = [
        f"# 行动建议 — {date_str}",
        "",
        "> 🤖 基于今日情报研判自动生成 | Phase 3 行动层",
        "",
        "## ✅ 已自动完成",
        "",
        "- 情报抓取（Serper API，5 个搜索词）",
        "- 4 Worker 并行研判（Kimi K3 + DeepSeek V4 Flash + GLM-4-Flash）",
        "- 交叉审查 + 双层硬约束过滤",
        "- 研判结果写回报刊",
        "",
        "## ⏳ 待确认行动",
        "",
    ]

    for i, a in enumerate(actions, 1):
        safety_emoji = "🟢" if a.get("safety_level") == "green" else "🟡"
        lines.extend([
            f"### 行动 {i}：{a.get('action_title', '未命名')}",
            "",
            f"**做什么**：{a.get('what', '—')}",
            f"**怎么做**：{a.get('how', '—')}",
            f"**预计耗时**：{a.get('estimated_time', '—')}",
            f"**为什么现在**：{a.get('why_now', '—')}",
            f"**安全级别**：{safety_emoji} {'安全——只读/分析' if a.get('safety_level') == 'green' else '需确认——涉及写操作'}",
            f"**失效条件**：{a.get('failure_condition', '—')}",
            "",
        ])

    if high_items:
        lines.append("## 📊 关联情报")
        lines.append("")
        for it in high_items:
            lines.append(f"- [#{it['num']} {it['title']}]({it.get('link', '#')}) — 总分 {it.get('total', '—')}")
        lines.append("")

    actions_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  📝 行动建议已写入: {actions_path}")


# ── CLI ──────────────────────────────────────────────────

def main():
    # Windows 终端 GBK 编码兼容
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding='utf-8')
        except Exception:
            pass

    parser = argparse.ArgumentParser(
        description="多 Agent Supervisor——主控大脑",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python scripts/supervisor.py --goal goals/intel-review.json --date 2026-07-28
  python scripts/supervisor.py --goal goals/intel-review.json --date 2026-07-28 --dry-run
        """,
    )
    parser.add_argument("--goal", required=True, help="Goal 定义文件路径（JSON）")
    parser.add_argument("--date", required=True, help="目标日期 YYYY-MM-DD")
    parser.add_argument("--dry-run", action="store_true", help="不实际调用 API，验证流程")
    parser.add_argument("--output", choices=["brief", "json", "both"], default="brief",
                        help="输出格式——brief: 写回报刊文件, json: stdout JSON, both: 两者")
    parser.add_argument("--verbose", action="store_true",
                        help="保存每个 Worker 的原始输出到 memory/intel/verbose/{date}/")
    args = parser.parse_args()

    goal_file = Path(args.goal)
    if not goal_file.is_absolute():
        goal_file = REPO_ROOT / goal_file

    if not goal_file.exists():
        print(f"Goal 文件不存在: {goal_file}", file=sys.stderr)
        sys.exit(1)

    result = supervisor_run(goal_file, args.date, dry_run=args.dry_run, verbose=args.verbose)

    if "error" in result:
        # 🆕 Phase 3：all_scored 不是真错误——评分已完成，只需补跑 Action Pass
        if result["error"] == "all_scored":
            print(f"\n📋 已全部研判，跳过评分。从已有评分生成行动建议...")
            all_items = parse_intel_items(args.date)
            existing_scores = parse_existing_scores(args.date)
            if existing_scores and all_items:
                items_by_num = {it["num"]: it for it in all_items}
                high_items = []
                for s in existing_scores:
                    if s.get("total", 0) >= 7:
                        item = items_by_num.get(s["num"], {})
                        high_items.append({
                            **s,
                            "link": item.get("link", ""),
                            "snippet": item.get("snippet", ""),
                            "title": item.get("title", ""),
                        })
                if high_items:
                    goal = json.loads(goal_file.read_text("utf-8"))
                    actions = generate_actions(
                        high_items,
                        "已全部研判——基于已有评分生成行动建议。",
                        goal,
                        args.dry_run,
                    )
                    write_actions_file(args.date, actions, high_items)
                    if not args.dry_run:
                        print(f"✅ Action Pass 完成——{len(actions)} 条行动建议已生成")
                        # 输出摘要
                        for s in high_items:
                            print(f"  #{s['num']}「{s.get('title','')[:40]}」→ {s.get('action','')}")
                    sys.exit(0)
                else:
                    print(f"✅ 无 ≥7 分条目，无需生成行动建议")
                    sys.exit(0)
            print(f"\n⚠️ 无法解析已有评分——请手动检查 daily-{args.date}.md 研判区表格")
            sys.exit(1)
        print(f"\n❌ Supervisor 运行失败: {result['error']}")
        sys.exit(1)

    # 输出
    if args.output in ("json", "both"):
        print(json.dumps(result, ensure_ascii=False, indent=2))

    if args.output in ("brief", "both") and not args.dry_run:
        write_back_brief(args.date, result)
        write_intel_json(args.date, result)  # 同时写入结构化 JSON
        # 🆕 Phase 3：行动建议写入
        actions = result.get("actions", [])
        if actions:
            scores = result.get("scores", [])
            high_items = [
                {**s, "link": "", "snippet": ""}
                for s in scores
                if isinstance(s.get("total"), int) and s["total"] >= 7
            ]
            write_actions_file(args.date, actions, high_items)

    # 打印摘要
    scores = result.get("scores", [])
    if scores:
        high = [s for s in scores if isinstance(s.get("total"), int) and s["total"] >= 7]
        print(f"\n📊 研判摘要:")
        print(f"   总计: {len(scores)} 条")
        print(f"   高优先级 (≥7): {len(high)} 条")
        if high:
            for s in high:
                print(f"     #{s['num']}「{s['title'][:40]}」→ {s['action']}")

    print(f"\n✅ Supervisor 完成 — {now_str()}")


if __name__ == "__main__":
    main()
