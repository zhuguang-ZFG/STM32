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


def sram2_retain():
    f = Fig("ch24-sram2-retain", "SRAM2 想带状态过 Standby：查 RRS 与料号 / SRAM2 across modes")
    rows = [
        ("Sleep / Stop 0·1·2", "SRAM1/2 与大多数寄存器照常保持", "不用额外配置", GREEN_D),
        ("Standby", "VCORE 关，主 SRAM 与普通寄存器丢；", "SRAM2 保持是可选项：置 RRS，", RED),
        ("Shutdown", "比 Standby 更深，主 SRAM 丢；", "RTC/备份域是否保持看供电与配置", MUTED),
    ]
    y = 140
    for name, l1, l2, c in rows:
        f.rect(96, y, 984, 96, color=c, fill=WHITE)
        f.htext(272, y + 40, name, size=25, color=c, anchor="middle",
                weight="bold")
        f.text(430, y + 40, l1, size=22, color=INK)
        f.text(430, y + 74, l2, size=22, color=c if c != MUTED else INK)
        y += 112
    f.panel(96, 484, 984, 108, AMBER_FILL)
    f.rect(96, 484, 984, 108, color=AMBER_STROKE, sw=3.0)
    f.text(W / 2, 522, "Standby 的 SRAM2 保持必须由目标料号和 RRS 配置确认", size=26,
           color=RED, anchor="middle", weight="bold")
    f.text(W / 2, 562, "不能从别的 L4 料号照抄；醒来先查复位标志，才知道走的是哪条路",
           size=22, color=INK, anchor="middle")
    f.rect(96, 616, 984, 78, color=GREEN, fill=WHITE)
    f.multi(W / 2, 646, ["最小状态放 RTC 后备寄存器：Standby 里一定活着，", "不用赌 SRAM2 的配置"], size=22,
            color=INK, lh=34, anchor="middle")
    return f


def sleep_checklist():
    f = Fig("ch24-sleep-checklist", "Stop 2 入睡前五步 / pre-sleep checklist")
    f.htext(W / 2, 114, "进入前：先证明可以睡——五步做完才轮到 WFI", size=24,
            color=INK, anchor="middle", weight="bold", hl=True)
    rows = [
        ("1", "等不可中断事务收尾", GREEN_D,
         "UART / DMA / Flash 写入等不可中断事务结束；记录缓冲区仍归谁"),
        ("2", "只留一个预期唤醒源（RTC/EXTI/WKUP/LPTIM）", BLUE_D,
         "先禁用 → 清外设标志、EXTI/NVIC pending、PWR 唤醒标志 → 再重新使能"),
        ("3", "不用的 GPIO 收进模拟态", AMBER_STROKE,
         "设为模拟、无上下拉；外部上拉、传感器和 VDDUSB 仍会产生板级电流"),
        ("4", "选好 Stop 唤醒时钟 · ST 示例显式选 MSI", BLUE_D,
         "__HAL_RCC_WAKEUPSTOP_CLK_CONFIG(RCC_STOP_WAKEUPCLOCK_MSI)"),
        ("5", "暂停 SysTick", RED,
         "否则 1 ms tick 会成为第一个中断——测到的是『每毫秒醒一次』，不是 Stop 2"),
    ]
    y = 156
    for num, label, c, detail in rows:
        f.rect(84, y, 984, 84, color=c, fill=WHITE)
        f.circle(134, y + 42, 25, color=c, sw=2.8, fill=WHITE)
        f.text(134, y + 51, num, size=26, color=c, anchor="middle",
               weight="bold")
        f.text(178, y + 37, label, size=23, color=c, weight="bold")
        f.text(178, y + 68, detail, size=19, color=INK)
        y += 98
    f.rect(84, 650, 984, 78, color=RED, fill=WHITE)
    f.text(110, 681, "症状：一进 Stop 2 就醒", size=21, color=RED,
           weight="bold")
    f.text(110, 711, "SysTick、旧 EXTI/RTC/PWR 标志或浮空唤醒脚仍有效 → "
           "暂停 tick，按『禁用 → 清标志 → 重新使能』处理唯一唤醒源",
           size=17, color=INK)
    return f


def irq_order():
    f = Fig("ch24-irq-order", "先快照，再让 HAL 清位 / snapshot before HAL clears")
    f.text(72, 122, "同一个中断里的五个时刻：原始位还在 → 被 HAL 清零 → 只剩软件副本",
           size=20, color=MUTED)
    rows = [
        ("①", "闹钟到期，芯片仍在 Stop 2",
         "RTC_ISR.WUTF 与 EXTI 唤醒线置位，此刻没有任何代码在读取", "还在", GREEN_D),
        ("②", "RTC_WKUP_IRQHandler 第一行",
         "RTC->ISR / EXTI->PR1 / PWR->SR1 一次拷进保留 SRAM", "唯一窗口", GREEN_D),
        ("③", "HAL_RTCEx_WakeUpTimerIRQHandler()",
         "先清 EXTI RTC 唤醒线，再清 RTC_FLAG_WUTF：原始位从此消失", "清零", RED),
        ("④", "HAL callback 或 EnterSTOP2 返回",
         "这时再读 WUTF 只能是 0；『已经太晚』说的就是这里", "全 0", RED),
        ("⑤", "主循环消费记录",
         "只做 sequence 稳定复制，读 SRAM 副本，不再碰硬件位", "软件副本", BLUE_D),
    ]
    y = 152
    for num, label, detail, badge, c in rows:
        f.rect(72, y, 1008, 78, color=c, fill=WHITE)
        f.circle(120, y + 39, 24, color=c, sw=2.6, fill=WHITE)
        f.text(120, y + 47, num, size=24, color=c, anchor="middle", weight="bold")
        f.text(166, y + 30, label, size=22, color=c, weight="bold")
        f.text(166, y + 60, detail, size=18, color=INK)
        f.rect(966, y + 14, 96, 30, color=c, fill=WHITE, double=False)
        f.text(1014, y + 35, badge, size=17, color=c, anchor="middle",
               weight="bold")
        y += 92
    f.rect(72, 616, 492, 100, color=GREEN_D, fill=WHITE)
    f.text(96, 648, "对的顺序（本章代码）", size=20, color=GREEN_D, weight="bold")
    f.multi(96, 680, ["快照 → __DMB → sequence++ →",
                      "然后才调用 HAL（由它清位）"], size=18, color=INK, lh=30)
    f.rect(588, 616, 492, 100, color=RED, fill=WHITE)
    f.text(612, 648, "错的做法", size=20, color=RED, weight="bold")
    f.multi(612, 680, ["callback / 返回后补读，或只打印",
                       "『醒了』：读到的全是 0"], size=18, color=INK, lh=30)
    f.htext(W / 2, 752, "证据只能是 IRQ 入口写进保留 SRAM 的快照", size=22,
            color=INK, anchor="middle", weight="bold", hl=True)
    return f


def duty_integration():
    f = Fig("ch24-duty-integration", "一个周期的电荷账 / charge per cycle")
    f.text(72, 120, "T = 1 s：活动+恢复 8 ms @ 5 mA，其余 992 ms @ 2 µA（按时间比例画）",
           size=19, color=MUTED)
    f.line(96, 300, 1056, 300, color=INK, sw=2.4)
    f.text(1064, 306, "t", size=18, color=MUTED)
    f.line(96, 288, 1056, 288, color=GREEN_D, sw=2.6, amp=0.6)
    f.text(660, 274, "992 ms @ 2 µA（睡眠平台）", size=18, color=GREEN_D,
           anchor="middle")
    f.fillrect(170, 140, 8, 148, RED)
    f.rect(170, 140, 8, 148, color=RED, sw=1.6, double=False)
    f.arrow(322, 180, 188, 168, color=RED, bend=0.0)
    f.text(330, 176, "8 ms 唤醒尖峰", size=20, color=RED, weight="bold")
    f.text(330, 202, "按 1 s 的比例只有约 7 px 宽，采样一漏就没了", size=17,
           color=MUTED)
    f.rect(84, 356, 500, 196, color=BLUE_D, fill=WHITE)
    f.text(108, 388, "① 先分段积分（Q = I × t）", size=20, color=BLUE_D,
           weight="bold")
    f.multi(108, 424, ["Q_active+wakeup = 5 mA × 0.008 s",
                       "                = 0.040000 mA·s",
                       "Q_sleep = 0.002 mA × 0.992 s",
                       "        = 0.001984 mA·s"], size=19, color=INK, lh=34)
    f.rect(608, 356, 460, 196, color=GREEN_D, fill=WHITE)
    f.text(632, 388, "② 再除以整周期", size=20, color=GREEN_D, weight="bold")
    f.multi(632, 424, ["Q_cycle = 0.040000 + 0.001984",
                       "        = 0.041984 mA·s",
                       "I_avg   ≈ 42 µA",
                       "1000 mAh ÷ 0.042 A ≈ 2.72 年"], size=19, color=INK,
            lh=34)
    f.rect(84, 578, 984, 84, color=RED, fill=WHITE)
    f.text(108, 610, "算术平均 (5 mA + 2 µA) / 2 = 2.5 mA，比真值大 ~60 倍",
           size=20, color=RED, weight="bold")
    f.text(108, 642, "错在把 8 ms 与 992 ms 当成等权；积分是按时间加权的", size=18,
           color=INK)
    f.htext(W / 2, 706, "采样率下限由最短脉冲决定：f_s ≥ 10 / 8 ms = 1.25 kHz",
            size=22, color=INK, anchor="middle", weight="bold", hl=True)
    f.text(72, 748, "电压变化时改用能量积分 E_cycle = Σ V[k]·I[k]·Δt；报告写清最小/平均/最大与原始波形",
           size=17, color=MUTED)
    return f


def two_firmware():
    f = Fig("ch24-two-firmware", "两份固件，一条低功耗路径 / one path, two builds")
    f.text(72, 120, "功能固件证明闭环，测量固件证明电流；底下的 Stop 2 路径必须完全一致",
           size=19, color=MUTED)
    f.rect(72, 150, 492, 286, color=GREEN_D, fill=WHITE)
    f.htext(96, 188, "A · 功能固件（带证据输出）", size=21, color=GREEN_D,
            weight="bold")
    f.multi(96, 228, ["允许：MCO、UART 日志、定时器翻转",
                      "证明：唤醒源识别、时钟恢复、通信可用",
                      "禁止：拿这份的电流去验收",
                      "原因：观测手段本身抬高电流"], size=18, color=INK, lh=36)
    f.text(96, 396, "用途：实验 A", size=18, color=GREEN_D, weight="bold")
    f.rect(588, 150, 492, 286, color=BLUE_D, fill=WHITE)
    f.htext(612, 188, "B · 测量固件（无日志）", size=21, color=BLUE_D,
            weight="bold")
    f.multi(612, 228, ["关掉：MCO、UART 日志、LED、无关传感器",
                       "证明：Q_cycle、I_avg 与理想续航",
                       "不能证明：通信时序是否可用",
                       "用途：实验 B，JP6 串表 + 采样率"], size=18, color=INK,
            lh=36)
    f.text(612, 396, "f_s ≥ 10 / t_min 同样适用于这份", size=18, color=BLUE_D,
           weight="bold")
    f.arrow(318, 442, 318, 474, color=INK, bend=0.0)
    f.arrow(834, 442, 834, 474, color=INK, bend=0.0)
    f.panel(72, 478, 1008, 100, AMBER_FILL)
    f.rect(72, 478, 1008, 100, color=AMBER_STROKE, sw=3.0)
    f.text(W / 2, 516, "共用：同一 Stop 2 入口、同一 RTC 唤醒、同一时钟恢复函数",
           size=22, color=INK, anchor="middle", weight="bold")
    f.text(W / 2, 550, "两份固件只在『证据往哪走』上分叉", size=18, color=INK,
           anchor="middle")
    f.rect(72, 598, 1008, 84, color=RED, fill=WHITE)
    f.text(96, 630, "把功能固件的 MCO / 串口波形当低功耗结果 = 让观测手段污染被测值",
           size=20, color=RED, weight="bold")
    f.text(96, 662, "同一低功耗路径才有可比性；差异只能出现在证据输出", size=18,
           color=INK)
    f.htext(W / 2, 742, "实验 A 与实验 B 的电流数字不能互相引用", size=22,
            color=INK, anchor="middle", weight="bold", hl=True)
    return f


FIGS = {
    "ch24-part-id": part_id,
    "ch24-modes": modes,
    "ch24-wake-clocks": wake_clocks,
    "ch24-pin-mux": pin_mux,
    "ch24-idd": idd,
    "ch24-sram2-retain": sram2_retain,
    "ch24-sleep-checklist": sleep_checklist,
    "ch24-irq-order": irq_order,
    "ch24-duty-integration": duty_integration,
    "ch24-two-firmware": two_firmware,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))
