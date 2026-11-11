"""Glyph coverage per font role: rare characters render or the build stops naming chars and fonts."""
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from PIL import Image
import fonts
from video_job import FilmBuilder, inspect_environment

RARE = '犇羴鱻龘囧槑'


def fake_font(path, characters):
    """A tiny real TrueType font whose cmap holds only the given characters."""
    names = ['.notdef'] + [f'uni{ord(character):04X}' for character in characters]
    def square():
        pen = TTGlyphPen(None)
        pen.moveTo((50, 0)); pen.lineTo((50, 600)); pen.lineTo((550, 600)); pen.lineTo((550, 0)); pen.closePath()
        return pen.glyph()
    builder = FontBuilder(1000, isTTF=True)
    builder.setupGlyphOrder(names)
    builder.setupCharacterMap({ord(character): f'uni{ord(character):04X}' for character in characters})
    builder.setupGlyf({name: square() for name in names})
    builder.setupHorizontalMetrics({name: (600, 0) for name in names})
    builder.setupHorizontalHeader(ascent=800, descent=-200)
    builder.setupNameTable({'familyName': 'Coverage Fixture', 'styleName': 'Regular'})
    builder.setupOS2(sTypoAscender=800, sTypoDescender=-200, usWinAscent=800, usWinDescent=200)
    builder.setupPost()
    builder.save(str(path))
    return str(path)


class FontCoverageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.basic = fake_font(self.root/'basic.ttf', '中文测试。')
        self.full = fake_font(self.root/'full.ttf', '中文测试。' + RARE)

    def tearDown(self):
        self.temporary.cleanup()

    def test_missing_glyph_names_characters_and_every_font_tried(self):
        with patch('fonts.candidates', return_value=[(self.basic, 0)]):
            with self.assertRaises(ValueError) as failure:
                fonts.select('caption', '测试犇羴')
        message = str(failure.exception)
        self.assertIn('犇(U+7287)', message)
        self.assertIn('羴(U+7FB4)', message)
        self.assertIn(self.basic, message)

    def test_role_chain_falls_back_to_the_first_covering_font(self):
        with patch('fonts.candidates', return_value=[(self.basic, 0), (self.full, 0)]):
            self.assertEqual(fonts.select('handwriting', '测试'), (self.basic, 0))
            self.assertEqual(fonts.select('handwriting', '测试' + RARE), (self.full, 0))

    def test_explicit_font_is_never_silently_replaced(self):
        with patch('fonts.candidates', return_value=[(self.full, 0)]):
            with self.assertRaisesRegex(ValueError, '龘'):
                fonts.select('handwriting', RARE, {'path': self.basic})

    def test_every_role_collects_the_text_it_will_render(self):
        manifest = {'pages': [{'beats': [{'text': '旁白囧', 'actions': [{'type': 'text', 'text': '标题犇'}, {'type': 'marker'}]}],
                               'visual_groups': [{'actions': [{'type': 'text', 'text': '跨句鱻'}]}]}],
                    'hand': {'pen_text': '笔杆槑'}, 'watermark': {'text': '水印龘'}}
        self.assertEqual(fonts.role_texts(manifest), {'handwriting': '标题犇跨句鱻笔杆槑', 'caption': '旁白囧', 'watermark': '水印龘'})
        manifest['watermark']['enabled'] = False
        self.assertEqual(fonts.role_texts(manifest)['watermark'], '')

    def test_build_stops_before_rendering_when_a_caption_glyph_is_missing(self):
        Image.new('RGB', (640, 360), 'white').save(self.root/'cover.png')
        manifest = {'version': 1, 'runtime_fixture': True, 'title': '覆盖', 'canvas': {'width': 640, 'height': 360, 'fps': 24},
                    'cover': {'source': 'cover.png', 'seconds': 1}, 'font': {'path': self.full}, 'captions': {'font': {'path': self.basic}},
                    'pages': [{'beats': [{'id': 'a', 'text': '测试犇。', 'audio': 'a.wav', 'actions': [{'type': 'text', 'text': '中文', 'x': 10, 'y': 10}]}]}]}
        (self.root/'job.json').write_text(json.dumps(manifest, ensure_ascii=False))
        with self.assertRaises(ValueError) as failure:
            FilmBuilder(self.root)
        self.assertIn('caption', str(failure.exception))
        self.assertIn('犇(U+7287)', str(failure.exception))
        self.assertIn(self.basic, str(failure.exception))
        report = inspect_environment(self.root)
        self.assertFalse(report['ready'])
        self.assertIn('犇', report['font_error'])
        self.assertTrue(any(line.startswith('Fonts:') for line in report['fixes']))
        manifest['captions']['font']['path'] = self.full
        (self.root/'job.json').write_text(json.dumps(manifest, ensure_ascii=False))
        report = inspect_environment(self.root)  # narration missing must not hide that rendering itself is possible
        self.assertEqual(report['missing_inputs'], ['a.wav'])
        self.assertEqual(report['capabilities']['render'], all(report['tools'].values()))
        self.assertFalse(report['capabilities']['narration_ready'])
        self.assertFalse(report['ready'])
        self.assertTrue(any(line.startswith('Narration:') for line in report['fixes']))

    def test_rare_characters_resolve_with_installed_system_fonts(self):
        manifest = {'pages': [{'beats': [{'text': RARE, 'actions': [{'type': 'text', 'text': RARE}]}]}],
                    'hand': {'pen_text': RARE}, 'watermark': {'text': RARE}}
        try:
            report = fonts.check_coverage(manifest)
        except (ValueError, FileNotFoundError) as error:
            self.skipTest('No installed Chinese font covers the rare characters: ' + str(error).splitlines()[0])
        for role in ('handwriting', 'caption', 'watermark'):
            path, index = report[role]['path'], report[role]['index']
            self.assertTrue(all(ord(character) in fonts.codepoints(path, index) for character in RARE), role)
        self.assertEqual(manifest['captions']['font']['path'], report['caption']['path'])
        self.assertEqual(manifest['font']['path'], report['handwriting']['path'])


if __name__ == '__main__':
    unittest.main()
