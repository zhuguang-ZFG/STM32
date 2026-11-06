#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""通信类动画：UART 帧、I2C 事务、SPI 移位、CAN 仲裁、USB 枚举。"""

from __future__ import annotations

from svgkit import Svg, T, anim_fade, anim_flow, anim_tx, css_kf

W, H = 900, 620

REDUCED = "@media (prefers-reduced-motion: reduce){*{animation:none!important}}"


def _step_highlight(prefix: str, n: int, period=6.0, window=0.22,
                    peak=0.35, rest=0.06) -> str:
    css = []
    step = 100.0 / n
    for i in range(n):
        a = i * step
        b = min(a + step * window, 99.2)
        name = f"{prefix}{i}-hl"
        css.append(
            f"@keyframes {name}{{0%,{a:.2f}%{{opacity:{rest}}}"
            f"{a + 0.25:.2f}%,{b:.2f}%{{opacity:{peak}}}"
            f"{min(b + 0.25, 100):.2f}%,100%{{opacity:{rest}}}}}"
        )
        css.append(f".{prefix}{i}{{animation:{name} {period}s linear infinite;}}")
    return "\n".join(css)


def _seq_flash(prefix: str, n: int, period=5.0, window=0.55,
               peak=1.0, rest=0.22) -> str:
    css = []
    step = 100.0 / n
    for i in range(n):
        a = i * step
        b = min(a + step * window, 99.2)
        name = f"{prefix}{i}-sq"
        css.append(
            f"@keyframes {name}{{0%,{a:.2f}%{{opacity:{rest}}}"
            f"{a + 0.3:.2f}%,{b:.2f}%{{opacity:{peak}}}"
            f"{min(b + 0.3, 100):.2f}%,100%{{opacity:{rest}}}}}"
        )
        css.append(f".{prefix}{i}{{animation:{name} {period}s linear infinite;}}")
    return "\n".join(css)




def uart_frame() -> Svg:
    s = Svg(W, H, "UART 帧结构：一个字节是怎么发出去的",
            "以 115200 8N1 为例：1 起始位 + 8 数据位 + 0 校验 + 1 停止位")
    s.header(tag="06 串口", tag_color=T.CYAN)

    bits = [0] + [1, 0, 1, 0, 0, 1, 0, 1] + [1]      # 0xA5，LSB 先发
    names = ["起始", "D0", "D1", "D2", "D3", "D4", "D5", "D6", "D7", "停止"]
    cw = 80
    x0 = 40
    for i, (b, nm) in enumerate(zip(bits, names)):
        x = x0 + i * cw
        color = T.RED if b == 0 else T.GREEN
        s.rect(x, 92, cw - 6, 46, fill=T.PANEL, stroke=T.STROKE, rx=8)
        s.text(x + (cw - 6) / 2, 112, nm, size=12, anchor="middle",
               fill=T.MUTED)
        s.text(x + (cw - 6) / 2, 132, str(b), size=15, anchor="middle",
               fill=color, weight="700", mono=True)
        s.rect(x, 92, cw - 6, 46, fill=color, rx=8, opacity=0.16, cls=f"b{i}")
    s.add_style(_seq_flash("b", len(bits), period=4.4, peak=0.42, rest=0.1))

    # 波形
    s.axis(40, 176, 800, 90, ylabel="3.3V")
    s.text(40, 168, "TX 线电平（空闲为高）", size=11, fill=T.MUTED)
    s.waveform(40, 176, 800, 90, bits, color=T.CYAN, sw=2)
    for i in range(len(bits) + 1):
        s.line(x0 + i * cw - 3, 176, x0 + i * cw - 3, 266, stroke=T.GRID, sw=1,
               dash="3 4")
    s.line(40, 176, 40, 266, stroke=T.RED, sw=1.5, cls="cursor")
    s.add_style(anim_tx(".cursor", dur="4.4s", x1=0, x2=800))

    # 时间标注
    s.text(40, 292, "每格 = 1 位 = 1/115200 s ≈ 8.68 µs；整帧 10 位 ≈ 86.8 µs。"
                    "上图是 0xA5，低位 D0 先发（和 SPI 相反）",
           size=12, fill=T.AMBER)

    # 波特率表
    s.title_block(40, 330, "波特率与误差", color=T.GREEN)
    rows = [
        ("9600", "104.2 µs", "±2% 即可", "与老设备通信、RS485 长线"),
        ("115200", "8.68 µs", "±2.5%", "最常用：串口打印、模块通信"),
        ("921600", "1.085 µs", "±1.5%", "高速数据采集，注意线材与干扰"),
        ("2000000", "0.5 µs", "±1%", "F4/H7 才稳，建议改用 USB/SPI"),
    ]
    s.rect(40, 344, 820, 128, fill=T.BG2, stroke=T.STROKE, rx=8)
    heads = ["波特率", "位时间", "允许误差", "典型用途"]
    for i, hd in enumerate(heads):
        s.text(60 + i * 200, 364, hd, size=11.5, fill=T.CYAN, weight="600")
    for r, row in enumerate(rows):
        for i, v in enumerate(row):
            s.text(60 + i * 200, 384 + r * 18, v, size=11,
                   fill=T.MUTED if i else T.TEXT, mono=(i < 2))
    s.text(60, 458, "16 倍过采样：USARTDIV = 39.0625，BRR = (39<<4)|1 = 0x271",
           size=11, fill=T.GREEN)

    # 三种收发方式
    s.rect(40, 484, 820, 58, fill=T.PANEL, stroke=T.STROKE, rx=8)
    s.text(58, 506, "别把 BRR 背成 fCK/波特率；阻塞适合打印，中断适合指令，DMA+IDLE 适合连收",
           size=12, fill=T.TEXT, weight="700")
    s.text(58, 526, "数值上 0x271 碰巧等于 72000000/115200，是因为小数分到了低 4 位",
           size=11, fill=T.MUTED)
    s.footer("常见坑：TX/RX 接反、没共地、波特率不匹配（乱码）、"
             "电平不是 3.3 V（用 USB-TTL 而不是 RS232）")
    return s


# --------------------------------------------------------------------------- I2C 事务


def i2c_transaction() -> Svg:
    """静态时序图：contract test 要求这张没有 <style>（PDF 版直接读第一帧）。

    动起来的是配套的 assets/gif/i2c-timing.gif；这里把同一个事务画成一张
    能打印的图：SDA / SCL 都画出来，采样点标在 SCL 高电平中间。
    """
    s = Svg(W, H, "I2C 一次完整写事务：SDA 的一个字节怎么走完",
            "START → 7 位地址 + W → ACK → 数据字节 → ACK → STOP；点上标出每一拍的采样位置")
    s.header(tag="07 I2C", tag_color=T.GREEN)

    # 写 0xA5 到地址 0x3C：7 位地址是 0111100，不是 8 位写法 0x78
    cells = [
        ("START", "", T.RED),
        ("0", "A6", T.VIOLET), ("1", "A5", T.VIOLET), ("1", "A4", T.VIOLET),
        ("1", "A3", T.VIOLET), ("1", "A2", T.VIOLET), ("0", "A1", T.VIOLET),
        ("0", "A0", T.VIOLET),
        ("0", "W", T.CYAN), ("0", "ACK", T.GREEN),
        ("1", "D7", T.AMBER), ("0", "D6", T.AMBER), ("1", "D5", T.AMBER),
        ("0", "D4", T.AMBER), ("0", "D3", T.AMBER), ("1", "D2", T.AMBER),
        ("0", "D1", T.AMBER), ("1", "D0", T.AMBER),
        ("0", "ACK", T.GREEN), ("STOP", "", T.RED),
    ]
    n = len(cells)
    x0, cw, pad = 30, 40, 4

    phases = [("START", 0, 1, T.RED), ("地址 7 位 + W", 1, 9, T.VIOLET),
              ("ACK", 9, 10, T.GREEN), ("数据 0xA5", 10, 18, T.AMBER),
              ("ACK", 18, 19, T.GREEN), ("STOP", 19, 20, T.RED)]
    for label, a, b, color in phases:
        xa, xb = x0 + a * cw, x0 + b * cw
        s.rect(xa + 1, 76, xb - xa - 2, 18, fill=T.PANEL, stroke=color, rx=4)
        s.text((xa + xb) / 2, 89, label, size=10, anchor="middle", fill=color,
               weight="600")

    for i, (bit, tag, color) in enumerate(cells):
        x = x0 + i * cw
        s.rect(x, 104, cw - pad, 44, fill=T.PANEL, stroke=color, rx=4)
        s.text(x + (cw - pad) / 2, 122, bit,
               size=13 if tag else 9, anchor="middle", fill=color,
               weight="700", mono=bool(tag))
        if tag:
            s.text(x + (cw - pad) / 2, 140, tag, size=9, anchor="middle",
                   fill=T.DIM)

    # SDA 与 SCL 的真实形状：SDA 只在 SCL 低时变；START/STOP 在 SCL 高时跳变
    sda_hi, sda_lo = 232, 268
    scl_hi, scl_lo = 312, 348
    levels = [1] + [int(c[0]) if c[1] else (0 if c[0] == "STOP" else 1)
                    for c in cells[1:]]

    d = [f"M {x0} {sda_hi}"]
    d.append(f"H {x0 + cw * 0.55:.1f}")
    d.append(f"L {x0 + cw * 0.55 + 6:.1f} {sda_lo}")      # START：SCL 高时 SDA 下降
    for i in range(1, n - 1):
        xa = x0 + i * cw + 2
        yy = sda_hi if levels[i] else sda_lo
        d.append(f"L {xa:.1f} {yy}")
        d.append(f"H {x0 + (i + 1) * cw:.1f}")
    last = x0 + (n - 1) * cw
    d.append(f"H {last + cw * 0.45:.1f}")
    d.append(f"L {last + cw * 0.45 + 6:.1f} {sda_hi}")     # STOP：SCL 高时 SDA 上升
    s.path(" ".join(d), stroke=T.VIOLET, sw=2)
    s.text(x0 + 2, sda_hi - 10, "SDA", size=11, fill=T.VIOLET, weight="700",
           mono=True)

    d = [f"M {x0} {scl_hi}"]
    d.append(f"H {x0 + cw:.1f}")                            # START 期间 SCL 为高
    for i in range(1, n - 1):
        xa = x0 + i * cw
        d.append(f"L {xa:.1f} {scl_lo}")
        d.append(f"H {xa + cw * 0.45:.1f}")
        d.append(f"L {xa + cw * 0.45:.1f} {scl_hi}")
        d.append(f"H {xa + cw:.1f}")
    d.append(f"H {x0 + n * cw:.1f}")
    s.path(" ".join(d), stroke=T.CYAN, sw=2)
    s.text(x0 + 2, scl_hi - 10, "SCL", size=11, fill=T.CYAN, weight="700",
           mono=True)

    # 采样点：一个点对应一位，位置在 SCL 高电平中间
    for i in range(1, n - 1):
        sx = x0 + i * cw + cw * 0.78
        sy = sda_hi if levels[i] else sda_lo
        s.circle(sx, sy, 3.4, fill=T.TEXT)
        s.line(sx, sy, sx, 306, stroke=T.GRID, sw=1)

    s.text(30, 372, "SDA 只能在 SCL 为低的窗口里变；START / STOP 反过来，必须在 SCL 高时跳变。"
                    "第 9 拍 ACK 是接收方把 SDA 拉低，不是发送方。",
           size=11, fill=T.MUTED)

    s.rect(40, 392, 400, 116, fill=T.PANEL, stroke=T.STROKE, rx=8)
    s.text(58, 416, "为什么必须加上拉电阻", size=12.5, fill=T.TEXT, weight="700")
    for i, t in enumerate([
        "I2C 是开漏输出：只能拉低，不能拉高",
        "上拉电阻决定上升沿速度与功耗",
        "3.3 V / 400 kHz：4.7 kΩ 是安全默认值",
        "总线电容 > 200 pF 时减小到 2.2 kΩ",
    ]):
        s.text(58, 440 + i * 19, "· " + t, size=11, fill=T.MUTED)

    s.rect(460, 392, 400, 116, fill=T.PANEL, stroke=T.STROKE, rx=8)
    s.text(478, 416, "地址陷阱：0x3C 还是 0x78？", size=12.5, fill=T.TEXT,
           weight="700")
    for i, t in enumerate([
        "7 位 0x3C 左移 1 位 = 8 位写地址 0x78",
        "HAL 的 DevAddress 要传 0x3C<<1，不是 0x3C",
        "扫描器若打印 0x78，右移才是手册上的 0x3C",
        "总线上所有设备地址不能重复",
    ]):
        s.text(478, 440 + i * 19, "· " + t, size=11, fill=T.MUTED)

    s.rect(40, 520, 820, 30, fill=T.BG2, stroke=T.STROKE, rx=8)
    s.text(58, 540, "总线卡死自救：把 SCL 当普通 IO 手动发 9 个脉冲 + 一个 STOP，"
                    "再 HAL_I2C_DeInit / Init 重新初始化", size=11, fill=T.AMBER)
    s.footer("标准 100 kHz / 快速 400 kHz / 快速+ 1 MHz；SCL 高电平时间与上拉阻值强相关")
    return s



# --------------------------------------------------------------------------- SPI 移位


def spi_transfer() -> Svg:
    s = Svg(W, H, "SPI 全双工：两个移位寄存器在环形交换",
            "主机发一个字节的同时，从机也在发一个字节 —— 这就是「全双工」")
    s.header(tag="08 SPI", tag_color=T.VIOLET)

    # 主机寄存器
    s.text(60, 100, "主机移位寄存器", size=12.5, fill=T.CYAN, weight="600")
    s.text(620, 100, "从机移位寄存器", size=12.5, fill=T.GREEN, weight="600")
    mbits = [1, 0, 1, 0, 0, 1, 0, 1]
    sbits = [0, 1, 1, 0, 1, 0, 0, 1]
    for i, b in enumerate(mbits):
        s.rect(60 + i * 44, 112, 38, 38, fill=T.PANEL2, stroke=T.CYAN, rx=4)
        s.text(79 + i * 44, 137, str(b), size=14, anchor="middle", fill=T.CYAN,
               mono=True)
    for i, b in enumerate(sbits):
        s.rect(556 + i * 42, 112, 36, 38, fill=T.PANEL2, stroke=T.GREEN, rx=4)
        s.text(574 + i * 42, 137, str(b), size=14, anchor="middle", fill=T.GREEN,
               mono=True)

    # 数据线
    s.arrow(420, 150, 554, 150, color=T.CYAN, sw=2, cls="mosi")
    s.text(499, 142, "MOSI 主 → 从", size=11, anchor="middle", fill=T.CYAN)
    s.arrow(554, 172, 420, 172, color=T.GREEN, sw=2, cls="miso")
    s.text(499, 192, "MISO 从 → 主", size=11, anchor="middle", fill=T.GREEN)
    s.add_style(anim_flow(".mosi", dur="1.4s", dash="8 12", shift=-20))
    s.add_style(anim_flow(".miso", dur="1.4s", dash="8 12", shift=-20))

    # 移动的 bit：一拍一个，3.4 s 走完 4 个，够慢才数得清
    PERIOD = 3.4
    for i in range(4):
        s.circle(426, 150, 4.5, fill=T.CYAN, cls=f"bit{i}")
    s.add_style("\n".join(
        css_kf(f"bit{i}-mv", [("0%", "transform:translateX(0);opacity:0"),
                              ("12%", "opacity:1"), ("84%", "opacity:1"),
                              ("96%", "transform:translateX(148px);opacity:0"),
                              ("100%", "transform:translateX(148px);opacity:0")])
        + f".bit{i}{{animation:bit{i}-mv {PERIOD}s ease-in-out infinite {i * PERIOD / 8:.2f}s;}}"
        for i in range(4)))

    # SCK 波形
    s.text(60, 168, "0xA5 高位先出", size=11, fill=T.CYAN)
    s.text(556, 168, "0x69 同时移入", size=11, fill=T.GREEN)
    s.text(40, 224, "SCK（8 个上升沿，CPOL=0 / CPHA=0，空闲为低）", size=11,
           fill=T.MUTED)
    s.axis(40, 236, 800, 60)
    s.waveform(40, 240, 800, 54, [0, 1] * 8, color=T.AMBER, sw=2)
    # 8 个采样点跟着拍子亮：上升沿采样，不是下降沿
    for k in range(8):
        s.circle(40 + 50 * (2 * k + 1), 248, 4.2, fill=T.AMBER, cls=f"sm{k}")
    s.add_style("\n".join(
        css_kf(f"sm{k}-on", [("0%", "opacity:0.15"),
                             (f"{k / 8 * 100:.2f}%", "opacity:0.15"),
                             (f"{k / 8 * 100 + 2.0:.2f}%", "opacity:1"),
                             (f"{k / 8 * 100 + 9.0:.2f}%", "opacity:0.35"),
                             ("100%", "opacity:0.15")])
        + f".sm{k}{{animation:sm{k}-on {PERIOD}s linear infinite;}}"
        for k in range(8)))
    s.text(40, 318, "Mode 0：上升沿采样，下降沿移位。SPI 高位先出（和 UART 相反）。"
                    "想读 1 字节必须同时发 1 字节，没数据就发 0xFF。",
           size=11, fill=T.MUTED)

    # 模式表
    s.title_block(40, 356, "CPOL / CPHA 四种模式（选错就读不到数据）", color=T.CYAN)
    s.rect(40, 368, 500, 120, fill=T.BG2, stroke=T.STROKE, rx=8)
    heads = ["模式", "CPOL", "CPHA", "空闲电平", "采样边沿"]
    for i, hd in enumerate(heads):
        s.text(60 + i * 96, 390, hd, size=11, fill=T.CYAN, weight="600")
    modes = [
        ("Mode 0", "0", "0", "低", "第 1 个边沿（上升）"),
        ("Mode 1", "0", "1", "低", "第 2 个边沿（下降）"),
        ("Mode 2", "1", "0", "高", "第 1 个边沿（下降）"),
        ("Mode 3", "1", "1", "高", "第 2 个边沿（上升）"),
    ]
    for r, m in enumerate(modes):
        for i, v in enumerate(m):
            s.text(60 + i * 96, 412 + r * 20, v, size=10.5,
                   fill=T.TEXT if i == 0 else T.MUTED, mono=(i < 3))

    s.rect(560, 368, 300, 120, fill=T.PANEL, stroke=T.STROKE, rx=8)
    s.text(578, 392, "常见器件的模式", size=12, fill=T.TEXT, weight="700")
    for i, t in enumerate(["W25Q64 / W25Q128：Mode 0 或 3",
                           "ST7789 / ILI9341：Mode 0",
                           "nRF24L01：Mode 0",
                           "MCP2515 / 多数 ADC：Mode 0"]):
        s.text(578, 414 + i * 18, "· " + t, size=10.5, fill=T.MUTED)

    s.rect(40, 500, 820, 30, fill=T.BG2, stroke=T.STROKE, rx=8)
    s.text(58, 520, "读 ID 全 0xFF：MISO 悬空或片选没拉低；全 0x00：时钟没出来（NSS/BR 配置错）",
           size=11, fill=T.AMBER)
    s.footer("NSS 建议软件控制：HAL_SPI_Transmit 前后手动拉低/拉高对应 GPIO")
    return s



# --------------------------------------------------------------------------- CAN 仲裁


def can_arbitration() -> Svg:
    canvas = Svg(W, H, "CAN：发 1 却读到 0，就退出仲裁",
                 "标准数据帧 · 11 位 ID · 高位先比 · 这里只画仲裁逻辑，不按实际位时间播放")
    canvas.header(tag="13 CAN", tag_color=T.ORANGE)
    origin, cell_width = 150, 60
    nodes = (
        ("A", "0x100", "00100000000", T.CYAN),
        ("B", "0x200", "01000000000", T.GREEN),
        ("C", "0x300", "01100000000", T.VIOLET),
    )
    canvas.text(40, 96, "三节点同时开始；bit9 是第一次不同的一位。", size=19, weight="700")
    canvas.rect(origin + cell_width - 4, 107, cell_width + 2, 335,
                fill=T.AMBER, opacity=0.12, rx=4)
    for column in range(11):
        canvas.text(origin + column * cell_width + 25, 126, str(10 - column),
                    size=14, anchor="middle", fill=T.MUTED, mono=True)
    for row, (name, identifier, bit_string, color) in enumerate(nodes):
        vertical = 144 + row * 72
        canvas.text(40, vertical + 23, f"节点 {name}", size=17, fill=color, weight="700")
        canvas.text(40, vertical + 44, identifier, size=14, mono=True)
        for column, bit in enumerate(bit_string):
            horizontal = origin + column * cell_width
            listening = row > 0 and column > 1
            canvas.rect(horizontal, vertical, 50, 46, fill=T.PANEL,
                        stroke=T.STROKE, rx=4)
            canvas.text(horizontal + 25, vertical + 30, "—" if listening else bit,
                        size=21, fill=T.MUTED if listening else color,
                        mono=True, anchor="middle", weight="700")
        if row > 0:
            canvas.text(824, vertical + 29, "转接收", size=15, fill=T.RED)
    canvas.text(40, 382, "总线", size=18, fill=T.CYAN, weight="700")
    canvas.text(40, 402, "显性 0 优先", size=13, fill=T.MUTED)
    for column, bit in enumerate(nodes[0][2]):
        horizontal = origin + column * cell_width
        canvas.rect(horizontal, 360, 50, 46, fill=T.PANEL2,
                    stroke=T.CYAN, rx=4)
        canvas.text(horizontal + 25, 391, bit, size=21, fill=T.CYAN,
                    anchor="middle", weight="700", mono=True)
    canvas.rect(origin - 3, 355, 56, 56, fill="none", stroke=T.CYAN,
                sw=2, rx=4, cls="bit-scan moving")
    canvas.rect(origin + cell_width - 3, 211, 56, 128, fill="none", stroke=T.RED,
                sw=2, rx=4, cls="loss-mark moving", opacity=0)
    canvas.line(origin + cell_width + 25, 412, origin + cell_width + 25, 436,
                stroke=T.AMBER, sw=2)
    canvas.text(40, 472, "bit9：A 发 0，B/C 发 1；总线是 0，B/C 退出并改为接收。",
                size=18, weight="700")
    canvas.text(40, 507, "A 继续发送，帧没有被破坏；B/C 失去仲裁不产生错误帧。", size=17)
    canvas.text(40, 539, "自动重发开启时，B/C 等总线空闲后再竞争；关闭时需软件重新请求发送。",
                size=15, fill=T.MUTED)
    positions = []
    for column in range(11):
        positions.append(f"{column * 8}%{{transform:translateX({column * cell_width}px)}}")
    positions.append("100%{transform:translateX(600px)}")
    canvas.add_style(
        "@keyframes bit-scan{" + "".join(positions) + "}"
        ".bit-scan{animation:bit-scan 9s steps(1,end) infinite}"
        "@keyframes loss-mark{0%,11%{opacity:0}12%,100%{opacity:1}}"
        ".loss-mark{animation:loss-mark 9s steps(1,end) infinite}"
        "@media (prefers-reduced-motion:reduce){*{animation:none!important}.moving{display:none}}"
        "@media print{*{animation:none!important}.moving{display:none}}"
    )
    canvas.footer("RM0008 Rev 21 §24.7 · 自绘逻辑示意；不表示位填充、电平幅值或总线测量结果")
    return canvas


# --------------------------------------------------------------------------- USB 枚举


def usb_enumeration() -> Svg:
    s = Svg(W, H, "USB 设备枚举：从地址 0 到可用",
            "沿着请求与回应往下看，第一笔没有正确回应的请求就是排查起点")
    s.header(tag="14 USB", tag_color=T.BLUE)

    s.rect(40, 84, 150, 380, fill=T.PANEL, stroke=T.CYAN, rx=8)
    s.text(115, 112, "主机", size=14, anchor="middle", fill=T.CYAN,
           weight="700")
    s.text(115, 134, "PC / 树莓派", size=11, anchor="middle", fill=T.MUTED)
    s.text(115, 156, "Host", size=11, anchor="middle", fill=T.MUTED)
    s.rect(710, 84, 150, 380, fill=T.PANEL, stroke=T.GREEN, rx=8)
    s.text(785, 112, "设备", size=14, anchor="middle", fill=T.GREEN,
           weight="700")
    s.text(785, 134, "STM32", size=11, anchor="middle", fill=T.MUTED)
    s.text(785, 156, "Device", size=11, anchor="middle", fill=T.MUTED)

    steps = [
        ("① 检测到设备", "全速：D+ 经 1.5 kΩ 上拉，主机据此识别速率", T.RED, "d2h"),
        ("② 总线复位", "D+ 与 D− 同时拉低（SE0）≥ 10 ms", T.ORANGE, "h2d"),
        ("③ 读前 8 字节", "地址仍是 0，只为拿到 bMaxPacketSize0", T.AMBER, "both"),
        ("④ SET_ADDRESS", "部分主机会先再复位一次；随后分配地址 1~127", T.GREEN, "h2d"),
        ("⑤ 读完整设备描述符", "改用新地址读取 18 字节，拿到 VID / PID", T.CYAN, "both"),
        ("⑥ 读配置描述符", "先读 9 字节，再按 wTotalLength 读完", T.BLUE, "both"),
        ("⑦ SET_CONFIGURATION", "选中配置，CDC / HID 开始工作", T.VIOLET, "h2d"),
    ]
    period = 5.6
    window = 100 / len(steps)
    motion_css = []
    for i, (title, sub, color, flow) in enumerate(steps):
        y = 96 + i * 52
        s.rect(210, y, 480, 42, fill=T.PANEL, stroke=T.STROKE, rx=8,
               cls=f"usb-row{i}")
        s.rect(210, y, 4, 42, fill=color, rx=2)
        s.text(226, y + 18, title, size=12, fill=T.TEXT, weight="600")
        s.text(226, y + 34, sub, size=10, fill=T.MUTED)
        direction = {"d2h": "设备 → 主机", "h2d": "主机 → 设备",
                     "both": "请求 ↔ 回应"}[flow]
        s.text(674, y + 18, direction, size=9.2, anchor="end", fill=color,
               weight="600")

        start = i * window
        end = start + window * .84
        motion_css.append(css_kf(
            f"usb-row{i}-on",
            [("0%,100%", f"stroke:{T.STROKE}"),
             (f"{start:.2f}%,{end:.2f}%", f"stroke:{color}")]))
        motion_css.append(
            f".usb-row{i}{{animation:usb-row{i}-on {period}s linear infinite;}}")

        def packet(name, x, dx, begin, finish):
            s.circle(x, y + 4, 4.5, fill=color, stroke=T.BG, sw=1.5,
                     opacity=0, cls=name)
            motion_css.append(css_kf(
                f"{name}-mv",
                [("0%,100%", "opacity:0;transform:translateX(0)"),
                 (f"{begin:.2f}%", "opacity:0;transform:translateX(0)"),
                 (f"{begin + .7:.2f}%", "opacity:1;transform:translateX(0)"),
                 (f"{finish:.2f}%", f"opacity:1;transform:translateX({dx}px)"),
                 (f"{finish + .7:.2f}%", f"opacity:0;transform:translateX({dx}px)")]))
            motion_css.append(
                f".{name}{{animation:{name}-mv {period}s ease-in-out infinite;}}")

        if flow == "d2h":
            packet(f"usb-p{i}", 682, -464, start + 1, end - 1)
        elif flow == "h2d":
            packet(f"usb-p{i}", 218, 464, start + 1, end - 1)
        else:
            middle = start + window * .43
            packet(f"usb-p{i}a", 218, 464, start + .7, middle)
            packet(f"usb-p{i}b", 682, -464, middle + .7, end - .7)
    s.add_style("\n".join(motion_css))

    s.rect(40, 476, 400, 54, fill=T.BG2, stroke=T.STROKE, rx=8)
    s.text(58, 500, "描述符按层级展开", size=12, fill=T.TEXT, weight="700")
    s.text(58, 518, "设备 → 配置 → 接口 → 端点，主机逐层索取", size=10.5,
           fill=T.MUTED)
    s.rect(460, 476, 400, 54, fill=T.BG2, stroke=T.STROKE, rx=8)
    s.text(478, 500, "CDC 还是 HID？", size=12, fill=T.TEXT, weight="700")
    s.text(478, 518, "CDC 传字节流；HID 传固定格式的报告", size=10.5,
           fill=T.MUTED)
    s.footer("枚举失败先查：48 MHz 时钟、D+ 上拉、第一笔无回应的请求、描述符总长度")
    return s




# --------------------------------------------------------------------------- Ethernet / lwIP / MQTT


def network_packet_journey() -> Svg:
    s = Svg(W, H, "MQTT 消息穿过 STM32 网络栈",
            "每层只管自己的语义：消息 · 字节流 · 寻址 · 帧 · 物理")
    s.header(title="网络包旅程：从 APP 到 PHY 的证据链",
             subtitle="mechanism · FA-002 continuous-line · MQTT QoS1 over TLS/TCP",
             tag="27 网络", tag_color=T.CYAN)
    css = []
    layers = [
        ("APP", "{temp:23.6}", "业务序号 / 幂等键", T.PINK),
        ("MQTT", "PUBLISH · QoS1", "至少一次 ≠ 业务一次", T.VIOLET),
        ("TLS", "record + tag", "CA · SNI · 时间 · RNG", T.AMBER),
        ("TCP", "seq · ACK · RTX", "字节流无消息边界", T.GREEN),
        ("IP", "src/dst · TTL", "地址 · 掩码 · 网关", T.CYAN),
        ("Eth", "dst MAC · type · FCS", "ARP / 二层广播域", T.BLUE),
        ("DMA", "desc → RMII → PHY", "SRAM 对齐 · Cache 一致", T.ORANGE),
    ]
    x, y0, bw, bh, gap = 48, 92, 500, 52, 8
    for i, (name, payload, boundary, color) in enumerate(layers):
        y = y0 + i * (bh + gap)
        s.rect(x, y, bw, bh, fill=T.PANEL, stroke=color, rx=8)
        s.rect(x, y, 78, bh, fill=T.BG2, stroke=color, rx=8)
        s.text(x + 39, y + 30, name, size=12, anchor="middle", fill=color, weight="700")
        s.text(x + 96, y + 20, payload, size=11, mono=True, fill=T.TEXT, weight="600")
        s.text(x + 96, y + 40, boundary, size=10, fill=T.MUTED)
        s.rect(x, y, bw, bh, fill=color, rx=8, opacity=0.1, cls=f"net{i}")
        if i < len(layers) - 1:
            s.arrow(x + bw / 2, y + bh + 1, x + bw / 2, y + bh + gap - 1,
                    color=T.CYAN, sw=2, head=5, cls="net-flow")
    css.append(_step_highlight("net", 7, period=7.0, window=0.12, peak=0.3))
    css.append(anim_flow(".net-flow", dur="1.0s", dash="4 7", shift=-11))
    s.rect(572, 92, 288, 200, fill=T.BG2, stroke=T.STROKE, rx=8)
    s.text(590, 118, "链路证据顺序", size=13, fill=T.TEXT, weight="700")
    proof = [
        ("1", "PHY link", "读 BSR，不只看 LED", T.ORANGE),
        ("2", "ARP", "who-has / is-at", T.BLUE),
        ("3", "IP", "ping≠业务可达", T.CYAN),
        ("4", "TCP", "SYN→SYN/ACK→ACK", T.GREEN),
        ("5", "TLS/MQTT", "握手 + CONNACK", T.VIOLET),
    ]
    for i, (n, key, note, color) in enumerate(proof):
        yy = 148 + i * 28
        s.circle(600, yy - 4, 9, fill=color)
        s.text(600, yy, n, size=9, anchor="middle", fill=T.BG, weight="700")
        s.text(620, yy, key, size=11, mono=True, fill=color, weight="700")
        s.text(700, yy, note, size=10, fill=T.MUTED)
    s.rect(572, 310, 288, 220, fill=T.PANEL, stroke=T.RED, rx=8)
    s.text(590, 338, "五个不能混为一谈", size=13, fill=T.TEXT, weight="700")
    warnings = [
        ("TCP ACK", "≠ 业务已落盘"),
        ("MQTT QoS1", "至少一次，要幂等"),
        ("ping 通", "≠ DNS/TLS/MQTT OK"),
        ("link up", "≠ DMA/Cache/IP OK"),
        ("收到一段", "≠ 流式分帧完成"),
    ]
    for i, (claim, truth) in enumerate(warnings):
        yy = 368 + i * 30
        s.text(590, yy, "×", size=13, fill=T.RED, weight="700")
        s.text(610, yy, claim, size=11, mono=True, fill=T.TEXT)
        s.text(710, yy, truth, size=10, fill=T.MUTED)
    s.rect(48, 530, 500, 36, fill=T.BG2, stroke=T.STROKE, rx=8)
    s.text(60, 554, "分层验收：PHY → ARP/IP → TCP → TLS → MQTT → 业务语义",
           size=12, fill=T.TEXT, weight="700")
    css.append(REDUCED)
    s.add_style("\n".join(css))
    s.footer(note="自绘矢量动画 · FA-002 · 网络分层证据链，非抓包截图",
             label="自绘矢量动画 · STM32 知识轨")
    return s



def uart_idle_dma() -> Svg:
    s = Svg(W, H, "UART + DMA + IDLE：两类接收契约",
            "Size=首个未写位置；交给业务的永远是新增字节区间")
    s.header(title="UART IDLE+DMA：契约 A（Normal）与契约 B（Circular）",
             subtitle="mechanism · FA-002 continuous-line · 附录 A · 115200 8N1",
             tag="附录 A", tag_color=T.CYAN)
    css = []
    s.title_block(40, 92, "① 总线：字节阵到达，间隙 ≥1 帧触发 IDLE（约 86.8 μs @115200）",
                  color=T.AMBER)
    for i, lab in enumerate(["D0", "D1", "D2", "D3", "D4", "…", "IDLE"]):
        x = 48 + i * 78
        col = T.RED if lab == "IDLE" else T.CYAN
        s.rect(x, 118, 70, 44, fill=T.PANEL, stroke=col, rx=8)
        s.text(x + 35, 146, lab, size=13, anchor="middle", fill=col, weight="700", mono=True)
        s.rect(x, 118, 70, 44, fill=col, rx=8, opacity=0.12, cls=f"by{i}")
    css.append(_step_highlight("by", 7, period=5.6, window=0.12, peak=0.32))
    s.title_block(40, 184, "② DMA 缓冲 cap=128：Size = 首个未写位置（1..128）", color=T.GREEN)
    s.rect(40, 210, 820, 56, fill=T.PANEL, stroke=T.GREEN, rx=8)
    s.rect(40, 210, 280, 56, fill=T.GREEN, opacity=0.18, rx=8, cls="buf")
    s.text(60, 244, "写满区 [0, Size)", size=13, fill=T.GREEN, weight="700")
    s.text(340, 244, "Size=7 例", size=13, fill=T.TEXT, mono=True, weight="700")
    s.text(480, 244, "HT@64 仅契约 B 使用", size=12, fill=T.MUTED)
    s.text(720, 244, "127", size=12, fill=T.DIM, mono=True)
    css.append(anim_fade(".buf", dur="2.4s", a=0.1, b=0.35))
    s.rect(40, 288, 400, 200, fill=T.BG2, stroke=T.CYAN, rx=8)
    s.text(56, 316, "契约 A · Normal", size=14, fill=T.CYAN, weight="700")
    for i, line in enumerate([
        "ReceiveToIdle_DMA 后立即关 HT",
        "IDLE（或 TC）→ RxEventCallback(Size)",
        "复制 [0, Size) 进软件队列",
        "回调内重新武装，并再次关 HT",
        "适合：不定长命令帧",
    ]):
        s.text(56, 348 + i * 24, f"· {line}", size=12, fill=T.TEXT)
        s.rect(48, 336 + i * 24, 6, 16, fill=T.CYAN, rx=2, cls=f"ca{i}")
    css.append(_seq_flash("ca", 5, period=5.0, window=0.45, peak=1.0, rest=0.25))
    s.rect(460, 288, 400, 200, fill=T.BG2, stroke=T.VIOLET, rx=8)
    s.text(476, 316, "契约 B · Circular", size=14, fill=T.VIOLET, weight="700")
    for i, line in enumerate([
        "开 HT、TC、IDLE 三个来源",
        "new = (Size − old_pos) mod cap",
        "只交新增区间给业务",
        "再 old_pos = Size",
        "适合：连续流 / 高吞吐",
    ]):
        s.text(476, 348 + i * 24, f"· {line}", size=12, fill=T.TEXT)
        s.rect(468, 336 + i * 24, 6, 16, fill=T.VIOLET, rx=2, cls=f"cb{i}")
    css.append(_seq_flash("cb", 5, period=5.0, window=0.45, peak=1.0, rest=0.25))
    s.rect(40, 508, 820, 48, fill=T.PANEL, stroke=T.RED, rx=8)
    s.text(56, 538, "陷阱：把 Size 当长度却忘了 Circular 取模；HT 回调里做重活超过半缓冲窗口。",
           size=13, fill=T.RED, weight="700")
    css.append(REDUCED)
    s.add_style("\n".join(css))
    s.footer(note="自绘矢量动画 · FA-002 · UART IDLE+DMA 契约，非逻辑分析仪实拍",
             label="自绘矢量动画 · STM32 知识轨 · 附录 A")
    return s



ALL = [uart_frame, i2c_transaction, spi_transfer, can_arbitration,
       usb_enumeration, network_packet_journey, uart_idle_dma]

NAMES = {
    "uart_frame": "uart-frame",
    "i2c_transaction": "i2c-transaction",
    "spi_transfer": "spi-transfer",
    "can_arbitration": "can-arbitration",
    "usb_enumeration": "usb-enumeration",
    "network_packet_journey": "network-packet-journey",
    "uart_idle_dma": "uart-idle-dma",
}

