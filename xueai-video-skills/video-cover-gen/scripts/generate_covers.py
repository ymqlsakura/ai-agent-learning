"""
═══════════════════════════════════════════════════════════════
 视频封面生成器 · 横版 4:3 (1600×1200) + 竖版 3:4 (1080×1440)
 「学习 AI · 1000 天」系列模板 · 抖音/小红书/视频号通用

 用法：
   python generate_covers.py --config cover-config.json
   python generate_covers.py --config cover-config.json --out custom/dir/
═══════════════════════════════════════════════════════════════
"""
import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter


# ════════════════════════════════════════════════════════════
#  🎨 设计 token · 全局色板 + 字体
# ════════════════════════════════════════════════════════════
BG          = (12, 12, 14)
BG_ELEVATED = (24, 24, 28)
ACCENT      = (255, 90, 31)
ACCENT_DEEP = (220, 60, 10)
PAPER       = (242, 230, 195)
TEXT        = (235, 235, 230)
MUTED       = (130, 130, 130)
GRID_BORDER = (60, 60, 65)

FONT_BOLD = r"C:/Windows/Fonts/msyhbd.ttc"
FONT_REG  = r"C:/Windows/Fonts/msyh.ttc"


def font(path, size):
    return ImageFont.truetype(path, size)


def draw_glow(img, color, x, y, radius, alpha=80):
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for r in range(radius, 0, -8):
        a = int(alpha * (r / radius) * 0.15)
        gd.ellipse([x - r, y - r, x + r, y + r],
                   fill=(color[0], color[1], color[2], a))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=20))
    img.paste(glow, (0, 0), glow)


def draw_tile(draw, x, y, w, h, num, name, fnum, fname):
    draw.rounded_rectangle([x, y, x + w, y + h], radius=10,
                           fill=BG_ELEVATED, outline=GRID_BORDER, width=2)
    draw.text((x + 18, y + h // 2), num, font=fnum, fill=ACCENT, anchor="lm")
    draw.text((x + w - 18, y + h // 2), name, font=fname, fill=TEXT, anchor="rm")


def draw_top_band(d, W, day_num, series_label):
    d.ellipse([60, 80, 76, 96], fill=ACCENT)
    d.text((90, 78), series_label, font=font(FONT_BOLD, 22), fill=MUTED)
    d.text((W - 60, 78), f"Day {day_num}",
           font=font(FONT_BOLD, 26), fill=TEXT, anchor="rt")
    d.line([(60, 122), (W - 60, 122)], fill=(35, 35, 38), width=1)


def normalize_tiles(raw_tiles):
    """支持 [(num,name), ...] 和 [[num,name], ...] 两种格式"""
    return [tuple(t) for t in raw_tiles]


# ════════════════════════════════════════════════════════════
#  横版 1600×1200 (4:3)
# ════════════════════════════════════════════════════════════
def make_horizontal(cfg, out_dir):
    W, H = 1600, 1200
    img = Image.new("RGB", (W, H), BG)
    img_rgba = img.convert("RGBA")
    draw_glow(img_rgba, ACCENT, 0, 0, 500, alpha=60)
    draw_glow(img_rgba, ACCENT, W, H, 600, alpha=50)
    img = img_rgba.convert("RGB")
    d = ImageDraw.Draw(img)

    day_str = str(cfg["day_number"]).zfill(3)
    tiles = normalize_tiles(cfg.get("tiles", []))

    # 顶部识别带
    d.ellipse([60, 80, 76, 96], fill=ACCENT)
    d.text((90, 78), cfg["series_label"], font=font(FONT_BOLD, 22), fill=MUTED)
    d.text((W - 60, 78), cfg["date"], font=font(FONT_REG, 20), fill=MUTED, anchor="rt")
    d.line([(60, 122), (W - 60, 122)], fill=(35, 35, 38), width=1)

    # 左栏 · 计数器
    LX = 110
    d.text((LX, 250), f"—— {cfg['series_subtag']} ——",
           font=font(FONT_REG, 24), fill=MUTED)
    d.text((LX, 510), day_str, font=font(FONT_BOLD, 240), fill=PAPER, anchor="lm")
    d.text((LX + 470, 570), f"/ {cfg['total_days']}",
           font=font(FONT_REG, 50), fill=MUTED, anchor="lm")
    d.line([(LX, 680), (LX + 500, 680)], fill=ACCENT, width=4)
    d.text((LX, 730), f"Day {cfg['day_number']}",
           font=font(FONT_BOLD, 72), fill=TEXT, anchor="lt")
    if cfg.get("episode_label"):
        d.text((LX, 820), cfg["episode_label"],
               font=font(FONT_REG, 28), fill=MUTED, anchor="lt")

    # 中线
    d.line([(770, 200), (770, 1000)], fill=(35, 35, 38), width=1)

    # 右栏 · 钩子 + tiles
    RX = 830
    d.text((RX, 250), "今天学", font=font(FONT_REG, 32), fill=MUTED)
    d.text((RX, 310), cfg["hook_main"],
           font=font(FONT_BOLD, 96), fill=TEXT, anchor="lt")
    d.text((RX, 425), cfg["title_line1"],
           font=font(FONT_BOLD, 76), fill=PAPER, anchor="lt")

    hook_y = 540
    d.rounded_rectangle([RX, hook_y, RX + 620, hook_y + 90], radius=14, fill=ACCENT)
    d.text((RX + 310, hook_y + 45),
           f"{len(tiles)} 个 · {cfg['title_line2']}",
           font=font(FONT_BOLD, 46), fill=BG, anchor="mm")

    d.text((RX, hook_y + 120), cfg["cta_main"],
           font=font(FONT_REG, 26), fill=MUTED, anchor="lt")

    # tiles
    tw, th = 200, 54
    gx, gy = RX, hook_y + 210
    cols = 3
    visible = min(6, len(tiles))
    for i in range(visible):
        num, name = tiles[i]
        cx = gx + (i % cols) * (tw + 18)
        cy = gy + (i // cols) * (th + 14)
        draw_tile(d, cx, cy, tw, th, num, name,
                  font(FONT_BOLD, 20), font(FONT_REG, 22))

    if len(tiles) > 6:
        more_names = [n for _, n in tiles[6:]]
        d.text((RX, gy + 2 * (th + 14) + 14),
               "+ " + " · ".join(more_names[:5]) + (" ..." if len(more_names) > 5 else ""),
               font=font(FONT_REG, 20), fill=ACCENT, anchor="lt")

    # 底部带
    d.line([(60, H - 80), (W - 60, H - 80)], fill=(35, 35, 38), width=1)
    d.text((60, H - 50), f"{cfg['series_subtag']} · 关注 跟着学",
           font=font(FONT_REG, 22), fill=MUTED)
    d.text((W - 60, H - 50), cfg["cta_sub"],
           font=font(FONT_REG, 22), fill=MUTED, anchor="rt")

    out = out_dir / cfg["horizontal_filename"]
    img.save(out, "PNG", optimize=True)
    print(f"horizontal: {out}")
    return out


# ════════════════════════════════════════════════════════════
#  竖版 1080×1440 (3:4)
# ════════════════════════════════════════════════════════════
def make_vertical(cfg, out_dir):
    W, H = 1080, 1440
    img = Image.new("RGB", (W, H), BG)
    img_rgba = img.convert("RGBA")
    draw_glow(img_rgba, ACCENT, 100, 150, 400, alpha=60)
    draw_glow(img_rgba, ACCENT, W - 100, H - 150, 450, alpha=50)
    img = img_rgba.convert("RGB")
    d = ImageDraw.Draw(img)

    day_str = str(cfg["day_number"]).zfill(3)
    tiles = normalize_tiles(cfg.get("tiles", []))

    # 顶部识别带
    draw_top_band(d, W, cfg["day_number"], cfg["series_label"])

    # 钩子区
    d.text((W // 2, 145), "今天学 ↓", font=font(FONT_REG, 24), fill=MUTED, anchor="mt")
    d.text((W // 2, 200), cfg["hook_main"],
           font=font(FONT_BOLD, 110), fill=TEXT, anchor="mt")

    # 可选红色横幅
    title_y = 360
    if cfg.get("hook_sub"):
        bar_y, bar_h = 340, 76
        d.rounded_rectangle([90, bar_y, W - 90, bar_y + bar_h],
                            radius=12, fill=ACCENT)
        d.text((W // 2, bar_y + bar_h // 2), cfg["hook_sub"],
               font=font(FONT_BOLD, 38), fill=BG, anchor="mm")
        title_y = 440

    # 主标题
    d.text((W // 2, title_y), cfg["title_line1"],
           font=font(FONT_BOLD, 94), fill=PAPER, anchor="mt")
    d.text((W // 2, title_y + 115), cfg["title_line2"],
           font=font(FONT_BOLD, 74), fill=TEXT, anchor="mt")

    # 计数器
    d.line([(140, 645), (W - 140, 645)], fill=(40, 40, 45), width=1)
    d.text((W // 2, 670), cfg["series_subtag"],
           font=font(FONT_REG, 24), fill=MUTED, anchor="mt")
    d.text((W // 2 - 50, 770), day_str,
           font=font(FONT_BOLD, 156), fill=PAPER, anchor="mm")
    d.text((W // 2 + 170, 800), f"/ {cfg['total_days']}",
           font=font(FONT_REG, 36), fill=MUTED, anchor="lm")
    d.line([(W // 2 - 70, 870), (W // 2 + 70, 870)], fill=ACCENT, width=4)

    # tiles
    if cfg.get("tiles_section_title"):
        d.text((W // 2, 905), cfg["tiles_section_title"],
               font=font(FONT_BOLD, 28), fill=TEXT, anchor="mt")

    grid_top = 960
    tw, th = 290, 70
    cols = 3
    gap_x, gap_y = 18, 12
    grid_left = (W - cols * tw - (cols - 1) * gap_x) // 2

    for i, (num, name) in enumerate(tiles):
        cx = grid_left + (i % cols) * (tw + gap_x)
        cy = grid_top + (i // cols) * (th + gap_y)
        draw_tile(d, cx, cy, tw, th, num, name,
                  font(FONT_BOLD, 24), font(FONT_REG, 22))

    # CTA
    d.line([(140, 1310), (W - 140, 1310)], fill=(40, 40, 45), width=1)
    d.text((W // 2, 1340), cfg["cta_main"],
           font=font(FONT_BOLD, 32), fill=TEXT, anchor="mt")
    d.text((W // 2, 1390), cfg["cta_sub"],
           font=font(FONT_REG, 22), fill=MUTED, anchor="mt")
    if cfg.get("episode_label"):
        d.text((W // 2, 1420), cfg["episode_label"],
               font=font(FONT_BOLD, 20), fill=ACCENT, anchor="mt")

    out = out_dir / cfg["vertical_filename"]
    img.save(out, "PNG", optimize=True)
    print(f"vertical:   {out}")
    return out


# ════════════════════════════════════════════════════════════
#  默认配置（用作脱敏 fallback）
# ════════════════════════════════════════════════════════════
DEFAULT_CONFIG = {
    "out_dir": ".",
    "series_label":  "AI · 1000 DAYS",
    "series_subtag": "学习 AI · 1000 天",
    "day_number":    1,
    "total_days":    1000,
    "date":          "2026·01·01",
    "episode_label": "",
    "hook_main":     "标题",
    "hook_sub":      "",
    "title_line1":   "副标题 1",
    "title_line2":   "副标题 2",
    "tiles":         [["01", "示例"]],
    "tiles_section_title": "",
    "cta_main":      "底部金句",
    "cta_sub":       "粉丝群免费领",
    "horizontal_filename": "cover-横版-1600x1200.png",
    "vertical_filename":   "cover-竖版-1080x1440.png",
}


def main():
    p = argparse.ArgumentParser(description="视频封面生成器（横版 4:3 + 竖版 3:4）")
    p.add_argument("--config", required=True, help="JSON 配置文件路径")
    p.add_argument("--out", help="输出目录（默认读 config 里的 out_dir）")
    p.add_argument("--horizontal-only", action="store_true", help="只出横版")
    p.add_argument("--vertical-only", action="store_true", help="只出竖版")
    args = p.parse_args()

    with open(args.config, encoding="utf-8") as f:
        cfg = json.load(f)

    # 用 default 填充缺省字段
    merged = {**DEFAULT_CONFIG, **cfg}

    out_dir = Path(args.out or merged.get("out_dir", "."))
    out_dir.mkdir(parents=True, exist_ok=True)

    if not args.vertical_only:
        make_horizontal(merged, out_dir)
    if not args.horizontal_only:
        make_vertical(merged, out_dir)

    print("\n✓ 封面生成完成")


if __name__ == "__main__":
    main()
