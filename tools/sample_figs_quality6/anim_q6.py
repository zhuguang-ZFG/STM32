#!/usr/bin/env python3
"""Rebuild the UART, WWDG and supervisor mechanism animations in place."""
from __future__ import annotations

import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))

from svgkit import Svg, T
from sample_figs_quality3._common import audit_anim

OUT = TOOLS.parent / "assets" / "animations"


def _finish(svg, css, note):
    svg.add_style(css + """
@media (prefers-reduced-motion: reduce){*{animation:none!important}.moving{display:none}}
@media print{*{animation:none!important}.moving{display:none}}
""")
    svg.footer(note=note, label="自绘矢量动画 · FA-002 · STM32 知识库")
    return svg


def _label(svg, x, y, title, detail, color, width=220):
    svg.rect(x, y, width, 66, fill=T.PANEL, stroke=color, rx=8)
    svg.text(x + width / 2, y + 26, title, size=17, fill=color,
             anchor="middle", weight="700")
    svg.text(x + width / 2, y + 49, detail, size=13, anchor="middle")


def ore_overwrite_flow() -> Svg:
    svg = Svg(900, 620, "ORE：旧字节留下，新字节丢失",
              "STM32F103 · RXNE、ORE 与两级接收缓冲")
    svg.header(tag="06")
    svg.text(40, 95, "① 字节 1 已进 DR，CPU 还没读；字节 2 又接收完了", size=19, weight="700")
    _label(svg, 40, 124, "RX 线上", "字节 1 = 0xA5；字节 2 = 0x5A", T.CYAN, 250)
    _label(svg, 350, 124, "接收移位寄存器", "字节 2 等待交给 DR", T.AMBER, 230)
    _label(svg, 640, 124, "DR / RDR", "仍保存字节 1：0xA5", T.GREEN, 220)
    svg.arrow(294, 157, 344, 157, color=T.CYAN)
    svg.arrow(584, 157, 634, 157, color=T.RED)
    svg.line(607, 140, 607, 174, stroke=T.RED, sw=2)
    svg.line(601, 140, 613, 152, stroke=T.RED, sw=2)
    svg.text(610, 213, "RXNE=1：DR 还没腾空", size=15, fill=T.RED, anchor="middle")
    svg.circle(304, 157, 6, fill=T.CYAN, cls="incoming moving")
    svg.text(40, 259, "② 新字节不能覆盖 DR；ORE=1 报告来不及取数", size=19, weight="700")
    _label(svg, 40, 286, "字节 1：保留", "读 DR 仍能取出 0xA5", T.GREEN, 250)
    _label(svg, 325, 286, "字节 2：丢失", "移位寄存器随后被覆盖", T.RED, 250)
    _label(svg, 610, 286, "标志：RXNE=1，ORE=1", "清标志不会找回丢失的字节", T.AMBER, 250)
    svg.rect(325, 286, 250, 66, fill=T.RED, rx=8, opacity=0, cls="loss moving")
    svg.text(40, 397, "③ CPU 按顺序处理：先 SR，后 DR", size=19, weight="700")
    _label(svg, 40, 420, "先读 SR（0x00）", "保存错误状态", T.CYAN, 250)
    _label(svg, 355, 420, "再读 DR（0x04）", "取出旧字节，完成清除序列", T.GREEN, 270)
    svg.arrow(298, 453, 347, 453, color=T.CYAN)
    svg.text(650, 443, "RXNE → 0", size=17, fill=T.GREEN)
    svg.text(650, 473, "ORE → 0", size=17, fill=T.GREEN)
    svg.circle(306, 453, 6, fill=T.GREEN, cls="clear moving")
    svg.text(40, 529, "只读 DR 会清 RXNE，但不构成 ORE / FE 所需的 SR→DR 清除序列。", size=16)
    svg.text(40, 554, "115200 8N1：约 8.68 µs/位，86.8 µs/帧；动画已放慢。", size=14, fill=T.MUTED)
    css = """
@keyframes incoming{0%,8%{transform:translateX(0);opacity:0}10%{opacity:1}30%{transform:translateX(34px);opacity:1}31%,100%{opacity:0}}
@keyframes loss{0%,30%,61%,100%{opacity:0}32%,59%{opacity:.18}}
@keyframes clear{0%,62%{transform:translateX(0);opacity:0}64%{opacity:1}83%{transform:translateX(32px);opacity:1}84%,100%{opacity:0}}
.incoming{animation:incoming 10s linear infinite}.loss{animation:loss 10s linear infinite}.clear{animation:clear 10s linear infinite}
"""
    return _finish(svg, css, "RM0008 Rev 21 §27.3.3 / §27.6.1 · 原理示意，非示波器实测")


def wwdg_window_flow() -> Svg:
    svg = Svg(900, 620, "WWDG：窗口内喂狗就重新计数",
              "STM32F103 · PCLK1=36 MHz · 预分频 8 · W=0x50 · 初值 0x7F")
    svg.header(tag="11", tag_color=T.AMBER)
    start, window, floor, end = 80, 620.5, 804.5, 816
    svg.text(40, 98, "计数越小，经过的时间越长；下方两条路径从同一个初值分别出发。", size=17)
    svg.rect(start, 126, window - start, 40, fill=T.PANEL, stroke=T.RED, rx=2)
    svg.rect(window, 126, floor - window, 40, fill=T.PANEL, stroke=T.GREEN, rx=2)
    svg.rect(floor, 126, end - floor, 40, fill=T.RED, rx=2)
    svg.text(320, 152, "T > 0x50：喂早会复位", size=17, anchor="middle", fill=T.RED)
    svg.text(711, 152, "允许重载", size=16, anchor="middle", fill=T.GREEN)
    for position, label, anchor in ((start, "0x7F", "middle"), (window, "0x50", "middle"),
                                    (floor, "0x40", "end"), (end + 12, "0x3F", "start")):
        svg.line(position if position <= end else end, 170,
                 position if position <= end else end, 182, stroke=T.STROKE, sw=1)
        svg.text(position, 204, label, size=14, anchor=anchor, mono=True)
    svg.text(40, 246, "路径 A：在 T=0x48 时重载 0x7F，开始下一轮", size=19, fill=T.GREEN, weight="700")
    svg.arrow(start, 291, 712.5, 291, color=T.GREEN)
    svg.path("M712.5 291 V325 H80 V291", stroke=T.GREEN, sw=2)
    svg.text(390, 348, "成功喂狗 → 回到初值；不会接着走向 0x3F", size=16, fill=T.GREEN, anchor="middle")
    svg.circle(start, 291, 7, fill=T.GREEN, cls="reload moving")
    svg.text(40, 394, "路径 B：一直不重载，0x40 → 0x3F 时复位", size=19, fill=T.RED, weight="700")
    svg.arrow(start, 433, end, 433, color=T.RED)
    svg.circle(start, 433, 7, fill=T.RED, cls="expire moving")
    svg.circle(end, 433, 13, stroke=T.RED, sw=2)
    svg.text(80, 474, "0x40 时可触发 EWI；到 0x3F 时 T6 清零。", size=16)
    svg.text(40, 521, "一拍 = 4096 × 8 / 36 MHz ≈ 910.2 µs；64 拍 ≈ 58.25 ms。", size=16)
    svg.text(40, 548, "窗口 0x40 ≤ T ≤ 0x50；示意动画放慢，数轴按计数差等比例。", size=15, fill=T.MUTED)
    css = """
@keyframes reload{0%,8%{transform:translateX(0)}76%{transform:translateX(632.5px)}77%{transform:translateX(0)}100%{transform:translateX(0)}}
@keyframes expire{0%,8%{transform:translateX(0)}88%,100%{transform:translateX(736px)}}
.reload{animation:reload 10s linear infinite}.expire{animation:expire 10s linear infinite}
"""
    return _finish(svg, css, "RM0008 Rev 21 §20.3 · 自绘机制对照，非实测超时")


def supervisor_flow() -> Svg:
    svg = Svg(900, 620, "看门狗：任何关键任务停滞，都不能喂",
              "epoch 是完成工作后递增的进度计数；任务之间没有 A→B→C 的执行依赖")
    svg.header(tag="28")
    svg.text(40, 98, "每个任务只汇报进度；只有监督任务能刷新 IWDG。", size=19, weight="700")
    for row, (task, detail, color) in enumerate((
        ("任务 A · 采样", "完成一批采样 → epoch++", T.GREEN),
        ("任务 B · 协议", "完成一次有效事务 → epoch++", T.CYAN),
        ("任务 C · 存储", "完成一次写入 → epoch++", T.AMBER),
    )):
        vertical = 125 + row * 92
        _label(svg, 40, vertical, task, detail, color, 275)
        svg.arrow(322, vertical + 33, 396, vertical + 33, color=color)
        svg.circle(330, vertical + 33, 5, fill=color, cls=f"report{row} moving")
    svg.rect(404, 125, 222, 250, fill=T.PANEL, stroke=T.CYAN, rx=8)
    svg.text(515, 160, "监督任务", size=22, anchor="middle", weight="700", fill=T.CYAN)
    for offset, label in enumerate(("各任务按自身期限前进？", "队列积压在界限内？", "内存水位正常？", "状态机没有卡住？")):
        svg.text(420, 205 + offset * 36, label, size=15)
    svg.arrow(631, 181, 670, 181, color=T.GREEN)
    svg.arrow(631, 302, 670, 302, color=T.RED)
    _label(svg, 680, 145, "全部通过", "监督者刷新 IWDG", T.GREEN, 180)
    _label(svg, 680, 266, "任一项失败", "停止刷新，等待复位", T.RED, 180)
    svg.text(40, 420, "对照一轮检查：", size=18, weight="700")
    svg.rect(40, 439, 820, 44, fill=T.PANEL, stroke=T.GREEN, rx=8)
    svg.text(56, 467, "A 前进、B 前进、C 前进，其他条件通过 → 喂狗", size=17, fill=T.GREEN)
    svg.rect(40, 493, 820, 44, fill=T.PANEL, stroke=T.RED, rx=8)
    svg.text(56, 521, "B 超过自己的期限仍未前进，即使 A/C 正常 → 不喂狗", size=17, fill=T.RED)
    svg.circle(648, 181, 5, fill=T.GREEN, cls="pass moving")
    svg.circle(648, 302, 5, fill=T.RED, cls="fail moving")
    svg.text(40, 563, "故障摘要尽力保存并设截止点；保存失败也不能继续喂狗。", size=15, fill=T.MUTED)
    css = """
@keyframes report{0%,5%{transform:translateX(0);opacity:0}8%{opacity:1}30%{transform:translateX(56px);opacity:1}31%,100%{opacity:0}}
@keyframes missing{0%,5%{transform:translateX(0);opacity:0}8%{opacity:1}30%{transform:translateX(56px);opacity:1}31%,100%{opacity:0}}
@keyframes pass{0%,32%,47%,100%{opacity:0}34%,45%{opacity:1}}
@keyframes fail{0%,78%,95%,100%{opacity:0}80%,93%{opacity:1}}
.report0,.report2{animation:report 6s linear infinite}.report1{animation:missing 12s linear infinite}
.pass{animation:pass 12s linear infinite}.fail{animation:fail 12s linear infinite}
"""
    return _finish(svg, css, "自绘系统设计模式 · 不表示具体调度顺序或硬件测量结果")


ANIMS = [
    ("sample-06-ore-overwrite-flow.svg", ore_overwrite_flow),
    ("sample-11-wwdg-window-flow.svg", wwdg_window_flow),
    ("sample-28-supervisor-flow.svg", supervisor_flow),
]


def main() -> None:
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    output.mkdir(parents=True, exist_ok=True)
    for name, builder in ANIMS:
        path = output / name
        builder().save(str(path))
        audit_anim(name, str(path))


if __name__ == "__main__":
    main()
