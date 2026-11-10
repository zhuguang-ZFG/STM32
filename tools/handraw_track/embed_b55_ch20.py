# -*- coding: utf-8 -*-
"""B55: embed the ch20 chapter-exit card plate into zh/en docs."""
from embed import embed_after_text

SPECS = [
    ("docs/20-学习资源与工具链.md",
     "离开本章前，应有一份构建环境清单、四张带 revision/页码的来源卡、一组五层工具证据和一次干净重建对比。",
     "ch20-exit-kit.png",
     "Handraw：章末四张交付卡（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。看哪里：章末四张交付卡——构建环境卡（编译器版本、preset、ELF 哈希）、四张来源卡（DS/RM/ES 加 revision 与页码，留一栏「不能证明」）、一次 SPI 读 Flash 的五层证据、一次干净重建的 ELF/map 对比；证明什么：每张卡只证明自己那一栏——构建归谁、结论能追到哪一页、证据链到没到引脚、重建差异能否追因；不能证明什么：这是交付清单，不是实测，也替代不了手册原文。出处：本章「动手实验」与章末清单。"),
    ("docs/en/20-resources.md",
     "Before leaving this chapter, keep a build-environment inventory, four manual references with revision and page, one five-layer evidence set, and one clean-rebuild comparison.",
     "ch20-exit-kit.png",
     "Handraw: the four chapter-exit cards (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). Where to look: the four cards you leave the chapter with — build environment (compiler version, preset, ELF hash), four source cards (DS/RM/ES with revision and page, plus a cannot-prove slot), one five-layer evidence set for an SPI Flash read, and one clean-rebuild ELF/map diff; Proves each card proves only its own column — build ownership, traceability to a page, whether the evidence chain reaches the pin, whether a rebuild diff can be attributed; Cannot turn the checklist into a measurement or replace the manual text. See the Hands-on labs and the closing checklist."),
]

if __name__ == "__main__":
    bad = 0
    for spec in SPECS:
        if not embed_after_text(*spec):
            bad += 1
    if bad:
        raise SystemExit(f"{bad} embed(s) failed")
