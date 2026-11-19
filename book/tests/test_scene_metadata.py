"""scenes.json 是站点与印刷渲染器共用的 schema，两边都得能读。

站点侧额外写入 width/height（来自 PNG 头），用于 <noscript> 回退图的布局预留。
这些键对 Python 渲染器是可选的，但一旦存在就必须是正数，且与真实 PNG 尺寸一致——
换图不更新尺寸会让站点在无 JS 时跳版，而这里能直接拦住。
"""
import json
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "book"))

from build_html import load_stick_scenes  # noqa: E402

SCENES = ROOT / "docs/.vitepress/data/scenes.json"
PUBLIC = ROOT / "docs/public"


def png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        head = handle.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        raise AssertionError(f"{path} is not a PNG")
    return struct.unpack(">II", head[16:24])


class SceneMetadataTests(unittest.TestCase):
    def test_renderer_accepts_the_extra_dimensions(self):
        scenes = load_stick_scenes(SCENES)
        self.assertGreaterEqual(len(scenes), 5)
        for scene_id, scene in scenes.items():
            for key in ("label", "caption", "fallback"):
                self.assertTrue(scene[key], f"{scene_id}: empty {key}")
            for key in ("width", "height"):
                self.assertIn(key, scene, f"{scene_id}: missing {key}")
                self.assertIsInstance(scene[key], int)
                self.assertGreater(scene[key], 0)

    def test_dimensions_match_the_real_png_header(self):
        scenes = json.loads(SCENES.read_text(encoding="utf-8"))
        for scene_id, scene in scenes.items():
            rel = str(scene["fallback"]).lstrip("/")
            width, height = png_size(PUBLIC / rel)
            self.assertEqual(
                (scene["width"], scene["height"]),
                (width, height),
                f"{scene_id}: scenes.json 与 {rel} 的实际尺寸不一致",
            )


if __name__ == "__main__":
    unittest.main()