#!/usr/bin/env python3
"""List a job's remaining work shot by shot, so long films can be finished chapter by chapter."""
import argparse
import hashlib
import json
from pathlib import Path
from narration_master import script_text
from storyboard_lint import alignment_beats, load, page_actions, plan, sha256, usage


def read(path):
    return json.loads(Path(path).read_text()) if path and Path(path).is_file() else {}


def status(job):
    root = Path(job).resolve()
    manifest = json.loads((root / 'job.json').read_text())
    todo, errors = [], []
    narration = manifest.get('narration') or {}
    source, alignment = [root / narration[key] if narration.get(key) else None for key in ('source', 'alignment')]
    if not source or not source.is_file():
        todo.append(('-', 'lock the complete narration master (narration.source)'))
    elif not alignment or not alignment.is_file():
        todo.append(('-', 'write the narration alignment (narration.alignment)'))
    elif read(alignment).get('source_sha256') != sha256(source) or read(alignment).get('script_sha256') != hashlib.sha256(script_text(manifest).encode()).hexdigest():
        todo.append(('-', 'alignment is stale: realign the current master and script'))
    board = load(root, manifest)
    if board is None:
        todo.append(('-', 'write storyboard.json from the locked narration, set job.json "storyboard", run storyboard_lint.py --budget'))
    else:
        record_path = root / manifest.get('art_direction', {}).get('record', 'design/art-direction.json')
        records = {(record_path.parent / entry['source']).resolve(): entry for entry in read(record_path).get('images', [])}
        plans = {item['id']: item for item in read(root / manifest['drawing_plan']).get('illustrations', [])} if manifest.get('drawing_plan') else {}
        reviews = {item['plan_id']: item for item in read(root / manifest['drawing_review']).get('illustrations', [])} if manifest.get('drawing_review') else {}
        placed = {}
        for _, _, action in page_actions(manifest):
            placed.setdefault(action.get('visual'), []).append(action)
        for shot in board.get('shots', []):
            for visual in shot.get('visuals', []):
                label, actions = shot.get('id'), placed.get(visual.get('id'), [])
                if not actions:
                    missing = visual.get('kind') == 'illustration' and not (root / visual.get('source', '-')).is_file()
                    todo.append((label, f'{visual.get("id")}: {"generate the image, then " if missing else ""}place the planned {visual.get("kind")} "{visual.get("subject")}" in job.json'))
                for action in (action for action in actions if action['type'] == 'illustration'):
                    image = root / action['source']
                    if not image.is_file():
                        todo.append((label, f'{visual["id"]}: generate image {action["source"]}'))
                        continue
                    entry, review = records.get(image.resolve(), {}), reviews.get(action.get('drawing_plan_id'), {})
                    if entry.get('status') != 'pass' or entry.get('sha256') != sha256(image):
                        todo.append((label, f'{visual["id"]}: art-direction review missing or stale for {action["source"]}'))
                    if action.get('drawing_plan_id') not in plans:
                        todo.append((label, f'{visual["id"]}: drawing plan missing (drawing_plan_id)'))
                    elif not all(subject.get('identity_cues') for subject in plans[action['drawing_plan_id']].get('subjects', [])):
                        todo.append((label, f'{visual["id"]}: add identity_cues to the drawing plan subjects and rerun preflight'))
                    if review.get('status') != 'pass' or review.get('source_sha256') != sha256(image):
                        todo.append((label, f'{visual["id"]}: drawing review missing or stale'))
                    elif review.get('recognizability', {}).get('status') != 'pass':
                        todo.append((label, f'{visual["id"]}: thumbnail recognizability test missing (drawing_contract.py JOB --thumbnails)'))
        try:
            errors = plan(board, alignment_beats(root, manifest))['errors'] + usage(root, manifest, board)
        except (ValueError, KeyError, FileNotFoundError) as error:
            errors = [str(error)]
    return {'remaining': len(todo) + len(errors), 'next_shot': next((shot for shot, _ in todo if shot != '-'), None),
            'todo': [{'shot': shot, 'item': item} for shot, item in todo], 'lint_errors': errors,
            'note': 'Actual cadence, reuse and drawing-time checks run in build'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('job', type=Path)
    print(json.dumps(status(parser.parse_args().job), ensure_ascii=False, indent=1))
