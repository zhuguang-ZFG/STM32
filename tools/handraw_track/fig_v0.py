# -*- coding: utf-8 -*-
"""Knowledge-track plates for ch01-ch03 (L0 起步).

Every number and label is copied from the chapter it belongs to; the plates
are explanatory diagrams, not measurements or board photos. Deterministic:
same code -> same SVG bytes -> same PNG pixels.
"""
from pathlib import Path

from hd import (AMBER_PALE, AMBER_STROKE, BLUE_D, BLUE_FILL, GRAY_FILL,
                GREEN_D, GREEN_FILL, INK, MUTED, RED, RED_FILL, WHITE, Fig,
                save)

STAGE = Path(__file__).resolve().parents[2] / ".temp" / "l0-l5-pass" / "figures"
MONO = "'Consolas','Courier New',monospace"


def ch01_memory_two_addresses():
    """Flash holds the .data backup; RAM holds the runtime copy."""
    f = Fig("ch01-memory-two-addresses",
            "一个变量，两个地址：Flash 备份与 RAM 本体",
            title_color=BLUE_D, tag="CH 01 · 启动与内存")
    f.text(64, 126,
           ".data 的初值备份烧在 Flash，运行时本体住 RAM；上电后由 Reset_Handler 逐字搬过去。",
           size=19, color=MUTED)

    # ---- Flash warehouse ----
    f.card(64, 160, 500, 340, BLUE_D, fill=BLUE_FILL)
    f.text(84, 194, "Flash 仓库 · 0x08000000", size=21, color=BLUE_D,
           weight="bold")
    f.text(84, 220, "烧录时只带 .data 的初值备份", size=14, color=MUTED)
    f.pill(84, 234, 460, 36, "0x08000000 · .isr_vector · 392 B", BLUE_D,
           fill=WHITE, size=15)
    f.text(84, 296, "0x080002a0 · LMA · 文件里真有的 12 B", size=15,
           color=AMBER_STROKE, weight="bold")
    bytes12 = ["05", "00", "00", "00",
               "01", "00", "00", "00",
               "68", "69", "00", "00"]
    for i, b in enumerate(bytes12):
        x = 84 + i * 38
        color = GREEN_D if i < 4 else (AMBER_STROKE if i < 8 else BLUE_D)
        f.rect(x, 308, 38, 50, color=color, fill=WHITE, sw=1.8, double=False)
        f.text(x + 19, 341, b, size=15, color=INK, anchor="middle", font=MONO)
    for cx, label in ((160, "g_init = 5"), (312, "g_flag = 1"),
                      (464, 'g_msg = "hi"')):
        f.text(cx, 378, label, size=14, color=INK, anchor="middle")
    f.text(84, 406, "FileSiz 0x0000c：备份 12 B 随固件烧进 Flash", size=14,
           color=INK)
    f.text(84, 430, ".bss 初值全 0，文件里不占字节（NOBITS）", size=14,
           color=MUTED)
    f.text(84, 462, "上电后谁搬？看下面的搬运条。", size=14, color=GREEN_D,
           weight="bold")
    f.text(84, 486, "改链接脚本或换芯片，LMA 与大小都会变。", size=13,
           color=MUTED)

    # ---- RAM residence ----
    f.card(588, 160, 500, 340, GREEN_D, fill=GREEN_FILL)
    f.text(608, 194, "RAM 住所 · 0x20000000", size=21, color=GREEN_D,
           weight="bold")
    f.text(608, 220, "运行时本体住这里；地址向上增大 ↑", size=14, color=MUTED)
    f.text(608, 242, "0x20020000 · _estack（RAM 顶）", size=13, color=MUTED)
    f.rect(608, 250, 460, 48, color=RED, fill=RED_FILL, sw=2.0, double=False)
    f.text(624, 272, "栈：最小 1 KB（_Min_Stack_Size = 0x400）", size=15,
           color=RED, weight="bold")
    f.text(624, 290, "向下长 ↓", size=13, color=RED)
    f.rect(608, 306, 460, 32, color=MUTED, fill=WHITE, sw=1.8, dash="7 6",
           double=False)
    f.text(838, 328, "堆与栈尚未碰面的空地", size=14, color=MUTED,
           anchor="middle")
    f.rect(608, 346, 460, 48, color=AMBER_STROKE, fill=AMBER_PALE, sw=2.0,
           double=False)
    f.text(624, 368, "堆：最小 512 B（_Min_Heap_Size = 0x200）", size=15,
           color=AMBER_STROKE, weight="bold")
    f.text(624, 386, "从 _ebss 之后向上长 ↑", size=13, color=AMBER_STROKE)
    f.rect(608, 402, 460, 32, color=AMBER_STROKE, fill=WHITE, sw=2.0,
           double=False)
    f.text(624, 424, ".bss 32 B：启动时清零（文件里 0 B）", size=14, color=INK)
    f.rect(608, 442, 460, 32, color=GREEN_D, fill=WHITE, sw=2.0, double=False)
    f.text(624, 464, '.data 12 B：g_init / g_flag / g_msg="hi"', size=14,
           color=INK)
    f.text(608, 490, "0x20000000 · 0x2000000c · 0x2000002c", size=12.5,
           color=MUTED)

    # ---- the mover ----
    f.card(64, 516, 1024, 56, AMBER_STROKE, fill=AMBER_PALE)
    f.arrow(88, 544, 148, 544, color=AMBER_STROKE, sw=2.6, bend=0.0, head=9)
    f.text(168, 551,
           "上电后 Reset_Handler 逐字读 Flash、写 RAM；.bss 另行清零，不搬。",
           size=17, color=INK, weight="bold")

    # ---- readelf ledger ----
    f.card(64, 588, 1024, 110, BLUE_D, fill=WHITE)
    f.text(84, 618,
           "readelf 第二条 LOAD：VirtAddr 0x20000000（RAM） / "
           "PhysAddr 0x080002a0（Flash）", size=15, color=INK)
    f.text(84, 646,
           "FileSiz 0x0000c（12 B） < MemSiz 0x00002c（44 B：.data 12 + .bss 32）",
           size=15, color=INK)
    f.text(84, 674,
           "判读形状：VMA 落 0x2000xxxx，LMA 落 0x0800xxxx，文件里的货比 RAM 里少。",
           size=14, color=MUTED)

    f.htext(576, 730,
            "烧录文件只带初值备份；RAM 里的 5，要等 Reset_Handler 搬完才可信。",
            size=22, color=INK, weight="bold", anchor="middle", hl=True)
    f.text(576, 762,
           "数字取自本章 mem_probe.elf 与 readelf 输出；布局示意，非实测。",
           size=15, color=MUTED, anchor="middle")
    return f


def ch02_volatile_contract():
    """Three optimizer moves, the volatile withdrawal, and CMSIS types."""
    f = Fig("ch02-volatile-contract",
            "编译器看不见的写：volatile 的合同",
            title_color=GREEN_D, tag="CH 02 · volatile 与寄存器")
    f.text(64, 126,
           "优化器按 as-if 删改普通内存；硬件寄存器在程序之外改变，合同要写进类型。",
           size=19, color=MUTED)

    f.text(64, 172, "① 优化器的三项授权（对硬件寄存器都是错的）", size=20,
           color=BLUE_D, weight="bold")
    cards = [
        (64, "缓存", "多次读合成一次",
         ["poll_plain：整函数只读一次", "循环变成 .L3: b .L3 死转"],
         BLUE_D, BLUE_FILL, "copy"),
        (410, "删除", "写了没人再读的赋值",
         ["delay_plain：-O2 只剩 ret / bx lr", "一千圈延时在产物里没有存在过"],
         GREEN_D, GREEN_FILL, "trash"),
        (756, "合并", "连续两次置位合成一次",
         ["cfg_plain：三次读-改-写", "并成一次 orr #7"],
         AMBER_STROKE, AMBER_PALE, "merge"),
    ]
    for x, name, sub, lines, color, fill, icon in cards:
        f.card(x, 188, 324, 150, color, fill=fill)
        f.text(x + 20, 222, name, size=22, color=color, weight="bold")
        f.text(x + 20, 248, sub, size=14, color=MUTED)
        f.multi(x + 20, 282, lines, size=14, color=INK, lh=24)
        if icon == "copy":
            f.icon_copy(x + 266, 204, 40, color)
        elif icon == "trash":
            f.icon_trash(x + 266, 204, 40, color)
        else:
            f.icon_merge(x + 266, 204, 40, color)

    f.text(64, 372, "② volatile 只收回这三项授权，不保证原子", size=20,
           color=GREEN_D, weight="bold")
    f.card(64, 388, 620, 160, GREEN_D, fill=GREEN_FILL)
    f.multi(84, 420, [
        "每次使用都必须真实访存：不许缓存、不许删、不许凭空造。",
        "poll_volatile：循环回到每圈一条 ldr r3, [r2, #4]。",
    ], size=15, color=INK, lh=27)
    f.text(84, 492,
           "读-改-写三步仍可被中断打断：isr_toggle 三条指令、两个间隙。",
           size=14, color=RED, weight="bold")
    f.text(84, 522, "要原子性：临界区、BSRR 一类外设侧原子入口，或内存屏障。",
           size=13.5, color=MUTED)

    f.card(704, 388, 384, 160, RED, fill=RED_FILL)
    f.text(724, 418, "三次写被折叠", size=17, color=RED, weight="bold")
    f.text(724, 446, "普通结构体：", size=13.5, color=MUTED)
    f.text(724, 470, "ldr / orr #7 / str", size=15, color=INK, font=MONO)
    f.text(724, 498, "字段带 __IO：三组 ldr/orr/str", size=14, color=GREEN_D,
           weight="bold")
    f.text(724, 526, "硬件要三个动作，少发就不生效。", size=13, color=MUTED)

    f.text(64, 572, "③ CMSIS 用类型写合同：__I / __O / __IO", size=20,
           color=AMBER_STROKE, weight="bold")
    types = [
        (64, "__I", "volatile const", "程序只读，硬件随时可能改",
         BLUE_D, BLUE_FILL),
        (410, "__O", "volatile", "只写，语义上强调写", GREEN_D, GREEN_FILL),
        (756, "__IO", "volatile", "读和写都可能被硬件改变",
         AMBER_STROKE, AMBER_PALE),
    ]
    for x, name, expands, meaning, color, fill in types:
        f.card(x, 588, 324, 96, color, fill=fill)
        f.text(x + 20, 622, name, size=21, color=color, weight="bold",
               font=MONO)
        f.text(x + 92, 620, expands, size=14.5, color=INK, font=MONO)
        f.text(x + 20, 656, meaning, size=13.5, color=MUTED)

    f.text(64, 708,
           "GPIO_TypeDef 整组寄存器用 __IO；只读的 IDR / SR 用 const volatile。",
           size=15, color=INK)
    f.htext(576, 740,
            "volatile 改的是访问方式，不改段归属、地址，也不改原子性。",
            size=20, color=INK, weight="bold", anchor="middle", hl=True)
    f.text(576, 768,
           "汇编对照取自本章 -O0 / -O2 产物；布局示意，非实测。",
           size=14, color=MUTED, anchor="middle")
    return f


def ch03_struct_overlay():
    """GPIO_TypeDef offsets over the register block, plus padding."""
    f = Fig("ch03-struct-overlay",
            "结构体罩住寄存器块：偏移、对齐与填充",
            title_color=BLUE_D, tag="CH 03 · 寄存器与结构体")
    f.text(64, 126,
           "GPIOF_BASE = 0x40021400；声明顺序即偏移顺序，BSRR 在 0x18，整个结构体 0x28。",
           size=19, color=MUTED)

    f.text(64, 170, "① 寄存器地图 → 结构体偏移", size=20, color=BLUE_D,
           weight="bold")
    regs = [
        ("MODER", "0x00", 80), ("OTYPER", "0x04", 80), ("OSPEEDR", "0x08", 80),
        ("PUPDR", "0x0C", 80), ("IDR", "0x10", 80), ("ODR", "0x14", 80),
        ("BSRR", "0x18", 80), ("LCKR", "0x1C", 80), ("AFR[2]", "0x20-0x24", 160),
    ]
    x = 64
    for name, off, w in regs:
        color = AMBER_STROKE if name == "BSRR" else BLUE_D
        fill = AMBER_PALE if name == "BSRR" else WHITE
        f.rect(x, 186, w, 56, color=color, fill=fill, sw=2.0, double=False)
        f.text(x + w / 2, 210, name, size=14 if w > 80 else 13,
               color=INK, anchor="middle", weight="bold")
        f.text(x + w / 2, 232, off, size=13, color=MUTED, anchor="middle")
        x += w

    f.card(884, 186, 204, 80, AMBER_STROKE, fill=AMBER_PALE)
    f.text(900, 212, "BSRR：第 7 格", size=15, color=AMBER_STROKE,
           weight="bold")
    f.text(900, 234, "6 × 4 B = 0x18", size=14, color=INK)
    f.text(900, 256, "sizeof = 0x28", size=14, color=INK)

    f.text(64, 296,
           "GPIOF_BASE 0x40021400 + 0x18 = 0x40021418；地址按 4 字节对齐递增。",
           size=15, color=INK)
    f.text(64, 320,
           "_Static_assert 同时钉住 offsetof(BSRR) 与 sizeof(GPIO_TypeDef)。",
           size=14, color=MUTED)

    f.text(64, 360, "② 对齐与填充：Padded_t 12 B，Packed_t 8 B", size=20,
           color=GREEN_D, weight="bold")
    f.text(64, 388, "Padded_t { uint8_t a; uint32_t b; uint8_t c; }",
           size=15, color=GREEN_D, weight="bold")
    cells = [("a", 0, GREEN_D), ("x", 1, MUTED), ("x", 2, MUTED),
             ("x", 3, MUTED), ("b", 4, BLUE_D), ("b", 5, BLUE_D),
             ("b", 6, BLUE_D), ("b", 7, BLUE_D), ("c", 8, GREEN_D),
             ("x", 9, MUTED), ("x", 10, MUTED), ("x", 11, MUTED)]
    for i, (label, off, color) in enumerate(cells):
        x = 64 + i * 60
        f.rect(x, 400, 60, 50, color=color,
               fill=AMBER_PALE if label == "x" else WHITE, sw=1.8,
               double=False)
        f.text(x + 30, 433, label, size=16, color=INK, anchor="middle",
               weight="bold", font=MONO)
        f.text(x + 30, 466, str(off), size=12, color=MUTED, anchor="middle")

    f.card(820, 388, 268, 128, GREEN_D, fill=GREEN_FILL)
    f.text(838, 416, "Padded_t", size=17, color=GREEN_D, weight="bold")
    f.multi(838, 444, ["sizeof = 12", "a@0  b@4  c@8",
                       "洞 1：a 后 3 B", "洞 2：c 后 3 B"], size=13.5,
            color=INK, lh=22)

    f.text(64, 524, "Packed_t { uint32_t b; uint8_t a; uint8_t c; }",
           size=15, color=BLUE_D, weight="bold")
    cells2 = [("b", 0), ("b", 1), ("b", 2), ("b", 3),
              ("a", 4), ("c", 5), ("x", 6), ("x", 7)]
    for i, (label, off) in enumerate(cells2):
        x = 64 + i * 60
        color = BLUE_D if label == "b" else (GREEN_D if label in "ac" else MUTED)
        f.rect(x, 536, 60, 50, color=color,
               fill=AMBER_PALE if label == "x" else WHITE, sw=1.8,
               double=False)
        f.text(x + 30, 569, label, size=16, color=INK, anchor="middle",
               weight="bold", font=MONO)
        f.text(x + 30, 602, str(off), size=12, color=MUTED, anchor="middle")

    f.card(820, 524, 268, 104, BLUE_D, fill=BLUE_FILL)
    f.text(838, 552, "Packed_t", size=17, color=BLUE_D, weight="bold")
    f.multi(838, 580, ["sizeof = 8", "b@0  a@4  c@5",
                       "省下的 4 B 来自成员顺序"], size=13.5, color=INK,
            lh=22)

    f.text(64, 652,
           "arr[1] − arr[0] = 12 B：尾部填充保证 sizeof 含在 stride 里，数组不歪。",
           size=15, color=INK)
    f.htext(576, 706,
            "偏移由声明顺序、4 字节宽度与对齐规则共同决定；位域与 pack 不进寄存器映射。",
            size=20, color=INK, weight="bold", anchor="middle", hl=True)
    f.text(576, 740,
           "偏移与 sizeof 取自本章 _Static_assert；布局示意，非实测。",
           size=14, color=MUTED, anchor="middle")
    return f


def ch01_const_ram_economics():
    """const LUT: .data 256 -> 0, .text 148 -> 404, start copies 64 words
    fewer. Numbers from ch01 lut_probe.c record."""
    f = Fig("ch01-const-ram-economics",
            "加一个 const：256 字节的表从 RAM 搬回 Flash",
            title_color=GREEN_D, tag="CH 01 · 内存模型")
    f.text(64, 126,
           "表还是那张表，只是不再要 RAM 的户口：初值本来就存 Flash，查表也直接读 Flash。",
           size=19, color=MUTED)

    # ---- left: plain LUT, lives in .data ----
    f.card(64, 156, 500, 330, BLUE_D, fill=BLUE_FILL)
    f.text(84, 190, "uint8_t lut[256] = {1,2,3};", size=19, color=BLUE_D,
           weight="bold", font=MONO)
    f.text(84, 218, "可写：住在 .data，两边各一份", size=14, color=MUTED)
    f.metric(96, 268, ".data 256", "RAM 本体 0x20000000", BLUE_D)
    f.metric(300, 268, ".text 148", "Flash 里的代码", MUTED)
    f.text(84, 322, "nm：20000000 00000100 D lut", size=14.5, color=INK,
           font=MONO)
    f.text(84, 350, "第二个 LOAD：FileSiz 0x100 · MemSiz 0x700",
           size=14.5, color=INK)
    f.text(84, 386, "启动搬运循环要多跑 64 个字", size=15, color=RED,
           weight="bold")
    f.text(84, 414, "RAM 从 256 字节起算，堆栈挤在同一个 128 KB 里",
           size=14, color=MUTED)

    # ---- right: const LUT, lives in Flash ----
    f.card(588, 156, 500, 330, GREEN_D, fill=GREEN_FILL)
    f.text(608, 190, "const uint8_t lut[256] = {1,2,3};", size=19,
           color=GREEN_D, weight="bold", font=MONO)
    f.text(608, 218, "只读：住 Flash，RAM 里查无此人", size=14, color=MUTED)
    f.metric(620, 268, ".data 0", "RAM 让出 256 字节", GREEN_D)
    f.metric(824, 268, ".text 404", "Flash 多存这份表", AMBER_STROKE)
    f.text(608, 322, "nm：0800021c 00000100 T lut", size=14.5, color=INK,
           font=MONO)
    f.text(608, 350, "第二个 LOAD：FileSiz 0x00000 · MemSiz 0x600",
           size=14.5, color=INK)
    f.text(608, 386, "启动少拷 64 个字（256÷4）", size=15, color=GREEN_D,
           weight="bold")
    f.text(608, 414, "判据是「初值是否全零/只读」，不是有没有写 =",
           size=14, color=MUTED)

    # ---- bottom: the trade, spelled out ----
    f.panel(64, 516, 1024, 120, AMBER_PALE, amp=1.6)
    f.rect(64, 516, 1024, 120, color=AMBER_STROKE, sw=1.8, fill=None,
           amp=1.6)
    f.text(96, 556, "这笔账的两半：", size=17, color=AMBER_STROKE,
           weight="bold")
    f.text(96, 588, "省下的是 RAM 那一半；Flash 那一半本来就要花——初值总得有人存。",
           size=16, color=INK)
    f.text(96, 616, "要运行时改写的表（校准补偿）不能 const：改用 RAM 工作副本，启动时从 Flash 模板拷入。",
           size=14.5, color=MUTED)

    f.htext(64, 700, "一个 const 换 256 字节 RAM；RAM 越小的型号，这笔交易越值",
            size=22, color=INK, weight="bold", hl=True)
    f.text(576, 730,
           "数字取自本章 lut_probe.c 实测记录；F407 128 KB，small 型号几十 KB。",
           size=14, color=MUTED, anchor="middle")
    return f


def ch02_ub_compiler_fuel():
    """UB gives the optimizer license: is_bigger_after_inc folds to movs
    r0,#1; 1u<<33 gives 2 (-O0) vs 0 (-O2). Facts from ch02 probe record."""
    f = Fig("ch02-ub-compiler-fuel",
            "UB：编译器拿「你不会越界」当优化燃料",
            title_color=RED, tag="CH 02 · volatile 与 UB")
    f.text(64, 126,
           "标准撒手的地方，编译器按最省指令的走法排；两个答案都对，因为题目本身没有答案。",
           size=19, color=MUTED)

    # ---- left: signed overflow folds ----
    f.card(64, 156, 520, 360, RED, fill=RED_FILL)
    f.text(84, 190, "return x + 1 > x;", size=20, color=RED, weight="bold",
           font=MONO)
    f.text(84, 216, "x = INT_MAX 那一刻加法已溢出，属于 UB", size=14,
           color=MUTED)
    f.pill(84, 236, 300, 40, "-O2：movs r0, #1", RED, fill=WHITE, size=16)
    f.text(84, 306, "推理链：你保证不喂 INT_MAX → 比较恒真 → 整段折叠",
           size=14.5, color=INK)
    f.pill(84, 324, 360, 40, "-O2 -fwrapv：mvn r3, #-2147483648", GREEN_D,
           fill=WHITE, size=15)
    f.text(84, 394, "回绕口径下编译器失去假设权，只能真算：", size=14.5,
           color=INK)
    f.text(84, 420, "INT_MAX+1 = INT_MIN，比较为假，返回 0", size=15,
           color=GREEN_D, weight="bold")
    f.text(84, 456, "-O0 也不是逐行照实执行：函数体同样只剩装载常量",
           size=14, color=MUTED)
    f.text(84, 484, "「-O0 能跑」从来不是正确性证据", size=15, color=RED,
           weight="bold")

    # ---- right: shift count changes face ----
    f.card(608, 156, 480, 360, BLUE_D, fill=BLUE_FILL)
    f.text(628, 190, "1u << 33", size=20, color=BLUE_D, weight="bold",
           font=MONO)
    f.text(628, 216, "计数 ≥ 位宽，UB——两档两个答案", size=14, color=MUTED)
    f.metric(640, 268, "-O0 → 2", "33&31=1，1u<<1", BLUE_D)
    f.metric(850, 268, "-O2 → 0", "认出 UB，任选最省", AMBER_STROKE)
    f.text(628, 322, "三条红线：计数≥位宽 · 计数为负 · 左移进符号位",
           size=15, color=INK, weight="bold")
    f.text(628, 352, "安全写法：计数编译期可证 < 32，或运行期先查再移",
           size=14.5, color=INK)
    f.text(628, 386, "-fwrapv 只救有符号加/减/乘的溢出，", size=14.5,
           color=MUTED)
    f.text(628, 412, "移位三条红线一条都不救", size=14.5, color=MUTED)
    f.text(628, 456, "掩码写 1UL 只防符号位，防不住计数越界", size=14,
           color=MUTED)
    f.text(628, 484, "gcc 16.1.0 宿主实测，交叉档同判", size=14, color=MUTED)

    # ---- bottom: what UB actually buys the optimizer ----
    f.panel(64, 540, 1024, 96, AMBER_PALE, amp=1.6)
    f.rect(64, 540, 1024, 96, color=AMBER_STROKE, sw=1.8, fill=None,
           amp=1.6)
    f.text(96, 578, "燃料换来的速度：越界检查不用生成、边界不用判断、循环不用守",
           size=16, color=INK)
    f.text(96, 608, "代价：换优化档、换编译器、加一行代码，同一个函数就换一张脸。",
           size=14.5, color=MUTED)

    f.htext(64, 700, "UB 题目本身没有标准答案——别在它上面建立任何行为假设",
            size=22, color=RED, weight="bold", hl=True)
    f.text(576, 730,
           "读数取自本章 probe.sh 宿主记录；布局示意，非实测波形。",
           size=14, color=MUTED, anchor="middle")
    return f


def ch06_boot_five_stations():
    """Boot five stations with the seven literal-pool words. Facts from
    ch06 startup section (objdump of link_probe)."""
    f = Fig("ch06-boot-five-stations",
            "启动五站：硬件两读，到最后一声 bl main",
            title_color=BLUE_D, tag="CH 06 · 链接与启动")
    f.text(64, 126,
           "链接脚本把地址条写进字面量池，启动文件照单搬运；每一站都有失败的样子。",
           size=19, color=MUTED)

    # ---- five stations: 2 rows (3 + 2) ----
    st = [
        ("1 硬件两读", "硅片硬逻辑", "0x08000000→MSP\n0x08000004→PC",
         "向量表被 gc：SP 变成机器码，第一次压栈就死", BLUE_D, BLUE_FILL),
        ("2 开 FPU", "Reset_Handler", "CPACR 0xE000ED88\nCP10/11 置 0xF<<20",
         "漏了：第一条 FPU 指令 UsageFault(NOCP)", GREEN_D, GREEN_FILL),
        ("3 搬 .data", "Reset_Handler", "_sidata→_sdata.._edata\n0x08000218→0x20000000",
         "没搬：全局变量是上电垃圾", AMBER_STROKE, AMBER_PALE),
        ("4 清 .bss", "Reset_Handler", "_sbss.._ebss 写 0\n0x20000004..0x20001008",
         "没清：未初始化全局不是 0，随板子变", AMBER_STROKE, AMBER_PALE),
        ("5 bl main", "Reset_Handler", "跳进 C 世界\n返回则 .L_hang 转圈",
         "裸机 main return = 停机，等看门狗", RED, RED_FILL),
    ]
    pos = [(64, 156), (438, 156), (812, 156), (251, 330), (625, 330)]
    for (name, who, act, fail, c, fl), (x, y) in zip(st, pos):
        f.card(x, y, 276, 156, c, fill=fl)
        f.text(x + 16, y + 32, name, size=19, color=c, weight="bold")
        f.text(x + 16, y + 54, who, size=12.5, color=MUTED)
        lines = act.split("\n")
        for j, ln in enumerate(lines):
            f.text(x + 16, y + 78 + j * 22, ln, size=13, color=INK,
                   font=MONO)
        f.text(x + 16, y + 128, fail, size=12.5, color=c, weight="bold")
    for x0, x1 in ((340, 438), (714, 812)):
        f.arrow(x0, 234, x1, 234, color=MUTED, sw=2.2, bend=0.0, head=8)
    f.arrow(527, 286, 560, 318, color=MUTED, sw=2.2, bend=0.0, head=8)
    f.arrow(901, 286, 780, 318, color=MUTED, sw=2.2, bend=0.0, head=8)

    # ---- literal pool strip: the seven address slips ----
    f.panel(64, 516, 1024, 118, GRAY_FILL, amp=1.6)
    f.rect(64, 516, 1024, 118, color=MUTED, sw=1.6, fill=None, amp=1.6)
    f.text(88, 546, "Reset_Handler 字面量池 · 七张地址条", size=15,
           color=INK, weight="bold")
    words = [("0x20020000", "_estack", BLUE_D),
             ("0xe000ed88", "CPACR", GREEN_D),
             ("0x20000000", "_sdata", AMBER_STROKE),
             ("0x20000004", "_edata", AMBER_STROKE),
             ("0x08000218", "_sidata", AMBER_STROKE),
             ("0x20000004", "_sbss", AMBER_STROKE),
             ("0x20001008", "_ebss", AMBER_STROKE)]
    for i, (w, name, c) in enumerate(words):
        x = 88 + i * 142
        f.text(x, 576, w, size=13.5, color=c, font=MONO, weight="bold")
        f.text(x, 596, name, size=12.5, color=MUTED)
    f.text(88, 622, "_sbss == _edata：清零循环从搬运循环的终点接着跑",
           size=13.5, color=INK)

    f.htext(64, 700, "站 3、4 干完，站 5 才有资格跳：三个环节缺一个，g_init 就不是 5",
            size=21, color=INK, weight="bold", hl=True)
    f.text(576, 730,
           "地址与字面量取自本章 link_probe 的 objdump 记录；流程示意，非实拍。",
           size=14, color=MUTED, anchor="middle")
    return f


def ch03_map_translation_fails():
    """Three ways to translate a register map wrong, from ch03 broken.sh:
    missing RESERVED shifts DR, AFR[2]->AFR keeps BSRR but shrinks sizeof,
    pack(1) forces b@1."""
    f = Fig("ch03-map-translation-fails",
            "地图翻译错一格：三种坏法",
            title_color=RED, tag="CH 03 · 结构体与 ABI")
    f.text(64, 126,
           "偏移是排队的：前面错一格，后面整体前移；最阴的一种是前面的偏移全对、只有 sizeof 少了 4。",
           size=19, color=MUTED)

    # ---- three broken variants ----
    f.card(64, 156, 336, 300, RED, fill=RED_FILL)
    f.text(84, 190, "① 漏一个 RESERVED", size=19, color=RED, weight="bold")
    f.text(84, 218, "地图上的空洞没人顶住", size=13.5, color=MUTED)
    f.pill(84, 236, 200, 40, "DR: 0x08 → 0x04", RED, fill=WHITE, size=15)
    f.text(84, 306, "后面每个成员整体前移", size=14.5, color=INK)
    f.text(84, 334, "写入落到隔壁寄存器", size=14.5, color=RED, weight="bold")
    f.text(84, 366, "修法：空洞补占位成员", size=14, color=MUTED)
    f.text(84, 408, "broken.sh 实测", size=13, color=MUTED)

    f.card(424, 156, 336, 300, AMBER_STROKE, fill=AMBER_PALE)
    f.text(444, 190, "② AFR[2] 写成 AFR", size=19, color=AMBER_STROKE,
           weight="bold")
    f.text(444, 218, "少写一个寄存器", size=13.5, color=MUTED)
    f.pill(444, 236, 200, 40, "BSRR 仍 = 0x18", GREEN_D, fill=WHITE,
           size=15)
    f.pill(444, 286, 200, 40, "sizeof 0x28 → 0x24", RED, fill=WHITE,
           size=15)
    f.text(444, 356, "排在 AFR 后的寄存器整体前移", size=14.5, color=INK)
    f.text(444, 384, "前面全对、后面错——最难查", size=14.5, color=RED,
           weight="bold")
    f.text(444, 408, "只断言 sizeof 或只断言偏移都会漏", size=13,
           color=MUTED)

    f.card(784, 156, 304, 300, BLUE_D, fill=BLUE_FILL)
    f.text(804, 190, "③ 加 pack(1)", size=19, color=BLUE_D, weight="bold")
    f.text(804, 218, "填充压掉，对齐破坏", size=13.5, color=MUTED)
    f.pill(804, 236, 180, 40, "sizeof = 6", RED, fill=WHITE, size=15)
    f.text(804, 306, "a@0 · b@1 · c@5", size=14.5, color=INK, font=MONO)
    f.text(804, 334, "b 落在非对齐偏移", size=14.5, color=RED,
           weight="bold")
    f.text(804, 366, "M4 上可能 UsageFault", size=14.5, color=RED,
           weight="bold")
    f.text(804, 408, "pack 只配协议帧/文件头", size=13, color=MUTED)

    # ---- four preconditions ----
    f.panel(64, 486, 1024, 110, GRAY_FILL, amp=1.6)
    f.rect(64, 486, 1024, 110, color=MUTED, sw=1.6, fill=None, amp=1.6)
    f.text(88, 518, "结构体映射可靠的四条前提", size=15.5, color=INK,
           weight="bold")
    f.text(88, 548, "① 顺序与地图逐个一致，空洞用 RESERVED 顶住",
           size=14.5, color=INK)
    f.text(88, 576, "② 宽度一致（AFR[2] 不是 AFR）", size=14.5, color=INK)
    f.text(590, 548, "③ 每个寄存器成员 volatile（CMSIS __IO）",
           size=14.5, color=INK)
    f.text(590, 576, "④ 头文件版本与芯片匹配", size=14.5, color=INK)

    f.htext(64, 700, "offsetof + sizeof + _Static_assert 三件一起上，缺一就留死角",
            size=21, color=INK, weight="bold", hl=True)
    f.text(576, 730,
           "读数取自本章 broken.sh 宿主实测；布局示意，非内存转储。",
           size=14, color=MUTED, anchor="middle")
    return f


def ch04_ring_two_schools():
    """Ring buffer full/empty verdict: A sacrifices one slot (7 usable),
    B uses monotonic index (8 usable). Facts from ch04 probe record."""
    f = Fig("ch04-ring-two-schools",
            "满/空之争：指针相等是空还是满？",
            title_color=BLUE_D, tag="CH 04 · 函数指针与状态机")
    f.text(64, 126,
           "读写指针相等，两派都叫「空」；分歧只在满——一个牺牲一格当哨兵，一个数在飞量。",
           size=19, color=MUTED)

    # ---- school A ----
    f.card(64, 156, 500, 320, AMBER_STROKE, fill=AMBER_PALE)
    f.text(84, 190, "A 派 · 牺牲一格", size=20, color=AMBER_STROKE,
           weight="bold")
    f.text(84, 216, "留一个空位当哨兵，判定直白", size=14, color=MUTED)
    f.pill(84, 234, 260, 42, "(w+1) % CAP == r → 满", AMBER_STROKE,
           fill=WHITE, size=15)
    f.metric(96, 320, "7 格", "8 格物理容量，只能用 7", AMBER_STROKE)
    f.text(84, 372, "空判定：w == r（两派相同）", size=14.5, color=INK)
    f.text(84, 400, "代价：一格永久浪费", size=14.5, color=MUTED)
    f.text(84, 432, "满写被拒路径实测触发过（n_refused > 0）", size=13.5,
           color=MUTED)

    # ---- school B ----
    f.card(588, 156, 500, 320, GREEN_D, fill=GREEN_FILL)
    f.text(608, 190, "B 派 · 单调索引", size=20, color=GREEN_D,
           weight="bold")
    f.text(608, 216, "指针不取模，在飞量判满", size=14, color=MUTED)
    f.pill(608, 234, 300, 42, "(uint8_t)(w - r) >= CAP → 满", GREEN_D,
           fill=WHITE, size=15)
    f.metric(620, 320, "8 格", "8 格物理容量全部可用", GREEN_D)
    f.text(608, 372, "无符号减法模 256：w 从 255 回绕到 0，", size=14.5,
           color=INK)
    f.text(608, 400, "在飞量依旧正确，不用写回绕判断", size=14.5, color=INK)
    f.text(608, 432, "长跑 600 步跨过 255→0：n_put == n_get", size=13.5,
           color=MUTED)

    # ---- publish order ----
    f.panel(64, 506, 1024, 92, RED_FILL, amp=1.6)
    f.rect(64, 506, 1024, 92, color=RED, sw=1.8, fill=None, amp=1.6)
    f.text(88, 538, "发布顺序：先写数据 → release 屏障 → 再发布 w；消费者 acquire 后才取数据",
           size=15.5, color=INK, weight="bold")
    f.text(88, 568, "顺序反了就是「读到空槽」的经典 bug——中断生产、主循环消费的正确性全押在这条序上",
           size=14, color=MUTED)

    f.htext(64, 700, "单生产单消费才有这些免费判定；双端都写就得加临界区",
            size=21, color=INK, weight="bold", hl=True)
    f.text(576, 730,
           "读数取自本章 probe.sh 断言记录（560/560）；机制示意，非实测波形。",
           size=14, color=MUTED, anchor="middle")
    return f


def ch07_spl_minimum_loop():
    """SPL minimum blinking loop: five files, two macros, one non-weak
    SysTick_Handler trap. Facts from ch07 (frozen SPL V3.5.0 build)."""
    f = Fig("ch07-spl-minimum-loop",
            "SPL 最小闭环：少一个文件就是链接错",
            title_color=GREEN_D, tag="CH 07 · 构建与遗留栈")
    f.text(64, 126,
           "F103C8 点灯要成套：五类文件、两个宏，缺一样现象各不相同；链接通过只证明接口闭合。",
           size=19, color=MUTED)

    # ---- left: five files ----
    f.card(64, 156, 500, 310, BLUE_D, fill=BLUE_FILL)
    f.text(84, 190, "五类文件，成套出现", size=19, color=BLUE_D,
           weight="bold")
    files = [("CMSIS 设备头", "寄存器与内核定义"),
             ("system_stm32f10x.c", "时钟假设要和晶振一致"),
             ("启动文件（medium-density）", "向量表与堆栈初值"),
             ("链接脚本 F103C8", "Flash/RAM 地块"),
             ("stm32f10x_conf.h + 驱动 src/*.c", "只加 inc 不加 .c → 链接 undefined")]
    for i, (name, note) in enumerate(files):
        y = 222 + i * 48
        f.text(84, y, name, size=14.5, color=INK, weight="bold")
        f.text(84, y + 20, note, size=12.5, color=MUTED)

    # ---- right: two macros ----
    f.card(588, 156, 500, 310, AMBER_STROKE, fill=AMBER_PALE)
    f.text(608, 190, "两个宏必须进编译命令", size=19, color=AMBER_STROKE,
           weight="bold")
    f.pill(608, 208, 280, 42, "STM32F10X_MD", AMBER_STROKE, fill=WHITE,
           size=16)
    f.text(608, 276, "选中容量器件定义；配错 → 中断号、", size=14.5,
           color=INK)
    f.text(608, 302, "外设能力、启动文件与芯片不匹配", size=14.5, color=INK)
    f.pill(608, 330, 380, 42, "USE_STDPERIPH_DRIVER", AMBER_STROKE,
           fill=WHITE, size=16)
    f.text(608, 398, "让 stm32f10x.h 引入 conf.h；漏 →", size=14.5,
           color=INK)
    f.text(608, 424, "GPIO_InitTypeDef 等声明不可见", size=14.5, color=INK)
    f.text(608, 452, "写在 IDE 截图里不影响预处理", size=13.5, color=MUTED)

    # ---- bottom: measured ELF + trap ----
    f.panel(64, 496, 600, 110, GRAY_FILL, amp=1.6)
    f.rect(64, 496, 600, 110, color=MUTED, sw=1.6, fill=None, amp=1.6)
    f.text(88, 528, "冻结 commit 编译实测（GNU Arm 10.3.1）", size=14.5,
           color=INK, weight="bold")
    f.text(88, 560, "text 1976 B · data 20 B · bss 1028 B", size=15,
           color=BLUE_D, font=MONO, weight="bold")
    f.text(88, 588, "符号表里只有一个 SysTick_Handler", size=14,
           color=MUTED)
    f.panel(692, 496, 396, 110, RED_FILL, amp=1.6)
    f.rect(692, 496, 396, 110, color=RED, sw=1.8, fill=None, amp=1.6)
    f.text(716, 528, "坑：模板 stm32f10x_it.c 已有非 weak 的", size=14,
           color=INK)
    f.text(716, 554, "空 SysTick_Handler——替换它，别并存，", size=14,
           color=INK)
    f.text(716, 580, "否则 multiple definition", size=14, color=RED,
           weight="bold")

    f.htext(64, 700, "链接闭合不证明板级行为：验收仍是 PC13 约 1 Hz、SystemCoreClock 等于真主频",
            size=19.5, color=INK, weight="bold", hl=True)
    f.text(576, 730,
           "读数取自本章 examples/spl-f1-blink 实测；SPL V3.5.0，STSW-STM32054。",
           size=14, color=MUTED, anchor="middle")
    return f


FIGS = {
    "ch01-memory-two-addresses": ch01_memory_two_addresses,
    "ch01-const-ram-economics": ch01_const_ram_economics,
    "ch02-volatile-contract": ch02_volatile_contract,
    "ch02-ub-compiler-fuel": ch02_ub_compiler_fuel,
    "ch03-struct-overlay": ch03_struct_overlay,
    "ch03-map-translation-fails": ch03_map_translation_fails,
    "ch04-ring-two-schools": ch04_ring_two_schools,
    "ch06-boot-five-stations": ch06_boot_five_stations,
    "ch07-spl-minimum-loop": ch07_spl_minimum_loop,
}


if __name__ == "__main__":
    import sys

    STAGE.mkdir(parents=True, exist_ok=True)
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        fig = FIGS[n]()
        save(fig, str(STAGE / (n + ".svg")))
        print("wrote", STAGE / (n + ".svg"))