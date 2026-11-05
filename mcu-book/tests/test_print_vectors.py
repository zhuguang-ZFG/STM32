"""印前矢量守卫的回归测试（unittest：CI 用 `unittest discover`）。

背景（2026-10-26）：另一条会话会把滤镜版题图写回 `chapter-art/`。滤镜版一旦
进 HTML 快照，88 枚题图会在 PDF 里全部栅格化，而 12 门里没有任何一项会因此
变红（版面密度只看单页密度，不看图片数量）。这两道断言把「静默降质」变成硬失败。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import build_print  # noqa: E402
import check_pdf  # noqa: E402

VECTOR = '<svg viewBox="0 0 320 88"><path d="M0 0 C 10 10, 20 20, 30 30" stroke-width="2.2"/></svg>'
FILTERED = (
    '<svg viewBox="0 0 320 88"><filter id="hw-x"><feTurbulence baseFrequency="0.013"/>'
    '</filter><g filter="url(#hw-x)"><path d="M0 0"/></g></svg>'
)


class _Page:
    def __init__(self, images: int) -> None:
        self._images = images

    def get_images(self) -> list[tuple[int, ...]]:
        return [(i,) for i in range(self._images)]


class _Doc:
    def __init__(self, per_page: list[int]) -> None:
        self._pages = [_Page(n) for n in per_page]
        self.page_count = len(per_page)

    def __getitem__(self, index: int) -> _Page:
        return self._pages[index]


class PrintVectorGuardTests(unittest.TestCase):
    def test_vector_html_passes(self) -> None:
        build_print.assert_vector_art(f"<html><body>{VECTOR}</body></html>")

    def test_filtered_emblem_is_rejected(self) -> None:
        with self.assertRaises(SystemExit) as caught:
            build_print.assert_vector_art(f"<html><body>{FILTERED}</body></html>")
        self.assertIn("feTurbulence", str(caught.exception))

    def test_raster_budget_accepts_photos_only(self) -> None:
        self.assertEqual([], check_pdf.check_raster_budget(
            _Doc([0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1])))

    def test_raster_budget_rejects_rasterised_emblems(self) -> None:
        problems = check_pdf.check_raster_budget(_Doc([1] * 60))
        self.assertTrue(problems)
        self.assertIn("光栅图 60 张", problems[0])


if __name__ == "__main__":
    unittest.main()
