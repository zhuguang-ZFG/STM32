#!/usr/bin/env python3
"""Verify one installable entry, vendor integrity, routed guides and presets."""
import hashlib
import json
from pathlib import Path
from hosted_assets import asset_available, checked as preset_intact, records as hosted_records

PACKAGE = Path(__file__).resolve().parents[1]
PACKAGE_BUDGET_BYTES, FILE_BUDGET_BYTES = 50 * 1024**2, 10 * 1024**2


def packaged_files(root=PACKAGE):
    return [p for p in sorted(root.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.name != '.DS_Store' and p.suffix != '.pyc']


def validate_package():
    entries = list(PACKAGE.rglob('SKILL.md'))
    if entries != [PACKAGE / 'SKILL.md']:
        raise ValueError('The installation must expose exactly one SKILL.md')
    records = json.loads((PACKAGE / 'dependencies/vendor-manifest.json').read_text())
    checked = 0
    for dependency in records:
        directory = PACKAGE / 'dependencies' / dependency['name']
        if not (directory / 'GUIDE.md').is_file() or not (directory / 'LICENSE').is_file():
            raise ValueError('Missing guide or license: ' + dependency['name'])
        for record in dependency['files']:
            path = directory / record['path']
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != record['sha256']:
                raise ValueError('Bundled dependency changed: ' + str(path.relative_to(PACKAGE)))
            checked += 1
    for guide in ['FILM-ART GUIDE.md', 'DIRECTOR-VISION GUIDE.md']:
        if not (PACKAGE / 'dependencies/omniailab-ai-director/references' / guide).is_file():
            raise ValueError('Missing routed director guide: ' + guide)
    for directory, collection, required_fields in [
            ('hands', 'presets', ['source']), ('voices', 'voices', ['reference_audio', 'reference_text'])]:
        catalog = json.loads((PACKAGE / 'assets' / directory / 'catalog.json').read_text())
        ids = [entry['id'] for entry in catalog[collection]]
        if len(ids) != len(set(ids)) or catalog['default'] not in ids:
            raise ValueError('Invalid catalog: ' + directory)
        for entry in catalog[collection]:
            if directory == 'voices' and entry.get('requires_import'):
                if entry.get('reference_audio') or entry.get('reference_text'):
                    raise ValueError('An import-only reference must not bundle an external recording')
                continue
            for field in required_fields:
                if not asset_available(PACKAGE / 'assets' / directory / entry[field]):
                    raise ValueError('Missing preset: ' + entry['id'])
    previews = json.loads((PACKAGE/'assets/style-previews/manifest.json').read_text())['images']
    hosted = hosted_records()
    for preview in previews:
        record = hosted['assets/style-previews/'+preview['thumbnail']]
        if record['sha256'] != preview['thumbnail_sha256']:
            raise ValueError('Catalog preview changed: '+preview['id'])
    for key, record in hosted.items():
        if not (PACKAGE/key).is_file() or not preset_intact((PACKAGE/key).read_bytes(), record):
            raise ValueError('Packaged preset missing or changed: '+key)
    files = packaged_files()
    total = sum(path.stat().st_size for path in files)
    oversized = [str(path.relative_to(PACKAGE)) for path in files if path.stat().st_size > FILE_BUDGET_BYTES]
    if oversized or total > PACKAGE_BUDGET_BYTES:
        raise ValueError(f'Package budget exceeded (total {total/1024**2:.1f} MB <= 50 MB, single file <= 10 MB): {oversized}')
    return {'catalog_previews_checked': len(previews), 'status': 'passed', 'skill_entries': 1, 'bundled_dependencies': len(records),
            'vendor_files_checked': checked, 'packaged_presets_checked': len(hosted), 'package_megabytes': round(total/1024**2, 2)}


if __name__ == '__main__':
    print(json.dumps(validate_package(), ensure_ascii=False))
