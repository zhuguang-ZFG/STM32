"""Video canvas aspect ratios: presets, custom sizes, and default 2:3 vertical."""
import re

# Long side is 1920 where it fits; short side stays even. 2:3 is the product default (since 2.0).
PRESETS = {
    '9:16': (1080, 1920),
    '3:4':  (1440, 1920),
    '2:3':  (1280, 1920),
    '16:9': (1920, 1080),
    '4:3':  (1920, 1440),
    '3:2':  (1920, 1280),
}
DEFAULT_RATIO = '2:3'
MIN_SIDE, MAX_SIDE = 720, 2160
MAX_PIXELS = int(1920 * 1920 * 1.05)


def normalize_ratio(value):
    if not isinstance(value, str):
        raise ValueError('aspect_ratio must be a string like 9:16 or custom')
    text = value.strip().lower().replace('：', ':').replace(' ', '')
    if text in PRESETS:
        return text
    if text in ('custom', '自定义'):
        return 'custom'
    if re.fullmatch(r'\d+:\d+', text):
        raise ValueError(f'Unknown aspect ratio {value!r}; use one of {list(PRESETS)} or custom')
    raise ValueError(f'Unknown aspect ratio {value!r}')


def _even(value):
    value = int(round(value))
    return value if value % 2 == 0 else value + 1


def resolve_canvas(aspect_ratio=DEFAULT_RATIO, width=None, height=None, fps=30):
    """Return {aspect_ratio, width, height, fps}. Custom requires both width and height."""
    ratio = normalize_ratio(aspect_ratio or DEFAULT_RATIO)
    if ratio == 'custom':
        if width is None or height is None:
            raise ValueError('custom aspect requires width and height')
        width, height = int(width), int(height)
    else:
        width, height = PRESETS[ratio]
        if width is not None and height is not None:
            # Explicit pixels win only when they match the named ratio within 2.5%.
            if abs((int(width) / int(height)) - (PRESETS[ratio][0] / PRESETS[ratio][1])) > .025:
                raise ValueError(f'width/height do not match aspect_ratio {ratio}')
            width, height = int(width), int(height)
    width, height = _even(width), _even(height)
    if not (MIN_SIDE <= width <= MAX_SIDE and MIN_SIDE <= height <= MAX_SIDE):
        raise ValueError(f'Each side must be within {MIN_SIDE}..{MAX_SIDE} and even')
    if width * height > MAX_PIXELS:
        raise ValueError(f'Canvas pixels exceed the {MAX_PIXELS} budget')
    fps = int(fps if fps is not None else 30)
    if not 1 <= fps <= 60:
        raise ValueError('fps must be within 1..60')
    return {'aspect_ratio': ratio, 'width': width, 'height': height, 'fps': fps}


def validate_aspect_choice(value):
    if not isinstance(value, dict):
        raise ValueError('Aspect choice must be an object')
    canvas = resolve_canvas(value.get('aspect_ratio', DEFAULT_RATIO), value.get('width'), value.get('height'), value.get('fps', 30))
    return {'aspect_ratio': canvas['aspect_ratio'], 'width': canvas['width'], 'height': canvas['height'],
            **({'fps': canvas['fps']} if 'fps' in value else {})}


def text_menu():
    """Numbered lines for native/TTY pickers."""
    lines = [f'{index + 1}) {name}  ({PRESETS[name][0]}×{PRESETS[name][1]})'
             + ('  ← 默认' if name == DEFAULT_RATIO else '')
             for index, name in enumerate(PRESETS)]
    lines.append(f'{len(PRESETS) + 1}) 自定义  (输入宽×高，每边 {MIN_SIDE}..{MAX_SIDE})')
    return lines
