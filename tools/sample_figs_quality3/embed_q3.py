#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Embed ch11–17 quality figures into zh+en chapters."""

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
    # ---- ch11 ----
    {
        "zh": ROOT / "docs" / "11-RTC与看门狗.md",
        "en": ROOT / "docs" / "en" / "11-rtc-watchdog.md",
        "marker_zh": "### 1. RTC 与备份域",
        "marker_en": "### 1. The RTC and the backup domain",
        "needle": "sample-11-backup-domain.svg",
        "src_zh": "../assets/diagrams/sample-11-backup-domain.svg",
        "src_en": "../../assets/diagrams/sample-11-backup-domain.svg",
        "width": 760,
        "alt_zh": "备份域：VBAT 续电，LSE 32.768 kHz 走时",
        "alt_en": "Backup domain: VBAT keeps RTC; LSE 32.768 kHz",
        "cap_zh": "▲ 自绘。VBAT 续电备份域；LSE 最准，LSI 仅作备用。",
        "cap_en": "▲ Drawn for this book. VBAT keeps the backup domain; LSE is preferred over LSI.",
    },
    {
        "zh": ROOT / "docs" / "11-RTC与看门狗.md",
        "en": ROOT / "docs" / "en" / "11-rtc-watchdog.md",
        "marker_zh": "### 4. IWDG 与 WWDG 对比",
        "marker_en": "### 4. IWDG vs WWDG",
        "needle": "sample-11-iwdg-math.svg",
        "src_zh": "../assets/diagrams/sample-11-iwdg-math.svg",
        "src_en": "../../assets/diagrams/sample-11-iwdg-math.svg",
        "width": 760,
        "alt_zh": "IWDG 一秒公式：40 kHz / 64 = 625 Hz，Reload 624",
        "alt_en": "IWDG 1 s math: 40 kHz / 64 = 625 Hz, Reload 624",
        "cap_zh": "▲ 自绘。超时用 (Reload+1)；写成 625 会多一拍。",
        "cap_en": "▲ Drawn for this book. Timeout uses (Reload+1); 625 is one tick too many.",
    },
    {
        "zh": ROOT / "docs" / "11-RTC与看门狗.md",
        "en": ROOT / "docs" / "en" / "11-rtc-watchdog.md",
        "marker_zh": "## 关键插图",
        "marker_en": "## Key figures",
        "needle": "sample-11-iwdg-feed-flow.svg",
        "src_zh": "../assets/animations/sample-11-iwdg-feed-flow.svg",
        "src_en": "../../assets/animations/sample-11-iwdg-feed-flow.svg",
        "width": 720,
        "alt_zh": "IWDG：625 Hz 倒数，到 0 前喂狗",
        "alt_en": "IWDG: 625 Hz countdown, feed before zero",
        "cap_zh": "▲ 自绘矢量动画（FA-002）。LSI→625 Hz→倒数→喂狗。",
        "cap_en": "▲ Hand-drawn CSS animation (FA-002). LSI→625 Hz→count→feed.",
    },
    # ---- ch12 ----
    {
        "zh": ROOT / "docs" / "12-Flash与IAP升级.md",
        "en": ROOT / "docs" / "en" / "12-flash-iap.md",
        "marker_zh": "### 1. Flash 组织结构",
        "marker_en": "### 1. How Flash is organized",
        "needle": "sample-12-page-erase.svg",
        "src_zh": "../assets/diagrams/sample-12-page-erase.svg",
        "src_en": "../../assets/diagrams/sample-12-page-erase.svg",
        "width": 760,
        "alt_zh": "F103C8 按 1 KB 页擦除；APP 从 0x08004800 起",
        "alt_en": "F103C8 erases 1 KB pages; APP starts at 0x08004800",
        "cap_zh": "▲ 自绘。中容量 1 KB/页；C8 末页是 0x0800FC00。",
        "cap_en": "▲ Drawn for this book. Medium-density 1 KB pages; C8 last page is 0x0800FC00.",
    },
    {
        "zh": ROOT / "docs" / "12-Flash与IAP升级.md",
        "en": ROOT / "docs" / "en" / "12-flash-iap.md",
        "marker_zh": "### 2. 解锁与编程流程",
        "marker_en": "### 2. Unlock and the programming sequence",
        "needle": "sample-12-key-order.svg",
        "src_zh": "../assets/diagrams/sample-12-key-order.svg",
        "src_en": "../../assets/diagrams/sample-12-key-order.svg",
        "width": 760,
        "alt_zh": "FLASH 解锁：先 0x45670123 再 0xCDEF89AB",
        "alt_en": "FLASH unlock: KEY1 0x45670123 then KEY2 0xCDEF89AB",
        "cap_zh": "▲ 自绘。钥匙顺序反了锁打不开；跳转要装 MSP 与复位向量。",
        "cap_en": "▲ Drawn for this book. Reversed keys leave LOCK set; jump needs MSP and Reset_Handler.",
    },
    {
        "zh": ROOT / "docs" / "12-Flash与IAP升级.md",
        "en": ROOT / "docs" / "en" / "12-flash-iap.md",
        "marker_zh": "## 关键插图",
        "marker_en": "## Key figures",
        "needle": "sample-12-iap-jump-flow.svg",
        "src_zh": "../assets/animations/sample-12-iap-jump-flow.svg",
        "src_en": "../../assets/animations/sample-12-iap-jump-flow.svg",
        "width": 720,
        "alt_zh": "IAP：按序解锁再装 MSP 与复位向量",
        "alt_en": "IAP: unlock in order, then load MSP and Reset_Handler",
        "cap_zh": "▲ 自绘矢量动画（FA-002）。KEY1→KEY2→半字→向量→VTOR。",
        "cap_en": "▲ Hand-drawn CSS animation (FA-002). KEY1→KEY2→half-word→vectors→VTOR.",
    },
    # ---- ch13 ----
    {
        "zh": ROOT / "docs" / "13-CAN总线.md",
        "en": ROOT / "docs" / "en" / "13-can.md",
        "marker_zh": "### 5. 波特率与采样点",
        "marker_en": "### 5. Baud rate and sample point",
        "needle": "sample-13-bit-quanta.svg",
        "src_zh": "../assets/diagrams/sample-13-bit-quanta.svg",
        "src_en": "../../assets/diagrams/sample-13-bit-quanta.svg",
        "width": 760,
        "alt_zh": "36 MHz 下预分频 9、8 个 250 ns 份额是 500 kbit/s",
        "alt_en": "Prescaler 9 at 36 MHz: eight 250 ns quanta = 500 kbit/s",
        "cap_zh": "▲ 自绘。采样点 75%；预分频写错会变成 450 kbit/s。",
        "cap_en": "▲ Drawn for this book. Sample at 75%; wrong prescaler yields 450 kbit/s.",
    },
    {
        "zh": ROOT / "docs" / "13-CAN总线.md",
        "en": ROOT / "docs" / "en" / "13-can.md",
        "marker_zh": "### 6. 过滤器与双 FIFO（F1）",
        "marker_en": "### 6. Filters and two FIFOs (F1)",
        "needle": "sample-13-filter-fifo.svg",
        "src_zh": "../assets/diagrams/sample-13-filter-fifo.svg",
        "src_en": "../../assets/diagrams/sample-13-filter-fifo.svg",
        "width": 760,
        "alt_zh": "F1：14 个过滤组和 FIFO0/FIFO1",
        "alt_en": "F1: 14 filter banks and FIFO0/FIFO1",
        "cap_zh": "▲ 自绘。硬实时进 FIFO0，批量进 FIFO1；溢出要提速排空。",
        "cap_en": "▲ Drawn for this book. Hard-realtime → FIFO0; bulk → FIFO1; fix overrun by draining faster.",
    },
    {
        "zh": ROOT / "docs" / "13-CAN总线.md",
        "en": ROOT / "docs" / "en" / "13-can.md",
        "marker_zh": "### 7. 总线关闭之后怎么回来",
        "marker_en": "### 7. Coming back from bus-off",
        "needle": "sample-13-tec-busoff.svg",
        "src_zh": "../assets/diagrams/sample-13-tec-busoff.svg",
        "src_en": "../../assets/diagrams/sample-13-tec-busoff.svg",
        "width": 760,
        "alt_zh": "TEC 128 进被动；超过 255 才 Bus-Off",
        "alt_en": "TEC 128 = error-passive; TEC > 255 = bus-off",
        "cap_zh": "▲ 自绘。单节点无 ACK 只到 128；Bus-Off 要另造发送错误。",
        "cap_en": "▲ Drawn for this book. Lone node without ACK stops at 128; bus-off needs real Tx errors.",
    },
    {
        "zh": ROOT / "docs" / "13-CAN总线.md",
        "en": ROOT / "docs" / "en" / "13-can.md",
        "marker_zh": "## 关键插图",
        "marker_en": "## Key figures",
        "needle": "sample-13-can-arb-flow.svg",
        "src_zh": "../assets/animations/sample-13-can-arb-flow.svg",
        "src_en": "../../assets/animations/sample-13-can-arb-flow.svg",
        "width": 720,
        "alt_zh": "CAN：8 个 250 ns 时间份额走到采样点",
        "alt_en": "CAN: eight 250 ns quanta walk to the sample point",
        "cap_zh": "▲ 自绘矢量动画（FA-002）。Sync→BS1→75% 采样→BS2→2 µs。",
        "cap_en": "▲ Hand-drawn CSS animation (FA-002). Sync→BS1→75% sample→BS2→2 µs.",
    },
    # ---- ch14 ----
    {
        "zh": ROOT / "docs" / "14-USB.md",
        "en": ROOT / "docs" / "en" / "14-usb.md",
        "marker_zh": "### 1. USB 速率与 STM32 外设",
        "marker_en": "### 1. Speeds and which STM32 block you actually have",
        "needle": "sample-14-usbpre-48.svg",
        "src_zh": "../assets/diagrams/sample-14-usbpre-48.svg",
        "src_en": "../../assets/diagrams/sample-14-usbpre-48.svg",
        "width": 760,
        "alt_zh": "USBPRE=0 时 72/1.5=48 MHz；D+ 上拉标识全速",
        "alt_en": "USBPRE=0 => 72/1.5=48 MHz; D+ pull-up marks full-speed",
        "cap_zh": "▲ 自绘。全速硬性 48 MHz；USBPRE=1 会枚举失败。",
        "cap_en": "▲ Drawn for this book. FS needs 48 MHz; USBPRE=1 breaks enumeration.",
    },
    {
        "zh": ROOT / "docs" / "14-USB.md",
        "en": ROOT / "docs" / "en" / "14-usb.md",
        "marker_zh": "### 3. 端点 Endpoint",
        "marker_en": "### 3. Endpoints",
        "needle": "sample-14-pma-map.svg",
        "src_zh": "../assets/diagrams/sample-14-pma-map.svg",
        "src_en": "../../assets/diagrams/sample-14-pma-map.svg",
        "width": 760,
        "alt_zh": "F1 USB：8 个端点共享 512 字节 PMA",
        "alt_en": "F1 USB: eight endpoints share a 512-byte PMA",
        "cap_zh": "▲ 自绘。IN/OUT 站在主机侧；PMA 重叠会毁掉包。",
        "cap_en": "▲ Drawn for this book. IN/OUT are host-named; overlapping PMA corrupts packets.",
    },
    {
        "zh": ROOT / "docs" / "14-USB.md",
        "en": ROOT / "docs" / "en" / "14-usb.md",
        "marker_zh": "## 关键插图",
        "marker_en": "## Key figures",
        "needle": "sample-14-usb-48m-flow.svg",
        "src_zh": "../assets/animations/sample-14-usb-48m-flow.svg",
        "src_en": "../../assets/animations/sample-14-usb-48m-flow.svg",
        "width": 720,
        "alt_zh": "USB：D+ 上拉 → 48 MHz → 18/67 字节",
        "alt_en": "USB: D+ pull-up → 48 MHz → 18/67 bytes",
        "cap_zh": "▲ 自绘矢量动画（FA-002）。上拉→主机看见→USBPRE→描述符。",
        "cap_en": "▲ Hand-drawn CSS animation (FA-002). Pull-up→host sees FS→USBPRE→descriptors.",
    },
    # ---- ch15 ----
    {
        "zh": ROOT / "docs" / "15-FreeRTOS入门.md",
        "en": ROOT / "docs" / "en" / "15-freertos.md",
        "marker_zh": "### 2. 任务状态迁移",
        "marker_en": "### 2. Task state transitions",
        "needle": "sample-15-task-states.svg",
        "src_zh": "../assets/diagrams/sample-15-task-states.svg",
        "src_en": "../../assets/diagrams/sample-15-task-states.svg",
        "width": 760,
        "alt_zh": "FreeRTOS 四态：Running / Ready / Blocked / Suspended",
        "alt_en": "FreeRTOS states: Running / Ready / Blocked / Suspended",
        "cap_zh": "▲ 自绘。1 ms 节拍；128 字=512 字节；别和 HAL 抢 SysTick。",
        "cap_en": "▲ Drawn for this book. 1 ms tick; 128 words=512 bytes; do not share SysTick with HAL.",
    },
    {
        "zh": ROOT / "docs" / "15-FreeRTOS入门.md",
        "en": ROOT / "docs" / "en" / "15-freertos.md",
        "marker_zh": "### 10. 中断里只能用 FromISR API",
        "marker_en": "### 10. In an interrupt you may only call FromISR APIs",
        "needle": "sample-15-fromisr.svg",
        "src_zh": "../assets/diagrams/sample-15-fromisr.svg",
        "src_en": "../../assets/diagrams/sample-15-fromisr.svg",
        "width": 760,
        "alt_zh": "ISR 里只能用 FromISR；抢占优先级数值至少 5",
        "alt_en": "ISR may only call FromISR; preempt priority numeric ≥ 5",
        "cap_zh": "▲ 自绘。队列/信号量任务版 API 禁止进中断。",
        "cap_en": "▲ Drawn for this book. Task-context queue/sem APIs are banned inside ISRs.",
    },
    {
        "zh": ROOT / "docs" / "15-FreeRTOS入门.md",
        "en": ROOT / "docs" / "en" / "15-freertos.md",
        "marker_zh": "## 关键插图",
        "marker_en": "## Key figures",
        "needle": "sample-15-rtos-tick-flow.svg",
        "src_zh": "../assets/animations/sample-15-rtos-tick-flow.svg",
        "src_en": "../../assets/animations/sample-15-rtos-tick-flow.svg",
        "width": 720,
        "alt_zh": "RTOS：1 ms 节拍，优先级 2 先跑",
        "alt_en": "RTOS: 1 ms tick, priority 2 runs first",
        "cap_zh": "▲ 自绘矢量动画（FA-002）。节拍→就绪→prio2→128 字。",
        "cap_en": "▲ Hand-drawn CSS animation (FA-002). Tick→ready→prio2→128 words.",
    },
    # ---- ch16 ----
    {
        "zh": ROOT / "docs" / "16-低功耗设计.md",
        "en": ROOT / "docs" / "en" / "16-low-power.md",
        "marker_zh": "### 1. 三种低功耗模式对比",
        "marker_en": "### 1. The three low-power modes compared",
        "needle": "sample-16-mode-current.svg",
        "src_zh": "../assets/diagrams/sample-16-mode-current.svg",
        "src_en": "../../assets/diagrams/sample-16-mode-current.svg",
        "width": 760,
        "alt_zh": "Sleep 毫安；Stop 14 µA；Standby 2 µA（条件写清）",
        "alt_en": "Sleep in mA; Stop 14 µA; Standby 2 µA (conditions named)",
        "cap_zh": "▲ 自绘。勿把 14/24 µA 并成 20；1.4 µA 是备份域不是整机。",
        "cap_en": "▲ Drawn for this book. Do not merge 14/24 µA into 20; 1.4 µA is VBAT domain only.",
    },
    {
        "zh": ROOT / "docs" / "16-低功耗设计.md",
        "en": ROOT / "docs" / "en" / "16-low-power.md",
        "marker_zh": "### 3. STOP 唤醒后时钟恢复",
        "marker_en": "### 3. Restoring the clock after STOP wakes",
        "needle": "sample-16-clock-restore.svg",
        "src_zh": "../assets/diagrams/sample-16-clock-restore.svg",
        "src_en": "../../assets/diagrams/sample-16-clock-restore.svg",
        "width": 760,
        "alt_zh": "Stop 醒来先是 HSI 8 MHz，再装回 72 MHz 才是 115200",
        "alt_en": "After Stop: HSI 8 MHz first, then PLL 72 MHz before 115200",
        "cap_zh": "▲ 自绘。不重配时钟时 0x271 在 8 MHz 下是 12800。",
        "cap_en": "▲ Drawn for this book. Without restore, BRR 0x271 at 8 MHz is 12800 bit/s.",
    },
    {
        "zh": ROOT / "docs" / "16-低功耗设计.md",
        "en": ROOT / "docs" / "en" / "16-low-power.md",
        "marker_zh": "## 关键插图",
        "marker_en": "## Key figures",
        "needle": "sample-16-stop-wake-flow.svg",
        "src_zh": "../assets/animations/sample-16-stop-wake-flow.svg",
        "src_en": "../../assets/animations/sample-16-stop-wake-flow.svg",
        "width": 720,
        "alt_zh": "Stop 唤醒：HSI 8 MHz 装回 72 MHz 再开串口",
        "alt_en": "Stop wake: HSI 8 MHz → PLL 72 MHz → UART 115200",
        "cap_zh": "▲ 自绘矢量动画（FA-002）。Stop→唤醒→HSI→PLL→115200。",
        "cap_en": "▲ Hand-drawn CSS animation (FA-002). Stop→wake→HSI→PLL→115200.",
    },
    # ---- ch17 ----
    {
        "zh": ROOT / "docs" / "17-调试与性能优化.md",
        "en": ROOT / "docs" / "en" / "17-debug.md",
        "marker_zh": "### 1. SWD vs JTAG",
        "marker_en": "### 1. SWD vs JTAG",
        "needle": "sample-17-swd-pins.svg",
        "src_zh": "../assets/diagrams/sample-17-swd-pins.svg",
        "src_en": "../../assets/diagrams/sample-17-swd-pins.svg",
        "width": 760,
        "alt_zh": "SWD：PA13/PA14/NRST；SWO 占 PB3",
        "alt_en": "SWD: PA13/PA14/NRST; SWO uses PB3",
        "cap_zh": "▲ 自绘。M3 硬件断点 6 个；SWD 脚改成 GPIO 会丢调试口。",
        "cap_en": "▲ Drawn for this book. M3 has 6 HW breakpoints; reclaiming SWD pins bricks debug.",
    },
    {
        "zh": ROOT / "docs" / "17-调试与性能优化.md",
        "en": ROOT / "docs" / "en" / "17-debug.md",
        "marker_zh": "### 4. HardFault 定位三件套",
        "marker_en": "### 4. The three-piece HardFault kit",
        "needle": "sample-17-cfsr-bits.svg",
        "src_zh": "../assets/diagrams/sample-17-cfsr-bits.svg",
        "src_en": "../../assets/diagrams/sample-17-cfsr-bits.svg",
        "width": 760,
        "alt_zh": "CFSR @ 0xE000ED28；bit 15=1 才采信 BFAR",
        "alt_en": "CFSR @ 0xE000ED28; trust BFAR only when bit 15 = 1",
        "cap_zh": "▲ 自绘。先 CFSR 再 HFSR/BFAR；72 拍@72 MHz 是 1 µs。",
        "cap_en": "▲ Drawn for this book. CFSR first; 72 counts at 72 MHz = 1 µs.",
    },
    {
        "zh": ROOT / "docs" / "17-调试与性能优化.md",
        "en": ROOT / "docs" / "en" / "17-debug.md",
        "marker_zh": "## 关键插图",
        "marker_en": "## Key figures",
        "needle": "sample-17-cfsr-flow.svg",
        "src_zh": "../assets/animations/sample-17-cfsr-flow.svg",
        "src_en": "../../assets/animations/sample-17-cfsr-flow.svg",
        "width": 720,
        "alt_zh": "CFSR：bit 15=1 才采信 BFAR，再数 72 拍",
        "alt_en": "CFSR: bit 15=1 unlocks BFAR; then 72 counts",
        "cap_zh": "▲ 自绘矢量动画（FA-002）。Fault→CFSR→bit15→BFAR→1 µs。",
        "cap_en": "▲ Hand-drawn CSS animation (FA-002). Fault→CFSR→bit15→BFAR→1 µs.",
    },
]


def main() -> None:
    n = 0
    for item in EMBEDS:
        block_zh = _blk(item["src_zh"], item["width"], item["alt_zh"], item["cap_zh"])
        block_en = _blk(item["src_en"], item["width"], item["alt_en"], item["cap_en"])
        if _insert_after_heading(item["zh"], item["marker_zh"], item["needle"], block_zh):
            n += 1
        if _insert_after_heading(item["en"], item["marker_en"], item["needle"], block_en):
            n += 1
    print(f"embed ops applied: {n} / {len(EMBEDS)*2}")


if __name__ == "__main__":
    main()
