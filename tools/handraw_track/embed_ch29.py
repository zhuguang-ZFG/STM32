# -*- coding: utf-8 -*-
"""Embed ch29 handraw knowledge-track PNGs (ZH+EN)."""
from embed import embed_after_text

ZH = "docs/29-电机驱动与供电.md"
EN = "docs/en/29-motor-drive-and-power.md"

specs = [
    (ZH, "## 核心机制：驱动桥在五个状态之间切换",
     "ch29-five-states.png",
     "Handraw：驱动桥五种状态与信号组合（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。PWM/AIN1/AIN2/STBY 组合出待机/滑行/短接制动/正转/反转五态（TB6612 p.4 逐行核验）；STBY=L 是默认安全态；方向有效时 PWM=L 是制动不是滑行；不是实拍。"),
    (ZH, "### 逻辑电源与电机电源是两回事",
     "ch29-two-supplies.png",
     "Handraw：逻辑 Vcc 与电机 VM 两路电源（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。Vcc 2.7–5.5 V（冻结 3.3 V）与 VM 4.5–12 V（冻结 6–12 V）分两路，GND 必须共地；VIH ≥ 0.7×Vcc、PWM 上限 100 kHz；不是实拍。"),
    (ZH, "### 电流三档：别把最大额定当连续能力",
     "ch29-current-tiers.png",
     "Handraw：电流三档与采购余量（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。连续 ≤1.0 A/通道才是预算依据，1.2 A 绝对最大与 3.2 A 脉冲档不得当连续用；堵转 ≤0.8 A 目标留 20% 余量；模块散热是 BLK-P0-4 实测项；不是实拍。"),
    (EN, "## How the drive bridge switches among five states",
     "ch29-five-states.png",
     "Handraw: five bridge states from four signal lines (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). PWM/AIN1/AIN2/STBY compose standby/coast/short-brake/CW/CCW (TB6612 p.4, row-by-row); STBY=L is the default safe state; PWM=L with a valid direction is brake, not coast; not a photo."),
    (EN, "### Logic supply and motor supply are two different things",
     "ch29-two-supplies.png",
     "Handraw: logic Vcc vs motor VM rails (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). Vcc 2.7–5.5 V (frozen 3.3 V) and VM 4.5–12 V (frozen 6–12 V) are separate rails sharing one ground; VIH ≥ 0.7×Vcc, PWM ceiling 100 kHz; not a photo."),
    (EN, "### Three current ratings: never read the maximum as continuous capability",
     "ch29-current-tiers.png",
     "Handraw: three current tiers and purchase margin (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). Only the ≤1.0 A/channel operating tier budgets continuous run; 1.2 A absolute maximum and 3.2 A pulse tier are not continuous bases; stall ≤0.8 A target keeps 20% margin; module dissipation is the BLK-P0-4 measurement item; not a photo."),
    ('docs/29-电机驱动与供电.md',
     '## 失败分支与最短排查',
     'ch29-fault-triage.png',
     'Handraw：驱动桥不切换的排查序（原理示意）',
     '▲ 知识轨（Handraw · 原理示意/非实拍）。排查序固定：VM→STBY→AIN 逻辑→PWM 示波器，从外到内不回溯；电流档越界先降负载；不是实拍。'),
    ('docs/en/29-motor-drive-and-power.md',
     '## Failure branches and shortest diagnosis',
     'ch29-fault-triage.png',
     'Handraw: bridge fault triage order (原理示意)',
     '▲ Knowledge track (Handraw · 原理示意 / not a photo). Fixed order: VM → STBY → AIN logic → PWM scope, outside-in without backtracking; current-tier violation means unloading first; not a photo.'),
]

bad = 0
for doc, anchor, png, alt, caption in specs:
    if not embed_after_text(doc, anchor, png, alt, caption):
        bad += 1
if bad:
    raise SystemExit(f"{bad} embed(s) failed")
