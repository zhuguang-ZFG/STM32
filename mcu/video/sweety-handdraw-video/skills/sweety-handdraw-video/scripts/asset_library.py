#!/usr/bin/env python3
"""Local library of approved illustrations, so common props, poses and icons are generated once and reused.

    asset_library.py add JOB inputs/art/laptop.png --tags 电脑,办公 --note "侧面打开的笔记本"
    asset_library.py find --tags 电脑 [--style 17]
    asset_library.py use JOB <entry id> --to inputs/art/laptop.png

Only images whose art-direction review passed in their job can be added; the library keeps the image bytes, the
pre-generation brief and prompt, the review, the resolved style and the semantic parts the job drew it with.
`use` copies the image and its evidence into another job and appends a `library_reuse` record that is NOT yet
reviewed: look at the picture in the new context, then set status "pass" and write the evidence yourself.
The library lives outside the skill and the jobs: $HANDDRAW_LIBRARY or ~/.local/share/sweety-handdraw-video/library."""
import argparse
import hashlib
import json
import os
import shutil
import sys
import time
from pathlib import Path


def library_root():
    root = Path(os.environ.get('HANDDRAW_LIBRARY', Path.home() / '.local/share/sweety-handdraw-video/library')).expanduser()
    (root / 'images').mkdir(parents=True, exist_ok=True)
    return root


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_index(root):
    path = root / 'index.json'
    return json.loads(path.read_text()) if path.is_file() else {'version': 1, 'entries': []}


def save_index(root, index):
    path = root / 'index.json'
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(index, ensure_ascii=False, indent=1))
    temporary.replace(path)


def job_record(job, manifest):
    reference = manifest.get('art_direction', {}).get('record')
    if not reference:
        raise ValueError('This job has no art_direction.record')
    path = job / reference
    return path, json.loads(path.read_text())


def add(job, image, tags, note=''):
    job = Path(job).resolve()
    manifest = json.loads((job / 'job.json').read_text())
    record_path, record = job_record(job, manifest)
    source = (job / image).resolve()
    entry = next((item for item in record['images'] if (record_path.parent / item['source']).resolve() == source), None)
    if entry is None or entry.get('status') != 'pass' or entry.get('sha256') != digest(source):
        raise ValueError('Only an image whose art-direction review passed (and is unchanged since) can join the library')
    sha = digest(source)
    root = library_root()
    index = load_index(root)
    if any(item['id'] == sha[:16] for item in index['entries']):
        raise ValueError(f'Already in the library as {sha[:16]}')
    folder = root / 'images' / sha[:16]
    folder.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, folder / ('image' + source.suffix.lower()))
    for field in ('brief_file', 'prompt_file'):
        shutil.copy2(record_path.parent / entry[field], folder / f"{field.split('_')[0]}{Path(entry[field]).suffix or '.txt'}")
    style = job / 'style' / 'resolved.json'
    actions = [action for page in manifest['pages'] for holder in page.get('visual_groups', []) + page['beats']
               for action in holder.get('actions') or [] if action.get('type') == 'illustration' and (job / action['source']).resolve() == source]
    item = {'id': sha[:16], 'sha256': sha, 'file': f'images/{sha[:16]}/image{source.suffix.lower()}', 'tags': sorted(set(tags)), 'note': note,
            'evidence': entry.get('evidence'), 'style': json.loads(style.read_text()) if style.is_file() else None,
            'parts': [{key: action[key] for key in ('parts', 'part_regions', 'crop', 'drawing_plan_id') if key in action} for action in actions],
            'source_job': str(job), 'added': time.strftime('%Y-%m-%d')}
    index['entries'].append(item)
    save_index(root, index)
    return item


def style_label(item):
    """Library number or model-designed style name of the job the image came from."""
    style = item.get('style') or {}
    return str(style.get('style_id') or style.get('id') or style.get('style_name') or '')


def find(tags=(), style=None, text=None):
    index = load_index(library_root())
    result = []
    for item in index['entries']:
        if set(tags) - set(item['tags']):
            continue
        if style and style not in style_label(item):
            continue
        if text and text not in item.get('note', '') and text not in ' '.join(item['tags']):
            continue
        result.append({key: item[key] for key in ('id', 'tags', 'note', 'file', 'added')} | {'style': style_label(item)})
    return result


def use(job, identity, target):
    job = Path(job).resolve()
    root = library_root()
    item = next((entry for entry in load_index(root)['entries'] if entry['id'] == identity), None)
    if item is None:
        raise ValueError(f'No library entry {identity}')
    image = root / item['file']
    if digest(image) != item['sha256']:
        raise ValueError('Library image changed since it was added; remove and add it again')
    destination = job / target
    if destination.exists() and digest(destination) != item['sha256']:
        raise ValueError(f'{target} already exists with different content')
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(image, destination)
    manifest = json.loads((job / 'job.json').read_text())
    record_path, record = job_record(job, manifest)
    evidence_dir = record_path.parent / 'library'
    evidence_dir.mkdir(exist_ok=True)
    entry = {'source': os.path.relpath(destination, record_path.parent), 'sha256': item['sha256'], 'method': 'library_reuse',
             'library_entry': item['id'], 'library_evidence': item.get('evidence'), 'status': 'pending_review',
             'evidence': '', 'note': 'Reused from the local library: look at it in this film, then set status pass with your own evidence.'}
    for field in ('brief', 'prompt'):
        found = next((path for path in image.parent.glob(f'{field}.*')), None)
        if found is None:
            raise ValueError(f'Library entry lacks its {field}')
        copy = evidence_dir / f"{item['id']}-{field}{found.suffix}"
        shutil.copy2(found, copy)
        entry[f'{field}_file'] = os.path.relpath(copy, record_path.parent)
        entry[f'{field}_sha256'] = digest(copy)
    record['images'] = [existing for existing in record['images'] if existing.get('source') != entry['source']] + [entry]
    temporary = record_path.with_suffix('.tmp')
    temporary.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(record_path)
    return {'copied': str(destination), 'record': str(record_path), 'status': 'pending_review', 'parts_used_before': item['parts'],
            'style_of_entry': style_label(item)}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest='command', required=True)
    adding = commands.add_parser('add')
    adding.add_argument('job', type=Path)
    adding.add_argument('image')
    adding.add_argument('--tags', required=True)
    adding.add_argument('--note', default='')
    finding = commands.add_parser('find')
    finding.add_argument('--tags', default='')
    finding.add_argument('--style')
    finding.add_argument('--text')
    using = commands.add_parser('use')
    using.add_argument('job', type=Path)
    using.add_argument('id')
    using.add_argument('--to', required=True)
    arguments = parser.parse_args()
    split = lambda value: [tag.strip() for tag in value.replace('，', ',').split(',') if tag.strip()]
    if arguments.command == 'add':
        result = add(arguments.job, arguments.image, split(arguments.tags), arguments.note)
    elif arguments.command == 'find':
        result = find(split(arguments.tags), arguments.style, arguments.text)
    else:
        result = use(arguments.job, arguments.id, arguments.to)
    print(json.dumps(result, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    sys.exit(main())
