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
            "sample-19-slot-fill-flow.svg",
            "sample-19-flash-fit.svg",
            "ch19-flash-fit.png",
            "one-slot.gif",
            "sample-19-pick-ladder.svg",
            "ch19-pick-ladder.png",
            "dma-buffer-ownership.svg",
            "iap-acceptance-gates.svg",
            "ch19-iap-gates.png",
            "network-debug-ladder.svg",
            "rtos-startup-gates.svg",
            "sample-19-milestone-triage.svg",
            "ch19-milestone-triage.png",
            "sample-19-sram-budget.svg",
            "ch19-sram-budget.png",
        )
        for language in ("zh", "en"):
            self.assertEqual(0, chapter[language]["visual_anchor_deficit"])
            self.assertEqual(assets, chapter[language]["asset_sequence"])
        for field in ("h2_delta", "h3_delta", "table_delta", "code_block_delta"):
            self.assertEqual(0, chapter["parity"][field])

    def test_first_hardware_loop_has_visual_and_structure_parity(self) -> None:
        chapter = self.by_id["01"]
        expected_assets = (
            "boot-sequence.svg", "sample-01-swd-vectors.svg", "ch01-swd-vectors.png",
            "swd-fetch.gif", "sample-01-flash-swd-flow.svg", "sample-01-env-compare.svg",
            "ch01-four-envs-one-elf.png", "single-build-contract.svg", "sample-01-flash-path.svg",
            "ch01-three-flash-paths.png", "project-structure.svg", "sample-01-rdp-unlock.svg",
            "ch01-rdp-unlock.png", "sample-01-flash-triage.svg", "ch01-flash-triage.png",
            "sample-01-debug-connect.svg", "ch01-debug-connect-rings.png", "sample-01-build-accept.svg",
        )
        for language in ("zh", "en"):
            edition = chapter[language]
            self.assertEqual(18, edition["pdf_visual_anchors"])
            self.assertEqual(0, edition["visual_anchor_deficit"])
            self.assertEqual(expected_assets, edition["asset_sequence"])
        for field in ("h2_delta", "h3_delta", "table_delta", "code_block_delta"):
            self.assertEqual(0, chapter["parity"][field])

    def test_gpio_interrupt_timer_close_phase_one(self) -> None:
        expected = {
            "03": (

                "gpio-blink.svg", "ch03-handdraw.svg", "ch03-common-anode-before-after.png",
                "sample-03-gpio-bsrr-flow.svg", "sample-03-gpio-led.svg", "ch03-pa0-ok-pc13-wrong.png",
                "ch03-gpio-three-questions.png", "ch03-push-pull-vs-open-drain.png", "sample-03-current-path.svg",
                "ch03-led-current-limit.png", "sample-03-moder-map.svg", "bluepill-stm32f103c8t6.jpg",
                "bluepill-stm32f103c8t6-popolon.jpg", "stack-gpio-pc13-led.png", "pinout-bluepill.svg",
                "led-blink.gif", "sample-03-exti-vs-poll.svg", "ch03-poll-vs-exti.png",
            ),
            "04": (

                "nvic-interrupt-flow.svg", "sample-04-nvic-preempt-flow.svg", "sample-04-exception-stack.svg",
                "ch04-exception-stack.png", "nvic-preempt.gif", "sample-04-priority-group.svg",
                "ch04-priority-group.png", "interrupt-priority.svg", "ch04-preempt-vs-sub.png",
                "gpio-input-interrupt.svg", "sample-04-exti-line-map.svg", "ch04-exti-line-map.png",
                "sample-04-exti-triage.svg", "ch04-exti-triage.png", "sample-04-tail-chaining.svg",
                "ch04-tail-chaining.png",
            ),
            "05": (

                "timer-pwm.svg", "sample-05-pwm-edge-flow.svg", "sample-05-pwm-1khz.svg",
                "ch05-pwm-1khz.png", "pwm-1khz.gif", "sample-05-timebase-math.svg",
                "ch05-timebase-math.png", "sample-05-shadow-regs.svg", "ch05-shadow-regs.png",
                "timer-modes.svg", "sample-05-pwm-debug.svg", "ch05-pwm-debug.png",
                "pwm-breath.gif", "sample-05-deadtime.svg", "ch05-deadtime.png",
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

                "uart-frame.svg", "sample-06-uart-baud-wire.svg", "sample-06-uart-frame.svg",
                "ch06-uart-frame.png", "uart-idle.gif", "sample-06-frame-annotated.svg",
                "uart-bits.gif", "sample-06-baud-formula.svg", "ch06-baud-formula.png",
                "sample-06-baud-triage.svg", "ch06-baud-triage.png", "sample-06-tx-rx-crossover.svg",
                "ch06-tx-rx-crossover.png", "sample-06-idle-dma.svg", "ch06-idle-dma.png",
            ),
            "07": (

                "i2c-transaction.svg", "sample-07-i2c-ack-flow.svg", "sample-07-i2c-addr.svg",
                "ch07-i2c-addr.png", "i2c-addr.gif", "sample-07-pullup-cap.svg",
                "ch07-pullup-cap.png", "sample-07-start-ack.svg", "ch07-start-ack.png",
                "i2c-timing.gif", "sample-07-sr-restart.svg", "ch07-sr-restart.png",
                "sample-07-i2c-triage.svg", "ch07-i2c-triage.png",
            ),
            "08": (

                "spi-transfer.svg", "sample-08-spi-jedec-flow.svg", "sample-08-spi-jedec.svg",
                "ch08-spi-jedec.png", "spi-jedec.gif", "sample-08-mode0-edges.svg",
                "sample-08-cpha-modes.svg", "ch08-cpha-modes.png", "sample-08-br-table.svg",
                "ch08-br-table.png", "sample-08-nss-multi.svg", "ch08-nss-multi.png",
                "sample-08-bus-compare.svg", "sample-08-spi-triage.svg", "ch08-spi-triage.png",
            ),
            "09": (

                "adc-sar.svg", "sample-09-adc-sar-weights.svg", "sample-09-adc-sar.svg",
                "ch09-adc-sar.png", "adc-sample.gif", "sample-09-vref-rails.svg",
                "ch09-vref-rails.png", "sample-09-sar-ladder.svg", "ch09-sar-ladder.png",
                "sar-adc.gif", "dma-circular.svg", "sample-09-sample-time.svg",
                "ch09-sample-time.png", "sample-09-adc-triage.svg", "ch09-adc-triage.png",
            ),
            "10": (

                "dma-circular.svg", "sample-10-dma-circular-ht.svg", "sample-10-dma-cndtr.svg",
                "ch10-dma-cndtr.png", "dma-cndtr.gif", "sample-10-mem2mem-vs-peri.svg",
                "ch10-mem2mem-vs-peri.png", "sample-10-dma-triage.svg", "ch10-dma-triage.png",
                "sample-10-dma-phases.svg", "ch10-dma-phases.png", "dma-buffer-ownership.svg",
                "dma-ring.gif", "sample-10-cndtr-ledger.svg", "ch10-cndtr-ledger.png",
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
            "11": (

                "iwdg-window.svg", "sample-11-iwdg-feed-flow.svg", "sample-11-iwdg-1s.svg",
                "ch11-iwdg-1s.png", "iwdg-1s.gif", "sample-11-backup-domain.svg",
                "ch11-backup-domain.png", "sample-11-wdg-compare.svg", "ch11-wdg-compare.png",
                "sample-11-iwdg-math.svg", "ch11-iwdg-math.png", "watchdog-reset-evidence.svg",
                "sample-11-rtc-triage.svg", "ch11-rtc-triage.png",
            ),
            "12": (

                "flash-iap.svg", "sample-12-iap-jump-flow.svg", "sample-12-iap-map.svg",
                "ch12-iap-map.png", "iap-jump.gif", "sample-12-page-erase.svg",
                "ch12-page-erase.png", "sample-12-flash-triage.svg", "ch12-flash-triage.png",
                "sample-12-key-order.svg", "ch12-key-order.png", "iap-acceptance-gates.svg",
                "ch12-acceptance-gates.png", "sample-12-boot-compare.svg", "ch12-boot-compare.png",
            ),
            "13": (

                "can-arbitration.svg", "sample-13-can-arb-flow.svg", "sample-13-can-bit.svg",
                "ch13-can-bit.png", "can-500k.gif", "sample-13-bit-quanta.svg",
                "ch13-bit-quanta.png", "sample-13-filter-fifo.svg", "ch13-filter-fifo.png",
                "sample-13-can-triage.svg", "ch13-can-triage.png", "sample-13-tec-busoff.svg",
                "ch13-tec-busoff.png",
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

    def test_usb_and_rtos_add_protocol_and_deadline_evidence(self) -> None:
        expected = {
            "14": (

                "usb-enumeration.svg", "sample-14-usb-48m-flow.svg", "sample-14-usb-enum.svg",
                "ch14-usb-enum.png", "usb-48m.gif", "sample-14-usbpre-48.svg",
                "ch14-usbpre-48.png", "sample-14-pma-map.svg", "ch14-pma-map.png",
                "usb-enumeration-zh.gif", "sample-14-descriptor-map.svg", "ch14-descriptor-map.png",
                "pinout-bluepill.svg", "instrument-evidence-ladder.svg", "ch14-evidence-ladder.png",
            ),
            "15": (

                "freertos-scheduler.svg", "sample-15-rtos-tick-flow.svg", "sample-15-rtos-prio.svg",
                "ch15-rtos-prio.png", "rtos-tick.gif", "sample-15-task-states.svg",
                "ch15-task-states.png", "rtos-deadline-budget.svg", "ch15-deadline-budget.png",
                "rtos-owner-task.svg", "ch15-owner-task.png", "sample-15-fromisr.svg",
                "ch15-fromisr.png", "sample-15-rtos-triage.svg", "rtos-startup-gates.svg",
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
            "16": (

                "lowpower-wakeup.svg", "sample-16-stop-wake-flow.svg", "sample-16-stop-wake.svg",
                "ch16-stop-wake.png", "stop-wake.gif", "sample-16-stop-compare.svg",
                "ch16-stop-compare.png", "sample-16-mode-current.svg", "ch16-mode-current.png",
                "sample-16-clock-restore.svg", "ch16-clock-restore.png", "lowpower-current-evidence.svg",
                "sample-16-pwr-triage.svg", "ch16-pwr-triage.png",
            ),
            "17": (

                "debug-swo.svg", "sample-17-cfsr-flow.svg", "sample-17-cfsr.svg",
                "ch17-cfsr.png", "cfsr-read.gif", "sample-17-swd-pins.svg",
                "ch17-swd-pins.png", "sample-17-obs-compare.svg", "ch17-obs-compare.png",
                "sample-17-cfsr-bits.svg", "ch17-cfsr-bits.png", "fault-triage-ladder.svg",
                "sample-17-perf-triage.svg", "ch17-perf-triage.png",
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


    def test_phase_four_projects_faq_resources_boards_and_sim(self) -> None:
        expected = {
            "18": (

                "toolchain-flow.svg", "sample-18-boot0-flow.svg", "sample-18-boot-triage.svg",
                "ch18-boot-triage.png", "boot0-low.gif", "sample-18-link-map.svg",
                "ch18-link-map.png", "sample-18-hardfault-ladder.svg", "ch18-hardfault-ladder.png",
                "sample-18-faq-compare.svg", "ch18-faq-compare.png", "sample-18-uart-garbled.svg",
                "ch18-uart-garbled.png",
            ),
            "19": (

                "peripheral-wiring.svg", "sample-19-slot-fill-flow.svg", "sample-19-flash-fit.svg",
                "ch19-flash-fit.png", "one-slot.gif", "sample-19-pick-ladder.svg",
                "ch19-pick-ladder.png", "dma-buffer-ownership.svg", "iap-acceptance-gates.svg",
                "ch19-iap-gates.png", "network-debug-ladder.svg", "rtos-startup-gates.svg",
                "sample-19-milestone-triage.svg", "ch19-milestone-triage.png", "sample-19-sram-budget.svg",
                "ch19-sram-budget.png",
            ),
            "20": (

                "project-structure.svg", "sample-20-evidence-flow.svg", "sample-20-lookup-flow.svg",
                "sample-20-manual-names.svg", "ch20-manual-names.png", "manual-choice-map.svg",
                "ch20-manual-choice.png", "sample-20-lib-compare.svg", "ch20-lib-compare.png",
                "firmware-stack-choice.svg", "instrument-evidence-ladder.svg", "ch20-evidence-ladder.png",
                "single-build-contract.svg", "sample-20-evidence-triage.svg", "ch20-evidence-triage.png",
            ),
            "21": (

                "bluepill-stm32f103c8t6.svg", "sample-21-crystal-boot-flow.svg", "sample-21-board-compare.svg",
                "ch21-board-compare.png", "sample-21-vdd-3v3.svg", "ch21-vdd-3v3.png",
                "bluepill-stm32f103c8t6.svg", "blackpill-stm32f411ce.svg", "nucleo-f411re.svg",
                "f4-discovery.svg", "f103zet6-dev.svg", "pinout-bluepill.svg",
                "sample-21-usb-ttl.svg", "ch21-usb-ttl.png", "peripheral-wiring.svg",
                "sample-21-power-swd.svg", "sample-21-hse-load.svg", "ch21-hse-load.png",
                "sample-21-nrst-boot0.svg", "ch21-nrst-boot0.png",
            ),
            "22": (

                "toolchain-flow.svg", "sample-22-sim-pick-flow.svg", "simulator-comparison.svg",
                "ch22-sim-compare.png", "sample-22-wokwi-scope.svg", "ch22-wokwi-scope.png",
                "simulation-model-boundary.svg", "sample-22-renode-path.svg", "ch22-renode-path.png",
                "sample-22-sim-triage.svg", "ch22-sim-triage.png", "sample-22-hw-gap.svg",
                "ch22-hw-gap.png", "simulation-acceptance-gates.svg",
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


    def test_phase_five_family_migration_spl_network_rtos(self) -> None:
        expected = {
            "23": (

                "pinout-stm32g071rb-lqfp64.svg", "ch23-part-id.png", "pinout-bluepill.svg",
                "sample-23-boot0-swclk.svg", "sample-23-boot-latch.svg", "ch23-boot-latch.png",
                "g0-boot-swd.svg", "sample-23-boot-source-flow.svg", "sample-23-f1-g0-compare.svg",
                "ch23-pin-compare.png", "sample-23-f1-copy-traps.svg", "ch23-pinmux.png",
            ),
            "24": (

                "pinout-stm32l476rg-lqfp64.svg", "ch24-part-id.png", "nucleo-f411re-embedded-world.jpg",
                "nucleo-f401re-embedded-world.jpg", "sample-24-stop2-retain.svg", "sample-24-mode-compare.svg",
                "ch24-modes.png", "l4-stop2-evidence.svg", "sample-24-wake-restore-flow.svg",
                "ch24-wake-clocks.png", "sample-24-wake-triage.svg", "ch24-pin-mux.png",
                "sample-24-idd-jp6.svg", "ch24-idd.png", "l4-idd-bench.svg",
            ),
            "25": (

                "pinout-stm32h743zi-lqfp144.svg", "ch25-part-id.png", "h7-power-domains.svg",
                "ch25-pin-compare.png", "sample-25-voltage-scale.svg", "ch25-rev-vos.png",
                "h7-revision-clock-decision.svg", "sample-25-hse-to-480-flow.svg", "ch25-clock-math.png",
                "h7-clock-chain.svg", "h7-startup-evidence.svg", "h7-pinmux-conflicts.svg",
                "ch25-pinmux.png", "sample-25-migrate-triage.svg", "sample-25-dcache-dma.svg",
                "network-cache-ownership.svg",
            ),
            "26": (

                "spl-ownership-boundary.svg", "ch26-four-layers.png", "sample-26-file-matrix.svg",
                "ch26-defines.png", "sample-26-clk-cfg-en-flow.svg", "spl-init-pipeline.svg",
                "ch26-init-steps.png", "bluepill-stm32f103c8t6.svg", "sample-26-spl-hal-compare.svg",
                "ch26-spl-hal.png", "sample-26-timeout-poll.svg", "ch26-timeout-poll.png",
                "nvic-interrupt-flow.svg", "dma-circular.svg",
            ),
            "27": (

                "network-packet-journey.svg", "sample-27-rmii-checklist.svg", "ch27-rmii-signals.png",
                "network-cache-ownership.svg", "ch27-cache-dma.png", "sample-27-tcp-framing.svg",
                "ch27-api-context.png", "sample-27-link-dhcp-flow.svg", "network-online-state.svg",
                "tcp-byte-stream.svg", "ch27-tcp-framing.png", "sample-27-link-triage.svg",
                "ch27-backoff.png", "network-debug-ladder.svg",
            ),
            "28": (

                "rtos-system-layers.svg", "sample-28-four-concepts.svg", "ch28-four-concepts.png",
                "sample-28-os-compare.svg", "ch28-os-compare.png", "nucleo-f411re-embedded-world.jpg",
                "nucleo-f401re-embedded-world.jpg", "sample-28-isr-owner-flow.svg", "sample-28-owner-flow.svg",
                "rtos-owner-task.svg", "ch28-owner-task.png", "sample-28-three-times.svg",
                "rtos-deadline-budget.svg", "ch28-three-times.png", "freertos-scheduler.svg",
                "rtos-config-paths.svg", "rtos-startup-gates.svg", "sample-28-fault-triage.svg",
                "ch28-fault-triage.png",
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

    def test_chapter_24_has_matching_structure_and_visual_distribution(self) -> None:
        chapter = self.by_id["24"]
        expected_assets = (
            "pinout-stm32l476rg-lqfp64.svg", "ch24-part-id.png", "nucleo-f411re-embedded-world.jpg",
            "nucleo-f401re-embedded-world.jpg", "sample-24-stop2-retain.svg", "sample-24-mode-compare.svg",
            "ch24-modes.png", "l4-stop2-evidence.svg", "sample-24-wake-restore-flow.svg",
            "ch24-wake-clocks.png", "sample-24-wake-triage.svg", "ch24-pin-mux.png",
            "sample-24-idd-jp6.svg", "ch24-idd.png", "l4-idd-bench.svg",
        )

        for language in ("zh", "en"):
            edition = chapter[language]
            self.assertEqual(14, edition["pdf_visual_anchors"])
            self.assertEqual(0, edition["visual_anchor_deficit"])
            self.assertEqual(2, edition["photos"])
            self.assertEqual(2, edition["animations"])
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
