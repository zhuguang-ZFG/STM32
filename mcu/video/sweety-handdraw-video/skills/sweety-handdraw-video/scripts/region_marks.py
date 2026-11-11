#!/usr/bin/env python3
"""Set-of-Mark regions for an illustration: number the closed areas of its line art (plus distinct color
areas inside large ones) and write a legible overlay, so the model only maps region numbers to ordered
semantic parts: action "region_map" + "part_regions":[{"id":"head","regions":[3,4,7]}, ...]."""
import argparse
import colorsys
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
import line_topology
from paint_motion import palette


def compute(pixels, alpha, outline):
    visible = alpha > 0
    clean = line_topology.clean_outline(outline)
    walls = ndimage.binary_dilation(clean if clean.any() else outline)
    labels, _ = ndimage.label(visible & ~walls)
    sizes = np.bincount(labels.ravel())
    minimum = max(40, int(.0004 * visible.sum()))
    keep = sizes >= minimum
    keep[0] = False
    labels = np.where(keep[labels], labels, 0)
    kinds = {value: 'closed' for value in np.flatnonzero(keep)}
    rgb = pixels[:, :, :3].astype(float)
    for value in list(kinds):
        mask = labels == value
        if sizes[value] < max(4000, .03 * visible.sum()):
            continue
        groups = np.zeros(mask.shape, np.int32)
        groups[mask] = palette(rgb[mask]) + 1
        pieces = []
        for group in np.unique(groups[mask]):
            parts, count = ndimage.label(ndimage.binary_opening(groups == group, iterations=2))
            part_sizes = np.bincount(parts.ravel())
            pieces += [parts == k for k in range(1, count + 1) if part_sizes[k] >= max(10 * minimum, .15 * sizes[value])]
        for piece in sorted(pieces, key=lambda piece: -piece.sum())[1:]:
            identity = labels.max() + 1
            labels[piece] = identity
            kinds[identity] = 'color'
    # Line work far from every closed area (an arrow, a tendril) gets its own number instead of joining a neighbour.
    far = visible & (labels == 0) & (ndimage.distance_transform_edt(labels == 0) > 12)
    strokes, count = ndimage.label(far, structure=np.ones((3, 3)))
    stroke_sizes = np.bincount(strokes.ravel())
    for value in range(1, count + 1):
        if stroke_sizes[value] >= 2 * minimum:
            identity = labels.max() + 1
            labels[strokes == value] = identity
            kinds[identity] = 'line'
    _, nearest = ndimage.distance_transform_edt(labels == 0, return_indices=True)
    labels = np.where(visible, labels[nearest[0], nearest[1]], 0)
    regions = []
    for old in [value for value in np.unique(labels) if value]:
        mask = labels == old
        (top, left), (bottom, right) = np.argwhere(mask).min(0), np.argwhere(mask).max(0) + 1
        depth = ndimage.distance_transform_edt(np.pad(mask[top:bottom, left:right], 1))[1:-1, 1:-1]
        y, x = np.unravel_index(int(np.argmax(depth)), depth.shape)
        regions.append({'old': int(old), 'area': int(mask.sum()), 'anchor': [int(left + x), int(top + y)],
                        'bbox': [int(left), int(top), int(right), int(bottom)], 'kind': kinds.get(old, 'closed'),
                        'color': '#%02x%02x%02x' % tuple(int(v) for v in np.median(rgb[mask], axis=0))})
    regions.sort(key=lambda region: (region['anchor'][1] // 40, region['anchor'][0]))
    numbered = np.zeros(labels.shape, np.int32)
    for identity, region in enumerate(regions, 1):
        numbered[labels == region.pop('old')] = identity
        region['id'] = identity
    return numbered, regions


def font(size):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def overlay(pixels, alpha, labels, regions):
    scale = 2 if max(labels.shape) < 1200 else 1
    base = np.full(labels.shape + (3,), 255.)
    weight = (alpha.astype(float) / 255)[..., None]
    base = base * (1 - weight * .55) + pixels[:, :, :3] * weight * .55
    tint = np.zeros(labels.shape + (3,))
    for region in regions:
        hue = (region['id'] * .618034) % 1
        tint[labels == region['id']] = np.array(colorsys.hsv_to_rgb(hue, .65, .95)) * 255
    painted = (labels > 0)[..., None]
    image = np.where(painted, base * .6 + tint * .4, base)
    edges = (labels != np.roll(labels, 1, 0)) | (labels != np.roll(labels, 1, 1))
    image[edges & (labels > 0)] = (40, 40, 40)
    picture = Image.fromarray(image.astype(np.uint8)).resize((labels.shape[1] * scale, labels.shape[0] * scale), Image.Resampling.NEAREST)
    draw = ImageDraw.Draw(picture)
    for region in regions:
        size = int(np.clip(np.sqrt(region['area']) * scale / 3, 12, 30))
        x, y = region['anchor'][0] * scale, region['anchor'][1] * scale
        draw.text((x, y), str(region['id']), font=font(size), fill=(0, 0, 0), anchor='mm', stroke_width=max(2, size // 6), stroke_fill=(255, 255, 255))
    return picture


def build_region_marks(source, width, height, prefix, crop=None, outline_mask=None):
    from stroke_assets import prepare_artwork
    artwork = prepare_artwork(source, width, height, crop, outline_mask)
    labels, regions = compute(artwork['pixels'], artwork['alpha'], artwork['outline'])
    prefix = Path(prefix)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(Path(source).read_bytes()).hexdigest()
    overlay(artwork['pixels'], artwork['alpha'], labels, regions).save(prefix.with_suffix('.png'))
    np.savez_compressed(prefix.with_suffix('.npz'), labels=labels, source_sha256=np.array(digest))
    record = {'source': str(source), 'source_sha256': digest, 'crop': crop, 'width': width, 'height': height,
              'outline_mask': str(outline_mask) if outline_mask else None, 'shape': list(labels.shape),
              'overlay': str(prefix.with_suffix('.png')), 'region_map': str(prefix.with_suffix('.npz')), 'regions': regions}
    prefix.with_suffix('.json').write_text(json.dumps(record, ensure_ascii=False, indent=1))
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('job', type=Path)
    parser.add_argument('plan_id', help='drawing_plan_id of the illustration action, or #N for the N-th illustration (0-based)')
    arguments = parser.parse_args()
    from drawing_contract import illustration_actions
    root = arguments.job.resolve()
    actions = list(illustration_actions(json.loads((root / 'job.json').read_text())))
    if arguments.plan_id.startswith('#'):
        action, identity = actions[int(arguments.plan_id[1:])], 'illustration-' + arguments.plan_id[1:]
    else:
        action = next(item for item in actions if item.get('drawing_plan_id') == arguments.plan_id)
        identity = arguments.plan_id
    resolve = lambda value: (root / value).resolve() if value else None
    record = build_region_marks(resolve(action['source']), int(action['width']), int(action['height']), root / 'design' / 'regions' / identity,
                                action.get('crop'), resolve(action.get('outline_mask')))
    print(json.dumps({'overlay': record['overlay'], 'regions': len(record['regions']),
                      'action_fields': {'region_map': f'design/regions/{identity}.npz',
                                        'part_regions': [{'id': '<part>', 'regions': ['<numbers from the overlay>']}]}}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
