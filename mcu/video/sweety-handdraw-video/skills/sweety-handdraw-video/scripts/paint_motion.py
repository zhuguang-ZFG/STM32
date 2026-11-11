"""Color like a person with a marker: per part, per color region, first a pass along the inside of the region's edge,
then short back-and-forth strokes across the shape (a slanted hatch on round shapes), then touch-ups for corners the
marker missed, and finally a few broad soft shading strokes. A fresh stroke is streaky, felt-textured color; it turns
solid where the next stroke overlaps it or a moment later, so paint never stamps in as flat blocks."""
import math
import numpy as np
from scipy import ndimage
from line_drawing import frame_floor, lift_seconds, weighted_lengths

FILL_SPEED = 700.     # px/s of marker travel for a person coloring at 1080p
SHADE_SECONDS = .35   # per shaded part, at human pace
SHADE_RAMP = .3       # seconds over which a broad soft stroke blends flat color into the source
SCALES = (1., 1.5, 2., 3.)
CAREFUL = 2.          # up to this marker scale a region gets its edge pass and overlapping strokes; the broadest marker
                      # (a window too short for care) sweeps rows at the old spacing with no edge pass
FILL_FACTOR = 6.      # coloring cap: a broad marker has no detail to follow, so time-lapsed coloring reads as human at 6x
FILL_FRAME_PX = 120.  # a broad marker may sweep this far per frame: its own width keeps the swept color continuous
PART_PAUSE = .12      # short rest when the marker moves to the next semantic part
ROW_SPACING = 1.1     # stroke step in marker radii: neighbouring strokes overlap, so most paint gets a second coat
QUICK_SPACING = 1.25  # ... and the broadest marker's step
REACH = 9.            # longest stroke in marker radii; a wider shape is colored in lanes, as a wrist would
ELONGATED = 1.8       # a shape this much longer than wide is colored across, the marker travelling along it
HATCH = math.radians(-60)   # a right hand's natural slant on a round shape (lower left to upper right)
TILT = math.radians(18)     # strokes across a long shape lean this much toward the natural slant
EDGE_MIN = 2.         # a region thicker than this many radii first gets a pass along the inside of its edge
EDGE_INSET = .55      # that pass runs this many radii inside the edge
STREAK = 3.2          # px period of the felt streaks along a stroke
WET = (.42, .9)       # alpha range of a single streaky coat
COAT_DELAY = .3       # seconds after which a single coat reads solid (sooner when the next stroke overlaps it)
COAT_REACH = 6.       # ... but no later than the marker takes to travel this many radii
COAT_RAMP = .12       # seconds over which streaky color settles to solid
JOIN = 4.             # passes whose ends are this many radii apart are joined without lifting the marker
FRONT_FRAMES = 1.5    # frames over which a freshly touched pixel comes in: a moving marker smears, it does not stamp


def inpaint_lines(pixels, line_zone):
    """Replace ink (and its anti-aliased halo) with the nearest paint so lines live only in the line layer."""
    if not line_zone.any() or line_zone.all():
        return pixels.copy()
    _, nearest = ndimage.distance_transform_edt(line_zone, return_indices=True)
    return pixels[nearest[0], nearest[1]]


def palette(colors, count=3, rounds=8, merge=28.):
    """Small k-means; clusters whose colors are perceptually close are merged (noise is not a region)."""
    luminance = colors @ [.299, .587, .114]
    order = np.argsort(luminance)
    centers = np.array([colors[order[int(q * (len(colors) - 1))]] for q in np.linspace(.1, .9, count)])
    for _ in range(rounds):
        labels = np.argmin(((colors[:, None] - centers[None]) ** 2).sum(2), 1)
        centers = np.array([colors[labels == k].mean(0) if (labels == k).any() else centers[k] for k in range(count)])
    target = list(range(count))
    for first in range(count):
        for second in range(first + 1, count):
            if np.linalg.norm(centers[first] - centers[second]) < merge:
                target = [target[first] if value == target[second] else value for value in target]
    return np.array(target)[labels]


def region_pixels(region, image):
    (left, top), (height, width) = region['offset'], region['mask'].shape
    return image[top:top + height, left:left + width][region['mask']]


def color_regions(rgb, visible, owners, part_count, labels=None, size=1.):
    """Regions to paint: the model's region map when given, else palette regions per part.
    Specks are absorbed by their nearest region instead of becoming separate passes."""
    regions = []
    for part in range(part_count):
        mask = visible & (owners == part)
        area = int(mask.sum())
        if area < 60:  # a few specks are not a region to colour; the line layer carries this part
            continue
        cells = np.argwhere(mask)
        (top, left), (bottom, right) = cells.min(0), cells.max(0) + 1
        crop = (slice(top, bottom), slice(left, right))
        local = mask[crop]
        found = np.zeros(local.shape, np.int32)
        if labels is not None:
            found[local] = labels[crop][local]
        elif area >= 120:
            clusters = np.zeros(local.shape, np.int32)
            clusters[local] = palette(rgb[crop][local].astype(float)) + 1
            for cluster in np.unique(clusters[local]):
                pieces, count = ndimage.label(ndimage.binary_opening(clusters == cluster, iterations=2))
                sizes = np.bincount(pieces.ravel())
                for piece in range(1, count + 1):
                    if sizes[piece] >= max(400 * size * size, .03 * area):  # the same piece of paint at any picture size
                        found[pieces == piece] = found.max() + 1
        sizes = np.bincount(found[local], minlength=found.max() + 1)
        large = [value for value in range(1, len(sizes)) if sizes[value] >= max(60, .01 * area)]
        found[~np.isin(found, large)] = 0
        if not large:
            found[local], large = 1, [1]
        _, nearest = ndimage.distance_transform_edt(found == 0, return_indices=True)
        found = np.where(local, found[nearest[0], nearest[1]], 0)
        for value in large:
            region = {'part': part, 'offset': np.array([left, top]), 'mask': found == value}
            region.update(area=int(region['mask'].sum()), flat=np.median(region_pixels(region, rgb), axis=0))
            regions.append(region)
    regions.sort(key=lambda region: (region['part'], region['offset'][1], region['offset'][0], -region['area']))
    return regions


def axes(points):
    center = points.mean(0)
    axis = np.linalg.eigh(np.cov(points.T))[1][:, -1] if len(points) > 3 else np.array([1., 0.])
    axis = axis if (axis[0] > 0 if abs(axis[0]) >= abs(axis[1]) else axis[1] > 0) else -axis
    across = np.array([-axis[1], axis[0]])
    return center, axis, (across if (across[1] > 0 if abs(across[1]) >= abs(across[0]) else across[0] > 0) else -across)


def rotate(vector, angle):
    cosine, sine = math.cos(angle), math.sin(angle)
    return np.array([cosine * vector[0] - sine * vector[1], sine * vector[0] + cosine * vector[1]])


def hatch_axes(points, tilt=None):
    """(center, stroke direction, sweep direction). A long shape is stroked across and swept along its length,
    leaning toward the hand's slant; a round one gets the slant itself. The sweep runs down (or right)."""
    center = points.mean(0)
    if len(points) > 3:
        values, vectors = np.linalg.eigh(np.cov(points.T))
        elongation = math.sqrt(max(values[1], 1e-6) / max(values[0], 1e-6))
    else:
        elongation, vectors = 1., np.eye(2)
    slant = np.array([math.cos(HATCH), math.sin(HATCH)])
    if elongation >= ELONGATED:
        axis = vectors[:, 0]
        axis = axis if axis @ slant >= 0 else -axis
        # Lean toward the slant, never past it.
        lean = math.copysign(min(TILT, math.acos(float(np.clip(axis @ slant, -1, 1)))), axis[0] * slant[1] - axis[1] * slant[0])
        axis = rotate(axis, lean)
    else:
        axis = slant
    if tilt:
        axis = rotate(axis, tilt)
    across = np.array([-axis[1], axis[0]])
    if (across[1] if abs(across[1]) >= abs(across[0]) else across[0]) < 0:
        across = -across
    return center, axis, across


def resample(polyline, step):
    polyline = np.asarray(polyline, float)
    if len(polyline) < 2:
        return polyline
    arc = np.r_[0., np.cumsum(np.linalg.norm(np.diff(polyline, axis=0), axis=1))]
    if arc[-1] <= step:
        return polyline[[0, -1]]
    fine = np.linspace(0, arc[-1], int(math.ceil(arc[-1] / step)) + 1)
    return np.c_[np.interp(fine, arc, polyline[:, 0]), np.interp(fine, arc, polyline[:, 1])]


def edge_paths(distance, offset, radius, step):
    """Closed paths along the inside of the region edge, EDGE_INSET radii in, starting at the top."""
    inset = EDGE_INSET * radius
    ys, xs = np.nonzero(np.abs(distance - inset) <= .8)
    if not len(xs):
        return []
    points = np.c_[xs, ys].astype(float)
    keys = np.floor(points / step).astype(np.int64)
    _, first = np.unique(keys[:, 0] * 1_000_003 + keys[:, 1], return_index=True)
    points = points[np.sort(first)]
    free = np.ones(len(points), bool)
    paths, current = [], int(np.lexsort((points[:, 0], points[:, 1]))[0])
    while free.any():
        free[current] = False
        path = [current]
        while free.any():
            gaps = np.linalg.norm(points - points[path[-1]], axis=1)
            gaps[~free] = np.inf
            nearest = int(np.argmin(gaps))
            if gaps[nearest] > 2.6 * step:
                break
            free[nearest] = False
            path.append(nearest)
        line = points[path]
        if len(line) > 2 and np.linalg.norm(line[-1] - line[0]) <= 2.6 * step:
            line = np.vstack([line, line[:1]])
        if len(line) >= 3:
            # A hand does not follow pixel steps: ease the path, keeping its ends.
            smooth = line.copy()
            smooth[1:-1] = (line[:-2] + 2 * line[1:-1] + line[2:]) / 4
            paths.append(resample(smooth, step) + offset)
        if free.any():
            remaining = np.nonzero(free)[0]
            current = int(remaining[np.argmin(np.linalg.norm(points[remaining] - line[-1], axis=1))])
    return paths


def hatch(points, center, axis, across, radius, step, spacing=None):
    """Back-and-forth strokes along `axis`, stepped along `across` with rounded turns. Strokes longer than REACH
    radii are cut into lanes (lane borders wander from row to row); a row that no longer overlaps the previous one in
    its lane starts a new cell. Returns polylines."""
    along_values, across_values = (points - center) @ axis, (points - center) @ across
    spacing = (spacing or ROW_SPACING) * radius
    low, high = along_values.min(), along_values.max()
    lanes = max(1, int(round((high - low) / (REACH * radius))))
    rows = []
    for index, offset in enumerate(np.arange(across_values.min() + .45 * radius, across_values.max() + .45 * radius, spacing)):
        band = np.sort(along_values[np.abs(across_values - offset) <= .6 * spacing])
        if not len(band):
            continue
        borders = low + (high - low) * np.arange(1, lanes) / lanes + .35 * radius * np.sin(1.7 * index + 2.3 * np.arange(1, lanes))
        pieces = []
        for run in np.split(band, np.where(np.diff(band) > 2 * radius)[0] + 1):
            a, b = run[0] - .3 * radius, run[-1] + .3 * radius
            cuts = [a] + [value for value in borders if a + radius < value < b - radius] + [b]
            pieces += [(offset, start, finish, int(np.searchsorted(borders, (start + finish) / 2))) for start, finish in zip(cuts, cuts[1:])]
        rows.append(pieces)
    unused = {(row, k) for row, runs in enumerate(rows) for k in range(len(runs))}
    cells, bulge = [], .35 * spacing
    position = lambda along, offset: center + along * axis + offset * across
    while unused:
        row, k = min(unused, key=lambda item: (rows[item[0]][item[1]][3], item))
        chain = [(row, k)]
        unused.discard((row, k))
        while row + 1 < len(rows):
            _, low_end, high_end, lane = rows[row][k]
            overlaps = [(min(high_end, b) - max(low_end, a), j) for j, (_, a, b, other) in enumerate(rows[row + 1])
                        if (row + 1, j) in unused and other == lane and min(high_end, b) > max(low_end, a)]
            if not overlaps:
                break
            row, k = row + 1, max(overlaps)[1]
            chain.append((row, k))
            unused.discard((row, k))
        polyline, previous = [], None
        for index, (row, k) in enumerate(chain):
            offset, a, b, _ = rows[row][k]
            if index % 2:
                a, b = b, a
            if previous is not None:
                end, end_offset, direction = previous
                turn = max(end, a) + bulge if direction > 0 else min(end, a) - bulge
                u = np.linspace(0, 1, 10)[1:-1, None]
                start, middle, finish = position(end, end_offset), position(turn, (end_offset + offset) / 2), position(a, offset)
                polyline.append((1 - u) ** 2 * start + 2 * u * (1 - u) * middle + u * u * finish)
            along = np.linspace(a, b, max(2, int(abs(b - a) / step) + 1))
            polyline.append(position(along[:, None], offset))
            previous = (b, offset, 1 if b >= a else -1)
        cells.append(np.vstack(polyline))
    return cells


def nearest_order(cells, tip):
    """Cells in the order a hand takes them: always the nearest end next, walking a cell backwards when that is closer."""
    remaining, ordered = list(cells), []
    while remaining:
        if tip is None:
            index, reverse = 0, False
        else:
            ends = [(min(np.linalg.norm(cell[0] - tip), np.linalg.norm(cell[-1] - tip)), index) for index, cell in enumerate(remaining)]
            index = min(ends)[1]
            reverse = np.linalg.norm(remaining[index][-1] - tip) < np.linalg.norm(remaining[index][0] - tip)
        cell = remaining.pop(index)
        cell = cell[::-1] if reverse else cell
        ordered.append(cell)
        tip = cell[-1]
    return ordered


def joined(cells, radius, step):
    """Consecutive passes a few marker widths apart become one scribble: a person does not lift the marker for the next
    lane or a touch-up nearby. The connecting move paints only what it crosses inside the region."""
    result = []
    for cell in cells:
        if result and np.linalg.norm(cell[0] - result[-1][-1]) <= JOIN * radius:
            result[-1] = np.vstack([result[-1], resample(np.vstack([result[-1][-1], cell[0]]), step)[1:-1], cell])
        else:
            result.append(cell)
    return result


def uncovered(mask, offset, cells, radius):
    """Pixels of the region no marker sample reaches (the renderer touches what lies within radius + ~1.6 px)."""
    free = np.ones(mask.shape, bool)
    if cells:
        samples = np.rint(np.vstack(cells) - offset).astype(int)
        inside = (samples[:, 0] >= 0) & (samples[:, 1] >= 0) & (samples[:, 0] < mask.shape[1]) & (samples[:, 1] < mask.shape[0])
        free[samples[inside, 1], samples[inside, 0]] = False
    if free.all():
        return mask.copy()
    return mask & (ndimage.distance_transform_edt(free) > radius + .5)


def touch_ups(mask, offset, cells, radius, step, axis):
    """Short dabs for corners and slivers the strokes missed: a person goes back for them at the end."""
    dabs = []
    for _ in range(3):
        missed = uncovered(mask, offset, cells + dabs, radius)
        if not missed.any():
            break
        pieces, _ = ndimage.label(missed, np.ones((3, 3)))
        for label, piece in enumerate(ndimage.find_objects(pieces), 1):
            ys, xs = np.nonzero(pieces[piece] == label)
            points = np.c_[xs + piece[1].start, ys + piece[0].start].astype(float) + offset
            center = points.mean(0)
            along = (points - center) @ axis
            if np.ptp(along) <= radius:
                dabs.append(np.repeat(center[None], 2, axis=0))
            else:
                dabs.append(resample(np.vstack([center + along.min() * axis, center + along.max() * axis]), step))
    return dabs


def strokes(region, radius, careful=True):
    """The marker path of one region: edge pass, hatch, touch-ups (each a list of polylines, in drawing order)."""
    mask, offset = region['mask'], region['offset']
    if 'distance' not in region:
        region['distance'] = ndimage.distance_transform_edt(np.pad(mask, 1))[1:-1, 1:-1].astype(np.float32)
    distance, step = region['distance'], max(1.5, radius / 4)
    ys, xs = np.nonzero(mask)
    points = np.c_[xs, ys].astype(float) + offset
    if careful:
        center, axis, across = hatch_axes(points, region.get('tilt'))
    else:
        # No time for care: long rows along the shape (fewest turns), no edge pass, no touch-ups.
        center, axis, across = axes(points)
        if region.get('tilt'):
            axis = rotate(axis, region['tilt'])
            across = np.array([-axis[1], axis[0]])
    region.update(center=center, axis=axis, across=across, edge=None, careful=careful)
    cells = []
    if careful and region.get('edges', True) and distance.max() > EDGE_MIN * radius:
        cells = edge_paths(distance, offset, radius, step)
        if cells:
            region['edge'] = (EDGE_INSET + 1) * radius
            inner = distance > (EDGE_INSET + .75) * radius
            ys, xs = np.nonzero(inner)
            points = np.c_[xs, ys].astype(float) + offset
    if len(points):
        cells += nearest_order(hatch(points, center, axis, across, radius, step, None if careful else QUICK_SPACING),
                               cells[-1][-1] if cells else None)
    if careful:
        cells += nearest_order(touch_ups(mask, offset, cells, radius, step, axis), cells[-1][-1] if cells else None)
    return joined(cells, radius, step) or [np.repeat(center[None], 2, axis=0)]


def plan(regions, scale, size=1.):
    """Every region, however small, gets its own pass of the marker: nothing settles in without a brush.
    A larger picture takes a proportionally broader marker (size), so coloring it is not more work."""
    careful = scale <= CAREFUL
    part_area = {}
    for region in regions:
        part_area[region['part']] = part_area.get(region['part'], 0) + region['area']
    for region in regions:
        # A careful colorist sizes the marker to each shape; in a hurry one broad marker does the whole part.
        area = region['area'] if careful else part_area[region['part']]
        region['radius'] = float(np.clip(math.sqrt(area) / 7, 7, 24 * size) * scale * region.get('brush', 1.))
        region['cells'] = strokes(region, region['radius'], careful)


def shaded_parts(regions, rgb, part_count):
    """Parts whose source differs visibly from flat color get a short shading pass."""
    result = []
    for part in range(part_count):
        mine = [region for region in regions if region['part'] == part]
        if mine and np.average([np.abs(region_pixels(region, rgb) - region['flat']).mean() for region in mine],
                               weights=[region['area'] for region in mine]) > 6:
            result.append(part)
    return result


def nearest_first(regions, tip):
    """Color a part the way its lines were drawn: start with the region nearest the marker (a larger region wins a
    near tie) and keep moving to the closest uncolored one, instead of scanning the part from the top."""
    remaining, ordered, tip = list(regions), [], np.asarray(tip, float)
    while remaining:
        region = min(remaining, key=lambda item: np.linalg.norm(item['cells'][0][0] - tip) - .5 * math.sqrt(item.get('area', 0)))
        remaining = [item for item in remaining if item is not region]
        ordered.append(region)
        tip = region['cells'][-1][-1]
    return ordered


def timeline(regions, shading, part_count, tip, pace, lifts=1., start=0., total=1., fps=30, record=False, size=1.):
    """Lay out every marker pass and shading band in order; returns (segments, parts, bands, end seconds, tip)."""
    tip = np.asarray(tip, float)
    segments, cursor, parts, bands = [], start, [], []
    shade_time = SHADE_SECONDS * min(1., FILL_SPEED * 1.5 / pace)
    lapse = max(1., pace / (FILL_SPEED * size))

    def travel(destination):
        nonlocal cursor
        lift = lift_seconds(np.linalg.norm(destination - tip), fps, lifts, lapse, size)
        segments.append({'kind': 'travel', 'start': cursor / total, 'end': (cursor + lift) / total,
                         'points': [tip.tolist(), destination.tolist()]})
        cursor += lift

    for part in range(part_count):
        part_start = cursor
        for region in nearest_first([region for region in regions if region['part'] == part], tip):
            passes = []
            for cell in region['cells']:
                travel(cell[0])
                weights = weighted_lengths(cell)
                seconds = max(frame_floor(fps, lapse), weights[-1] / pace)
                segments.append({'kind': 'color', 'start': cursor / total, 'end': (cursor + seconds) / total,
                                 'points': cell.tolist(), 'lengths': weights.tolist(), 'radius': region['radius'] + 2.5})
                passes.append((cell, (cursor + seconds * weights / max(1e-6, weights[-1])) / total))
                cursor += seconds
                tip = cell[-1]
            if record:
                region.update(passes=passes, end=cursor / total, window=3 * region['radius'] / pace / total,
                              coat=min(COAT_DELAY, COAT_REACH * region['radius'] / pace) / total)
        if part in shading:
            mine = np.vstack([np.c_[np.nonzero(r['mask'])[::-1]].astype(float) + r['offset'] for r in regions if r['part'] == part])
            center, axis, across = axes(mine)
            along, side = (mine - center) @ axis, (mine - center) @ across
            count = int(np.clip(round(np.ptp(side) / 90), 1, 4))
            edges = np.linspace(side.min(), side.max(), count + 1)
            band = {'part': part, 'center': center, 'axis': axis, 'across': across, 'edges': edges,
                    'along': (along.min(), along.max()), 'times': []}
            for index in range(count):
                points = center + np.linspace(along.min(), along.max(), 24)[:, None] * axis + (edges[index] + edges[index + 1]) / 2 * across
                travel(points[0])
                seconds = shade_time / count
                segments.append({'kind': 'shade', 'start': cursor / total, 'end': (cursor + seconds) / total, 'points': points.tolist(),
                                 'lengths': weighted_lengths(points).tolist(), 'radius': float(np.ptp(edges) / count / 2 + 4)})
                band['times'].append((cursor / total, (cursor + seconds) / total))
                cursor += seconds
                tip = points[-1]
            bands.append(band)
        parts.append([part_start / total, cursor / total])
        if part_start < cursor and part + 1 < part_count and any(r['part'] == part + 1 for r in regions):
            pause = PART_PAUSE * min(1., FILL_SPEED / max(pace, 1e-6))
            segments.append({'kind': 'pause', 'start': cursor / total, 'end': (cursor + pause) / total,
                             'points': [tip.tolist(), tip.tolist()]})
            cursor += pause
    return segments, parts, bands, cursor, tip


def fill_cap(speed, fps):
    return min(FILL_SPEED * FILL_FACTOR, FILL_FRAME_PX * fps) * speed


def requirements(regions, rgb, part_count, tip, speed=1., fps=30, shade=True, size=1.):
    """Seconds for: base marker at human pace with shading; a 1.5x marker at the cap with shading;
    the broadest marker at the cap with short lifts and no shading."""
    shading = shaded_parts(regions, rgb, part_count) if shade else []
    result = {}
    cap = fill_cap(speed, fps)
    for key, scale, pace, shade, lifts in (('required', SCALES[0], FILL_SPEED * speed, shading, 1.), ('moderate', SCALES[1], cap, shading, 1.),
                                           ('minimum', SCALES[-1], cap, [], .5)):
        plan(regions, scale, size)
        result[key] = timeline(regions, shade, part_count, tip, pace, lifts, fps=fps, size=size)[3]
    return result


def schedule(regions, rgb, part_count, tip, budget, start, total, speed=1., fps=30, shade=True, size=1.):
    """Pick marker size, pace and lift length so the fill fits the budget: bigger marker first, then pace
    up to the cap; shading is dropped before the cap is exceeded. Returns segments, per-part [start, end]
    fractions, shading bands, end fraction, pen tip and counts."""
    shading = shaded_parts(regions, rgb, part_count) if shade else []
    base, cap = FILL_SPEED * speed, fill_cap(speed, fps)
    seconds = lambda pace, lifts=1., shade=None: timeline(regions, shading if shade is None else shade, part_count, tip, pace, lifts, fps=fps, size=size)[3]
    for scale in SCALES:
        plan(regions, scale, size)
        if seconds(cap) <= budget:
            break
    if seconds(cap) > budget:
        shading = []
    lifts = next((value for value in (1., .7, .5) if seconds(cap, value) <= budget), .5)
    low, high = base / 1.6, cap * 8
    if seconds(low, lifts) <= budget:
        high = low
    for _ in range(40):
        if high - low < 1:
            break
        middle = (low + high) / 2
        low, high = (middle, high) if seconds(middle, lifts) > budget else (low, middle)
    segments, parts, bands, end, tip = timeline(regions, shading, part_count, tip, high, lifts, start, total, fps, record=True, size=size)
    counts = {'fill_regions': len(regions), 'fill_passes': sum(len(r['cells']) for r in regions),
              'marker_radius_scale': scale, 'fill_speed_px_s': round(high, 1), 'fill_over_cap': bool(high > cap * 1.001),
              'shaded_parts': len(shading)}
    return segments, parts, bands, end / total, tip, counts


def bristles(values, seed):
    """Smooth 1-D value noise in [0, 1]: the streaks a marker's felt leaves along its stroke."""
    rng = np.random.default_rng(seed)
    low = math.floor(float(values.min())) - 1
    lattice = rng.random(int(math.ceil(float(values.max()) - low)) + 3)
    cell = np.floor(values - low).astype(int)
    fraction = values - low - cell
    fraction = fraction * fraction * (3 - 2 * fraction)
    return lattice[cell] * (1 - fraction) + lattice[cell + 1] * fraction


def texture(region, box_shape, seed):
    """Alpha of a single wet coat over the region crop: felt streaks running with the strokes (parallel to the edge in
    the edge band), varying slowly along them."""
    top, left = region['offset'][1], region['offset'][0]
    ys, xs = np.mgrid[top:top + box_shape[0], left:left + box_shape[1]].astype(np.float32)
    u = (xs - region['center'][0]) * region['across'][0] + (ys - region['center'][1]) * region['across'][1]
    v = (xs - region['center'][0]) * region['axis'][0] + (ys - region['center'][1]) * region['axis'][1]
    if region.get('edge'):
        u = np.where(region['distance'] <= region['edge'], region['distance'] * 1.7, u)
    # Ink pools unevenly: a slow blotch over the streaks keeps an edge band from reading as contour rings.
    blotch = ndimage.gaussian_filter(np.random.default_rng(seed + 2).random(box_shape).astype(np.float32), max(2., .6 * region['radius']))
    blotch = (blotch - blotch.min()) / max(1e-6, float(np.ptp(blotch)))
    streak = .5 * bristles(u / STREAK, seed) + .28 * bristles(u / (3.1 * STREAK) + v / (4 * region['radius']), seed + 1) + .22 * blotch
    return (WET[0] + (WET[1] - WET[0]) * streak).astype(np.float32)


def ramps(total, fps):
    """[front, coat] ramps of the paint layer in fractions of a drawing event lasting `total` seconds."""
    return np.array([FRONT_FRAMES / fps / total, COAT_RAMP / total], np.float32)


def render(shape, regions, bands, owners):
    """Marker reveal maps: first touch time and its coverage (streaky wet coat, ragged edge), the time the coat reads
    solid (second overlapping stroke, or a moment later), flat colors, and per-pixel shading time (flat -> source)."""
    first = np.full(shape, np.inf, np.float32)
    cover = np.zeros(shape, np.float32)
    full = np.full(shape, np.inf, np.float32)
    flat = np.zeros(shape + (3,), np.float32)
    rng = np.random.default_rng(7)
    grain = (.8 + .2 * rng.random(shape)).astype(np.float32)
    ragged = ndimage.gaussian_filter(rng.random(shape).astype(np.float32), 1.2)
    ragged = (ragged - ragged.min()) / max(1e-6, float(np.ptp(ragged)))
    for index, region in enumerate(regions):
        (left, top), (height, width) = region['offset'], region['mask'].shape
        mask, radius = region['mask'], region['radius']
        edge = max(4., region.get('soft', 0.) * radius)
        box = (slice(top, top + height), slice(left, left + width))
        flat[box][mask] = region['flat']
        wet = texture(region, (height, width), 11 + 2 * index) if region.get('streaks', True) else grain[box]
        first_local, cover_local, grain_local = first[box], cover[box], ragged[box]
        second_local = np.full((height, width), np.inf, np.float32)
        rough = .3 if region.get('careful', True) else 0.   # a quick broad pass keeps its full, even edge
        for cell, times in region['passes']:
            for (x, y), when in zip(cell - region['offset'], times):
                x0, x1 = int(max(0, x - radius - 3)), int(min(width, x + radius + 4))
                y0, y1 = int(max(0, y - radius - 3)), int(min(height, y + radius + 4))
                if x1 <= x0 or y1 <= y0:
                    continue
                ys, xs = np.ogrid[y0:y1, x0:x1]
                window = (slice(y0, y1), slice(x0, x1))
                # The felt edge is ragged: coverage only ever shrinks inside the nominal disc.
                coverage = np.clip((radius + 2 - np.hypot(xs - x, ys - y)) / edge - rough * grain_local[window], 0, 1) * mask[window]
                seen = np.isfinite(first_local[window])
                touched = (coverage > .1) & ~seen
                first_local[window][touched] = when
                passing = (coverage > 0) & (when - first_local[window] <= region['window'])
                cover_local[window][passing] = np.maximum(cover_local[window], coverage * wet[window])[passing]
                again = (coverage > .5) & seen & (when - first_local[window] > region['window']) & ~np.isfinite(second_local[window])
                second_local[window][again] = when
        missing = mask & ~np.isfinite(first_local)
        if missing.any():
            _, nearest = ndimage.distance_transform_edt(~(np.isfinite(first_local) & mask), return_indices=True)
            first_local[missing] = first_local[nearest[0], nearest[1]][missing]
            cover_local[missing] = wet[missing]
        settled = np.minimum(second_local, first_local + region.get('coat', 0.))
        full[box][mask] = np.minimum(np.maximum(settled, first_local), region['end'])[mask]
    shade = full.copy()
    for band in bands:
        ys, xs = np.nonzero(owners == band['part'])
        relative = np.c_[xs, ys].astype(float) - band['center']
        side, along = relative @ band['across'], relative @ band['axis']
        index = np.clip(np.searchsorted(band['edges'], side) - 1, 0, len(band['times']) - 1)
        low, high = band['along']
        fraction = np.clip((along - low) / max(1., high - low), 0, 1) * .8
        starts, ends = np.array(band['times']).T
        shade[ys, xs] = starts[index] + fraction * (ends[index] - starts[index])
    return first, cover, full, flat, shade
