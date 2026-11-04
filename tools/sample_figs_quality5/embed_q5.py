#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Embed ch23–28 + appendix F quality figures into zh+en chapters."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

BLOCK = """
<p align="center">
  <img src="{src}" width="{width}" alt="{alt}">
  <br><sub>{cap}</sub>
</p>
"""


def _insert_after_heading(path: Path, marker: str, needle: str, block: str) -> bool:
    text = path.read_text(encoding="utf-8")
    if needle in text:
        print("skip", path.name, needle)
        return False
    if marker not in text:
        raise SystemExit(f"marker missing in {path}: {marker!r}")
    idx = text.index(marker)
    nl = text.find("\n", idx)
    if nl < 0:
        raise SystemExit(f"no newline after marker in {path}")
    insert_at = nl + 1
    text = text[:insert_at] + "\n" + block + "\n" + text[insert_at:]
    path.write_text(text, encoding="utf-8")
    print("+", path.parent.name, path.name, "<-", needle)
    return True


def _blk(src, width, alt, cap):
    return BLOCK.format(src=src, width=width, alt=alt, cap=cap)


EMBEDS = [
    # ---- ch23 ----
    {
        "zh": ROOT / "docs" / "23-STM32G0引脚.md",
        "en": ROOT / "docs" / "en" / "23-stm32g0-pins.md",
        "marker_zh": "## BOOT0 与 SWCLK 共脚：先判定启动来源",
        "marker_en": "## BOOT0 shares SWCLK: determine the boot source first",
        "needle": "sample-23-boot0-swclk.svg",
        "src_zh": "../assets/diagrams/sample-23-boot0-swclk.svg",
        "src_en": "../../assets/diagrams/sample-23-boot0-swclk.svg",
        "width": 760,
        "alt_zh": "G0：BOOT0 采样先于 SWD 信任",
        "alt_en": "G0: sample BOOT0 before trusting SWD",
        "cap_zh": "▲ 自绘。先判定启动来源，再驱动 SWCLK。",
        "cap_en": "▲ Drawn for this book. Decide boot source, then drive SWCLK.",
    },
    {
        "zh": ROOT / "docs" / "23-STM32G0引脚.md",
        "en": ROOT / "docs" / "en" / "23-stm32g0-pins.md",
        "marker_zh": "### 共脚硬件：采样稳定与调试驱动要同时成立",
        "marker_en": "### Shared-pin hardware: stable sampling and debug drive must coexist",
        "needle": "sample-23-boot-source-flow.svg",
        "src_zh": "../assets/animations/sample-23-boot-source-flow.svg",
        "src_en": "../../assets/animations/sample-23-boot-source-flow.svg",
        "width": 720,
        "alt_zh": "G0 启动来源判定流程动画",
        "alt_en": "G0 boot-source decision flow",
        "cap_zh": "▲ 自绘矢量动画（FA-002）。option → BOOT0 → 向量 → SWD。",
        "cap_en": "▲ Hand-drawn CSS animation (FA-002). option → BOOT0 → vectors → SWD.",
    },
    {
        "zh": ROOT / "docs" / "23-STM32G0引脚.md",
        "en": ROOT / "docs" / "en" / "23-stm32g0-pins.md",
        "marker_zh": "## 从 F1 抄代码时最容易摔的几处",
        "marker_en": "## Common ways an F1 port falls over",
        "needle": "sample-23-f1-copy-traps.svg",
        "src_zh": "../assets/diagrams/sample-23-f1-copy-traps.svg",
        "src_en": "../../assets/diagrams/sample-23-f1-copy-traps.svg",
        "width": 760,
        "alt_zh": "F1 抄脚到 G0 的常见陷阱",
        "alt_en": "Common F1→G0 pin copy traps",
        "cap_zh": "▲ 自绘。同名外设 ≠ 同脚；以 DS 表为准。",
        "cap_en": "▲ Drawn for this book. Same peripheral name ≠ same pin; trust the DS table.",
    },
    # ---- ch24 ----
    {
        "zh": ROOT / "docs" / "24-STM32L4引脚.md",
        "en": ROOT / "docs" / "en" / "24-stm32l4-pins.md",
        "marker_zh": "## 低功耗模式与状态保持（RM0351）",
        "marker_en": "## Low-power modes and retained state (RM0351)",
        "needle": "sample-24-stop2-retain.svg",
        "src_zh": "../assets/diagrams/sample-24-stop2-retain.svg",
        "src_en": "../../assets/diagrams/sample-24-stop2-retain.svg",
        "width": 760,
        "alt_zh": "L4 Stop2 保持与必须重配对照",
        "alt_en": "L4 Stop2 retention vs must-redo map",
        "cap_zh": "▲ 自绘。Stop2 不是 RAM 永存；先画保持表再睡。",
        "cap_en": "▲ Drawn for this book. Stop2 is not forever-RAM; map retention first.",
    },
    {
        "zh": ROOT / "docs" / "24-STM32L4引脚.md",
        "en": ROOT / "docs" / "en" / "24-stm32l4-pins.md",
        "marker_zh": "## Stop 2 进入、唤醒与时钟恢复闭环",
        "marker_en": "## Stop 2: entry, wake evidence, and clock recovery",
        "needle": "sample-24-wake-restore-flow.svg",
        "src_zh": "../assets/animations/sample-24-wake-restore-flow.svg",
        "src_en": "../../assets/animations/sample-24-wake-restore-flow.svg",
        "width": 720,
        "alt_zh": "Stop2 唤醒后时钟与通信恢复流程",
        "alt_en": "Stop2 wake: restore clocks before talking",
        "cap_zh": "▲ 自绘矢量动画（FA-002）。flag → 时钟 → 通信 → 应用。",
        "cap_en": "▲ Hand-drawn CSS animation (FA-002). flag → clocks → comms → app.",
    },
    {
        "zh": ROOT / "docs" / "24-STM32L4引脚.md",
        "en": ROOT / "docs" / "en" / "24-stm32l4-pins.md",
        "marker_zh": "## 可复算的电流测量与续航账",
        "marker_en": "## A current and battery-life calculation you can reproduce",
        "needle": "sample-24-idd-jp6.svg",
        "src_zh": "../assets/diagrams/sample-24-idd-jp6.svg",
        "src_en": "../../assets/diagrams/sample-24-idd-jp6.svg",
        "width": 760,
        "alt_zh": "Nucleo JP6 电流测量与续航账",
        "alt_en": "Nucleo JP6 IDD measurement and battery math",
        "cap_zh": "▲ 自绘。JP6 积分是验收页；别用万用表拍脑袋。",
        "cap_en": "▲ Drawn for this book. JP6 integral is the accept sheet — not a DMM guess.",
    },
    # ---- ch25 ----
    {
        "zh": ROOT / "docs" / "25-STM32H7引脚.md",
        "en": ROOT / "docs" / "en" / "25-stm32h7-pins.md",
        "marker_zh": "## 先选供电与电压档，再切换 480 MHz",
        "marker_en": "## Select the supply and voltage scale before 480 MHz",
        "needle": "sample-25-voltage-scale.svg",
        "src_zh": "../assets/diagrams/sample-25-voltage-scale.svg",
        "src_en": "../../assets/diagrams/sample-25-voltage-scale.svg",
        "width": 760,
        "alt_zh": "H7 电压档与 480 MHz 门禁",
        "alt_en": "H7 voltage scale gate before 480 MHz",
        "cap_zh": "▲ 自绘。VOS 就绪证据先于 PLL 锁频。",
        "cap_en": "▲ Drawn for this book. VOS ready evidence before PLL lock.",
    },
    {
        "zh": ROOT / "docs" / "25-STM32H7引脚.md",
        "en": ROOT / "docs" / "en" / "25-stm32h7-pins.md",
        "marker_zh": "## HSE 8 MHz 到 480 MHz：一条可复算的时钟链",
        "marker_en": "## From 8 MHz HSE to 480 MHz: a reproducible clock chain",
        "needle": "sample-25-hse-to-480-flow.svg",
        "src_zh": "../assets/animations/sample-25-hse-to-480-flow.svg",
        "src_en": "../../assets/animations/sample-25-hse-to-480-flow.svg",
        "width": 720,
        "alt_zh": "HSE→PLL→480 MHz 时钟链动画",
        "alt_en": "HSE→PLL→480 MHz clock-chain motion",
        "cap_zh": "▲ 自绘矢量动画（FA-002）。VOS → HSE → PLL1 → SYS。",
        "cap_en": "▲ Hand-drawn CSS animation (FA-002). VOS → HSE → PLL1 → SYS.",
    },
    {
        "zh": ROOT / "docs" / "25-STM32H7引脚.md",
        "en": ROOT / "docs" / "en" / "25-stm32h7-pins.md",
        "marker_zh": "## 从 F4 迁过来",
        "marker_en": "## Moving a design across from F4",
        "needle": "sample-25-dcache-dma.svg",
        "src_zh": "../assets/diagrams/sample-25-dcache-dma.svg",
        "src_en": "../../assets/diagrams/sample-25-dcache-dma.svg",
        "width": 760,
        "alt_zh": "H7 D-Cache 与 DMA 可见性边界",
        "alt_en": "H7 D-Cache vs DMA visibility boundary",
        "cap_zh": "▲ 自绘。CPU 看见的内存 ≠ DMA 看见的；先 clean/invalidate。",
        "cap_en": "▲ Drawn for this book. CPU view ≠ DMA view; clean/invalidate first.",
    },
    # ---- ch26 ----
    {
        "zh": ROOT / "docs" / "26-STM32F10x标准外设库SPL.md",
        "en": ROOT / "docs" / "en" / "26-spl.md",
        "marker_zh": "## 2. 工程骨架：少一个文件都可能“函数有声明、链接没实现”",
        "marker_en": "## 2. Project skeleton",
        "needle": "sample-26-file-matrix.svg",
        "src_zh": "../assets/diagrams/sample-26-file-matrix.svg",
        "src_en": "../../assets/diagrams/sample-26-file-matrix.svg",
        "width": 760,
        "alt_zh": "SPL 必链文件矩阵",
        "alt_en": "SPL must-link file matrix",
        "cap_zh": "▲ 自绘。缺一个 .c = 声明有、链接无。",
        "cap_en": "▲ Drawn for this book. Missing one .c = declared, never linked.",
    },
    {
        "zh": ROOT / "docs" / "26-STM32F10x标准外设库SPL.md",
        "en": ROOT / "docs" / "en" / "26-spl.md",
        "marker_zh": "## 3. 统一调用模型：时钟、默认值、配置、使能",
        "marker_en": "## 3. The common model: clock, defaults, configuration, enable",
        "needle": "sample-26-clk-cfg-en-flow.svg",
        "src_zh": "../assets/animations/sample-26-clk-cfg-en-flow.svg",
        "src_en": "../../assets/animations/sample-26-clk-cfg-en-flow.svg",
        "width": 720,
        "alt_zh": "SPL 时钟→配置→使能调用链动画",
        "alt_en": "SPL clock→config→enable call-chain motion",
        "cap_zh": "▲ 自绘矢量动画（FA-002）。RCC → 默认值 → Init → 使能。",
        "cap_en": "▲ Hand-drawn CSS animation (FA-002). RCC → defaults → Init → enable.",
    },
    {
        "zh": ROOT / "docs" / "26-STM32F10x标准外设库SPL.md",
        "en": ROOT / "docs" / "en" / "26-spl.md",
        "marker_zh": "### 轮询必须自己带超时",
        "marker_en": "### Polling needs a deadline",
        "needle": "sample-26-timeout-poll.svg",
        "src_zh": "../assets/diagrams/sample-26-timeout-poll.svg",
        "src_en": "../../assets/diagrams/sample-26-timeout-poll.svg",
        "width": 760,
        "alt_zh": "SPL 轮询必须自带超时",
        "alt_en": "SPL polling must carry its own timeout",
        "cap_zh": "▲ 自绘。HAL 超时习惯不能带进 SPL 死循环。",
        "cap_en": "▲ Drawn for this book. HAL timeout habits do not travel into SPL forever-loops.",
    },
    # ---- ch27 ----
    {
        "zh": ROOT / "docs" / "27-网络与协议栈.md",
        "en": ROOT / "docs" / "en" / "27-network.md",
        "marker_zh": "### 1. RMII 最少要对清这些信号",
        "marker_en": "### RMII signals to reconcile",
        "needle": "sample-27-rmii-checklist.svg",
        "src_zh": "../assets/diagrams/sample-27-rmii-checklist.svg",
        "src_en": "../../assets/diagrams/sample-27-rmii-checklist.svg",
        "width": 760,
        "alt_zh": "RMII 最少信号核对清单",
        "alt_en": "Minimum RMII signal checklist",
        "cap_zh": "▲ 自绘。先对清线，再怪 lwIP。",
        "cap_en": "▲ Drawn for this book. Reconcile wires before blaming lwIP.",
    },
    {
        "zh": ROOT / "docs" / "27-网络与协议栈.md",
        "en": ROOT / "docs" / "en" / "27-network.md",
        "marker_zh": "## 从 link 到可用网络的启动状态机",
        "marker_en": "## Startup state machine: link is not online",
        "needle": "sample-27-link-dhcp-flow.svg",
        "src_zh": "../assets/animations/sample-27-link-dhcp-flow.svg",
        "src_en": "../../assets/animations/sample-27-link-dhcp-flow.svg",
        "width": 720,
        "alt_zh": "链路到可用 IP 的启动流程",
        "alt_en": "Link-to-usable-IP bring-up flow",
        "cap_zh": "▲ 自绘矢量动画（FA-002）。PHY → link → IP → ping。",
        "cap_en": "▲ Hand-drawn CSS animation (FA-002). PHY → link → IP → ping.",
    },
    {
        "zh": ROOT / "docs" / "27-网络与协议栈.md",
        "en": ROOT / "docs" / "en" / "27-network.md",
        "marker_zh": "## lwIP 三套 API 与线程边界",
        "marker_en": "## The three lwIP APIs and their thread boundaries",
        "needle": "sample-27-tcp-framing.svg",
        "src_zh": "../assets/diagrams/sample-27-tcp-framing.svg",
        "src_en": "../../assets/diagrams/sample-27-tcp-framing.svg",
        "width": 760,
        "alt_zh": "TCP 粘包与消息边界",
        "alt_en": "TCP framing and message edges",
        "cap_zh": "▲ 自绘。字节流≠消息；自己定帧。",
        "cap_en": "▲ Drawn for this book. A byte stream is not a message — frame it.",
    },
    # ---- ch28 ----
    {
        "zh": ROOT / "docs" / "28-嵌入式系统与RTOS生态.md",
        "en": ROOT / "docs" / "en" / "28-system-rtos.md",
        "marker_zh": "## 先把四个概念分开",
        "marker_en": "## Separate four concepts first",
        "needle": "sample-28-four-concepts.svg",
        "src_zh": "../assets/diagrams/sample-28-four-concepts.svg",
        "src_en": "../../assets/diagrams/sample-28-four-concepts.svg",
        "width": 760,
        "alt_zh": "裸机 / 前后台 / RTOS / Linux 四概念分界",
        "alt_en": "Bare-metal / foreground-background / RTOS / Linux boundaries",
        "cap_zh": "▲ 自绘。先分概念，再选内核名字。",
        "cap_en": "▲ Drawn for this book. Separate concepts before naming a kernel.",
    },
    {
        "zh": ROOT / "docs" / "28-嵌入式系统与RTOS生态.md",
        "en": ROOT / "docs" / "en" / "28-system-rtos.md",
        "marker_zh": "### 所有者任务：比“到处加互斥量”更容易证明",
        "marker_en": "### An owner task is easier to prove than scattered mutexes",
        "needle": "sample-28-isr-owner-flow.svg",
        "src_zh": "../assets/animations/sample-28-isr-owner-flow.svg",
        "src_en": "../../assets/animations/sample-28-isr-owner-flow.svg",
        "width": 720,
        "alt_zh": "ISR 投递、所有者任务写硬件",
        "alt_en": "ISR posts; owner task writes the device",
        "cap_zh": "▲ 自绘矢量动画（FA-002）。ISR 只投递，所有者才碰硬件。",
        "cap_en": "▲ Hand-drawn CSS animation (FA-002). ISR posts; owner alone touches hardware.",
    },
    {
        "zh": ROOT / "docs" / "28-嵌入式系统与RTOS生态.md",
        "en": ROOT / "docs" / "en" / "28-system-rtos.md",
        "marker_zh": "### 三种时间必须区分",
        "marker_en": "### Three different times",
        "needle": "sample-28-three-times.svg",
        "src_zh": "../assets/diagrams/sample-28-three-times.svg",
        "src_en": "../../assets/diagrams/sample-28-three-times.svg",
        "width": 760,
        "alt_zh": "周期、超时、截止点三种时间",
        "alt_en": "Period, timeout, and deadline vocabulary",
        "cap_zh": "▲ 自绘。实时性来自预算，不来自 RTOS 商标。",
        "cap_en": "▲ Drawn for this book. Real time is a budget, not a brand name.",
    },
    # ---- appendix F ----
    {
        "zh": ROOT / "stm32-book" / "book" / "F-开源地图.md",
        "en": ROOT / "stm32-book" / "book" / "en" / "F-oss-map.md",
        "marker_zh": "## 六个知识点：只有读源码才拿得到",
        "marker_en": "## Six facts you only get by reading the source",
        "needle": "sample-f-six-facts.svg",
        "src_zh": "../../assets/diagrams/sample-f-six-facts.svg",
        "src_en": "../../../assets/diagrams/sample-f-six-facts.svg",
        "width": 760,
        "alt_zh": "六个只有读源码才拿得到的知识点",
        "alt_en": "Six facts only source reading reveals",
        "cap_zh": "▲ 自绘。星标数替代不了这六条证据。",
        "cap_en": "▲ Drawn for this book. Star counts do not replace these six facts.",
    },
    {
        "zh": ROOT / "stm32-book" / "book" / "F-开源地图.md",
        "en": ROOT / "stm32-book" / "book" / "en" / "F-oss-map.md",
        "marker_zh": "## 仓库地图",
        "marker_en": "## Repository map",
        "needle": "sample-f-repo-lane-flow.svg",
        "src_zh": "../../assets/animations/sample-f-repo-lane-flow.svg",
        "src_en": "../../../assets/animations/sample-f-repo-lane-flow.svg",
        "width": 720,
        "alt_zh": "选一条仓库车道读到底",
        "alt_en": "Pick one repo lane and read it through",
        "cap_zh": "▲ 自绘矢量动画（FA-002）。选树 → 钉 SHA → 引用 → 实验卡。",
        "cap_en": "▲ Hand-drawn CSS animation (FA-002). pick → pin SHA → quote → lab card.",
    },
    {
        "zh": ROOT / "stm32-book" / "book" / "F-开源地图.md",
        "en": ROOT / "stm32-book" / "book" / "en" / "F-oss-map.md",
        "marker_zh": "## 社区：提问之前先做五件事",
        "marker_en": "## Community: five things before you ask",
        "needle": "sample-f-ask-before.svg",
        "src_zh": "../../assets/diagrams/sample-f-ask-before.svg",
        "src_en": "../../../assets/diagrams/sample-f-ask-before.svg",
        "width": 760,
        "alt_zh": "提问前五件事清单",
        "alt_en": "Five things before you ask the community",
        "cap_zh": "▲ 自绘。提问模板先于情绪发帖。",
        "cap_en": "▲ Drawn for this book. A question template before an emotional post.",
    },
]


def main() -> None:
    n = 0
    for e in EMBEDS:
        block_zh = _blk(e["src_zh"], e["width"], e["alt_zh"], e["cap_zh"])
        block_en = _blk(e["src_en"], e["width"], e["alt_en"], e["cap_en"])
        if _insert_after_heading(e["zh"], e["marker_zh"], e["needle"], block_zh):
            n += 1
        if _insert_after_heading(e["en"], e["marker_en"], e["needle"], block_en):
            n += 1
    print(f"embed inserts: {n}")


if __name__ == "__main__":
    main()
