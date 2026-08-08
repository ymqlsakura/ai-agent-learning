"""
渲染「学习 AI · 1000 天」开场片段
Wrapping `npx remotion render Opener` / `npx remotion still Opener`

用法见 SKILL.md · 一句话：
  python render_opener.py --day 30 --topic "今天学：龙虾接微信" --out day30-opener.mp4
"""
import argparse
import datetime
import json
import os
import subprocess
import sys
from pathlib import Path


# ════════════════════════════════════════════════════════════
#  ⚙️ 配置 · 跟你机器对应
# ════════════════════════════════════════════════════════════
REMOTION_DIR_DEFAULT = r"D:/video/_系统/remotion-base"


def main():
    p = argparse.ArgumentParser(description="渲染 1000 天开场片段")
    p.add_argument("--day", type=int, required=True, help="第几天（1-1000）")
    p.add_argument("--topic", required=True, help="今天学什么 · 副标题")
    p.add_argument("--total-days", type=int, default=1000)
    p.add_argument("--date", default="", help="日期 YYYY·MM·DD（默认今天）")
    p.add_argument("--episode-label", default="", help="EP.XX 标识（默认空）")
    p.add_argument("--still", action="store_true", help="渲单帧 PNG 而非视频")
    p.add_argument("--frame", type=int, default=75, help="单帧时第几帧（默认 75）")
    p.add_argument("--out", required=True, help="输出文件路径 (.mp4 / .png)")
    p.add_argument("--remotion-dir", default=REMOTION_DIR_DEFAULT)
    args = p.parse_args()

    # 默认日期 = 今天
    date_str = args.date or datetime.date.today().strftime("%Y·%m·%d")

    # 构造 props JSON
    props = {
        "dayNumber":     args.day,
        "totalDays":     args.total_days,
        "topic":         args.topic,
        "episodeLabel":  args.episode_label,
        "dateLabel":     date_str,
    }
    props_json = json.dumps(props, ensure_ascii=False)

    # 输出目录
    out_path = Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Remotion 项目目录
    remotion_dir = Path(args.remotion_dir).resolve()
    if not remotion_dir.exists():
        sys.exit(f"❌ Remotion 项目不存在: {remotion_dir}")

    # 拼命令
    cmd_kind = "still" if args.still else "render"
    cmd = ["npx", "remotion", cmd_kind, "Opener",
           f"--props={props_json}"]
    if args.still:
        cmd.append(f"--frame={args.frame}")
    cmd.append(str(out_path))

    print(f"📦 Remotion 项目: {remotion_dir}")
    print(f"🎬 输出: {out_path}")
    print(f"⚙️  Props: {props_json}")
    print(f"▶️  {' '.join(cmd)}\n")

    # 在 Remotion 项目目录下跑
    try:
        # Windows 下用 shell=True 兼容 npx.cmd
        result = subprocess.run(
            cmd,
            cwd=str(remotion_dir),
            shell=(os.name == "nt"),
        )
        if result.returncode != 0:
            sys.exit(f"❌ 渲染失败 · exit {result.returncode}")
    except FileNotFoundError as e:
        sys.exit(f"❌ 找不到 npx · 请装 Node.js: {e}")

    print(f"\n✓ 完成: {out_path}")


if __name__ == "__main__":
    main()
