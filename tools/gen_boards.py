#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成 assets/boards/*.svg —— 板卡实物结构图。

说明：这些图是**依据官方数据手册 / 开源原理图自绘的矢量结构图**，
不是厂商实拍照片。图中标注了主控、晶振、稳压、按键、LED、排针定义与尺寸，
可作为接线、买板、识别山寨板的对照图。实拍照片请看官方产品页（见 docs/21 章）。
"""

from __future__ import annotations

from svgkit import Svg, T, anim_blink, anim_flow, anim_tx

W, H = 900, 620

PCB = "#123a2e"          # 绿色 PCB
PCB_DARK = "#0d2b22"
PCB_BLUE = "#123057"     # 蓝色药丸
PCB_BLUE_DARK = "#0c2242"
PCB_BLACK = "#141821"    # 黑色药丸
PCB_BLACK_DARK = "#0c0f16"
SILK = "#e8f1ff"
GOLD = "#e2b23c"
PAD = "#c8a02c"


# --------------------------------------------------------------------------- 通用零件


def board(s, x, y, w, h, fill=PCB, dark=PCB_DARK, r=14, holes=True):
    """画一块 PCB：阴影 + 板体 + 四角安装孔 + 丝印边框。"""
    s.rect(x + 5, y + 7, w, h, fill="#00000055", rx=r)
    s.rect(x, y, w, h, fill=fill, stroke=dark, rx=r, sw=2)
    s.rect(x + 6, y + 6, w - 12, h - 12, fill="none", stroke="#ffffff22", rx=r - 4,
           sw=1)
    if holes:
        for hx, hy in ((x + 14, y + 14), (x + w - 14, y + 14), (x + 14, y + h - 14),
                       (x + w - 14, y + h - 14)):
            s.circle(hx, hy, 5, fill=dark, stroke=GOLD, sw=1.6)


def header(s, x, y, n, pitch, side="top", labels=None, label_size=9,
           color=GOLD, flip=False, label_dy=None):
    """排针：n 个焊盘 + 引脚名。side=top 标签在上方，bottom 标签在下方。"""
    labels = labels or []
    for i in range(n):
        px = x + i * pitch
        if side == "top":
            s.rect(px, y - 16, pitch - 3, 16, fill=color, rx=2.5)
            s.rect(px + 3, y - 12, pitch - 9, 8, fill="#00000066", rx=1.5)
        else:
            s.rect(px, y, pitch - 3, 16, fill=color, rx=2.5)
            s.rect(px + 3, y + 4, pitch - 9, 8, fill="#00000066", rx=1.5)
        if i < len(labels):
            dy = label_dy if label_dy is not None else (-24 if side == "top" else 34)
            s.text(px + (pitch - 3) / 2, y + dy, labels[i], size=label_size,
                   anchor="middle", fill=SILK)


def chip(s, cx, cy, w, h, name, sub="", color="#1b1f28", pins=4, pin_side=10):
    """画一颗 LQFP 芯片（带四边引脚）。"""
    s.rect(cx - w / 2 - 8, cy - h / 2 - 8, w + 16, h + 16, fill="#0a0d13",
           stroke="#2a3242", rx=4)
    for i in range(pins):
        t = (i + 0.5) / pins
        if pin_side:
            s.rect(cx - w / 2 - 9, cy - h / 2 + t * h - 2, 9, 4, fill="#9aa4b2")
            s.rect(cx + w / 2, cy - h / 2 + t * h - 2, 9, 4, fill="#9aa4b2")
        s.rect(cx - w / 2 + t * w - 2, cy - h / 2 - 9, 4, 9, fill="#9aa4b2")
        s.rect(cx - w / 2 + t * w - 2, cy + h / 2, 4, 9, fill="#9aa4b2")
    s.rect(cx - w / 2, cy - h / 2, w, h, fill=color, stroke="#39424f", rx=3)
    s.circle(cx - w / 2 + 9, cy - h / 2 + 9, 3.4, fill="#5b6472")
    s.text(cx, cy - 2, name, size=11.5, anchor="middle", fill="#dfe6f0",
           weight="700", mono=True)
    if sub:
        s.text(cx, cy + 13, sub, size=9, anchor="middle", fill="#8b98b0",
               mono=True)


def crystal(s, x, y, w=46, h=20, label="8 MHz"):
    s.rect(x, y, w, h, fill="#c9ced6", stroke="#8d949e", rx=5)
    s.rect(x + 5, y + 4, w - 10, h - 8, fill="#e7ebf0", rx=3)
    s.text(x + w / 2, y + h + 12, label, size=8.5, anchor="middle", fill=SILK)


def button(s, cx, cy, r=13, label="RST"):
    s.circle(cx, cy, r, fill="#2b3038", stroke="#59606c", sw=2)
    s.circle(cx, cy, r - 5, fill="#d8b23a", stroke="#8d7420", sw=1.2)
    s.text(cx, cy + r + 12, label, size=8.5, anchor="middle", fill=SILK)


def usb(s, x, y, w=54, h=44, kind="micro", side="left"):
    body = "#c9ced6"
    s.rect(x, y, w, h, fill=body, stroke="#8d949e", rx=4)
    s.rect(x + 5, y + 5, w - 10, h - 10, fill="#8d949e", rx=2)
    if kind == "micro":
        s.rect(x + 8, y + h / 2 - 7, w - 14, 14, fill="#5d6470", rx=2)
    elif kind == "type-c":
        s.rect(x + 8, y + h / 2 - 5, w - 14, 10, fill="#5d6470", rx=5)
    s.text(x + w / 2, y - 8, f"{kind} USB", size=9, anchor="middle", fill=SILK)


def smd(s, x, y, w, h, label, color="#2b3038"):
    """小贴片元件 + 丝印标注。"""
    s.rect(x, y, w, h, fill=color, stroke="#4a5260", rx=2)
    s.rect(x - 3, y + 1, 3, h - 2, fill="#c9ced6")
    s.rect(x + w, y + 1, 3, h - 2, fill="#c9ced6")
    if label:
        s.text(x + w / 2, y - 5, label, size=8.5, anchor="middle", fill=SILK)


def led_smd(s, x, y, color, label=""):
    s.rect(x, y, 12, 8, fill=color, rx=2, stroke="#00000088")
    if label:
        s.text(x + 6, y - 5, label, size=8.5, anchor="middle", fill=SILK)


def callout(s, x, y, n, color=T.CYAN):
    s.circle(x, y, 10, fill=T.BG, stroke=color, sw=2)
    s.text(x, y + 4, str(n), size=11, anchor="middle", fill=color, weight="700")


def legend(s, x, y, items, cols=2, colw=430, dy=25, size=11.5):
    for i, (n, text_) in enumerate(items):
        r, c = divmod(i, cols)
        xx = x + c * colw
        yy = y + r * dy
        s.circle(xx + 8, yy - 4, 8, fill=T.BG, stroke=T.CYAN, sw=1.6)
        s.text(xx + 8, yy, str(n), size=9.5, anchor="middle", fill=T.CYAN,
               weight="700")
        s.text(xx + 24, yy, text_, size=size, fill=T.MUTED)


def specs(s, x, y, items, w=200, h=58, gap=12):
    for i, (k, v, color) in enumerate(items):
        xx = x + i * (w + gap)
        s.rect(xx, y, w, h, fill=T.PANEL, stroke=T.STROKE, rx=9)
        s.rect(xx, y, w, 3, fill=color, rx=2)
        s.text(xx + 12, y + 26, k, size=11, fill=T.MUTED)
        s.text(xx + 12, y + 46, v, size=13, fill=T.TEXT, weight="700")


# --------------------------------------------------------------------------- 蓝色药丸


def bluepill() -> Svg:
    s = Svg(W, H, "Blue Pill · STM32F103C8T6 最小系统板",
            "自绘矢量结构图（非实拍照片）：排针定义、板载元件与典型参数")
    s.header(tag="实物结构图", tag_color=T.CYAN)

    bx, by, bw, bh = 150, 100, 600, 254
    board(s, bx, by, bw, bh, fill=PCB_BLUE, dark=PCB_BLUE_DARK)
    usb(s, 96, 205, 54, 44, "micro")

    top = ["VB", "PC13", "PC14", "PC15", "PA0", "PA1", "PA2", "PA3", "PA4",
           "PA5", "PA6", "PA7", "PB0", "PB1", "PB10", "PB11", "RST", "3V3",
           "GND", "GND"]
    bot = ["3V3", "GND", "5V", "PB9", "PB8", "PB7", "PB6", "PB5", "PB4",
           "PA15", "PA12", "PA11", "PA10", "PA9", "PA8", "PB15", "PB14",
           "PB13", "PB12", "5V"]
    header(s, 170, by + 18, 20, 28, side="top", labels=top, label_dy=-24)
    header(s, 170, by + bh - 34, 20, 28, side="bottom", labels=bot, label_dy=34)

    chip(s, 450, 227, 96, 96, "STM32F103", "C8T6 · LQFP48", pins=6)
    s.text(450, 300, "72 MHz · 64 KB Flash · 20 KB SRAM", size=9.5,
           anchor="middle", fill=SILK)
    s.text(450, 132, "Blue Pill", size=13, anchor="middle", fill="#7fd4ff",
           weight="700")

    crystal(s, 236, 150, 46, 20, "8 MHz HSE")
    crystal(s, 236, 246, 46, 20, "32.768 kHz LSE")
    smd(s, 640, 140, 34, 20, "RT9193-33")
    smd(s, 170, 250, 26, 14, "1.5k D+")
    led_smd(s, 560, 140, T.RED, "PWR")
    led_smd(s, 610, 140, T.GREEN, "PC13")
    button(s, 690, 300, 13, "NRST")

    # BOOT 跳线
    for i, name in enumerate(("BOOT0", "BOOT1")):
        y = 290 + i * 30
        s.rect(300, y, 60, 20, fill="#0a0d13", stroke=GOLD, rx=3)
        for j in range(3):
            s.circle(310 + j * 20, y + 10, 5, fill=GOLD)
        s.text(300, y - 6, name, size=8.5, fill=SILK)
    s.rect(306, 292, 18, 14, fill="#1b1f28", rx=3)
    s.rect(306, 322, 18, 14, fill="#1b1f28", rx=3)
    s.text(370, 300, "跳线帽短接 1-2：从 Flash 启动", size=8.5, fill=SILK)

    # 编号标注
    callout(s, 236, 150, 1)
    callout(s, 236, 246, 2)
    callout(s, 450, 227, 3)
    callout(s, 640, 140, 4)
    callout(s, 330, 300, 5)
    callout(s, 690, 300, 6)
    callout(s, 616, 140, 7)
    callout(s, 170, 250, 8)

    legend(s, 40, 410, [
        (1, "8 MHz 外部晶振（HSE）：PLL ×9 → 72 MHz 系统时钟"),
        (2, "32.768 kHz 低速晶振（LSE）：RTC 走时，部分批次未焊"),
        (3, "主控 STM32F103C8T6（LQFP48，Cortex-M3）"),
        (4, "RT9193-33 LDO：USB 5 V → 3.3 V，最大 300 mA"),
        (5, "BOOT0 / BOOT1 跳线：决定从 Flash / 系统存储器 / SRAM 启动"),
        (6, "NRST 复位按键：按下拉低 NRST，低电平复位"),
        (7, "板载 LED：PWR 电源指示 + PC13 用户灯（低电平点亮）"),
        (8, "USB D+ 1.5 kΩ 上拉：让主机识别为全速设备（部分板用芯片内部上拉）"),
    ])
    s.text(40, 508, "两排 20 pin 排针定义（以 USB 端为起点）。不同厂家丝印略有差异，"
                    "接线前请用万用表确认 3V3 / GND，勿反接 5 V。", size=11,
           fill=T.AMBER)

    specs(s, 40, 524, [
        ("主控", "STM32F103C8T6", T.BLUE),
        ("主频 / 内核", "72 MHz · Cortex-M3", T.CYAN),
        ("存储", "64 KB Flash · 20 KB SRAM", T.GREEN),
        ("下载方式", "SWD（PA13/PA14）· 串口 ISP", T.AMBER),
    ])
    s.footer("尺寸 53 × 22.5 mm · 常见山寨点：Flash 标 64 KB 实为 128 KB、晶振未焊、USB 座松动")
    return s


def blackpill() -> Svg:
    s = Svg(W, H, "Black Pill · STM32F411CEU6 最小系统板",
            "自绘矢量结构图（非实拍照片）：Type-C 供电、100 MHz 主频、2×20 排针")
    s.header(tag="实物结构图", tag_color=T.VIOLET)

    bx, by, bw, bh = 170, 100, 560, 270
    board(s, bx, by, bw, bh, fill=PCB_BLACK, dark=PCB_BLACK_DARK)
    usb(s, 116, 213, 54, 44, "type-c")

    chip(s, 450, 235, 100, 100, "STM32F411", "CEU6 · UFQFPN48", pins=6)
    s.text(450, 305, "100 MHz · 512 KB Flash · 128 KB SRAM", size=9.5,
           anchor="middle", fill=SILK)
    s.text(450, 128, "WeAct Black Pill V3.1", size=12, anchor="middle",
           fill="#c4b5fd", weight="700")

    crystal(s, 250, 150, 44, 20, "25 MHz HSE")
    crystal(s, 250, 250, 44, 20, "32.768 kHz")
    smd(s, 660, 150, 32, 18, "LDO 3V3")
    led_smd(s, 560, 138, T.GREEN, "PC13")
    led_smd(s, 610, 138, T.RED, "PWR")
    button(s, 690, 330, 12, "NRST")
    button(s, 620, 330, 12, "BOOT0")
    s.rect(300, 300, 60, 18, fill="#0a0d13", stroke=GOLD, rx=3)
    for j in range(3):
        s.circle(310 + j * 20, 309, 5, fill=GOLD)
    s.text(300, 294, "BOOT0", size=8.5, fill=SILK)
    s.rect(330, 300, 18, 14, fill="#1b1f28", rx=3)

    # 排针（只标功能组，不臆造顺序）
    header(s, 196, by + 16, 20, 27, side="top", labels=[""] * 20)
    header(s, 196, by + bh - 32, 20, 27, side="bottom", labels=[""] * 20)
    s.text(196 + 20 * 27 / 2, 76, "2 × 20 pin · 2.54 mm 排针（PA0~PA15 / PB0~PB15 全部引出）",
           size=11, anchor="middle", fill=T.MUTED)
    s.text(196 + 20 * 27 / 2, 404, "排针顺序以 WeAct 官方 README 的 pinout 图为准（见 21 章链接）",
           size=11, anchor="middle", fill=T.MUTED)

    legend(s, 40, 428, [
        (1, "Type-C 供电 + 数据：板载 5 V→3.3 V LDO，支持 USB DFU 下载"),
        (2, "25 MHz HSE：F411 的 PLL 要求 25 MHz 晶振（与 F103 的 8 MHz 不同）"),
        (3, "STM32F411CEU6：Cortex-M4F，100 MHz，带 FPU/DSP"),
        (4, "BOOT0 按键 + NRST 按键：免跳线，一键进 DFU"),
        (5, "PC13 用户 LED；PA0 预留用户按键焊盘（部分批次）"),
        (6, "预留 SPI Flash 焊盘（W25Q16/W25Q64，部分批次已焊）"),
        (7, "SWD 调试口在 PA13(SWDIO) / PA14(SWCLK)，与 F103 相同"),
        (8, "注意：F411 的 USB 使用 PA11/PA12，与 CAN1 复用冲突"),
    ])
    specs(s, 40, 522, [
        ("主控", "STM32F411CEU6", T.VIOLET),
        ("主频 / 内核", "100 MHz · Cortex-M4F", T.CYAN),
        ("存储", "512 KB Flash · 128 KB SRAM", T.GREEN),
        ("下载方式", "USB DFU · SWD · 串口", T.AMBER),
    ])
    s.footer("尺寸 52.5 × 25.4 mm · 山寨识别：晶振频率写 8 MHz、无 32.768 kHz、LDO 丝印被抹掉")
    return s




# --------------------------------------------------------------------------- Nucleo


def nucleo_f411re() -> Svg:
    s = Svg(W, H, "NUCLEO-F411RE 官方开发板",
            "自绘矢量结构图（非实拍照片）：板载 ST-Link + Arduino/Morpho 双排针")
    s.header(tag="实物结构图", tag_color=T.GREEN)

    bx, by, bw, bh = 70, 96, 440, 372
    board(s, bx, by, bw, bh, fill="#1d4ed8", dark="#153a9e")

    s.rect(bx + 14, by + 14, 150, 128, fill="#0f2f8a", stroke="#7aa2ff", rx=8)
    s.text(bx + 89, by + 40, "ST-Link/V2-1", size=11.5, anchor="middle",
           fill="#cfe0ff", weight="700")
    s.text(bx + 89, by + 58, "调试器 + 虚拟串口", size=8.5, anchor="middle",
           fill="#9db8ff")
    usb(s, bx - 44, by + 40, 44, 36, "mini")
    s.rect(bx + 24, by + 76, 130, 52, fill="#0a1f5e", stroke="#7aa2ff", rx=6)
    s.text(bx + 89, by + 96, "SWD 跳线 SB", size=8.5, anchor="middle",
           fill="#9db8ff")
    s.text(bx + 89, by + 112, "断开后可用外部 ST-Link", size=8, anchor="middle",
           fill="#9db8ff")

    chip(s, bx + 300, by + 190, 104, 104, "STM32F411", "RET6 · LQFP64", pins=7)
    s.text(bx + 300, by + 262, "100 MHz · 512 KB Flash · 128 KB SRAM", size=9,
           anchor="middle", fill="#dbeafe")

    crystal(s, bx + 200, by + 60, 42, 18, "8 MHz X3")
    crystal(s, bx + 210, by + 330, 42, 18, "32.768 kHz")
    button(s, bx + 60, by + 210, 12, "B2 RESET")
    button(s, bx + 60, by + 262, 12, "B1 USER")
    led_smd(s, bx + 300, by + 60, T.GREEN, "LD2 PA5")
    led_smd(s, bx + 250, by + 60, T.RED, "LD1 PWR")
    led_smd(s, bx + 350, by + 60, T.AMBER, "LD3 COM")
    s.rect(bx + 330, by + 300, 90, 46, fill="#0a1f5e", stroke="#7aa2ff", rx=6)
    s.text(bx + 375, by + 322, "Arduino", size=9.5, anchor="middle",
           fill="#9db8ff")
    s.text(bx + 375, by + 336, "UNO R3 接口", size=8, anchor="middle",
           fill="#9db8ff")

    for i in range(19):
        s.rect(bx + 10, by + 150 + i * 11, 10, 8, fill=GOLD, rx=2)
        s.rect(bx + bw - 20, by + 150 + i * 11, 10, 8, fill=GOLD, rx=2)
    s.text(bx + 15, by + 146, "CN7（左 38 pin）", size=8.5, fill="#dbeafe")
    s.text(bx + bw - 21, by + 146, "CN10（右 38 pin）", size=8.5,
           anchor="end", fill="#dbeafe")

    callout(s, bx + 300, by + 190, 1)
    callout(s, bx + 89, by + 40, 2)
    callout(s, bx + 200, by + 60, 3)
    callout(s, bx + 60, by + 262, 4)
    callout(s, bx + 310, by + 60, 5)
    callout(s, bx + 375, by + 322, 6)

    px = 540
    s.rect(px, 96, 320, 232, fill=T.PANEL, stroke=T.STROKE, rx=12)
    s.text(px + 16, 122, "板载资源", size=13.5, fill=T.TEXT, weight="700")
    rows = [
        ("主控", "STM32F411RET6（LQFP64）"),
        ("主频", "100 MHz（HSE 8 MHz，PLLM=8/N=200/P=2）"),
        ("存储", "512 KB Flash / 128 KB SRAM"),
        ("调试", "板载 ST-Link/V2-1：SWD + 虚拟串口 + DFU"),
        ("按键", "B1 用户键（PC13）、B2 复位"),
        ("LED", "LD1 电源、LD2 用户（PA5）、LD3 调试通信"),
        ("排针", "Morpho CN7/CN10（全部 IO）+ Arduino R3"),
        ("供电", "USB 5 V 或 VIN 7~12 V，板载 3.3 V LDO"),
    ]
    for i, (k, v) in enumerate(rows):
        yy = 150 + i * 22
        s.text(px + 16, yy, k, size=10.5, fill=T.CYAN)
        s.text(px + 76, yy, v, size=10.5, fill=T.MUTED)

    s.rect(px, 340, 320, 128, fill=T.BG2, stroke=T.STROKE, rx=12)
    s.text(px + 16, 366, "和 BluePill 怎么选？", size=13, fill=T.TEXT,
           weight="700")
    s.code(px + 16, 390, [
        "Nucleo：自带调试器，开箱即用，贵 3 倍",
        "BluePill：便宜小巧，需另买 ST-Link",
        "",
        "学习阶段：Nucleo 起步，BluePill 做成品",
        "注意：F411 的 USB(PA11/PA12) 与 CAN1 冲突",
    ], size=10, lh=16, color=T.GREEN)

    s.footer("官方产品页有实拍照片与完整原理图：st.com → NUCLEO-F411RE（见 docs/21 章链接）")
    return s


def f4_discovery() -> Svg:
    s = Svg(W, H, "STM32F4-Discovery（F407VG）",
            "自绘矢量结构图（非实拍照片）：官方评估板，传感器 + 音频 + 4 颗 LED")
    s.header(tag="实物结构图", tag_color=T.ORANGE)

    bx, by, bw, bh = 60, 96, 500, 330
    board(s, bx, by, bw, bh, fill="#0e3b6e", dark="#0a2a52")
    s.text(bx + bw / 2, by + 26, "STM32F4DISCOVERY", size=13, anchor="middle",
           fill="#bcd8ff", weight="700")

    s.rect(bx + 12, by + 44, 120, 132, fill="#08214a", stroke="#7aa2ff", rx=8)
    s.text(bx + 72, by + 68, "ST-Link/V2-A", size=10, anchor="middle",
           fill="#cfe0ff", weight="700")
    s.text(bx + 72, by + 84, "SWD + 虚拟串口", size=8, anchor="middle",
           fill="#9db8ff")
    usb(s, bx - 46, by + 70, 46, 36, "mini")
    s.text(bx + 72, by + 158, "CN2 SWD 排针", size=8, anchor="middle",
           fill="#9db8ff")

    chip(s, bx + 260, by + 150, 104, 104, "STM32F407", "VGT6 · LQFP100", pins=7)
    s.text(bx + 260, by + 222, "168 MHz · 1 MB Flash · 192 KB SRAM", size=9,
           anchor="middle", fill="#dbeafe")

    crystal(s, bx + 200, by + 60, 40, 18, "8 MHz")
    crystal(s, bx + 330, by + 60, 40, 18, "32.768 kHz")
    for i, (name, col) in enumerate((("LD3", T.GREEN), ("LD4", T.ORANGE),
                                     ("LD5", T.RED), ("LD6", T.BLUE))):
        led_smd(s, bx + 150 + i * 46, by + 268, col, name)
    s.text(bx + 240, by + 292, "4 颗用户 LED：PD12~PD15", size=8, fill="#dbeafe")
    button(s, bx + 150, by + 244, 11, "B1 PA0")
    button(s, bx + 60, by + 300, 11, "RESET")

    s.rect(bx + 200, by + 236, 96, 26, fill="#08214a", stroke="#7aa2ff", rx=5)
    s.text(bx + 248, by + 254, "LIS3DSH 加速度计", size=8, anchor="middle",
           fill="#9db8ff")
    s.rect(bx + 340, by + 232, 120, 44, fill="#08214a", stroke="#7aa2ff", rx=5)
    s.text(bx + 400, by + 250, "CS43L22 音频 DAC", size=8.5, anchor="middle",
           fill="#9db8ff")
    s.text(bx + 400, by + 266, "3.5 mm 耳机座", size=8, anchor="middle",
           fill="#9db8ff")
    s.rect(bx + 340, by + 296, 120, 24, fill="#08214a", stroke="#7aa2ff", rx=5)
    s.text(bx + 400, by + 313, "MP45DT02 MEMS 麦克风", size=8, anchor="middle",
           fill="#9db8ff")
    usb(s, bx + 462, by + 110, 44, 40, "micro")
    s.text(bx + 500, by + 108, "USB OTG FS", size=8.5, anchor="middle",
           fill="#dbeafe")
    for i in range(24):
        s.rect(bx + 8, by + 200 + i * 5, 8, 4, fill=GOLD, rx=1)
        s.rect(bx + bw - 16, by + 200 + i * 5, 8, 4, fill=GOLD, rx=1)

    callout(s, bx + 260, by + 150, 1)
    callout(s, bx + 72, by + 68, 2)
    callout(s, bx + 500, by + 120, 3)
    callout(s, bx + 248, by + 249, 4)
    callout(s, bx + 400, by + 248, 5)
    callout(s, bx + 400, by + 308, 6)
    callout(s, bx + 220, by + 268, 7)
    callout(s, bx + 200, by + 60, 8)

    legend(s, 592, 130, [
        (1, "主控 STM32F407VGT6：168 MHz，带 FPU/DSP"),
        (2, "板载 ST-Link/V2-A：SWD 调试 + 虚拟串口"),
        (3, "USB OTG FS（micro-AB）：可做主/从机"),
        (4, "LIS3DSH 三轴加速度计（SPI1）"),
        (5, "CS43L22 音频 DAC + 3.5 mm 耳机输出"),
        (6, "MP45DT02 MEMS 麦克风（I2S/PDM）"),
        (7, "4 颗用户 LED（PD12~PD15）+ 用户按键（PA0）"),
        (8, "8 MHz HSE + 32.768 kHz LSE 晶振"),
    ], cols=1, dy=36, size=10.5)

    specs(s, 60, 442, [
        ("主控", "STM32F407VGT6", T.ORANGE),
        ("主频 / 内核", "168 MHz · Cortex-M4F", T.CYAN),
        ("存储", "1 MB Flash · 192 KB SRAM", T.GREEN),
        ("板载外设", "加速度计 / 音频 / 麦克风 / 4LED", T.VIOLET),
    ])
    s.rect(60, 512, 500, 56, fill=T.BG2, stroke=T.STROKE, rx=10)
    s.text(76, 534, "适合学什么：DMA 音频播放、I2S、USB、传感器融合、FFT/滤波（有 FPU）",
           size=11, fill=T.MUTED)
    s.text(76, 554, "注意：F4 系列 Flash 是「扇区擦除」，写之前先看 docs/12 章",
           size=11, fill=T.AMBER)
    s.footer("官方产品页：st.com → STM32F4DISCOVERY（含实拍照片、原理图与 Gerber）")
    return s




def f103zet6_dev() -> Svg:
    s = Svg(W, H, "STM32F103ZET6 大板（战舰/野火风格）",
            "自绘矢量结构图（非实拍照片）：144 脚全部引出，板载 LCD/SD/Flash/RS232/CAN/RS485")
    s.header(tag="实物结构图", tag_color=T.BLUE)

    bx, by, bw, bh = 40, 92, 560, 380
    board(s, bx, by, bw, bh, fill="#0f3f6b", dark="#0b2c4c")
    s.text(bx + bw / 2, by + 24, "STM32F103ZET6 开发板", size=13,
           anchor="middle", fill="#bcd8ff", weight="700")

    chip(s, bx + 240, by + 190, 110, 110, "STM32F103", "ZET6 · LQFP144", pins=8)
    s.text(bx + 240, by + 266, "72 MHz · 512 KB Flash · 64 KB SRAM",
           size=8.5, anchor="middle", fill="#dbeafe")

    blocks = [
        ("LCD 接口 (FSMC)", bx + 380, by + 60, 150, 40, T.CYAN),
        ("摄像头接口", bx + 380, by + 110, 150, 34, T.CYAN),
        ("SD 卡座", bx + 380, by + 154, 150, 34, T.VIOLET),
        ("W25Q128 SPI Flash", bx + 380, by + 198, 150, 30, T.GREEN),
        ("AT24C02 EEPROM", bx + 380, by + 238, 150, 30, T.GREEN),
        ("CH340 USB 转串口", bx + 380, by + 278, 150, 32, T.AMBER),
        ("TJA1050 CAN 收发器", bx + 60, by + 300, 150, 32, T.ORANGE),
        ("MAX485 收发器", bx + 220, by + 300, 140, 32, T.ORANGE),
        ("RS232 (SP3232)", bx + 60, by + 258, 150, 32, T.PINK),
        ("有源蜂鸣器", bx + 220, by + 258, 140, 30, T.PINK),
    ]
    for label, x, y, w, h, color in blocks:
        s.rect(x, y, w, h, fill="#08224a", stroke=color, rx=5, sw=1.2)
        s.text(x + w / 2, y + h / 2 + 4, label, size=8.5, anchor="middle",
               fill="#cfe0ff")

    crystal(s, bx + 150, by + 80, 44, 18, "8 MHz")
    crystal(s, bx + 150, by + 130, 44, 18, "32.768 kHz")
    led_smd(s, bx + 80, by + 60, T.RED, "PWR")
    led_smd(s, bx + 80, by + 96, T.GREEN, "DS0")
    led_smd(s, bx + 80, by + 132, T.BLUE, "DS1")
    for i, name in enumerate(("KEY0", "KEY1", "WK_UP")):
        button(s, bx + 40 + i * 46, by + 190, 10, name)
    button(s, bx + 150, by + 200, 10, "RESET")
    s.rect(bx + 380, by + 320, 150, 40, fill="#08224a", stroke=T.AMBER, rx=5)
    s.text(bx + 455, by + 344, "JTAG/SWD 20 pin", size=9, anchor="middle",
           fill="#cfe0ff")
    s.rect(bx + 60, by + 340, 130, 30, fill="#08224a", stroke=T.RED, rx=5)
    s.text(bx + 125, by + 360, "DC 5V 输入 + 3.3V LDO", size=8.5,
           anchor="middle", fill="#cfe0ff")
    for i in range(24):
        s.rect(bx + 8, by + 150 + i * 6, 10, 4, fill=GOLD, rx=1)
        s.rect(bx + bw - 18, by + 150 + i * 6, 10, 4, fill=GOLD, rx=1)
    s.text(bx + 14, by + 146, "2 × 24 pin 排针（144 脚全引出）", size=8.5,
           fill="#dbeafe")

    px = 620
    s.rect(px, 92, 240, 190, fill=T.PANEL, stroke=T.STROKE, rx=12)
    s.text(px + 14, 118, "为什么买大板？", size=13, fill=T.TEXT, weight="700")
    s.code(px + 14, 142, [
        "144 脚全引出，外设一次配齐：",
        "  · FSMC 并口 LCD（刷屏比 SPI 快 20 倍）",
        "  · 摄像头 DCMI 接口",
        "  · SDIO / SD 卡",
        "  · CAN、RS485、RS232 三种总线",
        "  · 双 Flash/EEPROM 练 I2C/SPI",
        "",
        "缺点：体积大、贵、例程容易「跑马灯化」",
    ], size=10, lh=17, color=T.GREEN)

    s.rect(px, 296, 240, 176, fill=T.BG2, stroke=T.STROKE, rx=12)
    s.text(px + 14, 322, "板载总线一览", size=13, fill=T.TEXT, weight="700")
    rows = [("I2C1", "AT24C02（PB6/PB7）"),
            ("SPI1", "W25Q128（PA5~PA7）"),
            ("USART1", "CH340 下载（PA9/PA10）"),
            ("USART2/3", "RS232 / RS485"),
            ("CAN1", "TJA1050（PA11/PA12）"),
            ("FSMC", "LCD 与外部 SRAM/NAND"),
            ("SDIO", "SD 卡（PC8~PC12）"),
            ("ADC", "板载电位器 + 光敏（PA0/PA1）")]
    for i, (k, v) in enumerate(rows):
        yy = 348 + i * 15
        s.text(px + 14, yy, k, size=10, fill=T.CYAN)
        s.text(px + 78, yy, v, size=10, fill=T.MUTED)

    specs(s, 40, 486, [
        ("主控", "STM32F103ZET6", T.BLUE),
        ("主频 / 内核", "72 MHz · Cortex-M3", T.CYAN),
        ("存储", "512 KB Flash · 64 KB SRAM", T.GREEN),
        ("外设数量", "112 个 GPIO · 21 通道 ADC", T.VIOLET),
    ])
    s.footer("大板原理图（PDF）建议去卖家资料包下载，对照 docs/21 章「如何看懂最小系统」一起看")
    return s



# --------------------------------------------------------------------------- 引脚全图


def pinout_bluepill() -> Svg:
    s = Svg(W, H, "STM32F103C8T6（LQFP48）引脚全图",
            "自绘矢量结构图（非实拍照片）：48 脚编号、名称与常用复用功能")
    s.header(tag="引脚图", tag_color=T.AMBER)

    cx, cy, cs = 400, 300, 200
    s.rect(cx - cs / 2, cy - cs / 2, cs, cs, fill="#1b1f28", stroke="#39424f",
           rx=6)
    s.circle(cx - cs / 2 + 14, cy - cs / 2 + 14, 5, fill="#5b6472")
    s.text(cx, cy - 24, "STM32F103C8T6", size=14, anchor="middle",
           fill="#dfe6f0", weight="700", mono=True)
    s.text(cx, cy + 0, "LQFP48 · 7 × 7 mm", size=10, anchor="middle",
           fill="#8b98b0")
    s.text(cx, cy + 22, "Cortex-M3 · 72 MHz", size=10, anchor="middle",
           fill="#8b98b0")
    s.text(cx, cy + 44, "64 KB Flash / 20 KB SRAM", size=10, anchor="middle",
           fill="#8b98b0")

    left = ["VBAT", "PC13", "PC14", "PC15", "PD0/OSC_IN", "PD1/OSC_OUT",
            "NRST", "VSSA", "VDDA", "PA0", "PA1", "PA2"]
    bottom = ["PA3", "PA4", "PA5", "PA6", "PA7", "PB0", "PB1", "PB2/BOOT1",
              "PB10", "PB11", "VSS_1", "VDD_1"]
    right = ["PB12", "PB13", "PB14", "PB15", "PA8", "PA9", "PA10", "PA11",
             "PA12", "PA13", "VSS_2", "VDD_2"]
    top = ["PA14", "PA15", "PB3", "PB4", "PB5", "PB6", "PB7", "BOOT0",
           "PB8", "PB9", "VSS_3", "VDD_3"]

    def style(name):
        if name.startswith(("VDD", "VSS", "VDDA", "VSSA", "VBAT")):
            return T.RED
        if name.startswith(("PC", "PD")):
            return T.VIOLET
        if name.startswith("PA"):
            return T.CYAN
        if name.startswith("PB"):
            return T.GREEN
        return T.AMBER

    pitch = cs / 12
    for i, nm in enumerate(left):
        y = cy - cs / 2 + (i + 0.5) * pitch
        s.line(cx - cs / 2 - 16, y, cx - cs / 2, y, stroke=GOLD, sw=2)
        s.text(cx - cs / 2 - 20, y + 3, str(i + 1), size=8, anchor="end",
               fill=T.DIM, mono=True)
        s.text(cx - cs / 2 - 34, y + 3, nm, size=8.5, anchor="end",
               fill=style(nm), mono=True)
    for i, nm in enumerate(bottom):
        x = cx - cs / 2 + (i + 0.5) * pitch
        s.line(x, cy + cs / 2, x, cy + cs / 2 + 16, stroke=GOLD, sw=2)
        s.text(x, cy + cs / 2 + 28, str(i + 13), size=8, anchor="middle",
               fill=T.DIM, mono=True)
        s.text(x, cy + cs / 2 + 44, nm, size=8.5, anchor="middle",
               fill=style(nm), mono=True)
    for i, nm in enumerate(right):
        y = cy + cs / 2 - (i + 0.5) * pitch
        s.line(cx + cs / 2, y, cx + cs / 2 + 16, y, stroke=GOLD, sw=2)
        s.text(cx + cs / 2 + 20, y + 3, str(i + 25), size=8, fill=T.DIM,
               mono=True)
        s.text(cx + cs / 2 + 34, y + 3, nm, size=8.5, fill=style(nm), mono=True)
    for i, nm in enumerate(top):
        x = cx + cs / 2 - (i + 0.5) * pitch
        s.line(x, cy - cs / 2 - 16, x, cy - cs / 2, stroke=GOLD, sw=2)
        s.text(x, cy - cs / 2 - 22, str(i + 37), size=8, anchor="middle",
               fill=T.DIM, mono=True)
        s.text(x, cy - cs / 2 - 34, nm, size=8.5, anchor="middle",
               fill=style(nm), mono=True)

    px = 570
    s.rect(px, 130, 290, 320, fill=T.PANEL, stroke=T.STROKE, rx=12)
    s.text(px + 14, 156, "常用复用功能（AF）", size=13, fill=T.TEXT,
           weight="700")
    rows = [
        ("PA9 / PA10", "USART1_TX / RX（默认下载口）", T.CYAN),
        ("PA2 / PA3", "USART2_TX / RX", T.CYAN),
        ("PB6 / PB7", "I2C1_SCL / SDA（接 OLED）", T.GREEN),
        ("PA5 / PA6 / PA7", "SPI1_SCK / MISO / MOSI", T.GREEN),
        ("PA4", "SPI1_NSS 或 ADC_IN4", T.GREEN),
        ("PA11 / PA12", "USB_DM / DP（同时是 CAN_RX/TX）", T.VIOLET),
        ("PA13 / PA14", "SWDIO / SWCLK（调试口，别复用）", T.RED),
        ("PA0 ~ PA7", "ADC1_IN0 ~ IN7", T.AMBER),
        ("PB0 / PB1", "ADC1_IN8 / IN9，TIM3_CH3/CH4", T.AMBER),
        ("PA8 ~ PA11", "TIM1_CH1 ~ CH4（PWM / 舵机）", T.PINK),
        ("PC13", "板载用户 LED（低电平点亮）", T.VIOLET),
        ("PD0 / PD1", "8 MHz 晶振输入 / 输出", T.AMBER),
        ("PB2", "BOOT1（默认下拉）", T.AMBER),
        ("BOOT0", "启动模式选择，需外部 10 kΩ 下拉", T.AMBER),
    ]
    for i, (k, v, c) in enumerate(rows):
        yy = 182 + i * 19
        s.text(px + 14, yy, k, size=9.5, mono=True, fill=c)
        s.text(px + 132, yy, v, size=9, fill=T.MUTED)

    s.rect(40, 470, 820, 100, fill=T.BG2, stroke=T.STROKE, rx=12)
    s.text(58, 496, "看引脚图的 5 个要点", size=12.5, fill=T.TEXT, weight="700")
    notes = [
        "① 电源：VDD_1/2/3 各配 100 nF 去耦电容，VDDA 加 10 nF + 1 µF，VBAT 接 3.3 V 或纽扣电池",
        "② NRST 内部已有上拉，外部只需 100 nF 到地，不必再并 10 kΩ",
        "③ BOOT0 必须有 10 kΩ 下拉，否则上电可能进入系统存储器（串口下载）模式",
        "④ 5 V 容忍：数据手册标 FT 的引脚可接 5 V 数字信号；VDDA / 模拟输入不能超 3.3 V",
        "⑤ 未使用的 IO 建议配成模拟输入或输出低，可显著降低功耗（见 docs/16 章）",
    ]
    for i, n in enumerate(notes):
        s.text(58, 518 + i * 18, n, size=10.5, fill=T.MUTED)
    s.footer("引脚编号以 ST 官方数据手册 DS5319（F103x8/B）第 4 章 Pinouts 为准")
    return s



# --------------------------------------------------------------------------- 外设接线总览


def peripheral_wiring() -> Svg:
    s = Svg(W, H, "常用外设接线总览", "以 BluePill 为例：8 个入门外设的引脚分配与总线归属")
    s.header(tag="接线图", tag_color=T.PINK)

    s.rect(360, 205, 180, 190, fill=T.PANEL2, stroke=T.CYAN, rx=12, sw=2)
    s.text(450, 240, "STM32F103", size=15, anchor="middle", fill=T.TEXT,
           weight="700")
    s.text(450, 262, "C8T6", size=12, anchor="middle", fill=T.MUTED)
    s.text(450, 296, "PA5  PB6  PA9", size=10.5, anchor="middle", fill=T.CYAN,
           mono=True)
    s.text(450, 314, "PA0  PB7  PA10", size=10.5, anchor="middle", fill=T.CYAN,
           mono=True)
    s.text(450, 332, "PA1  PA6  PB0", size=10.5, anchor="middle", fill=T.CYAN,
           mono=True)
    s.text(450, 350, "PA7  PA4  PB12", size=10.5, anchor="middle", fill=T.CYAN,
           mono=True)
    s.text(450, 378, "3.3 V / GND 共用", size=10, anchor="middle", fill=T.MUTED)

    left = [
        ("LED + 330Ω", "PA5 · 推挽输出", T.GREEN, 140),
        ("按键（对地）", "PA0 · 上拉输入 + EXTI", T.VIOLET, 214),
        ("电位器 / 光敏", "PA1 · ADC1_IN1", T.AMBER, 288),
        ("SG90 舵机", "PB0 · TIM3_CH3 PWM", T.PINK, 362),
    ]
    right = [
        ("SSD1306 OLED", "PB6 SCL / PB7 SDA · I2C1", T.CYAN, 140),
        ("W25Q64 Flash", "PA5/6/7 + PA4 CS · SPI1", T.GREEN, 214),
        ("HC-05 蓝牙", "PA9 TX / PA10 RX · USART1", T.BLUE, 288),
        ("DHT11 温湿度", "PB12 · 单总线时序", T.ORANGE, 362),
    ]
    for label, sub, color, y in left:
        s.rect(40, y, 200, 54, fill=T.PANEL, stroke=color, rx=10)
        s.text(56, y + 24, label, size=12, fill=T.TEXT, weight="600")
        s.text(56, y + 42, sub, size=10, fill=color, mono=True)
        s.arrow(244, y + 27, 356, y + 27, color=color, sw=2, dash="6 8",
                cls=f"wf{y}")
    for label, sub, color, y in right:
        s.rect(660, y, 200, 54, fill=T.PANEL, stroke=color, rx=10)
        s.text(676, y + 24, label, size=12, fill=T.TEXT, weight="600")
        s.text(676, y + 42, sub, size=10, fill=color, mono=True)
        s.arrow(544, y + 27, 656, y + 27, color=color, sw=2, dash="6 8",
                cls=f"wf{y}")

    css = []
    for _, _, _, y in left + right:
        css.append(anim_flow(f".wf{y}", dur="1.8s", dash="6 8", shift=-14))
    s.add_style("\n".join(css))

    tips = [
        ("资源冲突要先查", "SPI1 的 PA5~PA7 与 ADC、TIM2 复用；一个引脚同一时刻只能有一个功能", T.RED),
        ("电平要匹配", "HC-05、OLED、W25Q64 都是 3.3 V 器件，5 V 模块（如继电器）需电平转换或三极管驱动", T.AMBER),
        ("共地是前提", "所有外设必须与开发板 GND 相连；只接信号线不接地是最常见的「玄学故障」", T.GREEN),
    ]
    for i, (t, note, color) in enumerate(tips):
        x = 40 + i * 274
        s.rect(x, 452, 258, 76, fill=T.BG2, stroke=T.STROKE, rx=10)
        s.rect(x, 452, 3, 76, fill=color, rx=2)
        s.text(x + 14, 476, t, size=12, fill=T.TEXT, weight="700")
        s.text(x + 14, 494, note[:30], size=9.5, fill=T.MUTED)
        if len(note) > 30:
            s.text(x + 14, 510, note[30:], size=9.5, fill=T.MUTED)
    s.footer("完整接线表见各章「硬件与接线」小节与 examples/*/README.md")
    return s


ALL = [bluepill, blackpill, nucleo_f411re, f4_discovery, f103zet6_dev,
       pinout_bluepill, peripheral_wiring]

NAMES = {
    "bluepill": "bluepill-stm32f103c8t6",
    "blackpill": "blackpill-stm32f411ce",
    "nucleo_f411re": "nucleo-f411re",
    "f4_discovery": "f4-discovery",
    "f103zet6_dev": "f103zet6-dev",
    "pinout_bluepill": "pinout-bluepill",
    "peripheral_wiring": "peripheral-wiring",
}
