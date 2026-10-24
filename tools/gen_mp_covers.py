#!/usr/bin/env python3
"""生成公众号封面 + 头像。

- 章节封面：final-videos/chNN/chNN-cover.png(1920x1080) -> 900x506 缩放
  -> 垂直居中裁 383px（公众号头图 2.35:1）-> 左上补画被裁掉的系列徽章
- 速查表封面：无现成封面，按同一视觉语言用 PIL 绘制
- 头像：从 ch00 封面抠机器人吉祥物，500x500

用法：python tools/gen_mp_covers.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "wechat-mp" / "covers"
FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"

NAVY = (15, 23, 42)
CYAN = (34, 211, 238)
YELLOW = (251, 191, 36)
WHITE = (248, 250, 252)

# 键 = md2mp.py 的前缀规则 f"cs-{stem[:6]}"
CHEATSHEETS = {
    "cs-HAL速查表": ("HAL 速查表", "常用函数一页查"),
    "cs-寄存器速查表": ("寄存器速查表", "RCC / GPIO / UART / TIM"),
    "cs-外设总线与引": ("外设总线与引脚速查表", "接线不再翻手册"),
    "cs-错误码与排查": ("错误码与排查速查表", "报错先来这查"),
}


def pill(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str,
         font: ImageFont.FreeTypeFont, fg, border) -> None:
    x, y = xy
    box = draw.textbbox((0, 0), text, font=font)
    w, h = box[2] - box[0] + 28, box[3] - box[1] + 18
    draw.rounded_rectangle([x, y, x + w, y + h], radius=h // 2, outline=border, width=2)
    draw.text((x + 14, y + 9 - box[1]), text, font=font, fill=fg)


def chapter_cover(ch: str) -> None:
    src = ROOT / "final-videos" / ch / f"{ch}-cover.png"
    im = Image.open(src).convert("RGB").resize((900, 506), Image.LANCZOS)
    im = im.crop((0, 61, 900, 444))  # 2.35:1，保留「第NN章」章标与标题
    im.save(OUT / f"{ch}.jpg", quality=90)


def cheatsheet_cover(key: str, title: str, sub: str) -> None:
    im = Image.new("RGB", (900, 383), NAVY)
    draw = ImageDraw.Draw(im)
    pill(draw, (36, 30), "STM32 零基础自学",
         ImageFont.truetype(FONT_BOLD, 22), CYAN, CYAN)
    chip = ImageFont.truetype(FONT_BOLD, 26)
    box = draw.textbbox((0, 0), "速查表", font=chip)
    w = box[2] - box[0] + 36
    draw.rounded_rectangle([36, 84, 36 + w, 140], radius=10, fill=YELLOW)
    draw.text((54, 96 - box[1]), "速查表", font=chip, fill=NAVY)
    draw.text((36, 168), title, font=ImageFont.truetype(FONT_BOLD, 64), fill=WHITE)
    draw.text((36, 268), sub, font=ImageFont.truetype(FONT_BOLD, 34), fill=CYAN)
    # 右侧装饰：大括号芯片符号
    draw.text((700, 120), "{ }", font=ImageFont.truetype(FONT_BOLD, 120), fill=(30, 41, 59))
    im.save(OUT / f"{key}.jpg", quality=90)


def avatar() -> None:
    """从 ch00 封面抠吉祥物（机器人区域居中裁正方形）。"""
    src = Image.open(ROOT / "final-videos" / "ch00" / "ch00-cover.png").convert("RGB")
    im = src.crop((1340, 232, 1786, 678)).resize((500, 500), Image.LANCZOS)
    im.save(OUT / "avatar.png")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    # 封面源在不入库的 final-videos/chNN/。这里仍只裁 ch00–ch25。
    # 仓库正文已是 00–28；本地有 ch26、ch27、ch28 封面后再把 range 改成 29。
    for i in range(26):
        ch = f"ch{i:02d}"
        chapter_cover(ch)
        print(f"[cover] {ch}.jpg")
    for key, (title, sub) in CHEATSHEETS.items():
        cheatsheet_cover(key, title, sub)
        print(f"[cover] {key}.jpg")
    avatar()
    print("[cover] avatar.png")


if __name__ == "__main__":
    main()
