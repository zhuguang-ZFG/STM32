"""Element motion: easing curves (incl. springs), motion presets and their transform of a finished element's layer.

A motion is {type, start, end, strength, ...} in film seconds on an event. Presets fall in four families:
- emphasis (plays once when the narration comes back to the element): pop, pulse, wiggle, shake, nod, glow, jelly,
  tada, bounce, heartbeat, rubber_band, swing;
- idle (loops from its start until the page ends): float, breathe, sway, boil (hand-drawn line boil);
- exit (before the page turns): fade_out, shrink_out, pop_out, fly_out;
- puppet (moves one semantic part of a drawn picture about an automatic pivot): part_nod, part_tilt, part_wave,
  part_bob.
Transforms compose: offsets add, scales and opacity multiply, rotations add. Pure functions; the renderer caches."""
import math
import numpy as np
from PIL import Image, ImageFilter

EMPHASIS = {'pop': .6, 'pulse': .9, 'wiggle': .7, 'shake': .45, 'nod': .6, 'glow': 1.2, 'jelly': .8, 'tada': 1., 'bounce': .8,
            'heartbeat': 1., 'rubber_band': .8, 'swing': 1.}
IDLE = {'float': 3., 'breathe': 3.2, 'sway': 3.6, 'boil': .375}
EXIT = {'fade_out': .4, 'shrink_out': .45, 'pop_out': .45, 'fly_out': .5}
PUPPET = {'part_nod': .8, 'part_tilt': 1., 'part_wave': 1.2, 'part_bob': .8}
TYPES = {**EMPHASIS, **IDLE, **EXIT, **PUPPET}  # default seconds (idle: one loop period)
GLOW = (255, 214, 92)
BOIL_FPS, BOIL_VARIANTS = 8, 3


# ---------------------------------------------------------------- easing

def spring(t, stiffness=170., damping=12., mass=1.):
    """Damped spring from 0 to 1 at unit time scale (t in 0..1 spans the settle time); overshoots when underdamped."""
    t = float(np.clip(t, 0, 1)) * 1.6
    omega = math.sqrt(stiffness / mass)
    zeta = damping / (2 * math.sqrt(stiffness * mass))
    if zeta < 1:
        wd = omega * math.sqrt(1 - zeta * zeta)
        return 1 - math.exp(-zeta * omega * t) * (math.cos(wd * t) + zeta * omega / wd * math.sin(wd * t))
    return 1 - math.exp(-omega * t) * (1 + omega * t)


def ease(name, t):
    """Named easing on t in 0..1: linear, in/out/inout + quad|cubic|quart|expo|sine|back|elastic|bounce, spring, minjerk."""
    t = float(np.clip(t, 0, 1))
    if name in (None, 'linear'):
        return t
    if name == 'minjerk' or name == 'inout':
        return 10 * t ** 3 - 15 * t ** 4 + 6 * t ** 5
    if name == 'spring':
        return spring(t)
    if name.startswith('inout_'):
        base = name[6:]
        return .5 * ease('in_' + base, 2 * t) if t < .5 else .5 + .5 * ease('out_' + base, 2 * t - 1)
    if name.startswith('out_'):
        return 1 - ease('in_' + name[4:], 1 - t)
    kind = name[3:] if name.startswith('in_') else name
    if kind == 'quad':
        return t * t
    if kind == 'cubic':
        return t ** 3
    if kind == 'quart':
        return t ** 4
    if kind == 'expo':
        return 0. if t == 0 else 2 ** (10 * t - 10)
    if kind == 'sine':
        return 1 - math.cos(t * math.pi / 2)
    if kind == 'back':
        c = 1.70158
        return (c + 1) * t ** 3 - c * t * t
    if kind == 'elastic':
        return 0. if t in (0, 1) else -(2 ** (10 * t - 10)) * math.sin((t * 10 - 10.75) * 2 * math.pi / 3)
    if kind == 'bounce':
        return 1 - bounce_out(1 - t)
    raise ValueError(f'Unknown easing: {name}')


def bounce_out(t):
    n, d = 7.5625, 2.75
    if t < 1 / d:
        return n * t * t
    if t < 2 / d:
        t -= 1.5 / d
        return n * t * t + .75
    if t < 2.5 / d:
        t -= 2.25 / d
        return n * t * t + .9375
    t -= 2.625 / d
    return n * t * t + .984375


EASINGS = ('linear', 'minjerk', 'spring') + tuple(f'{direction}_{kind}' for direction in ('in', 'out', 'inout')
                                                     for kind in ('quad', 'cubic', 'quart', 'expo', 'sine', 'back', 'elastic', 'bounce'))


# ---------------------------------------------------------------- camera moves

# Named moves for pages[].camera[].move: the timing and easing a camera operator gives that move (explicit fields win).
# impact: a decaying shake on arrival (screen px); hop: share by which the zoom dips mid-move on a long trip.
CAMERA_MOVES = {
    'cut': {'seconds': 0.},
    'push_in': {'seconds': 1., 'ease': 'inout_cubic'},
    'pull_out': {'seconds': 1.4, 'ease': 'out_cubic'},
    'pan': {'seconds': .75, 'ease': 'inout_sine'},
    'drift': {'seconds': 3., 'ease': 'inout_sine'},
    'hop': {'seconds': 1.2, 'ease': 'inout_cubic', 'hop': .3},
    'whip': {'seconds': .28, 'ease': 'inout_quart'},
    'snap': {'seconds': .3, 'ease': 'out_expo'},
    'slam': {'seconds': .18, 'ease': 'out_back', 'impact': 10.},
    'dolly_zoom': {'seconds': 2.4, 'ease': 'inout_sine'},  # needs a subject: it keeps its size while the page zooms past it
}
IMPACT_DECAY = .14   # seconds for an arrival shake to fall to 1/e


def camera_key(key):
    """A camera key with its named move's defaults filled in."""
    return {**CAMERA_MOVES.get(key.get('move'), {}), **{name: value for name, value in key.items() if name != 'move'}}


def impact_shake(amplitude, t):
    """(dx, dy, degrees) of a camera arrival shake t seconds after arrival: low-frequency, quickly decaying."""
    if amplitude <= 0 or not 0 <= t < 6 * IMPACT_DECAY:
        return 0., 0., 0.
    size = amplitude * math.exp(-t / IMPACT_DECAY)
    tau = 2 * math.pi * t
    return (size * (.65 * math.sin(11 * tau + .4) + .35 * math.sin(17 * tau + 2.1)),
            size * (.65 * math.sin(13 * tau + 1.3) + .35 * math.sin(19 * tau + .2)), .035 * size * math.sin(9 * tau + .9))


def hump(t):
    """0 -> 1 -> 0 over t in 0..1, smooth at both ends."""
    return math.sin(math.pi * float(np.clip(t, 0, 1)))


# ---------------------------------------------------------------- presets

def identity():
    return {'dx': 0., 'dy': 0., 'sx': 1., 'sy': 1., 'rotate': 0., 'opacity': 1., 'glow': 0., 'anchor': (.5, .5)}


def state(motion, time):
    """Transform contribution of one motion at film time `time` (None when inactive)."""
    kind, strength = motion['type'], float(motion.get('strength', 1.))
    start, end = motion['start'], motion['end']
    out = identity()
    if kind in IDLE:
        if time < start:
            return None
        period = max(.2, end - start)
        phase = ((time - start) / period) % 1.
        ramp = min(1., (time - start) / .6)  # idle loops fade in so they never jump
        if kind == 'float':
            out['dy'] = -6 * strength * ramp * math.sin(2 * math.pi * phase)
        elif kind == 'breathe':
            out['sx'] = out['sy'] = 1 + .012 * strength * ramp * math.sin(2 * math.pi * phase)
            out['anchor'] = (.5, 1.)
        elif kind == 'sway':
            out['rotate'] = 1.6 * strength * ramp * math.sin(2 * math.pi * phase)
            out['anchor'] = (.5, 1.)
        elif kind == 'boil':
            out['boil'] = int((time - start) * BOIL_FPS) % BOIL_VARIANTS
        return out
    if not start <= time < end and not (kind in EXIT and time >= end):
        return None
    f = float(np.clip((time - start) / max(1e-6, end - start), 0, 1))
    if kind in EXIT:
        k = ease('in_cubic', f)
        if kind == 'fade_out':
            out['opacity'] = 1 - k
        elif kind == 'shrink_out':
            out['sx'] = out['sy'] = 1 - .9 * k
            out['opacity'] = 1 - k
        elif kind == 'pop_out':
            grow = 1 + .15 * hump(min(1, f * 2.5)) if f < .4 else 1 - (f - .4) / .6
            out['sx'] = out['sy'] = max(.01, grow)
            out['opacity'] = 1 - ease('in_quad', max(0, (f - .4) / .6))
        elif kind == 'fly_out':
            out['dy'] = -400 * strength * k
            out['opacity'] = 1 - k
        return out
    if kind == 'pop':
        out['sx'] = out['sy'] = 1 + .12 * strength * hump(f)
    elif kind == 'pulse':
        out['sx'] = out['sy'] = 1 + .06 * strength * abs(math.sin(2 * math.pi * f))
    elif kind == 'wiggle':
        out['rotate'] = 5 * strength * math.sin(6 * math.pi * f) * (1 - f)
    elif kind == 'shake':
        out['dx'] = 8 * strength * math.sin(10 * math.pi * f) * (1 - f)
    elif kind == 'nod':
        out['dy'] = -10 * strength * hump(f)
    elif kind == 'glow':
        out['glow'] = .75 * strength * hump(f)
    elif kind == 'jelly':  # squash and stretch about the base, volume kept
        wave = math.sin(5 * math.pi * f) * (1 - f)
        out['sx'], out['sy'] = 1 + .14 * strength * wave, 1 - .14 * strength * wave
        out['anchor'] = (.5, 1.)
    elif kind == 'tada':
        out['sx'] = out['sy'] = 1 + .1 * strength * hump(min(1, f * 1.4))
        out['rotate'] = 4 * strength * math.sin(8 * math.pi * f) * (f > .1) * (1 - f)
    elif kind == 'bounce':  # hop and land with a squash
        height = max(0., math.sin(math.pi * min(1, f / .6)))
        out['dy'] = -28 * strength * height
        land = max(0., math.sin(math.pi * (f - .6) / .4)) if f > .6 else 0.
        out['sx'], out['sy'] = 1 + .1 * strength * land, 1 - .1 * strength * land
        out['anchor'] = (.5, 1.)
    elif kind == 'heartbeat':
        beat = max(hump(min(1, f / .25)), .7 * hump(float(np.clip((f - .3) / .25, 0, 1))))
        out['sx'] = out['sy'] = 1 + .09 * strength * beat
    elif kind == 'rubber_band':
        wave = math.sin(4 * math.pi * f) * (1 - f)
        out['sx'], out['sy'] = 1 + .22 * strength * wave, 1 - .16 * strength * wave
    elif kind == 'swing':
        out['rotate'] = 12 * strength * math.sin(4 * math.pi * f) * (1 - f)
        out['anchor'] = (.5, 0.)
    return out


def combine(states):
    total = identity()
    for item in states:
        total['dx'] += item['dx']
        total['dy'] += item['dy']
        total['sx'] *= item['sx']
        total['sy'] *= item['sy']
        total['rotate'] += item['rotate']
        total['opacity'] *= item['opacity']
        total['glow'] = max(total['glow'], item['glow'])
        if item['anchor'] != (.5, .5):
            total['anchor'] = item['anchor']
        if 'boil' in item:
            total['boil'] = item['boil']
    return total


def is_identity(total):
    return (abs(total['dx']) < .05 and abs(total['dy']) < .05 and abs(total['sx'] - 1) < 1e-3 and abs(total['sy'] - 1) < 1e-3
            and abs(total['rotate']) < .02 and total['opacity'] > .999 and total['glow'] < 1e-3 and 'boil' not in total)


def apply(layer, total, scale=1.):
    """Transformed RGBA layer and its paste offset (relative to the layer's own top-left), board scale aware."""
    width, height = layer.size
    pad = int(math.ceil(max(width, height) * (max(total['sx'], total['sy'], 1) - 1) + abs(total['rotate']) / 90 * max(width, height)
                        + 40 * scale * total['glow'] + 2))
    canvas = Image.new('RGBA', (width + 2 * pad, height + 2 * pad))
    if total['glow'] > 0:
        alpha = Image.new('L', canvas.size)
        alpha.paste(layer.getchannel('A'), (pad, pad))
        radius = max(4., .03 * max(width, height))
        alpha = alpha.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(radius)).point(lambda v: round(v * total['glow']))
        canvas.paste(Image.new('RGBA', canvas.size, GLOW + (255,)), (0, 0), alpha)
    canvas.alpha_composite(layer, (pad, pad))
    ax, ay = pad + total['anchor'][0] * width, pad + total['anchor'][1] * height
    angle = math.radians(total['rotate'])
    cos, sin = math.cos(angle), math.sin(angle)
    sx, sy = max(1e-3, total['sx']), max(1e-3, total['sy'])
    # Inverse map: output (u, v) -> source; rotate about the anchor, then scale about it, then move by (dx, dy).
    dx, dy = total['dx'] * scale, total['dy'] * scale
    a, b = cos / sx, sin / sx
    d, e = -sin / sy, cos / sy
    c = ax - a * (ax + dx) - b * (ay + dy)
    f = ay - d * (ax + dx) - e * (ay + dy)
    moved = canvas.transform(canvas.size, Image.Transform.AFFINE, (a, b, c, d, e, f), Image.Resampling.BICUBIC)
    if total['opacity'] < .999:
        moved.putalpha(moved.getchannel('A').point(lambda v: round(v * max(0., total['opacity']))))
    return moved, (-pad, -pad)


# ---------------------------------------------------------------- line boil

def boil_variants(layer, amplitude=1.1, seed=7):
    """BOIL_VARIANTS copies of a finished drawing with a different smooth sub-pixel wobble each: cycled at 8 fps they
    give the 'alive' boil of hand-drawn animation without changing what is drawn."""
    from scipy import ndimage
    pixels = np.asarray(layer, np.float32)
    height, width = pixels.shape[:2]
    rng = np.random.default_rng(seed)
    ys, xs = np.mgrid[:height, :width].astype(np.float32)
    variants = []
    for _ in range(BOIL_VARIANTS):
        fields = [ndimage.gaussian_filter(rng.standard_normal((height, width)).astype(np.float32), 9) for _ in range(2)]
        fields = [field / max(1e-6, np.abs(field).max()) * amplitude for field in fields]
        warped = np.stack([ndimage.map_coordinates(pixels[..., channel], [ys + fields[1], xs + fields[0]], order=1, mode='nearest')
                           for channel in range(4)], axis=-1)
        variants.append(Image.fromarray(np.clip(np.rint(warped), 0, 255).astype(np.uint8)))
    return variants


# ---------------------------------------------------------------- puppet: move one semantic part

def part_rig(final, owners, part):
    """Split a finished picture into (rest, part layer, pivot): the rest has the part removed and the hole behind it
    filled from the neighbouring paint (so a small turn shows no paper gap); the pivot is where the part meets the
    rest of the figure (neck under a head, shoulder of an arm)."""
    from scipy import ndimage
    pixels = np.asarray(final)
    mask = owners == part
    if not mask.any():
        raise ValueError('Puppet part has no pixels')
    others = (owners >= 0) & ~mask
    touching = ndimage.binary_dilation(mask, iterations=2) & others
    if touching.any():
        ys, xs = np.nonzero(touching)
    else:
        ys, xs = np.nonzero(mask)
        ys = ys[ys >= np.percentile(ys, 90)]
        xs = np.nonzero(mask)[1][np.nonzero(mask)[0] >= np.percentile(np.nonzero(mask)[0], 90)]
    pivot = (float(xs.mean()), float(ys.mean()))
    part_layer = pixels.copy()
    part_layer[~mask, 3] = 0
    rest = pixels.copy()
    distance, nearest = ndimage.distance_transform_edt(~others, return_indices=True)
    fill = mask & (distance <= 10)
    rest[fill] = pixels[nearest[0][fill], nearest[1][fill]]
    rest[mask & ~fill, 3] = 0
    return Image.fromarray(rest), Image.fromarray(part_layer), pivot


def puppet_state(motion, time):
    """Rotation (degrees) and lift (px) of a puppet part at this time, or None."""
    start, end, strength = motion['start'], motion['end'], float(motion.get('strength', 1.))
    if not start <= time < end:
        return None
    f = (time - start) / max(1e-6, end - start)
    kind = motion['type']
    if kind == 'part_nod':
        return 6 * strength * math.sin(4 * math.pi * f) * (1 - f) * (1 if motion.get('side', 'right') == 'right' else -1), 0.
    if kind == 'part_tilt':
        return 8 * strength * hump(f) * (1 if motion.get('side', 'right') == 'right' else -1), 0.
    if kind == 'part_wave':
        return 14 * strength * math.sin(6 * math.pi * f) * hump(f), 0.
    if kind == 'part_bob':
        return 0., -10 * strength * abs(math.sin(2 * math.pi * f)) * (1 - f)
    return None


def puppet_frame(rig, angle, lift, scale=1.):
    rest, part, (px, py) = rig
    if abs(angle) < .05 and abs(lift) < .05:
        frame = rest.copy()
        frame.alpha_composite(part)
        return frame
    turned = part.rotate(angle, Image.Resampling.BICUBIC, center=(px, py), translate=(0, lift * scale))
    frame = rest.copy()
    frame.alpha_composite(turned)
    return frame
