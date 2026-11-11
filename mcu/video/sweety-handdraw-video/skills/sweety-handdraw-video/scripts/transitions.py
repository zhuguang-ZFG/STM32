"""Page transitions beyond camera moves, all drawn procedurally (no third-party art): wipes, zooms and pushes; paper
(page turns in four directions, a sheet laid over, a tear, a card flip, a cube, tiles, shards); ink and paint (a
marker sweep, an ink bloom, an iris or ink blot, a dry-brush reveal); erasers (a felt whiteboard eraser, a pencil
rubber with crumbs); and accents (a whip pan, a zoom through, a flash).

Every effect is f(renderer, old frame, new frame, fraction 0..1, window) -> frame."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from motion_profile import distance_fraction

GHOST = .12          # share of the old ink left behind right after the first pass, cleared by the end


def wipe(renderer, old, new, fraction, window):
    """The new page slides in under a soft edge moving in the given direction."""
    width, height = old.size
    moving = float(distance_fraction(fraction, 'minjerk'))
    direction = window.get('direction', 'left')
    span = width if direction in ('left', 'right') else height
    feather = max(8, round(.04 * span))
    edge = moving * (span + feather) - feather
    axis = np.arange(span, dtype=np.float32)
    if direction in ('left', 'up'):
        axis = span - 1 - axis
    ramp = np.clip((edge - axis) / feather + .5, 0, 1)
    mask = np.broadcast_to(ramp[None, :] if direction in ('left', 'right') else ramp[:, None], (height, width))
    return Image.composite(new, old, Image.fromarray(np.rint(mask * 255).astype(np.uint8)))


def zoom(renderer, old, new, fraction, window):
    """Push into the old page while it fades, and settle the new page from a slight pull-back."""
    width, height = old.size
    moving = float(distance_fraction(fraction, 'minjerk'))

    def scaled(image, factor):
        size = (round(width * factor), round(height * factor))
        resized = image.resize(size, Image.Resampling.BICUBIC)
        if factor >= 1:
            left, top = (size[0] - width) // 2, (size[1] - height) // 2
            return resized.crop((left, top, left + width, top + height))
        canvas = Image.new('RGBA', (width, height), renderer.paper)
        canvas.alpha_composite(resized.convert('RGBA'), ((width - size[0]) // 2, (height - size[1]) // 2))
        return canvas
    return Image.blend(scaled(old, 1 + .18 * moving), scaled(new, .94 + .06 * moving), moving)


def eraser_sprite(width, height):
    """A felt whiteboard eraser seen from above at a slight angle, with a soft shadow; cached per size."""
    pad = max(6, round(height * .25))
    image = Image.new('RGBA', (width + 2 * pad, height + 2 * pad))
    shadow = Image.new('L', image.size)
    ImageDraw.Draw(shadow).rounded_rectangle((pad + 6, pad + 10, pad + width + 6, pad + height + 10), radius=height // 4, fill=90)
    image.putalpha(shadow.filter(ImageFilter.GaussianBlur(pad / 2)))
    image = Image.composite(Image.new('RGBA', image.size, (30, 26, 22, 255)), Image.new('RGBA', image.size), image.getchannel('A'))
    draw = ImageDraw.Draw(image)
    felt = round(height * .32)
    draw.rounded_rectangle((pad, pad + height - felt, pad + width, pad + height), radius=height // 5, fill=(70, 72, 78, 255))
    draw.rounded_rectangle((pad, pad, pad + width, pad + height - felt + 4), radius=height // 4, fill=(52, 108, 168, 255))
    draw.rounded_rectangle((pad + width * .08, pad + height * .14, pad + width * .92, pad + height * .3), radius=height // 8, fill=(98, 152, 206, 255))
    return image, pad


def erase_rows(width, height):
    """Sweeps across the screen: one more on a tall phone screen."""
    return 5 if height > width else 4


def erase_times(width, height, rows=None):
    """Per-pixel fraction of the sweep at which the eraser first covers it: boustrophedon rows from the top."""
    rows = rows or erase_rows(width, height)
    small = (max(1, width // 8), max(1, height // 8))
    xs, ys = np.meshgrid((np.arange(small[0]) + .5) / small[0], (np.arange(small[1]) + .5) / small[1])
    row = np.minimum((ys * rows).astype(int), rows - 1)
    along = np.where(row % 2 == 0, xs, 1 - xs)
    times = (row + along) / rows
    image = Image.fromarray(times.astype(np.float32)).resize((width, height), Image.Resampling.BILINEAR)
    return np.asarray(image)


def erase(renderer, old, new, fraction, window):
    """The eraser sweeps the old page in rows from the top; erased ink leaves a faint ghost that the following rows
    and the end of the sweep clear. After the page boundary the new (still blank) page shows. style "felt" (a
    whiteboard eraser, default) or "rubber" (a small pencil eraser scrubbing in tighter rows, leaving crumbs that are
    brushed off at the end)."""
    width, height = old.size
    rubber = window.get('style') == 'rubber'
    cache = renderer.__dict__.setdefault('erase_cache', {})
    rows = erase_rows(width, height) + (3 if rubber else 0)
    if (width, height, rubber) not in cache:
        band = height / rows
        sprite = rubber_sprite(round(band * 1.5), round(band * .7)) if rubber else eraser_sprite(round(band * .75 * 2.2), round(band * .75))
        cache[(width, height, rubber)] = (erase_times(width, height, rows), sprite)
    times, (sprite, pad) = cache[(width, height, rubber)]
    sweep = min(1., fraction / .8)  # the old page's share of the window; the rest shows the blank new page
    if sweep >= 1:
        return new
    erased = np.clip((sweep - times) / .04, 0, 1)
    ghost = GHOST * np.clip(1 - (sweep - times) / .35, 0, 1) * (sweep < .999)
    keep = np.clip(1 - erased + ghost * erased, 0, 1)
    paper = np.array(renderer.paper[:3], np.float32)
    pixels = np.asarray(old.convert('RGB'), np.float32)
    mixed = paper + (pixels - paper) * keep[..., None]
    frame = Image.fromarray(np.rint(mixed).astype(np.uint8)).convert('RGBA')
    row = min(int(sweep * rows), rows - 1)
    along = sweep * rows - row
    x = (along if row % 2 == 0 else 1 - along) * width
    y = (row + .5) / rows * height
    wobble = 4 * math.sin(sweep * 40)
    if rubber:
        # A pencil eraser scrubs: quick short strokes back and forth along its row; crumbs fall where it has been.
        x += .35 * sprite.width * math.sin(sweep * rows * 26)
        wobble = 3 * math.sin(sweep * rows * 31)
        draw_crumbs(frame, sweep, rows, width, height, fraction)
    frame.alpha_composite(sprite, (round(x - sprite.width / 2), round(y - sprite.height / 2 + wobble)))
    return frame


def draw_crumbs(frame, sweep, rows, width, height, fraction, count=48):
    """Rolled eraser crumbs piled where the rubber turns at the end of each scrubbed row (seeded, so they stay put),
    brushed off the page over the last fifth."""
    rng = np.random.default_rng(61)
    born = np.sort(rng.uniform(0, 1, count))
    jitter = rng.normal(0, .18, (count, 2))
    sizes = rng.uniform(2.2, 5.5, count) * max(1., height / 1920 * 1.6)
    angles = rng.uniform(0, math.pi, count)
    away = float(np.clip((fraction - .8) / .2, 0, 1))
    if away >= 1:
        return
    draw = ImageDraw.Draw(frame)
    band = height / rows
    for when, (jx, jy), size, angle in zip(born, jitter, sizes, angles):
        if when > sweep:
            break
        row = min(int(when * rows), rows - 1)
        along = when * rows - row
        if along < .85:
            continue  # crumbs pile up where the rubber turns at the end of a row
        along = .97 - .3 * abs(jx)
        x = (along if row % 2 == 0 else 1 - along) * width + jx * band + away * width * 1.2
        y = (row + .5 + jy) / rows * height + away * band * .6
        dx, dy = size * math.cos(angle), size * .45 * math.sin(angle)
        draw.line((x - dx, y - dy, x + dx, y + dy), fill=(188, 128, 134, round(230 * (1 - away))), width=max(2, round(size * .7)))


# ---------------------------------------------------------------- v2.0 transitions

def arrays(old, new):
    return np.asarray(old.convert('RGB'), np.float32), np.asarray(new.convert('RGB'), np.float32)


def image(pixels):
    return Image.fromarray(np.clip(np.rint(pixels), 0, 255).astype(np.uint8)).convert('RGBA')


def smooth(fraction):
    return float(distance_fraction(float(np.clip(fraction, 0, 1)), 'minjerk'))


def slide_over(renderer, old, new, fraction, window):
    """The next sheet is laid on top: it slides in from the side with a soft drop shadow and settles straight."""
    width, height = old.size
    f = smooth(fraction)
    direction = window.get('direction', 'left')
    sign = -1 if direction in ('left', 'up') else 1
    frame = old.copy().convert('RGBA')
    dim = Image.new('RGBA', frame.size, (0, 0, 0, round(40 * f)))
    frame.alpha_composite(dim)
    sheet = new.rotate(-3 * (1 - f) * sign, Image.Resampling.BICUBIC, expand=False, fillcolor=renderer.paper)
    offset = (round(-sign * (1 - f) * width * 1.05), 0) if direction in ('left', 'right') else (0, round(-sign * (1 - f) * height * 1.05))
    shadow = Image.new('L', (width + 80, height + 80), 0)
    ImageDraw.Draw(shadow).rectangle((40, 40, width + 40, height + 40), fill=110)
    shadow = shadow.filter(ImageFilter.GaussianBlur(22))
    tint = Image.new('RGBA', shadow.size, (20, 18, 16, 255))
    tint.putalpha(shadow)
    frame.alpha_composite(tint, (offset[0] - 40 + 14, offset[1] - 40 + 18))
    frame.alpha_composite(sheet.convert('RGBA'), offset)
    return frame


def rough_field(width, height, scale, seed):
    """Smooth noise in about -1..1 for ragged edges and ink blooms (cached per size)."""
    from scipy import ndimage
    rng = np.random.default_rng(seed)
    small = rng.standard_normal((max(2, height // 8), max(2, width // 8))).astype(np.float32)
    field = ndimage.gaussian_filter(small, scale / 8)
    field /= max(1e-6, np.abs(field).max())
    return np.asarray(Image.fromarray(field.astype(np.float32)).resize((width, height), Image.Resampling.BILINEAR))


def marker_wipe(renderer, old, new, fraction, window):
    """A broad marker sweeps a band of colour across the screen on a diagonal, then sweeps on to reveal the next page
    behind its ragged edge."""
    a, b = arrays(old, new)
    height, width = a.shape[:2]
    cache = renderer.__dict__.setdefault('wipe_cache', {})
    if (width, height) not in cache:
        cache[(width, height)] = rough_field(width, height, 30, 11) * .035 * width
    jitter = cache[(width, height)]
    color = np.array(Image.new('RGB', (1, 1), window.get('color', '#F2C14E')).getpixel((0, 0)), np.float32)
    ys, xs = np.mgrid[:height, :width].astype(np.float32)
    along = (xs + .35 * ys) / (width + .35 * height) * (width + .35 * height) + jitter
    span = width + .35 * height
    lead = smooth(min(1, fraction / .55)) * (span * 1.15) - .05 * span      # colour arrives
    tail = smooth(max(0, (fraction - .45) / .55)) * (span * 1.15) - .05 * span  # colour leaves, next page shows
    covered = along < lead
    revealed = along < tail
    out = np.where(revealed[..., None], b, np.where(covered[..., None], color, a))
    streak = (np.sin(ys / 9.) * .04 + 1)[..., None]  # faint marker streaks along the sweep
    band = covered & ~revealed
    out[band] = out[band] * streak[band]
    return image(out)


def ink_bleed(renderer, old, new, fraction, window):
    """Ink blooms from a point with soft organic edges and covers the page; the next page then opens inside the ink
    from the same point, so the cut happens under a wash of ink."""
    a, b = arrays(old, new)
    height, width = a.shape[:2]
    cache = renderer.__dict__.setdefault('bleed_cache', {})
    if (width, height) not in cache:
        cache[(width, height)] = rough_field(width, height, 90, 23) * .05 + rough_field(width, height, 20, 5) * .015
    noise = cache[(width, height)]
    cx, cy = window.get('target') or (width / 2, height * .45)
    ys, xs = np.mgrid[:height, :width].astype(np.float32)
    far = max(math.hypot(cx, cy), math.hypot(width - cx, cy), math.hypot(cx, height - cy), math.hypot(width - cx, height - cy))
    distance = np.hypot(xs - cx, ys - cy) / far + noise
    ink_radius = smooth(min(1, fraction / .6)) * 1.12
    open_radius = smooth(max(0, (fraction - .45) / .55)) * 1.12
    ink = np.array(Image.new('RGB', (1, 1), window.get('color', '#1E2733')).getpixel((0, 0)), np.float32)
    inked = np.clip((ink_radius - distance) / .01, 0, 1)[..., None]
    opened = np.clip((open_radius - distance) / .01, 0, 1)[..., None]
    return image((a * (1 - inked) + ink * inked) * (1 - opened) + b * opened)


def iris(renderer, old, new, fraction, window):
    """A circle closes on a point of the old page and opens on the new one (an old-film iris, in ink)."""
    a, b = arrays(old, new)
    height, width = a.shape[:2]
    cx, cy = window.get('target') or (width / 2, height * .45)
    ys, xs = np.mgrid[:height, :width].astype(np.float32)
    distance = np.hypot(xs - cx, ys - cy)
    full = max(math.hypot(cx, cy), math.hypot(width - cx, cy), math.hypot(cx, height - cy), math.hypot(width - cx, height - cy))
    closing = fraction < .5
    radius = full * (1 - smooth(fraction / .5)) if closing else full * smooth((fraction - .5) / .5)
    ink = np.array(Image.new('RGB', (1, 1), window.get('color', '#1E2733')).getpixel((0, 0)), np.float32)
    if window.get('style') == 'blot':
        # An ink blot, not a lens: the edge wanders like ink soaking into paper.
        cache = renderer.__dict__.setdefault('blot_cache', {})
        if (width, height) not in cache:
            cache[(width, height)] = rough_field(width, height, 60, 71) * .06 * full + rough_field(width, height, 10, 73) * .012 * full
        distance = distance + cache[(width, height)]
    inside = np.clip((radius - distance) / 2.5, 0, 1)[..., None]
    out = (a if closing else b) * inside + ink * (1 - inside)
    return image(out)


def perspective_coefficients(source, target):
    """PIL PERSPECTIVE coefficients mapping output corners `target` to input corners `source`."""
    matrix, vector = [], []
    for (x, y), (u, v) in zip(target, source):
        matrix.append([x, y, 1, 0, 0, 0, -u * x, -u * y])
        matrix.append([0, 0, 0, x, y, 1, -v * x, -v * y])
        vector += [u, v]
    return np.linalg.solve(np.array(matrix, float), np.array(vector, float)).tolist()


def card_flip(renderer, old, new, fraction, window):
    """The page turns over like a card on its vertical axis, with perspective; the next page is on its back."""
    width, height = old.size
    f = smooth(fraction)
    angle = math.pi * f
    face = old if f < .5 else new
    cos = abs(math.cos(angle))
    if cos < .02:
        return Image.new('RGBA', old.size, renderer.paper)
    half = width / 2 * cos
    depth = .12 * math.sin(angle) * height  # the far edge shrinks
    near_left = f < .5
    left_top, left_bottom = (width / 2 - half, (0 if near_left else depth)), (width / 2 - half, (height if near_left else height - depth))
    right_top, right_bottom = (width / 2 + half, (depth if near_left else 0)), (width / 2 + half, (height - depth if near_left else height))
    target = [left_top, right_top, right_bottom, left_bottom]
    source = [(0, 0), (width, 0), (width, height), (0, height)]
    warped = face.convert('RGB').transform((width, height), Image.Transform.PERSPECTIVE, perspective_coefficients(source, target),
                                           Image.Resampling.BICUBIC, fillcolor=(214, 208, 196))
    shade = Image.new('RGB', (width, height), (0, 0, 0))
    return Image.blend(warped, shade, .25 * math.sin(angle)).convert('RGBA')


def zoom_through(renderer, old, new, fraction, window):
    """A match cut: the camera dives into a point of the old page (an element) and comes out of the new page there."""
    width, height = old.size
    cx, cy = window.get('target') or (width / 2, height / 2)
    f = float(np.clip(fraction, 0, 1))

    def zoomed(image_, factor, origin):
        ox, oy = origin
        box = (ox - ox / factor, oy - oy / factor, ox + (width - ox) / factor, oy + (height - oy) / factor)
        return image_.convert('RGB').resize((width, height), Image.Resampling.BICUBIC, box=box)
    dive = 1 + 7 * (f / .6) ** 2.2 if f < .6 else 8.
    rise = 1.6 - .6 * smooth((f - .4) / .6) if f > .4 else 1.6
    first = zoomed(old, dive, (cx, cy))
    if f <= .4:
        return first.convert('RGBA')
    second = zoomed(new, rise, (cx, cy))
    mix = smooth((f - .4) / .3)
    return Image.blend(first, second, mix).convert('RGBA')


def whip(renderer, old, new, fraction, window):
    """A whip pan: the old page streaks out sideways with motion blur and the new one streaks in."""
    width, height = old.size
    f = smooth(fraction)
    sign = -1 if window.get('direction', 'left') == 'left' else 1
    strip = Image.new('RGB', (width * 2, height), renderer.paper[:3])
    strip.paste(old.convert('RGB'), (0 if sign < 0 else width, 0))
    strip.paste(new.convert('RGB'), (width if sign < 0 else 0, 0))
    position = f * width if sign < 0 else (1 - f) * width
    speed = math.sin(math.pi * float(np.clip(fraction, 0, 1)))
    blur = int(.18 * width * speed)
    pixels = np.asarray(strip, np.float32)
    samples = max(1, blur // 12)
    acc = np.zeros((height, width, 3), np.float32)
    for k in range(samples):
        x = int(round(position + (k / max(1, samples - 1) - .5) * blur)) if samples > 1 else int(round(position))
        x = max(0, min(width, x))
        acc += pixels[:, x:x + width]
    return image(acc / samples)


def push(renderer, old, new, fraction, window):
    """The next page pushes the current one out of the frame (left, right, up or down)."""
    width, height = old.size
    f = smooth(fraction)
    direction = window.get('direction', 'left')
    frame = Image.new('RGBA', (width, height), renderer.paper)
    if direction in ('left', 'right'):
        shift = round(f * width) * (-1 if direction == 'left' else 1)
        frame.alpha_composite(old.convert('RGBA'), (shift, 0))
        frame.alpha_composite(new.convert('RGBA'), (shift + (width if direction == 'left' else -width), 0))
    else:
        shift = round(f * height) * (-1 if direction == 'up' else 1)
        frame.alpha_composite(old.convert('RGBA'), (0, shift))
        frame.alpha_composite(new.convert('RGBA'), (0, shift + (height if direction == 'up' else -height)))
    return frame


# ---------------------------------------------------------------- 2.0: paper, brushes, erasers and accents

ORIENT = {  # (to the canonical direction (the effect moves leftward, from the right edge), and back)
    'left': (lambda x: x, lambda x: x),
    'right': (lambda x: x[:, ::-1], lambda x: x[:, ::-1]),
    'up': (lambda x: np.rot90(x, 1), lambda x: np.rot90(x, -1)),
    'down': (lambda x: np.rot90(x, -1), lambda x: np.rot90(x, 1)),
}


def oriented(effect, renderer, old, new, fraction, window):
    """Run an array effect written for one direction in the window's direction (left, right, up or down)."""
    there, back = ORIENT[window.get('direction', 'left')]
    a, b = arrays(old, new)
    return image(np.ascontiguousarray(back(effect(renderer, np.ascontiguousarray(there(a)), np.ascontiguousarray(there(b)), fraction, window))))


def page_turn(renderer, old, new, fraction, window):
    """A page turned like a book: the fold sweeps from the right edge to the left on a slight slant; the lifted part
    folds over as a flap showing the paper's back (shaded, a ghost of the print showing through), the next page lies
    beneath with a contact shadow along the fold. direction: left (forward), right (back), up (a notepad flipped
    up from the bottom), down."""
    return oriented(turned_page, renderer, old, new, fraction, window)


def turned_page(renderer, a, b, fraction, window):
    height, width = a.shape[:2]
    slant = math.radians(window.get('angle', 14))
    normal = np.array([math.cos(slant), math.sin(slant)], np.float32)
    reach = width * normal[0] + height * abs(normal[1])
    position = (1.02 - 1.2 * smooth(fraction)) * reach  # fold distance along the normal from the top-left corner
    ys, xs = np.mgrid[:height, :width].astype(np.float32)
    d = xs * normal[0] + ys * normal[1] - position
    out = np.where((d > 0)[..., None], b, a)
    out = out * (1 - np.where(d > 0, .3 * np.exp(-d / (.04 * width)), 0))[..., None]  # contact shadow under the flap
    # Flap: a pixel left of the fold is covered when its mirror image across the fold lies on the original sheet.
    curl = .94  # a curling sheet is foreshortened a little
    mx, my = xs - 2 * d * normal[0] * curl, ys - 2 * d * normal[1] * curl
    flap = (d < 0) & (mx >= 0) & (mx <= width - 1) & (my >= 0) & (my <= height - 1)
    if flap.any():
        paper = np.array(renderer.paper[:3], np.float32)
        ghost = a[np.rint(my[flap]).astype(int), np.rint(mx[flap]).astype(int)]
        depth = np.clip(-d[flap] / (.5 * width), 0, 1)
        tone = .97 - .12 * depth + .05 * np.exp(-(-d[flap]) / 10.)  # bright crease at the fold, darker toward the free edge
        back = paper * tone[:, None] * .92 + ghost * .08
        out[flap] = back
        # The flap casts a soft shadow onto the old page just beyond its free edge.
        edge = (d < 0) & ~flap
        reach_back = np.minimum(np.abs(mx - np.clip(mx, 0, width - 1)) + np.abs(my - np.clip(my, 0, height - 1)), 60)
        out[edge] = out[edge] * (1 - .22 * np.exp(-reach_back[edge] / 14.))[:, None]
    return out


def tear_line(width, height, seed=31):
    """y of a ragged tear across the page for every x: a slight slant, a slow wander and a fine fibre jitter."""
    rng = np.random.default_rng(seed)
    xs = np.arange(width, dtype=np.float32)
    wander = np.interp(xs, np.linspace(0, width, 7), rng.normal(0, .035 * height, 7))
    jitter = np.convolve(rng.normal(0, 2.2, width + 8), np.ones(4) / 4, 'same')[4:width + 4]
    return height * (.47 + .06 * xs / width) + wander + jitter


def paper_tear(renderer, old, new, fraction, window):
    """The page is torn across: the tear runs from one edge to the other (the halves part a little behind it,
    showing white paper fibre along both torn edges), then the halves fall away with their shadows and the next page
    lies beneath."""
    a, b = arrays(old, new)
    height, width = a.shape[:2]
    cache = renderer.__dict__.setdefault('tear_cache', {})
    if (width, height) not in cache:
        line = tear_line(width, height)
        fibre = 2.5 + 2.5 * (rough_field(width, 8, 6, 37)[4] * .5 + .5)
        cache[(width, height)] = line, fibre
    line, fibre = cache[(width, height)]
    ys, xs = np.mgrid[:height, :width].astype(np.float32)
    beyond = ys - line[None, :]                       # < 0 above the tear
    paper = np.array(renderer.paper[:3], np.float32) * 1.02
    torn = min(1., fraction / .3)
    front = torn * (width + 120) - 60
    part = .9 * np.clip((front - xs[0]) / 60, 0, 1)   # how far the halves have parted, per column (px)
    frame = Image.fromarray(np.rint(b).astype(np.uint8)).convert('RGBA')
    fall = max(0., (fraction - .3) / .7) ** 1.7
    for upper in (True, False):
        side = beyond < 0 if upper else beyond >= 0
        rim = side & (np.abs(beyond) < fibre[None, :])
        rgba = np.dstack([np.where(rim[..., None], paper, a), np.where(side, 255., 0.)])
        piece = Image.fromarray(np.clip(np.rint(rgba), 0, 255).astype(np.uint8))
        if fraction < .3:
            # The tear opens behind its front: each column of a half moves a few pixels away from the line.
            shift = np.rint(part * (-6 if upper else 6)).astype(int)
            source = np.clip(ys.astype(int) - shift[None, :], 0, height - 1)
            moved = np.take_along_axis(np.asarray(piece), source[..., None].repeat(4, 2), 0)
            piece = Image.fromarray(np.ascontiguousarray(moved))
        else:
            sign = -1 if upper else 1
            piece = piece.rotate(sign * 9 * fall, Image.Resampling.BICUBIC, center=(width * (.15 if upper else .85), line.mean()),
                                 translate=(-sign * .25 * width * fall, sign * 1.1 * height * fall))
        shadow = Image.new('RGBA', piece.size, (24, 20, 16, 0))
        shadow.putalpha(piece.getchannel('A').filter(ImageFilter.GaussianBlur(9)).point(lambda value: value * .35))
        frame.alpha_composite(shadow, (8, 12))
        frame.alpha_composite(piece)
    return frame


def brush_reveal(renderer, old, new, fraction, window):
    """A broad dry brush paints the next page in with a few slanted strokes, one after another; its bristles leave
    gaps that the rest of the stroke fills, and its ragged edges overlap the next stroke."""
    a, b = arrays(old, new)
    height, width = a.shape[:2]
    cache = renderer.__dict__.setdefault('brush_cache', {})
    if (width, height) not in cache:
        strokes = 4 if height > width else 3
        angle = math.radians(window.get('angle', 24))
        across, along = np.array([-math.sin(angle), math.cos(angle)]), np.array([math.cos(angle), math.sin(angle)])
        ys, xs = np.mgrid[:height, :width].astype(np.float32)
        u = xs * across[0] + ys * across[1]                       # across the strokes
        v = xs * along[0] + ys * along[1]                         # along them
        u = (u - u.min()) / np.ptp(u) * strokes
        v = (v - v.min()) / np.ptp(v)
        ragged = rough_field(width, height, 14, 41) * .12
        band = np.clip(np.floor(u + ragged), 0, strokes - 1)
        forward = np.where(band % 2 == 0, v, 1 - v)                # boustrophedon, like a person painting a wall
        bristle = np.clip(rough_field(width, height, 2, 43) * .5 + .5, 0, 1)
        times = (band + forward) / strokes * .9 + .1 * bristle ** 2  # dry gaps fill a moment after the head passes
        cache[(width, height)] = times.astype(np.float32)
    times = cache[(width, height)]
    shown = np.clip((fraction - times) / .025, 0, 1)[..., None]
    return image(a * (1 - shown) + b * shown)


def cube(renderer, old, new, fraction, window):
    """The page is the face of a cube that turns: the old face swings away and the next face swings in beside it,
    in perspective, each darkening as it turns from the light."""
    width, height = old.size
    f = smooth(fraction)
    theta = math.pi / 2 * f
    sign = 1 if window.get('direction', 'left') == 'left' else -1
    depth = 2.2 * width                                            # camera distance
    frame = Image.new('RGB', (width, height), tuple(int(value * .9) for value in renderer.paper[:3]))

    def project(x, z):
        k = depth / (depth + z)
        return width / 2 + (x - width / 2) * k, k

    def corners(angle):
        # A face of a cube of side `width` turning about its vertical centre axis (centre at depth width/2).
        cx, cz = width / 2, width / 2
        result = []
        for x0 in (0, width):
            x, z = x0 - cx, -cz
            xr, zr = x * math.cos(angle) - z * math.sin(angle), x * math.sin(angle) + z * math.cos(angle)
            result.append((xr + cx, zr + cz))
        return result

    faces = [(old, -sign * theta), (new, sign * (math.pi / 2 - theta))]
    for face, angle in sorted(faces, key=lambda item: -abs(item[1])):
        (x0, z0), (x1, z1) = corners(angle)
        (sx0, k0), (sx1, k1) = project(x0, z0), project(x1, z1)
        if sx1 - sx0 < 2:
            continue
        target = [(sx0, height / 2 - height / 2 * k0), (sx1, height / 2 - height / 2 * k1),
                  (sx1, height / 2 + height / 2 * k1), (sx0, height / 2 + height / 2 * k0)]
        source = [(0, 0), (width, 0), (width, height), (0, height)]
        warped = face.convert('RGB').transform((width, height), Image.Transform.PERSPECTIVE, perspective_coefficients(source, target),
                                               Image.Resampling.BICUBIC)
        mask = Image.new('L', (width, height))
        ImageDraw.Draw(mask).polygon(target, fill=255)
        shade = Image.blend(warped, Image.new('RGB', (width, height), (0, 0, 0)), .45 * abs(math.sin(angle)))
        frame.paste(shade, mask=mask)
    return frame.convert('RGBA')


def shard_plan(width, height, count, seed=53):
    """Voronoi paper shards: per-pixel shard index, and per shard its centre, drift, spin and start delay."""
    rng = np.random.default_rng(seed)
    seeds = np.c_[rng.uniform(0, width, count), rng.uniform(0, height, count)]
    small = (max(2, width // 4), max(2, height // 4))
    ys, xs = np.mgrid[:small[1], :small[0]].astype(np.float32) * 4
    labels = np.argmin(((xs[..., None] - seeds[:, 0]) ** 2 + (ys[..., None] - seeds[:, 1]) ** 2), -1).astype(np.uint8)
    labels = np.asarray(Image.fromarray(labels).resize((width, height), Image.Resampling.NEAREST))
    return labels, seeds, rng.uniform(-1, 1, (count, 3))


def shards(renderer, old, new, fraction, window):
    """The page cracks into paper shards that drop and spin away (nearest the target first), uncovering the next page."""
    width, height = old.size
    count = 16
    cache = renderer.__dict__.setdefault('shard_cache', {})
    if (width, height) not in cache:
        cache[(width, height)] = shard_plan(width, height, count)
    labels, seeds, randomness = cache[(width, height)]
    cx, cy = window.get('target') or (width / 2, height * .45)
    order = np.hypot(seeds[:, 0] - cx, seeds[:, 1] - cy)
    delays = .15 + .35 * order / max(1., order.max())
    a = np.asarray(old.convert('RGB'))
    frame = new.convert('RGBA').copy()
    crack = fraction < .2
    for index in np.argsort(-delays):
        t = max(0., (fraction - delays[index]) / (1 - delays[index]))
        mask = labels == index
        if t >= 1 or not mask.any():
            continue
        ys, xs = np.nonzero(mask)
        box = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)
        rgba = np.dstack([a[box[1]:box[3], box[0]:box[2]], np.where(mask[box[1]:box[3], box[0]:box[2]], 255, 0).astype(np.uint8)])
        piece = Image.fromarray(rgba)
        drift = randomness[index]
        dx = (seeds[index, 0] - cx) * .25 * t + drift[0] * 40 * t
        dy = 1.3 * height * t * t + drift[1] * 30 * t
        piece = piece.rotate(drift[2] * 70 * t, Image.Resampling.BICUBIC, expand=True)
        x = round(box[0] + (box[2] - box[0]) / 2 + dx - piece.width / 2)
        y = round(box[1] + (box[3] - box[1]) / 2 + dy - piece.height / 2)
        if t > 0:
            shadow = Image.new('RGBA', piece.size, (24, 20, 16, 0))
            shadow.putalpha(piece.getchannel('A').filter(ImageFilter.GaussianBlur(6)).point(lambda value: value * .3))
            frame.alpha_composite(shadow, (x + 6, y + 10))
        frame.alpha_composite(piece, (x, y))
    if crack:
        # Cracks show first: thin dark lines along the shard borders.
        border = np.zeros(labels.shape, bool)
        border[1:] |= labels[1:] != labels[:-1]
        border[:, 1:] |= labels[:, 1:] != labels[:, :-1]
        line = Image.fromarray(np.where(border, round(160 * min(1, fraction / .12)), 0).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))
        ink = Image.new('RGBA', (width, height), (40, 34, 30, 0))
        ink.putalpha(line)
        frame.alpha_composite(ink)
    return frame


def tiles(renderer, old, new, fraction, window):
    """The next page is laid down tile by tile in a diagonal wave: each paper tile drops onto the old page from a
    little above, with a shadow that tightens as it lands."""
    width, height = old.size
    columns = 4 if height > width else 6
    rows = max(2, round(columns * height / width))
    frame = old.convert('RGBA').copy()
    order = sorted(((row + column, row, column) for row in range(rows) for column in range(columns)))
    for _, row, column in order:
        left, top = round(column * width / columns), round(row * height / rows)
        right, bottom = round((column + 1) * width / columns), round((row + 1) * height / rows)
        delay = (row + column) / (rows + columns - 2) * .62
        t = float(np.clip((fraction - delay) / .38, 0, 1))
        if t <= 0:
            continue
        land = 1 - (1 - t) ** 3
        lift = 1 - land
        tile = new.crop((left, top, right, bottom)).convert('RGBA')
        size = (round((right - left) * (1 + .18 * lift)), round((bottom - top) * (1 + .18 * lift)))
        tile = tile.resize(size, Image.Resampling.BICUBIC)
        tile.putalpha(round(255 * min(1., t * 3)))
        x = left - (size[0] - (right - left)) // 2
        y = top - (size[1] - (bottom - top)) // 2 - round(.04 * height * lift)
        shadow = Image.new('RGBA', (size[0] + 40, size[1] + 40), (24, 20, 16, 0))
        mask = Image.new('L', shadow.size)
        ImageDraw.Draw(mask).rectangle((20, 20, 20 + size[0], 20 + size[1]), fill=round(90 * min(1., t * 3) * (.4 + .6 * lift)))
        shadow.putalpha(mask.filter(ImageFilter.GaussianBlur(6 + 10 * lift)))
        frame.alpha_composite(shadow, (x - 20 + round(4 + 14 * lift), y - 20 + round(6 + 20 * lift)))
        frame.alpha_composite(tile, (x, y))
    return frame


def flash(renderer, old, new, fraction, window):
    """A flash cut: the frame burns out to white (or the given colour) and the next page comes out of it."""
    a, b = arrays(old, new)
    color = np.array(Image.new('RGB', (1, 1), window.get('color', '#FFFDF6')).getpixel((0, 0)), np.float32)
    if fraction < .3:
        mix = (fraction / .3) ** 2
        return image(a + (color - a) * mix)
    mix = 1 - smooth((fraction - .3) / .7)
    return image(b + (color - b) * mix)


def rubber_sprite(width, height):
    """A small pink rubber eraser, slightly worn at one end, with a soft shadow."""
    pad = max(5, round(height * .3))
    image_ = Image.new('RGBA', (width + 2 * pad, height + 2 * pad))
    shadow = Image.new('L', image_.size)
    ImageDraw.Draw(shadow).rounded_rectangle((pad + 5, pad + 8, pad + width + 5, pad + height + 8), radius=height // 3, fill=90)
    image_.putalpha(shadow.filter(ImageFilter.GaussianBlur(pad / 2)))
    image_ = Image.composite(Image.new('RGBA', image_.size, (30, 26, 22, 255)), Image.new('RGBA', image_.size), image_.getchannel('A'))
    draw = ImageDraw.Draw(image_)
    draw.rounded_rectangle((pad, pad, pad + width, pad + height), radius=height // 3, fill=(232, 150, 160, 255))
    draw.rounded_rectangle((pad + width * .62, pad, pad + width, pad + height), radius=height // 3, fill=(70, 120, 190, 255))
    draw.rectangle((pad + width * .62, pad, pad + width * .7, pad + height), fill=(70, 120, 190, 255))
    draw.rounded_rectangle((pad + width * .06, pad + height * .18, pad + width * .56, pad + height * .36), radius=height // 8, fill=(246, 190, 196, 255))
    return image_, pad
