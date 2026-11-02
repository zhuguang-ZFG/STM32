#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 assets/diagrams/classic-03-*.svg —— 第 03 章 GPIO 经典课的 11 张静态证据图。

每张图对应长片 storyboard 里的一个学习任务（ch03-s08 … s26），
事实口径与 docs/03-GPIO与LED.md、RM0008、DS5319 保持一致。
纯静态 SVG：无脚本、无动画、无外部图片 / href / filter / url()。
"""

from __future__ import annotations

import os
import xml.dom.minidom

from svgkit import Svg, T

W, H = 960, 660

FOOTER_LABEL = "自绘矢量动画 · STM32 知识库"


# ----------------------------------------------------------------------
# 小元件
# ----------------------------------------------------------------------

def _ground(s: Svg, x: float, y: float, color: str = T.STROKE) -> None:
    """GND 符号，上端子位于 (x, y)。"""
    s.line(x, y, x, y + 10, stroke=color, sw=1.5)
    s.line(x - 12, y + 10, x + 12, y + 10, stroke=color, sw=2)
    s.line(x - 7, y + 16, x + 7, y + 16, stroke=color, sw=2)
    s.line(x - 3, y + 22, x + 3, y + 22, stroke=color, sw=2)


def _note_box(s: Svg, x, y, w, h, title, lines, color, title_color=None,
              size=11.5, lh=22) -> None:
    """带色边框的要点框：粗体标题 + 若干行小字。"""
    s.rect(x, y, w, h, fill=T.PANEL, stroke=color, rx=8)
    s.text(x + 20, y + 30, title, size=13, weight="700",
           fill=title_color or color)
    for i, ln in enumerate(lines):
        s.text(x + 20, y + 56 + i * lh, ln, size=size, fill=T.TEXT)


def _code_panel(s: Svg, x, y, w, h, lines, size=12.5, lh=21.5,
                color=T.GREEN) -> None:
    s.rect(x, y, w, h, fill=T.PANEL, stroke=T.STROKE, rx=8)
    s.code(x + 20, y + 34, lines, size=size, lh=lh, color=color)


# ----------------------------------------------------------------------
# s08 开漏：只会拉低，高电平靠外部上拉
# ----------------------------------------------------------------------

def open_drain() -> Svg:
    s = Svg(W, H, "开漏输出：只主动拉低，高电平靠外部上拉",
            "写 0 时 NMOS 把总线拉到低；写 1 时输出级进入高阻，电平由外部上拉决定")
    s.header(tag="ch03-s08 · 开漏机制", tag_color=T.CYAN)

    panels = [
        ("写 0：NMOS 导通，主动拉低", 24, T.GREEN, True),
        ("写 1：NMOS 截止，输出级高阻", 492, T.AMBER, False),
    ]
    for title, px, color, closed in panels:
        s.rect(px, 84, 444, 320, fill=T.PANEL, stroke=color, rx=8)
        s.text(px + 222, 116, title, size=15, anchor="middle", weight="700")
        s.rect(px + 306, 96, 108, 30, fill=T.BG2, stroke=T.STROKE, rx=4)
        s.text(px + 360, 115, "ODR 写 0" if closed else "ODR 写 1",
               size=11, anchor="middle", mono=True, fill=T.MUTED)

        bus_y = 196
        s.line(px + 24, bus_y, px + 420, bus_y, stroke=T.CYAN, sw=2)
        s.text(px + 28, bus_y - 12, "总线（如 SDA）", size=11, fill=T.CYAN)

        # 总线上挂的其他开漏设备
        s.line(px + 360, bus_y, px + 360, bus_y + 8, stroke=T.STROKE, sw=1.5)
        s.rect(px + 306, bus_y + 8, 108, 26, fill=T.BG2, stroke=T.STROKE, rx=4)
        s.text(px + 360, bus_y + 26, "其他开漏设备", size=10, anchor="middle",
               fill=T.MUTED)

        # 外部上拉：3.3 V → Rp → 总线
        s.rect(px + 48, 122, 64, 26, fill=T.PANEL2, stroke=T.STROKE, rx=4)
        s.text(px + 80, 140, "3.3 V", size=11, anchor="middle", mono=True)
        s.line(px + 80, 148, px + 80, 158, stroke=T.STROKE, sw=1.5)
        s.rect(px + 62, 158, 36, 26, fill=T.BG, stroke=T.STROKE, rx=4)
        s.text(px + 80, 176, "Rp", size=11, anchor="middle", mono=True,
               fill=T.VIOLET, weight="700")
        s.line(px + 80, 184, px + 80, bus_y, stroke=T.STROKE, sw=1.5)
        s.text(px + 122, 172, "外部上拉", size=10, fill=T.MUTED)

        # NMOS 开关支路：总线 → NMOS → GND
        mx = px + 190
        s.line(mx, bus_y, mx, 244, stroke=T.STROKE, sw=1.5)
        s.circle(mx, 248, 3.5, fill=T.TEXT)
        if closed:
            s.line(mx, 248, mx, 284, stroke=T.GREEN, sw=2)
        else:
            s.line(mx, 248, mx + 26, 268, stroke=T.AMBER, sw=2)
        s.circle(mx, 288, 3.5, fill=T.TEXT)
        s.line(mx, 288, mx, 318, stroke=T.STROKE, sw=1.5)
        _ground(s, mx, 318)
        s.text(mx + 36, 254, "NMOS", size=11, mono=True, fill=T.MUTED)
        if closed:
            s.text(mx + 36, 276, "导通", size=12, fill=T.GREEN, weight="700")
            s.rect(px + 28, 288, 150, 42, fill=T.PANEL2, stroke=T.GREEN, rx=4)
            s.text(px + 103, 315, "总线 = 低 0", size=13, anchor="middle",
                   weight="700", fill=T.GREEN, mono=True)
            s.text(px + 28, 364, "电流：3.3 V → Rp → NMOS → GND", size=11,
                   fill=T.MUTED)
            s.text(px + 28, 386, "低电平是主动拉出来的", size=11, fill=T.MUTED)
        else:
            s.text(mx + 36, 254, "截止", size=12, fill=T.AMBER, weight="700")
            s.text(mx + 36, 300, "输出级 = 高阻（Hi-Z）", size=13,
                   fill=T.AMBER, weight="700")
            s.text(mx + 36, 322, "引脚对地近似断开", size=10.5, fill=T.MUTED)
            s.rect(px + 28, 288, 190, 42, fill=T.PANEL2, stroke=T.CYAN, rx=4)
            s.text(px + 123, 315, "总线 = 高 1（上拉供给）", size=12.5,
                   anchor="middle", weight="700", fill=T.CYAN)
            s.text(px + 28, 364, "NMOS 无电流入地，Rp 把线拉回 3.3 V",
                   size=11, fill=T.MUTED)
            s.text(px + 28, 386, "高电平是外部上拉给的", size=11, fill=T.MUTED)

    _note_box(s, 24, 424, 444, 160, "共享总线为什么用开漏（I2C）", [
        "· 任一设备写 0 都能把线拉低 —— 线与",
        "· 全部写 1 时总线高阻，Rp 把线送回高电平",
        "· 没有推挽输出高 / 低对顶烧驱动的风险",
    ], T.CYAN)
    _note_box(s, 492, 424, 444, 160, "把开漏当推挽用：常见现象", [
        "· 高电平出不来，或只能靠上拉慢慢爬升",
        "· 上升沿拖尾，高速信号直接变形",
        "· 要驱动 LED、时钟线，请改用推挽输出",
    ], T.RED)
    s.footer("机制依据 RM0008 GPIO 输出级；上拉取值与速度见 I2C 章节",
             label=FOOTER_LABEL)
    return s


# ----------------------------------------------------------------------
# s11 五类基础寄存器：CRL+CRH 是一类
# ----------------------------------------------------------------------

def register_map() -> Svg:
    s = Svg(W, H, "GPIO 寄存器地图：6 个名字，5 类角色",
            "CRL+CRH 同属配置类；IDR 读回、ODR 输出、BSRR/BRR 原子改位（F1）")
    s.header(tag="ch03-s11 · 寄存器地图", tag_color=T.VIOLET)

    regs = [
        ("CRL",  "0x00", "配置引脚 0–7（MODE/CNF）",   "① 配置类", T.VIOLET,
         ["决定输入 / 输出、上下拉、复用", "CRL+CRH 是同一类配置"]),
        ("CRH",  "0x04", "配置引脚 8–15（MODE/CNF）",  "① 配置类", T.VIOLET,
         ["决定输入 / 输出、上下拉、复用", "CRL+CRH 是同一类配置"]),
        ("IDR",  "0x08", "只读：引脚上的真实输入电平", "② 读回",   T.CYAN,
         ["按键、外部信号都靠它读回"]),
        ("ODR",  "0x0C", "读写：输出电平",             "③ 输出",   T.AMBER,
         ["写它改电平；|= 是读改写"]),
        ("BSRR", "0x10", "写 1 原子：低 16 位置位 / 高 16 位复位",
         "④ 原子改位", T.GREEN, ["单指令置位 / 复位，不碰别的位"]),
        ("BRR",  "0x14", "写 1 复位（F1 专有）",        "⑤ 复位",   T.BLUE,
         ["F4 没有 BRR，并入 BSRR 高 16 位"]),
    ]
    for i, (name, off, role, cls, color, desc) in enumerate(regs):
        y = 100 + i * 80
        s.rect(40, y, 380, 54, fill=T.PANEL, stroke=T.STROKE, rx=4)
        s.rect(40, y, 5, 54, fill=color)
        s.text(60, y + 24, name, size=16, mono=True, weight="700", fill=T.TEXT)
        s.text(404, y + 24, off, size=10.5, mono=True, anchor="end",
               fill=T.MUTED)
        s.text(60, y + 44, role, size=10.5, fill=T.MUTED)
        s.line(420, y + 27, 462, y + 27, stroke=T.STROKE, sw=1.5)
        if i < 2:
            continue  # 配置类画跨两行的大框
        s.rect(462, y, 170, 54, fill=T.PANEL2, stroke=color, rx=4)
        s.text(547, y + 33, cls, size=13, anchor="middle", weight="700",
               fill=color)
        for j, d in enumerate(desc):
            s.text(660, y + 22 + j * 20, d, size=11, fill=T.MUTED)

    # 配置类：跨 CRL+CRH 两行的大框，明确「同一类」
    s.rect(462, 100, 170, 134, fill=T.PANEL2, stroke=T.VIOLET, rx=4)
    s.text(547, 140, "① 配置类", size=13, anchor="middle", weight="700",
           fill=T.VIOLET)
    s.text(547, 166, "CRL+CRH", size=12, anchor="middle", mono=True,
           fill=T.VIOLET)
    s.text(547, 190, "是同一类", size=12, anchor="middle", weight="700",
           fill=T.VIOLET)
    for j, d in enumerate(["MODE/CNF 决定模式", "输入 / 输出 / 上下拉 / 复用",
                           "一个口 16 脚，两半分管"]):
        s.text(660, 122 + j * 20, d, size=11, fill=T.MUTED)

    s.rect(40, 566, 896, 44, fill=T.BG2, stroke=T.STROKE, rx=4)
    s.text(60, 593, "只改一个脚、不碰别人：BSRR 写 1 置位 / 复位最直接（F1 另有 BRR 专门复位）；"
                    "ODR 读改写不是唯一办法。",
           size=12, fill=T.TEXT)
    s.footer("偏移与功能依据 RM0008 第 9 章 GPIO 寄存器", label=FOOTER_LABEL)
    return s


# ----------------------------------------------------------------------
# s12 初始化顺序：先开时钟，再配引脚
# ----------------------------------------------------------------------

def init_code() -> Svg:
    s = Svg(W, H, "初始化：先开时钟，再配引脚",
            "外设时钟没开时，写进配置寄存器的值到不了硬件")
    s.header(tag="ch03-s12 · 初始化顺序", tag_color=T.GREEN)

    _code_panel(s, 24, 84, 604, 400, [
        "①  __HAL_RCC_GPIOC_CLK_ENABLE();  /* 先开 GPIOC 时钟 */",
        "   __HAL_RCC_GPIOA_CLK_ENABLE();  /* 用到哪个口开哪个 */",
        "",
        "②  GPIO_InitTypeDef gpio = {0};",
        "   gpio.Pin   = GPIO_PIN_13;",
        "   gpio.Mode  = GPIO_MODE_OUTPUT_PP;",
        "   gpio.Pull  = GPIO_NOPULL;",
        "   gpio.Speed = GPIO_SPEED_FREQ_LOW;",
        "",
        "③  HAL_GPIO_Init(GPIOC, &gpio);   /* 写进 CRL/CRH */",
        "",
        "④  while (1) {",
        "       HAL_GPIO_TogglePin(GPIOC, GPIO_PIN_13);",
        "       HAL_Delay(500);             /* 500 ms -> 1 Hz */",
        "   }",
    ], size=12.5, lh=24)

    steps = [
        ("① 开时钟", "RCC → GPIOC / GPIOA", T.GREEN),
        ("② 配引脚", "Pin/Mode/Pull/Speed → CRL/CRH", T.CYAN),
        ("③ 读写电平", "主循环 BSRR / ODR / IDR", T.VIOLET),
    ]
    for i, (label, sub, color) in enumerate(steps):
        y = 92 + i * 104
        s.box(656, y, 280, 80, label, sub, fill=T.PANEL2, stroke=color,
              color=color, size=14)
        if i < 2:
            s.arrow(796, y + 80, 796, y + 104, color=T.STROKE, sw=2, head=6)

    s.rect(656, 404, 280, 80, fill=T.PANEL, stroke=T.RED, rx=8)
    s.text(676, 432, "最常见坑", size=12.5, weight="700", fill=T.RED)
    s.text(676, 454, "时钟没开：配置写进去了，", size=10.5, fill=T.TEXT)
    s.text(676, 474, "硬件却收不到（总线无钟）。", size=10.5, fill=T.TEXT)

    s.rect(24, 508, 912, 64, fill=T.BG2, stroke=T.STROKE, rx=4)
    s.text(48, 536, "读代码的顺序：① 先找时钟使能  ② 再看 HAL_GPIO_Init 的参数  "
                    "③ 最后看主循环怎么写电平。",
           size=12.5, fill=T.TEXT)
    s.text(48, 558, "例程结构见 project-examples。", size=11, fill=T.MUTED)
    s.footer("时钟树见第 02 章；GPIO 寄存器见 RM0008 第 9 章",
             label=FOOTER_LABEL)
    return s


# ----------------------------------------------------------------------
# s13 HAL、BSRR、ODR：原子边界不同
# ----------------------------------------------------------------------

def write_methods() -> Svg:
    s = Svg(W, H, "三种写法，一条边界",
            "HAL 与 BSRR 同为原子写位；只有 ODR 读改写存在竞争窗口")
    s.header(tag="ch03-s13 · 写位路径", tag_color=T.GREEN)

    cols = [
        ("A · HAL 库", T.GREEN,
         ["HAL_GPIO_WritePin(GPIOC,", "    GPIO_PIN_13, GPIO_PIN_SET);"],
         "展开成：GPIOC->BSRR = BS13", "一次 32 位写 · 原子 ✓", T.GREEN),
        ("B · 直接写 BSRR", T.GREEN,
         ["GPIOC->BSRR =", "    GPIO_BSRR_BS13;"],
         "低 16 位写 1 = 置位", "一次 32 位写 · 原子 ✓", T.GREEN),
        ("C · ODR 读改写", T.RED,
         ["GPIOC->ODR ^=", "    GPIO_PIN_13;"],
         "读 → 改 → 写，三条指令", "中间可被插队 · 竞争 ⚠", T.RED),
    ]
    for i, (title, color, code, mid, verdict, vcolor) in enumerate(cols):
        x = 24 + i * 312
        s.rect(x, 84, 300, 46, fill=T.PANEL2, stroke=color, rx=8)
        s.text(x + 150, 114, title, size=14, anchor="middle", weight="700",
               fill=color)
        s.rect(x, 130, 300, 204, fill=T.PANEL, stroke=T.STROKE, rx=8)
        for j, ln in enumerate(code):
            s.text(x + 16, 162 + j * 21, ln, size=11, mono=True, fill=T.GREEN)
        s.arrow(x + 150, 208, x + 150, 230, color=T.STROKE, sw=1.5, head=5)
        s.text(x + 150, 254, mid, size=11, anchor="middle", mono=True,
               fill=T.BLUE)
        s.rect(x + 16, 272, 268, 46, fill=T.BG, stroke=vcolor, rx=4)
        s.text(x + 150, 301, verdict, size=12.5, anchor="middle", weight="700",
               fill=vcolor)

    # ODR 读改写的竞争现场
    s.rect(24, 358, 912, 190, fill=T.PANEL, stroke=T.STROKE, rx=8)
    s.text(48, 388, "ODR 读改写的丢位现场（主流程 vs 中断）", size=13,
           weight="700")
    s.text(40, 437, "主流程", size=11, fill=T.MUTED)
    s.rect(110, 412, 170, 36, fill=T.BG2, stroke=T.STROKE, rx=4)
    s.text(195, 435, "① 读 ODR（旧值）", size=11, anchor="middle")
    s.arrow(280, 430, 320, 430, color=T.STROKE, sw=1.5, head=5)
    s.rect(320, 412, 160, 36, fill=T.BG2, stroke=T.STROKE, rx=4)
    s.text(400, 435, "② 改：^= bit13", size=11, anchor="middle", mono=True)
    s.arrow(480, 430, 520, 430, color=T.STROKE, sw=1.5, head=5)
    s.rect(520, 412, 190, 36, fill=T.BG2, stroke=T.RED, rx=4)
    s.text(615, 435, "③ 写回 ODR（旧值）", size=11, anchor="middle")
    s.text(730, 435, "ISR 改的位被覆盖丢失", size=12.5, fill=T.RED,
           weight="700")
    s.text(40, 506, "中断", size=11, fill=T.MUTED)
    s.rect(350, 482, 230, 36, fill=T.BG, stroke=T.RED, rx=4, dash="5 4")
    s.text(465, 505, "ISR：BSRR 置位 bit5", size=11, anchor="middle",
           fill=T.RED, mono=True)
    s.arrow(465, 482, 465, 452, color=T.RED, sw=1.5, head=5, dash="5 4")

    s.text(48, 572, "HAL 的价值是封装与可读性，不是把非原子变成原子；"
                    "比较写法要看实际寄存器路径，不比函数长短。",
           size=12, fill=T.TEXT)
    s.footer("依据 RM0008：BSRR/BRR 写 1 生效、单指令完成；ODR 读改写需三条指令",
             label=FOOTER_LABEL)
    return s


# ----------------------------------------------------------------------
# s15 位带：ODR bit13 的别名入口
# ----------------------------------------------------------------------

def bitband() -> Svg:
    s = Svg(W, H, "位带：ODR 的另一个写位入口",
            "外设位带区 0x42000000 起：把寄存器的一位映射成一个别名地址")
    s.header(tag="ch03-s15 · 位带别名", tag_color=T.AMBER)

    s.text(40, 112, "GPIOC->ODR @ 0x4001100C", size=14, mono=True,
           weight="700")
    for i in range(16):
        bit = 15 - i
        x = 40 + i * 36
        hi = (bit == 13)
        s.rect(x, 130, 36, 46, fill=T.AMBER if hi else T.PANEL,
               stroke=T.STROKE, rx=4)
        s.text(x + 18, 124, str(bit), size=9, anchor="middle", fill=T.MUTED,
               mono=True)
        if hi:
            s.text(x + 18, 158, "13", size=15, anchor="middle", weight="700",
                   fill="#ffffff", mono=True)
    s.text(166, 200, "▲ 目标位 bit13", size=11, anchor="middle", fill=T.AMBER,
           weight="700")
    s.arrow(166, 208, 166, 238, color=T.AMBER, sw=2, head=6)

    s.rect(40, 244, 880, 104, fill=T.PANEL, stroke=T.STROKE, rx=8)
    s.text(64, 276, "别名地址 = 0x42000000 +（寄存器地址 − 0x40000000）× 32 + 位号 × 4",
           size=13, weight="700")
    s.text(64, 304, "= 0x42000000 + (0x4001100C - 0x40000000) * 32 + 13 * 4",
           size=13, mono=True, fill=T.BLUE)
    s.text(64, 332, "= 0x422201B4 （写这个别名地址 = 直接改 ODR bit13，无需读改写）",
           size=13, mono=True, weight="700", fill=T.GREEN)

    s.rect(40, 376, 440, 140, fill=T.PANEL, stroke=T.STROKE, rx=8)
    s.text(64, 408, "代码里的样子", size=12.5, weight="700")
    s.code(64, 434, [
        "#define PC13_OUT  BITBAND_PERIPH(0x4001100CUL, 13)",
        "PC13_OUT = 0;   /* PC13 输出低 -> 灯亮 */",
        "PC13_OUT = 1;   /* PC13 输出高 -> 灯灭 */",
    ], size=11.5, lh=24)

    _note_box(s, 504, 376, 456, 140, "别被长地址吓到", [
        "· 先确认原寄存器（GPIOC ODR）和位号（13）",
        "· 别名只是入口：时钟、模式仍归 RCC 与 CRH 管",
        "· 边界与 ODR 相同；位带不是第二套 GPIO",
    ], T.AMBER)
    s.footer("公式与外设位带区（0x42000000）见 Cortex-M3 / RM0008 位带说明",
             label=FOOTER_LABEL)
    return s


# ----------------------------------------------------------------------
# s17 重映射：F1 先开 AFIO，F4 用 AFR
# ----------------------------------------------------------------------

def remap() -> Svg:
    s = Svg(W, H, "F1 重映射：AFIO 时钟 → MAPR → 新引脚",
            "F4 改成每个引脚自己的 AFR 字段；换系列先换手册")
    s.header(tag="ch03-s17 · 重映射", tag_color=T.VIOLET)

    s.rect(24, 84, 444, 340, fill=T.PANEL, stroke=T.VIOLET, rx=8)
    s.text(246, 116, "F1（RM0008）：例 USART1 → PB6/PB7", size=14,
           anchor="middle", weight="700", fill=T.VIOLET)
    f1 = [
        ("① 开 AFIO 时钟", "__HAL_RCC_AFIO_CLK_ENABLE()"),
        ("② 写 AFIO->MAPR 重映射位", "USART1_REMAP = 1"),
        ("③ 信号从新脚 PB6/PB7 出", "示波器在新脚上能看到波形"),
    ]
    for i, (label, sub) in enumerate(f1):
        y = 140 + i * 74
        s.box(64, y, 364, 56, label, sub, fill=T.PANEL2, stroke=T.VIOLET,
              color=T.TEXT, size=13)
        if i < 2:
            s.arrow(246, y + 56, 246, y + 74, color=T.STROKE, sw=2, head=6)
    s.rect(64, 362, 364, 48, fill=T.BG, stroke=T.RED, rx=4)
    s.text(246, 382, "不开 AFIO 时钟：MAPR 写不进，", size=11, anchor="middle",
           fill=T.RED)
    s.text(246, 400, "新脚一直安静。", size=11, anchor="middle", fill=T.RED)

    s.rect(492, 84, 444, 340, fill=T.PANEL, stroke=T.CYAN, rx=8)
    s.text(714, 116, "F4：每脚自选 AF 号", size=14, anchor="middle",
           weight="700", fill=T.CYAN)
    f4 = [
        ("GPIOx_AFRL / AFRH", "每个引脚 4 bit 字段选 AF0–AF15"),
        ("例：PA9 的 AFRH[7:4] = AF7", "→ USART1_TX"),
        ("无需 AFIO 时钟", "F4 没有 MAPR；规则在 F4 手册"),
    ]
    for i, (label, sub) in enumerate(f4):
        y = 140 + i * 74
        s.box(532, y, 364, 56, label, sub, fill=T.PANEL2, stroke=T.CYAN,
              color=T.TEXT, size=13)
        if i < 2:
            s.arrow(714, y + 56, 714, y + 74, color=T.STROKE, sw=2, head=6)
    s.rect(532, 362, 364, 48, fill=T.BG, stroke=T.AMBER, rx=4)
    s.text(714, 391, "别把 F1 的顺序原样搬到 F4。", size=11, anchor="middle",
           fill=T.AMBER)

    s.rect(24, 448, 912, 120, fill=T.BG2, stroke=T.STROKE, rx=8)
    s.text(48, 482, "对照记忆", size=13, weight="700")
    s.text(48, 510, "F1：AFIO 时钟先行 → 写 MAPR → 再配 GPIO 模式；顺序反了，信号到不了新脚。",
           size=12, fill=T.TEXT)
    s.text(48, 538, "F4：没有 MAPR，查每脚 AFR 字段和 AF 编号表；换系列先换手册。",
           size=12, fill=T.TEXT)
    s.footer("F1 依据 RM0008 AFIO 章节；F4 的 AFR 规则见对应型号参考手册",
             label=FOOTER_LABEL)
    return s


# ----------------------------------------------------------------------
# s18 5 V 容忍：查 DS5319 的 FT 与注入电流
# ----------------------------------------------------------------------

def ft_evidence() -> Svg:
    s = Svg(W, H, "5 V 能不能接：先查 DS5319，不看运气",
            "引脚表的 FT 标识与注入电流条件说了算；点亮一次不是耐压证据")
    s.header(tag="ch03-s18 · 5 V 边界", tag_color=T.RED)

    s.box(40, 150, 170, 90, "5 V 模块", "传感器 / 模块信号", fill=T.PANEL2,
          stroke=T.STROKE, size=14)
    s.text(125, 266, "别问「别人板子上能亮」", size=10.5, anchor="middle",
           fill=T.MUTED)
    s.arrow(210, 195, 270, 195, color=T.STROKE, sw=2, head=7)

    s.rect(270, 140, 260, 110, fill=T.PANEL, stroke=T.AMBER, rx=8)
    s.text(400, 178, "① 查 DS5319 引脚表", size=14, anchor="middle",
           weight="700", fill=T.AMBER)
    s.text(400, 206, "这只脚标了 FT 吗？", size=13, anchor="middle")
    s.text(400, 230, "（不是「STM32 都耐 5 V」）", size=10.5, anchor="middle",
           fill=T.MUTED)

    s.arrow(530, 180, 600, 150, color=T.AMBER, sw=2, head=6)
    s.text(565, 150, "标了 FT", size=11, anchor="middle", fill=T.AMBER,
           weight="700")
    s.arrow(530, 210, 600, 310, color=T.RED, sw=2, head=6)
    s.text(565, 300, "没标 FT", size=11, anchor="middle", fill=T.RED,
           weight="700")

    _note_box(s, 600, 96, 336, 122, "FT：5 V 容忍，但有条件", [
        "· 注入电流 I_INJ 必须在手册范围内",
        "· VDD 上下电状态另有注入限制",
        "· 核对表 5 的条件后再接",
    ], T.AMBER, size=11, lh=21)
    _note_box(s, 600, 264, 336, 122, "普通脚：不要硬接 5 V", [
        "· 普通脚 Vin 不得超过手册允许范围",
        "· 轻则电平错误，重则打伤芯片",
        "· 先电平转换或分压，再进引脚",
    ], T.RED, size=11, lh=21)

    s.rect(40, 424, 896, 150, fill=T.PANEL, stroke=T.RED, rx=8)
    s.text(64, 456, "为什么「能亮一次」不算证据", size=13, weight="700",
           fill=T.RED)
    s.text(64, 484, "· 绝对最大额定值是长期边界，一次实验验证不了；",
           size=12, fill=T.TEXT)
    s.text(64, 508, "· 注入电流超限的损伤会累积，当时示波器看不出来；",
           size=12, fill=T.TEXT)
    s.text(64, 532, "· 电气边界只回到 DS5319 表 5（绝对最大额定值）与引脚表的 FT 列。",
           size=12, fill=T.TEXT)
    s.footer("条件摘自 DS5319 表 5；以手头芯片对应版本的最新手册为准",
             label=FOOTER_LABEL)
    return s


# ----------------------------------------------------------------------
# s23 按键抖动：波形、采样点、经验值
# ----------------------------------------------------------------------

def debounce() -> Svg:
    s = Svg(W, H, "按键抖动：先量波形，再谈消抖",
            "抖动期内样本拒绝，稳定后多次一致才接受；10–20 ms 只是经验范围")
    s.header(tag="ch03-s23 · 抖动与消抖", tag_color=T.AMBER)

    def tx(t: float) -> float:
        return 90 + t * 7.9

    hi, lo = 140.0, 260.0

    # 原始波形
    s.rect(24, 84, 912, 250, fill=T.PANEL, stroke=T.STROKE, rx=8)
    s.text(48, 112, "原始波形（按键接 PA1，上拉，按下为低）", size=12.5,
           weight="700")
    s.text(40, 146, "3.3V", size=10, mono=True, fill=T.MUTED)
    s.text(40, 266, "0V", size=10, mono=True, fill=T.MUTED)
    for t0, t1, lab in ((6, 14, "抖动：触点弹跳"), (60, 68, "释放抖动")):
        s.rect(tx(t0), 118, tx(t1) - tx(t0), 160, fill=T.RED, opacity=0.07,
               stroke=T.RED, dash="4 3", sw=1)
        s.text(tx((t0 + t1) / 2), 108, lab, size=11, anchor="middle",
               fill=T.RED, weight="700")
        s.text(tx((t0 + t1) / 2), 306, "≈8 ms", size=10, anchor="middle",
               fill=T.MUTED, mono=True)
    # 电平序列：(时刻, 跳变后的电平)
    seq = [(0, hi), (6, lo), (8, hi), (10, lo), (12, hi), (14, lo),
           (60, hi), (62, lo), (64, hi), (66, lo), (68, hi), (100, hi)]
    pts = [(tx(seq[0][0]), seq[0][1])]
    for t, lvl in seq[1:]:
        pts.append((tx(t), pts[-1][1]))   # 水平
        pts.append((tx(t), lvl))          # 垂直跳变
    s.path("M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in pts),
           stroke=T.CYAN, sw=2)
    s.text(tx(37), 282, "按下（稳定低）", size=11, anchor="middle",
           fill=T.MUTED)
    s.text(tx(88), 132, "空闲（稳定高）", size=11, anchor="middle",
           fill=T.MUTED)
    s.line(90, 288, tx(100), 288, stroke=T.GRID, sw=1)
    s.text(tx(100), 306, "t / ms", size=10, anchor="end", fill=T.MUTED,
           mono=True)

    # 采样点
    s.rect(24, 350, 912, 110, fill=T.PANEL, stroke=T.STROKE, rx=8)
    s.text(48, 378, "采样点：抖动期内拒绝（×），稳定后多次一致才接受（✓）",
           size=12.5, weight="700")
    for t in range(4, 100, 4):
        x = tx(t)
        if t in (8, 12, 64):
            s.circle(x, 414, 7, fill=T.BG, stroke=T.RED, sw=1.5)
            s.text(x, 418, "×", size=10, anchor="middle", fill=T.RED,
                   weight="700")
        elif t in (20, 24, 28):
            s.circle(x, 414, 7, fill=T.BG, stroke=T.GREEN, sw=1.5)
            s.text(x, 418, "✓", size=10, anchor="middle", fill=T.GREEN,
                   weight="700")
        else:
            s.circle(x, 414, 3, fill=T.STROKE, opacity=0.5)
    s.text(tx(10), 444, "× 拒绝", size=11, anchor="middle", fill=T.RED,
           weight="700")
    s.text(tx(24), 444, "✓ 连续一致 → 接受", size=11, anchor="middle",
           fill=T.GREEN, weight="700")
    s.text(tx(100), 444, "t / ms", size=10, anchor="end", fill=T.MUTED,
           mono=True)

    _note_box(s, 24, 480, 448, 92, "延时确认", [
        "读到低 → 延时 → 再读仍低，才算按下；",
        "延时值按实测抖动宽度取，不抄别人的。",
    ], T.CYAN, size=11, lh=22)
    _note_box(s, 488, 480, 448, 92, "周期采样", [
        "定时器周期读键，连续 N 次一致才更新状态；",
        "与第 04 章 EXTI 边沿触发形成对照。",
    ], T.VIOLET, size=11, lh=22)
    s.footer("10–20 ms 是经验范围，RM0008 / DS5319 均未规定；先量实际波形，再选消抖参数",
             label=FOOTER_LABEL)
    return s


# ----------------------------------------------------------------------
# s24 轮询边界：100 ms 阻塞 vs 短按
# ----------------------------------------------------------------------

def polling() -> Svg:
    s = Svg(W, H, "主循环阻塞 100 ms：短按被漏检",
            "轮询两次之间按完的脉冲，主循环根本看不见")
    s.header(tag="ch03-s24 · 轮询边界", tag_color=T.RED)

    def tx(t: float) -> float:
        return 90 + t * 2.05

    s.rect(24, 84, 912, 340, fill=T.PANEL, stroke=T.STROKE, rx=8)

    # 上：含 100 ms 阻塞的主循环
    s.text(44, 120, "含 100 ms 阻塞任务的主循环", size=12.5, weight="700")
    s.line(90, 170, 910, 170, stroke=T.STROKE, sw=1.5)
    for t in (0, 100, 200, 300):
        s.rect(tx(t) + 6, 156, tx(t + 100) - tx(t) - 12, 28, fill=T.ORANGE,
               opacity=0.15, stroke=T.ORANGE, dash="4 3", sw=1)
    s.text(tx(50), 174, "阻塞任务 ~100 ms", size=10.5, anchor="middle",
           fill=T.ORANGE, weight="700")
    for t in (0, 100, 200, 300, 400):
        s.circle(tx(t), 170, 5, fill=T.GREEN)
    s.text(tx(0), 148, "读 IDR", size=10, fill=T.GREEN)
    # 短按脉冲（低 30 ms），落在两次轮询之间
    p0, p1 = tx(130), tx(160)
    s.path(f"M 90 196 L {p0:.1f} 196 L {p0:.1f} 224 L {p1:.1f} 224 "
           f"L {p1:.1f} 196 L 910 196", stroke=T.CYAN, sw=2)
    s.text(tx(145), 244, "按键短脉冲 ~30 ms", size=10.5, anchor="middle",
           fill=T.MUTED)
    s.circle(tx(145), 210, 13, fill=T.BG, stroke=T.RED, sw=2)
    s.text(tx(145), 215, "✗", size=13, anchor="middle", fill=T.RED,
           weight="700")
    s.text(tx(172), 204, "落在两次轮询之间按完 → 漏检", size=12.5, fill=T.RED,
           weight="700")
    s.line(24, 272, 936, 272, stroke=T.GRID, sw=1)

    # 下：对照，10 ms 快轮询
    s.text(44, 306, "对照：无阻塞、每 10 ms 轮询", size=12.5, weight="700")
    s.line(90, 330, 910, 330, stroke=T.STROKE, sw=1.5)
    for t in range(0, 401, 10):
        s.circle(tx(t), 330, 2.5, fill=T.GREEN, opacity=0.8)
    s.path(f"M 90 356 L {p0:.1f} 356 L {p0:.1f} 384 L {p1:.1f} 384 "
           f"L {p1:.1f} 356 L 910 356", stroke=T.CYAN, sw=2)
    s.circle(tx(145), 370, 13, fill=T.BG, stroke=T.GREEN, sw=2)
    s.text(tx(145), 375, "✓", size=13, anchor="middle", fill=T.GREEN,
           weight="700")
    s.text(tx(172), 364, "脉冲宽度内有采样点 → 检出", size=12.5, fill=T.GREEN,
           weight="700")
    s.text(910, 410, "t / ms（0–400）", size=10, anchor="end", fill=T.MUTED,
           mono=True)

    s.rect(24, 444, 912, 60, fill=T.BG2, stroke=T.STROKE, rx=4)
    s.text(48, 468, "轮询的边界：采样间隔长于脉冲宽度时，漏检是迟早的事 —— 不是按键坏了，是轮询的盲区。",
           size=12, fill=T.TEXT)
    s.text(48, 492, "实验：主循环加 100 ms 阻塞后短按 PA1，记录漏检与响应延迟；下一章交给 EXTI。",
           size=12, fill=T.TEXT)
    s.footer("对照实验见 docs/03 动手实验（实验三）", label=FOOTER_LABEL)
    return s


# ----------------------------------------------------------------------
# s25 实验一：PC13 1 Hz 三份证据对齐（无 PA5）
# ----------------------------------------------------------------------

def pc13_evidence() -> Svg:
    s = Svg(W, H, "实验一：1 Hz 要靠三份证据对齐",
            "代码、寄存器读回、时间轴测量指向同一个 1 s，才算对上")
    s.header(tag="ch03-s25 · 三证对齐", tag_color=T.GREEN)

    # ① 代码证据
    s.rect(24, 84, 300, 300, fill=T.PANEL, stroke=T.VIOLET, rx=8)
    s.text(174, 116, "① 代码：500 ms 翻转", size=13.5, anchor="middle",
           weight="700", fill=T.VIOLET)
    s.code(44, 152, [
        "HAL_GPIO_TogglePin(GPIOC,",
        "    GPIO_PIN_13);",
        "HAL_Delay(500);",
    ], size=11, lh=22)
    s.rect(44, 240, 260, 44, fill=T.BG, stroke=T.VIOLET, rx=4)
    s.text(174, 267, "预期周期 = 2 × 500 ms", size=12, anchor="middle",
           weight="700", fill=T.VIOLET)
    s.text(44, 322, "延时或定时器先算出 500 ms，", size=11, fill=T.MUTED)
    s.text(44, 344, "理论周期 1000 ms。", size=11, fill=T.MUTED)

    # ② 读回证据
    s.rect(348, 84, 300, 300, fill=T.PANEL, stroke=T.CYAN, rx=8)
    s.text(498, 116, "② 读回：PC13 ODR 交替", size=13.5, anchor="middle",
           weight="700", fill=T.CYAN)
    rows = [("t = 0.0 s", "ODR13 = 1", False, "灯灭"),
            ("t = 0.5 s", "ODR13 = 0", True, "灯亮"),
            ("t = 1.0 s", "ODR13 = 1", False, "灯灭")]
    for i, (ts, vs, lit, ls) in enumerate(rows):
        y = 152 + i * 42
        s.text(368, y, ts, size=11.5, mono=True, fill=T.TEXT)
        s.text(478, y, vs, size=11, mono=True, fill=T.BLUE)
        s.circle(596, y - 4, 8, fill=T.RED if lit else T.BG,
                 stroke=T.STROKE, sw=1.5)
        s.text(612, y, ls, size=11, fill=T.MUTED)
    s.rect(368, 288, 260, 44, fill=T.BG, stroke=T.CYAN, rx=4)
    s.text(498, 315, "读回：1 → 0 → 1，节奏一致", size=12, anchor="middle",
           weight="700", fill=T.CYAN)
    s.text(368, 364, "调试器 / 日志读 PC13 ODR。", size=11, fill=T.MUTED)

    # ③ 时间轴证据
    s.rect(672, 84, 288, 300, fill=T.PANEL, stroke=T.GREEN, rx=8)
    s.text(816, 116, "③ 时间轴：量周期", size=13.5, anchor="middle",
           weight="700", fill=T.GREEN)
    s.path("M 700 160 L 760 160 L 760 210 L 820 210 L 820 160 "
           "L 880 160 L 880 210 L 932 210", stroke=T.CYAN, sw=2)
    s.double_arrow(760, 244, 880, 244, color=T.GREEN, sw=1.5)
    s.text(820, 236, "T = 1.000 s", size=11.5, anchor="middle", mono=True,
           weight="700", fill=T.GREEN)
    s.text(700, 292, "示波器 / 逻辑分析仪量周期；", size=11, fill=T.TEXT)
    s.text(700, 316, "仿真时间轴也可以，但要注明", size=11, fill=T.AMBER)
    s.text(700, 340, "「仿真证据，非实测」。", size=11, fill=T.AMBER)

    for cx in (174, 498, 816):
        s.arrow(cx, 384, cx, 402, color=T.STROKE, sw=1.5, head=5)

    s.rect(24, 410, 912, 134, fill=T.PANEL, stroke=T.GREEN, rx=8)
    s.text(48, 442, "对齐判决：三份证据指向同一个 1 s ✓", size=13.5,
           weight="700", fill=T.GREEN)
    s.text(48, 470, "· 代码说 1000 ms，PC13 ODR 读回高低交替，时间轴量到 1.000 s：代码 — 寄存器 — 电平连起来了。",
           size=11.5, fill=T.TEXT)
    s.text(48, 494, "· 只凭眼睛看灯闪不算数：900 ms 和 1100 ms 肉眼分不出。",
           size=11.5, fill=T.TEXT)
    s.text(48, 518, "· 没有仪器时：明确标注哪些是仿真证据，不要把仿真当实测。",
           size=11.5, fill=T.TEXT)
    s.footer("PC13 共阳低电平点亮；读回走调试器或日志（project-examples）",
             label=FOOTER_LABEL)
    return s


# ----------------------------------------------------------------------
# s26 实验二接线：PA0 串 270 Ω 点灯，PA1 上拉按键
# ----------------------------------------------------------------------

def pa0_pa1_wiring() -> Svg:
    s = Svg(W, H, "实验二接线：PA0 串 270 Ω 点灯，PA1 上拉按键",
            "接线、读回、现象形成闭环；换 EXTI 实验前先拆外接灯")
    s.header(tag="ch03-s26 · 实验二接线", tag_color=T.CYAN)

    # 左：接线图
    s.rect(24, 84, 560, 440, fill=T.PANEL, stroke=T.STROKE, rx=8)
    s.rect(60, 180, 150, 240, fill=T.PANEL2, stroke=T.STROKE, rx=8)
    s.text(135, 286, "STM32", size=14, anchor="middle", weight="700")
    s.text(135, 308, "F103C8T6", size=11, anchor="middle", mono=True,
           fill=T.MUTED)
    s.text(135, 340, "BluePill 核心板", size=10, anchor="middle",
           fill=T.MUTED)

    # PA0 → 270 Ω → LED → GND
    s.rect(204, 230, 12, 20, fill=T.BG, stroke=T.STROKE, rx=2)
    s.text(198, 245, "PA0", size=11, anchor="end", mono=True, weight="700")
    s.line(216, 240, 260, 240, stroke=T.STROKE, sw=1.5)
    s.text(238, 226, "推挽输出", size=10, anchor="middle", fill=T.MUTED)
    s.rect(260, 224, 80, 32, fill=T.BG, stroke=T.STROKE, rx=4)
    s.text(300, 245, "270 Ω", size=13, anchor="middle", mono=True,
           weight="700", fill=T.VIOLET)
    s.line(340, 240, 388, 240, stroke=T.STROKE, sw=1.5)
    s.poly([(388, 224), (388, 256), (416, 240)], stroke=T.TEXT, sw=2)
    s.line(416, 224, 416, 256, stroke=T.TEXT, sw=2)
    s.text(402, 214, "LED", size=10.5, anchor="middle", fill=T.MUTED)
    s.line(416, 240, 448, 240, stroke=T.STROKE, sw=1.5)
    _ground(s, 448, 240)
    s.text(330, 292, "共阴：写 1 灯亮，写 0 灯灭", size=11, anchor="middle",
           fill=T.GREEN, weight="700")

    # PA1 → 按键 → GND（内部上拉）
    s.rect(204, 330, 12, 20, fill=T.BG, stroke=T.STROKE, rx=2)
    s.text(198, 345, "PA1", size=11, anchor="end", mono=True, weight="700")
    s.line(216, 340, 258, 340, stroke=T.STROKE, sw=1.5)
    s.text(237, 326, "上拉输入", size=10, anchor="middle", fill=T.MUTED)
    s.circle(262, 340, 3, fill=T.TEXT)
    s.line(262, 340, 290, 320, stroke=T.TEXT, sw=2)
    s.circle(296, 340, 3, fill=T.TEXT)
    s.text(280, 310, "按键", size=10.5, anchor="middle", fill=T.MUTED)
    s.line(296, 340, 340, 340, stroke=T.STROKE, sw=1.5)
    _ground(s, 340, 340)
    s.text(300, 392, "按下：PA1 读到低 0", size=11, anchor="middle",
           fill=T.CYAN, weight="700")

    s.text(48, 470, "LED 共阴：阳极接电阻侧，阴极接地；按键另一端接地。",
           size=11, fill=T.MUTED)
    s.text(48, 492, "PA1 用内部上拉：空闲读 1，按下读 0（读 IDR）。",
           size=11, fill=T.MUTED)

    # 右：计算 / 记录 / 换实验
    s.rect(616, 84, 320, 150, fill=T.PANEL, stroke=T.GREEN, rx=8)
    s.text(636, 116, "限流电阻怎么算（例程估算）", size=12.5, weight="700",
           fill=T.GREEN)
    s.text(636, 146, "(3.3 − 2.0) V / 5 mA = 260 Ω", size=12, mono=True,
           fill=T.TEXT)
    s.text(636, 172, "→ 取标准值 270 Ω", size=12.5, mono=True, weight="700",
           fill=T.GREEN)
    s.text(636, 202, "2.0 V / 5 mA 是普通红灯估算，换灯要重算。", size=10.5,
           fill=T.MUTED)

    s.rect(616, 250, 320, 130, fill=T.PANEL, stroke=T.CYAN, rx=8)
    s.text(636, 282, "实验记录三件套", size=12.5, weight="700", fill=T.CYAN)
    s.text(636, 310, "□ 接线：引脚、阻值、LED 极性", size=11.5, fill=T.TEXT)
    s.text(636, 336, "□ 读回：IDR / ODR 的实际值", size=11.5, fill=T.TEXT)
    s.text(636, 362, "□ 现象：按键与灯的对照", size=11.5, fill=T.TEXT)

    s.rect(616, 396, 320, 128, fill=T.PANEL, stroke=T.RED, rx=8)
    s.text(636, 428, "换实验先拆线", size=12.5, weight="700", fill=T.RED)
    s.text(636, 456, "下一章 PA0 要做 EXTI0 输入；", size=11, fill=T.TEXT)
    s.text(636, 480, "先拆外接灯，再进中断实验，", size=11, fill=T.TEXT)
    s.text(636, 504, "别让一只脚同时挑两份担子。", size=11, fill=T.TEXT)

    s.footer("接法与 270 Ω 计算见 docs/03 硬件与接线；PA0 是 LQFP48 第 10 脚（DS5319）",
             label=FOOTER_LABEL)
    return s


# ----------------------------------------------------------------------
# 汇总输出
# ----------------------------------------------------------------------

ALL = [
    open_drain,
    register_map,
    init_code,
    write_methods,
    bitband,
    remap,
    ft_evidence,
    debounce,
    polling,
    pc13_evidence,
    pa0_pa1_wiring,
]

NAMES = {
    "open_drain": "classic-03-open-drain",
    "register_map": "classic-03-register-map",
    "init_code": "classic-03-init-code",
    "write_methods": "classic-03-write-methods",
    "bitband": "classic-03-bitband",
    "remap": "classic-03-remap",
    "ft_evidence": "classic-03-ft-evidence",
    "debounce": "classic-03-debounce",
    "polling": "classic-03-polling",
    "pc13_evidence": "classic-03-pc13-evidence",
    "pa0_pa1_wiring": "classic-03-pa0-pa1-wiring",
}

# 与 stm32-book/tests/test_classic_l1.py 冻结的标签一一对应
REQUIRED = {
    "classic-03-open-drain": ["高阻"],
    "classic-03-register-map": ["BSRR"],
    "classic-03-init-code": ["__HAL_RCC_GPIOC_CLK_ENABLE"],
    "classic-03-write-methods": ["HAL 与 BSRR"],
    "classic-03-bitband": ["0x4001100C"],
    "classic-03-remap": ["MAPR"],
    "classic-03-ft-evidence": ["注入电流"],
    "classic-03-debounce": ["抖动"],
    "classic-03-polling": ["漏检"],
    "classic-03-pc13-evidence": ["PC13 ODR"],
    "classic-03-pa0-pa1-wiring": ["270 Ω"],
}

FORBIDDEN = ["<script", "href", "url(", "filter", "animation"]


def main(argv):
    here = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(os.path.dirname(here), "assets", "diagrams")
    os.makedirs(out_dir, exist_ok=True)
    only = set(argv[1:])
    for fn in ALL:
        name = NAMES[fn.__name__]
        if only and name not in only:
            continue
        path = os.path.join(out_dir, name + ".svg")
        fn().save(path)
        xml.dom.minidom.parse(path)
        with open(path, encoding="utf-8") as f:
            text = f.read()
        for label in REQUIRED[name]:
            if label not in text:
                raise SystemExit(f"[fail] {name}.svg 缺少标签 {label!r}")
        for bad in FORBIDDEN:
            if bad in text:
                raise SystemExit(f"[fail] {name}.svg 含禁用内容 {bad!r}")
        print(f"[ok] {name}.svg ({len(text.encode('utf-8'))} bytes)")


if __name__ == "__main__":
    main(__import__("sys").argv)
