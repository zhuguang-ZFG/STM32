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



def power_domains():
    f = Fig("ch25-power-domains", "H7 的三个电源域 / D1 · D2 · D3, switched apart")
    f.text(96, 138, "芯片内部分成 D1、D2、D3 三个电源域，可以分别关时钟或断电", size=22,
           color=MUTED)
    # 芯片框
    f.rect(96, 164, 700, 400, color=INK, fill=WHITE, sw=2.6)
    domains = [("D1", "CPU 与 AXI 一侧", GREEN_D, 128, 196),
               ("D2", "外设总线一侧", BLUE_D, 128, 320),
               ("D3", "低功耗一侧", AMBER_STROKE, 128, 444)]
    for name, note, c, x, y in domains:
        f.rect(x, y, 260, 100, color=c, fill=WHITE, sw=2.2)
        f.text(x + 130, y + 44, name, size=27, color=c, anchor="middle",
               weight="bold")
        f.text(x + 130, y + 78, note, size=18, color=MUTED, anchor="middle")
        f.text(470, y + 56, "↔ 可单独关时钟或断电", size=19, color=INK)
    # 右侧三只脚
    pins = [("VCAP1/2", "指向内核稳压器", GREEN_D, 164),
            ("VDD33USB", "第 95 脚，USB 专用", BLUE_D, 318),
            ("PDR_ON", "第 143 脚，掉电复位", RED, 472)]
    for name, note, c, y in pins:
        f.rect(840, y, 252, 110, color=c, fill=WHITE, sw=2.2)
        f.text(966, y + 44, name, size=23, color=c, anchor="middle",
               weight="bold")
        f.text(966, y + 80, note, size=17, color=INK, anchor="middle")
    f.panel(96, 604, 996, 76, AMBER_FILL)
    f.rect(96, 604, 996, 76, color=AMBER_STROKE, sw=3.0)
    f.text(W / 2, 650, "结构关系示意：不给出电容值，也不替代目标板原理图；要电流去电气特性",
           size=23, color=INK, anchor="middle", weight="bold")
    return f

def vcap_caps():
    f = Fig("ch25-vcap-caps", "VCAP 是内核稳压器的电容脚 / caps for the core")
    f.text(96, 128, "DS12110 Figure 7：内核供电有两只 VCAP；外接电容值去电气节查，图上不标",
           size=20, color=MUTED)
    # 左：芯片内的内核稳压器与两只外接电容
    f.rect(90, 156, 470, 314, color=INK, sw=2.4)
    f.text(110, 188, "STM32H743 芯片内", size=18, color=MUTED)
    f.rect(140, 212, 320, 84, color=GREEN_D, fill=WHITE, sw=2.2)
    f.text(300, 248, "内核稳压器", size=25, color=GREEN_D, anchor="middle",
           weight="bold")
    f.text(300, 280, "输出电容必须外接", size=17, color=MUTED, anchor="middle")
    f.line(190, 296, 190, 470, color=INK, sw=2.2)
    f.line(390, 296, 390, 470, color=INK, sw=2.2)
    f.line(190, 470, 190, 524, color=INK, sw=2.2)
    f.line(390, 470, 390, 524, color=INK, sw=2.2)
    f.text(212, 502, "脚 71 VCAP1", size=21, color=GREEN_D, weight="bold")
    f.text(412, 502, "脚 106 VCAP2", size=21, color=GREEN_D, weight="bold")
    for xc in (190, 390):
        f.line(xc - 28, 532, xc + 28, 532, color=INK, sw=3.4)
        f.line(xc - 28, 548, xc + 28, 548, color=INK, sw=3.4)
        f.line(xc, 548, xc, 578, color=INK, sw=2.2)
        f.circle(xc, 586, 5, color=INK, sw=2.0)
    f.text(238, 549, "外接电容", size=19, color=INK)
    f.text(96, 622, "容值只按 DS12110 的 VCAP 电气节选；本图不标电容值",
           size=19, color=MUTED)
    # 右：一行表格带出的三个不能
    f.text(640, 188, "一行表格，三个不能", size=24, color=RED, weight="bold")
    rows = [("直接接 VDD", "它们不是供电输入脚"),
            ("省掉电容", "内核稳压离不开这两只"),
            ("当普通去耦脚挪作他用", "手册原话：不是普通去耦脚")]
    y = 210
    for t, s in rows:
        f.rect(640, y, 440, 84, color=RED, fill=WHITE, sw=2.2)
        f.text(668, y + 52, "×", size=40, color=RED, weight="bold")
        f.text(714, y + 36, t, size=23, color=INK, weight="bold")
        f.text(714, y + 66, s, size=18, color=MUTED)
        y += 92
    f.rect(640, 508, 440, 84, color=BLUE, fill=WHITE, sw=2.2)
    f.text(660, 540, "F1 呢？", size=21, color=BLUE_D, weight="bold")
    f.text(660, 572, "内核供电在 F1 内部完成，没有 VCAP 脚", size=19, color=INK)
    # 底：失效模式与封装核对
    f.panel(90, 640, 990, 92, AMBER_FILL)
    f.rect(90, 640, 990, 92, color=AMBER_STROKE, sw=3.0)
    f.text(W / 2, 676, "没按电气节装电容 → 内核不起振或随机死（迁移排错表第一行）",
           size=23, color=INK, anchor="middle", weight="bold")
    f.text(W / 2, 710, "封装核对从 PE2（第 1 脚）开始，同时确认两只 VCAP 与目标板实际连接",
           size=20, color=INK, anchor="middle")
    return f


FIGS = {
    "ch25-part-id": part_id,
    "ch25-pin-compare": pin_compare,
    "ch25-rev-vos": rev_vos,
    "ch25-clock-math": clock_math,
    "ch25-pinmux": pinmux,
    "ch25-power-domains": power_domains,
    "ch25-vcap-caps": vcap_caps,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))
