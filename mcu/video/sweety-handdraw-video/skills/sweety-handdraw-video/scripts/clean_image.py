#!/usr/bin/env python3
"""Remove embedded metadata and source xattrs from an image in pure Python, then audit.

Same result as the bundled sweety-image-privacy + `exiftool -all=` path, without Bun or ExifTool:
the container is rewritten keeping only image-data chunks/segments (pixels are never re-encoded),
so EXIF, GPS, XMP, IPTC, ICC, text/comments, timestamps and C2PA/JUMBF blocks are dropped.
No simulated camera profile is ever written.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import time
from PIL import Image

PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'
PNG_KEEP = {b'IHDR', b'PLTE', b'tRNS', b'IDAT', b'IEND', b'acTL', b'fcTL', b'fdAT'}
WEBP_KEEP = {b'VP8 ', b'VP8L', b'VP8X', b'ALPH', b'ANIM', b'ANMF'}
IMAGE_DATA_INFO = {'transparency', 'interlace', 'progressive', 'progression', 'adobe', 'adobe_transform',
                   'loop', 'duration', 'background', 'timestamp', 'blend', 'disposal'}
MAC_SOURCE_XATTRS = ('com.apple.metadata:kMDItemWhereFroms', 'com.apple.quarantine')


def png_chunks(data):
    position = 8
    while position < len(data):
        length, kind = struct.unpack('>I4s', data[position:position + 8])
        yield kind, data[position:position + 12 + length]
        position += 12 + length


def strip_png(data):
    return PNG_SIGNATURE + b''.join(chunk for kind, chunk in png_chunks(data) if kind in PNG_KEEP)


def strip_jpeg(data):
    """Drop APP0-APP13/APP15 and COM before the first scan; keep APP14 (Adobe colour transform) and cut trailers after EOI."""
    output, position = [data[:2]], 2
    while position < len(data):
        if data[position] != 0xFF:
            raise ValueError('Malformed JPEG marker stream')
        marker = data[position + 1]
        if marker == 0xFF:
            position += 1
            continue
        length = struct.unpack('>H', data[position + 2:position + 4])[0]
        segment = data[position:position + 2 + length]
        if not ((0xE0 <= marker <= 0xEF and marker != 0xEE) or marker == 0xFE):
            output.append(segment)
        position += 2 + length
        if marker == 0xDA:
            end = data.find(b'\xff\xd9', position)
            if end < 0:
                raise ValueError('JPEG has no end-of-image marker')
            output.append(data[position:end + 2])
            return b''.join(output)
    raise ValueError('JPEG has no image scan')


def strip_webp(data):
    chunks, position = [], 12
    while position < len(data):
        kind, length = struct.unpack('<4sI', data[position:position + 8])
        if kind in WEBP_KEEP:
            chunks.append([kind, bytearray(data[position + 8:position + 8 + length])])
        position += 8 + length + (length & 1)
    for chunk in chunks:
        if chunk[0] == b'VP8X':
            chunk[1][0] &= ~0x2C & 0xFF  # clear ICC (0x20), EXIF (0x08), XMP (0x04) flags
    chunks = [chunk for chunk in chunks if chunk[0] != b'VP8X' or chunk[1][0] & 0x12]  # keep only for alpha/animation
    body = b'WEBP' + b''.join(kind + struct.pack('<I', len(payload)) + bytes(payload) + b'\0' * (len(payload) & 1) for kind, payload in chunks)
    return b'RIFF' + struct.pack('<I', len(body)) + body


def strip_metadata(data):
    if data.startswith(PNG_SIGNATURE):
        return strip_png(data)
    if data.startswith(b'\xff\xd8'):
        return strip_jpeg(data)
    if data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        return strip_webp(data)
    raise ValueError('Unsupported image format; convert to PNG, JPEG or WebP first')


def pixels(path):
    with Image.open(path) as image:
        image.load()
        return image.mode, image.size, getattr(image, 'n_frames', 1), image.tobytes()


def embedded_metadata(path):
    with Image.open(path) as image:
        found = [key for key in image.info if key not in IMAGE_DATA_INFO]
        return found + (['exif'] if image.getexif() else [])


def xattrs(path):
    if hasattr(os, 'listxattr'):
        return sorted(os.listxattr(path))
    if shutil.which('xattr'):
        return subprocess.run(['xattr', str(path)], capture_output=True, text=True, check=True).stdout.split('\n')[:-1]
    return []


def clear_xattrs(path):
    """Linux: remove user.* (browser origin/referrer); macOS: xattr -c, retrying while quarantine or Where-from reappears."""
    if hasattr(os, 'removexattr'):
        for name in xattrs(path):
            if name.startswith('user.'):
                os.removexattr(path, name)
        return xattrs(path)
    for attempt in range(5):
        if shutil.which('xattr'):
            subprocess.run(['xattr', '-c', str(path)], capture_output=True)
        time.sleep(.25)
        remaining = xattrs(path)
        if not any(name in MAC_SOURCE_XATTRS for name in remaining):
            return remaining
    raise ValueError('Could not clear macOS source attributes: ' + ', '.join(remaining))


def clean_image(source, audit_path):
    source = Path(source).resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    before = pixels(source)
    original = source.read_bytes()
    cleaned = strip_metadata(original)
    with tempfile.NamedTemporaryFile(dir=source.parent, prefix='.clean-', suffix=source.suffix, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(cleaned)
    try:
        if pixels(temporary) != before:
            raise ValueError('Metadata removal changed decoded pixels; source left untouched')
        os.chmod(temporary, os.stat(source).st_mode & 0o777)
        temporary.replace(source)
    finally:
        temporary.unlink(missing_ok=True)
    remaining = embedded_metadata(source)
    if remaining:
        raise ValueError('Embedded privacy metadata remains after cleanup: ' + ', '.join(remaining))
    report = {'file': source.name, 'sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
              'embedded_metadata_empty': True, 'xattrs_remaining': clear_xattrs(source),
              'camera_profile_removed': True,
              'note': 'System-managed provenance attributes can remain; this is not an AI detector guarantee.'}
    audit_path = Path(audit_path)
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('image', type=Path)
    parser.add_argument('--audit', type=Path, required=True)
    arguments = parser.parse_args()
    print(json.dumps(clean_image(arguments.image, arguments.audit), ensure_ascii=False))
