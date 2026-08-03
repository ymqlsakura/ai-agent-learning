"""共享配置——API 端点、模型名、搜索词、路径集中管理。

所有硬编码值从 supervisor.py 和 daily_intel.py 提取到此文件。
修改配置只需改这里，不用全局搜替换。
"""

from pathlib import Path
from datetime import timezone, timedelta

# ── 时区 ─────────────────────────────────────────────────
TZ = timezone(timedelta(hours=8))  # 北京时间

# ── 路径 ─────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent
GOALS_DIR = REPO_ROOT / "goals"
INTEL_DIR = REPO_ROOT / "memory" / "intel"
INDEX_PATH = INTEL_DIR / "INDEX.md"

# ── Serper API ───────────────────────────────────────────
SERPER_API_URL = "https://google.serper.dev/search"
MAX_PER_QUERY = 3  # 每个关键词最多取几条（查询多，每条少取，保多样性）

# ── DeepSeek API（用于每日摘要——可选） ──────────────────
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_MODEL = "deepseek-v4-flash"

# ── 搜索关键词 ──────────────────────────────────────────
# (query, language, region, tbs)
QUERIES = [
    ("AI industry breaking news highlights this week", "en", "us", "qdr:w"),
    ("new AI agent tools frameworks released 2026", "en", "us", None),
    ("solo founder one person business AI startup 2026", "en", "us", None),
    ("Claude Code new features updates 2026", "en", "us", None),
    ("China AI policy regulation 2026", "en", "us", None),
    ("一人公司 AI 创业 新工具 2026", "zh-cn", "cn", None),
]

# ── 已知主题标签（用于自动标注） ─────────────────────────
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

# ── 供应商域名 ───────────────────────────────────────────
# 这些来源的条目杠杆率默认降 1 分（独立媒体 > 社区讨论 > 供应商自述）
VENDOR_DOMAINS = {
    "blog.jetbrains.com",
    "www.langchain.com",
    "www.taskade.com",
    "code.claude.com",
    "developers.google.com",
    "openai.com",
    "platform.openai.com",
    "anthropic.com",
    "aws.amazon.com",
    "azure.microsoft.com",
}

# ── Worker API 配置 ──────────────────────────────────────
WORKERS = {
    "kimi": {
        "name": "Kimi K3",
        "base_url": "https://api.moonshot.cn/v1/chat/completions",
        "model": "kimi-k3",
        "env_key": "KIMI_API_KEY",
        "strength": "长文档分析、中文市场情报、一人公司案例、政策解读",
        "reasoning_effort": "low",
        "temperature": 1.0,       # Kimi K3 只接受 temperature=1
    },
    "deepseek": {
        "name": "DeepSeek V4 Flash",
        "base_url": "https://api.deepseek.com/chat/completions",
        "model": "deepseek-v4-flash",
        "env_key": "DEEPSEEK_API_KEY",
        "strength": "技术架构评估、成本估算、工程可行性、工具对比",
    },
    "grok": {
        "name": "Grok 4.5",
        "base_url": "https://api.x.ai/v1/chat/completions",
        "model": "grok-4.5",
        "env_key": "GROK_API_KEY",
        "strength": "技术趋势预判、跨领域关联分析、商业模式可行性、前沿话题嗅觉",
        "temperature": 0.7,
    },
    "glm": {
        "name": "GLM-4-Flash",
        "base_url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        "model": "glm-4-flash",
        "env_key": "GLM_API_KEY",
        "strength": "学术方法论评估、教育视角、政策文本分析、中文内容质量判断",
        "temperature": 0.3,
    },
}

# ── Token 定价（$/百万 tokens） ──────────────────────────
TOKEN_PRICES = {
    "kimi":     {"input": 0.60, "output": 0.60},
    "deepseek": {"input": 0.14, "output": 0.14},
    "grok":     {"input": 2.00, "output": 6.00},
    "glm":      {"input": 0.00, "output": 0.00},  # GLM-4-Flash 永久免费
}

# ── 研判参数 ─────────────────────────────────────────────
MAX_ROUNDS = 5       # 最大迭代轮数（R1 初始评分 + R2 交叉审查 + R3 争议解决 + R4-5 补缺）
API_TIMEOUT = 90     # 单次 API 调用超时（秒）
MAX_WORKERS = 4      # 最大并行 Worker 数
