"""Every figure a chapter shows must have a tracked source in the repo.

The hand-drawn layer has two sources: `assets/illustrations/handraw/*.svg`
(one plate per file) and `assets/illustrations/staged/**/*.svg` (the v0/v1/v2/
b3/onramp/learning family, rendered into `docs/public/images/` by
`tools/handraw_track/publish_staged.py`). A committed PNG with no source is a
plate nobody can rebuild or retint, so the guard fails when a chapter starts
referencing one.

Plan documents under `docs/superpowers/plans/` are excluded: they quote
placeholder paths such as `/images/x.png` on purpose.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
PUBLIC = DOCS / "public"

REF = re.compile(r"/(images|arch|figures|anim)/([A-Za-z0-9._-]+)\.(?:png|svg|gif)")

# arch plates that ship under a name that differs from their source file
ARCH_ALIAS = {"cortex-m-4gb-map.png": "arch-cortex-m-4gb.svg"}


def _sources() -> tuple[set[str], set[str]]:
    hand = {p.stem for p in (ROOT / "assets/illustrations/handraw").glob("*.svg")}
    staged = {p.stem for p in (ROOT / "assets/illustrations/staged").rglob("*.svg")}
    return hand, staged


def _arch_sources() -> set[str]:
    names = {
        p.name.replace("arch-", "").replace(".svg", ".png")
        for p in (ROOT / "assets/illustrations/handraw").glob("arch-*.svg")
    }
    names |= set(ARCH_ALIAS)
    return names


class FigureSourceTests(unittest.TestCase):
    def test_handraw_plates_are_paired(self):
        """Every handraw PNG must have its SVG neighbour, and vice versa.

        Unpaired PNGs are how the hand-drawn layer accumulated 89 files
        (72 MB) that no one could rebuild or attribute: they were drawn once,
        shipped, and the source was never committed. Retiring them once is
        not enough — the directory has to stay paired.
        """
        layer = ROOT / "assets/illustrations/handraw"
        png = {p.stem for p in layer.glob("*.png")}
        svg = {p.stem for p in layer.glob("*.svg")}
        self.assertEqual(
            sorted(png - svg), [],
            "handraw PNG without an SVG source (unbuildable, retire or draw it)")
        self.assertEqual(
            sorted(svg - png), [],
            "handraw SVG without a rendered PNG (run tools/handraw_track/render.py)")

    def _chapters(self):
        for md in DOCS.rglob("*.md"):
            if "superpowers" in md.parts:
                continue
            yield md

    def test_chapter_figures_have_a_source(self):
        hand, staged = _sources()
        arch = _arch_sources()
        missing: list[str] = []
        for md in self._chapters():
            text = md.read_text(encoding="utf-8", errors="ignore")
            for kind, name in REF.findall(text):
                target = PUBLIC / kind / f"{name}.{('png' if kind in ('images', 'arch') else 'svg')}"
                if kind == "images" and not (PUBLIC / "images" / f"{name}.png").exists():
                    continue  # broken links are the link scan's job, not this one
                if kind == "arch":
                    if not (PUBLIC / "arch" / f"{name}.png").exists():
                        continue
                    if f"{name}.png" not in arch:
                        missing.append(f"{md.relative_to(ROOT)} -> /arch/{name}.png")
                    continue
                if kind != "images":
                    continue
                if name not in hand and name not in staged:
                    missing.append(f"{md.relative_to(ROOT)} -> /images/{name}.png")
        self.assertEqual(missing, [], "figures without a tracked source: "
                         + ", ".join(sorted(missing)[:8]))

    def test_staged_sources_are_tracked_not_temp(self):
        """Staged plates must be written under assets/, never into .temp/."""
        staged = ROOT / "assets/illustrations/staged"
        self.assertTrue(staged.is_dir(), "staged source directory is gone")

        module_dir = ROOT / "tools/handraw_track"
        offenders = []
        for path in module_dir.glob("fig_*.py"):
            text = path.read_text(encoding="utf-8", errors="ignore")
            if '".temp"' in text and "staged" not in text:
                offenders.append(path.name)
        self.assertEqual(offenders, [],
                         "these modules still write plates to .temp/: "
                         + ", ".join(sorted(offenders)))

        # every staged module is wired into the publish entry point
        publish = (module_dir / "publish_staged.py").read_text(encoding="utf-8")
        for name in ("fig_v0", "fig_v1b", "fig_v2e", "fig_v4a", "fig_v7a",
                     "fig_onramp", "fig_merged_b3", "fig_learning"):
            self.assertIn(f'"{name}"', publish, f"{name} missing from publish_staged")

    def test_readme_lists_the_same_staged_modules(self):
        """The palette note must not drift from publish_staged.MODULES.

        A short list in the README is how the staged family got half
        regenerated once already: the doc named 6 of 14 modules, so six
        plates kept the old tint.
        """
        import re
        import sys

        sys.path.insert(0, str(ROOT / "tools/handraw_track"))
        from publish_staged import MODULES

        readme = (ROOT / "tools/handraw_track/README.md").read_text(
            encoding="utf-8")
        start = readme.index("暂存族（会发布")
        end = readme.index("直接把", start)
        named = set(re.findall(r"fig_[a-z0-9_]+", readme[start:end]))
        self.assertEqual(named, set(MODULES),
                         f"README names {sorted(named - set(MODULES))} extra, "
                         f"misses {sorted(set(MODULES) - named)}")


if __name__ == "__main__":
    unittest.main()
