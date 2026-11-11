"""Prepare one job's background-music bed: loop with a crossfade, fade in and out, duck under the
narration, and optional level dips. Hosts used to script this by hand for every film; measuring the
same chain here makes the bed deterministic and comparable across jobs. Music stays opt-in: the
explicit user instruction is still checked by audio_contract before this runs."""
from pathlib import Path
import hashlib
import json
import math
import subprocess
import wave
import numpy as np

SAMPLE_RATE = 48000
DEFAULT_CROSSFADE_SECONDS = 4.
DEFAULT_FADE_IN_SECONDS = 1.2
DEFAULT_FADE_OUT_SECONDS = 3.
DIP_LEVEL = .06       # a dip leaves about 6% of the music under the line it must clear
DIP_RAMP_SECONDS = .25
# Ducking under speech: gentle pressure that recovers between sentences.
SIDECHAIN = 'sidechaincompress=threshold=0.05:ratio=3:attack=25:release=350:makeup=1:link=average'


def source_seconds(path):
    output = subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', str(path)])
    seconds = float(json.loads(output)['format']['duration'])
    if not math.isfinite(seconds) or seconds <= 0:
        raise ValueError(f'Background music has no measurable duration: {path}')
    return seconds


def bounded(value, low, high, name):
    value = float(value)
    if not math.isfinite(value) or not low <= value <= high:
        raise ValueError(f'audio.music.{name} must be within {low}..{high}')
    return value


def dips_from(music, duration):
    dips = []
    for entry in music.get('dips') or []:
        if not isinstance(entry, (list, tuple)) or len(entry) != 2:
            raise ValueError('Each audio.music dip must be a [start, end] pair of seconds')
        start, end = float(entry[0]), float(entry[1])
        if not (math.isfinite(start) and math.isfinite(end) and 0 <= start < end <= duration + .001):
            raise ValueError(f'Music dip {entry} must lie inside the narration duration {duration:.2f}s')
        dips.append((start, min(end, duration)))
    return dips


def loop_music(samples, frames, overlap):
    """Crossfade decoded stereo samples at exact frame offsets, independent of FFmpeg filter scheduling."""
    if samples.ndim != 2 or samples.shape[1] != 2 or not len(samples) or not np.isfinite(samples).all():
        raise ValueError('Background music must decode to nonempty finite stereo samples')
    overlap = max(0, min(int(overlap), len(samples) // 3))
    stride = len(samples) - overlap
    repeats = max(1, math.ceil((frames - overlap) / stride))
    if repeats > 64:
        raise ValueError('Background music is far shorter than the film; provide a longer source'
                         ' instead of looping dozens of times')
    looped = np.empty((frames, 2), dtype=np.float32)
    first = min(frames, len(samples))
    looped[:first] = samples[:first]
    edge = len(samples)
    while edge < frames:
        start = edge - overlap
        count = min(overlap, frames - start)
        if count:
            weights = (np.arange(count, dtype=np.float32) + 1)[:, None] / (overlap + 1)
            looped[start:start + count] = looped[start:start + count] * (1 - weights) + samples[:count] * weights
        copied = min(stride, frames - edge)
        looped[edge:edge + copied] = samples[overlap:overlap + copied]
        edge = start + len(samples)
    return looped


def apply_dips(bed, dips):
    """Lower the bed inside each dip with short ramps; min-combined so overlapping dips never stack."""
    with wave.open(str(bed), 'rb') as stream:
        parameters = stream.getparams()
        samples = np.frombuffer(stream.readframes(stream.getnframes()), dtype='<i2').reshape(-1, 2).astype(np.float32)
    envelope = np.ones(len(samples), np.float32)
    ramp = round(DIP_RAMP_SECONDS * SAMPLE_RATE)
    for start, end in dips:
        first, last = min(len(samples), round(start * SAMPLE_RATE)), min(len(samples), round(end * SAMPLE_RATE))
        window = np.ones(len(samples), np.float32)
        window[first:last] = DIP_LEVEL
        left = np.arange(max(0, first - ramp), first)
        right = np.arange(last, min(len(samples), last + ramp))
        if len(left):
            window[left] = np.linspace(1., DIP_LEVEL, len(left) + 1)[1:]
        if len(right):
            window[right] = np.linspace(DIP_LEVEL, 1., len(right) + 1)[:-1]
        envelope = np.minimum(envelope, window)
    mixed = np.rint(samples * envelope[:, None]).clip(-32768, 32767).astype('<i2')
    with wave.open(str(bed), 'wb') as stream:
        stream.setparams(parameters)
        stream.writeframes(mixed.tobytes())


def prepare(root, work, music):
    """Write work/music-bed.wav from music['source'] at the assembled narration's exact duration.

    Returns (bed path, report). The report carries the source and bed hashes, the effective
    parameters after clamping and the ffmpeg filter, so a job can be reproduced or audited later."""
    root, work = Path(root), Path(work)
    source = Path(music['source'])
    source = source.resolve() if source.is_absolute() else (root / source).resolve()
    if not source.is_file():
        raise ValueError(f'Background music source does not exist: {music["source"]}')
    narration = work / 'narration.wav'
    if not narration.is_file():
        raise ValueError('Music preparation runs during build, after the narration is assembled; no work/narration.wav yet')
    with wave.open(str(narration), 'rb') as stream:
        duration = stream.getnframes() / stream.getframerate()
    source_length = source_seconds(source)
    crossfade = min(bounded(music.get('crossfade_seconds', DEFAULT_CROSSFADE_SECONDS), .5, 10., 'crossfade_seconds'),
                    max(.25, source_length / 3))
    fade_in = min(bounded(music.get('fade_in_seconds', DEFAULT_FADE_IN_SECONDS), 0., 10., 'fade_in_seconds'), duration / 3)
    fade_out = min(bounded(music.get('fade_out_seconds', DEFAULT_FADE_OUT_SECONDS), 0., 10., 'fade_out_seconds'), duration / 3)
    duck = bool(music.get('duck', True))
    dips = dips_from(music, duration)
    decoded = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(source), '-ar', str(SAMPLE_RATE), '-ac', '2',
                              '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    samples = np.frombuffer(decoded, dtype='<f4').reshape(-1, 2)
    frames = round(duration * SAMPLE_RATE)
    overlap = min(round(crossfade * SAMPLE_RATE), len(samples) // 3)
    looped = loop_music(samples, frames, overlap)
    chain = f'[0:a]atrim=end_sample={frames},asetpts=PTS-STARTPTS'
    if fade_in > 0:
        chain += f',afade=t=in:d={fade_in:g}'
    if fade_out > 0:
        chain += f',afade=t=out:st={duration - fade_out:.3f}:d={fade_out:g}'
    chain += '[bed]'
    command = ['ffmpeg', '-y', '-v', 'error', '-f', 'f32le', '-ar', str(SAMPLE_RATE), '-ac', '2', '-i', 'pipe:0']
    mapping = '[bed]'
    if duck:
        command += ['-i', str(narration)]
        # Some FFmpeg versions stop the sidechain before its buffered tail drains.
        # Feed one second of guard silence, then trim the result to the exact sample count.
        chain += f';[bed]apad=pad_dur=1[padded];[1:a]apad=pad_dur=1[sidechain];[padded][sidechain]{SIDECHAIN},atrim=end_sample={frames}[ducked]'
        mapping = '[ducked]'
    bed = work / 'music-bed.wav'
    subprocess.run(command + ['-filter_complex', chain, '-map', mapping, '-ar', str(SAMPLE_RATE), '-ac', '2',
                              '-c:a', 'pcm_s16le', str(bed)], input=looped.astype('<f4', copy=False).tobytes(), check=True)
    if dips:
        apply_dips(bed, dips)
    with wave.open(str(bed), 'rb') as stream:
        if (stream.getframerate(), stream.getnchannels()) != (SAMPLE_RATE, 2):
            raise ValueError('Prepared music bed must be 48 kHz stereo')
        if abs(stream.getnframes() / stream.getframerate() - duration) > .05:
            raise ValueError('Prepared music bed drifted from the narration duration; keep the raw music source unchanged')
    report = {'source': str(source), 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
              'bed': str(bed.resolve()), 'bed_sha256': hashlib.sha256(bed.read_bytes()).hexdigest(),
              'duration_seconds': round(duration, 3), 'crossfade_seconds': round(overlap / SAMPLE_RATE, 3),
              'loop_method': 'pcm_linear_crossfade',
              'fade_in_seconds': round(fade_in, 3), 'fade_out_seconds': round(fade_out, 3),
              'duck': duck, 'dips': [list(dip) for dip in dips], 'filter': chain}
    (work / 'music-preparation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    return bed, report
