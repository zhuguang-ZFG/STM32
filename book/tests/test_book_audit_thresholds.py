import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / ".temp" / "audit_book.current.json"

# Baseline captured 2026-11-26 from tools/audit_book.py --format json.
# Ceilings: values may improve (deficit/gap/below_target down; anchors/photos up), never regress.
BASELINE = {
    "summary_zh": {"pdf_visual_anchors": 345, "chapters_below_target": 21, "chapters_with_photos": 0},
    "chapters": {
        "ch06": {"visual_anchor_deficit": 3, "max_visual_gap_chars": 5826},
        "ch11": {"visual_anchor_deficit": 5, "max_visual_gap_chars": 4829},
        "ch26": {"visual_anchor_deficit": 3, "max_visual_gap_chars": 5313},
        "ch46": {"visual_anchor_deficit": 4, "max_visual_gap_chars": 8846},
        "apD": {"visual_anchor_deficit": 5, "max_visual_gap_chars": 5954},
    },
}


class BookAuditThresholdTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not AUDIT.exists():
            raise unittest.SkipTest(
                "missing .temp/audit_book.current.json; run: python tools/audit_book.py --format json --write .temp/audit_book.current.json"
            )
        cls.data = json.loads(AUDIT.read_text(encoding="utf-8"))
        cls.summary_zh = cls.data["summary"]["zh"]
        cls.by_id = {c["id"]: c["zh"] for c in cls.data["chapters"]}

    def test_global_metrics_do_not_regress(self):
        base = BASELINE["summary_zh"]
        self.assertGreaterEqual(self.summary_zh["pdf_visual_anchors"], base["pdf_visual_anchors"])
        self.assertLessEqual(self.summary_zh["chapters_below_target"], base["chapters_below_target"])
        self.assertGreaterEqual(self.summary_zh["chapters_with_photos"], base["chapters_with_photos"])

    def test_target_chapters_do_not_regress(self):
        for cid, base in BASELINE["chapters"].items():
            self.assertIn(cid, self.by_id, cid)
            got = self.by_id[cid]
            self.assertLessEqual(got["visual_anchor_deficit"], base["visual_anchor_deficit"], cid)
            self.assertLessEqual(got["max_visual_gap_chars"], base["max_visual_gap_chars"], cid)
