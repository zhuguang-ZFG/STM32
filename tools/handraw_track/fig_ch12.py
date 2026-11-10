# -*- coding: utf-8 -*-
"""ch12 knowledge-track figure (facts from docs/12, RM0008 Rev 21 ch.3).

The unlock keys and the jump words already have their own boards. What the
prose only carries as a numbered list plus a code loop is the half-word
programming rhythm: erase runs PER -> AR -> STRT -> poll BSY -> check EOP,
then programming sets PG=1, writes one 16-bit half-word at addr + i*2, waits
for BSY, and repeats until the buffer is done; a 32-bit value therefore takes
two half-word writes and the sequence ends with CR.LOCK=1.
"""
from hd import *


def halfword_loop():
    f = Fig("ch12-halfword-loop",
            "半字写入：写一个，等一个 / one half-word, one BSY wait")

    f.text(84, 130, "开锁后先擦后写：每一步都等忙标志清零再做下一步，最后记得重新上锁",
           size=21, color=MUTED)

    # ---- 第 1 步：整页擦除的五拍 ----
    f.text(84, 158, "先擦：整页擦除，五拍走完才算擦过", size=19,
           color=GREEN_D, weight="bold")
    steps = [
        ("① CR.PER=1", "置 1 选页擦除", GREEN_D),
        ("② FLASH_AR", "写入页地址", BLUE_D),
        ("③ CR.STRT=1", "启动擦除", BLUE_D),
        ("④ 轮询 SR.BSY", "等到它 =0", RED),
        ("⑤ 检查 SR.EOP", "擦除完成标志", GREEN_D),
    ]
    for i, (t, s, col) in enumerate(steps):
        x = 84 + i * 201
        f.rect(x, 172, 176, 120, color=col, fill=WHITE, sw=2.4)
        f.text(x + 88, 214, t, size=20, color=col, anchor="middle",
               weight="bold")
        f.text(x + 88, 252, s, size=17, color=INK, anchor="middle")
        if i:
            f.arrow(x - 23, 232, x - 2, 232, color=INK, sw=2.4, bend=0.0)
    f.text(84, 318, "F1 页擦除 ~20~40 ms：忙标志落下之前，别急着去读",
           size=17, color=AMBER_STROKE)

    # ---- 第 2 步：半字编程循环 ----
    f.text(84, 372, "再写：半字循环，写一个等一个", size=19,
           color=BLUE_D, weight="bold")
    boxes = [
        (84, 190, "① 置 CR.PG=1", ["进入编程模式"], BLUE_D),
        (322, 240, "② 写一个半字", ["地址 addr + i×2", "（2 字节对齐）"], GREEN_D),
        (610, 190, "③ 轮询 SR.BSY", ["等它落回 0"], RED),
        (852, 212, "④ 全部写完", ["置 CR.LOCK=1", "重新上锁"], AMBER_STROKE),
    ]
    for x, w, t, lines, col in boxes:
        f.rect(x, 388, w, 110, color=col, fill=WHITE, sw=2.4)
        f.text(x + w / 2, 420, t, size=20, color=col, anchor="middle",
               weight="bold")
        f.multi(x + w / 2, 448, lines, size=17, color=INK, anchor="middle",
                lh=25)
    f.arrow(276, 443, 320, 443, color=INK, sw=2.4, bend=0.0)
    f.arrow(564, 443, 608, 443, color=INK, sw=2.4, bend=0.0)
    f.arrow(802, 443, 850, 443, color=INK, sw=2.4, bend=0.0)
    # 循环回边：没写完就回到写半字那一步
    f.arrow(705, 502, 442, 502, color=RED, sw=2.6, bend=-0.28)
    f.text(573, 560, "没写完：i++，地址 +2，再等一次 BSY", size=17,
           color=RED, anchor="middle")

    # ---- 底：两条硬规矩 ----
    f.rect(84, 584, 480, 104, color=BLUE_D, fill=WHITE, sw=2.4)
    f.text(104, 614, "一个 32 位值 = 两次半字写", size=20, color=BLUE_D,
           weight="bold")
    f.multi(104, 642, ["data[i] → addr，data[i+1] → addr+2",
                       "F103 不能按字节编程"], size=17, color=INK, lh=25)

    f.rect(596, 584, 468, 104, color=GREEN_D, fill=WHITE, sw=2.4)
    f.text(616, 614, "擦除后读回 0xFFFF", size=20, color=GREEN_D,
           weight="bold")
    f.multi(616, 642, ["写入只能把 1 变成 0", "0 想回到 1：先擦整页"],
            size=17, color=INK, lh=25)

    f.htext(84, 726, "口诀：写一个半字，等一次 BSY；没写完地址加 2，再来一遍",
            size=23, color=INK, weight="bold", hl=True)
    return f


def ymodem_flow():
    f = Fig("ch12-ymodem-flow",
            "YMODEM 四步：谁先说话 / who speaks first")
    f.text(84, 130, "带 CRC 的可靠文件传输；每一步卡住时，先查这一格",
           size=21, color=MUTED)

    # two-lane roles
    f.rect(84, 168, 180, 56, color=BLUE_D, fill=WHITE, sw=2.4)
    f.text(174, 203, "设备 Bootloader", size=18, color=BLUE_D,
           anchor="middle", weight="bold")
    f.rect(884, 168, 180, 56, color=GREEN_D, fill=WHITE, sw=2.4)
    f.text(974, 203, "上位机", size=18, color=GREEN_D, anchor="middle",
           weight="bold")
    f.line(264, 196, 884, 196, color=MUTED, sw=1.6, amp=0.6)

    steps = [
        ("① 设备周期发 'C'", "请求以 CRC 方式发送；收不到 'C' 先查波特率与共地", BLUE_D),
        ("② 上位机发首包", "文件名 + 大小；设备据此定 APP 地址并擦页", GREEN_D),
        ("③ 逐包数据 128/1024 B", "每包带 CRC16；校验过才写 Flash 并回 ACK，错了回 NAK 重发", BLUE_D),
        ("④ 空包收尾", "整包 CRC 过了才置「APP 有效」标志，再复位跳转", GREEN_D),
    ]
    y = 256
    for t, s, c in steps:
        f.rect(84, y, 700, 78, color=c, fill=WHITE, sw=2.4)
        f.text(108, y + 32, t, size=20, color=c, weight="bold")
        f.text(108, y + 62, s, size=17, color=INK)
        y += 94

    f.rect(820, 256, 248, 360, color=RED, fill=WHITE, sw=2.4)
    f.htext(944, 292, "卡住先查", size=19, color=RED, anchor="middle",
            weight="bold", hl=True)
    f.multi(944, 336, ["无 'C'：串口参数", "首包错：工具设置", "NAK 循环：线/缓存",
                       "写完跳不了：", "五道验收门", "(本章 §4)"],
            size=16, color=INK, lh=32, anchor="middle")
    return f


def option_bytes():
    f = Fig("ch12-option-bytes",
            "选项字节：F1 与 F4 的档位不一样 / option bytes differ")
    f.text(84, 130, "读保护改错会整片擦除；F4 的 0xCC 不可逆。先备份，再动手",
           size=20, color=RED, weight="bold")

    # F1 column
    f.rect(84, 176, 490, 330, color=BLUE_D, fill=WHITE, sw=2.6)
    f.text(329, 212, "STM32F1（本章 BluePill）", size=20, color=BLUE_D,
           anchor="middle", weight="bold")
    f.multi(112, 258, ["RDP = 0xA5：不保护", "RDP = 其他：读保护生效",
                       "没有 Level 2 这一档", "解除读保护 = 整片擦除主闪存",
                       "WRP 按页写保护", "USER：nRST_STOP / nRST_STDBY / WDG_SW"],
            size=18, color=INK, lh=40)

    # F4 column
    f.rect(606, 176, 462, 330, color=GREEN_D, fill=WHITE, sw=2.6)
    f.text(837, 212, "STM32F4", size=20, color=GREEN_D, anchor="middle",
           weight="bold")
    f.multi(634, 258, ["RDP = 0xAA：Level 0，不保护", "RDP ≠ 0xAA/0xCC：Level 1（写 0x55）",
                       "RDP = 0xCC：Level 2，不可逆", "WRP 按扇区写保护",
                       "参数区与 Bootloader 同扇区", "= 擦参数会擦掉 Bootloader"],
            size=18, color=INK, lh=40)

    f.rect(84, 540, 984, 108, color=RED, fill=WHITE, sw=2.6)
    f.htext(W / 2, 578, "两条不可逆边界", size=20, color=RED, anchor="middle",
            weight="bold", hl=True)
    f.text(W / 2, 620, "F4 写 0xCC 后无法再用调试口恢复；F1/F4 解除读保护都会擦整片 —— 先读回配置（HAL_FLASHEx_OBGetConfig），先备份",
           size=16, color=INK, anchor="middle")
    return f


FIGS = {
    "ch12-halfword-loop": halfword_loop,
    "ch12-ymodem-flow": ymodem_flow,
    "ch12-option-bytes": option_bytes,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))
