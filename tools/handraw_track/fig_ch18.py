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


def five_steps():
    f = Fig("ch18-five-steps", "排错五步：从复现到手册")
    f.text(72, 128, "保留触发条件和失败现场；每次只验证一个假设。", size=22, color=MUTED)

    steps = [
        (72, "复现", ["记录触发条件、", "频率、运行负载"], "区分稳定失败与偶发", GREEN_D),
        (281, "最小化", ["退到只点灯 /", "只回环的最小工程"], "配置问题还是逻辑问题", BLUE_D),
        (490, "二分", ["注释一半代码，", "或逐个外设使能"], "定位引入问题的模块", AMBER_STROKE),
        (699, "看证据", ["串口日志 / 波形 /", "CFSR · BFAR"], "用数据代替猜测", RED),
        (908, "对照手册", ["查 RM / DS 的", "寄存器与时序"], "「以为对」是否真对", BLUE_D),
    ]
    for i, (x, name, action, purpose, col) in enumerate(steps):
        f.rect(x, 168, 172, 120, color=col, fill=WHITE)
        f.circle(x + 86, 168, 22, color=col, fill=WHITE, sw=2.6)
        f.text(x + 86, 176, str(i + 1), size=22, color=col, anchor="middle",
               weight="bold")
        f.text(x + 86, 222, name, size=26, color=col, anchor="middle", weight="bold")
        f.multi(x + 86, 250, action, size=18, color=INK, lh=26, anchor="middle")
        f.text(x + 86, 318, purpose, size=17, color=MUTED, anchor="middle")
    for x0, x1 in ((248, 277), (457, 486), (666, 695), (875, 904)):
        f.arrow(x0, 228, x1, 228, color=INK, sw=2.4, bend=0)

    # 修改后回到复现：同一条件复测
    f.stroke([(994, 342), (994, 396), (158, 396), (158, 352)],
             color=RED, sw=2.2, amp=1.2, dash="7 7", opacity=0.9)
    f.arrowhead(158, 350, 0, -1, color=RED, head=10)
    f.htext(576, 424, "每次只验证一个假设 · 修改后用同一条件复测", size=21, color=RED,
            anchor="middle", weight="bold", hl=True)

    f.line(72, 456, 1080, 456, color=MUTED, sw=1.3)

    # 三条铁律
    f.text(72, 498, "三条铁律", size=27, color=INK, weight="bold")
    rules = [(72, "能测就别猜", GREEN_D), (416, "先共地再看信号", BLUE_D),
             (760, "改一处只改一处", RED)]
    for x, rule, col in rules:
        f.rect(x, 518, 320, 84, color=col, fill=WHITE)
        f.text(x + 160, 570, rule, size=28, color=col, anchor="middle", weight="bold")
    f.text(72, 646, "猜测式修改会让两个错误叠在一起，最后谁也不认领。", size=20, color=MUTED)
    f.text(72, 696, "五步有顺序：先复现、再最小化；前两步走完还不知道范围，再二分、看证据。", size=21, color=INK)
    return f


def peripheral_triage():
    f = Fig("ch18-peripheral-triage", "九条外设 FAQ：先测什么，再改哪里")
    f.text(72, 120, "每条症状先做一项能区分原因的测量；测出结果，再改一处。",
           size=20, color=MUTED)

    for x, label in ((88, "症状 · P1–P9"), (396, "先测什么（第一边界）"),
                     (810, "按结果改哪里")):
        f.text(x, 158, label, size=20, color=INK, weight="bold")
    f.line(72, 172, 1080, 172, color=MUTED, sw=1.4)

    rows = [
        ("引脚写了没变化", "读 ODR，再量引脚电平", "开 RCC / 查模式复用"),
        ("按一下进多条中断", "记两次进入的时间戳差", "只记事件；时间戳确认"),
        ("收到的都是乱码", "量一位宽度与共地", "核 PCLK2 与 BRR"),
        ("I2C 卡住或超时", "量 SCL/SDA 空闲电平", "补上拉、核地址、9 时钟"),
        ("Flash 读回全 0xFF", "看片选与 MISO 采样沿", "W25Q 用 Mode0"),
        ("ADC 读数一直跳", "量 VDDA 是否稳", "去耦、加长采样"),
        ("PWM 没有波形", "读 CNT 是否在递增", "查 Start、AF 与通道"),
        ("DMA 只搬一次", "读 CCR 确认模式位", "改 DMA_CIRCULAR"),
        ("断电后时间归零", "查 LSE 起振与 VBAT", "按晶振选 5–15 pF"),
    ]
    y = 186
    for i, (sym, probe, fix) in enumerate(rows):
        f.rect(72, y, 272, 52, color=RED, fill=WHITE, sw=2.2)
        f.text(86, y + 33, f"P{i + 1}", size=17, color=MUTED)
        f.text(124, y + 33, sym, size=19, color=RED, weight="bold")
        f.arrow(348, y + 26, 372, y + 26, color=MUTED, sw=2.4, bend=0, head=8)
        f.rect(380, y, 380, 52, color=INK, fill=WHITE, sw=2.0)
        f.text(396, y + 33, probe, size=18, color=INK)
        f.arrow(764, y + 26, 788, y + 26, color=MUTED, sw=2.4, bend=0, head=8)
        f.rect(796, y, 284, 52, color=GREEN_D, fill=WHITE, sw=2.2)
        f.text(810, y + 33, fix, size=18, color=GREEN_D)
        y += 64
    return f


def hardware_triage():
    f = Fig("ch18-hardware-triage",
            "板子不对劲，先看四件事 / hardware triage H1–H4")
    f.text(84, 128, "只用图前已出现的 H1–H4：每个症状先给判据，再给「不能证明什么」",
           size=20, color=MUTED)

    cards = [
        ("H1", "LED 不亮", RED,
         ["先查极性：长脚 → 限流电阻 → 引脚",
          "PC13 不能向外供电流，别当驱动脚",
          "3.3 V + 270 Ω 直接点一次，先证明灯好"],
         "不能证明：固件已经在跑"),
        ("H2", "板子发烫", AMBER_STROKE,
         ["先断电再查：3.3 V 与 GND 有没有短路",
          "查电源反接、5 V 灌进 3.3 V 引脚",
          "发烫位置就是线索，别继续带电摸"],
         "不能证明：不烫就代表供电顺序对"),
        ("H3", "电流为 0", BLUE_D,
         ["先量供电引脚上的 3.3 V，不是模块标签",
          "核对电流表：串联、量程、保险丝",
          "0 电流先怀疑表与线，不先怀疑 BOOT"],
         "不能证明：表读 0 等于芯片没启动"),
        ("H4", "复位抖动 / 反复重启", GREEN_D,
         ["复位后第一时间读并存 RCC 复位标志",
          "再查供电纹波与 NRST 上的干扰",
          "NRST 内部上拉；0.1 µF 从第 7 脚到 GND"],
         "不能证明：晚读标志会被下一次复位覆盖"),
    ]
    for i, (tag, title, color, lines, boundary) in enumerate(cards):
        x = 84 + (i % 2) * 510
        y = 164 + (i // 2) * 292
        f.rect(x, y, 494, 264, color=color, fill=WHITE, sw=2.4)
        f.text(x + 20, y + 40, tag, size=25, color=color, weight="bold")
        f.text(x + 68, y + 40, title, size=22, color=color, weight="bold")
        f.multi(x + 22, y + 78, lines, size=16, color=INK, lh=26)
        f.text(x + 22, y + 214, boundary, size=15, color=MUTED)

    f.text(84, 760, "四条判据覆盖「灯 / 热 / 电 / 复位」；外设与 RTOS 症状见后两张图",
           size=16, color=MUTED)
    return f


def rtos_triage():
    f = Fig("ch18-rtos-triage",
            "上了 RTOS 之后，四种卡法 / RTOS triage R1–R4")
    f.text(84, 128, "只用图前已出现的 R1–R4；先定位是哪一层在卡，再改配置",
           size=20, color=MUTED)

    cards = [
        ("R1", "HAL_Delay 卡死", BLUE_D,
         ["先看 HAL_GetTick() 还涨不涨",
          "HAL 的 1 ms 基准挪到 TIM4",
          "SysTick 归内核，configTICK_RATE_HZ=1000"],
         "计时器停了，Delay 才停；不是 Delay 坏了"),
        ("R2", "configASSERT 自旋", RED,
         ["停在中断优先级断言：数值必须 ≥5",
          "阈值 5 << (8−4) = 0x50，比的是移位值",
          "空指针也会掉进同一个断言"],
         "断言关掉不会变安全，只会变随机"),
        ("R3", "xTaskCreate 失败", AMBER_STROKE,
         ["看返回码：堆不够，还是栈需求不够",
          "configTOTAL_HEAP_SIZE 只对静态数组堆生效",
          "heap_3 走 malloc，改的是链接脚本的堆"],
         "堆加大不解决优先级配错"),
        ("R4", "ISR 里调普通 API → HardFault", GREEN_D,
         ["普通 xQueueSend 不能进 ISR",
          "换 xQueueSendFromISR + portYIELD_FROM_ISR",
          "先看调用栈，再看故障地址"],
         "HardFault 的位置不等于根因"),
    ]
    for i, (tag, title, color, lines, boundary) in enumerate(cards):
        x = 84 + (i % 2) * 510
        y = 164 + (i // 2) * 292
        f.rect(x, y, 494, 264, color=color, fill=WHITE, sw=2.4)
        f.text(x + 20, y + 40, tag, size=25, color=color, weight="bold")
        f.text(x + 68, y + 40, title, size=22, color=color, weight="bold")
        f.multi(x + 22, y + 78, lines, size=16, color=INK, lh=26)
        f.text(x + 22, y + 214, boundary, size=15, color=MUTED)

    f.text(84, 760, "R1/R3 是配置与资源，R2/R4 是优先级与调用纪律；两类的改法不同",
           size=16, color=MUTED)
    return f


def pin_card():
    f = Fig("ch18-pin-card",
            "LQFP48 顶视：FAQ 里点名的脚与它们的邻居")

    f.text(576, 136, "顶视图，非封装图：pin 1 在左上标记处，逆时针编号；只标本章用到的脚",
           size=16, color=MUTED, anchor="middle")

    left, top, size = 448, 214, 256
    right, bottom = left + size, top + size
    pitch = size / 12

    def pos(i):
        if i <= 12:            # left, top -> bottom
            return left, top + (i - 0.5) * pitch, (-18, 0)
        if i <= 24:            # bottom, left -> right
            return left + (i - 13 + 0.5) * pitch, bottom, (0, 18)
        if i <= 36:            # right, bottom -> top
            return right, bottom - (i - 25 + 0.5) * pitch, (18, 0)
        return right - (i - 37 + 0.5) * pitch, top, (0, -18)   # top, right -> left

    marked = {1, 2, 3, 4, 7, 10, 34, 35, 37, 44}
    for i in range(1, 49):
        x, y, (dx, dy) = pos(i)
        col = RED if i in marked else MUTED
        f.line(x, y, x + dx, y + dy, color=col,
               sw=2.4 if i in marked else 1.4, amp=0.4)
        if i in marked:
            lx, ly = x + dx * 1.55, y + dy * 1.55
            anchor = "middle"
            if dx < 0:
                anchor = "end"
            elif dx > 0:
                anchor = "start"
            f.text(lx, ly + 4, str(i), size=11, color=RED, anchor=anchor,
                   weight="bold")

    f.rect(left, top, size, size, color=INK, fill=WHITE, sw=3.0)
    f.circle(left + 24, top + 24, 7, color=INK, fill=INK, sw=1.2)
    f.text(left + 40, top + 30, "pin 1", size=12, color=MUTED)

    lcards = [
        (182, 88, "第 1 脚 VBAT", ["备份域电池：主电源掉了，", "RTC 与 BKP 靠它续电"]),
        (278, 88, "第 2 脚 PC13", ["只能灌电流：≤3 mA、≤2 MHz", "不能当电流源点灯"]),
        (374, 96, "第 3 / 4 脚：LSE", ["32.768 kHz；PRL = 32767", "才是 1 Hz"]),
        (478, 88, "第 7 脚 NRST", ["内部上拉；图 31 外部", "电容 0.1 µF 到地"]),
        (574, 88, "第 10 脚 PA0", ["第 03 章外接灯 270 Ω", "Standby 的 WKUP 是上升沿"]),
    ]
    targets = [(430, pos(1)[1]), (430, pos(2)[1]), (430, pos(3)[1] + 11),
               (430, pos(7)[1]), (430, pos(10)[1])]
    for (cy, h, head, lines), (tx, ty) in zip(lcards, targets):
        f.rect(84, cy, 296, h, color=INK, fill=WHITE, sw=1.8, double=False)
        f.text(104, cy + 30, head, size=16, color=INK, weight="bold")
        f.multi(104, cy + 54, lines, size=12.5, color=MUTED, lh=20)
        f.stroke([(382, cy + 40), (tx - 6, ty)], color=MUTED, sw=1.3, amp=0.3,
                 dash="5 5")

    rcards = [
        (170, 96, "第 34 脚 PA13 = SWDIO", ["第 37 脚 PA14 = SWCLK（顶边）",
                                           "接反或没共地就连不上"]),
        (286, 76, "第 35 脚 VSS_2", ["不是 SWCLK；相邻脚别接错"]),
        (382, 92, None, ["系统存储器启动 ≠ 芯片认不出，", "也不表示 Flash 已被擦除",
                         "Flash 里的旧镜像可能还在"]),
    ]
    for cy, h, head, lines in rcards:
        f.rect(772, cy, 296, h, color=INK, fill=WHITE, sw=1.8, double=False)
        if head:
            f.text(792, cy + 32, head, size=16, color=INK, weight="bold")
            f.multi(792, cy + 58, lines, size=13, color=MUTED, lh=22)
        else:
            f.multi(792, cy + 32, lines, size=13, color=MUTED, lh=22)

    f.stroke([(770, 218), (724, pos(34)[1])], color=MUTED, sw=1.3, amp=0.3, dash="5 5")
    f.stroke([(770, 324), (724, pos(35)[1])], color=MUTED, sw=1.3, amp=0.3, dash="5 5")

    f.rect(430, 516, 286, 116, color=RED, fill=WHITE, sw=2.0)
    f.text(452, 550, "第 44 脚 BOOT0（顶边）", size=16, color=RED, weight="bold")
    f.multi(452, 578, [
        "= 0：主闪存 0x08000000，与 BOOT1 无关",
        "= 1 且 BOOT1 = 0：系统存储器 0x1FFFF000",
        "0x1FFFB000 属互联型，不能套 C8",
    ], size=12.5, color=MUTED, lh=21)

    f.htext(84, 692, "先按脚号对事实，再谈接线：第 35 脚不是 SWCLK，第 44 脚拉高也不擦 Flash",
            size=20, weight="bold")
    f.text(84, 730, "脚号与功能见 DS5319 表 5 与图 31；本图只重排本章点名脚，其余脚查原表",
           size=14, color=MUTED)
    return f


def download_triage():
    f = Fig("ch18-download-triage",
            "下载与调试 D1–D7：先分组，再挑第一项检查")

    f.text(84, 138, "四组问题的证据链不同：连接看线与 ID，下载看算法与保护，观察看符号，运行看现场",
           size=17, color=MUTED)

    cols = [
        (84, BLUE, "连接（D1 / D2 / D6）", [
            ("D1 连不上", ["先量 SWDIO/SWCLK、共地、3.3 V", "接 NRST 试 connect under reset"]),
            ("D2 烧完失联", ["PA13/PA14 被改成 GPIO", "复位下连接；或改 BOOT0=1、",
                          "BOOT1=0 从系统存储器启动"]),
            ("D6 固件旧", ["用 Upgrade 工具升级", "克隆 ST-Link 慎升级"]),
        ]),
        (340, AMBER_STROKE, "下载（D3）", [
            ("D3 下载一半失败", ["核对型号、Flash 算法与时钟", "读保护 RDP？解除会擦主 Flash",
                              "先确认再动选项字节"]),
            ("边界", ["下载成功 ≠ 程序在跑", "运行问题看最右一列"]),
        ]),
        (596, GREEN_D, "观察（D4 / D5）", [
            ("D4 断点不生效", ["FPB 的 6 个比较器是否已占", "ELF 与目标固件要同一份"]),
            ("D5 单步乱跳", ["优化重排、内联", "改 -O0 或 -Og 再看行号"]),
        ]),
        (852, RED, "运行（D7）", [
            ("D7 一进调试就 HardFault", ["先保存寄存器与故障现场", "CFSR 分类，再看 BFAR",
                                       "bit15 有效才读地址", "同一份 ELF 定位（第 17 章）"]),
            ("边界", ["HardFault 位置 ≠ 根因", "栈帧坏先查栈"]),
        ]),
    ]
    for x, col, head, items in cols:
        f.rect(x, 176, 240, 350, color=col, fill=WHITE, sw=2.4)
        f.text(x + 18, 214, head, size=17, color=col, weight="bold")
        yy = 252
        for tag, lines in items:
            f.text(x + 18, yy, tag, size=14, color=INK, weight="bold")
            f.multi(x + 18, yy + 22, lines, size=12.5, color=MUTED, lh=19)
            yy += 26 + 19 * len(lines) + 12

    f.panel(84, 560, 1008, 66, "#FBEFD3", amp=1.8)
    f.text(588, 590, "分组的意义：连接问题先量线、不看优化等级；运行问题先存现场、不猜代码",
           size=17, color=INK, anchor="middle")
    f.text(588, 616, "每一组只改一处，改完用同一条件复测", size=13.5,
           color=MUTED, anchor="middle")

    f.htext(84, 680, "先认出坏在哪一段，再决定动哪一处",
            size=20, weight="bold")
    f.text(84, 716, "D1–D7 全文见本章第二节；D7 的寄存器判读见第 17 章",
           size=14, color=MUTED)
    return f


def peripheral_roots():
    f = Fig("ch18-peripheral-roots",
            "九条外设 FAQ 的三种根因：开关没开、对不上、没处理物理层")

    f.text(84, 138, "P1–P9 按「第一项检查」归类；同一现象可能跨两类，顺序比结论重要",
           size=17, color=MUTED)

    cols = [
        (84, BLUE, "开关没开", [
            ("P1 GPIO 写了不动", "GPIOx 时钟没使能"),
            ("P7 PWM 无输出", "没调 HAL_TIM_PWM_Start；AF 未配"),
            ("P4 I2C 卡死", "上拉缺失；7 位地址错"),
        ]),
        (436, GREEN_D, "配置对不上", [
            ("P3 串口乱码", "BRR 与 PCLK2 对不上；未共地"),
            ("P5 SPI 全 FF", "CS 没拉低；Mode0；MISO"),
            ("P6 ADC 跳动", "参考不稳；采样时间短"),
            ("P8 DMA 只搬一次", "期望循环却配了 NORMAL"),
        ]),
        (788, RED, "物理层没处理", [
            ("P2 按一次进多次中断", "抖动未消抖"),
            ("P9 RTC 归零", "LSE 未起振；VBAT；电容"),
            ("P4 总线被拉死", "9 个时钟脉冲恢复"),
        ]),
    ]
    for x, col, head, items in cols:
        f.rect(x, 176, 316, 366, color=col, fill=WHITE, sw=2.4)
        f.text(x + 20, 216, head, size=20, color=col, weight="bold")
        yy = 258
        for tag, line in items:
            f.text(x + 20, yy, tag, size=14.5, color=INK, weight="bold")
            f.text(x + 20, yy + 24, "→ " + line, size=13, color=MUTED)
            yy += 70

    f.panel(84, 570, 1008, 84, "#F7DCD8", amp=1.8)
    f.text(588, 602, "同一现象可能跨两类：I2C 卡死既可能缺上拉，也可能总线被拉死",
           size=18, color=INK, anchor="middle", weight="bold")
    f.text(588, 630, "按「时钟 → 引脚复用 → 标志」的顺序过完老三样，再看波特率、过滤器和采样时间",
           size=14, color=MUTED, anchor="middle")

    f.htext(84, 706, "先归类，再改一处；三类根因的修法互不替代",
            size=20, weight="bold")
    f.text(84, 742, "P1–P9 条目与出处见本章第三节；I2C 恢复见 P4 处理",
           size=14, color=MUTED)
    return f


def hardware_extra():
    f = Fig("ch18-hardware-extra",
            "H5–H7：晶振、面包板、共地——先把硬件变量钉住")

    f.text(84, 138, "三个现象都能伪装成软件问题；先固定接线与电容，再怀疑代码",
           size=17, color=MUTED)

    cards = [
        (84, BLUE, "H5 外部晶振不起振", [
            "现象：HSERDY / LSERDY 超时",
            "应用可能停在错误处理",
            "原因：负载电容、虚焊、走线",
            "处理：按晶振手册选电容；查焊接",
            "再查软件的超时路径",
            "别推成：HSE 失败 = 必然 HSI 回退",
            "LSE 失败也不会自动换时钟源",
        ]),
        (436, AMBER_STROKE, "H6 面包板接触不良", [
            "现象：时好时坏，晃动就复位",
            "原因：接触电阻大、杜邦线太长",
            "处理：换线、缩短连线",
            "关键信号直接焊死",
        ]),
        (788, RED, "H7 串口 / 下载的共地", [
            "现象：不共地就乱码或连不上",
            "原因：两个电源地电位不同",
            "处理：先把 GND 连在一起",
            "先共地，再看信号",
        ]),
    ]
    for x, col, head, lines in cards:
        f.rect(x, 176, 316, 330, color=col, fill=WHITE, sw=2.4)
        f.text(x + 20, 218, head, size=18, color=col, weight="bold")
        f.multi(x + 20, 262, lines, size=14, color=INK, lh=30)

    f.panel(84, 548, 1008, 82, "#FBEFD3", amp=1.8)
    f.text(588, 580, "H5 的「超时」是软件看到的，根因可能在线与电容",
           size=18, color=INK, anchor="middle", weight="bold")
    f.text(588, 608, "同一块板换一根线、补一次焊，就把「偶发」变成「可复现」",
           size=14, color=MUTED, anchor="middle")

    f.htext(84, 692, "先固定硬件变量，再谈软件：能测就别猜",
            size=20, weight="bold")
    f.text(84, 728, "H5–H7 见本章第四节；晶振电容与 LSE 细节见第 11 章",
           size=14, color=MUTED)
    return f


FIGS = {
    "ch18-hardware-triage": hardware_triage,
    "ch18-rtos-triage": rtos_triage,
    "ch18-multi-def": multi_def,
    "ch18-boot-triage": boot_triage,
    "ch18-link-map": link_map,
    "ch18-hardfault-ladder": hardfault_ladder,
    "ch18-faq-compare": faq_compare,
    "ch18-uart-garbled": uart_garbled,
    "ch18-peripheral-triage": peripheral_triage,
    "ch18-five-steps": five_steps,
    "ch18-pin-card": pin_card,
    "ch18-download-triage": download_triage,
    "ch18-peripheral-roots": peripheral_roots,
    "ch18-hardware-extra": hardware_extra,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))
