#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 assets/diagrams/*.svg —— 静态框图（架构、工程结构、总线、优先级）。"""

from __future__ import annotations

from svgkit import Svg, T

W, H = 900, 560


def first_lab_wiring() -> Svg:
    s = Svg(W, H, "第一次上电：一个主供电路径，四根 SWD 线",
            "BluePill 由 Micro-USB 供电时，不再连接 ST-Link 的 3.3V；第一课暂不接 USB-TTL")
    s.header(tag="00 接线 · IG-002", tag_color=T.GREEN)

    s.rect(38, 96, 190, 112, fill=T.PANEL, stroke=T.GREEN, rx=8)
    s.text(133, 126, "USB 电源", size=14, anchor="middle", fill=T.TEXT, weight="800")
    s.text(133, 154, "5 V → Micro-USB", size=11, anchor="middle", fill=T.GREEN,
           mono=True)
    s.text(133, 181, "本实验唯一主供电", size=10, anchor="middle", fill=T.MUTED)

    s.rect(354, 86, 300, 230, fill="#123a2e", stroke=T.GREEN, rx=8)
    s.text(504, 119, "BluePill · STM32F103C8T6", size=15, anchor="middle",
           fill="#dbeafe", weight="800")
    s.rect(430, 145, 148, 86, fill="#151922", stroke="#9db8ff", rx=4)
    s.text(504, 181, "STM32F103C8T6", size=11, anchor="middle", mono=True,
           fill="#dbeafe", weight="700")
    s.text(504, 207, "BOOT0 = 0", size=10, anchor="middle", mono=True,
           fill=T.AMBER)
    s.text(376, 272, "PC13 LED · 低电平亮", size=10.5, fill="#dbeafe")
    s.text(632, 296, "VDD 实测约 3.3 V", size=10.5, anchor="end", fill=T.CYAN)

    s.arrow(230, 152, 350, 152, color=T.GREEN, sw=2, head=8)
    s.text(290, 137, "供电", size=10, anchor="middle", fill=T.GREEN)

    s.rect(38, 258, 190, 202, fill=T.PANEL, stroke=T.CYAN, rx=8)
    s.text(133, 290, "ST-Link · 仅调试", size=14, anchor="middle", fill=T.TEXT,
           weight="800")
    pins = [("SWDIO", "PA13", T.CYAN), ("SWCLK", "PA14", T.CYAN),
            ("GND", "GND", T.MUTED), ("NRST", "NRST 可选", T.VIOLET)]
    for i, (left, right, color) in enumerate(pins):
        yy = 322 + i * 30
        s.text(58, yy, left, size=10.5, mono=True, fill=color, weight="700")
        s.text(208, yy, right, size=10.2, mono=True, anchor="end", fill=T.MUTED)
        s.line(230, yy - 4, 350, 174 + i * 30, stroke=color, sw=2)
    s.text(58, 438, "3.3V", size=10.5, mono=True, fill=T.RED, weight="800")
    s.text(208, 438, "不接", size=10.5, anchor="end", fill=T.RED, weight="800")
    s.line(232, 425, 260, 449, stroke=T.RED, sw=2)
    s.line(260, 425, 232, 449, stroke=T.RED, sw=2)

    s.rect(688, 96, 174, 220, fill=T.BG2, stroke=T.AMBER, rx=8)
    s.text(775, 127, "上电前 3 项", size=13, anchor="middle", fill=T.TEXT, weight="800")
    checks = ["① BOOT0 = 0", "② GND 共地", "③ 只有一个主供电"]
    for i, check in enumerate(checks):
        s.text(708, 164 + i * 39, check, size=10.8, fill=T.MUTED)
    s.text(775, 286, "上电后量 VDD", size=11, anchor="middle", fill=T.CYAN,
           weight="700")

    s.rect(354, 348, 508, 112, fill=T.PANEL, stroke=T.STROKE, rx=8)
    s.text(376, 379, "USB-TTL 留到 UART 章节", size=13, fill=T.TEXT, weight="800")
    s.text(376, 407, "第一课不接 PA9 / PA10，也不把 USB-TTL 的 3.3V 并入供电。",
           size=10.5, fill=T.MUTED)
    s.text(376, 435, "先把编译、SWD、复位和 PC13 波形四件事分别证明。", size=10.5,
           fill=T.GREEN, weight="700")
    s.footer("视觉规范：FA-029 几何图解叙事 · IG-002 中心标注 · C-03 / C-10 / C-27 / C-31",
             label="自绘矢量图 · STM32 知识库")
    return s


def first_success_gates() -> Svg:
    s = Svg(W, H, "第一次成功不是“灯亮了”，而是四份证据对得上",
            "构建、烧录、复位路径和引脚频率逐关验收；前一关没有证据，不改后一关")
    s.header(tag="00 验收 · IG-008", tag_color=T.CYAN)

    gates = [
        ("1 · Build", "ELF / AXF", "编译退出码 = 0", T.GREEN),
        ("2 · Flash", "0x08000000", "Program + verify 通过", T.CYAN),
        ("3 · Reset", "BOOT0 = 0", "main 断点命中", T.AMBER),
        ("4 · Measure", "PC13 · active-low", "T = 1.000 s", T.VIOLET),
    ]
    x0, y, bw, gap = 34, 105, 184, 34
    for i, (title, target, evidence, color) in enumerate(gates):
        x = x0 + i * (bw + gap)
        s.rect(x, y, bw, 132, fill=T.PANEL, stroke=color, rx=8)
        s.rect(x, y, bw, 7, fill=color, rx=2)
        s.text(x + 18, y + 40, title, size=13, fill=color, weight="800")
        s.text(x + 18, y + 72, target, size=10.5, mono=True, fill=T.TEXT,
               weight="700")
        s.text(x + 18, y + 102, evidence, size=10, fill=T.MUTED)
        if i < len(gates) - 1:
            s.arrow(x + bw + 4, y + 66, x + bw + gap - 4, y + 66,
                    color=T.CYAN, sw=2, head=6)

    s.rect(34, 278, 832, 184, fill=T.BG2, stroke=T.STROKE, rx=8)
    s.text(54, 309, "第一处失败决定下一步", size=13, fill=T.TEXT, weight="800")
    failures = [
        ("没有 ELF", "先修编译/链接，不碰线", T.GREEN),
        ("verify 失败", "查供电、GND、SWDIO、SWCLK", T.CYAN),
        ("main 不进", "查 BOOT0、NRST、向量表", T.AMBER),
        ("频率不对", "查时钟、SysTick、半周期", T.VIOLET),
    ]
    for i, (symptom, action, color) in enumerate(failures):
        yy = 344 + i * 28
        s.text(54, yy, symptom, size=10.5, mono=True, fill=color, weight="800")
        s.text(216, yy, action, size=10.5, fill=T.MUTED)

    s.rect(590, 326, 250, 108, fill=T.PANEL, stroke=T.VIOLET, rx=8)
    s.text(610, 355, "1 Hz 的可复算条件", size=12, fill=T.TEXT, weight="800")
    s.text(610, 383, "HAL_Delay(500) × 2", size=11, mono=True, fill=T.CYAN)
    s.text(610, 409, "高 500 ms + 低 500 ms", size=10.5, fill=T.MUTED)
    s.footer("视觉规范：FA-002 概念连续线 · IG-008 多路径流程 · C-03 / C-10 / C-27 / C-31",
             label="自绘矢量图 · STM32 知识库")
    return s


def dma_buffer_ownership() -> Svg:
    s = Svg(W, H, "DMA 缓冲区：谁能写，谁能读",
            "外设数据寄存器经 DMA 写入循环数组；HT/TC 交出半区，CNDTR 统计数据项而不是字节")
    s.header(tag="10 DMA · IG-004", tag_color=T.CYAN)

    s.rect(34, 102, 184, 112, fill=T.PANEL, stroke=T.AMBER, rx=8)
    s.text(126, 132, "外设 DR", size=14, anchor="middle", fill=T.TEXT, weight="800")
    s.text(126, 160, "固定地址", size=10.5, anchor="middle", mono=True, fill=T.AMBER)
    s.text(126, 187, "每次请求产生 1 项", size=10, anchor="middle", fill=T.MUTED)

    s.rect(302, 88, 250, 144, fill=T.PANEL, stroke=T.CYAN, rx=8)
    s.text(427, 120, "DMA 通道", size=14, anchor="middle", fill=T.TEXT, weight="800")
    s.text(324, 151, "映射", size=10.5, fill=T.MUTED)
    s.text(528, 151, "DMA1_CH1", size=10.5, anchor="end", mono=True, fill=T.CYAN)
    s.text(324, 178, "宽度", size=10.5, fill=T.MUTED)
    s.text(528, 178, "half-word", size=10.5, anchor="end", mono=True, fill=T.CYAN)
    s.text(324, 205, "CNDTR", size=10.5, fill=T.MUTED)
    s.text(528, 205, "剩余数据项", size=10.5, anchor="end", fill=T.CYAN, weight="700")

    s.arrow(222, 158, 298, 158, color=T.AMBER, sw=2, head=7)
    s.text(260, 143, "request", size=9.5, anchor="middle", mono=True, fill=T.MUTED)

    s.rect(638, 82, 228, 176, fill=T.BG2, stroke=T.GREEN, rx=8)
    s.text(752, 112, "rx_buf[64]", size=13, anchor="middle", mono=True, fill=T.TEXT, weight="800")
    s.rect(660, 132, 184, 42, fill=T.PANEL, stroke=T.GREEN, rx=4)
    s.text(752, 158, "前半区 0…31", size=10.5, anchor="middle", fill=T.GREEN, weight="700")
    s.rect(660, 190, 184, 42, fill=T.PANEL, stroke=T.VIOLET, rx=4)
    s.text(752, 216, "后半区 32…63", size=10.5, anchor="middle", fill=T.VIOLET, weight="700")
    s.arrow(556, 158, 634, 158, color=T.CYAN, sw=2, head=7)
    s.text(595, 143, "MINC", size=9.5, anchor="middle", mono=True, fill=T.MUTED)

    s.rect(34, 296, 832, 166, fill=T.BG2, stroke=T.STROKE, rx=8)
    s.text(54, 326, "交接规则", size=13, fill=T.TEXT, weight="800")
    rules = [
        ("DMA 写前半区", "CPU 只处理后半区", T.GREEN),
        ("HT：CNDTR = 32", "前半区交给 CPU", T.CYAN),
        ("DMA 写后半区", "CPU 只处理前半区", T.VIOLET),
        ("TC：CNDTR 回卷", "后半区交给 CPU", T.AMBER),
    ]
    for i, (left, right, color) in enumerate(rules):
        yy = 356 + i * 25
        s.text(54, yy, left, size=10.5, mono=True, fill=color, weight="700")
        s.text(286, yy, right, size=10.5, fill=T.MUTED)

    s.rect(560, 324, 280, 112, fill=T.PANEL, stroke=T.RED, rx=8)
    s.text(580, 352, "两种静默错误", size=12, fill=T.RED, weight="800")
    s.text(580, 380, "通道错：CNDTR 不动", size=10.5, fill=T.MUTED)
    s.text(580, 407, "宽度错：项数对，字节边界错", size=10.5, fill=T.MUTED)

    s.footer("视觉规范：FA-002 概念连续线 · IG-004 双列边界 · C-03 / C-10 / C-27 / C-31",
             label="自绘矢量图 · STM32 知识库")
    return s


def watchdog_reset_evidence() -> Svg:
    s = Svg(W, H, "看门狗复位必须留下三份证据",
            "触发条件、复位原因和重启后的持久记录要能互相对账；只看到 LED 重闪不算验收")
    s.header(tag="11 复位 · IG-008", tag_color=T.RED)
    gates = [
        ("1 · 故障", "停止喂狗", "GPIO 拉高标记", T.AMBER),
        ("2 · 超时", "IWDG → 0", "测得复位延迟", T.RED),
        ("3 · 复位", "RCC_CSR", "IWDGRSTF = 1", T.CYAN),
        ("4 · 重启", "BKP / Flash", "boot_id + 1", T.GREEN),
    ]
    x0, y, bw, gap = 32, 104, 184, 34
    for i, (title, target, evidence, color) in enumerate(gates):
        x = x0 + i * (bw + gap)
        s.rect(x, y, bw, 132, fill=T.PANEL, stroke=color, rx=8)
        s.text(x + 16, y + 38, title, size=13, fill=color, weight="800")
        s.text(x + 16, y + 72, target, size=10.5, mono=True, fill=T.TEXT, weight="700")
        s.text(x + 16, y + 102, evidence, size=10, fill=T.MUTED)
        if i < 3:
            s.arrow(x + bw + 4, y + 66, x + bw + gap - 4, y + 66,
                    color=T.CYAN, sw=2, head=6)

    s.rect(34, 278, 514, 178, fill=T.BG2, stroke=T.STROKE, rx=8)
    s.text(54, 310, "对账项", size=13, fill=T.TEXT, weight="800")
    rows = [
        ("延迟", "由 LSI 实测决定，不拿 40 kHz 典型值当保证", T.AMBER),
        ("原因", "上电先读 IWDGRSTF，再清复位标志", T.CYAN),
        ("持久", "RTC/BKP 继续，普通 SRAM 不继续", T.GREEN),
        ("恢复", "记录 boot_id 后再重新使能业务", T.VIOLET),
    ]
    for i, (name, note, color) in enumerate(rows):
        yy = 342 + i * 27
        s.text(54, yy, name, size=10.5, fill=color, weight="800")
        s.text(126, yy, note, size=10.2, fill=T.MUTED)

    s.rect(574, 278, 292, 178, fill=T.PANEL, stroke=T.RED, rx=8)
    s.text(594, 310, "不能单独证明", size=13, fill=T.RED, weight="800")
    s.text(594, 345, "LED 又开始闪", size=10.5, fill=T.MUTED)
    s.text(594, 374, "串口重新打印启动语", size=10.5, fill=T.MUTED)
    s.text(594, 403, "大约一秒后复位", size=10.5, fill=T.MUTED)
    s.text(594, 432, "这些都缺少复位原因", size=10.5, fill=T.RED, weight="700")
    s.footer("视觉规范：FA-002 概念连续线 · IG-008 多路径流程 · C-03 / C-10 / C-27 / C-31",
             label="自绘矢量图 · STM32 知识库")
    return s


def iap_acceptance_gates() -> Svg:
    s = Svg(W, H, "IAP 升级要过五道门",
            "接收、边界、校验、跳转和应用心跳逐关验收；任一门失败都留在 Bootloader")
    s.header(tag="12 升级 · IG-010", tag_color=T.VIOLET)
    gates = [
        ("Receive", "长度 / CRC", T.CYAN),
        ("Range", "APP slot 内", T.AMBER),
        ("Vector", "MSP + Reset", T.GREEN),
        ("Jump", "VTOR / MSP", T.VIOLET),
        ("Heartbeat", "app version", T.PINK),
    ]
    x0, y, bw, gap = 24, 110, 150, 26
    for i, (name, proof, color) in enumerate(gates):
        x = x0 + i * (bw + gap)
        s.rect(x, y, bw, 108, fill=T.PANEL, stroke=color, rx=8)
        s.text(x + bw / 2, y + 38, name, size=12, anchor="middle", mono=True,
               fill=color, weight="800")
        s.text(x + bw / 2, y + 75, proof, size=10, anchor="middle", fill=T.MUTED)
        if i < 4:
            s.arrow(x + bw + 3, y + 54, x + bw + gap - 3, y + 54,
                    color=T.CYAN, sw=2, head=6)

    s.rect(44, 270, 512, 178, fill=T.BG2, stroke=T.STROKE, rx=8)
    s.text(64, 302, "失败留在 Bootloader", size=13, fill=T.TEXT, weight="800")
    failures = [
        ("CRC 错", "不擦旧 APP；请求重传"),
        ("越界", "拒绝写 Bootloader / 参数区"),
        ("MSP 不在 SRAM", "镜像无效，不跳转"),
        ("Reset 不在 slot", "镜像无效，不跳转"),
        ("无 heartbeat", "回滚或下次启动回 Bootloader"),
    ]
    for i, (symptom, action) in enumerate(failures):
        yy = 331 + i * 23
        s.text(64, yy, symptom, size=10.2, mono=True, fill=T.RED, weight="700")
        s.text(190, yy, action, size=10.2, fill=T.MUTED)

    s.rect(582, 270, 276, 178, fill=T.PANEL, stroke=T.GREEN, rx=8)
    s.text(602, 302, "最小交付证据", size=13, fill=T.GREEN, weight="800")
    s.text(602, 338, "image length + CRC", size=10.2, mono=True, fill=T.MUTED)
    s.text(602, 366, "slot start / end", size=10.2, mono=True, fill=T.MUTED)
    s.text(602, 394, "vector[0] / vector[1]", size=10.2, mono=True, fill=T.MUTED)
    s.text(602, 422, "boot_id + app_version", size=10.2, mono=True, fill=T.MUTED)
    s.footer("视觉规范：FA-002 概念连续线 · IG-010 阶段进阶 · C-03 / C-10 / C-27 / C-31",
             label="自绘矢量图 · STM32 知识库")
    return s


def lowpower_current_evidence() -> Svg:
    s = Svg(W, H, "低功耗验收看完整电流波形",
            "静态底电流、唤醒峰值、活跃时间和周期共同决定平均电流；开发板漏电要单独扣除")
    s.header(tag="16 功耗 · IG-009", tag_color=T.GREEN)
    s.line(54, 272, 848, 272, stroke=T.STROKE, sw=1.5)
    points = [(54, 252), (168, 252), (184, 122), (250, 122), (266, 252),
              (520, 252), (536, 156), (590, 156), (606, 252), (848, 252)]
    for i in range(len(points) - 1):
        s.line(points[i][0], points[i][1], points[i + 1][0], points[i + 1][1],
               stroke=T.CYAN if i < 5 else T.VIOLET, sw=2)
    s.text(78, 246, "STOP floor", size=10, mono=True, fill=T.GREEN, weight="700")
    s.text(217, 108, "active peak", size=10, anchor="middle", mono=True, fill=T.RED, weight="700")
    s.text(563, 142, "wake / sample", size=10, anchor="middle", mono=True, fill=T.AMBER, weight="700")
    s.double_arrow(184, 300, 266, 300, color=T.RED, sw=1.5)
    s.text(225, 294, "t_active", size=9.5, anchor="middle", mono=True, fill=T.MUTED)
    s.double_arrow(54, 330, 520, 330, color=T.CYAN, sw=1.5)
    s.text(287, 324, "period", size=9.5, anchor="middle", mono=True, fill=T.MUTED)

    s.rect(38, 366, 520, 112, fill=T.BG2, stroke=T.GREEN, rx=8)
    s.text(58, 394, "平均电流", size=12.5, fill=T.GREEN, weight="800")
    s.text(58, 426, "Iavg = (Σ Istate × tstate) / period", size=11, mono=True, fill=T.TEXT, weight="700")
    s.text(58, 454, "同时记录电压、唤醒原因、时钟恢复完成点", size=10.2, fill=T.MUTED)

    s.rect(584, 366, 278, 112, fill=T.PANEL, stroke=T.RED, rx=8)
    s.text(604, 394, "测量边界", size=12.5, fill=T.RED, weight="800")
    s.text(604, 423, "断开调试器 / LED / USB", size=10.2, fill=T.MUTED)
    s.text(604, 449, "DS 典型值 ≠ 开发板实测", size=10.2, fill=T.RED, weight="700")
    s.footer("视觉规范：FA-002 概念连续线 · IG-009 时间轴节点 · C-03 / C-10 / C-27 / C-31",
             label="自绘矢量图 · STM32 知识库")
    return s


def fault_triage_ladder() -> Svg:
    s = Svg(W, H, "HardFault 先冻结证据，再改代码",
            "栈帧 PC/LR、CFSR/HFSR 与有效地址寄存器逐层收窄；没有证据前不靠猜测改优化级别")
    s.header(tag="17 故障 · IG-008", tag_color=T.RED)
    steps = [
        ("1", "冻结现场", "禁中断 · 不继续运行", T.RED),
        ("2", "读栈帧", "PC / LR / xPSR", T.AMBER),
        ("3", "分类", "CFSR / HFSR", T.CYAN),
        ("4", "地址有效?", "BFARVALID / MMARVALID", T.VIOLET),
        ("5", "源码定位", "addr2line + ELF", T.GREEN),
    ]
    x0, y, bw, gap = 24, 104, 150, 26
    for i, (num, title, proof, color) in enumerate(steps):
        x = x0 + i * (bw + gap)
        s.rect(x, y, bw, 120, fill=T.PANEL, stroke=color, rx=8)
        s.text(x + 18, y + 31, num, size=13, fill=color, weight="800")
        s.text(x + 75, y + 58, title, size=11.5, anchor="middle", fill=T.TEXT, weight="800")
        s.text(x + 75, y + 88, proof, size=9.5, anchor="middle", mono=True, fill=T.MUTED)
        if i < 4:
            s.arrow(x + bw + 3, y + 60, x + bw + gap - 3, y + 60,
                    color=T.CYAN, sw=2, head=6)

    s.rect(40, 274, 500, 178, fill=T.BG2, stroke=T.STROKE, rx=8)
    s.text(60, 306, "判读顺序", size=13, fill=T.TEXT, weight="800")
    rows = [
        ("PRECISERR", "精确总线错误：栈 PC 通常可用"),
        ("IMPRECISERR", "异步写错误：PC 可能只是后来位置"),
        ("BFARVALID", "置位后才读取 BFAR"),
        ("FORCED", "可配置 Fault 被升级到 HardFault"),
    ]
    for i, (flag, note) in enumerate(rows):
        yy = 338 + i * 26
        s.text(60, yy, flag, size=10.2, mono=True, fill=T.CYAN, weight="700")
        s.text(180, yy, note, size=10.2, fill=T.MUTED)

    s.rect(568, 274, 294, 178, fill=T.PANEL, stroke=T.RED, rx=8)
    s.text(588, 306, "不要先做", size=13, fill=T.RED, weight="800")
    s.text(588, 342, "改成 -O0 再说", size=10.5, fill=T.MUTED)
    s.text(588, 371, "注释一半代码碰运气", size=10.5, fill=T.MUTED)
    s.text(588, 400, "无条件打印 BFAR", size=10.5, fill=T.MUTED)
    s.text(588, 429, "复位后丢掉现场", size=10.5, fill=T.RED, weight="700")
    s.footer("视觉规范：FA-002 概念连续线 · IG-008 多路径流程 · C-03 / C-10 / C-27 / C-31",
             label="自绘矢量图 · STM32 知识库")
    return s


def layers_hal_ll_reg() -> Svg:
    s = Svg(W, H, "四种代码风格的分层关系",
            "寄存器 / LL / HAL / 应用：抽象越高越通用，越低越省资源")
    s.header(tag="架构", tag_color=T.VIOLET)

    layers = [
        ("应用 / 业务逻辑", "你的 main.c、状态机、协议解析", T.PINK),
        ("HAL 库", "HAL_GPIO_Init / HAL_UART_Transmit …（可移植性最好）", T.CYAN),
        ("LL 库", "LL_GPIO_SetOutputPin / LL_TIM_EnableCounter …（轻量、贴近寄存器）", T.GREEN),
        ("寄存器", "GPIOA->BSRR = GPIO_PIN_5（CMSIS 定义，最快最省）", T.AMBER),
        ("外设硬件", "GPIO / TIM / USART / SPI / ADC … 硅片上的电路", T.RED),
    ]
    y = 92
    for name, note, color in layers:
        s.rect(40, y, 470, 62, fill=T.PANEL, stroke=color, rx=8)
        s.rect(40, y, 5, 62, fill=color, rx=2)
        s.text(60, y + 27, name, size=14, fill=T.TEXT, weight="700")
        s.text(60, y + 47, note, size=10.5, fill=T.MUTED)
        y += 72
    s.double_arrow(524, 92, 524, 452, color=T.STROKE, sw=1.5)
    s.text(540, 270, "抽象层次提高 →", size=11, fill=T.MUTED)

    s.rect(600, 92, 260, 150, fill=T.PANEL2, stroke=T.STROKE, rx=8)
    s.text(618, 118, "怎么选？", size=13, fill=T.TEXT, weight="700")
    s.code(618, 140, [
        "学习 / 做项目：HAL + CubeMX",
        "资源紧张：关键路径用 LL",
        "极致性能：直接写寄存器",
        "看懂底层：对照 RM 读寄存器",
    ], size=10, lh=18, color=T.GREEN)

    s.rect(600, 258, 260, 194, fill=T.BG2, stroke=T.STROKE, rx=8)
    s.text(618, 284, "性能对照（72 MHz 下）", size=12.5, fill=T.TEXT, weight="700")
    rows = [("HAL_GPIO_TogglePin", "≈ 40 周期"),
            ("LL_GPIO_TogglePin", "≈ 10 周期"),
            ("GPIOA->BSRR = ...", "≈ 2 周期"),
            ("中断响应（硬件）", "12 周期"),
            ("DMA 搬 1 字节", "0 周期（不占 CPU）")]
    for i, (k, v) in enumerate(rows):
        yy = 308 + i * 24
        s.text(618, yy, k, size=10.5, mono=True, fill=T.CYAN)
        s.text(842, yy, v, size=10.5, fill=T.MUTED, anchor="end")

    s.rect(40, 468, 820, 62, fill=T.BG2, stroke=T.STROKE, rx=8)
    s.text(58, 492, "三者可以混用", size=12.5, fill=T.TEXT, weight="700")
    s.text(58, 512, "CubeMX 生成的工程本身就是「HAL 初始化 + LL/寄存器加速」的混合体；"
                    "不要因为「用了库」就觉得不底层。", size=11, fill=T.MUTED)
    s.footer("结论：先用 HAL 把功能跑通，再用 DWT 测出瓶颈，最后只优化瓶颈处的几行代码")
    return s


def project_structure() -> Svg:
    s = Svg(W, H, "一个标准 STM32 工程长什么样",
            "CubeMX + Makefile / Keil / CubeIDE 生成的结构基本一致")
    s.header(tag="工程结构", tag_color=T.CYAN)

    tree = [
        (0, "MyProject/", T.TEXT, True),
        (1, "MyProject.ioc", T.AMBER, False),
        (1, "Core/", T.CYAN, True),
        (2, "Inc/  main.h · stm32f1xx_hal_conf.h · stm32f1xx_it.h", T.MUTED, False),
        (2, "Src/  main.c · stm32f1xx_it.c · stm32f1xx_hal_msp.c", T.MUTED, False),
        (1, "Drivers/", T.GREEN, True),
        (2, "STM32F1xx_HAL_Driver/  HAL 外设驱动（只读，别改）", T.MUTED, False),
        (2, "CMSIS/  Device/ 内核定义与 startup_stm32f103xb.s", T.MUTED, False),
        (1, "Middlewares/", T.VIOLET, True),
        (2, "Third_Party/FreeRTOS / FatFs / USB_Device …", T.MUTED, False),
        (1, "BSP/  （自己写）", T.PINK, True),
        (2, "led.c/.h · key.c/.h · oled.c/.h · delay.c/.h", T.MUTED, False),
        (1, "MDK-ARM/ 或 build/", T.ORANGE, True),
        (2, "链接脚本 STM32F103C8Tx_FLASH.ld、输出 .hex/.bin", T.MUTED, False),
        (1, "Makefile / CMakeLists.txt", T.RED, False),
        (1, ".mxproject · .gitignore · README.md", T.DIM, False),
    ]
    y = 92
    for depth, text_, color, bold in tree:
        x = 40 + depth * 28
        if depth:
            s.line(x - 14, y - 5, x - 14, y + 5, stroke=T.STROKE, sw=1)
            s.line(x - 14, y, x - 4, y, stroke=T.STROKE, sw=1)
        s.text(x, y, text_, size=11.5 if depth else 13, fill=color,
               mono=depth > 0, weight="700" if bold else "normal")
        y += 26

    s.rect(520, 92, 340, 210, fill=T.PANEL, stroke=T.STROKE, rx=8)
    s.text(538, 118, "四条铁律", size=13, fill=T.TEXT, weight="700")
    s.code(538, 142, [
        "1. 不要修改 Drivers/ 里的 HAL 源码",
        "   （升级 CubeMX 时会被覆盖）",
        "2. 自己的外设驱动统一放 BSP/",
        "3. 中断服务函数只写在 it.c 里",
        "4. .ioc 要提交到 Git，build/ 不要",
    ], size=10.5, lh=19, color=T.GREEN)

    s.rect(520, 316, 340, 136, fill=T.BG2, stroke=T.STROKE, rx=8)
    s.text(538, 342, "编译产物", size=13, fill=T.TEXT, weight="700")
    rows = [(".elf", "带调试信息，用于下载/仿真"),
            (".hex", "Intel HEX，文本格式，含地址"),
            (".bin", "纯二进制，用于 IAP/OTA"),
            (".map", "各段大小，排查 RAM 溢出必看")]
    for i, (k, v) in enumerate(rows):
        yy = 366 + i * 22
        s.text(538, yy, k, size=10.5, mono=True, fill=T.AMBER)
        s.text(578, yy, v, size=10.5, fill=T.MUTED)

    s.rect(40, 480, 820, 50, fill=T.BG2, stroke=T.STROKE, rx=8)
    s.text(58, 510, "小技巧：把 BSP 目录做成 Git 子模块或独立仓库，"
                    "换芯片时只需改初始化，业务代码可整体复用。", size=11,
           fill=T.MUTED)
    s.footer("完整示例见 examples/ 目录，每个示例都给出 CubeMX 配置要点与文件清单")
    return s


def peripheral_bus() -> Svg:
    s = Svg(W, H, "外设挂在哪条总线上（以 STM32F411 为例）",
            "AHB/APB 分频决定外设能跑多快，也决定波特率、PWM 频率的上限")
    s.header(tag="总线", tag_color=T.GREEN)

    s.rect(40, 88, 180, 60, fill=T.PANEL, stroke=T.CYAN, rx=8)
    s.text(130, 112, "SYSCLK", size=14, anchor="middle", fill=T.TEXT,
           weight="700")
    s.text(130, 132, "100 MHz", size=11, anchor="middle", fill=T.CYAN)

    s.arrow(222, 118, 300, 118, color=T.CYAN, sw=2)
    s.rect(302, 88, 200, 60, fill=T.PANEL, stroke=T.BLUE, rx=8)
    s.text(402, 112, "AHB 总线", size=14, anchor="middle", fill=T.TEXT,
           weight="700")
    s.text(402, 132, "HCLK = 100 MHz（÷1）", size=11, anchor="middle",
           fill=T.BLUE)

    s.arrow(402, 150, 402, 174, color=T.BLUE, sw=2)
    s.rect(302, 176, 200, 50, fill=T.PANEL2, stroke=T.BLUE, rx=8)
    s.text(402, 206, "AHB1 / AHB2", size=12.5, anchor="middle", fill=T.BLUE)
    ahb = ["GPIOA~H", "DMA1/2", "CRC / RNG", "USB OTG FS", "FSMC", "DCMI"]
    for i, n in enumerate(ahb):
        x = 40 + (i % 3) * 176
        y = 250 + (i // 3) * 38
        s.rect(x, y, 160, 30, fill=T.PANEL, stroke=T.STROKE, rx=8)
        s.text(x + 80, y + 20, n, size=11, anchor="middle", fill=T.CYAN)
    s.line(300, 202, 300, 232, stroke=T.BLUE, sw=1.5, dash="4 5")
    s.line(120, 232, 646, 232, stroke=T.BLUE, sw=1.5, dash="4 5")
    s.line(120, 232, 120, 250, stroke=T.BLUE, sw=1.5, dash="4 5")
    s.line(646, 232, 646, 250, stroke=T.BLUE, sw=1.5, dash="4 5")

    s.arrow(504, 118, 600, 118, color=T.GREEN, sw=2)
    s.rect(602, 88, 258, 60, fill=T.PANEL, stroke=T.GREEN, rx=8)
    s.text(731, 112, "APB1 / APB2", size=14, anchor="middle", fill=T.TEXT,
           weight="700")
    s.text(731, 132, "PCLK1 = 50 MHz · PCLK2 = 100 MHz", size=10.5,
           anchor="middle", fill=T.GREEN)

    apb1 = ["USART2/3", "I2C1/2/3", "SPI2/3", "TIM2~5", "CAN1", "USB 48M"]
    apb2 = ["USART1/6", "SPI1", "ADC1", "TIM1/9/10/11", "SDIO", "SYSCFG"]
    s.text(602, 194, "APB1（最高 50 MHz）", size=12, fill=T.VIOLET, weight="700")
    s.text(602, 338, "APB2（最高 100 MHz）", size=12, fill=T.PINK, weight="700")
    for i, n in enumerate(apb1):
        x = 602 + (i % 2) * 132
        y = 204 + (i // 2) * 34
        s.rect(x, y, 126, 28, fill=T.PANEL2, stroke=T.STROKE, rx=4)
        s.text(x + 63, y + 19, n, size=10.5, anchor="middle", fill=T.VIOLET)
    for i, n in enumerate(apb2):
        x = 602 + (i % 2) * 132
        y = 348 + (i // 2) * 34
        s.rect(x, y, 126, 28, fill=T.PANEL2, stroke=T.STROKE, rx=4)
        s.text(x + 63, y + 19, n, size=10.5, anchor="middle", fill=T.PINK)

    s.rect(40, 348, 520, 160, fill=T.BG2, stroke=T.STROKE, rx=8)
    s.text(58, 374, "为什么必须记住总线？", size=12.5, fill=T.TEXT, weight="700")
    notes = [
        "① 波特率算错：USART2 在 APB1（50 MHz），USART1 在 APB2（100 MHz）",
        "② PWM 频率上限：TIM2 挂 APB1，但定时器时钟有 ×2 倍频（50→100 MHz）",
        "③ 超频红线：APB1 不能超 50 MHz，APB2 不能超 100 MHz",
        "④ ADC 时钟：由 APB2 分频，F4 最高 36 MHz，超过则采样不准",
        "⑤ 时钟使能宏（__HAL_RCC_*_CLK_ENABLE）忘记调用 = 外设完全没反应",
    ]
    for i, n in enumerate(notes):
        s.text(58, 398 + i * 22, n, size=10.5, fill=T.MUTED)

    s.rect(560, 462, 300, 46, fill=T.PANEL, stroke=T.STROKE, rx=8)
    s.text(578, 482, "查表工具", size=11.5, fill=T.TEXT, weight="700")
    s.text(578, 500, "cheatsheets/外设总线与引脚速查表.md", size=10,
           fill=T.CYAN, mono=True)
    s.footer("数据来源：RM0383（F411 参考手册）「Reset and clock control」框图")
    return s




def interrupt_priority() -> Svg:
    s = Svg(W, H, "抢占优先级与中断嵌套",
            "图中 A 的抢占号是 1，B 是 2；数字越小越先打断")
    s.header(tag="中断优先级", tag_color=T.VIOLET)

    s.axis(80, 110, 780, 200, ylabel="CPU 执行", xlabel="时间 →")
    rows = [("主循环", T.MUTED, 0), ("IRQ A", T.CYAN, 1),
            ("IRQ B", T.AMBER, 2)]
    for i, (name, color, _) in enumerate(rows):
        s.text(74, 152 + i * 50, name, size=11, anchor="end", fill=color)

    seg = [
        (0, 90, "主循环", T.MUTED, 0),
        (90, 60, "A", T.CYAN, 1),
        (150, 50, "B", T.AMBER, 2),
        (200, 60, "A 继续", T.CYAN, 1),
        (260, 120, "主循环", T.MUTED, 0),
        (380, 70, "B", T.AMBER, 2),
        (450, 90, "A", T.CYAN, 1),
        (540, 240, "主循环", T.MUTED, 0),
    ]
    for x, w, label, color, row in seg:
        s.rect(80 + x, 130 + row * 50, w, 32, fill=color, rx=4, opacity=0.85)
        s.text(80 + x + w / 2, 151 + row * 50, label, size=10.5,
               anchor="middle", fill="#fbfaf7", weight="700")
    for x, txt in ((90, "A 触发"), (150, "B 抢占 A"), (200, "B 返回"),
                   (380, "B 触发")):
        s.line(80 + x, 112, 80 + x, 330, stroke=T.STROKE, sw=1, dash="3 4")
        s.text(80 + x, 106, txt, size=9.5, anchor="middle", fill=T.DIM)

    s.rect(40, 350, 400, 156, fill=T.PANEL, stroke=T.STROKE, rx=8)
    s.text(58, 376, "优先级分组表", size=12.5, fill=T.TEXT, weight="700")
    rows2 = [("GROUP_0", "0 位抢占 / 4 位子优先级", "几乎不嵌套"),
             ("GROUP_2", "2 位抢占 / 2 位子优先级", "最常用"),
             ("GROUP_4", "4 位抢占 / 0 位子优先级", "只用抢占，最直观"),
             ("数值范围", "0（最高）~ 15（最低）", "HAL_NVIC_SetPriority")]
    for i, (k, v, note) in enumerate(rows2):
        yy = 402 + i * 26
        s.text(58, yy, k, size=10.5, mono=True, fill=T.CYAN)
        s.text(158, yy, v, size=10.5, fill=T.TEXT)
        s.text(322, yy, note, size=9.5, fill=T.MUTED)

    s.rect(460, 350, 400, 156, fill=T.BG2, stroke=T.STROKE, rx=8)
    s.text(478, 376, "常见错误", size=12.5, fill=T.TEXT, weight="700")
    errs = [
        "在 ISR 里调用 HAL_Delay（死等，因为 SysTick 优先级更低）",
        "忘记清中断标志 → 出中断立刻又进，表现为程序卡死",
        "把 EXTI 优先级设得比 DMA 低，导致数据被覆盖",
        "在 ISR 里做耗时运算（浮点、printf）导致丢中断",
        "FreeRTOS 中改优先级后忘记同步 configMAX_SYSCALL_INTERRUPT_PRIORITY",
    ]
    for i, e in enumerate(errs):
        s.text(478, 400 + i * 21, "· " + e, size=10, fill=T.MUTED)
    s.footer("抢占优先级相同的中断不能互相打断，只能排队；子优先级只决定排队顺序")
    return s




def l4_idd_bench() -> Svg:
    s = Svg(W, H, "NUCLEO-L476RG：JP6 IDD 动态功耗测量接线",
            "电流通道串入 JP6；电压通道直接测 MCU 端 VDD；两条线必须同时记录")
    s.header(tag="24 L4 测量", tag_color=T.GREEN)

    # 左：电源与功耗仪
    s.rect(40, 112, 170, 126, fill=T.PANEL, stroke=T.GREEN, rx=8)
    s.text(125, 142, "动态功耗仪", size=14, anchor="middle", fill=T.TEXT, weight="700")
    s.text(125, 168, "SOURCE 3.3 V", size=11, anchor="middle", mono=True, fill=T.GREEN)
    s.text(125, 190, "I(t) 高速采样", size=11, anchor="middle", mono=True, fill=T.CYAN)
    s.text(125, 214, "记录 burden / range", size=9.5, anchor="middle", fill=T.MUTED)

    # 中：JP6 断点
    s.arrow(214, 164, 330, 164, color=T.GREEN, sw=2, head=7)
    s.text(270, 151, "电流路径", size=10, anchor="middle", fill=T.GREEN)
    s.circle(348, 164, 9, fill=T.BG2, stroke=T.AMBER, sw=2)
    s.circle(392, 164, 9, fill=T.BG2, stroke=T.AMBER, sw=2)
    s.line(357, 164, 383, 142, stroke=T.RED, sw=2)
    s.text(370, 122, "JP6 (IDD) 拔下", size=11.5, anchor="middle", fill=T.AMBER,
           weight="700")
    s.arrow(401, 164, 484, 164, color=T.GREEN, sw=2, head=7)

    # 右：Nucleo 目标区
    s.rect(486, 92, 374, 238, fill="#123a2e", stroke="#0d2b22", rx=8)
    s.rect(500, 108, 346, 68, fill="#0d2b22", stroke="#8b98b0", rx=8)
    s.text(673, 134, "ST-LINK 区", size=13, anchor="middle", fill="#dfe6f0", weight="700")
    s.text(673, 158, "功能调试可接；功耗测量需排查回灌", size=9.5,
           anchor="middle", fill="#e2b23c")
    s.rect(500, 190, 346, 122, fill="#123057", stroke="#7aa2ff", rx=8)
    s.text(673, 216, "目标 MCU 供电域", size=13, anchor="middle", fill="#dfe6f0",
           weight="700")
    s.rect(620, 236, 106, 52, fill="#151922", stroke="#808a9a", rx=4)
    s.text(673, 260, "STM32L476RG", size=10.5, anchor="middle", mono=True,
           fill="#dfe6f0", weight="700")
    s.text(673, 279, "VDD / VSS", size=9, anchor="middle", mono=True, fill="#8b98b0")

    # 电压 sense 独立通道
    s.rect(40, 278, 170, 98, fill=T.BG2, stroke=T.CYAN, rx=8)
    s.text(125, 307, "电压通道", size=13, anchor="middle", fill=T.TEXT, weight="700")
    s.text(125, 332, "VDD at MCU", size=11, anchor="middle", mono=True, fill=T.CYAN)
    s.text(125, 354, "同步观察压降/复位", size=9.5, anchor="middle", fill=T.MUTED)
    s.line(210, 326, 580, 326, stroke=T.CYAN, sw=2)
    s.arrow(580, 326, 620, 280, color=T.CYAN, sw=2, head=7)
    s.line(210, 350, 760, 350, stroke=T.MUTED, sw=2, dash="5 6")
    s.arrow(760, 350, 726, 280, color=T.MUTED, sw=2, head=6)

    s.rect(40, 404, 820, 92, fill=T.PANEL, stroke=T.STROKE, rx=8)
    s.text(58, 430, "测量前四项断言", size=12.5, fill=T.TEXT, weight="700")
    notes = [
        "① JP6 已拔：电流只经过仪器，不跨接跳线",
        "② MCU 端 VDD 在活动峰值期间仍高于允许下限",
        "③ SWD/USB/外设 GPIO 不形成旁路或反向供电",
        "④ 采样率 >= 10 / t_min，至少捕获 10 个完整周期",
    ]
    for i, note in enumerate(notes):
        x = 58 + (i % 2) * 400
        y = 454 + (i // 2) * 23
        s.text(x, y, note, size=10.2, fill=T.MUTED)
    s.footer("视觉规范：FA-029 几何图解叙事 · IG-002 中心标注 · C-03 / C-10 / C-27 / C-31")
    return s




def network_debug_ladder() -> Svg:
    s = Svg(W, H, "STM32 网络排错阶梯：在哪一层第一次偏离？",
            "每次只验证一层；下层证据没成立，不要继续改上层协议参数")
    s.header(tag="27 网络排错", tag_color=T.CYAN)

    rows = [
        ("L1", "PHY / RMII", "link=1 · 50 MHz REF_CLK · MDIO 可读", "示波器 + PHY BSR", T.ORANGE),
        ("L2", "Ethernet / ARP", "本机发 ARP，能收到目标 MAC", "Wireshark: arp", T.BLUE),
        ("L3", "IPv4 / ICMP", "IP/掩码/网关正确，同网段可 ping", "ipconfig · ping", T.CYAN),
        ("L4", "UDP / TCP", "端口可达；TCP 完成三次握手", "Wireshark: tcp.flags.syn", T.GREEN),
        ("L5", "DNS / TLS", "DNS 得到预期地址；证书链与主机名通过", "nslookup · TLS error", T.AMBER),
        ("L7", "HTTP / MQTT", "状态码/CONNACK/QoS 与业务序号可追踪", "curl · mosquitto_sub", T.VIOLET),
    ]
    x0, y0, row_h = 44, 94, 62
    for i, (level, name, assertion, evidence, color) in enumerate(rows):
        y = y0 + i * row_h
        s.rect(x0, y, 812, 50, fill=T.PANEL if i % 2 == 0 else T.BG2,
               stroke=color, rx=8)
        s.rect(x0, y, 54, 50, fill=color, rx=8)
        s.text(x0 + 27, y + 30, level, size=12, anchor="middle", fill=T.BG,
               weight="800", mono=True)
        s.text(116, y + 21, name, size=11.5, fill=color, weight="700")
        s.text(116, y + 40, assertion, size=9.7, fill=T.MUTED)
        s.rect(626, y + 9, 210, 32, fill=T.BG, stroke=T.STROKE, rx=4)
        s.text(731, y + 29, evidence, size=9.2, anchor="middle", mono=True,
               fill=T.TEXT)
        if i < len(rows) - 1:
            s.arrow(72, y + 52, 72, y + row_h - 2, color=T.MUTED, sw=2,
                    head=5)

    s.rect(44, 478, 812, 48, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(62, 499, "止损规则", size=11.5, fill=T.RED, weight="700")
    s.text(126, 499, "第一次失败层就是当前边界：保留 PCAP、寄存器/错误码和配置快照，再改一个变量",
           size=10, fill=T.TEXT)
    s.text(126, 517, "不要用“重启后偶尔能通”替代可重复证据；不要在 ping 不通时先调 MQTT keepalive",
           size=9.4, fill=T.MUTED)
    s.footer("link → ARP → IP → TCP/UDP → DNS/TLS → 应用协议；自下而上，逐层留证据")
    return s


def spl_ownership_boundary() -> Svg:
    """SPL、HAL 与寄存器的所有权边界，而不是函数名替换表。"""
    s = Svg(W, H, "HAL 与 SPL 最终写的是同一组寄存器",
            "一条外设实例只能有一个初始化与恢复所有者；混用读接口可以，双重接管不可以")
    s.header(tag="26 SPL · IG-012", tag_color=T.CYAN)

    lanes = [
        ("HAL 路径", "Handle + 状态 + 回调", "HAL_UART_Init", T.VIOLET),
        ("SPL 路径", "InitStruct + 直接函数", "USART_Init", T.GREEN),
        ("寄存器边界", "BRR / CR1 / CR2 / CR3", "USART1", T.AMBER),
        ("真实硬件", "PA9 TX · PA10 RX · 波形", "示波器 / 逻辑分析仪", T.RED),
    ]
    y = 96
    for i, (name, contract, api, color) in enumerate(lanes):
        w = 760 - i * 100
        x = 70 + i * 50
        s.rect(x, y, w, 76, fill=T.PANEL if i % 2 == 0 else T.BG2,
               stroke=color, rx=8)
        s.rect(x, y, 7, 76, fill=color, rx=2)
        s.text(x + 24, y + 29, name, size=14, fill=color, weight="700")
        s.text(x + 170, y + 29, contract, size=10.5, fill=T.MUTED)
        s.text(x + w - 18, y + 29, api, size=10.5, fill=T.TEXT,
               anchor="end", mono=True)
        s.text(x + 24, y + 55,
               "所有权：初始化 · 中断 · DMA · 超时 · 恢复必须属于同一条路径",
               size=9.7, fill=T.DIM)
        y += 92

    s.rect(40, 474, 394, 56, fill=T.BG2, stroke=T.GREEN, rx=8)
    s.text(58, 498, "允许", size=11.5, fill=T.GREEN, weight="700")
    s.text(112, 498, "SPL 配置，调试器只读寄存器验证", size=10.5, fill=T.TEXT)
    s.text(112, 517, "迁移时一次切换一条完整外设链", size=9.7, fill=T.MUTED)
    s.rect(466, 474, 394, 56, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(484, 498, "禁止", size=11.5, fill=T.RED, weight="700")
    s.text(538, 498, "先用 SPL 初始化，再让 HAL 接管同一 USART", size=10.2,
           fill=T.TEXT)
    s.text(538, 517, "两套状态互不知情，恢复路径会互相覆盖", size=9.7, fill=T.MUTED)
    s.footer("视觉规范：FA-002 概念连续线 · IG-012 分层结构 · C-03 / C-10 / C-27 / C-31",
             label="自绘矢量图 · STM32 知识库")
    return s


def network_cache_ownership() -> Svg:
    """H7 Ethernet DMA 在可缓存内存上的 TX/RX 所有权交接。"""
    s = Svg(W, H, "CPU、Cache 与 Ethernet DMA：谁看见哪一份数据？",
            "TX 在交给 DMA 前 clean；RX 在 DMA 完成且 CPU 接管后 invalidate；方向相反，顺序不能交换")
    s.header(tag="27 网络 · IG-012", tag_color=T.GREEN)

    nodes = [
        (70, 118, 180, 96, "CPU", "写 payload\n读 pbuf", T.CYAN),
        (360, 118, 180, 96, "D-Cache", "可能仍是旧副本", T.AMBER),
        (650, 118, 180, 96, "SRAM 描述符/缓冲", "DMA 与 CPU 的交接区", T.VIOLET),
        (650, 344, 180, 96, "Ethernet DMA", "读 TX · 写 RX", T.GREEN),
        (360, 344, 180, 96, "MAC / RMII", "帧与 50 MHz 接口", T.PINK),
        (70, 344, 180, 96, "PHY / 线缆", "link 只是第一层证据", T.RED),
    ]
    for x, y, w, h, title, note, color in nodes:
        s.rect(x, y, w, h, fill=T.PANEL, stroke=color, rx=8)
        s.text(x + w / 2, y + 34, title, size=13, anchor="middle",
               fill=color, weight="700")
        for i, line in enumerate(note.split("\n")):
            s.text(x + w / 2, y + 61 + i * 19, line, size=9.7,
                   anchor="middle", fill=T.MUTED)

    s.arrow(252, 146, 356, 146, color=T.CYAN, sw=2)
    s.text(304, 133, "CPU 写", size=9.5, anchor="middle", fill=T.CYAN)
    s.arrow(542, 146, 646, 146, color=T.GREEN, sw=2)
    s.text(594, 128, "TX clean", size=9.5, anchor="middle", fill=T.GREEN)
    s.text(594, 143, "发布所有权", size=9, anchor="middle", fill=T.MUTED)
    s.arrow(740, 218, 740, 340, color=T.GREEN, sw=2)
    s.text(756, 286, "DMA 取帧", size=9.5, fill=T.GREEN)
    s.arrow(646, 392, 544, 392, color=T.PINK, sw=2)
    s.arrow(356, 392, 254, 392, color=T.RED, sw=2)

    s.arrow(700, 340, 700, 218, color=T.VIOLET, sw=2, dash="6 6")
    s.text(618, 278, "RX 写 SRAM", size=9.5, fill=T.VIOLET)
    s.arrow(646, 186, 542, 186, color=T.AMBER, sw=2, dash="6 6")
    s.text(594, 204, "RX invalidate", size=9.5, anchor="middle", fill=T.AMBER)
    s.arrow(356, 186, 252, 186, color=T.CYAN, sw=2, dash="6 6")
    s.text(304, 204, "CPU 接管", size=9.5, anchor="middle", fill=T.CYAN)

    s.rect(40, 466, 820, 64, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(58, 491, "最常见的错", size=11.5, fill=T.RED, weight="700")
    s.text(150, 491, "把 clean / invalidate 当作“都刷新一下”，或在 DMA 仍拥有缓冲时让 CPU 修改它。",
           size=10.4, fill=T.TEXT)
    s.text(150, 514, "验收必须同时记录：缓冲地址与对齐、Cache 操作方向、描述符状态、PCAP 中的实际帧。",
           size=9.8, fill=T.MUTED)
    s.footer("视觉规范：FA-029 几何图解叙事 · IG-012 分层结构 · C-03 / C-10 / C-27 / C-31",
             label="自绘矢量图 · STM32 知识库")
    return s


def tcp_byte_stream() -> Svg:
    """TCP 分段与应用消息边界的连续时间轴。"""
    s = Svg(W, H, "TCP 交付字节，不交付你的消息边界",
            "发送端三次 send 可能被合并或拆分；接收端只能按长度字段或分隔符重新组帧")
    s.header(tag="27 TCP · IG-009", tag_color=T.CYAN)

    s.text(42, 110, "应用写入", size=11.5, fill=T.TEXT, weight="700")
    messages = [(150, 92, 150, "A · 6 B", T.CYAN),
                (312, 92, 230, "B · 10 B", T.GREEN),
                (554, 92, 120, "C · 4 B", T.AMBER)]
    for x, y, w, label, color in messages:
        s.rect(x, y, w, 40, fill=color, rx=4, opacity=.84)
        s.text(x + w / 2, y + 25, label, size=10.5, anchor="middle",
               fill=T.BG, weight="700")

    s.arrow(420, 140, 420, 190, color=T.STROKE, sw=2)
    s.text(438, 172, "TCP 可任意分段", size=10, fill=T.MUTED)
    s.text(42, 222, "网络分段", size=11.5, fill=T.TEXT, weight="700")
    segments = [(150, 204, 92, "A0..A5+B0"), (246, 204, 184, "B1..B9+C0..C1"),
                (434, 204, 84, "C2..C3")]
    for i, (x, y, w, label) in enumerate(segments):
        s.rect(x, y, w, 40, fill=T.PANEL, stroke=T.STROKE, rx=4)
        s.text(x + w / 2, y + 25, label, size=9.4, anchor="middle",
               fill=(T.CYAN, T.GREEN, T.AMBER)[i], mono=True)

    s.arrow(420, 254, 420, 304, color=T.STROKE, sw=2)
    s.text(438, 286, "recv 也可短读", size=10, fill=T.MUTED)
    s.text(42, 338, "接收缓存", size=11.5, fill=T.TEXT, weight="700")
    chunks = [(150, 320, 70, "4 B"), (224, 320, 106, "7 B"),
              (334, 320, 54, "2 B"), (392, 320, 128, "7 B")]
    for x, y, w, label in chunks:
        s.rect(x, y, w, 40, fill=T.BG2, stroke=T.CYAN, rx=4)
        s.text(x + w / 2, y + 25, label, size=9.5, anchor="middle",
               fill=T.CYAN, mono=True)

    s.rect(586, 292, 274, 92, fill=T.PANEL, stroke=T.GREEN, rx=8)
    s.text(604, 320, "正确解析器", size=12, fill=T.GREEN, weight="700")
    s.text(604, 344, "[len][type][sequence][payload][crc]", size=9.5,
           fill=T.TEXT, mono=True)
    s.text(604, 366, "循环消费完整帧；不完整就保留", size=9.7, fill=T.MUTED)

    s.rect(40, 412, 400, 116, fill=T.BG2, stroke=T.GREEN, rx=8)
    s.text(58, 439, "必须成立", size=11.5, fill=T.GREEN, weight="700")
    for i, note in enumerate(("长度有上限，先验证再分配", "一次 recv 可含 0.5、1 或多帧",
                              "超时属于连接策略，不属于分帧规则")):
        s.text(58, 465 + i * 20, "· " + note, size=10, fill=T.MUTED)
    s.rect(460, 412, 400, 116, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(478, 439, "不能假设", size=11.5, fill=T.RED, weight="700")
    for i, note in enumerate(("一次 send 对应一次 recv", "recv 返回短数据就是断线",
                              "用结构体裸发就天然跨平台")):
        s.text(478, 465 + i * 20, "· " + note, size=10, fill=T.MUTED)
    s.footer("视觉规范：FA-002 概念连续线 · IG-009 时间轴节点 · C-03 / C-10 / C-27 / C-31",
             label="自绘矢量图 · STM32 知识库")
    return s


def rtos_owner_task() -> Svg:
    """两个调用者争抢驱动与单一所有者任务的前后对比。"""
    s = Svg(W, H, "给驱动加很多锁，仍不等于拥有清楚的所有权",
            "把完整事务送给唯一所有者，片选、DMA、超时和恢复才能落在同一个状态机里")
    s.header(tag="所有权 · IG-011", tag_color=T.VIOLET)

    s.text(220, 100, "并发直调：锁住了函数，没锁住完整事务", size=13,
           anchor="middle", fill=T.RED, weight="700")
    callers = [(60, 134, "任务 A", T.CYAN), (280, 134, "任务 B", T.AMBER)]
    for x, y, name, color in callers:
        s.rect(x, y, 140, 56, fill=T.PANEL, stroke=color, rx=8)
        s.text(x + 70, y + 33, name, size=12, anchor="middle", fill=color,
               weight="700")
        s.arrow(x + 70, y + 60, 220, 244, color=color, sw=2)
    s.rect(120, 246, 200, 76, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(220, 272, "SPI API + mutex", size=12, anchor="middle",
           fill=T.RED, weight="700")
    s.text(220, 297, "CS / DMA / timeout 分散", size=9.8, anchor="middle",
           fill=T.MUTED)
    s.arrow(220, 326, 220, 374, color=T.RED, sw=2)
    s.rect(120, 376, 200, 62, fill=T.PANEL, stroke=T.STROKE, rx=8)
    s.text(220, 403, "同一外设", size=12, anchor="middle", fill=T.TEXT,
           weight="700")
    s.text(220, 424, "交叉片选 / 恢复竞态", size=9.5, anchor="middle", fill=T.RED)

    s.text(680, 100, "所有者任务：一次只接受一笔完整事务", size=13,
           anchor="middle", fill=T.GREEN, weight="700")
    for i, (name, color) in enumerate((("任务 A", T.CYAN), ("任务 B", T.AMBER))):
        y = 134 + i * 72
        s.rect(500, y, 120, 48, fill=T.PANEL, stroke=color, rx=8)
        s.text(560, y + 29, name, size=11, anchor="middle", fill=color,
               weight="700")
        s.arrow(624, y + 24, 664, 220, color=color, sw=2)
    s.rect(646, 194, 214, 176, fill=T.BG2, stroke=T.GREEN, rx=8)
    s.text(753, 222, "SPI owner", size=12.5, anchor="middle", fill=T.GREEN,
           weight="700")
    for i, note in enumerate(("队列接收完整事务", "拉低 / 拉高 CS", "启动并等待 DMA",
                              "统一超时与恢复", "返回稳定结果码")):
        s.text(666, 250 + i * 22, "· " + note, size=9.8, fill=T.MUTED)
    s.arrow(753, 374, 753, 414, color=T.GREEN, sw=2)
    s.rect(646, 416, 214, 62, fill=T.PANEL, stroke=T.STROKE, rx=8)
    s.text(753, 442, "同一外设", size=12, anchor="middle", fill=T.TEXT,
           weight="700")
    s.text(753, 463, "串行事务 · 可审计恢复", size=9.5, anchor="middle", fill=T.GREEN)

    s.rect(370, 120, 56, 358, fill=T.PANEL, stroke=T.STROKE, rx=8)
    s.text(398, 298, "→", size=28, anchor="middle", fill=T.CYAN, weight="700")
    s.footer("视觉规范：FA-002 概念连续线 · IG-011 前后变化对比 · C-03 / C-10 / C-27 / C-31",
             label="自绘矢量图 · STM32 知识库")
    return s


def rtos_deadline_budget() -> Svg:
    """响应时间组成与 deadline 的单条可复算时间轴。"""
    s = Svg(W, H, "“实时”不是快，而是最坏响应仍早于截止点",
            "把阻塞、执行和抢占分别量出来：R = B + C + S；平均值不能替代最坏值")
    s.header(tag="实时预算 · IG-009", tag_color=T.AMBER)

    x0, y, total = 82, 220, 730
    s.line(x0, y, x0 + total, y, stroke=T.STROKE, sw=2)
    pieces = [
        (0, 120, "B 阻塞", "等资源所有者", T.RED),
        (120, 250, "C 执行", "任务自己的 WCET", T.GREEN),
        (370, 180, "S 干扰", "更高优先级任务/ISR", T.AMBER),
        (550, 110, "C 继续", "完成剩余工作", T.GREEN),
    ]
    for start, width, name, note, color in pieces:
        x = x0 + start
        s.rect(x, y - 38, width, 76, fill=color, rx=4, opacity=.84)
        s.text(x + width / 2, y - 7, name, size=11, anchor="middle",
               fill=T.BG, weight="700")
        s.text(x + width / 2, y + 18, note, size=8.8, anchor="middle", fill=T.BG)

    marks = [(x0, "release", T.CYAN), (x0 + 660, "finish", T.GREEN),
             (x0 + total, "deadline D", T.RED)]
    for x, label, color in marks:
        s.line(x, 146, x, 302, stroke=color, sw=2, dash="5 5")
        s.text(x, 132, label, size=10, anchor="middle", fill=color, weight="700")

    s.double_arrow(x0, 318, x0 + 660, 318, color=T.CYAN, sw=1.5, text_="R = B + C + S")
    s.double_arrow(x0, 354, x0 + total, 354, color=T.RED, sw=1.5, text_="D")
    s.text(450, 392, "验收条件：Rmax ≤ D", size=17, anchor="middle",
           fill=T.GREEN, weight="800", mono=True)

    s.rect(40, 426, 400, 102, fill=T.BG2, stroke=T.GREEN, rx=8)
    s.text(58, 452, "要测", size=11.5, fill=T.GREEN, weight="700")
    for i, note in enumerate(("ISR 占用与最长临界区", "mutex 最长持有时间与优先级继承",
                              "任务 WCET、周期、抖动和队列峰值")):
        s.text(112, 452 + i * 23, note, size=10, fill=T.MUTED)
    s.rect(460, 426, 400, 102, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(478, 452, "不能只看", size=11.5, fill=T.RED, weight="700")
    for i, note in enumerate(("CPU 平均利用率", "一次实验里的平均延迟", "任务优先级数字看起来很高")):
        s.text(558, 452 + i * 23, note, size=10, fill=T.MUTED)
    s.footer("视觉规范：FA-002 概念连续线 · IG-009 时间轴节点 · C-03 / C-10 / C-27 / C-31",
             label="自绘矢量图 · STM32 知识库")
    return s


def rtos_config_paths() -> Svg:
    """三套系统把配置与硬件描述送入固件的不同路径。"""
    s = Svg(W, H, "三套 RTOS 生态：配置从哪里进入最终固件？",
            "函数名不是主要差异；真正影响维护的是配置入口、硬件描述、驱动模型和构建产物")
    s.header(tag="28 生态 · IG-004", tag_color=T.VIOLET)

    columns = [
        (42, "FreeRTOS", T.CYAN, [
            ("配置", "FreeRTOSConfig.h"),
            ("硬件", "CubeMX / HAL / BSP"),
            ("对象", "task / queue / timer"),
            ("构建", "工程自行组合服务"),
        ]),
        (322, "RT-Thread", T.GREEN, [
            ("配置", "menuconfig / rtconfig.h"),
            ("硬件", "BSP + device framework"),
            ("对象", "thread / IPC / device"),
            ("构建", "SCons + components"),
        ]),
        (602, "Zephyr", T.AMBER, [
            ("配置", "Kconfig / prj.conf"),
            ("硬件", "Devicetree + bindings"),
            ("对象", "kernel + device model"),
            ("构建", "west + CMake + Ninja"),
        ]),
    ]
    for x, title, color, rows in columns:
        s.rect(x, 92, 256, 360, fill=T.PANEL, stroke=color, rx=8)
        s.rect(x, 92, 256, 48, fill=color, rx=8, opacity=.86)
        s.text(x + 128, 122, title, size=14, anchor="middle", fill=T.BG,
               weight="800")
        for i, (kind, detail) in enumerate(rows):
            yy = 164 + i * 66
            s.text(x + 18, yy, kind, size=10.5, fill=color, weight="700")
            s.text(x + 76, yy, detail, size=9.8, fill=T.TEXT, mono=True)
            if i < len(rows) - 1:
                s.arrow(x + 128, yy + 16, x + 128, yy + 43,
                        color=T.STROKE, sw=1.5, head=5)
        s.rect(x + 18, 410, 220, 24, fill=T.BG2, stroke=color, rx=4)
        s.text(x + 128, 427, "→ firmware.elf", size=9.8, anchor="middle",
               fill=color, mono=True, weight="700")

    s.rect(42, 474, 816, 56, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(60, 498, "迁移检查", size=11.5, fill=T.RED, weight="700")
    s.text(132, 498, "不要逐函数替换；逐项核对配置单位、设备所有权、ISR 边界、超时语义与启动顺序。",
           size=10.3, fill=T.TEXT)
    s.text(132, 518, "同一个 GPIO 闪灯能编译，不代表网络、低功耗和故障恢复已经等价。",
           size=9.7, fill=T.MUTED)
    s.footer("视觉规范：FA-029 几何图解叙事 · IG-004 双列多行对比 · C-03 / C-10 / C-27 / C-31",
             label="自绘矢量图 · STM32 知识库")
    return s


# --------------------------------------------------------------------------- Book 2.0 首批视觉锚点


def manual_choice_map() -> Svg:
    """把问题路由到权威文档，而不是把六类文档画成平铺清单。"""
    s = Svg(W, H, "先问问题，再选手册", "同一颗 STM32 通常要同时打开 DS 与 RM；勘误表 ES 不能省")
    s.header(tag="20 文档 · IG-008", tag_color=T.CYAN)
    questions = [
        ("引脚 / 电压 / 极限值", "DS", "确认具体订货号与封装", T.CYAN),
        ("寄存器 / 时序 / 状态机", "RM", "再回寄存器表核对位定义", T.GREEN),
        ("Cortex-M 内核 / Fault", "PM", "区分内核规则与厂商外设", T.VIOLET),
        ("已知硅片问题", "ES", "按 revision 判断规避条件", T.RED),
        ("一种设计方法", "AN", "做法不是器件规格", T.AMBER),
        ("工具 / 开发板用法", "UM", "版本和板卡必须对得上", T.PINK),
    ]
    for i, (question, doc, boundary, color) in enumerate(questions):
        x = 42 + (i % 2) * 414
        y = 92 + (i // 2) * 112
        s.rect(x, y, 392, 88, fill=T.PANEL if i % 2 == 0 else T.BG2,
               stroke=color, rx=8)
        s.text(x + 18, y + 28, question, size=12.5, fill=T.TEXT, weight="700")
        s.rect(x + 278, y + 14, 92, 30, fill=color, rx=4, opacity=.88)
        s.text(x + 324, y + 34, doc, size=13, anchor="middle", fill=T.BG,
               weight="800", mono=True)
        s.text(x + 18, y + 58, boundary, size=10.2, fill=T.MUTED)
        s.text(x + 18, y + 76, "搜索：型号 + 文档号 + 关键词", size=9.4,
               fill=T.DIM, mono=True)
    s.rect(42, 446, 816, 66, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(60, 472, "停止条件", size=11.5, fill=T.RED, weight="700")
    s.text(132, 472, "找不到型号、封装或 revision，就先补齐身份；不要用搜索结果摘要代替原文。",
           size=10.6, fill=T.TEXT)
    s.text(132, 495, "引脚和电气看 DS；寄存器和时序看 RM；异常行为还要交叉检查 ES。", size=10.2,
           fill=T.MUTED)
    s.footer("视觉规范：FA-002 概念连续线 · IG-008 多路径流程 · C-03 / C-10 / C-27 / C-31",
             label="自绘矢量图 · STM32 知识库")
    return s


def firmware_stack_choice() -> Svg:
    s = Svg(W, H, "固件栈不是排名表，而是边界选择", "先判断项目约束，再决定 HAL/LL、SPL、libopencm3 或 RTOS 生态")
    s.header(tag="20 选型 · IG-004", tag_color=T.VIOLET)
    columns = [
        (42, "新 STM32 项目", T.CYAN, ("HAL / LL", "CubeMX 与官方包", "跨系列维护成本低")),
        (254, "锁版 F1 旧工程", T.GREEN, ("SPL", "只维护既有边界", "不要和 HAL 双重接管")),
        (466, "轻量裸机", T.AMBER, ("libopencm3", "接受社区支持边界", "自行冻结版本与构建")),
        (678, "系统级产品", T.VIOLET, ("RTOS 生态", "设备模型与组件", "预算启动/恢复/升级")),
    ]
    for x, title, color, rows in columns:
        s.rect(x, 96, 180, 310, fill=T.PANEL, stroke=color, rx=8)
        s.rect(x, 96, 180, 46, fill=color, rx=8, opacity=.86)
        s.text(x + 90, 125, title, size=12, anchor="middle", fill=T.BG, weight="800")
        for i, row in enumerate(rows):
            yy = 184 + i * 74
            s.text(x + 90, yy, row, size=10.5 if i else 13, anchor="middle",
                   fill=color if i == 0 else T.TEXT, weight="700" if i == 0 else "normal")
            if i < 2:
                s.line(x + 24, yy + 23, x + 156, yy + 23, stroke=T.GRID, sw=1)
    s.rect(42, 432, 816, 80, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(60, 458, "明确判断", size=11.5, fill=T.RED, weight="700")
    s.text(132, 458, "新项目优先 HAL/LL；只有维护锁定版本的 F1 旧工程时才继续用 SPL。", size=11,
           fill=T.TEXT, weight="700")
    s.text(132, 484, "改变判断的条件：现有资产、认证冻结、团队能力、实时/内存预算与生命周期。", size=10.2,
           fill=T.MUTED)
    s.footer("视觉规范：FA-029 几何图解叙事 · IG-004 多列对比 · C-03 / C-10 / C-27 / C-31",
             label="自绘矢量图 · STM32 知识库")
    return s


def instrument_evidence_ladder() -> Svg:
    s = Svg(W, H, "工具给出的证据，一层比一层接近引脚", "日志能说明代码走过；只有测量能说明电压与时序真的到达硬件")
    s.header(tag="证据层级 · IG-010", tag_color=T.GREEN)
    rows = [
        ("源码 / 构建日志", "编译了哪些文件、宏、链接脚本", "不能证明固件已在目标板运行", T.VIOLET),
        ("GDB / 寄存器读回", "CPU 到过哪一行，外设状态为何", "不能证明引脚电气质量", T.CYAN),
        ("串口 / RTT 日志", "运行顺序、错误码、时间戳", "日志本身也可能阻塞或丢失", T.GREEN),
        ("逻辑分析仪", "数字电平、协议字节、相对时序", "看不清过冲、纹波和模拟裕量", T.AMBER),
        ("示波器 / 电源分析仪", "边沿、幅值、纹波、电流随时间", "探头接法与带宽仍会影响结论", T.RED),
    ]
    for i, (tool, proves, limit, color) in enumerate(rows):
        x = 74 + i * 28
        y = 92 + i * 75
        w = 752 - i * 56
        s.rect(x, y, w, 62, fill=T.PANEL if i % 2 == 0 else T.BG2,
               stroke=color, rx=8)
        s.text(x + 18, y + 25, tool, size=11.5, fill=color, weight="700")
        s.text(x + 176, y + 25, proves, size=10.2, fill=T.TEXT)
        s.text(x + 176, y + 47, "边界：" + limit, size=9.6, fill=T.MUTED)
    s.footer("视觉规范：FA-002 概念连续线 · IG-010 阶段进阶 · C-03 / C-10 / C-27 / C-31",
             label="自绘矢量图 · STM32 知识库")
    return s


def single_build_contract() -> Svg:
    s = Svg(W, H, "唯一构建合同：IDE 只是入口", "源文件、宏、头文件、链接脚本和产物必须由同一套 CMake preset 定义")
    s.header(tag="构建合同 · IG-012", tag_color=T.CYAN)
    inputs = [("CubeIDE", T.VIOLET), ("VS Code", T.CYAN), ("CLion", T.GREEN), ("CI", T.AMBER)]
    for i, (name, color) in enumerate(inputs):
        y = 96 + i * 74
        s.rect(42, y, 150, 48, fill=T.PANEL, stroke=color, rx=8)
        s.text(117, y + 30, name, size=12, anchor="middle", fill=color, weight="700")
        s.arrow(196, y + 24, 300, 244, color=color, sw=2)
    s.rect(302, 178, 278, 132, fill=T.BG2, stroke=T.CYAN, rx=8)
    s.text(441, 208, "CMakePresets.json", size=13, anchor="middle", fill=T.CYAN,
           weight="800", mono=True)
    for i, item in enumerate(("sources + defines", "include dirs + toolchain", "linker script + options")):
        s.text(441, 238 + i * 22, item, size=10.2, anchor="middle", fill=T.MUTED, mono=True)
    outputs = [("app.elf", "调试 / 下载", T.GREEN), ("app.map", "内存证据", T.AMBER),
               ("app.bin", "IAP / 量产", T.VIOLET)]
    for i, (name, note, color) in enumerate(outputs):
        y = 100 + i * 90
        s.arrow(584, 244, 670, y + 26, color=color, sw=2)
        s.rect(674, y, 184, 54, fill=T.PANEL, stroke=color, rx=8)
        s.text(690, y + 23, name, size=11.5, fill=color, weight="700", mono=True)
        s.text(690, y + 43, note, size=9.7, fill=T.MUTED)
    s.rect(302, 352, 556, 100, fill=T.PANEL, stroke=T.RED, rx=8)
    s.text(320, 379, "禁止第二套事实", size=11.5, fill=T.RED, weight="700")
    s.text(320, 403, "不要让 IDE 私下维护另一份源文件、宏、include 或链接脚本。", size=10.5, fill=T.TEXT)
    s.text(320, 428, "验收：本机与 CI 的 ELF 哈希、map 和编译命令可追溯。", size=10.2, fill=T.MUTED)
    s.footer("视觉规范：FA-002 概念连续线 · IG-012 分层结构 · C-03 / C-10 / C-27 / C-31",
             label="自绘矢量图 · STM32 知识库")
    return s


def simulator_comparison() -> Svg:
    s = Svg(W, H, "Wokwi、Renode 与真板验证的不是同一层", "先用模型缩短反馈，再把结论带回目标硬件")
    s.header(tag="22 对比 · IG-004", tag_color=T.VIOLET)
    cols = [
        (42, "Wokwi", T.CYAN, ("浏览器接线与现象", "GPIO / EXTI / I²C / TIM", "不证明真实边沿与 DMA")),
        (322, "Renode", T.GREEN, ("可脚本化机器模型", "ELF / UART / 外设访问", "实现随版本与平台描述变化")),
        (602, "目标真板", T.RED, ("实际供电、时钟与硅片", "波形 / 电流 / revision", "最终验收边界")),
    ]
    for x, title, color, rows in cols:
        s.rect(x, 92, 256, 342, fill=T.PANEL, stroke=color, rx=8)
        s.rect(x, 92, 256, 50, fill=color, rx=8, opacity=.86)
        s.text(x + 128, 124, title, size=15, anchor="middle", fill=T.BG, weight="800")
        labels = ("看什么", "能证明", "不能证明")
        for i, (label, row) in enumerate(zip(labels, rows)):
            yy = 178 + i * 84
            s.text(x + 18, yy, label, size=10, fill=color, weight="700")
            s.text(x + 18, yy + 27, row, size=10.5, fill=T.TEXT)
            if i < 2:
                s.line(x + 18, yy + 48, x + 238, yy + 48, stroke=T.GRID, sw=1)
    s.rect(42, 460, 816, 52, fill=T.BG2, stroke=T.CYAN, rx=8)
    s.text(60, 492, "顺序：模型里复现逻辑 → 固化输入与版本 → 真板测量 → 记录差异；不能反过来用模型覆盖实测。",
           size=10.4, fill=T.TEXT, weight="700")
    s.footer("视觉规范：FA-029 几何图解叙事 · IG-004 多列对比 · C-03 / C-10 / C-27 / C-31",
             label="自绘矢量图 · STM32 知识库")
    return s


def simulation_model_boundary() -> Svg:
    s = Svg(W, H, "一段固件要穿过四层模型", "上层现象成立，只说明它下面已经实现的模型足够支撑这一次运行")
    s.header(tag="22 模型 · IG-012", tag_color=T.CYAN)
    layers = [
        ("实验现象", "LED / OLED / UART 字节", T.PINK),
        ("外设模型", "GPIO / TIM / USART / DMA 是否实现", T.VIOLET),
        ("芯片平台", "地址、IRQ、时钟、复位值与引脚别名", T.CYAN),
        ("仿真引擎", "调度、时间推进、版本与脚本接口", T.GREEN),
        ("宿主环境", "浏览器 / 本机、文件路径、串口或 socket", T.AMBER),
    ]
    for i, (name, detail, color) in enumerate(layers):
        x = 74 + i * 32
        y = 92 + i * 72
        w = 752 - i * 64
        s.rect(x, y, w, 58, fill=T.PANEL if i % 2 == 0 else T.BG2,
               stroke=color, rx=8)
        s.text(x + 18, y + 25, name, size=11.5, fill=color, weight="700")
        s.text(x + 158, y + 25, detail, size=10.4, fill=T.TEXT)
        s.text(x + 158, y + 46, "先在本层找到证据，再向下追", size=9.4, fill=T.MUTED)
    s.rect(42, 466, 816, 46, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(60, 495, "例：DMA 未实现时，接线图正确也不能验证“空闲线 + 环形缓冲”收包。", size=10.6,
           fill=T.RED, weight="700")
    s.footer("视觉规范：FA-002 概念连续线 · IG-012 分层结构 · C-03 / C-10 / C-27 / C-31",
             label="自绘矢量图 · STM32 知识库")
    return s


def h7_power_domains() -> Svg:
    s = Svg(W, H, "H743 的电源脚、内核稳压器与三个域", "D1/D2/D3 是片内电源与时钟域，不是三路可以随意接线的 VDD")
    s.header(tag="25 电源 · IG-002", tag_color=T.RED)
    s.rect(298, 178, 304, 178, fill=T.PANEL2, stroke=T.CYAN, rx=8)
    s.text(450, 214, "STM32H743ZI", size=18, anchor="middle", fill=T.CYAN, weight="800")
    for i, (name, color) in enumerate((("D1 · CM7 / AXI", T.VIOLET), ("D2 · AHB/APB", T.GREEN),
                                       ("D3 · 低速/备份", T.AMBER))):
        y = 242 + i * 34
        s.rect(330, y, 240, 26, fill=T.BG2, stroke=color, rx=4)
        s.text(450, y + 18, name, size=10.3, anchor="middle", fill=color, weight="700")
    ports = [
        (42, 102, "VDD / VDDA", "1.62–3.6 V；按 DS 去耦", T.CYAN, 298, 214),
        (42, 384, "VCAP1 / VCAP2", "内核稳压器电容；不可接 VDD", T.RED, 298, 320),
        (658, 102, "VDD33USB", "USB PHY 专用供电", T.VIOLET, 602, 214),
        (658, 384, "PDR_ON", "内部/外部电源监控边界", T.AMBER, 602, 320),
    ]
    for x, y, title, note, color, tx, ty in ports:
        s.rect(x, y, 200, 72, fill=T.PANEL, stroke=color, rx=8)
        s.text(x + 100, y + 28, title, size=12, anchor="middle", fill=color, weight="700")
        s.text(x + 100, y + 52, note, size=9.5, anchor="middle", fill=T.MUTED)
        s.arrow(x + (200 if x < 450 else 0), y + 36, tx, ty, color=color, sw=2)
    s.rect(42, 474, 816, 38, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(60, 499, "供电拓扑由原理图与器件 revision 决定；HAL_PWREx_ConfigSupply() 必须与 LDO/SMPS 实物一致。",
           size=10.2, fill=T.TEXT, weight="700")
    s.footer("视觉规范：FA-029 几何图解叙事 · IG-002 中心结构 · C-03 / C-10 / C-27 / C-31",
             label="自绘矢量图 · STM32 知识库")
    return s


def h7_revision_clock_decision() -> Svg:
    s = Svg(W, H, "400 MHz 还是 480 MHz，先看 silicon revision", "产品名相同不代表硅片 revision 相同；ES0392 决定 VOS0 是否存在")
    s.header(tag="25 决策 · IG-008", tag_color=T.AMBER)
    s.rect(330, 88, 240, 58, fill=T.PANEL, stroke=T.CYAN, rx=8)
    s.text(450, 113, "读取器件丝印 / REV_ID", size=12.5, anchor="middle", fill=T.CYAN, weight="700")
    s.text(450, 134, "DBGMCU->IDCODE + ES0392", size=9.8, anchor="middle", fill=T.MUTED, mono=True)
    s.arrow(450, 150, 450, 196, color=T.CYAN, sw=2)
    s.rect(330, 198, 240, 58, fill=T.BG2, stroke=T.VIOLET, rx=8)
    s.text(450, 232, "revision 是 V？", size=14, anchor="middle", fill=T.VIOLET, weight="800")
    branches = [
        (42, 320, "否：Rev Y / W", "VOS1 · PLLN=400", "CPU 400 / HCLK 200 / PCLK 100 MHz", T.AMBER),
        (590, 320, "是：Rev V", "VOS1 ready → VOS0 · PLLN=480", "CPU 480 / HCLK 240 / PCLK 120 MHz", T.GREEN),
    ]
    for x, y, title, path, result, color in branches:
        s.arrow(450, 260, x + 134, y - 8, color=color, sw=2)
        s.rect(x, y, 268, 112, fill=T.PANEL, stroke=color, rx=8)
        s.text(x + 134, y + 29, title, size=12.5, anchor="middle", fill=color, weight="800")
        s.text(x + 134, y + 58, path, size=10.2, anchor="middle", fill=T.TEXT, mono=True)
        s.text(x + 134, y + 84, result, size=9.6, anchor="middle", fill=T.MUTED)
    s.rect(246, 458, 408, 54, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(450, 480, "任何路径：先验证供电方案，再等 VOSRDY，最后配置 PLL。", size=10.3,
           anchor="middle", fill=T.RED, weight="700")
    s.text(450, 499, "请求过的频率 ≠ 已经成立的频率。", size=9.8, anchor="middle", fill=T.MUTED)
    s.footer("视觉规范：FA-002 概念连续线 · IG-008 决策流程 · C-03 / C-10 / C-27 / C-31",
             label="自绘矢量图 · STM32 知识库")
    return s


def h7_startup_evidence() -> Svg:
    s = Svg(W, H, "480 MHz 启动后，要拿到三类互相独立的证据", "软件读回、MCO 测量和外设闭环分别排除不同错误")
    s.header(tag="25 证据 · IG-010", tag_color=T.GREEN)
    cards = [
        (42, "1 · 软件读回", ("SYSCLK = 480 MHz", "HCLK = 240 MHz", "记录供电/REV_ID/失败步骤"), T.CYAN),
        (322, "2 · 独立时钟输出", ("PC9 输出 MCO2", "SYSCLK / 5 = 96 MHz", "示波器或计数器实测"), T.AMBER),
        (602, "3 · 外设闭环", ("UART 波特率 / PWM 周期", "SysTick / RTOS tick", "独立 kernel clock 另验"), T.GREEN),
    ]
    for x, title, rows, color in cards:
        s.rect(x, 100, 256, 286, fill=T.PANEL, stroke=color, rx=8)
        s.rect(x, 100, 256, 48, fill=color, rx=8, opacity=.86)
        s.text(x + 128, 130, title, size=13, anchor="middle", fill=T.BG, weight="800")
        for i, row in enumerate(rows):
            yy = 194 + i * 64
            s.circle(x + 34, yy - 4, 8, fill=color, opacity=.82)
            s.text(x + 56, yy, row, size=10.2, fill=T.TEXT)
            if i < 2:
                s.line(x + 24, yy + 26, x + 232, yy + 26, stroke=T.GRID, sw=1)
    s.rect(42, 420, 816, 92, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(60, 449, "不能替代", size=11.5, fill=T.RED, weight="700")
    s.text(132, 449, "HAL_Delay(1000) 大约一秒，只检查一条路径；它不证明 USB、FDCAN 或其他 kernel clock。",
           size=10.3, fill=T.TEXT)
    s.text(132, 478, "96 MHz 是计算期望；仓库没有实测数据。只有仪器读数与计算一致时，才成为板级证据。",
           size=10.2, fill=T.MUTED)
    s.footer("视觉规范：FA-002 概念连续线 · IG-010 阶段进阶 · C-03 / C-10 / C-27 / C-31",
             label="自绘矢量图 · STM32 知识库")
    return s


def h7_pinmux_conflicts() -> Svg:
    s = Svg(W, H, "H7 复用冲突：功能可选，不等于能同时占用", "先列板级必需接口，再为每个冲突组只保留一个所有者")
    s.header(tag="25 复用 · IG-011", tag_color=T.VIOLET)
    conflicts = [
        ("PA11 / PA12", "FDCAN1 RX/TX", "OTG_FS DM/DP", "FDCAN 可移到 PD0/PD1 或 PB8/PB9", T.CYAN),
        ("PB6 / PB7", "USART1 TX/RX", "I²C1 SCL/SDA", "I²C1 可改 PB8/PB9，但要再查 FDCAN", T.GREEN),
        ("PC9", "MCO2", "板级外设 / 其他 AF", "测时钟前先核对原理图和 Table 9", T.AMBER),
    ]
    for i, (pins, left, right, escape, color) in enumerate(conflicts):
        y = 92 + i * 126
        s.rect(42, y, 816, 102, fill=T.PANEL if i % 2 == 0 else T.BG2,
               stroke=color, rx=8)
        s.text(64, y + 30, pins, size=12, fill=color, weight="800", mono=True)
        s.rect(238, y + 16, 212, 34, fill=T.BG, stroke=color, rx=4)
        s.text(344, y + 38, left, size=10.5, anchor="middle", fill=T.TEXT, weight="700")
        s.text(466, y + 38, "或", size=10, anchor="middle", fill=T.RED, weight="800")
        s.rect(482, y + 16, 212, 34, fill=T.BG, stroke=color, rx=4)
        s.text(588, y + 38, right, size=10.5, anchor="middle", fill=T.TEXT, weight="700")
        s.text(238, y + 76, "解法：" + escape, size=10, fill=T.MUTED)
    s.rect(42, 482, 816, 30, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(450, 502, "CubeMX 无冲突只是起点；原理图、封装脚号与目标板已占资源仍要逐项对账。", size=10.2,
           anchor="middle", fill=T.RED, weight="700")
    s.footer("视觉规范：FA-029 几何图解叙事 · IG-011 前后/冲突对比 · C-03 / C-10 / C-27 / C-31",
             label="自绘矢量图 · STM32 知识库")
    return s


ALL = [first_lab_wiring, first_success_gates, dma_buffer_ownership,
       watchdog_reset_evidence, iap_acceptance_gates,
       lowpower_current_evidence, fault_triage_ladder,
       layers_hal_ll_reg, project_structure, peripheral_bus, interrupt_priority,
       l4_idd_bench, network_debug_ladder, spl_ownership_boundary,
       network_cache_ownership, tcp_byte_stream, rtos_owner_task,
       rtos_deadline_budget, rtos_config_paths, manual_choice_map,
       firmware_stack_choice, instrument_evidence_ladder, single_build_contract,
       simulator_comparison, simulation_model_boundary, h7_power_domains,
       h7_revision_clock_decision, h7_startup_evidence, h7_pinmux_conflicts]

NAMES = {
    "first_lab_wiring": "first-lab-wiring",
    "first_success_gates": "first-success-gates",
    "dma_buffer_ownership": "dma-buffer-ownership",
    "watchdog_reset_evidence": "watchdog-reset-evidence",
    "iap_acceptance_gates": "iap-acceptance-gates",
    "lowpower_current_evidence": "lowpower-current-evidence",
    "fault_triage_ladder": "fault-triage-ladder",
    "layers_hal_ll_reg": "layers-hal-ll-reg",
    "project_structure": "project-structure",
    "peripheral_bus": "peripheral-bus",
    "interrupt_priority": "interrupt-priority",
    "l4_idd_bench": "l4-idd-bench",
    "network_debug_ladder": "network-debug-ladder",
    "spl_ownership_boundary": "spl-ownership-boundary",
    "network_cache_ownership": "network-cache-ownership",
    "tcp_byte_stream": "tcp-byte-stream",
    "rtos_owner_task": "rtos-owner-task",
    "rtos_deadline_budget": "rtos-deadline-budget",
    "rtos_config_paths": "rtos-config-paths",
    "manual_choice_map": "manual-choice-map",
    "firmware_stack_choice": "firmware-stack-choice",
    "instrument_evidence_ladder": "instrument-evidence-ladder",
    "single_build_contract": "single-build-contract",
    "simulator_comparison": "simulator-comparison",
    "simulation_model_boundary": "simulation-model-boundary",
    "h7_power_domains": "h7-power-domains",
    "h7_revision_clock_decision": "h7-revision-clock-decision",
    "h7_startup_evidence": "h7-startup-evidence",
    "h7_pinmux_conflicts": "h7-pinmux-conflicts",
}


def main(argv):
    import os
    import xml.dom.minidom
    here = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(os.path.dirname(here), "assets", "diagrams")
    os.makedirs(out_dir, exist_ok=True)
    only = set(argv[1:])
    for fn in ALL:
        name = NAMES[fn.__name__]
        if only and name not in only:
            continue
        path = os.path.join(out_dir, name + ".svg")
        fn().save(path)
        xml.dom.minidom.parse(path)
        print(f"[ok] {name}.svg")


if __name__ == "__main__":
    main(__import__("sys").argv)
