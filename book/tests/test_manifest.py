import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from book import manifest as m


class ManifestTest(unittest.TestCase):
    def setUp(self):
        self.rows = m.load_toc()
        self.manifest = m.build_manifest(self.rows)

    def test_counts(self):
        self.assertEqual([p["id"] for p in self.manifest["parts"]], [f"v{i}" for i in range(8)])
        chapters = [c for p in self.manifest["parts"] for c in p["chapters"]]
        self.assertEqual(len(chapters), 46)
        self.assertEqual(len(self.manifest["appendices"]), 6)

    def test_chapter_ids_sequential(self):
        chapters = [c["id"] for p in self.manifest["parts"] for c in p["chapters"]]
        self.assertEqual(chapters, [f"ch{i:02d}" for i in range(1, 47)])

    def test_files_match_volume_dirs(self):
        for part in self.manifest["parts"]:
            prefix = m.VOL_DIR[part["id"]]
            for chapter in part["chapters"]:
                self.assertTrue(chapter["file"].startswith(prefix), chapter)
        for appendix in self.manifest["appendices"]:
            self.assertTrue(appendix["file"].startswith("appendix/"), appendix)

    def test_platforms_valid(self):
        for part in self.manifest["parts"]:
            for chapter in part["chapters"]:
                self.assertTrue(chapter["platforms"])
                self.assertLessEqual(set(chapter["platforms"]), m.ALLOWED_PLATFORMS)

    def test_status_planned(self):
        for part in self.manifest["parts"]:
            for chapter in part["chapters"]:
                self.assertEqual(chapter["status"], "planned")

    def test_committed_manifest_current(self):
        self.assertEqual(m.OUT.read_text(encoding="utf-8"), m.dumps(self.manifest))


if __name__ == "__main__":
    unittest.main()
