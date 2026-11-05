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
    s = Svg(W, H, "I2C 一次完整读写事务",
            "START → 7 位地址 + R/W → ACK → 数据字节 → ACK → STOP")
    s.header(tag="07 I2C", tag_color=T.GREEN)

    # 写 0xA5 到地址 0x3C：7 位地址是 0111100，不是 8 位写法 0x78
    cells = [
        ("ST", "", T.RED),
        ("0", "A6", T.VIOLET), ("1", "A5", T.VIOLET), ("1", "A4", T.VIOLET),
        ("1", "A3", T.VIOLET), ("1", "A2", T.VIOLET), ("0", "A1", T.VIOLET),
        ("0", "A0", T.VIOLET),
        ("0", "W", T.CYAN), ("0", "AK", T.GREEN),
        ("1", "D7", T.AMBER), ("0", "D6", T.AMBER), ("1", "D5", T.AMBER),
        ("0", "D4", T.AMBER), ("0", "D3", T.AMBER), ("1", "D2", T.AMBER),
        ("0", "D1", T.AMBER), ("1", "D0", T.AMBER),
        ("0", "AK", T.GREEN), ("SP", "", T.RED),
    ]
    x0, cw = 28, 42
    s.text(28, 96, "SDA 位（0x3C = 0111100，写 0xA5；数据在 SCL 为低时才允许变化）",
           size=12, fill=T.MUTED)
    for i, (bit, tag, color) in enumerate(cells):
        x = x0 + i * cw
        s.rect(x, 108, cw - 4, 44, fill=T.PANEL, stroke=color, rx=4)
        s.text(x + (cw - 4) / 2, 126, bit, size=13, anchor="middle",
               fill=color, weight="700", mono=True)
        if tag:
            s.text(x + (cw - 4) / 2, 144, tag, size=9, anchor="middle",
                   fill=T.DIM)
    s.text(28, 172, "ST/SP：SCL 为高时 SDA 下降=START、上升=STOP。AK 是第 9 拍，由从机拉低。",
           size=11, fill=T.MUTED)
    # SCL 示意：数据位期间先低后高，SDA 在低电平区变化
    s.text(28, 198, "SCL", size=12, fill=T.CYAN, mono=True)
    scl = []
    for bit, tag, _c in cells:
        if tag in ("",):
            scl += [1, 1]
        else:
            scl += [0, 1]
    s.waveform(28, 206, 20 * cw, 36, scl, color=T.CYAN, sw=2)

    # 右侧要点
    s.rect(40, 356, 400, 132, fill=T.PANEL, stroke=T.STROKE, rx=8)
    s.text(58, 380, "为什么必须加上拉电阻", size=12.5, fill=T.TEXT, weight="700")
    for i, t in enumerate([
        "I2C 是开漏输出：只能拉低，不能拉高",
        "上拉电阻决定上升沿速度与功耗",
        "3.3 V / 400 kHz：4.7 kΩ 是安全默认值",
        "总线电容 > 200 pF 时减小到 2.2 kΩ",
    ]):
        s.text(58, 404 + i * 20, "· " + t, size=11, fill=T.MUTED)

    s.rect(460, 356, 400, 132, fill=T.PANEL, stroke=T.STROKE, rx=8)
    s.text(478, 380, "地址陷阱：0x3C 还是 0x78？", size=12.5, fill=T.TEXT,
           weight="700")
    for i, t in enumerate([
        "7 位 0x3C 左移 1 位 = 8 位写地址 0x78",
        "HAL 的 DevAddress 要传 0x3C<<1，不是 0x3C",
        "扫描器若打印 0x78，右移才是手册上的 0x3C",
        "总线上所有设备地址不能重复",
    ]):
        s.text(478, 404 + i * 20, "· " + t, size=11, fill=T.MUTED)

    s.rect(40, 500, 820, 30, fill=T.BG2, stroke=T.STROKE, rx=8)
    s.text(58, 520, "总线卡死自救：把 SCL 当普通 IO 手动发 9 个脉冲 + 一个 STOP，"
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

    # 移动的 bit
    for i in range(4):
        s.circle(426, 150, 4.5, fill=T.CYAN, cls=f"bit{i}")
    s.add_style("\n".join(
        css_kf(f"bit{i}-mv", [("0%", "transform:translateX(0);opacity:0"),
                              ("15%", "opacity:1"), ("85%", "opacity:1"),
                              ("100%", "transform:translateX(148px);opacity:0")])
        + f".bit{i}{{animation:bit{i}-mv 1.6s linear infinite {i * 0.4:.1f}s;}}"
        for i in range(4)))

    # SCK 波形
    s.text(60, 168, "0xA5 高位先出", size=11, fill=T.CYAN)
    s.text(556, 168, "0x69 同时移入", size=11, fill=T.GREEN)
    s.text(40, 224, "SCK（8 个上升沿，CPOL=0 / CPHA=0，空闲为低）", size=11,
           fill=T.MUTED)
    s.axis(40, 236, 800, 60)
    s.waveform(40, 240, 800, 54, [0, 1] * 8, color=T.AMBER, sw=2)
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
    s = Svg(W, H, "CAN 非破坏性仲裁：ID 越小优先级越高",
            "三个节点同时发送，逐位比较：显性 0 覆盖隐性 1，输了的一方自动退出且不丢帧")
    s.header(tag="13 CAN", tag_color=T.ORANGE)

    # 11 位 ID，左边是 bit10。0x100=0b00100000000，比 0x200/0x300 更小
    ids = [("节点 A", "0x100", "00100000000", T.CYAN),
           ("节点 B", "0x200", "01000000000", T.GREEN),
           ("节点 C", "0x300", "01100000000", T.VIOLET)]
    bits = 11
    cw = 62
    x0 = 130
    # 表头
    s.text(x0 + bits * cw / 2, 92, "11 位标识符（标准帧）", size=12,
           anchor="middle", fill=T.MUTED)
    for j in range(bits):
        s.text(x0 + j * cw + cw / 2, 112, str(10 - j), size=9,
               anchor="middle", fill=T.DIM)

    for i, (name, hexid, bstr, color) in enumerate(ids):
        y = 132 + i * 62
        s.text(40, y + 24, name, size=12, fill=color, weight="600")
        s.text(40, y + 42, hexid, size=11, mono=True, fill=T.MUTED)
        for j, ch in enumerate(bstr):
            x = x0 + j * cw
            win = (ch == "0") or (i == 0)
            s.rect(x, y, cw - 6, 40, fill=T.PANEL2 if win else T.PANEL,
                   stroke=T.STROKE, rx=4)
            s.text(x + (cw - 6) / 2, y + 26, ch, size=14, anchor="middle",
                   fill=color if win else T.DIM, mono=True, cls=f"c{i}")
        s.text(x0 + bits * cw + 8, y + 26, "仲裁中" if i == 0 else "退出",
               size=11, fill=T.GREEN if i == 0 else T.RED)
    # 高亮逐位扫描 + 失败节点变暗
    s.add_style(_seq_flash("c", 3, period=5.0, window=0.7, peak=1, rest=0.55))

    s.rect(40, 326, 820, 96, fill=T.BG2, stroke=T.STROKE, rx=8)
    s.text(58, 350, "为什么叫「非破坏性」仲裁", size=12.5, fill=T.TEXT,
           weight="700")
    for i, t in enumerate([
        "B、C 在 bit9 发隐性 1，读回 A 的显性 0，立刻退出；0x100 最小所以 A 赢",
        "退出的节点不会丢失数据，等总线空闲后自动重发（硬件自动完成）",
        "因此 CAN 不会像以太网那样「碰撞后随机退避」，实时性可预测",
    ]):
        s.text(58, 374 + i * 20, "· " + t, size=11, fill=T.MUTED)

    s.title_block(40, 442, "一帧数据还包含什么", color=T.CYAN)
    items = [("SOF", "1 位起始"), ("ID", "11/29 位标识符"),
             ("RTR/IDE", "帧类型与格式"), ("DLC", "数据长度 0~8"),
             ("Data", "0~8 字节"), ("CRC", "15 位 + 1 位界定符"),
             ("ACK 槽", "接收方拉低应答"), ("EOF", "7 位隐性结束")]
    for i, (k, v) in enumerate(items):
        x = 40 + (i % 4) * 208
        y = 456 + (i // 4) * 42
        s.rect(x, y, 196, 34, fill=T.PANEL, stroke=T.STROKE, rx=8)
        s.text(x + 12, y + 15, k, size=11.5, fill=T.CYAN, mono=True)
        s.text(x + 12, y + 29, v, size=10, fill=T.MUTED)
    s.text(40, 544, "位填充：连续 5 个相同位后必须插入 1 个相反位，"
                    "保证接收方能持续同步；差分电平 CANH−CANL ≈ 2 V（显性）/ 0 V（隐性）",
           size=10.5, fill=T.MUTED)
    s.footer("波特率 = 1 / (tq × (1 + BS1 + BS2))，采样点建议放在 75%~87.5% 处")
    return s


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

