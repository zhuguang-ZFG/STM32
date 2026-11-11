"""Frame composition of a drawn illustration (shared by the renderer, the builder and the metrics):
paper <- paint (flat marker color: a streaky wet coat where the marker passes, settling solid) <- shade (source paint, soft broad strokes)
<- sketch (light construction lines, faded after inking) <- line layer (revealed exactly where the nib passed)."""
from pathlib import Path
import numpy as np
from PIL import Image

SHARP = 250.   # reveal ramp of a nib or marker edge, in fractions of the event


def ramp(start, length):
    """Length of a ramp that starts at `start`, shortened so it is complete by the end of the event (fraction 1)."""
    return np.maximum(np.minimum(length, 1 - start), 1e-6)


def over(top_rgb, top_alpha, rgb, alpha):
    result = top_alpha + alpha * (1 - top_alpha)
    color = (top_rgb * top_alpha[..., None] + rgb * (alpha * (1 - top_alpha))[..., None]) / np.maximum(result, 1e-6)[..., None]
    return color, result


def prepare(maps, line, paint, shade, sketch=None):
    """maps: npz-like time maps; line/paint/shade/sketch: RGBA uint8 arrays."""
    as_float = lambda image: np.asarray(image, np.float32) / 255
    line, paint, shade = as_float(line), as_float(paint), as_float(shade)
    layers = {'line_rgb': line[..., :3], 'line_alpha': line[..., 3], 'flat': paint[..., :3], 'shade_rgb': shade[..., :3],
              'alpha': shade[..., 3], 'ink': np.asarray(maps['ink'], np.float32),
              'color': np.asarray(maps['color'], np.float32), 'cover': np.asarray(maps['color_cover'], np.float32),
              'full': np.asarray(maps['color_full'], np.float32), 'shade': np.asarray(maps['shade'], np.float32),
              'shade_ramp': float(maps['shade_ramp']),
              'paint_ramps': tuple(float(value) for value in maps['paint_ramps']) if 'paint_ramps' in maps else (0., 0.)}
    if sketch is not None:
        sketch = as_float(sketch)
        layers.update(sketch_rgb=sketch[..., :3], sketch_alpha=sketch[..., 3], sketch=np.asarray(maps['sketch'], np.float32),
                      sketch_fade=tuple(float(value) for value in maps['sketch_fade']))
    # Per-pixel first change and settle time: frames only recompute the pixels in between.
    finite = lambda values: np.where(np.isfinite(values), values, -np.inf)
    times = [layers['ink'], layers['color']] + ([layers['sketch']] if sketch is not None else [])
    layers['start'] = np.minimum.reduce(times)
    settle = [finite(layers['ink'] + 1 / SHARP), finite(layers['full'] + ramp(layers['full'], layers['paint_ramps'][1])),
              finite(layers['color'] + ramp(layers['color'], layers['paint_ramps'][0])),
              finite(layers['shade'] + layers['shade_ramp'])]
    if sketch is not None:
        settle.append(np.where(np.isfinite(layers['sketch']), sum(layers['sketch_fade']), -np.inf).astype(np.float32))
    layers['settle'] = np.maximum.reduce(settle)
    layers['final'] = blend(layers, np.float32(1e30))
    return layers


def load(directory, name):
    directory = Path(directory)
    image = lambda suffix: np.array(Image.open(directory / f'{name}-{suffix}.png').convert('RGBA'))
    maps = np.load(directory / f'{name}.npz')
    sketch = image('sketch') if (directory / f'{name}-sketch.png').exists() else None
    return prepare(maps, image('line'), image('paint'), image('shade'), sketch)


def blend(layers, progress, where=Ellipsis):
    """RGBA uint8 of the selected pixels at this fraction of the drawing event."""
    pick = lambda key: layers[key][where]
    front, coat = layers['paint_ramps']
    color, full = pick('color'), pick('full')
    # A fresh coat comes in over a frame or two at its streaky strength, then settles to solid (always by the end).
    wet = pick('cover') * (np.clip((progress - color) / ramp(color, front), 0, 1) if front > 0 else (progress >= color))
    dry = np.clip((progress - full) / ramp(full, coat), 0, 1) if coat > 0 else (progress >= full)
    paint = (wet + (1 - wet) * dry) * pick('alpha')
    mix = np.clip((progress - pick('shade')) / layers['shade_ramp'], 0, 1)[..., None]
    flat = pick('flat')
    rgb, alpha = flat + (pick('shade_rgb') - flat) * mix, paint.astype(np.float32)
    if 'sketch' in layers:
        start, length = layers['sketch_fade']
        visible = pick('sketch_alpha') * np.clip((progress - pick('sketch')) * SHARP, 0, 1) * (1 - np.clip((progress - start) / length, 0, 1))
        rgb, alpha = over(pick('sketch_rgb'), visible, rgb, alpha)
    ink = pick('line_alpha') * np.clip((progress - pick('ink')) * SHARP, 0, 1)
    rgb, alpha = over(pick('line_rgb'), ink, rgb, alpha)
    return np.concatenate([np.rint(np.clip(rgb, 0, 1) * 255), np.rint(np.clip(alpha, 0, 1) * 255)[..., None]], -1).astype(np.uint8)


def compose(layers, progress):
    """RGBA uint8 frame of the illustration at this fraction of its drawing event."""
    progress = np.float32(progress)
    frame = np.where((progress >= layers['settle'])[..., None], layers['final'], np.uint8(0))
    active = (layers['start'] <= progress) & (progress < layers['settle'])
    if active.any():
        frame[active] = blend(layers, progress, active)
    return frame
