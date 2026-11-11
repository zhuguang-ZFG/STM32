#!/usr/bin/env python3
"""生成站点社交分享卡（og:image），确定性输出——非 AI 生图，中文不会乱码。

用法：
    python scripts/gen-og-cover.py [输出路径]
默认输出 docs/public/og-cover.png（1200x630，社交平台推荐尺寸）。

依赖 Pillow，**仅在重新生成时需要**；产物已入库，构建与 CI 都不依赖本脚本。
配色对齐站点主题（--mcu-brand #3451b2 / 深色下的 #8ab4ff）。
"""
import sys
from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 630
BRAND = (52, 81, 178)          # #3451b2
BRAND_LIGHT = (138, 180, 255)  # #8ab4ff
BG_TOP = (11, 18, 32)          # #0b1220
BG_BOTTOM = (19, 28, 51)       # #131c33
DIE = (24, 34, 60)
INK = (240, 245, 255)
MUTED = (150, 166, 199)

# 跨平台字体回退：优先中文黑体，其次任何可用的中文/西文字体。
BOLD_CANDIDATES = [
    r"C:\Windows\Fonts\msyhbd.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
]
REG_CANDIDATES = [
    r"C:\Windows\Fonts\msyh.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    r"C:\Windows\Fonts\simsun.ttc",
]


def pick_font(candidates, size):
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    raise SystemExit("找不到可用字体，请安装中文字体或修改候选列表")


def gradient(img, top, bottom):
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / (H - 1)
        d.line(
            [(0, y), (W, y)],
            fill=tuple(round(top[i] + (bottom[i] - top[i]) * t) for i in range(3)),
        )


def draw_chip(d, cx, cy, s):
    """右侧 MCU 示意图：本体 + 四边引脚 + 一脚标记。"""
    x0, y0, x1, y1 = cx - s // 2, cy - s // 2, cx + s // 2, cy + s // 2
    pin_len, pin_w, n = 26, 10, 5
    step = s // n
    for i in range(n):
        off = -s // 2 + step * i + step // 2 - pin_w // 2
        d.rectangle([cx + off, y0 - pin_len, cx + off + pin_w, y0], fill=BRAND_LIGHT)
        d.rectangle([cx + off, y1, cx + off + pin_w, y1 + pin_len], fill=BRAND_LIGHT)
        d.rectangle([x0 - pin_len, cy + off, x0, cy + off + pin_w], fill=BRAND_LIGHT)
        d.rectangle([x1, cy + off, x1 + pin_len, cy + off + pin_w], fill=BRAND_LIGHT)
    d.rounded_rectangle([x0, y0, x1, y1], radius=22, fill=DIE, outline=BRAND_LIGHT, width=3)
    d.rounded_rectangle([x0 + 24, y0 + 24, x1 - 24, y1 - 24], radius=12, outline=(70, 96, 150), width=2)
    d.ellipse([x0 + 36, y0 + 36, x0 + 62, y0 + 62], fill=BRAND_LIGHT)
    d.text((cx, cy - 4), "MCU", font=pick_font(BOLD_CANDIDATES, 46), fill=INK, anchor="mm")
    d.text((cx, cy + 44), "Cortex-M / Xtensa", font=pick_font(REG_CANDIDATES, 19), fill=MUTED, anchor="mm")


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "docs/public/og-cover.png"
    img = Image.new("RGB", (W, H), BG_TOP)
    gradient(img, BG_TOP, BG_BOTTOM)

    # 极淡网格
    grid = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grid)
    for x in range(0, W, 40):
        gd.line([(x, 0), (x, H)], fill=(255, 255, 255, 9))
    for y in range(0, H, 40):
        gd.line([(0, y), (W, y)], fill=(255, 255, 255, 9))
    img = Image.alpha_composite(img.convert("RGBA"), grid).convert("RGB")

    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 10, H], fill=BRAND)  # 左侧品牌竖条
    draw_chip(d, 955, 300, 220)

    x = 92
    d.text((x, 148), "寄存器级深度教学 · 全程实物实验",
           font=pick_font(REG_CANDIDATES, 27), fill=MUTED)
    d.text((x, 192), "通往单片机之路",
           font=pick_font(BOLD_CANDIDATES, 78), fill=INK)
    d.text((x, 312), "STM32F407 × ESP32-S3",
           font=pick_font(BOLD_CANDIDATES, 42), fill=BRAND_LIGHT)
    d.text((x, 380), "C 语言精髓 · RTOS 双精讲 · 从寄存器到工程实践",
           font=pick_font(REG_CANDIDATES, 27), fill=MUTED)
    d.line([(x, 470), (x + 520, 470)], fill=(70, 96, 150), width=2)
    d.text((x, 494), "zhuguang-zfg.github.io/mcu",
           font=pick_font(REG_CANDIDATES, 24), fill=BRAND_LIGHT)

    img.save(out, "PNG", optimize=True)
    print(f"wrote {out} ({img.width}x{img.height})")


if __name__ == "__main__":
    main()
