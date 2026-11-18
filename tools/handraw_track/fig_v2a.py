# -*- coding: utf-8 -*-
"""Hand-drawn plates for V2a (ch16 AT24C02 page wrap, ch19 reset-cause fusebox).

Facts pinned to the fact sheet, verbatim:
ch16: AT24C02 2 Kbit = 256 B, page 8 B, tWR ~ 5 ms (来源说法待复核),
7-bit addr 0x50; write START->0xA0->ACK->字地址->ACK->数据->ACK->STOP;
read ...Sr->0xA1->...NACK->STOP; low 3 address bits wrap inside the page,
high 5 fixed; 20 bytes from 0x00 leaves 0x00~0x07 = b16 b17 b18 b19
b12 b13 b14 b15 (b0-b11 lost); ACK polling DR=0xA0, AF->clear->retry;
single-byte RX end 清ADDR->关ACK->置STOP->读DR; E05 hardware_status
pending (未实测).
ch19: RCC_CSR bits 31 LPWRRSTF / 30 WWDGRSTF / 29 IWDGRSTF / 28 SFTRSTF /
27 PORRSTF / 26 PINRSTF / 25 BORRSTF / 24 RMVF; mask csr & 0xFE000000U;
F407 0x40023874, F103 0x40021024; internal reset drives NRST >= 20 us;
POR sets PORRSTF AND PINRSTF; IWDG t=(4*2^PR)*(RLR+1)/f_LSI, LSI F103
40 kHz / F407 32 kHz (来源说法未复核), RLR=999 /64 -> 2.000 s vs 1.600 s;
WWDG window 0x3F<T<W; reset record 12 B, magic 0x57444731 written last;
HardFault CFSR 0xE000ED28, BFAR 0xE000ED38, pc=sp[6]; watchdog numbers
文档推导, board scenes 未实测.

Deterministic: hd.Fig seeds its own RNG; re-running gives the same SVG.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hd import (AMBER_PALE, AMBER_STROKE, BLUE_D, BLUE_FILL, GRAY_FILL,  # noqa: E402
                GREEN_D, GREEN_FILL, INK, MUTED, RED, RED_FILL, WHITE, Fig,
                save)

MONO = "'Consolas','Courier New',monospace"

STAGE = Path(__file__).resolve().parents[2] / "assets" / "illustrations" / "staged" / "l0-l5-pass" / "figures"


def ch16_at24c02_page_wrap():
    f = Fig("ch16-at24c02-page-wrap", "AT24C02：8 格旋转门",
            title_color=BLUE_D, tag="CH 16 · I2C 与 EEPROM")
    f.text(64, 126,
           "一页只有 8 个格子：从 0x00 写 20 字节会绕回页首，门卫 ACK 等写周期结束才点头。",
           size=19, color=MUTED)

    # Spec pills.
    f.pill(64, 138, 180, 30, "2 Kbit = 256 B", BLUE_D, fill=BLUE_FILL, size=16)
    f.pill(260, 138, 110, 30, "页 8 B", GREEN_D, fill=GREEN_FILL, size=16)
    f.pill(386, 138, 190, 30, "7-bit 地址 0x50", AMBER_STROKE,
           fill=AMBER_PALE, size=16)
    f.text(600, 159, "布局示意，非按比例", size=14, color=MUTED)

    # (a) The 8-cubby carousel: one page, wrap arrow under the strip.
    f.card(64, 176, 1024, 210, BLUE_D, fill=BLUE_FILL)
    f.text(576, 198, "低 3 位地址在页内回卷，高 5 位固定", size=15,
           color=MUTED, anchor="middle")
    vals = ["b16", "b17", "b18", "b19", "b12", "b13", "b14", "b15"]
    for i in range(8):
        x = 80 + i * 124
        f.rect(x, 214, 112, 62, color=BLUE_D, sw=2.0, fill=WHITE,
               double=False)
        f.text(x + 56, 236, f"0x0{i}", size=15, color=MUTED,
               anchor="middle", weight="bold")
        f.text(x + 56, 264, vals[i], size=20, color=INK, anchor="middle",
               weight="bold")
    # Wrap: cubby 7 back to cubby 0, bowing below the strip.
    f.arrow(1004, 284, 136, 284, color=RED, sw=2.6, bend=-0.055, head=10)
    f.text(560, 336, "第 9 字节绕回页首", size=15, color=RED,
           anchor="middle", weight="bold")
    f.stamp(880, 344, "b0–b11 被覆盖", size=19, angle=-8)

    # (b) Write handshake: envelope chain.
    f.card(64, 402, 636, 128, GREEN_D, fill=GREEN_FILL)
    f.text(84, 434, "写握手", size=21, color=GREEN_D, weight="bold")
    f.envelope(84, 446, 52, 40, GREEN_D)
    chain = [
        ("pill", "START", GREEN_D, GREEN_FILL, 78),
        ("pill", "0xA0", BLUE_D, BLUE_FILL, 66),
        ("ack", "ACK", GREEN_D, WHITE, 40),
        ("pill", "字地址", BLUE_D, BLUE_FILL, 78),
        ("ack", "ACK", GREEN_D, WHITE, 40),
        ("pill", "数据", BLUE_D, BLUE_FILL, 62),
        ("ack", "ACK", GREEN_D, WHITE, 40),
        ("pill", "STOP", RED, RED_FILL, 66),
    ]
    x = 152
    for kind, label, color, fill, w in chain:
        if kind == "pill":
            f.pill(x, 450, w, 34, label, color, fill=fill, size=16)
        else:
            f.circle(x + w / 2, 467, 20, color=color, sw=2.0, fill=WHITE)
            f.text(x + w / 2, 473, label, size=13, color=color,
                   anchor="middle", weight="bold")
        x += w + 10
    f.text(84, 512, "ACK 要等写周期完成才点头（tWR 见左下）", size=15,
           color=MUTED)

    # Read handshake: shorter chain beside it.
    f.card(716, 402, 372, 128, BLUE_D, fill=BLUE_FILL)
    f.text(736, 434, "读握手", size=21, color=BLUE_D, weight="bold")
    rchain = [
        ("…Sr", BLUE_D, BLUE_FILL, 60),
        ("0xA1", BLUE_D, BLUE_FILL, 66),
        ("…", MUTED, WHITE, 44),
        ("NACK", RED, RED_FILL, 70),
        ("STOP", RED, RED_FILL, 66),
    ]
    x = 736
    for label, color, fill, w in rchain:
        f.pill(x, 450, w, 34, label, color, fill=fill, size=16)
        x += w + 10
    f.text(736, 512, "主机回 NACK：不再读了", size=15, color=MUTED)

    # (c) Bottom left: the doorman (ACK polling).
    f.card(64, 546, 500, 158, AMBER_STROKE, fill=AMBER_PALE)
    f.text(84, 576, "门卫：写周期没完不点头", size=21, color=AMBER_STROKE,
           weight="bold")
    f.clockface(128, 628, 30, AMBER_STROKE, hand=(-1, 2))
    f.text(180, 620, "tWR ≈ 5 ms", size=26, color=AMBER_STROKE,
           weight="bold")
    f.text(180, 648, "来源说法待复核", size=14, color=MUTED)
    f.text(84, 684, "ACK polling：DR=0xA0 → AF → clear → retry", size=16,
           color=INK, weight="bold")

    # Bottom right: single-byte RX end order.
    f.card(580, 546, 508, 158, GREEN_D, fill=GREEN_FILL)
    f.text(600, 576, "单字节收尾：顺序不能乱", size=21, color=GREEN_D,
           weight="bold")
    steps = [("清ADDR", 92), ("关ACK", 82), ("置STOP", 92), ("读DR", 76)]
    x = 600
    for i, (label, w) in enumerate(steps):
        f.pill(x, 600, w, 38, label, GREEN_D, fill=WHITE, size=17)
        if i < 3:
            f.arrow(x + w + 2, 619, x + w + 16, 619, color=GREEN_D,
                    sw=2.0, bend=0.0, head=7)
        x += w + 18
    f.text(600, 672, "读握手 NACK 之后，按此顺序收尾", size=15, color=MUTED)

    # Takeaway + evidence footer.
    f.htext(64, 738, "页写 8 字节就停；跨页要分包，等 ACK 再发下一包",
            size=22, color=INK, weight="bold", hl=True)
    f.text(576, 764,
           "tWR ≈ 5 ms 来源说法待复核 · E05 hardware_status pending（未实测）· 布局示意，非实测",
           size=15, color=MUTED, anchor="middle")
    return f


def ch19_reset_cause_fusebox():
    f = Fig("ch19-reset-cause-fusebox", "复位保险盒：先拍照",
            title_color=RED, tag="CH 19 · 复位与看门狗")
    f.text(64, 126,
           "RCC_CSR 是七盏锁存灯：先给整板拍照留证，再按 RMVF 清灯。",
           size=19, color=MUTED)

    # (a) Fuse-box panel: seven latching lamps + RMVF switch.
    f.card(64, 168, 1024, 216, RED, fill=RED_FILL)
    f.text(84, 200, "RCC_CSR · 七盏复位原因灯", size=21, color=RED,
           weight="bold")
    lamps = [
        (31, "LPWRRSTF"), (30, "WWDGRSTF"), (29, "IWDGRSTF"),
        (28, "SFTRSTF"), (27, "PORRSTF"), (26, "PINRSTF"),
        (25, "BORRSTF"),
    ]
    for i, (bit, name) in enumerate(lamps):
        cx = 130 + i * 120
        f.text(cx, 228, str(bit), size=15, color=MUTED, anchor="middle",
               weight="bold")
        f.circle(cx, 258, 20, color=RED, sw=2.2, fill=WHITE)
        f.circle(cx, 258, 7, color=RED, sw=1.4, fill=RED)
        f.text(cx, 300, name, size=14, color=INK, anchor="middle",
               weight="bold")
    # RMVF: the separate clear switch, photograph first.
    f.magnifier(966, 212, 40, RED)
    f.text(986, 272, "先拍照", size=15, color=RED, anchor="middle",
           weight="bold")
    f.pill(920, 286, 152, 38, "RMVF · bit24", RED, fill=WHITE, size=16)
    f.text(996, 348, "按下 = 清灯", size=14, color=MUTED, anchor="middle")
    # Mask + both chip addresses under the lamps.
    f.pill(84, 326, 280, 36, "csr & 0xFE000000U", RED, fill=WHITE, size=16)
    f.pill(384, 326, 240, 36, "F407 0x40023874", BLUE_D, fill=WHITE, size=15)
    f.pill(640, 326, 240, 36, "F103 0x40021024", BLUE_D, fill=WHITE, size=15)

    # (b) IWDG arithmetic card.
    f.card(64, 400, 500, 168, BLUE_D, fill=BLUE_FILL)
    f.text(84, 432, "IWDG：独立看门狗倒计时", size=21, color=BLUE_D,
           weight="bold")
    f.text(84, 462, "t = (4×2^PR)×(RLR+1) / f_LSI", size=17, color=INK,
           weight="bold")
    f.text(84, 490, "RLR=999，预分频 /64", size=16, color=INK)
    f.text(84, 522, "F103：1.600 s", size=24, color=GREEN_D, weight="bold")
    f.text(300, 522, "F407：2.000 s", size=24, color=RED, weight="bold")
    f.text(84, 552, "LSI：F103 40 kHz / F407 32 kHz（来源说法未复核）",
           size=14, color=MUTED)

    # WWDG window + NRST + POR double lamp.
    f.card(580, 400, 508, 168, GREEN_D, fill=GREEN_FILL)
    f.text(600, 432, "WWDG 窗口 · NRST · POR", size=21, color=GREEN_D,
           weight="bold")
    f.text(600, 462, "窗口：0x3F < T < W，喂早喂晚都复位", size=16,
           color=INK)
    f.text(600, 490, "内部复位拉低 NRST ≥ 20 µs", size=16, color=INK)
    f.text(600, 518, "POR 同时点亮 PORRSTF 与 PINRSTF", size=16, color=INK)
    f.text(600, 548, "两盏灯一起亮，别只读一盏", size=14, color=MUTED)

    # (c) Bottom strip: reset record + HardFault snapshot.
    f.card(64, 584, 500, 104, AMBER_STROKE, fill=AMBER_PALE)
    f.text(84, 614, "复位记录 12 B", size=19, color=AMBER_STROKE,
           weight="bold")
    f.text(84, 644, "magic 0x57444731 最后写", size=16, color=INK,
           weight="bold")
    f.text(84, 672, "magic 在 = 记录完整（文档推导）", size=14, color=MUTED)

    f.card(580, 584, 508, 104, RED, fill=WHITE)
    f.text(600, 614, "HardFault 现场三件套", size=19, color=RED,
           weight="bold")
    f.text(600, 644, "CFSR 0xE000ED28 · BFAR 0xE000ED38", size=16,
           color=INK, weight="bold")
    f.text(600, 672, "pc = sp[6]（文档推导）", size=14, color=MUTED)

    # Stamp: photograph before clearing.
    f.stamp(880, 700, "先拍照，再按 RMVF", size=19, angle=-7)

    # Takeaway + evidence footer.
    f.htext(64, 738, "先读 RCC_CSR 留证，再按 RMVF；看门狗喂在窗口里",
            size=22, color=INK, weight="bold", hl=True)
    f.text(576, 764,
           "看门狗数字均为文档推导 · LSI 频率来源说法未复核 · 板级场景未实测 · 布局示意，非实测",
           size=15, color=MUTED, anchor="middle")
    return f



def ch16_spi_shift_ring():
    """SPI shift ring and mode table: both sides shift one bit per SCK
    beat; modes differ only in idle level and sample edge. Facts from
    ch16 section six."""
    f = Fig("ch16-spi-shift-ring",
            "SPI 移位环：发和收是同一个动作",
            title_color=BLUE_D, tag="CH 16 · I2C 与 SPI")
    f.text(64, 126,
           "主从各一个 8 位移位寄存器，MOSI/MISO 把头尾接成环；8 拍之后两个字节完成对调。",
           size=19, color=MUTED)

    # ---- shift ring ----
    f.card(96, 156, 420, 130, BLUE_D, fill=BLUE_FILL)
    f.text(116, 188, "主机移位寄存器 0xA5", size=15.5, color=BLUE_D,
           weight="bold")
    f.card(636, 156, 420, 130, GREEN_D, fill=GREEN_FILL)
    f.text(656, 188, "从机移位寄存器 0x3C", size=15.5, color=GREEN_D,
           weight="bold")
    f.arrow(520, 196, 630, 196, color=BLUE_D, sw=2.6, bend=0.0, head=10)
    f.text(575, 178, "MOSI", size=13.5, color=BLUE_D, anchor="middle",
           weight="bold")
    f.arrow(630, 246, 520, 246, color=GREEN_D, sw=2.6, bend=0.0, head=10)
    f.text(575, 268, "MISO", size=13.5, color=GREEN_D, anchor="middle",
           weight="bold")
    f.text(96, 316, "SCK 每来一拍：两边各移出一位、移进一位；MSB 先出（LSBFIRST=0 复位值）",
           size=14, color=INK)
    f.text(96, 342, "只想读也得假写一个字节顶出从机数据；只想写也得把换回来的读走，否则下次接收溢出",
           size=14, color=MUTED)

    # ---- mode table ----
    modes = [("0", "0", "0", "低", "第 1 沿（上升）", GREEN_D, GREEN_FILL),
             ("1", "0", "1", "低", "第 2 沿（下降）", BLUE_D, BLUE_FILL),
             ("2", "1", "0", "高", "第 1 沿（下降）", BLUE_D, BLUE_FILL),
             ("3", "1", "1", "高", "第 2 沿（上升）", AMBER_STROKE, AMBER_PALE)]
    for i, (m, cpol, cpha, idle, sample, c, fl) in enumerate(modes):
        x = 96 + i * 244
        f.card(x, 372, 228, 120, c, fill=fl)
        f.text(x + 16, 402, "Mode " + m, size=17, color=c,
               weight="bold")
        f.text(x + 16, 432, "CPOL=" + cpol + "  CPHA=" + cpha,
               size=14, color=INK, font=MONO)
        f.text(x + 16, 456, "空闲 " + idle, size=13.5, color=MUTED)
        f.text(x + 16, 478, "采样 " + sample, size=13.5, color=INK)

    # ---- mismatch verdict ----
    f.panel(64, 516, 1024, 84, RED_FILL, amp=1.6)
    f.rect(64, 516, 1024, 84, color=RED, sw=1.8, fill=None, amp=1.6)
    f.text(88, 548, "模式错配不报错：MOSI 波形看着正常，从机读到的字节整体错一位",
           size=15, color=RED, weight="bold")
    f.text(88, 578, "定位法：逻辑分析仪对空闲电平与采样沿；W25Q64/ST7789 多为 Mode 0，W25Q64 也支持 Mode 3",
           size=14, color=MUTED)

    f.htext(64, 700, "BR 只有 /2 到 /256 八档、没有 /3：10MHz 目标只能落相邻档（84MHz /8 = 10.5MHz）",
            size=19.5, color=INK, weight="bold", hl=True)
    f.text(576, 730,
           "模式表与分频档取自本章 CR1 位段取证；示意，非实测波形。",
           size=14, color=MUTED, anchor="middle")
    return f


def ch18_stop_wake_clock():
    """Stop exit: HSE/PLL are off, wake lands on HSI; clock must be
    rebuilt in order. Facts from ch18 section four."""
    f = Fig("ch18-stop-wake-clock",
            "Stop 退出：PLL 不会自己回来",
            title_color=RED, tag="CH 18 · 低功耗")
    f.text(64, 126,
           "Stop 期间 HSE 与 PLL 停掉，醒来硬件把 HSI 接上：F103 是 8MHz，F407 是 16MHz。",
           size=19, color=MUTED)

    # ---- wake chain ----
    chain = [("醒来：HSI 在跑，PLL 停", "别用 72/168MHz 的外设参数"),
             ("开 HSE，等 HSERDY", "8MHz 晶振"),
             ("配 PLL 并等 PLLRDY", "F1：HSE x9；F4：M8 N336 P2 Q7"),
             ("Flash latency：F1=2WS · F4=5WS", "3.3V 口径"),
             ("SYSCLK 切 PLL，等 SWS", "写 SW 不等于已切换"),
             ("重开外设时钟，重算 SysTick/BRR/TIM", "F1：71999、0x271；F4：167999、729")]
    for i, (a, b) in enumerate(chain):
        y = 164 + i * 60
        c = RED if i == 0 else BLUE_D
        fl = RED_FILL if i == 0 else BLUE_FILL
        f.panel(96, y, 560, 50, fl, amp=1.5)
        f.rect(96, y, 560, 50, color=c, sw=1.8, fill=None, amp=1.5)
        f.text(112, y + 21, a, size=14.5, color=c, weight="bold")
        f.text(112, y + 40, b, size=13, color=MUTED, font=MONO)

    # ---- uart evidence ----
    f.card(700, 164, 388, 280, AMBER_STROKE, fill=AMBER_PALE)
    f.text(720, 196, "串口最先暴露", size=18, color=AMBER_STROKE,
           weight="bold")
    f.text(720, 228, "F103：0x271 在 72MHz = 115200", size=13.5, color=INK,
           font=MONO)
    f.text(720, 254, "醒在 HSI 8MHz：同一个 0x271 = 12800", size=13.5,
           color=RED, font=MONO, weight="bold")
    f.text(720, 292, "F407：729 在 84MHz = 115226", size=13.5, color=INK,
           font=MONO)
    f.text(720, 318, "PCLK2 掉到 8MHz：729 打出 10973", size=13.5, color=RED,
           font=MONO, weight="bold")
    f.text(720, 356, "和 115200 差约 90%，对端收到帧错", size=13.5,
           color=MUTED)
    f.text(720, 388, "恢复 PLL 后按新 PCLK 重算 BRR", size=13.5, color=INK)
    f.text(720, 414, "两套分母不能互抄", size=13.5, color=RED, weight="bold")

    # ---- who does what ----
    f.panel(64, 530, 1024, 80, GRAY_FILL, amp=1.6)
    f.rect(64, 530, 1024, 80, color=MUTED, sw=1.6, fill=None, amp=1.6)
    f.text(88, 560, "EnterSTOPMode 只负责进 Stop，不替你恢复 PLL：__WFI() 返回后自己调时钟初始化",
           size=14.5, color=INK, weight="bold")
    f.text(88, 588, "HAL 时基挂 SysTick 的，先恢复 tick 再配时钟，避免配置里的超时判断用错节拍",
           size=13.5, color=MUTED)

    f.htext(64, 700, "「醒来 PLL 自动回来」是错误说法：六步重走，分母按 F1/F4 各算各的",
            size=21, color=INK, weight="bold", hl=True)
    f.text(576, 730,
           "恢复表与 BRR 读数取自本章取证记录；流程示意，非实测。",
           size=14, color=MUTED, anchor="middle")
    return f


FIGS = {
    "ch16-at24c02-page-wrap": ch16_at24c02_page_wrap,
    "ch16-spi-shift-ring": ch16_spi_shift_ring,
    "ch18-stop-wake-clock": ch18_stop_wake_clock,
    "ch19-reset-cause-fusebox": ch19_reset_cause_fusebox,
}


if __name__ == "__main__":
    names = sys.argv[1:] or list(FIGS)
    STAGE.mkdir(parents=True, exist_ok=True)
    for n in names:
        f = FIGS[n]()
        save(f, str(STAGE / (n + ".svg")))
        print("wrote", STAGE / (n + ".svg"))