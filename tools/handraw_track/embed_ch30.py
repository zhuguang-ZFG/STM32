# -*- coding: utf-8 -*-
"""Embed ch30 handraw knowledge-track PNGs (ZH+EN)."""
from embed import embed_after_text

ZH = "docs/30-直流电机开环调速.md"
EN = "docs/en/30-dc-motor-open-loop-speed.md"

specs = [
    (ZH, "### 可复算的 PWM 配置",
     "ch30-pwm-math.png",
     "Handraw：可复算的 PWM 配置与端点（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。72 MHz/PSC=0/ARR=3599→20 kHz；CCR=duty‰×3600/1000；100% 须 CCR>ARR（=ARR 差一格 99.97%）；不是实拍。"),
    (ZH, "### 带符号占空比：方向与幅值分离",
     "ch30-signed-duty.png",
     "Handraw：带符号占空比与斜坡（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。符号=方向、绝对值=幅值，映射只有 motor_bridge.c 一处；±50‰/10 ms 斜坡；duty_limit 900‰；不是实拍。"),
    (ZH, "### 斜坡与停止策略",
     "ch30-stop-triage.png",
     "Handraw：停止语义选择与 REVERSING（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。PWM=0 两映射（滑行/短接制动）+待机；换向必须走 REVERSING（降 0→等停稳 |rpm|≤5→保持 100 ms）；命令流断 500 ms（F01）锁存停机；不是实拍。"),
    (EN, "### A PWM configuration you can recompute",
     "ch30-pwm-math.png",
     "Handraw: recomputable PWM setup and endpoints (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). 72 MHz/PSC=0/ARR=3599 → 20 kHz; CCR = duty‰×3600/1000; 100% requires CCR>ARR (=ARR leaves one tick, 99.97%); not a photo."),
    (EN, "### Signed duty: direction and magnitude separated",
     "ch30-signed-duty.png",
     "Handraw: signed duty and ramp (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). Sign = direction, absolute value = magnitude, one mapping in motor_bridge.c; ramp ±50‰ per 10 ms; duty_limit 900‰; not a photo."),
    (EN, "### Ramps and stop policy",
     "ch30-stop-triage.png",
     "Handraw: stop semantics and REVERSING (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). Two PWM=0 mappings (coast/short brake) plus standby; reversal must walk REVERSING (to 0 → standstill |rpm|≤5 → hold 100 ms); 500 ms silent command stream (F01) latches a stop; not a photo."),
    ('docs/30-直流电机开环调速.md',
     '## 失败分支与最短排查',
     'ch30-no-spin-triage.png',
     'Handraw：电机不转的排查序（原理示意）',
     '▲ 知识轨（Handraw · 原理示意/非实拍）。不转排查：状态机→斜坡→CCR 表→电流档；遥测帧先看状态位与 rpm 原始计数；不是实拍。'),
    ('docs/en/30-dc-motor-open-loop-speed.md',
     '## Failure branches and shortest diagnosis',
     'ch30-no-spin-triage.png',
     'Handraw: motor-wont-spin triage order (原理示意)',
     '▲ Knowledge track (Handraw · 原理示意 / not a photo). Triage: state machine → ramp → CCR table → current tier; telemetry frame first, hardware last; not a photo.'),
]

bad = 0
for doc, anchor, png, alt, caption in specs:
    if not embed_after_text(doc, anchor, png, alt, caption):
        bad += 1
if bad:
    raise SystemExit(f"{bad} embed(s) failed")
