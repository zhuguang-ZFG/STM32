# -*- coding: utf-8 -*-
"""AI tool-flow and defense plate (ch43).

Facts pinned to the chapter: MCP has three parties (Hosts/Clients/Servers),
three primitives (Resources/Prompts/Tools), and per-server authorization
("one server, one client"); Sampling/Logging were deprecated in the pinned
spec snapshot. Three defense layers: soft prompt/CLAUDE.md, tool gate, hard
CI/test gate. Permission four questions: read paths, write paths, commands,
credentials; production credentials never enter the agent environment.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hd import *  # noqa: E402,F401,F403


def ai_defense():
    f = Fig("arch-ai-defense", "授权按 server 切，防线留在模型外")

    f.rect(48, 118, 1056, 240, color=BLUE_D, fill=WHITE, sw=2.6)
    f.htext(64, 150, "MCP：三方、三类原语、一 server 一 client", size=22,
            color=BLUE_D, weight="bold")

    f.rect(64, 174, 280, 146, color=BLUE_D, fill=PAPER, sw=2.2)
    f.text(80, 200, "Host（编辑器 / IDE）", size=16, color=BLUE_D,
           weight="bold")
    for x, label in [(82, "Client A"), (214, "Client B")]:
        f.rect(x, 218, 112, 52, color=BLUE_D, fill=WHITE, sw=2.0)
        f.text(x + 10, 250, label, size=15, color=INK)

    f.rect(440, 182, 260, 62, color=GREEN_D, fill=WHITE, sw=2.2)
    f.text(452, 208, "Server A / 文件系统（只读）", size=15, color=GREEN_D,
           weight="bold")
    f.text(452, 230, "resources + read_file", size=14, color=MUTED)
    f.rect(440, 260, 260, 62, color=RED, fill=WHITE, sw=2.2)
    f.text(452, 286, "Server B / 构建（白名单）", size=15, color=RED,
           weight="bold")
    f.text(452, 308, "tools + run_build", size=14, color=MUTED)

    f.arrow(194, 216, 438, 210, color=GREEN_D, sw=2.2, bend=-0.05)
    f.arrow(326, 244, 438, 291, color=RED, sw=2.2, bend=0.12)
    f.text(350, 196, "授权 1", size=13, color=GREEN_D, weight="bold")
    f.text(350, 322, "授权 2", size=13, color=RED, weight="bold")

    f.rect(740, 182, 340, 140, color=AMBER_STROKE, fill=PAPER, sw=2.2)
    f.text(754, 208, "三类原语", size=16, color=AMBER_STROKE, weight="bold")
    f.text(754, 234, "Resources / Prompts / Tools", size=15, color=INK)
    f.text(754, 260, "Sampling / Logging：快照已 deprecated", size=13,
           color=MUTED)
    f.text(754, 286, "每个 server 单独同意，不给全局代理权。", size=14,
           color=RED)
    f.text(754, 308, "换 server 就重新授权。", size=14, color=RED)

    f.text(64, 342, "拓扑是三方，不是“一个万能代理”；授权颗粒度落在 server。",
           size=15, color=INK)

    f.rect(48, 378, 620, 270, color=GREEN_D, fill=WHITE, sw=2.6)
    f.htext(64, 410, "三层防线：越往下越不依赖模型自觉", size=21,
            color=GREEN_D, weight="bold")
    layers = [
        (432, "软约束", "提示词 / CLAUDE.md", "模型可能忘", AMBER_STROKE),
        (500, "工具闸门", "只读工具 / 写白名单", "配置层拦截", BLUE_D),
        (568, "硬门禁", "CI / slop_lint / 测试", "不经过模型意志；失败自己报警",
         RED),
    ]
    for y, title, sub, note, c in layers:
        f.rect(64, y, 588, 58, color=c, fill=PAPER, sw=2.0)
        f.text(78, y + 24, title, size=18, color=c, weight="bold")
        f.text(176, y + 22, sub, size=14, color=INK)
        f.text(176, y + 42, note, size=13, color=MUTED)
    f.text(64, 638, "软约束可以忘，硬门禁不会。", size=15, color=RED)

    f.rect(684, 378, 420, 270, color=AMBER_STROKE, fill=WHITE, sw=2.6)
    f.htext(700, 410, "权限四问", size=21, color=AMBER_STROKE,
            weight="bold")
    questions = ["1  能读哪些路径？", "2  能写哪些路径？",
                 "3  能跑哪些命令？", "4  带什么凭据？"]
    for i, q in enumerate(questions):
        f.text(704, 446 + i * 36, q, size=18, color=INK)
    f.rect(704, 586, 380, 44, color=RED, fill=PAPER, sw=2.2)
    f.text(716, 614, "生产凭据永不进 agent 环境", size=16, color=RED,
           weight="bold")

    f.htext(576, 704, "MCP 是协议，不是第四个工具；至少要有一层防线在模型外。",
            size=21, color=AMBER_STROKE, anchor="middle", weight="bold",
            hl=True, hl_fill=AMBER_FILL)
    return f


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[2] / "assets" / "illustrations" / "handraw"
    save(ai_defense(), str(out / "arch-ai-defense.svg"))
    print("wrote arch-ai-defense.svg")
