#!/usr/bin/env python3
"""Line-art quality gate: is this outline something a person could draw stroke by stroke?
Dense junctions, tiny closed holes, specks and short texture marks mean edge-detected texture: hundreds of
short marks no hand would draw in the window. Regenerate or simplify the line art (lineart_exception only records a
deliberate texture the pen will still draw mark by mark)."""
import argparse
import json
import numpy as np
from scipy import ndimage
import line_topology
from stroke_paths import thin_ink

# Calibrated on v1.3 samples: clean coloring-book/ink art passes, edge-detected shirt texture (wolf p4) fails.
THRESHOLDS = {'junctions_per_100px': 2.5, 'small_holes_per_kpx': 5.0, 'speck_ratio': .05, 'texture_stroke_ratio': .16}
MINIMUM_SKELETON = 400


def measure(outline, strokes=None, clean=None, skeleton=None):
    clean = line_topology.clean_outline(outline) if clean is None else clean
    skeleton = line_topology.prune_spurs(thin_ink(clean)) if skeleton is None else skeleton
    length = int(skeleton.sum())
    adjacency = line_topology.graph(skeleton)
    junction = np.zeros(skeleton.shape, bool)
    for (y, x), neighbors in adjacency.items():
        junction[y, x] = len(neighbors) >= 3
    junctions = ndimage.label(junction, structure=np.ones((3, 3)))[1]
    holes, count = ndimage.label(~clean)
    sizes = np.bincount(holes.ravel())
    border = set(np.unique(np.r_[holes[0], holes[-1], holes[:, 0], holes[:, -1]]).tolist())
    small_holes = sum(1 for label in range(1, count + 1) if sizes[label] < 60 and label not in border)
    blobs, _ = ndimage.label(outline, structure=np.ones((3, 3)))
    blob_sizes = np.bincount(blobs.ravel())
    specks = int(blob_sizes[1:][blob_sizes[1:] < 20].sum())
    if strokes is None:
        strokes = line_topology.extract_strokes(outline)[0]
    short = sum(stroke['length'] for stroke in strokes if stroke['length'] < 25)
    return {'skeleton_px': length, 'junctions_per_100px': round(100 * junctions / max(1, length), 3),
            'small_holes_per_kpx': round(1000 * small_holes / max(1, length), 3),
            'speck_ratio': round(specks / max(1, int(outline.sum())), 4),
            'texture_stroke_ratio': round(short / max(1., sum(stroke['length'] for stroke in strokes)), 3)}


def evaluate(outline, strokes=None, clean=None, skeleton=None):
    metrics = measure(outline, strokes, clean, skeleton)
    failures = [key for key, limit in THRESHOLDS.items() if metrics[key] > limit] if metrics['skeleton_px'] >= MINIMUM_SKELETON else []
    return {'passed': not failures, 'failures': failures, 'metrics': metrics, 'thresholds': THRESHOLDS}


def failure_message(gate):
    details = ', '.join(f"{key}={gate['metrics'][key]} (limit {gate['thresholds'][key]})" for key in gate['failures'])
    # The only way out is a drawable picture: switching to reveal or waiving the gate would drop the drawing instead.
    return ('Line art is texture-like and cannot be drawn stroke by stroke: ' + details +
            '. Regenerate or simplify the image: clean continuous outlines, fewer and longer marks, no hatching, stippling or texture edges.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source')
    parser.add_argument('--width', type=int, required=True)
    parser.add_argument('--height', type=int, required=True)
    parser.add_argument('--crop', type=int, nargs=4)
    parser.add_argument('--outline-mask')
    arguments = parser.parse_args()
    from stroke_assets import prepare_artwork
    artwork = prepare_artwork(arguments.source, arguments.width, arguments.height, arguments.crop, arguments.outline_mask)
    result = evaluate(artwork['outline'])
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result['passed'] else 1)
