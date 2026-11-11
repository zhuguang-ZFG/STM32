"""Catch small artwork, white padding and declarations that merely rename empty layouts."""
from pathlib import Path
import tempfile
import unittest
from PIL import Image, ImageDraw
from composition import check_presentation_match, measure_pages, validate_composition, validate_boards, validate_board_pages, validate_board_timing


def dense_shot():
    return {'id': 'comparison', 'beats': ['a'], 'visuals': [{'id': 'scene', 'kind': 'illustration'}],
            'composition': {'layout': 'scene', 'focus': 'scene', 'context': [
                {'visual': 'scene', 'element': 'full basket', 'explains': 'shows the accumulated cost'},
                {'visual': 'scene', 'element': 'empty basket', 'explains': 'shows the alternative outcome'}]}}


class CompositionPlanTests(unittest.TestCase):
    def test_dense_page_can_have_one_scene_with_meaningful_support(self):
        self.assertEqual(validate_composition(dense_shot(), 'dense_infographic'), [])

    def test_missing_context_repeated_decoration_and_unknown_visuals_fail(self):
        self.assertTrue(validate_composition({'id': 'empty'}, 'dense_infographic'))
        for change in ('unknown', 'duplicate', 'no-purpose'):
            with self.subTest(change=change):
                shot = dense_shot()
                context = shot['composition']['context']
                if change == 'unknown':
                    context[0]['visual'] = 'unplanned'
                elif change == 'duplicate':
                    context[1] = dict(context[0])
                else:
                    context[0]['explains'] = ' '
                self.assertTrue(validate_composition(shot, 'dense_infographic'))

    def test_picture_book_does_not_need_unrelated_supporting_objects(self):
        self.assertEqual(validate_composition({'id': 'hero'}, 'picture_book'), [])

    def test_design_cannot_claim_dense_while_storyboard_uses_sparse(self):
        with self.assertRaisesRegex(ValueError, 'must match'):
            check_presentation_match({'mode': 'dense_infographic'}, {'presentation': {'mode': 'picture_book', 'reason': 'one subject'}})


class AccumulatingBoardTests(unittest.TestCase):
    def setUp(self):
        self.board = {'presentation': {'mode': 'accumulating_board'}, 'shots': [
            {'id': 'first', 'board': 'lesson', 'beats': ['a'], 'visuals': [{'id': 'v0'}]},
            {'id': 'second', 'board': 'lesson', 'beats': ['b'], 'visuals': [{'id': 'v1'}]}],
            'boards': [{'id': 'lesson', 'purpose': 'explain a comparison', 'regions': [
                {'id': 'left', 'purpose': 'show the cause', 'box': [.05, .1, .45, .8], 'visuals': ['v0']},
                {'id': 'right', 'purpose': 'show the result', 'box': [.55, .1, .95, .8], 'visuals': ['v1']}]}]}

    def test_regions_are_planned_before_images_and_cover_every_visual(self):
        self.assertEqual(validate_boards(self.board, 'accumulating_board'), [])
        self.board['boards'][0]['regions'][1]['visuals'] = ['unplanned']
        self.assertTrue(validate_boards(self.board, 'accumulating_board'))

    def test_same_board_cannot_be_split_into_one_page_per_sentence(self):
        manifest = {'pages': [{'beats': [{'id': 'a'}]}, {'beats': [{'id': 'b'}]}]}
        self.assertIn('one physical page', '\n'.join(validate_board_pages(manifest, self.board)))
        manifest = {'pages': [{'beats': [{'id': 'a'}, {'id': 'b'}]}]}
        self.assertEqual(validate_board_pages(manifest, self.board), [])

    def test_large_artwork_must_fit_the_declared_board_region(self):
        manifest = {'canvas': {'width': 1000, 'height': 1000}, 'pages': [{'beats': [
            {'id': 'a', 'actions': [{'type': 'illustration', 'visual': 'v0', 'x': 50, 'y': 100, 'width': 800, 'height': 200}]}, {'id': 'b'}]}]}
        self.assertIn('does not fit', '\n'.join(validate_board_pages(manifest, self.board)))

    def test_actual_drawing_progresses_in_region_reading_order(self):
        timeline = {'pages': [{'events': [{'visual': 'v0', 'start': 10}, {'visual': 'v1', 'start': 1}]}]}
        self.assertIn('reading order', '\n'.join(validate_board_timing(self.board, timeline)))
        timeline['pages'][0]['events'][0]['start'] = 0
        self.assertEqual(validate_board_timing(self.board, timeline), [])


class VisiblePageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / 'work/assets').mkdir(parents=True)
        self.board = {'presentation': {'mode': 'focus_diagram'}, 'shots': [{'beats': ['a']}]}

    def measure(self, art, x=0, y=0, **options):
        art.save(self.root / 'work/assets/scene.png')
        timeline = {'canvas': {'width': 400, 'height': 600}, 'paper': '#FFFFFF',
                    'assets': {'scene': {'type': 'illustration'}},
                    'pages': [{'beats': [{'id': 'a'}], 'events': [
                        {'asset': 'scene', 'x': x, 'y': y, 'caption': False, 'image': ['scene.png', None]}]}]}
        return measure_pages(self.root, timeline, self.board, **options)

    def test_tiny_picture_does_not_pass_by_requesting_a_large_white_asset(self):
        art = Image.new('RGBA', (400, 600), 'white')
        ImageDraw.Draw(art).rectangle((180, 260, 220, 300), fill='#253020')
        report = self.measure(art)
        self.assertTrue(report['errors'])
        self.assertLess(report['pages'][0]['picture_extent_ratio'], .02)

    def test_adequate_single_hero_passes_without_added_decoration(self):
        report = self.measure(Image.new('RGBA', (280, 380), '#558855'), x=60, y=60)
        self.assertEqual(report['errors'], [])
        self.assertEqual(report['warnings'], [])
        self.assertFalse(report['visual_acceptance_claimed'])

    def test_intentional_negative_space_requires_a_reason(self):
        self.board['shots'][0]['composition'] = {'negative_space_reason': 'A distant figure shows the scale of the desert'}
        report = self.measure(Image.new('RGBA', (20, 20), '#558855'))
        self.assertEqual(report['errors'], [])
        self.assertTrue(report['warnings'])
        self.assertTrue(report['pages'][0]['intentional_negative_space'])

    def test_fixture_is_measured_but_not_rejected_as_a_finished_film(self):
        report = self.measure(Image.new('RGBA', (10, 10), '#558855'), fixture=True)
        self.assertEqual(report['errors'], [])
        self.assertLess(report['pages'][0]['picture_extent_ratio'], .01)

    def test_markers_and_captions_cannot_disguise_a_tiny_picture(self):
        Image.new('RGBA', (10, 10), '#558855').save(self.root / 'work/assets/scene.png')
        timeline = {'canvas': {'width': 400, 'height': 600}, 'assets': {
            'scene': {'type': 'illustration'}, 'marker': {'type': 'marker'}, 'caption': {'type': 'handwritten_text'}},
            'pages': [{'beats': [{'id': 'a'}], 'events': [
                {'asset': 'scene', 'x': 0, 'y': 0, 'image': ['scene.png', None]},
                {'asset': 'marker', 'x': 0, 'y': 0},
                {'asset': 'caption', 'x': 0, 'y': 520, 'caption': True}]}]}
        report = measure_pages(self.root, timeline, self.board)
        self.assertTrue(report['errors'])
        self.assertEqual(report['pages'][0]['picture_uses'], 1)


if __name__ == '__main__':
    unittest.main()
