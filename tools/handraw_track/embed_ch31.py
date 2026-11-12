# -*- coding: utf-8 -*-
"""Embed ch31 handraw knowledge-track PNGs (ZH+EN)."""
from embed import embed_after_text

ZH = "docs/31-编码器与转速测量.md"
EN = "docs/en/31-encoder-and-rpm-measurement.md"

specs = [
    (ZH, "### 四倍频与方向",
     "ch31-quadrature.png",
     "Handraw：四倍频计数与方向判定（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。TIM2 编码器模式 3（SMS=011）两路上下沿都计数 → 4×PPR；冻结示例 110×4=440 CPR；A 领先 B 加计数；不是实拍。"),
    (ZH, "### 定窗计数公式",
     "ch31-rpm-formula.png",
     "Handraw：定窗计数公式与量化下限（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。rpm=60×Δ/(CPR×Δt)；Δ=11/CPR=440/10 ms→150 rpm 回验一致；量化下限 60/(440×0.01)≈13.6 rpm，低速逐格跳是测量特性；不是实拍。"),
    (ZH, "### 回绕与最大可信速度",
     "ch31-wrap-triage.png",
     "Handraw：16 位回绕消歧与断线分辨（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。65530 与 100 的有符号增量=+6 不是 −65430；判据 |Δ|<32768/2；零计数不能单独证明断线，区分靠 A/B 波形；不是实拍。"),
    (EN, "### 4x counting and direction",
     "ch31-quadrature.png",
     "Handraw: 4x counting and direction (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). TIM2 encoder mode 3 (SMS=011) counts both edges on both channels → 4×PPR; frozen example 110×4 = 440 CPR; A leading B counts up; not a photo."),
    (EN, "### The fixed-window formula",
     "ch31-rpm-formula.png",
     "Handraw: fixed-window formula and quantization floor (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). rpm = 60×Δ/(CPR×Δt); Δ=11, CPR=440, 10 ms → 150 rpm, checked backwards; quantization floor 60/(440×0.01) ≈ 13.6 rpm, stepwise low-speed readings are a measurement property; not a photo."),
    (EN, "### Wraparound and the maximum trustworthy speed",
     "ch31-wrap-triage.png",
     "Handraw: 16-bit wrap disambiguation vs disconnect (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). Signed delta of 65530 and 100 is +6, not −65430; rule |Δ|<32768/2; zero counts alone cannot prove a disconnect — distinguish by A/B waveforms; not a photo."),
]

bad = 0
for doc, anchor, png, alt, caption in specs:
    if not embed_after_text(doc, anchor, png, alt, caption):
        bad += 1
if bad:
    raise SystemExit(f"{bad} embed(s) failed")
