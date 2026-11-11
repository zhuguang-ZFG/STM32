"""Verify packaged public presets; repair a missing or damaged copy from pinned mirrors into a cache."""
import argparse
import hashlib
from http.client import HTTPException
import json
import os
from pathlib import Path, PurePosixPath
import re
import tempfile
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

PACKAGE = Path(__file__).resolve().parents[1]
TIMEOUT_SECONDS = 15


def public_url(url):
    parts = urlsplit(url)
    return parts.scheme == 'https' and bool(parts.hostname) and not parts.username and not parts.password


def records():
    data = json.loads((PACKAGE / 'assets/hosted-manifest.json').read_text())['files']
    for key, record in data.items():
        path = PurePosixPath(key)
        if path.is_absolute() or '..' in path.parts or str(path) != key or '\\' in key:
            raise ValueError('Invalid hosted asset path')
        if not record.get('urls') or not all(public_url(url) for url in record['urls']):
            raise ValueError('Hosted assets require public HTTPS URLs')
        if type(record['bytes']) is not int or record['bytes'] <= 0 or not re.fullmatch('[a-f0-9]{64}', record['sha256']):
            raise ValueError('Hosted assets require size and SHA-256')
    return data


def checked(content, record):
    return len(content) == record['bytes'] and hashlib.sha256(content).hexdigest() == record['sha256']


def cache_path(key, record):
    base = Path(os.environ.get('HANDDRAW_ASSET_CACHE', str(Path.home() / '.cache/sweety-handdraw-video'))).expanduser()
    return base / record['sha256'] / Path(key).name


def candidate_urls(key, record):
    """HANDDRAW_MIRROR is a prefix (https:// or file://) laid out like the package; it is tried first."""
    mirror = os.environ.get('HANDDRAW_MIRROR', '').strip().rstrip('/')
    return ([mirror + '/' + key] if mirror else []) + list(record['urls'])


def fetch(key, record, destination):
    """Return verified bytes from the first working URL; on total failure list every URL and the manual path."""
    failures = []
    for url in candidate_urls(key, record):
        try:
            with urlopen(Request(url, headers={'User-Agent': 'sweety-handdraw-video'}), timeout=TIMEOUT_SECONDS) as response:
                content = response.read(record['bytes'] + 1)
            if checked(content, record):
                return content
            failures.append(f'{url} -> size/SHA-256 mismatch')
        except (OSError, ValueError, HTTPException) as error:
            failures.append(f'{url} -> {error}')
    raise ValueError(f'Could not download a verified copy of {key} ({record["bytes"]} bytes, sha256 {record["sha256"]}).\n  '
                     + '\n  '.join(failures) + f'\nDownload any URL above manually and save it as: {destination}'
                     + '\nOr set HANDDRAW_MIRROR to a reachable mirror prefix.')


def asset_available(path):
    path = Path(path)
    if path.is_file():
        return True
    try:
        return path.relative_to(PACKAGE).as_posix() in records()
    except ValueError:
        return False


def resolve_asset(path):
    path = Path(path)
    try:
        key = path.relative_to(PACKAGE).as_posix()
    except ValueError:
        if not path.is_file():
            raise FileNotFoundError(path)
        return path
    record = records().get(key)
    if record is None:
        if not path.is_file():
            raise FileNotFoundError(path)
        return path
    target = cache_path(key, record)
    for candidate in (path, target):
        if candidate.is_file() and checked(candidate.read_bytes(), record):
            return candidate
    if os.environ.get('HANDDRAW_OFFLINE') == '1':
        raise ValueError(f'Offline asset missing or damaged: {key}; place a verified copy at {path} or {target}')
    content = fetch(key, record, target)
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(content)
    try:
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)
    return target


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('keys', nargs='*')
    parser.add_argument('--all', action='store_true')
    arguments = parser.parse_args()
    keys = list(records()) if arguments.all else arguments.keys
    if not keys:
        parser.error('Provide asset keys or --all')
    for key in keys:
        if key not in records():
            parser.error('Unknown asset: ' + key)
        print(resolve_asset(PACKAGE / key))
