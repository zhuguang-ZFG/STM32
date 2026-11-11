"""Lift the navy preset's pen out of its hand: same pen, same angle and scale, fingers removed.

The barrel is a straight cylinder, so it is unrolled into an (along, across) strip, the columns the thumb hides are
replaced by the nearest clean barrel column, edge colours are taken a few pixels inside the silhouette (no skin
fringe), and the strip is mapped back so the nib keeps its calibrated pixel position.

    python3 assets/hands/prompts/pen-only.py assets/hands/navy.png assets/hands/pen-only.png
"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

source, target = Path(sys.argv[1]), Path(sys.argv[2])
image = np.array(Image.open(source).convert('RGBA')).astype(np.float64)
rgb, alpha = image[:, :, :3], image[:, :, 3]
nib = np.array([94., 16.])                      # calibrated nib of navy.png
H, W = 340, 560                                 # the pen lies inside this corner of the source
dark = (rgb.mean(2) < 75) & (np.ptp(rgb, 2) < 30) & (alpha > 200)
dark[H:], dark[:, W:] = False, False
points = np.c_[np.nonzero(dark)[::-1]].astype(float)


def frame(axis):
    return axis, np.array([-axis[1], axis[0]]), (points - nib) @ axis, (points - nib) @ np.array([-axis[1], axis[0]])


axis = np.linalg.svd(points - points.mean(0), full_matrices=False)[2][0]
axis, normal, along, across = frame(axis if axis[0] > 0 else -axis)
# The nib lies on the pen's axis: aim the axis from the nib through the centre of the far, unhidden barrel.
far = (along > 430) & (along < 470)
centre = nib + 450 * axis + (np.percentile(across[far], 99) + np.percentile(across[far], 1)) / 2 * normal
axis, normal, along, across = frame((centre - nib) / np.linalg.norm(centre - nib))

ts = np.arange(0., along.max() + 1)
upper, lower = np.full(len(ts), np.nan), np.full(len(ts), np.nan)
for index, t in enumerate(ts):
    column = np.abs(along - t) < 2
    if column.sum() > 3:
        upper[index], lower[index] = np.percentile(across[column], 99), np.percentile(across[column], 1)
barrel = (ts > 120) & (ts < 480)
radius = float(np.median(((upper - lower) / 2)[(ts > 270) & (ts < 470)]))
hidden = barrel & ~((upper > radius - 3) & (lower < -radius + 3))
clean = int(np.nonzero(barrel & ~hidden & (ts > 270))[0][0])
half = np.full(len(ts), radius)
cone, tail = ts <= 120, ts >= 480
half[cone] = np.maximum.accumulate(ndimage.uniform_filter1d(np.nan_to_num((upper - lower) / 2)[cone], 7))
half[tail] = np.minimum(radius, np.nan_to_num((upper - lower) / 2)[tail])
shift = np.where(cone | tail, np.nan_to_num((upper + lower) / 2), 0.)

# Strip in (along, across): colour inset 3 px from the silhouette so no skin bleeds in; hidden columns copy clean barrel.
ns = np.arange(-radius - 2, radius + 2.01, .5)
T, N = np.meshgrid(ts, ns, indexing='ij')
limit = np.maximum(half, 1.)[:, None] - 3
inset = np.clip(N, -limit, limit) + shift[:, None]
sample = np.where(hidden[:, None], ts[clean], T)
sx, sy = nib[0] + sample * axis[0] + inset * normal[0], nib[1] + sample * axis[1] + inset * normal[1]
strip = np.dstack([ndimage.map_coordinates(rgb[:, :, c], [sy, sx], order=1) for c in range(3)])
coverage = np.clip(half[:, None] + .5 - np.abs(N), 0, 1)

ys, xs = np.mgrid[0:H, 0:W].astype(float)
local_t = (xs - nib[0]) * axis[0] + (ys - nib[1]) * axis[1]
local_n = (xs - nib[0]) * normal[0] + (ys - nib[1]) * normal[1]
index_t = np.clip(local_t, 0, len(ts) - 1)
index_n = np.clip((local_n - np.interp(index_t, ts, shift) - ns[0]) / .5, 0, len(ns) - 1)
out = np.zeros((H, W, 4))
for c in range(3):
    out[:, :, c] = ndimage.map_coordinates(strip[:, :, c], [index_t, index_n], order=1)
out[:, :, 3] = np.where((local_t >= 0) & (local_t <= ts[-1]), ndimage.map_coordinates(coverage, [index_t, index_n], order=1), 0) * 255
Image.fromarray(np.rint(out).astype(np.uint8)).save(target)
print(json.dumps({'axis_degrees': round(float(np.degrees(np.arctan2(axis[1], axis[0]))), 2), 'length_px': int(ts[-1]),
                  'radius_px': round(radius, 1), 'hidden_columns': int(hidden.sum()), 'clean_column': float(ts[clean]),
                  'size': [W, H], 'nib': nib.tolist()}))
