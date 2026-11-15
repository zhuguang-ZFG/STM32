# -*- coding: utf-8 -*-
"""Learning-route plates for ch46 and the open-source appendix.

Facts are pinned to the ch46 table and the GitHub API snapshot dated
2026-11-15; licenses were read from each repository root. Deterministic:
same code -> same SVG bytes -> same PNG pixels.
"""
from pathlib import Path

from hd import (AMBER_FILL, AMBER_STROKE, BLUE_D, GREEN_D, INK, MUTED, RED, W,
                WHITE, Fig, save)

STAGE = Path(__file__).resolve().parents[2] / ".temp" / "learning-plates"


def ch46_l0_l5_ladder():
    """Six evidence levels mapped onto the merged book's eight volumes."""
    f = Fig("ch46-l0-l5-ladder", "从入门到精通：六级能力与过关证据")
    f.text(72, 126,
           "级别按证据划分，不按读完的章数划分；每一级都写明下一级还缺的那份证据。",
           size=17, color=MUTED)

    for label, x in (("级别", 76), ("卷/章", 168), ("过关证据", 360),
                     ("下一级缺什么", 786)):
        f.text(x, 148, label, size=14, color=BLUE_D, weight="bold")

    rows = [
        ("L0", "起步", "卷 0；第 8–9 章",
         ["独立编译、烧录、复位，留下版本记录",
          "说清芯片、引脚、电源、时钟边界"],
         ["一只脚的真实电平", "与波形"], GREEN_D),
        ("L1", "驱动", "第 9–12 章",
         ["GPIO、中断、时基、定时器/PWM 驱动外设",
          "波形、寄存器读回、可见结果三者一致"],
         ["字节怎么进出，", "缓冲区归谁"], BLUE_D),
        ("L2", "数据", "第 13–17 章；附录 A",
         ["UART、SPI、I2C、ADC/DAC、DMA、Flash",
          "时序图、缓冲区状态、代码路径能对上"],
         ["失败能否复现，", "原因能否区分"], AMBER_STROKE),
        ("L3", "可靠", "卷 2",
         ["掉电、升级、看门狗、低功耗、崩溃现场",
          "能复现失败，并把原因区分开"],
         ["任务、资源与截止时间", "能否预算"], RED),
        ("L4", "系统", "卷 3–5",
         ["RTOS、迁移、网络、Cache、运动控制",
          "写出边界、最坏情况、恢复路径与取舍"],
         ["一份别人能重建、验收、", "交接的交付包"], GREEN_D),
        ("L5", "交付", "卷 6–7",
         ["项目组织、仿真、测试、板级接线、验收",
          "资料与开源引用一起进交付包"],
         ["终点：能对别人的系统", "做同样的证据审查"], BLUE_D),
    ]

    y = 158
    for level, name, vol, evidence, missing, color in rows:
        f.rect(64, y, 1024, 76, color=color, fill=WHITE, sw=2.0,
               double=False)
        f.rect(76, y + 12, 70, 52, color=color, fill=WHITE, sw=2.4,
               double=False)
        f.text(111, y + 46, level, size=21, color=color, anchor="middle",
               weight="bold", font="'Consolas','Courier New',monospace")
        f.text(168, y + 32, name, size=20, color=INK, weight="bold")
        f.text(168, y + 56, vol, size=13.5, color=MUTED)
        f.text(360, y + 30, evidence[0], size=15, color=INK)
        f.text(360, y + 54, evidence[1], size=15, color=INK)
        f.text(786, y + 30, missing[0], size=14.5, color=AMBER_STROKE)
        f.text(786, y + 54, missing[1], size=14.5, color=AMBER_STROKE)
        y += 84

    f.panel(64, 670, 1024, 84, AMBER_FILL)
    f.text(88, 704, "读序是卷 0→卷 7，能力归档按证据。", size=19, color=INK,
           weight="bold")
    f.text(88, 734,
           "卷 3–5 先收 L4 的系统证据，卷 6–7 再用交付包收口。",
           size=16, color=MUTED)
    return f


def _card(f, x, y, color, title, subtitle, lines):
    f.rect(x, y, 498, 238, color=color, fill=WHITE, sw=2.4, double=False)
    f.text(x + 24, y + 38, title, size=22, color=color, weight="bold")
    f.text(x + 24, y + 64, subtitle, size=13.5, color=MUTED)
    f.multi(x + 24, y + 96, lines, size=14.5, color=INK, lh=23)


def ch46_oss_four_lanes():
    """Four kinds of community resources, with license boundaries."""
    f = Fig("ch46-oss-four-lanes", "社区开源资源：书、课、代码、文章分开读")
    f.text(64, 126,
           "星标取 2026-11-15 GitHub API；许可取仓库根文件。",
           size=16, color=MUTED)
    f.text(64, 152,
           "书和课帮你找路径；判据仍在手册、编译和测量。",
           size=16, color=MUTED)

    _card(f, 64, 176, BLUE_D, "开源书 / 指南",
          "补最小可运行路径，补另一种语言视角",
          ["cpq/bare-metal-programming-guide · MIT · 5010★",
           "rust-embedded/book + discovery · 代码 MIT/Apache",
           "怎么用：补启动、寄存器、链接脚本；Rust 路线看另一套抽象",
           "边界：地址、时钟、位段回 RM/DS；换板先查外设",
           "正文许可：book 为 CC BY-SA 4.0，discovery 为 CC BY 4.0"])

    _card(f, 590, 176, GREEN_D, "开源课程 / 实验课",
          "按周或按实验推进，补全链路与从零实现",
          ["microsoft/IoT-For-Beginners · MIT · 17191★",
           "jserv/mini-arm-os · BSD-2-Clause · 1264★",
           "怎么用：12 周 24 课补 IoT 全链路；从零写上下文切换",
           "边界：课程作业不是产品验收；教学内核不是产品 RTOS"])

    _card(f, 64, 450, AMBER_STROKE, "书的配套代码",
          "例程可以读，许可要单独看",
          ["cnoviello/mastering-stm32 · GPL-3.0 · 496★",
           "仓库只放书里的例程，书正文不在仓库",
           "怎么用：对照《Mastering STM32》的例程读 HAL",
           "边界：GPL-3.0 代码不要直接链进闭源固件"])

    _card(f, 590, 450, RED, "社区文集 / 片段",
          "找现象与排错思路，不替代手册",
          ["memfault/interrupt · CC BY-SA 4.0 · 560★",
           "nkolban/esp32-snippets · Apache-2.0 · 2521★",
           "怎么用：读排错、升级、可观测性文章；查 ESP32 片段",
           "边界：文章/片段不是手册；nkolban 片段停在 2024，先对 IDF"])

    f.panel(64, 716, 1024, 58, AMBER_FILL)
    f.text(88, 752,
           "同一份证据标准：能编译、能复现、能指回手册或仓库版本。星标只说明人多，不说明该读。",
           size=16, color=INK, weight="bold")
    return f


PLATES = {
    "ch46-l0-l5-ladder": ch46_l0_l5_ladder,
    "ch46-oss-four-lanes": ch46_oss_four_lanes,
}


if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(PLATES)
    STAGE.mkdir(parents=True, exist_ok=True)
    for n in names:
        f = PLATES[n]()
        save(f, str(STAGE / (n + ".svg")))
        print("wrote", STAGE / (n + ".svg"))
