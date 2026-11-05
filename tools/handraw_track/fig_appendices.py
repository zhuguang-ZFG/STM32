# -*- coding: utf-8 -*-
"""Appendix A–F knowledge-track figures (handraw grammar, real appendix facts)."""
from hd import *


# ============================== Appendix A ==============================
def app_a_invariants():
    f = Fig("app-a-invariants", "先写四条不变量 / four invariants first")
    items = [
        ("1", GREEN_D, "DMA 正在写的区域", "应用不能同时改写"),
        ("2", BLUE_D, "Size 是首个未写位置", "仅契约 A 才等于本轮长度"),
        ("3", AMBER_STROKE, "交给业务的是新增区间", "不是整块数组冒充一帧"),
        ("4", RED, "消费者跟不上要计数", "静默覆盖 ≠ 可靠接收"),
    ]
    y = 150
    for num, c, a, b in items:
        f.circle(96, y + 28, 28, color=c, fill=WHITE, sw=3)
        f.htext(96, y + 36, num, size=28, color=c, anchor="middle", weight="bold")
        f.rect(140, y, 900, 72, color=c, fill=WHITE, sw=2.5)
        f.htext(170, y + 32, a, size=28, color=c, weight="bold")
        f.text(170, y + 58, b, size=22, color=MUTED)
        y += 92
    f.htext(W / 2, 560, "先写不变量，再选契约 A 或 B；两类代码拼在一起最容易丢字节",
            size=24, color=BLUE_D, anchor="middle", weight="bold", hl=True)
    return f


def app_a_contract_a():
    f = Fig("app-a-contract-a", "契约 A：Normal + 每次重新武装 / contract A")
    f.rect(70, 140, 480, 420, color=GREEN, fill=WHITE, sw=3)
    f.htext(310, 180, "契约 A · Normal DMA", size=30, color=GREEN_D,
            anchor="middle", weight="bold")
    f.multi(100, 230, [
        "适合：命令行 / 中低吞吐",
        "每次 IDLE → 一整块连续数据",
        "关键：关闭 HT，且每次",
        "  重新武装后再关一次 HT",
        "RX_DMA_CAP = 128",
        "ring_write → uart_rx_arm()",
    ], size=26, color=INK, lh=42)
    f.rect(600, 140, 480, 420, color=RED, fill=WHITE, sw=3)
    f.htext(840, 180, "空窗与误用", size=30, color=RED, anchor="middle", weight="bold")
    f.multi(630, 230, [
        "复制+重新武装期间",
        "  新字节可触发 ORE",
        "吞吐高 / 连续流 → 改契约 B",
        "只在启动时关一次 HT",
        "  → 半缓冲提前结束",
        "  → 后半帧被下一轮覆盖",
    ], size=26, color=INK, lh=42)
    f.htext(W / 2, 610, "调大缓冲区掩盖不了空窗；连续流请用契约 B",
            size=24, color=MUTED, anchor="middle")
    return f


def app_a_contract_b():
    f = Fig("app-a-contract-b", "契约 B：Circular + 按位置取增量 / contract B")
    # ring sketch
    f.circle(300, 340, 160, color=BLUE, fill=WHITE, sw=4)
    f.htext(300, 250, "old_pos", size=24, color=GREEN_D, anchor="middle", weight="bold")
    f.htext(300, 430, "Size / pos", size=24, color=RED, anchor="middle", weight="bold")
    f.arrow(300, 270, 300, 400, color=AMBER_STROKE, sw=3)
    f.htext(300, 340, "环", size=36, color=BLUE_D, anchor="middle", weight="bold")
    f.rect(560, 150, 520, 420, color=BLUE, fill=WHITE, sw=3)
    f.multi(590, 200, [
        "启动一次，不再次 ReceiveToIdle",
        "pos > old_pos → 连续新区间",
        "pos < old_pos → 尾段 + 头段",
        "pos == old_pos → 去重（HT≈IDLE）",
        "重新启动会重置 DMA 位置",
        "  → old_pos 失去意义",
    ], size=26, color=INK, lh=44)
    f.htext(W / 2, 620, "连续流：DMA 不停；应用只推进 old_pos",
            size=24, color=MUTED, anchor="middle")
    return f


def app_a_isr_boundary():
    f = Fig("app-a-isr-boundary", "ISR 与业务层边界 / ISR vs application")
    cols = [
        ("ISR 可做", GREEN_D, ["有界拷贝到环", "dropped_bytes++", "记 ORE/FE/NE", "FromISR 通知（优先级合规）"]),
        ("ISR 禁止", RED, ["解析 JSON", "拿互斥量阻塞", "长日志打印", "业务状态机推进"]),
        ("可观察状态", BLUE_D, ["DMA 写位置", "软件写/读位置", "队列满计数", "UART 错误计数"]),
    ]
    cw, gap = 340, 24
    x0 = (W - (cw * 3 + gap * 2)) / 2
    for i, (title, c, lines) in enumerate(cols):
        x = x0 + i * (cw + gap)
        f.rect(x, 150, cw, 380, color=c, fill=WHITE, sw=3)
        f.htext(x + cw / 2, 200, title, size=30, color=c, anchor="middle", weight="bold")
        f.multi(x + 28, 260, lines, size=26, color=INK, lh=48)
    f.htext(W / 2, 580, "FreeRTOS：UART/DMA IRQ 优先级须满足 configMAX_SYSCALL_INTERRUPT_PRIORITY",
            size=22, color=MUTED, anchor="middle")
    return f


def app_a_verify():
    f = Fig("app-a-verify", "最小验证矩阵 / minimal verification matrix")
    rows = [
        ("不同长度命令", "完整入队", "非整帧 IDLE 冒充业务帧"),
        ("人为制造 ORE", "接收能恢复", "恢复后无静默丢计"),
        ("HT + IDLE 近发", "无重复切片", "pos==old_pos 去重在"),
        ("消费者故意慢", "dropped_bytes↑", "无静默覆盖"),
    ]
    f.rect(70, 140, 1010, 70, color=INK, fill=GRAY_FILL, sw=2)
    f.htext(200, 185, "刺激", size=26, color=INK, anchor="middle", weight="bold")
    f.htext(520, 185, "期望可见结果", size=26, color=INK, anchor="middle", weight="bold")
    f.htext(860, 185, "不证明什么", size=26, color=INK, anchor="middle", weight="bold")
    y = 220
    colors = [GREEN, BLUE, AMBER_STROKE, RED]
    for (a, b, c), col in zip(rows, colors):
        f.rect(70, y, 1010, 72, color=col, fill=WHITE, sw=2)
        f.text(200, y + 44, a, size=24, color=INK, anchor="middle")
        f.text(520, y + 44, b, size=24, color=INK, anchor="middle")
        f.text(860, y + 44, c, size=22, color=MUTED, anchor="middle")
        y += 80
    return f


# ============================== Appendix B ==============================
def app_b_four_rows():
    f = Fig("app-b-four-rows", "先和账对上的四行 / four rows before the list")
    rows = [
        ("gpio-blink", "PC13 低电平点亮", "极性反了 / 把亮度要求搬到普通脚"),
        ("timer-pwm", "72 MHz·PSC71·ARR999 → 1 kHz", "示波见 500 Hz 或 2 kHz"),
        ("uart-dma-idle", "USART1 115200 BRR 0x271", "把 0.16% 误当本 USART 误差"),
        ("can-bxcan", "APB1 36 MHz·预分频9 → 500k", "分析仪停在 450 kbit/s"),
    ]
    y = 145
    for name, ok, bad in rows:
        f.rect(70, y, 1010, 88, color=BLUE, fill=WHITE, sw=2.5)
        f.htext(100, y + 36, name, size=26, color=BLUE_D, weight="bold")
        f.text(100, y + 68, "对上：" + ok, size=22, color=GREEN_D)
        f.text(560, y + 68, "对不上：" + bad, size=20, color=RED)
        y += 100
    f.htext(W / 2, 590, "四行对不上，不要加下一条总线",
            size=26, color=INK, anchor="middle", weight="bold", hl=True)
    return f


def app_b_channel_desc():
    f = Fig("app-b-channel-desc", "通道与描述符再对三行 / channel & descriptor")
    cols = [
        ("spi-flash", GREEN_D, ["0x9F → EF 40 17", "BR=010 @72 MHz → SCK 9 MHz", "全 0/FF = 接线或模式错"]),
        ("usb-cdc", BLUE_D, ["USBPRE=0 → 48 MHz", "配置集 67 字节", "VID/PID 0x1209/0x0001"]),
        ("freertos-task", AMBER_STROKE, ["栈深单位是字", "128 字 = 512 字节", "当成字节 → 一创建就 HardFault"]),
    ]
    cw, gap = 340, 24
    x0 = (W - (cw * 3 + gap * 2)) / 2
    for i, (t, c, lines) in enumerate(cols):
        x = x0 + i * (cw + gap)
        f.rect(x, 150, cw, 360, color=c, fill=WHITE, sw=3)
        f.htext(x + cw / 2, 210, t, size=28, color=c, anchor="middle", weight="bold")
        f.multi(x + 28, 280, lines, size=24, color=INK, lh=50)
    f.htext(W / 2, 570, "第三表：请求号 · 描述符长度 · 栈的单位",
            size=24, color=MUTED, anchor="middle")
    return f


def app_b_run_order():
    f = Fig("app-b-run-order", "推荐跑法五步 / useful order")
    steps = [
        ("1", "先闭环", "gpio → exti → timer", GREEN_D),
        ("2", "再加一条外设", "uart · i2c · spi · adc", BLUE_D),
        ("3", "再谈状态", "rtc · iap · can · usb", AMBER_STROKE),
        ("4", "并发最后", "freertos-task", RED),
        ("5", "旧库单独", "spl-f1-blink（勿混 HAL）", MUTED),
    ]
    x = 60
    for num, title, detail, c in steps:
        f.rect(x, 180, 200, 300, color=c, fill=WHITE, sw=3)
        f.circle(x + 100, 240, 28, color=c, fill=WHITE, sw=3)
        f.htext(x + 100, 248, num, size=28, color=c, anchor="middle", weight="bold")
        f.htext(x + 100, 310, title, size=26, color=c, anchor="middle", weight="bold")
        f.multi(x + 20, 360, detail.split(" · ") if " · " in detail else [detail],
                size=20, color=INK, lh=32, anchor="start")
        # fix multi for short strings
        x += 215
    f.htext(W / 2, 540, "调度问题与驱动问题分开：裸机行为可解释后，才上 RTOS",
            size=24, color=MUTED, anchor="middle")
    return f


def app_b_delivery():
    f = Fig("app-b-delivery", "每个例程的交付记录 / delivery record")
    fields = [
        ("料号 / 板", "丝印与来源"),
        ("工具", "IDE · 编译器 · Cube 标签"),
        ("接线", "电源 · 共地 · 外设脚"),
        ("期望", "可测量的频率/字节/状态"),
        ("实测", "仪器读数 · 错误寄存器"),
        ("边界", "未覆盖的失败路径"),
        ("复现", "干净工程到观察的最短路"),
    ]
    y = 145
    for i, (a, b) in enumerate(fields):
        col = [GREEN, BLUE, AMBER_STROKE, RED][i % 4]
        f.rect(70, y, 300, 52, color=col, fill=GRAY_FILL, sw=2)
        f.htext(220, y + 34, a, size=24, color=INK, anchor="middle", weight="bold")
        f.rect(380, y, 700, 52, color=col, fill=WHITE, sw=2)
        f.text(410, y + 34, b, size=24, color=MUTED)
        y += 58
    return f


# ============================== Appendix C ==============================
def app_c_discipline():
    f = Fig("app-c-discipline", "答案怎么用 / how to use the answers")
    cols = [
        ("先自己做", GREEN_D, ["合上答案页", "写可观察结果", "记下不确定点"]),
        ("再对照", BLUE_D, ["对关键数字", "对边界句", "对“不证明什么”"]),
        ("禁止", RED, ["背答案当理解", "跳过仪器步骤", "改料号却留旧公式"]),
    ]
    cw, gap = 340, 24
    x0 = (W - (cw * 3 + gap * 2)) / 2
    for i, (t, c, lines) in enumerate(cols):
        x = x0 + i * (cw + gap)
        f.rect(x, 160, cw, 340, color=c, fill=WHITE, sw=3)
        f.htext(x + cw / 2, 220, t, size=32, color=c, anchor="middle", weight="bold")
        f.multi(x + 36, 290, lines, size=26, color=INK, lh=52)
    f.htext(W / 2, 560, "附录 C 是核对表，不是替你做实验的脚本",
            size=26, color=MUTED, anchor="middle")
    return f


def app_c_early_checks():
    f = Fig("app-c-early-checks", "前几章自测焦点 / early-chapter check focus")
    items = [
        ("00–02", "学习环 · 工具链 · 时钟树入口", GREEN_D),
        ("03–05", "GPIO 极性 · EXTI · 1 kHz PWM 算术", BLUE_D),
        ("06–08", "BRR · I2C 地址 · SPI 模式/BR", AMBER_STROKE),
        ("09–11", "采样时间 · CNDTR · IWDG 1 s", RED),
    ]
    y = 160
    for tag, body, c in items:
        f.rect(70, y, 180, 80, color=c, fill=GRAY_FILL, sw=2)
        f.htext(160, y + 50, tag, size=28, color=c, anchor="middle", weight="bold")
        f.rect(260, y, 820, 80, color=c, fill=WHITE, sw=2)
        f.text(290, y + 50, body, size=26, color=INK)
        y += 95
    return f


def app_c_bus_system():
    f = Fig("app-c-bus-system", "总线到系统的核对轴 / bus → system axis")
    cols = [
        ("总线", GREEN_D, ["UART 空闲≠帧", "CAN 环回≠ACK", "USB 枚举≠兼容"]),
        ("存储/启动", BLUE_D, ["页擦除粒度", "IAP 跳转向量", "损坏镜像拒跳"]),
        ("并发/功耗", AMBER_STROKE, ["FromISR 优先级", "Stop 唤醒时钟", "看门狗喂谁"]),
        ("排错", RED, ["CFSR 先读", "证据链分层", "改一处只验证一处"]),
    ]
    cw, gap = 258, 16
    x0 = (W - (cw * 4 + gap * 3)) / 2
    for i, (t, c, lines) in enumerate(cols):
        x = x0 + i * (cw + gap)
        f.rect(x, 150, cw, 380, color=c, fill=WHITE, sw=3)
        f.htext(x + cw / 2, 210, t, size=30, color=c, anchor="middle", weight="bold")
        f.multi(x + 24, 280, lines, size=24, color=INK, lh=48)
    return f


def app_c_not_proof():
    f = Fig("app-c-not-proof", "答对数字 ≠ 产品证据 / right number ≠ product proof")
    f.rect(100, 160, 950, 120, color=GREEN, fill=WHITE, sw=3)
    f.htext(W / 2, 210, "自测答对：公式、寄存器名、边界句能对上",
            size=28, color=GREEN_D, anchor="middle", weight="bold")
    f.htext(W / 2, 250, "证明你读懂了章节契约", size=24, color=MUTED, anchor="middle")
    f.arrow(W / 2, 290, W / 2, 350, color=AMBER_STROKE, sw=3)
    f.rect(100, 360, 950, 180, color=RED, fill=WHITE, sw=3)
    f.multi(W / 2, 420, [
        "不证明：量产公差 · 全主机兼容 · 最坏响应 · 安全启动",
        "那些要另开验收卡，附录 C 不替你签收",
    ], size=26, color=INK, anchor="middle", lh=48)
    return f


# ============================== Appendix D ==============================
def app_d_lookup():
    f = Fig("app-d-lookup", "术语怎么查 / how to look up a term")
    steps = [
        ("1", "先定领域", "时钟？总线？RTOS？"),
        ("2", "对章节", "术语表分组 ≈ 章主题"),
        ("3", "回正文锚点", "公式/寄存器在章内"),
        ("4", "再对附录 E", "文档号 · Rev · 许可"),
    ]
    x = 70
    for num, a, b in steps:
        f.rect(x, 180, 250, 280, color=BLUE, fill=WHITE, sw=3)
        f.circle(x + 125, 250, 30, color=BLUE_D, fill=WHITE, sw=3)
        f.htext(x + 125, 258, num, size=30, color=BLUE_D, anchor="middle", weight="bold")
        f.htext(x + 125, 330, a, size=26, color=INK, anchor="middle", weight="bold")
        f.text(x + 125, 380, b, size=20, color=MUTED, anchor="middle")
        x += 270
    f.htext(W / 2, 530, "术语表给定义与对照，不替代 RM/DS 原文",
            size=26, color=MUTED, anchor="middle")
    return f


def app_d_clusters():
    f = Fig("app-d-clusters", "术语分组地图 / glossary clusters")
    cells = [
        ("时钟与复位", GREEN_D), ("GPIO / 复用", GREEN_D),
        ("中断与异常", BLUE_D), ("定时器 / PWM", BLUE_D),
        ("UART·I2C·SPI", AMBER_STROKE), ("CAN / USB", AMBER_STROKE),
        ("ADC·DAC·DMA", RED), ("Flash / 低功耗", RED),
        ("RTOS / 并发", MUTED), ("以太网 / MQTT", MUTED),
        ("调试", INK), ("工程习惯", INK),
    ]
    for i, (name, c) in enumerate(cells):
        r, col = divmod(i, 4)
        x = 90 + col * 255
        y = 150 + r * 120
        f.rect(x, y, 240, 95, color=c, fill=WHITE, sw=2.5)
        f.htext(x + 120, y + 55, name, size=24, color=c, anchor="middle", weight="bold")
    return f


def app_d_pin_table():
    f = Fig("app-d-pin-table", "表末四格：数字怎样钉住 / four cells that pin a number")
    cells = [
        ("可订购料号", "丝印全名；H7 还要修订号", GREEN_D),
        ("文档号 / 章", "RM/DS/AN + Rev 或章节", BLUE_D),
        ("寄存器 / 公式", "写哪些域、哪条除法", AMBER_STROKE),
        ("算术结果", "代入后的值与误差", RED),
    ]
    y = 150
    for title, body, c in cells:
        f.rect(80, y, 990, 85, color=c, fill=WHITE, sw=3)
        f.htext(120, y + 52, title, size=28, color=c, weight="bold")
        f.text(420, y + 52, body, size=24, color=INK)
        y += 100
    f.htext(W / 2, 590, "空一格，数字就还只是线索",
            size=26, color=MUTED, anchor="middle")
    return f


def app_d_not_rm():
    f = Fig("app-d-not-rm", "术语表不是手册 / glossary ≠ reference manual")
    f.rect(80, 160, 480, 360, color=GREEN, fill=WHITE, sw=3)
    f.htext(320, 220, "术语表提供", size=30, color=GREEN_D, anchor="middle", weight="bold")
    f.multi(120, 290, ["中英对照与短定义", "与章节主题对齐的分组", "指向正文/附录 E 的线索"],
            size=26, color=INK, lh=50)
    f.rect(600, 160, 480, 360, color=RED, fill=WHITE, sw=3)
    f.htext(840, 220, "术语表不提供", size=30, color=RED, anchor="middle", weight="bold")
    f.multi(640, 290, ["电气极限与时序闭式", "全寄存器位域表", "替代你手边的 RM/DS"],
            size=26, color=INK, lh=50)
    return f


# ============================== Appendix E ==============================
def app_e_layers():
    f = Fig("app-e-layers", "四层来源 / four source layers")
    layers = [
        ("1", "规范与芯片手册", "DS · RM · PM · 协议规范", GREEN_D),
        ("2", "厂商代码与 AN", "某一版、某一料上的一种做法", BLUE_D),
        ("3", "社区与开源实现", "找坑、比风格；结论≠规范", AMBER_STROKE),
        ("4", "本书原创", "教学顺序与实验；参数回指 1–3", RED),
    ]
    y = 145
    for num, a, b, c in layers:
        f.circle(110, y + 40, 32, color=c, fill=WHITE, sw=3)
        f.htext(110, y + 48, num, size=28, color=c, anchor="middle", weight="bold")
        f.rect(160, y, 900, 80, color=c, fill=WHITE, sw=2.5)
        f.htext(190, y + 34, a, size=28, color=c, weight="bold")
        f.text(190, y + 62, b, size=22, color=MUTED)
        y += 95
    return f


def app_e_snapshot():
    f = Fig("app-e-snapshot", "快照规则 / snapshot rules")
    rows = [
        ("手册引用", "至少文档号；会变的事实还要 Rev/图/表/章"),
        ("GitHub", "冻在 tag 或完整 commit；“今天 main 一样”不算"),
        ("社区文章", "访问日期 + 用途；只是线索"),
        ("复现笔记", "料号 · 丝印 · Cube 包 · 编译器 · 时钟"),
    ]
    y = 150
    for a, b in rows:
        f.rect(70, y, 260, 90, color=BLUE_D, fill=GRAY_FILL, sw=2)
        f.htext(200, y + 55, a, size=26, color=BLUE_D, anchor="middle", weight="bold")
        f.rect(340, y, 740, 90, color=BLUE, fill=WHITE, sw=2)
        f.text(370, y + 55, b, size=22, color=INK)
        y += 105
    return f


def app_e_pin_number():
    f = Fig("app-e-pin-number", "一笔数字怎样才算钉住 / when a number is pinned")
    # 115200 pattern
    f.htext(W / 2, 160, "115200 格子的范例（USART1 @ APB2 72 MHz）",
            size=28, color=INK, anchor="middle", weight="bold")
    f.multi(W / 2, 230, [
        "公式 fPCLK / (16 × baud) → 39.0625",
        "BRR = 0x271 · 分频误差 0",
        "只写“0.16% 误差”、无 USART 号无 BRR → 格子没钉住",
        "那 0.16% 是 36 MHz 行，或丢掉 72 MHz 小数的结果",
    ], size=26, color=INK, anchor="middle", lh=48)
    f.rect(120, 460, 910, 100, color=AMBER_STROKE, fill=AMBER_FILL, sw=2)
    f.htext(W / 2, 520, "料号 + 时钟入口 + 寄存器域 + 算术，四格齐才算钉住",
            size=26, color=INK, anchor="middle", weight="bold")
    return f


def app_e_license():
    f = Fig("app-e-license", "许可边界 / license boundary")
    rows = [
        ("docs/ · 原创图文", "CC BY 4.0", GREEN_D),
        ("assets/photos/ 五张第三方实拍", "CC0 ×2 · CC BY-SA 4.0 ×2 · MIT ×1", BLUE_D),
        ("examples/ · tools/ · 代码片段", "MIT", AMBER_STROKE),
        ("ST / Arm / 第三方手册与源码", "不转载；只链文档号与必要事实", RED),
    ]
    y = 150
    for a, b, c in rows:
        f.rect(70, y, 1010, 90, color=c, fill=WHITE, sw=3)
        f.htext(100, y + 55, a, size=26, color=c, weight="bold")
        f.text(620, y + 55, b, size=24, color=INK)
        y += 105
    return f


def app_e_fill_cell():
    f = Fig("app-e-fill-cell", "把一格填满 / what fills one cell")
    headers = ["格子", "写什么", "500 kbit/s 范例"]
    f.rect(60, 140, 1060, 60, color=INK, fill=GRAY_FILL, sw=2)
    f.htext(160, 180, headers[0], size=24, color=INK, anchor="middle", weight="bold")
    f.htext(480, 180, headers[1], size=24, color=INK, anchor="middle", weight="bold")
    f.htext(860, 180, headers[2], size=24, color=INK, anchor="middle", weight="bold")
    rows = [
        ("可订购料号", "丝印全名", "F103C8T6 上的 bxCAN"),
        ("时钟", "进入公式的时钟", "APB1 = 36 MHz"),
        ("寄存器", "域名与取值", "预分频9 · BS1=5 · BS2=2"),
        ("算术", "一次除法", "36e6/(9×8)=500000"),
        ("证伪", "仪器读数推翻", "450k → 10tq·预分频8"),
    ]
    y = 210
    cols = [GREEN, BLUE, AMBER_STROKE, RED, MUTED]
    for (a, b, c), col in zip(rows, cols):
        f.rect(60, y, 1060, 60, color=col, fill=WHITE, sw=2)
        f.text(160, y + 38, a, size=22, color=INK, anchor="middle")
        f.text(480, y + 38, b, size=22, color=INK, anchor="middle")
        f.text(860, y + 38, c, size=20, color=MUTED, anchor="middle")
        y += 65
    return f


# ============================== Appendix F ==============================
def app_f_stars():
    f = Fig("app-f-stars", "星标多 ≠ 该读 / stars ≠ should-read")
    f.rect(80, 160, 480, 360, color=RED, fill=WHITE, sw=3)
    f.htext(320, 230, "星标只说明", size=30, color=RED, anchor="middle", weight="bold")
    f.multi(120, 300, ["人多 · 曝光高", "不等于匹配你的问题", "不等于许可已核过"],
            size=26, color=INK, lh=50)
    f.rect(600, 160, 480, 360, color=GREEN, fill=WHITE, sw=3)
    f.htext(840, 230, "该不该读只看", size=30, color=GREEN_D, anchor="middle", weight="bold")
    f.multi(640, 300, ["有没有你要的 .h", "有没有那个函数", "能冻到 SHA / tag"],
            size=26, color=INK, lh=50)
    return f


def app_f_lane():
    f = Fig("app-f-lane", "选一条仓库车道读到底 / pick one repo lane")
    steps = ["选树", "读文件", "冻 SHA", "写引用", "实验卡"]
    x = 90
    for i, s in enumerate(steps):
        f.rect(x, 260, 170, 140, color=BLUE, fill=WHITE, sw=3)
        f.htext(x + 85, 340, s, size=28, color=BLUE_D, anchor="middle", weight="bold")
        if i < len(steps) - 1:
            f.arrow(x + 175, 330, x + 210, 330, color=AMBER_STROKE, sw=3)
        x += 215
    f.htext(W / 2, 180, "不要同时开五条仓“看看热闹”",
            size=28, color=INK, anchor="middle", weight="bold", hl=True)
    f.htext(W / 2, 480, "星标表是地图，不是阅读清单的替身",
            size=24, color=MUTED, anchor="middle")
    return f


def app_f_six_facts():
    f = Fig("app-f-six-facts", "六个只有读源码才拿得到 / six facts from source")
    facts = [
        "Cube 许可是配料表",
        "CMSIS 内联在头文件",
        "libopencm3 把手册翻成址",
        "lwIP pbuf 是链不是拷",
        "FreeRTOS 就绪表在 tasks.c",
        "Zephyr device.h 是 DT 投影",
    ]
    for i, s in enumerate(facts):
        r, c = divmod(i, 3)
        x = 80 + c * 350
        y = 170 + r * 180
        col = [GREEN, BLUE, AMBER_STROKE, RED, MUTED, INK][i]
        f.rect(x, y, 330, 140, color=col, fill=WHITE, sw=3)
        f.htext(x + 165, y + 80, s, size=24, color=col, anchor="middle", weight="bold")
    return f


def app_f_ask_before():
    f = Fig("app-f-ask-before", "提问之前先做五件事 / five things before asking")
    items = [
        ("1", "读 README / ISSUE 模板"),
        ("2", "冻到具体 commit"),
        ("3", "最小复现工程"),
        ("4", "贴仪器/日志原文"),
        ("5", "说明已排除的路径"),
    ]
    y = 150
    for num, body in items:
        f.circle(120, y + 36, 28, color=BLUE_D, fill=WHITE, sw=3)
        f.htext(120, y + 44, num, size=26, color=BLUE_D, anchor="middle", weight="bold")
        f.rect(170, y, 900, 72, color=BLUE, fill=WHITE, sw=2.5)
        f.htext(200, y + 46, body, size=28, color=INK, weight="bold")
        y += 88
    return f


def app_f_evidence():
    f = Fig("app-f-evidence", "证据口径 / evidence rule")
    cols = [
        ("手册优先", GREEN_D, ["RM/DS 冲突时", "以适用条件为准", "开源差异写入迁移表"]),
        ("源码第二", BLUE_D, ["函数级引用", "tag/SHA 冻结", "许可读 LICENSE"]),
        ("社区第三", AMBER_STROKE, ["访问日期", "只作线索", "回手册核对"]),
        ("实验收口", RED, ["可观察结果", "写清不证明什么", "可复现步骤"]),
    ]
    cw, gap = 258, 16
    x0 = (W - (cw * 4 + gap * 3)) / 2
    for i, (t, c, lines) in enumerate(cols):
        x = x0 + i * (cw + gap)
        f.rect(x, 150, cw, 380, color=c, fill=WHITE, sw=3)
        f.htext(x + cw / 2, 210, t, size=28, color=c, anchor="middle", weight="bold")
        f.multi(x + 24, 280, lines, size=24, color=INK, lh=48)
    return f


FIGS = {
    "app-a-invariants": app_a_invariants,
    "app-a-contract-a": app_a_contract_a,
    "app-a-contract-b": app_a_contract_b,
    "app-a-isr-boundary": app_a_isr_boundary,
    "app-a-verify": app_a_verify,
    "app-b-four-rows": app_b_four_rows,
    "app-b-channel-desc": app_b_channel_desc,
    "app-b-run-order": app_b_run_order,
    "app-b-delivery": app_b_delivery,
    "app-c-discipline": app_c_discipline,
    "app-c-early-checks": app_c_early_checks,
    "app-c-bus-system": app_c_bus_system,
    "app-c-not-proof": app_c_not_proof,
    "app-d-lookup": app_d_lookup,
    "app-d-clusters": app_d_clusters,
    "app-d-pin-table": app_d_pin_table,
    "app-d-not-rm": app_d_not_rm,
    "app-e-layers": app_e_layers,
    "app-e-snapshot": app_e_snapshot,
    "app-e-pin-number": app_e_pin_number,
    "app-e-license": app_e_license,
    "app-e-fill-cell": app_e_fill_cell,
    "app-f-stars": app_f_stars,
    "app-f-lane": app_f_lane,
    "app-f-six-facts": app_f_six_facts,
    "app-f-ask-before": app_f_ask_before,
    "app-f-evidence": app_f_evidence,
}


if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        fig = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(fig, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))
