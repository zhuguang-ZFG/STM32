"""Procedural background-music beds: soft lo-fi/ambient pieces written and played entirely by this code.

Nothing is sampled or quoted. A mood fixes a key, a mode, a tempo and a short diatonic progression (generic chord
movement, stacked from the scale); every note is synthesized: warm pads (detuned band-limited wavetables through a
low-pass), a mellow FM electric piano or a modal pluck playing seeded arpeggio patterns, a sine bass, and in some moods
very soft drums (sine-sweep kick, brushed noise snare, band-limited shaker/hat). A synthetic stereo reverb, a gentle
master low-pass at 7.5 kHz (no harsh highs) and a loudness target finish the bed. Sections of 8 bars rotate density
(A sparse, B full, C varied, D thinner) and every progression returns to its first chord, so any whole number of bars
loops; loop=True wraps the release and reverb tails onto the start, making the render sample-exactly periodic.

The same mood and seed always render the same bed. The bed then goes through music_bed.prepare like any user music:
fades, sidechain ducking under the narration and optional dips."""
from pathlib import Path
import argparse
import hashlib
import json
import math
import wave
import numpy as np
from scipy import signal

SAMPLE_RATE = 48000
VERSION = 'music-synth-1'
TARGET_LUFS = -16.          # bed loudness before the layer gain and ducking
DEFAULT_GAIN = .25          # mixer gain when the job gives none: about 22 dB under the voice while it speaks
CEILING_DBFS = -1.
MAX_SECONDS = 1800.
SECTION_BARS = 8
MASTER_LOWPASS_HZ = 7500.
BASS_LEVEL = .5             # keeps the low end under the pads: a narrator's fundamental lives at 90-250 Hz

MAJOR, DORIAN, LYDIAN = (0, 2, 4, 5, 7, 9, 11), (0, 2, 3, 5, 7, 9, 10), (0, 2, 4, 6, 7, 9, 11)
HARMONIC_MINOR = (0, 2, 3, 5, 7, 8, 11)
# Section densities: (pad, keys/pluck, bass, drums) multipliers for A, B, C, D.
SECTIONS = ((1., .75, 0., 0.), (1., 1., 1., 1.), (.9, 1., 1., .8), (1., .6, .8, 0.))
MOODS = {
    'calm': {'description': 'slow, open, reassuring', 'tonic': 50, 'scale': MAJOR, 'bpm': 66, 'progression': (0, 3, 5, 4),
             'bars_per_chord': 2, 'extension': 6, 'pad': .9, 'cutoff': 1100, 'lead': 'ep', 'pattern': 'quarters',
             'lead_level': .45, 'bass': .3, 'drums': None, 'reverb': .34, 'swing': .5},
    'warm': {'description': 'lo-fi, friendly, a little nostalgic', 'tonic': 53, 'scale': MAJOR, 'bpm': 74, 'progression': (1, 4, 0, 5),
             'bars_per_chord': 1, 'extension': 6, 'pad': .6, 'cutoff': 1500, 'lead': 'ep', 'pattern': 'stabs',
             'lead_level': .6, 'bass': .55, 'drums': 'lofi', 'reverb': .26, 'swing': .58},
    'curious': {'description': 'light, playful, wondering', 'tonic': 55, 'scale': LYDIAN, 'bpm': 92, 'progression': (0, 1, 4, 5),
                'bars_per_chord': 1, 'extension': 6, 'pad': .5, 'cutoff': 1700, 'lead': 'pluck', 'pattern': 'broken_eighths',
                'lead_level': .62, 'bass': .35, 'drums': 'shaker', 'reverb': .3, 'swing': .54, 'decay': .45},
    'focused': {'description': 'steady pulse for explanations', 'tonic': 57, 'scale': DORIAN, 'bpm': 84, 'progression': (0, 3, 0, 6),
                'bars_per_chord': 1, 'extension': 6, 'pad': .55, 'cutoff': 1300, 'lead': 'pluck', 'pattern': 'pulse',
                'lead_level': .55, 'bass': .5, 'drums': 'steady', 'reverb': .22, 'swing': .5, 'decay': .6},
    'tense': {'description': 'low, suspended, unresolved', 'tonic': 50, 'scale': HARMONIC_MINOR, 'bpm': 70, 'progression': (0, 5, 3, 4),
              'bars_per_chord': 2, 'extension': 8, 'pad': .85, 'cutoff': 850, 'lead': 'pluck', 'pattern': 'sparse',
              'lead_level': .5, 'bass': .6, 'drums': 'heartbeat', 'reverb': .3, 'swing': .5, 'decay': .8},
}


def seed_for(*parts):
    return int.from_bytes(hashlib.sha256('|'.join(str(part) for part in parts).encode()).digest()[:8], 'little')


def frequency(midi):
    return 440. * 2 ** ((midi - 69) / 12)


def chord_tones(mood, degree):
    """Diatonic chord on a scale degree: root, third, fifth and the mood's extension (7th or 9th), as pitch offsets."""
    scale = mood['scale']
    tones = []
    for step in (0, 2, 4, mood['extension']):
        index = degree + step
        tones.append(scale[index % 7] + 12 * (index // 7))
    return tones


def voiced(tones, tonic, low):
    """Close voicing: every chord tone placed inside one octave starting at `low` (smooth voice leading for free)."""
    notes = []
    for tone in tones:
        midi = tonic + tone
        while midi < low:
            midi += 12
        while midi >= low + 12:
            midi -= 12
        notes.append(midi)
    return sorted(set(notes))


_TABLES = {}


def wavetable(harmonics, size=2048):
    """One band-limited cycle (soft saw: 1/k^1.2 partials), cached by partial count."""
    if harmonics not in _TABLES:
        phase = np.arange(size) / size
        cycle = sum(np.sin(2 * np.pi * k * phase) / k ** 1.2 for k in range(1, harmonics + 1))
        _TABLES[harmonics] = cycle / np.abs(cycle).max()
    return _TABLES[harmonics]


def oscillator(table, phase):
    position = (phase % 1.) * len(table)
    whole = position.astype(np.int64)
    part = position - whole
    return table[whole] * (1 - part) + table[(whole + 1) % len(table)] * part


class Score:
    """Stereo dry and reverb-send buffers that notes are added into at sample positions."""
    def __init__(self, frames, tail):
        self.frames = frames
        self.dry = np.zeros((frames + tail, 2), np.float32)
        self.send = np.zeros((frames + tail, 2), np.float32)

    def add(self, at, stereo, send):
        at = max(0, int(at))
        end = min(len(self.dry), at + len(stereo))
        if end > at:
            self.dry[at:end] += stereo[:end - at].astype(np.float32)
            self.send[at:end] += (send * stereo[:end - at]).astype(np.float32)


def pan(mono, position):
    angle = (np.clip(position, -1, 1) + 1) * np.pi / 4
    return np.stack([mono * np.cos(angle), mono * np.sin(angle)], axis=1)


def pad_chord(notes, seconds, cutoff, rng):
    """Detuned wavetable pair per note plus a sine body; 1.4 s swell, 1.1 s release, low-passed at the mood cutoff."""
    release = 1.1
    count = int((seconds + 4 * release) * SAMPLE_RATE)
    t = np.arange(count) / SAMPLE_RATE
    attack = np.minimum(1., t / 1.4)
    envelope = (.5 - .5 * np.cos(np.pi * attack)) * np.where(t < seconds, 1., np.exp(-(t - seconds) / release))
    left, right = np.zeros(count), np.zeros(count)
    for midi in notes:
        base = frequency(midi)
        harmonics = max(1, int(min(4000., 2.5 * cutoff) / base))
        table = wavetable(harmonics)
        for cents, side in ((-6, .38), (6, .62)):
            drift = 1.5 * np.sin(2 * np.pi * rng.uniform(.05, .17) * t + rng.uniform(0, 2 * np.pi))
            rate = base * 2 ** ((cents + drift) / 1200)
            phase = np.cumsum(rate) / SAMPLE_RATE + rng.uniform()
            voice = oscillator(table, phase) * .5
            left += voice * math.cos(side * np.pi / 2)
            right += voice * math.sin(side * np.pi / 2)
        body = .35 * np.sin(2 * np.pi * base * t + rng.uniform(0, 2 * np.pi))
        left += body * .707
        right += body * .707
    sos = signal.butter(2, cutoff, 'lowpass', fs=SAMPLE_RATE, output='sos')
    stereo = np.stack([signal.sosfilt(sos, left), signal.sosfilt(sos, right)], axis=1)
    return stereo * envelope[:, None] / max(1, len(notes)) ** .5


def electric_piano(midi, seconds, velocity, rng):
    """Two-operator FM (1:1) with a fast-decaying index: a soft bell attack settling into a near-sine tone."""
    base = frequency(midi)
    decay = float(np.clip(1.8 * (220 / base) ** .5, .6, 2.4))
    count = int((seconds + .6) * SAMPLE_RATE)
    t = np.arange(count) / SAMPLE_RATE
    index = (1.4 * velocity + .3) * np.exp(-t / .22) + .12
    tone = np.sin(2 * np.pi * base * t + index * np.sin(2 * np.pi * base * t + rng.uniform(0, 2 * np.pi)))
    envelope = (1 - np.exp(-t / .002)) * np.exp(-t / decay) * np.where(t < seconds, 1., np.exp(-(t - seconds) / .15))
    return tone * envelope * velocity


def pluck(midi, velocity, decay, rng):
    """Modal pluck: six slightly stretched partials, higher ones dying faster (soft kalimba/muted-guitar colour)."""
    base = frequency(midi)
    count = int(4 * decay * SAMPLE_RATE)
    t = np.arange(count) / SAMPLE_RATE
    tone = np.zeros(count)
    for k in range(1, 7):
        partial = k * base * (1 + .0004 * k * k)
        if partial > 5000:
            break
        tone += rng.uniform(.8, 1.2) / k ** 1.6 * np.exp(-t / (decay / k ** .9)) * np.sin(2 * np.pi * partial * t + rng.uniform(0, 2 * np.pi))
    return tone * np.minimum(1., t / .0015) * velocity


def bass(midi, seconds, velocity):
    base = frequency(midi)
    count = int((seconds + .3) * SAMPLE_RATE)
    t = np.arange(count) / SAMPLE_RATE
    tone = np.sin(2 * np.pi * base * t) + .25 * np.sin(4 * np.pi * base * t) + .06 * np.sin(6 * np.pi * base * t)
    envelope = np.minimum(1., t / .02) * (.75 + .25 * np.exp(-t / .3)) * np.where(t < seconds, 1., np.exp(-(t - seconds) / .08))
    return tone * envelope * velocity


def drum(kind, velocity, rng):
    if kind == 'kick':
        t = np.arange(int(.5 * SAMPLE_RATE)) / SAMPLE_RATE
        phase = 2 * np.pi * np.cumsum(46 + 70 * np.exp(-t / .035)) / SAMPLE_RATE
        return np.sin(phase) * np.exp(-t / .16) * (1 - np.exp(-t / .0015)) * velocity
    if kind == 'low_kick':  # heartbeat: lower, rounder
        t = np.arange(int(.6 * SAMPLE_RATE)) / SAMPLE_RATE
        phase = 2 * np.pi * np.cumsum(40 + 35 * np.exp(-t / .04)) / SAMPLE_RATE
        return np.sin(phase) * np.exp(-t / .2) * (1 - np.exp(-t / .004)) * velocity
    bands = {'brush': (900, 4000, .09, .005), 'hat': (4500, 8500, .03, .001), 'shaker': (3000, 7000, .05, .012)}
    low, high, decay, attack = bands[kind]
    t = np.arange(int(6 * decay * SAMPLE_RATE)) / SAMPLE_RATE
    sos = signal.butter(2, (low, high), 'bandpass', fs=SAMPLE_RATE, output='sos')
    noise = signal.sosfilt(sos, rng.standard_normal(len(t))) * 2.5
    hit = noise * np.exp(-t / decay) * (1 - np.exp(-t / attack))
    if kind == 'brush':
        hit += .3 * np.sin(2 * np.pi * 190 * t) * np.exp(-t / .05)
    return hit * velocity


def lead_steps(pattern, rng):
    """(16th step, chord-tone index, velocity) per bar for the lead instrument."""
    if pattern == 'quarters':
        order = [0, 1, 2, 3] if rng.uniform() < .5 else [0, 2, 1, 3]
        return [(step, order[number], rng.uniform(.5, .75)) for number, step in enumerate((0, 4, 8, 12)) if number == 0 or rng.uniform() > .2]
    if pattern == 'stabs':
        return [(step, None, rng.uniform(.5, .7)) for step in (0, 7, 10) if step == 0 or rng.uniform() > .25]
    if pattern == 'broken_eighths':
        shape = [0, 2, 1, 3, 2, 4, 3, 1] if rng.uniform() < .5 else [0, 1, 2, 4, 3, 2, 1, 2]
        return [(2 * number, shape[number], rng.uniform(.45, .7) * (1.1 if number % 2 else 1.)) for number in range(8) if rng.uniform() > .15]
    if pattern == 'pulse':
        shape = [0, 2, 0, 3, 0, 2, 0, 4]
        return [(2 * number, shape[number], (.7 if number % 2 == 0 else .5) * rng.uniform(.85, 1.)) for number in range(8)]
    if pattern == 'sparse':
        return [(2 * number, int(rng.integers(0, 4)), rng.uniform(.4, .65)) for number in range(8) if rng.uniform() < .45 or number == 0]
    raise ValueError(pattern)


def drum_steps(style, rng):
    hits = {'lofi': [('kick', 0, .8), ('brush', 4, .45), ('kick', 10, .55), ('brush', 12, .45)] +
                    [('hat', step, .22 if step % 4 else .3) for step in range(0, 16, 2)],
            'shaker': [('shaker', step, .3 if step % 4 else .18) for step in range(0, 16, 2)] + [('kick', 0, .35)],
            'steady': [('kick', 0, .7), ('kick', 8, .55)] + [('hat', step, .18 if step % 4 else .25) for step in range(0, 16, 2)],
            'heartbeat': [('low_kick', 0, .5), ('low_kick', 3, .32)]}[style]
    return [(kind, step, velocity * rng.uniform(.85, 1.1)) for kind, step, velocity in hits if kind not in ('hat', 'shaker') or rng.uniform() > .08]


def reverb_response(seconds, rng):
    """Decorrelated stereo noise tail, -60 dB at `seconds`, darkened and thinned, with a 25 ms pre-delay."""
    count = int(seconds * SAMPLE_RATE)
    t = np.arange(count) / SAMPLE_RATE
    response = rng.standard_normal((count, 2)) * np.exp(-6.9 * t / seconds)[:, None]
    response = signal.sosfilt(signal.butter(2, 4500, 'lowpass', fs=SAMPLE_RATE, output='sos'), response, axis=0)
    response = signal.sosfilt(signal.butter(1, 180, 'highpass', fs=SAMPLE_RATE, output='sos'), response, axis=0)
    response[:, 1] = .6 * response[:, 0] + .8 * response[:, 1]  # partly correlated: wide but mono-safe
    response = np.vstack([np.zeros((int(.025 * SAMPLE_RATE), 2)), response])
    return response / np.sqrt((response ** 2).sum(axis=0))


def soft_ceiling(samples, ceiling, knee=.7):
    start = knee * ceiling
    magnitude = np.abs(samples)
    over = magnitude > start
    samples[over] = np.sign(samples[over]) * (start + (ceiling - start) * np.tanh((magnitude[over] - start) / (ceiling - start)))
    return samples


def render(mood_name, seconds, seed=0, loop=False, first_bar=0):
    """Stereo float32 bed of `seconds` (rounded up to whole bars when loop=True) and a record of what was played.
    first_bar starts the arrangement later (e.g. SECTION_BARS for a preview of the full section B); bars keep their
    absolute numbers, so a bar sounds the same whatever the render starts or ends with."""
    if mood_name not in MOODS:
        raise ValueError(f'Unknown builtin music mood {mood_name!r}; choose one of ' + ', '.join(MOODS))
    if not math.isfinite(seconds) or not 0 < seconds <= MAX_SECONDS:
        raise ValueError(f'Builtin music renders 0..{MAX_SECONDS:g} seconds')
    mood = MOODS[mood_name]
    beat = 60. / mood['bpm']
    bar = 4 * beat
    bars = math.ceil(seconds / bar - 1e-9)
    frames = round(bars * bar * SAMPLE_RATE) if loop else round(seconds * SAMPLE_RATE)
    tail = int(4 * SAMPLE_RATE)
    score = Score(frames, tail)
    step_seconds = beat / 4
    chords = []
    if not isinstance(first_bar, int) or first_bar < 0:
        raise ValueError('first_bar must be a nonnegative integer')
    for local in range(bars):
        number = first_bar + local
        section = (number // SECTION_BARS) % len(SECTIONS)
        density = SECTIONS[section]
        rng = np.random.default_rng(seed_for(VERSION, mood_name, seed, 'bar', number))
        position = (number // mood['bars_per_chord']) % len(mood['progression'])
        degree = mood['progression'][position]
        tones = chord_tones(mood, degree)
        start = local * bar
        swell = .92 + .08 * math.sin(2 * math.pi * number / (2 * SECTION_BARS * len(SECTIONS)))  # slow breathing
        if number % mood['bars_per_chord'] == 0 and density[0]:
            pad_notes = voiced(tones, mood['tonic'], mood['tonic'] + 5)
            length = mood['bars_per_chord'] * bar
            score.add(start * SAMPLE_RATE, pad_chord(pad_notes, length, mood['cutoff'], rng) * mood['pad'] * density[0] * swell * .5, .5)
            chords.append(degree)
        lead_notes = voiced(tones, mood['tonic'], mood['tonic'] + 12)
        lead_notes = lead_notes + [note + 12 for note in lead_notes[:2]]
        if density[1]:
            for step, tone, velocity in lead_steps(mood['pattern'], rng):
                swung = step + (2 * mood['swing'] - 1) * 2 if step % 4 == 2 else step
                at = (start + swung * step_seconds + rng.normal(0, .004)) * SAMPLE_RATE
                level = velocity * mood['lead_level'] * density[1] * swell
                if mood['lead'] == 'ep':
                    chord = lead_notes[:4] if tone is None else [lead_notes[tone % len(lead_notes)]]
                    for offset, midi in enumerate(chord):  # stabs are lightly strummed
                        held = (3 if tone is None else 4) * step_seconds * 1.8
                        voice = electric_piano(midi, held, level / len(chord) ** .5, rng)
                        tremolo = 1 + .18 * np.sin(2 * np.pi * 4.2 * (at / SAMPLE_RATE + np.arange(len(voice)) / SAMPLE_RATE))
                        score.add(at + offset * .012 * SAMPLE_RATE, pan(voice, .25 * np.sin(2 * np.pi * .9 * np.arange(len(voice)) / SAMPLE_RATE)) * tremolo[:, None] * .5, .35)
                else:
                    midi = lead_notes[tone % len(lead_notes)]
                    score.add(at, pan(pluck(midi, level, mood['decay'], rng), rng.uniform(-.35, .35)) * .5, .35)
        if mood['bass'] and density[2]:
            root = mood['tonic'] - 12 + mood['scale'][degree % 7]
            while root >= mood['tonic']:
                root -= 12
            hits = [(0, 7), (8, 6)] if mood['drums'] != 'heartbeat' else [(0, 3), (3, 2), (8, 3), (11, 2)]
            for step, length in hits:
                tone = bass(root, length * step_seconds, BASS_LEVEL * mood['bass'] * density[2] * rng.uniform(.85, 1.))
                score.add((start + step * step_seconds) * SAMPLE_RATE, pan(tone, 0.) * .5, 0.)
        if mood['drums'] and density[3]:
            for kind, step, velocity in drum_steps(mood['drums'], rng):
                swung = step + (2 * mood['swing'] - 1) * 2 if step % 4 == 2 else step
                at = (start + swung * step_seconds + rng.normal(0, .003)) * SAMPLE_RATE
                hit = drum(kind, velocity * density[3] * .35, rng)
                score.add(at, pan(hit, .25 if kind in ('hat', 'shaker') else 0.) * .5, .12)
    rng = np.random.default_rng(seed_for(VERSION, mood_name, seed, 'reverb'))
    response = reverb_response(2.6, rng)
    wet = np.stack([signal.oaconvolve(score.send[:, channel], response[:, channel])[:len(score.send)] for channel in (0, 1)], axis=1)
    mixed = score.dry.astype(np.float64) + mood['reverb'] * 3 * wet
    del wet
    if loop:  # wrap release and reverb tails onto the start: the bed becomes exactly periodic
        overflow = mixed[frames:]
        mixed = mixed[:frames].copy()
        for offset in range(0, len(overflow), frames):
            part = overflow[offset:offset + frames]
            mixed[:len(part)] += part
    else:
        mixed = mixed[:frames]
    master = signal.butter(2, (35, MASTER_LOWPASS_HZ), 'bandpass', fs=SAMPLE_RATE, output='sos')
    if loop:  # filter two periods and keep the second, so the filter state is periodic too
        mixed = signal.sosfilt(master, np.vstack([mixed, mixed]), axis=0)[frames:]
    else:
        mixed = signal.sosfilt(master, mixed, axis=0)
    from audio_gate import loudness_lufs
    measured = loudness_lufs(mixed)
    mixed *= 10 ** ((TARGET_LUFS - measured) / 20)
    soft_ceiling(mixed, 10 ** (CEILING_DBFS / 20))
    record = {'version': VERSION, 'mood': mood_name, 'seed': seed, 'loop': loop, 'bpm': mood['bpm'], 'key_midi': mood['tonic'],
              'bars': bars, 'first_bar': first_bar, 'seconds': round(frames / SAMPLE_RATE, 3), 'progression_degrees': list(mood['progression']),
              'target_lufs': TARGET_LUFS, 'loudness_lufs': loudness_lufs(mixed),
              'peak_dbfs': round(float(20 * np.log10(np.abs(mixed).max() + 1e-12)), 2)}
    return mixed.astype(np.float32), record


def write_wav(path, stereo, fade_in=0., fade_out=0.):
    stereo = np.array(stereo, dtype=np.float64)
    if fade_in > 0:
        count = min(len(stereo), round(fade_in * SAMPLE_RATE))
        stereo[:count] *= (.5 - .5 * np.cos(np.pi * np.arange(count) / count))[:, None]
    if fade_out > 0:
        count = min(len(stereo), round(fade_out * SAMPLE_RATE))
        stereo[len(stereo) - count:] *= (.5 + .5 * np.cos(np.pi * np.arange(count) / count))[:, None]
    data = np.rint(np.clip(stereo, -1, 32767 / 32768) * 32768).astype('<i2')
    with wave.open(str(path), 'wb') as stream:
        stream.setparams((2, 2, SAMPLE_RATE, 0, 'NONE', 'not compressed'))
        stream.writeframes(data.tobytes())


def parse_source(source):
    """'builtin:<mood>' -> mood name, else None (a file path)."""
    if not isinstance(source, str) or not source.startswith('builtin:'):
        return None
    mood = source.split(':', 1)[1].strip()
    if mood not in MOODS:
        raise ValueError(f'Unknown builtin music {source!r}; choose builtin:' + ', builtin:'.join(MOODS))
    return mood


def render_source(work, music):
    """Generate the raw bed for audio.music {"source": "builtin:<mood>", "seed": n} at the narration's duration as
    work/audio/music-<mood>-seed<n>.wav. Returns (path, record); music_bed.prepare then fades and ducks it."""
    mood = parse_source(music.get('source'))
    seed = music.get('seed', 0)
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ValueError('audio.music.seed must be an integer')
    narration = Path(work) / 'narration.wav'
    if not narration.is_file():
        raise ValueError('Builtin music renders during build, after the narration is assembled; no work/narration.wav yet')
    with wave.open(str(narration), 'rb') as stream:
        seconds = stream.getnframes() / stream.getframerate()
    stereo, record = render(mood, seconds, seed, loop=False)
    audio = Path(work) / 'audio'
    audio.mkdir(parents=True, exist_ok=True)
    path = audio / f'music-{mood}-seed{seed}.wav'
    write_wav(path, stereo)
    record['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    return path, record


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Render a procedural music bed (preview or loop) to a 48 kHz stereo wav.')
    parser.add_argument('mood', choices=sorted(MOODS))
    parser.add_argument('--seconds', type=float, default=20.)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--loop', action='store_true', help='Whole bars, exactly periodic (tails wrapped to the start)')
    parser.add_argument('--fade', type=float, default=0., help='Fade in and out (seconds) for listening previews')
    parser.add_argument('--first-bar', type=int, default=0, help=f'Start later in the arrangement ({SECTION_BARS} = full section B)')
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    stereo, record = render(arguments.mood, arguments.seconds, arguments.seed, arguments.loop, arguments.first_bar)
    write_wav(arguments.output, stereo, arguments.fade, 2 * arguments.fade)
    print(json.dumps(record, ensure_ascii=False))
