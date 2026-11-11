#!/usr/bin/env python3
"""Narration adapter for local VoiceStudio: one request per semantic chunk; no hidden remote fallback."""
from pathlib import Path
from hosted_assets import resolve_asset
import argparse
import hashlib
import json
import tempfile
import urllib.parse
from narration_master import build_master, SAMPLE_RATE

PACKAGE = Path(__file__).resolve().parents[1]
PERSONAL_CATALOG = Path.home()/'.local/share/sweety-handdraw-video/voices/catalog.json'
CONSENT = ('self', 'authorized')
REFERENCE_RATE_RANGE = (2.5, 8.)
# Sent explicitly as the official Qwen3-TTS sampling values; VoiceStudio 0.5.x /generate has no such
# form fields and keeps the model defaults, so these only take effect on servers that read them.
SAMPLING = {'temperature': '0.9', 'top_p': '1.0', 'top_k': '50', 'repetition_penalty': '1.05'}


def load_voice_catalog(root):
    """Packaged presets keep their names; personal/job catalogs add references or consented custom voices."""
    catalog = json.loads((PACKAGE/'assets/voices/catalog.json').read_text())
    packaged = {voice['id']: voice for voice in catalog['voices']}
    identities = {identifier: {key: profile[key] for key in ('name', 'description', 'requires_original_reference') if key in profile}
                  for identifier, profile in packaged.items()}
    for path in (PERSONAL_CATALOG, Path(root)/'options/local-voices.json'):
        if not path.is_file():
            continue
        local = json.loads(path.read_text())
        local_root = path.parent if path == PERSONAL_CATALOG else Path(root)
        for entry in local['voices']:
            entry = dict(entry)
            for field in ('reference_audio', 'reference_text', 'preview_audio'):
                if entry.get(field):
                    value = Path(entry[field]).expanduser()
                    entry[field] = str(value if value.is_absolute() else (local_root/value).resolve())
            if entry['id'] in packaged:
                packaged[entry['id']].update({**entry, **identities[entry['id']]})
            elif entry.get('consent') in CONSENT and entry.get('name') and entry.get('reference_audio') and entry.get('reference_text'):
                catalog['voices'] = [voice for voice in catalog['voices'] if voice['id'] != entry['id']] + [{**entry, 'custom': True}]
        if local.get('default') in {voice['id'] for voice in catalog['voices']}:
            catalog['default'] = local['default']
    for profile in catalog['voices']:
        profile['preferred'] = profile['id'] == catalog['default']
    return catalog


def checked_reference(audio, transcript, expected_audio_hash=None, expected_text_hash=None):
    """Unchanged, clean (audio_gate) and fully transcribed; a partial ref_text makes the model read leftovers."""
    from audio_gate import decode, require_clean
    from align import speech_span, spoken
    audio = Path(audio).resolve()
    if not audio.is_file() or not transcript.strip():
        raise ValueError('Voice reference requires an existing audio file and exact transcript')
    if expected_audio_hash and hashlib.sha256(audio.read_bytes()).hexdigest() != expected_audio_hash:
        raise ValueError('Voice reference audio changed after import')
    if expected_text_hash and hashlib.sha256(transcript.strip().encode()).hexdigest() != expected_text_hash:
        raise ValueError('Voice reference transcript changed after import')
    samples = decode(audio)
    require_clean(samples, 'Voice reference ' + audio.name, str(audio), short_clip=True)
    start, end = speech_span(samples)
    rate = len(spoken(transcript)) / max(.01, end - start)
    if not REFERENCE_RATE_RANGE[0] <= rate <= REFERENCE_RATE_RANGE[1]:
        raise ValueError(f'Reference transcript must cover the whole clip exactly ({rate:.1f} chars/s of speech)')
    return audio, transcript.strip()


def voice_reference(options, root):
    root = Path(root).resolve()
    if options.get('reference_audio'):
        if not options.get('reference_text'):
            raise ValueError('A custom voice requires its exact reference transcript')
        return checked_reference(root/options['reference_audio'], options['reference_text'], options.get('reference_sha256'))
    directory = PACKAGE/'assets'/'voices'
    packaged = json.loads((directory/'catalog.json').read_text())
    catalog = load_voice_catalog(root)
    identifier = options.get('voice', catalog['default'])
    packaged_profile = next((voice for voice in packaged['voices'] if voice['id'] == identifier), None)
    profile = next((voice for voice in catalog['voices'] if voice['id'] == identifier), None)
    if profile is None:
        raise ValueError('Unknown voice: ' + identifier)
    if not profile.get('reference_audio'):
        raise ValueError('Import the user-provided audio and exact transcript for this reference voice')
    if packaged_profile and packaged_profile.get('requires_original_reference'):
        if profile.get('reference_kind') != 'source_recording' or not profile.get('reference_sha256'):
            raise ValueError('This voice requires an imported source recording; generated previews cannot replace it')
    audio = Path(profile['reference_audio']).expanduser()
    transcript = Path(profile['reference_text']).expanduser()
    audio = audio if audio.is_absolute() else resolve_asset(directory/audio)
    transcript = transcript if transcript.is_absolute() else directory/transcript
    if not audio.is_file() or not transcript.is_file():
        raise ValueError('Voice reference audio or transcript is not installed: ' + identifier)
    return checked_reference(audio, transcript.read_text(), profile.get('reference_sha256'), profile.get('transcript_sha256'))


def studio_synthesizer(service_url, fields, reference_audio):
    import requests
    from audio_gate import decode

    def synthesize(text, seed):
        with reference_audio.open('rb') as reference:
            response = requests.post(service_url + '/generate', data={**fields, 'text': text, 'seed': str(seed)},
                                     files={'ref_audio': ('reference.wav', reference, 'audio/wav')}, timeout=600)
        response.raise_for_status()
        if not response.headers.get('Content-Type', '').startswith('audio/'):
            raise ValueError('VoiceStudio did not return audio')
        with tempfile.NamedTemporaryFile(suffix='.wav') as handle:
            handle.write(response.content)
            handle.flush()
            return decode(handle.name), SAMPLE_RATE
    return synthesize


def studio_transcriber(service_url, language):
    """VoiceStudio /transcribe (accurate mode) as the ASR + timestamp source for chunk checks and captions."""
    import requests

    def transcribe(path):
        with open(path, 'rb') as audio:
            response = requests.post(service_url + '/transcribe', files={'audio': (Path(path).name, audio, 'audio/wav')},
                                     data={'mode': 'accurate', 'language': language}, timeout=300)
        response.raise_for_status()
        result = response.json()
        words = [word for segment in result.get('segments', []) for word in segment.get('words') or [segment]]
        return {'text': result['text'], 'words': [{'text': word.get('text', word.get('word', '')), 'start': word['start'], 'end': word['end']} for word in words]}
    return transcribe


def main():
    import requests
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('job', type=Path)
    parser.add_argument('--url', help='Override voice_studio.url; local HTTP only')
    parser.add_argument('--transcribe', action='store_true', help='Use VoiceStudio /transcribe for chunk ASR and caption timestamps')
    arguments = parser.parse_args()
    root = arguments.job.resolve()
    manifest = json.loads((root / 'job.json').read_text())
    options = manifest.get('voice_studio', {})
    service_url = (arguments.url or options.get('url', 'http://127.0.0.1:3900')).rstrip('/')
    endpoint = urllib.parse.urlparse(service_url)
    if endpoint.scheme != 'http' or endpoint.hostname not in ('127.0.0.1', 'localhost', '::1') or endpoint.username or endpoint.password:
        raise ValueError('This adapter accepts only an unauthenticated local VoiceStudio service')
    reference_audio, reference_text = voice_reference(options, root)
    try:
        response = requests.get(service_url + '/engines/tts', timeout=10)
        response.raise_for_status()
        engine = response.json()
    except requests.RequestException as error:
        raise SystemExit('VoiceStudio 未安装、未启动或服务不可达：本任务没有旁白，不会交付无声视频冒充完整成片。请安装并启动 VoiceStudio，或在 VoiceStudio 编辑后导出旁白。') from error
    backend = options.get('backend', 'mlx-audio')
    expected_model = options.get('model', 'mlx-community/Qwen3-TTS-12Hz-1.7B-Base-bf16')
    if engine.get('active') != backend or engine.get('active_model') != expected_model:
        raise ValueError('VoiceStudio active engine/model differs from the configured voice; no global settings were changed')
    fields = {'ref_text': reference_text, 'language': options.get('language', 'Chinese'), 'engine': backend,
              'speed': str(options.get('speed', 1.03)), 'effect_preset': options.get('effect_preset', 'broadcast'),
              'max_chunk_chars': '0', **SAMPLING}
    identity = {'engine': 'voice-studio', 'model': expected_model, 'fields': fields,
                'reference_sha256': hashlib.sha256(reference_audio.read_bytes()).hexdigest()}
    if arguments.transcribe:
        options = {**options, 'asr': studio_transcriber(service_url, options.get('asr_language', 'zh'))}
    target, alignment = build_master(root, manifest, studio_synthesizer(service_url, fields, reference_audio), identity, options)
    print('READY', target, alignment, flush=True)


if __name__ == '__main__':
    main()
