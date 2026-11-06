# -*- coding: utf-8 -*-
"""ch27 knowledge-track figures (facts from docs/27-网络与协议栈.md)."""
from hd import *


def rmii_signals():
    f = Fig("ch27-rmii-signals", "RMII 先对清这几根线 / check wires first")
    cells = [
        ("REF_CLK", "50 MHz — 时钟来自 PHY 还是 MCU 输出", GREEN_D),
        ("TXD0/1 + TX_EN", "复用脚 · 速度等级 · 与 PHY 端对应", GREEN_D),
        ("RXD0/1 + CRS_DV", "PHY link 之后有没有帧活动", BLUE_D),
        ("MDC + MDIO", "能否稳定读 PHY ID 与 BSR link 位", BLUE_D),
        ("NRST + strap", "PHY 地址 · 上下拉别被别的器件抢", AMBER_STROKE),
        ("磁性件 + RJ45", "中心抽头供电 · 端接 · ESD · 线序", MUTED),
    ]
    bw, bh, gap = 520, 96, 20
    x0, y0 = 56, 130
    for i, (name, note, c) in enumerate(cells):
        x = x0 + (i % 2) * (bw + gap + 8)
        y = y0 + (i // 2) * (bh + gap)
        f.rect(x, y, bw, bh, color=c, fill=WHITE)
        f.text(x + 26, y + 40, name, size=26, color=c, weight="bold")
        f.text(x + 26, y + 74, note, size=21, color=INK)
    # bottom notes
    f.rect(56, 560, 520, 196, color=RED, fill=WHITE)
    f.htext(316, 602, "link LED 只是线索", size=26, color=RED, anchor="middle",
            weight="bold", hl=True)
    f.multi(316, 646, ["PHY 亮灯 ≠ 验收：还要读 OUI/型号、", "BSR link 位、协商速率与双工，",
                       "并确认 MAC 同步同一速率"], size=22, color=INK, lh=36,
            anchor="middle")
    f.rect(600, 560, 520, 196, color=RED, fill=WHITE)
    f.htext(860, 602, "MDIO 读不到 PHY", size=26, color=RED, anchor="middle",
            weight="bold")
    f.multi(860, 646, ["先停在硬件层，复位释放、strap、", "PHY 地址逐项核对 —",
                       "改 IP 修不了不存在的 PHY"], size=22, color=INK, lh=36,
            anchor="middle")
    return f


def cache_dma():
    f = Fig("ch27-cache-dma", "Ethernet DMA 看见的内存 / who owns the buffer")
    # left: TX
    f.htext(300, 132, "TX：CPU → DMA", size=27, color=GREEN_D, anchor="middle",
            weight="bold")
    f.rect(110, 156, 400, 150, color=GREEN, fill=WHITE)
    f.multi(134, 200, ["CPU 写完 payload", "先 clean 整条", "Cache line（32 B）"],
            size=25, color=GREEN_D, lh=37)
    f.text(310, 348, "DMA 读到的一定是最新", size=23, color=MUTED, anchor="middle")
    # right: RX
    f.htext(852, 132, "RX：DMA → CPU", size=27, color=BLUE_D, anchor="middle",
            weight="bold")
    f.rect(642, 156, 420, 150, color=BLUE, fill=WHITE)
    f.multi(666, 200, ["DMA 写完之后", "对收包范围", "invalidate，再给 lwIP"],
            size=25, color=BLUE_D, lh=37)
    f.text(852, 348, "CPU 不会读到旧 line", size=23, color=MUTED, anchor="middle")
    # danger strip
    f.panel(110, 420, 952, 118, AMBER_FILL)
    f.rect(110, 420, 952, 118, color=AMBER_STROKE, sw=3.0)
    f.text(W / 2, 462, "危险：对没按 32 B 对齐的窄区间直接 invalidate",
           size=27, color=RED, anchor="middle", weight="bold")
    f.text(W / 2, 502, "首尾 line 里别的脏变量会一起丢 — 缓冲区独占并对齐", size=24,
           color=INK, anchor="middle")
    # DTCM note
    f.rect(110, 586, 952, 108, color=RED, fill=WHITE)
    f.multi(140, 630, ["Ethernet DMA 到不了 0x20000000 的 DTCM",
                       "描述符与缓冲放 D1/D2 SRAM，map 文件里核对地址"],
            size=25, color=RED, lh=39)
    return f


def api_context():
    f = Fig("ch27-api-context", "lwIP 三套 API 的上下文 / call it from where")
    cols = [
        ("raw callback", GREEN_D, ["NO_SYS 主循环", "或 tcpip_thread", "零拷贝空间大", "自己维护状态机"]),
        ("Netconn", BLUE_D, ["应用任务", "邮箱连 tcpip_thread", "阻塞式", "ST 官方示例"]),
        ("BSD socket", AMBER_STROKE, ["应用任务", "socket / connect", "send / recv / select", "可移植应用层"]),
    ]
    cw, gap = 336, 30
    x0 = (W - (cw * 3 + gap * 2)) / 2
    y0 = 132
    for i, (name, c, lines) in enumerate(cols):
        x = x0 + i * (cw + gap)
        f.rect(x, y0, cw, 210, color=c, fill=WHITE)
        f.htext(x + cw / 2, y0 + 46, name, size=28, color=c, anchor="middle",
                weight="bold", hl=(c == AMBER_STROKE))
        f.multi(x + 30, y0 + 92, lines, size=24, color=INK, lh=36)
    f.panel(110, 408, 952, 106, AMBER_FILL)
    f.rect(110, 408, 952, 106, color=AMBER_STROKE, sw=3.0)
    f.text(W / 2, 452, "禁止：在 Ethernet IRQ 或定时器 IRQ 里直接调 raw API",
           size=26, color=RED, anchor="middle", weight="bold")
    f.text(W / 2, 492, "tcp_write() / udp_send() 只能出现在上面三类上下文里",
           size=23, color=INK, anchor="middle")
    f.text(W / 2, 566, "IRQ 只收集事件、归还描述符、唤醒正确的上下文",
           size=24, color=MUTED, anchor="middle")
    f.text(W / 2, 608, "LWIP_ASSERT_CORE_LOCKED() 开发期保留；锁不能从中断拿",
           size=23, color=MUTED, anchor="middle")
    return f


def tcp_framing():
    f = Fig("ch27-tcp-framing", "TCP 是字节流，帧自己定 / define the frame")
    # send vs recv
    f.htext(300, 134, "一次 send() ≠ 一次 recv()", size=27, color=RED,
            anchor="middle", weight="bold", hl=True)
    f.multi(300, 182, ["4 KB 消息可能分多次到", "两条小消息可能一次读到"],
            size=24, color=INK, lh=38, anchor="middle")
    # header sketch
    f.rect(96, 250, 560, 372, color=BLUE, fill=WHITE)
    rows = [
        ("magic 0x534E", "先确认是我们的协议", BLUE_D),
        ("ver + type", "版本与消息类型", BLUE_D),
        ("payload_len", "网络字节序；先读长度", GREEN_D),
        ("sequence", "业务序号，回执对账", GREEN_D),
        ("payload", "…", INK),
        ("CRC32", "TLS 也不能替代校验", AMBER_STROKE),
    ]
    yy = 286
    for name, note, c in rows:
        f.rect(120, yy, 232, 42, color=c, fill=WHITE)
        f.text(236, yy + 30, name, size=23, color=c, anchor="middle",
               weight="bold")
        f.text(510, yy + 30, note, size=20, color=MUTED, anchor="middle")
        yy += 55
    # right notes
    f.multi(880, 300, ["应用协议至少定义：", "魔数 / 版本 / 长度", "类型 / 序号 / 完整性",
                       "", "只有应用层规则", "能把字节流还原成消息"],
            size=24, color=INK, lh=40, anchor="middle")
    return f


def backoff():
    f = Fig("ch27-backoff", "断网恢复：有上限的退避 / bounded backoff")
    f.panel(216, 120, 720, 84, AMBER_FILL)
    f.rect(216, 120, 720, 84, color=AMBER_STROKE, sw=3.0)
    f.text(W / 2, 158, "backoff = min(B_max, B_base × 2^n) + jitter",
           size=29, color=INK, anchor="middle", weight="bold")
    f.text(W / 2, 196, "n 有上限，成功稳定运行一段时间后才清零", size=22,
           color=MUTED, anchor="middle")
    rules = [
        ("link down 就别再建 socket", GREEN_D),
        ("DNS / TCP / TLS / MQTT 分别计数", BLUE_D),
        ("一个总 deadline，不无限阻塞", GREEN_D),
        ("喂狗条件 = 网络任务在推进", BLUE_D),
        ("离线队列限字节与时间", AMBER_STROKE),
    ]
    bw, gap = 620, 0
    y = 258
    for i, (t, c) in enumerate(rules):
        yy = y + i * 76
        f.rect(271, yy, 620, 58, color=c, fill=WHITE)
        f.text(300, yy + 38, t, size=25, color=INK)
        f.circle(258, yy + 29, 13, color=c, fill=WHITE, sw=2.4)
        f.text(258, yy + 37, str(i + 1), size=20, color=c, anchor="middle",
               weight="bold")
    f.text(W / 2, 700, "旧命令重放前查有效期、设备状态与幂等键", size=24,
           color=RED, anchor="middle", weight="bold")
    return f


def pbuf_chain():
    f = Fig("ch27-pbuf-chain", "pbuf 是所有权：链上走，引用跟着走 / pbuf is ownership")
    # top: one message split across a chain
    f.text(W / 2, 128, "应用想发的「HELLO WORLD 123」，lwIP 交出来的可能是一条 pbuf 链",
           size=25, color=MUTED, anchor="middle")
    chain = [("pbuf 1", "HE", GREEN_D), ("pbuf 2", "LLO ", BLUE_D),
             ("pbuf 3", "WORLD 123", AMBER_STROKE)]
    x = 96
    for i, (name, data, c) in enumerate(chain):
        f.rect(x, 152, 300, 128, color=c, fill=WHITE)
        f.text(x + 150, 190, name, size=26, color=c, anchor="middle",
               weight="bold")
        f.text(x + 150, 240, f"payload「{data}」", size=23, color=INK,
               anchor="middle")
        if i < 2:
            f.arrow(x + 306, 216, x + 366, 216, color=INK, bend=0.0, head=13)
            f.text(x + 336, 198, "next", size=20, color=MUTED, anchor="middle")
        x += 360
    f.text(W / 2, 322, "想当一段连续内存用就先拷出来；直接引用就把链走完",
           size=24, color=INK, anchor="middle")
    # left: reference rules
    f.rect(96, 356, 560, 260, color=GREEN, fill=WHITE)
    f.htext(376, 396, "引用规则", size=27, color=GREEN_D, anchor="middle",
            weight="bold")
    f.multi(126, 442, ["收到 pbuf：你持有一份引用，数据活着",
                       "转手（交给别的任务/队列）：",
                       "　引用跟着走，别再替它 free",
                       "自己用完：pbuf_free() 一次，恰好一次"],
            size=24, color=INK, lh=37)
    # right: two failure modes
    f.rect(680, 356, 376, 260, color=RED, fill=WHITE)
    f.htext(868, 396, "两种死法", size=27, color=RED, anchor="middle",
            weight="bold", hl=True)
    f.multi(708, 442, ["漏 free：几小时后堆耗尽，",
                       "　新连接建不起来",
                       "多 free：当场崩，",
                       "　现场是无辜的路过代码"],
            size=24, color=INK, lh=37)
    f.panel(96, 640, 960, 84, AMBER_FILL)
    f.rect(96, 640, 960, 84, color=AMBER_STROKE, sw=3.0)
    f.text(W / 2, 692, "谁持引用谁负责 free——交出去就别再碰", size=28, color=INK,
           anchor="middle", weight="bold")
    return f


FIGS = {
    "ch27-rmii-signals": rmii_signals,
    "ch27-cache-dma": cache_dma,
    "ch27-api-context": api_context,
    "ch27-tcp-framing": tcp_framing,
    "ch27-backoff": backoff,
    "ch27-pbuf-chain": pbuf_chain,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))
