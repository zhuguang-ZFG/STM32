"""Exercise asset download integrity, mirror order and offline behavior without public service access."""
from pathlib import Path
import hashlib
import io
import json
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import URLError
import hosted_assets


class HostedAssetTests(unittest.TestCase):
    def fixture(self, root, content, urls=('https://cdn.example.test/a.png', 'https://release.example.test/a.png')):
        (root/'assets').mkdir()
        key = 'assets/hands/test.png'
        record = {'urls': list(urls), 'bytes': len(content), 'sha256': hashlib.sha256(content).hexdigest()}
        (root/'assets/hosted-manifest.json').write_text(json.dumps({'files': {key: record}}))
        return key

    def test_valid_download_then_offline_cache_and_corruption_rejection(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); content = b'test asset bytes'
            key = self.fixture(root, content)
            with patch.object(hosted_assets, 'PACKAGE', root), patch.dict('os.environ', {'HANDDRAW_ASSET_CACHE':str(root/'cache'),'HANDDRAW_OFFLINE':'0','HANDDRAW_MIRROR':''}):
                self.assertTrue(hosted_assets.asset_available(root/key))
                with patch('hosted_assets.urlopen', return_value=io.BytesIO(content)) as request:
                    target = hosted_assets.resolve_asset(root/key)
                    self.assertEqual(target.read_bytes(), content)
                    request.assert_called_once()
                with patch.dict('os.environ', {'HANDDRAW_OFFLINE':'1'}), patch('hosted_assets.urlopen') as request:
                    self.assertEqual(hosted_assets.resolve_asset(root/key), target)
                    request.assert_not_called()
                    target.write_bytes(b'corrupt')
                    with self.assertRaisesRegex(ValueError, 'Offline'):
                        hosted_assets.resolve_asset(root/key)
                with patch('hosted_assets.urlopen', side_effect=lambda *a, **k: io.BytesIO(b'wrong')):
                    with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch'):
                        hosted_assets.resolve_asset(root/key)

    def test_packaged_copy_is_used_without_network(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); content = b'packaged bytes'
            key = self.fixture(root, content)
            (root/key).parent.mkdir(parents=True); (root/key).write_bytes(content)
            with patch.object(hosted_assets, 'PACKAGE', root), patch('hosted_assets.urlopen') as request:
                self.assertEqual(hosted_assets.resolve_asset(root/key), root/key)
                request.assert_not_called()

    def test_mirror_first_then_ordered_fallback_and_actionable_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); content = b'mirrored bytes'
            key = self.fixture(root, content)
            tried = []
            def flaky(request, timeout):
                tried.append(request.full_url)
                self.assertLessEqual(timeout, 20)
                if 'release' in request.full_url:
                    return io.BytesIO(content)
                raise URLError('blocked')
            environment = {'HANDDRAW_ASSET_CACHE': str(root/'cache'), 'HANDDRAW_OFFLINE': '0', 'HANDDRAW_MIRROR': 'https://gitee.example.test/raw/'}
            with patch.object(hosted_assets, 'PACKAGE', root), patch.dict('os.environ', environment):
                with patch('hosted_assets.urlopen', side_effect=flaky):
                    target = hosted_assets.resolve_asset(root/key)
                self.assertEqual(tried, ['https://gitee.example.test/raw/' + key, 'https://cdn.example.test/a.png', 'https://release.example.test/a.png'])
                self.assertEqual(target.read_bytes(), content)
                target.unlink()
                with patch('hosted_assets.urlopen', side_effect=URLError('offline')):
                    with self.assertRaises(ValueError) as failure:
                        hosted_assets.resolve_asset(root/key)
                message = str(failure.exception)
                for url in tried:
                    self.assertIn(url, message)
                self.assertIn(str(target), message)

    def test_cache_never_accepts_traversal_or_unverified_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'assets').mkdir()
            (root/'assets/hosted-manifest.json').write_text(json.dumps({'files':{'../escape.png':{'urls':['https://example.test/a'],'bytes':1,'sha256':'0'*64}}}))
            with patch.object(hosted_assets,'PACKAGE',root), self.assertRaisesRegex(ValueError,'path'):
                hosted_assets.records()
            (root/'assets/hosted-manifest.json').write_text(json.dumps({'files':{'a.png':{'urls':['http://example.test/a'],'bytes':1,'sha256':'0'*64}}}))
            with patch.object(hosted_assets,'PACKAGE',root), self.assertRaisesRegex(ValueError,'HTTPS'):
                hosted_assets.records()

    def test_real_manifest_matches_packaged_bytes(self):
        for key, record in hosted_assets.records().items():
            self.assertTrue(hosted_assets.checked((hosted_assets.PACKAGE/key).read_bytes(), record), key)
            self.assertTrue(record['urls'][0].startswith('https://cdn.jsdelivr.net/gh/threerocks/sweety-handdraw-video@'), key)

    def test_bundled_style_picker_previews_are_local_files(self):
        from style_choice import prepare_catalog
        with tempfile.TemporaryDirectory() as directory, patch('hosted_assets.urlopen', side_effect=AssertionError('network')):
            catalog = prepare_catalog(directory, hosted_assets.PACKAGE/'dependencies/hand-drawn-styles')
            self.assertEqual(len(catalog['styles']), 21)
            for style in catalog['styles']:
                self.assertEqual(style['preview'], 'previews/' + style['id'] + '.jpg')
                self.assertTrue((Path(directory)/'style'/style['preview']).is_file())


if __name__ == '__main__':
    unittest.main()
