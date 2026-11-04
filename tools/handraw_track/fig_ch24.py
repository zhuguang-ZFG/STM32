# -*- coding: utf-8 -*-
"""ch24 knowledge-track figures (facts from docs/24, DS10198 Rev 11 / RM0351)."""
from hd import *


def part_id():
    f = Fig("ch24-part-id", "STM32L476RG 与它的电流档 / decode and currents")
    f.panel(296, 116, 560, 76, AMBER_FILL)
    f.rect(296, 116, 560, 76, color=AMBER_STROKE, sw=3.0)
    f.text(W / 2, 146, "STM32L476RG：M4F @ 80 MHz", size=30, color=INK,
           anchor="middle", weight="bold")
    f.text(W / 2, 178, "1.71–3.6 V · Flash 1 MB · SRAM 128 KB · LQFP64", size=20,
           color=MUTED, anchor="middle")
    rows = [
        ("VBAT 300 nA · Shutdown 30 nA", GREEN_D),
        ("Standby 120 nA · 带 RTC 420 nA", GREEN_D),
        ("Stop 2 = 1.1 µA（带 RTC 1.4 µA），唤醒 4 µs", BLUE_D),
        ("Run：LDO 100 µA/MHz · SMPS 39 µA/MHz", BLUE_D),
    ]
    y = 232
    for t, c in rows:
        f.rect(120, y, 912, 58, color=c, fill=WHITE)
        f.text(150, y + 37, t, size=23, color=c, weight="bold")
        y += 76
    f.htext(W / 2, 612, "封面典型值 ≠ 你板子的实测值", size=27, color=RED,
            anchor="middle", weight="bold", hl=True)
    f.multi(W / 2, 656, ["板上的 LDO、LED、外设回灌会抬高整板电流 —", "别拿手册封面数字验收万用表"],
            size=22, color=INK, lh=36, anchor="middle")
    return f


def modes():
    f = Fig("ch24-modes", "醒来从哪里继续 / where do you wake up")
    f.rect(80, 140, 480, 300, color=GREEN, fill=WHITE)
    f.htext(320, 184, "Sleep / Stop 0·1·2", size=27, color=GREEN_D,
            anchor="middle", weight="bold")
    f.multi(320, 228, ["从 WFI/WFE 的", "下一条指令继续", "", "SRAM1/2 与大多数", "寄存器保持"],
            size=23, color=INK, lh=36, anchor="middle")
    f.rect(592, 140, 480, 300, color=RED, fill=WHITE)
    f.htext(832, 184, "Standby / Shutdown", size=27, color=RED, anchor="middle",
            weight="bold")
    f.multi(832, 228, ["唤醒走复位路径", "主 SRAM 与普通寄存器丢", "", "用 RTC + 备份寄存器", "保存最小状态，查复位标志"],
            size=23, color=INK, lh=36, anchor="middle")
    f.htext(W / 2, 500, "Stop 2 更深地关 VCORE，PLL 在 Stop 中关闭", size=25,
            color=INK, anchor="middle", weight="bold", hl=True)
    f.text(W / 2, 548, "把两类混在一起 = 把已经丢的 RAM 当成还在", size=24, color=RED,
           anchor="middle")
    f.text(W / 2, 592, "外设能否在目标模式唤醒：逐项查 RM0351，不从别的料号照抄",
           size=22, color=MUTED, anchor="middle")
    return f


def wake_clocks():
    f = Fig("ch24-wake-clocks", "醒来 ≠ 80 MHz 已恢复 / clocks after Stop 2")
    f.panel(216, 122, 720, 84, AMBER_FILL)
    f.rect(216, 122, 720, 84, color=AMBER_STROKE, sw=3.0)
    f.text(W / 2, 156, "STOPWUCK 选 MSI 或 HSI16 临时接管", size=26, color=INK,
           anchor="middle", weight="bold")
    f.text(W / 2, 192, "CPU 已继续执行 ≠ 80 MHz PLL 已恢复", size=23, color=RED,
           anchor="middle", weight="bold")
    items = [
        ("SysTick", "重新按目标 HCLK 配置", GREEN_D),
        ("UART 波特率", "内核时钟变了，BRR 要重算", BLUE_D),
        ("Flash 等待周期", "频率变了 LATENCY 也要变", BLUE_D),
        ("定时器周期", "PCLK 变了 ARR/PSC 重算", AMBER_STROKE),
        ("USB / 精确定时", "时钟源没回到 PLL 前别用", RED),
    ]
    y = 258
    for t, d, c in items:
        f.rect(150, y, 250, 56, color=c, fill=WHITE)
        f.text(275, y + 36, t, size=22, color=c, anchor="middle", weight="bold")
        f.text(430, y + 36, d, size=22, color=INK)
        y += 74
    f.htext(W / 2, 668, "先恢复时钟，再恢复通信，最后才是应用逻辑", size=25,
            color=INK, anchor="middle", weight="bold", hl=True)
    return f


def pin_mux():
    f = Fig("ch24-pin-mux", "L476RG 抢脚清单 / shared pins")
    rows = [
        ("PA11 / PA12", "CAN1_RX/TX 与 OTG_FS_DM/DP（44/45）", "都要就 CAN 改 PB8/PB9", RED),
        ("PB6 / PB7", "I2C1_SCL/SDA（58/59）", "另一组 PB8/PB9（61/62）", AMBER_STROKE),
        ("PA2 / PA3", "USART2_TX/RX（16/17）", "调试口常客", BLUE_D),
        ("PA5–PA7", "SPI1 SCK/MISO/MOSI（21–23）", "PA4 = NSS（20）", BLUE_D),
        ("PA13 / PA14", "SWD（46 / 49）", "BOOT0=60，不与 SWCLK 共用", GREEN_D),
        ("VDDUSB", "脚 48，电源脚不是 GPIO", "和 VSS（47）分开", GREEN_D),
    ]
    y0 = 136
    for t, a, b, c in rows:
        f.rect(80, y0, 220, 66, color=c, fill=WHITE)
        f.text(190, y0 + 40, t, size=22, color=c, anchor="middle", weight="bold")
        f.text(326, y0 + 28, a, size=21, color=INK)
        f.text(326, y0 + 54, b, size=19, color=MUTED)
        y0 += 84
    f.htext(W / 2, 672, "PA11/PA12 的抢脚和 F103 上 USB 抢 CAN 是同一类坑",
            size=24, color=RED, anchor="middle", weight="bold", hl=True)
    return f


def idd():
    f = Fig("ch24-idd", "JP6 只切 MCU 的 IDD / measure the right thing")
    f.rect(120, 130, 420, 190, color=GREEN, fill=WHITE)
    f.multi(330, 174, ["拔掉 JP6 (IDD)", "串入电流表", "量的是 MCU 电流", "≠ 整板输入电流"],
            size=23, color=GREEN_D, lh=36, anchor="middle")
    f.rect(632, 130, 420, 190, color=RED, fill=WHITE)
    f.multi(842, 174, ["ST-LINK、LED、", "外部模块经 GPIO 回灌", "都不在 JP6 里", "要逐项排查"],
            size=23, color=RED, lh=36, anchor="middle")
    f.panel(120, 376, 912, 118, AMBER_FILL)
    f.rect(120, 376, 912, 118, color=AMBER_STROKE, sw=3.0)
    f.text(W / 2, 416, "万用表的负担电压会让 MCU 的 VDD 下跌甚至复位", size=25,
           color=RED, anchor="middle", weight="bold")
    f.text(W / 2, 456, "动态功耗分析仪或低阻分流器才同时看到 µA 睡眠与 mA 唤醒",
           size=22, color=INK, anchor="middle")
    f.htext(W / 2, 566, "唤醒尖峰采样率下限：f_s ≥ 10 / t_min", size=27, color=INK,
            anchor="middle", weight="bold", hl=True)
    f.multi(W / 2, 614, ["最短活动脉冲内至少 10 个样本；同时记录 MCU 端 VDD，", "料号、revision、固件 commit、睡眠配置一样不能少"],
            size=22, color=INK, lh=36, anchor="middle")
    return f


FIGS = {
    "ch24-part-id": part_id,
    "ch24-modes": modes,
    "ch24-wake-clocks": wake_clocks,
    "ch24-pin-mux": pin_mux,
    "ch24-idd": idd,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))
