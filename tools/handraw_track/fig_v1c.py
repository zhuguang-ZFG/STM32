# -*- coding: utf-8 -*-
"""V1c knowledge-track figures for ch15 (ADC/DAC) and ch17 (Flash/OTA).

Numbers and labels come from the two chapters only: 12-bit, 3.3 V,
805.7 uV, 2482 / 0x9B2, 1.65 V, 21 MHz / 12 MHz, 480 KB slots, sector 1
metadata, 16 KB Bootloader, 32 KB unused in Slot B, 22+22 KB on F103C8.
Layouts are schematic, not measured and not to scale.
"""
from pathlib import Path

from hd import *

OUT = Path(__file__).resolve().parents[2] / ".temp" / "l0-l5-pass" / "figures"


def adc_dac_chain():
    f = Fig("v1c-adc-dac-chain", "ADC 采样链：从模拟电压到 DMA 缓冲",
            title_color=BLUE_D)
    f.text(576, 132, "STM32F407 · 12 位 · VREF = 3.3 V · 1 LSB = 805.7 µV",
           size=20, color=MUTED, anchor="middle")

    # ---- top: analog in -> sample/hold -> SAR -> DMA -> buffer ----
    boxes = [
        (54, "模拟输入", BLUE_D,
         ["PA0 / IN0", "0 – 3.3 V", "源阻抗 R_s"]),
        (266, "采样保持", AMBER_STROKE,
         ["C_ADC 充电", "t > 9.01τ / 9.70τ", "采样窗口定精度"]),
        (478, "SAR ADC", RED,
         ["12 轮二分", "4096 → 1 档", "V_dac ≤ Vin 保留"]),
        (690, "DMA", GREEN_D,
         ["半字搬运 DR", "NDTR = 采样个数", "DMA2 Stream0/4"]),
        (902, "滤波 / 输出", BLUE_D,
         ["uint16_t 数组", "按 rank 顺序", "控制 / 上位机"]),
    ]
    for x, title, color, lines in boxes:
        f.rect(x, 188, 180, 132, color=color, fill=WHITE, sw=2.4)
        f.text(x + 90, 220, title, size=22, color=color,
               anchor="middle", weight="bold")
        f.multi(x + 12, 251, lines, size=16, color=INK, lh=25)
    for x in (234, 446, 658, 870):
        f.arrow(x, 254, x + 30, 254, color=BLUE, bend=0, head=8)

    f.text(54, 344, "F407：84 MHz ÷4 → 21 MHz", size=17, color=INK)
    f.text(590, 344, "F103：72 MHz ÷6 → 12 MHz", size=17, color=INK)
    f.text(54, 368, "采样 + 12 周期", size=17, color=INK)
    f.text(590, 368, "采样 + 12.5 周期", size=17, color=INK)

    # ---- middle: one worked value path ----
    f.rect(54, 392, 1028, 150, color=BLUE_D, fill=WHITE, sw=2.4)
    f.text(76, 424, "2.00 V 的去路（模型算术，不是板上读数）",
           size=21, color=BLUE_D, weight="bold")
    chips = [
        (76, 280, "Vin = 2.00 V", BLUE_D),
        (392, 300, "12 轮 → 2482 = 0x9B2", RED),
        (728, 332, "回算 1.99966 V；差 0.42 LSB", GREEN_D),
    ]
    for x, w, label, color in chips:
        f.rect(x, 446, w, 70, color=color, fill=PAPER, sw=2.2)
        f.text(x + w / 2, 489, label, size=20, color=INK,
               anchor="middle", weight="bold")
    f.arrow(356, 481, 388, 481, color=BLUE, bend=0, head=8)
    f.arrow(692, 481, 724, 481, color=BLUE, bend=0, head=8)
    f.text(76, 534, "1 LSB = 3.3 V / 4096 = 805.7 µV；码 2048 = 1.65 V",
           size=18, color=MUTED)

    # ---- bottom: DAC reverse path ----
    f.rect(54, 564, 1028, 140, color=GREEN_D, fill=WHITE, sw=2.4)
    f.text(76, 596, "反方向：DAC 把码变回电压（F407，PA4）",
           size=21, color=GREEN_D, weight="bold")
    dac = [
        (76, 250, "DHR12R1 = 2048", AMBER_STROKE),
        (356, 190, "DOR1", BLUE_D),
        (576, 210, "缓冲器", MUTED),
        (816, 240, "PA4 ≈ 1.65 V", GREEN_D),
    ]
    for x, w, label, color in dac:
        f.rect(x, 612, w, 64, color=color, fill=PAPER, sw=2.2)
        f.text(x + w / 2, 652, label, size=20, color=INK,
               anchor="middle", weight="bold")
    for x0, x1 in ((326, 352), (546, 572), (786, 812)):
        f.arrow(x0, 644, x1, 644, color=BLUE, bend=0, head=8)
    f.text(76, 697,
           "TIM6 TRGO 触发；DMA1 Stream5 Channel7 递样本；F103C8 无 DAC，改用 PWM+RC",
           size=17, color=MUTED)

    f.htext(576, 736, "先保住电压，再分 4096 档；精度上限由采样窗口决定",
            size=24, color=INK, weight="bold", anchor="middle", hl=True)
    f.text(576, 762,
           "数值取自本章：3.3 V、805.7 µV、2482、0x9B2、1.65 V；未按电气比例绘制",
           size=15, color=MUTED, anchor="middle")
    return f


def flash_ota_rollback():
    f = Fig("v1c-flash-ota-rollback", "升级、校验、回滚：换槽是一条小记录",
            title_color=GREEN_D)
    f.text(576, 132,
           "STM32F407 · 1 MB · Bootloader 扇区 0 · 元数据扇区 1 · Slot A/B 各 480 KB",
           size=19, color=MUTED, anchor="middle")

    # ---- layout bar (schematic widths, addresses are real) ----
    f.text(54, 174, "Flash 版图（布局示意，不按比例）", size=18, color=MUTED)
    bar = [
        (54, 64, "Boot", "16 KB", BLUE_D),
        (118, 96, "元数据", "16 KB", AMBER_STROKE),
        (214, 390, "Slot A · 480 KB", "", GREEN_D),
        (604, 390, "Slot B · 480 KB", "", BLUE),
        (994, 88, "留空", "32 KB", GRAY_FILL),
    ]
    for x, w, label, sub, color in bar:
        f.rect(x, 186, w, 66, color=color, fill=color, sw=2.2)
        txt_color = INK if color == GRAY_FILL else WHITE
        if sub:
            f.text(x + w / 2, 213, label, size=17, color=txt_color,
                   anchor="middle", weight="bold", halo=False)
            f.text(x + w / 2, 237, sub, size=14, color=txt_color,
                   anchor="middle", halo=False)
        else:
            f.text(x + w / 2, 226, label, size=19, color=txt_color,
                   anchor="middle", weight="bold", halo=False)
    f.text(54, 268, "0x08000000", size=14, color=MUTED)
    f.text(214, 268, "0x08008000", size=14, color=MUTED)
    f.text(604, 268, "0x08080000", size=14, color=MUTED)
    f.text(1082, 268, "0x08100000", size=14, color=MUTED, anchor="end")
    f.text(54, 292, "Slot B 的 512 KB 只划 480 KB 给镜像；两槽等大",
           size=16, color=MUTED)

    # ---- five-step upgrade ----
    f.text(54, 326, "一次升级的五步（任一步失败都不动当前槽）",
           size=18, color=MUTED)
    steps = [
        (54, "① 写备槽", GREEN_D, ["只擦 Slot B", "Slot A 不动"]),
        (264, "② 校验", BLUE_D, ["长度 ≤ 槽大小", "CRC32 + 向量两字"]),
        (474, "③ 提交", AMBER_STROKE, ["追加 seq+1 记录", "meta_crc 最后写"]),
        (684, "④ 首启自检", GREEN_D, ["点灯 / 串口 / 外设", "通过 → 有效"]),
        (894, "⑤ 回退", RED, ["不确认 → 标无效", "追加 active=A"]),
    ]
    for x, title, color, lines in steps:
        f.rect(x, 338, 188, 126, color=color, fill=WHITE, sw=2.4)
        f.text(x + 94, 370, title, size=19, color=color,
               anchor="middle", weight="bold")
        f.multi(x + 12, 402, lines, size=15, color=INK, lh=26)
    for x in (242, 452, 662, 872):
        f.arrow(x, 401, x + 20, 401, color=BLUE, bend=0, head=7)

    # ---- two failure boundaries ----
    f.text(54, 502, "两条失败边界", size=18, color=MUTED)
    f.rect(54, 516, 502, 172, color=RED, fill=WHITE, sw=2.4)
    f.text(74, 550, "镜像长事务：写 B 时断电", size=20, color=RED,
           weight="bold")
    f.multi(74, 584, [
        "B 只写了一半：CRC 不过，记录不提交",
        "Slot A 全程未动，重启仍跑 A",
        "这条边界由「只写备槽」保证",
        "恢复动作：重写 B，不动 A",
    ], size=16, color=INK, lh=28)

    f.rect(580, 516, 502, 172, color=AMBER_STROKE, fill=WHITE, sw=2.4)
    f.text(600, 550, "记录短事务：提交时断电", size=20, color=AMBER_STROKE,
           weight="bold")
    f.multi(600, 584, [
        "meta_crc 不过：这条记录不算数",
        "启动扫记录，选上一条有效 seq",
        "回滚只在下一次启动发生",
        "恢复动作：追加 active=A 的记录",
    ], size=16, color=INK, lh=28)

    f.htext(576, 724, "长事务失败不动旧槽；短事务失败退回上一条记录",
            size=24, color=INK, weight="bold", anchor="middle", hl=True)
    f.text(576, 756,
           "数字取自本章：1 MB、扇区 1、480 KB、F103C8 双槽 22+22 KB；布局示意，非实测",
           size=15, color=MUTED, anchor="middle")
    return f


FIGS = {
    "ch15-adc-dac-chain": adc_dac_chain,
    "ch17-flash-ota-rollback": flash_ota_rollback,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    OUT.mkdir(parents=True, exist_ok=True)
    for n in names:
        f = FIGS[n]()
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))
