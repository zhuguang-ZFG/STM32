#!/usr/bin/env python3
"""Native production choices for Codex / Claude Code / TTY.

Flow:
  1. config_type: model_infer (default) | active_select
  2. model_infer → validate defaults, write selection, no browser
  3. active_select → aspect → style → voice → captions (text menus; optional TTY)

HTML popups are no longer the primary path (--html keeps a legacy server for debug).
"""
import argparse
import json
import sys
from pathlib import Path
import secrets
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlsplit
from aspect_ratio import DEFAULT_RATIO, PRESETS, resolve_canvas, text_menu as aspect_menu, validate_aspect_choice
from hosted_assets import resolve_asset, asset_available
from style_choice import prepare_catalog, validate_selection, text_style_menu

PACKAGE = Path(__file__).resolve().parents[1]
CONFIG_TYPES = ('model_infer', 'active_select')
# Active path only asks what changes the film structure. Hand/ads/watermark stay defaults unless explicit.
ACTIVE_STAGES = ('aspect', 'style', 'voice', 'captions')
ALL_CHOICE_KEYS = ACTIVE_STAGES + ('hand', 'advertising', 'watermark')


def save_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(path)


def default_bundle(content, style=None, voice='magnetic-narrator', aspect_ratio=DEFAULT_RATIO):
    """Model-authored defaults before any user turn. Style defaults to model inference."""
    canvas = resolve_canvas(aspect_ratio)
    return {
        'content': content,
        'config_type': 'model_infer',
        'aspect': {'aspect_ratio': canvas['aspect_ratio'], 'width': canvas['width'], 'height': canvas['height']},
        'style': style or {'mode': 'inferred'},
        'hand': {'preset': 'pen-only'},
        'voice': {'voice': voice},
        'advertising': {'text': ''},
        'watermark': {'text': ''},
        'captions': {'mode': 'quiet'},
        'rationale': {},
    }


def validate_choice(stage, value, catalog, hands, voices):
    if not isinstance(value, dict):
        raise ValueError('Choice must be an object')
    if stage == 'aspect':
        validate_aspect_choice(value)
    elif stage == 'style':
        validate_selection(value, catalog)
    elif stage == 'hand' and value.get('preset') not in {hand['id'] for hand in hands}:
        raise ValueError('Unknown drawing tool')
    elif stage == 'voice' and value.get('voice') not in {voice['id'] for voice in voices if voice.get('available', True)}:
        raise ValueError('This voice reference is not installed')
    elif stage == 'advertising' and (not isinstance(value.get('text'), str) or len(value['text']) > 16):
        raise ValueError('笔杆广告最多16个字符，不能自动截短')
    elif stage == 'watermark' and (not isinstance(value.get('text'), str) or len(value['text']) > 180):
        raise ValueError('请输入不超过180个字符的水印，或留空不加')
    elif stage == 'captions' and value.get('mode') not in ('quiet', 'plate'):
        raise ValueError('Unknown subtitle appearance')
    elif stage not in ALL_CHOICE_KEYS:
        raise ValueError(f'Unknown stage {stage}')


def validate_defaults(defaults, catalog, hands, voices):
    if not isinstance(defaults.get('content'), str) or not defaults['content'].strip():
        raise ValueError('MISSING_CONTENT: 请先输入主题或故事内容')
    config_type = defaults.get('config_type', 'model_infer')
    if config_type not in CONFIG_TYPES:
        raise ValueError(f'config_type must be one of {CONFIG_TYPES}')
    for stage in ALL_CHOICE_KEYS:
        if stage not in defaults:
            raise ValueError(f'defaults missing {stage}')
        validate_choice(stage, defaults[stage], catalog, hands, voices)
    return config_type


class ChoiceSession:
    """Active-select session with per-step deadline. model_infer completes immediately."""

    def __init__(self, job, defaults, explicit, catalog, hands, voices, timeout=60, now=None):
        self.job = Path(job)
        self.defaults = defaults
        self.catalog, self.hands, self.voices = catalog, hands, voices
        self.timeout = min(60, max(.01, float(timeout)))
        self.config_type = validate_defaults(defaults, catalog, hands, voices)
        saved_path = self.job / 'options/selection.json'
        saved = json.loads(saved_path.read_text()) if saved_path.is_file() else {}
        if saved and saved.get('content') != defaults['content']:
            raise ValueError('Use a new job directory for different content; existing choices were preserved')
        self.choices = dict(saved.get('choices', {}))
        # Hidden defaults always present so apply_choices stays simple.
        for stage in ('hand', 'advertising', 'watermark'):
            if stage not in self.choices:
                value = explicit.get(stage, defaults[stage]) if stage in (explicit or {}) else defaults[stage]
                validate_choice(stage, value, catalog, hands, voices)
                reason = 'explicit_user_request' if stage in (explicit or {}) else 'default'
                self.choices[stage] = {'value': value, 'reason': reason}
        for stage, value in (explicit or {}).items():
            if stage == 'config_type':
                continue
            validate_choice(stage, value, catalog, hands, voices)
            self.choices[stage] = {'value': value, 'reason': 'explicit_user_request'}
        self.stages = [] if self.config_type == 'model_infer' else list(ACTIVE_STAGES)
        if self.config_type == 'model_infer':
            for stage in ACTIVE_STAGES:
                if stage not in self.choices:
                    self.choices[stage] = {'value': defaults[stage], 'reason': 'model_infer'}
            self.index = 0
            self.started = time.monotonic() if now is None else now
            self.persist(complete=True)
            return
        self.index = 0
        self.started = time.monotonic() if now is None else now
        self.skip_answered()
        self.persist()

    def skip_answered(self):
        while self.index < len(self.stages) and self.stages[self.index] in self.choices:
            self.index += 1

    def persist(self, complete=None):
        done = self.index >= len(self.stages) if complete is None else complete
        save_json(self.job / 'options/selection.json', {
            'complete': done,
            'config_type': self.config_type,
            'choices': self.choices,
            'timeout_seconds': self.timeout,
            'content': self.defaults['content'],
            'stages': list(self.stages),
        })
        if 'style' in self.choices:
            choice = self.choices['style']
            selection = dict(choice['value'])
            reason = choice['reason']
            if reason == 'timeout_default':
                evidence = 'No answer before the optional preference deadline; used model-authored defaults'
            elif reason == 'model_infer':
                evidence = 'config_type=model_infer; model resolves style from content'
            else:
                evidence = 'User selected or delegated this style route'
            selection.update(confirmation=reason if reason != 'model_infer' else 'user_delegated', evidence=evidence)
            # Map model_infer default inferred style onto the style pipeline's confirmation vocabulary.
            if reason == 'model_infer' and selection.get('mode') == 'inferred':
                selection['confirmation'] = 'user_delegated'
            save_json(self.job / 'style/selection.json', selection)

    def advance(self, now=None):
        if self.config_type == 'model_infer':
            return self.status(now if now is not None else time.monotonic())
        now = time.monotonic() if now is None else now
        changed = False
        while self.index < len(self.stages) and now - self.started >= self.timeout:
            stage = self.stages[self.index]
            self.choices[stage] = {'value': self.defaults[stage], 'reason': 'timeout_default', 'waited_seconds': self.timeout}
            self.index += 1
            self.skip_answered()
            self.started += self.timeout
            changed = True
        if changed:
            self.persist()
        return self.status(now)

    def choose(self, stage, value, now=None):
        now = time.monotonic() if now is None else now
        self.advance(now)
        if self.config_type == 'model_infer':
            raise ValueError('model_infer path has no interactive stages')
        if self.index == len(self.stages) or stage != self.stages[self.index]:
            raise ValueError('This step has advanced; use the saved choices or submit a later correction in chat')
        validate_choice(stage, value, self.catalog, self.hands, self.voices)
        self.choices[stage] = {'value': value, 'reason': 'user_dialog'}
        self.index += 1
        self.skip_answered()
        self.started = now
        self.persist()
        return self.status(now)

    def status(self, now=None):
        now = time.monotonic() if now is None else now
        complete = self.index >= len(self.stages)
        stage = None if complete else self.stages[self.index]
        return {
            'complete': complete,
            'config_type': self.config_type,
            'stage': stage,
            'index': self.index,
            'remaining_seconds': 0 if complete else max(0, self.timeout - (now - self.started)),
            'choices': self.choices,
            'menu': stage_menu(stage, self.catalog, self.voices) if stage else None,
        }


def stage_menu(stage, catalog, voices):
    if stage == 'aspect':
        return {'prompt': '视频比例', 'options': aspect_menu()}
    if stage == 'style':
        return {'prompt': '画风（文字列表，无预览图）', 'options': text_style_menu(catalog)}
    if stage == 'voice':
        lines = []
        for index, voice in enumerate(voices, 1):
            if not voice.get('available', True):
                continue
            label = voice.get('name') or voice['id']
            lines.append(f'{index}) {label}  [{voice["id"]}]')
        return {'prompt': '声音', 'options': lines}
    if stage == 'captions':
        return {'prompt': '字幕形态', 'options': ['1) quiet  无底板短句（默认）', '2) plate  深色底板']}
    return None


def load_voices(job):
    from voice_studio import load_voice_catalog
    voices = load_voice_catalog(job)['voices']
    for voice in voices:
        voice['audio_path'] = str(PACKAGE / 'assets/voices' / voice['reference_audio']) if voice.get('reference_audio') else None
        voice['available'] = bool(voice['audio_path'] and asset_available(Path(voice['audio_path'])))
        if voice.get('requires_original_reference'):
            voice['available'] = voice['available'] and voice.get('reference_kind') == 'source_recording' and bool(voice.get('reference_sha256'))
        preview = PACKAGE / 'assets/voices' / voice.get('preview_audio', '')
        if voice.get('preview_audio') and asset_available(preview):
            voice['audio_path'] = str(preview)
        voice['preview_available'] = bool(voice['audio_path'] and asset_available(Path(voice['audio_path'])))
    return voices


def apply_choices(job):
    job = Path(job).resolve()
    selection = json.loads((job / 'options/selection.json').read_text())
    if not selection.get('complete'):
        raise ValueError('Optional choice collection is still running')
    choices = {name: entry['value'] for name, entry in selection['choices'].items()}
    for key in ALL_CHOICE_KEYS:
        if key not in choices:
            raise ValueError(f'selection missing {key}')
    manifest = json.loads((job / 'job.json').read_text())
    canvas = resolve_canvas(choices['aspect'].get('aspect_ratio', DEFAULT_RATIO),
                            choices['aspect'].get('width'), choices['aspect'].get('height'),
                            manifest.get('canvas', {}).get('fps', 30))
    manifest['canvas'] = {'width': canvas['width'], 'height': canvas['height'], 'fps': canvas['fps'],
                          'aspect_ratio': canvas['aspect_ratio']}
    hand = dict(choices['hand'])
    hand['pen_text'] = choices['advertising']['text']
    manifest['hand'] = hand
    manifest['watermark'] = {'text': choices['watermark']['text'], 'opacity': .24}
    for engine in ('voice_studio', 'voxcpm'):
        options = manifest.setdefault(engine, {})
        options.pop('reference_audio', None)
        options.pop('reference_text', None)
        options.update(choices['voice'])
    captions = manifest.setdefault('captions', {})
    captions.update(color='#FFFFFF', stroke_width=2, stroke_color='#000000')
    if choices['captions']['mode'] == 'quiet':
        captions.update(background=None)
    else:
        captions.update(background={'color': '#243039', 'opacity': .76}, color='#FFFFFF')
    save_json(job / 'job.json', manifest)
    return manifest


def menu_payload(catalog, hands, voices, defaults):
    return {
        'config_types': [
            {'id': 'model_infer', 'label': '模型推理（默认）', 'hint': '按主题与内容自动选最佳项'},
            {'id': 'active_select', 'label': '主动选择', 'hint': '逐项选择比例/风格/声音/字幕'},
        ],
        'aspect_presets': [{'id': name, 'size': f'{size[0]}×{size[1]}', 'default': name == DEFAULT_RATIO}
                           for name, size in PRESETS.items()] + [{'id': 'custom', 'size': '宽×高'}],
        'styles': text_style_menu(catalog, as_records=True),
        'voices': [{'id': v['id'], 'name': v.get('name') or v['id'], 'available': v.get('available', True)}
                   for v in voices],
        'captions': [{'id': 'quiet', 'label': '无底板短句'}, {'id': 'plate', 'label': '深色底板'}],
        'defaults': {k: defaults.get(k) for k in ('config_type', 'aspect', 'style', 'voice', 'captions', 'hand')},
        'hands': [{'id': h['id']} for h in hands],
        'note': '无预览图。风格列表仅供参考，模型推理不受列表约束。',
    }


def tty_select(session):
    """Numbered stdin menus for hosts without AskUserQuestion."""
    status = session.advance()
    print('CONFIG_TYPE=' + session.config_type, flush=True)
    if session.config_type == 'model_infer':
        print('PRODUCTION_OPTIONS_COMPLETE=' + str(session.job / 'options/selection.json'), flush=True)
        return status
    while not status['complete']:
        stage = status['stage']
        menu = status['menu']
        print(f'\n[{stage}] {menu["prompt"]}  (剩余 {status["remaining_seconds"]:.0f}s，回车=默认)', flush=True)
        for line in menu['options']:
            print('  ' + line, flush=True)
        try:
            raw = input('> ').strip()
        except EOFError:
            raw = ''
        if not raw:
            # timeout-like: accept default for this stage immediately
            session.choices[stage] = {'value': session.defaults[stage], 'reason': 'timeout_default', 'waited_seconds': 0}
            session.index += 1
            session.skip_answered()
            session.started = time.monotonic()
            session.persist()
            status = session.status()
            continue
        try:
            value = parse_tty_answer(stage, raw, session)
            status = session.choose(stage, value)
        except ValueError as error:
            print('ERROR: ' + str(error), flush=True)
            status = session.advance()
    print('PRODUCTION_OPTIONS_COMPLETE=' + str(session.job / 'options/selection.json'), flush=True)
    return status


def parse_tty_answer(stage, raw, session):
    if stage == 'aspect':
        if raw in PRESETS or raw == 'custom' or 'x' in raw.lower() or '×' in raw:
            if raw in PRESETS:
                return {'aspect_ratio': raw}
            if raw == 'custom':
                raise ValueError('自定义请输入 宽x高，例如 1080x1920')
            parts = raw.lower().replace('×', 'x').split('x')
            if len(parts) != 2:
                raise ValueError('自定义格式 宽x高')
            return {'aspect_ratio': 'custom', 'width': int(parts[0]), 'height': int(parts[1])}
        index = int(raw)
        names = list(PRESETS) + ['custom']
        if not 1 <= index <= len(names):
            raise ValueError('out of range')
        chosen = names[index - 1]
        if chosen == 'custom':
            raise ValueError('自定义请输入 宽x高，例如 1080x1920')
        return {'aspect_ratio': chosen}
    if stage == 'style':
        if raw in ('0', 'infer', '模型推理'):
            return {'mode': 'inferred'}
        styles = session.catalog['styles']
        if raw.isdigit():
            index = int(raw)
            if index == 0:
                return {'mode': 'inferred'}
            if 1 <= index <= len(styles):
                return {'mode': 'catalog', 'catalog_id': styles[index - 1]['id']}
        # bare catalog id
        if any(entry['id'] == raw for entry in styles):
            return {'mode': 'catalog', 'catalog_id': raw}
        return {'mode': 'custom', 'user_description': raw}
    if stage == 'voice':
        available = [v for v in session.voices if v.get('available', True)]
        if raw.isdigit():
            index = int(raw)
            if 1 <= index <= len(available):
                return {'voice': available[index - 1]['id']}
        if any(v['id'] == raw for v in available):
            return {'voice': raw}
        raise ValueError('unknown voice')
    if stage == 'captions':
        if raw in ('1', 'quiet'):
            return {'mode': 'quiet'}
        if raw in ('2', 'plate'):
            return {'mode': 'plate'}
        raise ValueError('choose quiet or plate')
    raise ValueError('unknown stage')


def collect(job, defaults_path, explicit_path=None, timeout=60, mode='auto'):
    """mode: auto | tty | file | html. auto = model_infer completes; active_select prints menu JSON for the host agent."""
    job = Path(job).resolve()
    defaults = json.loads(Path(defaults_path).read_text())
    explicit = json.loads(Path(explicit_path).read_text()) if explicit_path else {}
    if 'config_type' in explicit:
        defaults['config_type'] = explicit['config_type']
    # Fill missing default keys so older defaults.json still work.
    base = default_bundle(defaults.get('content') or ' ')
    for key, value in base.items():
        defaults.setdefault(key, value)
    catalog_path = job / 'style/catalog.json'
    catalog = json.loads(catalog_path.read_text()) if catalog_path.is_file() else prepare_catalog(job, PACKAGE / 'dependencies/hand-drawn-styles')
    hands = json.loads((PACKAGE / 'assets/hands/catalog.json').read_text())['presets']
    voices = load_voices(job)
    session = ChoiceSession(job, defaults, explicit, catalog, hands, voices, timeout)
    if mode == 'html':
        return serve_html(session, catalog, hands, voices, defaults, port=0)
    if mode == 'tty' or (mode == 'auto' and session.config_type == 'active_select' and sys.stdin.isatty()):
        return tty_select(session)
    # file / agent path: print contract for the host model to ask natively
    status = session.advance()
    payload = {
        'status': status,
        'menus': menu_payload(catalog, hands, voices, defaults),
        'selection_path': str(job / 'options/selection.json'),
        'instruction': (
            '若 config_type=model_infer：已完成，继续制作。'
            '若 active_select：用宿主原生选项（Claude Code AskUserQuestion / Codex 等价提问 / 终端数字）按 status.stage 逐项询问，'
            '用户选定后运行: python3 scripts/production_options.py JOB --choose STAGE --value JSON'
        ),
    }
    print('PRODUCTION_OPTIONS_CONTRACT=' + json.dumps(payload, ensure_ascii=False), flush=True)
    if status['complete']:
        print('PRODUCTION_OPTIONS_COMPLETE=' + str(job / 'options/selection.json'), flush=True)
    return status


def serve_html(session, catalog, hands, voices, defaults, port=0):
    """Legacy localhost page kept for debug only."""
    token = secrets.token_urlsafe(24)
    payload = menu_payload(catalog, hands, voices, defaults)
    payload['legacy'] = True
    template = (PACKAGE / 'assets/production-options.html').read_text()
    page = template.replace('__DATA__', json.dumps(payload, ensure_ascii=False).replace('<', '\\u003c')).replace('__TOKEN__', token).encode()
    job = session.job

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def reply(self, status, body, kind='application/json'):
            self.send_response(status)
            self.send_header('Content-Type', kind)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            path = urlsplit(self.path).path
            if path == '/':
                return self.reply(200, page, 'text/html; charset=utf-8')
            if path == '/status':
                return self.reply(200, json.dumps(session.advance()).encode())
            return self.reply(404, b'{}')

        def do_POST(self):
            if self.path != '/choice' or self.headers.get('Origin') != 'http://127.0.0.1:' + str(self.server.server_port) or self.headers.get('X-Options-Token') != token:
                return self.reply(403, b'{}')
            try:
                length = int(self.headers.get('Content-Length', 0))
                if not 0 < length < 12000:
                    raise ValueError('Invalid request length')
                answer = json.loads(self.rfile.read(length))
                status = session.choose(answer['stage'], answer['value'])
                self.reply(200, json.dumps(status).encode())
            except (KeyError, ValueError, TypeError) as error:
                self.reply(400, json.dumps({'error': str(error)}, ensure_ascii=False).encode())

    server = HTTPServer(('127.0.0.1', port), Handler)
    server.timeout = .5
    print('PRODUCTION_OPTIONS_URL=http://127.0.0.1:' + str(server.server_port), flush=True)
    print('WARNING: HTML options are legacy; prefer native/TTY menus', flush=True)
    announced = False
    while True:
        server.handle_request()
        if session.advance()['complete'] and not announced:
            print('PRODUCTION_OPTIONS_COMPLETE=' + str(job / 'options/selection.json'), flush=True)
            announced = True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('job', type=Path)
    parser.add_argument('--defaults', type=Path)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--explicit', type=Path)
    parser.add_argument('--timeout', type=float, default=60)
    parser.add_argument('--mode', choices=['auto', 'tty', 'file', 'html'], default='auto')
    parser.add_argument('--choose', dest='choose_stage')
    parser.add_argument('--value', dest='choose_value')
    parser.add_argument('--port', type=int, default=0)
    args = parser.parse_args()
    if args.apply:
        apply_choices(args.job)
        print('PRODUCTION_OPTIONS_APPLIED=' + str(args.job / 'job.json'))
    elif args.choose_stage:
        job = Path(args.job).resolve()
        defaults_path = job / 'options/defaults.json'
        if not defaults_path.is_file():
            raise SystemExit('options/defaults.json required for --choose')
        defaults = json.loads(defaults_path.read_text())
        base = default_bundle(defaults.get('content') or ' ')
        for key, value in base.items():
            defaults.setdefault(key, value)
        defaults['config_type'] = 'active_select'
        catalog = json.loads((job / 'style/catalog.json').read_text()) if (job / 'style/catalog.json').is_file() else prepare_catalog(job, PACKAGE / 'dependencies/hand-drawn-styles')
        hands = json.loads((PACKAGE / 'assets/hands/catalog.json').read_text())['presets']
        voices = load_voices(job)
        session = ChoiceSession(job, defaults, {}, catalog, hands, voices, args.timeout)
        value = json.loads(args.choose_value)
        print(json.dumps(session.choose(args.choose_stage, value), ensure_ascii=False))
    elif not args.defaults:
        parser.error('--defaults is required when collecting choices')
    else:
        collect(args.job, args.defaults, args.explicit, args.timeout, args.mode)
