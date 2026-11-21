# -*- coding: utf-8 -*-
"""V2e hand-drawn plates: ch09 GPIO breaker-tables-command, ch12 counter
three knobs, ch13 COBS paper tape.

Facts pinned verbatim from the chapters. ch09: RCC 0x4002_3800, AHB1ENR
offset 0x30, GPIOF bit5; PF6 bits[13:12], clear 0x3000 then set 0x1000;
MODER=01 OTYPER=0 OSPEEDR=00 PUPDR=00; BSRR bit6 BS6 0x00000040 / bit22
BR6 0x00400000, write-only; ODR |= compiles to ldr/orr/str; common-anode
3.3V lights on low; MODER=10 pairs with AFR, PA9 AF7 USART1_TX; PA13/PA14
stay SWD; F103 CRL/CRH on APB2, AFIO MAPR remap. e01 hardware_status
pending. ch12: PSC=83 ARR=999 CCR=500, 84MHz/84=1MHz, 1MHz/1000=1kHz 1ms,
500/1000=50%; APB1=/4 PCLK1=42MHz, TIM3=42x2=84MHz (manual rule);
f=TIMclk/((PSC+1)(ARR+1)); OC1M=110 OC1PE=1 CC1E=1; input capture copies
CNT into CCR on edge, TIM2 32-bit free-run 1 count=1us, TIM3 measuring
itself reads delta 0. e03 pending. ch13: length-prefix / escape / COBS
recovery costs; raw<254 overhead fixed 1; INFO seq=7 raw 01 01 07 00 00
00 CC B0 -> wire 04 01 01 07 01 01 03 CC B0 00 (8+1+1=10); 6+64+2=72 ->
73 -> 74; CRC-16/CCITT-FALSE check 0x29B1; EMPTY/COLLECT/DISCARD, oversize
at 73, timeout 100ms; lost frame-tail swallows next frame, retry sends a
lone 0x00 first; ack-enqueue before execute. e02 pending.
No board measurements; layouts are schematic.

Deterministic: hd.Fig seeds its own RNG; re-running gives the same SVG.
"""
from __future__ import annotations

from functools import partial
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hd import (AMBER_PALE, AMBER_STROKE, BLUE_D, BLUE_FILL, GRAY_FILL,  # noqa: E402
                GREEN_D, GREEN_FILL, HAND, INK, MUTED, RED, RED_FILL,
                WHITE, Fig, save)

MONO = "'Consolas','Courier New',monospace"
STAGE = Path(__file__).resolve().parents[2] / "assets" / "illustrations" / "staged" / "l0-l5-pass" / "figures"


def knife_switch(f, cx, cy, color):
    """Open knife switch: two terminals, lever lifted off the right one."""
    f.circle(cx - 45, cy, 6, color=color, sw=2.0, fill=WHITE)
    f.circle(cx + 45, cy, 6, color=color, sw=2.0, fill=color)
    f.line(cx - 80, cy, cx - 51, cy, color=color, sw=2.2)
    f.line(cx + 51, cy, cx + 80, cy, color=color, sw=2.2)
    f.line(cx - 45, cy, cx + 34, cy - 38, color=color, sw=2.6)


def ch09_gpio_breaker_tables():
    f = Fig("ch09-gpio-breaker-tables", "GPIO：先合闸，再填表，后发令",
            title_color=BLUE_D, tag="CH 09 · GPIO")
    f.text(64, 126, "时钟没到，寄存器只是橱窗：写进去不响，读回全是 0。",
           size=19, color=MUTED)

    # ---- row 1: breaker / four tables / BSRR command ----
    f.card(54, 150, 300, 230, BLUE_D, fill=BLUE_FILL)
    f.text(70, 184, "① 合闸", size=20, color=BLUE_D, weight="bold")
    knife_switch(f, 204, 240, BLUE_D)
    f.text(204, 292, "RCC_AHB1ENR bit5", size=15, color=INK,
           anchor="middle", weight="bold")
    f.text(70, 322, "RCC 0x4002_3800", size=14, color=INK, font=MONO)
    f.text(70, 346, "AHB1ENR 偏移 0x30", size=14, color=INK)
    f.text(70, 370, "没合闸：写不响，读回全 0", size=14, color=RED)

    f.card(378, 150, 360, 230, GREEN_D, fill=GREEN_FILL)
    f.text(394, 184, "② 四张表，每脚两格", size=20, color=GREEN_D,
           weight="bold")
    tables = [("MODER", "2 位", "01"), ("OTYPER", "1 位", "0"),
              ("OSPEEDR", "2 位", "00"), ("PUPDR", "2 位", "00")]
    for i, (name, width, val) in enumerate(tables):
        y = 214 + i * 26
        f.text(394, y, name, size=15, color=INK, weight="bold", font=MONO)
        f.text(530, y, width, size=14, color=MUTED)
        f.text(620, y, val, size=15, color=GREEN_D, weight="bold",
               font=MONO)
    f.text(394, 326, "PF6 占 bits[13:12]（6×2）", size=15, color=INK)
    f.text(394, 352, "先清 0x3000，再置 0x1000", size=15, color=INK,
           weight="bold")
    f.text(394, 374, "直接 |=1：10/11 会落成 11", size=14, color=MUTED)

    f.card(762, 150, 336, 230, AMBER_STROKE, fill=AMBER_PALE)
    f.text(778, 184, "③ BSRR 发令", size=20, color=AMBER_STROKE,
           weight="bold")
    f.text(778, 214, "只写：写 1 生效，写 0 无影响", size=15, color=INK)
    f.pill(778, 228, 150, 40, "bit6 BS6 拉高", GREEN_D, fill=WHITE, size=15)
    f.pill(940, 228, 142, 40, "bit22 BR6 拉低", RED, fill=WHITE, size=15)
    f.text(778, 300, "BS6 = 0x00000040", size=14, color=INK, font=MONO)
    f.text(778, 324, "BR6 = 0x00400000", size=14, color=INK, font=MONO)
    f.text(778, 352, "共阳接 3.3V：拉低才亮", size=15, color=INK,
           weight="bold")
    f.text(778, 374, "读回恒 0，只做纯赋值", size=14, color=MUTED)

    # ---- row 2: ODR read-modify-write window + AF pairing ----
    f.card(54, 400, 660, 180, RED, fill=RED_FILL)
    f.text(70, 432, "ODR |= 编译成三条指令", size=20, color=RED,
           weight="bold")
    for x, label in ((80, "ldr"), (216, "orr"), (352, "str")):
        f.pill(x, 452, 96, 40, label, RED, fill=WHITE, size=17)
    f.arrow(180, 472, 212, 472, color=RED, sw=2.2, bend=0.0, head=7)
    f.arrow(316, 472, 348, 472, color=RED, sw=2.2, bend=0.0, head=7)
    f.text(128, 512, "读", size=13, color=MUTED, anchor="middle")
    f.text(264, 512, "改", size=13, color=MUTED, anchor="middle")
    f.text(400, 512, "写回", size=13, color=MUTED, anchor="middle")
    f.arrow(332, 545, 332, 502, color=RED, sw=2.4, bend=0.0, head=8)
    f.text(332, 564, "中断", size=14, color=RED, anchor="middle",
           weight="bold")
    f.text(70, 568, "症状：偶尔丢一次电平", size=15, color=RED,
           weight="bold")
    f.text(480, 462, "中断插队改另一位 →", size=15, color=RED)
    f.text(480, 488, "旧值整体写回，改动被覆盖", size=15, color=INK)
    f.text(480, 524, "BSRR 一条 str 原子完成", size=15, color=GREEN_D,
           weight="bold")
    f.text(480, 550, "写 0 无影响，连掩码都省", size=14, color=MUTED)

    f.card(738, 400, 360, 180, GREEN_D, fill=GREEN_FILL)
    f.text(754, 432, "复用要成对", size=20, color=GREEN_D, weight="bold")
    f.pill(754, 448, 150, 38, "MODER=10", BLUE_D, fill=WHITE, size=16)
    f.pill(920, 448, 150, 38, "AFR 选号", BLUE_D, fill=WHITE, size=16)
    f.text(754, 514, "只写 AFR：章盖了门没开", size=15, color=INK)
    f.text(754, 540, "只改 MODER：接进的是 AF0", size=15, color=INK)
    f.text(754, 566, "PA9 → AF7 = USART1_TX", size=15, color=INK,
           weight="bold")

    # ---- row 3: F103 boundary + SWD verdict ----
    f.card(54, 600, 780, 96, BLUE_D, fill=BLUE_FILL)
    f.text(70, 632, "F103 另一套：CRL/CRH · GPIO 时钟在 APB2", size=16,
           color=INK)
    f.text(70, 664, "换脚走 AFIO MAPR 整组重映射，先开 AFIO 时钟", size=16,
           color=INK)
    f.stamp(960, 648, "PA13/PA14 留给 SWD", RED, size=17, angle=-6)

    f.htext(54, 738, "先合闸，再填四张表；改位用 BSRR 纯赋值",
            size=22, color=INK, weight="bold", hl=True)
    f.text(576, 764,
           "位段与地址转引自 RM0090 §8.4 · e01 hardware_status pending · 布局示意，非实测",
           size=15, color=MUTED, anchor="middle")
    return f


def ch12_counter_three_knobs():
    figure = Fig("ch12-counter-three-knobs", "一只计数器，三个旋钮",
                 title_color=GREEN_D, tag="CH 12 · 定时器与 PWM")
    label = partial(figure.text, font="'Microsoft YaHei',sans-serif", halo=False)
    label(64, 132, "本图：F407 TIM3 · TIMclk = 84 MHz · 向上计数 · PWM1 正极性",
          size=23, color=INK)

    knobs = [
        (64, "PSC = 83", "计数步速", "84 MHz ÷ 84 = 1 MHz", BLUE_D, BLUE_FILL),
        (416, "ARR = 999", "一圈计数", "0 到 999，共 1000 次", GREEN_D, GREEN_FILL),
        (768, "CCR = 500", "高电平区间", "CNT < 500 时输出高", AMBER_STROKE, AMBER_PALE),
    ]
    for position, value, meaning, result, color, fill in knobs:
        figure.card(position, 164, 320, 132, color, fill=fill)
        label(position + 22, 204, value, size=29, color=color,
              weight="bold", font=MONO)
        label(position + 22, 243, meaning, size=24, color=INK)
        label(position + 22, 278, result, size=22, color=INK)

    figure.card(64, 320, 1024, 304, GREEN_D, fill=WHITE)
    label(88, 358, "上下对齐看：跨过 CCR 的时刻，就是高电平结束的时刻。",
          size=24, color=INK)
    label(88, 400, "CNT", size=27, color=GREEN_D, weight="bold", font=MONO)
    label(88, 438, "CCR = 500", size=22, color=AMBER_STROKE, font=MONO)
    label(254, 474, "0", size=22, color=INK, anchor="end", font=MONO)
    label(1048, 390, "ARR = 999", size=22, color=GREEN_D,
          anchor="end", font=MONO)
    figure.stroke([(280, 476), (664, 392), (664, 476),
                   (1048, 392), (1048, 476)], color=GREEN_D, sw=3.4, amp=0.4)
    figure.line(280, 434, 1048, 434, color=AMBER_STROKE,
                sw=2.0, dash="8 6", amp=0.2)
    for position in (472, 664, 856):
        figure.line(position, 434 if position != 664 else 476,
                    position, 564, color=MUTED, sw=1.2, dash="5 5", amp=0.2)
    label(88, 520, "PA6 高", size=24, color=BLUE_D)
    label(88, 560, "低", size=24, color=BLUE_D)
    figure.stroke([(280, 512), (472, 512), (472, 556), (664, 556),
                   (664, 512), (856, 512), (856, 556), (1048, 556)],
                  color=BLUE_D, sw=3.4, amp=0.3)
    label(376, 598, "高 0.5 ms", size=22, color=BLUE_D, anchor="middle")
    label(856, 598, "一周期 1 ms", size=22, color=GREEN_D, anchor="middle")

    label(64, 672, "频率 = TIMclk / ((PSC + 1) × (ARR + 1)) = 1 kHz",
          size=26, color=INK)
    label(64, 714, "高电平占比 = CCR / (ARR + 1) = 500 / 1000 = 50%",
          size=26, color=INK)
    label(576, 760, "改 CCR 只移动翻点；输入捕获另见正文。参数为算例，E03 待上板实测。",
          size=19, color=MUTED, anchor="middle")
    return figure


def byte_cells(f, x0, y, values, w, gap, fills, outline, size=18):
    for i, v in enumerate(values):
        x = x0 + i * (w + gap)
        f.rect(x, y, w, 50, color=outline, sw=2.0, fill=fills[i],
               double=False)
        f.text(x + w / 2, y + 32, v, size=size, color=INK,
               anchor="middle", weight="bold", font=MONO)


def ch13_cobs_paper_tape():
    f = Fig("ch13-cobs-paper-tape", "字节纸带：0x00 是唯一的剪口",
            title_color=BLUE_D, tag="CH 13 · UART 与帧协议")
    f.text(64, 126,
           "UART 只保证逐位传输，不知道命令在哪结束；边界要写进字节流本身。",
           size=19, color=MUTED)

    # ---- row 1: three framing methods and their loss costs ----
    f.card(54, 150, 330, 150, RED, fill=RED_FILL)
    f.text(70, 182, "长度前缀", size=18, color=RED, weight="bold")
    f.text(70, 212, "帧头写「后面还有 N 字节」", size=14, color=INK)
    f.text(70, 240, "丢一字节：长度字段错位", size=14, color=RED)
    f.text(70, 264, "之后每一帧都按错的长度切", size=14, color=RED)

    f.card(408, 150, 330, 150, AMBER_STROKE, fill=AMBER_PALE)
    f.text(424, 182, "转义 SLIP/HDLC", size=18, color=AMBER_STROKE,
           weight="bold")
    f.text(424, 212, "保留帧标志，出现就转义", size=14, color=INK)
    f.text(424, 240, "等下一个标志重新对齐", size=14, color=INK)
    f.text(424, 264, "最坏情况数据长度翻倍", size=14, color=AMBER_STROKE)

    f.card(762, 150, 330, 150, GREEN_D, fill=GREEN_FILL)
    f.text(778, 182, "COBS（本协议）", size=18, color=GREEN_D,
           weight="bold")
    f.text(778, 212, "数据里的 0 全换掉", size=14, color=INK)
    f.text(778, 240, "0x00 只当帧尾，等 0 对齐", size=14, color=GREEN_D,
           weight="bold")
    f.text(778, 264, "raw<254：开销恒为 1 字节", size=14, color=INK)

    # ---- row 2: the worked 10-byte example ----
    f.card(54, 320, 1044, 210, BLUE_D, fill=BLUE_FILL)
    f.text(70, 352, "手算一帧：INFO seq=7 → 8 raw + 1 COBS + 1 帧尾 = 10 字节",
           size=18, color=BLUE_D, weight="bold")
    f.text(1082, 352, "绿=码字 · 红=帧尾 0x00", size=13, color=MUTED,
           anchor="end")
    raw = ["01", "01", "07", "00", "00", "00", "CC", "B0"]
    raw_fills = [WHITE, WHITE, WHITE, AMBER_PALE, AMBER_PALE, AMBER_PALE,
                 WHITE, WHITE]
    byte_cells(f, 80, 364, raw, 90, 6, raw_fills, BLUE_D)
    fields = [(125, "version"), (221, "type"), (365, "seq=7"),
              (557, "length=0"), (749, "CRC")]
    for cx, label in fields:
        f.text(cx, 432, label, size=13, color=MUTED, anchor="middle")
    f.text(870, 388, "raw 8 字节", size=15, color=INK, weight="bold")
    f.text(870, 412, "CRC 0xB0CC", size=14, color=INK, font=MONO)
    f.text(870, 436, "检查值 0x29B1", size=13, color=MUTED)
    f.arrow(450, 442, 450, 458, color=BLUE_D, sw=2.2, bend=0.0, head=7)
    f.text(480, 456, "按 0 切段，段前放「段长+1」", size=14, color=BLUE_D)
    wire = ["04", "01", "01", "07", "01", "01", "03", "CC", "B0", "00"]
    wire_fills = [GREEN_FILL, WHITE, WHITE, WHITE, GREEN_FILL, GREEN_FILL,
                  GREEN_FILL, WHITE, WHITE, RED_FILL]
    byte_cells(f, 80, 466, wire, 86, 8, wire_fills, BLUE_D)

    # ---- row 3: three-state machine + lost-tail cost ----
    f.card(54, 550, 640, 150, GREEN_D, fill=GREEN_FILL)
    f.text(70, 582, "三态状态机：逐字节喂", size=19, color=GREEN_D,
           weight="bold")
    f.pill(80, 598, 120, 40, "EMPTY", GREEN_D, fill=WHITE, size=16)
    f.pill(280, 598, 140, 40, "COLLECT", GREEN_D, fill=WHITE, size=16)
    f.pill(500, 598, 140, 40, "DISCARD", RED, fill=WHITE, size=16)
    f.arrow(204, 618, 276, 618, color=GREEN_D, sw=2.2, bend=0.0, head=7)
    f.text(240, 608, "非零", size=12, color=MUTED, anchor="middle")
    f.arrow(424, 618, 496, 618, color=RED, sw=2.2, bend=0.0, head=7)
    f.text(460, 608, "满73/超时", size=12, color=MUTED, anchor="middle")
    f.arrow(350, 650, 142, 650, color=BLUE_D, sw=2.2, bend=-0.10, head=8)
    f.text(246, 678, "0x00：解码", size=13, color=BLUE_D, anchor="middle")
    f.arrow(570, 656, 142, 668, color=AMBER_STROKE, sw=2.2, bend=-0.10,
            head=8)
    f.text(356, 694, "0x00：丢弃结束", size=13, color=AMBER_STROKE,
           anchor="middle")

    f.card(718, 550, 380, 150, RED, fill=RED_FILL)
    f.text(734, 582, "丢帧尾的代价", size=19, color=RED, weight="bold")
    f.text(734, 612, "丢的恰是帧尾 0：下一帧被当残段吞掉", size=15,
           color=RED)
    f.text(734, 640, "主机重试前先单独发一个 0x00", size=15, color=INK,
           weight="bold")
    f.pill(734, 656, 348, 38, "确认先于执行：入队成功才执行", RED,
           fill=WHITE, size=14)

    f.htext(54, 738, "0x00 只当帧尾；丢了字节，等下一个 0 重新对齐",
            size=22, color=INK, weight="bold", hl=True)
    f.text(576, 764,
           "帧布局源码静态 · 样例独立复算 · e02 hardware_status pending · 布局示意，非实测",
           size=15, color=MUTED, anchor="middle")
    return f



def ch09_bitband_alias():
    """Bit-band alias formula worked for PF6, plus the three data
    register division. Facts from ch09/ch08 records."""
    f = Fig("ch09-bitband-alias",
            "位带：把一位搬进别名区",
            title_color=BLUE_D, tag="CH 09 · GPIO")
    f.text(64, 126,
           "写别名地址，硬件替你完成一次原子读改写；只覆盖两个区的前 1 MB，一次只管一位。",
           size=19, color=MUTED)

    f.card(64, 156, 560, 210, BLUE_D, fill=BLUE_FILL)
    f.text(84, 190, "别名公式（外设位带区）", size=18, color=BLUE_D,
           weight="bold")
    f.text(84, 222, "别名 = 0x42000000 + (地址 - 0x40000000) * 32", size=15,
           color=INK, font=MONO, weight="bold")
    f.text(84, 250, "                 + 位号 * 4", size=15, color=INK,
           font=MONO, weight="bold")
    f.text(84, 286, "F407 的 PF6 算过一遍（第 8 章）：", size=14.5, color=INK)
    f.text(84, 314, "GPIOF_ODR 0x40021414 bit6 -> 0x42428298", size=15,
           color=BLUE_D, font=MONO, weight="bold")
    f.text(84, 346, "写这个字 = 硬件原子改 ODR 的 bit6", size=14, color=MUTED)

    f.card(648, 156, 440, 210, GREEN_D, fill=GREEN_FILL)
    f.text(668, 190, "三个数据寄存器分工", size=18, color=GREEN_D,
           weight="bold")
    divs = [("IDR", "只读：引脚此刻的真实电平"),
            ("ODR", "可读可写：读改写有插队窗口"),
            ("BSRR", "只写：一条 str 原子，BS 低 16 位、BR 高 16 位")]
    for i, (r, note) in enumerate(divs):
        y = 224 + i * 44
        f.text(668, y, r, size=15.5, color=GREEN_D, weight="bold", font=MONO)
        f.text(760, y, note, size=13, color=INK)
    f.text(668, 352, "共阳接 3.3V：BR6（0x00400000）拉低 = 亮", size=13.5,
           color=INK)

    f.panel(64, 396, 1024, 100, RED_FILL, amp=1.6)
    f.rect(64, 396, 1024, 100, color=RED, sw=1.8, fill=None, amp=1.6)
    f.text(88, 428, "极性记反，代码完全反着工作：这套板子「高 16 位亮、低 16 位灭」",
           size=15, color=RED, weight="bold")
    f.text(88, 458, "BSRR |= x 读到 0 后碰巧等价于纯赋值——结果对，习惯错：只写寄存器的意图用 = 表达",
           size=14, color=INK)
    f.text(88, 484, "HAL_GPIO_WritePin 底层同样落 BSRR：用库不改原子性结论",
           size=14, color=MUTED)

    f.htext(64, 560, "两条原子路都通：位带或 BSRR；多比特字段回掩码操作",
            size=21, color=INK, weight="bold", hl=True)
    f.text(576, 590,
           "别名地址取自第 8/9 章推算记录；示意，非实测。",
           size=14, color=MUTED, anchor="middle")
    return f


def ch12_capture_two_pitfalls():
    """Input capture: measuring PWM with its own timer reads delta 0;
    wraparound needs three conditions. Facts from ch12 S6 record."""
    f = Fig("ch12-capture-two-pitfalls",
            "输入捕获两坑：自己测自己，回绕三条件",
            title_color=RED, tag="CH 12 · 定时器")
    f.text(64, 126,
           "TIM2 以 1MHz 自由计数、1 计数 = 1us；两次边沿的差值直接读成微秒。坑全在时基的选择上。",
           size=19, color=MUTED)

    f.card(64, 156, 500, 200, RED, fill=RED_FILL)
    f.text(84, 190, "坑一：拿 PWM 自己的定时器测自己", size=17, color=RED,
           weight="bold")
    f.text(84, 218, "TIM3 ARR=999，PWM 周期正好 1000 计数", size=14.5,
           color=INK)
    f.text(84, 244, "同相位边沿每周期落在同一个 CNT 上", size=14.5, color=INK)
    f.pill(84, 262, 220, 42, "差值恒为 0", RED, fill=WHITE, size=17)
    f.text(84, 328, "分不出经过了几圈——解法：换独立的 TIM2 捕获", size=14,
           color=MUTED)

    f.card(588, 156, 500, 200, AMBER_STROKE, fill=AMBER_PALE)
    f.text(608, 190, "坑二：回绕不是无脑相减", size=17, color=AMBER_STROKE,
           weight="bold")
    f.text(608, 218, "三条件：模数=位宽（2^32）· 间隔<一整圈 · 无丢边沿",
           size=14, color=INK)
    f.text(608, 244, "反例 TIM3：last=990、now=10，真差 20", size=14.5,
           color=INK, font=MONO)
    f.pill(608, 262, 300, 42, "uint32 相减 -> 4294966316", RED, fill=WHITE,
           size=14.5, text_color=RED)
    f.text(608, 328, "模 1000 也救不了：分不清零圈还是一整圈", size=14,
           color=MUTED)

    f.panel(64, 386, 1024, 116, GREEN_FILL, amp=1.6)
    f.rect(64, 386, 1024, 116, color=GREEN_D, sw=1.8, fill=None, amp=1.6)
    f.text(88, 418, "S6 的判定纪律（capture.h）", size=15.5, color=GREEN_D,
           weight="bold")
    f.text(88, 448, "32 位自由计数时基 · 只接受 100us-500ms 间隔 · 首次捕获只建基准 · 过捕获（overcapture）重建基准",
           size=14, color=INK)
    f.text(88, 476, "超 1 秒无新边沿清零；主循环用 PRIMASK 短临界区复制快照，临界区外使用",
           size=14, color=MUTED)

    f.htext(64, 560, "delta = now - previous：三条件齐了才是周期，否则是垃圾",
            size=21, color=INK, weight="bold", hl=True)
    f.text(576, 590,
           "数字取自本章 S6/capture.h 断言记录；机制示意，非实测波形。",
           size=14, color=MUTED, anchor="middle")
    return f


def ch13_brr_error_budget():
    """BRR integer is the denominator; error budget derived from 8.5
    bit-times. Facts from ch13 S7 record."""
    f = Fig("ch13-brr-error-budget",
            "BRR 整数值就是分母：误差预算 5.882%",
            title_color=BLUE_D, tag="CH 13 · UART 帧协议")
    f.text(64, 126,
           "16 × USARTDIV 正好是寄存器那 16 位：固件直接写整数，先算误差预算再挑 PCLK。",
           size=19, color=MUTED)

    f.card(64, 156, 470, 220, BLUE_D, fill=BLUE_FILL)
    f.text(84, 190, "BRR = round(PCLK / baud)", size=18, color=BLUE_D,
           weight="bold", font=MONO)
    f.text(84, 218, "16 x USARTDIV = 16*Mantissa + Fraction", size=14,
           color=INK, font=MONO)
    f.text(84, 248, "115200 @ 84MHz：BRR=729 -> 115226（+0.023%）", size=14,
           color=INK, font=MONO)
    f.text(84, 278, "Mantissa 39 + Fraction 1 写成 625 一个整数", size=14,
           color=INK, font=MONO)
    f.text(84, 316, "1 到 65535 全试过：四舍五入值就是最优值", size=14,
           color=MUTED)
    f.text(84, 344, "（宿主算术口径，非板上实测）", size=13, color=MUTED)

    f.card(558, 156, 530, 220, GREEN_D, fill=GREEN_FILL)
    f.text(578, 190, "预算从 8.5 个位时间推出来", size=18, color=GREEN_D,
           weight="bold")
    f.text(578, 218, "最险时刻：最后一位的中点 = 8.5 位", size=14.5, color=INK)
    f.text(578, 246, "|误差| x 8.5 < 0.5 -> 总容差 5.882%", size=15,
           color=GREEN_D, font=MONO, weight="bold")
    f.text(578, 274, "收发两端对半分：每端 2.941%", size=14.5, color=INK)
    f.text(578, 304, "1MHz 配 115200：BRR=9 -> -3.549%，一项吃掉六成，",
           size=14, color=RED, weight="bold")
    f.text(578, 330, "剩 2.333% 两端分，HSI ±1% 刚够，没有余量", size=14,
           color=RED, weight="bold")
    f.text(578, 360, "16MHz 配 921600：+2.124%，同样卡在量化", size=14,
           color=MUTED)

    f.panel(64, 406, 1024, 100, AMBER_PALE, amp=1.6)
    f.rect(64, 406, 1024, 100, color=AMBER_STROKE, sw=1.8, fill=None,
           amp=1.6)
    f.text(88, 438, "OVER8=1 的误差账两处来源对不上（S7 给 -0.794%，按字段定义复算约 -8.6%）",
           size=15, color=AMBER_STROKE, weight="bold")
    f.text(88, 468, "这里不下结论、标待复核：要落定得置 OVER8 后读回 BRR 并用仪器量线上位宽",
           size=14, color=INK)
    f.text(88, 494, "经验值「±2%-3%」的出处就是这条 8.5 位推导，不含温漂与走线延迟",
           size=13.5, color=MUTED)

    f.panel(64, 530, 1024, 100, GRAY_FILL, amp=1.6)
    f.rect(64, 530, 1024, 100, color=MUTED, sw=1.6, fill=None, amp=1.6)
    f.text(88, 562, "把预算走成三步", size=15.5, color=INK, weight="bold")
    f.text(88, 592, "① 算 BRR = round(PCLK/baud) 与实际误差　② 对照总容差 5.882%（每端 2.941%）",
           size=14.5, color=INK, font=MONO)
    f.text(88, 618, "③ 余量留给温漂与采样抖动——不为零就换 PCLK 或降波特率",
           size=14.5, color=INK, font=MONO)

    f.htext(64, 700, "先算 8.5 位再挑 PCLK——量化吃掉预算的六成，就没有余量了",
            size=21, color=INK, weight="bold", hl=True)
    f.text(576, 730,
           "读数取自本章 S7 八行误差表（宿主脚本口径）；推导示意。",
           size=14, color=MUTED, anchor="middle")
    return f


FIGS = {
    "ch09-gpio-breaker-tables": ch09_gpio_breaker_tables,
    "ch09-bitband-alias": ch09_bitband_alias,
    "ch12-counter-three-knobs": ch12_counter_three_knobs,
    "ch12-capture-two-pitfalls": ch12_capture_two_pitfalls,
    "ch13-cobs-paper-tape": ch13_cobs_paper_tape,
    "ch13-brr-error-budget": ch13_brr_error_budget,
}


if __name__ == "__main__":
    names = sys.argv[1:] or list(FIGS)
    STAGE.mkdir(parents=True, exist_ok=True)
    for n in names:
        f = FIGS[n]()
        save(f, str(STAGE / (n + ".svg")))
        print("wrote", STAGE / (n + ".svg"))
