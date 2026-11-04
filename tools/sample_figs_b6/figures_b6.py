#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static B6 Handraw figures for chapters 23-28 and appendix F.

    python tools/sample_figs_b6/figures_b6.py assets/diagrams
"""

from __future__ import annotations

import importlib.util
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from svgkit import Svg, T


def _load_common():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_common.py")
    spec = importlib.util.spec_from_file_location("sample_figs_b6_common", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_common = _load_common()
credit = _common.credit
audit_static = _common.audit_static


def f1_g0_compare() -> Svg:
    c = Svg(960, 880, "F1 迁到 G0 时封装脚序、BOOT/SWCLK 共脚与选项字节不能照抄",
            "STM32G071RB · chapter 23 · DS12232 / RM0444 / AN2606")
    c.header(title="F1 → G0 迁移对照：五处不能照抄", tag="23", tag_color=T.CYAN)
    c.text(40, 88, "同一功能名，电气与启动语义可能已经换人", size=16, fill=T.TEXT, weight="700")
    c.text(40, 114, "compare · pin / boot latch / AF / option bytes / max clock", size=13, fill=T.CYAN)

    rows = [
        ("封装脚序", "F103C8 BluePill", "G071RB LQFP64", "同名外设脚位重排", "先对 Table 12–14", T.BLUE),
        ("BOOT / SWD", "BOOT0 独立脚", "BOOT0 与 SWCLK 共脚", "调试与启动抢同一脚", "第四个 SYSCLK 锁存", T.CYAN),
        ("选项字节", "常用 RDP/WRP", "BOOT_LOCK / DBG_SWEN", "失联分支变多", "读回后再改", T.GREEN),
        ("复用表", "F1 AF 习惯", "G0 必须查表", "抄 AF 会落到空脚", "只写表内名字", T.AMBER),
        ("时钟上限", "72 MHz 口径", "家族最高 64 MHz", "超频假设失效", "按 DS 限值验收", T.VIOLET),
    ]
    heads = ("检查项", "F1 习惯", "G0 现实", "摔点", "第一动作")
    xs = [40, 170, 360, 560, 760]
    widths = [120, 180, 190, 190, 160]
    y0 = 150
    for i, h in enumerate(heads):
        c.rect(xs[i], y0, widths[i], 40, fill=T.BG2, stroke=T.STROKE, rx=4)
        c.text(xs[i] + widths[i] / 2, y0 + 26, h, size=13, fill=T.MUTED, anchor="middle", weight="700")
    for r, (a, b, d, e, f, color) in enumerate(rows):
        y = y0 + 52 + r * 100
        vals = (a, b, d, e, f)
        for i, val in enumerate(vals):
            c.rect(xs[i], y, widths[i], 88, fill=T.PANEL, stroke=color if i == 0 else T.STROKE, rx=8)
            c.text(xs[i] + widths[i] / 2, y + 48, val, size=13 if i else 14,
                   fill=color if i == 0 else T.TEXT, anchor="middle", weight="700" if i == 0 else "400")

    c.rect(40, 760, 880, 56, fill=T.BG2, stroke=T.GREEN, rx=8)
    c.text(56, 784, "对照口径：以 G071RB 订货号 + DS12232 / RM0444 修订为准；空 Flash、RDP、DBG_SWEN 另做闭环。",
           size=13, fill=T.TEXT)
    c.text(56, 804, "开源对照：配套例程只提供结构，不替代手册脚注。", size=12, fill=T.MUTED)
    credit(c, "自绘 · F1/G0 迁移五问对照 · 非实拍")
    return c


def l4_mode_compare() -> Svg:
    c = Svg(960, 880, "L4 低功耗模式对比：保留状态、唤醒源与电流口径一次看清",
            "STM32L476RG · chapter 24 · RM0351 / AN4746 / DS10198")
    c.header(title="L4 低功耗四档对照：睡前先问保留了什么", tag="24", tag_color=T.GREEN)
    c.text(40, 88, "Sleep / Stop 1 / Stop 2 / Standby — 不是越深越好，是证据链能不能接上",
           size=15, fill=T.TEXT, weight="700")
    c.text(40, 114, "compare · retained state · wake path · IDD is chip-typical not board truth",
           size=13, fill=T.CYAN)

    modes = [
        ("Sleep", "CPU 停", "外设可跑", "任意中断", "调试最易", T.BLUE),
        ("Stop 1", "时钟停", "SRAM+寄存器", "EXTI/RTC…", "恢复快", T.CYAN),
        ("Stop 2", "更深停", "部分保留", "受限唤醒源", "封面 1.1 µA*", T.GREEN),
        ("Standby", "几乎掉电", "备份域", "WKUP/RTC", "等于冷启动", T.AMBER),
    ]
    for i, (name, cpu, ret, wake, note, color) in enumerate(modes):
        x = 40 + i * 230
        c.rect(x, 150, 210, 320, fill=T.PANEL, stroke=color, rx=8)
        c.rect(x, 150, 210, 48, fill=T.BG2, stroke=color, rx=8)
        c.text(x + 105, 180, name, size=18, fill=color, anchor="middle", weight="700")
        for j, (lab, val) in enumerate((("CPU", cpu), ("保留", ret), ("唤醒", wake), ("备注", note))):
            yy = 220 + j * 55
            c.text(x + 16, yy, lab, size=12, fill=T.MUTED)
            c.text(x + 16, yy + 24, val, size=14, fill=T.TEXT, weight="700")

    c.rect(40, 500, 880, 120, fill=T.PANEL, stroke=T.STROKE, rx=8)
    c.title_block(56, 520, "验收提醒（首帧可读）", color=T.AMBER)
    lines = [
        "1. Stop 2 封面电流是芯片典型值，不是本仓库整板实测；JP6 / 积分波形才进账。",
        "2. HAL 清位前先留下唤醒证据；SysTick 若不停，1 ms 节拍会反复叫醒。",
        "3. 醒后临时时钟是 MSI 或 HSI16，通信前必须恢复到业务时钟并复验。",
    ]
    for i, line in enumerate(lines):
        c.text(56, 560 + i * 22, line, size=13, fill=T.TEXT)

    c.rect(40, 650, 880, 90, fill=T.BG2, stroke=T.GREEN, rx=8)
    c.text(56, 680, "出处优先：RM0351 模式表、DS10198 典型值、AN4746 测量边界；CubeL4 Stop2 示例仅对照。",
           size=13, fill=T.TEXT)
    c.text(56, 708, "*1.1 µA / 带 RTC 1.4 µA 为手册封面数，必须随 revision、VDD、温度一并记录。",
           size=12, fill=T.MUTED)
    credit(c, "自绘 · L4 低功耗四档对照 · 非实拍")
    return c


def l4_wake_triage() -> Svg:
    c = Svg(960, 880, "Stop 2 醒不来 / 乱醒 / 醒后通信失败的三岔口排错",
            "STM32L476RG · chapter 24 · RM0351 wake evidence")
    c.header(title="Stop 2 唤醒排错：先分清三种失败", tag="24", tag_color=T.AMBER)
    c.text(40, 88, "triage · never woke · woke too often · woke but link broken", size=14, fill=T.CYAN)

    branches = [
        ("从未醒来", T.RED, ["唤醒源未使能", "进入前 EXTI 极性错", "BOOT/复位被误判"], "第一探针", "IRQ 入口读原始标志"),
        ("反复醒来", T.AMBER, ["SysTick 未停", "外设噪声打 EXTI", "RTC 周期过密"], "第一探针", "停节拍后再进 Stop"),
        ("醒了无业务", T.VIOLET, ["时钟停在 MSI/HSI", "GPIO 复用未恢复", "串口波特率漂"], "第一探针", "四项恢复证据清单"),
    ]
    for i, (title, color, causes, probe_h, probe) in enumerate(branches):
        x = 40 + i * 300
        c.rect(x, 130, 280, 420, fill=T.PANEL, stroke=color, rx=8)
        c.rect(x, 130, 280, 52, fill=T.BG2, stroke=color, rx=8)
        c.text(x + 140, 162, title, size=17, fill=color, anchor="middle", weight="700")
        c.text(x + 20, 210, "常见原因", size=13, fill=T.MUTED, weight="700")
        for j, cause in enumerate(causes):
            c.rect(x + 16, 230 + j * 48, 248, 40, fill=T.BG, stroke=T.STROKE, rx=4)
            c.text(x + 140, 255 + j * 48, cause, size=13, fill=T.TEXT, anchor="middle")
        c.rect(x + 16, 400, 248, 120, fill=T.BG2, stroke=color, rx=8)
        c.text(x + 140, 432, probe_h, size=13, fill=color, anchor="middle", weight="700")
        c.text(x + 140, 470, probe, size=14, fill=T.TEXT, anchor="middle", weight="700")

    c.rect(40, 580, 880, 160, fill=T.PANEL, stroke=T.GREEN, rx=8)
    c.title_block(56, 600, "四项恢复证据（醒后必须齐）", color=T.GREEN)
    for i, item in enumerate(("原始唤醒位已记录", "系统时钟已回到业务源", "外设时钟与分频已复算", "通信首包有对端确认")):
        x = 56 + (i % 2) * 420
        y = 650 + (i // 2) * 36
        c.circle(x, y, 6, fill=T.GREEN)
        c.text(x + 18, y + 5, item, size=14, fill=T.TEXT)
    credit(c, "自绘 · Stop2 唤醒三岔口 · 非实拍")
    return c


def h7_migrate_triage() -> Svg:
    c = Svg(960, 880, "F4 迁 H7：供电档、硅片 revision、Cache/DMA 与时钟链的排错顺序",
            "STM32H743ZI · chapter 25 · DS12110 / RM0433 / ES0392")
    c.header(title="F4 → H7 迁移排错：先供电与 revision，再谈 480 MHz", tag="25", tag_color=T.VIOLET)
    c.text(40, 88, "triage · supply/VOS · revision · VCAP · cache/DMA · clock evidence", size=14, fill=T.CYAN)

    steps = [
        ("1 供电宏≠原理图", "LDO/SMPS/VCAP 实际拓扑", "对照板级供电再选 VOS", T.RED),
        ("2 认硅片 revision", "Rev Y/W 无 VOS0", "480 MHz 仅 Rev V 路径", T.AMBER),
        ("3 Cache/DMA 域", "DTCM 对 Ethernet DMA 不可见", "缓冲域、对齐、维护方向", T.CYAN),
        ("4 时钟链验收", "MCO + 频率读回 + 外设波形", "计算预期不是实测替代", T.GREEN),
    ]
    for i, (title, detail, action, color) in enumerate(steps):
        y = 130 + i * 130
        c.rect(40, y, 880, 110, fill=T.PANEL, stroke=color, rx=8)
        c.rect(40, y, 64, 110, fill=T.BG2, stroke=color, rx=8)
        c.text(72, y + 62, str(i + 1), size=28, fill=color, anchor="middle", weight="700")
        c.text(130, y + 40, title, size=18, fill=color, weight="700")
        c.text(130, y + 68, detail, size=14, fill=T.TEXT)
        c.text(130, y + 94, "动作：" + action, size=13, fill=T.MUTED)

    c.rect(40, 670, 880, 90, fill=T.BG2, stroke=T.STROKE, rx=8)
    c.text(56, 702, "官方优先：DS12110 / RM0433 / ES0392；CubeH7 时钟与 MSP 示例仅对照，不覆盖板级供电。",
           size=13, fill=T.TEXT)
    c.text(56, 730, "冲突时以手册适用条件为准；社区 480 MHz 帖子不能跳过 revision 门。", size=12, fill=T.MUTED)
    credit(c, "自绘 · H7 迁移四步排错 · 非实拍")
    return c


def spl_hal_compare() -> Svg:
    c = Svg(960, 880, "SPL 与 HAL/LL：版本边界、初始化所有权与迁移对照",
            "STM32F10x SPL V3.5.0 · chapter 26 · STSW-STM32054 / RM0008")
    c.header(title="SPL ↔ HAL/LL 对照：一次只迁一个外设", tag="26", tag_color=T.BLUE)
    c.text(40, 88, "compare · ownership · IRQ model · DMA wiring · freeze-then-migrate", size=14, fill=T.CYAN)

    cols = [
        ("维度", "SPL V3.5.0", "HAL / LL", T.MUTED),
        ("版本门", "钉死 V3.5.0 + 宏", "Cube 包 + HAL 版本", T.BLUE),
        ("初始化", "时钟→默认→配置→使能", "MSP + Init + 回调约定", T.CYAN),
        ("中断", "自己写 IRQ 分发", "HAL 回调可挡证据", T.GREEN),
        ("DMA", "两驱动不自动绑", "Handle 绑定仍要验收", T.AMBER),
        ("迁移策略", "先冻结波形基线", "单外设对照再切换", T.VIOLET),
    ]
    for i, (a, b, d, color) in enumerate(cols):
        y = 120 + i * 90
        for j, (x, w, text) in enumerate(((40, 200, a), (250, 330, b), (590, 330, d))):
            fill = T.BG2 if i == 0 else T.PANEL
            c.rect(x, y, w, 78, fill=fill, stroke=color if j == 0 and i else T.STROKE, rx=8)
            c.text(x + w / 2, y + 44, text, size=14 if i else 15,
                   fill=color if (i and j == 0) else T.TEXT, anchor="middle",
                   weight="700" if i == 0 or j == 0 else "400")

    c.rect(40, 680, 880, 80, fill=T.BG2, stroke=T.GREEN, rx=8)
    c.text(56, 710, "开源镜像只用于核对目录与原型；规范结论回到 ST 产品页与 RM0008。禁止 SPL/HAL 双重初始化。",
           size=13, fill=T.TEXT)
    c.text(56, 738, "保留 SPL 的理由必须写进工程清单；否则按单外设波形对照迁到 HAL/LL。", size=12, fill=T.MUTED)
    credit(c, "自绘 · SPL/HAL 迁移对照 · 非实拍")
    return c


def net_link_triage() -> Svg:
    c = Svg(960, 880, "网络分层排错：link、ping、TCP、MQTT/TLS 各层证据不能互相代替",
            "chapter 27 · RM0433 / AN4839 / lwIP pitfalls")
    c.header(title="联网排错阶梯：每层只问本层证据", tag="27", tag_color=T.CYAN)
    c.text(40, 88, "triage · PHY link ≠ ping ≠ TCP ACK ≠ MQTT up ≠ business commit", size=14, fill=T.CYAN)

    layers = [
        ("L1 链路", "RJ45 / link LED", "RMII 时钟与脚", "示波器/寄存器 link", T.BLUE),
        ("L2/L3", "ARP / ping", "MAC 地址与 IP", "PCAP 见请求应答", T.CYAN),
        ("L4 TCP", "SYN/ACK / 分帧", "MSS 与缓冲域", "序号与长度字段", T.GREEN),
        ("应用", "MQTT/TLS/业务", "证书时间与 QoS", "落盘/幂等证据", T.VIOLET),
    ]
    for i, (name, symptom, check, evidence, color) in enumerate(layers):
        y = 130 + i * 115
        c.rect(40, y, 880, 100, fill=T.PANEL, stroke=color, rx=8)
        c.rect(40, y, 160, 100, fill=T.BG2, stroke=color, rx=8)
        c.text(120, y + 56, name, size=16, fill=color, anchor="middle", weight="700")
        c.text(220, y + 36, "现象：" + symptom, size=14, fill=T.TEXT)
        c.text(220, y + 62, "先查：" + check, size=14, fill=T.TEXT)
        c.text(220, y + 88, "证据：" + evidence, size=13, fill=T.MUTED)
        if i < len(layers) - 1:
            c.arrow(120, y + 100, 120, y + 115, color=T.STROKE, sw=1.5, marker=True)

    c.rect(40, 610, 880, 150, fill=T.BG2, stroke=T.AMBER, rx=8)
    c.title_block(56, 630, "H7 额外门：DMA 看见的内存", color=T.AMBER)
    c.text(56, 670, "Ethernet DMA 不能访问 DTCM（0x20000000）；缓冲 32 字节对齐；Cache 维护分清方向。",
           size=14, fill=T.TEXT)
    c.text(56, 698, "官方：RM0433 / AN4839；开源：CubeH7 lwIP 示例与 lwIP pitfalls 仅对照线程边界。",
           size=13, fill=T.MUTED)
    c.text(56, 726, "禁止用 link LED 代替 ping，用 TCP ACK 代替业务 exactly-once。", size=13, fill=T.TEXT)
    credit(c, "自绘 · 网络分层排错阶梯 · 非实拍")
    return c


def os_compare() -> Svg:
    c = Svg(960, 880, "FreeRTOS / RT-Thread / Zephyr / CMSIS-RTOS2：选型对照而不是口号对照",
            "chapter 28 · FreeRTOS 11.3.2 / RT-Thread 5.3.0 / Zephyr 4.4.2 / CMSIS 6.4.0")
    c.header(title="RTOS 选型对照：API 名字不能替代预算与上下文", tag="28", tag_color=T.VIOLET)
    c.text(40, 88, "compare · kernel shape · device model · config surface · proof cost", size=14, fill=T.CYAN)

    systems = [
        ("FreeRTOS", "小内核自组合", "自行拼驱动", "Config 即合同", "最易裁剪", T.BLUE),
        ("RT-Thread", "组件+设备框架", "先找设备再操作", "启动按书脊编号", "生态组件多", T.CYAN),
        ("Zephyr", "DT+Kconfig 生成", "子系统共同构建", "工作队列≠白送线程", "配置面大", T.GREEN),
        ("CMSIS-RTOS2", "统一接口层", "不统一实现", "移植外观一致", "仍要验底层", T.AMBER),
    ]
    for i, (name, shape, device, caveat, note, color) in enumerate(systems):
        x = 40 + i * 230
        c.rect(x, 140, 210, 430, fill=T.PANEL, stroke=color, rx=8)
        c.rect(x, 140, 210, 56, fill=T.BG2, stroke=color, rx=8)
        c.text(x + 105, 174, name, size=16, fill=color, anchor="middle", weight="700")
        for j, (lab, val) in enumerate((("形态", shape), ("设备模型", device), ("关键门", caveat), ("备注", note))):
            yy = 220 + j * 80
            c.text(x + 16, yy, lab, size=12, fill=T.MUTED)
            c.text(x + 16, yy + 28, val, size=13, fill=T.TEXT, weight="700")

    c.rect(40, 600, 880, 160, fill=T.BG2, stroke=T.GREEN, rx=8)
    c.title_block(56, 620, "选型时固定问四句", color=T.GREEN)
    qs = [
        "最坏时延预算是否按任务/IRQ/IPC 分开写清？",
        "驱动生命周期是否有超时与恢复，而不只是 Init 成功？",
        "配置（Config/Kconfig/DT）能否作为可审计合同复查？",
        "故障注入是否覆盖队列满、任务冻结、驱动超时？",
    ]
    for i, q in enumerate(qs):
        c.text(56, 660 + i * 24, f"{i+1}. {q}", size=13, fill=T.TEXT)
    credit(c, "自绘 · 四系统选型对照 · 非实拍")
    return c


def rtos_fault_triage() -> Svg:
    c = Svg(960, 880, "系统故障三岔口：队列满、任务冻结、驱动超时如何收敛到第一分歧",
            "chapter 28 · owner task / health supervisor / watchdog")
    c.header(title="系统故障排错：先回到第一处分歧", tag="28", tag_color=T.RED)
    c.text(40, 88, "triage · queue full · task frozen · driver timeout · supervisor feeds WDG only",
           size=14, fill=T.CYAN)

    branches = [
        ("队列满", T.AMBER, ["生产者过快", "消费者阻塞在驱动", "队列深度无预算"], "第一探针", "队列水位 + 持锁时间"),
        ("任务冻结", T.RED, ["死锁/优先级反转", "等待无超时", "栈溢出改返回址"], "第一探针", "高水位与任务状态"),
        ("驱动超时", T.VIOLET, ["外设挂死", "DMA 未完成", "IRQ 丢失"], "第一探针", "驱动状态机时间戳"),
    ]
    for i, (title, color, causes, ph, probe) in enumerate(branches):
        x = 40 + i * 300
        c.rect(x, 130, 280, 400, fill=T.PANEL, stroke=color, rx=8)
        c.rect(x, 130, 280, 50, fill=T.BG2, stroke=color, rx=8)
        c.text(x + 140, 160, title, size=17, fill=color, anchor="middle", weight="700")
        for j, cause in enumerate(causes):
            c.rect(x + 16, 200 + j * 50, 248, 42, fill=T.BG, stroke=T.STROKE, rx=4)
            c.text(x + 140, 226 + j * 50, cause, size=13, fill=T.TEXT, anchor="middle")
        c.rect(x + 16, 370, 248, 130, fill=T.BG2, stroke=color, rx=8)
        c.text(x + 140, 410, ph, size=13, fill=color, anchor="middle", weight="700")
        c.text(x + 140, 450, probe, size=14, fill=T.TEXT, anchor="middle", weight="700")

    c.rect(40, 560, 880, 200, fill=T.PANEL, stroke=T.GREEN, rx=8)
    c.title_block(56, 580, "监督者规则（可进实验三）", color=T.GREEN)
    rules = [
        "只有健康监督者喂狗；业务任务成功不直接等于系统健康。",
        "启动顺序：先证明底座（时钟/内存/存储），再开放服务端口。",
        "每个故障注入场景要能指回第一分歧点，而不是最后崩溃点。",
        "开源版本钉死：FreeRTOS/RTT/Zephyr/CMSIS 的 tag 写进验收记录。",
    ]
    for i, r in enumerate(rules):
        c.text(56, 620 + i * 28, f"• {r}", size=13, fill=T.TEXT)
    credit(c, "自绘 · 系统故障三岔口 · 非实拍")
    return c


def oss_map() -> Svg:
    c = Svg(960, 880, "开源地图：按证据层选择仓库，星标多不等于该读",
            "appendix F · Cube / CMSIS / libopencm3 / FreeRTOS / RT-Thread")
    c.header(title="开源项目地图：先问要哪一份证据", tag="F", tag_color=T.GREEN)
    c.text(40, 88, "concept · clone → find the .h / function → compare with RM/DS → keep license boundary",
           size=13, fill=T.CYAN)

    cards = [
        ("厂商实现", "STM32Cube*", "Init/MSP/例程结构", "BSD/Apache/SLA 混用", T.BLUE),
        ("内核头文件", "CMSIS_6", "__I/__O/__IO 权限", "Apache-2.0", T.CYAN),
        ("手册翻译", "libopencm3", "memorymap.h 宏", "见 COPYING", T.GREEN),
        ("调度内核", "FreeRTOS-Kernel", "port 层上下文切换", "MIT", T.AMBER),
        ("组件框架", "RT-Thread", "设备框架与启动序", "Apache-2.0", T.VIOLET),
        ("生成式构建", "Zephyr", "DT + Kconfig", "Apache-2.0+", T.PINK),
    ]
    for i, (role, repo, read, lic, color) in enumerate(cards):
        x = 40 + (i % 3) * 300
        y = 130 + (i // 3) * 240
        c.rect(x, y, 280, 210, fill=T.PANEL, stroke=color, rx=8)
        c.rect(x, y, 280, 46, fill=T.BG2, stroke=color, rx=8)
        c.text(x + 140, y + 30, role, size=15, fill=color, anchor="middle", weight="700")
        c.text(x + 20, y + 78, repo, size=16, fill=T.TEXT, weight="700")
        c.text(x + 20, y + 118, "先读：" + read, size=13, fill=T.TEXT)
        c.text(x + 20, y + 152, "许可：" + lic, size=12, fill=T.MUTED)
        c.text(x + 20, y + 184, "边界：仅对照，不分发源码", size=12, fill=T.MUTED)

    c.rect(40, 640, 880, 120, fill=T.BG2, stroke=T.STROKE, rx=8)
    c.text(56, 672, "提问前五件事：订货号、手册修订、最小复现、已排除项、期望行为——再贴仓库路径。",
           size=14, fill=T.TEXT)
    c.text(56, 702, "星标是人气，不是阅读优先级；归档与只读镜像要分开标注。", size=13, fill=T.MUTED)
    c.text(56, 732, "冲突裁定：官方 RM/DS 适用条件优先；开源差异写入坑表。", size=13, fill=T.TEXT)
    credit(c, "自绘 · 开源证据层地图 · 非实拍")
    return c


FIGURES = (
    ("sample-23-f1-g0-compare.svg", f1_g0_compare),
    ("sample-24-mode-compare.svg", l4_mode_compare),
    ("sample-24-wake-triage.svg", l4_wake_triage),
    ("sample-25-migrate-triage.svg", h7_migrate_triage),
    ("sample-26-spl-hal-compare.svg", spl_hal_compare),
    ("sample-27-link-triage.svg", net_link_triage),
    ("sample-28-os-compare.svg", os_compare),
    ("sample-28-fault-triage.svg", rtos_fault_triage),
    ("sample-f-oss-map.svg", oss_map),
)


def main(out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    for name, builder in FIGURES:
        path = os.path.join(out_dir, name)
        builder().save(path)
        audit_static(name, path)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "assets/diagrams")
