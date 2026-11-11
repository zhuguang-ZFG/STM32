"""Stroke-order handwriting: Make Me a Hanzi outlines revealed along their medians, font paths for the rest.

Glyph data (Arphic Public License, see assets/hanzi/ARPHICPL.TXT) covers GB2312; other characters are fetched
once from jsDelivr into the asset cache. A line with any unavailable ideograph returns None so the caller can
draw the whole line with the font instead.
"""
from pathlib import Path
import json
import lzma
import os
import re
import sys
import unicodedata
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import urlopen
import numpy as np
from PIL import Image, ImageDraw
from scipy.spatial import cKDTree
from motion_profile import time_fraction

PACKAGE = Path(__file__).resolve().parents[1]
BUNDLE = PACKAGE / 'assets/hanzi/gb2312-strokes.json.xz'
SOURCE = 'hanzi-writer-data@2.0.1'
CDN = 'https://cdn.jsdelivr.net/npm/' + SOURCE + '/{}.json'
INK_SPEED, MAX_SPEED, TRAVEL_SPEED = 8., 14., 20.  # em per second
VIDEO_LAPSE = 1.8  # natural pace / video pace
BOLD = .012  # extra half-width in em
_bundle = None
_online = os.environ.get('HANDDRAW_HANZI_FETCH', '1') != '0'


def is_hanzi(character):
    return unicodedata.name(character, '').startswith(('CJK UNIFIED IDEOGRAPH', 'CJK COMPATIBILITY IDEOGRAPH'))


def cache_path(character):
    base = Path(os.environ.get('HANDDRAW_ASSET_CACHE', str(Path.home() / '.cache/sweety-handdraw-video'))).expanduser()
    return base / SOURCE / f'{ord(character):x}.json'


def well_formed(data):
    strokes, medians = data.get('strokes'), data.get('medians')
    return (isinstance(strokes, list) and isinstance(medians, list) and 0 < len(strokes) == len(medians)
            and all(isinstance(stroke, str) for stroke in strokes)
            and all(len(median) >= 2 and all(len(point) == 2 for point in median) for median in medians))


def character_data(character):
    """Return [outlines, medians] or None; never raises for missing data or an offline machine."""
    global _bundle, _online
    if _bundle is None:
        _bundle = json.loads(lzma.decompress(BUNDLE.read_bytes()))['characters']
    if character in _bundle:
        return _bundle[character]
    path = cache_path(character)
    try:
        data = json.loads(path.read_text()) if path.is_file() else None
        if data is None and _online:
            with urlopen(CDN.format(quote(character)), timeout=4) as response:
                data = json.loads(response.read(1 << 20))
            if well_formed(data):
                path.parent.mkdir(parents=True, exist_ok=True)
                temporary = path.with_suffix('.tmp')
                temporary.write_text(json.dumps({'strokes': data['strokes'], 'medians': data['medians']}))
                temporary.replace(path)
    except HTTPError:
        return None
    except (OSError, ValueError):
        _online = False
        return None
    return [data['strokes'], data['medians']] if data and well_formed(data) else None


def outline(path, steps=6):
    """Flatten an SVG M/L/Q/C/Z outline (absolute or relative) to a polygon."""
    tokens = re.findall(r'[MLQCZmlqcz]|-?\d+(?:\.\d+)?', path)
    points, current, command, index = [], np.zeros(2), 'M', 0
    curve = np.linspace(0, 1, steps + 1)[1:, None]
    while index < len(tokens):
        if tokens[index].isalpha():
            command = tokens[index]
            index += 1
            continue
        count = {'m': 2, 'l': 2, 'q': 4, 'c': 6}[command.lower()]
        values = np.array(tokens[index:index + count], dtype=float).reshape(-1, 2)
        index += count
        if command.islower():
            values += current
        if len(values) == 1:
            points.append(values[0])
        elif len(values) == 2:
            points.extend((1-curve)**2*current + 2*(1-curve)*curve*values[0] + curve**2*values[1])
        else:
            points.extend((1-curve)**3*current + 3*(1-curve)**2*curve*values[0] + 3*(1-curve)*curve**2*values[1] + curve**3*values[2])
        current = values[-1]
    return np.array(points)


def densify(points, step=1.):
    points = np.asarray(points, dtype=float)
    keep = np.r_[True, np.linalg.norm(np.diff(points, axis=0), axis=1) > 1e-6]
    points = points[keep]
    if len(points) < 2:
        return np.array([points[0], points[0] + [.01, 0]])
    distance = np.r_[0, np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))]
    samples = np.linspace(0, distance[-1], max(2, int(np.ceil(distance[-1] / step)) + 1))
    return np.c_[np.interp(samples, distance, points[:, 0]), np.interp(samples, distance, points[:, 1])]


def arc_lengths(points):
    return np.r_[0, np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))]


def extend_to_tips(points, alpha, limit):
    """Carry the nib from the median ends to the outline tips so end pixels stay under the pen."""
    def reach(tip, inner):
        direction = tip - inner
        direction /= max(1e-6, np.linalg.norm(direction))
        extension = []
        for distance in np.arange(.5, limit, .5):
            x, y = np.rint(tip + direction * distance).astype(int)
            if not (0 <= y < alpha.shape[0] and 0 <= x < alpha.shape[1]) or alpha[y, x] < .5:
                break
            extension.append(tip + direction * distance)
        return extension
    head = reach(points[0], points[min(3, len(points) - 1)])[::-1]
    tail = reach(points[-1], points[max(0, len(points) - 4)])
    return np.vstack([np.array(head).reshape(-1, 2), points, np.array(tail).reshape(-1, 2)])


def push_corners(points, alpha, size):
    """Move sharp median turns into the outline corner, where a writer's pen actually turns."""
    points = np.asarray(points, dtype=float).copy()
    for index in range(1, len(points) - 1):
        incoming, outgoing = points[index] - points[index - 1], points[index + 1] - points[index]
        incoming /= max(1e-6, np.linalg.norm(incoming))
        outgoing /= max(1e-6, np.linalg.norm(outgoing))
        if incoming @ outgoing > .5:
            continue
        direction = incoming - outgoing
        direction /= max(1e-6, np.linalg.norm(direction))
        reach = 0.
        while reach < size * .2:
            x, y = np.rint(points[index] + direction * (reach + .5)).astype(int)
            if not (0 <= y < alpha.shape[0] and 0 <= x < alpha.shape[1]) or alpha[y, x] < .5:
                break
            reach += .5
        points[index] += direction * max(0., reach - size * .04)
    return points


def orient(path):
    """Font fallback strokes run left-to-right when horizontal, otherwise top-to-bottom."""
    delta = path[-1] - path[0]
    if np.hypot(*delta) >= 2 and (delta[0] < 0 if abs(delta[0]) > abs(delta[1]) else delta[1] < 0):
        return path[::-1]
    return path


def fit_to_font(font, size):
    """Match the data glyphs to the font's own ideograph height and centre so mixed punctuation lines up."""
    scale = size / 1024
    reference = np.vstack([outline(stroke) for stroke in character_data('国')[0]])
    low, high = reference[:, 1].min(), reference[:, 1].max()
    box = font.getbbox('国')
    factor = float(np.clip((box[3] - box[1]) / max(1, (high - low) * scale), .9, 1.15))
    return scale * factor, (low + high) / 2, (box[1] + box[3]) / 2


def hanzi_strokes(data, advance, fit):
    """Outline polygons and medians in pixel coordinates relative to the pen origin ('la' anchor)."""
    scale, data_middle, font_middle = fit
    convert = lambda points: np.c_[advance / 2 + (np.asarray(points, float)[:, 0] - 512) * scale,
                                   font_middle - (np.asarray(points, float)[:, 1] - data_middle) * scale]
    return [(convert(outline(stroke)), convert(median)) for stroke, median in zip(*data)]


def bounds(strokes, pad):
    corners = np.vstack([polygon for polygon, _ in strokes])
    left, top = np.floor(corners.min(axis=0) - pad).astype(int) - 1
    right, bottom = np.ceil(corners.max(axis=0) + pad).astype(int) + 2
    return int(left), int(top), int(right), int(bottom)


def rasterize(polygon, shape, offset, bold=0., supersample=4):
    image = Image.new('L', (shape[1] * supersample, shape[0] * supersample))
    points = [tuple(point) for point in (polygon - offset) * supersample]
    drawing = ImageDraw.Draw(image)
    drawing.polygon(points, fill=255)
    if bold > 0:
        # A thin brush outline gives the calligraphic outlines a marker-like weight.
        drawing.line(points + points[:1], fill=255, width=max(1, round(2 * bold * supersample)), joint='curve')
    return np.asarray(image.resize((shape[1], shape[0]), Image.Resampling.BOX), dtype=np.float32) / 255


def schedule(characters, size, seconds, fps):
    """Natural, minimum (visibility/speed cap) and final durations for strokes and pen lifts."""
    frame = 1 / max(1, fps)
    items, previous = [], None
    for index, strokes in enumerate(characters):
        for number, points in enumerate(strokes):
            if previous is not None:
                gap = np.linalg.norm(points[0] - previous) / size
                items.append(['travel', index, max(frame, (.03 if number else .08) + gap / TRAVEL_SPEED), frame / 2])
            length = arc_lengths(points)[-1] / size
            items.append(['ink', index, max(2 * frame, .04 + length / INK_SPEED), max(2 * frame, length / MAX_SPEED)])
            previous = points[-1]
    natural, minimum = sum(item[2] for item in items), sum(item[3] for item in items)
    # Video pace: a title is written in about half its natural time and then stays; extra window time is handed back.
    paced = max(minimum, natural / VIDEO_LAPSE)
    seconds = paced if seconds is None else min(float(seconds), paced)
    if seconds >= minimum:
        blend = (seconds - minimum) / max(1e-9, natural - minimum)
        durations = [item[3] + blend * (item[2] - item[3]) for item in items]
    else:
        durations = [item[3] * seconds / minimum for item in items]
    timing = {'seconds': seconds, 'natural_seconds': round(float(natural), 3), 'minimum_seconds': round(float(minimum), 3),
              'compressed': bool(seconds < minimum)}
    return [duration / seconds for duration in durations], timing


def build_line(text, font, size, color, seconds=None, fps=30, margin=5):
    """Return (pixels, reveal, owners, segments, characters, origin, report) or None when any glyph lacks data."""
    fit = fit_to_font(font, size) if any(is_hanzi(character) for character in text) else None
    glyphs, cursor = [], 0.
    for character in text:
        if is_hanzi(character):
            data = character_data(character)
            if data is None:
                return None
            strokes = hanzi_strokes(data, font.getlength(character), fit)
            glyphs.append([character, round(cursor), bounds(strokes, size * BOLD), strokes])
        else:
            glyphs.append([character, round(cursor), font.getbbox(character), None])
        cursor += font.getlength(character)
    left = min([0] + [x + box[0] for _, x, box, _ in glyphs])
    top = min([0] + [box[1] for _, _, box, _ in glyphs])
    right = max([int(np.ceil(cursor))] + [x + box[2] for _, x, box, _ in glyphs])
    bottom = max([0] + [box[3] for _, _, box, _ in glyphs])
    width, height, origin = int(right - left + 2 * margin), int(bottom - top + 2 * margin), [int(margin - left), int(margin - top)]
    alpha = np.zeros((height, width), dtype=np.float32)
    # Each character: (layer offset, patch shape, [(stroke alpha patch or None, nib path in layer coordinates)]).
    characters = []
    for character, x, box, strokes in glyphs:
        offset = np.array([origin[0] + x + box[0], origin[1] + box[1]])
        shape = (max(1, box[3] - box[1]), max(1, box[2] - box[0]))
        entries = []
        if strokes is not None:
            for number, (polygon, median) in enumerate(strokes):
                # A real pen presses unevenly: vary each stroke's weight so the line reads hand-written, not typeset.
                factor = .82 + .5 * (((ord(character) * 2654435761 + number * 40503) % 1000) / 1000.)
                patch = rasterize(polygon, shape, np.array(box[:2]), size * BOLD * factor)
                points = extend_to_tips(densify(push_corners(median - box[:2], patch, size)), patch, size * .1)
                entries.append((patch, densify(points) + offset))
        else:
            from stroke_assets import ordered_paths
            glyph = Image.new('L', (shape[1], shape[0]))
            ImageDraw.Draw(glyph).text((-box[0], -box[1]), character, font=font, fill=255)
            patch = np.asarray(glyph, dtype=np.float32) / 255
            paths = [orient(path) for path in ordered_paths(patch > 30 / 255)]
            entries = [(patch if number == 0 else None, densify(path) + offset) for number, path in enumerate(paths)]
            if not paths and patch.any():
                entries = [(patch, np.array([offset + shape[::-1] / 2, offset + shape[::-1] / 2 + [.01, 0]]))]
        characters.append((offset, shape, entries))
        for patch, _ in entries:
            if patch is not None:
                region = alpha[offset[1]:offset[1] + shape[0], offset[0]:offset[0] + shape[1]]
                np.maximum(region, patch, out=region)
    fractions, timing = schedule([[points for _, points in entries] for _, _, entries in characters], size, seconds, fps)
    reveal = np.full((height, width), np.inf, dtype=np.float32)
    owners = np.full((height, width), -1, dtype=np.int16)
    segments, intervals, cursor, item, previous = [], [], 0., 0, None
    for index, ((offset, shape, entries), (character, _, _, strokes)) in enumerate(zip(characters, glyphs)):
        rows, columns = slice(offset[1], offset[1] + shape[0]), slice(offset[0], offset[0] + shape[1])
        local_reveal, local_alpha = reveal[rows, columns], alpha[rows, columns]
        yy, xx = np.mgrid[rows, columns]
        start = None
        timed = []
        for patch, points in entries:
            if previous is not None:
                segments.append({'kind': 'travel', 'start': cursor, 'end': cursor + fractions[item],
                                 'points': [previous.tolist(), points[0].tolist()]})
                cursor += fractions[item]
                item += 1
            lengths = arc_lengths(points)
            segments.append({'kind': 'ink', 'start': cursor, 'end': cursor + fractions[item], 'points': points.tolist(),
                             'lengths': lengths.tolist(), 'profile': 'minjerk', 'character_index': index})
            timed.append((patch, points, lengths, cursor, fractions[item]))
            start = cursor if start is None else start
            cursor += fractions[item]
            item += 1
            previous = points[-1]
        if strokes is not None:
            # Earliest stroke that holds at least half of the pixel's final coverage owns its reveal time.
            for patch, points, lengths, begin, duration in timed:
                selected = (patch > 0) & ~np.isfinite(local_reveal) & (patch >= .5 * local_alpha)
                if selected.any():
                    _, nearest = cKDTree(points).query(np.c_[xx[selected], yy[selected]])
                    local_reveal[selected] = begin + duration * time_fraction(lengths[nearest] / max(1e-6, lengths[-1]), 'minjerk')
        elif timed:
            selected = (timed[0][0] > 0) & ~np.isfinite(local_reveal)
            ends = np.cumsum([len(points) for _, points, _, _, _ in timed])
            points = np.vstack([points for _, points, _, _, _ in timed])
            _, nearest = cKDTree(points).query(np.c_[xx[selected], yy[selected]])
            stroke = np.searchsorted(ends, nearest, side='right')
            times = np.empty(len(nearest))
            for number, (_, _, lengths, begin, duration) in enumerate(timed):
                chosen = stroke == number
                position = nearest[chosen] - (ends[number - 1] if number else 0)
                times[chosen] = begin + duration * time_fraction(lengths[position] / max(1e-6, lengths[-1]), 'minjerk')
            local_reveal[selected] = times
        owners[rows, columns][np.isfinite(local_reveal) & (owners[rows, columns] < 0)] = index
        intervals.append({'index': index, 'character': character, 'start': start if start is not None else cursor, 'end': cursor})
    pixels = np.zeros((height, width, 4), dtype=np.uint8)
    pixels[:, :, :3] = tuple(int(color[index:index + 2], 16) for index in (1, 3, 5))
    pixels[:, :, 3] = np.rint(alpha * 255).astype(np.uint8)
    reveal[pixels[:, :, 3] == 0] = np.inf
    owners[pixels[:, :, 3] == 0] = -1
    if timing['seconds'] < timing['minimum_seconds'] / 2:
        print(f"handwriting: {text!r} gets {timing['seconds']:.2f}s, so several strokes share one frame; "
              f"give it >= {timing['minimum_seconds']}s (natural {timing['natural_seconds']}s) via weight", file=sys.stderr)
    report = {'mode': 'stroke_order', 'source': SOURCE, **timing}
    return pixels, reveal, owners, segments, intervals, origin, report
