"""The staged publish chain must treat a deleted plate as work, not as absence.

The failure this guards: deriving the expected set from `docs/public/images/`
means a deleted PNG simply stops being expected, so `--check` reported
"drift 0" over 62 plates and a normal run never restored the 63rd.
"""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/handraw_track"))

import publish_staged as P


def fake_render(svg: Path) -> bytes:
    return f"<png {svg.stem}>".encode()


class StagedPublishTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.images = Path(self.tmp.name)
        self.expected = {s: Path(f"{s}.svg") for s in ("alpha", "beta")}

    def tearDown(self):
        self.tmp.cleanup()

    def test_deleted_target_is_drift(self):
        (self.images / "alpha.png").write_bytes(fake_render(Path("alpha.svg")))
        missing, stale, _ = P.diff(self.expected, self.images, fake_render)
        self.assertEqual(missing, ["beta"], "a deleted plate must be expected")
        self.assertEqual(stale, [])

    def test_publish_recreates_deleted_target(self):
        (self.images / "alpha.png").write_bytes(fake_render(Path("alpha.svg")))
        created, updated = P.publish(self.expected, self.images, fake_render)
        self.assertEqual(created, ["beta"])
        self.assertEqual(updated, [])
        self.assertEqual((self.images / "beta.png").read_bytes(),
                         fake_render(Path("beta.svg")))

    def test_publish_repairs_stale_bytes(self):
        (self.images / "alpha.png").write_bytes(b"outdated")
        (self.images / "beta.png").write_bytes(fake_render(Path("beta.svg")))
        created, updated = P.publish(self.expected, self.images, fake_render)
        self.assertEqual((created, updated), ([], ["alpha"]))
        missing, stale, _ = P.diff(self.expected, self.images, fake_render)
        self.assertEqual((missing, stale), ([], []))

    def test_published_without_source_is_reported(self):
        for name in self.expected:
            (self.images / f"{name}.png").write_bytes(fake_render(Path(f"{name}.svg")))
        (self.images / "legacy.png").write_bytes(b"x")
        _, _, orphan = P.diff(self.expected, self.images, fake_render)
        self.assertEqual(orphan, ["legacy"])

    def test_expected_set_comes_from_generators_not_from_published(self):
        """An empty images dir still yields every generated plate."""
        missing, _, _ = P.diff(self.expected, self.images, fake_render)
        self.assertEqual(missing, ["alpha", "beta"])

    def test_real_staged_tree_is_fully_expected(self):
        """Every staged SVG in the repo is an expected published target."""
        expected = P.expected_plates()
        self.assertGreaterEqual(len(expected), 86)
        for stem in ("ch01-memory-two-addresses", "ch46-l0-l5-ladder",
                     "ch00-swd-four-wires", "ch45-first-failed-boundary"):
            self.assertIn(stem, expected)


if __name__ == "__main__":
    unittest.main()
