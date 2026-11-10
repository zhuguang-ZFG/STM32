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



def tls_prereqs():
    f = Fig("ch27-tls-prereqs",
            "TLS：能握手不等于安全 / a successful handshake is not security")

    # ---- 上：四个前提门 ----
    f.text(84, 126, "TLS 客户端四个前提：缺一个，身份或保密就塌一角",
           size=22, color=MUTED)
    gates = [(84, "受信 CA", "证书链要能验到根"),
             (352, "主机名匹配", "set_hostname 一致"),
             (620, "可靠随机数", "CTR_DRBG 真实熵源"),
             (888, "可信时间", "证书有效期才判得了")]
    for x, title, sub in gates:
        f.rect(x, 168, 180, 110, color=BLUE_D, fill=WHITE, sw=2.6)
        f.multi(x + 14, 196, [title, sub], size=19, color=BLUE_D, weight="bold", lh=30)

    # ---- 中：VERIFY_NONE 陷阱 ----
    f.rect(84, 320, 984, 170, color=RED, fill=WHITE, sw=2.6)
    f.text(104, 352, "陷阱：认证模式关掉（VERIFY_NONE）", size=22, color=RED, weight="bold")
    f.multi(104, 388,
            ["握手照样成功 —— 但只证明加密通道建立了",
             "服务器身份没有任何人担保：仿冒服务器也能握手成功",
             "时间没建立之前，证书有效期根本判断不了"],
            size=19, color=INK, lh=30)

    # ---- 下：生产不变量 ----
    f.rect(84, 530, 984, 160, color=GREEN_D, fill=WHITE, sw=2.6)
    f.multi(104, 560,
            ["生产不变量：VERIFY_REQUIRED + set_hostname 验证证书链",
             "CTR_DRBG 由真实熵源播种（硬件 RNG 也要健康检测）",
             "私钥不进 Git、不进日志；量产设备唯一凭据，规划吊销与轮换",
             "证书错误别无限快速重试；区分 close_notify / reset / 超时"],
            size=19, color=INK, lh=30)
    f.text(104, 748, "真正的证据：认证模式、验证结果、协商版本与对端身份 —— 不是端口",
           size=20, color=GREEN_D, weight="bold")
    return f


def four_ledgers():
    f = Fig("ch27-four-ledgers",
            "网络四本账：每个数都能复算 / four ledgers")
    panels = [
        ("内存账", BLUE_D, ["RAM_net = 描述符 + RX 池 + TX 池",
                           "　+ lwIP 堆 + socket 缓冲",
                           "　+ TLS 峰值 + 离线队列"]),
        ("吞吐账", GREEN_D, ["goodput = 应用载荷字节",
                            "　　　　　÷ 观测时间",
                            "只算应用收到的，不算重传"]),
        ("可靠账", RED, ["丢失/重试率 = 重试或丢失消息",
                        "　　　　　　÷ 尝试发送消息",
                        ""]),
        ("恢复账", AMBER_STROKE, ["恢复时间 = 首次应用成功时刻",
                                 "　　　　 − 故障注入时刻",
                                 ""]),
    ]
    for i, (t, c, lines) in enumerate(panels):
        col, row = i % 2, i // 2
        x, y = 84 + col * 504, 128 + row * 214
        f.rect(x, y, 480, 194, color=c, fill=WHITE, sw=2.6)
        f.text(x + 20, y + 40, t, size=23, color=c, weight="bold")
        f.multi(x + 20, y + 84, lines, size=19, color=INK, lh=34)
    f.panel(84, 574, 984, 92, AMBER_FILL)
    f.rect(84, 574, 984, 92, color=AMBER_STROKE, sw=2.6)
    f.text(576, 610, "报峰值，不报平均", size=22, color=INK, anchor="middle", weight="bold")
    f.text(576, 646, "最小空闲堆 · 最小剩余栈 · 最大 pbuf · 最大并发连接 · TLS 握手峰值 · 最坏 DNS/TCP/TLS 延迟",
           size=17, color=INK, anchor="middle")
    f.text(576, 712, "故障注入至少：拔线 · 交换机重启 · DHCP 租约变化 · DNS 失败",
           size=18, color=MUTED, anchor="middle")
    f.text(576, 744, "服务端重启 · 证书错误 · 弱网丢包",
           size=18, color=MUTED, anchor="middle")
    return f


def lab_ladder():
    f = Fig("ch27-lab-ladder",
            "四个递进实验：每级多证明一层 / each lab proves one more layer")
    labs = [("A  ARP 与 ping", "证明 L1–L3", GREEN_D,
             ["PHY ID、link、速率、双工", "拔线 10 s 后回到可 ping"]),
            ("B  TCP echo 与分帧", "证明字节流边界", BLUE_D,
             ["1、MSS−1、MSS、MSS+1 长度", "1000 次消息无错位"]),
            ("C  DHCP · DNS · MQTT", "证明发现与会话", AMBER_STROKE,
             ["DORA；退避有上限", "QoS 1 重复靠幂等键消除"]),
            ("D  TLS 与 24 h", "证明身份与长期运行", RED,
             ["坏证书、错主机名必须失败", "堆、pbuf、栈不随重连恶化"])]
    for i, (t, tag, c, lines) in enumerate(labs):
        x, y = 84 + i * 170, 616 - i * 152
        f.rect(x, y, 470, 132, color=c, fill=WHITE, sw=2.6)
        f.text(x + 18, y + 36, t, size=21, color=c, weight="bold")
        f.text(x + 452, y + 36, tag, size=16, color=c, anchor="end")
        f.multi(x + 18, y + 76, lines, size=17, color=INK, lh=30)
        if i:
            f.arrow(x + 60, y + 150, x + 60, y + 134, color=MUTED, bend=0.0, head=8)
    f.multi(84, 150, ["前一级没过，", "不进下一级"], size=20, color=MUTED, lh=32)
    return f


def at_offload():
    f = Fig("ch27-at-offload",
            "AT 模组把 TCP/IP 移走了，状态机还在 MCU 这边 / the stack moved out")
    f.text(84, 130, "UART 只是串口，不是网络边界；模组里的栈再全，下面这些仍要固件自己兜住",
           size=20, color=MUTED)

    # left: module box
    f.rect(84, 168, 420, 300, color=MUTED, fill=WHITE, sw=2.6)
    f.text(294, 206, "AT 模组（ESP-01 / 4G Cat.1）", size=20, color=MUTED,
           anchor="middle", weight="bold")
    f.multi(116, 250, ["TCP / UDP / TLS 终止", "DNS、DHCP 在模组内", "socket 由 AT 命令开", "模组自己重连运营商网"],
            size=18, color=INK, lh=34)
    f.text(294, 444, "模组复位 = 全部状态丢失", size=17, color=RED, anchor="middle",
           weight="bold")

    # right: MCU keeps
    f.rect(648, 168, 420, 300, color=GREEN_D, fill=WHITE, sw=2.6)
    f.text(858, 206, "MCU 必须保留", size=20, color=GREEN_D, anchor="middle",
           weight="bold")
    f.multi(680, 250, ["命令超时 + 重试上限", "分帧缓存（不依赖一次 recv）", "业务幂等键（QoS 1 去重）",
                       "离线队列上限 + 掉网不发送", "喂狗：网络任务在推进"],
            size=18, color=INK, lh=34)

    # uart link
    f.line(504, 300, 648, 300, color=BLUE_D, sw=3.4, amp=0.8)
    f.line(504, 336, 648, 336, color=BLUE_D, sw=3.4, amp=0.8)
    f.text(576, 284, "TX / RX", size=16, color=BLUE_D, anchor="middle", weight="bold")
    f.text(576, 366, "没有「连接」只有字节", size=15, color=MUTED, anchor="middle")

    boxes = [
        ("掉线检测", "靠 PINGREQ/应用心跳自己的超时，不是 UART 断线", BLUE_D),
        ("恢复对账", "重连后先对幂等键与队列水位，再继续发", RED),
        ("模组 ≠ 看门狗", "模组活着 ≠ 业务链路活着", AMBER_STROKE),
    ]
    y = 540
    for t, s, c in boxes:
        f.rect(84, y, 984, 56, color=c, fill=WHITE, sw=2.2, double=False)
        f.text(108, y + 37, t, size=19, color=c, weight="bold")
        f.text(268, y + 37, s, size=18, color=INK)
        y += 72
    return f


def sendall_loop():
    f = Fig("ch27-sendall-loop",
            "send_all：一个截止点，四个出口 / one deadline, four exits")
    # deadline banner
    f.rect(56, 122, 1040, 56, color=BLUE_D, fill=WHITE, sw=2.6)
    f.text(W / 2, 158, "deadline = sys_now() + 2000 —— 调用处只算一次，循环里绝不重置"
           "（差值强转 int32_t 可跨回绕）", size=19, color=INK, anchor="middle")

    # left: loop steps
    steps = [
        ("① send(fd, buf+sent, len−sent, MSG_DONTWAIT)", "非阻塞：可能只收下一部分字节", BLUE_D),
        ("② n > 0 → sent += n，回到 ①", "EINTR 同样回到 ①，不换截止点", GREEN_D),
        ("③ EAGAIN / EWOULDBLOCK → 算剩余", "remaining = (int32_t)(deadline − sys_now())", BLUE_D),
        ("④ remaining ≤ 0？", "是 → TIMEOUT；否 → select(fd, writable, remaining)", AMBER_STROKE),
        ("⑤ select 返回", "ready>0 回 ①；ready==0 → TIMEOUT；非 EINTR 错误 → ERROR", GREEN_D),
    ]
    y = 206
    for t, s, c in steps:
        f.rect(56, y, 600, 66, color=c, fill=WHITE, sw=2.4)
        f.text(80, y + 30, t, size=19, color=c, weight="bold")
        f.text(80, y + 56, s, size=16, color=INK)
        y += 82

    # right: four exits
    exits = [
        ("SEND_ALL_OK", "全部字节已交给内核", GREEN_D),
        ("SEND_ALL_TIMEOUT", "本地窗口 2 s 没推进；≠ 服务端已处理", AMBER_STROKE),
        ("SEND_ALL_CLOSED", "对端关闭连接", RED),
        ("SEND_ALL_ERROR", "非 EINTR 的 errno，交给上层定恢复", RED),
    ]
    y = 206
    for t, s, c in exits:
        f.rect(700, y, 396, 82, color=c, fill=WHITE, sw=2.4)
        f.text(724, y + 34, t, size=18, color=c, weight="bold")
        f.text(724, y + 64, s, size=15, color=INK)
        y += 98
    f.arrow(668, 380, 692, 380, color=BLUE_D, sw=2.6)
    f.text(680, 360, "四种", size=14, color=BLUE_D, anchor="middle")

    # bottom: business ack note
    f.rect(56, 640, 1040, 64, color=RED, fill=WHITE, sw=2.4)
    f.text(W / 2, 680, "要「业务已落盘」：应用层 ACK 回带同一 sequence，服务端按幂等键去重",
           size=20, color=RED, anchor="middle", weight="bold")
    return f


FIGS = {
    "ch27-at-offload": at_offload,
    "ch27-sendall-loop": sendall_loop,
    "ch27-four-ledgers": four_ledgers,
    "ch27-lab-ladder": lab_ladder,
    "ch27-rmii-signals": rmii_signals,
    "ch27-cache-dma": cache_dma,
    "ch27-api-context": api_context,
    "ch27-tcp-framing": tcp_framing,
    "ch27-backoff": backoff,
    "ch27-pbuf-chain": pbuf_chain,
    "ch27-tls-prereqs": tls_prereqs,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))
