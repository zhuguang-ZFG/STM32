# -*- coding: utf-8 -*-
"""ch25 knowledge-track figures (facts from docs/25, DS12110 Rev 11 / ES0392)."""
from hd import *


def part_id():
    f = Fig("ch25-part-id", "STM32H743ZIT6 是谁 / decode the part")
    f.panel(336, 118, 480, 76, AMBER_FILL)
    f.rect(336, 118, 480, 76, color=AMBER_STROKE, sw=3.0)
    f.text(W / 2, 148, "STM32H743ZI T 6", size=32, color=INK, anchor="middle",
           weight="bold")
    f.text(W / 2, 180, "Z = 144 脚 · I = 2 MB Flash · T = LQFP", size=20,
           color=MUTED, anchor="middle")
    facts = [
        ("内核", "Cortex-M7 @ 最高 480 MHz，双精度 FPU + 16 KB I/D Cache", GREEN_D),
        ("供电", "1.62 V – 3.6 V", GREEN_D),
        ("电源域", "D1 / D2 / D3 三个片内域，可分别关时钟或断电", BLUE_D),
        ("CAN", "2 × FDCAN（不是 F1/F4 的 bxCAN）", BLUE_D),
        ("USB", "2 × OTG（1 FS + 1 HS/FS），脚 95 VDD33USB 专用供电", AMBER_STROKE),
        ("调试", "PA13=脚 105 / PA14=脚 109；BOOT0=脚 138 独立", AMBER_STROKE),
    ]
    y = 236
    for t, d, c in facts:
        f.rect(120, y, 210, 56, color=c, fill=WHITE)
        f.text(225, y + 36, t, size=23, color=c, anchor="middle", weight="bold")
        f.text(356, y + 36, d, size=22, color=INK)
        y += 74
    f.text(W / 2, 690, "封装核对从 PE2（第 1 脚）开始，再数 VCAP1/2、VDD33USB、PDR_ON",
           size=23, color=MUTED, anchor="middle")
    return f


def pin_compare():
    f = Fig("ch25-pin-compare", "F1/F4 与 H7 的脚不是一套 / pin families differ")
    rows = [
        ("第 1 脚", "F103C8 = VBAT", "PE2（从右往左数）", RED),
        ("内核供电", "F1 内部，无 VCAP", "VCAP1=71 · VCAP2=106，外接电容", GREEN_D),
        ("USB 电源", "F1 没有", "脚 95 VDD33USB，不是普通 VDD", BLUE_D),
        ("掉电复位", "无此脚", "脚 143 PDR_ON", BLUE_D),
        ("BOOT", "F1 专用脚", "脚 138 BOOT0，与 SWD 分开", AMBER_STROKE),
        ("CAN", "bxCAN", "FDCAN：PA11/12 或 PD0/1 或 PB8/9", GREEN_D),
    ]
    y0 = 136
    f.text(150, y0 - 14, "项", size=20, color=MUTED, anchor="middle")
    f.text(430, y0 - 14, "F1 / F4", size=20, color=MUTED, anchor="middle")
    f.text(820, y0 - 14, "H743 LQFP144", size=20, color=MUTED, anchor="middle")
    for t, a, b, c in rows:
        y = y0
        f.rect(66, y, 170, 70, color=c, fill=WHITE)
        f.text(151, y + 42, t, size=21, color=c, anchor="middle", weight="bold")
        f.text(430, y + 42, a, size=21, color=MUTED, anchor="middle")
        f.rect(640, y, 446, 70, color=c, fill=WHITE)
        f.text(863, y + 42, b, size=21, color=INK, anchor="middle")
        y0 = y + 88
    f.htext(W / 2, 668, "有 L1 Cache：DMA 缓冲不维护一致性，调试器里的数组是旧的",
            size=24, color=RED, anchor="middle", weight="bold", hl=True)
    return f


def rev_vos():
    f = Fig("ch25-rev-vos", "revision 决定 400 还是 480 / VOS gate")
    # two lanes
    f.rect(90, 130, 430, 200, color=GREEN, fill=WHITE)
    f.htext(305, 172, "Rev Y / Rev W", size=28, color=GREEN_D, anchor="middle",
            weight="bold")
    f.multi(305, 214, ["没有 VOS0", "VOS1 上限 400 MHz", "照抄 480 配置 = 启动失败"],
            size=23, color=INK, lh=36, anchor="middle")
    f.rect(632, 130, 430, 200, color=BLUE, fill=WHITE)
    f.htext(847, 172, "Rev V", size=28, color=BLUE_D, anchor="middle",
            weight="bold")
    f.multi(847, 214, ["才允许 VOS0 → 480 MHz", "先在 VOS1 就绪，再进 VOS0", "每次换挡等 VOSRDY"],
            size=23, color=INK, lh=36, anchor="middle")
    f.htext(W / 2, 392, "怎么知道自己的 revision？", size=27, color=INK,
            anchor="middle", weight="bold", hl=True)
    f.multi(W / 2, 436, ["读 DBGMCU->IDCODE 的 REV_ID，对照 RM0433 / ES0392",
                         "不要靠开发板商品名或丝印批次猜"],
            size=23, color=INK, lh=36, anchor="middle")
    f.panel(110, 526, 952, 96, AMBER_FILL)
    f.rect(110, 526, 952, 96, color=AMBER_STROKE, sw=3.0)
    f.text(W / 2, 566, "供电方案启动初期配一次：LDO 板就 LDO_SUPPLY", size=25,
           color=INK, anchor="middle", weight="bold")
    f.text(W / 2, 602, "SMPS 板要同时改板级器件与软件宏 — 只改宏救不了板", size=22,
           color=INK, anchor="middle")
    return f


def clock_math():
    f = Fig("ch25-clock-math", "8 MHz 到 400 / 480 可复算 / clock arithmetic")
    f.panel(216, 122, 720, 90, AMBER_FILL)
    f.rect(216, 122, 720, 90, color=AMBER_STROKE, sw=3.0)
    f.text(W / 2, 158, "8 MHz ÷ PLLM4 × PLLN ÷ PLLP2", size=28, color=INK,
           anchor="middle", weight="bold")
    f.text(W / 2, 196, "400 路：N=400 → 400 MHz　480 路：N=480 → 480 MHz",
           size=22, color=INK, anchor="middle")
    tiers = [
        ("SystemCoreClock（CPU）", "480 MHz", GREEN_D),
        ("SystemD2Clock / HCLK", "240 MHz", BLUE_D),
        ("APB PCLK", "120 MHz", BLUE_D),
        ("APB 定时器时钟", "240 MHz（×2）", AMBER_STROKE),
    ]
    y = 258
    for t, v, c in tiers:
        f.rect(170, y, 560, 62, color=c, fill=WHITE)
        f.text(196, y + 38, t, size=23, color=INK)
        f.text(700, y + 38, v, size=23, color=c, anchor="end", weight="bold")
        y += 82
    f.multi(880, 300, ["别把 CPU 频率", "直接当 PCLK 用", "", "UART / PWM 的", "波特率与时基", "按各自时钟重算"],
            size=23, color=RED, lh=38, anchor="middle")
    f.htext(W / 2, 636, "升频后用 MCO2 / 波形验收，不用“看起来对了”", size=24,
            color=INK, anchor="middle", weight="bold", hl=True)
    return f


def pinmux():
    f = Fig("ch25-pinmux", "一只脚一个所有者 / one pin, one owner")
    # conflict 1
    f.rect(90, 140, 420, 230, color=RED, fill=WHITE)
    f.htext(300, 182, "PA11 / PA12", size=28, color=RED, anchor="middle",
            weight="bold")
    f.multi(300, 224, ["脚 103 / 104", "FDCAN1_RX/TX", "OTG_FS_DM/DP", "— 两个功能抢同一对脚"],
            size=23, color=INK, lh=36, anchor="middle")
    f.arrow(430, 255, 620, 255, color=GREEN_D, sw=3.2, head=11)
    f.htext(742, 214, "迁移出口", size=24, color=GREEN_D, anchor="middle",
            weight="bold")
    f.rect(632, 232, 430, 138, color=GREEN, fill=WHITE)
    f.multi(847, 274, ["FDCAN1 改到", "PD0 / PD1（脚 114/115）", "或 PB8 / PB9（脚 139/140）"],
            size=23, color=GREEN_D, lh=36, anchor="middle")
    # conflict 2
    f.rect(90, 424, 420, 210, color=AMBER_STROKE, fill=WHITE)
    f.htext(300, 466, "PB6 / PB7", size=28, color=AMBER_STROKE, anchor="middle",
            weight="bold")
    f.multi(300, 508, ["脚 136 / 137", "USART1_TX/RX", "也是 I2C1_SCL/SDA", "— 别同时配两个复用"],
            size=23, color=INK, lh=36, anchor="middle")
    f.rect(632, 424, 430, 210, color=BLUE, fill=WHITE)
    f.htext(847, 466, "CubeMX 无红叉", size=24, color=BLUE_D, anchor="middle",
            weight="bold")
    f.multi(847, 508, ["≠ 板级可用", "同一只脚不要配两个复用", "原理图与 DS12110", "Table 9 才是依据"],
            size=23, color=INK, lh=36, anchor="middle")
    f.text(W / 2, 700, "PC2_C / PC3_C 的 _C 是 ADC 专用路径，原理图别写成普通 PC2",
           size=22, color=MUTED, anchor="middle")
    return f


FIGS = {
    "ch25-part-id": part_id,
    "ch25-pin-compare": pin_compare,
    "ch25-rev-vos": rev_vos,
    "ch25-clock-math": clock_math,
    "ch25-pinmux": pinmux,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))
