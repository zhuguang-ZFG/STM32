#!/usr/bin/env python3
""" motor 专题 29–32 章草稿的数值断言（P4 MC-401 配套）。

草稿暂存于 plans/2026-11-11-motor-control/chapters-draft/（落位 docs/ 属
MC-406）。本测试把章内两处可复算数值钉死，防止文案回归：

1. ch30 PWM 端点：ARR=3599、计数 3600 格、PWM1 恒有效必须 CCR>ARR
   （CCR=ARR 时 3599/3600 ≈ 99.97%，差一格）。
2. ch30 串口带宽：43 B/帧 × 100 Hz × 8N1(10 bit/字节) = 43 kbit/s，
   占 115200 波特率 ≈ 37.3%（不是 4%）。
"""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CH30 = ROOT / "plans" / "2026-11-11-motor-control" / "chapters-draft" / "30-直流电机开环调速.md"


class MotorDraftNumberTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = CH30.read_text(encoding="utf-8")

    def test_pwm_100_percent_requires_ccr_above_arr(self) -> None:
        arr = 72_000_000 // 20_000 - 1
        self.assertEqual(3599, arr)
        counts = arr + 1  # CNT 取值 0..ARR 共 3600 格
        self.assertEqual(3600, counts)
        # PWM1 有效条件 CNT < CCR：CCR=ARR 时仍有一格无效
        self.assertLess(arr, counts)
        self.assertAlmostEqual(arr / counts, 0.99972, places=5)

        self.assertIn("| ARR | 3599 |", self.text)
        self.assertIn("须大于 ARR", self.text)
        self.assertIn("CCR>ARR", self.text)
        self.assertNotIn("3600=ARR", self.text)
        self.assertNotIn("CCR≥ARR", self.text)
        self.assertNotIn("100%（CCR=ARR）", self.text)

    def test_serial_bandwidth_is_37_percent_not_4(self) -> None:
        bits_per_frame = 43 * 10  # 8N1：每字节 1 起始 + 8 数据 + 1 停止
        bit_rate = bits_per_frame * 100  # SAMPLE 帧 @100 Hz
        self.assertEqual(43_000, bit_rate)
        pct = bit_rate / 115_200 * 100
        self.assertAlmostEqual(pct, 37.3, delta=0.05)
        # 字节口径的带宽预算另行成立：4300 B/s
        self.assertEqual(4_300, 43 * 100)

        self.assertIn("37.3%", self.text)
        self.assertIn("43 kbit/s", self.text)
        self.assertNotIn("带宽的 4%", self.text)


if __name__ == "__main__":
    unittest.main()
