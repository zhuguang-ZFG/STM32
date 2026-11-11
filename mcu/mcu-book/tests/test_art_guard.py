"""art_guard 御舆准入的回归测试（unittest：CI 用 `unittest discover`）。

2026-10-26 实测缺陷：6 枚题图的 <text> 基线落在 y=86..94，字形降部被静默裁掉——
构建、get_text()、12 门印前检查全都不报错，只有把 PDF 放大到印刷尺寸才看得见。
这里钉住「文字必须完整落在 320×88 画布内」这条判据。
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import art_guard  # noqa: E402

HEAD = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 88" '
    'fill="none" stroke="var(--cover-ink, #123b33)" '
    'stroke-linecap="round" stroke-linejoin="round">'
)
INK = 'fill="var(--cover-ink, #123b33)" stroke="none"'


def emblem(text_y: float, size: float = 8) -> str:
    return (
        HEAD
        + '<path d="M20 30 C 60 26, 100 26, 140 30" stroke-width="2.2"/>'
        + '<path d="M20 44 C 60 42, 100 42, 140 44" stroke-width="1.4"/>'
        + f'<text x="160" y="{text_y}" font-family="sans-serif" '
        f'font-size="{size}" {INK} text-anchor="middle">标签</text></svg>'
    )


class ArtGuardYuyuTests(unittest.TestCase):
    def violations(self, svg: str) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "c-01-sample.svg"
            path.write_text(svg, encoding="utf-8", newline="\n")
            return art_guard.check_svg(path, yuyu=True)

    def test_text_baseline_at_canvas_bottom_is_rejected(self) -> None:
        """基线 y=88：降部落到画布外，必须拦下。"""
        errors = self.violations(emblem(88))
        self.assertTrue(any("超出画布下缘" in e for e in errors), errors)

    def test_text_baseline_below_canvas_is_rejected(self) -> None:
        """基线 y=94（实测 rtthread-01 的写法）：整行几乎在画布外。"""
        errors = self.violations(emblem(94, size=7))
        self.assertTrue(any("超出画布下缘" in e for e in errors), errors)

    def test_text_inside_canvas_passes(self) -> None:
        """基线 y=74 是量产里的常用位置，不得误报。"""
        self.assertEqual([], self.violations(emblem(74)))

    def test_filter_era_emblem_is_rejected(self) -> None:
        """滤镜时代的写法在御舆路线下必须报错（filter/id/url 三连）。"""
        svg = (
            HEAD
            + '<filter id="hw-x"><feTurbulence baseFrequency="0.013"/></filter>'
            + '<g filter="url(#hw-x)">'
            + '<path d="M20 30 L140 30" stroke-width="2.2"/>'
            + '<path d="M20 44 L140 44" stroke-width="1.4"/></g></svg>'
        )
        errors = self.violations(svg)
        self.assertGreaterEqual(len([e for e in errors if "违规内容" in e]), 3, errors)


if __name__ == "__main__":
    unittest.main()
