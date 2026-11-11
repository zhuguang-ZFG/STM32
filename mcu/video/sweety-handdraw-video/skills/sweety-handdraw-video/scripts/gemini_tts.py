#!/usr/bin/env python3
"""Optional cloud narration: Gemini TTS through the Interactions API, only with the user's GEMINI_API_KEY.

Docs: https://ai.google.dev/gemini-api/docs/speech-generation . One request per semantic chunk, raw
16-bit PCM (audio/l16, 24 kHz mono) converted locally; Gemini returns no timestamps, so captions come
from local ASR or the pause split. Live calls are untested here; tests mock HTTP.
"""
import argparse
import base64
import json
import os
from pathlib import Path
import numpy as np
from narration_master import build_master

URL = 'https://generativelanguage.googleapis.com/v1beta/interactions'
MODEL = 'gemini-3.8-flash-tts'
VOICE = 'Iapetus'
RATE = 24000


def request_body(text, options):
    content = {'type': 'text', 'text': text}
    if options.get('style'):
        content['annotations'] = [{'type': 'speech_metadata', 'style': options['style']}]
    return {'model': options.get('model', MODEL), 'input': [{'type': 'user_input', 'content': [content]}],
            'response_format': {'type': 'audio', 'mime_type': 'audio/l16', 'sample_rate': RATE},
            'generation_config': {'speech_config': [{'voice': options.get('voice', VOICE)}]}}


def audio_from(response):
    outputs = [item for step in response.get('steps', []) if step.get('type') == 'model_output'
               for item in step.get('content', []) if item.get('type') == 'audio']
    if not outputs:
        raise RuntimeError('Gemini TTS returned no audio')
    return np.frombuffer(base64.b64decode(outputs[-1]['data']), dtype='<i2').astype(np.float64) / 32768


def synthesizer(options):
    import requests
    key = os.environ.get('GEMINI_API_KEY')
    if not key:
        raise SystemExit('Optional Gemini TTS needs GEMINI_API_KEY; local VoxCPM2 stays the default')

    def synthesize(text, seed):  # no seed parameter; a retry is a new request
        response = requests.post(URL, headers={'x-goog-api-key': key, 'Content-Type': 'application/json'},
                                 json=request_body(text, options), timeout=300)
        if response.status_code != 200:
            raise RuntimeError(f'Gemini TTS HTTP {response.status_code}')
        return audio_from(response.json()), RATE
    return synthesize


def generate(job):
    root = Path(job).resolve()
    manifest = json.loads((root/'job.json').read_text())
    options = manifest.get('gemini_tts', {})
    identity = {'engine': 'gemini-interactions', 'model': options.get('model', MODEL), 'voice': options.get('voice', VOICE), 'style': options.get('style')}
    target, alignment = build_master(root, manifest, synthesizer(options), identity, options)
    print('READY', target, alignment, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('job', type=Path)
    generate(parser.parse_args().job)
