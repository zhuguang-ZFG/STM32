# -*- coding: utf-8 -*-
"""ch31 knowledge-track figures (handraw grammar, frozen motor facts)."""
from hd import *


# ------------------------------------------------------------ fig 1
def quadrature():
    f = Fig("ch31-quadrature", "四倍频与方向 / 4x counting and direction",
            title_color=BLUE_D)
    # A/B waveforms
    ya = 190
    f.htext(120, 150, "A 领先 B → 加计数", size=26, color=BLUE_D, weight="bold")
    for ch, y, c, off in (("A", ya, BLUE_D, 0), ("B", ya + 110, GREEN_D, 60)):
        f.text(110, y + 30, ch, size=28, color=c, weight="bold")
        x = 170
        for i in range(6):
            up = (i % 2 == 0)
            shift = off if ch == "B" else 0
            f.stroke([(x + shift, y + (0 if up else 60)),
                      (x + 80 + shift, y + (0 if up else 60))], color=c, sw=3.0)
            f.stroke([(x + 80 + shift, y + (0 if up else 60)),
                      (x + 80 + shift, y + (60 if up else 0))], color=c, sw=3.0)
            x += 80
    f.htext(W / 2, 470, "TIM2 编码器模式 3（SMS=011）：A、B 两路上下沿都计数 → 4×PPR",
            size=27, color=INK, anchor="middle", weight="bold", hl=True)
    f.multi(90, 540, [
        "每相每圈 PPR 个脉冲 → 四倍频后 4×PPR 个计数（冻结示例 110 × 4 = 440 CPR）",
        "B 领先 A → 减计数；方向由谁先到来决定，不需要额外方向线",
    ], size=25, color=INK, lh=40)
    return f


# ------------------------------------------------------------ fig 2
def rpm_formula():
    f = Fig("ch31-rpm-formula", "定窗计数公式 / fixed-window RPM",
            title_color=GREEN_D)
    f.rect(80, 140, 992, 90, color=GREEN_D, fill=WHITE, r=8)
    f.htext(W / 2, 196, "rpm_raw = 60 × Δ / (CPR × Δt)        Δt = 10 ms",
            size=30, color=INK, anchor="middle", weight="bold")
    f.rect(80, 260, 992, 130, color=BLUE_D, fill=WHITE, r=8)
    f.htext(120, 306, "代例：Δ=11, CPR=440, Δt=0.01 s", size=26, color=BLUE_D,
            weight="bold")
    f.multi(120, 348, ["60×11/(440×0.01) = 150 rpm；回验：150 rpm = 2.5 转/s → 0.025 转 × 440 = 11 ✓"],
            size=24, color=INK, lh=34)
    f.rect(80, 430, 992, 130, color=AMBER_STROKE, fill=WHITE, r=8)
    f.htext(120, 476, "量化下限：rpm_quant = 60/(440×0.01) ≈ 13.6 rpm",
            size=26, color=AMBER_STROKE, weight="bold")
    f.multi(120, 518, ["窗内不足 1 个计数测不到 → 低速读数逐格跳是测量特性，不是控制故障"],
            size=24, color=INK, lh=34)
    f.multi(90, 630, [
        "rpm=0 只说明窗内无计数 —— 静止判定（REVERSING 停稳判据）用同一量化知识",
        "需要更细分辨率：加长测量窗（牺牲带宽）或换更高 CPR 编码器",
    ], size=24, color=INK, lh=38)
    return f


# ------------------------------------------------------------ fig 3
def wrap_triage():
    f = Fig("ch31-wrap-triage", "回绕消歧与断线分辨 / wrap and disconnect",
            title_color=RED)
    f.rect(80, 140, 600, 250, color=BLUE_D, fill=WHITE, r=10)
    f.htext(120, 188, "16 位回绕消歧", size=28, color=BLUE_D, weight="bold")
    f.multi(120, 236, [
        "样本 65530 与 100 的有符号增量：",
        "(100 − 65530 + 32768) mod 65536 − 32768 = +6",
        "不是 −65430 —— 差值解释进 ±32767 区间",
        "判据：真实 |Δ| < 32768/2",
    ], size=23, color=INK, lh=36)
    f.rect(720, 140, 352, 250, color=GREEN_D, fill=WHITE, r=10)
    f.htext(896, 188, "余量核验", size=28, color=GREEN_D, anchor="middle",
            weight="bold")
    f.multi(748, 236, ["上限 600 rpm = 10 转/s", "10 ms 窗最多 4400 计数", "≪ 32768，消歧安全"],
            size=23, color=INK, lh=36)
    f.rect(80, 440, 992, 170, color=RED, fill=WHITE, r=10)
    f.htext(120, 488, "「零计数」不能单独证明断线", size=27, color=RED,
            weight="bold")
    f.multi(120, 532, [
        "电机静止 ⇔ 窗内无计数；断线 ⇔ 也无计数 —— 两者同表象",
        "区分证据：手转轴看遥测 Δ 与 CNT 是否变化；示波器看 A/B 波形是否消失",
    ], size=24, color=INK, lh=38)
    f.multi(90, 660, ["换编码器 / 提速上限 → 消歧判据必须重算"],
            size=25, color=MUTED, lh=38)
    return f


FIGS = {
    "ch31-quadrature": quadrature,
    "ch31-rpm-formula": rpm_formula,
    "ch31-wrap-triage": wrap_triage,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))
