#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mechanism animations for ch23–28 + appendix F — new files + remake g0-boot-swd."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from svgkit import Svg, T, anim_flow
from sample_figs_quality5._common import audit_anim

W, H = 900, 620
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                   "assets", "animations")


def _step_highlight(prefix: str, n: int, period=6.0, window=0.2, peak=0.35, rest=0.06) -> str:
    css = []
    step = 100.0 / n
    for i in range(n):
        a = i * step
        b = min(a + step * window, 99.0)
        name = f"{prefix}{i}-flash"
        css.append(
            f"@keyframes {name}{{0%,{a:.2f}%{{opacity:{rest}}}"
            f"{a + 0.25:.2f}%,{b:.2f}%{{opacity:{peak}}}"
            f"{min(b + 0.25, 100):.2f}%,100%{{opacity:{rest}}}}}"
        )
        css.append(f".{prefix}{i}{{animation:{name} {period}s linear infinite;}}")
    return "\n".join(css)


def _flow_row(s, steps, css, y0=100):
    bw, gap, x0, bh = 120, 18, 40, 100
    for i, (t, n, col) in enumerate(steps):
        x = x0 + i * (bw + gap)
        s.rect(x, y0, bw, bh, fill=T.PANEL, stroke=col, rx=8)
        s.text(x + bw / 2, y0 + 32, t, size=13, anchor="middle", fill=col, weight="700")
        s.text(x + bw / 2, y0 + 60, n, size=11, anchor="middle", fill=T.TEXT, mono=True)
        s.rect(x, y0, bw, bh, fill=col, rx=8, cls=f"s{i}", opacity=0.12)
        if i < len(steps) - 1:
            ax1, ax2 = x + bw + 4, x + bw + gap - 4
            s.arrow(ax1, y0 + bh / 2, ax2, y0 + bh / 2, color=T.STROKE, sw=2)
            s.line(ax1, y0 + bh / 2, ax2, y0 + bh / 2, stroke=T.CYAN, sw=2, cls=f"f{i}")
            css.append(anim_flow(f".f{i}", dur="1.2s", dash="6 12", shift=-18))
    css.append(_step_highlight("s", len(steps), period=7.0))


def _panel_rows(s, rows, y0=250):
    for i, (a, b, col) in enumerate(rows):
        y = y0 + i * 44
        s.rect(40, y, 820, 38, fill=T.PANEL, stroke=T.STROKE, rx=8)
        s.text(56, y + 24, a, size=13, fill=col, weight="700", mono=True)
        s.text(840, y + 24, b, size=13, fill=T.TEXT, anchor="end")


def boot_source_flow() -> Svg:
    s = Svg(W, H, "G0 boot source decide", "option bytes → BOOT0 sample → Flash or system")
    s.header(title="G0：先判定启动来源再碰 SWD", subtitle="mechanism · FA-002 continuous-line",
             tag="23", tag_color=T.CYAN)
    css = []
    steps = [
        ("OPT", "nBOOT_SEL", T.CYAN),
        ("PIN", "BOOT0 samp", T.GREEN),
        ("PATH", "Flash/sys", T.AMBER),
        ("VECTOR", "MSP+Reset", T.VIOLET),
        ("SWD", "attach", T.GREEN),
        ("OK", "halt", T.CYAN),
    ]
    _flow_row(s, steps, css)
    s.title_block(40, 230, "Happy path: Flash alias, then SWCLK is a debug pin — not a boot pin fight", color=T.GREEN)
    _panel_rows(s, [
        ("OPT", "read nBOOT0 / nSWBOOT0 before blaming the cable", T.CYAN),
        ("PIN", "BOOT0 level at NRST release latches the path", T.GREEN),
        ("SWD", "only after path is Flash for application debug", T.AMBER),
        ("FAIL", "noise on SWCLK while BOOT samples high → false 'no ST-Link'", T.RED),
    ])
    s.rect(40, 450, 820, 70, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(56, 478, "Static plates keep F1 copy traps; motion is decide→vector→SWD.", size=13, fill=T.TEXT)
    s.text(56, 500, "Remake companion: g0-boot-swd.svg (FA-002).", size=12, fill=T.MUTED)
    css.append("@media (prefers-reduced-motion: reduce){*{animation:none!important}}")
    s.add_style("\n".join(css))
    s.footer(note="自绘矢量动画（FA-002）· G0 boot source",
             label="自绘矢量动画 · STM32 知识库")
    return s


def stop2_wake_flow() -> Svg:
    s = Svg(W, H, "L4 Stop2 wake restore", "flag → clocks → comms → app")
    s.header(title="L4 Stop2：唤醒后先恢复时钟再说话", subtitle="mechanism · FA-002 continuous-line",
             tag="24", tag_color=T.GREEN)
    css = []
    steps = [
        ("SLEEP", "Stop2", T.CYAN),
        ("IRQ", "flag", T.GREEN),
        ("CLK", "HSI/PLL", T.AMBER),
        ("UART", "re-baud", T.VIOLET),
        ("APP", "work", T.GREEN),
        ("OK", "evidence", T.CYAN),
    ]
    _flow_row(s, steps, css)
    s.title_block(40, 230, "Do not log on UART until restore evidence is green", color=T.GREEN)
    _panel_rows(s, [
        ("IRQ", "record wake source before HAL clears it", T.CYAN),
        ("CLK", "SystemCoreClock + timer tick proof", T.GREEN),
        ("COM", "re-init USART / I2C after dividers exist", T.AMBER),
        ("IDD", "JP6 integral is a separate accept sheet", T.VIOLET),
    ])
    s.rect(40, 450, 820, 70, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(56, 478, "Retention map stays on sample-24-stop2-retain.", size=13, fill=T.TEXT)
    s.text(56, 500, "Motion is sleep→flag→clock→comms.", size=12, fill=T.MUTED)
    css.append("@media (prefers-reduced-motion: reduce){*{animation:none!important}}")
    s.add_style("\n".join(css))
    s.footer(note="自绘矢量动画（FA-002）· L4 Stop2 wake",
             label="自绘矢量动画 · STM32 知识库")
    return s


def hse_to_480_flow() -> Svg:
    s = Svg(W, H, "H7 HSE to 480 MHz", "VOS → HSE → PLL1 → SYS")
    s.header(title="H7：电压档就绪后再锁 480 MHz", subtitle="mechanism · FA-002 continuous-line",
             tag="25", tag_color=T.AMBER)
    css = []
    steps = [
        ("VOS", "ready", T.CYAN),
        ("HSE", "8 MHz", T.GREEN),
        ("PLL1", "mul/div", T.AMBER),
        ("SYS", "480M", T.VIOLET),
        ("BUS", "HCLK", T.GREEN),
        ("OK", "triad", T.CYAN),
    ]
    _flow_row(s, steps, css)
    s.title_block(40, 230, "Evidence triad: SystemCoreClock, timer, one peripheral gate", color=T.GREEN)
    _panel_rows(s, [
        ("VOS", "wait VOSRDY for the scale you programmed", T.CYAN),
        ("HSE", "Nucleo 8 MHz typical — measure before PLL blame", T.GREEN),
        ("PLL", "only after supply path matches DS table", T.AMBER),
        ("CACHE", "DMA clean/invalidate is a later plate", T.VIOLET),
    ])
    s.rect(40, 450, 820, 70, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(56, 478, "Voltage-scale static plate gates this motion.", size=13, fill=T.TEXT)
    s.text(56, 500, "h7-clock-chain remains the long-form companion.", size=12, fill=T.MUTED)
    css.append("@media (prefers-reduced-motion: reduce){*{animation:none!important}}")
    s.add_style("\n".join(css))
    s.footer(note="自绘矢量动画（FA-002）· H7 HSE→480",
             label="自绘矢量动画 · STM32 知识库")
    return s


def spl_init_flow() -> Svg:
    s = Svg(W, H, "SPL init call chain", "RCC → deinit/defaults → init → cmd")
    s.header(title="SPL：时钟 → 默认值 → 配置 → 使能", subtitle="mechanism · FA-002 continuous-line",
             tag="26", tag_color=T.CYAN)
    css = []
    steps = [
        ("RCC", "clock on", T.CYAN),
        ("DEF", "struct", T.GREEN),
        ("INIT", "GPIO/UART", T.AMBER),
        ("CMD", "enable", T.VIOLET),
        ("IRQ", "misc NVIC", T.GREEN),
        ("OK", "poll/TO", T.CYAN),
    ]
    _flow_row(s, steps, css)
    s.title_block(40, 230, "No HAL MSP callback — every clock and NVIC line is explicit", color=T.GREEN)
    _panel_rows(s, [
        ("RCC", "APB/AHB enable before GPIO_Init", T.CYAN),
        ("DEF", "fill struct; do not trust stack garbage", T.GREEN),
        ("IRQ", "misc.c NVIC_Init — you dispatch in the ISR", T.AMBER),
        ("TO", "poll loops carry timeouts (static plate)", T.RED),
    ])
    s.rect(40, 450, 820, 70, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(56, 478, "File matrix plate lists which .c must be linked.", size=13, fill=T.TEXT)
    s.text(56, 500, "Motion is the call order only.", size=12, fill=T.MUTED)
    css.append("@media (prefers-reduced-motion: reduce){*{animation:none!important}}")
    s.add_style("\n".join(css))
    s.footer(note="自绘矢量动画（FA-002）· SPL init chain",
             label="自绘矢量动画 · STM32 知识库")
    return s


def link_dhcp_flow() -> Svg:
    s = Svg(W, H, "Link to usable IP", "PHY → link → DHCP/static → ping")
    s.header(title="网络：链路亮不等于地址可用", subtitle="mechanism · FA-002 continuous-line",
             tag="27", tag_color=T.GREEN)
    css = []
    steps = [
        ("PHY", "MDIO ID", T.CYAN),
        ("LINK", "bit", T.GREEN),
        ("MAC", "start", T.AMBER),
        ("IP", "DHCP/static", T.VIOLET),
        ("PING", "known host", T.GREEN),
        ("OK", "app", T.CYAN),
    ]
    _flow_row(s, steps, css)
    s.title_block(40, 230, "RMII wiring plate first — then this bring-up motion", color=T.GREEN)
    _panel_rows(s, [
        ("PHY", "read ID register before chasing lwIP", T.CYAN),
        ("LINK", "LED is a clue; MAC clock must match REF_CLK", T.GREEN),
        ("IP", "DHCP fail ≠ 'Ethernet dead' — check lease path", T.AMBER),
        ("TCP", "framing plate owns message edges later", T.VIOLET),
    ])
    s.rect(40, 450, 820, 70, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(56, 478, "H7 cache/DMA ownership stays on sample-25-dcache-dma.", size=13, fill=T.TEXT)
    s.text(56, 500, "Motion is PHY→link→IP→ping.", size=12, fill=T.MUTED)
    css.append("@media (prefers-reduced-motion: reduce){*{animation:none!important}}")
    s.add_style("\n".join(css))
    s.footer(note="自绘矢量动画（FA-002）· link→IP",
             label="自绘矢量动画 · STM32 知识库")
    return s


def isr_owner_flow() -> Svg:
    s = Svg(W, H, "ISR to owner task", "ISR posts; owner task writes the device")
    s.header(title="RTOS：ISR 只投递，所有者任务才碰硬件", subtitle="mechanism · FA-002 continuous-line",
             tag="28", tag_color=T.VIOLET)
    css = []
    steps = [
        ("IRQ", "sample", T.CYAN),
        ("POST", "queue", T.GREEN),
        ("OWNER", "task", T.AMBER),
        ("DEVICE", "one writer", T.VIOLET),
        ("ACK", "done", T.GREEN),
        ("OK", "budget", T.CYAN),
    ]
    _flow_row(s, steps, css)
    s.title_block(40, 230, "Mutex spray is not a design — name the owner", color=T.GREEN)
    _panel_rows(s, [
        ("IRQ", "shortest work: capture + post FromISR", T.CYAN),
        ("OWNER", "only task that talks to the peripheral", T.GREEN),
        ("TIME", "period / timeout / deadline vocabulary plate", T.AMBER),
        ("FAIL", "priority inversion without a documented ceiling", T.RED),
    ])
    s.rect(40, 450, 820, 70, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(56, 478, "sample-28-owner-flow remains; this motion is the handoff spine.", size=13, fill=T.TEXT)
    s.text(56, 500, "Four-concepts plate chooses the model first.", size=12, fill=T.MUTED)
    css.append("@media (prefers-reduced-motion: reduce){*{animation:none!important}}")
    s.add_style("\n".join(css))
    s.footer(note="自绘矢量动画（FA-002）· ISR→owner",
             label="自绘矢量动画 · STM32 知识库")
    return s


def repo_lane_flow() -> Svg:
    s = Svg(W, H, "Pick a repo lane", "clone → file → quote → lab note")
    s.header(title="附录 F：选一条仓库车道读到底", subtitle="mechanism · FA-002 continuous-line",
             tag="F", tag_color=T.VIOLET)
    css = []
    steps = [
        ("PICK", "one tree", T.CYAN),
        ("CLONE", "pin SHA", T.GREEN),
        ("FIND", "the file", T.AMBER),
        ("QUOTE", "line", T.VIOLET),
        ("NOTE", "lab card", T.GREEN),
        ("OK", "ask/ready", T.CYAN),
    ]
    _flow_row(s, steps, css)
    s.title_block(40, 230, "Six-facts plate lists what only source reveals", color=T.GREEN)
    _panel_rows(s, [
        ("PICK", "Cube / CMSIS / libopencm3 / FreeRTOS / RTT", T.CYAN),
        ("PIN", "archived ≠ frozen — record the commit", T.GREEN),
        ("ASK", "five-before checklist when stuck", T.AMBER),
        ("MAP", "sample-f-oss-map for the landscape", T.VIOLET),
    ])
    s.rect(40, 450, 820, 70, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(56, 478, "Motion is pick→pin→quote — not a star-count race.", size=13, fill=T.TEXT)
    s.text(56, 500, "Community ask plate owns the question template.", size=12, fill=T.MUTED)
    css.append("@media (prefers-reduced-motion: reduce){*{animation:none!important}}")
    s.add_style("\n".join(css))
    s.footer(note="自绘矢量动画（FA-002）· appendix F repo lane",
             label="自绘矢量动画 · STM32 知识库")
    return s


def remake_g0_boot_swd() -> Svg:
    """In-place remake of weak g0-boot-swd.svg to FA-002 teaching quality."""
    s = Svg(W, H, "G0 BOOT vs SWD", "sample boot, then attach")
    s.header(title="G0：BOOT 采样稳定后再驱动 SWCLK", subtitle="mechanism · FA-002 continuous-line · remake",
             tag="23", tag_color=T.CYAN)
    css = []
    steps = [
        ("NRST", "release", T.CYAN),
        ("BOOT", "sample", T.GREEN),
        ("LATCH", "path", T.AMBER),
        ("FLASH", "vectors", T.VIOLET),
        ("SWCLK", "drive", T.GREEN),
        ("HALT", "debug", T.CYAN),
    ]
    _flow_row(s, steps, css)
    s.title_block(40, 230, "Shared-pad reality: boot decision owns the first milliseconds", color=T.GREEN)
    _panel_rows(s, [
        ("NRST", "release edge is when BOOT0 is sampled", T.CYAN),
        ("OPT", "nBOOT_SEL may ignore the pin — read options", T.GREEN),
        ("SWD", "attach after Flash path is proven", T.AMBER),
        ("OLD", "pre-remake lacked FA-002 credit / reduced-motion pack", T.MUTED),
    ])
    s.rect(40, 450, 820, 70, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(56, 478, "Filename kept: g0-boot-swd.svg — denser teaching remake.", size=13, fill=T.TEXT)
    s.text(56, 500, "Companion new anim: sample-23-boot-source-flow.svg.", size=12, fill=T.MUTED)
    css.append("@media (prefers-reduced-motion: reduce){*{animation:none!important}}")
    s.add_style("\n".join(css))
    s.footer(note="自绘矢量动画（FA-002）· G0 BOOT/SWD remake",
             label="自绘矢量动画 · STM32 知识库")
    return s


ANIMS = [
    ("sample-23-boot-source-flow.svg", boot_source_flow),
    ("sample-24-wake-restore-flow.svg", stop2_wake_flow),
    ("sample-25-hse-to-480-flow.svg", hse_to_480_flow),
    ("sample-26-clk-cfg-en-flow.svg", spl_init_flow),
    ("sample-27-link-dhcp-flow.svg", link_dhcp_flow),
    ("sample-28-isr-owner-flow.svg", isr_owner_flow),
    ("sample-f-repo-lane-flow.svg", repo_lane_flow),
    ("g0-boot-swd.svg", remake_g0_boot_swd),  # in-place remake
]


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    for name, fn in ANIMS:
        svg = fn()
        path = os.path.join(OUT, name)
        svg.save(path)
        audit_anim(name, path)


if __name__ == "__main__":
    main()
