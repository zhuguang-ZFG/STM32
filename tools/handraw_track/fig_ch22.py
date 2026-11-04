# -*- coding: utf-8 -*-
"""ch22 knowledge-track figures (facts from docs/22, Wokwi / Renode dual-track)."""
from hd import *


def sim_compare():
    f = Fig("ch22-sim-compare", "三列对照 / Wokwi · Renode · 真板")
    cols = [
        (80, "Wokwi", "看接线与现象", "能证明 GPIO/EXTI/I²C/TIM",
         "不证明真实边沿与 DMA", BLUE_D),
        (416, "Renode", "可脚本化机器模型", "能证明 ELF/UART/外设访问",
         "实现随版本与平台描述变", GREEN_D),
        (752, "目标真板", "供电·时钟·硅片", "能证明波形/电流/revision",
         "最终验收边界在这里", RED),
    ]
    for x, name, see, prove, notp, c in cols:
        f.rect(x, 128, 300, 360, color=c, fill=WHITE)
        f.htext(x + 150, 168, name, size=26, color=c, anchor="middle",
                weight="bold", hl=True)
        f.multi(x + 150, 220,
                ["看什么", see, "", "能证明", prove, "", "不能证明", notp],
                size=18, color=INK, lh=28, anchor="middle")
    f.htext(W / 2, 540, "模型里复现逻辑 → 固化版本 → 真板测量 → 记录差异",
            size=24, color=INK, anchor="middle", weight="bold", hl=True)
    f.text(W / 2, 590, "不能反过来用仿真绿灯覆盖实测",
           size=22, color=RED, anchor="middle")
    f.text(W / 2, 640, "出处：simulator-comparison · IG-004 · 不是实拍",
           size=18, color=MUTED, anchor="middle")
    return f


def wokwi_scope():
    f = Fig("ch22-wokwi-scope", "Wokwi 擅长与边界 / logic yes · analog desk")
    rows = [
        (90, "Good fit", GREEN_D, ["GPIO / UART / I²C 接线", "LED + 串口实验", "快速迭代状态机"]),
        (410, "OK w/ care", AMBER_STROKE, ["SPI 波形模式", "简单定时器", "上桌再用示波器复核"]),
        (730, "Poor fit", RED, ["ADC 精度", "USB 眼图 / CAN PHY", "晶振起振余量"]),
    ]
    for x, title, c, lines in rows:
        f.rect(x, 130, 300, 280, color=c, fill=WHITE)
        f.htext(x + 150, 172, title, size=24, color=c, anchor="middle",
                weight="bold", hl=True)
        f.multi(x + 150, 230, lines, size=20, color=INK, lh=36, anchor="middle")
    f.panel(90, 450, 940, 90, AMBER_FILL)
    f.rect(90, 450, 940, 90, color=AMBER_STROKE, sw=3.0)
    f.text(W / 2, 486, "每个 Wokwi 示例都有 BluePill 上的孪生验收字符串",
           size=24, color=INK, anchor="middle", weight="bold")
    f.text(W / 2, 520, "diagram.json + sketch 讲故事；硅片勘误仍看 DS/ES",
           size=20, color=MUTED, anchor="middle")
    f.htext(W / 2, 590, "别只在浏览器里调时序竞赛，上桌才知道谁赢",
            size=24, color=RED, anchor="middle", weight="bold", hl=True)
    f.text(W / 2, 640, "Wokwi 脚号 ≠ BluePill 丝印 —— 以手册引脚为准",
           size=20, color=MUTED, anchor="middle")
    return f


def renode_path():
    f = Fig("ch22-renode-path", "Renode 四步 / platform → ELF → UART")
    steps = [
        (70, "1. platform", ".resc 板定义", "machine / peripherals", BLUE_D),
        (340, "2. load ELF", "sysbus LoadELF", "向量表仍按 PM", GREEN_D),
        (610, "3. start", "start / pause", "脚本可断言", AMBER_STROKE),
        (880, "4. UART", "analyzer / log", "对齐验收字符串", RED),
    ]
    for x, t, a, b, c in steps:
        f.rect(x, 140, 240, 200, color=c, fill=WHITE)
        f.text(x + 120, 190, t, size=24, color=c, anchor="middle", weight="bold")
        f.text(x + 120, 240, a, size=20, color=INK, anchor="middle")
        f.text(x + 120, 280, b, size=18, color=MUTED, anchor="middle")
    for x0 in (310, 580, 850):
        f.arrow(x0, 240, x0 + 30, 240, color=INK, sw=2.6, bend=0.0, head=9)
    f.multi(W / 2, 400,
            ["仓库两条脚本先跑通再改平台；固定 Renode 版本号",
             "适合 CI 式 UART 断言；弱于模拟与山寨布线",
             "绿灯日志 ≠ HSE 焊接质量"],
            size=22, color=INK, lh=36, anchor="middle")
    f.htext(W / 2, 540, "golden string 与真板实验单保持同一句",
            size=26, color=RED, anchor="middle", weight="bold", hl=True)
    f.text(W / 2, 600, "fork 平台文件却不记版本 = 不可复现的绿",
           size=22, color=MUTED, anchor="middle")
    return f


def sim_triage():
    f = Fig("ch22-sim-triage", "仿真三岔口 / 模型 · 主机 · 板级物理")
    branches = [
        (70, "岔口一 · 模型缺口", BLUE_D,
         ["外设根本没进模拟器", "板能选 ≠ 外设全建模", "对照支持表勾选缺口",
          "未建模项移出仿真验收"]),
        (410, "岔口二 · 主机环境", AMBER_STROKE,
         [".resc / board.json 路径", "Python·权限·串口桥", "先跑最小 blink ELF",
          "工具版本号写进计划"]),
        (750, "岔口三 · 板级物理", RED,
         ["仿真全绿真板失败", "晶振/USB/纹波不在模型", "线长·上拉·地回流",
          "仿真门与真板门分列"]),
    ]
    for x, title, c, lines in branches:
        f.rect(x, 128, 310, 360, color=c, fill=WHITE)
        f.htext(x + 155, 168, title, size=20, color=c, anchor="middle",
                weight="bold", hl=True)
        f.multi(x + 155, 230, lines, size=18, color=INK, lh=40, anchor="middle")
    f.htext(W / 2, 540, "仿真证明「逻辑在模型假设下成立」",
            size=24, color=INK, anchor="middle", weight="bold", hl=True)
    f.text(W / 2, 590, "真板证明「物理世界也成立」——两句不能并成一句",
           size=22, color=RED, anchor="middle")
    f.text(W / 2, 640, "Wokwi ≠ 完整 RM · Renode ≠ 模拟 · PCB 寄生仍在台上",
           size=18, color=MUTED, anchor="middle")
    return f


def hw_gap():
    f = Fig("ch22-hw-gap", "仿真与实物差距 / 哪些必须上桌")
    boxes = [
        (70, 130, 240, 220, "必须上桌", RED,
         ["晶振起振 / CSS", "USB 枚举 / CAN PHY", "电源跌落与纹波"]),
        (340, 130, 240, 220, "仿真先过", GREEN_D,
         ["状态机逻辑", "IRQ 先后叙事", "map / overflow"]),
        (610, 130, 240, 220, "两边都要", BLUE_D,
         ["UART 验收串", "GPIO 真值表", "IAP 槽位算术"]),
        (880, 130, 200, 220, "永不跳过", AMBER_STROKE,
         ["BOOT0=0", "量 3.3 V", "SWD 通断"]),
    ]
    for x, y, w, h, t, c, lines in boxes:
        f.rect(x, y, w, h, color=c, fill=WHITE)
        f.htext(x + w / 2, y + 40, t, size=22, color=c, anchor="middle",
                weight="bold", hl=True)
        f.multi(x + w / 2, y + 90, lines, size=18, color=INK, lh=34,
                anchor="middle")
    f.panel(70, 400, 1010, 100, AMBER_FILL)
    f.rect(70, 400, 1010, 100, color=AMBER_STROKE, sw=3.0)
    f.text(W / 2, 440, "晋升路径：sim 绿 → desk 绿 → 才叫本章完成",
           size=24, color=INK, anchor="middle", weight="bold")
    f.text(W / 2, 478, "只在山寨板上复现的失败，正是第 21 章身份记录的价值",
           size=20, color=MUTED, anchor="middle")
    f.htext(W / 2, 560, "仿真教结构；真板教余量",
            size=28, color=RED, anchor="middle", weight="bold", hl=True)
    f.text(W / 2, 620, "双轨诚实：浏览器 alone 永远毕不了业",
           size=22, color=INK, anchor="middle")
    return f


FIGS = {
    "ch22-sim-compare": sim_compare,
    "ch22-wokwi-scope": wokwi_scope,
    "ch22-renode-path": renode_path,
    "ch22-sim-triage": sim_triage,
    "ch22-hw-gap": hw_gap,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        fig = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(fig, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))
