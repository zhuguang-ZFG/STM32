#!/usr/bin/env python3
"""为视频号 / 小红书 / 抖音 / B站 生成平台封面（竖版 3:4、9:16，通用 1:1）。

设计语言与横版 1920x1080 封面一致：深蓝渐变底、青色系列徽章、黄色章标、
白/青大标题、黄字钩子句、右下机器人。

用法：python tools/gen_platform_covers.py [--only 11] [--style all|feed|xhs|hook]
输出：final-videos/chNN/chNN-cover-{3x4,6x7,9x16,1x1}.jpg（feed）
      chNN-hook-9x16.jpg（抖音钩子条） / chNN-xhs-3x4.jpg（小红书大字报）
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


from cover_copy import COPY

ROOT = Path(__file__).resolve().parent.parent
FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"

NAVY_TOP = (15, 23, 42)
NAVY_BOT = (26, 42, 66)
CYAN = (34, 211, 238)
YELLOW = (251, 191, 36)
WHITE = (248, 250, 252)
MUTED = (148, 163, 184)
CREAM = (253, 248, 236)
INK = (22, 30, 46)
ACCENT = (229, 57, 53)

def robot_box(src: Path, pad: int = 8) -> tuple[int, int, int, int]:
    """按青色描边自动定位机器人（各章位置一致，避免手调坐标）。"""
    import numpy as np
    im = np.asarray(Image.open(src).convert("RGB")).astype(int)
    r, g, b = im[:, :, 0], im[:, :, 1], im[:, :, 2]
    mask = (g > 150) & (b > 180) & (r < 120)
    ys, xs = np.nonzero(mask)
    sel = xs > 1250                      # 排除左侧青色标题文字
    x0, x1 = int(xs[sel].min()), int(xs[sel].max())
    y0, y1 = int(ys[sel].min()), int(ys[sel].max())
    h, w = im.shape[:2]
    return (max(0, x0 - pad), max(0, y0 - pad), min(w, x1 + pad), min(h, y1 + pad))


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_BOLD, size)


def gradient(w: int, h: int) -> Image.Image:
    im = Image.new("RGB", (w, h), NAVY_TOP)
    dr = ImageDraw.Draw(im)
    for y in range(h):
        t = y / max(1, h - 1)
        dr.line([(0, y), (w, y)], fill=(
            round(NAVY_TOP[0] + (NAVY_BOT[0] - NAVY_TOP[0]) * t),
            round(NAVY_TOP[1] + (NAVY_BOT[1] - NAVY_TOP[1]) * t),
            round(NAVY_TOP[2] + (NAVY_BOT[2] - NAVY_TOP[2]) * t),
        ))
    return im


def pill(dr: ImageDraw.ImageDraw, xy: tuple[int, int], text: str,
         f: ImageFont.FreeTypeFont, fg, border, pad_x=26, pad_y=14, width=3) -> int:
    x, y = xy
    box = dr.textbbox((0, 0), text, font=f)
    w, h = box[2] - box[0] + pad_x * 2, box[3] - box[1] + pad_y * 2
    dr.rounded_rectangle([x, y, x + w, y + h], radius=h // 2, outline=border, width=width)
    dr.text((x + pad_x, y + pad_y - box[1]), text, font=f, fill=fg)
    return h


def chip(dr: ImageDraw.ImageDraw, xy: tuple[int, int], text: str,
         f: ImageFont.FreeTypeFont, bg=YELLOW, fg=NAVY_TOP) -> int:
    x, y = xy
    box = dr.textbbox((0, 0), text, font=f)
    w, h = box[2] - box[0] + 56, box[3] - box[1] + 34
    dr.rounded_rectangle([x, y, x + w, y + h], radius=14, fill=bg)
    dr.text((x + 28, y + 17 - box[1]), text, font=f, fill=fg)
    return h


_COMPOUNDS = ("存储器|定时器|看门狗|时钟树|开发环境|环境搭建|零基础|寄存器|单片机|"
              "数据手册|中断|引脚|下载器|调试器|串口|发送器|接收器|闪烁|点亮")
_ASCII = r"[A-Za-z0-9_./+\-]+"


def _tokens(text: str) -> list[str]:
    """ASCII 单词与常用术语整体不断行（Wokwi/存储器 不被劈开），其余 CJK 逐字断。"""
    return re.findall(_COMPOUNDS + "|" + _ASCII + "|.", text)


def fit_lines(dr: ImageDraw.ImageDraw, text: str, max_w: int,
              max_size: int, min_size: int, max_lines: int) -> tuple[ImageFont.FreeTypeFont, list[str]]:
    """从大到小找字号，使 text 在 max_lines 内不超宽。按字符断行（中英混排）。"""
    size = max_size
    while size >= min_size:
        f = font(size)
        lines, cur = [], ""
        for tok in _tokens(text):
            trial = cur + tok
            if dr.textlength(trial, font=f) <= max_w:
                cur = trial
            else:
                lines.append(cur)
                cur = tok
        if cur:
            lines.append(cur)
        if len(lines) <= max_lines:
            return f, lines
        size -= 6
    return font(min_size), [text]


def hook_text(digest: str, limit: int = 16) -> str:
    """取摘要首个短语作钩子句（按「、，,：:」切）；超长时按词边界截，不留悬空分隔符。"""
    first = re.split(r"[、，,：:；;]", digest)[0].strip()
    if len(first) > limit:
        cur = ""
        for tok in _tokens(first):
            if len(cur) + len(tok) > limit:
                break
            cur += tok
        first = cur
    return first.rstrip(" /、，,；;：:").strip()


def split_title(title: str) -> tuple[str, str]:
    """拆成 (ASCII 前缀, 其余)，用于双色标题：RTC / 看门狗。"""
    m = re.match(r"^([A-Za-z0-9][A-Za-z0-9 ./+\-]*?)(?=[\u4e00-\u9fff]|$)", title)
    if m and m.group(1).strip():
        return m.group(1).strip(), title[m.end():].strip()
    return "", title


def draw_title(dr: ImageDraw.ImageDraw, xy: tuple[int, int], title: str,
               max_w: int, max_size: int, min_size: int, max_lines: int) -> int:
    latin, rest = split_title(title)
    f, lines = fit_lines(dr, title, max_w, max_size, min_size, max_lines)
    x, y = xy
    line_h = int(f.size * 1.28)
    for line in lines:
        cx = x
        if latin and line.startswith(latin):
            dr.text((cx, y), latin, font=f, fill=CYAN)
            cx += dr.textlength(latin, font=f) + dr.textlength(" ", font=f) * 0.2
            rest_part = line[len(latin):].lstrip()
            if rest_part:
                dr.text((cx, y), rest_part, font=f, fill=WHITE)
        else:
            dr.text((cx, y), line, font=f, fill=WHITE)
        y += line_h
    return y


def robot(src: Path, box: tuple[int, int, int, int], height: int) -> Image.Image:
    """裁机器人并从四边泛洪抠掉背景（青色描边作为边界，机身不受影响）。"""
    from PIL import ImageFilter
    im = Image.open(src).convert("RGB").crop(box)
    w = round(im.width * height / im.height)
    im = im.resize((w, height), Image.LANCZOS)

    SENT = (255, 0, 255)
    work = im.copy()
    seeds = [(1, 1), (w - 2, 1), (1, height - 2), (w - 2, height - 2),
             (w // 2, 1), (w // 2, height - 2), (1, height // 2), (w - 2, height // 2)]
    for seed in seeds:
        try:
            ImageDraw.floodfill(work, seed, SENT, thresh=26)
        except Exception:
            pass

    mask = Image.new("L", (w, height), 255)
    px, mk = work.load(), mask.load()
    for y in range(height):
        for x in range(w):
            if px[x, y] == SENT:
                mk[x, y] = 0
    # 只保留最大连通域（去掉对话气泡尾巴、"?" 等碎片）
    from collections import deque
    W, H = mask.size
    mpx = mask.load()
    seen = bytearray(W * H)
    best, best_size = [], 0
    for sy in range(0, H, 2):
        for sx in range(0, W, 2):
            if mpx[sx, sy] == 0 or seen[sy * W + sx]:
                continue
            q = deque([(sx, sy)])
            seen[sy * W + sx] = 1
            comp = []
            while q:
                x, y = q.popleft()
                comp.append((x, y))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < W and 0 <= ny < H and not seen[ny * W + nx] and mpx[nx, ny]:
                        seen[ny * W + nx] = 1
                        q.append((nx, ny))
            if len(comp) > best_size:
                best_size, best = len(comp), comp
    keep = Image.new("L", (W, H), 0)
    kpx = keep.load()
    for x, y in best:
        kpx[x, y] = 255
    mask = Image.composite(mask, Image.new("L", (W, H), 0), keep)
    mask = mask.filter(ImageFilter.GaussianBlur(1.2))

    out = im.convert("RGBA")
    out.putalpha(mask)
    return out


def traces(im: Image.Image, x0: int, y0: int, x1: int, y1: int) -> None:
    """中段右侧空档画低透明度电路走线（水平段+45°折弯+焊盘/过孔），填白不抢戏。"""
    if y1 - y0 < 120 or x1 - x0 < 260:
        return
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    c = CYAN + (56,)
    band = y1 - y0
    ys = (y0 + band * 0.18, y0 + band * 0.52, y0 + band * 0.84)
    xs = (x0 + (x1 - x0) * 0.06, x0 + (x1 - x0) * 0.50, x0 + (x1 - x0) * 0.78)
    # 三条走线：起点焊盘 → 折弯 → 终点焊盘（各条错位）
    runs = [
        (xs[0], ys[0], xs[1], ys[0], xs[1], ys[1]),
        (xs[1], ys[0], xs[2], ys[0], xs[2], ys[2]),
        (xs[0], ys[2], xs[0] + (xs[2] - xs[0]) * 0.45, ys[2], xs[0] + (xs[2] - xs[0]) * 0.45, ys[1]),
    ]
    for ax, ay, bx, by, cx2, cy2 in runs:
        d.line([(ax, ay), (bx, by), (cx2, cy2)], fill=c, width=5, joint="curve")
        for px, py in ((ax, ay), (cx2, cy2)):
            d.ellipse([px - 11, py - 11, px + 11, py + 11], fill=c)
    # 过孔（空心环）
    for vx, vy in ((xs[1], ys[1]), (xs[2], ys[0])):
        d.ellipse([vx - 9, vy - 9, vx + 9, vy + 9], outline=c, width=4)
    im.alpha_composite(ov)


def compose(ch: str, title: str, digest: str, size: tuple[int, int], out: Path,
            *, title_max: int, title_lines: int, robot_h: int, bottom: float = 0.045,
            banner: tuple[str, str] | None = None,
            chip_text: str | None = None) -> None:
    """chip_text: 覆盖左上角章标（合集封面等场景用，默认「第 NN 章」）。"""
    w, h = size
    im = gradient(w, h).convert("RGBA")
    dr = ImageDraw.Draw(im)
    m = round(w * 0.075)                      # 安全边距（平台 UI 覆盖区）

    y = m
    y += pill(dr, (m, y), "STM32 零基础自学", font(round(w * 0.036)), CYAN, CYAN) + round(h * 0.022)
    y += chip(dr, (m, y), chip_text or f"第 {int(ch[2:])} 章", font(round(w * 0.052))) + round(h * 0.03)

    y = draw_title(dr, (m, y), title, w - m * 2, title_max, round(w * 0.05), title_lines) + round(h * 0.02)
    # 标题右侧竖带画电路走线（不透明文字盒子会盖住重叠处，安全）
    traces(im, round(w * 0.50), y - round(h * 0.015),
           w - round(w * 0.05), h - round(h * bottom) - robot_h - round(h * 0.04))

    hook = hook_text(digest)
    if hook:
        fh = font(round(w * 0.044))
        box = dr.textbbox((0, 0), hook, font=fh)
        bh = box[3] - box[1] + 40
        bw = min(w - m * 2, box[2] - box[0] + 56)
        dr.rounded_rectangle([m, y, m + bw, y + bh], radius=12, fill=(64, 46, 34),
                             outline=YELLOW, width=2)
        dr.text((m + 28, y + 20 - box[1]), hook, font=fh, fill=YELLOW)
        y += bh

    # 摘要要点 chips（最多 2 条，填充中段信息密度）
    parts = [x.strip() for x in re.split(r"[、，,]", digest) if x.strip()][1:3]
    cy = y + round(h * 0.035)
    if parts:
        fc = font(round(w * 0.040))
        for part in parts:
            part = part[:14]
            box = dr.textbbox((0, 0), part, font=fc)
            cw, chh = box[2] - box[0] + 44, box[3] - box[1] + 30
            if m + cw > w - m:
                break
            dr.rounded_rectangle([m, cy, m + cw, cy + chh], radius=10,
                                 outline=(56, 89, 122), width=2)
            dr.text((m + 22, cy + 15 - box[1]), part, font=fc, fill=CYAN)
            cy += chh + round(h * 0.018)

    if banner:
        label, gain = banner
        by = cy + round(h * 0.03)
        bh = round(h * 0.105)
        dr.rounded_rectangle([m, by, w - m, by + bh], radius=16, fill=YELLOW)
        dr.text((m + 34, by + round(h * 0.014)), label,
                font=font(round(w * 0.030)), fill=(120, 53, 15))
        dr.text((m + 34, by + round(h * 0.055)), gain,
                font=font(round(w * 0.046)), fill=NAVY_TOP)

    src = ROOT / "final-videos" / ch / f"{ch}-cover.png"
    rb = robot(src, robot_box(src), robot_h)
    rx, ry = w - rb.width - round(w * 0.035), h - rb.height - round(h * bottom)
    # 机器人背光（青色柔光，融入场景）
    glow = Image.new("RGBA", im.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([rx - 60, ry - 40, rx + rb.width + 60, ry + rb.height + 70],
               fill=CYAN + (46,))
    glow = glow.filter(ImageFilter.GaussianBlur(70))
    im.alpha_composite(glow)
    im.alpha_composite(rb, (rx, ry))
    im = im.convert("RGB")
    dr = ImageDraw.Draw(im)
    dr.text((m, h - m - round(h * 0.028)), "SIAI小宇宙 · 逐章连载",
            font=font(round(w * 0.028)), fill=MUTED)

    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out, quality=90, optimize=True)


def fit_one(dr: ImageDraw.ImageDraw, text: str, max_w: int, max_size: int,
            min_size: int) -> ImageFont.FreeTypeFont:
    """单个短行按宽度选字号（大字报用，两行共用较小者保证视觉一致）。"""
    size = max_size
    while size > min_size:
        f = font(size)
        box = dr.textbbox((0, 0), text, font=f)
        if box[2] - box[0] <= max_w:
            return f
        size -= 4
    return font(min_size)


def compose_xhs(ch: str, title: str, digest: str, pain: tuple[str, str], out: Path,
                size: tuple[int, int] = (1080, 1440)) -> None:
    """小红书「大字报」：米白底 + 两行痛点句，第二行红色反转。"""
    w, h = size
    im = Image.new("RGB", (w, h), CREAM)
    dr = ImageDraw.Draw(im)
    m = round(w * 0.08)
    max_w = w - m * 2

    y = m
    y += pill(dr, (m, y), "STM32 零基础自学", font(round(w * 0.036)), INK, INK) + round(h * 0.028)
    y += chip(dr, (m, y), f"第 {int(ch[2:])} 章", font(round(w * 0.052)),
              bg=ACCENT, fg=CREAM) + round(h * 0.05)

    l1, l2 = pain
    fs = min(fit_one(dr, l1, max_w, round(w * 0.16), round(w * 0.07)).size,
             fit_one(dr, l2, max_w, round(w * 0.16), round(w * 0.07)).size)
    f = font(fs)
    for i, line in enumerate((l1, l2)):
        dr.text((m, y), line, font=f, fill=INK if i == 0 else ACCENT)
        y += round(fs * 1.24)

    y += round(h * 0.03)
    dr.rectangle([m, y, m + round(w * 0.18), y + 8], fill=ACCENT)
    y += round(h * 0.045)
    dr.text((m, y), title, font=font(round(w * 0.042)), fill=(70, 85, 105))

    # 底部要点列表（填充下半区，避免大片空白）
    bullets = [x.strip() for x in re.split(r"[、，,]", digest) if x.strip()][:3]
    by = round(h * 0.68)
    for item in bullets:
        item = item if len(item) <= 24 else item[:24] + "…"
        fb = fit_one(dr, item, max_w - 30, round(w * 0.040), round(w * 0.030))
        dr.ellipse([m, by + round(w * 0.019), m + 12, by + round(w * 0.019) + 12], fill=ACCENT)
        dr.text((m + 30, by), item, font=fb, fill=(48, 60, 78))
        by += round(h * 0.062)

    dr.text((m, h - m - round(h * 0.026)), "SIAI小宇宙 · 逐章连载",
            font=font(round(w * 0.028)), fill=(120, 130, 145))

    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out, quality=90, optimize=True)


TARGETS = {
    "3x4": ((1080, 1440), dict(title_max=118, title_lines=2, robot_h=470, bottom=0.05)),
    "9x16": ((1080, 1920), dict(title_max=132, title_lines=2, robot_h=560, bottom=0.12)),
    "6x7": ((1080, 1260), dict(title_max=110, title_lines=2, robot_h=360, bottom=0.05)),
    "1x1": ((1080, 1080), dict(title_max=96, title_lines=2, robot_h=300, bottom=0.05)),
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="只做某一章（如 11）")
    ap.add_argument("--style", default="all", choices=["all", "feed", "xhs", "hook"],
                    help="feed=竖版/方版基础样式, xhs=小红书大字报, hook=抖音钩子条")
    args = ap.parse_args()

    manifest = json.loads((ROOT / "wechat-mp" / "manifest.json").read_text(encoding="utf-8"))
    entries = {e["id"]: e for e in manifest if e["id"].startswith("ch")}

    for ch, e in sorted(entries.items()):
        if args.only and ch != f"ch{int(args.only):02d}":
            continue
        title = e["title"].split("|")[-1].strip()
        digest = e.get("digest", "")
        copy = COPY.get(ch, {})
        base = ROOT / "final-videos" / ch
        if args.style in ("all", "feed"):
            for name, (size, kw) in TARGETS.items():
                out = base / f"{ch}-cover-{name}.jpg"
                compose(ch, title, digest, size, out, **kw)
                print(f"[cover] {out.relative_to(ROOT)}")
        if args.style in ("all", "hook"):
            out = base / f"{ch}-hook-9x16.jpg"
            compose(ch, title, digest, (1080, 1920), out, title_max=124, title_lines=2,
                    robot_h=430, bottom=0.07,
                    banner=("这一章你能学会", copy["gain"]))
            print(f"[cover] {out.relative_to(ROOT)}")
        if args.style in ("all", "xhs"):
            out = base / f"{ch}-xhs-3x4.jpg"
            compose_xhs(ch, title, digest, copy["pain"], out)
            print(f"[cover] {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
