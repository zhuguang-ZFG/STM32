"""Additional mechanism plates for the merged book's reading gaps."""
from __future__ import annotations

import math
from functools import partial
from pathlib import Path

from hd import (AMBER_PALE, AMBER_STROKE, BLUE_D, BLUE_FILL, GRAY_FILL,
                GREEN_D, GREEN_FILL, INK, MUTED, RED, RED_FILL, WHITE,
                Fig, save)

STAGE = Path(__file__).resolve().parents[2] / "assets/illustrations/staged/reading-pass/figures"
LABEL_FONT = "'Microsoft YaHei',sans-serif"


def plate(stem, title, subtitle):
    figure = Fig(stem, title)
    label = partial(figure.text, font=LABEL_FONT, halo=False)
    label(64, 142, subtitle, size=23, color=MUTED)
    return figure, label


def note(figure, label, text):
    figure.marker(64, 704, 1024, 46, AMBER_PALE)
    label(82, 736, text, size=22, color=INK)


def ch00_swd():
    figure, label = plate("ch00-swd-four-wires", "烧录先接通这四条线", "BluePill / F103C8；按接口丝印确认线序，不按排针位置猜。")
    figure.rect(80, 195, 340, 400, color=BLUE_D, fill=BLUE_FILL)
    figure.rect(732, 195, 340, 400, color=GREEN_D, fill=GREEN_FILL)
    label(250, 243, "ST-Link", size=32, color=BLUE_D, anchor="middle", weight="bold")
    label(902, 243, "目标板 F103C8", size=30, color=GREEN_D, anchor="middle", weight="bold")
    for position, (left, right, color) in enumerate([
        ("SWDIO", "PA13 / SWDIO", BLUE_D),
        ("SWCLK", "PA14 / SWCLK", GREEN_D),
        ("GND", "GND", INK),
        ("3V3 / VTref", "3.3 V", AMBER_STROKE),
    ]):
        height = 300 + position * 78
        label(105, height + 8, left, size=25, color=color)
        label(754, height + 8, right, size=25, color=color)
        figure.circle(402, height, 6, color=color, fill=WHITE)
        figure.circle(750, height, 6, color=color, fill=WHITE)
        figure.line(412, height, 738, height, color=color, sw=3.2)
    label(576, 636, "先共地，再核对信号与电压", size=30, anchor="middle", weight="bold")
    note(figure, label, "3V3 的供电 / 参考电压职能依下载器型号确认；板子保留 Serial Wire。")
    return figure


def ch00_uart():
    figure, label = plate("ch00-uart-crossing", "串口收发要交叉", "USB-TTL 选 3.3 V 电平；本图只连接信号与共地。")
    figure.rect(80, 205, 300, 375, color=BLUE_D, fill=BLUE_FILL)
    figure.rect(772, 205, 300, 375, color=GREEN_D, fill=GREEN_FILL)
    label(230, 255, "F103C8", size=34, color=BLUE_D, anchor="middle", weight="bold")
    label(922, 255, "USB-TTL", size=32, color=GREEN_D, anchor="middle", weight="bold")
    for height, left, right in [(330, "PA9 / TX", "TX"), (425, "PA10 / RX", "RX"), (530, "GND", "GND")]:
        label(110, height + 8, left, size=28)
        label(802, height + 8, right, size=28)
    figure.arrow(382, 330, 768, 425, color=BLUE_D, sw=4, bend=0)
    figure.arrow(768, 330, 382, 425, color=GREEN_D, sw=4, bend=0)
    figure.line(382, 530, 768, 530, color=INK, sw=3)
    figure.rect(480, 363, 190, 40, color=MUTED, fill=WHITE, double=False)
    label(575, 392, "交叉，不相连", size=22, anchor="middle")
    label(576, 625, "115200 · 8N1       AT  →  OK", size=31, anchor="middle", weight="bold")
    note(figure, label, "TX 接对端 RX；图示应答来自例程预期，尚无本轮上板记录。")
    return figure


def ch05_printf():
    figure, label = plate("ch05-printf-hook", "printf 的字节从哪里出去", "格式化由 C 库完成；把字节送到哪里，由底层钩子决定。")
    for position, (text, color, fill) in enumerate([
        ("printf", BLUE_D, BLUE_FILL), ("newlib 格式化", GREEN_D, GREEN_FILL), ("_write", AMBER_STROKE, AMBER_PALE)
    ]):
        left = 72 + position * 345
        figure.doc(left, 215, 270, 145, color)
        figure.panel(left + 15, 247, 240, 66, fill)
        label(left + 135, 289, text, size=29, color=color, anchor="middle", weight="bold")
        if position < 2:
            figure.arrow(left + 280, 285, left + 333, 285, color=color, bend=0)
    figure.line(900, 364, 900, 420, color=AMBER_STROKE)
    figure.line(240, 420, 900, 420, color=AMBER_STROKE)
    for center, title, detail, color in [
        (240, "USART", "写串口寄存器", BLUE_D),
        (570, "SWO / ITM", "调试输出通道", GREEN_D),
        (900, "Semihosting", "经调试器回 PC", AMBER_STROKE),
    ]:
        figure.arrow(center, 420, center, 475, color=color, bend=0)
        figure.rect(center - 140, 480, 280, 132, color=color, fill=WHITE)
        label(center, 526, title, size=28, color=color, anchor="middle", weight="bold")
        label(center, 569, detail, size=25, anchor="middle")
    note(figure, label, "这里画的是可选出口；实际工程必须提供相应实现与运行条件。")
    return figure


def ch06_size():
    figure, label = plate("ch06-size-two-budgets", "data 为什么占两份空间", "沿用本章 size 算例：text = 280 B，data = 12 B，bss = 32 B。")
    for height, title, blocks, total in [
        (250, "Flash", [(280, "text 280 B", BLUE_D, BLUE_FILL), (12, "", AMBER_STROKE, AMBER_PALE)], "292 B"),
        (475, "RAM", [(12, "data 12 B", AMBER_STROKE, AMBER_PALE), (32, "bss 32 B", GREEN_D, GREEN_FILL)], "44 B"),
    ]:
        label(80, height - 35, title, size=33, weight="bold")
        cursor = 250
        for amount, text, color, fill in blocks:
            width = amount * (2.0 if title == "Flash" else 13.0)
            figure.rect(cursor, height, width, 95, color=color, fill=fill)
            if text:
                label(cursor + width / 2, height + 57, text, size=25, color=color, anchor="middle", weight="bold")
            cursor += width
        label(1000, height + 57, total, size=31, anchor="middle", weight="bold")
    figure.arrow(823, 345, 328, 468, color=AMBER_STROKE, bend=-0.07)
    label(415, 403, "data 初值复制到 RAM", size=26, color=AMBER_STROKE, anchor="middle", weight="bold")
    label(827, 230, "data 12 B", size=23, color=AMBER_STROKE, anchor="middle")
    label(576, 647, "Flash = text + data       RAM = data + bss", size=29, anchor="middle")
    note(figure, label, "两条使用各自比例尺；栈 / 堆预留是否计入，仍查链接脚本与 map。")
    return figure


def ch07_dependencies():
    figure, label = plate("ch07-header-dependency", "漏一条边，就会留下旧固件", "头文件变化要传到目标文件；依赖关系决定局部重建范围。")
    positions = [(90, 215, "main.c", BLUE_D), (90, 480, "board.h", RED), (440, 330, "main.o", GREEN_D), (810, 330, "blink.elf", AMBER_STROKE)]
    for left, top, title, color in positions:
        figure.doc(left, top, 240, 125, color)
        label(left + 120, top + 70, title, size=30, color=color, anchor="middle", weight="bold")
    figure.arrow(335, 280, 435, 355, color=BLUE_D, bend=0)
    figure.arrow(335, 520, 435, 425, color=RED, bend=0)
    figure.arrow(690, 395, 805, 395, color=AMBER_STROKE, bend=0)
    label(380, 565, "这条依赖不能漏", size=27, color=RED, weight="bold")
    label(576, 650, "-MMD -MP  →  生成 .d  →  Make 读回依赖", size=29, anchor="middle")
    note(figure, label, "箭头沿变化传播方向绘制；图外的目标仍按自己的依赖决定是否重建。")
    return figure


def ch10_preemption():
    figure, label = plate("ch10-preemption-timeline", "同级等候，高一级先执行", "F407 · PRIGROUP=4（3 抢占 + 1 子）；已使能，未屏蔽。")
    figure.arrow(300, 182, 1080, 182, color=INK, bend=0)
    label(1080, 214, "时间（非等比例）", size=23, anchor="end")
    for position, title, color in [(445, "EXTI9_5 请求", AMBER_STROKE), (585, "EXTI1 请求", GREEN_D)]:
        label(position, 244, title, size=24, color=color, anchor="middle")
        figure.line(position, 250, position, 645, color=color, sw=1.4, dash="5 7")
    for top, title, priority, color in [
        (260, "EXTI0", "抢占 2 / 子 0", BLUE_D),
        (410, "EXTI1", "抢占 1 / 子 0", GREEN_D),
        (560, "EXTI9_5", "抢占 2 / 子 1", AMBER_STROKE),
    ]:
        label(70, top + 35, title, size=31, color=color, weight="bold")
        label(70, top + 70, priority, size=24, color=color)
        figure.line(300, top + 38, 1080, top + 38, color=MUTED, sw=1.2)
    for left, width, title in [(300, 285, "运行"), (750, 160, "续跑")]:
        figure.rect(left, 260, width, 76, color=BLUE_D, fill=BLUE_FILL)
        label(left + width / 2, 309, title, size=32, color=BLUE_D, anchor="middle", weight="bold")
    figure.rect(585, 260, 165, 76, color=MUTED, fill=GRAY_FILL, dash="7 6")
    label(667, 309, "暂停", size=30, color=MUTED, anchor="middle")
    figure.rect(585, 410, 165, 76, color=GREEN_D, fill=GREEN_FILL)
    label(667, 459, "运行", size=32, color=GREEN_D, anchor="middle", weight="bold")
    figure.rect(445, 560, 465, 76, color=AMBER_STROKE, fill=AMBER_PALE, dash="7 6")
    label(677, 609, "挂起：仍在等待", size=30, color=AMBER_STROKE, anchor="middle")
    figure.rect(910, 560, 170, 76, color=AMBER_STROKE, fill=AMBER_PALE)
    label(995, 609, "运行", size=32, color=AMBER_STROKE, anchor="middle", weight="bold")
    figure.arrow(585, 341, 585, 404, color=GREEN_D, bend=0)
    label(605, 382, "抢占", size=24, color=GREEN_D)
    figure.arrow(750, 404, 750, 341, color=BLUE_D, bend=0)
    label(770, 382, "返回断点", size=24, color=BLUE_D)
    figure.arrow(910, 341, 910, 554, color=AMBER_STROKE, bend=0)
    label(930, 434, "ISR0 退出", size=24, color=AMBER_STROKE)
    label(576, 684, "ISR0 → ISR1 → ISR0（续）→ ISR9_5", size=30, anchor="middle", weight="bold")
    note(figure, label, "只画执行顺序，不表示耗时；同抢占级不能靠子优先级打断 ISR。")
    return figure


def ch13_checks():
    figure, label = plate("ch13-frame-validation", "帧尾出现后，还要过三道检查", "0x00 只结束一段编码字节；收到分隔符不等于收到合法命令。")
    for position, (title, detail, color, fill) in enumerate([
        ("COBS 解码", "恢复 raw 字节", BLUE_D, BLUE_FILL),
        ("核对长度", "raw = length + 8", AMBER_STROKE, AMBER_PALE),
        ("核对 CRC", "覆盖头与 payload", GREEN_D, GREEN_FILL),
    ]):
        left = 75 + position * 350
        figure.gate(left, 245, 290, 275, color, str(position + 1))
        figure.panel(left + 8, 350, 274, 130, fill)
        label(left + 145, 397, title, size=31, color=color, anchor="middle", weight="bold")
        label(left + 145, 446, detail, size=24, anchor="middle")
        if position < 2:
            figure.arrow(left + 300, 300, left + 340, 300, color=color, bend=0)
        figure.arrow(left + 145, 526, left + 145, 578, color=RED, bend=0)
    figure.line(220, 590, 920, 590, color=RED)
    label(576, 643, "任一检查失败 → 丢弃并计数；类型 / 版本另按协议检查", size=25, color=RED, anchor="middle")
    note(figure, label, "容量链：raw 最大 72 B → COBS 最大 73 B → 加帧尾共 74 B。")
    return figure


def ch14_completion():
    figure, label = plate("ch14-two-completions", "两个 TC，对应两个完成时刻", "最后一字节离开内存，与最后停止位离开引脚，是两个边界。")
    figure.doc(75, 205, 225, 125, BLUE_D)
    label(187, 277, "内存缓冲", size=30, color=BLUE_D, anchor="middle", weight="bold")
    for left, title, color in [(430, "USART DR", AMBER_STROKE), (790, "移位寄存器", GREEN_D)]:
        figure.rect(left, 205, 280, 125, color=color, fill=WHITE)
        label(left + 140, 277, title, size=29, color=color, anchor="middle", weight="bold")
    figure.arrow(310, 265, 420, 265, color=BLUE_D, bend=0)
    figure.arrow(715, 265, 780, 265, color=AMBER_STROKE, bend=0)
    figure.arrow(100, 490, 1070, 490, color=INK, bend=0)
    figure.line(385, 410, 385, 590, color=BLUE_D, dash="8 7")
    figure.line(900, 410, 900, 590, color=GREEN_D, dash="8 7")
    label(385, 398, "DMA TC", size=31, color=BLUE_D, anchor="middle", weight="bold")
    label(900, 398, "USART TC", size=31, color=GREEN_D, anchor="middle", weight="bold")
    figure.rect(390, 455, 505, 70, color=AMBER_STROKE, fill=AMBER_PALE)
    label(642, 499, "移位寄存器仍在发送", size=29, anchor="middle")
    label(385, 633, "最后字节已写 DR", size=25, color=BLUE_D, anchor="middle")
    label(900, 633, "停止位已发完", size=25, color=GREEN_D, anchor="middle")
    note(figure, label, "RS-485 切方向、断电或睡眠前，等待 USART TC；本图时距不按比例。")
    return figure


def ch14_lifetime():
    figure, label = plate("ch14-buffer-lifetime", "DMA 还在搬，缓冲区就得还在", "自动局部数组：作用域必须覆盖 DMA 使用期与后续软件访问。")
    figure.rect(64, 181, 1024, 238, color=RED, fill=WHITE)
    label(86, 219, "提前返回", size=28, color=RED, weight="bold")
    for height, title in [(276, "数组有效期"), (345, "DMA 访问")]:
        label(90, height, title, size=25)
    figure.rect(290, 246, 260, 40, color=BLUE_D, fill=BLUE_FILL)
    figure.rect(340, 315, 210, 40, color=GREEN_D, fill=GREEN_FILL)
    figure.rect(550, 315, 460, 40, color=RED, fill=RED_FILL)
    figure.line(550, 237, 550, 368, color=RED, dash="8 7")
    label(340, 236, "启动", size=22, anchor="middle")
    label(550, 236, "返回", size=22, color=RED, anchor="middle")
    label(1010, 304, "搬完", size=22, anchor="end")
    label(780, 345, "仍在访问失效的数组", size=24, color=RED, anchor="middle", weight="bold")
    label(780, 394, "下一次调用可能复用这片存储区", size=24, color=RED, anchor="middle")
    figure.rect(64, 445, 1024, 238, color=GREEN_D, fill=WHITE)
    label(86, 484, "等待访问结束后返回", size=28, color=GREEN_D, weight="bold")
    for height, title in [(552, "数组有效期"), (621, "DMA 访问")]:
        label(90, height, title, size=25)
    figure.rect(290, 522, 720, 40, color=BLUE_D, fill=BLUE_FILL)
    figure.rect(340, 591, 470, 40, color=GREEN_D, fill=GREEN_FILL)
    figure.line(810, 510, 810, 645, color=GREEN_D, dash="8 7")
    figure.line(1010, 510, 1010, 645, color=BLUE_D, dash="8 7")
    label(340, 512, "启动", size=22, anchor="middle")
    label(810, 512, "DMA 停止", size=22, color=GREEN_D, anchor="middle")
    label(1010, 512, "返回", size=22, color=BLUE_D, anchor="middle")
    label(910, 659, "软件也已用完", size=22, color=GREEN_D, anchor="middle")
    note(figure, label, "普通模式示意；静态数组仍不能提前重用，循环缓冲须先停止传输。")
    return figure


def ch15_settling():
    figure, label = plate("ch15-sampling-settle", "采样时间要留给电容充电", "F407 算例模型：τ = 408 ns；器件常数是假设值，精确值待手册复核。")
    figure.line(155, 575, 155, 230, color=INK)
    figure.arrow(155, 575, 1060, 575, color=INK, bend=0)
    figure.line(155, 255, 1060, 255, color=GREEN_D, dash="8 7")
    label(1055, 237, "输入电压", size=24, color=GREEN_D, anchor="end")
    points = [(155 + index * 8, 575 - 320 * (1 - math.exp(-(index * 8) / 75))) for index in range(111)]
    figure.stroke(points, color=BLUE_D, sw=4)
    for left, title, detail, color in [
        (181, "3 周期", "142.9 ns，充电不足", RED),
        (890, "84 周期", "4.0 µs，超过 9.01τ", GREEN_D),
    ]:
        figure.line(left, 275, left, 585, color=color, dash="7 6")
        label(left if left > 300 else 365, 640 if left > 300 else 360, title, size=30, color=color, weight="bold")
        label(left if left > 300 else 365, 675 if left > 300 else 400, detail, size=22, color=color, anchor="end" if left > 300 else "start")
    label(520, 493, "t > 9.01τ   →   选不小于所需时间的 SMP 档", size=25)
    note(figure, label, "曲线为零初值充电模型；只画采样阶段，不包含后续 SAR 转换时间。")
    return figure


def ch16_jedec():
    figure, label = plate("ch16-jedec-byte-lanes", "读 ID 时，第一字节不是厂商号", "W25Q64 的 0x9F 事务；主机每发一个字节，也同时收回一个字节。")
    label(70, 269, "MOSI", size=29, color=BLUE_D, weight="bold")
    label(70, 449, "MISO", size=29, color=GREEN_D, weight="bold")
    for position, (sent, received) in enumerate([("9F", "忽略"), ("FF", "EF"), ("FF", "40"), ("FF", "17")]):
        left = 235 + position * 210
        figure.rect(left, 220, 185, 90, color=BLUE_D, fill=BLUE_FILL)
        figure.rect(left, 400, 185, 90, color=GREEN_D, fill=GREEN_FILL if position else GRAY_FILL)
        label(left + 92, 278, sent, size=34, color=BLUE_D, anchor="middle", weight="bold")
        label(left + 92, 458, received, size=32, color=GREEN_D if position else MUTED, anchor="middle", weight="bold")
        figure.arrow(left + 92, 322, left + 92, 383, color=MUTED, bend=0)
        label(left + 92, 545, f"rx[{position}]", size=25, anchor="middle")
    figure.stroke([(185, 595), (220, 595), (220, 640), (1065, 640), (1065, 595), (1090, 595)], color=RED, sw=3)
    label(85, 636, "CS", size=29, color=RED, weight="bold")
    label(645, 610, "一次连续的 CS 低电平", size=26, color=RED, anchor="middle")
    note(figure, label, "从 rx[1] 拼 EF 40 17；读走 RXNE，收尾等 BSY=0 再拉高 CS。")
    return figure


def ch17_erase_units():
    figure, label = plate("ch17-parameter-erase-units", "双备份先分开擦除单位", "两份记录只分开地址还不够；擦除范围决定它们能否互相兜底。")
    for left, title, color in [(70, "同一扇区", RED), (620, "独立页 / 扇区", GREEN_D)]:
        label(left + 230, 225, title, size=32, color=color, anchor="middle", weight="bold")
    figure.rect(75, 280, 455, 255, color=RED, fill=RED_FILL)
    figure.rect(625, 280, 220, 255, color=GREEN_D, fill=GREEN_FILL)
    figure.rect(865, 280, 220, 255, color=BLUE_D, fill=BLUE_FILL)
    for left, title in [(105, "A"), (325, "B"), (650, "A"), (890, "B")]:
        figure.doc(left, 325, 160, 140, INK)
        label(left + 80, 407, title, size=39, anchor="middle", weight="bold")
    for offset in range(0, 420, 50):
        figure.line(95 + offset, 510, 145 + offset, 300, color=RED, sw=2)
    label(300, 603, "擦一处，两份一起受损", size=27, color=RED, anchor="middle")
    figure.arrow(975, 555, 975, 615, color=BLUE_D, bend=0)
    label(855, 663, "擦备份 B，保留有效 A", size=27, color=GREEN_D, anchor="middle")
    note(figure, label, "F103C8 可用两页；F407 要另留扇区，空间代价须先在布局中计算。")
    return figure


def ch18_backup():
    figure, label = plate("ch18-backup-power-island", "主电源掉了，谁还在供电", "备份域能保留什么，要同时看芯片型号、VBAT 与写保护。")
    figure.rect(70, 235, 360, 350, color=BLUE_D, fill=BLUE_FILL)
    label(250, 288, "主电源 VDD", size=34, color=BLUE_D, anchor="middle", weight="bold")
    figure.chip(165, 345, 170, 130, BLUE_D)
    label(250, 422, "CPU / SRAM", size=25, color=BLUE_D, anchor="middle")
    label(250, 545, "掉电后不保证保留", size=26, anchor="middle")
    figure.rect(650, 235, 430, 350, color=GREEN_D, fill=GREEN_FILL)
    label(865, 288, "备份域", size=34, color=GREEN_D, anchor="middle", weight="bold")
    label(865, 370, "RTC + 备份寄存器", size=29, anchor="middle")
    label(865, 435, "F407：另有 4 KB BKPSRAM", size=25, anchor="middle")
    label(865, 505, "F103C8：没有备份 SRAM", size=24, anchor="middle")
    figure.line(500, 345, 590, 345, color=AMBER_STROKE, sw=5)
    figure.line(515, 369, 575, 369, color=AMBER_STROKE, sw=3)
    figure.arrow(545, 384, 645, 460, color=AMBER_STROKE, bend=0)
    label(545, 315, "VBAT", size=27, color=AMBER_STROKE, anchor="middle", weight="bold")
    label(576, 650, "写之前解除 DBP；BDRST 会复位备份域", size=30, anchor="middle")
    note(figure, label, "本图只讲掉电保留；VBAT 也失电就不能保留，不表示所有复位都保留。")
    return figure


def ch19_debug_freeze():
    figure, label = plate("ch19-debug-watchdog-freeze", "断点停住时，看门狗也可能停了", "F407：DBGMCU_APB1_FZ 的 bit11 / bit12 分别冻结 WWDG / IWDG。")
    for top, title, fill, color in [(230, "调试冻结打开", BLUE_FILL, BLUE_D), (465, "独立运行实验", GREEN_FILL, GREEN_D)]:
        label(80, top - 25, title, size=30, color=color, weight="bold")
        figure.arrow(80, top + 80, 1065, top + 80, color=INK, bend=0)
        figure.rect(250, top + 25, 600, 100, color=color, fill=fill)
        label(550, top + 86, "内核停住 / WDG 暂停" if top == 230 else "任务卡住 / WDG 继续倒数", size=31, color=color, anchor="middle")
    label(920, 275, "不复位", size=28, color=BLUE_D, weight="bold")
    label(920, 510, "超时复位", size=28, color=GREEN_D, weight="bold")
    label(576, 658, "烧录 → 断开调试 → 断电重上电 → 注入故障", size=29, anchor="middle")
    note(figure, label, "冻结位可能跨系统复位保留；调试时不复位，不能代替独立运行验证。")
    return figure


def ch20_optimization():
    figure, label = plate("ch20-optimization-symbols", "优化后，函数与断点会挪位置", "本章 GNU Arm 10.3.1 宿主实验；两份对象都带 -g3。")
    for left, title, color, fill, lines in [
        (75, "-Og", BLUE_D, BLUE_FILL, [("scale", "0x0A B"), ("sum_bytes", "0x16 B")]),
        (630, "-O2", GREEN_D, GREEN_FILL, [("scale", "内联到 main"), ("sum_bytes", "0x18 B")]),
    ]:
        label(left + 220, 223, title, size=39, color=color, anchor="middle", weight="bold")
        figure.doc(left, 265, 450, 275, color)
        for position, (name, value) in enumerate(lines):
            height = 310 + position * 110
            figure.panel(left + 18, height - 5, 414, 76, fill)
            label(left + 35, height + 26, name, size=29, color=color, weight="bold")
            label(left + 410, height + 54, value, size=26, anchor="end")
    figure.arrow(525, 388, 625, 388, color=AMBER_STROKE, bend=0)
    label(295, 612, "line 7 → 0x0C", size=30, color=BLUE_D, anchor="middle")
    label(850, 612, "line 7 → 0x00", size=30, color=GREEN_D, anchor="middle")
    note(figure, label, "-g3 不禁止内联；地址与字节数只属于本章这份实验，不是通用常数。")
    return figure


def ch22_delay():
    figure, label = plate("ch22-delay-tick-phase", "delay 一拍，不一定等足一拍", "1 kHz tick；两次调用都到下一个 tick 边界成为就绪。")
    for top, called, title in [(300, 300, "较早调用"), (520, 660, "较晚调用")]:
        label(75, top - 70, title, size=28, weight="bold")
        figure.arrow(150, top, 1060, top, color=INK, bend=0)
        for left, text in [(230, "tick k"), (800, "tick k+1")]:
            figure.line(left, top - 35, left, top + 35, color=MUTED, dash="6 5")
            label(left, top + 78, text, size=25, anchor="middle")
        figure.rect(called, top - 25, 800 - called, 50, color=BLUE_D, fill=BLUE_FILL)
        figure.arrow(called, top - 95, called, top - 31, color=BLUE_D, bend=0)
        label(called, top - 109, "vTaskDelay(1)", size=26, color=BLUE_D, anchor="middle")
        figure.circle(800, top, 8, color=GREEN_D, fill=GREEN_FILL)
        label(815, top - 52, "变为就绪", size=25, color=GREEN_D)
    label(576, 664, "等待区间 (0, 1] ms；真正运行还要等待调度", size=29, anchor="middle")
    note(figure, label, "固定周期用计划唤醒点；图示忽略 tick 回绕，只说明调用相位的差别。")
    return figure


def ch23_float_frame():
    figure, label = plate("ch23-fpu-frame-cost", "浮点现场，会让任务栈变厚", "FreeRTOS ARM_CM4F 端口；按已保存上下文计数，不含额外对齐余量。")
    for left, title, blocks in [
        (85, "基本现场", [(8, "硬件核心帧 · 8 字", BLUE_D, BLUE_FILL), (9, "软件核心帧 · 9 字", GREEN_D, GREEN_FILL)]),
        (640, "浮点现场", [(26, "硬件扩展帧 · 26 字", BLUE_D, BLUE_FILL), (25, "软件帧 · 25 字", GREEN_D, GREEN_FILL)]),
    ]:
        label(left + 210, 221, title, size=34, anchor="middle", weight="bold")
        cursor = 270
        for amount, text, color, fill in blocks:
            height = amount * 6.5
            figure.rect(left, cursor, 420, height, color=color, fill=fill)
            label(left + 210, cursor + height / 2 + 9, text, size=27, color=color, anchor="middle", weight="bold")
            cursor += height
        label(left + 210, cursor + 50, "17 字 = 68 B" if left == 85 else "51 字 = 204 B", size=32, anchor="middle", weight="bold")
    label(296, 533, "EXC_RETURN bit4 = 1", size=27, color=BLUE_D, anchor="middle")
    label(296, 591, "新任务首帧另含对齐：18 字", size=25, anchor="middle")
    note(figure, label, "扩展帧含 s0–s15 / FPSCR；软件另存 s16–s31，懒堆叠可能先只留空间。")
    return figure


def ch24_from_isr():
    figure, label = plate("ch24-fromisr-deferred-switch", "FromISR 唤醒后，切换先排队", "Cortex-M4F；只有唤醒了更高优先级任务，才请求 PendSV。")
    for position, (title, color, fill) in enumerate([
        ("正在处理 ISR", BLUE_D, BLUE_FILL), ("异常退出边界", AMBER_STROKE, AMBER_PALE), ("PendSV", GREEN_D, GREEN_FILL)
    ]):
        left = 80 + position * 350
        figure.rect(left, 235, 290, 105, color=color, fill=fill)
        label(left + 145, 300, title, size=28, color=color, anchor="middle", weight="bold")
        if position < 2:
            figure.arrow(left + 300, 286, left + 340, 286, color=color, bend=0)
    figure.stroke([(110, 390), (110, 600), (365, 600)], color=BLUE_D, sw=3)
    for height, text in [(415, "队列入项"), (485, "置唤醒 flag"), (555, "末尾统一 yield")]:
        label(145, height, text, size=27, color=BLUE_D)
    figure.arrow(380, 550, 640, 550, color=AMBER_STROKE, bend=0)
    label(510, 500, "挂起请求", size=29, color=AMBER_STROKE, anchor="middle")
    figure.arrow(650, 550, 920, 420, color=GREEN_D, bend=0)
    label(925, 525, "保存 / 选任务 / 恢复", size=24, color=GREEN_D, anchor="middle")
    label(576, 660, "满队列立即报错；FromISR 没有阻塞等待参数", size=29, anchor="middle")
    note(figure, label, "PendSV 等更高优先级异常退场后执行；调用者仍须满足 ISR 优先级约束。")
    return figure


def ch25_fragmentation():
    figure, label = plate("ch25-total-vs-largest", "总空闲足够，也可能分配失败", "几何示意：图中块大小包含管理头与对齐；不是实验日志。")
    label(80, 230, "同一片堆，按地址排列", size=30, weight="bold")
    cursor = 80
    for width, title, color, fill in [
        (260, "空闲 768 B", GREEN_D, GREEN_FILL),
        (230, "已用", RED, RED_FILL),
        (260, "空闲 768 B", GREEN_D, GREEN_FILL),
        (250, "已用", RED, RED_FILL),
    ]:
        figure.rect(cursor, 280, width, 130, color=color, fill=fill)
        label(cursor + width / 2, 355, title, size=27, color=color, anchor="middle", weight="bold")
        cursor += width
    figure.rect(230, 510, 500, 95, color=BLUE_D, fill=BLUE_FILL)
    label(480, 570, "申请：1024 B 连续载荷", size=30, color=BLUE_D, anchor="middle", weight="bold")
    figure.line(770, 525, 850, 595, color=RED, sw=5)
    figure.line(850, 525, 770, 595, color=RED, sw=5)
    label(576, 661, "总空闲 1536 B；最大连续块只有 768 B", size=31, anchor="middle")
    note(figure, label, "跨着已用块的两个洞不能合并；总量、水位与最大连续块要分别看。")
    return figure


def ch34_cache_neighbors():
    figure, label = plate("ch34-cache-line-neighbor", "invalidate 会碰到同一行的邻居", "M7 的 D-Cache 行 32 B；维护以整行为单位，不只影响缓冲区里的字节。")
    label(80, 223, "共享一行：有丢更新风险", size=31, color=RED, weight="bold")
    figure.rect(80, 270, 1000, 120, color=RED, fill=RED_FILL)
    figure.rect(80, 270, 250, 120, color=AMBER_STROKE, fill=AMBER_PALE)
    figure.rect(330, 270, 500, 120, color=BLUE_D, fill=BLUE_FILL)
    label(205, 340, "脏邻居变量", size=29, color=AMBER_STROKE, anchor="middle")
    label(580, 340, "窄 DMA 缓冲", size=31, color=BLUE_D, anchor="middle")
    label(955, 340, "余量", size=29, anchor="middle")
    figure.arrow(580, 415, 580, 465, color=RED, bend=0)
    label(580, 500, "整行 invalidate：邻居未写回的更新也会丢", size=29, color=RED, anchor="middle")
    figure.rect(80, 550, 1000, 100, color=GREEN_D, fill=GREEN_FILL)
    label(580, 611, "缓冲独占完整 cache 行：32 B 对齐 + 整数行长度", size=29, color=GREEN_D, anchor="middle", weight="bold")
    note(figure, label, "本图只解释共享行危险；完整 RX / TX 交接还要遵循正文的方向与所有权规则。")
    return figure


def ch41_configuration():
    figure, label = plate("ch41-configure-save-reboot", "改配置、保存、重启是三件事", "EEPROM 双槽示意；configure 立即改 RAM，save 才持久化。")
    for left, title, color in [(80, "RAM 当前值", BLUE_D), (780, "已保存值", GREEN_D)]:
        figure.doc(left, 240, 290, 205, color)
        label(left + 145, 302, title, size=31, color=color, anchor="middle", weight="bold")
        label(left + 145, 377, "新配置" if left == 80 else "有效快照", size=33, anchor="middle")
    figure.arrow(390, 300, 760, 300, color=AMBER_STROKE, bend=0)
    label(575, 267, "save + 完成提交", size=29, color=AMBER_STROKE, anchor="middle")
    figure.arrow(760, 420, 390, 420, color=GREEN_D, bend=0)
    label(575, 464, "重启加载有效槽", size=29, color=GREEN_D, anchor="middle")
    figure.rect(90, 545, 975, 106, color=RED, fill=RED_FILL)
    label(577, 589, "改了没 save → 断电后加载旧值", size=30, color=RED, anchor="middle", weight="bold")
    label(577, 629, "提交标记未完成 → 不选这次写入的新槽", size=27, anchor="middle")
    note(figure, label, "NVS 单 blob 另按自身 commit 机制；本图不表示两平台有相同回退语义。")
    return figure


def ch45_boundaries():
    figure, label = plate("ch45-first-failed-boundary", "先找到第一处不成立的边界", "以灯不闪为例：每走一步留一项证据，一次只改变一个条件。")
    stages = [
        (80, 220, "能读目标 ID？", "否 → 查供电 / 共地 / SWD", BLUE_D),
        (430, 350, "下载成功？", "否 → 查烧录日志 / 目标型号", AMBER_STROKE),
        (780, 480, "从 Flash 运行？", "否 → 查 BOOT0 / 复位", GREEN_D),
    ]
    for position, (left, top, title, detail, color) in enumerate(stages):
        figure.rect(left, top, 290, 115, color=color, fill=WHITE)
        label(left + 145, top + 66, title, size=28, color=color, anchor="middle", weight="bold")
        label(left + 145, top - 23, detail, size=21, color=color, anchor="middle")
        if position < 2:
            figure.arrow(left + 294, top + 70, left + 342, top + 170, color=INK, bend=0)
            label(left + 308, top + 126, "是", size=22)
    label(576, 668, "前三项成立，再查 GPIO 时钟、引脚与 LED 极性", size=29, anchor="middle")
    note(figure, label, "这条树只对应入门点灯；其他现象回分诊表，不能跳过区分证据直接改参数。")
    return figure


FIGS = {
    "ch00-swd-four-wires": ch00_swd,
    "ch00-uart-crossing": ch00_uart,
    "ch05-printf-hook": ch05_printf,
    "ch06-size-two-budgets": ch06_size,
    "ch07-header-dependency": ch07_dependencies,
    "ch10-preemption-timeline": ch10_preemption,
    "ch13-frame-validation": ch13_checks,
    "ch14-two-completions": ch14_completion,
    "ch14-buffer-lifetime": ch14_lifetime,
    "ch15-sampling-settle": ch15_settling,
    "ch16-jedec-byte-lanes": ch16_jedec,
    "ch17-parameter-erase-units": ch17_erase_units,
    "ch18-backup-power-island": ch18_backup,
    "ch19-debug-watchdog-freeze": ch19_debug_freeze,
    "ch20-optimization-symbols": ch20_optimization,
    "ch22-delay-tick-phase": ch22_delay,
    "ch23-fpu-frame-cost": ch23_float_frame,
    "ch24-fromisr-deferred-switch": ch24_from_isr,
    "ch25-total-vs-largest": ch25_fragmentation,
    "ch34-cache-line-neighbor": ch34_cache_neighbors,
    "ch41-configure-save-reboot": ch41_configuration,
    "ch45-first-failed-boundary": ch45_boundaries,
}


def main():
    STAGE.mkdir(parents=True, exist_ok=True)
    for stem, builder in FIGS.items():
        save(builder(), str(STAGE / f"{stem}.svg"))
    print(f"wrote {len(FIGS)} reading plates")


if __name__ == "__main__":
    main()
