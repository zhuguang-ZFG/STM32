"""Delivery receipt: playback and listening are reported on their own, and a user's rejection voids the receipt."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
from video_verifier import file_hash, finalize_job, reject_job

CATEGORIES = ('content', 'visual', 'motion', 'audio', 'privacy')


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = root = Path(self.temporary.name)
        for folder in ('work', 'outputs'):
            (root / folder).mkdir()
        (root / 'job.json').write_text('{}')
        (root / 'work/timeline.json').write_text(json.dumps({'manifest_sha256': file_hash(root / 'job.json')}))
        self.render(b'first film')
        self.fingerprint = mock.patch('video_verifier.build_fingerprint', return_value='inputs')
        self.fingerprint.start()

    def tearDown(self):
        self.fingerprint.stop()
        self.temporary.cleanup()

    def render(self, content, playback='pass', listening='pass'):
        (self.root / 'outputs/film.mp4').write_bytes(content)
        video = file_hash(self.root / 'outputs/film.mp4')
        (self.root / 'work/verification.json').write_text(json.dumps({
            'status': 'engineering_passed_review_required', 'audio_gate': {'status': 'PASS'}, 'caption_sync': {'status': 'PASS'},
            'video_sha256': video, 'build_fingerprint': 'inputs', 'duration_seconds': 12.}))
        path = self.root / 'review.json'
        review = json.loads(path.read_text()) if path.exists() else {}
        review.update({'video_sha256': video, **{category: {'status': 'pass', 'evidence': 'checked'} for category in CATEGORIES},
                       'continuous_playback': {'status': playback, 'evidence': 'played start to end in QuickTime' if playback else ''},
                       'listening': {'status': listening, 'evidence': 'no audio output on this host' if listening == 'not_done' else 'listened'}})
        path.write_text(json.dumps(review, ensure_ascii=False))

    def receipt(self):
        return json.loads((self.root / 'outputs/verification.json').read_text()), (self.root / 'outputs/verification.txt').read_text()

    def test_playback_and_listening_must_be_recorded_and_not_done_stays_open(self):
        self.render(b'first film', playback='not_checked')
        with self.assertRaisesRegex(ValueError, 'continuous_playback'):
            finalize_job(self.root)
        self.render(b'first film', listening='fail')
        with self.assertRaisesRegex(ValueError, 'listening'):
            finalize_job(self.root)
        self.render(b'first film', listening='not_done')
        finalize_job(self.root)
        receipt, text = self.receipt()
        self.assertEqual(receipt['status'], 'delivery_review_completed_with_open_checks')
        self.assertEqual(receipt['open_checks'], ['listening'])
        self.assertIn('连续播放：通过', text)
        self.assertIn('听音：未完成，no audio output on this host', text)

    def test_user_rejection_voids_the_receipt_until_a_new_render(self):
        finalize_job(self.root)
        self.assertEqual(self.receipt()[0]['status'], 'delivery_review_completed')
        with self.assertRaisesRegex(ValueError, 'what the user rejected'):
            reject_job(self.root, ' ')
        reject_job(self.root, '人物不像在画，像揭开')
        receipt, text = self.receipt()
        self.assertEqual(receipt['status'], 'rejected_by_user')
        self.assertIn('用户已拒绝，需要返工', text)
        with self.assertRaisesRegex(ValueError, 'rejected this video'):
            finalize_job(self.root)
        self.render(b'reworked film')
        finalize_job(self.root)
        receipt, _ = self.receipt()
        self.assertEqual(receipt['status'], 'delivery_review_completed')
        self.assertEqual(len(receipt['review']['rejections']), 1)


if __name__ == '__main__':
    unittest.main()
