#!/usr/bin/env python3
"""Import a reference and its exact transcript into one job; dirty references are rejected.

Presets take their original recording; any other id is a custom voice and needs --consent self
(the user's own voice) or authorized (the speaker's permission). Clean a noisy recording first with
scripts/clean_reference.py.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
from production_options import save_json
from voice_studio import checked_reference, CONSENT


def import_reference(job, identifier, name, audio, transcript, reference_kind='user_supplied', consent=None):
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}', identifier):
        raise ValueError('Voice id must use lowercase letters, digits and hyphens')
    catalog_path = Path(__file__).resolve().parents[1]/'assets/voices/catalog.json'
    presets = {voice['id'] for voice in json.loads(catalog_path.read_text())['voices']}
    if identifier not in presets and consent not in CONSENT:
        raise ValueError('A custom voice needs consent: self (your own voice) or authorized (speaker permission); never clone others or platform voices')
    if reference_kind not in ('user_supplied', 'source_recording', 'synthetic_direction'):
        raise ValueError('Unknown reference kind')
    audio, transcript = Path(audio).resolve(), Path(transcript).resolve()
    if not audio.is_file() or not transcript.is_file() or not transcript.read_text().strip():
        raise ValueError('Provide reference audio and its nonempty exact transcript')
    checked_reference(audio, transcript.read_text())
    destination = Path(job).resolve()/'options/voices'/identifier
    destination.mkdir(parents=True, exist_ok=True)
    copied_audio, copied_text = destination/('reference'+audio.suffix), destination/'transcript.txt'
    if copied_audio.exists() or copied_text.exists():
        raise ValueError('This job already has a reference with that id')
    shutil.copyfile(audio, copied_audio)
    shutil.copyfile(transcript, copied_text)
    catalog_path = Path(job).resolve()/'options/local-voices.json'
    catalog = json.loads(catalog_path.read_text()) if catalog_path.is_file() else {'voices': []}
    catalog['voices'] = [entry for entry in catalog['voices'] if entry['id'] != identifier] + [{
        'id': identifier, 'name': name, 'description': '用户自有或授权的参考音色；仅存放在当前任务',
        'reference_audio': str(copied_audio), 'reference_text': str(copied_text), 'source': 'User-provided local reference', 'redistribution': 'not bundled',
        'reference_kind': reference_kind, 'reference_sha256': hashlib.sha256(copied_audio.read_bytes()).hexdigest(),
        'transcript_sha256': hashlib.sha256(copied_text.read_text().strip().encode()).hexdigest(), **({'consent': consent} if consent else {})}]
    save_json(catalog_path, catalog)
    return catalog_path


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('job', type=Path)
    parser.add_argument('--id', required=True)
    parser.add_argument('--name', required=True)
    parser.add_argument('--audio', type=Path, required=True)
    parser.add_argument('--transcript', type=Path, required=True)
    parser.add_argument('--kind', choices=['user_supplied', 'source_recording', 'synthetic_direction'], default='user_supplied')
    parser.add_argument('--consent', choices=CONSENT, help='Required for custom voices: self or authorized')
    args = parser.parse_args()
    print(import_reference(args.job, args.id, args.name, args.audio, args.transcript, args.kind, args.consent))
