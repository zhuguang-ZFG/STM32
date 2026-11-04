# -*- coding: utf-8 -*-
"""Embed ch27 handraw knowledge-track PNGs (ZH+EN)."""
from embed import run

ZH = "docs/27-网络与协议栈.md"
EN = "docs/en/27-network.md"

run([
    (ZH, "sample-27-rmii-checklist.svg", "ch27-rmii-signals.png",
     "Handraw：RMII 信号分组核对（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。REF_CLK 50 MHz、TXD0/1+TX_EN、RXD0/1+CRS_DV、MDC+MDIO、NRST+strap、磁性件+RJ45 六组各验什么；link LED 只是线索，MDIO 读不到 PHY 停在硬件层；不是实拍。"),
    (ZH, "network-cache-ownership.svg", "ch27-cache-dma.png",
     "Handraw：TX clean 与 RX invalidate（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。TX 交接前 clean 整条 32 B line，RX 在 DMA 写完后 invalidate；未对齐窄区间 invalidate 会丢首尾 line 的脏变量；Ethernet DMA 到不了 0x20000000 的 DTCM；不是实拍。"),
    (ZH, "sample-27-tcp-framing.svg", "ch27-api-context.png",
     "Handraw：lwIP 三套 API 调用上下文（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。raw 只在 NO_SYS 主循环或 tcpip_thread；Netconn/socket 在应用任务；禁止在 Ethernet/定时器 IRQ 里直接调 tcp_write()/udp_send()；不是实拍。"),
    (ZH, "tcp-byte-stream.svg", "ch27-tcp-framing.png",
     "Handraw：字节流上的自定义帧（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。一次 send() 不对应一次 recv()；帧含 magic 0x534E、ver+type、payload_len（网络字节序）、sequence、CRC32；TLS 不能替代业务校验；不是实拍。"),
    (ZH, "sample-27-link-triage.svg", "ch27-backoff.png",
     "Handraw：有上限的指数退避（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。backoff = min(B_max, B_base×2^n)+jitter，n 有上限；link down 不建 socket，DNS/TCP/TLS/MQTT 分别计数，喂狗条件是网络任务在推进；不是实拍。"),

    (EN, "sample-27-rmii-checklist.svg", "ch27-rmii-signals.png",
     "Handraw: RMII signal groups (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). REF_CLK 50 MHz, TXD0/1+TX_EN, RXD0/1+CRS_DV, MDC+MDIO, NRST+strap, magnetics+RJ45; link LED is only a clue; if MDIO cannot read the PHY, stop at the hardware layer; not a photo."),
    (EN, "network-cache-ownership.svg", "ch27-cache-dma.png",
     "Handraw: TX clean vs RX invalidate (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). TX cleans full 32 B lines before handoff; RX invalidates after DMA writes; unaligned narrow invalidates also drop dirty data in first/last lines; Ethernet DMA cannot reach DTCM at 0x20000000; not a photo."),
    (EN, "sample-27-tcp-framing.svg", "ch27-api-context.png",
     "Handraw: lwIP API call contexts (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). raw API only from the NO_SYS main loop or tcpip_thread; Netconn/sockets from application tasks; never call tcp_write()/udp_send() from Ethernet or timer IRQs; not a photo."),
    (EN, "tcp-byte-stream.svg", "ch27-tcp-framing.png",
     "Handraw: defining a frame over a byte stream (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). One send() does not match one recv(); frame carries magic 0x534E, ver+type, payload_len (network byte order), sequence, CRC32; TLS does not replace application checks; not a photo."),
    (EN, "sample-27-link-triage.svg", "ch27-backoff.png",
     "Handraw: bounded exponential backoff (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). backoff = min(B_max, B_base×2^n)+jitter with a capped n; no socket while link is down; DNS/TCP/TLS/MQTT count separately; watchdog feeding requires network progress; not a photo."),
])
