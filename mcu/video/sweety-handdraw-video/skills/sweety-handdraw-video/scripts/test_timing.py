"""Stage timing: agent marks pair up, tool records accumulate, summary totals are readable."""
from pathlib import Path
import json
import tempfile
import unittest
import timing


class TimingTests(unittest.TestCase):
    def test_marks_tool_records_and_summary(self):
        with tempfile.TemporaryDirectory() as directory:
            job = Path(directory); (job/'job.json').write_text('{}')
            timing.mark(job, 'script', 'start', now=100.)
            with self.assertRaisesRegex(ValueError, 'mark start'):
                timing.mark(job, 'voice', 'end', now=110.)
            timing.mark(job, 'script', 'end', now=400.)
            timing.mark(job, 'voice', 'start', now=400.)
            timing.record(job, 'build', 500., 530.5, 'ok')
            records = json.loads((job/'work/timing.json').read_text())['records']
            self.assertEqual([(item['stage'], item['source'], item.get('seconds')) for item in records],
                             [('script', 'agent', 300.), ('voice', 'agent', None), ('build', 'tool', 30.5)])
            text = timing.summary(job)
            self.assertIn('script', text); self.assertIn('0:05:00', text); self.assertIn('still open', text)
            self.assertIn('0:07:10', text)  # wall clock 100 -> 530.5

    def test_tool_record_needs_a_job(self):
        with tempfile.TemporaryDirectory() as directory:
            timing.record(directory, 'doctor', 0., 1., 'ok')
            self.assertFalse((Path(directory)/'work').exists())


if __name__ == '__main__':
    unittest.main()
