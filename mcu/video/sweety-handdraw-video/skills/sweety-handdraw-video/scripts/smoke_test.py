#!/usr/bin/env python3
"""Offline runtime regression: synthetic fixtures, never claimed as a finished story."""
from pathlib import Path
import argparse
import json
import os
import subprocess
import sys
import wave
import numpy as np
from PIL import Image, ImageDraw
from fonts import select

RARE = '犇羴鱻龘囧槑'


def write_test_tone(path, seconds, frequency):
    rate = 48000
    times = np.arange(round(seconds * rate)) / rate
    envelope = np.minimum(times / .06, 1) * np.minimum((seconds - times) / .06, 1)
    signal = (.12 * envelope * np.sin(2 * np.pi * frequency * times) * 32767).astype('<i2')
    with wave.open(str(path), 'wb') as stream:
        stream.setparams((1, 2, rate, 0, 'NONE', 'not compressed'))
        stream.writeframes(signal.tobytes())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='New empty directory for isolated fixture files')
    arguments = parser.parse_args()
    root = arguments.output.resolve()
    root.mkdir(parents=True, exist_ok=False)
    inputs = root / 'inputs'
    inputs.mkdir()
    cover = Image.new('RGB', (960, 540), '#f4eedf')
    ImageDraw.Draw(cover).text((70, 70), 'RUNTIME CHECK - NOT A FINISHED STORY', fill='#302c26')
    cover.save(inputs / 'cover.png')
    icon = Image.new('RGBA', (220, 180))
    drawing = ImageDraw.Draw(icon)
    drawing.rounded_rectangle((15, 20, 190, 160), radius=22, fill='#da934f', outline='#282520', width=5)
    drawing.ellipse((65, 60, 130, 125), fill='#9fb568', outline='#282520', width=3)
    icon.save(inputs / 'icon.png')
    tiny = Image.new('RGBA', (7, 7))
    ImageDraw.Draw(tiny).rectangle((2, 2, 4, 4), fill='#ea7488')
    tiny.save(inputs / 'tiny-color.png')
    contour = Image.new('L',(7,7))
    ImageDraw.Draw(contour).rectangle((2,2,4,4),outline=255,width=1)
    contour.save(inputs / 'tiny-outline.png')
    ink = Image.new('RGBA', (100, 60))
    ImageDraw.Draw(ink).line((8, 45, 50, 10, 90, 45), fill='#202020', width=3)
    ink.save(inputs / 'ink-only.png')
    try:  # rare glyphs join the fixture wherever an installed font covers them; the failure path is unit-tested
        rare = RARE if select('handwriting', RARE) and select('caption', RARE) else ''
    except (ValueError, FileNotFoundError):
        rare = ''
    durations = [8.0, 4.4, 3.2]  # beat a holds a title, a marker and a two-region icon that needs ~2.1 s to draw
    for index, duration in enumerate(durations):
        write_test_tone(inputs / f'beat-{index}.wav', duration, 220 + 55 * index)
    manifest = {'version': 1, 'runtime_fixture': True, 'title': '运行回归测试', 'canvas': {'width': 960, 'height': 540, 'fps': 24},
        'cover': {'source': 'inputs/cover.png', 'seconds': 1.0}, 'hand': {'scale': .27},
        'audio': {'trim_silence': False}, 'captions': {'font_size': 24, 'bottom_margin': 18},
        'pages': [ {'beats': [
            {'id': 'a', 'text': '测试标题、底纹和插画路径。', 'audio': 'inputs/beat-0.wav', 'actions': [
                {'type': 'marker', 'x': 60, 'y': 48, 'width': 450, 'height': 26, 'weight': .3},
                {'type': 'text', 'text': '今晚，花十分钟。', 'x': 64, 'y': 20, 'size': 42},
                {'type': 'illustration', 'parts': [{'id': 'object', 'polygon': [[0,0],[1,0],[1,1],[0,1]]}], 'source': 'inputs/icon.png', 'x': 120, 'y': 140, 'width': 220, 'height': 180, 'weight': 2}]},
            {'id': 'b', 'text': '小色块和纯线稿都需要完整绘制。', 'audio': 'inputs/beat-1.wav', 'actions': [
                {'type': 'illustration', 'parts': [{'id': 'object', 'polygon': [[0,0],[1,0],[1,1],[0,1]]}], 'source': 'inputs/tiny-color.png', 'outline_mask':'inputs/tiny-outline.png', 'x': 580, 'y': 170, 'width': 7, 'height': 7},
                {'type': 'illustration', 'parts': [{'id': 'object', 'polygon': [[0,0],[1,0],[1,1],[0,1]]}], 'source': 'inputs/ink-only.png', 'x': 650, 'y': 190, 'width': 100, 'height': 60},
                {'type': 'marker', 'style': 'circle', 'x': 540, 'y': 110, 'width': 300, 'height': 220, 'weight': .4},
                {'type': 'illustration', 'drawing': {'mode': 'reveal'}, 'parts': [{'id': 'object', 'polygon': [[0,0],[1,0],[1,1],[0,1]]}], 'source': 'inputs/icon.png', 'x': 760, 'y': 330, 'width': 160, 'height': 130}]}]},
            {'beats': [{'id': 'c', 'text': '换页后，时间由实际音频决定。' + rare, 'audio': 'inputs/beat-2.wav', 'actions': [
                {'type': 'text', 'text': '第二页' + rare, 'x': 140, 'y': 120, 'size': 50},
                {'type': 'marker', 'style': 'underline', 'x': 140, 'y': 190, 'width': 360, 'height': 20, 'weight': .3}]}]}]}
    (root / 'job.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    command = [sys.executable, '-B', str(Path(__file__).with_name('handdraw_video.py'))]
    environment = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}
    for stage in ('doctor', 'build', 'render', 'verify'):
        subprocess.run(command + [stage, str(root)], check=True, env=environment)
    timeline = json.loads((root / 'work' / 'timeline.json').read_text())
    if len(timeline['pages']) != 2 or len(timeline['cues']) != 3:
        raise AssertionError('Page/beat counts were not taken from the job')
    if abs((timeline['pages'][0]['end'] - timeline['pages'][0]['start']) - (timeline['pages'][1]['end'] - timeline['pages'][1]['start'])) < 1:
        raise AssertionError('Different audio lengths produced fixed-length pages')
    blocked = subprocess.run(command + ['finalize', str(root)], capture_output=True, text=True, env=environment)
    if blocked.returncode == 0 or 'Runtime fixtures can never be delivered' not in blocked.stderr:
        raise AssertionError('A runtime fixture was not blocked from delivery')
    original = (root / 'job.json').read_text()
    changed = json.loads(original)
    changed['title'] = '修改后的未验证任务'
    (root / 'job.json').write_text(json.dumps(changed, ensure_ascii=False))
    stale = subprocess.run(command + ['verify', str(root)], capture_output=True, text=True, env=environment)
    (root / 'job.json').write_text(original)
    if stale.returncode == 0 or 'Manifest changed' not in stale.stderr:
        raise AssertionError('A stale manifest was incorrectly accepted')
    stages = [item['stage'] for item in json.loads((root / 'work' / 'timing.json').read_text())['records']]
    if stages[:4] != ['doctor', 'build', 'render', 'verify']:
        raise AssertionError('Tool stages were not timed: ' + ', '.join(stages))
    if rare and rare not in timeline['cues'][-1]['text']:
        raise AssertionError('Rare characters were dropped from the captions')
    report = {'status': 'offline_runtime_checks_passed', 'fixture_only': True, 'visual_acceptance_claimed': False, 'rare_glyphs': rare,
        'checks': ['variable pages and beat counts', 'actual-audio timing', '960x540 at 24fps',
                   'Chinese stroke tips and punctuation', 'tiny isolated color patch', 'ink-only artwork', 'reveal-mode illustration',
                   'full H264/AAC decode', 'runtime fixtures cannot be delivered', 'changed manifest blocks old verification',
                   'stage timing records'] + (['rare glyph coverage'] if rare else [])}
    (root / 'smoke-result.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
