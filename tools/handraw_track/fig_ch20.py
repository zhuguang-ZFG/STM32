# -*- coding: utf-8 -*-
"""ch20 knowledge-track figures (facts from docs/20).

manual_route: the three-step manual lookup — pick the manual (RM for
registers/timing, DS for pins/electrical, AN for methods), Ctrl+F the
register or bit name, then read the functional description for timing and
formulas. Worked example 1: TIM1 duty -> RM0008, search CCR1, ch.15,
duty = CCR1/(ARR+1). Example 2: PA11 as USB -> DS5319, search PA11, the
Alternate functions column.

cube_suite: the official tool division of labor — CubeMX (configuration,
generates init code) -> CubeIDE (build and debug on Eclipse+GCC) ->
CubeProgrammer (flash hex/bin, option bytes, readout protection); the trio
covers 90% of scenarios, CubeMonitor watches run-time variables and power.
"""
from hd import *


def manual_route():
    f = Fig("ch20-manual-route",
            "查手册三步：先选书，再 Ctrl+F，再读上下文 / pick, search, read")

    # ---- 三步主路 ----
    steps = [("① 定手册", ["寄存器/时序 → RM", "引脚/电气 → DS", "做法 → AN"], BLUE_D),
             ("② 搜关键词", ["直接搜寄存器名 TIMx_CCR1", "或位名 CEN"], GREEN_D),
             ("③ 读上下文", ["看功能描述章的时序图", "与公式，再回位表核对"], AMBER_STROKE)]
    x = 84
    for i, (name, lines, color) in enumerate(steps):
        f.rect(x, 150, 300, 132, color=color, fill=WHITE, sw=2.4)
        f.text(x + 150, 184, name, size=22, color=color, anchor="middle",
               weight="bold")
        for j, ln in enumerate(lines):
            f.text(x + 18, 214 + j * 26, ln, size=16, color=INK)
        if i < 2:
            f.arrow(x + 306, 216, x + 342, 216, color=INK, bend=0.0, head=12)
        x += 348

    # ---- 例 1 ----
    f.rect(84, 320, 486, 264, color=GREEN_D, fill=WHITE, sw=2.4)
    f.text(100, 350, "例 1：TIM1 的占空比怎么算", size=20, color=GREEN_D,
           weight="bold")
    f.multi(100, 382, ["→ RM0008（寄存器与时序归它管）",
                       "→ Ctrl+F 搜 CCR1，落到第 15 章",
                       "→ 读 PWM mode 小节：",
                       "    占空比 = CCR1 / (ARR + 1)",
                       "    频率 = fCK_CNT / (ARR + 1)",
                       "→ 回位表核对 OC1M 选 PWM、CC1E 使能"],
            size=17, color=INK, lh=27)

    # ---- 例 2 ----
    f.rect(606, 320, 486, 264, color=BLUE_D, fill=WHITE, sw=2.4)
    f.text(622, 350, "例 2：PA11 能不能做 USB", size=20, color=BLUE_D,
           weight="bold")
    f.multi(622, 382, ["→ DS5319（引脚与电气归它管）",
                       "→ Ctrl+F 搜 PA11，落到引脚表",
                       "→ 看 Alternate functions 列：",
                       "    PA11 = USB_DM（同时也是 CAN_RX）",
                       "→ 复用冲突的细节回 RM0008 第 9 章",
                       "  看 AFIO 重映射"],
            size=17, color=INK, lh=27)

    f.htext(84, 640, "搜中文搜不到时，用英文关键词加手册编号：RM0008 TIM PWM register",
            size=21, color=INK, weight="bold", hl=True)
    f.text(84, 678, "本图只整理本章「查手册的三步」的路线，手册内容以原 PDF 为准", size=17,
           color=MUTED)
    return f


def cube_suite():
    f = Fig("ch20-cube-suite",
            "三件套分工：配置 → 编译调试 → 烧录 / the Cube trio")
    f.text(72, 143, "第 20 章 · ST 的资料全部免费，从 st.com 出发 · 三件套即可覆盖 90% 场景",
           size=23, color=MUTED)

    # ---- 三件套流水线 ----
    tools = [(72, "CubeMX", "配置",
              ["图形化配置", "引脚、时钟、外设", "生成初始化代码"], BLUE_D),
             (430, "CubeIDE", "编译调试",
              ["编译与调试", "在同一个工程里", "基于 GCC"], GREEN_D),
             (788, "CubeProgrammer", "烧录 / 选项字节",
              ["烧录 hex / bin", "读写选项字节", "解除读保护"], AMBER_STROKE)]
    y0, bw, bh = 185, 292, 180
    for x, name, role, lines, color in tools:
        f.rect(x, y0, bw, bh, color=color, fill=WHITE, sw=2.6)
        f.text(x + 20, y0 + 44, name, size=25, color=color, weight="bold")
        f.text(x + 20, y0 + 78, role, size=21, color=INK, weight="bold")
        f.multi(x + 20, y0 + 110, lines, size=18, color=INK, lh=26)
    f.arrow(368, 275, 424, 275, color=INK, bend=0.0)
    f.arrow(726, 275, 782, 275, color=INK, bend=0.0)

    # ---- 第四件：CubeMonitor（不在三件套内） ----
    f.rect(331, 435, 490, 104, color=MUTED, fill=WHITE, dash="7 6", double=False)
    f.text(576, 471, "CubeMonitor（三件套之外）", size=24, color=MUTED,
           anchor="middle", weight="bold")
    f.text(576, 507, "运行时变量可视化 · 功耗监测（配合 X-NUCLEO）", size=18,
           color=INK, anchor="middle")

    f.line(72, 585, 1080, 585, color=MUTED, sw=1.3)
    f.htext(72, 628, "配置用 CubeMX · 编译调试用 CubeIDE · 烧录和选项字节用 CubeProgrammer",
            size=23, color=INK, weight="bold", hl=True)
    f.text(72, 672, "三件套即可覆盖 90% 场景；数据手册、参考手册、应用笔记也从 st.com 下载。",
           size=21, color=INK)
    f.text(72, 706, "工具怎么用查 UM：UM 讲工具 / 评估板 / 库的使用说明（如 CubeMX / CubeIDE 的 UM）。",
           size=21, color=INK)
    f.text(72, 740, "本图整理本章「官方资源地图」一节的工具分工；各工具能力以官方文档为准。",
           size=19, color=MUTED)
    return f


def exit_kit():
    f = Fig("ch20-exit-kit",
            "章末四张交付卡：构建 · 来源 · 证据 · 重建 / four exit cards")
    f.text(W / 2, 122,
           "四张卡各证一栏：构建归谁 · 追到哪页 · 到没到引脚 · 差异能否追因",
           size=20, color=MUTED, anchor="middle")

    def card(x, y, w, h, color, num, title):
        f.rect(x, y, w, h, color=color, fill=WHITE, sw=2.4)
        f.circle(x + 34, y + 30, 17, color=color, sw=2.0, fill=GRAY_FILL)
        f.text(x + 34, y + 38, num, size=18, color=color, anchor="middle",
               weight="bold")
        f.text(x + 62, y + 38, title, size=20, color=color, weight="bold")

    def stamp(x, y, kind, text):
        ok = kind == "证明"
        c = GREEN_D if ok else RED
        tw = 40 if ok else 64
        f.rect(x, y - 15, tw, 22, color=c, fill=WHITE, sw=1.6,
               double=False, amp=1.0, r=4)
        f.text(x + tw / 2, y + 1, kind, size=13, color=c, anchor="middle",
               weight="bold")
        f.text(x + tw + 8, y + 1, text, size=15, color=INK)

    # ---- ① 构建环境卡 ----
    card(84, 142, 480, 304, BLUE_D, "1", "构建环境卡")
    entries = [("CubeIDE", 100), ("VS Code", 212), ("CLion", 324), ("CI", 436)]
    for name, ex in entries:
        f.rect(ex, 194, 100, 30, color=BLUE_D, fill=GRAY_FILL, sw=1.6,
               double=False, amp=1.0, r=4)
        f.text(ex + 50, 214, name, size=14, color=INK, anchor="middle")
    f.line(150, 232, 486, 232, color=BLUE_D, sw=1.6, amp=1.2)
    for _, ex in entries:
        f.line(ex + 50, 224, ex + 50, 232, color=BLUE_D, sw=1.4, amp=0.8)
    f.arrow(318, 232, 318, 250, color=BLUE_D, bend=0.0, head=8)
    f.rect(100, 252, 436, 36, color=BLUE_D, fill=WHITE, sw=1.8,
           double=False, amp=1.2)
    f.text(318, 276, "同一个 CMakePreset（debug）· 一份定义", size=16,
           color=BLUE_D, anchor="middle", weight="bold")
    f.text(100, 316, "记录：编译器版本 · preset · ELF 哈希", size=15,
           color=INK)
    f.text(100, 342, "四个入口只换界面，不换源文件与宏", size=15, color=MUTED)
    f.line(100, 362, 548, 362, color=MUTED, sw=1.0, dash="5 5", amp=0.8)
    stamp(100, 390, "证明", "构建归同一个 preset，换 IDE 不换定义")
    stamp(100, 418, "不能证明", "生成的固件功能正确")

    # ---- ② 来源卡 ×4 ----
    card(588, 142, 480, 304, GREEN_D, "2", "来源卡 ×4")
    rows = [("DS · 引脚", 188), ("DS · 电气上限", 220),
            ("RM · 寄存器位", 252), ("ES · 勘误", 284)]
    for name, ry in rows:
        f.rect(604, ry, 168, 26, color=GREEN_D, fill=GRAY_FILL, sw=1.5,
               double=False, amp=1.0, r=4)
        f.text(616, ry + 19, name, size=14, color=INK)
        f.text(788, ry + 19, "rev ____ · 页 ____", size=14, color=MUTED)
    f.text(604, 330, "每条问题一张卡：来源 + revision + 页码", size=14,
           color=MUTED)
    f.text(604, 368, "不能证明：", size=15, color=RED, weight="bold")
    f.line(694, 374, 1000, 374, color=RED, sw=1.4, dash="5 5", amp=0.8)
    f.text(1006, 370, "自己填", size=12, color=MUTED)
    stamp(604, 420, "证明", "结论能追到某页与 revision")

    # ---- ③ 五层证据 ----
    card(84, 462, 480, 296, AMBER_STROKE, "3", "五层证据：一次 SPI 读 Flash")
    f.text(100, 520, "同一次读 Flash，五张票分开存", size=14, color=MUTED)
    layers = ["构建日志", "寄存器读回", "运行日志", "逻辑解码", "示波器波形"]
    ty = 532
    for i, name in enumerate(layers):
        f.rect(100, ty, 448, 26, color=AMBER_STROKE, fill=WHITE, sw=1.8,
               double=False, amp=1.0, r=4, dash="6 4")
        f.circle(122, ty + 13, 8, color=AMBER_STROKE, sw=1.5, fill=GRAY_FILL)
        f.text(122, ty + 18, str(i + 1), size=11, color=INK, anchor="middle",
               weight="bold")
        f.text(142, ty + 19, name, size=15, color=INK)
        f.text(532, ty + 18, "L%d" % (i + 1), size=12, color=MUTED,
               anchor="end")
        ty += 31
    f.line(100, 694, 548, 694, color=MUTED, sw=1.0, dash="5 5", amp=0.8)
    stamp(100, 718, "证明", "五层都存，覆盖范围分开写")
    stamp(100, 744, "不能证明", "票齐不等于结论对")

    # ---- ④ 重建对比 ----
    card(588, 462, 480, 296, RED, "4", "干净重建：ELF / map 对比")
    f.text(604, 512, "清空可重建的 build → 固定依赖重建", size=14,
           color=MUTED)
    for bx, label in ((622, "旧 ELF / map"), (850, "新 ELF / map")):
        f.rect(bx, 542, 168, 64, color=RED, fill=GRAY_FILL, sw=1.8,
               double=False, amp=1.2)
        f.text(bx + 84, 578, label, size=16, color=INK, anchor="middle",
               weight="bold")
    f.arrow(794, 574, 846, 574, color=RED, bend=0.0, head=9)
    f.text(820, 552, "diff", size=13, color=RED, anchor="middle",
           weight="bold")
    f.arrow(820, 610, 820, 634, color=RED, bend=0.0, head=9)
    f.line(620, 640, 1036, 640, color=RED, sw=1.6, amp=1.0)
    tags = [("工具链", 604, 96), ("宏", 712, 68), ("源文件", 792, 110),
            ("链接脚本", 914, 138)]
    for name, tx, tw in tags:
        f.line(tx + tw / 2, 640, tx + tw / 2, 648, color=RED, sw=1.4, amp=0.8)
        f.rect(tx, 648, tw, 28, color=RED, fill=WHITE, sw=1.6,
               double=False, amp=1.0, r=4)
        f.text(tx + tw / 2, 667, name, size=14, color=INK, anchor="middle")
    f.line(604, 696, 1052, 696, color=MUTED, sw=1.0, dash="5 5", amp=0.8)
    stamp(604, 724, "证明", "每个差异都能归到四类之一")
    stamp(604, 748, "不能证明", "追因前，不能判是谁改的")
    return f


def dma_f1_vs_f4():
    f = Fig("ch20-dma-f1-vs-f4",
            "F4 的 DMA 结论能不能搬到 F1：三个差异先核对")
    f.text(84, 118, "示例 3 的前提：F1 的 DMA 没有 FIFO 和突发档位，照搬配置必出错",
           size=21, color=MUTED)
    rows = [
        ("FIFO 阈值", "有（4 档阈值）", "无", RED),
        ("突发档位 BURST", "有（4/8/16 beat）", "无", RED),
        ("传输错误模型", "按 FIFO/突发检查", "简单 TE 标志", AMBER_STROKE),
    ]
    y = 168
    f.text(84, y - 6, "特性", size=20, color=MUTED, weight="bold")
    f.text(430, y - 6, "F4（RM0090/AN4031）", size=20, color=MUTED, weight="bold")
    f.text(806, y - 6, "F1（RM0008）", size=20, color=MUTED, weight="bold")
    y += 22
    for dim, f4, f1, c in rows:
        f.rect(84, y, 300, 78, color=c, fill=WHITE, sw=2.4)
        f.text(100, y + 48, dim, size=21, color=c, weight="bold")
        f.rect(430, y, 330, 78, color=INK, fill=WHITE, sw=2.0)
        f.text(446, y + 48, f4, size=20, color=INK)
        f.rect(806, y, 258, 78, color=INK, fill=WHITE, sw=2.0)
        f.text(822, y + 48, f1, size=20, color=INK)
        y += 96
    f.rect(84, y + 12, 980, 66, color=RED, fill=WHITE, sw=2.6)
    f.htext(W / 2, y + 48, "F4 的 DMA 优化结论先核对外设差异，再谈搬用",
            size=22, color=RED, anchor="middle", weight="bold", hl=True)
    return f


FIGS = {
    "ch20-dma-f1-vs-f4": dma_f1_vs_f4,
    "ch20-exit-kit": exit_kit,
    "ch20-manual-route": manual_route,
    "ch20-cube-suite": cube_suite,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))
