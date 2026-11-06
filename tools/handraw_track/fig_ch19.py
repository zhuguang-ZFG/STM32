# -*- coding: utf-8 -*-
"""Six deterministic project planning plates: capacities are not measurements.

F103C8 capacities: DS5319. Single-slot map: chapter12/iap-bootloader.
heap_4 budget shows an explicit hypothetical allocation, not a measured map.
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


FIGS = {
    "ch19-ab-partition": ab_partition,
    "ch19-flash-fit": flash_fit,
    "ch19-pick-ladder": pick_ladder,
    "ch19-iap-gates": iap_gates,
    "ch19-milestone-triage": milestone_triage,
    "ch19-sram-budget": sram_budget,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))
