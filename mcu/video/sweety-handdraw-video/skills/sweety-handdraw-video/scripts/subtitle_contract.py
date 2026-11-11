"""Reject duplicate caption layers, artwork under subtitles, muxed tracks and automatically loaded sidecars."""
import json
import math
from pathlib import Path
import subprocess
import numpy as np
from PIL import Image


def validate_subtitles(timeline):
    if timeline.get('captions') != {'presentation': 'burned', 'owner': 'caption_events'}:
        raise ValueError('Exactly one burned subtitle owner is required')
    captions = []
    for page in timeline['pages']:
        for event in page['events']:
            asset = timeline['assets'][event['asset']]
            is_caption = asset['type'] == 'typeset_caption'
            if bool(event.get('caption')) != is_caption or (event.get('role') == 'caption') != is_caption:
                raise ValueError('Caption asset and event roles must match')
            if is_caption:
                start, end = event['start'], event['hide']
                if not math.isfinite(start + end) or not page['start'] <= start < end <= page['end'] + .001:
                    raise ValueError('Subtitle must remain inside its page')
                captions.append((start, end, asset['text']))
            elif (asset.get('text') in {cue['text'] for cue in timeline['cues']}
                  and event.get('y', 0) >= timeline.get('canvas', {}).get('height', 1080) * .8):
                raise ValueError('Narration subtitle is duplicated in a bottom artwork text layer')
    captions.sort()
    cues = sorted((cue['start'], cue['end'], cue['text']) for cue in timeline['cues'])
    if captions != cues:
        raise ValueError('Every subtitle cue must have exactly one matching caption event')
    if any(left[1] > right[0] + 1e-7 for left, right in zip(captions, captions[1:])):
        raise ValueError('Multiple subtitles are visible at the same time')
    return {'owner': 'caption_events', 'cue_count': len(cues), 'maximum_simultaneous_captions': 1}


def caption_clearance(timeline, directory):
    """Artwork visible while a subtitle shows keeps clear of the subtitle's glyphs plus a margin. Checked on the real
    pixels at layout scale (camera moves aside): staying inside the canvas does not mean staying out of the subtitle."""
    margin, alpha, intruders = round(timeline['canvas']['height'] * .012), {}, {}
    def opaque(name, scale=1.):
        # Assets of a zoomed page are built at its board resolution; compare them at screen scale.
        if name not in alpha:
            image = Image.open(Path(directory) / f'{name}.png').getchannel('A')
            if scale != 1.:
                image = image.resize((max(1, round(image.width / scale)), max(1, round(image.height / scale))), Image.Resampling.BILINEAR)
            alpha[name] = np.array(image) > 24
        return alpha[name]
    for page in timeline['pages']:
        captions = [event for event in page['events'] if event['caption']]
        for event in page['events']:
            for caption in captions:
                if event['caption'] or event['start'] >= caption['hide'] or caption['start'] >= event['hide']:
                    continue
                glyphs = Image.open(Path(directory) / f"{caption['asset']}.png").getchannel('A').getbbox()
                if not glyphs:
                    continue
                art = opaque(event['asset'], float(event.get('scale', 1.)))
                x, y = round(event['x']), round(event['y'])
                left, top = max(caption['x'] + glyphs[0] - margin, x), max(caption['y'] + glyphs[1] - margin, y)
                right = min(caption['x'] + glyphs[2] + margin, x + art.shape[1])
                bottom = min(caption['y'] + glyphs[3] + margin, y + art.shape[0])
                if left < right and top < bottom and art[top - y:bottom - y, left - x:right - x].any():
                    asset = timeline['assets'][event['asset']]
                    label = (event.get('image') or [None])[0] or asset.get('text') or event['asset']
                    intruders.setdefault(label, (round(caption['start'], 2), timeline['assets'][caption['asset']]['text'], caption['y'] + glyphs[1] - margin))
    if intruders:
        raise ValueError('Artwork runs under the subtitle; move or shrink it to end above the subtitle band: ' +
                         '; '.join(f'{label} at {start}s under "{text}" (keep above y={limit})' for label, (start, text, limit) in intruders.items()))
    return {'margin_px': margin}


def validate_subtitle_delivery(video):
    video = Path(video)
    # Players differ in sidecar naming rules, so keep all editing subtitles elsewhere.
    suffixes = {'.srt', '.ass', '.ssa', '.vtt', '.sub', '.idx'}
    if any(path.suffix.lower() in suffixes for path in video.parent.iterdir() if path.is_file()):
        raise ValueError('Move subtitle sidecars into editing/ before delivering a burned-caption video')
    result = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 's', '-show_entries',
                             'stream=index', '-of', 'json', str(video)], check=True, capture_output=True, text=True)
    if json.loads(result.stdout).get('streams'):
        raise ValueError('Burned-caption video must not contain another subtitle track')
    return {'subtitle_streams': 0, 'adjacent_sidecars': 0, 'presentation': 'burned'}
