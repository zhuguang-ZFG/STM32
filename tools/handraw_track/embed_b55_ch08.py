# -*- coding: utf-8 -*-
"""B55: embed the two ch08 knowledge-track plates into zh/en docs (bottom-up)."""
from embed import embed_after_text

SPECS = [
    # 2. ch08-page-write-flow — after the "before leaving" paragraph
    ("docs/08-SPI总线.md",
     "离开本章前，应有一张 JEDEC 四线波形、WREN 前后的状态寄存器记录和一份 16 字节读回比对。",
     "ch08-page-write-flow.png",
     "Handraw：页写入的五级台阶（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。看哪里：五级台阶从 CS 拉低发 0x06（WREN）开始，CS 拉高结束写使能事务、WEL 置位，再拉低发 0x02（PAGE PROGRAM）加一页 256 字节，CS 拉高后进入右侧轮询 0x05 直到状态字节位 0 清零；证明什么：写使能是独立的一次事务，跳过它 WEL 不置位、数据不变；忙位属于 Flash 状态字节，不是 SPI_SR；不能证明什么：这是命令顺序图，不含页边界回卷、编程耗时与实际波形，也不是逻辑分析仪截图。出处：[RM0008 Rev 21 第 25 章](#source-rm0008-spi) 与 [例程](#source-project-examples)。"),
    ("docs/en/08-spi.md",
     "Before leaving this chapter, keep one four-wire JEDEC capture, status-register records before and after WREN, and the 16-byte readback comparison.",
     "ch08-page-write-flow.png",
     "Handraw: the five rungs of a page write (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). Where to look: five rungs start at CS low with 0x06 (WREN), CS high ends the write-enable transaction and sets WEL, CS low again sends 0x02 (PAGE PROGRAM) plus one 256-byte page, and CS high leads into the poll loop that reads 0x05 until bit 0 of the status byte clears; Proves write-enable is its own transaction (skip it and WEL stays clear, so the data does not change) and the busy bit belongs to the flash status byte, not SPI_SR; Cannot prove page-boundary wrap, programming time or any waveform — not a logic-analyzer capture. See [RM0008 Rev 21 ch.25](#source-rm0008-spi) and the [example](#source-project-examples)."),

    # 1. ch08-id-assembly — after the learning-goals checkbox
    ("docs/08-SPI总线.md",
     "- [ ] 会用 W25Q64 读 ID/读写页、ST7789 初始化",
     "ch08-id-assembly.png",
     "Handraw：ID 的四个接收槽与 24 位拼接（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。看哪里：左边四个接收槽 rx[0] 到 rx[3]，右边汇成一个 24 位数，rx[0] 被划掉，rx[1]、rx[2]、rx[3] 分别标着左移 16、8、0 位；证明什么：ID 只取 rx[1]=0xEF（Winbond）、rx[2]=0x40（类型，不是容量）、rx[3]=0x17（容量），三段移位相或才得到 0xEF4017；不能证明什么：这是字节到字段的对应图，不含移位时序与采样沿，也不是逻辑分析仪截图。出处：[RM0008 Rev 21 第 25.5.1 节](#source-rm0008-spi) 与 [例程](#source-project-examples)。"),
    ("docs/en/08-spi.md",
     "- [ ] Read a W25Q64 ID, read and write a page, and initialize an ST7789",
     "ch08-id-assembly.png",
     "Handraw: four receive slots assembled into a 24-bit ID (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). Where to look: four receive slots rx[0]–rx[3] on the left feed one 24-bit word on the right, with rx[0] struck out and rx[1], rx[2], rx[3] tagged 16, 8, and 0 shifts left; Proves the id uses only rx[1]=0xEF (Winbond), rx[2]=0x40 (memory type, not capacity) and rx[3]=0x17 (capacity), and the three fields shift and OR into 0xEF4017; Cannot prove shift timing or a sampling edge — this is a byte-to-field map, not a logic-analyzer capture. See [RM0008 Rev 21 §25.5.1](#source-rm0008-spi) and the [example](#source-project-examples)."),
]

if __name__ == "__main__":
    bad = 0
    for spec in SPECS:
        if not embed_after_text(*spec):
            bad += 1
    if bad:
        raise SystemExit(f"{bad} embed(s) failed")
