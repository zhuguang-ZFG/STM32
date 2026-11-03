#!/usr/bin/env python3
"""Edge-TTS narration runner for a sweety-handdraw-video job (Windows adaptation, zero source changes).

One request per semantic chunk via narration_master.build_master; word timestamps come from
edge-tts WordBoundary events (offset/duration in 100 ns units) and mp3 is converted locally
to 48 kHz mono s16 wav with ffmpeg. Run with the skill's scripts/ and video/pydeps on
PYTHONPATH, using the scoop-base python (bare `python`).
"""
import argparse
import asyncio
import json
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np

VOICE = 'zh-CN-YunyangNeural'
RATE = '+2%'
OUTPUT_RATE = 48000


async def _synthesize_async(text, mp3_path):
    import edge_tts
    words = []
    communicate = edge_tts.Communicate(text, VOICE, rate=RATE, boundary='WordBoundary')
    with open(mp3_path, 'wb') as stream:
        async for chunk in communicate.stream():
            if chunk['type'] == 'audio':
                stream.write(chunk.get('data', b''))
            elif chunk['type'] == 'WordBoundary':
                offset, duration = chunk.get('offset', 0), chunk.get('duration', 0)
                words.append({'text': chunk.get('text', ''),
                              'start': offset / 1e7,
                              'end': (offset + duration) / 1e7})
    if not words:
        raise RuntimeError('edge-tts returned no WordBoundary events for: ' + text[:40])
    return words


def synthesize(text, seed):
    """narration_master contract: (samples, rate, words) with word times in seconds."""
    with tempfile.TemporaryDirectory() as folder:
        mp3 = Path(folder) / 'chunk.mp3'
        wav = Path(folder) / 'chunk.wav'
        words = asyncio.run(_synthesize_async(text, mp3))
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', str(mp3),
                        '-af', 'highpass=f=80,highpass=f=80', '-ar', str(OUTPUT_RATE), '-ac', '1',
                        '-sample_fmt', 's16', str(wav)],
                       check=True)
        with wave.open(str(wav)) as stream:
            rate = stream.getframerate()
            samples = np.frombuffer(stream.readframes(stream.getnframes()), dtype='<i2').astype(np.float64) / 32768
    # edge-tts mp3 carries a stationary ~33 Hz codec hum in pauses; the ffmpeg cascade only
    # attenuates it, so finish it with a steep zero-phase highpass (no group delay: word
    # timestamps stay aligned). Male voice fundamental (~114 Hz) is untouched.
    from scipy.signal import butter, sosfiltfilt
    sos = butter(6, 58, btype='highpass', fs=OUTPUT_RATE, output='sos')
    samples = sosfiltfilt(sos, samples)
    if not len(samples):
        raise RuntimeError('edge-tts produced empty audio for: ' + text[:40])
    return samples, rate, words


def generate(job):
    from narration_master import build_master
    root = Path(job).resolve()
    manifest = json.loads((root / 'job.json').read_text())
    options = manifest.get('edge_tts', {})
    identity = {'engine': 'edge-tts', 'voice': options.get('voice', VOICE), 'rate': options.get('rate', RATE)}
    target, alignment = build_master(root, manifest, synthesize, identity, {'asr': False, 'seed': 2026})
    print('READY', target, alignment, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('job', type=Path)
    generate(parser.parse_args().job)
