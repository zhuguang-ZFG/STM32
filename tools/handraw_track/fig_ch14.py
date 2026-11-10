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


def cdc_vs_hid():
    f = Fig("ch14-cdc-vs-hid",
            "CDC 与 HID 怎么选 / CDC versus HID at a glance")
    rows = [
        ("用途", "虚拟串口，字节流", "键盘/鼠标/报告"),
        ("端点", "1 批量 IN + 1 批量 OUT (+1 中断 IN)", "1 中断 IN（+可选 OUT）"),
        ("带宽", "高，可跑满全速", "低，受 bInterval 限"),
        ("数据单位", "字节流，自己切消息", "固定格式报告 Report"),
        ("驱动", "Win10+ 免驱", "全平台免驱"),
    ]
    f.rect(84, 150, 480, 56, color=GREEN_D, fill=WHITE, sw=2.6)
    f.htext(324, 184, "CDC：插上变串口", size=24, color=GREEN_D,
            anchor="middle", weight="bold")
    f.rect(594, 150, 470, 56, color=BLUE_D, fill=WHITE, sw=2.6)
    f.htext(829, 184, "HID：插上变键盘", size=24, color=BLUE_D,
            anchor="middle", weight="bold")
    y = 226
    for dim, cdc, hid in rows:
        f.text(84, y + 26, dim, size=20, color=MUTED, weight="bold")
        f.rect(210, y, 354, 44, color=GREEN_D, fill=WHITE, sw=2.0)
        f.text(222, y + 29, cdc, size=18, color=INK)
        f.rect(594, y, 470, 44, color=BLUE_D, fill=WHITE, sw=2.0)
        f.text(606, y + 29, hid, size=18, color=INK)
        y += 58
    f.rect(84, y + 10, 980, 66, color=INK, fill=WHITE, sw=2.2)
    f.htext(W / 2, y + 45, "送日志/采样数据 → CDC；要系统当键盘鼠标读 → HID",
            size=22, color=INK, anchor="middle", weight="bold", hl=True)
    return f


def usb_can_conflict():
    f = Fig("ch14-usb-can-conflict",
            "USB 与 CAN 抢的是芯片资源 / three shared resources")

    f.text(84, 132,
           "两个例程各写各的，撞车却撞在三样只有一份的芯片资源上",
           size=21, color=MUTED)

    cards = [
        ("① 引脚", "PA11 / PA12", BLUE_D,
         ["USB_DM / USB_DP", "复位后也是 CAN 的默认脚",
          "第 13 章已改到 PB8/PB9"]),
        ("② 存储", "512 B 专用 SRAM", GREEN_D,
         ["USB 与 CAN 共用这一块", "同一块存储，不能各占一半",
          "端点缓冲也从这里分"]),
        ("③ 中断", "USB_LP_CAN_RX0", AMBER_STROKE,
         ["就是 CAN 接收那条向量", "互联型表印 USB_LP_CAN1_RX0",
          "两个例程不要编进同一个工程"]),
    ]
    for i, (tag, name, color, lines) in enumerate(cards):
        x = 84 + i * 342
        f.rect(x, 166, 300, 186, color=color, fill=WHITE, sw=2.4)
        f.text(x + 18, 198, tag, size=17, color=MUTED, weight="bold")
        f.text(x + 18, 234, name, size=21, color=color, weight="bold")
        f.multi(x + 18, 270, lines, size=17, color=INK, lh=27)
    f.arrow(234, 354, 400, 442, color=MUTED, sw=2.4, bend=0.0)
    f.arrow(576, 354, 576, 442, color=MUTED, sw=2.4, bend=0.0)
    f.arrow(918, 354, 752, 442, color=MUTED, sw=2.4, bend=0.0)

    f.rect(336, 444, 480, 84, color=AMBER_STROKE, fill=WHITE, sw=3.0)
    f.text(576, 480, "二选一闸门", size=24, color=AMBER_STROKE,
           anchor="middle", weight="bold")
    f.text(576, 512, "同一份资源只交给一家", size=17, color=MUTED,
           anchor="middle")

    f.arrow(430, 530, 298, 564, color=BLUE_D, sw=2.6, bend=0.0)
    f.arrow(722, 530, 854, 564, color=GREEN_D, sw=2.6, bend=0.0)
    f.rect(84, 566, 420, 104, color=BLUE_D, fill=WHITE, sw=2.4)
    f.text(106, 604, "USB 设备例程", size=22, color=BLUE_D, weight="bold")
    f.text(106, 636, "CDC / HID 就在 PA11/PA12 上", size=17, color=INK)
    f.text(106, 660, "F103 只做设备，不做主机", size=16, color=MUTED)
    f.rect(648, 566, 420, 104, color=GREEN_D, fill=WHITE, sw=2.4)
    f.text(670, 604, "CAN 例程", size=22, color=GREEN_D, weight="bold")
    f.text(670, 636, "第 13 章已改到 PB8/PB9", size=17, color=INK)
    f.text(670, 660, "不要再把 CAN 留在 PA11/PA12", size=16, color=MUTED)

    f.htext(84, 736, "冲突在芯片资源层：三样各只有一份，只能二选一",
            size=23, color=INK, weight="bold", hl=True)
    return f


def transfer_pick():
    f = Fig("ch14-transfer-pick",
            "四问选端点：延迟与可靠性互换 / a four-question picker")

    f.text(84, 132,
           "从需求往下问：答「是」进右叶，答「否」进下一问——每片叶子一种端点",
           size=20, color=MUTED)

    questions = [
        "① 要枚举或类请求吗？",
        "② 迟到可接受，错包要重发吗？",
        "③ 小而定期，延迟有界吗？",
        "④ 旧数据到了就没用吗？",
    ]
    leaves = [
        ("控制 Control", BLUE_D, "EP0 · 双向", "枚举、配置、类请求"),
        ("批量 Bulk", GREEN_D, "批量 IN / OUT · 64 B/包",
         "CDC、U 盘、打印机（错包重发）"),
        ("中断 Interrupt", AMBER_STROKE, "中断 IN · 固定轮询间隔",
         "HID 键盘、小数据上报"),
        ("等时 Isochronous", RED, "等时 IN / OUT · 每帧留时段",
         "音频、摄像头（错过不补）"),
    ]
    for i, (q, (name, color, ep, use)) in enumerate(zip(questions, leaves)):
        y = 158 + i * 128
        f.rect(84, y, 440, 96, color=AMBER_STROKE, fill=WHITE, sw=2.4)
        f.text(106, y + 44, q, size=20, color=INK, weight="bold")
        f.arrow(528, y + 48, 646, y + 48, color=color, sw=2.4, bend=0.0)
        f.text(584, y + 38, "是", size=17, color=color, anchor="middle",
               weight="bold")
        if i < 3:
            f.arrow(112, y + 98, 112, y + 124, color=MUTED, sw=2.0,
                    bend=0.0)
            f.text(126, y + 116, "否", size=16, color=MUTED)

        f.rect(652, y, 416, 96, color=color, fill=WHITE, sw=2.4)
        f.text(674, y + 32, name, size=22, color=color, weight="bold")
        f.text(674, y + 62, ep, size=18, color=INK)
        f.text(674, y + 86, use, size=17, color=MUTED)

    f.arrow(112, 640, 112, 654, color=MUTED, sw=2.0, bend=0.0)
    f.text(126, 648, "否", size=16, color=MUTED)
    f.rect(84, 656, 440, 48, color=MUTED, sw=2.2, dash="7 6", double=False)
    f.text(104, 686, "四问全「否」：没有第五种类型，回需求重来",
           size=17, color=MUTED)

    f.htext(84, 748, "四档分的是同一条总线：延迟与可靠性互换，不是四种速度",
            size=22, color=INK, weight="bold", hl=True)
    return f


FIGS = {
    "ch14-cdc-vs-hid": cdc_vs_hid,
    "ch14-enum-checklist": enum_checklist,
    "ch14-ctrl-transfer": ctrl_transfer,
    "ch14-usb-can-conflict": usb_can_conflict,
    "ch14-transfer-pick": transfer_pick,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))
