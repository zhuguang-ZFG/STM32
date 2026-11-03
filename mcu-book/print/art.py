"""自绘主题插图（书稿工艺层）：封面与 10 个分部隔页的矢量小插画。

风格统一：240×160 viewBox、细线几何、主色 #0e6e5c（站点 accent），
浅色底 #e2f1ec、辅助 #7fc8b8、点缀 #d97706（暖色只用于高光）。
全部手写 SVG，无外部素材、无版权问题；字体只用通用 sans（图内只有极少量标签）。
"""

from __future__ import annotations

import re

ACCENT = "#0e6e5c"
SOFT = "#e2f1ec"
LIGHT = "#7fc8b8"
WARM = "#d97706"
INK = "#123b33"


def _svg(body: str, label: str, view: str = "0 0 240 160") -> str:
    """每个图各自给紧凑 viewBox：留白由版面 CSS 控制，不由图内空白决定。"""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{view}" '
        f'role="img" aria-label="{label}">{body}</svg>'
    )


def _chip(x: float, y: float, w: float, h: float, label: str = "", texts: list[str] | None = None) -> str:
    """一枚芯片：外框 + 四边引脚 + 内框。label 文字默认随形状返回；给了 texts 就单独收集（不随形状进抖动滤镜）。"""
    parts = [
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{SOFT}" stroke="{ACCENT}" stroke-width="2"/>',
        f'<rect x="{x+10}" y="{y+10}" width="{w-20}" height="{h-20}" rx="3" fill="none" stroke="{LIGHT}" stroke-width="1.2"/>',
    ]
    for i in range(4):
        px = x + 12 + i * (w - 24) / 3
        parts.append(f'<line x1="{px}" y1="{y-10}" x2="{px}" y2="{y}" stroke="{ACCENT}" stroke-width="2"/>')
        parts.append(f'<line x1="{px}" y1="{y+h}" x2="{px}" y2="{y+h+10}" stroke="{ACCENT}" stroke-width="2"/>')
    for i in range(2):
        py = y + 14 + i * (h - 28)
        parts.append(f'<line x1="{x-10}" y1="{py}" x2="{x}" y2="{py}" stroke="{ACCENT}" stroke-width="2"/>')
        parts.append(f'<line x1="{x+w}" y1="{py}" x2="{x+w+10}" y2="{py}" stroke="{ACCENT}" stroke-width="2"/>')
    if label:
        t = (
            f'<text x="{x+w/2}" y="{y+h/2+5}" text-anchor="middle" font-family="sans-serif" '
            f'font-size="14" font-weight="bold" fill="{INK}">{label}</text>'
        )
        if texts is not None:
            texts.append(t)
        else:
            parts.append(t)
    return "".join(parts)



def _hw_part(pid: str, items: list[str], label: str, view: str) -> str:
    """分部隔页：双描笔压分层（无滤镜）。

    实测（2026-10-26）：滤镜习语在两条路径上结果不同——直接内联进 HTML 的
    章首题图带滤镜不落位图；走 <img> 内联的封面/隔页大图带滤镜会被 Chromium
    光栅化（p1 + 10 张隔页各多出 1 张位图）。故大图统一双描纯矢量。

    分部隔页不走滤镜（实测：封面/隔页级大图带滤镜会在印前光栅化成位图，
    章首小图不会；大图用双描笔压分层表达手绘感）。分支形状自带 fill={SOFT}——
    淡影层 suppress fill，否则只是白付一遍填充字节。文字直接叠最上层。
    """
    shapes = "".join(i for i in items if not i.startswith("<text"))
    texts = "".join(i for i in items if i.startswith("<text"))
    shadow = re.sub(r'\sfill="[^"]*"', "", shapes)
    return _svg(
        f'<g stroke-linecap="round" stroke-linejoin="round" fill="none">'
        f'<g stroke-width="1.4" opacity="0.35">{shadow}</g>'
        f'<g stroke-width="2">{shapes}</g></g>{texts}',
        label, view,
    )
# 封面墨色：站点/打印各自用 CSS 变量 --cover-ink 注入，默认墨绿。
COVER_INK = "var(--cover-ink, #123b33)"


def cover_art() -> str:
    """封面主视觉：手绘开发板俯视（Blue Pill 风格长条板）。

    习语与章首题图一致：抖动滤镜 + 双描笔压分层（主线 2 + 淡影
    1.4 opacity .35）+ 整板微倾 -1°。QFP 主芯片+四边引脚、上下排针焊盘、USB、
    晶振+负载电容、复位键、LED+限流电阻、BOOT 跳线、SWD 四针、45° 走线与过孔、
    四角固定孔。stroke 走 --cover-ink（站点亮/暗双态、打印墨绿）。丝印文字在
    滤镜组外，保持清晰且可搜索。
    """
    c = COVER_INK
    p: list[str] = []  # 板子线稿
    t: list[str] = []  # 丝印文字：不进任何变换，保持清晰

    def label(x: float, y: float, s: str, sz: float = 6) -> None:
        t.append(
            f'<text x="{x}" y="{y}" font-size="{sz}" font-family="sans-serif" fill="{c}" stroke="none">{s}</text>'
        )
    p.append('<rect x="30" y="55" width="260" height="80" rx="7" stroke-width="2"/>')
    for cx, cy in [(40, 65), (40, 125), (280, 65), (280, 125)]:
        p.append(f'<circle cx="{cx}" cy="{cy}" r="4" stroke-width="1.1"/>'
                 f'<circle cx="{cx}" cy="{cy}" r="1.4" stroke-width="1.1"/>')
    for i in range(13):
        x = round(58 + i * 16.5, 1)
        p.append(f'<rect x="{x}" y="60" width="6.5" height="6.5" stroke-width="1.1"/>'
                 f'<circle cx="{round(x+3.2,1)}" cy="63.2" r="1.1" stroke-width="1.1"/>'
                 f'<rect x="{x}" y="123.5" width="6.5" height="6.5" stroke-width="1.1"/>'
                 f'<circle cx="{round(x+3.2,1)}" cy="126.7" r="1.1" stroke-width="1.1"/>')
    p.append('<rect x="45" y="76" width="20" height="38" rx="2.5" stroke-width="2"/>'
             '<line x1="49" y1="82" x2="61" y2="82" stroke-width="1.1"/>'
             '<line x1="49" y1="108" x2="61" y2="108" stroke-width="1.1"/>')
    label(47, 74, "USB", 7)
    for bx, lbl in [(72, "BOOT0"), (86, "BOOT1")]:
        for k in range(3):
            p.append(f'<circle cx="{bx}" cy="{86+k*7}" r="1.6" stroke-width="1.1"/>')
        p.append(f'<rect x="{bx-3}" y="84.5" width="6" height="9.5" rx="1.5" stroke-width="1.1"/>')
        label(bx - 2, 104, lbl[-1], 7)
    p.append('<rect x="140" y="66" width="58" height="58" rx="3" stroke-width="2"/>'
             '<rect x="152" y="78" width="34" height="34" stroke-width="1.1" stroke-dasharray="3 2.5"/>'
             '<circle cx="146" cy="72" r="1.6" stroke-width="1.1"/>')
    for i in range(9):
        off_x = round(144.4 + i * 5.6, 1)   # 芯片体 x=140..198：上下排引脚
        off_y = round(70.4 + i * 5.6, 1)    # 芯片体 y=66..124：左右排引脚
        p.append(f'<line x1="{off_x}" y1="60" x2="{off_x}" y2="66" stroke-width="1.1"/>'
                 f'<line x1="{off_x}" y1="124" x2="{off_x}" y2="130" stroke-width="1.1"/>'
                 f'<line x1="134" y1="{off_y}" x2="140" y2="{off_y}" stroke-width="1.1"/>'
                 f'<line x1="198" y1="{off_y}" x2="204" y2="{off_y}" stroke-width="1.1"/>')
    label(158, 99, "MCU", 10)
    p.append('<rect x="212" y="72" width="24" height="13" rx="6" stroke-width="1.1"/>'
             '<line x1="204" y1="76" x2="212" y2="76" stroke-width="1.1"/>'
             '<line x1="204" y1="81" x2="212" y2="81" stroke-width="1.1"/>'
             '<rect x="212" y="88" width="6" height="3.4" stroke-width="1.1"/>'
             '<rect x="222" y="88" width="6" height="3.4" stroke-width="1.1"/>')
    label(238, 82, "8MHz", 7)
    p.append('<rect x="218" y="96" width="15" height="11" rx="2" stroke-width="1.1"/>'
             '<circle cx="225.5" cy="101.5" r="2.2" stroke-width="1.1"/>')
    label(216, 115, "RST", 7)
    p.append('<rect x="242" y="62" width="8" height="8" stroke-width="1.1"/>'
             '<line x1="246" y1="64" x2="246" y2="68" stroke-width="1.1"/>'
             '<rect x="254" y="64.5" width="7" height="3.4" stroke-width="1.1"/>')
    label(241, 58.5, "LED", 7)
    for k in range(4):
        p.append(f'<rect x="266" y="{76+k*11}" width="6.5" height="6.5" stroke-width="1.1"/>'
                 f'<circle cx="269.2" cy="{round(79.2+k*11,1)}" r="1.1" stroke-width="1.1"/>')
    label(255, 74, "SWD", 7)
    for d in ["M140 70 L116 70 L110 64 L110 63",
              "M140 90 L120 90 L114 96 L102 96 L97 91 L97 66",
              "M134 104 L124 104 L119 109 L102 109 L96 115 L96 122",
              "M198 70 L248 70 L252 66 L252 63",
              "M204 90 L232 90 L237 95 L237 112 L241 116 L241 122",
              "M160 124 L160 126", "M180 130 L180 126"]:
        p.append(f'<path d="{d}" stroke-width="1.1"/>')
    for cx, cy in [(110, 63.5), (97, 66), (96, 122), (252, 63.5), (241, 122), (160, 126.5), (180, 126.5)]:
        p.append(f'<circle cx="{cx}" cy="{cy}" r="1.7" stroke-width="1.1"/>')
    lines = "".join(p)
    body = (
        # 整板微倾 -1°：破掉"绝对水平"的机器感；双描笔压（主线 + 0.35 淡影补笔）。
        # 封面不走滤镜：实测大图带滤镜会光栅化（题图小图不会）。
        f'<g transform="rotate(-1 160 95)" fill="none" stroke="{c}" '
        f'stroke-linecap="round" stroke-linejoin="round">'
        f'<g stroke-width="1.4" opacity="0.35">{lines}</g>'
        f'<g stroke-width="2">{lines}</g></g>'
        + "".join(t)
    )
    return _svg(body, "手绘开发板", "0 30 320 130")


def part_art(part_id: str) -> str:
    """按分部 id 返回主题小插画（空字符串表示没有配图的 fallback）。"""
    if part_id == "pc":
        items = [
            f'<text x="18" y="70" font-family="monospace" font-size="44" fill="{ACCENT}">{{ }}</text>',
            f'<rect x="92" y="30" width="112" height="20" rx="3" fill="{SOFT}" stroke="{ACCENT}" stroke-width="1.6"/>',
            f'<rect x="92" y="58" width="112" height="20" rx="3" fill="{SOFT}" stroke="{ACCENT}" stroke-width="1.6"/>',
            f'<rect x="92" y="86" width="112" height="20" rx="3" fill="{SOFT}" stroke="{ACCENT}" stroke-width="1.6"/>',
            f'<path d="M150 116 V96" stroke="{WARM}" stroke-width="2.4"/>',
            f'<path d="M144 104 L150 96 L156 104" fill="none" stroke="{WARM}" stroke-width="2.4"/>',
            f'<text x="100" y="46" font-family="monospace" font-size="11" fill="{INK}">0x2000</text>',
            f'<text x="100" y="74" font-family="monospace" font-size="11" fill="{INK}">0x2004</text>',
            f'<text x="100" y="102" font-family="monospace" font-size="11" fill="{INK}">0x2008</text>',
        ]
        return _hw_part("pc", items, "C 与指针", "14 26 194 94")
    if part_id == "pb":
        blocks = []
        for i, label in enumerate(("预处理", "编译", "汇编", "链接")):
            x = 14 + i * 56
            blocks.append(f'<rect x="{x}" y="58" width="46" height="34" rx="4" fill="{SOFT}" stroke="{ACCENT}" stroke-width="1.6"/>')
            blocks.append(f'<text x="{x+23}" y="79" text-anchor="middle" font-family="sans-serif" font-size="11" fill="{INK}">{label}</text>')
            if i < 3:
                blocks.append(f'<path d="M{x+48} 75 H{x+54}" stroke="{ACCENT}" stroke-width="2"/>')
        blocks.append(f'<path d="M60 110 H180" stroke="{LIGHT}" stroke-width="2" stroke-dasharray="4 3"/>')
        blocks.append(f'<rect x="96" y="122" width="48" height="22" rx="3" fill="{SOFT}" stroke="{ACCENT}" stroke-width="1.6"/>')
        blocks.append(f'<text x="120" y="137" text-anchor="middle" font-family="monospace" font-size="11" fill="{INK}">.bin</text>')
        return _hw_part("pb", blocks, "四步构建", "10 54 222 94")
    if part_id == "ps":
        txts: list[str] = []
        cells = [_chip(84, 30, 72, 60, "F407", txts)]
        for i in range(4):
            cells.append(f'<rect x="{40+i*42}" y="116" width="34" height="20" rx="2" fill="{SOFT}" stroke="{ACCENT}" stroke-width="1.4"/>')
            cells.append(f'<text x="{57+i*42}" y="130" text-anchor="middle" font-family="monospace" font-size="10" fill="{INK}">R{i}</text>')
        return _hw_part("ps", cells + txts, "寄存器", "36 16 168 124")
    if part_id == "pf":
        # 就绪队列：优先级从高到低三条泳道，每条上挂任务块，右侧标优先级
        bars = []
        for i, (label, n) in enumerate((("高", 1), ("中", 2), ("低", 3))):
            y = 36 + i * 34
            bars.append(f'<text x="34" y="{y+14}" font-family="sans-serif" font-size="10" fill="{INK}">{label}</text>')
            bars.append(f'<path d="M52 {y+10} H206" stroke="{LIGHT}" stroke-width="1.2" stroke-dasharray="3 3"/>')
            for k in range(n):
                x = 56 + k * 40
                bars.append(f'<rect x="{x}" y="{y}" width="34" height="20" rx="3" fill="{SOFT}" stroke="{ACCENT}" stroke-width="1.6"/>')
        bars.append(f'<path d="M24 32 V146 M18 140 L24 148 L30 140" fill="none" stroke="{WARM}" stroke-width="2"/>')
        bars.append(f'<text x="130" y="150" text-anchor="middle" font-family="sans-serif" font-size="10" fill="{INK}">按优先级取下一个任务</text>')
        return _hw_part("pf", bars, "就绪队列与优先级", "16 28 200 128")
    if part_id == "pr":
        parts = [
            f'<circle cx="120" cy="44" r="12" fill="{SOFT}" stroke="{ACCENT}" stroke-width="2"/>',
            f'<path d="M112 54 L60 108 M120 56 V108 M128 54 L180 108" fill="none" stroke="{ACCENT}" stroke-width="2"/>',
        ]
        for x in (60, 120, 180):
            parts.append(f'<rect x="{x-22}" y="108" width="44" height="24" rx="4" fill="{SOFT}" stroke="{ACCENT}" stroke-width="1.6"/>')
            parts.append(f'<text x="{x}" y="124" text-anchor="middle" font-family="sans-serif" font-size="11" fill="{INK}">线程</text>')
        return _hw_part("pr", parts, "多线程", "34 28 172 108")
    if part_id == "px":
        # 同一个需求，两条实现路线：左 FreeRTOS、右 RT-Thread，中间一条分界
        parts = [
            f'<path d="M120 30 V128" stroke="{LIGHT}" stroke-width="1.4" stroke-dasharray="5 4"/>',
            f'<rect x="30" y="34" width="62" height="24" rx="4" fill="{SOFT}" stroke="{ACCENT}" stroke-width="1.6"/>',
            f'<rect x="148" y="34" width="62" height="24" rx="4" fill="{SOFT}" stroke="{ACCENT}" stroke-width="1.6"/>',
            f'<text x="61" y="50" text-anchor="middle" font-family="sans-serif" font-size="10" fill="{INK}">FreeRTOS</text>',
            f'<text x="179" y="50" text-anchor="middle" font-family="sans-serif" font-size="10" fill="{INK}">RT-Thread</text>',
        ]
        for i, label in enumerate(("任务模型", "IPC", "内存管理")):
            y = 74 + i * 20
            parts.append(f'<path d="M92 {y} H44 M148 {y} H196" stroke="{ACCENT}" stroke-width="1.2"/>')
            parts.append(
                f'<text x="120" y="{y+3.5}" text-anchor="middle" font-family="sans-serif" '
                f'font-size="9" fill="{INK}">{label}</text>'
            )
        parts.append(f'<text x="120" y="140" text-anchor="middle" font-family="sans-serif" font-size="10" fill="{INK}">逐项对照与选型</text>')
        return _hw_part("px", parts, "双 OS 逐项对照", "24 28 192 120")
    if part_id == "pe":
        # 波纹以芯片上方 (120,50) 为圆心向上展开；芯片尺寸与其它图一致（48×48）
        txts: list[str] = []
        parts = [_chip(96, 64, 48, 48, "S3", txts)]
        for r in (13, 22, 31):
            parts.append(
                f'<path d="M{120-r} 50 A{r} {r} 0 0 1 {120+r} 50" '
                f'fill="none" stroke="{ACCENT}" stroke-width="1.8"/>'
            )
        parts.append(f'<circle cx="120" cy="50" r="3.2" fill="{WARM}"/>')
        parts.append(
            f'<text x="120" y="136" text-anchor="middle" font-family="sans-serif" '
            f'font-size="9.5" fill="{INK}">Wi-Fi / BLE 上网</text>'
        )
        # viewBox 宽高比与其它分部图保持一致（约 1.6:1），否则同一 CSS 宽度下这张会被放大
        return _hw_part("pe", parts + txts, "无线连接", "40 14 160 128")
    if part_id == "pg":
        txts: list[str] = []
        parts = [
            _chip(30, 46, 56, 56, "F4", txts),
            _chip(154, 46, 56, 56, "V1", txts),
            f'<path d="M92 64 H148 M142 58 L150 64 L142 70" fill="none" stroke="{ACCENT}" stroke-width="2.2"/>',
            f'<path d="M148 88 H92 M98 82 L90 88 L98 94" fill="none" stroke="{WARM}" stroke-width="2.2"/>',
        ]
        return _hw_part("pg", parts + txts, "双系对照", "16 32 208 84")
    if part_id == "pl":
        # 一条闭合回路：GPIO → 限流电阻 → LED → GND，引脚与导线真正相接
        parts = [
            f'<path d="M34 112 H70" stroke="{ACCENT}" stroke-width="2"/>',
            f'<rect x="70" y="104" width="30" height="16" rx="2" fill="{SOFT}" stroke="{ACCENT}" stroke-width="1.6"/>',
            f'<text x="85" y="132" text-anchor="middle" font-family="sans-serif" font-size="9" fill="{INK}">220Ω</text>',
            f'<path d="M100 112 H118" stroke="{ACCENT}" stroke-width="2"/>',
            f'<path d="M118 100 L118 124 L140 112 Z" fill="{SOFT}" stroke="{ACCENT}" stroke-width="1.6"/>',
            f'<path d="M140 100 V124" stroke="{ACCENT}" stroke-width="2"/>',
            f'<path d="M140 112 H176" stroke="{ACCENT}" stroke-width="2"/>',
            f'<path d="M176 104 V120 M180 107 V117 M184 110 V114" stroke="{ACCENT}" stroke-width="2"/>',
            f'<text x="36" y="104" font-family="sans-serif" font-size="9" fill="{INK}">PF9</text>',
            f'<text x="172" y="134" font-family="sans-serif" font-size="9" fill="{INK}">GND</text>',
            f'<path d="M132 92 L138 80 M146 96 L158 90 M126 90 L124 78" stroke="{WARM}" stroke-width="2"/>',
        ]
        return _hw_part("pl", parts, "点亮 LED 的回路", "26 72 170 70")
    if part_id == "pj":
        txts: list[str] = []
        parts = [
            _chip(24, 52, 48, 48, "F4", txts),
            _chip(168, 52, 48, 48, "S3", txts),
            f'<path d="M76 76 H164" stroke="{ACCENT}" stroke-width="2.4"/>',
        ]
        for x in (96, 116, 136):
            parts.append(f'<circle cx="{x}" cy="76" r="4" fill="{WARM}"/>')
        parts.append(f'<text x="120" y="126" text-anchor="middle" font-family="sans-serif" font-size="11" fill="{INK}">双板项目</text>')
        return _hw_part("pj", parts + txts, "双板综合项目", "10 38 220 95")
    if part_id == "pa":
        # 人机结对：模型气泡（方角尖尾）给代码且埋雷，人气泡（圆角圆尾）回以对账勾
        parts = [
            f'<path d="M28 26 H116 Q124 26 124 34 V66 Q124 74 116 74 H60 L44 88 L48 74 H28 Q20 74 20 66 V34 Q20 26 28 26 Z" fill="{SOFT}" stroke="{ACCENT}" stroke-width="2"/>',
            f'<path d="M34 42 h34 M34 52 h44 M34 62 h26" stroke="{ACCENT}" stroke-width="1.6"/>',
            f'<path d="M98 40 l8 8 M106 40 l-8 8" stroke="{WARM}" stroke-width="2"/>',
            f'<path d="M152 34 H212 Q220 34 220 42 V64 Q220 72 212 72 H176 L162 84 L166 72 H152 Q144 72 144 64 V42 Q144 34 152 34 Z" fill="{SOFT}" stroke="{ACCENT}" stroke-width="2"/>',
            f'<path d="M156 52 l6 7 l14 -16" fill="none" stroke="{ACCENT}" stroke-width="2.4"/>',
            f'<path d="M128 46 H140 M136 42 L142 46 L136 50" fill="none" stroke="{ACCENT}" stroke-width="1.8"/>',
            f'<path d="M140 58 H128 M132 54 L126 58 L132 62" fill="none" stroke="{ACCENT}" stroke-width="1.8"/>',
        ]
        return _hw_part("pa", parts, "人机结对：模型给代码，人给对账", "16 22 208 70")
    return ""
