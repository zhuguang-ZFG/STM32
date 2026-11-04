#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static B4 figure for chapter 15: FreeRTOS triage.

No CSS animation and no SMIL.

    python tools/sample_figs_b4/ch15_b4.py assets/diagrams
"""

from __future__ import annotations

import hashlib
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from svgkit import Svg, T


def _credit(canvas: Svg, note: str) -> None:
    canvas.line(24, canvas.h - 36, canvas.w - 24, canvas.h - 36, stroke=T.GRID, sw=1)
    canvas.text(24, canvas.h - 16, note, size=11, fill=T.MUTED)
    canvas.text(canvas.w - 24, canvas.h - 16, "自绘 · 静态 · CC BY 4.0", size=11, fill=T.DIM, anchor="end")


def rtos_triage() -> Svg:
    canvas = Svg(
        960,
        880,
        "任务不动、栈溢出、优先级异常：1 ms 一个 tick，128 字是 512 字节，FromISR 的抢占优先级数值至少 5",
        "STM32F103C8T6 · chapter 15 · FreeRTOS Kernel V11.3.2",
    )
    canvas.header(title="RTOS 三岔口：调度器、栈的单位、优先级方向", tag="15", tag_color=T.CYAN)
    canvas.text(40, 86, "RTOS 三岔口：先看调度器起没起，再看栈的单位是字还是字节，最后看优先级的方向",
                size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "three branches, one rule each: TIM4 timebase / word-vs-byte stack / numeric priority 5",
                size=14, fill=T.CYAN)
    canvas.text(40, 138,
                "configTICK_RATE_HZ = 1000 (1 ms)   configTOTAL_HEAP_SIZE = 10240   "
                "configMAX_SYSCALL_INTERRUPT_PRIORITY = 0x50",
                size=13, fill=T.AMBER, mono=True)

    canvas.text(40, 170, "岔口一  任务不动：调度器根本没起来", size=16, fill=T.RED, weight="700")
    canvas.text(920, 170, "SysTick · ARM_CM3 · configTOTAL_HEAP_SIZE", size=11, fill=T.MUTED,
                anchor="end", mono=True)
    canvas.rect(40, 184, 880, 174, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 214, "症状：vTaskStartScheduler() 迟迟不返回，HAL_Delay 卡住，或者一启动就 HardFault",
                size=14, fill=T.TEXT)
    canvas.text(56, 240, "原因 A：内核和 HAL 抢 SysTick。SYS → Timebase Source 改 TIM4，两边共用就一起卡死",
                size=14, fill=T.TEXT)
    canvas.text(56, 266, "原因 B：移植层选了 ARM_CM4F。M3 没有 FPU，编译能过，调度器一启动就 HardFault",
                size=14, fill=T.TEXT)
    canvas.text(56, 292, "原因 C：xTaskCreate 返回 pdFAIL。堆不够，configTOTAL_HEAP_SIZE 是 10240 字节",
                size=14, fill=T.TEXT)
    canvas.text(56, 318, "检查点：LED 128 字、KEY 192 字、UART 256 字，三块任务栈都从这 10240 字节里出",
                size=14, fill=T.TEXT)
    canvas.text(56, 344, "探针：在 vTaskStartScheduler 之前停一次，逐个看三个 xTaskCreate 的返回值",
                size=13, fill=T.MUTED)

    canvas.text(40, 386, "岔口二  一调 printf 就 HardFault：栈的单位是字", size=16, fill=T.AMBER, weight="700")
    canvas.text(920, 386, "xTaskCreate depth · 4 B/word", size=11, fill=T.MUTED, anchor="end", mono=True)
    canvas.rect(40, 400, 880, 174, fill=T.PANEL, stroke=T.AMBER, rx=8)
    canvas.text(56, 430, "症状：某个任务一打印就 HardFault，或者别的任务的变量、任务名莫名变了",
                size=14, fill=T.TEXT)
    canvas.text(56, 456, "原因 A：把 128 当成字节。xTaskCreate 的深度单位是字，一字 4 字节，128 字 = 512 字节",
                size=14, fill=T.TEXT)
    canvas.text(56, 482, "同一处错算：KEY 192 字才是 768 字节，UART 256 字才是 1024 字节；按字节只给了四分之一",
                size=14, fill=T.TEXT)
    canvas.text(56, 508, "原因 B：函数里的局部大数组吃栈，改成 static 或全局，把栈留给调用链和中断嵌套",
                size=14, fill=T.TEXT)
    canvas.text(56, 534, "检查点：configCHECK_FOR_STACK_OVERFLOW=2，实现 vApplicationStackOverflowHook 停住看任务名",
                size=14, fill=T.TEXT)
    canvas.text(56, 560, "探针：uxTaskGetStackHighWaterMark 读剩余字数，接近 0 就把栈加大",
                size=13, fill=T.MUTED)

    canvas.text(40, 612, "岔口三  优先级异常：方向反了，或者数值进了禁区", size=16, fill=T.VIOLET, weight="700")
    canvas.text(920, 612, "0x50 = 5 << (8 − 4) · mutex inheritance", size=11, fill=T.MUTED,
                anchor="end", mono=True)
    canvas.rect(40, 626, 880, 164, fill=T.PANEL, stroke=T.VIOLET, rx=8)
    canvas.text(56, 654, "症状 A：优先级 1 的任务压过优先级 2。任务优先级数值大的先跑，方向正好和 NVIC 相反",
                size=14, fill=T.TEXT)
    canvas.text(56, 680, "症状 B：一进中断就停在 configASSERT。抢占优先级数值太小，0 到 4 的中断不许调 FromISR",
                size=14, fill=T.TEXT)
    canvas.text(56, 706, "数值：0x50 = 5 << (8 − 4)，所以 EXTI0 的抢占优先级写 5，数值 5 及以后才由内核屏蔽",
                size=14, fill=T.TEXT)
    canvas.text(56, 732, "症状 C：高优先级被中优先级拖住，这是优先级反转。二值信号量没有继承，改用互斥量",
                size=14, fill=T.TEXT)
    canvas.text(56, 758, "探针：GPIO 翻转量高优先级任务的最长等待，二值信号量与 xSemaphoreCreateMutex() 各测一次",
                size=13, fill=T.MUTED)

    canvas.rect(40, 796, 880, 40, fill=T.BG2, stroke=T.GREEN, rx=8)
    canvas.text(56, 812, "底注  节拍 1000 Hz 就是 1 ms，内核只按 tick 记时间，更短的期限它保证不了。",
                size=12, fill=T.TEXT)
    canvas.text(56, 828, "先干 3 ms 活再 vTaskDelay(10)，周期约 13 ms；要固定 10 ms 周期用 vTaskDelayUntil。",
                size=12, fill=T.TEXT)

    _credit(canvas, "自绘。优先级、FromISR 与堆语义来自 FreeRTOS Kernel V11.3.2；栈、TIM4 与任务优先级来自本仓库 freertos-task。")
    return canvas


FIGURES = [
    ("sample-15-rtos-triage.svg", rtos_triage),
]

T_COLORS = {
    value
    for name in dir(T)
    if name.isupper() and isinstance(value := getattr(T, name), str) and value.startswith("#")
}
TEXT_RE = re.compile(r"<text\b[^>]*>(.*?)</text>", flags=re.DOTALL)


def _audit(name: str, path: str) -> str:
    raw = open(path, "rb").read()
    text = raw.decode("utf-8")
    width, height = (int(part) for part in re.search(r'\bwidth="(\d+)" height="(\d+)"', text).groups())
    strokes = set(re.findall(r'stroke-width="([^"]+)"', text))
    radii = set(re.findall(r'\brx="([^"]+)"', text))
    colors = {item.lower() for item in re.findall(r"#(?:[0-9A-Fa-f]{6})(?![0-9A-Fa-f])", text)}
    digest = hashlib.sha256("\n".join(TEXT_RE.findall(text)).encode("utf-8")).hexdigest()

    assert width == 960, (name, "width", width)
    assert height == 880, (name, "height", height)
    assert strokes <= {"1", "1.5", "2"}, (name, "stroke-width", sorted(strokes))
    assert radii <= {"2", "4", "8"}, (name, "rx", sorted(radii))
    assert colors <= T_COLORS, (name, "colors", sorted(colors - T_COLORS))
    assert "自绘" in text, (name, "credit")
    for banned in ("<animate", "@keyframes", "animation:", "矢量动画"):
        assert banned not in text, (name, "animation", banned)
    assert len(raw) < 60 * 1024, (name, "bytes", len(raw))
    print(f"{name}  {width}x{height}  {len(raw)} bytes  text_hash={digest}")
    return digest


def main(argv: list[str] | None = None) -> None:
    args = sys.argv[1:] if argv is None else argv
    out_dir = args[0] if args else os.path.join("assets", "diagrams")
    os.makedirs(out_dir, exist_ok=True)
    for name, make in FIGURES:
        path = make().save(os.path.join(out_dir, name))
        _audit(name, path)


if __name__ == "__main__":
    main()
