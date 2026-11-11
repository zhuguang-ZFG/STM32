"""分部隔页题图覆盖：manifest 每个 part id 都必须有非空 part_art。

2026-10-27 接入第十一部时的实证风险：part_art() 是 if 链 + 末尾 return ""
fallback，新部 id 漏加分支时构建照常通过——隔页静默空一块，13 门与
art_guard 都不报。这里钉死「清单里每个部都有配图」这条判据。
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "print"))

import art  # noqa: E402  # type: ignore[import-not-found]


class PartArtCoverageTests(unittest.TestCase):
    def test_every_manifest_part_has_art(self) -> None:
        manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
        missing = [p["id"] for p in manifest["parts"] if not art.part_art(p["id"]).strip()]
        self.assertEqual([], missing)

    def test_part_art_has_no_filter_or_bitmap_path(self) -> None:
        manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
        for p in manifest["parts"]:
            svg = art.part_art(p["id"])
            with self.subTest(part=p["id"]):
                self.assertNotIn("feTurbulence", svg)
                self.assertNotIn("<filter", svg)
                self.assertNotIn("href=", svg)


if __name__ == "__main__":
    unittest.main()
