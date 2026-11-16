# -*- coding: utf-8 -*-
"""Knowledge-track plates for the merged v0 foundations and v6 projects.

All numbers and claims are copied from the chapter text; the plates are
explanatory diagrams, not measurements or board photos.
"""
from hd import *


def v0_call_frame():
    f = Fig("v0-04-call-frame", "一跳之后：函数指针、参数与栈帧")
    f.text(72, 140, "Cortex-M4 · 向量表是 Flash 里的函数指针数组；跳过去之后，AAPCS 接管参数、返回值与栈。",
           size=20, color=MUTED)

    # ---- ① 查表与间接调用 ----
    f.text(72, 194, "① 一跳：查表 + blx", size=23, color=BLUE_D, weight="bold")
    f.rect(72, 212, 290, 72, color=BLUE_D, fill=WHITE)
    f.text(92, 241, "FSM[3][4]", size=22, color=BLUE_D, weight="bold")
    f.text(92, 269, "状态 × 事件 → 动作", size=17, color=INK)
    f.arrow(217, 286, 217, 314, color=BLUE_D, bend=0)
    f.rect(72, 318, 290, 44, color=BLUE_D, fill=WHITE, sw=2.2, double=False)
    f.text(92, 346, "t = FSM[state][event]", size=17, color=INK)
    f.arrow(217, 364, 217, 392, color=AMBER_STROKE, bend=0)
    f.rect(72, 396, 290, 46, color=AMBER_STROKE, fill=WHITE)
    f.text(92, 425, "blx r3", size=22, color=AMBER_STROKE, weight="bold")
    f.text(72, 470, "查表 + 间接调用 + strb：4 条有效指令", size=17, color=INK)
    f.text(72, 496, "表放在 .rodata；FSM 48 B 不占 RAM", size=16, color=MUTED)

    f.rect(72, 532, 290, 150, color=GREEN_D, fill=WHITE, sw=2.4)
    f.text(92, 561, "向量表：同一机制", size=18, color=GREEN_D, weight="bold")
    f.multi(92, 591, ["0x08000000  _estack",
                      "0x08000004  Reset_Handler",
                      "0x08000008  EXTI0_IRQHandler"], size=14.5, color=INK, lh=23)
    f.text(92, 663, "槽位只认符号名，不认 C 类型", size=15, color=MUTED)

    # ---- ② 参数落位 ----
    f.text(400, 194, "② 参数：r0–r3，再往栈上", size=22, color=GREEN_D, weight="bold")
    for i, (reg, arg) in enumerate([("r0", "a1"), ("r1", "a2"), ("r2", "a3"), ("r3", "a4")]):
        x = 400 + i * 72
        f.rect(x, 212, 64, 50, color=GREEN_D, fill=WHITE, sw=2.2, double=False)
        f.text(x + 32, 237, reg, size=18, color=GREEN_D, anchor="middle", weight="bold")
        f.text(x + 32, 255, arg, size=13, color=MUTED, anchor="middle")
    f.text(400, 286, "前 4 个参数", size=16, color=MUTED)

    f.rect(400, 318, 286, 152, color=GREEN_D, fill=WHITE, sw=2.2)
    f.text(418, 346, "sum6：第 5、6 个走栈", size=17, color=GREEN_D, weight="bold")
    f.multi(418, 376, ["r0–r3 = 1,2,3,4",
                       "[sp] = 5   [sp+4] = 6",
                       "ldr r2,[sp]；ldr r0,[sp,#4]",
                       "返回 21；函数自己的帧 0 B"], size=15, color=INK, lh=23)
    f.rect(400, 488, 286, 112, color=AMBER_STROKE, fill=WHITE, sw=2.2)
    f.text(418, 516, "mix(int tag, long long v)", size=16, color=AMBER_STROKE, weight="bold")
    f.multi(418, 544, ["tag → r0", "v → r2:r3（偶数号寄存器）", "r1 空着，不进 64 位参数"],
            size=15, color=INK, lh=22)
    f.text(400, 624, "签名排序：64 位在前，int 在后", size=16, color=MUTED)

    # ---- ③ 栈帧 ----
    f.text(720, 194, "③ 栈帧：24 字节的来去", size=21, color=BLUE_D, weight="bold")
    f.text(720, 222, "Cortex-M4 · push {r4, lr}；sub sp,#16；pop {r4, pc}",
           size=15, color=MUTED)
    f.text(720, 258, "高地址", size=15, color=MUTED)
    f.rect(720, 270, 300, 42, color=MUTED, fill=WHITE, sw=2.0, double=False, dash="6 5")
    f.text(740, 297, "调用方栈参数（如有）", size=15, color=MUTED)
    f.rect(720, 316, 300, 42, color=BLUE_D, fill=WHITE, sw=2.2, double=False)
    f.text(740, 343, "push：保存 r4", size=16, color=INK)
    f.rect(720, 362, 300, 42, color=BLUE_D, fill=WHITE, sw=2.2, double=False)
    f.text(740, 389, "push：保存 LR（返回地址）", size=16, color=INK)
    f.rect(720, 408, 300, 64, color=GREEN_D, fill=WHITE, sw=2.2, double=False)
    f.text(740, 437, "sub sp,#16：buf[16]", size=16, color=INK)
    f.text(740, 460, "16 B", size=15, color=MUTED)
    f.line(1030, 476, 1030, 492, color=INK, sw=2)
    f.text(1044, 489, "sp", size=16, color=INK, weight="bold")
    f.text(720, 512, "低地址", size=15, color=MUTED)
    f.text(720, 546, "8 + 16 = 24 B", size=20, color=BLUE_D, weight="bold")
    f.text(720, 578, "pop {r4, pc}：弹栈与跳转合一", size=16, color=RED)
    f.text(720, 608, "叶子函数：不存 LR，bx lr 返回", size=15, color=MUTED)
    f.text(720, 636, "ISR 签名：void f(void)", size=16, color=INK)
    f.text(720, 662, "签名错，链接器不一定报错", size=15, color=RED)

    f.htext(72, 706, "跳过去只决定“去哪”；参数、栈帧与返回，全由 AAPCS 决定。",
            size=21, color=INK, weight="bold", hl=True)
    return f


def v0_four_steps():
    f = Fig("v0-05-four-steps", "65 行 C，四步之后只剩 660 字节")
    f.text(72, 140, "xPack GNU Arm Embedded GCC 15.2.1 · 每一步都留下可检查的文件；链接由 collect2 代理。",
           size=19, color=MUTED)

    boxes = [
        (72, "main.c", "65 行", "源文件", BLUE_D),
        (270, "main.i", "1575 行", "-E 预处理 · cc1", BLUE_D),
        (468, "main.s", "3757 行", "-S 编译 · cc1", GREEN_D),
        (666, "main.o", ".text 0xA8", "-c 汇编 · as", GREEN_D),
        (864, "blink.elf", "text 660", "链接 · collect2 → ld", AMBER_STROKE),
    ]
    for i, (x, name, value, step, color) in enumerate(boxes):
        f.rect(x, 184, 178, 112, color=color, fill=WHITE, sw=2.4)
        f.text(x + 89, 219, name, size=20, color=color, anchor="middle", weight="bold")
        f.text(x + 89, 250, value, size=19, color=INK, anchor="middle")
        f.text(x + 89, 280, step, size=14, color=MUTED, anchor="middle")
        if i < len(boxes) - 1:
            f.arrow(x + 180, 240, x + 196, 240, color=color, bend=0, head=8)

    f.text(72, 344, "四步各留下什么", size=22, color=BLUE_D, weight="bold")
    cards = [
        (72, ".i", ["宏已摊平", "# 行号指向原文", "仍是 C 源码"], BLUE_D),
        (323, ".s", ["目标架构汇编", "读-改-写看得见", "地址进字面池"], GREEN_D),
        (574, ".o", ["可重定位目标", "地址栏是 0", "nm 看 U/T/W"], GREEN_D),
        (825, ".elf", ["VMA 0x08000188", "readelf 看节", "size 看三列"], AMBER_STROKE),
    ]
    for x, name, lines, color in cards:
        f.rect(x, 365, 231, 124, color=color, fill=WHITE, sw=2.2)
        f.text(x + 18, 395, name, size=20, color=color, weight="bold")
        f.multi(x + 18, 424, lines, size=15, color=INK, lh=22)

    f.rect(72, 520, 482, 74, color=GREEN_D, fill=WHITE, sw=2.2)
    f.text(92, 548, "text 660 = 392（向量表）+ 268（代码）", size=17,
           color=GREEN_D, weight="bold")
    f.text(92, 576, "objcopy -O binary 之后，bin 也是 660 B", size=16, color=INK)
    f.rect(598, 520, 482, 74, color=AMBER_STROKE, fill=WHITE, sw=2.2)
    f.text(618, 548, "ELF 文件 34,604 B", size=17, color=AMBER_STROKE, weight="bold")
    f.text(618, 576, "33,944 B 是调试信息与符号表", size=16, color=INK)

    f.text(72, 630, "三个容易读错的数", size=20, color=RED, weight="bold")
    f.multi(72, 660, [
        "① 65 → 1575 行：多出来的是头文件与宏，不是代码膨胀。",
        "② .o 的地址栏 00000000：可重定位，不是最终运行地址。",
        "③ 入口 0x8000189：最低位 1 是 Thumb 状态位，不是错位。",
    ], size=16, color=INK, lh=26)
    f.htext(72, 738, "读固件大部分靠 binutils：nm / objdump / readelf / size。",
            size=18, color=INK, weight="bold", hl=True)
    return f


def v0_vma_lma():
    f = Fig("v0-06-vma-lma", "门牌与行李：VMA、LMA 和一个 128 MB 的洞")
    f.text(72, 140, ".data 运行时住 RAM（VMA），初值寄存在 Flash（LMA）；LOADADDR(.data) 取的是 LMA。",
           size=19, color=MUTED)

    for x, name, addr, color in [
        (72, "Flash 1 MB", "0x08000000", BLUE_D),
        (426, "SRAM 128 KB", "0x20000000", GREEN_D),
        (780, "CCM 64 KB", "0x10000000", AMBER_STROKE),
    ]:
        f.rect(x, 178, 300, 44, color=color, fill=WHITE, sw=2.0, double=False)
        f.text(x + 150, 207, name, size=17, color=color, anchor="middle", weight="bold")
        f.text(x + 150, 232, addr, size=14, color=MUTED, anchor="middle")

    # ---- ① 正常 .data ----
    f.text(72, 286, "① 正常：>RAM AT> FLASH", size=22, color=GREEN_D, weight="bold")
    f.rect(72, 312, 210, 82, color=AMBER_STROKE, fill=WHITE, sw=2.2)
    f.text(92, 340, "Flash · 初值", size=17, color=AMBER_STROKE, weight="bold")
    f.text(92, 365, "g_live = 4 B", size=16, color=INK)
    f.text(92, 386, "LMA 0x08000218", size=14, color=MUTED)
    f.rect(340, 312, 210, 82, color=GREEN_D, fill=WHITE, sw=2.2)
    f.text(360, 340, "RAM · 运行值", size=17, color=GREEN_D, weight="bold")
    f.text(360, 365, "g_live", size=16, color=INK)
    f.text(360, 386, "VMA 0x20000000", size=14, color=MUTED)
    f.arrow(284, 353, 336, 353, color=GREEN_D, bend=0)
    f.text(310, 344, "搬 4 B", size=14, color=GREEN_D, anchor="middle")
    f.multi(72, 424, ["PhysAddr=0x08000218  VirtAddr=0x20000000",
                      "FileSiz=0x4  MemSiz=0x1008",
                      "4104 − 4 = 4100 B → 启动清 .bss"], size=15, color=INK, lh=23)

    # ---- ② 漏写 AT> FLASH ----
    f.text(72, 512, "② 漏写 AT> FLASH：LMA 塌进 RAM", size=22, color=RED, weight="bold")
    f.rect(72, 538, 210, 88, color=MUTED, fill=WHITE, sw=2.0, dash="7 6", double=False)
    f.text(92, 566, "Flash 里的初值还在", size=15, color=MUTED)
    f.text(92, 592, "但没人来取", size=15, color=RED)
    f.rect(340, 538, 210, 88, color=RED, fill=WHITE, sw=2.2)
    f.text(360, 566, "VMA = LMA", size=17, color=RED, weight="bold")
    f.text(360, 592, "0x20000000", size=15, color=INK)
    f.text(360, 616, "_sidata == _sdata", size=14, color=RED, weight="bold")
    f.text(72, 654, "启动循环把 _sdata 拷到 _sdata：0 B 搬运", size=18, color=RED, weight="bold")
    f.text(72, 680, "判据：nm 里 _sidata 必须落在 0x0800xxxx，且 ≠ _sdata", size=15, color=INK)

    # ---- ③ CCM 空洞 ----
    f.text(600, 286, "③ CCM：漏一个词，bin 涨到 128 MB", size=21, color=AMBER_STROKE, weight="bold")
    f.text(600, 316, "0x08000000", size=14, color=MUTED)
    f.text(1050, 316, "0x10000000", size=14, color=MUTED, anchor="end")
    f.rect(600, 328, 24, 54, color=GREEN_D, fill=WHITE, sw=2.0, double=False)
    f.rect(628, 328, 422, 54, color=RED, fill=WHITE, sw=2.0, dash="7 6", double=False)
    f.text(839, 361, "objcopy 补零：134,217,728 B 空洞", size=16, color=RED, anchor="middle")
    f.text(600, 414, "+ 16 B 初值 = 134,217,744 B", size=18, color=RED, weight="bold")
    f.text(600, 442, "660 B 固件 → 128 MB bin", size=16, color=INK)
    f.rect(600, 474, 480, 92, color=GREEN_D, fill=WHITE, sw=2.2)
    f.text(620, 502, "补上 >CCM AT> FLASH", size=17, color=GREEN_D, weight="bold")
    f.text(620, 528, "LMA 回到 Flash，0x0800022c 紧贴 .text", size=15, color=INK)
    f.text(620, 552, "bin 收回 576 B", size=15, color=INK)
    f.text(600, 602, "只写 >CCM：LMA 跟着 VMA 走；补 AT> FLASH：PhysAddr 回 0x0800xxxx",
           size=14.5, color=MUTED)
    f.text(600, 630, "图纸对了，启动文件不搬，CCM 初值仍是随机值。", size=15, color=RED)

    f.htext(72, 700, "VMA 给 CPU 的 ldr 看；LMA 给装载器与 objcopy 看。两者相等，搬运循环就空转。",
            size=19, color=INK, weight="bold", hl=True)
    f.text(72, 738, "KEEP 管向量表生死；AT> FLASH 管 .data 的行李。", size=16, color=MUTED)
    return f


def v0_build_map():
    f = Fig("v0-07-build-map", "同一判读法：先看依赖边，再看寄存器位")
    f.text(72, 140, "Make 图上的边决定谁重来；SPL 把时钟、结构体字段与位掩码翻译成寄存器写。",
           size=19, color=MUTED)

    # ---- ① Make 依赖图 ----
    f.text(72, 186, "① Make：变化沿边传播", size=21, color=BLUE_D, weight="bold")
    nodes = [
        (72, 210, 130, "main.c", BLUE_D),
        (222, 210, 160, "stm32f407.h", RED),
        (402, 210, 130, "startup.s", BLUE_D),
        (552, 210, 130, "linker.ld", BLUE_D),
        (72, 286, 130, "main.o", AMBER_STROKE),
        (402, 286, 130, "startup.o", BLUE_D),
        (682, 286, 150, "blink.elf", AMBER_STROKE),
        (872, 286, 96, "blink.bin", AMBER_STROKE),
        (988, 286, 92, "blink.hex", BLUE_D),
    ]
    # 边先画、节点后画：白底节点会遮住穿框的线，箭头仍停在框边
    f.arrow(137, 254, 137, 284, color=AMBER_STROKE, bend=0, head=8)
    f.arrow(467, 254, 467, 284, color=BLUE_D, bend=0, head=8)
    f.arrow(202, 300, 680, 300, color=AMBER_STROKE, bend=0, head=8)
    f.arrow(532, 316, 680, 316, color=BLUE_D, bend=0, head=8)
    f.arrow(617, 254, 755, 284, color=BLUE_D, bend=0, head=8)
    f.arrow(832, 300, 870, 300, color=AMBER_STROKE, bend=0, head=8)
    f.arrow(832, 316, 986, 316, color=BLUE_D, bend=0, head=8)
    f.line(302, 254, 137, 284, color=RED, sw=2.0, dash="6 5")
    for x, y, w, name, color in nodes:
        dash = "7 6" if name == "stm32f407.h" else None
        f.rect(x, y, w, 44, color=color, fill=PAPER, sw=2.2, double=False, dash=dash)
        f.text(x + w / 2, y + 29, name, size=15 if w >= 120 else 13,
               color=color, anchor="middle", weight="bold")
    f.text(72, 374, "缺的边：main.o 只依赖 main.c，不依赖 stm32f407.h", size=16, color=RED, weight="bold")
    f.text(72, 398, "补法：CFLAGS += -MMD -MP；-include $(OBJS:.o=.d)", size=15, color=INK)

    # ---- ② CMake / IDF / scons ----
    f.text(72, 438, "② CMake / IDF / scons：都是先生成再构建", size=21, color=GREEN_D, weight="bold")
    cards = [
        (72, "CMake", ["cmake -B build", "make -C build", "工具链文件在 project() 前"], BLUE_D),
        (414, "ESP-IDF", ["idf_component_register", "idf.py build", "Kconfig → sdkconfig"], GREEN_D),
        (756, "RT-Thread", ["SConscript", "scons / scons -j4", "Kconfig → .config"], AMBER_STROKE),
    ]
    for x, name, lines, color in cards:
        f.rect(x, 458, 310, 100, color=color, fill=WHITE, sw=2.2)
        f.text(x + 18, 487, name, size=18, color=color, weight="bold")
        f.multi(x + 18, 514, lines, size=15, color=INK, lh=20)
    f.text(72, 584, "Kconfig 与构建系统正交：一个管“怎么编”，一个管“编什么”。", size=15, color=MUTED)

    # ---- ③ SPL ----
    f.text(72, 620, "③ SPL：时钟 → 默认值 → 字段 → GPIO_Init → 位段", size=21, color=AMBER_STROKE, weight="bold")
    steps = [
        (72, "开时钟", "RCC_APB2PeriphClockCmd", BLUE_D),
        (272, "默认值", "GPIO_StructInit", GREEN_D),
        (472, "覆盖字段", "io.Pin / Mode / Speed", GREEN_D),
        (672, "GPIO_Init", "逐 pin 循环", AMBER_STROKE),
        (872, "写寄存器", "MODER / OTYPER\nOSPEEDR / PUPDR", RED),
    ]
    for i, (x, name, detail, color) in enumerate(steps):
        f.rect(x, 640, 180, 70, color=color, fill=WHITE, sw=2.2)
        f.text(x + 90, 666, name, size=17, color=color, anchor="middle", weight="bold")
        f.multi(x + 90, 689, detail.split("\n"), size=12.5, color=INK, anchor="middle", lh=16)
        if i < 4:
            f.arrow(x + 182, 675, x + 196, 675, color=color, bend=0, head=7)
    f.text(72, 730, "枚举值 = 位段值：Mode 0/1/2/3 左移 pinpos*2；OTYPER 移 pinpos。",
           size=14.5, color=INK)
    f.text(72, 754, "图上的边决定谁重来；寄存器里的位决定谁生效。", size=15, color=RED, weight="bold")
    return f


def v6_evidence_ladder():
    f = Fig("v6-40-evidence-ladder", "读数的来路，比读数本身更重要")
    f.text(72, 140, "四级证据标签 + 四类仪器判据；本章没有板级实测，所有 lab 仍是待执行。",
           size=19, color=MUTED)

    f.text(72, 188, "① 四级证据", size=22, color=BLUE_D, weight="bold")
    levels = [
        ("实测记录", "日期 · 板子 · 手段 · 原始日志", "换人可复现", GREEN_D),
        ("来源说法（未复核）", "引用时保留“未复核”", "不写成结论", AMBER_STROKE),
        ("文档推导", "给出算式或文档落点", "可复算", BLUE_D),
        ("未实测", "保留“待执行 / 待实测”", "不改写成结论", RED),
    ]
    for i, (name, line1, line2, color) in enumerate(levels):
        y = 212 + i * 104
        f.rect(72, y, 350, 90, color=color, fill=WHITE, sw=2.2)
        f.text(92, y + 29, name, size=18, color=color, weight="bold")
        f.text(92, y + 55, line1, size=15, color=INK)
        f.text(92, y + 78, line2, size=14, color=MUTED)
        if i < 3:
            f.arrow(247, y + 90, 247, y + 102, color=MUTED, bend=0, head=7)
    f.text(72, 646, "一条数字进书前先过这四级；这个动作比任何仪器都便宜。",
           size=16, color=MUTED)

    f.text(480, 188, "② 四类仪器：判据与坑", size=22, color=GREEN_D, weight="bold")
    instruments = [
        (480, 212, "万用表", ["mA 档起步", "µA 档先断电换孔", "表本身也有压降"], BLUE_D),
        (780, 212, "示波器", ["探头 ×1/×10 一致", "先算 CCR/(ARR+1)", "地线过长会振铃"], GREEN_D),
        (480, 380, "逻辑分析仪", ["采样率 ≥10× 目标", "400 kHz → ≥4 MHz", "下降沿 = 起始位"], AMBER_STROKE),
        (780, 380, "秒表", ["数 10 个周期取平均", "只回答数量级", "别把粗测当精测"], RED),
    ]
    for x, y, name, lines, color in instruments:
        f.rect(x, y, 280, 144, color=color, fill=WHITE, sw=2.2)
        f.text(x + 18, y + 32, name, size=18, color=color, weight="bold")
        f.multi(x + 18, y + 64, lines, size=15, color=INK, lh=24)

    f.text(480, 548, "仿真只证明 ELF 与当前模型配合；真板再验供电、引脚、波形、时钟、功耗。",
           size=15, color=INK)
    f.rect(480, 578, 580, 104, color=GREEN_D, fill=WHITE, sw=2.2)
    f.text(500, 606, "三句话收尾", size=17, color=GREEN_D, weight="bold")
    f.multi(500, 634, ["仿真证明了什么 / 真板新增证明了什么 / 还有什么没证明",
                       "四道门：构建 → 模型 → 目标板 → 验收"], size=15, color=INK, lh=24)

    f.htext(72, 720, "先押注，再测量，最后对账；差异处就是学习发生的地方。",
            size=20, color=INK, weight="bold", hl=True)
    return f


def v6_logger_budget():
    f = Fig("v6-41-logger-budget", "64 B 只是载荷：74 B 上线，1120 B 进队列")
    f.text(72, 140, "SAMPLE 全小端；protocol_encode 加 6 B 头、2 B CRC、COBS 与 0x00 分隔；队列满则丢新并计数。",
           size=18, color=MUTED)

    # ---- ① 64 B payload ----
    f.text(72, 186, "① SAMPLE 载荷 = 64 B", size=21, color=BLUE_D, weight="bold")
    x0, scale, y0 = 72, 1008 / 64, 210
    parts = [
        ("seq", 4, BLUE_D), ("time", 4, BLUE_D), ("gen", 4, BLUE_D),
        ("type", 1, AMBER_STROKE), ("valid", 1, AMBER_STROKE), ("status", 2, GREEN_D),
        ("raw[6] i32", 24, GREEN_D), ("filtered[6] i32", 24, BLUE_D),
    ]
    x = x0
    for name, size_b, color in parts:
        w = size_b * scale
        f.rect(x, y0, w, 62, color=color, fill=WHITE, sw=2.0, double=False)
        if size_b >= 24:
            f.text(x + w / 2, y0 + 38, f"{name} · {size_b} B", size=16,
                   color=color, anchor="middle", weight="bold")
        x += w
    f.text(72, 302, "4+4+4+1+1+2+24+24 = 64 B", size=18, color=BLUE_D, weight="bold")

    # ---- ② 74 B wire frame ----
    f.text(72, 344, "② 线上帧 = 74 B", size=21, color=GREEN_D, weight="bold")
    f.text(72, 372, "64 B payload + 6 B 头 + 2 B CRC + 1 B COBS + 1 B 0x00",
           size=16, color=INK)
    x0, scale, y0 = 72, 1008 / 74, 392
    wire = [("64 B payload", 64, BLUE_D), ("6 B 头", 6, GREEN_D),
            ("2 B CRC", 2, AMBER_STROKE), ("COBS 1", 1, RED), ("0x00 1", 1, RED)]
    x = x0
    for name, size_b, color in wire:
        w = size_b * scale
        f.rect(x, y0, w, 62, color=color, fill=WHITE, sw=2.0, double=False)
        if size_b == 64:
            f.text(x + w / 2, y0 + 38, name, size=16, color=color,
                   anchor="middle", weight="bold")
        x += w
    f.text(72, 486, "64 + 6 + 2 + 1 + 1 = 74 B；别把 64 B 当帧长。",
           size=18, color=GREEN_D, weight="bold")

    # ---- ③ 16-slot queue ----
    f.text(72, 528, "③ 16 槽队列：载荷 1 KiB，数组 1120 B", size=21,
           color=AMBER_STROKE, weight="bold")
    f.text(72, 556, "frame_t = type / seq / len + 64 B payload = 70 B", size=16, color=INK)
    slot_x, slot_w, gap, slot_y = 72, 54, 8, 576
    for i in range(16):
        color = GREEN_D if i < 15 else RED
        f.rect(slot_x + i * (slot_w + gap), slot_y, slot_w, 54,
               color=color, fill=WHITE, sw=2.0, double=False)
    f.text(72, 660, "16 × 64 B = 1 KiB 载荷；16 × 70 B = 1120 B 数组；100 ms 采样 → 1.6 s 突发。",
           size=16, color=INK, weight="bold")
    f.text(820, 660, "满则丢新 + dropped 计数", size=15, color=RED)

    f.rect(72, 692, 1008, 44, color=BLUE_D, fill=WHITE, sw=2.2, double=False)
    f.text(92, 720, "期限监督：now − last_ms[id] ≥ deadline_ms[id] · 采样 2500 ms · 通信 1500 ms · 宽限 3000 ms",
           size=15, color=INK)
    return f


def v6_acceptance_four():
    f = Fig("v6-42-acceptance-four", "四问先填，六项预算先算，交付才有证据")
    f.text(72, 140, "交付不是“灯亮过”；别人能复现、你能说出还没做的部分，才算做完。",
           size=19, color=MUTED)

    f.text(72, 184, "① 四问验收栏", size=22, color=BLUE_D, weight="bold")
    cards = [
        (72, "输入怎么测", ["仪器 / 判据", "拿什么量", "什么算过"], BLUE_D),
        (324, "状态怎么记录", ["日志 / 遥测", "指示灯语义", "写清楚"], GREEN_D),
        (576, "输出怎么验收", ["谁判定 / 阈值", "谁冻结", "测前写死"], AMBER_STROKE),
        (828, "失败后怎么恢复", ["复位 / 回滚", "降级", "先写恢复路径"], RED),
    ]
    for x, name, lines, color in cards:
        f.rect(x, 206, 240, 132, color=color, fill=WHITE, sw=2.2)
        f.text(x + 18, 238, name, size=17, color=color, weight="bold")
        f.multi(x + 18, 268, lines, size=15, color=INK, lh=22)
    f.text(72, 362, "填不出来，说明还没到动工的时候，先补设计。", size=16, color=MUTED)

    f.text(72, 404, "② 六项预算：每项都要有算式", size=21, color=AMBER_STROKE, weight="bold")
    budgets = [
        (72, "Flash", "text + data", BLUE_D),
        (414, "RAM", "data + bss", GREEN_D),
        (756, "最坏响应", "算式：____", AMBER_STROKE),
        (72, "平均电流", "算式：____", BLUE_D),
        (414, "带宽", "算式：____", GREEN_D),
        (756, "队列峰值", "16 × 70 B = 1120 B", AMBER_STROKE),
    ]
    for i, (x, name, formula, color) in enumerate(budgets):
        y = 426 + (i // 3) * 58
        f.rect(x, y, 300, 46, color=color, fill=WHITE, sw=2.0, double=False)
        f.text(x + 16, y + 29, name, size=16, color=color, weight="bold")
        f.text(x + 284, y + 29, formula, size=14, color=INK, anchor="end")
    f.text(72, 542, "任何一项超了：先缩功能或换目标芯片，不动阈值。", size=16, color=RED, weight="bold")
    f.text(72, 568, "五处“待纠正草图”声明随代码同页；不能直接烧录。", size=15, color=RED)

    f.rect(72, 596, 600, 118, color=GREEN_D, fill=WHITE, sw=2.2)
    f.text(92, 624, "交付包五件", size=17, color=GREEN_D, weight="bold")
    f.multi(92, 650, [
        "① 干净环境重建脚本   ② ELF + map",
        "③ 配置（版本 / hash / 记录）",
        "④ 接线图与验收记录   ⑤ 已知限制与恢复步骤",
    ], size=14.5, color=INK, lh=22)
    f.rect(700, 596, 380, 118, color=AMBER_STROKE, fill=WHITE, sw=2.2)
    f.text(720, 624, "每轮两行", size=17, color=AMBER_STROKE, weight="bold")
    f.multi(720, 650, ["这轮证明了什么", "还没证明什么",
                       "三岔口：贪多 / 跳步 / 无证据"], size=14.5, color=INK, lh=22)

    f.htext(72, 750, "交付的定义：别人能复现，你能说出还没做的部分。",
            size=19, color=INK, weight="bold", hl=True)
    return f


FIGS = {
    "v0-04-call-frame": v0_call_frame,
    "v0-05-four-steps": v0_four_steps,
    "v0-06-vma-lma": v0_vma_lma,
    "v0-07-build-map": v0_build_map,
    "v6-40-evidence-ladder": v6_evidence_ladder,
    "v6-41-logger-budget": v6_logger_budget,
    "v6-42-acceptance-four": v6_acceptance_four,
}


if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        fig = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(fig, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))
