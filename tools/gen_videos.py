#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_videos.py —— 每章一张可复现的讲解幻灯 GIF。

GIF 里的字只能是 ASCII（minigfx 的 5×7 点阵）。中文旁白写在各章
``<!-- video:chNN -->`` 标记里，由本脚本 ``--patch-docs`` 写入，
和画面逐帧对应。不使用版权素材，也不生成「实拍」画面。

用法::

    python3 tools/gen_videos.py              # 写 assets/video/*.gif
    python3 tools/gen_videos.py --patch-docs # 同时刷新章节里的嵌入与旁白
    python3 tools/gen_videos.py 03           # 只生成某一章
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from minigfx import C, Canvas, Gif  # noqa: E402

W, H = 448, 252
DELAY = 140  # 1.4 s / 帧，五帧约 7 秒，循环播放


def _fit(text, scale):
    """返回不超出画布的文本；超长直接报错，避免字叠到边框外。"""
    width = len(text) * (6 + 1) * scale
    if width > W - 16:
        raise ValueError(f"文字过宽 ({width}px): {text}")
    return text


def _chrome(title, step, total):
    c = Canvas(W, H, C.BG)
    c.fill_rect(0, 0, W, 26, C.BG2)
    c.fill_rect(0, 0, 3, 26, C.CYAN)
    c.text(_fit(title, 1), 10, 9, C.TEXT, 1)
    tag = f"{step}/{total}"
    c.text(tag, W - 8 - c.text_w(tag, 1), 9, C.CYAN, 1)
    for i in range(total):
        c.fill_rect(10 + i * 16, 30, 12, 3, C.CYAN if i < step else C.STROKE)
    c.hline(0, H - 16, W, C.GRID)
    c.text("SCRIPT GIF  NOT A PHOTO", 8, H - 12, C.DIM, 1)
    c.text("STM32 KB", W - 8 - c.text_w("STM32 KB", 1), H - 12, C.DIM, 1)
    return c


def _lines(c, rows, y=46, scale=1, color=C.TEXT, dy=None):
    dy = dy or (10 * scale + 6)
    for i, (text, col) in enumerate(rows):
        if isinstance(col, tuple) and len(col) != 3:
            text, col = col, color
        c.text(_fit(text, scale), 16, y + i * dy, col, scale)


def _frame_lines(title, step, total, head, rows):
    c = _chrome(title, step, total)
    c.text(_fit(head, 2), 16, 46, C.AMBER, 2)
    body = []
    for row in rows:
        body.append((row, C.TEXT) if isinstance(row, str) else row)
    _lines(c, body, y=74, scale=1, dy=18)
    return c


def _frame_steps(title, step, total, head, labels, active):
    c = _chrome(title, step, total)
    c.text(_fit(head, 2), 16, 44, C.AMBER, 2)
    n = len(labels)
    gap = 8
    bw = (W - 24 - gap * (n - 1)) // n
    y = 78
    for i, lab in enumerate(labels):
        x = 12 + i * (bw + gap)
        on = i == active
        c.panel(x, y, bw, 52, C.PANEL2 if on else C.PANEL,
                C.CYAN if on else C.STROKE, t=2 if on else 1)
        c.text_c(_fit(lab, 1), x + bw / 2, y + 22, C.CYAN if on else C.MUTED, 1)
        if i < n - 1:
            c.fill_rect(x + bw, y + 24, gap, 2, C.CYAN if i < active else C.STROKE)
    c.text("HIGHLIGHT = THIS STEP", 16, 148, C.MUTED, 1)
    return c


def _frame_wave(title, step, total, head, bits, note):
    c = _chrome(title, step, total)
    c.text(_fit(head, 2), 16, 44, C.AMBER, 2)
    c.panel(16, 74, W - 32, 70, C.PANEL, C.STROKE)
    c.waveform(28, 84, W - 56, 50, bits, C.GREEN, t=2)
    c.text(_fit(note, 1), 16, 160, C.MUTED, 1)
    return c


def _frame_cols(title, step, total, head, left, right):
    c = _chrome(title, step, total)
    c.text(_fit(head, 2), 16, 44, C.AMBER, 2)
    for i, (name, items, col) in enumerate((left, right)):
        x = 16 + i * 212
        c.panel(x, 72, 200, 110, C.PANEL, col)
        c.fill_rect(x, 72, 200, 18, col)
        c.text_c(_fit(name, 1), x + 100, 76, C.BG, 1)
        for k, item in enumerate(items):
            c.text(_fit(item, 1), x + 10, 100 + k * 16, C.TEXT, 1)
    return c


def _frame_quiz(title, step, total, questions):
    c = _chrome(title, step, total)
    c.text("SELF TEST", 16, 44, C.AMBER, 2)
    for i, q in enumerate(questions):
        y = 74 + i * 36
        c.panel(16, y, W - 32, 30, C.PANEL, C.STROKE)
        c.text(f"{i + 1}", 26, y + 11, C.CYAN, 1)
        c.text(_fit(q, 1), 44, y + 11, C.TEXT, 1)
    return c


def build(spec_frames, title):
    total = len(spec_frames)
    gif = Gif(W, H, delay=DELAY, loop=0)
    for i, spec in enumerate(spec_frames, start=1):
        kind = spec[0]
        if kind == "lines":
            frame = _frame_lines(title, i, total, spec[1], spec[2])
        elif kind == "steps":
            frame = _frame_steps(title, i, total, spec[1], spec[2], spec[3])
        elif kind == "wave":
            frame = _frame_wave(title, i, total, spec[1], spec[2], spec[3])
        elif kind == "cols":
            frame = _frame_cols(title, i, total, spec[1], spec[2], spec[3])
        elif kind == "quiz":
            frame = _frame_quiz(title, i, total, spec[1])
        else:
            raise ValueError(kind)
        gif.add(frame)
    return gif


# 每章 5 帧。旁白与帧一一对应，写进章节，不写进 GIF。
CHAPTERS = [
    {
        "id": "00", "slug": "learn", "title": "00 LEARN STM32",
        "narr": [
            "先把路线钉死：入门四周打底，进阶六周啃外设，实战八周做能给别人看的东西。",
            "顺序别跳：环境、时钟、GPIO，然后才是串口和项目。跳步最容易在时钟上摔跤。",
            "板子选 BluePill 就够起步。手册三件套是数据手册、参考手册、编程手册。",
            "别一上来就抄整套例程。先让一颗灯按你算过的频率闪。",
            "合上书：BOOT0 拉低进哪？HAL 和寄存器差在哪一层？",
        ],
        "frames": [
            ("lines", "ONE ROADMAP", ["4 WK BASE", "6 WK PERIPH", "8 WK BUILD"]),
            ("steps", "DO NOT SKIP", ["ENV", "CLOCK", "GPIO", "UART"], 1),
            ("lines", "BRING THESE", ["BLUEPILL F103", "ST-LINK", "DS + RM + PM"]),
            ("cols", "TRAP VS HABIT", ("TRAP", ["PASTE WHOLE DEMO", "IGNORE CLOCK"], C.RED),
             ("HABIT", ["ONE LED FIRST", "READ THE BIT"], C.GREEN)),
            ("quiz", ["BOOT0 LOW = ?", "HAL LAYER = ?", "FIRST WIN = ?"]),
        ],
    },
    {
        "id": "01", "slug": "env", "title": "01 TOOLCHAIN",
        "narr": [
            "源码变成灯在闪，中间只有四步：编译、链接、烧录、复位运行。",
            "Keil、CubeIDE、PlatformIO 都能走完这四步，差别是谁帮你填启动文件。",
            "向量表第 0 项是栈顶，第 1 项才是复位入口。先时钟，再搬 .data，再清 .bss。",
            "SWD 两根线就够下载。把 PA13、PA14 让给别的功能，下次就连不上。",
            "自测：复位后 CPU 先读哪个地址？烧录口占用哪两只脚？",
        ],
        "frames": [
            ("steps", "ONE BINARY", ["CC", "LD", "FLASH", "RUN"], 2),
            ("cols", "PICK A TOOL", ("KEIL", ["MDK PROJECT", "PACK DEVICE"], C.AMBER),
             ("GCC", ["CUBEIDE", "PIO"], C.CYAN)),
            ("lines", "RESET VECTOR", ["WORD0 = STACK", "WORD1 = RESET", "THEN CLOCK"]),
            ("lines", "KEEP SWD", ["PA13 SWDIO", "PA14 SWCLK", "DO NOT REMAP"]),
            ("quiz", ["WORD0 IS ?", "WORD1 IS ?", "SWD PINS ?"]),
        ],
    },
    {
        "id": "02", "slug": "clock", "title": "02 CLOCK MAP",
        "narr": [
            "型号字母是封装和容量，不是玄学。先看数据手册首页，再翻引脚。",
            "存储器地图把 Flash、SRAM、外设分成三段。外设本质是固定地址上的寄存器。",
            "F103 常见路径：8 MHz 晶振进 PLL，乘 9，得到 72 MHz。APB1 再二分频。",
            "口诀你已经见过：先开时钟再摸寄存器。时钟没开，写入像写进虚空。",
            "自测：72 MHz 时 Flash 要几个等待？AHB 和 APB1 谁更慢？",
        ],
        "frames": [
            ("lines", "NAME THE PART", ["F103 C8 T6", "C8 = FLASH", "T6 = LQFP"]),
            ("steps", "MEMORY MAP", ["FLASH", "SRAM", "PERIPH", "SYS"], 0),
            ("lines", "F103 TREE", ["HSE 8 MHZ", "PLL X9", "SYS 72  APB1 36"]),
            ("wave", "CLOCK GATE", [0, 0, 1, 1, 1, 1, 0, 1, 1, 1], "CLK OFF = WRITE VANISHES"),
            ("quiz", ["WAIT STATES?", "APB1 VS AHB?", "GATE FIRST?"]),
        ],
    },
    {
        "id": "03", "slug": "gpio", "title": "03 GPIO LED",
        "narr": [
            "GPIO 是所有外设的大门。模式选错，后面的总线全像闹鬼。",
            "推挽能强推高、强拉低。开漏的高要靠外部上拉，适合线与和 I2C。",
            "限流电阻按 R=(Vcc-Vf)/I 来算。3.3 V 红灯大约 270 欧就够亮。",
            "BluePill 板载灯在 PC13，低电平才亮。别和共阴外接灯搞反。",
            "口诀：F1 重映射先开 AFIO。自测：按键接 GND 该上拉还是下拉？",
        ],
        "frames": [
            ("cols", "8 MODES CUT", ("OUT", ["PP LED", "OD I2C"], C.GREEN),
             ("IN", ["PULL-UP KEY", "ANALOG ADC"], C.CYAN)),
            ("wave", "PP TOGGLE", [0, 0, 1, 1, 0, 0, 1, 1, 0, 0], "HIGH AND LOW BOTH DRIVEN"),
            ("lines", "LED RESISTOR", ["R = (VCC-VF)/I", "3.3V  2.0V  5MA", "R ABOUT 270 OHM"]),
            ("lines", "BLUEPILL LED", ["PC13 ACTIVE LOW", "PA0 ACTIVE HIGH", "ENABLE GPIO CLK"]),
            ("quiz", ["OD HIGH BY ?", "PC13 ON = ?", "KEY TO GND ?"]),
        ],
    },
    {
        "id": "04", "slug": "nvic", "title": "04 NVIC EXTI",
        "narr": [
            "轮询是 CPU 不停问；中断是脚来敲门。敲门前先把 NVIC 的门打开。",
            "优先级分组决定抢占和子优先级各占几位。同组里抢占数字小的先跑。",
            "同一条 EXTI 线，同一时刻只能接一个端口。PA0 和 PB0 不能同时挂 EXTI0。",
            "中断里只许抬旗。打印、延时、再去读 I2C，都会把后来的中断堵在门外。",
            "口诀：总闸分三档。自测：EXTI0 能同时留给 PA0 和 PB0 吗？",
        ],
        "frames": [
            ("cols", "POLL VS IRQ", ("POLL", ["CPU ASKS", "WASTES TIME"], C.AMBER),
             ("IRQ", ["PIN KNOCKS", "NVIC GATES"], C.CYAN)),
            ("steps", "IRQ PATH", ["EXTI", "NVIC", "STACK", "ISR"], 2),
            ("lines", "ONE LINE", ["EXTI0 = ONE PIN", "PA0 OR PB0", "NOT BOTH"]),
            ("lines", "ISR RULE", ["SET A FLAG", "NO PRINT", "NO HAL_DELAY"]),
            ("quiz", ["WHO PREEMPTS?", "EXTI0 SHARE?", "WORK IN ISR?"]),
        ],
    },
    {
        "id": "05", "slug": "tim", "title": "05 TIMER PWM",
        "narr": [
            "定时器就是一个会自己加的计数器。CNT 碰到 ARR 就回头，这就是周期。",
            "PWM 频率看 ARR 和 PSC，占空比看 CCR。三个数各管一件事。",
            "F103 上 APB1 定时器时钟常常是 72 MHz，不是 36。倍频规则要记。",
            "呼吸灯就是让 CCR 慢慢走。输入捕获锁的是 CNT，不是脚上的电压。",
            "口诀：捕获锁的是 CNT。自测：想要 1 kHz，你先定谁？",
        ],
        "frames": [
            ("wave", "CNT TO ARR", [0, 1, 1, 1, 1, 0, 1, 1, 1, 1], "EDGE = UPDATE EVENT"),
            ("lines", "THREE NUMBERS", ["PSC DIVIDES CLK", "ARR SETS PERIOD", "CCR SETS DUTY"]),
            ("lines", "F103 TIM CLK", ["APB1 BUS 36MHZ", "TIM CLK 72MHZ", "WHEN PRESC != 1"]),
            ("steps", "BREATH", ["CCR0", "CCR UP", "CCR MAX", "CCR DN"], 1),
            ("quiz", ["DUTY FROM ?", "CAPTURE LOCKS?", "1KHZ SETS ?"]),
        ],
    },
    {
        "id": "06", "slug": "uart", "title": "06 UART FRAME",
        "narr": [
            "UART 一帧从起始位的下降沿开始，接着 8 位数据，可选校验，最后停止位。",
            "波特率是双方约好的步点。误差大了，采样点会滑出数据位。",
            "空闲中断加 DMA，适合一帧不定长。ORE 要先读 SR 再读 DR。",
            "RS485 换方向要等 TC，不能等 TXE。TXE 只表示数据进了移位寄存器。",
            "口诀：ORE 先 SR 后 DR。自测：115200 8N1 的 8 是什么？",
        ],
        "frames": [
            ("wave", "8N1 FRAME", [1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 1], "IDLE H  START L  8 DATA  STOP H"),
            ("lines", "BAUD MATCH", ["BOTH SIDES SAME", "ERROR SLIPS BIT", "SAMPLE MID-BIT"]),
            ("steps", "DMA + IDLE", ["ARM DMA", "BYTES IN", "LINE IDLE", "PARSE"], 2),
            ("cols", "TXE VS TC", ("TXE", ["DR EMPTY", "SHIFT BUSY"], C.AMBER),
             ("TC", ["FRAME DONE", "RS485 TURN"], C.GREEN)),
            ("quiz", ["START BIT LVL?", "ORE ORDER?", "8 IN 8N1?"]),
        ],
    },
    {
        "id": "07", "slug": "i2c", "title": "07 I2C BUS",
        "narr": [
            "I2C 只有两根开漏线，SCL 和 SDA，都要上拉。谁都能把线拉低，谁都不能硬推高。",
            "一次写寄存器：START、地址、寄存器地址、数据、STOP。读的时候中间是重复起始。",
            "地址 0x3C 写进 HAL 常常要左移成 0x78。漏移一位，从机永远不 ACK。",
            "总线卡死时，用 GPIO 给 SCL 打九个脉冲，再补一个 STOP，然后交还外设。",
            "口诀：读寄存器走 Mem_Read。自测：ACK 是高还是低？",
        ],
        "frames": [
            ("lines", "OPEN DRAIN", ["SCL + SDA", "EXTERNAL PULLUP", "WIRED AND"]),
            ("steps", "WRITE REG", ["STA", "ADDR", "REG", "DATA"], 1),
            ("cols", "ADDR SHIFT", ("7-BIT", ["0x3C OLED", "ON THE WIRE"], C.CYAN),
             ("HAL", ["0x78 = <<1", "W BIT IN LSB"], C.AMBER)),
            ("lines", "BUS STUCK", ["SCL 9 PULSES", "THEN A STOP", "GIVE PINS BACK"]),
            ("quiz", ["WHO MAKES HIGH?", "ACK LEVEL?", "R/W BIT?"]),
        ],
    },
    {
        "id": "08", "slug": "spi", "title": "08 SPI SHIFT",
        "narr": [
            "SPI 是全双工移位。你每送出一位，也同时收进一位。没有「只发不收」。",
            "CPOL 是空闲时的时钟电平，CPHA 决定在哪条边沿采样。四种模式先和从机对齐。",
            "片选是帧的边界。很多芯片在 NSS 拉高时才把缓冲提交。",
            "模式错了，读出来的字节会像整体挪了一位。先对模式，再怀疑接线。",
            "自测：MOSI 和 MISO 能不能接反？模式 0 的空闲时钟是高还是低？",
        ],
        "frames": [
            ("cols", "FULL DUPLEX", ("MOSI", ["MASTER OUT", "SLAVE IN"], C.GREEN),
             ("MISO", ["MASTER IN", "SLAVE OUT"], C.CYAN)),
            ("wave", "MODE 0 CLK", [0, 1, 0, 1, 0, 1, 0, 1, 0, 0], "CPOL 0  IDLE LOW"),
            ("steps", "ONE BYTE", ["NSS LOW", "8 CLKS", "NSS HIGH", "LATCH"], 0),
            ("lines", "IF IT SHIFTS", ["CHECK CPOL CPHA", "THEN WIRES", "NSS IS THE FRAME"]),
            ("quiz", ["IDLE IN MODE0?", "NSS ROLE?", "TX WITHOUT RX?"]),
        ],
    },
    {
        "id": "09", "slug": "adc", "title": "09 ADC SAR",
        "narr": [
            "SAR 从最高位开始猜。每一步用比较器决定这一位留 1 还是改 0。",
            "采样时间要盖过源阻抗。电位器电阻太大，结果会漂。",
            "12 位结果换成电压：代码乘 Vref，再除以 4096。分母是 4096 不是 4095。",
            "F103C8 没有 DAC。要输出模拟电压，换带 DAC 的型号或外接芯片。",
            "口诀：采样看阻抗，换算除 4096，C8 没有 DAC。",
        ],
        "frames": [
            ("steps", "SAR BITS", ["MSB", "BIT10", "BIT9", "LSB"], 0),
            ("lines", "SAMPLE TIME", ["RC MUST SETTLE", "BIG R = DRIFT", "ADD CYCLES"]),
            ("lines", "12-BIT SCALE", ["V = CODE*VREF", "DIVIDE BY 4096", "NOT 4095"]),
            ("cols", "DAC OR NOT", ("F103C8", ["ADC YES", "DAC NO"], C.RED),
             ("F4 / G0", ["ADC YES", "DAC ON SOME"], C.GREEN)),
            ("quiz", ["SAR STARTS AT?", "DIVISOR?", "C8 HAS DAC?"]),
        ],
    },
    {
        "id": "10", "slug": "dma", "title": "10 DMA RING",
        "narr": [
            "DMA 替 CPU 搬家。CPU 继续算，外设数据自己进内存。",
            "F1 叫通道，F4 叫流。映射表写在参考手册里，不能凭感觉选。",
            "循环模式把缓冲区当成圆环。NDTR 剩下的个数告诉你写到哪。",
            "半字传输时，半满中断按元素个数算，再乘 2 才是字节。",
            "口诀：剩下的在 NDTR。自测：循环模式谁把指针拨回去？",
        ],
        "frames": [
            ("cols", "WHO MOVES", ("CPU", ["LOAD STORE", "STALLS"], C.AMBER),
             ("DMA", ["PERIPH TO RAM", "CPU FREED"], C.CYAN)),
            ("lines", "NAME IT", ["F1 = CHANNEL", "F4 = STREAM", "SEE THE MAP"]),
            ("steps", "RING", ["NDTR FULL", "HALF", "WRAP", "IRQ"], 2),
            ("lines", "HALF WORD", ["HT COUNTS ITEMS", "BYTES = N * 2", "CACHE ON M7"]),
            ("quiz", ["F1 UNIT?", "NDTR MEANS?", "WHO WRAPS?"]),
        ],
    },
    {
        "id": "11", "slug": "rtc", "title": "11 RTC WDG",
        "narr": [
            "RTC 走在备份域。主电源掉了，VBAT 和 LSE 还能让它继续数。",
            "1 秒不要写成 625。预分频是「减到 0」再加一拍，异步加同步要对齐。",
            "IWDG 只怕喂晚。WWDG 喂早喂晚都会复位，窗口两边都是悬崖。",
            "调试时先冻住看门狗，不然一单步就复位，像程序自己爆炸。",
            "口诀：1 秒是 624 不是 625。自测：WWDG 能不能提前喂？",
        ],
        "frames": [
            ("lines", "BACKUP DOMAIN", ["LSE 32.768K", "VBAT KEEPS RTC", "NOT RESET BY NRST"]),
            ("lines", "ONE SECOND", ["PREDIV ASYNC", "PREDIV SYNC", "USE 624 NOT 625"]),
            ("cols", "TWO DOGS", ("IWDG", ["LATE = RESET", "EARLY OK"], C.AMBER),
             ("WWDG", ["EARLY RESET", "LATE RESET"], C.RED)),
            ("lines", "DEBUG FREEZE", ["FREEZE IN DBGMCU", "OR SINGLE STEP", "RESETS THE CHIP"]),
            ("quiz", ["VBAT POWERS?", "624 OR 625?", "WWDG EARLY?"]),
        ],
    },
    {
        "id": "12", "slug": "iap", "title": "12 FLASH IAP",
        "narr": [
            "Flash 先解锁，再按页或扇区擦，然后才能写。写完上锁。",
            "IAP 把芯片分成引导区和应用程序。引导区收完新固件，再跳过去。",
            "跳转前要关中断、设好栈顶、再把向量表偏移告诉内核。",
            "读保护不是玩笑。F1 的钥匙和 F4 的钥匙不一样，改之前先备份。",
            "口诀：0xA5 是 F1 的开门钥匙。自测：擦之前为什么必须解锁？",
        ],
        "frames": [
            ("steps", "WRITE FLASH", ["UNLOCK", "ERASE", "PROGRAM", "LOCK"], 1),
            ("cols", "TWO SLOTS", ("BOOT", ["SMALL", "RECEIVES"], C.CYAN),
             ("APP", ["YOUR CODE", "VECTORS"], C.GREEN)),
            ("lines", "JUMP APP", ["DISABLE IRQ", "SET MSP", "SET VTOR"]),
            ("lines", "OPTION BYTES", ["F1 KEY 0xA5", "BACKUP FIRST", "READ PROTECT"]),
            ("quiz", ["ERASE NEEDS?", "VTOR POINTS?", "JUMP SETS MSP?"]),
        ],
    },
    {
        "id": "13", "slug": "can", "title": "13 CAN BUS",
        "narr": [
            "CAN 用差分线。显性是逻辑 0，能压过隐性。所以 ID 越小越优先。",
            "仲裁是非破坏的。输的人立刻改听，赢的那帧一个位都没坏。",
            "连续五个同电平要插一位相反的填充位，好让对方还能同步。",
            "MCU 里只有控制器。收发器和两端的 120 欧，得你自己接上。",
            "口诀：TEC 到 256 就闭嘴。自测：为什么单节点会进 Bus-Off？",
        ],
        "frames": [
            ("cols", "TWO LEVELS", ("DOM 0", ["DRIVES THE BUS", "WINS ARB"], C.GREEN),
             ("REC 1", ["RELEASES BUS", "YIELDS ARB"], C.AMBER)),
            ("steps", "ARBITRATE", ["SOF", "ID BITS", "LOSER RX", "WINNER"], 1),
            ("wave", "BIT STUFF", [1, 1, 1, 1, 1, 0, 0, 0, 0, 0], "5 SAME THEN INSERT FLIP"),
            ("lines", "NEED A PHY", ["MCU = CONTROLLER", "TJA1050 OUTSIDE", "120 OHM X2"]),
            ("quiz", ["ID SMALLER?", "STUFF AFTER?", "BUS-OFF TEC?"]),
        ],
    },
    {
        "id": "14", "slug": "usb", "title": "14 USB ENUM",
        "narr": [
            "USB 主机说了算。设备只能等着被问。F103 是全速设备，不是主机。",
            "枚举就是：复位、读描述符、设地址、读配置、设配置。",
            "卡在描述符，多半是长度字段或 48 MHz 时钟不准。",
            "CDC 是虚拟串口，走批量传输。HID 是键盘鼠标那类，走中断传输，常常免驱。",
            "自测：F103 的 DP/DM 在哪两只脚？CDC 和 HID 谁更依赖驱动？",
        ],
        "frames": [
            ("lines", "FS DEVICE", ["12 MBIT/S", "HOST POLLS", "F103 DEVICE ONLY"]),
            ("steps", "ENUMERATE", ["RESET", "DESC", "ADDR", "CFG"], 1),
            ("lines", "48 MHZ", ["PLL MUST HIT 48", "OR ENUM FAILS", "CHECK PRESCALER"]),
            ("cols", "TWO CLASSES", ("CDC", ["VIRTUAL COM", "BULK"], C.CYAN),
             ("HID", ["KEY / MOUSE", "INTERRUPT"], C.GREEN)),
            ("quiz", ["F103 ROLE?", "DP DM PINS?", "HID DRIVER?"]),
        ],
    },
    {
        "id": "15", "slug": "rtos", "title": "15 FREERTOS",
        "narr": [
            "任务只有几种状态：运行、就绪、阻塞、挂起。调度器挑就绪里优先级最高的。",
            "信号量是通知，队列是搬数据，互斥量是占着别动。别用错对象。",
            "Delay 是再等一会儿。DelayUntil 是下次几点醒，周期任务用后者。",
            "定时器回调里不准睡觉，也不准等队列。那是给别的任务的时间。",
            "自测：两个同优先级任务，时间片用完发生什么？",
        ],
        "frames": [
            ("steps", "TASK STATE", ["RUN", "READY", "BLOCK", "SUSP"], 0),
            ("cols", "OBJECTS", ("QUEUE", ["MOVES DATA", "COPY BYTES"], C.CYAN),
             ("MUTEX", ["LOCKS IT", "PRIORITY"], C.AMBER)),
            ("lines", "TWO DELAYS", ["DELAY = SLIP", "UNTIL = PERIOD", "USE UNTIL"]),
            ("lines", "TIMER CB", ["NO VTASKDELAY", "NO QUEUE WAIT", "JUST A KICK"]),
            ("quiz", ["WHO RUNS?", "PERIOD API?", "SLEEP IN CB?"]),
        ],
    },
    {
        "id": "16", "slug": "lp", "title": "16 LOW POWER",
        "narr": [
            "Sleep 只停 CPU，外设还在耗电。Stop 停时钟，Standby 几乎只留备份域。",
            "进 Stop 用 WFI。醒来之后系统时钟回到默认，必须重新配置。",
            "唤醒源要在睡前准备好：EXTI、RTC 闹钟，别指望一个已经关时钟的 UART。",
            "PVD 是掉电通知，不是复位本身。你还有一小段时间把数据收好。",
            "口诀：Sleep 还在耗电，Stop 才真的睡。自测：Stop 醒来第一件事？",
        ],
        "frames": [
            ("cols", "SLEEP / STOP", ("SLEEP", ["CPU HALT", "CLOCKS ON"], C.AMBER),
             ("STOP", ["CLOCKS OFF", "WAKE + PLL"], C.CYAN)),
            ("steps", "STOP WAKE", ["WFI", "IRQ", "CLOCK", "RUN"], 2),
            ("lines", "WAKE SOURCES", ["EXTI PIN", "RTC ALARM", "NOT A DEAD UART"]),
            ("lines", "PVD", ["VOLTAGE SAG", "IRQ FIRST", "THEN YOU SAVE"]),
            ("quiz", ["LOWEST MODE?", "AFTER STOP?", "PVD IS RESET?"]),
        ],
    },
    {
        "id": "17", "slug": "debug", "title": "17 DEBUG SWO",
        "narr": [
            "SWD 两根线调试。SWO 再加一根，就能把 printf 从 ITM 送出来，不必占 UART。",
            "HardFault 时先看栈里的 PC。那条指令附近就是现场。",
            "DWT 的周期计数器能给一段代码打表，比 GPIO 翻转更细。",
            "优化打开以后，局部变量可能不在内存里。调试版和发布版要分开看。",
            "自测：SWO 占用哪只脚？Fault 里最先看的寄存器是什么？",
        ],
        "frames": [
            ("lines", "SWD + SWO", ["SWDIO SWCLK", "SWO = TRACE", "ITM PRINTF"]),
            ("steps", "HARDFAULT", ["FAULT", "STACK", "READ PC", "FIX"], 2),
            ("lines", "DWT CYCLE", ["ENABLE CYCCNT", "READ TWICE", "DELTA = TIME"]),
            ("cols", "BUILD", ("DEBUG", ["-O0", "VARS LIVE"], C.GREEN),
             ("RELEASE", ["-O2 / -OS", "CHECK MAP"], C.AMBER)),
            ("quiz", ["SWO PIN?", "FAULT LOOKS?", "CYCCNT UNIT?"]),
        ],
    },
    {
        "id": "18", "slug": "faq", "title": "18 FAQ",
        "narr": [
            "灯不亮，先看三件事：时钟开了没、电平反了没、电阻有没有。",
            "下载失败，先看 SWD 还在不在、BOOT0 是不是被拉高、线松了没。",
            "串口乱码，先看波特率、共地、TX/RX 是不是接反。",
            "中断进不去，先看 NVIC 使能、优先级、是不是在更高级里死循环。",
            "把这张表当成诊所。先对现象，再动手改代码。",
        ],
        "frames": [
            ("lines", "LED DARK", ["CLK ENABLED?", "ACTIVE LEVEL?", "RESISTOR?"]),
            ("lines", "NO DOWNLOAD", ["SWD STILL FREE?", "BOOT0 LOW?", "CABLE?"]),
            ("lines", "GARBLED UART", ["BAUD", "COMMON GND", "TX RX SWAP"]),
            ("lines", "NO IRQ", ["NVIC ENABLE", "PRIORITY", "STUCK IN ISR"]),
            ("quiz", ["FIRST LED CHK?", "BOOT0 FOR FLASH?", "GARBAGE MEANS?"]),
        ],
    },
    {
        "id": "19", "slug": "projects", "title": "19 PROJECTS",
        "narr": [
            "项目按层叠上去：灯、按键、串口、传感器，再把它们收成一个产品。",
            "每个项目只加一个新外设。一次加三个，出错时你不知道怪谁。",
            "把引脚表写在 README 里。未来的你会感谢现在的你。",
            "演示时准备一条「预期现象」。没有预期，就不算做完。",
            "自测：你的下一个项目，新增加的外设只有哪一个？",
        ],
        "frames": [
            ("steps", "STACK SKILLS", ["LED", "KEY", "UART", "SENSOR"], 3),
            ("lines", "ONE NEW PART", ["ADD A SINGLE IO", "KEEP OLD TESTS", "THEN COMBINE"]),
            ("lines", "WRITE IT DOWN", ["PIN TABLE", "BAUD", "EXPECTED BLINK"]),
            ("cols", "DONE MEANS", ("CODE", ["BUILDS", "FLASHES"], C.CYAN),
             ("PROOF", ["YOU CAN SEE", "THE EFFECT"], C.GREEN)),
            ("quiz", ["ONE CHANGE?", "PIN TABLE?", "DONE WHEN?"]),
        ],
    },
    {
        "id": "20", "slug": "refs", "title": "20 REFERENCES",
        "narr": [
            "数据手册管引脚和电气，参考手册管寄存器，编程手册管内核。",
            "文件名能认：DS 是数据手册，RM 是参考手册，PM 是编程手册。",
            "Cube 固件包是例子，不是法律。和法律冲突时，以手册为准。",
            "社区帖子要核对型号。F1 的答案抄到 H7 上，常常是错的。",
            "自测：想查 CAN 过滤器的位，该打开 DS 还是 RM？",
        ],
        "frames": [
            ("cols", "THREE BOOKS", ("DS", ["PINS", "VOLTS"], C.AMBER),
             ("RM", ["REGISTERS", "PERIPH"], C.CYAN)),
            ("lines", "FILE NAMES", ["DS = DATASHEET", "RM = REF MAN", "PM = CORE"]),
            ("lines", "CUBE IS A MAP", ["GOOD EXAMPLES", "MANUAL WINS", "IF THEY DIFFER"]),
            ("lines", "MATCH THE DIE", ["F1 NOTE != H7", "CHECK THE PART", "THEN THE REV"]),
            ("quiz", ["PIN VOLTAGE?", "FILTER BITS?", "NVIC CORE?"]),
        ],
    },
    {
        "id": "21", "slug": "boards", "title": "21 BOARD MAP",
        "narr": [
            "仓库里的板图是矢量结构图，不是实拍照片。拿它对排针，别拿它当开箱图。",
            "最小系统就那几块：电源、复位、时钟、BOOT、调试口。少一块就别怪程序。",
            "BluePill 的山寨板晶振和稳压可能缩水。现象怪时先怀疑板子。",
            "去耦电容要贴着每一组 VDD。原理图上有，焊接漏了，一样会随机复位。",
            "自测：BOOT0 悬空时，上电可能进哪种启动？",
        ],
        "frames": [
            ("lines", "DRAWN NOT SHOT", ["SVG BY SCRIPT", "NOT A PHOTO", "SEE CHAPTER 21"]),
            ("steps", "MIN SYSTEM", ["3V3", "NRST", "HSE", "SWD"], 0),
            ("lines", "BLUEPILL", ["8 MHZ HSE", "PC13 LED", "BOOT0 PULLDOWN"]),
            ("lines", "DECOUPLE", ["100NF PER VDD", "CLOSE TO PIN", "VDDA EXTRA"]),
            ("quiz", ["PHOTO OR SVG?", "BOOT0 FLOAT?", "HSE VALUE?"]),
        ],
    },
    {
        "id": "22", "slug": "sim", "title": "22 SIMULATE",
        "narr": [
            "仿真分两家：Wokwi 在浏览器里接线，Renode 在命令行里跑同一颗 Cortex-M3。",
            "每个核心示例目录里有 diagram.json 和 wokwi.toml。引脚名跟 Wokwi 板定义走，A0 就是 PA0。",
            "Renode 脚本加载官方平台 platforms/cpus/stm32f103.repl，USART1 在 PA9/PA10。",
            "当前 Wokwi 的 BluePill 模型没有 DMA。串口空闲帧和 ADC 搬运要上真板，或只看接线。",
            "口诀：仿真看现象，真板对时序。自测：PC13 的灯在 Wokwi 里要不要再外接一颗？",
        ],
        "frames": [
            ("cols", "TWO SIMS", ("WOKWI", ["BROWSER", "WIRES"], C.CYAN),
             ("RENODE", ["MONITOR", "ELF"], C.AMBER)),
            ("lines", "PIN ALIAS", ["A0 MEANS PA0", "C13 MEANS PC13", "SEE BOARD.JSON"]),
            ("lines", "RENODE F103", ["stm32f103.repl", "USART1 PA9 PA10", "PORT 3456"]),
            ("lines", "NO DMA YET", ["WOKWI DMA OFF", "UART IDLE WAITS", "ADC DMA WAITS"]),
            ("quiz", ["A6 IS WHICH?", "PC13 EXTRA LED?", "REPL FILE?"]),
        ],
    },
]


def builders():
    """供 check_assets 逐帧回放比对。"""
    out = {}
    for ch in CHAPTERS:
        out[f"ch{ch['id']}-{ch['slug']}"] = lambda ch=ch: build(ch["frames"], ch["title"])
    return out


BUILDERS = builders()


def patch_docs(root):
    docs = os.path.join(root, "docs")
    for ch in CHAPTERS:
        name = None
        prefix = ch["id"] + "-"
        for fn in os.listdir(docs):
            if fn.startswith(prefix) and fn.endswith(".md"):
                name = fn
                break
        if name is None:
            raise SystemExit(f"找不到章节文件 {prefix}*.md")
        path = os.path.join(docs, name)
        text = open(path, encoding="utf-8").read()
        gif = f"../assets/video/ch{ch['id']}-{ch['slug']}.gif"
        lines = "\n".join(f"{i}. {s}" for i, s in enumerate(ch["narr"], start=1))
        block = (
            f"<!-- video:ch{ch['id']} -->\n"
            "<p align=\"center\">\n"
            f"  <img src=\"{gif}\" width=\"640\" alt=\"第 {ch['id']} 章讲解幻灯\">\n"
            "  <br><sub>▲ 本章讲解幻灯：程序生成的 GIF"
            "（tools/gen_videos.py，可复现，不是实拍）。旁白与五帧一一对应。</sub>\n"
            "</p>\n\n"
            "**旁白（跟着画面读，大约一分钟）**\n\n"
            f"{lines}\n"
            f"<!-- /video:ch{ch['id']} -->\n"
        )
        begin = f"<!-- video:ch{ch['id']} -->"
        end = f"<!-- /video:ch{ch['id']} -->"
        if begin in text and end in text:
            pre, rest = text.split(begin, 1)
            _, post = rest.split(end, 1)
            text = pre + block + post.lstrip("\n")
        else:
            anchor = "</p>\n"
            at = text.find(anchor)
            if at < 0:
                raise SystemExit(f"{name} 没有 hero </p>，无法插入幻灯")
            at += len(anchor)
            text = text[:at] + "\n" + block + "\n" + text[at:]
        open(path, "w", encoding="utf-8").write(text)
        print(f"[doc] {name}")


def main(argv):
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    out_dir = os.path.join(root, "assets", "video")
    os.makedirs(out_dir, exist_ok=True)
    only = [a for a in argv[1:] if not a.startswith("-")]
    if "--patch-docs" in argv:
        patch_docs(root)
    for ch in CHAPTERS:
        name = f"ch{ch['id']}-{ch['slug']}"
        if only and ch["id"] not in only and name not in only:
            continue
        path = os.path.join(out_dir, name + ".gif")
        build(ch["frames"], ch["title"]).save(path)
        print(f"[ok] {name}.gif  {os.path.getsize(path)} bytes")


if __name__ == "__main__":
    main(sys.argv)
