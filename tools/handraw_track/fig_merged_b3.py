# -*- coding: utf-8 -*-
"""B3 merged-book plates for ch29-32 (handraw grammar, research-anchored facts).

These four plates fill the handraw gap for merged-book chapters ch29 (GD32),
ch30 (ESP32-S3 boot), ch31 (ESP32 peripherals/audio) and ch32 (Wi-Fi/BLE/ESP-NOW).
They are written to a staging dir (.temp/b3-plates/) and rendered to PNG by
tools/handraw_track/render.py; the PNGs land in docs/public/images/ with the
mcNN- prefix so they never collide with the old-book chNN- handraw census.

Facts are pinned to the B3 research docs:
- .superpowers/sdd/2026-11-14-merged-book-b3-vol4-5/research/b3-migration-gd32-sources.md
- .../b3-esp32-sources.md
Deterministic: same code -> same SVG bytes -> same PNG pixels.
"""
from pathlib import Path

from hd import (AMBER_FILL, AMBER_STROKE, BLUE, BLUE_D, GREEN, GREEN_D, INK,
                MUTED, RED, W, WHITE, Fig, save)

STAGE = Path(__file__).resolve().parents[2] / ".temp" / "b3-plates"


def band(f, x, y, w, h, fill):
    f.panel(x, y, w, h, fill)


def plate_mc29():
    """GD32 vs STM32: clock tree deltas + USART landing spot."""
    f = Fig("mc29-gd32-contrast", "GD32 与 STM32：同名骨架，三处不同")
    # two columns
    cw, gap = 470, 44
    x0 = (W - (cw * 2 + gap)) / 2
    y0 = 150
    f.rect(x0, y0, cw, 330, color=GREEN_D, fill=WHITE)
    f.htext(x0 + cw / 2, y0 + 44, "STM32F4（RCC）", size=30, color=GREEN_D,
            anchor="middle", weight="bold")
    f.multi(x0 + 30, y0 + 96, [
        "PLL 一级，HSE 直驱", "APB1≤42MHz · APB2≤84MHz", "复位默认 HSI 16MHz",
        "统计口径：RCC_CFGR/PLLCFGR",
    ], size=24, color=INK, lh=40)
    f.rect(x0 + cw + gap, y0, cw, 330, color=BLUE_D, fill=WHITE)
    f.htext(x0 + cw + gap + cw / 2, y0 + 44, "GD32F4xx（RCU）", size=30,
            color=BLUE_D, anchor="middle", weight="bold")
    f.multi(x0 + cw + gap + 30, y0 + 96, [
        "PLL1/PLL2 配好且使能，", "  但不在时钟路径（配而不用）",
        "APB 分频上限与 F4 不同档", "IRC48M 兜底，缺省档位另查",
    ], size=24, color=INK, lh=40)
    band(f, x0 + cw + gap + 18, y0 + 240, cw - 36, 58, AMBER_FILL)
    f.htext(x0 + cw + gap + cw / 2, y0 + 278, "SystemInit 默认 168MHz，200M 是预设档",
            size=22, color=INK, anchor="middle", weight="bold")
    # bottom strip: USART landing
    y1 = 520
    f.rect(80, y1, W - 160, 200, color=AMBER_STROKE, fill=WHITE)
    f.htext(W / 2, y1 + 44, "换库最容易错的两格：USART 的地址与偏移", size=27,
            color=AMBER_STROKE, anchor="middle", weight="bold",
            hl=True, hl_fill=AMBER_FILL)
    f.multi(110, y1 + 92, [
        "USART0 = APB2 @ 0x40011000（APB1+0x4400 那格是 USART1）",
        "寄存器偏移按上游定谳：STAT0@0x00 · CTL0@0x0C",
        "同一外设骨架：改名先对地址，再对偏移，最后对位段",
    ], size=24, color=INK, lh=42)
    return f


def plate_mc30():
    """ESP32-S3 three-stick boot relay."""
    f = Fig("mc30-s3-boot-chain", "ESP32-S3 启动：三棒接力，日志就是分诊单")
    xs = [90, 460, 830]
    cw, ch = 250, 260
    y0 = 150
    stages = [
        ("① ROM", "rst: 日志", GREEN_D,
         ["上电第一棒", "固定掩膜代码", "卡点：rst 前无输出", "→ 查供电/晶振/串"]),
        ("② bootloader", "boot: 日志", BLUE_D,
         ["读分区表", "挑 app 分区", "卡点：boot 后停", "→ 查分区表/镜像"]),
        ("③ app", "app_start:", AMBER_STROKE,
         ["main task 起", "优先级 1 · 栈 3584 起", "卡点：进 app 后崩", "→ 查 sdkconfig 目标"]),
    ]
    for i, (name, log, c, lines) in enumerate(stages):
        x = xs[i]
        f.rect(x, y0, cw, ch, color=c, fill=WHITE)
        f.htext(x + cw / 2, y0 + 44, name, size=30, color=c, anchor="middle",
                weight="bold")
        f.htext(x + cw / 2, y0 + 78, log, size=22, color=MUTED, anchor="middle")
        f.multi(x + 24, y0 + 122, lines, size=22, color=INK, lh=36)
        if i < 2:
            f.arrow(xs[i] + cw + 8, y0 + ch / 2, xs[i + 1] - 8, y0 + ch / 2,
                    color=BLUE, sw=3.4)
    band(f, 90, 470, W - 180, 70, AMBER_FILL)
    f.htext(W / 2, 514, "分诊口诀：rst: 归 ROM，boot: 归引导，app_start: 之后才怪软件",
            size=26, color=INK, anchor="middle", weight="bold")
    f.rect(90, 580, W - 180, 130, color=RED, fill=WHITE)
    f.htext(W / 2, 620, "XIP 是最容易踩的架构差", size=26, color=RED,
            anchor="middle", weight="bold")
    f.text(W / 2, 660, "代码住在 Flash、经 Cache 窗口取指：关 Cache 的窗口里 Flash 不可执行",
           size=23, color=INK, anchor="middle")
    f.text(W / 2, 692, "与 F407「原地执行」是两平台最本质的一条差，IRAM 纪律由此而来",
           size=23, color=MUTED, anchor="middle")
    return f


def plate_mc31():
    """Audio dual-plane: control I2C + data I2S with three accounts."""
    f = Fig("mc31-matrix-audio", "音频双面：控制面走 I2C，数据面走 I2S")
    # control plane
    f.rect(80, 150, 470, 300, color=GREEN_D, fill=WHITE)
    f.htext(315, 194, "控制面 · I2C", size=30, color=GREEN_D, anchor="middle",
            weight="bold")
    f.multi(110, 246, [
        "ES8311：DAC 侧（放）", "ES7210：ADC 侧（收）",
        "寄存器页/音量/静音位", "esp_codec_dev 是管理组件，", "  版本钉 1.3.4，非 IDF 自带",
    ], size=23, color=INK, lh=38)
    # data plane
    f.rect(602, 150, 470, 300, color=BLUE_D, fill=WHITE)
    f.htext(837, 194, "数据面 · I2S", size=30, color=BLUE_D, anchor="middle",
            weight="bold")
    f.multi(632, 246, [
        "MCLK = 256 × fs（时钟母线）", "BCLK/LRCLK 按槽走",
        "单声道内容走 stereo 双槽位", "PA_EN 在扩展板上，", "  不在 ESP32 的 GPIO",
    ], size=23, color=INK, lh=38)
    # three accounts strip
    y1 = 500
    f.rect(80, y1, W - 160, 130, color=AMBER_STROKE, fill=WHITE)
    f.htext(W / 2, y1 + 40, "三笔账一起算，缺一笔就是空谈", size=26,
            color=AMBER_STROKE, anchor="middle", weight="bold",
            hl=True, hl_fill=AMBER_FILL)
    f.text(W / 2, y1 + 78, "码率 512 kbps（16k×16×2）· MCLK 4.096 MHz · 10ms 信封 = 延迟预算",
           size=23, color=INK, anchor="middle")
    f.text(W / 2, y1 + 108, "缓冲容量 = 采样率 × 容忍延迟 × 2；BLOCK_FRAMES=160 → 20ms 往返",
           size=22, color=MUTED, anchor="middle")
    f.htext(W / 2, 700, "纪律：先静音，再发声，后放开 PA", size=25, color=RED,
            anchor="middle", weight="bold")
    return f


def plate_mc32():
    """Wi-Fi event loop six steps + backoff ladder + ESP-NOW bypass."""
    f = Fig("mc32-wifi-espnow", "Wi-Fi 六步骨架，断了就按退避爬回去")
    steps = [
        "① NVS 先 init（校准+MAC 都住那）",
        "② 起事件循环（默认任务）",
        "③ wifi_init + 注册 handler",
        "④ 配 STA 配置（SSID/密码）",
        "⑤ start（异步，等 STA_START）",
        "⑥ connect；断了读 reason 分诊",
    ]
    y0 = 150
    for i, s in enumerate(steps):
        yy = y0 + i * 62
        f.rect(80, yy - 26, 610, 48, color=GREEN_D, fill=WHITE)
        f.text(102, yy + 6, s, size=24, color=INK)
    # right column: backoff + espnow
    f.rect(730, y0 - 26, 352, 210, color=AMBER_STROKE, fill=WHITE)
    f.htext(906, y0 + 14, "断线退避（秒）", size=25, color=AMBER_STROKE,
            anchor="middle", weight="bold")
    f.text(906, y0 + 56, "1→2→4→8→15→30→60", size=21, color=INK,
           anchor="middle", weight="bold")
    f.text(906, y0 + 96, "reason 201 没找到 AP", size=20, color=INK, anchor="middle")
    f.text(906, y0 + 128, "15 四次握手超时 · 202 认证失败", size=20, color=INK,
           anchor="middle")
    f.text(906, y0 + 160, "203 关联失败（4 是弃用码，别用）", size=20, color=RED,
           anchor="middle")
    f.rect(730, y0 + 240, 352, 150, color=BLUE_D, fill=WHITE)
    f.htext(906, y0 + 278, "ESP-NOW：旁路直连", size=25, color=BLUE_D,
            anchor="middle", weight="bold")
    f.multi(754, y0 + 314, [
        "不走 AP，peer 互发", "载荷 ≤250B（长帧 1470 分片）",
        "加密 peer ≤6 · 总 peer ≤20",
    ], size=20, color=INK, lh=30)
    f.htext(W / 2, 720, "handler 不能阻塞：长操作丢定时器或任务，别站在事件循环里",
            size=25, color=RED, anchor="middle", weight="bold", hl=True,
            hl_fill=AMBER_FILL)
    return f


PLATES = {
    "mc29-gd32-contrast": plate_mc29,
    "mc30-s3-boot-chain": plate_mc30,
    "mc31-matrix-audio": plate_mc31,
    "mc32-wifi-espnow": plate_mc32,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(PLATES)
    STAGE.mkdir(parents=True, exist_ok=True)
    for n in names:
        f = PLATES[n]()
        save(f, str(STAGE / (n + ".svg")))
        print("wrote", STAGE / (n + ".svg"))
