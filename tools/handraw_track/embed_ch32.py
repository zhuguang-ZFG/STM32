# -*- coding: utf-8 -*-
"""Embed ch32 handraw knowledge-track PNGs (ZH+EN)."""
from embed import embed_after_text

ZH = "docs/32-直流电机速度闭环.md"
EN = "docs/en/32-dc-motor-speed-closed-loop.md"

specs = [
    (ZH, "### PI 离散式与单位",
     "ch32-pi-step.png",
     "Handraw：PI 离散式与一步手算（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。e/I_try/u_try/clamp/条件积分五步；手算 e=−10 rpm→u_try=−20.05‰（负输出=反向驱动）；Kp=2.0、Ki=0.5、i_limit=500‰、duty_limit=900‰；不是实拍。"),
    (ZH, "### 状态机与事件优先级",
     "ch32-state-machine.png",
     "Handraw：状态机与事件优先级（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。DISABLED→ARMED→RUN/REVERSING→FAULT；故障（F01~F06）> STOP > 换向；故障锁存不人工 CLEAR 不自恢复；控制节拍 10 ms 与串口任务分离；不是实拍。"),
    (ZH, "### 调参步骤（每步带回退条件）",
     "ch32-tuning-ladder.png",
     "Handraw：调参阶梯与回退条件（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。六步阶梯：极性/CPR→开环扫速→升 Kp→加 Ki→饱和恢复→重做阶跃扰动反转，每步带通过判据与回退；换装置从第 1 步重做；不是实拍。"),
    (EN, "### The discrete PI and its units",
     "ch32-pi-step.png",
     "Handraw: discrete PI and one hand-computed tick (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). Five steps: e / I_try / u_try / clamp / conditional integration; hand-computed e=−10 rpm → u_try=−20.05‰ (negative output = reverse drive); Kp=2.0, Ki=0.5, i_limit=500‰, duty_limit=900‰; not a photo."),
    (EN, "### State machine and event priority",
     "ch32-state-machine.png",
     "Handraw: state machine and event priority (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). DISABLED→ARMED→RUN/REVERSING→FAULT; faults (F01–F06) outrank STOP, which outranks reversal; faults latch until manual CLEAR; the 10 ms control tick is isolated from the serial task; not a photo."),
    (EN, "### Tuning procedure (with a rollback condition per step)",
     "ch32-tuning-ladder.png",
     "Handraw: tuning ladder with rollback conditions (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). Six-step ladder — polarity/CPR, open-loop sweep, raise Kp, add Ki, saturation recovery, redo step/disturbance/reversal — each with a pass criterion and a rollback; change the rig and redo from step 1; not a photo."),
    ('docs/32-直流电机速度闭环.md',
     '## 失败分支与最短排查',
     'ch32-loop-fault-triage.png',
     'Handraw：闭环异常分流（原理示意）',
     '▲ 知识轨（Handraw · 原理示意/非实拍）。闭环异常先分流：振荡降 Kp、不响应查 FAULT/限幅、超调降 Ki/ramp；换装置从调参第 1 步重做；不是实拍。'),
    ('docs/en/32-dc-motor-speed-closed-loop.md',
     '## Failure branches and shortest diagnosis',
     'ch32-loop-fault-triage.png',
     'Handraw: closed-loop fault split (原理示意)',
     '▲ Knowledge track (Handraw · 原理示意 / not a photo). Split first: oscillation → cut Kp, no response → FAULT/limits, overshoot → Ki/ramp; retune from step 1 on any rig change; not a photo.'),
]

bad = 0
for doc, anchor, png, alt, caption in specs:
    if not embed_after_text(doc, anchor, png, alt, caption):
        bad += 1
if bad:
    raise SystemExit(f"{bad} embed(s) failed")
