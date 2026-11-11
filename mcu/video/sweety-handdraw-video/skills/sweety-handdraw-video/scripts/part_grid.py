#!/usr/bin/env python3
"""See an image the way part boxes are written: the picture on paper with a labelled 0.05 grid; every separate object
(orange, numbered) and every inked colour area the engine colours as one piece (blue, a1, a2...) outlined, with their
normalized boxes listed. Write parts from it as "box": [left, top, right, bottom] in the
drawing order you want; 2.0's snapping gives each inked area to the part that owns most of it, so boxes need not trace
shapes. Use "exclude_boxes" to hand a held prop or an overlapping limb to a later part.

    part_grid.py JOB inputs/art/i06-arrive.png [--crop L T R B]   ->  design/parts/i06-arrive.png and .json
"""
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

PAPER = (251, 247, 238, 255)
GRID, LABEL, OBJECT = (210, 40, 120), (30, 90, 200), (240, 120, 20)


def font(size):
    for path in ('/System/Library/Fonts/Hiragino Sans GB.ttc', '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def objects(image, minimum_share=.002):
    """Separate objects: opaque connected regions (alpha), or on an opaque image the non-paper regions."""
    pixels = np.asarray(image.convert('RGBA')).astype(int)
    alpha = pixels[..., 3]
    if alpha.min() < 250:
        solid = alpha > 128
    else:
        paper = pixels[0, 0, :3]
        solid = np.abs(pixels[..., :3] - paper).sum(-1) > 40
    labels, count = ndimage.label(ndimage.binary_closing(solid, iterations=2))
    height, width = solid.shape
    result = []
    for index, box in enumerate(ndimage.find_objects(labels), 1):
        area = int((labels[box] == index).sum())
        if area < minimum_share * width * height:
            continue
        result.append({'box': [round(box[1].start / width, 3), round(box[0].start / height, 3), round(box[1].stop / width, 3), round(box[0].stop / height, 3)],
                       'share': round(area / (width * height), 4)})
    result.sort(key=lambda item: (item['box'][1], item['box'][0]))
    for number, item in enumerate(result, 1):
        item['object'] = number
    return result


def areas(image, minimum_share=.003, work_side=800):
    """The colour pieces 2.0 paints as wholes (inked, one paint), largest first: these are what part boxes hand out."""
    import stroke_assets
    factor = min(1., work_side / max(image.size))
    width, height = max(8, round(image.width * factor)), max(8, round(image.height * factor))
    with __import__('tempfile').TemporaryDirectory() as directory:
        path = Path(directory) / 'image.png'
        image.save(path)
        art = stroke_assets.prepare_artwork(path, width, height)
    pieces, count, _, solid = stroke_assets.color_pieces(art['outline'], art['pixels'], art['alpha'])
    height, width = pieces.shape
    sizes = np.bincount(pieces.ravel(), minlength=count + 1)
    found = []
    for index in np.argsort(-sizes):
        if index == 0 or not solid[index] or sizes[index] < minimum_share * width * height:
            continue
        ys, xs = np.nonzero(pieces == index)
        colour = art['pixels'][ys, xs, :3].mean(0)
        found.append({'box': [round(xs.min() / width, 3), round(ys.min() / height, 3), round((xs.max() + 1) / width, 3), round((ys.max() + 1) / height, 3)],
                      'centre': [round(xs.mean() / width, 3), round(ys.mean() / height, 3)], 'share': round(float(sizes[index]) / (width * height), 4),
                      'colour': '#%02x%02x%02x' % tuple(int(value) for value in colour)})
    for number, item in enumerate(found, 1):
        item['area'] = f'a{number}'
    return found


def draw(image, found, painted=(), scale_to=900):
    canvas = Image.new('RGBA', image.size, PAPER)
    canvas.alpha_composite(image.convert('RGBA'))
    factor = scale_to / max(canvas.size)
    canvas = canvas.resize((round(canvas.width * factor), round(canvas.height * factor)), Image.Resampling.LANCZOS).convert('RGB')
    width, height = canvas.size
    pad = 40
    sheet = Image.new('RGB', (width + pad, height + pad), 'white')
    sheet.paste(canvas, (pad, pad))
    pen = ImageDraw.Draw(sheet)
    small, big = font(13), font(18)
    for k in range(21):
        f = k / 20
        x, y = pad + f * width, pad + f * height
        strong = k % 2 == 0
        pen.line((x, pad, x, pad + height), fill=GRID if strong else (235, 170, 200), width=1)
        pen.line((pad, y, pad + width, y), fill=GRID if strong else (235, 170, 200), width=1)
        if strong:
            pen.text((x - 10, 4), f'{f:.1f}'.lstrip('0') or '0', fill=GRID, font=small)
            pen.text((2, y - 8), f'{f:.1f}'.lstrip('0') or '0', fill=GRID, font=small)
    for item in found:
        left, top, right, bottom = item['box']
        pen.rectangle((pad + left * width, pad + top * height, pad + right * width, pad + bottom * height), outline=OBJECT, width=2)
        pen.text((pad + left * width + 4, pad + top * height + 2), str(item['object']), fill=OBJECT, font=big)
    for item in painted:
        x, y = pad + item['centre'][0] * width, pad + item['centre'][1] * height
        pen.ellipse((x - 17, y - 11, x + 17, y + 11), fill=(255, 255, 255), outline=LABEL, width=2)
        pen.text((x - 13, y - 9), item['area'], fill=LABEL, font=small)
    return sheet


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('job', type=Path)
    parser.add_argument('image', type=Path)
    parser.add_argument('--crop', type=int, nargs=4)
    arguments = parser.parse_args()
    image = Image.open(arguments.image if arguments.image.is_absolute() else arguments.job / arguments.image)
    if arguments.crop:
        image = image.crop(tuple(arguments.crop))
    found, painted = objects(image), areas(image)
    out = arguments.job / 'design' / 'parts'
    out.mkdir(parents=True, exist_ok=True)
    stem = Path(arguments.image).stem
    draw(image, found, painted).save(out / f'{stem}.png')
    record = {'image': str(arguments.image), 'crop': arguments.crop, 'objects': found, 'areas': painted}
    (out / f'{stem}.json').write_text(json.dumps(record, ensure_ascii=False, indent=1))
    print(json.dumps({'sheet': str(out / f'{stem}.png'), 'objects': len(found), 'areas': len(painted)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
