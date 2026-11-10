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
