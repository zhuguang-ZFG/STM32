# -*- coding: utf-8 -*-
"""ch14 knowledge-track figure (facts from docs/14, RM0008 / DS5319).

"Unknown USB device" only says which enumeration step failed; five things
must line up at once: 48 MHz clock, D+ 1.5 k pull-up, the standard requests,
descriptor lengths, and endpoint readiness. Where it stalls says what to
check: reading descriptors -> clock or descriptor fields; reading config ->
total length; the final step -> endpoint not ready.
"""
from hd import *

GATES = [
    ("48 MHz", "USBPRE = 0：72 ÷ 1.5；差一点读描述符就失败", BLUE_D),
    ("D+ 上拉", "1.5 kΩ 到 3.3 V（PA12 侧）；没有它主机不知道你插了", GREEN_D),
    ("标准请求", "地址 0 先要设备描述符前 8 字节，再给地址", AMBER_STROKE),
    ("描述符长度", "配置描述符总长度要和字节数一致（CDC 67 B）", RED),
    ("端点缓冲", "最后一步：端点没准备好就卡在配置", BLUE_D),
]


def enum_checklist():
    f = Fig("ch14-enum-checklist",
            "未知 USB 设备：五处同时对上才算数 / five gates, checked together")

    f.text(84, 138, "「未知 USB 设备」只说明枚举某一步失败——先对齐这五处，再谈驱动",
           size=21, color=MUTED)

    # ---- 五道门 ----
    y = 170
    for name, note, color in GATES:
        f.rect(84, y, 210, 66, color=color, fill=WHITE, sw=2.4)
        f.text(189, y + 28, name, size=21, color=color, anchor="middle",
               weight="bold")
        f.text(316, y + 40, note, size=18, color=INK)
        y += 82

    # ---- 卡在哪一步查哪处 ----
    f.rect(84, 596, 1008, 84, color=AMBER_STROKE, fill=WHITE, sw=2.4)
    f.text(100, 624, "枚举卡在哪一步，就查哪处", size=20, color=AMBER_STROKE,
           weight="bold")
    f.text(100, 654, "卡在读描述符 → 48 MHz 或描述符字段　｜　卡在读配置 → 总长度　｜　卡在最后一步 → 端点没准备好",
           size=17, color=INK)

    f.htext(84, 724, "五道门是「与」不是「或」：一道不对，设备管理器里就永远是未知设备",
            size=22, color=INK, weight="bold", hl=True)
    return f


def ctrl_transfer():
    f = Fig("ch14-ctrl-transfer",
            "控制传输三拍：请求、数据、状态 / SETUP, DATA, STATUS")

    f.text(84, 130, "每一次控制传输都在端点 0 上走三拍：先收请求，再走数据，状态拍收尾才算数",
           size=21, color=MUTED)

    # ---- 三拍骨架 ----
    stages = [
        (84, 270, "① SETUP 请求拍", "主机把请求写进 EP0", "枚举与标准请求", BLUE_D),
        (436, 280, "② DATA 数据拍", "数据跟着请求走", "方向看请求：交出或收下", GREEN_D),
        (798, 266, "③ STATUS 状态拍", "等状态传输走完", "这一笔请求才算生效", AMBER_STROKE),
    ]
    for x, w, t, l1, l2, col in stages:
        f.rect(x, 166, w, 120, color=col, fill=WHITE, sw=2.6)
        f.text(x + w / 2, 206, t, size=21, color=col, anchor="middle",
               weight="bold")
        f.multi(x + w / 2, 240, [l1, l2], size=17, color=INK, anchor="middle",
                lh=26)
    f.arrow(358, 226, 432, 226, color=INK, sw=2.4, bend=0.0)
    f.arrow(720, 226, 794, 226, color=INK, sw=2.4, bend=0.0)

    f.text(84, 322, "EP0 是双向端点（IN + OUT），bMaxPacketSize0 = 64；每帧都给控制传输留位置",
           size=18, color=MUTED)

    # ---- 例 A：SET_ADDRESS（第 4 步）----
    f.text(84, 386, "拿两笔枚举请求各走一遍", size=19, color=BLUE_D,
           weight="bold")
    f.rect(84, 412, 180, 88, color=RED, fill=WHITE, sw=2.4)
    f.multi(174, 442, ["例 A", "SET_ADDRESS", "（第 4 步）"], size=17,
            color=RED, anchor="middle", lh=24, weight="bold")
    f.rect(288, 412, 236, 88, color=RED, fill=WHITE, sw=2.0)
    f.multi(406, 442, ["主机把新地址", "交给设备（1~127）"], size=17,
            color=INK, anchor="middle", lh=26)
    f.rect(548, 412, 236, 88, color=RED, fill=WHITE, sw=2.0)
    f.multi(666, 442, ["等这一次", "状态传输走完"], size=17, color=INK,
            anchor="middle", lh=26)
    f.rect(808, 412, 256, 88, color=RED, fill=WHITE, sw=2.0)
    f.multi(936, 442, ["地址这才生效：", "后续请求都发往新地址"], size=17,
            color=RED, anchor="middle", lh=26, weight="bold")
    f.arrow(526, 456, 546, 456, color=INK, sw=2.2, bend=0.0)
    f.arrow(786, 456, 806, 456, color=INK, sw=2.2, bend=0.0)

    # ---- 例 B：GET_DESCRIPTOR（第 3 步）----
    f.rect(84, 524, 180, 88, color=GREEN_D, fill=WHITE, sw=2.4)
    f.multi(174, 554, ["例 B", "GET_DESCRIPTOR", "（第 3 步）"], size=17,
            color=GREEN_D, anchor="middle", lh=24, weight="bold")
    f.rect(288, 524, 236, 88, color=GREEN_D, fill=WHITE, sw=2.0)
    f.multi(406, 554, ["在地址 0 发起", "读设备描述符"], size=17, color=INK,
            anchor="middle", lh=26)
    f.rect(548, 524, 236, 88, color=GREEN_D, fill=WHITE, sw=2.0)
    f.multi(666, 554, ["设备先交描述符", "的前 8 字节"], size=17, color=INK,
            anchor="middle", lh=26)
    f.rect(808, 524, 256, 88, color=GREEN_D, fill=WHITE, sw=2.0)
    f.text(936, 564, "主机拿到", size=17, color=INK, anchor="middle")
    f.text(936, 592, "bMaxPacketSize0 = 64", size=17, color=BLUE_D,
           anchor="middle", weight="bold")
    f.arrow(526, 568, 546, 568, color=INK, sw=2.2, bend=0.0)
    f.arrow(786, 568, 806, 568, color=INK, sw=2.2, bend=0.0)

    # ---- 排查口诀 ----
    f.rect(84, 640, 980, 72, color=RED, fill=WHITE, sw=2.4)
    f.text(104, 668, "排查起点：抓包按顺序往后找", size=19, color=RED,
           weight="bold")
    f.text(104, 698, "第一笔没有得到正确回应的请求，就卡在这三拍里的某一拍——先看它停在哪一拍",
           size=17, color=INK)

    f.htext(84, 744, "口诀：请求开单、数据带货、状态销账——地址等状态走完才生效",
            size=23, color=INK, weight="bold", hl=True)
    return f


FIGS = {
    "ch14-enum-checklist": enum_checklist,
    "ch14-ctrl-transfer": ctrl_transfer,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))
