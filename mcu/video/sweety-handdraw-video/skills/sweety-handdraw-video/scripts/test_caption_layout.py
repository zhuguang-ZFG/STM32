"""Caption layout: word-aware breaking, kinsoku, balance, highlights, platform safe zone and cue splitting."""
from pathlib import Path
import re
import tempfile
import unittest
import numpy as np
from PIL import Image, ImageColor
import caption_assets
from caption_assets import (build_caption, caption_char_limit, caption_lines, caption_position, caption_safe_violations,
                            cue_char_limit, cue_pieces, display_line, display_units, number_spans, shown_width, split_text)
from align import align_master, caption_texts, spoken

REAL = ['我在X上专注发AI和Grok Bot的硬核技术内容和行业思考。', '我完成了从大厂开发到重构商业逻辑的转身，']
SAMPLES = REAL + [
    '今天是二零二六年十月二十六日，星期一。深秋，', '天涯上有一篇神帖，给出了四条铁律。而我这大半年，',
    '我用Claude Code结合OpenAI的API，', '那种感觉怎么形容呢？就像武侠小说里，', '速度快了3.5倍，2026年发布，占了54%。',
    '一个卡在瓶颈期多年的无名小卒，突然被高人一指，', '标题就叫《二零二七年以后，你要活成这个样子》。',
    '辛辛苦苦干满一年，却被裁员，一分钱绩效都没拿到。', '这周末，我和朋友就要开启第一场线下培训，讲X和Grok Bot。']
ATOMS = ['Grok Bot', 'Claude Code', 'OpenAI', 'API', '3.5倍', '2026年', '54%', '二零二六年十月二十六日', '二零二七年']


def breaks(pieces):
    positions, cursor = [], 0
    for piece in pieces[:-1]:
        cursor += len(piece)
        positions.append(cursor)
    return positions


def old_caption_texts(text, limit=24):
    breaks_ = '。！？!?…；;，,、：:'
    pieces = []
    for clause in re.findall('[^' + breaks_ + ']+[' + breaks_ + ']*|[' + breaks_ + ']+', text):
        if pieces and (not spoken(clause) or len(pieces[-1]) + len(clause) <= limit):
            pieces[-1] += clause
        else:
            pieces.append(clause)
    return pieces


class CaptionLayoutTests(unittest.TestCase):
    def setUp(self):
        self.jieba, caption_assets.USE_JIEBA = caption_assets.USE_JIEBA, False  # the built-in rules must stand alone
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)

    def tearDown(self):
        caption_assets.USE_JIEBA = self.jieba
        self.directory.cleanup()

    def test_the_two_real_sentences_break_between_words(self):
        self.assertEqual(caption_lines(REAL[0], display_units, 15, 2), ['我在X上专注发AI和Grok Bot的', '硬核技术内容和行业思考'])
        self.assertEqual(caption_lines(REAL[1], display_units, 14, 2), ['我完成了从大厂开发', '到重构商业逻辑的转身'])
        # Rendered on a vertical canvas with the default font and size.
        first = build_caption(self.root, 'a', REAL[0], {}, 1080, 1920)
        second = build_caption(self.root, 'b', REAL[1], {}, 1080, 1920)
        self.assertEqual(len(first['lines']), 2)
        self.assertIn('Grok Bot', first['lines'][0] + first['lines'][1])
        self.assertTrue(first['lines'][1].startswith('硬核') or first['lines'][1].startswith('和'), first['lines'])
        self.assertEqual(second['lines'], ['我完成了从大厂开发', '到重构商业逻辑的转身'])
        self.assertEqual((first['text'], second['text']), tuple(REAL))  # cue text is untouched; only the display drops ，。

    def test_no_orphan_punctuation_and_no_dangling_open_bracket(self):
        for text in SAMPLES:
            for limit in (6, 8, 10, 12, 14):
                pieces = split_text(text, limit, display_units)
                self.assertEqual(''.join(pieces), text)
                for piece in pieces:
                    self.assertNotIn(piece.lstrip()[:1], caption_assets.NO_START, (text, limit, pieces))
                    self.assertNotIn(piece.rstrip()[-1:], caption_assets.NO_END, (text, limit, pieces))
                    self.assertTrue(re.search(r'\w', piece), (text, limit, pieces))
                for line in (display_line(piece) for piece in pieces):
                    self.assertNotIn(line[-1:], set('，。、；：,;:'))
        self.assertEqual(display_line('那种感觉怎么形容呢？'), '那种感觉怎么形容呢？')
        self.assertEqual(display_line('转身，'), '转身')
        self.assertEqual(display_line('他说：“好。”'), '他说：“好”')
        self.assertEqual(display_line('真的……'), '真的……')
        self.assertEqual(display_line('转身，', strip=False), '转身，')
        self.assertEqual(display_line('真的，太牛了。', strip='all'), '真的 太牛了')

    def test_no_split_inside_latin_words_numbers_or_keywords(self):
        for text in SAMPLES:
            for limit in (6, 7, 9, 11, 13):  # (an opening bracket travels with the word after it)
                cuts = breaks(split_text(text, limit, display_units))
                for atom in (atom for atom in ATOMS if shown_width(atom) <= limit):  # wider ones must break somewhere
                    for match in re.finditer(re.escape(atom), text):
                        self.assertFalse([cut for cut in cuts if match.start() < cut < match.end()], (text, limit, atom))
        text = '我们今天聊聊硬核技术内容的未来'
        cuts = breaks(split_text(text, 8, display_units, keywords=['硬核技术内容']))
        self.assertFalse([cut for cut in cuts if 6 < cut < 12], cuts)
        # A Latin run wider than the line still breaks rather than overflowing.
        self.assertTrue(all(shown_width(piece) <= 4 for piece in split_text('Supercalifragilistic', 4, display_units)))

    def test_particles_never_open_a_line_and_two_lines_are_balanced(self):
        for text in SAMPLES:
            lines = caption_lines(text, display_units, max(8., shown_width(text) / 2 + 2.5), 2)
            self.assertIsNotNone(lines, text)
            self.assertNotIn(lines[-1][:1], set('的了着过地得们吗呢吧'), lines)
            if len(lines) == 2:
                widths = [shown_width(line) for line in lines]
                self.assertLessEqual(abs(widths[0] - widths[1]), 6, lines)
        self.assertEqual(caption_lines('他们效率比你高，产出比你多，成长比你快。', display_units, 13, 2),
                         ['他们效率比你高', '产出比你多，成长比你快'])

    def test_english_wraps_at_spaces_and_keeps_question_marks(self):
        text = 'I focus on AI and Grok Bot, sharing hardcore technical content and industry thinking.'
        pieces = split_text(text, 14, display_units)
        self.assertEqual(''.join(pieces), text)
        for cut in breaks(pieces):
            self.assertTrue(text[cut - 1] == ' ', pieces)
        self.assertEqual(display_line(pieces[-1]), pieces[-1].strip()[:-1])  # the closing period is dropped
        self.assertEqual(display_line('Why does it matter?'), 'Why does it matter?')
        self.assertEqual(display_line('Built in the U.S.'), 'Built in the U.S.')
        metadata = build_caption(self.root, 'english', 'Why does the caption sit above the buttons?', {}, 1080, 1920)
        words = 'Why does the caption sit above the buttons?'.split()
        self.assertEqual(' '.join(metadata['lines']).split(), words)
        cues = cue_pieces(text, 14)
        self.assertEqual(''.join(cues), text)
        self.assertTrue(all(cue.endswith(' ') or cue is cues[-1] for cue in cues), cues)

    def test_keyword_and_number_highlights_keep_outline_and_baseline(self):
        text = '我在X上专注发AI和Grok Bot的内容，2026年'
        plain = build_caption(self.root, 'plain', text, {}, 1080, 1920)
        marked = build_caption(self.root, 'marked', text, {'keywords': ['AI'], 'highlight_numbers': True}, 1080, 1920,
                               keywords=['Grok Bot'])
        self.assertEqual(plain['lines'], marked['lines'])
        self.assertEqual([item['text'] for item in marked['highlights']], ['AI', 'Grok Bot', '2026年'])
        self.assertEqual(plain['highlights'], [])
        before = np.array(Image.open(self.root / 'plain.png'))
        after = np.array(Image.open(self.root / 'marked.png'))
        self.assertEqual(before.shape, after.shape)
        # Same outline, same glyph positions: the alpha (shape) is unchanged, only fills recolor.
        self.assertLessEqual(np.abs(before[:, :, 3].astype(int) - after[:, :, 3].astype(int)).max(), 2)
        yellow = np.array(ImageColor.getrgb(caption_assets.HIGHLIGHT_COLOR))
        self.assertTrue((np.abs(after[:, :, :3].astype(int) - yellow).max(axis=2) < 8).sum() > 200)
        self.assertFalse((np.abs(before[:, :, :3].astype(int) - yellow).max(axis=2) < 8).any())
        sample = '拿到七十万年薪，有一篇神帖，二零二六年十月二十六日，3.5倍'
        self.assertEqual([sample[start:end] for start, end in number_spans(sample)],
                         ['七十万', '二零二六年十月二十六日', '3.5倍'])

    def test_vertical_captions_clear_the_platform_ui_and_landscape_stays_low(self):
        metadata = build_caption(self.root, 'v', REAL[1], {}, 1080, 1920)
        x, y = caption_position(metadata, {}, 1080, 1920)
        self.assertEqual(x, (1080 - metadata['width']) // 2)
        self.assertLessEqual(y + metadata['height'], 1920 - 384)
        self.assertGreater(y + metadata['height'], 1920 * .7)
        self.assertEqual(caption_safe_violations((x, y, metadata['width'], metadata['height']), 1080, 1920), [])
        self.assertEqual(metadata['font_size'], 52)
        self.assertEqual(metadata['stroke_width'], 4)
        # The last film's hand-set margin still wins, and is reported as covered by the bottom UI.
        x, y = caption_position(metadata, {'bottom_margin': 250}, 1080, 1920)
        self.assertEqual(y, 1920 - 250 - metadata['height'])
        problems = caption_safe_violations((x, y, metadata['width'], metadata['height']), 1080, 1920)
        self.assertTrue(problems and 'bottom platform UI' in problems[0])
        self.assertTrue(any('right button rail' in problem for problem in caption_safe_violations((60, 1400, 980, 80), 1080, 1920)))
        landscape = build_caption(self.root, 'h', REAL[1], {}, 1920, 1080)
        x, y = caption_position(landscape, {}, 1920, 1080)
        self.assertEqual(y, 1080 - landscape['height'] - round(1080 * .04))
        self.assertEqual(caption_safe_violations((x, y, landscape['width'], landscape['height']), 1920, 1080), [])
        self.assertEqual(caption_safe_violations((x, 1070, landscape['width'], landscape['height']), 1920, 1080), ['outside the canvas'])

    def test_cues_fit_one_vertical_line_and_join_back_exactly(self):
        self.assertEqual((caption_char_limit({}, 1080, 1920), caption_char_limit({}, 1920, 1080)), (14.5, 24))
        self.assertEqual(cue_char_limit({'pages': []}), caption_char_limit({}, 1280, 1920))   # 2:3 default canvas
        self.assertEqual(cue_char_limit({'canvas': {'aspect_ratio': '9:16'}}), 14.5)
        self.assertEqual(cue_char_limit({'canvas': {'aspect_ratio': '16:9'}}), 24)
        self.assertEqual(cue_char_limit({'canvas': {'width': 1080, 'height': 1920}, 'captions': {'max_chars': 16}}), 16)
        with self.assertRaises(ValueError):
            caption_char_limit({'max_chars': 2}, 1080, 1920)
        text = ('二零二六年，我完成了从大厂开发到重构商业逻辑的转身，也找回了写代码、做产品的纯粹快乐，哪怕是戴着FDE的帽子。'
                '我在X上专注发AI和Grok Bot的硬核技术内容和行业思考。')
        limit = cue_char_limit({'canvas': {'aspect_ratio': '9:16'}})
        cues = caption_texts(text, limit, split_long=True)
        self.assertEqual(''.join(cues), text)
        self.assertEqual(cues, cue_pieces(text, limit))
        self.assertIn('我在X上专注发AI和Grok Bot的', cues)
        self.assertIn('我完成了从大厂开发', cues)
        self.assertIn('到重构商业逻辑的转身，', cues)
        for cue in cues:
            self.assertLessEqual(shown_width(cue), limit, cue)
            self.assertNotIn(cue[:1], caption_assets.NO_START)
            lines = build_caption(self.root, 'cue', cue, {}, 1080, 1920)['lines']
            self.assertEqual(len(lines), 1, cue)
        for atom in ('Grok Bot', 'FDE'):
            self.assertTrue(any(atom in cue for cue in cues), cues)

    def test_whole_master_alignment_cuts_cues_for_the_canvas_from_character_times(self):
        beats = [{'id': 'a', 'text': REAL[1] + '也找回了写代码、做产品的纯粹快乐。'}, {'id': 'b', 'text': REAL[0]}]
        characters = spoken(''.join(beat['text'] for beat in beats))
        words = [{'text': character, 'start': index * .2, 'end': index * .2 + .15} for index, character in enumerate(characters)]
        source = self.root / 'master.wav'
        source.write_bytes(b'audio')
        old = align_master(source, beats, words, self.root / 'old.json', 'hash')
        new = align_master(source, beats, words, self.root / 'new.json', 'hash', cue_char_limit({}))
        self.assertEqual([cue['text'] for cue in old['beats'][1]['caption_cues']], [REAL[0]])
        for beat in new['beats']:
            cues = beat['caption_cues']
            self.assertEqual(''.join(cue['text'] for cue in cues), beat['text'])
            self.assertTrue(all(left['end'] <= right['start'] for left, right in zip(cues, cues[1:])))
            self.assertTrue(all(shown_width(cue['text']) <= 14.5 for cue in cues))
        self.assertEqual([cue['text'] for cue in new['beats'][0]['caption_cues']][:2], ['我完成了从大厂开发', '到重构商业逻辑的转身，'])
        # The split falls on the character times: 我完成了从大厂开发 is nine characters at 0.2 s each.
        self.assertAlmostEqual(new['beats'][0]['caption_cues'][1]['start'], 1.8)

    def test_old_default_calls_still_behave(self):
        for text in SAMPLES + ['好。这就是全部内容。', '第一页先讲一个故事，故事里有一条蛇。']:
            self.assertEqual(caption_texts(text), old_caption_texts(text))
            self.assertEqual(caption_texts(text, 1), old_caption_texts(text, 1))
        metadata = build_caption(self.root, 'old', '学会放过自己。', {}, 1920, 1080)
        self.assertEqual((metadata['font_size'], metadata['stroke_width'], metadata['stroke_color']), (38, 2, '#000000'))
        self.assertEqual(metadata['lines'], ['学会放过自己'])
        kept = build_caption(self.root, 'kept', '学会放过自己。', {'strip_punctuation': False}, 1920, 1080)
        self.assertEqual(kept['lines'], ['学会放过自己。'])
        explicit = {'font_size': 46, 'stroke_color': '#1E2733', 'stroke_width': 3, 'bottom_margin': 250, 'max_width_ratio': .86, 'max_lines': 2}
        for text in SAMPLES:  # every cue of the last film's layout still renders
            build_caption(self.root, 'film', text, explicit, 1080, 1920)
        with self.assertRaisesRegex(ValueError, 'Split long subtitles'):
            build_caption(self.root, 'long', '这是一句非常非常长的字幕' * 8, {}, 1920, 1080)


if __name__ == '__main__':
    unittest.main()
