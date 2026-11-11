"""Stroke-order handwriting: data order, left-to-right glyphs, timing floors and whole-line fallback."""
from pathlib import Path
import json
import os
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from PIL import Image
import handwriting
import stroke_assets
from drawing_contract import validate_strokes
from video_job import find_font
from video_verifier import match_reveal_to_tip


class HandwritingTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary.name)
        font, index = find_font({})
        stroke_assets.configure_assets(self.directory, font, index, 30)

    def tearDown(self):
        self.temporary.cleanup()

    def build(self, name, text, size=80, seconds=None):
        metadata = stroke_assets.build_text(name, text, size, seconds=seconds)
        maps = np.load(self.directory / f'{name}.npz')
        alpha = np.array(Image.open(self.directory / f'{name}.png'))[:, :, 3]
        return metadata, maps, alpha

    def test_strokes_follow_canonical_order_and_direction(self):
        metadata, maps, alpha = self.build('ten', '十')
        self.assertEqual(metadata['handwriting']['mode'], 'stroke_order')
        ink = [segment for segment in metadata['segments'] if segment['kind'] == 'ink']
        self.assertEqual(len(ink), 2)
        first, second = (np.array(segment['points']) for segment in ink)
        self.assertGreater(first[-1, 0] - first[0, 0], 3 * abs(first[-1, 1] - first[0, 1]))  # 横 left to right
        self.assertGreater(second[-1, 1] - second[0, 1], 3 * abs(second[-1, 0] - second[0, 0]))  # 竖 top to bottom
        self.assertTrue(all(segment['profile'] == 'minjerk' for segment in ink))
        self.assertTrue(validate_strokes(metadata))
        distances, _ = match_reveal_to_tip(metadata, maps['reveal'], alpha > 0, {'ink'})
        self.assertLess(distances.max(), .15 * 80)

    def test_characters_are_written_left_to_right_in_isolation(self):
        metadata, maps, alpha = self.build('line', '从一颗葡萄，ok')
        characters = metadata['characters']
        self.assertEqual([character['character'] for character in characters], list('从一颗葡萄，ok'))
        for left, right in zip(characters, characters[1:]):
            self.assertLessEqual(left['end'], right['start'] + 1e-9)
        centres = []
        for character in characters:
            mask = (maps['owners'] == character['index']) & (alpha > 0)
            self.assertTrue(mask.any(), character['character'])
            times = maps['reveal'][mask]
            self.assertGreaterEqual(times.min() + 1e-7, character['start'])
            self.assertLessEqual(times.max(), character['end'] + 1e-7)
            centres.append(np.nonzero(mask)[1].mean())
        self.assertEqual(centres, sorted(centres))
        self.assertTrue(np.isfinite(maps['reveal'][alpha > 0]).all())

    def test_missing_glyph_draws_the_whole_line_with_the_font(self):
        original = handwriting.character_data
        with patch.object(handwriting, 'character_data', lambda character: None if character == '一' else original(character)):
            metadata, maps, alpha = self.build('fallback', '从一开始')
        self.assertEqual(metadata['handwriting'], {'mode': 'font', 'reason': 'missing stroke data: 一'})
        distances, _ = match_reveal_to_tip(metadata, maps['reveal'], alpha > 0, {'ink'})
        self.assertLess(distances.max(), 9)
        self.assertTrue((maps['owners'][alpha > 0] >= 0).all())

    def test_lookup_uses_cache_and_never_raises_offline(self):
        with tempfile.TemporaryDirectory() as cache, patch.dict(os.environ, {'HANDDRAW_ASSET_CACHE': cache}), \
                patch.object(handwriting, '_online', False):
            self.assertIsNone(handwriting.character_data('鬱'))  # outside GB2312, nothing cached, offline
            path = handwriting.cache_path('鬱')
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps({'strokes': ['M 100 800 L 900 800 L 900 760 L 100 760 Z'], 'medians': [[[110, 780], [890, 780]]]}))
            self.assertEqual(len(handwriting.character_data('鬱')[0]), 1)
        self.assertIsNotNone(handwriting.character_data('永'))  # bundled GB2312 data needs no network

    def test_timing_keeps_visible_strokes_and_reports_short_budgets(self):
        metadata = stroke_assets.build_text('slow', '一二', 80, seconds=6.)
        report = metadata['handwriting']
        ink = [segment for segment in metadata['segments'] if segment['kind'] == 'ink']
        self.assertFalse(report['compressed'])
        self.assertGreaterEqual(min((segment['end'] - segment['start']) * 6 for segment in ink), 2 / 30 - 1e-9)
        self.assertLessEqual(metadata['segments'][-1]['end'], 1 + 1e-9)
        hurried = stroke_assets.build_text('fast', '一二', 80, seconds=.1)
        self.assertTrue(hurried['handwriting']['compressed'])
        self.assertTrue(validate_strokes(hurried))
        self.assertAlmostEqual(hurried['segments'][-1]['end'], 1., places=6)

    def test_font_strokes_run_left_to_right_or_top_down(self):
        self.assertEqual(handwriting.orient(np.array([[9., 5.], [1., 6.]]))[0].tolist(), [1., 6.])
        self.assertEqual(handwriting.orient(np.array([[3., 9.], [4., 1.]]))[0].tolist(), [4., 1.])
        metadata = stroke_assets.build_text('dash', '-', 80)
        stroke = np.array(next(segment for segment in metadata['segments'] if segment['kind'] == 'ink')['points'])
        self.assertLess(stroke[0, 0], stroke[-1, 0])


if __name__ == '__main__':
    unittest.main()
