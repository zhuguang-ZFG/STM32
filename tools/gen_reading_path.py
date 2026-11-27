"""Generate the chapter 46 reading maps, with svgkit's book palette.

FA-029 geometric diagrams / IG-008 branching flow; C-03/C-10/C-27/C-31.
Original diagrams based on chapter 46, not illustrations from another book.
Run from the repository root: python tools/gen_reading_path.py
"""

from pathlib import Path

from svgkit import Svg, T

OUT = Path(__file__).resolve().parents[1] / "docs/public/figures"


def label(s, x, y, text, color=T.TEXT, size=28, weight="normal"):
    s.text(x, y, text, size=size, fill=color, anchor="middle", weight=weight)


def routes():
    s = Svg(720, 800, "学完共同基础，再按项目选分支")
    label(s, 360, 56, "从一次点灯，走到一次交付", size=34, weight="700")
    s.rect(110, 88, 500, 104, fill=T.PANEL2, stroke=T.BLUE, rx=12)
    label(s, 360, 129, "起步：构建 → 烧录 → 复位", T.BLUE)
    label(s, 360, 168, "第 0 章 · 留下首次运行记录", size=26)
    s.arrow(360, 192, 360, 228, color=T.BLUE, head=10)
    s.rect(74, 232, 572, 112, fill=T.PANEL, stroke=T.BLUE, rx=12)
    label(s, 360, 274, "共同基础：驱动与数据路径", T.BLUE)
    label(s, 360, 316, "边做实验，边补语言、构建与排错", size=26)
    s.line(360, 344, 360, 350, stroke=T.GREEN, sw=3)
    s.line(360, 383, 360, 389, stroke=T.GREEN, sw=3)
    s.line(180, 389, 540, 389, stroke=T.GREEN, sw=3)
    label(s, 360, 375, "按需选，可组合", T.GREEN, 26)
    for x in (180, 540):
        s.arrow(x, 389, x, 420, color=T.GREEN, head=10)
    # Each column is one branch card; no arrow implies a prerequisite
    # between the options within a card.
    for x, title, lines in (
        (32, "组织与连接", ("并发：第 21–25 章", "联网：第 33 章")),
        (380, "控制与迁移", ("运动：第 36–39 章", "换芯片：第 28–34 章")),
    ):
        s.rect(x, 424, 308, 154, fill="#eef5ee", stroke=T.GREEN, rx=12)
        label(s, x + 154, 465, title, T.GREEN, weight="700")
        for i, line in enumerate(lines):
            label(s, x + 154, 510 + i * 40, line, size=26)
    s.line(180, 578, 180, 610, stroke=T.GREEN, sw=3)
    s.line(540, 578, 540, 610, stroke=T.GREEN, sw=3)
    s.line(180, 610, 540, 610, stroke=T.GREEN, sw=3)
    s.arrow(360, 610, 360, 645, color=T.GREEN, head=10)
    s.rect(74, 650, 572, 88, fill="#fbf0d7", stroke=T.AMBER, rx=12)
    label(s, 360, 687, "交付：重建 + 验收 + 失败恢复", T.AMBER)
    label(s, 360, 722, "第 42 章 · 连同所选功能的证据交给别人", size=24)
    label(s, 360, 779, "阅读路线示意；逐章先修条件见正文索引", T.MUTED, 24)
    return s


def source_reading():
    s = Svg(720, 650, "读源码时，每次只改一个能验证的量")
    label(s, 360, 57, "把一份例程读成自己的实验", size=34, weight="700")
    steps = [
        (90, "01  锁定来源", "提交、许可、板型与工具链", T.BLUE),
        (210, "02  建立基线", "先运行，记录未改动时的结果", T.BLUE),
        (330, "03  只改一个量", "例如：改变定时周期", T.GREEN),
        (450, "04  对照结果", "预测值 ↔ 波形 / 寄存器 / 日志", T.AMBER),
    ]
    for y, title, note, color in steps:
        s.rect(100, y, 530, 92, fill=T.PANEL, stroke=color, rx=12)
        label(s, 365, y + 36, title, color, 30, "700")
        label(s, 365, y + 74, note, size=26)
        if y != 450:
            s.arrow(365, y + 92, 365, y + 116, color=color, head=9)
    s.path("M 100 496 L 56 496 L 56 256 L 96 256", stroke=T.AMBER, sw=3)
    s.arrow(72, 256, 97, 256, color=T.AMBER, head=9)
    label(s, 360, 590, "不符：回查配置与测法，再做同一实验", T.AMBER, 28)
    label(s, 360, 632, "自绘流程示意 · 结果需在所选硬件或模型中验证", T.MUTED, 24)
    return s


if __name__ == "__main__":
    routes().save(str(OUT / "ch46-reading-routes.svg"))
    source_reading().save(str(OUT / "ch46-source-reading.svg"))
