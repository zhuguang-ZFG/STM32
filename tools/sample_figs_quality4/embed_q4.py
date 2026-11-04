#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Embed ch00/01/18–22 quality figures into zh+en chapters."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

BLOCK = """
<p align="center">
  <img src="{src}" width="{width}" alt="{alt}">
  <br><sub>{cap}</sub>
</p>
"""


def _insert_after_heading(path: Path, marker: str, needle: str, block: str) -> bool:
    text = path.read_text(encoding="utf-8")
    if needle in text:
        print("skip", path.name, needle)
        return False
    if marker not in text:
        raise SystemExit(f"marker missing in {path}: {marker!r}")
    idx = text.index(marker)
    nl = text.find("\n", idx)
    if nl < 0:
        raise SystemExit(f"no newline after marker in {path}")
    insert_at = nl + 1
    text = text[:insert_at] + "\n" + block + "\n" + text[insert_at:]
    path.write_text(text, encoding="utf-8")
    print("+", path.parent.name, path.name, "<-", needle)
    return True


def _blk(src, width, alt, cap):
    return BLOCK.format(src=src, width=width, alt=alt, cap=cap)


EMBEDS = [
    # ch00
    {
        "zh": ROOT / "docs" / "00-如何学习STM32.md",
        "en": ROOT / "docs" / "en" / "00-how-to-learn-stm32.md",
        "marker_zh": "### 2. 三种开发方式对比",
        "marker_en": "### 2. Three ways to write the firmware",
        "needle": "sample-00-three-ways.svg",
        "src_zh": "../assets/diagrams/sample-00-three-ways.svg",
        "src_en": "../../assets/diagrams/sample-00-three-ways.svg",
        "width": 760,
        "alt_zh": "三种写法：寄存器 / SPL / HAL，第一周只走一条车道",
        "alt_en": "Three lanes: register / SPL / HAL — pick one the first week",
        "cap_zh": "▲ 自绘。第一周只选一条车道；混用三个 API 会烧掉整周。",
        "cap_en": "▲ Drawn for this book. One lane the first week; mixing three APIs burns the week.",
    },
    {
        "zh": ROOT / "docs" / "00-如何学习STM32.md",
        "en": ROOT / "docs" / "en" / "00-how-to-learn-stm32.md",
        "marker_zh": "### 3. 三阶段学习路线图",
        "marker_en": "### 3. The three-stage roadmap",
        "needle": "sample-00-roadmap-gates.svg",
        "src_zh": "../assets/diagrams/sample-00-roadmap-gates.svg",
        "src_en": "../../assets/diagrams/sample-00-roadmap-gates.svg",
        "width": 760,
        "alt_zh": "三阶段门槛：闪灯 → 总线 → 系统，每级可测量",
        "alt_en": "Three-stage gates: blink → bus → system, each measurable",
        "cap_zh": "▲ 自绘。每阶段有可测门槛；别跳过 UART 验收去追 RTOS。",
        "cap_en": "▲ Drawn for this book. Measurable gates; do not skip UART accept for RTOS.",
    },
    {
        "zh": ROOT / "docs" / "00-如何学习STM32.md",
        "en": ROOT / "docs" / "en" / "00-how-to-learn-stm32.md",
        "marker_zh": "## BOOT0 改的是取指入口",
        "marker_en": "## BOOT0 changes the fetch alias",
        "needle": "sample-00-boot-fetch-flow.svg",
        "src_zh": "../assets/animations/sample-00-boot-fetch-flow.svg",
        "src_en": "../../assets/animations/sample-00-boot-fetch-flow.svg",
        "width": 720,
        "alt_zh": "BOOT0=0：从 0x08000000 取 MSP 与复位向量",
        "alt_en": "BOOT0=0: fetch MSP and Reset from 0x08000000",
        "cap_zh": "▲ 自绘矢量动画（FA-002）。BOOT0→别名→向量→运行。",
        "cap_en": "▲ Hand-drawn CSS animation (FA-002). BOOT0→alias→vectors→run.",
    },
    # ch01
    {
        "zh": ROOT / "docs" / "01-开发环境搭建.md",
        "en": ROOT / "docs" / "en" / "01-dev-environment.md",
        "marker_zh": "### 3. 四种开发环境对比",
        "marker_en": "### 3. Four development environments",
        "needle": "sample-01-env-compare.svg",
        "src_zh": "../assets/diagrams/sample-01-env-compare.svg",
        "src_en": "../../assets/diagrams/sample-01-env-compare.svg",
        "width": 760,
        "alt_zh": "四种环境一个契约：同一 ELF、同一 0x08000000",
        "alt_en": "Four IDEs, one contract: same ELF at 0x08000000",
        "cap_zh": "▲ 自绘。IDE 只是调用者；契约是同一 ELF 与烧录脚本。",
        "cap_en": "▲ Drawn for this book. The IDE is a caller; the contract is one ELF and flash script.",
    },
    {
        "zh": ROOT / "docs" / "01-开发环境搭建.md",
        "en": ROOT / "docs" / "en" / "01-dev-environment.md",
        "marker_zh": "### 芯片被读保护时怎么解锁",
        "marker_en": "### Clearing readout protection",
        "needle": "sample-01-rdp-unlock.svg",
        "src_zh": "../assets/diagrams/sample-01-rdp-unlock.svg",
        "src_en": "../../assets/diagrams/sample-01-rdp-unlock.svg",
        "width": 760,
        "alt_zh": "读保护解锁：RDP1 → 整片擦除 → RDP0",
        "alt_en": "RDP unlock: level 1 → mass erase → level 0",
        "cap_zh": "▲ 自绘。退出 RDP1 必整片擦除；先别怀疑 SWD 线。",
        "cap_en": "▲ Drawn for this book. Leaving RDP1 mass-erases; check OBR before rewiring SWD.",
    },
    {
        "zh": ROOT / "docs" / "01-开发环境搭建.md",
        "en": ROOT / "docs" / "en" / "01-dev-environment.md",
        "marker_zh": "## 时序与状态",
        "marker_en": "## Timing and state",
        "needle": "sample-01-flash-swd-flow.svg",
        "src_zh": "../assets/animations/sample-01-flash-swd-flow.svg",
        "src_en": "../../assets/animations/sample-01-flash-swd-flow.svg",
        "width": 720,
        "alt_zh": "SWD：烧录 ELF 后复位再取向量",
        "alt_en": "SWD: program ELF, reset, then fetch vectors",
        "cap_zh": "▲ 自绘矢量动画（FA-002）。烧录→复位→MSP/Reset。",
        "cap_en": "▲ Hand-drawn CSS animation (FA-002). Program→reset→MSP/Reset.",
    },
    # ch18
    {
        "zh": ROOT / "docs" / "18-常见问题FAQ.md",
        "en": ROOT / "docs" / "en" / "18-faq.md",
        "marker_zh": "## 一、编译与链接",
        "marker_en": "## 1. Build and link",
        "needle": "sample-18-link-map.svg",
        "src_zh": "../assets/diagrams/sample-18-link-map.svg",
        "src_en": "../../assets/diagrams/sample-18-link-map.svg",
        "width": 760,
        "alt_zh": "链接图排查：溢出 vs 错误的 FLASH ORIGIN",
        "alt_en": "Link-map triage: overflow vs wrong FLASH ORIGIN",
        "cap_zh": "▲ 自绘。C8=64 KB/20 KB；先读 region 再改 C。",
        "cap_en": "▲ Drawn for this book. C8=64 KB/20 KB; read the region line before rewriting C.",
    },
    {
        "zh": ROOT / "docs" / "18-常见问题FAQ.md",
        "en": ROOT / "docs" / "en" / "18-faq.md",
        "marker_zh": "## 二、下载与调试",
        "marker_en": "## 2. Download and debug",
        "needle": "sample-18-hardfault-ladder.svg",
        "src_zh": "../assets/diagrams/sample-18-hardfault-ladder.svg",
        "src_en": "../../assets/diagrams/sample-18-hardfault-ladder.svg",
        "width": 760,
        "alt_zh": "HardFault 梯子：先 CFSR，再信 BFAR",
        "alt_en": "HardFault ladder: CFSR first, then BFAR if valid",
        "cap_zh": "▲ 自绘。bit15=1 才信 BFAR；否则看压栈 PC。",
        "cap_en": "▲ Drawn for this book. Trust BFAR only when bit15=1; else use stacked PC.",
    },
    {
        "zh": ROOT / "docs" / "18-常见问题FAQ.md",
        "en": ROOT / "docs" / "en" / "18-faq.md",
        "marker_zh": "## 三、外设",
        "marker_en": "## 3. Peripherals",
        "needle": "sample-18-uart-garbled.svg",
        "src_zh": "../assets/diagrams/sample-18-uart-garbled.svg",
        "src_en": "../../assets/diagrams/sample-18-uart-garbled.svg",
        "width": 760,
        "alt_zh": "串口乱码清单：波特 · HSE · 交叉线 · 3.3 V",
        "alt_en": "UART garbled checklist: baud · HSE · swap · 3.3 V",
        "cap_zh": "▲ 自绘。先确认 SWS/BRR，再怀疑字符串代码。",
        "cap_en": "▲ Drawn for this book. Confirm SWS/BRR before rewriting string code.",
    },
    {
        "zh": ROOT / "docs" / "18-常见问题FAQ.md",
        "en": ROOT / "docs" / "en" / "18-faq.md",
        "marker_zh": "## 关键插图",
        "marker_en": "## Key figures",
        "needle": "sample-18-boot0-flow.svg",
        "src_zh": "../assets/animations/sample-18-boot0-flow.svg",
        "src_en": "../../assets/animations/sample-18-boot0-flow.svg",
        "width": 720,
        "alt_zh": "FAQ：BOOT0 拉低后从 Flash 启动",
        "alt_en": "FAQ: BOOT0 low, then Flash boot",
        "cap_zh": "▲ 自绘矢量动画（FA-002）。测 BOOT0 再改程序。",
        "cap_en": "▲ Hand-drawn CSS animation (FA-002). Measure BOOT0 before rewriting C.",
    },
    # ch19
    {
        "zh": ROOT / "docs" / "19-项目实战合集.md",
        "en": ROOT / "docs" / "en" / "19-projects.md",
        "marker_zh": "## 学习目标",
        "marker_en": "## Learning goals",
        "needle": "sample-19-pick-ladder.svg",
        "src_zh": "../assets/diagrams/sample-19-pick-ladder.svg",
        "src_en": "../../assets/diagrams/sample-19-pick-ladder.svg",
        "width": 760,
        "alt_zh": "选题梯子：星级对已通过的验收技能",
        "alt_en": "Pick ladder: star count vs skills you already accepted",
        "cap_zh": "▲ 自绘。选最小能逼出一条新总线的项目。",
        "cap_en": "▲ Drawn for this book. Pick the smallest project that forces one new bus.",
    },
    {
        "zh": ROOT / "docs" / "19-项目实战合集.md",
        "en": ROOT / "docs" / "en" / "19-projects.md",
        "marker_zh": "## 动手实验（选题与推进）",
        "marker_en": "## Hands-on labs (picking a project and moving it forward)",
        "needle": "sample-19-sram-budget.svg",
        "src_zh": "../assets/diagrams/sample-19-sram-budget.svg",
        "src_en": "../../assets/diagrams/sample-19-sram-budget.svg",
        "width": 760,
        "alt_zh": "SRAM 20 KB 预算：栈、DMA、.bss",
        "alt_en": "SRAM 20 KB budget: stacks, DMA, .bss",
        "cap_zh": "▲ 自绘。F103C8 先数缓冲区，再加任务。",
        "cap_en": "▲ Drawn for this book. Count buffers on C8 before adding tasks.",
    },
    {
        "zh": ROOT / "docs" / "19-项目实战合集.md",
        "en": ROOT / "docs" / "en" / "19-projects.md",
        "marker_zh": "## 关键插图",
        "marker_en": "## Key figures",
        "needle": "sample-19-slot-fill-flow.svg",
        "src_zh": "../assets/animations/sample-19-slot-fill-flow.svg",
        "src_en": "../../assets/animations/sample-19-slot-fill-flow.svg",
        "width": 720,
        "alt_zh": "单槽：16 KB + 2 KB + 0xB800 → 0x08010000",
        "alt_en": "One slot: 16 KB + 2 KB + 0xB800 → 0x08010000",
        "cap_zh": "▲ 自绘矢量动画（FA-002）。单镜像布局算术。",
        "cap_en": "▲ Hand-drawn CSS animation (FA-002). Single-image layout math.",
    },
    # ch20
    {
        "zh": ROOT / "docs" / "20-学习资源与工具链.md",
        "en": ROOT / "docs" / "en" / "20-resources.md",
        "marker_zh": "### 2. 手册命名规则（重点）",
        "marker_en": "### 2. How the manuals are named (this is the part to remember)",
        "needle": "sample-20-manual-names.svg",
        "src_zh": "../assets/diagrams/sample-20-manual-names.svg",
        "src_en": "../../assets/diagrams/sample-20-manual-names.svg",
        "width": 760,
        "alt_zh": "手册缩写：RM / DS / ES / PM 对上问题",
        "alt_en": "Manual acronyms: RM / DS / ES / PM matched to the question",
        "cap_zh": "▲ 自绘。先选对 PDF，再 Ctrl+F。",
        "cap_en": "▲ Drawn for this book. Pick the right PDF before Ctrl+F.",
    },
    {
        "zh": ROOT / "docs" / "20-学习资源与工具链.md",
        "en": ROOT / "docs" / "en" / "20-resources.md",
        "marker_zh": "### 4. 开源固件库对比",
        "marker_en": "### 4. Open-source firmware libraries, side by side",
        "needle": "sample-20-lib-compare.svg",
        "src_zh": "../assets/diagrams/sample-20-lib-compare.svg",
        "src_en": "../../assets/diagrams/sample-20-lib-compare.svg",
        "width": 760,
        "alt_zh": "固件库对比：SPL / HAL / LL / libopencm3",
        "alt_en": "Library compare: SPL / HAL / LL / libopencm3",
        "cap_zh": "▲ 自绘。一个项目冻结一套库与版本。",
        "cap_en": "▲ Drawn for this book. Freeze one library stack per project.",
    },
    {
        "zh": ROOT / "docs" / "20-学习资源与工具链.md",
        "en": ROOT / "docs" / "en" / "20-resources.md",
        "marker_zh": "## 遇到问题时去哪找证据",
        "marker_en": "## Where to look for evidence",
        "needle": "sample-20-evidence-flow.svg",
        "src_zh": "../assets/animations/sample-20-evidence-flow.svg",
        "src_en": "../../assets/animations/sample-20-evidence-flow.svg",
        "width": 720,
        "alt_zh": "取证：症状 → 选手册 → 记版本",
        "alt_en": "Evidence: symptom → pick manual → note revision",
        "cap_zh": "▲ 自绘矢量动画（FA-002）。博客是线索，冻结 PDF 是契约。",
        "cap_en": "▲ Hand-drawn CSS animation (FA-002). Blogs hint; frozen PDFs contract.",
    },
    # ch21
    {
        "zh": ROOT / "docs" / "21-原理图与实物图鉴.md",
        "en": ROOT / "docs" / "en" / "21-board-maps.md",
        "marker_zh": "### 1. BluePill · STM32F103C8T6",
        "marker_en": "### 1. BluePill · STM32F103C8T6",
        "needle": "sample-21-vdd-3v3.svg",
        "src_zh": "../assets/diagrams/sample-21-vdd-3v3.svg",
        "src_en": "../../assets/diagrams/sample-21-vdd-3v3.svg",
        "width": 760,
        "alt_zh": "BluePill 电源轨：5 V · 3V3 · VDDA · VBAT",
        "alt_en": "BluePill rails: 5 V · 3V3 · VDDA · VBAT",
        "cap_zh": "▲ 自绘。先量 3V3，再怀疑固件。",
        "cap_en": "▲ Drawn for this book. Measure 3V3 before blaming firmware.",
    },
    {
        "zh": ROOT / "docs" / "21-原理图与实物图鉴.md",
        "en": ROOT / "docs" / "en" / "21-board-maps.md",
        "marker_zh": "### 如何看懂一张最小系统原理图",
        "marker_en": "### How to read a minimum-system schematic",
        "needle": "sample-21-hse-load.svg",
        "src_zh": "../assets/diagrams/sample-21-hse-load.svg",
        "src_en": "../../assets/diagrams/sample-21-hse-load.svg",
        "width": 760,
        "alt_zh": "HSE 8 MHz：PD0/PD1 与负载电容",
        "alt_en": "HSE 8 MHz: PD0/PD1 and load caps",
        "cap_zh": "▲ 自绘。HSERDY 不到先查晶振焊接，再怪 PLLMUL。",
        "cap_en": "▲ Drawn for this book. No HSERDY → check the can before PLLMUL.",
    },
    {
        "zh": ROOT / "docs" / "21-原理图与实物图鉴.md",
        "en": ROOT / "docs" / "en" / "21-board-maps.md",
        "marker_zh": "### 7. 常用外设接线总览（peripheral-wiring）",
        "marker_en": "### 7. Peripheral wiring overview",
        "needle": "sample-21-usb-ttl.svg",
        "src_zh": "../assets/diagrams/sample-21-usb-ttl.svg",
        "src_en": "../../assets/diagrams/sample-21-usb-ttl.svg",
        "width": 760,
        "alt_zh": "USB-TTL ↔ USART1：PA9/PA10 交叉，共地 3.3 V",
        "alt_en": "USB-TTL ↔ USART1: cross PA9/PA10, shared 3.3 V GND",
        "cap_zh": "▲ 自绘。TX/RX 交叉、共地；别把 5 V 灌进 PA10。",
        "cap_en": "▲ Drawn for this book. Cross TX/RX, share GND; no 5 V into PA10.",
    },
    {
        "zh": ROOT / "docs" / "21-原理图与实物图鉴.md",
        "en": ROOT / "docs" / "en" / "21-board-maps.md",
        "marker_zh": "## 常见坑与排查",
        "marker_en": "## Pitfalls and troubleshooting",
        "needle": "sample-21-nrst-boot0.svg",
        "src_zh": "../assets/diagrams/sample-21-nrst-boot0.svg",
        "src_en": "../../assets/diagrams/sample-21-nrst-boot0.svg",
        "width": 760,
        "alt_zh": "NRST 与 BOOT0：引脚 7 与 44",
        "alt_en": "NRST and BOOT0: pins 7 and 44",
        "cap_zh": "▲ 自绘。BOOT0=1 会跑系统存储器，不是“程序丢了”。",
        "cap_en": "▲ Drawn for this book. BOOT0=1 boots system memory — not a 'lost' app.",
    },
    {
        "zh": ROOT / "docs" / "21-原理图与实物图鉴.md",
        "en": ROOT / "docs" / "en" / "21-board-maps.md",
        "marker_zh": "## 核心原理",
        "marker_en": "## Core ideas",
        "needle": "sample-21-crystal-boot-flow.svg",
        "src_zh": "../assets/animations/sample-21-crystal-boot-flow.svg",
        "src_en": "../../assets/animations/sample-21-crystal-boot-flow.svg",
        "width": 720,
        "alt_zh": "板级：3V3 与 HSE 就绪后再从 Flash 启动",
        "alt_en": "Board: 3V3 and HSE ready, then Flash boot",
        "cap_zh": "▲ 自绘矢量动画（FA-002）。上电顺序：电源→晶振→BOOT0→向量。",
        "cap_en": "▲ Hand-drawn CSS animation (FA-002). Power→crystal→BOOT0→vectors.",
    },
    # ch22
    {
        "zh": ROOT / "docs" / "22-仿真实验Wokwi与Renode.md",
        "en": ROOT / "docs" / "en" / "22-simulation-wokwi-renode.md",
        "marker_zh": "## Wokwi：图怎么读",
        "marker_en": "## Wokwi: how to read the diagram",
        "needle": "sample-22-wokwi-scope.svg",
        "src_zh": "../assets/diagrams/sample-22-wokwi-scope.svg",
        "src_en": "../../assets/diagrams/sample-22-wokwi-scope.svg",
        "width": 760,
        "alt_zh": "Wokwi 擅长与边界：逻辑可以，模拟要上桌",
        "alt_en": "Wokwi fit and limits: logic yes, analog on the desk",
        "cap_zh": "▲ 自绘。浏览器绿了还要 BluePill 同款验收。",
        "cap_en": "▲ Drawn for this book. Browser green still needs the BluePill accept.",
    },
    {
        "zh": ROOT / "docs" / "22-仿真实验Wokwi与Renode.md",
        "en": ROOT / "docs" / "en" / "22-simulation-wokwi-renode.md",
        "marker_zh": "## Renode：两条脚本",
        "marker_en": "## Renode: two scripts",
        "needle": "sample-22-renode-path.svg",
        "src_zh": "../assets/diagrams/sample-22-renode-path.svg",
        "src_en": "../../assets/diagrams/sample-22-renode-path.svg",
        "width": 760,
        "alt_zh": "Renode 路径：平台 → ELF → UART 分析",
        "alt_en": "Renode path: platform → ELF → UART analyzer",
        "cap_zh": "▲ 自绘。先跑仓库两条脚本，再改平台文件。",
        "cap_en": "▲ Drawn for this book. Run the two repo scripts before editing platforms.",
    },
    {
        "zh": ROOT / "docs" / "22-仿真实验Wokwi与Renode.md",
        "en": ROOT / "docs" / "en" / "22-simulation-wokwi-renode.md",
        "marker_zh": "## 仿真替不了的事",
        "marker_en": "## What simulation will not do for you",
        "needle": "sample-22-hw-gap.svg",
        "src_zh": "../assets/diagrams/sample-22-hw-gap.svg",
        "src_en": "../../assets/diagrams/sample-22-hw-gap.svg",
        "width": 760,
        "alt_zh": "仿真与实物差距：哪些必须上桌",
        "alt_en": "Sim vs hardware gap: what still needs the desk",
        "cap_zh": "▲ 自绘。双轨诚实：结构靠仿真，裕量靠桌面。",
        "cap_en": "▲ Drawn for this book. Dual-track: structure in sim, margins on the desk.",
    },
    {
        "zh": ROOT / "docs" / "22-仿真实验Wokwi与Renode.md",
        "en": ROOT / "docs" / "en" / "22-simulation-wokwi-renode.md",
        "marker_zh": "## 先选哪一家",
        "marker_en": "## Which one to open first",
        "needle": "sample-22-sim-pick-flow.svg",
        "src_zh": "../assets/animations/sample-22-sim-pick-flow.svg",
        "src_en": "../../assets/animations/sample-22-sim-pick-flow.svg",
        "width": 720,
        "alt_zh": "仿真：先选工具，绿线后再上桌",
        "alt_en": "Sim: pick a tool, go green, then the desk",
        "cap_zh": "▲ 自绘矢量动画（FA-002）。选型→证明→移植。",
        "cap_en": "▲ Hand-drawn CSS animation (FA-002). Pick→prove→port.",
    },
]


def main() -> None:
    n = 0
    for e in EMBEDS:
        block_zh = _blk(e["src_zh"], e["width"], e["alt_zh"], e["cap_zh"])
        block_en = _blk(e["src_en"], e["width"], e["alt_en"], e["cap_en"])
        if _insert_after_heading(e["zh"], e["marker_zh"], e["needle"], block_zh):
            n += 1
        if _insert_after_heading(e["en"], e["marker_en"], e["needle"], block_en):
            n += 1
    print(f"embed ops applied: {n} / {len(EMBEDS) * 2}")


if __name__ == "__main__":
    main()
