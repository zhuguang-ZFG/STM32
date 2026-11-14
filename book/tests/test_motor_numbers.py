"""motor 专题 ch37 章落位后的数值断言（B3 迁移版）。

旧测试 stm32-book/tests/test_motor_draft_numbers.py 钉的是 chapters-draft
草稿路径；ch37 落位到 docs/v5-motion/ 后守卫对象换成新书章节（迁移方案：
先加后删，任一中间状态都有哨兵）。算术断言与旧版一致：

1. ch37 PWM 端点：ARR=3599、计数 3600 格、PWM1 恒有效必须 CCR>ARR
   （CCR=ARR 时 3599/3600 ≈ 99.97%，差一格）。
2. ch37 串口带宽：43 B/帧 × 100 Hz × 8N1(10 bit/字节) = 43 kbit/s，
   占 115200 波特率 ≈ 37.3%（不是 4%）。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from book import manifest as mf


def _chapter_text(chapter_id: str) -> str:
    rows = {row["id"]: row for row in mf.load_toc()}
    rel = rows[chapter_id]["file"]
    return (ROOT / "docs" / rel).read_text(encoding="utf-8")


class MotorChapterLocationTest(unittest.TestCase):
    def test_ch37_path_pinned_in_toc(self):
        rows = {row["id"]: row for row in mf.load_toc()}
        self.assertEqual(rows["ch37"]["file"], "v5-motion/37-dc-motor-openloop.md")


class PwmEndpointTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = _chapter_text("ch37")

    def test_arr_arithmetic(self):
        pwm_hz = 20_000
        clock_hz = 72_000_000
        arr = clock_hz // pwm_hz - 1
        counts = arr + 1
        self.assertEqual(arr, 3599)
        self.assertEqual(counts, 3600)
        self.assertAlmostEqual(arr / counts, 0.99972, places=5)

    def test_chapter_pins_arr_value(self):
        self.assertIn("| ARR | 3599 |", self.text)
        self.assertIn("须大于 ARR", self.text)
        self.assertIn("CCR>ARR", self.text)

    def test_chapter_avoids_regression_wording(self):
        # 负向哨兵：旧文案的错误说法不得回归
        self.assertNotIn("3600=ARR", self.text)
        self.assertNotIn("CCR≥ARR", self.text)
        self.assertNotIn("100%（CCR=ARR）", self.text)


class SerialBandwidthTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = _chapter_text("ch37")

    def test_bandwidth_arithmetic(self):
        frame_bytes = 43
        frame_hz = 100
        bits_per_byte = 10  # 8N1：1 起始 + 8 数据 + 1 停止
        bytes_per_second = frame_bytes * frame_hz
        self.assertEqual(bytes_per_second, 4_300)
        bits_per_second = bytes_per_second * bits_per_byte
        self.assertEqual(bits_per_second, 43_000)
        ratio = bits_per_second / 115_200
        self.assertAlmostEqual(ratio, 0.373, delta=0.0005)

    def test_chapter_pins_bandwidth_value(self):
        self.assertIn("37.3%", self.text)
        self.assertIn("43 kbit/s", self.text)

    def test_chapter_avoids_regression_wording(self):
        self.assertNotIn("带宽的 4%", self.text)


if __name__ == "__main__":
    unittest.main()
