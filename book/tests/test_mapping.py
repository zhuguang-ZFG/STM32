import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from book import manifest as mf
from book import mapping as mp


class MappingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = mp.load_rows()
        cls.manifest = mf.build_manifest(mf.load_toc())

    def test_total_rows(self):
        self.assertEqual(len(self.rows), 141)

    def test_coverage_clean(self):
        self.assertEqual(mp.validate(self.rows, self.manifest), [])

    def test_duplicate_source_detected(self):
        rows = self.rows + [dict(self.rows[0])]
        errors = mp.validate(rows, self.manifest)
        self.assertTrue(any("duplicate source" in error for error in errors), errors)

    def test_unknown_target_detected(self):
        rows = [dict(row) for row in self.rows]
        rows[0] = {**rows[0], "targets": ["ch99"]}
        errors = mp.validate(rows, self.manifest)
        self.assertTrue(any("unknown target" in error for error in errors), errors)

    def test_every_target_has_source(self):
        used = {target for row in self.rows for target in row["targets"]}
        manifest = self.manifest
        all_ids = {chapter["id"] for part in manifest["parts"] for chapter in part["chapters"]}
        all_ids |= {appendix["id"] for appendix in manifest["appendices"]}
        self.assertEqual(all_ids - used, set())

    def test_committed_mapping_current(self):
        self.assertEqual(mp.MAPPING_JSON.read_text(encoding="utf-8"), mp.dumps(mp.build(self.rows)))


if __name__ == "__main__":
    unittest.main()
