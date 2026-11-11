"""Automatic direction for pages the model left plain: a camera that follows what is being drawn, a transition into
each page, and small life on finished pictures. Anything the job writes itself (camera, transition, motion) wins.

job.json "direction": {"camera": "auto"|"off", "transitions": "auto"|"off", "motion": "auto"|"off", "boil": true}
(all auto by default)."""
import math
import re

AUTO_ZOOM = 1.45      # deepest automatic push-in; pages with auto camera are built at this board scale
FRAME_FILL = .78      # the focus area fills this share of the visible frame
VIEW_HEIGHT = .66     # share of the screen height above the caption band (9:16) where the focus is framed
CHAPTER = re.compile(r'^(第[一二三四五六七八九十百0-9]+[条章节部分步课]|Part\s*\d|Chapter\s*\d)', re.I)
HOLDS = ('hold', 'drift', 'follow')   # how the camera holds a picture while it is drawn, page by page
QUICK_MOVES = ('whip', 'snap', 'slam')
PLAIN_TRANSITIONS = ('cut', 'fade', 'slide', 'pan', 'push')
SIGNATURES = ({'type': 'page_turn', 'seconds': 1.1}, {'type': 'page_turn', 'direction': 'up', 'seconds': 1.1},
              {'type': 'erase', 'seconds': 1.3}, {'type': 'paper_tear', 'seconds': 1.2})
QUIET = ({'type': 'slide_over', 'seconds': .8}, {'type': 'pan', 'seconds': .7}, {'type': 'push', 'seconds': .7})
ACCENTS = ({'type': 'brush_reveal', 'seconds': 1.1}, {'type': 'iris', 'style': 'blot', 'seconds': .9}, {'type': 'marker_wipe', 'seconds': 1.},
           {'type': 'zoom_through', 'seconds': 1.}, {'type': 'tiles', 'seconds': 1.}, {'type': 'ink_bleed', 'seconds': 1.},
           {'type': 'cube', 'seconds': .9}, {'type': 'whip', 'seconds': .45}, {'type': 'erase', 'style': 'rubber', 'seconds': 1.3},
           {'type': 'card_flip', 'seconds': .9}, {'type': 'shards', 'seconds': 1.1})


def options(manifest):
    value = manifest.get('direction') or {}
    if not isinstance(value, dict):
        raise ValueError('direction must be an object')
    result = {'camera': value.get('camera', 'auto'), 'transitions': value.get('transitions', 'auto'),
              'motion': value.get('motion', 'auto'), 'boil': bool(value.get('boil', True))}
    for key in ('camera', 'transitions', 'motion'):
        if result[key] not in ('auto', 'off'):
            raise ValueError(f'direction.{key} is auto or off')
    return result


def box(event, metadata):
    scale = float(event.get('scale', 1.))
    return event['x'], event['y'], event['x'] + metadata['width'] / scale, event['y'] + metadata['height'] / scale


def focus_segments(page, assets):
    """Pictures and the labels that follow them: one camera focus per picture."""
    segments = []
    for event in sorted((item for item in page['events'] if not item['caption']), key=lambda item: item['start']):
        area = box(event, assets[event['asset']])
        if event.get('role') == 'illustration' or not segments:
            segments.append({'start': event['start'], 'end': event['end'], 'boxes': [area]})
        else:
            segments[-1]['boxes'].append(area)
            segments[-1]['end'] = max(segments[-1]['end'], event['end'])
    return segments


def frame_for(boxes, width, height, vertical):
    left, top = min(b[0] for b in boxes), min(b[1] for b in boxes)
    right, bottom = max(b[2] for b in boxes), max(b[3] for b in boxes)
    pad_x, pad_y = .06 * (right - left) + 12, .06 * (bottom - top) + 12
    w, h = right - left + 2 * pad_x, bottom - top + 2 * pad_y
    usable = height * (VIEW_HEIGHT if vertical else .82)
    zoom = max(1., min(AUTO_ZOOM, FRAME_FILL * width / w, FRAME_FILL * usable / h))
    center = [(left + right) / 2, (top + bottom) / 2]
    # Keep the focus above the captions: aim the frame centre a little below the subject on a vertical screen.
    center[1] += (height / zoom) * (.5 - VIEW_HEIGHT / 2) * (1 if vertical else .3)
    return center, zoom


def view_rect(center, zoom, width, height):
    half_w, half_h = width / (2 * zoom), height / (2 * zoom)
    cx = min(max(center[0], half_w), width - half_w)
    cy = min(max(center[1], half_h), height - half_h)
    return cx - half_w, cy - half_h, cx + half_w, cy + half_h


def cut_through(rect, area):
    """True when the frame edge slices through the area (part of it shows, part does not)."""
    inside = rect[0] <= area[0] and rect[1] <= area[1] and area[2] <= rect[2] and area[3] <= rect[3]
    outside = area[2] <= rect[0] or area[0] >= rect[2] or area[3] <= rect[1] or area[1] >= rect[3]
    return not inside and not outside


def keep_titles_whole(center, zoom, segment, texts, width, height, vertical):
    """A push-in must not slice a title or label already on the page: take it into the frame when that still leaves a
    real close-up, otherwise move the frame until the text is wholly out of view."""
    for start, area in texts:
        if start >= segment['start'] or not cut_through(view_rect(center, zoom, width, height), area):
            continue
        widened, wider_zoom = frame_for(segment['boxes'] + [area], width, height, vertical)
        if wider_zoom >= 1.12:
            center, zoom = widened, wider_zoom
            continue
        rect = view_rect(center, zoom, width, height)
        if area[3] <= (rect[1] + rect[3]) / 2:      # the text sits above the focus: lower the frame below it
            shift = area[3] - rect[1] + 8
        else:                                        # below the focus: raise the frame above it
            shift = area[1] - rect[3] - 8
        focus_top, focus_bottom = min(b[1] for b in segment['boxes']), max(b[3] for b in segment['boxes'])
        moved = view_rect([center[0], center[1] + shift], zoom, width, height)
        if moved[1] <= focus_top and focus_bottom <= moved[3] and not cut_through(moved, area):
            center = [center[0], center[1] + shift]
        else:
            center, zoom = widened, wider_zoom   # a gentler push that shows the whole title beats a sliced one
        if cut_through(view_rect(center, zoom, width, height), area):
            center, zoom = [width / 2, height / 2], 1.   # still sliced (the frame leans down for the captions): show the page
    return center, zoom


def auto_camera(page, assets, width, height, index=0):
    """Camera keys (page-relative seconds) for a page the model left plain: frame each picture as it is drawn, travel
    to the next (a hop on a long trip), and pull back to the whole page before it turns. Pages take turns between
    three ways of holding a picture while it is drawn, so a film does not repeat one move: hold still, drift slowly in,
    or follow the pen."""
    segments = focus_segments(page, assets)
    if not segments:
        return None
    vertical = height > width
    keys, length = [], page['end'] - page['start']
    style = HOLDS[index % len(HOLDS)]
    texts = [(event['start'], box(event, assets[event['asset']])) for event in page['events']
             if not event['caption'] and event.get('role') == 'text']
    for number, segment in enumerate(segments):
        center, zoom = frame_for(segment['boxes'], width, height, vertical)
        center, zoom = keep_titles_whole(center, zoom, segment, texts, width, height, vertical)
        center = [round(value, 1) for value in center]
        if number == 0:
            keys.append({'at': 0., 'center': center, 'zoom': round(zoom, 3), 'move': 'cut'})
        else:
            at = max(.05, segment['start'] - page['start'] - .45)
            if at <= keys[-1]['at'] + .3:
                keys[-1].update(center=center, zoom=round(zoom, 3))
                continue
            previous = keys[-1]
            trip = math.dist(previous['center'], center) * min(previous['zoom'], zoom)
            move = 'hop' if trip > .55 * width and min(previous['zoom'], zoom) >= 1.2 else ('push_in' if zoom > previous['zoom'] * 1.08 else 'pan')
            keys.append({'at': round(at, 3), 'center': center, 'zoom': round(zoom, 3), 'move': move,
                         **({'seconds': .9} if move == 'pan' else {})})
        drawn = segment['end'] - segment['start']
        wide = max(1., zoom * .92)
        sliced = any(start < segment['start'] and cut_through(view_rect(center, wide, width, height), area) for start, area in texts)
        if style == 'drift' and zoom > 1.04 and drawn > 1.5 and not sliced:
            # Settle a little wide of the picture and ease in while it is drawn.
            keys[-1]['zoom'] = round(max(1., zoom * .92), 3)
            keys.append({'at': round(keys[-1]['at'] + (keys[-1].get('seconds', 1.) if number else 0) + .05, 3), 'center': center,
                         'zoom': round(zoom, 3), 'move': 'drift', 'seconds': round(min(3., drawn), 3)})
        elif style == 'follow' and zoom > 1.2 and drawn > 2.:
            keys[-1]['follow'] = True
    deepest = max(key['zoom'] for key in keys)
    finished = page.get('last_drawing_end', page['end']) - page['start']
    pull = max(finished + .6, length - 2.6)
    if deepest > 1.04 and pull < length - 1.:
        keys.append({'at': round(pull, 3), 'center': [width / 2, height / 2], 'zoom': 1., 'move': 'pull_out',
                     'seconds': round(min(1.5, length - pull - .4), 3)})
    elif deepest <= 1.04 and length > 4:
        # The page already fills the frame: a slow push gives the hold some life.
        keys = [{'at': 0., 'center': [width / 2, height / 2], 'zoom': 1., 'move': 'cut'},
                {'at': round(min(finished, length * .5), 3), 'center': [width / 2, height * .47], 'zoom': 1.06, 'move': 'drift',
                 'seconds': round(min(3., max(.5, length * .4)), 3)}]
    # Keys must not overlap: a later key starts after the previous move ends.
    for before, after in zip(keys, keys[1:]):
        from motion import camera_key
        end = before['at'] + camera_key(before).get('seconds', .8) * (before['at'] > 0)
        if after['at'] < end:
            after['at'] = round(min(end, length - .1), 3)
    return keys


def camera_moves(pages):
    """Every camera move of a film: (film seconds, move name, zoom before, zoom after, move seconds)."""
    from motion import camera_key
    moves = []
    for page in pages:
        zoom = 1.
        for key in page.get('camera') or []:
            key = camera_key(key)
            at = key.get('at', 0)
            if isinstance(at, str):
                at = next((beat['start'] - page['start'] for beat in page.get('beats', []) if beat['id'] == at[5:]), 0.)
            seconds = float(key.get('seconds', .8))
            if at > 0 and seconds > 0:
                moves.append((page['start'] + at, key.get('move', 'custom'), zoom, float(key.get('zoom', 1)), seconds))
            zoom = float(key.get('zoom', 1))
    return moves


def camera_warnings(pages):
    """Density rules for camera work (huashu-art-motion 镜头语言, anidoodle motion grammar): quick moves are accents,
    push-ins need rests between them, and one move repeated reads as a template."""
    moves, warnings = camera_moves(pages), []
    if not moves:
        return warnings
    quick = [move for move in moves if move[4] < .4 or move[1] in QUICK_MOVES]
    if len(moves) >= 6 and len(quick) > len(moves) / 3:
        warnings.append(f'Camera: {len(quick)} of {len(moves)} moves are whips/slams/snaps; keep quick moves to accents (at most a third)')
    run, longest, where = 0, 0, None
    for move in moves:
        run = run + 1 if move[3] > move[2] * 1.08 else 0
        if run > longest:
            longest, where = run, move[0]
    if longest >= 3:
        warnings.append(f'Camera: {longest} push-ins in a row ending at {where:.1f}s; rest the eye with a pan, a hold or a pull-out')
    span = max(60., pages[-1]['end'] - pages[0]['start'])
    pushes = sum(1 for move in moves if move[3] > move[2] * 1.08)
    if pushes / span * 60 > 8:
        warnings.append(f'Camera: {pushes / span * 60:.1f} push-ins per minute; above 8 the film feels restless')
    return warnings


def transition_warnings(pages):
    """The same designed transition three page turns in a row reads as a preset."""
    kinds = [(page.get('transition') or {}).get('type') for page in pages[1:]]
    for first, second, third in zip(kinds, kinds[1:], kinds[2:]):
        if first and first == second == third and first not in PLAIN_TRANSITIONS:
            return [f'Transitions: {first} three times in a row; vary them or keep one signature transition for chapters']
    return []


def is_chapter(page_spec):
    if page_spec.get('chapter'):
        return True
    actions = [action for holder in page_spec.get('visual_groups', []) + page_spec.get('beats', []) for action in holder.get('actions') or []]
    return any(action.get('type') == 'text' and CHAPTER.match(str(action.get('text', ''))) for action in actions)


def auto_transition(page_index, page_spec, previous):
    """A transition into a page: a signature paper move at a new chapter (a page turn, a notepad flip, an eraser, a
    tear, in turn); otherwise a quiet move, with a designed accent every third page; never the same twice in a row."""
    if is_chapter(page_spec):
        return dict(SIGNATURES[page_index % len(SIGNATURES)])
    pool = ACCENTS if page_index % 3 == 0 else QUIET
    for offset in range(len(pool)):
        choice = pool[(page_index // 3 + offset) % len(pool)]
        if choice['type'] != previous:
            return dict(choice)
    return {'type': 'pan', 'seconds': .7}


def auto_motions(event, boil=True):
    """Small life on a finished picture: a settle when the last stroke lands, then a gentle hand-drawn boil."""
    if event.get('role') != 'illustration' or event.get('motions'):
        return []
    effects = [{'type': 'pop', 'start': round(event['end'] + .05, 3), 'end': round(event['end'] + .5, 3), 'strength': .35}]
    if boil:
        effects.append({'type': 'boil', 'start': round(event['end'] + .5, 3), 'end': round(event['end'] + .875, 3), 'strength': 1.})
    return effects
