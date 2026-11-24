"""`publish_staged.py` must police the byte-for-byte published copies too.

`docs/public/images/*.png` and `docs/public/arch/*.png` hold verbatim copies of
`assets/illustrations/handraw/*.png` for plates that carry no staged SVG. Those
copies used to be invisible to the drift gate: 163 of them sat a commit behind
and the single doc-facing alias (`/arch/cortex-m-4gb-map.png`) was never
refreshed. These tests pin the three properties that make the gate trustworthy:

* a mirrored copy is compared against its handraw source, and drift makes
  `main()` exit 1;
* repair clears the drift;
* a plate the staged family owns is never claimed by the mirror set, even when
  a same-stem handraw PNG exists (a stale staged PNG once got copied over a
  fresh publish that way).

Everything runs in temp trees with the render step stubbed out; no Chromium and
no real asset is touched.
"""
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "handraw_track" / "publish_staged.py"


def _load_tool():
    spec = importlib.util.spec_from_file_location("publish_staged_under_test", TOOL)
    assert spec is not None and spec.loader is not None, f"cannot load {TOOL}"
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


class MirrorGateTest(unittest.TestCase):
    def setUp(self):
        self.tool = _load_tool()
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.handraw = base / "handraw"
        self.staged = base / "staged"
        self.images = base / "images"
        self.arch = base / "arch"
        for d in (self.handraw, self.staged, self.images, self.arch):
            d.mkdir()
        patches = [
            mock.patch.object(self.tool, "HANDRAW", self.handraw),
            mock.patch.object(self.tool, "STAGED", self.staged),
            mock.patch.object(self.tool, "IMAGES", self.images),
            mock.patch.object(self.tool, "ARCH", self.arch),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        self.addCleanup(self.tmp.cleanup)

    def _write(self, path: Path, data: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def test_drift_is_detected_and_named(self):
        self._write(self.handraw / "alpha.png", b"new-render")
        self._write(self.images / "alpha.png", b"old-render")
        self.assertEqual(self.tool.mirror_drift(), [self.images / "alpha.png"])

    def test_repair_clears_drift(self):
        self._write(self.handraw / "alpha.png", b"new-render")
        self._write(self.images / "alpha.png", b"old-render")
        self.assertEqual(self.tool.sync_mirrors(), [self.images / "alpha.png"])
        self.assertEqual(self.tool.mirror_drift(), [])
        self.assertEqual((self.images / "alpha.png").read_bytes(), b"new-render")

    def test_arch_alias_follows_its_generator_name(self):
        self._write(self.handraw / "arch-cortex-m-4gb.png", b"gen")
        self._write(self.arch / "cortex-m-4gb-map.png", b"old")
        self.assertEqual(self.tool.mirror_drift(), [self.arch / "cortex-m-4gb-map.png"])
        self.tool.sync_mirrors()
        self.assertEqual(self.tool.mirror_drift(), [])

    def test_staged_owned_plate_is_not_a_mirror(self):
        # Both trees carry ch46-roadmap-gates, but the staged SVG owns the
        # published PNG; a handraw file must not be treated as its source.
        self._write(self.staged / "group" / "ch46-roadmap-gates.svg", b"<svg/>")
        self._write(self.handraw / "ch46-roadmap-gates.png", b"wrong-source")
        self._write(self.images / "ch46-roadmap-gates.png", b"staged-render")
        self.assertEqual(self.tool.mirrored_plates(), {})
        self.assertEqual(self.tool.mirror_drift(), [])

    def test_check_exits_one_on_mirror_drift_and_zero_after_repair(self):
        self._write(self.handraw / "alpha.png", b"new-render")
        self._write(self.images / "alpha.png", b"old-render")
        # Stub the staged chain: this test is about mirror wiring, not Chromium.
        with mock.patch.object(self.tool, "regenerate", lambda: None), \
             mock.patch.object(self.tool, "expected_plates",
                               lambda *_a, **_k: {"staged-plate": Path("unused.svg")}), \
             mock.patch.object(self.tool, "diff",
                               lambda *_a, **_k: ([], [], [])), \
             mock.patch.object(sys, "argv", ["publish_staged.py", "--check"]):
            self.assertEqual(self.tool.main(), 1)
            self.tool.sync_mirrors()
            self.assertEqual(self.tool.main(), 0)


if __name__ == "__main__":
    unittest.main()
