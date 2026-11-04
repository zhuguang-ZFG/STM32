# -*- coding: utf-8 -*-
"""Embed appendix A–F handraw PNGs into stm32-book/book (+ en)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _asset_prefix(doc: str) -> str:
    # stm32-book/book/X.md -> ../../assets/
    # stm32-book/book/en/X.md -> ../../../assets/
    if "/en/" in doc.replace("\\", "/") or doc.startswith("stm32-book/book/en/"):
        return "../../../assets/"
    return "../../assets/"


def embed_after_img(doc: str, anchor_img: str, png: str, alt: str, caption: str,
                    width: str = "760") -> bool:
    path = ROOT / doc
    text = path.read_text(encoding="utf-8")
    if f"illustrations/handraw/{png}" in text:
        print(f"SKIP {doc}: {png} already embedded")
        return True
    pat = re.compile(
        r'(<p align="center">\s*\n\s*<img src="[^"]*?' + re.escape(anchor_img) +
        r'".*?</p>)', re.DOTALL)
    m = pat.search(text)
    if not m:
        print(f"MISS {doc}: anchor img {anchor_img}")
        return False
    prefix = _asset_prefix(doc)
    block = (
        f'\n\n<p align="center">\n'
        f'  <img src="{prefix}illustrations/handraw/{png}" '
        f'width="{width}" alt="{alt}">\n'
        f'  <br><sub>{caption}</sub>\n'
        f'</p>'
    )
    path.write_text(text[: m.end()] + block + text[m.end() :], encoding="utf-8", newline="\n")
    print(f"OK   {doc}: {png} after img {anchor_img}")
    return True


def embed_after_heading(doc: str, heading: str, png: str, alt: str, caption: str,
                        width: str = "760") -> bool:
    """Insert figure block immediately after a ## heading line."""
    path = ROOT / doc
    text = path.read_text(encoding="utf-8")
    if f"illustrations/handraw/{png}" in text:
        print(f"SKIP {doc}: {png} already embedded")
        return True
    # Match exact ## heading line
    pat = re.compile(r"(^##\s+" + re.escape(heading) + r"\s*\n)", re.M)
    m = pat.search(text)
    if not m:
        print(f"MISS {doc}: heading ## {heading}")
        return False
    prefix = _asset_prefix(doc)
    block = (
        f'\n<p align="center">\n'
        f'  <img src="{prefix}illustrations/handraw/{png}" '
        f'width="{width}" alt="{alt}">\n'
        f'  <br><sub>{caption}</sub>\n'
        f'</p>\n'
    )
    path.write_text(text[: m.end()] + block + text[m.end() :], encoding="utf-8", newline="\n")
    print(f"OK   {doc}: {png} after ## {heading}")
    return True


ZH_CAP = "▲ 知识轨（Handraw · 原理示意/非实拍）。{body}"
EN_CAP = "▲ Knowledge track (Handraw · 原理示意 / not a photo). {body}"


def run():
    specs = []

    # ----- A: after existing SVG + after key headings -----
    a_zh, a_en = "stm32-book/book/A-工程深读.md", "stm32-book/book/en/A-uart-dma.md"
    specs += [
        ("img", a_zh, "uart-idle-dma.svg", "app-a-invariants.png",
         "Handraw：四条接收不变量（原理示意）",
         ZH_CAP.format(body="DMA 写区应用不碰；Size 是首个未写位置；交给业务的是新增区间；跟不上必须计数。非实拍。")),
        ("img", a_en, "uart-idle-dma.svg", "app-a-invariants.png",
         "Handraw: four reception invariants (原理示意)",
         EN_CAP.format(body="Do not write the DMA region; Size is the first unwritten index; hand over the new slice; count overflow. Not a photo.")),
        ("h", a_zh, "2. 契约 A：Normal DMA，每次结束后重新武装", "app-a-contract-a.png",
         "Handraw：契约 A 与空窗（原理示意）",
         ZH_CAP.format(body="Normal DMA 每次重新武装并关 HT；复制期间可能 ORE；连续流改契约 B。非实拍。")),
        ("h", a_en, "2. Contract A: normal DMA, re-armed after every event", "app-a-contract-a.png",
         "Handraw: contract A and the gap (原理示意)",
         EN_CAP.format(body="Normal DMA re-arms and disables HT each round; ORE can hit during copy; use B for continuous streams. Not a photo.")),
        ("h", a_zh, "3. 契约 B：Circular DMA，启动一次，按位置取增量", "app-a-contract-b.png",
         "Handraw：契约 B 环形取模（原理示意）",
         ZH_CAP.format(body="启动一次；pos 与 old_pos 算增量；禁止每次重新 ReceiveToIdle。非实拍。")),
        ("h", a_en, "3. Contract B: circular DMA, armed once, read by position", "app-a-contract-b.png",
         "Handraw: contract B ring math (原理示意)",
         EN_CAP.format(body="Arm once; compute the new slice from pos and old_pos; never re-call ReceiveToIdle each callback. Not a photo.")),
        ("h", a_zh, "4. ISR 与业务层的边界", "app-a-isr-boundary.png",
         "Handraw：ISR 与业务边界（原理示意）",
         ZH_CAP.format(body="ISR 只做有界拷贝与计数；解析与阻塞留在任务；FromISR 要满足优先级。非实拍。")),
        ("h", a_en, "4. The boundary between the ISR and the application", "app-a-isr-boundary.png",
         "Handraw: ISR vs application (原理示意)",
         EN_CAP.format(body="ISR copies a bounded slice and counts; parsing and blocking stay in tasks; FromISR needs a legal priority. Not a photo.")),
        ("h", a_zh, "6. 最小验证矩阵", "app-a-verify.png",
         "Handraw：最小验证矩阵（原理示意）",
         ZH_CAP.format(body="刺激→可见结果→不证明什么；ORE 恢复与 dropped_bytes 必须可观察。非实拍。")),
        ("h", a_en, "6. A minimum check matrix", "app-a-verify.png",
         "Handraw: minimal verification matrix (原理示意)",
         EN_CAP.format(body="Stimulus → visible result → what it does not prove; ORE recovery and dropped_bytes must be observable. Not a photo.")),
    ]

    # ----- B -----
    b_zh, b_en = "stm32-book/book/B-例程索引.md", "stm32-book/book/en/B-examples.md"
    specs += [
        ("h", b_zh, "先和账对上的四行", "app-b-four-rows.png",
         "Handraw：先对四行账（原理示意）",
         ZH_CAP.format(body="PC13 极性、1 kHz PWM、USART1 BRR 0x271、CAN 500k；对不上不加下一条总线。非实拍。")),
        ("h", b_en, "Four rows to match before you run the list", "app-b-four-rows.png",
         "Handraw: four rows to match first (原理示意)",
         EN_CAP.format(body="PC13 polarity, 1 kHz PWM, USART1 BRR 0x271, CAN 500 kbit/s; do not add the next bus on a mismatch. Not a photo.")),
        ("h", b_zh, "通道和描述符再对三行", "app-b-channel-desc.png",
         "Handraw：通道与描述符三行（原理示意）",
         ZH_CAP.format(body="JEDEC EF4017、CDC 67 字节、栈深按字计。非实拍。")),
        ("h", b_en, "Three more rows for the channel and the descriptor", "app-b-channel-desc.png",
         "Handraw: channel and descriptor rows (原理示意)",
         EN_CAP.format(body="JEDEC EF4017, CDC 67-byte config, stack depth in words. Not a photo.")),
        ("h", b_zh, "推荐跑法", "app-b-run-order.png",
         "Handraw：推荐跑法五步（原理示意）",
         ZH_CAP.format(body="闭环→单外设→状态→并发→SPL 单独；勿混 HAL 初始化。非实拍。")),
        ("h", b_en, "A useful order", "app-b-run-order.png",
         "Handraw: useful run order (原理示意)",
         EN_CAP.format(body="Close the loop → one peripheral → state → concurrency → SPL alone; do not mix HAL init. Not a photo.")),
        ("h", b_zh, "每个例程的交付记录", "app-b-delivery.png",
         "Handraw：交付记录字段（原理示意）",
         ZH_CAP.format(body="料号/工具/接线/期望/实测/边界/复现；编译通过不算完成。非实拍。")),
        ("h", b_en, "A record for each example", "app-b-delivery.png",
         "Handraw: delivery record fields (原理示意)",
         EN_CAP.format(body="Part/tools/wiring/expected/actual/boundary/reproduce; compiling is not done. Not a photo.")),
    ]

    # ----- C -----
    c_zh, c_en = "stm32-book/book/C-习题答案.md", "stm32-book/book/en/C-answers.md"
    # Use first chapter heading present in both
    specs += [
        ("h", c_zh, "00 如何学习 STM32", "app-c-discipline.png",
         "Handraw：答案怎么用（原理示意）",
         ZH_CAP.format(body="先自做再对照；禁背答案替实验。非实拍。")),
        ("h", c_en, "00 How to Learn STM32", "app-c-discipline.png",
         "Handraw: how to use the answers (原理示意)",
         EN_CAP.format(body="Solve first, then compare; do not memorize answers instead of measuring. Not a photo.")),
        ("h", c_zh, "03 GPIO 与 LED", "app-c-early-checks.png",
         "Handraw：前几章自测焦点（原理示意）",
         ZH_CAP.format(body="极性、EXTI、1 kHz 算术是早期核对轴。非实拍。")),
        ("h", c_en, "03 GPIO and the LED", "app-c-early-checks.png",
         "Handraw: early-chapter check focus (原理示意)",
         EN_CAP.format(body="Polarity, EXTI, and 1 kHz arithmetic are the early check axes. Not a photo.")),
        ("h", c_zh, "13 CAN 总线", "app-c-bus-system.png",
         "Handraw：总线到系统核对轴（原理示意）",
         ZH_CAP.format(body="环回≠ACK；IAP 拒跳；FromISR 优先级；CFSR 先读。非实拍。")),
        ("h", c_en, "13 CAN", "app-c-bus-system.png",
         "Handraw: bus → system check axis (原理示意)",
         EN_CAP.format(body="Loopback ≠ ACK; refuse a bad IAP image; FromISR priority; read CFSR first. Not a photo.")),
        ("h", c_zh, "28 嵌入式系统与 RTOS 生态", "app-c-not-proof.png",
         "Handraw：答对数字≠产品证据（原理示意）",
         ZH_CAP.format(body="自测证明读懂契约，不签收量产与最坏响应。非实拍。")),
        ("h", c_en, "28 Systems and the RTOS Landscape", "app-c-not-proof.png",
         "Handraw: right number ≠ product proof (原理示意)",
         EN_CAP.format(body="Self-checks prove you read the contract; they do not sign off production or worst-case response. Not a photo.")),
    ]

    # ----- D -----
    d_zh, d_en = "stm32-book/book/D-术语表.md", "stm32-book/book/en/D-glossary.md"
    specs += [
        ("h", d_zh, "时钟与复位", "app-d-lookup.png",
         "Handraw：术语怎么查（原理示意）",
         ZH_CAP.format(body="定领域→对章节→回正文→对附录 E。非实拍。")),
        ("h", d_en, "Clocks and reset", "app-d-lookup.png",
         "Handraw: how to look up a term (原理示意)",
         EN_CAP.format(body="Pick the domain → match the chapter → return to the prose → check Appendix E. Not a photo.")),
        ("h", d_zh, "UART、I2C、SPI、CAN 与 USB", "app-d-clusters.png",
         "Handraw：术语分组地图（原理示意）",
         ZH_CAP.format(body="分组对齐章主题；表不是手册替身。非实拍。")),
        ("h", d_en, "UART, I2C, SPI, CAN, and USB", "app-d-clusters.png",
         "Handraw: glossary clusters (原理示意)",
         EN_CAP.format(body="Clusters follow chapter themes; the glossary is not a substitute manual. Not a photo.")),
        ("h", d_zh, "工程习惯", "app-d-pin-table.png",
         "Handraw：钉住数字的四格（原理示意）",
         ZH_CAP.format(body="料号·文档·寄存器/公式·算术；空一格仍是线索。非实拍。")),
        ("h", d_en, "Engineering habits", "app-d-pin-table.png",
         "Handraw: four cells that pin a number (原理示意)",
         EN_CAP.format(body="Part, document, register/formula, arithmetic; leave one empty and it is still a clue. Not a photo.")),
        ("h", d_zh, "调试", "app-d-not-rm.png",
         "Handraw：术语表不是手册（原理示意）",
         ZH_CAP.format(body="给对照与短定义；不给电气极限与全位域表。非实拍。")),
        ("h", d_en, "Debug", "app-d-not-rm.png",
         "Handraw: glossary ≠ reference manual (原理示意)",
         EN_CAP.format(body="Short definitions and cross-refs; not electrical limits or full bit-field tables. Not a photo.")),
    ]

    # ----- E -----
    e_zh, e_en = "stm32-book/book/E-参考资料.md", "stm32-book/book/en/E-sources.md"
    specs += [
        ("h", e_zh, "快照规则", "app-e-layers.png",
         "Handraw：四层来源（原理示意）",
         ZH_CAP.format(body="手册→厂商代码→社区→本书原创；彼此不替代。非实拍。")),
        ("h", e_en, "Snapshot rules", "app-e-layers.png",
         "Handraw: four source layers (原理示意)",
         EN_CAP.format(body="Manuals → vendor code → community → this book; layers do not replace each other. Not a photo.")),
        ("h", e_zh, "一笔数字怎样才算钉住", "app-e-snapshot.png",
         "Handraw：快照规则（原理示意）",
         ZH_CAP.format(body="文档号/Rev；Git 冻 SHA；社区记访问日；复现冻料号与工具链。非实拍。")),
        ("h", e_en, "When a number is actually pinned", "app-e-snapshot.png",
         "Handraw: snapshot rules (原理示意)",
         EN_CAP.format(body="Doc number/Rev; freeze Git at a SHA; date community posts; freeze part and toolchain for repro. Not a photo.")),
        ("h", e_zh, "把一格填满", "app-e-pin-number.png",
         "Handraw：115200 格子范例（原理示意）",
         ZH_CAP.format(body="USART1@72 MHz → BRR 0x271；只写误差百分比不算钉住。非实拍。")),
        ("h", e_en, "What fills one cell", "app-e-pin-number.png",
         "Handraw: the 115200 cell pattern (原理示意)",
         EN_CAP.format(body="USART1 at 72 MHz → BRR 0x271; an error percentage alone does not pin the cell. Not a photo.")),
        ("h", e_zh, "许可边界", "app-e-license.png",
         "Handraw：许可边界（原理示意）",
         ZH_CAP.format(body="CC BY / CC0 / MIT；第三方手册不转载。非实拍。")),
        ("h", e_en, "License boundary", "app-e-license.png",
         "Handraw: license boundary (原理示意)",
         EN_CAP.format(body="CC BY / CC0 / MIT; third-party manuals are linked, not redistributed. Not a photo.")),
        ("h", e_zh, "来源登记表", "app-e-fill-cell.png",
         "Handraw：把一格填满（原理示意）",
         ZH_CAP.format(body="料号·时钟·寄存器·算术·证伪；500 kbit/s 是填满范例。非实拍。")),
        ("h", e_en, "Source register", "app-e-fill-cell.png",
         "Handraw: what fills one cell (原理示意)",
         EN_CAP.format(body="Part, clock, register, arithmetic, falsifier; 500 kbit/s is the filled example. Not a photo.")),
    ]

    # ----- F: after existing SVGs + one heading -----
    f_zh, f_en = "stm32-book/book/F-开源地图.md", "stm32-book/book/en/F-oss-map.md"
    specs += [
        ("img", f_zh, "sample-f-repo-lane-flow.svg", "app-f-lane.png",
         "Handraw：选一条车道读到底（原理示意）",
         ZH_CAP.format(body="选树→读文件→冻 SHA→写引用→实验卡。非实拍。")),
        ("img", f_en, "sample-f-repo-lane-flow.svg", "app-f-lane.png",
         "Handraw: pick one repo lane (原理示意)",
         EN_CAP.format(body="Pick the tree → read the file → freeze the SHA → cite → lab card. Not a photo.")),
        ("img", f_zh, "sample-f-oss-map.svg", "app-f-stars.png",
         "Handraw：星标多≠该读（原理示意）",
         ZH_CAP.format(body="该不该读只看有没有目标 .h/函数。非实拍。")),
        ("img", f_en, "sample-f-oss-map.svg", "app-f-stars.png",
         "Handraw: stars ≠ should-read (原理示意)",
         EN_CAP.format(body="Read it only if the target .h or function is there. Not a photo.")),
        ("img", f_zh, "sample-f-six-facts.svg", "app-f-six-facts.png",
         "Handraw：六个源码知识点（原理示意）",
         ZH_CAP.format(body="许可配料表、CMSIS 内联、pbuf 链、就绪表等只能读源码拿到。非实拍。")),
        ("img", f_en, "sample-f-six-facts.svg", "app-f-six-facts.png",
         "Handraw: six facts from source (原理示意)",
         EN_CAP.format(body="License mix, CMSIS inlines, pbuf chains, ready lists — only source gives them. Not a photo.")),
        ("img", f_zh, "sample-f-ask-before.svg", "app-f-ask-before.png",
         "Handraw：提问前五件事（原理示意）",
         ZH_CAP.format(body="README、冻 commit、最小复现、原文日志、已排除路径。非实拍。")),
        ("img", f_en, "sample-f-ask-before.svg", "app-f-ask-before.png",
         "Handraw: five things before asking (原理示意)",
         EN_CAP.format(body="README, frozen commit, minimal repro, raw logs, paths already ruled out. Not a photo.")),
        ("h", f_zh, "证据口径", "app-f-evidence.png",
         "Handraw：证据口径（原理示意）",
         ZH_CAP.format(body="手册优先，源码第二，社区第三，实验收口。非实拍。")),
        ("h", f_en, "Evidence policy", "app-f-evidence.png",
         "Handraw: evidence rule (原理示意)",
         EN_CAP.format(body="Manuals first, source second, community third, lab closes the loop. Not a photo.")),
    ]

    bad = 0
    for spec in specs:
        kind = spec[0]
        if kind == "img":
            _, doc, anchor, png, alt, cap = spec
            if not embed_after_img(doc, anchor, png, alt, cap):
                bad += 1
        else:
            _, doc, heading, png, alt, cap = spec
            if not embed_after_heading(doc, heading, png, alt, cap):
                bad += 1
    if bad:
        sys.exit(f"{bad} embed(s) failed")
    print("all embeds ok")


if __name__ == "__main__":
    run()
