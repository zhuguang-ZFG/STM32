# -*- coding: utf-8 -*-
"""B54: embed the nine en-gap-closeout plates into zh/en docs (same order)."""
from embed import embed_after_text

SPECS = [
    # 1. ch16-battery-budget — §5 first paragraph
    ("docs/16-低功耗设计.md",
     "续航用电池容量除以平均电流。先把一个周期内各段的电流乘以持续时间，再除以周期；唤醒峰值也占时间，不能只看 Stop 的底电流。",
     "ch16-battery-budget.png",
     "Handraw：电池续航的周期账本（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。看哪里：一个周期拆成 active 与 sleep 两段，平均电流与续航换算在中间，右侧是 LDO Iq、10 kΩ 分压、MOS 门控分压、IWDG 四项常驻漏电。证明什么：Stop 地板不能单独预测续航，还要乘上醒着的时间与频次。不能证明什么：不是实测电流曲线，也不含后文算例与电池自放电。出处：[DS5319](#source-ds5319-pwr)、本章 §5 公式。"),
    ("docs/en/16-low-power.md",
     "Runtime is battery capacity divided by average current. Multiply each interval's current by its duration, add the results, then divide by the period. A wake peak also has a duration; the Stop floor alone cannot predict runtime.",
     "ch16-battery-budget.png",
     "Handraw: the battery runtime ledger over one period (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). Where to look: one period splits into active and sleep with the average-current and runtime formulas; the right column lists four standing leaks — LDO Iq, a 10 kΩ divider, a MOSFET-gated divider, and the IWDG. Proves the Stop floor alone cannot predict runtime; active time and its frequency must be multiplied in. Cannot prove a measured current waveform, the later worked example, or battery self-discharge. See [DS5319](#source-ds5319-pwr) and the §5 formulas."),

    # 2. ch18-hardware-triage — after H4 block
    ("docs/18-常见问题FAQ.md",
     "- **解决**：保存 RCC 复位原因标志，再测电源与 NRST；外部电容按图 31 在第 7 脚接 0.1 µF 到地。看门狗周期与调试行为见第 11 章。",
     "ch18-hardware-triage.png",
     "Handraw：硬件四症状分诊 H1–H4（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。看哪里：H1–H4 四张卡，每张给出判据与「不能证明什么」。证明什么：灯、热、电、复位四类症状各有先查项——极性、短路、表接法、复位标志，顺序比结论重要。不能证明什么：不是实测记录；灯亮、不烫、电流非零都不能单独证明固件正确。出处：[DS5319](#source-ds5319-gpio)、[RM0008](#source-rm0008-boot)、本章 H1–H4。"),
    ("docs/en/18-faq.md",
     "- **Fix**: save the RCC reset flags, then inspect supply and NRST. Add the 0.1 µF capacitor from pin 7 to ground as Figure 31 shows. See chapter 11 for watchdog periods and debug behavior.",
     "ch18-hardware-triage.png",
     "Handraw: hardware triage cards H1–H4 (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). Where to look: four cards H1–H4, each with its checks and its “cannot prove” line. Proves the LED, heat, current, and reset symptoms each have a first check — polarity, short, meter setup, reset flags — and the order matters more than the conclusion. Cannot prove measured results; a lit LED, a cool board, or a non-zero current does not by itself prove the firmware is right. See [DS5319](#source-ds5319-gpio), [RM0008](#source-rm0008-boot), and H1–H4 in this chapter."),

    # 3. ch18-rtos-triage — after R4 block
    ("docs/18-常见问题FAQ.md",
     "- **解决**：改 `xQueueSendFromISR` + `portYIELD_FROM_ISR`。",
     "ch18-rtos-triage.png",
     "Handraw：RTOS 四症状分诊 R1–R4（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。看哪里：R1–R4 四张卡，每张一张判据。证明什么：R1/R3 是配置与资源问题，R2/R4 是优先级与调用纪律问题，两类改法不同。不能证明什么：不是板上波形；HardFault 的位置不等于根因。出处：[FreeRTOS](#source-freertos-syscall)、本章 R1–R4。"),
    ("docs/en/18-faq.md",
     "- **Fix**: use `xQueueSendFromISR` and `portYIELD_FROM_ISR`.",
     "ch18-rtos-triage.png",
     "Handraw: RTOS triage cards R1–R4 (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). Where to look: four cards R1–R4, one check each. Proves R1/R3 are configuration and resource problems while R2/R4 are priority and call-discipline problems; the two classes are fixed differently. Cannot prove a board trace, and the HardFault location is not the root cause. See [FreeRTOS](#source-freertos-syscall) and R1–R4 in this chapter."),

    # 4. ch28-h745-boundaries — H745 intro paragraph, before the five-contract table
    ("docs/28-嵌入式系统与RTOS生态.md",
     "HSEM 提供原子占用和中断通知；它既不搬运 payload，也不替 Cortex-M7 维护数据 Cache。评审核间通道时，把下面五层分别冻结：",
     "ch28-h745-boundaries.png",
     "Handraw：HSEM 的三条边界（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。看哪里：顶部是 HSEM 提供的原子所有权与通知，下面三条边界分别是 payload 的存放、M7 data cache 的维护、释放与处理完成的顺序。证明什么：锁解决「谁先来」，不解决「货到没到」；三条边界都要单独定所有权与顺序。不能证明什么：不替代 RM0399 的寄存器定义，也不提前给出五层契约的字段与序号规则。出处：[RM0399](#source-rm0399)、[冻结的 stm32h745xx.h](#source-stm32h745-header)。"),
    ("docs/en/28-system-rtos.md",
     "HSEM provides atomic ownership and interrupt notification. It neither carries the payload nor maintains the Cortex-M7 data cache. Review an inter-core channel as five separate contracts:",
     "ch28-h745-boundaries.png",
     "Handraw: the three boundaries of HSEM (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). Where to look: the top box is what HSEM provides — atomic ownership and notification; the three boundaries below are payload placement, M7 data-cache maintenance, and the order between release and processing. Proves the lock answers “who goes first”, not “has the cargo arrived”, and each boundary needs its own ownership and ordering rule. Cannot replace the RM0399 register definitions or pre-empt the five contracts' field and sequence rules. See [RM0399](#source-rm0399) and [the frozen stm32h745xx.h](#source-stm32h745-header)."),

    # 5. ch11-bkp-magic — end of §2
    ("docs/11-RTC与看门狗.md",
     "典型用法：上电先读一个「魔法值」（如 `0xA5A5`），若匹配说明之前初始化过，直接读时间；否则写入魔法值并初始化日历。",
     "ch11-bkp-magic.png",
     "Handraw：BKP 魔数与上电流程（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。看哪里：上电→读 BKP_DR1→0xA5A5 的两条分支；下方是 F103C8 的十只 16-bit 与 F4 的二十只 32-bit。证明什么：魔数只决定「是否已初始化」，备份寄存器的容量与宽度按型号不同。不能证明什么：不代表走时准确（准不准由时钟源决定），也不是 VBAT 电流实测。出处：[RM0008](#source-rm0008-rtc)、[DS5319](#source-ds5319-rtc)。"),
    ("docs/en/11-rtc-watchdog.md",
     "The usual pattern: on power-up, read a \"magic value\" (for example `0xA5A5`). If it matches, the calendar was already initialized, so just read the time. If it does not match, write the magic value and initialize the calendar.",
     "ch11-bkp-magic.png",
     "Handraw: the BKP magic value and the power-up flow (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). Where to look: power-up → read BKP_DR1 → the two 0xA5A5 branches; below, the F103C8's ten 16-bit registers against the F4's twenty 32-bit ones. Proves the magic value only decides whether initialization already happened, while capacity and width depend on the part. Cannot prove timekeeping accuracy (the clock source decides that) and is not a VBAT current measurement. See [RM0008](#source-rm0008-rtc) and [DS5319](#source-ds5319-rtc)."),

    # 6. ch19-la-sampling — after the Approach paragraph
    ("docs/19-项目实战合集.md",
     "**技术方案**：下段实际采用 TIM 中断读取 GPIOC 低 8 位，并未配置 DMA；中断延迟、其他中断和读端口耗时都会影响采样间隔。DMA 采 GPIO 是另一种实现，须核对目标的请求映射和总线路径。先验证采样周期与输入保护，再添加触发与主机解码。",
     "ch19-la-sampling.png",
     "Handraw：逻辑分析仪两条采样实现（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。看哪里：实现 A 是 TIM 中断读 GPIOC，实现 B 是 TIM 触发 DMA，底部列出换实现前先验证的三件事。证明什么：示例片段不含 DMA，采样间隔抖动来自中断路径；换 DMA 要另核请求映射与总线路径。不能证明什么：不是采样波形实测，环形缓冲与 BUSY 的完整约定在下一段才展开。出处：本章 §7、[DS5319](#source-ds5319-swd)。"),
    ("docs/en/19-projects.md",
     "**Approach**: the fragment reads GPIOC's low eight bits in a TIM interrupt; it does not configure DMA. Interrupt latency, other interrupts, and the port-read cost all affect the sampling interval. Sampling GPIO through DMA is a separate implementation that requires checking the target's request mapping and bus path. Verify the sample period and input protection before adding triggers and host decoding.",
     "ch19-la-sampling.png",
     "Handraw: the two sampling implementations for the logic analyzer (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). Where to look: implementation A reads GPIOC in a TIM interrupt, implementation B lets a TIM-triggered DMA move the byte; the bottom strip lists the three checks before switching. Proves the example fragment uses no DMA and that its interval jitter comes from the interrupt path; a DMA version must re-check request mapping and bus path. Cannot prove a measured sample stream; the ring buffer and BUSY contract are only unfolded in the next paragraph. See §7 here and [DS5319](#source-ds5319-swd)."),

    # 7. ch15-two-priority-rules — Principle paragraph 6
    ("docs/15-FreeRTOS入门.md",
     "本例调用 `...FromISR` 的中断，抢占优先级数值必须大于等于 5。这个 5 来自 `configMAX_SYSCALL_INTERRUPT_PRIORITY = 0x50`：芯片只用高 4 位，`5 << (8 − 4) = 0x50`。比 5 更急的中断（0 到 4）不受内核的 BASEPRI 临界区屏蔽，不能在其中调用 FreeRTOS API，否则可能打断内核数据更新。启用有效的 `configASSERT` 后，带优先级校验的 API 路径可帮助发现这类错误。例程把 `EXTI0` 设成 5。见 [FreeRTOS Kernel V11.3.2](#source-freertos-syscall)。",
     "ch15-two-priority-rules.png",
     "Handraw：任务与中断两套优先级规则（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。看哪里：左列任务号大者先（2 > 1 > 0），右列中断号小者急（0 最急，FromISR 从 5 起），中间是移位值与 1 ms 时基分工。证明什么：两套编号方向相反，FromISR 只认数值 ≥5。不能证明什么：不是调度波形，也不含 configASSERT 的完整断言路径。出处：[FreeRTOS](#source-freertos-syscall)、[PM0056](#source-pm0056-nvic)。"),
    ("docs/en/15-freertos.md",
     "In this configuration, an interrupt that calls a `...FromISR` function needs a preemption priority number of 5 or a larger number. The 5 comes from `configMAX_SYSCALL_INTERRUPT_PRIORITY = 0x50`: the chip only uses the top 4 bits, and `5 << (8 − 4) = 0x50`. More urgent interrupts (0 to 4) remain unmasked by the kernel's BASEPRI critical sections. They must not call FreeRTOS APIs, which could interrupt a kernel data update. With an effective `configASSERT`, API paths that validate interrupt priority can help catch this error. The example sets `EXTI0` to 5. See [FreeRTOS Kernel V11.3.2](#source-freertos-syscall).",
     "ch15-two-priority-rules.png",
     "Handraw: the task and interrupt priority scales (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). Where to look: the left column runs task priority high-to-low (2 > 1 > 0); the right column runs NVIC priority low-number-first (0 is most urgent, FromISR starts at 5); the middle carries the shifted threshold and the 1 ms time-base split. Proves the two scales point in opposite directions and FromISR requires a numeric priority of at least 5. Cannot prove a scheduling trace or the full configASSERT path. See [FreeRTOS](#source-freertos-syscall) and [PM0056](#source-pm0056-nvic)."),

    # 8. ch12-last-page-math — right after the pitfalls heading, before the table
    ("docs/12-Flash与IAP升级.md",
     "## 常见坑与出处",
     "ch12-last-page-math.png",
     "Handraw：末页地址算术（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。看哪里：64 KB 地址尺、page 63 的起点、0x0801FC00 影子行、APP 46 KB 的区间。证明什么：末页边界要先算清，0x0801FC00 属于 128 KB 器件，不在这颗 C8 上。不能证明什么：不是芯片实读，也不替代 RM 的页擦除时序。出处：[RM0008](#source-rm0008-flash)、本章「时序与状态」。"),
    ("docs/en/12-flash-iap.md",
     "## Pitfalls and sources",
     "ch12-last-page-math.png",
     "Handraw: the last-page address arithmetic (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). Where to look: the 64 KB address ruler, page 63's start, the 0x0801FC00 ghost row, and the 46 KB app range. Proves the last-page boundary must be computed first, and 0x0801FC00 belongs to a 128 KB part, not this C8. Cannot prove a chip read-back and does not replace the RM erase timing. See [RM0008](#source-rm0008-flash) and “Timing and state” here."),

    # 9. ch04-lab-evidence — after the three labs, before §6
    ("docs/04-中断与NVIC.md",
     "3. **实验三（抢占证据）**：增加 TIM2 中断，并让两个 ISR 分别在入口置高、出口置低一只空闲 GPIO。用逻辑分析仪捕获嵌套波形，验证抢占优先级 1 的 EXTI0 能插入抢占优先级 2 的 TIM2。",
     "ch04-lab-evidence.png",
     "Handraw：三个实验各自的证据（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。看哪里：三个 Lab 各一卡，写清步骤与判据。证明什么：标志清零、去抖前后计数、双迹嵌套顺序，是三类可复查的证据。不能证明什么：不是已有波形或实测数据，图只给实验设计与判据。出处：[PM0056](#source-pm0056-nvic)、[RM0008](#source-rm0008-exti)。"),
    ("docs/en/04-interrupts-nvic.md",
     "3. **Lab 3 (preemption evidence):** Add a TIM2 interrupt. In each ISR, drive one spare GPIO high on entry and low on exit. Capture both traces with a logic analyzer and verify that preemption priority 1 EXTI0 enters during preemption priority 2 TIM2.",
     "ch04-lab-evidence.png",
     "Handraw: what each of the three labs leaves behind (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). Where to look: one card per lab, each with its steps and its check. Proves the cleared flag, the before/after bounce counts, and the two-trace nesting order are three reviewable kinds of evidence. Cannot prove existing waveforms or measured data; the plate only gives the experiment design and its criteria. See [PM0056](#source-pm0056-nvic) and [RM0008](#source-rm0008-exti)."),
]

if __name__ == "__main__":
    bad = 0
    for spec in SPECS:
        if not embed_after_text(*spec):
            bad += 1
    if bad:
        raise SystemExit(f"{bad} embed(s) failed")
