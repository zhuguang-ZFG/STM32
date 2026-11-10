# -*- coding: utf-8 -*-
"""B55: embed the two ch14 knowledge-track plates (bottom-up, 2 then 1)."""
from embed import embed_after_text

SPECS = [
    # 2. ch14-transfer-pick — takeaway paragraph before the transfer table
    ("docs/14-USB.md",
     "按「实时性 vs 可靠性」取舍——**控制**用于枚举配置，**批量**用于大数据（可靠性优先），**中断**用于小数据低延迟，**等时**用于音频视频（实时优先，允许丢）。",
     "ch14-transfer-pick.png",
     "Handraw：四问选传输类型（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。看哪里：一棵四问选型树——要枚举或类请求吗（控制）→ 迟到可接受但错包要重发吗（批量）→ 小而定期、延迟有界吗（中断）→ 旧数据到了就没用吗（等时）；每个叶子标端点类型与典型用途；证明什么：四种传输是「实时性 vs 可靠性」的四档取舍，不是四种速度；不能证明什么：不是抓包实测，也不判断某个端点的具体配置是否合法。出处：[RM0008](#source-rm0008-usb) 与 USB 2.0 规范第 9 章。"),
    ("docs/en/14-usb.md",
     "**Takeaway:** Trade latency against reliability. **Control** is for enumeration. **Bulk** moves bytes and retries. **Interrupt** is small and bounded. **Isochronous** keeps a time slot and is allowed to drop data.",
     "ch14-transfer-pick.png",
     "Handraw: the four-question transfer picker (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). Where to look: a four-question picker — enumeration or a class request (control), a late packet that can be retried (bulk), small periodic latency-bounded data (interrupt), stale data that is worthless (isochronous) — each leaf naming its endpoint type; Proves the four types are four trade-offs of latency against reliability, not four speeds; Cannot check whether one endpoint configuration is legal, and it is not a capture. See [RM0008](#source-rm0008-usb) and the USB 2.0 spec chapter 9."),

    # 1. ch14-usb-can-conflict — final row of the pitfalls table
    ("docs/14-USB.md",
     "| 和 CAN 例程链在一起，接收中断串了 | 两条例程共用一条向量 | 两个例程分开。CAN 不要留在 PA11/PA12 | [RM0008](#source-rm0008-usb) | 中容量表印 `USB_LP_CAN_RX0`，互联型表印 `USB_LP_CAN1_RX0`。F103 的 USB 是设备，不是主机 |",
     "ch14-usb-can-conflict.png",
     "Handraw：USB 与 CAN 共用的三样资源（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。看哪里：F103 上 USB 与 CAN 共用的三样东西——PA11/PA12 两只脚、512 字节专用 SRAM、USB_LP_CAN_RX0 这一条向量（互联型表写作 USB_LP_CAN1_RX0），下方一道「二选一」闸门；证明什么：冲突在芯片资源层而不是代码层，两个例程不能编进同一个工程；不能证明什么：不是波形实测，也不证明 CAN 改到 PB8/PB9 后时序仍满足要求。出处：[RM0008](#source-rm0008-usb)。"),
    ("docs/en/14-usb.md",
     "| Linked with the CAN example, the receive interrupt is shared | The two examples use one vector | Keep the examples apart. Do not leave CAN on PA11/PA12 | [RM0008](#source-rm0008-usb) | The printed medium-density name is `USB_LP_CAN_RX0`. The connectivity table prints `USB_LP_CAN1_RX0`. USB on this part is a device, not a host |",
     "ch14-usb-can-conflict.png",
     "Handraw: the three resources USB and CAN share (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). Where to look: the three things USB and CAN share on one F103 — PA11/PA12, the 512-byte dedicated SRAM, and the single USB_LP_CAN_RX0 vector (printed USB_LP_CAN1_RX0 in the connectivity table) — with a pick-one gate underneath; Proves the conflict sits in chip resources, not in code, so the two examples cannot share a project; Cannot prove that CAN timing holds after the PB8/PB9 remap, and it is not a capture. See [RM0008](#source-rm0008-usb)."),
]

if __name__ == "__main__":
    bad = 0
    for spec in SPECS:
        if not embed_after_text(*spec):
            bad += 1
    if bad:
        raise SystemExit(f"{bad} embed(s) failed")
