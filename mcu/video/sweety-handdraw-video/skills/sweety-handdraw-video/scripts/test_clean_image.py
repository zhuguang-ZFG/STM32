"""Pure-Python privacy cleanup: metadata gone, pixels untouched, same audit record, source xattrs cleared."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import struct
import sys
import tempfile
import unittest
import zlib
from unittest.mock import patch
from PIL import Image, ImageCms, PngImagePlugin
import clean_image

ICC = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()


def exif():
    data = Image.Exif()
    data[0x010F], data[0x0131], data[0x8298] = 'Canon', 'Generator 1.0', 'Private'
    return data.tobytes()


class CleanImageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def clean(self, path):
        before = Image.open(path); before.load()
        report = clean_image.clean_image(path, self.root / 'audit.json')
        after = Image.open(path); after.load()
        self.assertEqual((before.mode, before.size, before.tobytes()), (after.mode, after.size, after.tobytes()))
        self.assertEqual(json.loads((self.root / 'audit.json').read_text()), report)
        self.assertEqual(set(report), {'file', 'sha256', 'embedded_metadata_empty', 'xattrs_remaining', 'camera_profile_removed', 'note'})
        self.assertEqual(clean_image.embedded_metadata(path), [])
        return report

    def test_png_keeps_only_image_chunks(self):
        path = self.root / 'image.png'
        info = PngImagePlugin.PngInfo(); info.add_text('Software', 'generator'); info.add_itxt('XML:com.adobe.xmp', '<x:xmpmeta/>')
        image = Image.new('RGBA', (20, 10), (200, 100, 50, 128)); image.putpixel((3, 4), (1, 2, 3, 4))
        image.save(path, pnginfo=info, icc_profile=ICC, exif=exif(), dpi=(144, 144))
        raw = path.read_bytes(); end = raw.rindex(b'IEND') - 4
        c2pa = struct.pack('>I', 4) + b'caBX' + b'jumb' + struct.pack('>I', zlib.crc32(b'caBXjumb'))
        path.write_bytes(raw[:end] + c2pa + raw[end:])
        self.clean(path)
        self.assertEqual({kind for kind, _ in clean_image.png_chunks(path.read_bytes())}, {b'IHDR', b'IDAT', b'IEND'})

    def test_jpeg_drops_app_and_comment_but_keeps_adobe_colour_transform(self):
        rgb, cmyk = self.root / 'photo.jpg', self.root / 'print.jpg'
        Image.new('RGB', (16, 16), (30, 140, 220)).save(rgb, exif=exif(), icc_profile=ICC, comment=b'secret prompt')
        Image.new('CMYK', (16, 16), (10, 200, 30, 5)).save(cmyk)
        self.clean(rgb)
        self.assertNotIn(b'Canon', rgb.read_bytes())
        self.assertNotIn(b'secret prompt', rgb.read_bytes())
        self.assertNotIn(b'\xff\xe0', rgb.read_bytes()[:4])
        self.clean(cmyk)
        self.assertEqual(cmyk.read_bytes()[2:4], b'\xff\xee')  # APP14 Adobe decides CMYK inversion
        self.assertEqual(cmyk.read_bytes()[6:11], b'Adobe')

    def test_webp_drops_exif_icc_and_clears_extended_flags(self):
        path = self.root / 'image.webp'
        Image.new('RGBA', (12, 12), (10, 200, 30, 120)).save(path, lossless=True, exif=exif(), icc_profile=ICC)
        self.clean(path)
        data = path.read_bytes()
        self.assertNotIn(b'EXIF', data); self.assertNotIn(b'ICCP', data)

    def test_unsupported_format_is_refused_and_left_untouched(self):
        path = self.root / 'image.gif'
        Image.new('P', (4, 4)).save(path)
        original = path.read_bytes()
        with self.assertRaisesRegex(ValueError, 'Unsupported'):
            clean_image.clean_image(path, self.root / 'audit.json')
        self.assertEqual(path.read_bytes(), original)

    def test_pixel_change_aborts_without_replacing_the_source(self):
        path = self.root / 'image.png'
        Image.new('RGB', (4, 4), 'red').save(path)
        other = self.root / 'other.png'
        Image.new('RGB', (4, 4), 'blue').save(other)
        original = path.read_bytes()
        with patch('clean_image.strip_metadata', return_value=other.read_bytes()), self.assertRaisesRegex(ValueError, 'pixels'):
            clean_image.clean_image(path, self.root / 'audit.json')
        self.assertEqual(path.read_bytes(), original)
        self.assertEqual(sorted(item.name for item in self.root.iterdir()), ['image.png', 'other.png'])

    @unittest.skipUnless(sys.platform == 'darwin' and shutil.which('xattr'), 'macOS xattr CLI')
    def test_macos_download_attributes_are_cleared(self):
        path = self.root / 'download.png'
        Image.new('RGB', (4, 4), 'red').save(path)
        for name, value in (('com.apple.quarantine', '0081;6703a1b2;Safari;'), ('com.apple.metadata:kMDItemWhereFroms', 'https://example.test')):
            subprocess.run(['xattr', '-w', name, value, str(path)], check=True)
        report = self.clean(path)
        self.assertFalse(set(report['xattrs_remaining']) & set(clean_image.MAC_SOURCE_XATTRS))

    @unittest.skipUnless(hasattr(os, 'setxattr'), 'Linux xattr API')
    def test_linux_user_attributes_are_cleared(self):
        path = self.root / 'download.png'
        Image.new('RGB', (4, 4), 'red').save(path)
        try:
            os.setxattr(path, 'user.xdg.origin.url', b'https://example.test/image.png')
        except OSError:
            self.skipTest('filesystem without user xattrs')
        report = self.clean(path)
        self.assertNotIn('user.xdg.origin.url', report['xattrs_remaining'])


if __name__ == '__main__':
    unittest.main()
