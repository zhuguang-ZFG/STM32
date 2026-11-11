#!/usr/bin/env python3
"""Cut a clean 8-15 s cloning reference that ends at a sentence boundary; originals are never changed.

Optional stages run only when already installed: HTDemucs vocal separation (HANDDRAW_DEMUCS_PYTHON,
HANDDRAW_HTDEMUCS_WEIGHTS) and DeepFilterNet3 (HANDDRAW_MLX_PYTHON, HANDDRAW_DFN_MODEL). The result
must pass audio_gate and, when local ASR exists, cover the exact transcript.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import numpy as np
from scipy.io import wavfile
from audio_gate import decode, measure, SAMPLE_RATE
from align import activity, covers, transcribe
from voice_backends import tools, run_python

LEAD_SECONDS = .15
TAIL_SECONDS = (.5, .8)
DURATION_RANGE = (8., 15.)
PEAK_DBFS = -3.
SEPARATE = r'''
import json, sys, soundfile as sf, torch
from demucs.apply import apply_model
from demucs.hf import load_safetensors_model
source, target, weights = sys.argv[1:4]
audio, rate = sf.read(source, dtype='float32', always_2d=True)
model = load_safetensors_model(weights).eval()
waveform = torch.from_numpy(audio.T)
mean, scale = waveform.mean(0).mean(), waveform.mean(0).std()
with torch.inference_mode():
    separated = apply_model(model, ((waveform - mean) / scale)[None], device='cpu', shifts=1, split=True, overlap=.25, progress=False)[0] * scale + mean
sf.write(target, separated[model.sources.index('vocals')].mean(0).numpy(), rate, subtype='FLOAT')
print(json.dumps({'model': 'HTDemucs', 'sources': model.sources, 'sample_rate': rate, 'shifts': 1, 'overlap': .25}))
'''
DENOISE = r'''
import json, sys, numpy as np, soundfile as sf
from mlx_audio.sts.models.deepfilternet import DeepFilterNetModel
source, target, model = sys.argv[1:4]
audio, rate = sf.read(source, dtype='float32', always_2d=True)
audio = audio.mean(1)
enhanced = np.asarray(DeepFilterNetModel.from_pretrained(model, subfolder=None).enhance_array(audio), dtype=np.float32)
assert rate == 48000 and len(enhanced) == len(audio) and np.isfinite(enhanced).all()
sf.write(target, enhanced, rate, subtype='FLOAT')
print(json.dumps({'model': 'DeepFilterNet3 MLX', 'sample_rate': rate, 'timeline_preserved': True}))
'''


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_wav(path, samples, rate=SAMPLE_RATE):
    wavfile.write(path, rate, np.clip(np.rint(samples * 32767), -32768, 32767).astype('<i2'))


def boundaries(samples, start, end):
    """Snap a requested window to the real speech onset after start and the sentence end near end."""
    active = activity(samples)
    first, last = round(start * 100), min(len(active) - 1, round(end * 100))
    onset = next((index for index in range(max(0, first - 40), min(len(active), first + 60)) if active[index] and not active[max(0, index - 15):index].any()), None)
    candidates = [index for index in range(max((onset or 0) + 1, last - 60), min(len(active) - 1, last + 60)) if active[index] and not active[index + 1:index + 26].any()]
    if onset is None or not candidates:
        raise ValueError('No pause-bounded sentence near --start/--end (within 0.6 s); choose times at real sentence boundaries')
    offset = min(candidates, key=lambda index: abs(index - last))
    following = next((index for index in range(offset + 1, len(active)) if active[index]), len(active))
    return onset * .01, offset * .01 + .02, (following - offset) * .01 - .02


def clean(source, start, end, transcript, output, context=3., separate=True, denoise=True, asr=True):
    source, output = Path(source).resolve(), Path(output).resolve()
    if (output/'reference.wav').exists():
        raise ValueError('Output already has a reference; choose a new directory so earlier files stay intact')
    work = output/'work'
    work.mkdir(parents=True, exist_ok=True)
    found, steps = tools(), []
    window_start = max(0., start - context)
    contextual = work/'context.wav'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(window_start), '-i', str(source), '-t', str(end + context - window_start),
                    '-ar', '44100', '-ac', '2', str(contextual)], check=True)
    current = contextual
    if separate and found['demucs_python'] and found['htdemucs_weights']:
        vocals = work/'vocals.wav'
        steps.append({**run_python(found['demucs_python'], SEPARATE, current, vocals, found['htdemucs_weights']),
                      'weights_sha256': sha256(found['htdemucs_weights'])})
        current = vocals
    resampled = work/'mono-48k.wav'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(current), '-ac', '1', '-ar', str(SAMPLE_RATE), '-c:a', 'pcm_f32le', str(resampled)], check=True)
    current = resampled
    if denoise and found['mlx_python'] and found['deepfilternet3']:
        denoised = work/'denoised.wav'
        steps.append({**run_python(found['mlx_python'], DENOISE, current, denoised, found['deepfilternet3']),
                      'weights_sha256': sha256(found['deepfilternet3']/'model.safetensors')})
        current = denoised
    cleaned, raw = decode(current), decode(source, window_start, end + context - window_start)
    onset, offset, gap = boundaries(cleaned, start - window_start, end - window_start)
    first = max(0, round((onset - LEAD_SECONDS) * SAMPLE_RATE))
    natural = min(max(0., gap - .05), TAIL_SECONDS[1])
    stop = round((offset + natural) * SAMPLE_RATE)
    padding = max(0., TAIL_SECONDS[0] - natural)
    fade = np.linspace(1, 0, round(.01 * SAMPLE_RATE))
    reference = cleaned[first:stop].copy()
    reference[-len(fade):] *= fade
    reference = np.concatenate([reference, np.zeros(round(padding * SAMPLE_RATE))])
    duration = len(reference) / SAMPLE_RATE
    if not DURATION_RANGE[0] <= duration <= DURATION_RANGE[1]:
        raise ValueError(f'Reference must be {DURATION_RANGE[0]:.0f}-{DURATION_RANGE[1]:.0f} s after snapping to sentence boundaries; got {duration:.2f} s')
    gain = 10 ** (PEAK_DBFS / 20) / np.abs(reference).max()
    reference *= gain
    target = output/'reference.wav'
    write_wav(target, reference)
    (output/'transcript.txt').write_text(transcript.strip() + '\n')
    record = {'source': str(source), 'source_sha256': sha256(source), 'requested_seconds': [start, end],
              'used_seconds': [round(window_start + first / SAMPLE_RATE, 3), round(window_start + offset, 3)],
              'tail': {'natural_seconds': round(natural, 3), 'padded_seconds': round(padding, 3)}, 'gain_db': round(20 * np.log10(gain), 2),
              'steps': steps or [{'note': 'no separation/denoise model installed; trimmed only'}],
              'gate_before': measure(raw[first:stop], 'source window', True), 'gate_after': measure(reference, str(target), True),
              'reference_sha256': sha256(target), 'transcript_sha256': hashlib.sha256(transcript.strip().encode()).hexdigest(),
              'duration_seconds': round(duration, 3), 'listening': 'pending'}
    words = transcribe(target) if asr else None
    record['asr'] = covers(transcript, words['text'], homophones=False) if words else {'status': 'not_available'}
    (output/'clean-record.json').write_text(json.dumps(record, ensure_ascii=False, indent=2))
    if record['gate_after']['status'] != 'PASS' or record['asr']['status'] == 'fail':
        raise ValueError('Cleaned reference failed: ' + json.dumps({'gate': record['gate_after']['failures'], 'asr': record['asr']}, ensure_ascii=False))
    return record


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('source', type=Path)
    parser.add_argument('--start', type=float, required=True, help='Approximate start of the first sentence (s)')
    parser.add_argument('--end', type=float, required=True, help='Approximate end of the last sentence (s)')
    parser.add_argument('--transcript', type=Path, required=True, help='Exact transcript of exactly that span')
    parser.add_argument('--output', type=Path, required=True, help='New directory; never overwritten')
    parser.add_argument('--no-separate', action='store_true')
    parser.add_argument('--no-denoise', action='store_true')
    parser.add_argument('--no-asr', action='store_true')
    arguments = parser.parse_args()
    result = clean(arguments.source, arguments.start, arguments.end, arguments.transcript.read_text(), arguments.output,
                   separate=not arguments.no_separate, denoise=not arguments.no_denoise, asr=not arguments.no_asr)
    print(json.dumps({key: result[key] for key in ('used_seconds', 'duration_seconds', 'gate_after', 'asr')}, ensure_ascii=False, indent=2))
