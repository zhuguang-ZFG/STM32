# -*- coding: utf-8 -*-
"""Deterministic chapter 18 FAQ plates; no measured board data.

Boot: RM0008 Rev21 section3.4; pins/capacities: DS5319 F103C8T6.
Fault capture: ARM DUI0552A sections4.3.10--4.3.15.
"""
from hd import *


def multi_def():
    f = Fig("ch18-multi-def", "同一个共享变量，只定义一次")
    f.text(72, 145, "显式初始化的定义写进头文件，会进入每个包含它的翻译单元。", size=23, color=INK)
    f.rect(72, 182, 300, 107, color=RED, fill=WHITE)
    f.text(95, 218, "sensor.h", size=25, color=RED, weight="bold")
    f.text(95, 261, "int count = 0;", size=26, color=INK)
    for y, name in ((183, "main.c → main.o"), (329, "motor.c → motor.o")):
        f.rect(472, y, 290, 95, color=RED, fill=WHITE)
        f.text(617, y + 35, name, size=24, color=RED, anchor="middle", weight="bold")
        f.text(617, y + 72, "各自带一份 count 定义", size=22, color=INK, anchor="middle")
    f.arrow(382, 218, 461, 218, color=RED, bend=0)
    f.arrow(382, 261, 461, 352, color=RED, bend=0)
    f.line(776, 232, 823, 232, color=RED, sw=2.4)
    f.line(776, 377, 823, 377, color=RED, sw=2.4)
    f.line(823, 232, 823, 377, color=RED, sw=2.4)
    f.arrow(823, 304, 870, 304, color=RED, bend=0)
    f.text(888, 286, "链接冲突", size=27, color=RED, weight="bold")
    f.multi(888, 328, ["multiple", "definition"], size=23, color=RED, lh=32)
    f.line(72, 462, 1080, 462, color=MUTED, sw=1.2)
    f.text(72, 507, "共享对象的写法", size=27, color=GREEN_D, weight="bold")
    f.rect(72, 535, 430, 111, color=GREEN_D, fill=WHITE)
    f.text(96, 573, "sensor.h · 所有使用者都可包含", size=23, color=GREEN_D, weight="bold")
    f.text(96, 619, "extern int count;", size=27, color=INK)
    f.rect(602, 535, 478, 111, color=GREEN_D, fill=WHITE)
    f.text(626, 573, "sensor.c · 唯一一份定义", size=24, color=GREEN_D, weight="bold")
    f.text(626, 619, "int count = 0;", size=27, color=INK)
    f.arrow(513, 593, 589, 593, color=GREEN_D, bend=0)
    f.text(72, 696, "include guard 只防止同一翻译单元内重复包含，不能合并跨文件定义。", size=22, color=INK)
    f.text(72, 739, "头文件可以定义 static inline 辅助函数；它与共享全局对象的规则不同。", size=22, color=MUTED)
    return f


def boot_triage():
    f = Fig("ch18-boot-triage", "BOOT 选启动源，SWD 查连接")
    f.text(72, 143, "STM32F103C8T6 · 复位后第 4 个 SYSCLK 上升沿锁存 BOOT 引脚", size=23, color=MUTED)
    f.rect(409, 174, 334, 70, color=BLUE_D, fill=WHITE)
    f.text(576, 219, "BOOT0 · 第 44 脚", size=27, color=BLUE_D, anchor="middle", weight="bold")
    f.arrow(409, 208, 226, 294, color=GREEN_D, bend=0)
    f.text(284, 231, "0", size=27, color=GREEN_D, weight="bold")
    f.arrow(743, 208, 852, 273, color=BLUE_D, bend=0)
    f.text(788, 230, "1", size=27, color=BLUE_D, weight="bold")
    f.rect(690, 278, 326, 65, color=BLUE_D, fill=WHITE)
    f.text(853, 320, "再看 BOOT1", size=27, color=BLUE_D, anchor="middle", weight="bold")
    f.arrow(762, 351, 617, 395, color=AMBER_STROKE, bend=0)
    f.arrow(944, 351, 983, 395, color=RED, bend=0)
    f.text(679, 374, "0", size=25, color=AMBER_STROKE, weight="bold")
    f.text(980, 373, "1", size=25, color=RED, weight="bold")
    f.rect(72, 306, 320, 179, color=GREEN_D, fill=WHITE)
    f.text(232, 349, "主 Flash", size=30, color=GREEN_D, anchor="middle", weight="bold")
    f.text(232, 394, "0x08000000", size=27, color=INK, anchor="middle")
    f.text(232, 440, "BOOT1 任意", size=23, color=MUTED, anchor="middle")
    for x, title, addr, color in [(430, "系统存储器", "0x1FFFF000", AMBER_STROKE),
                                  (780, "SRAM", "0x20000000", RED)]:
        f.rect(x, 405, 300, 112, color=color, fill=WHITE)
        f.text(x + 150, 447, title, size=28, color=color, anchor="middle", weight="bold")
        f.text(x + 150, 489, addr, size=26, color=INK, anchor="middle")
    f.text(72, 559, "Flash / 系统区可映射到 0；SRAM 启动机制不同，初始化需重设 VTOR。", size=22, color=INK)
    f.line(72, 591, 1080, 591, color=MUTED, sw=1.3)
    f.text(72, 631, "SWD 能否读到芯片 ID，是另一项检查", size=26, color=BLUE_D, weight="bold")
    f.text(72, 676, "探针", size=26, color=BLUE_D, weight="bold")
    f.arrow(166, 669, 264, 669, color=BLUE_D, bend=0)
    f.text(288, 676, "PA13 · 34 / PA14 · 37", size=24, color=INK)
    f.arrow(654, 669, 738, 669, color=BLUE_D, bend=0)
    f.text(762, 676, "读 Device ID", size=26, color=GREEN_D, weight="bold")
    f.text(72, 726, "先核对供电、共地、SWDIO / SWCLK 与 NRST；BOOT0=1 不等于 SWD 失联。", size=21, color=MUTED)
    return f


def link_map():
    f = Fig("ch18-link-map", "先核对容量，再读链接映射")
    f.text(72, 144, "STM32F103C8T6 · 上半条长按容量同比例绘制；下半不表示占用大小。", size=22, color=MUTED)
    f.text(72, 199, "Flash", size=27, color=BLUE_D, weight="bold")
    f.rect(184, 172, 896, 51, color=BLUE_D, fill=WHITE, double=False)
    f.text(632, 207, "64 KiB · ORIGIN 0x08000000", size=25, color=BLUE_D, anchor="middle", weight="bold")
    f.text(72, 281, "SRAM", size=27, color=GREEN_D, weight="bold")
    f.rect(184, 254, 280, 51, color=GREEN_D, fill=WHITE, double=False)
    f.text(324, 290, "20 KiB", size=25, color=GREEN_D, anchor="middle", weight="bold")
    f.text(505, 288, "ORIGIN 0x20000000", size=25, color=GREEN_D)
    f.line(72, 343, 1080, 343, color=MUTED, sw=1.3)
    f.text(72, 387, "Flash：镜像中的内容", size=27, color=BLUE_D, weight="bold")
    f.text(672, 387, "SRAM：运行时内容", size=27, color=GREEN_D, weight="bold")
    f.rect(72, 415, 404, 86, color=BLUE_D, fill=WHITE)
    f.text(274, 451, ".text / .rodata", size=28, color=BLUE_D, anchor="middle", weight="bold")
    f.text(274, 483, "代码与只读常量", size=22, color=INK, anchor="middle")
    f.rect(72, 533, 404, 86, color=BLUE_D, fill=WHITE)
    f.text(274, 571, ".data 初始值 · LMA", size=26, color=BLUE_D, anchor="middle", weight="bold")
    f.text(274, 604, "仍占 Flash 镜像空间", size=22, color=INK, anchor="middle")
    f.rect(672, 533, 408, 86, color=GREEN_D, fill=WHITE)
    f.text(876, 571, ".data 变量 · VMA", size=26, color=GREEN_D, anchor="middle", weight="bold")
    f.text(876, 604, "初始化后在 RAM 中读写", size=22, color=INK, anchor="middle")
    f.arrow(486, 576, 657, 576, color=AMBER_STROKE, bend=0)
    f.text(572, 545, "启动时复制", size=21, color=AMBER_STROKE, anchor="middle")
    f.rect(672, 415, 408, 86, color=GREEN_D, fill=WHITE)
    f.text(876, 451, ".bss · 启动时清零", size=26, color=GREEN_D, anchor="middle", weight="bold")
    f.text(876, 483, "变量占 RAM；不存逐字节初值", size=21, color=INK, anchor="middle")
    f.text(72, 680, "overflow：该 region 的内容超出 LENGTH；先在 map 中查占用来源。", size=22, color=RED)
    f.text(72, 724, "ORIGIN 错：布局地址不符合目标与启动约定；扩大 LENGTH 不能修复它。", size=22, color=MUTED)
    return f


def hardfault_ladder():
    f = Fig("ch18-hardfault-ladder", "故障地址有效，栈 PC 也要单独核对")
    f.rect(72, 143, 1008, 121, color=BLUE_D, fill=WHITE)
    f.text(96, 181, "保存现场：BFAR / MMFAR 在先，再保留 CFSR / HFSR 与有效位", size=25, color=BLUE_D, weight="bold")
    f.text(96, 220, "同时保存 EXC_RETURN 与异常栈；避免把后续异常的新值混入判读。", size=23, color=INK)
    f.text(96, 250, "CFSR 0xE000ED28 · HFSR 0xE000ED2C · BFAR 0xE000ED38", size=20, color=MUTED)
    f.arrow(369, 274, 312, 319, color=GREEN_D, bend=0)
    f.arrow(783, 274, 840, 319, color=AMBER_STROKE, bend=0)
    f.text(72, 351, "地址线索", size=28, color=GREEN_D, weight="bold")
    f.text(620, 351, "代码线索", size=28, color=AMBER_STROKE, weight="bold")
    f.text(72, 394, "BFARVALID · CFSR bit 15", size=24, color=INK)
    f.line(100, 413, 100, 511, color=GREEN_D, sw=2)
    f.line(100, 438, 150, 438, color=GREEN_D, sw=2)
    f.line(100, 503, 150, 503, color=RED, sw=2)
    f.text(173, 446, "1：保留 BFAR 故障地址", size=25, color=GREEN_D)
    f.text(173, 511, "0：弃用 BFAR 的数值", size=25, color=RED)
    f.text(620, 394, "先确认异常栈帧与故障类型", size=24, color=INK)
    f.multi(620, 442, ["STKERR / MSTKERR：帧可能不完整", "IMPRECISERR：PC 可能滞后", "有效基本帧中 PC = frame[6]"], size=22, color=MUTED, lh=41)
    f.line(72, 575, 1080, 575, color=MUTED, sw=1.3)
    f.text(72, 619, "可信栈 PC", size=28, color=BLUE_D, weight="bold")
    f.arrow(270, 611, 360, 611, color=BLUE_D, bend=0)
    f.text(390, 619, "同一份 ELF", size=28, color=BLUE_D, weight="bold")
    f.arrow(622, 611, 712, 611, color=BLUE_D, bend=0)
    f.text(742, 619, "addr2line / 反汇编", size=27, color=GREEN_D, weight="bold")
    f.text(72, 679, "BFAR 是访存地址，不能拿来代替代码 PC；无效 BFAR 也不使栈帧自动可信。", size=22, color=INK)
    f.text(72, 725, "FORCED = HFSR bit 30：有故障升级，继续解码保存的 CFSR。", size=23, color=MUTED)
    return f


def faq_compare():
    f = Fig("ch18-faq-compare", "38 条 FAQ，先找第一处失败边界")
    f.text(72, 142, "8 + 7 + 9 + 7 + 7 = 38；每次留下证据，再改一处。", size=24, color=MUTED)
    rows = [(175, "C · 编译链接", "8", BLUE_D), (290, "D · 下载调试", "7", GREEN_D),
            (405, "P · 外设", "9", BLUE_D), (520, "H · 硬件", "7", RED),
            (635, "R · RTOS / 工具", "7", AMBER_STROKE)]
    for y, title, count, color in rows:
        f.line(72, y, 1080, y, color=MUTED, sw=1.2)
        f.circle(98, y + 48, 23, color=color, fill=WHITE)
        f.text(98, y + 57, count, size=27, color=color, anchor="middle", weight="bold")
        f.text(139, y + 56, title, size=25, color=color, weight="bold")
    # A diagnostic line from the real command, rather than an invented result.
    f.text(450, 213, "编译 / 链接命令", size=22, color=BLUE_D)
    f.line(450, 228, 627, 228, color=RED, sw=2)
    f.text(450, 256, "第一处完整错误", size=21, color=MUTED)
    f.arrow(665, 230, 722, 230, color=BLUE_D, bend=0)
    f.text(750, 235, "头文件路径 / 对象文件 / map", size=21, color=INK)
    # Probe reads identity; successful boot is a separate question.
    f.rect(450, 317, 158, 45, color=GREEN_D, fill=WHITE, double=False)
    f.text(529, 348, "SWD 探针", size=23, color=GREEN_D, anchor="middle")
    f.arrow(617, 340, 713, 340, color=GREEN_D, bend=0)
    f.text(750, 341, "能读 Device ID 吗？", size=23, color=INK)
    f.text(750, 372, "电源、共地、SWD 与复位", size=20, color=MUTED)
    # Pin-level waveform and upstream configuration.
    f.stroke([(450, 468), (475, 468), (475, 437), (513, 437), (513, 468), (551, 468), (551, 437), (589, 437), (589, 468), (620, 468)], color=BLUE_D, sw=2.6)
    f.text(535, 502, "引脚上的波形", size=20, color=MUTED, anchor="middle")
    f.arrow(665, 455, 722, 455, color=BLUE_D, bend=0)
    f.text(750, 460, "RCC 时钟 / GPIO / 状态位", size=22, color=INK)
    # Power and reset are levels to measure, rather than decorative circuitry.
    f.line(450, 576, 620, 576, color=RED, sw=2.6)
    for x in (475, 589):
        f.circle(x, 576, 6, color=RED, fill=WHITE)
    f.text(535, 555, "VDD / NRST", size=23, color=RED, anchor="middle")
    f.text(535, 612, "电压与复位波形", size=20, color=MUTED, anchor="middle")
    f.arrow(665, 570, 722, 570, color=RED, bend=0)
    f.text(750, 575, "先测供电，再查复位来源", size=22, color=INK)
    # Stack fill is symbolic, with no fabricated water-mark amount.
    for i in range(4):
        f.rect(450 + i * 40, 668, 40, 30, color=AMBER_STROKE, fill=WHITE, double=False)
    f.text(530, 729, "栈 / 堆 / 优先级记录", size=20, color=MUTED, anchor="middle")
    f.arrow(665, 685, 722, 685, color=AMBER_STROKE, bend=0)
    f.text(750, 690, "时基 / 分配结果 / FromISR", size=22, color=INK)
    return f


def uart_garbled():
    f = Fig("ch18-uart-garbled", "串口乱码，把接线和位宽都查清")
    f.text(72, 143, "USART1 · 3.3 V 逻辑电平 · TX 对 RX，共地；不要直接接 RS-232 电平。", size=23, color=INK)
    f.rect(72, 176, 296, 214, color=BLUE_D, fill=WHITE)
    f.rect(784, 176, 296, 214, color=GREEN_D, fill=WHITE)
    f.text(220, 213, "STM32F103", size=27, color=BLUE_D, anchor="middle", weight="bold")
    f.text(932, 213, "USB–UART 适配器", size=25, color=GREEN_D, anchor="middle", weight="bold")
    for y, left, right in [(257, "PA9 · TX", "TX"), (316, "PA10 · RX", "RX"), (367, "GND", "GND")]:
        f.text(96, y, left, size=25, color=BLUE_D)
        f.text(808, y, right, size=25, color=GREEN_D)
    f.arrow(374, 251, 774, 310, color=BLUE_D, bend=0)
    f.arrow(774, 251, 374, 310, color=GREEN_D, bend=0)
    f.line(374, 362, 774, 362, color=MUTED, sw=2.6)
    f.text(576, 347, "交叉处不连接", size=20, color=MUTED, anchor="middle")
    f.text(72, 436, "PPRE2=1，USART1 的 PCLK2=HCLK；BRR 原始值 0x271 = 625", size=22, color=INK)
    f.text(72, 476, "同一时间尺的单个位宽 · 理论值", size=25, color=INK, weight="bold")
    x0, scale = 356, 7.0
    for y, mhz, rate, color in [(534, 72, 115200, GREEN_D), (647, 8, 12800, RED)]:
        width = 1e6 / rate
        x1 = x0 + width * scale
        f.text(72, y - 7, f"{mhz} MHz / 625", size=24, color=color, weight="bold")
        f.text(72, y + 29, f"{rate} bit/s", size=23, color=color)
        f.stroke([(x0 - 24, y - 26), (x0, y - 26), (x0, y + 10), (x1, y + 10), (x1, y - 26), (1036, y - 26)], color=color, sw=2.6)
        f.text((x0 + x1) / 2, y + 45, f"{width:.3f} µs", size=21, color=color, anchor="middle")
    f.line(x0, 714, 1036, 714, color=MUTED, sw=1.3)
    for us in (0, 10, 30, 50, 70, 90):
        x = x0 + us * scale
        f.line(x, 709, x, 720, color=MUTED, sw=1.3)
        f.text(x, 746, str(us), size=19, color=MUTED, anchor="middle")
    f.text(1036, 747, "µs", size=20, color=MUTED)
    return f


FIGS = {
    "ch18-multi-def": multi_def,
    "ch18-boot-triage": boot_triage,
    "ch18-link-map": link_map,
    "ch18-hardfault-ladder": hardfault_ladder,
    "ch18-faq-compare": faq_compare,
    "ch18-uart-garbled": uart_garbled,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))
