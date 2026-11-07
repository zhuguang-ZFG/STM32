# -*- coding: utf-8 -*-
"""ch23 knowledge-track figures (facts from docs/23, DS12232 Rev 5 / RM0444)."""
from hd import *


def part_id():
    f = Fig("ch23-part-id", "STM32G071RB 是谁 / decode the part")
    f.panel(296, 116, 560, 76, AMBER_FILL)
    f.rect(296, 116, 560, 76, color=AMBER_STROKE, sw=3.0)
    f.text(W / 2, 146, "STM32G071RB：M0+ @ 64 MHz", size=30, color=INK,
           anchor="middle", weight="bold")
    f.text(W / 2, 178, "1.7–3.6 V · R = 64 脚 · B = 128 KB Flash · SRAM 36 KB",
           size=20, color=MUTED, anchor="middle")
    rows = [
        ("通信口", "2×I2C · 4×USART · 1×LPUART · 2×SPI", GREEN_D),
        ("Type-C", "UCPD（供电协商），不是 USB 设备控制器", BLUE_D),
        ("没有 CAN", "功能不存在时，别从复用表里硬找", RED),
        ("低功耗", "Sleep · Stop · Standby · Shutdown", BLUE_D),
    ]
    y = 236
    for t, d, c in rows:
        f.rect(120, y, 220, 62, color=c, fill=WHITE)
        f.text(230, y + 39, t, size=23, color=c, anchor="middle", weight="bold")
        f.text(368, y + 39, d, size=22, color=INK)
        y += 82
    f.htext(W / 2, 636, "先确认完整订货号、封装与外设表，再动手", size=25,
            color=INK, anchor="middle", weight="bold", hl=True)
    return f


def pin_compare():
    f = Fig("ch23-pin-compare", "F103 与 G071RB 的脚 / pin families differ")
    rows = [
        ("第 1 脚", "VBAT", "PC11（Table 12）", RED),
        ("复位", "专用 NRST", "PF2-NRST，可配 GPIO", GREEN_D),
        ("BOOT", "专用 BOOT0", "PA14-BOOT0 = SWCLK 共脚", AMBER_STROKE),
        ("复位后 GPIO", "多为浮空输入", "模拟输入（Table 11）", BLUE_D),
        ("PA11/PA12", "USB DM/DP", "普通 GPIO + UCPD 重映射位", BLUE_D),
        ("CAN", "bxCAN", "这颗料没有 CAN", RED),
        ("PC13–15", "备份域小电流", "只灌 ~3 mA / ≤2 MHz / 30 pF", GREEN_D),
    ]
    y0 = 132
    f.text(160, y0 - 14, "项", size=20, color=MUTED, anchor="middle")
    f.text(450, y0 - 14, "F103", size=20, color=MUTED, anchor="middle")
    f.text(860, y0 - 14, "G071RB", size=20, color=MUTED, anchor="middle")
    for t, a, b, c in rows:
        y = y0
        f.rect(66, y, 188, 56, color=c, fill=WHITE)
        f.text(160, y + 35, t, size=20, color=c, anchor="middle", weight="bold")
        f.text(450, y + 35, a, size=20, color=MUTED, anchor="middle")
        f.rect(650, y, 436, 56, color=c, fill=WHITE)
        f.text(868, y + 35, b, size=20, color=INK, anchor="middle")
        y0 = y + 74
    f.htext(W / 2, 682, "AF 表看 DS12232 Table 13/14，别抄 F407 的 AF 号",
            size=24, color=RED, anchor="middle", weight="bold", hl=True)
    return f


def boot_latch():
    f = Fig("ch23-boot-latch", "PA14：BOOT0 = SWCLK / one pin, two jobs")
    f.panel(256, 122, 640, 92, AMBER_FILL)
    f.rect(256, 122, 640, 92, color=AMBER_STROKE, sw=3.0)
    f.text(W / 2, 156, "复位释放后：第四个 SYSCLK 上升沿锁存启动源", size=25,
           color=INK, anchor="middle", weight="bold")
    f.text(W / 2, 194, "锁存之后 SWCLK 翻转不会反向改启动目标", size=22,
           color=GREEN_D, anchor="middle")
    dangers = [
        ("采样窗口内", "外部上拉 / 跳线 / 调试器把 PA14", "保持非预期电平"),
        ("BOOT_LOCK = 1", "优先强制 Main Flash", "拉 PA14 覆盖不了"),
        ("nBOOT_SEL", "选“用引脚还是选项位”", "不是 Bootloader 开关"),
        ("空片例外", "Main Flash 为空时", "可转入系统 Bootloader"),
    ]
    y = 268
    for t, a, b in dangers:
        f.rect(110, y, 250, 78, color=RED, fill=WHITE)
        f.text(235, y + 32, t, size=21, color=RED, anchor="middle",
               weight="bold")
        f.text(235, y + 60, "危险 / 边界", size=17, color=MUTED, anchor="middle")
        f.text(390, y + 32, a, size=21, color=INK)
        f.text(390, y + 60, b, size=21, color=INK)
        y += 94
    f.htext(W / 2, 700, "出厂默认不能替代现场读回 — Bootloader 或旧工程可能改写过",
            size=23, color=MUTED, anchor="middle")
    return f


def pinmux():
    f = Fig("ch23-pinmux", "G071RB 复用速查 / where things live")
    rows = [
        ("SWD", "PA13 SWDIO / PA14-BOOT0 SWCLK", "动了 PA14 就同时动了 BOOT0", RED),
        ("USART1", "PA9 / PA10，或 PC4 / PC5", "Table 13", GREEN_D),
        ("USART2", "PA2 / PA3", "Table 13", GREEN_D),
        ("I2C1", "PB6 / PB7，或 PB8 / PB9", "Table 14", BLUE_D),
        ("SPI1", "PA5/PA6/PA7，NSS=PA4 或 PB0", "Table 13 / 14", BLUE_D),
        ("HSE / LSE", "PF0/PF1 · PC14/PC15", "Table 12 脚名", AMBER_STROKE),
    ]
    y0 = 136
    for t, a, b, c in rows:
        f.rect(80, y0, 200, 66, color=c, fill=WHITE)
        f.text(180, y0 + 40, t, size=22, color=c, anchor="middle", weight="bold")
        f.text(306, y0 + 28, a, size=21, color=INK)
        f.text(306, y0 + 54, b, size=19, color=MUTED)
        y0 += 84
    f.htext(W / 2, 672, "PA11/PA12 复位后就是自己；PA9/PA10 重映射过去要先动 SYSCFG_CFGR1",
            size=23, color=MUTED, anchor="middle")
    return f


def g0_f1_compare():
    f = Fig("ch23-g0-f1-compare", "G071RB 与 F103C8 对照卡 / three cards before you leave")
    rows = [
        ("第 1 脚", "F103：VBAT", "G071：PC11——从左边往下数", RED),
        ("复位脚", "F103：NRST 专用脚", "G071：PF2 复位功能", AMBER_STROKE),
        ("BOOT", "F103：独立 BOOT0 焊盘", "G071：与 SWCLK 共用 PA14，复位后内部下拉", BLUE_D),
        ("USB", "F103：全速设备控制器", "G071：UCPD（Type-C 用），不是设备控制器", GREEN_D),
        ("CAN", "F103：bxCAN 有", "G071：没有 CAN，别在图上找发送脚", RED),
        ("PC13–15", "F103：PC13 带 LED", "G071：开关电流约 3 mA、≤2 MHz、≤30 pF", AMBER_STROKE),
    ]
    y = 140
    for item, f1, g0, c in rows:
        f.rect(84, y, 190, 62, color=c, fill=WHITE, sw=2.2)
        f.text(179, y + 38, item, size=21, color=c, anchor="middle",
               weight="bold")
        f.rect(288, y, 330, 62, color=INK, fill=WHITE, sw=1.8)
        f.text(300, y + 38, f1, size=18, color=INK)
        f.rect(630, y, 462, 62, color=c, fill=WHITE, sw=1.8)
        f.text(642, y + 38, g0, size=18, color=INK)
        y += 78
    f.text(300, 128, "F103C8（对照）", size=19, color=MUTED, anchor="middle")
    f.text(700, 128, "G071RB（DS12232 表 12）", size=19, color=MUTED,
           anchor="middle")
    f.htext(84, 640, "口诀：R 是 64 只脚，B 是 128 KB；复位在 PF2，USB 是 UCPD",
            size=23, color=INK, weight="bold", hl=True)
    f.text(84, 678, "与 F1 对照着记，迁移才不会踩空；默认状态是模拟输入，不是 F1 的浮空输入", size=17,
           color=MUTED)
    return f


def boot_tree():
    f = Fig("ch23-boot-tree", "G0x1 启动判定树 / boot decision tree")

    # legend: the three outcomes, one chip each
    def chip_row(x0, y0, items, size=18, gap=40, chip=30, chip_h=24):
        x = x0
        for name, c in items:
            f.rect(x, y0, chip, chip_h, color=c, fill=WHITE, sw=2.4,
                   double=False)
            f.text(x + chip + 8, y0 + chip_h - 5, name, size=size, color=c,
                   weight="bold")
            w = chip + 8 + text_w(name, size)
            x += w + gap

    def node(cx, cy, w, h, label, color=INK, size=22, sub=None, sub_color=None,
             sub_size=16, border_sw=2.6):
        f.rect(cx - w / 2, cy - h / 2, w, h, color=color, fill=WHITE,
               sw=border_sw)
        if sub:
            f.text(cx, cy - 2, label, size=size, color=color, anchor="middle",
                   weight="bold")
            f.text(cx, cy + h / 2 - 13, sub, size=sub_size,
                   color=sub_color or MUTED, anchor="middle")
        else:
            f.text(cx, cy + size * 0.36, label, size=size, color=color,
                   anchor="middle", weight="bold")

    def edge(x0, y0, x1, y1, label, lx, ly):
        f.arrow(x0, y0, x1, y1, color=INK, sw=2.4, bend=0.08, head=10)
        f.text(lx, ly, label, size=19, color=INK, anchor="middle",
               weight="bold")

    chip_row(300, 112, [("Main Flash", GREEN_D), ("System memory", BLUE_D),
                        ("Embedded SRAM", AMBER_STROKE)])

    # level 1: BOOT_LOCK
    node(576, 190, 250, 58, "① BOOT_LOCK = 1 ?")
    # level 2: nBOOT_SEL
    node(760, 320, 250, 58, "② nBOOT_SEL = 1 ?")
    # level 3: pin path / option-bit path
    node(480, 450, 280, 58, "③ BOOT0 脚（PA14）")
    node(990, 450, 280, 58, "④ nBOOT0（选项位）")
    # level 4: nBOOT1 switches
    node(465, 580, 190, 58, "⑤ nBOOT1 = ?")
    node(970, 580, 170, 58, "⑥ nBOOT1 = ?")
    # leaves
    node(175, 320, 300, 76, "Main Flash", color=GREEN_D, size=24,
         sub="强制优先 · 拉 PA14 覆盖不了", sub_color=RED, border_sw=3.0)
    node(180, 580, 200, 54, "Main Flash", color=GREEN_D, size=22)
    node(700, 580, 200, 54, "Main Flash", color=GREEN_D, size=22)
    node(300, 700, 210, 54, "System memory", color=BLUE_D, size=21)
    node(590, 700, 210, 54, "Embedded SRAM", color=AMBER_STROKE, size=21)
    node(830, 700, 200, 54, "System memory", color=BLUE_D, size=21)
    node(1055, 700, 190, 54, "Embedded SRAM", color=AMBER_STROKE, size=21)

    # edges
    edge(516, 219, 175, 282, "=1", 346, 246)
    edge(636, 219, 760, 291, "=0", 698, 246)
    edge(700, 349, 480, 421, "=0", 590, 381)
    edge(820, 349, 990, 421, "=1", 905, 381)
    edge(400, 479, 180, 553, "=0", 290, 512)
    edge(520, 479, 465, 551, "=1", 492, 512)
    edge(910, 479, 700, 553, "=1", 805, 512)
    edge(1010, 479, 970, 551, "=0", 987, 512)
    edge(405, 609, 300, 673, "=1", 352, 638)
    edge(525, 609, 590, 673, "=0", 557, 638)
    edge(910, 609, 830, 673, "=1", 862, 638)
    edge(1025, 609, 1055, 673, "=0", 1035, 638)

    f.htext(W / 2, 752, "nBOOT_SEL 选的是『用引脚还是选项位路径』，不是 Bootloader 开关",
            size=22, color=INK, anchor="middle", weight="bold", hl=True)
    return f


FIGS = {
    "ch23-part-id": part_id,
    "ch23-pin-compare": pin_compare,
    "ch23-boot-latch": boot_latch,
    "ch23-pinmux": pinmux,
    "ch23-g0-f1-compare": g0_f1_compare,
    "ch23-boot-tree": boot_tree,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))
