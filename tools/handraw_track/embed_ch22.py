# -*- coding: utf-8 -*-
"""Embed ch22 handraw knowledge-track PNGs (ZH+EN)."""
from embed import run

ZH = "docs/22-仿真实验Wokwi与Renode.md"
EN = "docs/en/22-simulation-wokwi-renode.md"

run([
    (ZH, "simulator-comparison.svg", "ch22-sim-compare.png",
     "Handraw：Wokwi/Renode/真板三列对照（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。模型复现逻辑后再上真板测量；仿真绿灯不能覆盖实测；不是实拍。"),
    (ZH, "sample-22-wokwi-scope.svg", "ch22-wokwi-scope.png",
     "Handraw：Wokwi 擅长与边界（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。逻辑/LED 适合；ADC/USB/晶振余量必须上桌；孪生验收在 BluePill；不是实拍。"),
    (ZH, "sample-22-renode-path.svg", "ch22-renode-path.png",
     "Handraw：Renode 平台→ELF→UART（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。四步脚本路径；golden string 与真板一致；绿灯≠HSE 焊接；不是实拍。"),
    (ZH, "sample-22-sim-triage.svg", "ch22-sim-triage.png",
     "Handraw：仿真三岔口模型/主机/板级（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。先分岔再修；仿真与真板两句证明不能并成一句；不是实拍。"),
    (ZH, "sample-22-hw-gap.svg", "ch22-hw-gap.png",
     "Handraw：仿真与实物差距必须上桌（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。sim 绿→desk 绿才算完成；晶振/USB/纹波仿真替不了；不是实拍。"),

    (EN, "simulator-comparison.svg", "ch22-sim-compare.png",
     "Handraw: Wokwi/Renode/desk three-column compare (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). Reproduce logic in the model, then measure on the desk; a green sim does not override hardware; not a photo."),
    (EN, "sample-22-wokwi-scope.svg", "ch22-wokwi-scope.png",
     "Handraw: Wokwi fit and limits (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). Logic/LED fit; ADC/USB/crystal margins need the desk; twin accept on BluePill; not a photo."),
    (EN, "sample-22-renode-path.svg", "ch22-renode-path.png",
     "Handraw: Renode platform→ELF→UART (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). Four-step script path; same golden string as the desk; green log ≠ HSE solder; not a photo."),
    (EN, "sample-22-sim-triage.svg", "ch22-sim-triage.png",
     "Handraw: sim triage model/host/board (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). Branch before you patch; sim proof and desk proof stay two sentences; not a photo."),
    (EN, "sample-22-hw-gap.svg", "ch22-hw-gap.png",
     "Handraw: sim vs hardware gap — desk required (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). sim green → desk green before done; crystal/USB/droop stay on the bench; not a photo."),
])
