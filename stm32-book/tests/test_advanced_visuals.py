from __future__ import annotations

import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


CHAPTERS = {
    ROOT / "docs" / "00-如何学习STM32.md": (
        4,
        (
            "toolchain-flow.svg",
            "sample-00-boot-state.svg",
            "first-lab-wiring.svg",
            "first-success-gates.svg",
        ),
    ),
    ROOT / "docs" / "01-开发环境搭建.md": (
        5,
        (
            "boot-sequence.svg",
            "sample-01-swd-vectors.svg",
            "swd-fetch.gif",
            "single-build-contract.svg",
            "project-structure.svg",
        ),
    ),
    ROOT / "docs" / "03-GPIO与LED.md": (
        4,
        (
            "gpio-blink.svg",
            "sample-03-gpio-led.svg",
            "pinout-bluepill.svg",
            "led-blink.gif",
        ),
    ),
    ROOT / "docs" / "05-定时器与PWM.md": (
        5,
        (
            "timer-pwm.svg",
            "sample-05-pwm-1khz.svg",
            "pwm-1khz.gif",
            "timer-modes.svg",
            "pwm-breath.gif",
        ),
    ),
    ROOT / "docs" / "09-ADC与DAC.md": (
        5,
        (
            "adc-sar.svg",
            "sample-09-adc-sar.svg",
            "adc-sample.gif",
            "sar-adc.gif",
            "dma-circular.svg",
        ),
    ),
    ROOT / "docs" / "10-DMA.md": (
        5,
        (
            "dma-circular.svg",
            "sample-10-dma-cndtr.svg",
            "dma-cndtr.gif",
            "dma-buffer-ownership.svg",
            "dma-ring.gif",
        ),
    ),
    ROOT / "docs" / "11-RTC与看门狗.md": (
        4,
        (
            "iwdg-window.svg",
            "sample-11-iwdg-1s.svg",
            "iwdg-1s.gif",
            "watchdog-reset-evidence.svg",
        ),
    ),
    ROOT / "docs" / "12-Flash与IAP升级.md": (
        4,
        (
            "flash-iap.svg",
            "sample-12-iap-map.svg",
            "iap-jump.gif",
            "iap-acceptance-gates.svg",
        ),
    ),
    ROOT / "docs" / "14-USB.md": (
        6,
        (
            "usb-enumeration.svg",
            "sample-14-usb-enum.svg",
            "usb-48m.gif",
            "usb-enumeration-zh.gif",
            "pinout-bluepill.svg",
            "instrument-evidence-ladder.svg",
        ),
    ),
    ROOT / "docs" / "15-FreeRTOS入门.md": (
        6,
        (
            "freertos-scheduler.svg",
            "sample-15-rtos-prio.svg",
            "rtos-tick.gif",
            "rtos-deadline-budget.svg",
            "rtos-owner-task.svg",
            "rtos-startup-gates.svg",
        ),
    ),
    ROOT / "docs" / "16-低功耗设计.md": (
        4,
        (
            "lowpower-wakeup.svg",
            "sample-16-stop-wake.svg",
            "stop-wake.gif",
            "lowpower-current-evidence.svg",
        ),
    ),
    ROOT / "docs" / "17-调试与性能优化.md": (
        4,
        (
            "debug-swo.svg",
            "sample-17-cfsr.svg",
            "cfsr-read.gif",
            "fault-triage-ladder.svg",
        ),
    ),
    ROOT / "docs" / "20-学习资源与工具链.md": (
        5,
        (
            "project-structure.svg",
            "manual-choice-map.svg",
            "firmware-stack-choice.svg",
            "instrument-evidence-ladder.svg",
            "single-build-contract.svg",
        ),
    ),
    ROOT / "docs" / "22-仿真实验Wokwi与Renode.md": (
        4,
        (
            "toolchain-flow.svg",
            "simulator-comparison.svg",
            "simulation-model-boundary.svg",
            "simulation-acceptance-gates.svg",
        ),
    ),
    ROOT / "docs" / "25-STM32H7引脚.md": (
        7,
        (
            "pinout-stm32h743zi-lqfp144.svg",
            "h7-power-domains.svg",
            "h7-revision-clock-decision.svg",
            "h7-clock-chain.svg",
            "h7-startup-evidence.svg",
            "h7-pinmux-conflicts.svg",
            "network-cache-ownership.svg",
        ),
    ),
    ROOT / "docs" / "26-STM32F10x标准外设库SPL.md": (
        5,
        (
            "spl-ownership-boundary.svg",
            "spl-init-pipeline.svg",
            "bluepill-stm32f103c8t6.svg",
            "nvic-interrupt-flow.svg",
            "dma-circular.svg",
        ),
    ),
    ROOT / "docs" / "27-网络与协议栈.md": (
        5,
        (
            "network-packet-journey.svg",
            "network-cache-ownership.svg",
            "network-online-state.svg",
            "tcp-byte-stream.svg",
            "network-debug-ladder.svg",
        ),
    ),
    ROOT / "docs" / "28-嵌入式系统与RTOS生态.md": (
        8,
        (
            "rtos-system-layers.svg",
            "nucleo-f411re-embedded-world.jpg",
            "nucleo-f401re-embedded-world.jpg",
            "rtos-owner-task.svg",
            "rtos-deadline-budget.svg",
            "freertos-scheduler.svg",
            "rtos-config-paths.svg",
            "rtos-startup-gates.svg",
        ),
    ),
}


class AdvancedVisualTests(unittest.TestCase):
    def test_visual_anchors_are_present_and_distributed(self) -> None:
        for path, (count, assets) in CHAPTERS.items():
            text = path.read_text(encoding="utf-8")
            positions = [match.start() for match in re.finditer(r"<img\b", text)]
            self.assertEqual(count, len(positions), path.name)
            for asset in assets:
                refs = re.findall(r'<img\b[^>]*src="([^"]+)"', text)
                self.assertEqual(1, sum(Path(ref).name == asset for ref in refs),
                                 (path.name, asset))

            points = [0, *positions, len(text)]
            largest_gap = max(right - left for left, right in zip(points, points[1:]))
            self.assertLessEqual(largest_gap, 5500, (path.name, largest_gap))

    def test_english_chapters_keep_the_same_visual_sequence(self) -> None:
        pairs = (
            ("00-如何学习STM32.md", "00-how-to-learn-stm32.md"),
            ("01-开发环境搭建.md", "01-dev-environment.md"),
            ("03-GPIO与LED.md", "03-gpio-and-led.md"),
            ("05-定时器与PWM.md", "05-timer-pwm.md"),
            ("09-ADC与DAC.md", "09-adc-dac.md"),
            ("10-DMA.md", "10-dma.md"),
            ("11-RTC与看门狗.md", "11-rtc-watchdog.md"),
            ("12-Flash与IAP升级.md", "12-flash-iap.md"),
            ("14-USB.md", "14-usb.md"),
            ("15-FreeRTOS入门.md", "15-freertos.md"),
            ("16-低功耗设计.md", "16-low-power.md"),
            ("17-调试与性能优化.md", "17-debug.md"),
            ("20-学习资源与工具链.md", "20-resources.md"),
            ("22-仿真实验Wokwi与Renode.md", "22-simulation-wokwi-renode.md"),
            ("25-STM32H7引脚.md", "25-stm32h7-pins.md"),
            ("26-STM32F10x标准外设库SPL.md", "26-spl.md"),
            ("27-网络与协议栈.md", "27-network.md"),
            ("28-嵌入式系统与RTOS生态.md", "28-system-rtos.md"),
        )
        for zh_name, en_name in pairs:
            zh = (ROOT / "docs" / zh_name).read_text(encoding="utf-8")
            en = (ROOT / "docs" / "en" / en_name).read_text(encoding="utf-8")
            zh_assets = [Path(item).name for item in re.findall(r'<img\b[^>]*src="([^"]+)"', zh)]
            en_assets = [Path(item).name for item in re.findall(r'<img\b[^>]*src="([^"]+)"', en)]
            self.assertEqual(zh_assets, en_assets, zh_name)

    def test_new_svg_assets_are_valid_and_use_recorded_handdraw_ids(self) -> None:
        animated = (
            "simulation-acceptance-gates.svg",
            "h7-clock-chain.svg",
            "spl-init-pipeline.svg",
            "network-online-state.svg",
            "rtos-startup-gates.svg",
        )
        static = (
            "first-lab-wiring.svg",
            "first-success-gates.svg",
            "dma-buffer-ownership.svg",
            "fault-triage-ladder.svg",
            "watchdog-reset-evidence.svg",
            "iap-acceptance-gates.svg",
            "lowpower-current-evidence.svg",
            "manual-choice-map.svg",
            "firmware-stack-choice.svg",
            "instrument-evidence-ladder.svg",
            "single-build-contract.svg",
            "simulator-comparison.svg",
            "simulation-model-boundary.svg",
            "h7-power-domains.svg",
            "h7-revision-clock-decision.svg",
            "h7-startup-evidence.svg",
            "h7-pinmux-conflicts.svg",
            "spl-ownership-boundary.svg",
            "network-cache-ownership.svg",
            "tcp-byte-stream.svg",
            "rtos-owner-task.svg",
            "rtos-deadline-budget.svg",
            "rtos-config-paths.svg",
        )
        for name in animated:
            path = ROOT / "assets" / "animations" / name
            ET.parse(path)
            text = path.read_text(encoding="utf-8")
            self.assertIn("animation:", text, name)
            self.assertIn("prefers-reduced-motion", text, name)
            self.assertIn("FA-002", text, name)

        for name in static:
            path = ROOT / "assets" / "diagrams" / name
            ET.parse(path)
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("animation:", text, name)
            self.assertIn("自绘矢量图", text, name)
            self.assertRegex(text, r"FA-(?:002|029)")

        readme = (ROOT / "assets" / "README.md").read_text(encoding="utf-8")
        for token in (
            "FA-002",
            "FA-029",
            "IG-002",
            "IG-004",
            "IG-008",
            "IG-009",
            "IG-010",
            "IG-011",
            "IG-012",
            "C-03",
            "C-10",
            "C-27",
            "C-31",
        ):
            self.assertIn(token, readme)

    def test_photo_spread_is_honest_about_exact_models(self) -> None:
        for path in (
            ROOT / "docs" / "28-嵌入式系统与RTOS生态.md",
            ROOT / "docs" / "en" / "28-system-rtos.md",
        ):
            text = path.read_text(encoding="utf-8")
            self.assertIn('class="photo-pair"', text)
            self.assertIn("Nucleo-F411RE", text)
            self.assertIn("Nucleo-F401RE", text)
            self.assertIn("assets/photos/README.md", text)
