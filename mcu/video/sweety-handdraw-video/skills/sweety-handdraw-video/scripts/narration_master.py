"""Keep one complete narration waveform authoritative for every visual timing.

The master is generated per semantic chunk (one beat, or sentences of a long beat), each gated and
regenerated on failure, then joined with measured pauses; long one-shot generation drifts and buzzes.
"""
from pathlib import Path
import hashlib
import json
import math
import re
import subprocess
import wave
import numpy as np

SAMPLE_RATE = 48000
MAX_CHUNK_CHARS = 100
MIN_CHUNK_CHARS = 8
SENTENCE_END = '。！？!?…'
CLAUSE_END = '，,、；;：:'
# Spoken characters per second of speech span. Accepted VoxCPM2 films ran 6.3 (snake) and 6.7 (wolf)
# chars/s overall and 5.9-7.5 per sentence group, so 6 would reject both accepted voices; skipped or
# babbled text is caught by ASR coverage, the rate only flags gross stretching or truncation.
SPEECH_RATE_RANGE = (3., 8.)
GENERATION_ATTEMPTS = 3
EDGE_SECONDS = (.06, .1)
# Silence between chunks (speech end to speech start). Measured at punctuation with align.activity:
# accepted VoxCPM2 films (snake, wolf) sentence median .15/.23 s, clause .15/.21 s; 89 sentence ends of
# clean human long-form narration median .60 s. Sentence/beat stay near the model's own cadence, a page
# turn takes the human sentence pause; jobs may override per kind (join_pause_seconds).
JOIN_PAUSE_SECONDS = {'clause': .2, 'sentence': .3, 'beat': .4, 'page': .6}
END_TAIL_SECONDS = .3
# Where a chunk really ends. The activity threshold alone cut 0.1 s after "speech", often through a breath or the
# model's own after-sound, with no fade: listeners heard a tick or a clipped extra syllable at sentence ends.
TAIL_QUIET_DB = -40.      # the last syllable has ended once the level stays this far under the chunk peak...
TAIL_QUIET_SECONDS = .03  # ...for this long
TAIL_BURST_DB = -30.      # a sound this loud after that quiet is not speech we asked for (an artifact after the sentence)
TAIL_LOUD_DB = -25.       # a chunk that still ends this loud, with no quiet after its last word, was cut off
TAIL_KEEP_SECONDS = .12   # natural decay and breath kept after the last syllable
FADE_OUT_SECONDS = .05    # shortest raised-cosine fade at a cut, so no edge lands on a sound
FADE_IN_SECONDS = .01


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def script_text(manifest):
    return ''.join(beat['text'] for page in manifest['pages'] for beat in page['beats'])


def generation_target(root, manifest):
    """Master path inside the job plus the complete script; the closing must already be in it."""
    settings = manifest.get('narration', {})
    target = (Path(root) / settings.get('source', 'inputs/narration/master.wav')).resolve()
    if not target.is_relative_to(Path(root).resolve()):
        raise ValueError('Generated narration master must stay inside the job')
    text = script_text(manifest)
    closing = manifest.get('ending', {}).get('closing_text')
    if closing and not text.endswith(closing):
        raise ValueError('Add the requested closing to the complete script before generating narration')
    return target, text


def pieces(text, breaks):
    return re.findall('[^' + breaks + ']+[' + breaks + ']*|[' + breaks + ']+', text)


def pack(parts, limit):
    packed = []
    for part in parts:
        if packed and len(packed[-1]) + len(part) <= limit:
            packed[-1] += part
        else:
            packed.append(part)
    return packed


def split_long(text, limit=MAX_CHUNK_CHARS):
    """A beat over the limit splits at sentence ends; only a single over-long sentence splits at clauses."""
    if len(text) <= limit:
        return [text]
    parts = []
    for sentence in pieces(text, SENTENCE_END):
        parts += [sentence] if len(sentence) <= limit else pack(pieces(sentence, CLAUSE_END), limit)
    return pack(parts, limit)


def narration_chunks(manifest, limit=MAX_CHUNK_CHARS):
    """Synthesis units: one beat each; beats ending mid-sentence or tiny ones join the next beat."""
    from align import spoken
    chunks = []
    for page_index, page in enumerate(manifest['pages']):
        for beat in page['beats']:
            for part, text in enumerate(split_long(beat['text'], limit)):
                unit = {'beat': beat['id'], 'page': page_index, 'text': text}
                last = chunks[-1] if chunks else None
                if last and part == 0 and (last['text'][-1] not in SENTENCE_END or len(spoken(last['text'])) < MIN_CHUNK_CHARS):
                    last['text'] += text
                    last['units'].append(unit)
                    continue
                join = None if not last else 'clause' if last['text'][-1] not in SENTENCE_END else 'sentence' if last['units'][-1]['beat'] == beat['id'] \
                    else 'beat' if last['units'][-1]['page'] == page_index else 'page'
                chunks.append({'text': text, 'units': [unit], 'join': join})
    if len(chunks) > 1 and len(spoken(chunks[-1]['text'])) < MIN_CHUNK_CHARS:
        tail = chunks.pop()
        chunks[-1]['text'] += tail['text']
        chunks[-1]['units'] += tail['units']
    return chunks


def to_rate(samples, rate):
    from scipy.signal import resample_poly
    samples = np.asarray(samples, dtype=np.float64).reshape(-1)
    if rate == SAMPLE_RATE:
        return samples
    factor = math.gcd(int(rate), SAMPLE_RATE)
    return resample_poly(samples, SAMPLE_RATE // factor, int(rate) // factor)


def write_pcm(path, samples):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.stem + '.writing.wav')
    with wave.open(str(temporary), 'wb') as stream:
        stream.setparams((1, 2, SAMPLE_RATE, 0, 'NONE', 'not compressed'))
        stream.writeframes(np.clip(np.rint(np.asarray(samples) * 32767), -32768, 32767).astype('<i2').tobytes())
    temporary.replace(path)


def read_pcm(path):
    with wave.open(str(path)) as stream:
        return np.frombuffer(stream.readframes(stream.getnframes()), dtype='<i2').astype(np.float64) / 32767


def frame_levels(samples, rate=SAMPLE_RATE):
    """Level of 20 ms frames every 10 ms, in dB under the chunk peak."""
    hop, width = round(.01 * rate), round(.02 * rate)
    if len(samples) < width:
        return np.full(1, -120.)
    peak = max(float(np.abs(samples).max()), 1e-9)
    starts = np.arange(0, len(samples) - width + 1, hop)
    energy = np.concatenate([[0.], np.cumsum(np.asarray(samples, float) ** 2)])
    rms = np.sqrt(np.maximum(energy[starts + width] - energy[starts], 0.) / width)
    return 20 * np.log10(np.maximum(rms, 1e-9) / peak)


def speech_tail(samples, words=None, rate=SAMPLE_RATE):
    """(cut seconds or None, report). The last syllable ends at the first quiet run after the last word starts; a burst
    after that quiet is dropped; None when the chunk still ends loud with no quiet after its last word (cut off)."""
    from align import speech_span
    levels = frame_levels(samples, rate)
    count = len(levels)
    duration = len(samples) / rate
    if words:
        anchor = float(words[-1]['start'])
    else:
        anchor = max(0., speech_span(samples, rate)[1] - .4)
    quiet = max(1, round(TAIL_QUIET_SECONDS / .01))
    first = min(count - 1, max(0, int(anchor / .01)))
    end_frame = None
    for frame in range(first, count - quiet + 1):
        if (levels[frame:frame + quiet] < TAIL_QUIET_DB).all():
            end_frame = frame
            break
    if end_frame is None:
        if levels[-3:].max() > TAIL_LOUD_DB:
            return None, {'status': 'cut_off', 'final_level_db': round(float(levels[-3:].max()), 1)}
        end_frame = first + int(np.argmin(levels[first:]))
    speech_end = end_frame * .01 + .01
    burst = next((frame for frame in range(end_frame + quiet, count) if levels[frame] > TAIL_BURST_DB), None)
    cut = speech_end + TAIL_KEEP_SECONDS
    if burst is not None:
        cut = min(cut, burst * .01 - .01)
    cut = min(max(cut, speech_end + .02), duration)
    report = {'status': 'artifact_dropped' if burst is not None and burst * .01 < duration else 'clean', 'speech_end': round(speech_end, 3),
              'cut': round(cut, 3), 'dropped_seconds': round(duration - cut, 3)}
    return cut, report


def finish_edges(samples, cut, speech_end, rate=SAMPLE_RATE):
    """Cut at `cut` with a raised-cosine fade from the end of speech (at least FADE_OUT_SECONDS) and a short fade-in."""
    samples = np.array(samples[:max(1, round(cut * rate))], float)
    fade = max(round(FADE_OUT_SECONDS * rate), len(samples) - round(speech_end * rate))
    fade = min(fade, len(samples))
    if fade > 1:
        samples[-fade:] *= .5 + .5 * np.cos(np.linspace(0, np.pi, fade))
    lead = min(round(FADE_IN_SECONDS * rate), len(samples))
    if lead > 1:
        samples[:lead] *= .5 - .5 * np.cos(np.linspace(0, np.pi, lead))
    return samples


def clean_edges(samples, words=None, rate=SAMPLE_RATE):
    """(samples ending cleanly after the last syllable, report); samples None when the chunk was cut off mid-sound."""
    cut, report = speech_tail(samples, words, rate)
    if cut is None:
        return None, report
    return finish_edges(samples, cut, report['speech_end'], rate), report


def check_chunk(samples, text, path, asr):
    """Noise gate, speech rate and ASR coverage (asr: True = local ASR when installed, or a callable)."""
    from audio_gate import measure
    from align import speech_span, spoken_syllables, covers, transcribe
    start, end = speech_span(samples)
    rate = spoken_syllables(text) / max(.01, end - start)
    result = {'gate': measure(samples, path.name, short_clip=True), 'chars_per_second': round(rate, 2), 'rate_unit': 'syllables'}
    failures = list(result['gate']['failures'])
    if not SPEECH_RATE_RANGE[0] <= rate <= SPEECH_RATE_RANGE[1]:
        failures.append(f'speech rate {rate:.2f} syllables/s outside {SPEECH_RATE_RANGE}')
    words = (asr if callable(asr) else transcribe)(path) if asr else None
    if words:
        result['asr'] = covers(text, words['text'])
        result['words'] = words['words']
        if result['asr']['status'] != 'pass':
            failures.append(f"ASR does not cover the text (CER {result['asr']['cer']})")
    else:
        result['asr'] = {'status': 'not_available' if asr else 'disabled'}
    return {**result, 'failures': failures, 'status': 'FAIL' if failures else 'PASS'}


def generate_chunk(synthesize, chunk, path, seed, asr):
    """synthesize(text, seed) -> (samples, rate) or (samples, rate, words) when the engine returns timestamps."""
    from align import speech_span
    attempts = []
    for attempt in range(GENERATION_ATTEMPTS):
        audio, rate, *timestamps = synthesize(chunk['text'], seed + attempt)
        audio = to_rate(audio, rate)
        if not len(audio) or not np.isfinite(audio).all():
            attempts.append({'seed': seed + attempt, 'status': 'FAIL', 'failures': ['empty or non-finite audio']})
            continue
        start, end = speech_span(audio)
        first = max(0, round((start - EDGE_SECONDS[0]) * SAMPLE_RATE))
        # Keep a generous tail for now: where speech really ends is decided with the recognized words below.
        audio = audio[first:round((end + .6) * SAMPLE_RATE)]
        write_pcm(path, audio)
        check = check_chunk(read_pcm(path), chunk['text'], path, asr)
        if timestamps and timestamps[0]:
            shift = first / SAMPLE_RATE
            check['words'] = [{**word, 'start': word['start'] - shift, 'end': word['end'] - shift} for word in timestamps[0]]
            check['timestamps'] = 'engine'
        cleaned, tail = clean_edges(read_pcm(path), check.get('words'))
        check['tail'] = tail
        if cleaned is None:
            check['failures'] = check['failures'] + [f"the chunk ends mid-sound ({tail['final_level_db']} dB): the last word is cut off"]
            check['status'] = 'FAIL'
        else:
            write_pcm(path, cleaned)
        attempts.append({'seed': seed + attempt, **check})
        if check['status'] == 'PASS':
            return attempts
    path.unlink(missing_ok=True)
    raise ValueError(f"Chunk failed {GENERATION_ATTEMPTS} attempts: {chunk['text'][:24]}... " + json.dumps([item['failures'] for item in attempts], ensure_ascii=False))


def chunk_alignment(layout, limit=None):
    """Beat ranges from chunk placement; caption cues inside each chunk from timestamps or pauses.
    limit (CJK characters per cue, caption_assets.cue_char_limit) packs clauses for the canvas; a clause longer than
    the limit splits at word-aware positions only when the chunk has character timestamps to time the pieces."""
    from align import caption_texts, piece_ranges
    captions = {}
    for chunk, offset, audio, words in layout:
        def cut(text):
            return caption_texts(text, limit, split_long=bool(words)) if limit else caption_texts(text)
        texts = [(unit['beat'], text) for unit in chunk['units'] for text in cut(unit['text'])]
        ranges, method = piece_ranges(audio, [text for _, text in texts], words)
        for (beat, text), (left, right) in zip(texts, ranges):
            captions.setdefault(beat, []).append((text, (offset + left, offset + right), method))
    return captions


def build_master(root, manifest, synthesize, identity, options=None):
    """Generate every chunk with gates and retries, join with measured pauses, write master + alignment."""
    from audio_gate import measure
    options = options or {}
    root = Path(root).resolve()
    target, text = generation_target(root, manifest)
    record_path = target.with_suffix('.voice.json')
    if target.exists() and not record_path.exists():
        raise ValueError('Existing untracked narration will not be overwritten: ' + str(target))
    seed, asr = int(options.get('seed', 2026)), options.get('asr', True)
    joins = {**JOIN_PAUSE_SECONDS, **options.get('join_pause_seconds', {})}
    chunks = narration_chunks(manifest, int(options.get('max_chunk_chars', MAX_CHUNK_CHARS)))
    folder = target.with_name(target.stem + '-chunks')
    layout, records, master, cursor = [], [], [], 0
    for index, chunk in enumerate(chunks):
        path = folder / f'{index:03d}.wav'
        signature = hashlib.sha256(json.dumps({'identity': identity, 'text': chunk['text'], 'seed': seed}, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        chunk_record_path = path.with_suffix('.json')
        record = json.loads(chunk_record_path.read_text()) if chunk_record_path.is_file() else {}
        if not (path.is_file() and record.get('signature') == signature):
            if path.exists() and not record:
                raise ValueError('Existing untracked chunk will not be overwritten: ' + str(path))
            attempts = generate_chunk(synthesize, chunk, path, seed, asr)
            record = {'signature': signature, 'index': index, 'text': chunk['text'], 'units': chunk['units'], 'join': chunk['join'],
                      'attempts': attempts, 'sha256': sha256(path)}
            chunk_record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2))
        audio = read_pcm(path)
        # Chunks made before the tail rule are cleaned here too: the master never inherits a hard cut or an after-sound.
        audio, tail = clean_edges(audio, record['attempts'][-1].get('words'))
        if audio is None:
            raise ValueError(f"Chunk {index} ends mid-sound ({tail['final_level_db']} dB): regenerate it (delete {path.name} and its .json)")
        record['tail'] = tail
        if chunk['join']:
            silence = max(0., joins[chunk['join']] - EDGE_SECONDS[0] - EDGE_SECONDS[1])
            master.append(np.zeros(round(silence * SAMPLE_RATE)))
            cursor += len(master[-1])
        layout.append((chunk, cursor / SAMPLE_RATE, audio, record['attempts'][-1].get('words')))
        master.append(audio)
        cursor += len(audio)
        records.append({**{key: record[key] for key in ('index', 'text', 'join', 'sha256')}, 'attempts': len(record['attempts']), 'tail': record['tail']})
    master.append(np.zeros(round(END_TAIL_SECONDS * SAMPLE_RATE)))
    samples = np.concatenate(master)
    gate = measure(samples, str(target))
    if gate['status'] != 'PASS':
        raise ValueError('Joined narration master failed the audio gate: ' + '; '.join(gate['failures']))
    write_pcm(target, samples)
    from align import entry
    from caption_assets import cue_char_limit
    captions, beats = chunk_alignment(layout, cue_char_limit(manifest)), []
    for page in manifest['pages']:
        for beat in page['beats']:
            items = captions[beat['id']]
            beats.append(entry(beat['id'], beat['text'], [item[0] for item in items], [item[1] for item in items], items[0][2]))
    alignment_path = (root / manifest.get('narration', {}).get('alignment', 'inputs/narration/alignment.json')).resolve()
    if alignment_path.exists() and json.loads(alignment_path.read_text()).get('method') != 'semantic_chunks':
        raise ValueError('Existing hand-made alignment will not be overwritten: ' + str(alignment_path))
    alignment_path.parent.mkdir(parents=True, exist_ok=True)
    alignment_path.write_text(json.dumps({'version': 1, 'source_sha256': sha256(target), 'script_sha256': hashlib.sha256(text.encode()).hexdigest(),
                                          'method': 'semantic_chunks', 'beats': beats}, ensure_ascii=False, indent=2))
    record_path.write_text(json.dumps({'method': 'semantic_chunks', 'identity': identity, 'seed': seed, 'text': text,
        'duration': len(samples) / SAMPLE_RATE, 'chunks': records, 'join_pause_seconds': joins, 'gate': gate,
        'alignment': str(alignment_path), 'subjective_listening': 'not_performed'}, ensure_ascii=False, indent=2))
    return target, alignment_path


def load_master(root, manifest, destination):
    settings = manifest.get('narration')
    if not settings or not settings.get('source') or not settings.get('alignment'):
        raise ValueError('Production requires narration.source and narration.alignment: finish the complete voice before visuals')
    options = manifest.get('audio', {})
    if float(options.get('pace', 1)) != 1 or options.get('trim_silence', False):
        raise ValueError('A locked narration master cannot be stretched or silence-trimmed')
    if any(float(options.get(key, 0)) != 0 for key in ('sentence_pause_seconds', 'page_pause_seconds')):
        raise ValueError('Page and sentence pauses cannot insert silence into a narration master')
    source = (Path(root) / settings['source']).resolve()
    alignment_path = (Path(root) / settings['alignment']).resolve()
    alignment = json.loads(alignment_path.read_text())
    if alignment.get('version', 1) != 1:
        raise ValueError('Unsupported narration alignment version')
    text = script_text(manifest)
    if alignment.get('source_sha256') != sha256(source):
        raise ValueError('Narration alignment belongs to a different audio master')
    if alignment.get('script_sha256') != hashlib.sha256(text.encode()).hexdigest():
        raise ValueError('Narration alignment belongs to a different script')
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(source), '-ar', str(SAMPLE_RATE),
                    '-ac', '1', '-c:a', 'pcm_s16le', str(destination)], check=True)
    with wave.open(str(destination)) as stream:
        samples = np.frombuffer(stream.readframes(stream.getnframes()), dtype='<i2').copy()
    if not len(samples) or not np.any(samples):
        raise ValueError('Narration master is empty or silent')
    duration = len(samples) / SAMPLE_RATE
    expected = [beat for page in manifest['pages'] for beat in page['beats']]
    entries = alignment.get('beats', [])
    if len(entries) != len(expected):
        raise ValueError('Narration alignment must cover every beat exactly once')
    previous_end = 0.
    beats = {}
    for expected_beat, entry in zip(expected, entries):
        identifier = expected_beat.get('id')
        if not identifier or entry.get('id') != identifier or entry.get('text') != expected_beat['text'] or identifier in beats:
            raise ValueError('Narration alignment IDs, order and text must match the script')
        start, end = float(entry['start']), float(entry['end'])
        if not math.isfinite(start + end) or not 0 <= previous_end <= start < end <= duration + 1 / SAMPLE_RATE:
            raise ValueError('Narration ranges must be finite, ordered, nonoverlapping and inside the master')
        beats[identifier] = {**entry, 'start': start, 'end': end}
        previous_end = end
    report = {'mode': 'continuous_master', 'source': str(source), 'source_sha256': sha256(source),
              'alignment': str(alignment_path), 'alignment_sha256': sha256(alignment_path),
              'duration': duration, 'sample_rate': SAMPLE_RATE, 'samples': len(samples),
              'pcm_sha256': hashlib.sha256(samples.astype('<i2').tobytes()).hexdigest(),
              'inserted_page_silence_seconds': 0, 'internal_samples_preserved': True}
    return samples, beats, report


def verify_compiled_master(root, timeline):
    """Detect lost breaths, inserted gaps, stale inputs or stretched master samples."""
    report = timeline.get('narration_master')
    if not report:
        return None
    if sha256(report['source']) != report['source_sha256'] or sha256(report['alignment']) != report['alignment_sha256']:
        raise ValueError('Narration master or alignment changed after build')
    with wave.open(str(Path(root) / 'work/narration.wav')) as stream:
        if (stream.getframerate(), stream.getnchannels(), stream.getsampwidth()) != (SAMPLE_RATE, 1, 2):
            raise ValueError('Compiled narration format changed')
        samples = np.frombuffer(stream.readframes(stream.getnframes()), dtype='<i2')
    start = round(timeline['cover_seconds'] * SAMPLE_RATE)
    master = samples[start:start + report['samples']]
    if hashlib.sha256(master.tobytes()).hexdigest() != report['pcm_sha256']:
        raise ValueError('Compiled narration changed the locked master waveform')
    if np.any(samples[:start]) or np.any(samples[start + report['samples']:]):
        raise ValueError('Cover and ending padding must not contain extra narration')
    return {'continuous_master': True, 'pcm_preserved': True, 'inserted_page_silence_seconds': 0}


def rebuild_master(root):
    """Re-join an existing master from its generated chunks under the current edge rules (no voice model needed).
    Every chunk must still match its text, voice and seed; a chunk that would need generating stops the rebuild."""
    root = Path(root).resolve()
    manifest = json.loads((root / 'job.json').read_text())
    target, _ = generation_target(root, manifest)
    record = json.loads(target.with_suffix('.voice.json').read_text())

    def synthesize(text, seed):
        raise ValueError('A chunk no longer matches its text or voice; regenerate the narration with the voice tool: ' + text[:24])
    options = {'seed': record['seed'], 'join_pause_seconds': record.get('join_pause_seconds', {}), 'asr': True}
    alignment = (root / manifest.get('narration', {}).get('alignment', 'inputs/narration/alignment.json')).resolve()
    if alignment.is_file() and json.loads(alignment.read_text()).get('method') != 'semantic_chunks':
        alignment.replace(alignment.with_name(alignment.stem + '.before-rebuild.json'))
    return build_master(root, manifest, synthesize, record['identity'], options)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['rebuild'])
    parser.add_argument('job', type=Path)
    arguments = parser.parse_args()
    master, alignment = rebuild_master(arguments.job)
    print(json.dumps({'master': str(master), 'alignment': str(alignment)}))

