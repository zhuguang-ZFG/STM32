# -*- coding: utf-8 -*-
"""ch21 knowledge-track figures (facts from docs/21, DS5319 / board maps)."""
from hd import *


def board_compare():
    f = Fig("ch21-board-compare", "三板对照 / package · debugger · 5V · USB")
    cols = [
        (96, "BluePill", "F103C8T6", "LQFP48 · 72 MHz",
         "64 KB / 20 KB", "外接 ST-LINK", "少数 FT 脚", "需外电路", BLUE_D),
        (416, "BlackPill", "F411CEU6", "UFQFPN48 · 100 MHz",
         "512 KB / 128 KB", "外接 ST-LINK", "多数 FT 仍看 DS", "板载器件口", GREEN_D),
        (736, "Nucleo-F411RE", "F411RET6", "LQFP64 · 100 MHz",
         "512 KB / 128 KB", "板载 ST-LINK/V2-1", "按 UM/DS 脚注", "ST-LINK+用户 USB", AMBER_STROKE),
    ]
    for x, name, part, pkg, mem, dbg, ft, usb, c in cols:
        f.rect(x, 128, 300, 470, color=c, fill=WHITE)
        f.htext(x + 150, 168, name, size=24, color=c, anchor="middle",
                weight="bold", hl=True)
        f.multi(x + 150, 214,
                [part, pkg, "", "Flash/RAM", mem, "", "调试器", dbg,
                 "", "5V 容忍", ft, "", "USB 路径", usb],
                size=18, color=INK, lh=26, anchor="middle")
    f.htext(W / 2, 650, "选板先对四问：内核与 Flash、板上调试器、5V 引脚、USB 谁供电",
            size=22, color=RED, anchor="middle", weight="bold", hl=True)
    f.text(W / 2, 698, "出处 DS5319 / Nucleo UM · 不是实拍板照片",
           size=20, color=MUTED, anchor="middle")
    return f


def vdd_3v3():
    f = Fig("ch21-vdd-3v3", "BluePill 电源轨 / 5V · 3V3 · VDDA · VBAT")
    boxes = [
        (90, 140, 220, 120, "USB 5 V", "micro-USB 入口", "进 AMS1117-3.3", BLUE_D),
        (390, 140, 220, 120, "3V3", "LDO 输出", "VDD + SWD 目标", GREEN_D),
        (690, 140, 220, 120, "VDDA", "模拟供电", "ADC/DAC/PLL", AMBER_STROKE),
        (240, 320, 280, 110, "VBAT", "引脚 1 备份域", "纽扣或接 3V3", RED),
        (560, 320, 280, 110, "量测门禁", "3V3 = 3.2–3.4 V", "与 ST-LINK 共地", GREEN_D),
    ]
    for x, y, w, h, t, a, b, c in boxes:
        f.rect(x, y, w, h, color=c, fill=WHITE)
        f.text(x + w / 2, y + 36, t, size=26, color=c, anchor="middle", weight="bold")
        f.text(x + w / 2, y + 68, a, size=20, color=INK, anchor="middle")
        f.text(x + w / 2, y + 96, b, size=18, color=MUTED, anchor="middle")
    f.arrow(310, 200, 390, 200, color=INK, sw=2.8, bend=0.05)
    f.arrow(610, 200, 690, 200, color=INK, sw=2.8, bend=0.05)
    f.htext(W / 2, 490, "先量 3V3，再怀疑固件", size=28, color=RED,
            anchor="middle", weight="bold", hl=True)
    f.multi(W / 2, 540,
            ["劣质 1117 / 缺去耦 → LED 亮时 SWD 发抖",
             "ST-LINK 3V3 与 USB 同时供电会打架",
             "手焊最小系统别让 VDDA 悬空"],
            size=22, color=INK, lh=34, anchor="middle")
    return f


def usb_ttl():
    f = Fig("ch21-usb-ttl", "USB-TTL ↔ USART1 / TX·RX 交叉 · 共地 3.3 V")
    f.rect(100, 140, 360, 360, color=BLUE_D, fill=WHITE)
    f.htext(280, 180, "MCU 侧", size=26, color=BLUE_D, anchor="middle",
            weight="bold", hl=True)
    rows = [
        ("PA9", "USART1_TX", "→ 适配器 RX"),
        ("PA10", "USART1_RX", "← 适配器 TX"),
        ("GND", "共地", "必须共用"),
        ("VCC", "通常不接", "勿回灌 5 V"),
    ]
    y = 230
    for a, b, c in rows:
        f.rect(130, y, 100, 48, color=BLUE_D, fill=WHITE)
        f.text(180, y + 32, a, size=22, color=BLUE_D, anchor="middle", weight="bold")
        f.text(250, y + 20, b, size=20, color=INK)
        f.text(250, y + 44, c, size=18, color=MUTED)
        y += 62
    f.rect(560, 140, 420, 360, color=GREEN_D, fill=WHITE)
    f.htext(770, 180, "USB-TTL 适配器", size=26, color=GREEN_D,
            anchor="middle", weight="bold", hl=True)
    f.multi(770, 240,
            ["TX → 接 PA10", "RX → 接 PA9", "GND → GND",
             "3.3 V 电平（或设跳线）", "", "验收：115200 8N1",
             "空闲高电平 ~3.3 V"],
            size=22, color=INK, lh=34, anchor="middle")
    f.arrow(460, 254, 560, 254, color=INK, sw=2.8, bend=0.0, head=10)
    f.arrow(560, 316, 460, 316, color=INK, sw=2.8, bend=0.0, head=10)
    f.htext(W / 2, 560, "交叉 TX/RX、共地；别把 5 V 灌进 PA10",
            size=26, color=RED, anchor="middle", weight="bold", hl=True)
    f.text(W / 2, 610, "HC-05 / 调试口同一套：电平匹配是前提",
           size=22, color=MUTED, anchor="middle")
    return f


def hse_load():
    f = Fig("ch21-hse-load", "HSE 8 MHz / PD0·PD1 · ~20 pF · HSERDY")
    pins = [
        (90, 140, 280, 160, "PD0", "OSC_IN", "晶振输入脚", BLUE_D),
        (420, 140, 280, 160, "PD1", "OSC_OUT", "晶振输出脚", BLUE_D),
        (750, 140, 280, 160, "CL1 / CL2", "~20 pF 级", "以板厂取值为准", AMBER_STROKE),
    ]
    for x, y, w, h, t, a, b, c in pins:
        f.rect(x, y, w, h, color=c, fill=WHITE)
        f.text(x + w / 2, y + 42, t, size=28, color=c, anchor="middle", weight="bold")
        f.text(x + w / 2, y + 84, a, size=22, color=INK, anchor="middle")
        f.text(x + w / 2, y + 120, b, size=18, color=MUTED, anchor="middle")
    f.panel(90, 340, 940, 100, AMBER_FILL)
    f.rect(90, 340, 940, 100, color=AMBER_STROKE, sw=3.0)
    f.text(W / 2, 378, "Bring-up：HSEON → HSERDY → PLLSRC/PLLMUL → SW=PLL → SWS=PLL",
           size=22, color=INK, anchor="middle", weight="bold")
    f.text(W / 2, 414, "72 MHz 时 Flash LATENCY=2；HSERDY 不到先查焊接，再怪 PLLMUL",
           size=20, color=RED, anchor="middle")
    f.multi(W / 2, 480,
            ["CSS 可回退 HSI —— 代码看似正常，UART 波特率已经说谎",
             "×1 探头戳 OSC_OUT 会把起振掐死；先用 HSI 证固件再恢复 HSE",
             "别默认每块山寨 BluePill 的 8 MHz 都能起"],
            size=21, color=INK, lh=34, anchor="middle")
    return f


def nrst_boot0():
    f = Fig("ch21-nrst-boot0", "NRST / BOOT0 / BOOT1 / 启动路径")
    boxes = [
        (70, 130, 250, 210, "NRST", "引脚 7", "低有效复位", "10 kΩ 上拉 + 100 nF", RED),
        (350, 130, 250, 210, "BOOT0", "引脚 44", "0 = 主 Flash", "1 = 系统存储器", BLUE_D),
        (630, 130, 250, 210, "BOOT1", "PB2", "与 BOOT0 组合", "Flash 启动保持 0", GREEN_D),
        (910, 130, 170, 210, "SWD", "PA13/14", "脚 34/37", "烧完别关", AMBER_STROKE),
    ]
    for x, y, w, h, t, a, b, c, col in boxes:
        f.rect(x, y, w, h, color=col, fill=WHITE)
        f.text(x + w / 2, y + 40, t, size=26, color=col, anchor="middle", weight="bold")
        f.text(x + w / 2, y + 80, a, size=20, color=INK, anchor="middle")
        f.text(x + w / 2, y + 120, b, size=18, color=INK, anchor="middle")
        f.text(x + w / 2, y + 160, c, size=16, color=MUTED, anchor="middle")
    rows = [
        ("BOOT0=0 · BOOT1=x", "主 Flash @ 0x08000000", "正常运行（默认）", GREEN_D),
        ("BOOT0=1 · BOOT1=0", "系统存储器（ROM ISP）", "不是“程序丢了”", RED),
        ("BOOT0=1 · BOOT1=1", "内嵌 SRAM", "调试 / 救砖", AMBER_STROKE),
    ]
    y = 380
    for t, a, b, c in rows:
        f.rect(90, y, 280, 52, color=c, fill=WHITE)
        f.text(230, y + 34, t, size=18, color=c, anchor="middle", weight="bold")
        f.text(400, y + 34, a, size=20, color=INK)
        f.text(780, y + 34, b, size=20, color=MUTED)
        y += 62
    f.htext(W / 2, 600, "BOOT0 拉高跑系统存储器，不是固件蒸发",
            size=26, color=RED, anchor="middle", weight="bold", hl=True)
    f.text(W / 2, 650, "ISP 后记得把 BOOT0 跳回 0，并确认 SWD 仍可连",
           size=22, color=INK, anchor="middle")
    return f


def minimal_five():
    f = Fig("ch21-minimal-five", "最小系统五件事 / measure these before blaming code")
    # 中间的芯片
    f.rect(460, 320, 232, 180, color=INK, fill=WHITE)
    f.htext(576, 396, "STM32F103C8T6", size=24, color=INK, anchor="middle",
            weight="bold")
    f.text(576, 434, "LQFP48", size=19, color=MUTED, anchor="middle")
    blocks = [
        ("电源", "3.3 V 进每一对 VDD/VSS，", "封装上每一对都要接，不能空着", GREEN_D, 84, 140, 360),
        ("去耦", "100 nF × 每个 VDD + 10 µF；", "VDDA 单独滤波，缺了 ADC 跳", BLUE_D, 724, 140, 360),
        ("复位", "NRST：10 kΩ 上拉 + 100 nF", "到地 + 按键；悬空易误复位", AMBER_STROKE, 84, 320, 360),
        ("BOOT", "BOOT0 用 10 kΩ 下拉；", "BOOT0 = 0 从主闪存启动", RED, 724, 320, 360),
        ("晶振", "8 MHz HSE + 负载电容；", "32.768 kHz LSE 焊盘留给 RTC", MUTED, 84, 500, 360),
    ]
    targets = {(84, 140): 352, (724, 140): 352, (84, 320): 406,
               (724, 320): 406, (84, 500): 470}
    for name, l1, l2, c, bx, by, bw in blocks:
        f.rect(bx, by, bw, 92, color=c, fill=WHITE)
        f.text(bx + 18, by + 36, name, size=25, color=c, weight="bold")
        f.text(bx + 18, by + 64, l1, size=18, color=INK)
        f.text(bx + 18, by + 86, l2, size=18, color=INK)
        tx = targets[(bx, by)]
        if bx < 400:
            f.arrow(bx + bw + 4, by + 46, 464, tx, color=c, bend=0.10, sw=2.6,
                    head=11)
        else:
            f.arrow(bx - 4, by + 46, 688, tx, color=c, bend=-0.10, sw=2.6,
                    head=11)
    f.panel(84, 632, 984, 78, AMBER_FILL)
    f.rect(84, 632, 984, 78, color=AMBER_STROKE, sw=3.0)
    f.text(W / 2, 682, "板子不工作：先量这五样，再怀疑你的程序", size=27,
           color=INK, anchor="middle", weight="bold")
    return f


def fake_id():
    f = Fig("ch21-fake-id", "山寨板鉴定：丝印 vs 寄存器 / identity record")
    f.text(W / 2, 130, "买的「F103C8T6」先别急着跑程序：四个外观疑点，拿三个身份寄存器对账",
           size=21, color=MUTED, anchor="middle")

    # ---- 左：丝印/外观会撒谎（四个疑点，全部来自正文「变种与山寨」行）----
    f.rect(70, 168, 450, 312, color=RED, fill=WHITE)
    f.htext(295, 210, "丝印会撒谎", size=26, color=RED, anchor="middle",
            weight="bold", hl=True)
    items = [
        ("兼容芯片冒充", "「C8T6」实为 CS32F103/APM32 等兼容芯片"),
        ("Flash 缩水", "只有 64 KB 却标 128 KB"),
        ("缺 LSE 晶振", "RTC 不走时"),
        ("劣质 LDO", "稳压偷工，板子发热"),
    ]
    y = 258
    for name, detail in items:
        f.circle(96, y - 7, 4.5, color=RED, fill=AMBER_FILL, sw=2.0)
        f.text(114, y, name, size=20, color=RED, weight="bold")
        f.text(114, y + 28, detail, size=17, color=INK)
        y += 56

    # ---- 中：对账箭头 ----
    f.text(576, 306, "读出来", size=17, color=MUTED, anchor="middle")
    f.text(576, 350, "对账", size=17, color=MUTED, anchor="middle")
    f.arrow(524, 326, 628, 326, color=INK, sw=2.6, bend=0.0, head=10)

    # ---- 右：三个身份寄存器（RM0008 第 30 章，地址照抄正文代码）----
    f.rect(632, 168, 450, 312, color=GREEN_D, fill=WHITE)
    f.htext(857, 210, "寄存器不会", size=26, color=GREEN_D, anchor="middle",
            weight="bold", hl=True)
    regs = [
        ("Device ID @ 0xE0042000", "0x410 = F103 中等容量"),
        ("Flash 容量 @ 0x1FFFF7E0（低 16 位）", "报 64 KB 才是正品 C8"),
        ("UID 唯一 ID @ 0x1FFFF7E8", "96 位唯一 ID，读 3 个字"),
    ]
    y = 256
    for name, val in regs:
        f.rect(656, y - 22, 402, 74, color=GREEN_D, fill=None, sw=1.6,
               amp=1.2, double=False, r=8)
        f.text(674, y + 4, name, size=19, color=INK, weight="bold")
        f.text(674, y + 34, val, size=17, color=GREEN_D)
        y += 78

    # ---- 下：身份记录五件套 ----
    f.panel(70, 516, 1010, 92, AMBER_FILL)
    f.rect(70, 516, 1010, 92, color=AMBER_STROKE, sw=3.0)
    f.text(W / 2, 554, "身份记录五件套：拍丝印 · Device ID · Flash 容量 · UID · 供电电压",
           size=23, color=INK, anchor="middle", weight="bold")
    f.text(W / 2, 588, "任何不一致都单独列出，不用「山寨」两个字代替具体证据",
           size=18, color=MUTED, anchor="middle")

    f.htext(W / 2, 656, "丝印和手册冲突时，这份记录就是裁决书",
            size=26, color=RED, anchor="middle", weight="bold", hl=True)
    f.text(W / 2, 700, "正品 F103C8 = Device ID 0x410 + Flash 64 KB；对不上就写进身份记录",
           size=19, color=MUTED, anchor="middle")
    return f


def identity_triage():
    f = Fig("ch21-identity-triage",
            "板子对不上账：三处核对再给结论")
    f.text(84, 118, "「跑不出 72 MHz」「丝印对不上」先核对证据，别用「山寨」代替具体记录",
           size=21, color=MUTED)
    steps = [
        ("① 读 Device ID / Flash 容量", "用调试器或 ISP 读回，与 DS5319 对账", GREEN_D),
        ("② 主频实测", "MCO 或示波器量 SYSCLK，不只看丝印标称", BLUE_D),
        ("③ 供电与发热", "量各 VDD 电流与压降，查去耦与 LDO", AMBER_STROKE),
    ]
    y = 165
    for t, n, c in steps:
        f.rect(84, y, 980, 88, color=c, fill=WHITE, sw=2.6)
        f.text(112, y + 38, t, size=24, color=c, weight="bold")
        f.text(112, y + 70, n, size=19, color=INK)
        y += 106
    f.rect(84, y + 12, 980, 66, color=RED, fill=WHITE, sw=2.6)
    f.htext(W / 2, y + 48, "任何一处不一致都单列记录，结论以证据为准",
            size=22, color=RED, anchor="middle", weight="bold", hl=True)
    return f


FIGS = {
    "ch21-identity-triage": identity_triage,
    "ch21-board-compare": board_compare,
    "ch21-vdd-3v3": vdd_3v3,
    "ch21-usb-ttl": usb_ttl,
    "ch21-hse-load": hse_load,
    "ch21-nrst-boot0": nrst_boot0,
    "ch21-minimal-five": minimal_five,
    "ch21-fake-id": fake_id,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        fig = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(fig, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))
