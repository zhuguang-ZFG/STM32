from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AUDIT_PATH = ROOT / "tools" / "audit_book.py"


def load_auditor():
    spec = importlib.util.spec_from_file_location("book_auditor", AUDIT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load auditor: {AUDIT_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


audit_book = load_auditor()


class BookAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = audit_book.build_audit()
        cls.by_id = {item["id"]: item for item in cls.payload["chapters"]}

    def test_audit_covers_both_editions(self) -> None:
        self.assertEqual(29, self.payload["chapter_count"])
        self.assertEqual({f"{number:02d}" for number in range(29)}, set(self.by_id))
        for item in self.payload["chapters"]:
            self.assertTrue(item["zh"]["file"].startswith("docs/"))
            self.assertTrue(item["en"]["file"].startswith("docs/en/"))

    def test_video_is_not_counted_as_a_pdf_visual(self) -> None:
        chapter = self.by_id["20"]["zh"]
        self.assertEqual(1, chapter["videos"])
        self.assertGreaterEqual(chapter["visual_assets"], chapter["pdf_visual_anchors"])

    def test_grouped_photos_are_one_reading_position(self) -> None:
        chapter = self.by_id["28"]["zh"]
        self.assertEqual(2, chapter["photos"])
        self.assertEqual(chapter["pdf_visual_anchors"] + 1, chapter["visual_assets"])

    def test_all_chapters_have_a_pdf_anchor_and_a_gap_measurement(self) -> None:
        for item in self.payload["chapters"]:
            for language in ("zh", "en"):
                chapter = item[language]
                self.assertGreaterEqual(chapter["pdf_visual_anchors"], 1, (item["id"], language))
                self.assertGreater(chapter["max_visual_gap_chars"], 0, (item["id"], language))
                self.assertGreaterEqual(chapter["target_visual_anchors"], 3)
            self.assertEqual(item["zh"]["target_visual_anchors"], item["en"]["target_visual_anchors"])

    def test_bilingual_visual_sequence_matches_repaired_chapters(self) -> None:
        for item in self.payload["chapters"]:
            self.assertIsInstance(item["parity"]["asset_sequence_equal"], bool)
        for chapter_id in ("01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28"):
            self.assertTrue(self.by_id[chapter_id]["parity"]["asset_sequence_equal"])

    def test_project_chapter_distributes_delivery_evidence(self) -> None:
        chapter = self.by_id["19"]
        assets = (
            "peripheral-wiring.svg",
            "sample-19-flash-fit.svg",
            "one-slot.gif",
            "dma-buffer-ownership.svg",
            "iap-acceptance-gates.svg",
            "network-debug-ladder.svg",
            "rtos-startup-gates.svg",
        )
        for language in ("zh", "en"):
            self.assertEqual(0, chapter[language]["visual_anchor_deficit"])
            self.assertEqual(assets, chapter[language]["asset_sequence"])
        for field in ("h2_delta", "h3_delta", "table_delta", "code_block_delta"):
            self.assertEqual(0, chapter["parity"][field])

    def test_first_hardware_loop_has_visual_and_structure_parity(self) -> None:
        chapter = self.by_id["01"]
        expected_assets = (
            "boot-sequence.svg",
            "sample-01-swd-vectors.svg",
            "swd-fetch.gif",
            "single-build-contract.svg",
            "sample-01-flash-path.svg",
            "project-structure.svg",
            "sample-01-flash-triage.svg",
            "sample-01-debug-connect.svg",
            "sample-01-build-accept.svg",
        )
        for language in ("zh", "en"):
            edition = chapter[language]
            self.assertEqual(9, edition["pdf_visual_anchors"])
            self.assertEqual(0, edition["visual_anchor_deficit"])
            self.assertEqual(expected_assets, edition["asset_sequence"])
        for field in ("h2_delta", "h3_delta", "table_delta", "code_block_delta"):
            self.assertEqual(0, chapter["parity"][field])

    def test_gpio_interrupt_timer_close_phase_one(self) -> None:
        expected = {
            "03": (
                "gpio-blink.svg",
                "ch03-handdraw.svg",
                "sample-03-gpio-led.svg",
                "bluepill-stm32f103c8t6.jpg",
                "stack-gpio-pc13-led.png",
                "pinout-bluepill.svg",
                "led-blink.gif",
            ),
            "04": (
                "nvic-interrupt-flow.svg",
                "sample-04-exception-stack.svg",
                "nvic-preempt.gif",
                "interrupt-priority.svg",
                "gpio-input-interrupt.svg",
                "sample-04-exti-triage.svg",
            ),
            "05": (
                "timer-pwm.svg",
                "sample-05-pwm-1khz.svg",
                "pwm-1khz.gif",
                "timer-modes.svg",
                "sample-05-pwm-debug.svg",
                "pwm-breath.gif",
            ),
        }
        for chapter_id, assets in expected.items():
            chapter = self.by_id[chapter_id]
            for language in ("zh", "en"):
                edition = chapter[language]
                self.assertEqual(0, edition["visual_anchor_deficit"])
                self.assertEqual(assets, edition["asset_sequence"])
            for field in ("h2_delta", "h3_delta", "table_delta", "code_block_delta"):
                self.assertEqual(0, chapter["parity"][field])

    def test_phase_two_reaches_memory_with_visual_parity(self) -> None:
        expected = {
            "06": (
                "uart-frame.svg",
                "sample-06-uart-frame.svg",
                "uart-idle.gif",
                "uart-bits.gif",
                "sample-06-baud-triage.svg",
                "sample-06-idle-dma.svg",
            ),
            "07": (
                "i2c-transaction.svg",
                "sample-07-i2c-addr.svg",
                "i2c-addr.gif",
                "i2c-timing.gif",
                "sample-07-i2c-triage.svg",
            ),
            "08": (
                "spi-transfer.svg",
                "sample-08-spi-jedec.svg",
                "spi-jedec.gif",
                "sample-08-cpha-modes.svg",
                "sample-08-spi-triage.svg",
            ),
            "09": (
                "adc-sar.svg",
                "sample-09-adc-sar.svg",
                "adc-sample.gif",
                "sar-adc.gif",
                "dma-circular.svg",
                "sample-09-adc-triage.svg",
            ),
            "10": (
                "dma-circular.svg",
                "sample-10-dma-cndtr.svg",
                "dma-cndtr.gif",
                "sample-10-dma-triage.svg",
                "dma-buffer-ownership.svg",
                "dma-ring.gif",
            ),
        }
        for chapter_id, assets in expected.items():
            chapter = self.by_id[chapter_id]
            for language in ("zh", "en"):
                edition = chapter[language]
                self.assertEqual(0, edition["visual_anchor_deficit"])
                self.assertEqual(assets, edition["asset_sequence"])
            for field in ("h2_delta", "h3_delta", "table_delta", "code_block_delta"):
                self.assertEqual(0, chapter["parity"][field])

    def test_reliability_phase_starts_with_reset_update_and_bus_evidence(self) -> None:
        expected = {
            "11": ("iwdg-window.svg", "sample-11-iwdg-1s.svg", "iwdg-1s.gif", "sample-11-wdg-compare.svg", "watchdog-reset-evidence.svg", "sample-11-rtc-triage.svg"),
            "12": ("flash-iap.svg", "sample-12-iap-map.svg", "iap-jump.gif", "sample-12-flash-triage.svg", "iap-acceptance-gates.svg", "sample-12-boot-compare.svg"),
            "13": ("can-arbitration.svg", "sample-13-can-bit.svg", "can-500k.gif", "sample-13-can-triage.svg"),
        }
        for chapter_id, assets in expected.items():
            chapter = self.by_id[chapter_id]
            for language in ("zh", "en"):
                edition = chapter[language]
                self.assertEqual(0, edition["visual_anchor_deficit"])
                self.assertEqual(assets, edition["asset_sequence"])
            for field in ("h2_delta", "h3_delta", "table_delta", "code_block_delta"):
                self.assertEqual(0, chapter["parity"][field])

    def test_usb_and_rtos_add_protocol_and_deadline_evidence(self) -> None:
        expected = {
            "14": (
                "usb-enumeration.svg",
                "sample-14-usb-enum.svg",
                "usb-48m.gif",
                "usb-enumeration-zh.gif",
                "sample-14-descriptor-map.svg",
                "pinout-bluepill.svg",
                "instrument-evidence-ladder.svg",
            ),
            "15": (
                "freertos-scheduler.svg",
                "sample-15-rtos-prio.svg",
                "rtos-tick.gif",
                "rtos-deadline-budget.svg",
                "rtos-owner-task.svg",
                "sample-15-rtos-triage.svg",
                "rtos-startup-gates.svg",
            ),
        }
        for chapter_id, assets in expected.items():
            chapter = self.by_id[chapter_id]
            for language in ("zh", "en"):
                edition = chapter[language]
                self.assertEqual(0, edition["visual_anchor_deficit"])
                self.assertEqual(assets, edition["asset_sequence"])
            for field in ("h2_delta", "h3_delta", "table_delta", "code_block_delta"):
                self.assertEqual(0, chapter["parity"][field])

    def test_phase_three_ends_with_power_and_fault_evidence(self) -> None:
        expected = {
            "16": ("lowpower-wakeup.svg", "sample-16-stop-wake.svg", "stop-wake.gif", "sample-16-stop-compare.svg", "lowpower-current-evidence.svg", "sample-16-pwr-triage.svg"),
            "17": ("debug-swo.svg", "sample-17-cfsr.svg", "cfsr-read.gif", "sample-17-obs-compare.svg", "fault-triage-ladder.svg", "sample-17-perf-triage.svg"),
        }
        for chapter_id, assets in expected.items():
            chapter = self.by_id[chapter_id]
            for language in ("zh", "en"):
                edition = chapter[language]
                self.assertEqual(0, edition["visual_anchor_deficit"])
                self.assertEqual(assets, edition["asset_sequence"])
            for field in ("h2_delta", "h3_delta", "table_delta", "code_block_delta"):
                self.assertEqual(0, chapter["parity"][field])

    def test_chapter_24_has_matching_structure_and_visual_distribution(self) -> None:
        chapter = self.by_id["24"]
        expected_assets = (
            "pinout-stm32l476rg-lqfp64.svg",
            "nucleo-f411re-embedded-world.jpg",
            "nucleo-f401re-embedded-world.jpg",
            "l4-stop2-evidence.svg",
            "l4-idd-bench.svg",
        )

        for language in ("zh", "en"):
            edition = chapter[language]
            self.assertEqual(4, edition["pdf_visual_anchors"])
            self.assertEqual(0, edition["visual_anchor_deficit"])
            self.assertEqual(2, edition["photos"])
            self.assertEqual(1, edition["animations"])
            self.assertEqual(expected_assets, edition["asset_sequence"])

        for path in (
            ROOT / "docs" / "24-STM32L4引脚.md",
            ROOT / "docs" / "en" / "24-stm32l4-pins.md",
        ):
            self.assertIn('class="photo-pair"', path.read_text(encoding="utf-8"))

        for field in ("h2_delta", "h3_delta", "table_delta", "code_block_delta"):
            self.assertEqual(0, chapter["parity"][field])

    def test_json_report_round_trips(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "audit.json"
            result = audit_book.main(["--format", "json", "--write", str(output)])
            self.assertEqual(0, result)
            loaded = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(29, loaded["chapter_count"])


if __name__ == "__main__":
    unittest.main()
