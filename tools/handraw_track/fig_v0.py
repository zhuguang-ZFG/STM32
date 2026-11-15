# -*- coding: utf-8 -*-
"""Knowledge-track plates for ch01-ch03 (L0 起步).

Every number and label is copied from the chapter it belongs to; the plates
are explanatory diagrams, not measurements or board photos. Deterministic:
same code -> same SVG bytes -> same PNG pixels.
"""
from pathlib import Path

from hd import (AMBER_FILL, AMBER_STROKE, BLUE_D, GREEN_D, INK, MUTED, RED,
                WHITE, Fig, save)

STAGE = Path(__file__).resolve().parents[2] / ".temp" / "l0-l5-pass" / "figures"


def ch01_memory_two_addresses():
    """Flash holds the .data backup; RAM holds the runtime copy."""
    f = Fig("ch01-memory-two-addresses",
            "一个变量，两个地址：Flash 初值备份与 RAM 运行地址")
    f.text(64, 124,
           "F407 工程 mem_probe.elf：.data 运行时住 RAM，初值另存 Flash；"
           "栈从 RAM 顶向下长，堆从 .bss 之后向上长。",
           size=17, color=MUTED)

    # ---- Flash panel ----
    f.rect(64, 176, 500, 410, color=BLUE_D, fill=WHITE, sw=2.4)
    f.text(88, 208, "Flash · 0x08000000", size=20, color=BLUE_D, weight="bold")
    f.text(88, 232, "烧录时固件住这里，只带 .data 的初值备份", size=14, color=MUTED)

    f.rect(88, 252, 452, 44, color=BLUE_D, fill=WHITE, sw=2.0, double=False)
    f.text(104, 280, "0x08000000  .isr_vector  392 B", size=15, color=INK)

    f.text(88, 330, "0x080002a0  LMA · 文件里真有的 12 B",
           size=14, color=AMBER_STROKE, weight="bold")
    cell_x, cell_w, cell_y, cell_h = 88, 37, 344, 54
    bytes12 = ["05", "00", "00", "00",
               "01", "00", "00", "00",
               "68", "69", "00", "00"]
    for i, b in enumerate(bytes12):
        x = cell_x + i * cell_w
        color = GREEN_D if i < 4 else (AMBER_STROKE if i < 8 else BLUE_D)
        f.rect(x, cell_y, cell_w, cell_h, color=color, fill=WHITE, sw=1.8,
               double=False)
        f.text(x + cell_w / 2, cell_y + 35, b, size=15, color=INK,
               anchor="middle", font="'Consolas','Courier New',monospace")
    for cx, label in ((162, "g_init = 5"), (310, "g_flag = 1"),
                      (458, 'g_msg = "hi"')):
        f.text(cx, 420, label, size=14, color=INK, anchor="middle")
    f.text(88, 456, "FileSiz 0x0000c：备份 12 B 随固件烧进 Flash",
           size=14, color=INK)
    f.text(88, 482, ".bss 的初值全是 0，文件里不占字节（NOBITS）",
           size=14, color=MUTED)
    f.text(88, 516, "上电后谁搬？Reset_Handler 逐字读这里、写 RAM。",
           size=14, color=GREEN_D, weight="bold")
    f.text(88, 542, "改链接脚本或换芯片，LMA 与大小都会变。", size=13, color=MUTED)

    # ---- RAM panel ----
    f.rect(600, 176, 488, 410, color=GREEN_D, fill=WHITE, sw=2.4)
    f.text(624, 208, "RAM · 0x20000000", size=20, color=GREEN_D, weight="bold")
    f.text(624, 232, "运行时本体住这里；地址向上增大 ↑", size=14, color=MUTED)

    f.text(624, 262, "0x20020000  _estack（RAM 顶）", size=13, color=MUTED)
    f.rect(624, 272, 440, 52, color=RED, fill=WHITE, sw=2.0, double=False)
    f.text(640, 294, "栈：最小 1 KB（_Min_Stack_Size = 0x400）",
           size=14, color=RED, weight="bold")
    f.text(640, 314, "向下长 ↓", size=13, color=RED)

    f.rect(624, 334, 440, 62, color=MUTED, fill=WHITE, sw=1.8, dash="7 6",
           double=False)
    f.text(844, 371, "堆与栈尚未碰面的空地", size=14, color=MUTED,
           anchor="middle")

    f.rect(624, 406, 440, 52, color=AMBER_STROKE, fill=WHITE, sw=2.0,
           double=False)
    f.text(640, 428, "堆：最小 512 B（_Min_Heap_Size = 0x200）",
           size=14, color=AMBER_STROKE, weight="bold")
    f.text(640, 448, "从 _ebss 之后向上长 ↑", size=13, color=AMBER_STROKE)

    f.rect(624, 468, 440, 40, color=AMBER_STROKE, fill=WHITE, sw=2.0,
           double=False)
    f.text(640, 494, ".bss 32 B：启动时清零（文件里 0 B）", size=14, color=INK)

    f.rect(624, 518, 440, 40, color=GREEN_D, fill=WHITE, sw=2.0, double=False)
    f.text(640, 544, '.data 12 B：g_init / g_flag / g_msg="hi"',
           size=14, color=INK)
    f.text(624, 580, "0x20000000  0x2000000c  0x2000002c", size=12.5,
           color=MUTED)

    # ---- bottom ledger ----
    f.rect(64, 604, 1024, 84, color=BLUE_D, fill=WHITE, sw=2.2)
    f.text(84, 632,
           "readelf 第二条 LOAD：VirtAddr 0x20000000（RAM） / "
           "PhysAddr 0x080002a0（Flash）",
           size=14.5, color=INK)
    f.text(84, 658,
           "FileSiz 0x0000c（12 B） < MemSiz 0x00002c（44 B：.data 12 + .bss 32）",
           size=14.5, color=INK)
    f.text(84, 682,
           "判读形状：VMA 落 0x2000xxxx，LMA 落 0x0800xxxx，文件里的货比 RAM 里少。",
           size=13.5, color=MUTED)

    f.htext(64, 716,
            "烧录文件只带初值备份；RAM 里的 5，要等 Reset_Handler 搬完才可信。",
            size=19, color=INK, weight="bold", hl=True)
    return f


def ch02_volatile_contract():
    """Three optimizer moves, the volatile withdrawal, and CMSIS types."""
    f = Fig("ch02-volatile-contract",
            "编译器看不见的写：volatile 的合同与 __I/__O/__IO")
    f.text(64, 124,
           "同一份源码，-O0 与 -O2 两份汇编：优化器按 as-if 删改普通内存，"
           "硬件寄存器却在程序之外改变。",
           size=17, color=MUTED)

    f.text(64, 172, "① 优化器对普通内存的三项动作（对硬件寄存器都是错的）",
           size=20, color=BLUE_D, weight="bold")
    cards = [
        (64, "缓存", "多次读合成一次",
         ["poll_plain：整函数只读一次", "循环变成 .L3: b .L3 死转"], BLUE_D),
        (410, "删除", "写了没人再读的赋值",
         ["delay_plain：-O2 只剩 ret / bx lr", "一千圈延时在产物里没有存在过"], GREEN_D),
        (756, "合并", "连续两次置位合成一次",
         ["cfg_plain：三次读-改-写", "并成一次 orr #7"], AMBER_STROKE),
    ]
    for x, name, sub, lines, color in cards:
        f.rect(x, 190, 324, 148, color=color, fill=WHITE, sw=2.2)
        f.text(x + 20, 222, name, size=22, color=color, weight="bold")
        f.text(x + 20, 246, sub, size=13.5, color=MUTED)
        f.multi(x + 20, 280, lines, size=14, color=INK, lh=23)

    f.text(64, 386, "② volatile 只收回这三项授权，不保证原子",
           size=20, color=GREEN_D, weight="bold")
    f.rect(64, 404, 620, 148, color=GREEN_D, fill=WHITE, sw=2.2)
    f.multi(84, 436, [
        "每次使用都必须真实访存：不许缓存、不许删、不许凭空造。",
        "poll_volatile：循环回到每圈一条 ldr r3, [r2, #4]。",
    ], size=15, color=INK, lh=27)
    f.text(84, 500, "读-改-写三步仍可被中断打断：isr_toggle 三条指令、两个间隙。",
           size=14, color=RED, weight="bold")
    f.text(84, 530, "要原子性：临界区、BSRR 一类外设侧原子入口，或内存屏障。",
           size=13.5, color=MUTED)

    f.rect(704, 404, 384, 148, color=RED, fill=WHITE, sw=2.2)
    f.text(724, 434, "三次写被折叠", size=17, color=RED, weight="bold")
    f.text(724, 462, "普通结构体：", size=13.5, color=MUTED)
    f.text(724, 486, "ldr / orr #7 / str", size=15, color=INK,
           font="'Consolas','Courier New',monospace")
    f.text(724, 514, "字段带 __IO：三组 ldr/orr/str", size=14, color=GREEN_D,
           weight="bold")
    f.text(724, 540, "硬件要三个动作，少发就不生效。", size=13, color=MUTED)

    f.text(64, 600, "③ CMSIS 用类型写合同：__I / __O / __IO",
           size=20, color=AMBER_STROKE, weight="bold")
    types = [
        (64, "__I", "volatile const", "程序只读，硬件随时可能改", BLUE_D),
        (410, "__O", "volatile", "只写，语义上强调写", GREEN_D),
        (756, "__IO", "volatile", "读和写都可能被硬件改变", AMBER_STROKE),
    ]
    for x, name, expands, meaning, color in types:
        f.rect(x, 618, 324, 86, color=color, fill=WHITE, sw=2.2)
        f.text(x + 20, 650, name, size=21, color=color, weight="bold",
               font="'Consolas','Courier New',monospace")
        f.text(x + 92, 648, expands, size=14.5, color=INK,
               font="'Consolas','Courier New',monospace")
        f.text(x + 20, 682, meaning, size=13.5, color=MUTED)

    f.text(64, 734,
           "GPIO_TypeDef 整组寄存器用 __IO；只读的 IDR / SR 用 const volatile。",
           size=15, color=INK)
    f.text(64, 760,
           "volatile 改的是访问方式，不改段归属、地址，也不改原子性。",
           size=18, color=INK, weight="bold")
    return f


def ch03_struct_overlay():
    """GPIO_TypeDef offsets over the register block, plus padding."""
    f = Fig("ch03-struct-overlay",
            "结构体罩住寄存器块：偏移、对齐与填充")
    f.text(64, 124,
           "GPIOF_BASE = 0x40021400；GPIO_TypeDef 9 个成员、10 个寄存器，"
           "BSRR 在 0x18，整个结构体 0x28。",
           size=17, color=MUTED)

    f.text(64, 164, "① 寄存器地图 → 结构体偏移", size=20, color=BLUE_D,
           weight="bold")
    f.rect(64, 180, 800, 92, color=BLUE_D, fill=WHITE, sw=2.0, double=False)
    f.text(84, 204, "GPIO_TypeDef：声明顺序即偏移顺序", size=14, color=MUTED)
    regs = [
        ("MODER", "0x00", 80), ("OTYPER", "0x04", 80), ("OSPEEDR", "0x08", 80),
        ("PUPDR", "0x0C", 80), ("IDR", "0x10", 80), ("ODR", "0x14", 80),
        ("BSRR", "0x18", 80), ("LCKR", "0x1C", 80), ("AFR[2]", "0x20-0x24", 160),
    ]
    x = 64
    for name, off, w in regs:
        color = AMBER_STROKE if name == "BSRR" else BLUE_D
        fill = AMBER_FILL if name == "BSRR" else WHITE
        f.rect(x, 220, w, 52, color=color, fill=fill, sw=2.0, double=False)
        f.text(x + w / 2, 242, name, size=14 if w > 80 else 12.5,
               color=INK, anchor="middle", weight="bold")
        f.text(x + w / 2, 262, off, size=12, color=MUTED, anchor="middle")
        x += w

    f.rect(884, 180, 204, 92, color=AMBER_STROKE, fill=WHITE, sw=2.0)
    f.text(900, 206, "BSRR：第 7 格", size=15, color=AMBER_STROKE,
           weight="bold")
    f.text(900, 230, "6 × 4 B = 0x18", size=14, color=INK)
    f.text(900, 254, "sizeof = 0x28", size=14, color=INK)

    f.text(64, 304,
           "GPIOF_BASE 0x40021400 + 0x18 = 0x40021418；地址按 4 字节对齐递增。",
           size=14, color=INK)
    f.text(64, 328,
           "_Static_assert 同时钉住 offsetof(BSRR) 与 sizeof(GPIO_TypeDef)。",
           size=13.5, color=MUTED)

    f.text(64, 372, "② 对齐与填充：Padded_t 12 B，Packed_t 8 B",
           size=20, color=GREEN_D, weight="bold")
    f.text(64, 400, "Padded_t { uint8_t a; uint32_t b; uint8_t c; }",
           size=14, color=GREEN_D, weight="bold")
    cells = [("a", 0, GREEN_D), ("x", 1, MUTED), ("x", 2, MUTED),
             ("x", 3, MUTED), ("b", 4, BLUE_D), ("b", 5, BLUE_D),
             ("b", 6, BLUE_D), ("b", 7, BLUE_D), ("c", 8, GREEN_D),
             ("x", 9, MUTED), ("x", 10, MUTED), ("x", 11, MUTED)]
    cell_w, cell_h, base_y = 60, 54, 412
    for i, (label, off, color) in enumerate(cells):
        x = 64 + i * cell_w
        f.rect(x, base_y, cell_w, cell_h, color=color,
               fill=AMBER_FILL if label == "x" else WHITE, sw=1.8,
               double=False)
        f.text(x + cell_w / 2, base_y + 35, label, size=16, color=INK,
               anchor="middle", weight="bold",
               font="'Consolas','Courier New',monospace")
        f.text(x + cell_w / 2, base_y + 72, str(off), size=11.5, color=MUTED,
               anchor="middle")

    f.rect(820, 400, 268, 140, color=GREEN_D, fill=WHITE, sw=2.2)
    f.text(838, 428, "Padded_t", size=17, color=GREEN_D, weight="bold")
    f.multi(838, 456, ["sizeof = 12", "a@0  b@4  c@8",
                       "洞 1：a 后 3 B", "洞 2：c 后 3 B"], size=13.5,
            color=INK, lh=22)

    f.text(64, 552, "Packed_t { uint32_t b; uint8_t a; uint8_t c; }",
           size=14, color=BLUE_D, weight="bold")
    cells2 = [("b", 0), ("b", 1), ("b", 2), ("b", 3),
              ("a", 4), ("c", 5), ("x", 6), ("x", 7)]
    for i, (label, off) in enumerate(cells2):
        x = 64 + i * cell_w
        color = BLUE_D if label == "b" else (GREEN_D if label in "ac" else MUTED)
        f.rect(x, 564, cell_w, cell_h, color=color,
               fill=AMBER_FILL if label == "x" else WHITE, sw=1.8,
               double=False)
        f.text(x + cell_w / 2, 564 + 35, label, size=16, color=INK,
               anchor="middle", weight="bold",
               font="'Consolas','Courier New',monospace")
        f.text(x + cell_w / 2, 564 + 72, str(off), size=11.5, color=MUTED,
               anchor="middle")

    f.rect(820, 552, 268, 126, color=BLUE_D, fill=WHITE, sw=2.2)
    f.text(838, 580, "Packed_t", size=17, color=BLUE_D, weight="bold")
    f.multi(838, 608, ["sizeof = 8", "b@0  a@4  c@5",
                       "省下的 4 B 来自成员顺序"], size=13.5, color=INK,
            lh=22)

    f.text(64, 702,
           "arr[1] − arr[0] = 12 B：尾部填充保证 sizeof 含在 stride 里，数组不歪。",
           size=14, color=INK)
    f.htext(64, 742,
            "偏移由声明顺序、4 字节宽度与对齐规则共同决定；位域与 pack 不进寄存器映射。",
            size=17, color=INK, weight="bold", hl=True)
    return f


FIGS = {
    "ch01-memory-two-addresses": ch01_memory_two_addresses,
    "ch02-volatile-contract": ch02_volatile_contract,
    "ch03-struct-overlay": ch03_struct_overlay,
}


if __name__ == "__main__":
    import sys

    STAGE.mkdir(parents=True, exist_ok=True)
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        fig = FIGS[n]()
        save(fig, str(STAGE / (n + ".svg")))
        print("wrote", STAGE / (n + ".svg"))
