# -*- coding: utf-8 -*-
"""Seven deterministic project planning plates: capacities are not measurements.

F103C8 capacities: DS5319. Single-slot map: chapter12/iap-bootloader.
heap_4 budget shows an explicit hypothetical allocation, not a measured map.
USB frame split: chapter14 full-speed bulk limit is 64 bytes per packet.
"""
from hd import *


def _segments(f, x, y, values, scale, h=68):
    for label, kib, color in values:
        width = kib * scale
        f.rect(x, y, width, h, color=color, fill=WHITE, sw=2.2, double=False)
        if width > 95:
            f.text(x + width / 2, y + 31, label, size=25, color=color, anchor="middle", weight="bold")
            f.text(x + width / 2, y + 59, f"{kib:g} KiB", size=22, color=MUTED, anchor="middle")
        x += width
    return x


def ab_partition():
    f = Fig("ch19-ab-partition", "同样的 46 KiB 镜像，C8 只能放一份")
    f.text(72, 143, "STM32F103C8 · 两条按同一比例绘制 · 结束地址均不包含在区间内", size=23, color=MUTED)
    scale, x0 = 8.8, 72
    limit = x0 + 64 * scale
    f.text(72, 195, "单槽 · 第 12 章", size=27, color=GREEN_D, weight="bold")
    _segments(f, x0, 220, [("Boot", 16, BLUE_D), ("", 2, AMBER_STROKE), ("APP", 46, GREEN_D)], scale)
    f.text(388, 194, "参数 2 KiB", size=22, color=AMBER_STROKE)
    f.line(386, 204, x0 + 17 * scale, 215, color=AMBER_STROKE, sw=2)
    f.text(72, 332, "16 + 2 + 46 = 64 KiB", size=27, color=GREEN_D, weight="bold")
    f.text(72, 387, "再放一份同样大小的 B 镜像", size=27, color=RED, weight="bold")
    _segments(f, x0, 411, [("Boot", 16, BLUE_D), ("", 2, AMBER_STROKE), ("A", 46, GREEN_D), ("B", 46, RED)], scale)
    f.line(limit, 214, limit, 488, color=INK, sw=2.5, dash="7 7")
    f.text(limit + 20, 321, "C8 Flash 到此", size=23, color=INK, weight="bold")
    f.text(limit + 20, 354, "0x08010000", size=24, color=INK)
    f.text(72, 526, "16 + 2 + 46 + 46 = 110 KiB", size=28, color=RED, weight="bold")
    f.text(72, 569, "B 从 0x08010000 开始，到 0x0801B800，已超出 C8 容量。", size=24, color=RED)
    f.line(72, 608, 1080, 608, color=MUTED, sw=1.3)
    f.text(72, 651, "把 46 KiB 分为 23 + 23，只说明容量可分。", size=27, color=BLUE_D, weight="bold")
    f.multi(72, 696, ["APP 必须缩小；仍需设计镜像状态、原子更新、确认与掉电恢复。", "两个槽位本身不能保证回滚，不能沿用单槽方案的结论。"], size=23, color=MUTED, lh=37)
    return f


def flash_fit():
    f = Fig("ch19-flash-fit", "先把 Flash 与 SRAM 的容量分开算")
    f.text(72, 143, "F103C8 · Flash 64 KiB / SRAM 20 KiB · 下图条长按同一容量比例", size=23, color=MUTED)
    f.text(72, 194, "Flash · 0x08000000", size=27, color=BLUE_D, weight="bold")
    f.text(500, 194, "参数 2 KiB", size=22, color=AMBER_STROKE)
    f.line(494, 201, 340, 212, color=AMBER_STROKE, sw=1.5)
    x0, scale = 72, 15.75
    _segments(f, x0, 218, [("Boot", 16, BLUE_D), ("", 2, AMBER_STROKE), ("APP", 46, GREEN_D)], scale, h=88)
    f.text(72, 346, "0x08000000", size=21, color=BLUE_D)
    f.text(324, 346, "0x08004000", size=21, color=AMBER_STROKE, anchor="middle")
    f.text(440, 387, "0x08004800", size=21, color=GREEN_D, anchor="middle")
    f.line(356, 310, 440, 310, color=GREEN_D, sw=1.5)
    f.line(440, 310, 440, 363, color=GREEN_D, sw=1.5)
    f.text(1080, 346, "0x08010000", size=21, color=INK, anchor="end")
    f.text(1080, 384, "16 + 2 + 46 = 64 KiB · APP 长度 0xB800", size=22, color=GREEN_D, anchor="end")
    f.text(72, 452, "SRAM · 0x20000000", size=27, color=BLUE_D, weight="bold")
    f.rect(x0, 476, 20 * scale, 64, color=BLUE_D, fill=WHITE, double=False)
    f.text(x0 + 10 * scale, 517, "20 KiB = 20480 B", size=25, color=BLUE_D, anchor="middle", weight="bold")
    f.text(425, 517, "结束：0x20005000（不含）", size=24, color=INK)
    f.text(72, 592, "uint8_t samples[64 * 1024]", size=27, color=RED, weight="bold")
    f.rect(x0, 617, 64 * scale, 43, color=RED, fill=WHITE, double=False)
    f.line(x0 + 20 * scale, 609, x0 + 20 * scale, 670, color=BLUE_D, sw=3, dash="6 5")
    f.text(576, 646, "65536 B > 20480 B", size=26, color=RED, anchor="middle", weight="bold")
    f.text(72, 718, "这个数组本身就已超出全部 SRAM，还没有计入其他数据、栈和堆。", size=24, color=MUTED)
    return f


def pick_ladder():
    f = Fig("ch19-pick-ladder", "选项目，先看哪一步还没有验过")
    f.text(72, 143, "每轮只新增一项不确定性；顺序随项目需求调整。", size=24, color=MUTED)
    steps = [(72, 352, "输入 / 输出", "点灯、按键或回环", BLUE_D),
             (348, 296, "一项新外设", "传感器 / 显示 / 总线", GREEN_D),
             (624, 240, "数据与时序", "DMA 所有权、吞吐、延迟", AMBER_STROKE)]
    for i, (x, y, title, note, color) in enumerate(steps):
        f.rect(x, y, 250, 114, color=color, fill=WHITE)
        f.text(x + 125, y + 43, title, size=27, color=color, anchor="middle", weight="bold")
        if i == 2:
            f.multi(x + 125, y + 75, ["DMA 所有权", "吞吐、延迟"], size=21, color=INK, anchor="middle", lh=27)
        else:
            f.text(x + 125, y + 85, note, size=21, color=INK, anchor="middle")
        if i < 2:
            nx, ny = steps[i + 1][0:2]
            f.arrow(x + 251, y + 46, nx - 8, ny + 77, color=color, bend=0)
    f.text(913, 268, "按需再加", size=25, color=BLUE_D, weight="bold")
    f.multi(913, 310, ["并发", "存储", "升级"], size=25, color=MUTED, lh=40)
    f.arrow(880, 292, 911, 292, color=BLUE_D, bend=0)
    f.line(72, 504, 1080, 504, color=MUTED, sw=1.3)
    f.text(72, 548, "需求决定芯片，主频高不等于外设齐全", size=27, color=BLUE_D, weight="bold")
    cols = [(72, "F103C8", ["Flash 64 / SRAM 20 KiB", "片内有 CAN 控制器"], BLUE_D),
            (425, "F411", ["先查具体后缀容量", "片内无 CAN 控制器"], RED),
            (778, "F407", ["先查封装与存储容量", "片内有 CAN 控制器"], GREEN_D)]
    for x, name, notes, color in cols:
        f.rect(x, 574, 302, 138, color=color, fill=WHITE)
        f.text(x + 20, 613, name, size=29, color=color, weight="bold")
        f.multi(x + 20, 651, notes, size=21, color=INK, lh=36)
    f.text(72, 750, "CAN 项目还需要外部收发器；改芯片后重查引脚、时钟与软件配置。", size=22, color=MUTED)
    return f


def iap_gates():
    f = Fig("ch19-iap-gates", "坏镜像在跳转前拒绝，运行后再确认")
    f.text(72, 143, "第 12 章的 C8 单槽布局：16 KiB Boot + 2 KiB 参数 + 46 KiB APP", size=23, color=MUTED)
    checks = [(72, "长度 / CRC", "完整且校验匹配", BLUE_D),
              (425, "目标范围", "不越 APP 槽边界", BLUE_D),
              (778, "向量入口", "栈顶、入口与布局合法", BLUE_D)]
    for i, (x, name, note, color) in enumerate(checks):
        f.rect(x, 181, 302, 113, color=color, fill=WHITE)
        f.text(x + 151, 225, name, size=29, color=color, anchor="middle", weight="bold")
        f.text(x + 151, 267, note, size=22, color=INK, anchor="middle")
        if i < 2:
            f.arrow(x + 306, 235, x + 345, 235, color=BLUE_D, bend=0)
        f.line(x + 151, 304, x + 151, 339, color=RED, sw=2)
    f.line(223, 339, 929, 339, color=RED, sw=2)
    f.arrow(576, 339, 576, 379, color=RED, bend=0)
    f.text(602, 369, "任一检查不通过", size=22, color=RED)
    f.rect(335, 388, 482, 96, color=RED, fill=WHITE)
    f.text(576, 425, "任何一项失败：拒绝启动该镜像", size=26, color=RED, anchor="middle", weight="bold")
    f.text(576, 463, "留在 Boot，提供重新下载或维护路径", size=22, color=INK, anchor="middle")
    f.text(72, 535, "全部通过", size=25, color=GREEN_D, weight="bold")
    f.arrow(243, 527, 315, 527, color=GREEN_D, bend=0)
    f.text(338, 535, "受控跳转 APP", size=27, color=GREEN_D, weight="bold")
    f.arrow(596, 527, 683, 527, color=GREEN_D, bend=0)
    f.text(706, 535, "版本 / 心跳 / 关键自检", size=26, color=GREEN_D, weight="bold")
    f.line(72, 580, 1080, 580, color=MUTED, sw=1.3)
    f.text(72, 626, "单槽 APP 被覆盖后，旧版本可能已经不存在。", size=27, color=RED, weight="bold")
    f.multi(72, 674, ["拒绝坏镜像、能重新下载，是恢复能力；不能据此声称已实现旧版本回滚。", "掉电恢复另测：传输、擦写、参数提交、首次启动各阶段中断后会怎样？"], size=23, color=MUTED, lh=40)
    return f


def milestone_triage():
    f = Fig("ch19-milestone-triage", "每个里程碑，都交出一个可观察结果")
    f.text(72, 143, "先走通最小功能；存储、升级与并发按需求加入。", size=24, color=MUTED)
    stages = [(72, "已知输入", "可重放的命令 / 信号", BLUE_D),
              (425, "单项功能", "本轮只新增一项不确定", GREEN_D),
              (778, "验收结果", "数值 / 波形 / 返回码", BLUE_D)]
    for i, (x, name, detail, color) in enumerate(stages):
        f.rect(x, 183, 302, 110, color=color, fill=WHITE)
        f.text(x + 151, 224, name, size=29, color=color, anchor="middle", weight="bold")
        f.text(x + 151, 266, detail, size=22, color=INK, anchor="middle")
        if i < 2:
            f.arrow(x + 307, 238, x + 345, 238, color=color, bend=0)
    f.line(576, 303, 576, 341, color=AMBER_STROKE, sw=2, dash="6 5")
    f.line(228, 341, 924, 341, color=AMBER_STROKE, sw=2, dash="6 5")
    for x, title, note in [(72, "需要留存？", "加存储与掉电测试"), (425, "需要升级？", "加镜像验证与恢复"), (778, "需要并发？", "加所有权与超时")]:
        f.line(x + 151, 341, x + 151, 375, color=AMBER_STROKE, sw=2, dash="6 5")
        f.rect(x, 383, 302, 104, color=AMBER_STROKE, fill=WHITE, dash="6 5", double=False)
        f.text(x + 151, 424, title, size=28, color=AMBER_STROKE, anchor="middle", weight="bold")
        f.text(x + 151, 465, note, size=23, color=INK, anchor="middle")
    f.line(72, 530, 1080, 530, color=MUTED, sw=1.3)
    rows = [(580, "范围太大", "删到一项可独立复现的功能；其余留到下一轮。", RED),
            (639, "跳过验收", "退回首次出现差异的模块，再向前集成。", BLUE_D),
            (698, "没有证据", "补输入、配置、结果与失败注入记录，再判断通过。", GREEN_D)]
    for y, title, note, color in rows:
        f.text(72, y, title, size=27, color=color, weight="bold")
        f.text(300, y, note, size=24, color=INK)
    return f


def sram_budget():
    f = Fig("ch19-sram-budget", "SRAM 预算，先避免把同一块内存算两遍")
    f.text(72, 142, "F103C8 · 20480 B · 0x20000000–0x20005000（结束不含）", size=23, color=MUTED)
    f.text(72, 184, "假设示例，非本仓库实测 map；条长按字节数绘制。", size=24, color=INK)
    x0, scale, y0 = 72, 1008 / 20480, 211
    # Categories are disjoint: ucHeap excluded from other static objects.
    allocations = [("其他静态对象", 4096, BLUE_D), ("heap_4 · ucHeap", 8192, GREEN_D),
                   ("MSP / C 堆预留", 2048, AMBER_STROKE), ("未分配", 6144, MUTED)]
    x = x0
    for label, size, color in allocations:
        width = size * scale
        f.rect(x, y0, width, 66, color=color, fill=WHITE, double=False)
        if size >= 4096:
            f.text(x + width / 2, y0 + 29, label, size=22, color=color, anchor="middle", weight="bold")
            f.text(x + width / 2, y0 + 57, f"{size} B", size=22, color=color, anchor="middle")
        x += width
    f.line(727.2, 282, 727.2, 309, color=AMBER_STROKE, sw=2)
    f.text(727.2, 309, "MSP / C 堆预留", size=22, color=AMBER_STROKE, anchor="middle")
    f.text(727.2, 339, "2048 B", size=22, color=AMBER_STROKE, anchor="middle")
    f.text(72, 378, "4096 + 8192 + 2048 + 6144 = 20480 B", size=27, color=BLUE_D, weight="bold")
    f.text(72, 421, "其他静态对象含 DMA / 全局缓冲，但不再包含下方的 ucHeap。", size=22, color=MUTED)
    f.text(72, 467, "展开同一块 ucHeap · 假设已按下列方式分配", size=25, color=GREEN_D, weight="bold")
    heap_x, heap_scale = 72, 1008 / 8192
    for label, size, color in [("动态任务栈", 4096, GREEN_D),
                                ("TCB / 队列等", 2048, BLUE_D),
                                ("heap 剩余", 2048, MUTED)]:
        width = size * heap_scale
        f.rect(heap_x, 490, width, 82, color=color, fill=WHITE, double=False)
        f.text(heap_x + width / 2, 522, label, size=24, color=color, anchor="middle", weight="bold")
        f.text(heap_x + width / 2, 557, f"{size} B", size=23, color=color, anchor="middle")
        heap_x += width
    f.text(72, 608, "TCB / 队列等一项已含管理开销；这些分配都在上条的 8192 B 内。", size=22, color=INK)
    f.text(72, 648, "ucHeap 通常在 .bss；静态创建的任务栈另按实际段位置计入，均只算一次。", size=22, color=MUTED)
    f.text(72, 693, "未分配的 6144 B 只是这个假设中的余额，不是已经验证的安全余量。", size=24, color=RED)
    f.text(72, 738, "最后用真实 map、栈水位、最小剩余 heap 与压力测试核对预算。", size=24, color=MUTED)
    return f


def usb_split():
    f = Fig("ch19-usb-split", "应用帧 133 字节，拆成 64 + 64 + 5 三包发送")
    f.text(72, 143, "项目 4 USB 采集卡 · 应用帧 = 帧头 + 序号 + 样本 + 校验 · 全速批量一包上限 64 字节",
           size=23, color=MUTED)

    # ---- ① 应用帧的组成 ----
    f.text(72, 182, "① 应用帧的组成", size=25, color=BLUE_D, weight="bold")
    parts = [(72, 220, "帧头", "0xAA 0x55 · 2 B", BLUE_D),
             (304, 212, "序号", "seq · 2 B", GREEN_D),
             (528, 388, "样本 · 64 个 × 2 字节", "128 B", AMBER_STROKE),
             (928, 152, "校验", "1 B", RED)]
    for x, w, name, sub, color in parts:
        f.rect(x, 205, w, 76, color=color, fill=WHITE, sw=2.4)
        f.text(x + w / 2, 235, name, size=23 if w > 160 else 22, color=color,
               anchor="middle", weight="bold")
        f.text(x + w / 2, 264, sub, size=18, color=INK, anchor="middle")
    # 分组括线：4 B / 128 B / 1 B
    for x0, x1, label in [(72, 516, "4 B（帧头 + 序号）"), (528, 916, "128 B"), (928, 1080, "1 B")]:
        f.line(x0, 298, x1, 298, color=MUTED, sw=1.6)
        f.line(x0, 298, x0, 306, color=MUTED, sw=1.6)
        f.line(x1, 298, x1, 306, color=MUTED, sw=1.6)
        f.text((x0 + x1) / 2, 330, label, size=20, color=MUTED, anchor="middle")
    f.text(72, 368, "4 + 128 + 1 = 133 字节", size=27, color=BLUE_D, weight="bold")
    f.text(1080, 368, "主机用 pyserial 或 pyusb 解帧", size=20, color=MUTED, anchor="end")

    # ---- ② 发送时拆包（同比例条） ----
    f.text(72, 410, "② 发送时拆包 · 全速批量一包上限 64 字节", size=25, color=BLUE_D, weight="bold")
    f.text(1080, 408, "包 3 · 5 B", size=22, color=AMBER_STROKE, anchor="end", weight="bold")
    f.line(1072, 413, 1062, 429, color=AMBER_STROKE, sw=2)
    x0, scale, by, bh = 72, 1008 / 133, 430, 70
    x = x0
    for name, kib, color in [("包 1", 64, BLUE_D), ("包 2", 64, GREEN_D), ("", 5, AMBER_STROKE)]:
        width = kib * scale
        f.rect(x, by, width, bh, color=color, fill=WHITE, sw=2.2, double=False)
        if width > 95:
            f.text(x + width / 2, by + 31, name, size=23, color=color, anchor="middle", weight="bold")
            f.text(x + width / 2, by + 59, f"{kib:g} B", size=21, color=MUTED, anchor="middle")
        x += width
    for bx, label in [(72, "0"), (72 + 64 * scale, "64"), (72 + 128 * scale, "128")]:
        f.line(bx, by + bh, bx, by + bh + 8, color=MUTED, sw=1.6)
        f.text(bx, by + bh + 28, label, size=19, color=MUTED, anchor="middle")
    f.line(1080, by + bh, 1080, by + bh + 8, color=MUTED, sw=1.6)
    f.text(72, 552, "64 + 64 + 5 = 133 字节 · 拆成三包发送 · 条长按同一比例", size=25,
           color=GREEN_D, weight="bold")

    # ---- ③ 规则与坑 ----
    f.rect(72, 585, 482, 84, color=GREEN_D, fill=WHITE, sw=2.4)
    f.text(92, 615, "端点描述符 wMaxPacketSize", size=21, color=GREEN_D, weight="bold")
    f.text(92, 645, "仍写 64，不能写 133", size=20, color=INK)
    f.rect(598, 585, 482, 84, color=RED, fill=WHITE, sw=2.4)
    f.text(618, 615, "常见坑：把 133 写成端点包长", size=21, color=RED, weight="bold")
    f.text(618, 645, "全速批量一包最多 64 字节", size=20, color=INK)

    f.htext(72, 706, "133 是应用帧长度；64 才是一包上限。拆三包发送，描述符仍写 64。",
            size=23, color=INK, weight="bold", hl=True)
    f.text(72, 742, "校验是 Checksum8，不是 CRC；USB 时钟 48 MHz 与 VID/PID 0x1209/0x0001 见第 14 章。",
           size=19, color=MUTED)
    return f


def log_ring():
    f = Fig("ch19-log-ring",
            "W25Q64 循环日志区：wr 递增、回卷只擦首扇区")
    # 扇区条
    f.text(84, 132, "LOG_BASE 起一段连续扇区：wr 顺序写，写到末尾回卷到首扇区",
           size=21, color=MUTED)
    x = 84
    y = 175
    for i in range(6):
        c = GREEN_D if i < 4 else AMBER_STROKE
        f.rect(x, y, 150, 70, color=c, fill=WHITE, sw=2.4)
        f.htext(x + 75, y + 42, f"扇区 {i}", size=19, color=c, anchor="middle")
        x += 160
    f.arrow(84 + 4 * 160 + 10, y + 90, 84 + 70, y + 90, color=INK, sw=2.4, head=8)
    f.text(84 + 4 * 160 - 240, y + 122, "wr 到末尾 → 回卷", size=18, color=MUTED)
    # 两条要点
    f.rect(84, 356, 470, 150, color=GREEN_D, fill=WHITE, sw=2.6)
    f.text(108, 392, "示例做到了", size=21, color=GREEN_D, weight="bold")
    f.text(108, 426, "记录格式固定（时间戳+温湿度×10）", size=18, color=INK)
    f.text(108, 456, "wr 地址递增，重启回到 LOG_BASE", size=18, color=INK)
    f.rect(594, 356, 470, 150, color=RED, fill=WHITE, sw=2.6)
    f.text(618, 392, "可用日志还缺", size=21, color=RED, weight="bold")
    f.text(618, 426, "逐扇区预擦 / 写完成检查 / 提交标记", size=18, color=INK)
    f.text(618, 456, "磨损均衡 / 重启扫描恢复 wr", size=18, color=INK)
    f.rect(84, 536, 980, 62, color=INK, fill=WHITE, sw=2.2)
    f.htext(W / 2, 570, "掉电保哪些记录，用断电测试确认，不靠猜",
            size=22, color=INK, anchor="middle", weight="bold", hl=True)
    return f


def la_sampling():
    f = Fig("ch19-la-sampling",
            "采 8 位并口：中断读，还是让 DMA 搬 / who moves the byte")
    f.text(84, 128, "两条实现都成立，但前置条件不同；先验证采样周期与输入保护，再谈换实现",
           size=20, color=MUTED)

    # ---- 实现 A ----
    f.rect(84, 168, 984, 150, color=GREEN_D, fill=WHITE, sw=2.4)
    f.text(108, 204, "实现 A（本章示例）：TIM 中断里读 GPIOC", size=20,
           color=GREEN_D, weight="bold")
    step = ["TIM 更新中断", "ISR 读 IDR & 0xFF", "写入缓冲"]
    for i, s in enumerate(step):
        x = 108 + i * 300
        f.rect(x, 224, 240, 52, color=GREEN_D, fill=WHITE, sw=2.0,
               double=False)
        f.text(x + 120, 256, s, size=17, color=INK, anchor="middle")
        if i:
            f.arrow(x - 50, 250, x - 8, 250, color=GREEN_D)
    f.text(108, 298, "抖动来源：中断延迟、其他中断插队、读端口的指令开销 —— 采样间隔不是理想等距",
           size=15, color=MUTED)

    # ---- 实现 B ----
    f.rect(84, 338, 984, 150, color=BLUE_D, fill=WHITE, sw=2.4)
    f.text(108, 374, "实现 B：TIM 触发 DMA 搬运", size=20, color=BLUE_D,
           weight="bold")
    step = ["TIM 触发请求", "DMA 读 GPIO", "写入缓冲"]
    for i, s in enumerate(step):
        x = 108 + i * 300
        f.rect(x, 394, 240, 52, color=BLUE_D, fill=WHITE, sw=2.0,
               double=False)
        f.text(x + 120, 426, s, size=17, color=INK, anchor="middle")
        if i:
            f.arrow(x - 50, 420, x - 8, 420, color=BLUE_D)
    f.text(108, 468, "前置核对：哪个请求通道映射到 GPIO、DMA 能不能走这条总线路径、缓冲对齐与长度",
           size=15, color=MUTED)

    # ---- 先验证清单 ----
    f.rect(84, 516, 984, 150, color=AMBER_STROKE, fill=WHITE, sw=2.4)
    f.text(108, 552, "换实现之前，先验证这三件", size=20, color=AMBER_STROKE,
           weight="bold")
    f.multi(108, 586, [
        "① 采样周期：TIM 的分频与重装算出来的周期，和你要的速率一致吗",
        "② 输入保护：5 V 信号进 3.3 V 引脚之前，限流与分压做了吗",
        "③ 缓冲约定：环形缓冲的写指针与 BUSY 的握手先定清楚（下一段展开）",
    ], size=16, color=INK, lh=27)

    f.htext(W / 2, 724, "中断读是示例，不是唯一解；DMA 也不是免费提速",
            size=22, color=INK, weight="bold", anchor="middle", hl=True)
    return f


def bt_car_chain():
    f = Fig("ch19-bt-car-chain",
            "蓝牙一条指令，从手机走到轮子 / F B L R S chain")
    f.text(72, 142, "项目 1 蓝牙遥控小车 · USART1 收字符 → Car_HandleCmd → TIM3 CH1/CH2 + DIR",
           size=19, color=MUTED)

    # ---- ① 链路 ----
    chain = [("手机 App", "F B L R S", BLUE_D),
             ("HC-05", "串口透传", GREEN_D),
             ("Car_HandleCmd(c)", "字符 switch", AMBER_STROKE),
             ("SetMotor(id, duty)", "PWM + 方向", INK)]
    for i, (name, sub, color) in enumerate(chain):
        x = 72 + i * 254
        f.rect(x, 172, 236, 76, color=color, fill=WHITE, sw=2.4)
        f.text(x + 118, 202, name, size=19, color=color, anchor="middle", weight="bold")
        f.text(x + 118, 230, sub, size=16, color=INK, anchor="middle")
        if i:
            f.arrow(x - 16, 210, x - 3, 210, color=INK, head=7, bend=0)

    # ---- ② 指令映射 ----
    f.text(72, 282, "字符 → 两路 duty（-100~100，符号定方向）", size=19, color=INK, weight="bold")
    maps = [("F 前进", ["1 路 +60", "2 路 +60"], GREEN_D),
            ("B 后退", ["-60", "-60"], BLUE_D),
            ("L 左转", ["1 路 0", "2 路 +60"], AMBER_STROKE),
            ("R 右转", ["+60", "0"], AMBER_STROKE),
            ("S 停止", ["0", "0"], RED)]
    for i, (name, lines, color) in enumerate(maps):
        x = 72 + i * 200
        f.rect(x, 300, 190, 104, color=color, fill=WHITE, sw=2.2)
        f.text(x + 95, 330, name, size=18, color=color, anchor="middle", weight="bold")
        f.multi(x + 95, 358, lines, size=15.5, color=INK, lh=21, anchor="middle")

    # ---- ③ SetMotor 里发生什么 ----
    f.rect(72, 428, 482, 140, color=GREEN_D, fill=WHITE, sw=2.4)
    f.text(92, 458, "电机 1（id=1）", size=18, color=GREEN_D, weight="bold")
    f.multi(92, 486, ["DIR = MOTOR_DIR_PORT / MOTOR_DIR_PIN",
                      "PWM = TIM3_CH1",
                      "pwm = |duty| × 999 / 100（0~999）"], size=15.5, color=INK, lh=24)
    f.rect(598, 428, 482, 140, color=BLUE_D, fill=WHITE, sw=2.4)
    f.text(618, 458, "电机 2（id=2）", size=18, color=BLUE_D, weight="bold")
    f.multi(618, 486, ["DIR = GPIOA / PIN_1",
                       "PWM = TIM3_CH2",
                       "同一条换算，0~999"], size=15.5, color=INK, lh=24)

    # ---- ④ 功率级还缺什么 ----
    f.rect(72, 590, 628, 86, color=RED, fill=WHITE, sw=2.4)
    f.text(92, 620, "L298N 每路要 IN1 / IN2 + ENA", size=17.5, color=RED, weight="bold")
    f.text(92, 648, "示例只有 DIR + PWM：正反转 / 制动 / 滑行真值表尚未实现", size=15.5, color=INK)
    f.rect(724, 590, 356, 86, color=AMBER_STROKE, fill=WHITE, sw=2.4)
    f.text(744, 620, "S 只把 PWM 置零", size=17.5, color=AMBER_STROKE, weight="bold")
    f.text(744, 648, "不代表制动或滑行", size=15.5, color=INK)

    f.text(72, 706, "方向脚不要放在第 10 脚 PA0：它和灯、ADC、WKUP 撞在一起。",
           size=17, color=MUTED)
    f.htext(72, 740, "指令解析只是前半程；功率级接线与真值表，是另一张清单。",
            size=20, color=INK, weight="bold", hl=True)
    return f


def usb_ownership():
    f = Fig("ch19-usb-ownership",
            "CDC_Transmit_FS 之后，这 133 字节归谁")
    f.text(72, 142, "项目 4 USB 采集卡 · frame[4 + 64×2 + 1] = 133 B · 帧头 0xAA 0x55 + seq + 样本 + Checksum8",
           size=18, color=MUTED)

    panels = [(72, BLUE_D, "① 函数内：栈帧所有", ["frame[133] 在局部栈上", "函数一返回，栈帧失效", "此时发送可能还没开始"]),
              (406, GREEN_D, "② 异步持有：外设还在用", ["CDC_Transmit_FS 通常", "异步持有发送缓冲",
                                                      "缓冲要活到发送完成"]),
              (740, RED, "③ 不做 BUSY：下一帧覆盖", ["忽略 BUSY 会丢帧", "断连、背压也要处理",
                                                     "覆盖发生在途缓冲"])]
    for x, color, head, lines in panels:
        f.rect(x, 176, 316, 320, color=color, fill=WHITE, sw=2.4)
        f.text(x + 18, 214, head, size=17.5, color=color, weight="bold")
        f.multi(x + 18, 250, lines, size=15.5, color=INK, lh=25)
    # ① 栈帧小图：返回后打叉
    f.rect(92, 348, 276, 52, color=BLUE_D, fill=WHITE, sw=2.0, dash="6 5")
    f.text(230, 380, "frame[133]", size=16, color=BLUE_D, anchor="middle")
    f.line(104, 352, 356, 396, color=RED, sw=2.2)
    f.line(104, 396, 356, 352, color=RED, sw=2.2)
    f.text(230, 430, "return 后失效", size=15, color=RED, anchor="middle")

    # ② 时间线：返回只是开始
    f.line(426, 408, 702, 408, color=MUTED, sw=1.6)
    for tx, label in [(462, "调用"), (516, "返回"), (672, "完成")]:
        f.line(tx, 402, tx, 414, color=MUTED, sw=1.6)
        f.text(tx, 436, label, size=13, color=MUTED, anchor="middle")
    f.line(462, 390, 672, 390, color=GREEN_D, sw=8)
    f.text(567, 372, "缓冲必须活着到完成", size=13.5, color=GREEN_D, anchor="middle")
    f.text(426, 466, "返回 ≠ 发送完成", size=14, color=RED, weight="bold")

    # ③ 顺序图：N+1 覆盖在途缓冲
    f.rect(760, 356, 276, 36, color=AMBER_STROKE, fill=WHITE, sw=2.0, double=False)
    f.text(898, 379, "帧 N：在途", size=14.5, color=INK, anchor="middle")
    f.rect(760, 414, 276, 36, color=RED, fill=WHITE, sw=2.0, double=False)
    f.text(898, 437, "帧 N+1：复用同一缓冲", size=14.5, color=INK, anchor="middle")
    f.arrow(898, 412, 898, 396, color=RED, head=7, bend=0)
    f.text(898, 478, "在途数据被覆盖", size=14, color=RED, anchor="middle", weight="bold")

    f.rect(72, 530, 984, 110, color=AMBER_STROKE, fill=WHITE, sw=2.2)
    f.text(92, 560, "主机侧：一次 read ≠ 一帧", size=17.5, color=AMBER_STROKE, weight="bold")
    f.text(92, 590, "AA 55 | seq（2 B）| 64 × uint16 | Checksum8（1 B）· 133 B 仍按 64 + 64 + 5 分包",
           size=15.5, color=INK)
    f.text(92, 618, "校验名是 Checksum8，不能据此称为 CRC", size=15.5, color=RED)

    f.htext(72, 690, "缓冲的所有权写进接口约定：谁分配、活到哪一刻、谁释放。",
            size=20, color=INK, weight="bold", hl=True)
    f.text(72, 726, "USB 时钟 48 MHz、VID/PID、端点包长见第 14 章。", size=16, color=MUTED)
    return f


def balance_loop():
    f = Fig("ch19-balance-loop",
            "直立环 5 ms：一条 PD 从倾角走到 PWM")
    f.text(72, 142, "项目 9 平衡小车 · 只有角度 P + 陀螺 D · 目标倾角 0° · 示例参数不是稳定承诺",
           size=18, color=MUTED)

    steps = [("① 5 ms 控制环", "Control_Loop_5ms()（TIM 中断里调用）", BLUE_D),
             ("② 读姿态", "IMU_GetAngle() / IMU_GetGyroY()", GREEN_D),
             ("③ 误差", "err = target_angle − angle", GREEN_D),
             ("④ PD 输出", "out = kp × err − kd × gyro", AMBER_STROKE),
             ("⑤ 限幅", "Clamp(pwm, −1000, 1000)", AMBER_STROKE),
             ("⑥ 送电机", "Motor_SetBoth(pwm)", RED)]
    for i, (head, detail, color) in enumerate(steps):
        y = 172 + i * 80
        f.rect(84, y, 452, 64, color=color, fill=WHITE, sw=2.2)
        f.text(104, y + 26, head, size=17, color=color, weight="bold")
        f.text(104, y + 49, detail, size=14, color=INK)
        if i < len(steps) - 1:
            f.arrow(310, y + 66, 310, y + 78, color=color, head=8, bend=0)

    cards = [(176, AMBER_STROKE, "上电前先核对", ["① 姿态轴向：哪个角是「前倾」",
                                                 "② 单位：度还是弧度，陀螺零偏",
                                                 "③ 电机极性：正 PWM 是否真往前推"]),
             (342, RED, "示例不是稳定参数", ["kp 25.0 / kd 0.8 仅示例",
                                            "没有积分项、没有速度环",
                                            "不能直接当底盘的稳定参数"]),
             (508, BLUE_D, "时序与阻塞", ["5 ms 是调度目标，要实测抖动",
                                          "IMU 读取会阻塞 → 移出 ISR",
                                          "再验控制任务的截止时间"])]
    for y, color, head, lines in cards:
        f.rect(590, y, 490, 142, color=color, fill=WHITE, sw=2.4)
        f.text(610, y + 34, head, size=17.5, color=color, weight="bold")
        f.multi(610, y + 66, lines, size=15, color=INK, lh=25)

    f.htext(72, 706, "先把轴向、单位、极性对上，再谈 PID 参数。",
            size=21, color=INK, weight="bold", hl=True)
    f.text(72, 742, "PD 参数只能靠实测整定；5 ms 是不是真能跑满，也要用实测回答。",
           size=16, color=MUTED)
    return f


FIGS = {
    "ch19-bt-car-chain": bt_car_chain,
    "ch19-usb-ownership": usb_ownership,
    "ch19-balance-loop": balance_loop,
    "ch19-la-sampling": la_sampling,
    "ch19-log-ring": log_ring,
    "ch19-ab-partition": ab_partition,
    "ch19-flash-fit": flash_fit,
    "ch19-pick-ladder": pick_ladder,
    "ch19-iap-gates": iap_gates,
    "ch19-milestone-triage": milestone_triage,
    "ch19-sram-budget": sram_budget,
    "ch19-usb-split": usb_split,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))
