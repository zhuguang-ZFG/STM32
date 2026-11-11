#!/usr/bin/env python3
"""Objective human-likeness measurements of a built illustration asset: stroke statistics, pen-tip
motion, ordering efficiency, part cuts, speed variation, and anti-reveal (does a pixel first appear
already in its final color?). Works on draw-v2 layered assets and on legacy reveal assets."""
import argparse
import json
import math
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

PAPER = np.array([255., 255., 255.])
ANALYSIS_WIDTH = 240


def load_frames(directory, name, metadata):
    """Return (progress -> RGB float frame on white paper using the renderer's own composition, paint-pixel mask)."""
    directory = Path(directory)
    maps = np.load(directory / f'{name}.npz')
    if 'ink_owner' in maps.files:
        import illustration_layers
        layers = illustration_layers.load(directory, name)
        compose = lambda progress: illustration_layers.compose(layers, progress).astype(float)
        paint = (layers['line_alpha'] < .1) & (layers['alpha'] > .05)
    else:
        pixels = np.array(Image.open(directory / f'{name}.png').convert('RGBA')).astype(float)
        data = {key: maps[key] for key in maps.files}
        paint = (pixels[:, :, 3] > 12) & ((data['ink_weight'] < .5) if 'ink_weight' in data else True)

        def compose(progress):
            if 'ink' in data:
                fraction = data['ink_weight'] * np.clip((progress - data['ink']) * 250, 0, 1) + \
                    (1 - data['ink_weight']) * np.clip((progress - data['color']) * 250, 0, 1)
            else:
                fraction = np.clip((progress - data['reveal']) * 250, 0, 1)
            return np.dstack([pixels[:, :, :3], pixels[:, :, 3] * fraction])

    def frame(progress):
        rgba = compose(progress)
        alpha = rgba[:, :, 3:] / 255
        return rgba[:, :, :3] * alpha + PAPER * (1 - alpha)
    return frame, paint


def small(image, width=ANALYSIS_WIDTH):
    picture = Image.fromarray(np.clip(image, 0, 255).astype(np.uint8))
    return np.asarray(picture.resize((width, max(1, round(picture.height * width / picture.width))), Image.Resampling.BOX), float)


def anti_reveal(frame, paint, seconds, fps=15):
    """Over painted (non-line) pixels at full resolution: the fraction whose first visible color already
    equals the final one (a reveal) and the fraction modified more than once (paint builds up)."""
    count = max(2, int(round(seconds * fps)))
    final = frame(2.)
    distance = lambda first, second: np.sqrt(((first - second) ** 2).mean(2))
    selected = paint & (distance(final, PAPER) > 12)
    if not selected.any():
        return {'first_visible_equals_final': None, 'modified_more_than_once': None}
    final = final[selected]
    first = np.zeros_like(final)
    seen = np.zeros(len(final), bool)
    changes = np.zeros(len(final), np.int32)
    previous = np.broadcast_to(PAPER, final.shape)
    for index in range(1, count + 1):
        current = frame(index / count)[selected]
        fresh = ~seen & (np.sqrt(((current - PAPER) ** 2).mean(1)) > 12)
        first[fresh] = current[fresh]
        seen |= fresh
        changes += (np.sqrt(((current - previous) ** 2).mean(1)) > 5.5) & seen
        previous = current
    same = np.sqrt(((first - final) ** 2).mean(1)) <= 10
    return {'first_visible_equals_final': round(float(same.mean()), 3), 'modified_more_than_once': round(float((changes >= 2).mean()), 3)}


def tip_motion(metadata, seconds, fps=30):
    from video_renderer import point_on_asset
    count = max(2, int(round(seconds * fps)))
    kinds, points = [], []
    segments = metadata['segments']
    for index in range(count):
        progress = (index + .5) / count
        active = next((segment for segment in segments if segment['start'] <= progress <= segment['end']), None)
        kinds.append(active['kind'] if active else 'gap')
        points.append(point_on_asset(metadata, progress))
    points, kinds = np.array(points), np.array(kinds)
    result = {}
    for phase, selected in (('outline', np.isin(kinds, ['ink', 'sketch'])), ('fill', np.isin(kinds, ['color', 'shade', 'brush']))):
        moves = np.diff(points, axis=0)[selected[1:] & selected[:-1]]
        if len(moves) < 3:
            continue
        horizontal = moves[:, 0][np.abs(moves[:, 0]) > 1]
        result[phase] = {'reversals_per_s': round(float((horizontal[1:] * horizontal[:-1] < 0).sum() / (len(moves) / fps)), 2),
                         'jump_median_px': round(float(np.median(np.linalg.norm(moves, axis=1))), 1),
                         'jump_over_60px': round(float((np.linalg.norm(moves, axis=1) > 60).mean()), 3),
                         'upward_fraction': round(float((moves[:, 1] < -2).mean()), 3)}
    return result


def endpoint_direction(points, start, reach=6):
    k = min(reach, len(points) - 1)
    vector = points[k] - points[0] if start else points[-1 - k] - points[-1]
    norm = np.linalg.norm(vector)
    return vector / norm if norm > 1e-9 else vector


def stroke_statistics(metadata, seconds):
    strokes = [segment for segment in metadata['segments'] if segment['kind'] == 'ink']
    if not strokes:
        return {}
    shapes = [np.array(segment['points'], float) for segment in strokes]
    lengths = np.array([np.linalg.norm(np.diff(points, axis=0), axis=1).sum() for points in shapes])
    durations = np.array([(segment['end'] - segment['start']) * seconds for segment in strokes])
    speeds = lengths / np.maximum(durations, 1e-6)
    parts = [segment.get('part_id', segment.get('part_index')) for segment in strokes]
    owners = metadata_owners(metadata, strokes)
    parts = owners if owners is not None else parts
    travel = greedy = 0.
    for part in set(parts):
        sequence = [points for points, owner in zip(shapes, parts) if owner == part]
        travel += sum(np.linalg.norm(b[0] - a[-1]) for a, b in zip(sequence, sequence[1:]))
        remaining, tip = list(range(1, len(sequence))), sequence[0][-1] if sequence else None
        while remaining:
            choice = min(((index, end) for index in remaining for end in (0, -1)),
                         key=lambda item: np.linalg.norm(sequence[item[0]][item[1]] - tip))
            greedy += np.linalg.norm(sequence[choice[0]][choice[1]] - tip)
            remaining.remove(choice[0])
            tip = sequence[choice[0]][-1 if choice[1] == 0 else 0]
    cut = set()
    ends = [(index, start, points[0] if start else points[-1]) for index, points in enumerate(shapes) for start in (True, False)]
    from scipy.spatial import cKDTree
    for a, b in cKDTree([end[2] for end in ends]).query_pairs(2.5):
        (i, start_i, _), (j, start_j, _) = ends[a], ends[b]
        if i != j and parts[i] != parts[j]:
            cosine = -np.dot(endpoint_direction(shapes[i], start_i), endpoint_direction(shapes[j], start_j))
            if math.degrees(math.acos(float(np.clip(cosine, -1, 1)))) <= 35:
                cut |= {i, j}
    return {'drawn_strokes': len(strokes), 'median_length_px': round(float(np.median(lengths)), 1),
            'under_15px_count': round(float((lengths < 15).mean()), 3),
            'under_15px_length': round(float(lengths[lengths < 15].sum() / max(1., lengths.sum())), 3),
            'travel_over_nearest': round(travel / max(1., greedy), 2), 'cut_by_parts': round(len(cut) / len(strokes), 3),
            'speed_mean_px_s': round(float(speeds.mean())), 'speed_cv': round(float(speeds.std() / max(1e-6, speeds.mean())), 3)}


def metadata_owners(metadata, strokes):
    if strokes and 'part_id' in strokes[0]:
        return [segment['part_id'] for segment in strokes]
    if metadata.get('parts') and strokes:
        bounds = [(part['outline_start'], part['outline_end'], part['id']) for part in metadata['parts']]
        return [next((identity for low, high, identity in bounds if low - 1e-9 <= segment['start'] <= high + 1e-9), None) for segment in strokes]
    return None


def ssim(first, second):
    blur = lambda image: ndimage.gaussian_filter(image, 1.5)
    mean_a, mean_b = blur(first), blur(second)
    variance_a, variance_b = blur(first * first) - mean_a ** 2, blur(second * second) - mean_b ** 2
    covariance = blur(first * second) - mean_a * mean_b
    return float((((2 * mean_a * mean_b + 1e-4) * (2 * covariance + 9e-4)) /
                  ((mean_a ** 2 + mean_b ** 2 + 1e-4) * (variance_a + variance_b + 9e-4))).mean())


def line_fidelity(directory, name, outline):
    """SSIM and edge F1 at viewing scale between the rendered line layer and the source outline."""
    line = np.array(Image.open(Path(directory) / f'{name}-line.png'))[:, :, 3] / 255.
    shrink = lambda image: small(np.dstack([image * 255] * 3))[:, :, 0] / 255
    rendered, source = shrink(line), shrink(outline.astype(float))
    first, second = rendered > .3, source > .3
    precision = (first & ndimage.binary_dilation(second)).sum() / max(1, first.sum())
    recall = (second & ndimage.binary_dilation(first)).sum() / max(1, second.sum())
    return {'line_ssim_240': round(ssim(rendered, source), 3), 'line_edge_f1_240': round(float(2 * precision * recall / max(1e-9, precision + recall)), 3)}


def organization(metadata):
    """How planned the line pass looks: strokes that grow out of ink already on the page, long pen jumps,
    and how many separate scraps of line are visible while the picture forms (fewer reads as planned)."""
    strokes = [np.array(segment['points'], float) for segment in metadata['segments'] if segment['kind'] == 'ink']
    if len(strokes) < 2:
        return {}
    diagonal = math.hypot(metadata['width'], metadata['height'])
    reach = max(3., .012 * diagonal)
    from scipy.spatial import cKDTree
    attached, lifts = 0, []
    for index in range(1, len(strokes)):
        drawn = cKDTree(np.vstack(strokes[:index]))
        attached += drawn.query(strokes[index][0])[0] <= reach or drawn.query(strokes[index][-1])[0] <= reach
        lifts.append(np.linalg.norm(strokes[index][0] - strokes[index - 1][-1]))
    lifts = np.array(lifts) / diagonal
    shape = (metadata['height'], metadata['width'])
    scraps = {}
    for share in (.25, .5, .75):
        mask = np.zeros(shape, bool)
        for points in strokes[:max(1, round(share * len(strokes)))]:
            cells = np.clip(np.rint(points).astype(int), 0, [shape[1] - 1, shape[0] - 1])
            mask[cells[:, 1], cells[:, 0]] = True
        scraps[f'{share:.0%}'] = int(ndimage.label(ndimage.binary_dilation(mask, iterations=max(2, round(reach / 2))))[1])
    return {'attached_strokes': round(attached / (len(strokes) - 1), 3), 'lift_mean_of_diagonal': round(float(lifts.mean()), 3),
            'long_jumps': int((lifts > .25).sum()), 'visible_scraps': scraps}


def speckles(directory, name, metadata):
    """Grain left in the line pass: tiny islands of ink and half-transparent ink pixels with no solid line
    next to them, measured on the frame where every line is down and no marker has started."""
    maps = np.load(Path(directory) / f'{name}.npz')
    if 'ink_owner' not in maps.files:
        return {}
    import illustration_layers
    layers = illustration_layers.load(directory, name)
    ink = np.asarray(maps['ink'])
    color = np.asarray(maps['color'])
    line_end = float(np.max(ink[np.isfinite(ink)], initial=0.))
    first_color = float(np.min(color[np.isfinite(color)], initial=1.))
    progress = min(line_end + .002, max(first_color - .001, 0.)) if np.isfinite(first_color) else line_end + .002
    visible = illustration_layers.compose(layers, np.float32(progress))[:, :, 3] / 255.
    solid = visible > .5
    labels, count = ndimage.label(solid, structure=np.ones((3, 3)))
    sizes = np.bincount(labels.ravel())[1:]
    partial = (visible > .08) & ~solid & ~ndimage.binary_dilation(solid, iterations=1)
    return {'speck_islands': int((sizes <= 6).sum()), 'loose_partial_pixels_per_kpx': round(1000 * float(partial.sum()) / max(1, int((visible > .08).sum())), 1)}


def measure(directory, name, seconds=None, outline=None, fps=30):
    metadata = json.loads((Path(directory) / f'{name}.json').read_text())
    seconds = float(seconds or metadata.get('seconds') or 1.)
    report = {'name': name, 'engine': metadata.get('engine', 'reveal-v1'), 'seconds': round(seconds, 2)}
    report.update(stroke_statistics(metadata, seconds))
    report['organization'] = organization(metadata)
    report['speckles'] = speckles(directory, name, metadata)
    report['tip'] = tip_motion(metadata, seconds, fps)
    report.update(anti_reveal(*load_frames(directory, name, metadata), seconds))
    if outline is not None and (Path(directory) / f'{name}-line.png').exists():
        report.update(line_fidelity(directory, name, outline))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('assets', type=Path, help='work/assets directory')
    parser.add_argument('name', help='asset name, e.g. element-0007')
    parser.add_argument('--seconds', type=float, help='event seconds (legacy assets do not record them)')
    arguments = parser.parse_args()
    print(json.dumps(measure(arguments.assets, arguments.name, arguments.seconds), ensure_ascii=False, indent=2))
