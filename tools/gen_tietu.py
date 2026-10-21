#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成公众号「贴图」竖版页面（1080x1440，3:4）。

为什么是竖版：贴图在手机上按屏幕宽度整屏缩放，1080 宽画布上的字号
要乘 430/1080 才是手机实际字号。上一版贴图（ch01 v1）用的是 900x560
横图、10.5px 字，到手机上只剩 5px —— 全糊。所以：

* 画布一律 1080x1440；
* 最小字号 28 -> 手机 11.1px（低于阈值直接失败）；
* 封面大字必须与图文标题逐字一致，且标题不超过后台 20 字上限。

用法：
    python tools/gen_tietu.py                 # 生成全部主题（含自检）
    python tools/gen_tietu.py flash-download   # 只生成一个主题
"""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from svgkit import Svg, T  # noqa: E402

W, H = 1080, 1440
M = 84          # 左右留白
CW = W - 2 * M  # 内容宽 912

# 排版尺度（1080 宽画布）
S_KICKER = 34
S_H1 = 72
S_H2 = 52
S_LEAD = 40
S_BODY = 34
S_CAP = 28

PHONE_W = 430       # 最常见的手机逻辑宽度
MIN_EFFECTIVE = 11  # 手机上最小可读字号（CSS px）
TITLE_MAX = 20      # 后台标题计数器上限（实测 0/20）


# ---------------------------------------------------------------- 画布构件

def header(s: Svg, kicker: str, page: str, accent: str = T.CYAN) -> None:
    """页眉：左侧系列标 + 右侧页码。"""
    s.rect(M, 92, 14, 34, fill=accent, rx=4)
    s.text(M + 30, 122, kicker, size=S_KICKER, fill=T.MUTED, weight="600", ls=1)
    s.text(W - M, 122, page, size=S_KICKER, fill=T.DIM, anchor="end", weight="600")
    s.line(M, 158, W - M, 158, stroke=T.STROKE, sw=2)


def footer(s: Svg, hint: str = "公众号「SIAI小宇宙」· 回复「资料」拿完整仓库") -> None:
    s.line(M, H - 150, W - M, H - 150, stroke=T.STROKE, sw=2)
    s.text(W / 2, H - 96, hint, size=S_CAP, fill=T.DIM, anchor="middle")


def lines(s: Svg, x: float, y: float, rows, size=S_BODY, fill=T.TEXT,
          gap=None, weight="normal", anchor="start") -> float:
    """按给定行数组逐行输出，返回下一行的 y。"""
    gap = gap or size * 1.55
    for i, row in enumerate(rows):
        s.text(x, y + i * gap, row, size=size, fill=fill, weight=weight, anchor=anchor)
    return y + len(rows) * gap


# ---------------------------------------------------------------- 主题数据

@dataclass
class Topic:
    slug: str
    ch: str                  # 输出目录：final-videos/<ch>/tietu-v2/<slug 为空则直接放该目录>
    kicker: str              # 页眉系列标
    badge: str               # 封面左下角章标
    title: str               # 图文标题（<=20 字，封面大字必须拼回它）
    cover_lines: tuple       # 封面三行大字
    cover_sub: tuple         # 封面副标题两行
    meaning_lead: str
    meaning_quote: str
    meaning_rows: tuple      # ((label, sub), ...) 3 条
    meaning_caption: str
    causes_head: str
    causes: tuple            # ((num, title, sub1, sub2), ...) 3 条
    causes_caption: str
    steps_head: str
    steps: tuple             # ((num, title, sub1, sub2), ...) 3 条
    steps_caption: str
    published: bool = False  # 已发布：不再重渲染 PNG，仅保留源码


# ---------------------------------------------------------------- 页面

def page_cover(t: Topic) -> Svg:
    """封面页：决定推荐流里点不点，字必须最大。"""
    s = Svg(W, H, title=t.title)
    s.rect(M, 96, 430, 78, fill="none", stroke=T.CYAN, rx=39, sw=3)
    s.text(M + 215, 148, "STM32 零基础自学", size=36, fill=T.CYAN,
           anchor="middle", weight="600")
    s.rect(M, 210, 210, 74, fill=T.AMBER, rx=14)
    s.text(M + 105, 262, t.badge, size=40, fill="#1a1205", anchor="middle", weight="700")

    s.text(M, 470, t.cover_lines[0], size=96, fill=T.TEXT, weight="700")
    s.text(M, 600, t.cover_lines[1], size=104, fill=T.AMBER, weight="700", ls=1)
    s.text(M, 760, t.cover_lines[2], size=76, fill=T.CYAN, weight="700")

    s.line(M, 850, W - M, 850, stroke=T.STROKE, sw=3)
    lines(s, M, 930, t.cover_sub, size=40, fill=T.MUTED, gap=64)

    s.text(M, H - 190, "SIAI小宇宙 · 逐章连载", size=32, fill=T.DIM)
    s.text(W - M, H - 190, "1 / 4", size=32, fill=T.DIM, anchor="end")
    s.line(M, H - 150, W - M, H - 150, stroke=T.STROKE, sw=2)
    s.text(W / 2, H - 96, "公众号「SIAI小宇宙」· 回复「资料」拿完整仓库",
           size=S_CAP, fill=T.DIM, anchor="middle")
    return s


def page_meaning(t: Topic) -> Svg:
    s = Svg(W, H, title=t.meaning_quote)
    header(s, t.kicker + " ①", "2 / 4")
    s.text(M, 300, t.meaning_lead, size=S_LEAD, fill=T.MUTED)
    s.text(M, 420, t.meaning_quote, size=S_H1, fill=T.AMBER, weight="700")
    s.line(M, 470, W - M, 470, stroke=T.STROKE, sw=2)

    y = 590
    for i, (a, b) in enumerate(t.meaning_rows, 1):
        s.rect(M, y - 52, CW, 150, fill=T.PANEL, stroke=T.STROKE, rx=18)
        s.text(M + 40, y, f"{i}", size=52, fill=T.CYAN, weight="700")
        s.text(M + 110, y - 6, a, size=S_H2 - 8, fill=T.TEXT, weight="600")
        s.text(M + 110, y + 52, b, size=S_CAP + 2, fill=T.MUTED)
        y += 190

    s.text(M, 1224, t.meaning_caption, size=S_CAP + 2, fill=T.AMBER)
    footer(s)
    return s


def page_causes(t: Topic) -> Svg:
    s = Svg(W, H, title=t.causes_head)
    header(s, t.kicker + " ②", "3 / 4", accent=T.AMBER)
    s.text(M, 300, "按概率排，先查第一个", size=S_LEAD, fill=T.MUTED)
    s.text(M, 400, t.causes_head, size=S_H1, fill=T.TEXT, weight="700")

    y = 500
    for num, title, sub1, sub2 in t.causes:
        s.rect(M, y, CW, 214, fill=T.PANEL, stroke=T.STROKE, rx=20)
        s.text(M + 44, y + 92, num, size=64, fill=T.AMBER, weight="700")
        s.text(M + 140, y + 86, title, size=S_H2, fill=T.TEXT, weight="700")
        lines(s, M + 140, y + 150, [sub1, sub2], size=S_BODY - 2, fill=T.MUTED, gap=46)
        y += 244

    s.text(M, 1258, t.causes_caption, size=S_CAP + 2, fill=T.CYAN)
    footer(s)
    return s


def page_steps(t: Topic) -> Svg:
    s = Svg(W, H, title=t.steps_head)
    header(s, t.kicker + " ③", "4 / 4", accent=T.GREEN)
    s.text(M, 300, "照这个顺序，别跳步", size=S_LEAD, fill=T.MUTED)
    s.text(M, 400, t.steps_head, size=S_H1, fill=T.TEXT, weight="700")

    y = 500
    for num, title, sub1, sub2 in t.steps:
        s.rect(M, y, CW, 214, fill=T.PANEL2, stroke=T.STROKE, rx=20)
        s.rect(M + 34, y + 44, 84, 84, fill=T.GREEN, rx=42)
        s.text(M + 76, y + 100, num, size=46, fill="#04120c", anchor="middle", weight="700")
        s.text(M + 150, y + 92, title, size=S_H2 - 4, fill=T.TEXT, weight="700")
        lines(s, M + 150, y + 158, [sub1, sub2], size=S_BODY - 2, fill=T.MUTED, gap=46)
        y += 244

    s.text(M, 1258, t.steps_caption, size=S_CAP + 2, fill=T.GREEN)
    footer(s)
    return s


PAGES = {
    "01-cover": page_cover,
    "02-meaning": page_meaning,
    "03-causes": page_causes,
    "04-steps": page_steps,
}


# ---------------------------------------------------------------- 主题内容

TOPICS = [
    # 已发布（2026-10-21 12:27），封面沿用旧文案，见 sources 说明。
    Topic(
        slug="", ch="ch01",
        kicker="STM32 · 下载报错", badge="第 1 章",
        title="No target 九成不是芯片坏了",
        cover_lines=("下载报", "No target？", "先查这三点"),
        cover_sub=("SWD 接线 · 共地 · 调试口被关", "九成不是芯片坏了"),
        meaning_lead="调试器这句话的意思是：",
        meaning_quote="「我找不到芯片」",
        meaning_rows=(
            ("SWD 只是两根问话的线", "SWDIO 问，SWCLK 打节拍"),
            ("芯片不回话，就报 No target", "跟「下载失败」不是一回事"),
            ("九成不是芯片坏了", "是线、是电、是程序关了调试口"),
        ),
        meaning_caption="先分清：找不到目标 ≠ 下载失败 ≠ 读保护",
        causes_head="三个原因",
        causes=(
            ("①", "没共地 / 没供电", "4 根线里 GND 最容易松", "板子单独供电，不要只靠调试器"),
            ("②", "SWDIO、SWCLK 接反", "丝印对上号：SWDIO 对 SWDIO", "接反不会烧板，但一定连不上"),
            ("③", "调试口被程序关了", "PA13/PA14 被配成普通 GPIO", "程序一跑起来，SWD 就失联了"),
        ),
        causes_caption="第 ③ 种最容易被误判成「板子烧了」",
        steps_head="三步排查",
        steps=(
            ("1", "量电", "万用表量 3V3 与 GND", "板和调试器要共地"),
            ("2", "按住 NRST 再点下载", "抢在程序跑起来之前连上", "CubeMX/IDE 里也有 Connect under reset"),
            ("3", "还不行就换启动方式", "BOOT0 拉高，从系统存储器启动", "用 STM32CubeProgrammer 全片擦除"),
        ),
        steps_caption="连不上不是板子坏了，是「连的时机」或「接的线」不对",
        published=True,
    ),
    Topic(
        slug="flash-download", ch="tietu",
        kicker="STM32 · 下载报错", badge="第 18 章",
        title="Flash下载失败查这三点",
        cover_lines=("Flash", "下载失败", "查这三点"),
        cover_sub=("算法选错 · 读保护 · 时钟", "先分清和 No target 的区别"),
        meaning_lead="下载器报这句话的时候：",
        meaning_quote="「写到一半，断了」",
        meaning_rows=(
            ("已经连上了芯片", "跟 No target 不是一回事"),
            ("卡在擦写 Flash 这一步", "算法、保护、时钟三选一"),
            ("多半不用换板子", "三种都能自己排掉"),
        ),
        meaning_caption="先分清：No target 是连不上，这一步是连上了写不进",
        causes_head="三个原因",
        causes=(
            ("①", "Flash 算法选错", "工程里挂的是别的型号的算法", "核对型号与 Flash 容量"),
            ("②", "芯片被读保护", "RDP 打开后下载器写不进去", "Option Bytes 里解除 RDP"),
            ("③", "调试时钟太快", "SWD 频率高，擦写时容易断", "降到 1 MHz 以下再试"),
        ),
        causes_caption="第 ② 种常被当成「芯片锁死了」",
        steps_head="三步排查",
        steps=(
            ("1", "核对 Flash 算法", "Debug → Flash Download 里看算法", "型号、容量都要对得上"),
            ("2", "解除读保护", "CubeProgrammer → Option Bytes", "RDP 改 Level 0 后重新上电"),
            ("3", "降低调试时钟再试", "SWD 频率调到 1 MHz 以下", "排除不稳导致的中途断开"),
        ),
        steps_caption="先别急着换板子：这三种都能自己排掉",
    ),
    Topic(
        slug="uart-garbled", ch="tietu",
        kicker="STM32 · 串口报错", badge="第 6 章",
        title="串口全是乱码先查三处",
        cover_lines=("串口", "全是乱码", "先查三处"),
        cover_sub=("波特率 · 共地 · 时钟", "收不到和乱码是两回事"),
        meaning_lead="收到一串乱码，说明：",
        meaning_quote="「速度没对上」",
        meaning_rows=(
            ("线是通的，数据也在来", "完全收不到才要查 TX/RX 接反"),
            ("错的是解码的节奏", "波特率、校验、停止位要一致"),
            ("也可能是时钟真的偏了", "HSE 起振失败会退回 HSI"),
        ),
        meaning_caption="先分清：乱码 ≠ 收不到，收不到要查接线",
        causes_head="三个原因",
        causes=(
            ("①", "波特率不匹配", "代码、CubeMX、串口助手三处都要对", "一边 115200 一边 9600 必乱"),
            ("②", "没有共地", "板和 USB-TTL 要接 GND", "只接 TX/RX 会时好时坏"),
            ("③", "时钟不是你以为的那个", "HSE 没起振就退回内部 HSI", "波特率整体偏，越跑越乱"),
        ),
        causes_caption="第 ③ 种最隐蔽：代码没改，换块板就乱了",
        steps_head="三步排查",
        steps=(
            ("1", "先对两端的波特率", "代码、CubeMX、串口助手逐个核对", "改完重新上电再试"),
            ("2", "把 GND 接上", "板子 GND 与 USB-TTL GND 短接", "杜邦线别超过 30 cm"),
            ("3", "确认时钟真的跑起来", "看 MCO 输出或用示波器量", "HSE 失败在时钟初始化里能看出来"),
        ),
        steps_caption="乱码是「速度」问题，收不到是「线」问题",
    ),
    Topic(
        slug="swd-brick", ch="tietu",
        kicker="STM32 · 调试失联", badge="第 18 章",
        title="烧完就变砖SWD救回来",
        cover_lines=("烧完就变砖", "SWD", "救回来"),
        cover_sub=("Debug 被关 · 引脚被占用", "不是芯片坏了"),
        meaning_lead="程序下载完，SWD 连不上了：",
        meaning_quote="「不是芯片死了」",
        meaning_rows=(
            ("程序把调试口占了", "PA13/PA14 被配成普通 GPIO"),
            ("或者干脆关了 Debug", "CubeMX 里选成 No Debug"),
            ("还有救", "按住 NRST 或改 BOOT0 都能抢回来"),
        ),
        meaning_caption="先分清：连不上 ≠ 芯片损坏",
        causes_head="三个原因",
        causes=(
            ("①", "Debug 选项被关", "SYS → Debug 选成 No Debug", "生成的代码会把 SWD 关掉"),
            ("②", "PA13/PA14 当普通 IO", "SWD 引脚被重映射走了", "程序一跑，调试器就失联"),
            ("③", "进了低功耗模式", "Stop/Standby 下调试口关闭", "唤醒前连不上是正常的"),
        ),
        causes_caption="第 ① 种最常见，而且能提前避免",
        steps_head="三步救回来",
        steps=(
            ("1", "按住 NRST 再点下载", "连上的瞬间松手", "IDE 里叫 Connect under reset"),
            ("2", "BOOT0 拉高换启动方式", "从系统存储器启动，跳过程序", "CubeProgrammer 全片擦除"),
            ("3", "擦完把 Debug 改回来", "SYS → Debug 选 Serial Wire", "重新生成代码再下载"),
        ),
        steps_caption="变砖多数是「自己关的门」，不是硬件坏",
    ),
]


# ---------------------------------------------------------------- 自检

def _est_width(text: str, size: float) -> float:
    """粗略估算文字宽度：CJK 按 1.0em，ASCII 按 0.55em。"""
    w = 0.0
    for ch in text:
        w += size * (1.0 if ord(ch) > 0x2E7F else 0.55)
    return w


def check_svg(path: str, t: Topic) -> list[str]:
    """返回问题列表：字号太小 / 文字溢出 / 标题与封面不一致。"""
    problems = []
    with open(path, encoding="utf-8") as f:
        svg = f.read()

    sizes = sorted({float(x) for x in re.findall(r'font-size="([0-9.]+)"', svg)})
    if sizes:
        phone = round(sizes[0] * PHONE_W / W, 1)
        if phone < MIN_EFFECTIVE:
            problems.append(f"最小字号 {sizes[0]} -> 手机 {phone}px < {MIN_EFFECTIVE}")

    for m in re.finditer(r'<text ([^>]*)>([^<]*)</text>', svg):
        attrs, content = m.group(1), m.group(2)
        am = re.search(r'x="([0-9.]+)"', attrs)
        sm = re.search(r'font-size="([0-9.]+)"', attrs)
        if not am or not sm:
            continue
        x, size = float(am.group(1)), float(sm.group(1))
        an = re.search(r'text-anchor="(\w+)"', attrs)
        anchor = an.group(1) if an else "start"
        content = (content.replace("&amp;", "&").replace("&lt;", "<")
                   .replace("&gt;", ">").replace("&quot;", '"'))
        w = _est_width(content, size)
        left = x - w / 2 if anchor == "middle" else (x - w if anchor == "end" else x)
        if left < 0 or left + w > W:
            problems.append(f"溢出({left:.0f}+{w:.0f}>{W}): {content[:24]}")
    return problems


def check_topic(t: Topic) -> list[str]:
    problems = []
    if len(t.title) > TITLE_MAX:
        problems.append(f"标题 {len(t.title)} 字 > {TITLE_MAX}")
    joined = "".join(t.cover_lines)
    if joined != t.title and not t.published:
        problems.append(f"封面「{joined}」≠ 标题「{t.title}」")
    return problems


def out_dir(root: str, t: Topic) -> str:
    """ch01 用 ch 目录（已发布），其余主题统一放 final-videos/tietu/<slug>/。"""
    if t.slug:
        return os.path.join(root, "final-videos", "tietu", t.slug)
    return os.path.join(root, "final-videos", t.ch, "tietu-v2")


def main(argv) -> int:
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    only = argv[1] if len(argv) > 1 else None
    bad = 0
    for t in TOPICS:
        if only and only not in (t.slug or "ch01"):
            continue
        d = out_dir(root, t)
        for name, fn in PAGES.items():
            p = os.path.join(d, name + ".svg")
            fn(t).save(p)
            problems = check_svg(p, t)
            status = "ok" if not problems else "FAIL"
            note = f"「{t.title}」{len(t.title)}/{TITLE_MAX} 字"
            if name == "01-cover":
                problems += check_topic(t)
                status = "ok" if not problems else "FAIL"
            bad += 0 if status == "ok" else 1
            print(f"[{status}] {t.slug or 'ch01'}/{name} {note if name == '01-cover' else ''}")
            for x in problems:
                print(f"       - {x}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
