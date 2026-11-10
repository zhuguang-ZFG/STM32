# -*- coding: utf-8 -*-
"""Chapter 01 knowledge-track plates (facts from docs/01, PM0075 / RM0008 / DS5319).

Three plates close the no-figure spans of chapter 1:
* rdp_unlock_paths  - CubeProgrammer GUI four steps vs the one-line OpenOCD
  `stm32f1x unlock 0`; both trigger a mass erase, and the F1 unprotected byte
  is 0xA5 (0xAA is the F4 spelling).
* one_elf_evidence  - CLI / CLion / VS Code / CI are callers of one
  CMakePresets.json + toolchain file + linker script + OpenOCD cfg, so the
  build log can only ever name one ELF (and a host .exe is a toolchain fault).
* boot_first_words  - reset fetch chain: 0x00000000 aliases 0x08000000, word 0
  is the MSP, word 1 is Reset_Handler; two exits leave the chain: PA13/PA14
  reused as GPIO kills SWD, BOOT0=1 boots 0x1FFFF000 system memory instead.
"""
from hd import *


def rdp_unlock_paths():
    f = Fig("ch01-rdp-unlock-paths",
            "解锁读保护：两条等价路径，同一个代价")

    # ---- 左：CubeProgrammer GUI 四步 ----
    f.rect(64, 122, 492, 322, color=BLUE_D, fill=WHITE, sw=2.6)
    f.text(88, 162, "① GUI：STM32CubeProgrammer", size=23, color=BLUE_D,
           weight="bold")
    steps = ["1. ST-LINK 连接方式 → Connect",
             "2. Option bytes → RDP 写 0xA5",
             "3. Apply（整片擦除随即开始）",
             "4. 重新下载程序"]
    for i, s in enumerate(steps):
        f.text(96, 210 + i * 54, s, size=21, color=INK)

    # ---- 右：OpenOCD 一条命令 ----
    f.rect(596, 122, 492, 322, color=GREEN_D, fill=WHITE, sw=2.6)
    f.text(620, 162, "② CLI：OpenOCD 等价命令", size=23, color=GREEN_D,
           weight="bold")
    f.multi(620, 206,
            ['openocd -f interface/stlink.cfg \\',
             '  -f target/stm32f1x.cfg \\',
             '  -c "init; reset halt;',
             '      stm32f1x unlock 0;',
             '      reset; shutdown"'],
            size=18, color=INK, lh=30)
    f.text(620, 400, "unlock 0 做的事与左边 Apply 相同", size=19, color=MUTED)

    # 中间等号
    f.circle(576, 282, 26, color=MUTED, sw=2.2, fill=WHITE)
    f.text(576, 292, "=", size=30, color=MUTED, anchor="middle",
           weight="bold")

    # ---- 红条：整片擦除 ----
    f.fillrect(64, 468, 1024, 58, AMBER_FILL, r=8)
    f.rect(64, 468, 1024, 58, color=RED, fill=None, sw=2.8, dash="8 6")
    f.text(96, 507, "解除 = 整片擦除主闪存：RDP≠0xA5 才允许读；写回 0xA5 前先擦光",
           size=22, color=RED, weight="bold")

    # ---- 底：0xA5 vs 0xAA ----
    f.rect(64, 556, 492, 132, color=GREEN_D, fill=WHITE, sw=2.4)
    f.text(88, 596, "F1 的无保护值：0xA5", size=23, color=GREEN_D,
           weight="bold")
    f.text(88, 638, "写 0xA5 之后才允许读出 Flash；", size=19, color=INK)
    f.text(88, 668, "编程回 0xA5 会先整片擦除。", size=19, color=INK)

    f.rect(596, 556, 492, 132, color=RED, fill=WHITE, sw=2.4)
    f.text(620, 596, "不认 0xAA（那是 F4 的写法）", size=23, color=RED,
           weight="bold")
    f.text(620, 638, "F103C8T6 按 0xAA 写没有效果，", size=19, color=INK)
    f.text(620, 668, "片子看起来仍保护着。", size=19, color=INK)

    f.text(64, 736, "读出被拒先怀疑 RDP，不要先换探针：连接成功与允许读出是两件事。",
           size=20, color=MUTED)
    return f


def one_elf_evidence():
    f = Fig("ch01-one-elf-evidence",
            "四个调用方，四份共享契约，同一个 ELF")

    f.text(64, 122, "调用方只负责按按钮；构建事实写在共享文件里，不复制进 IDE 配置。",
           size=21, color=INK)

    # ---- 四个调用方 ----
    callers = [("CLI", "cmake --preset debug", BLUE_D),
               ("CLion", "Preset: BluePill SPL Debug", BLUE_D),
               ("VS Code", "tasks.json → preset", BLUE_D),
               ("CI", "同一条 cmake 命令", BLUE_D)]
    xs = [64, 324, 584, 844]
    for x, (name, note, col) in zip(xs, callers):
        f.rect(x, 152, 236, 92, color=col, fill=WHITE, sw=2.4)
        f.text(x + 16, 186, name, size=23, color=col, weight="bold")
        f.text(x + 16, 220, note, size=17, color=INK)

    # 向下汇聚
    for x in xs:
        f.arrow(x + 118, 246, x + 118, 292, color=MUTED, sw=2.2, bend=0)

    # ---- 共享契约：四个文件 ----
    files = [("CMakePresets.json", "preset 名与缓存变量"),
             ("toolchain file", "arm-none-eabi-gcc"),
             ("链接脚本 .ld", "Flash / RAM 布局"),
             ("openocd/*.cfg", "transport 与 adapter speed")]
    for x, (name, note) in zip(xs, files):
        f.rect(x, 300, 236, 92, color=AMBER_STROKE, fill=AMBER_FILL, sw=2.4)
        f.text(x + 14, 334, name, size=19, color=INK, weight="bold")
        f.text(x + 14, 366, note, size=16, color=INK)

    f.text(64, 428, "构建日志只应出现一行编译器识别：arm-none-eabi-gcc；",
           size=20, color=GREEN_D, weight="bold")
    f.text(64, 456, "出现宿主机的 gcc / cl.exe，就是 toolchain file 没有生效。",
           size=20, color=MUTED)

    # ---- 汇聚到同一个 ELF ----
    for x in xs:
        f.arrow(x + 118, 394, 576, 512, color=GREEN_D, sw=2.2, bend=0)
    f.rect(320, 520, 512, 122, color=GREEN_D, fill=WHITE, sw=3.0)
    f.text(576, 562, "同一个 ELF", size=30, color=GREEN_D, anchor="middle",
           weight="bold")
    f.text(576, 602, "build/debug/spl-f1-blink.elf（+ .map / .bin）", size=19,
           color=INK, anchor="middle")
    f.text(576, 628, "program · verify · reset 都指向它", size=18, color=MUTED,
           anchor="middle")

    # ---- 底：三条证据 ----
    f.line(64, 670, 1088, 670, color=MUTED, sw=1.2)
    f.text(64, 708, "证据链：同一 preset → 同一编译器 → 同一链接脚本 → 同一份 ELF。",
           size=20, color=INK)
    f.text(64, 740, "换 IDE 只换调用方；改源文件、宏、头文件路径或链接脚本时，改的是共享入口。",
           size=19, color=MUTED)
    return f


def boot_first_words():
    f = Fig("ch01-boot-first-words",
            "复位后先取两个 32 位字：栈顶，然后才是复位入口")

    # ---- 顶部链：别名 → 第 0 字 → 第 1 字 ----
    boxes = [(64, "复位，BOOT0=0", ["0x00000000", "别名 0x08000000"], BLUE_D),
             (412, "第 0 字 @0x00000000", ["MSP 初值", "主栈指针从这开始"], GREEN_D),
             (760, "第 1 字 @0x00000004", ["Reset_Handler", "之后才到 main"], GREEN_D)]
    for x, head, lines, col in boxes:
        f.rect(x, 128, 296, 118, color=col, fill=WHITE, sw=2.6)
        f.text(x + 18, 166, head, size=21, color=col, weight="bold")
        f.multi(x + 18, 200, lines, size=19, color=INK, lh=28)
    f.arrow(364, 187, 404, 187, color=BLUE_D, sw=2.6, bend=0)
    f.arrow(712, 187, 752, 187, color=GREEN_D, sw=2.6, bend=0)

    f.text(64, 286, "物理存储器是 64 KB 闪存（C8）；别名不是第二份数据。",
           size=20, color=MUTED)

    # ---- 两个失败出口 ----
    f.text(64, 334, "两个出口让这条链断掉：", size=22, color=INK,
           weight="bold")

    # 出口一：Debug 关掉
    f.rect(64, 356, 492, 210, color=RED, fill=WHITE, sw=2.6)
    f.text(88, 396, "失败出口 ①：Debug 被关掉", size=22, color=RED,
           weight="bold")
    f.multi(88, 432,
            ["CubeMX / 代码把 PA13、PA14 配成普通 GPIO",
             "第 34 脚 SWDIO、第 37 脚 SWCLK 不再是调试口",
             "现象：烧一次后 No target connected",
             "处理：BOOT0 拉高进系统存储器，擦除后改回 Serial Wire"],
            size=18, color=INK, lh=30)

    # 出口二：BOOT0=1
    f.rect(596, 356, 492, 210, color=AMBER_STROKE, fill=WHITE, sw=2.6)
    f.text(620, 396, "失败出口 ②：BOOT0=1 且 BOOT1=0", size=22,
           color=AMBER_STROKE, weight="bold")
    f.multi(620, 432,
            ["取指落在系统存储器 0x1FFFF000",
             "不是 SRAM，也不是主闪存里的程序",
             "现象：程序还在，但就是没有被执行",
             "处理：BOOT0 回 0 复位，或两只 BOOT 都拉高进 SRAM"],
            size=18, color=INK, lh=30)

    # ---- 底注 ----
    f.line(64, 594, 1088, 594, color=MUTED, sw=1.2)
    f.text(64, 632, "排查顺序：先看 BOOT0 与 Debug 选项，再怀疑程序本身。",
           size=21, color=INK, weight="bold")
    f.text(64, 668, "中断入口是 VTOR + 4×(IRQn+16)，不是 0x08000000 + 4×IRQn。",
           size=19, color=MUTED)
    f.text(64, 700, "第 35 脚是 VSS_2、第 36 脚是 VDD_2，探针不要落在它们上面。",
           size=19, color=MUTED)
    return f


def main_skeleton():
    f = Fig("ch01-main-skeleton",
            "第一份 main.c 的四步合同 / the four-step main.c contract")
    steps = [
        ("① HAL_Init()", "复位外设、Flash 接口、SysTick", "HAL_Delay 从这一步起可用", GREEN_D),
        ("② SystemClock_Config()", "8 MHz HSE → PLL×9 = 72 MHz", "不跑这步就停在 HSI 8 MHz", BLUE_D),
        ("③ MX_GPIO_Init()", "__HAL_RCC_GPIOC_CLK_ENABLE()", "没开时钟，引脚寄存器写不动", AMBER_STROKE),
        ("④ while (1)", "TogglePin + HAL_Delay(500)", "只有这里才是「你的代码」", RED),
    ]
    y = 150
    for t, s, n, c in steps:
        f.rect(84, y, 690, 92, color=c, fill=WHITE, sw=2.6)
        f.text(112, y + 40, t, size=25, color=c, weight="bold")
        f.text(112, y + 72, s, size=20, color=INK)
        f.text(806, y + 56, n, size=19, color=MUTED)
        if y < 420:
            f.arrow(430, y + 94, 430, y + 118, color=INK, sw=2.6, head=9)
        y += 124
    # 右侧红框
    f.rect(84, 654, 984, 66, color=RED, fill=WHITE, sw=2.6)
    f.htext(W / 2, 688, "前三步是 CubeMX 的合同：别删、别改名、别移到 while 后面",
            size=23, color=RED, anchor="middle", weight="bold", hl=True)
    return f


FIGS = {
    "ch01-rdp-unlock-paths": rdp_unlock_paths,
    "ch01-one-elf-evidence": one_elf_evidence,
    "ch01-boot-first-words": boot_first_words,
    "ch01-main-skeleton": main_skeleton,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))
