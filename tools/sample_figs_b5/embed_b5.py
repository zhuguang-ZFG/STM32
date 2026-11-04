#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Embed B5 figures into zh/en chapters (idempotent)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

BLOCK = """
<p align=\"center\">
  <img src=\"{src}\" width=\"{width}\" alt=\"{alt}\">
  <br><sub>{caption}</sub>
</p>

"""

EMBEDS = [
    # ch18
    {
        "zh": ROOT / "docs" / "18-常见问题FAQ.md",
        "en": ROOT / "docs" / "en" / "18-faq.md",
        "marker_zh": "## 三、外设",
        "marker_en": "## 3. Peripherals",
        "needle": "sample-18-faq-compare.svg",
        "src_zh": "../assets/diagrams/sample-18-faq-compare.svg",
        "src_en": "../../assets/diagrams/sample-18-faq-compare.svg",
        "width": 760,
        "alt_zh": "编译链接、下载调试、外设、硬件、RTOS 五域各有第一探针，不要一次改五处配置",
        "alt_en": "Build/link, download/debug, peripherals, hardware, and RTOS each have one first probe — do not shotgun five config edits",
        "cap_zh": "▲ 自绘。FAQ 五域对照：每域只做第一探针，有证据再改一处。出处是 [RM0008 启动](#source-rm0008-boot) 和 [DS5319 NRST/SWD](#source-ds5319-nrst)。",
        "cap_en": "▲ Drawn for this book. Five FAQ domains, one first probe each. Sources: [RM0008 boot](#source-rm0008-boot) and [DS5319 NRST/SWD](#source-ds5319-nrst).",
    },
    # ch19
    {
        "zh": ROOT / "docs" / "19-项目实战合集.md",
        "en": ROOT / "docs" / "en" / "19-projects.md",
        "marker_zh": "## 动手实验（选题与推进）",
        "marker_en": "## Hands-on labs (picking a project and moving it forward)",
        "needle": "sample-19-milestone-triage.svg",
        "src_zh": "../assets/diagrams/sample-19-milestone-triage.svg",
        "src_en": "../../assets/diagrams/sample-19-milestone-triage.svg",
        "width": 760,
        "alt_zh": "范围太大、跳过里程碑、集成无证据：一槽一位、每槽可演示、合入前要有通过门",
        "alt_en": "Scope creep, skipped milestones, integration without evidence: one slot, one demo, a gate before merge",
        "cap_zh": "▲ 自绘。项目三岔口：贪多 / 跳步 / 无证据。出处是 [配套例程](#source-project-examples) 与本章验收门图。",
        "cap_en": "▲ Drawn for this book. Three project branches: scope / skipped gate / no evidence. Sources: [project examples](#source-project-examples) and this chapter's acceptance gates.",
    },
    # ch20 anim
    {
        "zh": ROOT / "docs" / "20-学习资源与工具链.md",
        "en": ROOT / "docs" / "en" / "20-resources.md",
        "marker_zh": "## 遇到问题时去哪找证据",
        "marker_en": "## Where to look for evidence",
        "needle": "sample-20-lookup-flow.svg",
        "src_zh": "../assets/animations/sample-20-lookup-flow.svg",
        "src_en": "../../assets/animations/sample-20-lookup-flow.svg",
        "width": 760,
        "alt_zh": "订货号对上 DS、RM、PM、AN/UM 的查找数据流",
        "alt_en": "Lookup flow from orderable part number through DS, RM, PM, and AN/UM",
        "cap_zh": "▲ 动画：订货号 → DS → RM → PM → AN/UM（作者自绘矢量动画，非实拍）。出处是本章手册地图与 [项目致谢](#source-project-credits)。",
        "cap_en": "▲ Animation: orderable PN → DS → RM → PM → AN/UM (drawn for this book, not a photo). Sources: this chapter's manual map and [project credits](#source-project-credits).",
        "after_marker": False,  # insert BEFORE marker content starts - actually insert right AFTER the heading line
        "place": "after_heading",
    },
    # ch20 triage
    {
        "zh": ROOT / "docs" / "20-学习资源与工具链.md",
        "en": ROOT / "docs" / "en" / "20-resources.md",
        "marker_zh": "## 常见坑与排查",
        "marker_en": "## Common traps and how to check them",
        "needle": "sample-20-evidence-triage.svg",
        "src_zh": "../assets/diagrams/sample-20-evidence-triage.svg",
        "src_en": "../../assets/diagrams/sample-20-evidence-triage.svg",
        "width": 760,
        "alt_zh": "手册找错、仪器越级、固件栈选错：先 DS/RM/PM 对号，再选证据阶，最后才动栈",
        "alt_en": "Wrong manual, instrument leapfrog, or wrong firmware stack: match DS/RM/PM first, then the evidence ladder, then the stack",
        "cap_zh": "▲ 自绘。证据三岔口。出处是 [手册选择地图](#source-project-credits) 与 [stlink 工具集](#source-stlink-tools)。",
        "cap_en": "▲ Drawn for this book. Evidence triage. Sources: [project credits](#source-project-credits) and [stlink tools](#source-stlink-tools).",
    },
    # ch21 compare
    {
        "zh": ROOT / "docs" / "21-原理图与实物图鉴.md",
        "en": ROOT / "docs" / "en" / "21-board-maps.md",
        "marker_zh": "## 核心原理",
        "marker_en": "## Core ideas",
        "needle": "sample-21-board-compare.svg",
        "src_zh": "../assets/diagrams/sample-21-board-compare.svg",
        "src_en": "../../assets/diagrams/sample-21-board-compare.svg",
        "width": 760,
        "alt_zh": "BluePill F103、BlackPill F411、Nucleo-F411RE：封装、调试器、5V 与 USB 路径对照",
        "alt_en": "BluePill F103, BlackPill F411, Nucleo-F411RE: package, debugger, 5V, and USB path compared",
        "cap_zh": "▲ 自绘对照（非实拍）。三板五问。出处是 [DS5319](#source-ds5319) 与 [项目致谢](#source-project-credits)。",
        "cap_en": "▲ Drawn comparison (not a photo). Three boards, five questions. Sources: [DS5319](#source-ds5319) and [project credits](#source-project-credits).",
        "place": "after_heading",
    },
    # ch21 anim
    {
        "zh": ROOT / "docs" / "21-原理图与实物图鉴.md",
        "en": ROOT / "docs" / "en" / "21-board-maps.md",
        "marker_zh": "## 硬件与接线",
        "marker_en": "## Hardware and wiring",
        "needle": "sample-21-power-swd.svg",
        "src_zh": "../assets/animations/sample-21-power-swd.svg",
        "src_en": "../../assets/animations/sample-21-power-swd.svg",
        "width": 760,
        "alt_zh": "上电到 SWD：3V3 → NRST → BOOT0=0 → SWDIO/SWCLK",
        "alt_en": "Power-up to SWD: 3V3 → NRST → BOOT0=0 → SWDIO/SWCLK",
        "cap_zh": "▲ 动画：供电→复位→BOOT0→SWD（作者自绘矢量动画，非实拍）。出处是 [DS5319](#source-ds5319) 与 [项目致谢](#source-project-credits)。",
        "cap_en": "▲ Animation: power → reset → BOOT0 → SWD (drawn for this book, not a photo). Sources: [DS5319](#source-ds5319) and [project credits](#source-project-credits).",
    },
    # ch22 triage
    {
        "zh": ROOT / "docs" / "22-仿真实验Wokwi与Renode.md",
        "en": ROOT / "docs" / "en" / "22-simulation-wokwi-renode.md",
        "marker_zh": "## 仿真替不了的事",
        "marker_en": "## What simulation will not do for you",
        "needle": "sample-22-sim-triage.svg",
        "src_zh": "../assets/diagrams/sample-22-sim-triage.svg",
        "src_en": "../../assets/diagrams/sample-22-sim-triage.svg",
        "width": 760,
        "alt_zh": "模型缺口、主机环境、板级物理：仿真能过不等于板上能过",
        "alt_en": "Model gap, host environment, board-only physics: a green sim is not a green board",
        "cap_zh": "▲ 自绘。仿真三岔口。出处是 [Wokwi Blue Pill 板定义](#source-wokwi-bluepill) 和 [Renode STM32 文档](#source-renode-stm32)。",
        "cap_en": "▲ Drawn for this book. Simulation triage. Sources: [Wokwi Blue Pill board](#source-wokwi-bluepill) and [Renode STM32 docs](#source-renode-stm32).",
    },
]


def insert(path: Path, marker: str, needle: str, block: str, place: str = "before_marker") -> bool:
    text = path.read_text(encoding="utf-8")
    if needle in text:
        print(f"skip {path.name}: already has {needle}")
        return False
    if marker not in text:
        raise SystemExit(f"marker missing in {path}: {marker}")
    if place == "after_heading":
        idx = text.index(marker)
        # end of heading line
        nl = text.index("\n", idx)
        # skip one blank line if present
        insert_at = nl + 1
        if insert_at < len(text) and text[insert_at] == "\n":
            insert_at += 1
        new = text[:insert_at] + "\n" + block + text[insert_at:]
    else:
        new = text.replace(marker, block + marker, 1)
    path.write_text(new, encoding="utf-8")
    print(f"embed {needle} -> {path.name}")
    return True


def main() -> None:
    for item in EMBEDS:
        place = item.get("place", "before_marker")
        zh_block = BLOCK.format(
            src=item["src_zh"], width=item["width"], alt=item["alt_zh"], caption=item["cap_zh"]
        )
        en_block = BLOCK.format(
            src=item["src_en"], width=item["width"], alt=item["alt_en"], caption=item["cap_en"]
        )
        insert(item["zh"], item["marker_zh"], item["needle"], zh_block, place)
        insert(item["en"], item["marker_en"], item["needle"], en_block, place)


if __name__ == "__main__":
    main()
