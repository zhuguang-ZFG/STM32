#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared classic animation remakes (FA-002 bar). Filename kept; video untouched."""
from __future__ import annotations
import importlib, inspect, re, sys, xml.dom.minidom
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TOOLS = ROOT / "tools"
OUT = ROOT / "assets" / "animations"
sys.path.insert(0, str(TOOLS))
from svgkit import Svg, T, anim_fade, anim_flow, anim_tx, css_kf
W, H = 900, 620
REDUCED = "@media (prefers-reduced-motion: reduce){*{animation:none!important}}"

def _step_highlight(prefix: str, n: int, period=6.0, window=0.22, peak=0.35, rest=0.06) -> str:
    css = []
    step = 100.0 / n
    for i in range(n):
        a = i * step
        b = min(a + step * window, 99.2)
        name = f"{prefix}{i}-hl"
        css.append(f"@keyframes {name}{{0%,{a:.2f}%{{opacity:{rest}}}{a + 0.25:.2f}%,{b:.2f}%{{opacity:{peak}}}{min(b + 0.25, 100):.2f}%,100%{{opacity:{rest}}}}}")
        css.append(f".{prefix}{i}{{animation:{name} {period}s linear infinite;}}")
    return "\n".join(css)

def _seq_flash(prefix: str, n: int, period=5.0, window=0.55, peak=1.0, rest=0.22) -> str:
    css = []
    step = 100.0 / n
    for i in range(n):
        a = i * step
        b = min(a + step * window, 99.2)
        name = f"{prefix}{i}-sq"
        css.append(f"@keyframes {name}{{0%,{a:.2f}%{{opacity:{rest}}}{a + 0.3:.2f}%,{b:.2f}%{{opacity:{peak}}}{min(b + 0.3, 100):.2f}%,100%{{opacity:{rest}}}}}")
        css.append(f".{prefix}{i}{{animation:{name} {period}s linear infinite;}}")
    return "\n".join(css)


def nvic_interrupt_flow() -> Svg:
    s = Svg(W, H, "中断响应全流程",
            "外设置位 → NVIC 仲裁 → 硬件入栈 → 取向量 → ISR → 出栈；数字来自 Cortex-M3")
    s.header(title="NVIC 响应链：从 SR 置位到 ISR 返回",
             subtitle="mechanism · FA-002 continuous-line · F103 / Cortex-M3",
             tag="04 NVIC", tag_color=T.CYAN)
    css = []
    stages = [
        ("① 外设置位", "EXTI_PR / TIMx_SR", "IRQn 例：EXTI0=6", T.BLUE),
        ("② NVIC 仲裁", "抢占优先级更小先跑", "GROUP_4：4 抢占 / 0 子", T.CYAN),
        ("③ 硬件入栈", "R0-R3,R12,LR,PC,xPSR", "固定 32 B · SP→R0", T.VIOLET),
        ("④ 取向量", "VTOR + 4×(IRQn+16)", "Reset=0，IRQ 从 16 起", T.AMBER),
        ("⑤ 执行 ISR", "清标志 · 置事件 · 快退", "禁 HAL_Delay / printf", T.GREEN),
        ("⑥ 出栈返回", "EXC_RETURN 恢复现场", "可 tail-chain 下一 IRQ", T.PINK),
    ]
    x0, y0, bw, bh, gapx, gapy = 36, 96, 200, 96, 22, 18
    for i, (title, a, b, color) in enumerate(stages):
        r, c = divmod(i, 3)
        x = x0 + c * (bw + gapx)
        y = y0 + r * (bh + gapy + 28)
        s.rect(x, y, bw, bh, fill=T.PANEL, stroke=color, rx=8)
        s.rect(x, y, bw, 5, fill=color, rx=2)
        s.text(x + 14, y + 30, title, size=13, fill=T.TEXT, weight="700")
        s.text(x + 14, y + 54, a, size=11, fill=T.MUTED, mono=True)
        s.text(x + 14, y + 76, b, size=10.5, fill=T.DIM)
        s.rect(x, y, bw, bh, fill=color, rx=8, opacity=0.12, cls=f"nv{i}")
        if c < 2:
            s.arrow(x + bw + 3, y + bh / 2, x + bw + gapx - 3, y + bh / 2,
                    color=T.CYAN, sw=2, head=7, cls="nv-flow")
        if c == 2 and r == 0:
            s.arrow(x + bw / 2, y + bh + 2, x + bw / 2, y + bh + 24,
                    color=T.CYAN, sw=2, head=7, cls="nv-flow")
    css.append(_step_highlight("nv", 6, period=7.2, window=0.14, peak=0.32))
    css.append(anim_flow(".nv-flow", dur="1.2s", dash="7 10", shift=-17))
    s.title_block(36, 360, "硬件栈帧 8×4 B（低地址在左，SP 停在 R0）", color=T.VIOLET)
    regs = ["R0", "R1", "R2", "R3", "R12", "LR", "PC", "xPSR"]
    for i, reg in enumerate(regs):
        x = 36 + i * 64
        s.rect(x, 384, 58, 44, fill=T.PANEL2, stroke=T.VIOLET, rx=4)
        s.text(x + 29, 410, reg, size=12, anchor="middle", fill=T.TEXT, mono=True)
        s.rect(x, 384, 58, 44, fill=T.VIOLET, rx=4, opacity=0.1, cls=f"sf{i}")
    css.append(_seq_flash("sf", 8, period=4.8, window=0.4, peak=0.55, rest=0.08))
    s.text(560, 410, "ISR 可直接用 C；返回靠 EXC_RETURN", size=11, fill=T.MUTED)
    s.rect(36, 450, 828, 100, fill=T.BG2, stroke=T.AMBER, rx=8)
    s.text(52, 478, "同抢占优先级不能互抢 · Tail-chaining 可省一对出入栈",
           size=13, fill=T.TEXT, weight="700")
    s.text(52, 504, "例：TIM2(IRQ=28) 跑着时 EXTI0(IRQ=6) 若抢占更高 → 打断；同级则排队。",
           size=12, fill=T.MUTED)
    s.text(52, 528, "ISR 只清 SR / 置标志；长活丢主循环。匹配 sample-04-nvic-preempt-flow。",
           size=12, fill=T.DIM)
    css.append(REDUCED)
    s.add_style("\n".join(css))
    s.footer(note="自绘矢量动画 · FA-002 · NVIC 响应链，非逻辑分析仪实拍",
             label="自绘矢量动画 · STM32 知识轨")
    return s


def dma_circular() -> Svg:
    s = Svg(W, H, "DMA 循环模式：CPU 与搬运工并行",
            "ADC1→DMA1 CH1→buf[N]；CNDTR 倒数；HT/TC 半区所有权切换")
    s.header(title="DMA 循环：CNDTR 倒数与 HT/TC 半区所有权",
             subtitle="mechanism · FA-002 continuous-line · F103 DMA1 CH1 ← ADC1",
             tag="10 DMA", tag_color=T.GREEN)
    css = []
    boxes = [
        (40, "ADC1", "CH0 · PA0", "DR 半字", T.AMBER),
        (250, "DMA1 CH1", "CIRC · MINC=1", "PSIZE/MSIZE=16", T.CYAN),
        (470, "RAM buf[N]", "N=256 半字", "对齐 + volatile", T.GREEN),
    ]
    for x, title, a, b, color in boxes:
        s.rect(x, 96, 180, 100, fill=T.PANEL, stroke=color, rx=8)
        s.rect(x, 96, 180, 5, fill=color, rx=2)
        s.text(x + 90, 130, title, size=14, anchor="middle", fill=color, weight="700")
        s.text(x + 90, 154, a, size=11, anchor="middle", fill=T.MUTED, mono=True)
        s.text(x + 90, 176, b, size=11, anchor="middle", fill=T.DIM)
    s.arrow(224, 146, 246, 146, color=T.AMBER, sw=2, cls="dma-f")
    s.arrow(434, 146, 466, 146, color=T.CYAN, sw=2, cls="dma-f")
    css.append(anim_flow(".dma-f", dur="1.1s", dash="7 10", shift=-17))
    for i in range(3):
        s.circle(230, 146, 4.5, fill=T.CYAN, cls=f"pk{i}")
    css.append("\n".join(
        css_kf(f"pk{i}-mv", [("0%", "transform:translateX(0)"),
                             ("50%", "transform:translateX(400px)"),
                             ("51%,100%", "transform:translateX(400px)")])
        + f".pk{i}{{animation:pk{i}-mv 1.8s linear infinite {i * 0.45:.2f}s;}}"
        for i in range(3)))
    s.rect(40, 220, 400, 110, fill=T.PANEL, stroke=T.GREEN, rx=8)
    s.text(240, 252, "Half A  [0 .. N/2)", size=15, anchor="middle", fill=T.GREEN, weight="700")
    s.text(240, 280, "HT：CPU 可读 A · DMA 写 B", size=12, anchor="middle", fill=T.TEXT)
    s.text(240, 304, "CNDTR 刚过 128（N=256）", size=11, anchor="middle", fill=T.MUTED, mono=True)
    s.rect(40, 220, 400, 110, fill=T.GREEN, rx=8, opacity=0.12, cls="ha0")
    s.rect(460, 220, 400, 110, fill=T.PANEL, stroke=T.AMBER, rx=8)
    s.text(660, 252, "Half B  [N/2 .. N)", size=15, anchor="middle", fill=T.AMBER, weight="700")
    s.text(660, 280, "TC：CPU 可读 B · DMA 重装写 A", size=12, anchor="middle", fill=T.TEXT)
    s.text(660, 304, "CNDTR 回 256（循环）", size=11, anchor="middle", fill=T.MUTED, mono=True)
    s.rect(460, 220, 400, 110, fill=T.AMBER, rx=8, opacity=0.12, cls="ha1")
    css.append(_step_highlight("ha", 2, period=3.6, window=0.45, peak=0.28))
    s.title_block(40, 352, "CNDTR 现场（半字计数）", color=T.CYAN)
    marks = [("256", "armed"), ("192", "填 A"), ("128", "HT"), ("64", "填 B"), ("0→256", "TC")]
    for i, (n, lab) in enumerate(marks):
        x = 40 + i * 170
        col = T.GREEN if lab in ("HT", "TC") else T.CYAN
        s.rect(x, 378, 155, 64, fill=T.PANEL, stroke=col, rx=8)
        s.text(x + 77, 404, n, size=14, anchor="middle", fill=col, weight="700", mono=True)
        s.text(x + 77, 426, lab, size=12, anchor="middle", fill=T.TEXT)
        s.rect(x, 378, 155, 64, fill=col, rx=8, opacity=0.1, cls=f"cd{i}")
    css.append(_step_highlight("cd", 5, period=6.0, window=0.16))
    s.rect(40, 462, 820, 88, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(56, 490, "陷阱：HT/TC 后解析错半区；ISR 里 printf 超过半缓冲时间 → 覆盖。",
           size=13, fill=T.RED, weight="700")
    s.text(56, 516, "ISR 只置标志；主循环排空完成半区。对齐 sample-10-dma-circular-ht / cndtr-ledger。",
           size=12, fill=T.MUTED)
    s.text(56, 536, "F1：7 通道无 FIFO；F4/H7：Stream+FIFO+双缓冲。buf 4B 对齐 + volatile；H7 管 D-Cache。",
           size=11, fill=T.DIM)
    css.append(REDUCED)
    s.add_style("\n".join(css))
    s.footer(note="自绘矢量动画 · FA-002 · 环形 DMA 半区所有权，非逻辑分析仪截图",
             label="自绘矢量动画 · STM32 知识轨")
    return s


def freertos_scheduler() -> Svg:
    s = Svg(W, H, "FreeRTOS 任务调度：状态机 + 甘特",
            "SysTick=1 ms；就绪队列挑最高优先级；同优先级时间片轮转")
    s.header(title="FreeRTOS 调度：状态迁移与单核甘特",
             subtitle="mechanism · FA-002 continuous-line · configTICK_RATE_HZ=1000",
             tag="15 FreeRTOS", tag_color=T.PINK)
    css = []
    states = [
        ("就绪 Ready", 70, 100, T.GREEN, "st0", "在就绪链表等选中"),
        ("运行 Running", 390, 100, T.CYAN, "st1", "独占 CPU（单核）"),
        ("阻塞 Blocked", 390, 220, T.AMBER, "st2", "Delay / Queue / Sem"),
        ("挂起 Suspended", 70, 220, T.VIOLET, "st3", "vTaskSuspend"),
    ]
    for name, x, y, color, cls, sub in states:
        s.rect(x, y, 190, 70, fill=T.PANEL, stroke=color, rx=8)
        s.text(x + 95, y + 28, name, size=13, anchor="middle", fill=T.TEXT, weight="700")
        s.text(x + 95, y + 52, sub, size=10, anchor="middle", fill=T.MUTED)
        s.rect(x, y, 190, 70, fill=color, rx=8, opacity=0.14, cls=cls)
    css.append(_step_highlight("st", 4, period=5.6, window=0.2, peak=0.34))
    s.arrow(264, 130, 386, 130, color=T.GREEN, sw=2, cls="e-flow")
    s.text(325, 118, "调度选中", size=10, anchor="middle", fill=T.GREEN)
    s.arrow(584, 130, 720, 130, color=T.CYAN, sw=2, head=6)
    s.text(652, 118, "抢占/时间片", size=10, anchor="middle", fill=T.MUTED)
    s.line(720, 130, 720, 88, stroke=T.CYAN, sw=2)
    s.arrow(720, 88, 264, 88, color=T.CYAN, sw=2, head=6)
    s.line(264, 88, 264, 130, stroke=T.CYAN, sw=2)
    s.arrow(485, 174, 485, 216, color=T.AMBER, sw=2, head=6)
    s.text(496, 198, "vTaskDelay", size=10, fill=T.AMBER)
    s.line(390, 255, 262, 255, stroke=T.AMBER, sw=2)
    s.arrow(262, 255, 165, 255, color=T.AMBER, sw=2, head=6)
    s.text(280, 274, "超时 / 事件", size=10, fill=T.AMBER)
    css.append(anim_flow(".e-flow", dur="1.3s", dash="6 8", shift=-14))
    s.text(40, 318, "单核甘特（同刻仅一条色带）· Tick=1 ms", size=12, fill=T.MUTED)
    rows = [
        ("T1 pri=3", T.CYAN, [(0, 8), (24, 6)]),
        ("T2 pri=2", T.GREEN, [(8, 8)]),
        ("T3 pri=1", T.AMBER, [(16, 8)]),
        ("Idle", T.DIM, [(30, 2)]),
    ]
    scale = 700 / 32
    for i, (name, color, spans) in enumerate(rows):
        y = 334 + i * 34
        s.text(40, y + 20, name, size=11, fill=color, mono=True)
        s.rect(150, y, 700, 26, fill=T.BG2, stroke=T.GRID, rx=4)
        for x0, w in spans:
            s.rect(150 + x0 * scale, y + 2, w * scale - 1, 22, fill=color, rx=4, opacity=0.88)
        for t in range(0, 33, 4):
            s.line(150 + t * scale, y, 150 + t * scale, y + 26, stroke=T.GRID, sw=1)
    s.line(150, 328, 150, 472, stroke=T.RED, sw=1.5, cls="cursor")
    css.append(anim_tx(".cursor", dur="5s", x1=0, x2=700))
    s.text(150, 488, "0 ms", size=9, fill=T.DIM)
    s.text(850, 488, "32 ms", size=9, fill=T.DIM, anchor="end")
    s.rect(40, 500, 820, 56, fill=T.BG2, stroke=T.STROKE, rx=8)
    s.text(56, 522, "铁律：数字越大优先级越高（与 NVIC 相反）· ISR 只用 FromISR · 用 HighWaterMark 看栈",
           size=12, fill=T.TEXT, weight="700")
    s.text(56, 542, "坑：未创建任务就 StartScheduler；在 ISR 里调阻塞 API 触发断言。对齐 sample-15-rtos-tick-flow。",
           size=11, fill=T.MUTED)
    css.append(REDUCED)
    s.add_style("\n".join(css))
    s.footer(note="自绘矢量动画 · FA-002 · FreeRTOS 调度机制，非 Tracealyzer 实拍",
             label="自绘矢量动画 · STM32 知识轨")
    return s


def rtos_system_layers() -> Svg:
    s = Svg(W, H, "嵌入式系统层：硬件到应用",
            "每层有所有者、超时与故障边界；RTOS 内核只是其中一层")
    s.header(title="系统分层：所有权 · 超时 · 故障边界",
             subtitle="mechanism · FA-002 continuous-line · ch28 选型前先列约束",
             tag="28 系统", tag_color=T.VIOLET)
    css = []
    layers = [
        ("应用", "控制回路 · 采集 · HMI · OTA 策略", "入口前置 · 出口结果码", T.CYAN),
        ("系统服务", "网络 · FS · 日志 · Shell · 时间", "组件可替换，契约不变", T.GREEN),
        ("OS API", "原生 / CMSIS-RTOS2", "统一接口，不抹平语义", T.AMBER),
        ("内核", "调度 · IPC · 定时器 · 堆 · 钩子", "Tick=1 ms 常见起点", T.VIOLET),
        ("BSP / 驱动", "HAL/LL · RTT device · Zephyr DM", "外设时钟与引脚归属", T.PINK),
        ("硬件", "Cortex-M · NVIC · DMA · Cache · PHY", "LQFP / BGA 封装约束", T.RED),
    ]
    x, y, bw, bh, gap = 40, 94, 540, 60, 10
    for i, (name, detail, rule, color) in enumerate(layers):
        yy = y + i * (bh + gap)
        s.rect(x, yy, bw, bh, fill=T.PANEL, stroke=color, rx=8)
        s.rect(x, yy, 8, bh, fill=color, rx=2)
        s.text(x + 24, yy + 24, name, size=14, fill=color, weight="700")
        s.text(x + 120, yy + 24, detail, size=11, fill=T.MUTED)
        s.text(x + 24, yy + 46, rule, size=10, fill=T.DIM)
        s.rect(x, yy, bw, bh, fill=color, rx=8, opacity=0.1, cls=f"ly{i}")
        if i < len(layers) - 1:
            s.arrow(x + bw / 2, yy + bh + 2, x + bw / 2, yy + bh + gap - 2,
                    color=T.CYAN, sw=2, head=5, cls="ly-flow")
    css.append(_step_highlight("ly", 6, period=7.2, window=0.14, peak=0.3))
    css.append(anim_flow(".ly-flow", dur="1.1s", dash="4 7", shift=-11))
    s.text(610, 110, "怎么选内核", size=14, fill=T.TEXT, weight="700")
    cards = [
        ("裸机", "状态机清晰 · 资源极紧", T.DIM),
        ("FreeRTOS", "小内核 · 自己拼服务", T.CYAN),
        ("RT-Thread", "设备框架 + 组件", T.GREEN),
        ("Zephyr", "Kconfig + Devicetree", T.AMBER),
    ]
    for i, (name, detail, color) in enumerate(cards):
        yy = 130 + i * 88
        s.rect(600, yy, 260, 72, fill=T.BG2, stroke=color, rx=8)
        s.text(616, yy + 28, name, size=13, fill=color, weight="700")
        s.text(616, yy + 52, detail, size=11, fill=T.MUTED)
        s.rect(600, yy, 260, 72, fill=color, rx=8, opacity=0.08, cls=f"ch{i}")
    css.append(_seq_flash("ch", 4, period=5.6, window=0.55, peak=0.4, rest=0.06))
    s.rect(600, 490, 260, 60, fill=T.PANEL, stroke=T.RED, rx=8)
    s.text(730, 514, "先列约束，再选生态", size=13, anchor="middle", fill=T.RED, weight="700")
    s.text(730, 536, "勿用 API 熟悉度代替需求", size=11, anchor="middle", fill=T.MUTED)
    s.rect(40, 530, 540, 36, fill=T.BG2, stroke=T.STROKE, rx=8)
    s.text(52, 554, "不变量：ISR 只发事件 · 资源单所有者 · 阻塞有截止 · 证据定位第一处分歧",
           size=11, fill=T.TEXT)
    css.append(REDUCED)
    s.add_style("\n".join(css))
    s.footer(note="自绘矢量动画 · FA-002 · 系统分层边界，非厂商架构海报",
             label="自绘矢量动画 · STM32 知识轨")
    return s


def network_packet_journey() -> Svg:
    s = Svg(W, H, "MQTT 消息穿过 STM32 网络栈",
            "每层只管自己的语义：消息 · 字节流 · 寻址 · 帧 · 物理")
    s.header(title="网络包旅程：从 APP 到 PHY 的证据链",
             subtitle="mechanism · FA-002 continuous-line · MQTT QoS1 over TLS/TCP",
             tag="27 网络", tag_color=T.CYAN)
    css = []
    layers = [
        ("APP", "{temp:23.6}", "业务序号 / 幂等键", T.PINK),
        ("MQTT", "PUBLISH · QoS1", "至少一次 ≠ 业务一次", T.VIOLET),
        ("TLS", "record + tag", "CA · SNI · 时间 · RNG", T.AMBER),
        ("TCP", "seq · ACK · RTX", "字节流无消息边界", T.GREEN),
        ("IP", "src/dst · TTL", "地址 · 掩码 · 网关", T.CYAN),
        ("Eth", "dst MAC · type · FCS", "ARP / 二层广播域", T.BLUE),
        ("DMA", "desc → RMII → PHY", "SRAM 对齐 · Cache 一致", T.ORANGE),
    ]
    x, y0, bw, bh, gap = 48, 92, 500, 52, 8
    for i, (name, payload, boundary, color) in enumerate(layers):
        y = y0 + i * (bh + gap)
        s.rect(x, y, bw, bh, fill=T.PANEL, stroke=color, rx=8)
        s.rect(x, y, 78, bh, fill=T.BG2, stroke=color, rx=8)
        s.text(x + 39, y + 30, name, size=12, anchor="middle", fill=color, weight="700")
        s.text(x + 96, y + 20, payload, size=11, mono=True, fill=T.TEXT, weight="600")
        s.text(x + 96, y + 40, boundary, size=10, fill=T.MUTED)
        s.rect(x, y, bw, bh, fill=color, rx=8, opacity=0.1, cls=f"net{i}")
        if i < len(layers) - 1:
            s.arrow(x + bw / 2, y + bh + 1, x + bw / 2, y + bh + gap - 1,
                    color=T.CYAN, sw=2, head=5, cls="net-flow")
    css.append(_step_highlight("net", 7, period=7.0, window=0.12, peak=0.3))
    css.append(anim_flow(".net-flow", dur="1.0s", dash="4 7", shift=-11))
    s.rect(572, 92, 288, 200, fill=T.BG2, stroke=T.STROKE, rx=8)
    s.text(590, 118, "链路证据顺序", size=13, fill=T.TEXT, weight="700")
    proof = [
        ("1", "PHY link", "读 BSR，不只看 LED", T.ORANGE),
        ("2", "ARP", "who-has / is-at", T.BLUE),
        ("3", "IP", "ping≠业务可达", T.CYAN),
        ("4", "TCP", "SYN→SYN/ACK→ACK", T.GREEN),
        ("5", "TLS/MQTT", "握手 + CONNACK", T.VIOLET),
    ]
    for i, (n, key, note, color) in enumerate(proof):
        yy = 148 + i * 28
        s.circle(600, yy - 4, 9, fill=color)
        s.text(600, yy, n, size=9, anchor="middle", fill=T.BG, weight="700")
        s.text(620, yy, key, size=11, mono=True, fill=color, weight="700")
        s.text(700, yy, note, size=10, fill=T.MUTED)
    s.rect(572, 310, 288, 220, fill=T.PANEL, stroke=T.RED, rx=8)
    s.text(590, 338, "五个不能混为一谈", size=13, fill=T.TEXT, weight="700")
    warnings = [
        ("TCP ACK", "≠ 业务已落盘"),
        ("MQTT QoS1", "至少一次，要幂等"),
        ("ping 通", "≠ DNS/TLS/MQTT OK"),
        ("link up", "≠ DMA/Cache/IP OK"),
        ("收到一段", "≠ 流式分帧完成"),
    ]
    for i, (claim, truth) in enumerate(warnings):
        yy = 368 + i * 30
        s.text(590, yy, "×", size=13, fill=T.RED, weight="700")
        s.text(610, yy, claim, size=11, mono=True, fill=T.TEXT)
        s.text(710, yy, truth, size=10, fill=T.MUTED)
    s.rect(48, 530, 500, 36, fill=T.BG2, stroke=T.STROKE, rx=8)
    s.text(60, 554, "分层验收：PHY → ARP/IP → TCP → TLS → MQTT → 业务语义",
           size=12, fill=T.TEXT, weight="700")
    css.append(REDUCED)
    s.add_style("\n".join(css))
    s.footer(note="自绘矢量动画 · FA-002 · 网络分层证据链，非抓包截图",
             label="自绘矢量动画 · STM32 知识轨")
    return s


def uart_idle_dma() -> Svg:
    s = Svg(W, H, "UART + DMA + IDLE：两类接收契约",
            "Size=首个未写位置；交给业务的永远是新增字节区间")
    s.header(title="UART IDLE+DMA：契约 A（Normal）与契约 B（Circular）",
             subtitle="mechanism · FA-002 continuous-line · 附录 A · 115200 8N1",
             tag="附录 A", tag_color=T.CYAN)
    css = []
    s.title_block(40, 92, "① 总线：字节阵到达，间隙 ≥1 帧触发 IDLE（约 86.8 μs @115200）",
                  color=T.AMBER)
    for i, lab in enumerate(["D0", "D1", "D2", "D3", "D4", "…", "IDLE"]):
        x = 48 + i * 78
        col = T.RED if lab == "IDLE" else T.CYAN
        s.rect(x, 118, 70, 44, fill=T.PANEL, stroke=col, rx=8)
        s.text(x + 35, 146, lab, size=13, anchor="middle", fill=col, weight="700", mono=True)
        s.rect(x, 118, 70, 44, fill=col, rx=8, opacity=0.12, cls=f"by{i}")
    css.append(_step_highlight("by", 7, period=5.6, window=0.12, peak=0.32))
    s.title_block(40, 184, "② DMA 缓冲 cap=128：Size = 首个未写位置（1..128）", color=T.GREEN)
    s.rect(40, 210, 820, 56, fill=T.PANEL, stroke=T.GREEN, rx=8)
    s.rect(40, 210, 280, 56, fill=T.GREEN, opacity=0.18, rx=8, cls="buf")
    s.text(60, 244, "写满区 [0, Size)", size=13, fill=T.GREEN, weight="700")
    s.text(340, 244, "Size=7 例", size=13, fill=T.TEXT, mono=True, weight="700")
    s.text(480, 244, "HT@64 仅契约 B 使用", size=12, fill=T.MUTED)
    s.text(720, 244, "127", size=12, fill=T.DIM, mono=True)
    css.append(anim_fade(".buf", dur="2.4s", a=0.1, b=0.35))
    s.rect(40, 288, 400, 200, fill=T.BG2, stroke=T.CYAN, rx=8)
    s.text(56, 316, "契约 A · Normal", size=14, fill=T.CYAN, weight="700")
    for i, line in enumerate([
        "ReceiveToIdle_DMA 后立即关 HT",
        "IDLE（或 TC）→ RxEventCallback(Size)",
        "复制 [0, Size) 进软件队列",
        "回调内重新武装，并再次关 HT",
        "适合：不定长命令帧",
    ]):
        s.text(56, 348 + i * 24, f"· {line}", size=12, fill=T.TEXT)
        s.rect(48, 336 + i * 24, 6, 16, fill=T.CYAN, rx=2, cls=f"ca{i}")
    css.append(_seq_flash("ca", 5, period=5.0, window=0.45, peak=1.0, rest=0.25))
    s.rect(460, 288, 400, 200, fill=T.BG2, stroke=T.VIOLET, rx=8)
    s.text(476, 316, "契约 B · Circular", size=14, fill=T.VIOLET, weight="700")
    for i, line in enumerate([
        "开 HT、TC、IDLE 三个来源",
        "new = (Size − old_pos) mod cap",
        "只交新增区间给业务",
        "再 old_pos = Size",
        "适合：连续流 / 高吞吐",
    ]):
        s.text(476, 348 + i * 24, f"· {line}", size=12, fill=T.TEXT)
        s.rect(468, 336 + i * 24, 6, 16, fill=T.VIOLET, rx=2, cls=f"cb{i}")
    css.append(_seq_flash("cb", 5, period=5.0, window=0.45, peak=1.0, rest=0.25))
    s.rect(40, 508, 820, 48, fill=T.PANEL, stroke=T.RED, rx=8)
    s.text(56, 538, "陷阱：把 Size 当长度却忘了 Circular 取模；HT 回调里做重活超过半缓冲窗口。",
           size=13, fill=T.RED, weight="700")
    css.append(REDUCED)
    s.add_style("\n".join(css))
    s.footer(note="自绘矢量动画 · FA-002 · UART IDLE+DMA 契约，非逻辑分析仪实拍",
             label="自绘矢量动画 · STM32 知识轨 · 附录 A")
    return s


TARGETS = [
    ("nvic-interrupt-flow.svg", "anim_gpio.py", "nvic_interrupt_flow", nvic_interrupt_flow),
    ("dma-circular.svg", "anim_sys.py", "dma_circular", dma_circular),
    ("freertos-scheduler.svg", "anim_sys.py", "freertos_scheduler", freertos_scheduler),
    ("rtos-system-layers.svg", "anim_sys.py", "rtos_system_layers", rtos_system_layers),
    ("network-packet-journey.svg", "anim_comm.py", "network_packet_journey", network_packet_journey),
    ("uart-idle-dma.svg", "anim_comm.py", "uart_idle_dma", uart_idle_dma),
]

def _replace_function(path: Path, fn_name: str, new_src: str) -> None:
    text = path.read_text(encoding="utf-8")
    pat = re.compile(rf"(def {re.escape(fn_name)}\(\)[\s\S]*?)(?=\ndef |\nALL\s*=|\Z)")
    m = pat.search(text)
    if not m:
        raise SystemExit(f"function {fn_name} not found in {path}")
    body = new_src.rstrip() + "\n\n\n"
    path.write_text(text[: m.start()] + body + text[m.end():], encoding="utf-8")

HELPER_BLOCK = (
    "\n"
    'REDUCED = "@media (prefers-reduced-motion: reduce)'
    '{*{animation:none!important}}"\n'
    "\n\n"
    "def _step_highlight(prefix: str, n: int, period=6.0, window=0.22,\n"
    "                    peak=0.35, rest=0.06) -> str:\n"
    "    css = []\n"
    "    step = 100.0 / n\n"
    "    for i in range(n):\n"
    "        a = i * step\n"
    "        b = min(a + step * window, 99.2)\n"
    '        name = f"{prefix}{i}-hl"\n'
    "        css.append(\n"
    '            f"@keyframes {name}{{0%,{a:.2f}%{{opacity:{rest}}}"\n'
    '            f"{a + 0.25:.2f}%,{b:.2f}%{{opacity:{peak}}}"\n'
    '            f"{min(b + 0.25, 100):.2f}%,100%{{opacity:{rest}}}}}"\n'
    "        )\n"
    '        css.append(f".{prefix}{i}{{animation:{name} {period}s linear infinite;}}")\n'
    '    return "\\n".join(css)\n'
    "\n\n"
    "def _seq_flash(prefix: str, n: int, period=5.0, window=0.55,\n"
    "               peak=1.0, rest=0.22) -> str:\n"
    "    css = []\n"
    "    step = 100.0 / n\n"
    "    for i in range(n):\n"
    "        a = i * step\n"
    "        b = min(a + step * window, 99.2)\n"
    '        name = f"{prefix}{i}-sq"\n'
    "        css.append(\n"
    '            f"@keyframes {name}{{0%,{a:.2f}%{{opacity:{rest}}}"\n'
    '            f"{a + 0.3:.2f}%,{b:.2f}%{{opacity:{peak}}}"\n'
    '            f"{min(b + 0.3, 100):.2f}%,100%{{opacity:{rest}}}}}"\n'
    "        )\n"
    '        css.append(f".{prefix}{i}{{animation:{name} {period}s linear infinite;}}")\n'
    '    return "\\n".join(css)\n'
    "\n"
)

def _ensure_helpers(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    changed = False
    if path.name == "anim_gpio.py" and "css_kf" not in text:
        old = "from svgkit import Svg, T, anim_blink, anim_fade, anim_flow, anim_tx"
        if old in text:
            text = text.replace(old, old + ", css_kf")
            changed = True
    has_all = (
        "def _step_highlight(" in text
        and "def _seq_flash(" in text
        and "REDUCED =" in text
    )
    if has_all:
        if changed:
            path.write_text(text, encoding="utf-8")
            print(f"[helpers-import] {path.name}")
        return
    text = re.sub(r"\nREDUCED = [^\n]*\n", "\n", text, count=1)
    text = re.sub(r"\ndef _step_highlight\([\s\S]*?(?=\ndef |\nALL\s*=)", "\n", text, count=1)
    text = re.sub(r"\ndef _seq_flash\([\s\S]*?(?=\ndef |\nALL\s*=)", "\n", text, count=1)
    if "W, H = 900, 620\n" not in text:
        raise SystemExit(f"W,H marker missing in {path}")
    text = text.replace("W, H = 900, 620\n", "W, H = 900, 620\n" + HELPER_BLOCK, 1)
    path.write_text(text, encoding="utf-8")
    print(f"[helpers] {path.name}")

def apply() -> None:
    for mod_file in ("anim_gpio.py", "anim_sys.py", "anim_comm.py"):
        _ensure_helpers(TOOLS / mod_file)
    for out_name, mod_file, fn_name, fn in TARGETS:
        src = inspect.getsource(fn)
        _replace_function(TOOLS / mod_file, fn_name, src)
        print(f"[src] {mod_file}::{fn_name}")
    for name in ("anim_gpio", "anim_sys", "anim_comm", "svgkit"):
        sys.modules.pop(name, None)
    from anim_gpio import nvic_interrupt_flow as f1
    from anim_sys import dma_circular as f2, freertos_scheduler as f3, rtos_system_layers as f4
    from anim_comm import network_packet_journey as f5, uart_idle_dma as f6
    regen = [
        ("nvic-interrupt-flow.svg", f1),
        ("dma-circular.svg", f2),
        ("freertos-scheduler.svg", f3),
        ("rtos-system-layers.svg", f4),
        ("network-packet-journey.svg", f5),
        ("uart-idle-dma.svg", f6),
    ]
    for name, fn in regen:
        svg = fn()
        path = OUT / name
        svg.save(path)
        xml.dom.minidom.parse(str(path))
        print(f"[ok] assets/animations/{name}  {path.stat().st_size} B")

if __name__ == "__main__":
    apply()
