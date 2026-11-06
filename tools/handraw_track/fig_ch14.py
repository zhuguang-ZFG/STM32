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


FIGS = {
    "ch14-enum-checklist": enum_checklist,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))
