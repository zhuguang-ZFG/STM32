#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Embed B6 figures into zh/en chapters and appendix F (idempotent)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

BLOCK = """
<p align="center">
  <img src="{src}" width="{width}" alt="{alt}">
  <br><sub>{caption}</sub>
</p>

"""

EMBEDS = [
    {
        "zh": ROOT / "docs" / "23-STM32G0引脚.md",
        "en": ROOT / "docs" / "en" / "23-stm32g0-pins.md",
        "marker_zh": "## BOOT0 与 SWCLK 共脚：先判定启动来源",
        "marker_en": "## BOOT0 shares SWCLK: determine the boot source first",
        "needle": "sample-23-boot-latch.svg",
        "src_zh": "../assets/animations/sample-23-boot-latch.svg",
        "src_en": "../../assets/animations/sample-23-boot-latch.svg",
        "width": 760,
        "alt_zh": "G0 BOOT0/SWCLK 共脚在第四个 SYSCLK 上升沿锁存启动源",
        "alt_en": "G0 samples the shared BOOT0/SWCLK pin on the fourth SYSCLK rising edge",
        "cap_zh": "▲ 动画：四个 SYSCLK 上升沿后锁存启动源（作者自绘矢量动画，非实拍）。出处是 [DS12232](#source-ds12232)、[RM0444](#source-rm0444) 与 [AN2606](#source-an2606)；开源对照见 [配套例程](#source-project-examples)。",
        "cap_en": "▲ Animation: boot source latches after four SYSCLK rising edges (drawn for this book, not a photo). Sources: [DS12232](#source-ds12232), [RM0444](#source-rm0444), [AN2606](#source-an2606); OSS compare: [project examples](#source-project-examples).",
        "place": "after_heading",
    },
    {
        "zh": ROOT / "docs" / "23-STM32G0引脚.md",
        "en": ROOT / "docs" / "en" / "23-stm32g0-pins.md",
        "marker_zh": "## 从 F1 抄代码时最容易摔的几处",
        "marker_en": "## Common ways an F1 port falls over",
        "needle": "sample-23-f1-g0-compare.svg",
        "src_zh": "../assets/diagrams/sample-23-f1-g0-compare.svg",
        "src_en": "../../assets/diagrams/sample-23-f1-g0-compare.svg",
        "width": 760,
        "alt_zh": "F1 迁 G0 五处不能照抄：脚序、BOOT/SWD、选项字节、复用表、时钟上限",
        "alt_en": "Five F1→G0 traps: pinout, BOOT/SWD, option bytes, AF tables, clock ceiling",
        "cap_zh": "▲ 自绘。F1→G0 迁移五问对照。出处是 [DS12232](#source-ds12232) / [RM0444](#source-rm0444)；例程结构仅对照 [配套例程](#source-project-examples)。",
        "cap_en": "▲ Drawn for this book. Five F1→G0 migration checks. Sources: [DS12232](#source-ds12232) / [RM0444](#source-rm0444); structure only: [project examples](#source-project-examples).",
    },
    {
        "zh": ROOT / "docs" / "24-STM32L4引脚.md",
        "en": ROOT / "docs" / "en" / "24-stm32l4-pins.md",
        "marker_zh": "## 低功耗模式与状态保持（RM0351）",
        "marker_en": "## Low-power modes and retained state (RM0351)",
        "needle": "sample-24-mode-compare.svg",
        "src_zh": "../assets/diagrams/sample-24-mode-compare.svg",
        "src_en": "../../assets/diagrams/sample-24-mode-compare.svg",
        "width": 760,
        "alt_zh": "L4 Sleep/Stop1/Stop2/Standby 四档保留状态与唤醒对照",
        "alt_en": "L4 Sleep/Stop1/Stop2/Standby retained-state and wake compare",
        "cap_zh": "▲ 自绘。L4 低功耗四档对照。出处是 [RM0351](#source-rm0351)、[DS10198](#source-ds10198)、[AN4746](#source-an4746)；Cube 示例仅对照 [stm32cube-l4-stop2](#source-stm32cube-l4-stop2)。",
        "cap_en": "▲ Drawn for this book. Four L4 low-power modes. Sources: [RM0351](#source-rm0351), [DS10198](#source-ds10198), [AN4746](#source-an4746); OSS compare: [stm32cube-l4-stop2](#source-stm32cube-l4-stop2).",
        "place": "after_heading",
    },
    {
        "zh": ROOT / "docs" / "24-STM32L4引脚.md",
        "en": ROOT / "docs" / "en" / "24-stm32l4-pins.md",
        "marker_zh": "## Stop 2 进入、唤醒与时钟恢复闭环",
        "marker_en": "## Stop 2: entry, wake evidence, and clock recovery",
        "needle": "sample-24-wake-triage.svg",
        "place": "after_heading",
        "src_zh": "../assets/diagrams/sample-24-wake-triage.svg",
        "src_en": "../../assets/diagrams/sample-24-wake-triage.svg",
        "width": 760,
        "alt_zh": "Stop2 从未醒来、反复醒来、醒后无业务三岔口排错",
        "alt_en": "Stop2 triage: never woke, woke too often, woke without service",
        "cap_zh": "▲ 自绘。Stop2 唤醒三岔口。出处是 [RM0351](#source-rm0351) 与 [stm32l4-hal-rtc](#source-stm32l4-hal-rtc) 捕获模式对照。",
        "cap_en": "▲ Drawn for this book. Stop2 wake triage. Sources: [RM0351](#source-rm0351) and [stm32l4-hal-rtc](#source-stm32l4-hal-rtc) capture pattern.",
    },
    {
        "zh": ROOT / "docs" / "25-STM32H7引脚.md",
        "en": ROOT / "docs" / "en" / "25-stm32h7-pins.md",
        "marker_zh": "## 从 F4 迁过来",
        "marker_en": "## Moving a design across from F4",
        "needle": "sample-25-migrate-triage.svg",
        "src_zh": "../assets/diagrams/sample-25-migrate-triage.svg",
        "src_en": "../../assets/diagrams/sample-25-migrate-triage.svg",
        "width": 760,
        "alt_zh": "F4 迁 H7：供电、revision、Cache/DMA、时钟链四步排错",
        "alt_en": "F4→H7 triage: supply, revision, cache/DMA, clock evidence",
        "cap_zh": "▲ 自绘。H7 迁移四步排错。出处是 [DS12110](#source-ds12110)、[RM0433](#source-rm0433)、[ES0392](#source-es0392)；Cube 时钟示例仅对照 [stm32cube-h7-clock](#source-stm32cube-h7-clock)。",
        "cap_en": "▲ Drawn for this book. Four-step H7 migration triage. Sources: [DS12110](#source-ds12110), [RM0433](#source-rm0433), [ES0392](#source-es0392); OSS: [stm32cube-h7-clock](#source-stm32cube-h7-clock).",
    },
    {
        "zh": ROOT / "docs" / "26-STM32F10x标准外设库SPL.md",
        "en": ROOT / "docs" / "en" / "26-spl.md",
        "marker_zh": "## 5. HAL、SPL 与寄存器怎样对上",
        "marker_en": "## 5. HAL, SPL, and the final register boundary",
        "needle": "sample-26-spl-hal-compare.svg",
        "src_zh": "../assets/diagrams/sample-26-spl-hal-compare.svg",
        "src_en": "../../assets/diagrams/sample-26-spl-hal-compare.svg",
        "width": 760,
        "alt_zh": "SPL 与 HAL/LL 在版本、初始化、中断、DMA 与迁移策略上的对照",
        "alt_en": "SPL versus HAL/LL on version, init, IRQ, DMA, and migration",
        "cap_zh": "▲ 自绘。SPL↔HAL 对照。出处是 [STSW-STM32054](#source-stsw-stm32054)、[RM0008](#source-rm0008)；目录核对仅用 [spl-f1-mirror](#source-spl-f1-mirror)。",
        "cap_en": "▲ Drawn for this book. SPL↔HAL compare. Sources: [STSW-STM32054](#source-stsw-stm32054), [RM0008](#source-rm0008); tree check only: [spl-f1-mirror](#source-spl-f1-mirror).",
    },
    {
        "zh": ROOT / "docs" / "27-网络与协议栈.md",
        "en": ROOT / "docs" / "en" / "27-network.md",
        "marker_zh": "## 分层排错与 Wireshark 证据",
        "marker_en": "## Layered diagnosis and PCAP evidence",
        "needle": "sample-27-link-triage.svg",
        "src_zh": "../assets/diagrams/sample-27-link-triage.svg",
        "src_en": "../../assets/diagrams/sample-27-link-triage.svg",
        "width": 760,
        "alt_zh": "网络分层排错：链路、ping、TCP、应用证据不能互相代替",
        "alt_en": "Layered network triage: link, ping, TCP, and app evidence are not interchangeable",
        "cap_zh": "▲ 自绘。联网分层排错阶梯。出处是 [RM0433](#source-rm0433)、[AN4839](#source-an4839)；开源对照 [stm32cube-h7-lwip](#source-stm32cube-h7-lwip) 与 [lwip-pitfalls](#source-lwip-pitfalls)。",
        "cap_en": "▲ Drawn for this book. Layered network triage. Sources: [RM0433](#source-rm0433), [AN4839](#source-an4839); OSS: [stm32cube-h7-lwip](#source-stm32cube-h7-lwip), [lwip-pitfalls](#source-lwip-pitfalls).",
    },
    {
        "zh": ROOT / "docs" / "28-嵌入式系统与RTOS生态.md",
        "en": ROOT / "docs" / "en" / "28-system-rtos.md",
        "marker_zh": "## 什么时候选哪一种",
        "marker_en": "## When to choose which system",
        "needle": "sample-28-os-compare.svg",
        "src_zh": "../assets/diagrams/sample-28-os-compare.svg",
        "src_en": "../../assets/diagrams/sample-28-os-compare.svg",
        "width": 760,
        "alt_zh": "FreeRTOS、RT-Thread、Zephyr、CMSIS-RTOS2 选型对照",
        "alt_en": "FreeRTOS, RT-Thread, Zephyr, and CMSIS-RTOS2 selection compare",
        "cap_zh": "▲ 自绘。四系统选型对照。出处是 [FreeRTOS 11.3.2](#source-freertos-1132)、[RT-Thread 5.3.0](#source-rtthread-530)、[Zephyr 4.4.2](#source-zephyr-442)、[CMSIS 6.4.0](#source-cmsis-640)。",
        "cap_en": "▲ Drawn for this book. Four-OS selection compare. Sources: [FreeRTOS 11.3.2](#source-freertos-1132), [RT-Thread 5.3.0](#source-rtthread-530), [Zephyr 4.4.2](#source-zephyr-442), [CMSIS 6.4.0](#source-cmsis-640).",
        "place": "after_heading",
    },
    {
        "zh": ROOT / "docs" / "28-嵌入式系统与RTOS生态.md",
        "en": ROOT / "docs" / "en" / "28-system-rtos.md",
        "marker_zh": "### 所有者任务：比“到处加互斥量”更容易证明",
        "marker_en": "### An owner task is easier to prove than scattered mutexes",
        "needle": "sample-28-owner-flow.svg",
        "src_zh": "../assets/animations/sample-28-owner-flow.svg",
        "src_en": "../../assets/animations/sample-28-owner-flow.svg",
        "width": 760,
        "alt_zh": "IRQ 投递、所有者消费、监督者喂狗的所有者任务数据流",
        "alt_en": "Owner-task flow: IRQ posts, owner consumes, supervisor feeds the watchdog",
        "cap_zh": "▲ 动画：IRQ→队列→所有者→执行器→监督者（作者自绘矢量动画，非实拍）。出处见本章 FreeRTOS/RT-Thread/Zephyr 版本钉死说明。",
        "cap_en": "▲ Animation: IRQ→queue→owner→actuator→supervisor (drawn for this book, not a photo). Sources: pinned FreeRTOS/RT-Thread/Zephyr tags in this chapter.",
        "place": "after_heading",
    },
    {
        "zh": ROOT / "docs" / "28-嵌入式系统与RTOS生态.md",
        "en": ROOT / "docs" / "en" / "28-system-rtos.md",
        "marker_zh": "## 常见失败模式",
        "marker_en": "## Common failure modes",
        "needle": "sample-28-fault-triage.svg",
        "src_zh": "../assets/diagrams/sample-28-fault-triage.svg",
        "src_en": "../../assets/diagrams/sample-28-fault-triage.svg",
        "width": 760,
        "alt_zh": "队列满、任务冻结、驱动超时三岔口与监督者规则",
        "alt_en": "Queue-full, task-frozen, and driver-timeout triage with supervisor rules",
        "cap_zh": "▲ 自绘。系统故障三岔口。出处是本章故障注入实验与 [FreeRTOS 11.3.2](#source-freertos-1132) 等开源 tag。",
        "cap_en": "▲ Drawn for this book. System-fault triage. Sources: this chapter's fault-injection labs and pinned OSS tags such as [FreeRTOS 11.3.2](#source-freertos-1132).",
    },
    {
        "zh": ROOT / "stm32-book" / "book" / "F-开源地图.md",
        "en": None,
        "marker_zh": "## 仓库地图",
        "marker_en": None,
        "needle": "sample-f-oss-map.svg",
        "src_zh": "../../assets/diagrams/sample-f-oss-map.svg",
        "src_en": None,
        "width": 760,
        "alt_zh": "按证据层组织的开源仓库地图：Cube、CMSIS、libopencm3、FreeRTOS、RT-Thread、Zephyr",
        "alt_en": "",
        "cap_zh": "▲ 自绘。开源证据层地图：先问要哪一份 `.h`/函数，再谈星标。许可边界见各仓库 `LICENSE`；官方 RM/DS 冲突时以手册为准。",
        "cap_en": "",
        "place": "after_heading",
    },
]


def _insert(path: Path, marker: str, needle: str, block: str, place: str) -> bool:
    text = path.read_text(encoding="utf-8")
    if needle in text:
        print("skip", path.name, needle)
        return False
    if marker not in text:
        raise SystemExit(f"marker missing in {path}: {marker!r}")
    if place == "after_heading":
        idx = text.find(marker)
        end = text.find("\n", idx)
        if end < 0:
            end = len(text)
        new = text[: end + 1] + "\n" + block + text[end + 1 :]
    else:
        # insert immediately before marker
        idx = text.find(marker)
        new = text[:idx] + block + text[idx:]
    path.write_text(new, encoding="utf-8")
    print("embed", path.name, needle)
    return True


def main() -> None:
    n = 0
    for item in EMBEDS:
        place = item.get("place", "before_marker")
        block_zh = BLOCK.format(
            src=item["src_zh"], width=item["width"], alt=item["alt_zh"], caption=item["cap_zh"]
        )
        if _insert(item["zh"], item["marker_zh"], item["needle"], block_zh, place):
            n += 1
        if item.get("en") and item.get("marker_en") and item.get("src_en"):
            block_en = BLOCK.format(
                src=item["src_en"], width=item["width"], alt=item["alt_en"], caption=item["cap_en"]
            )
            if _insert(item["en"], item["marker_en"], item["needle"], block_en, place):
                n += 1
    print(f"done embeds touched={n}")


if __name__ == "__main__":
    main()
