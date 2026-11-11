"""Keep the pen's work on screen: whatever is being drawn sits inside the camera view, above the caption band.

A camera move designed for one sentence can leave the next element off screen: a label written at the edge of a
push-in, text written while the camera still holds the previous picture, a parallax label sliding out during a pan, a
box marked around a picture the camera has not reached. The viewer then watches a pen that writes outside the frame.
After the timeline is assembled, every drawn element and every board overlay is checked against the camera view at
several moments of its drawing (or entrance) window, with its parallax shift and dolly scale.
When it is not wholly visible, a few fixes are tried: designed moves that start mid-drawing wait for the pen, and a
correcting camera key just before the element starts nudges the view, centres the element or pulls back to hold it
with what the view already shows. The fix that leaves the page best is kept, judged first by what the pen draws, then
by overlays (a pen working out of view is the worse fault); when none makes the page better the designed moves stay.
What no camera move can show (under the caption band, off the page, inside a dolly zoom) is reported for the layout."""
import math

import numpy as np

MARGIN = 24        # screen px kept between a drawn word or mark and the frame edge or the caption band
TIP_MARGIN = 6     # a picture only needs its pen tip on screen
SAMPLES = 7        # moments checked across an element's drawing window, at least
STEP = .25         # and at most this far apart (seconds): a long picture is checked all the way through
LEAD = .5          # a correcting move starts this long before the element (seconds), so it has arrived
MOVE_SECONDS = .55
ROUNDS = 6         # an inserted move can uncover another element; re-check this many times per page
HOLD = .4          # a move that had to wait is held this long before the next designed move
GROUP_SECONDS = 3. # a framing move also frames elements drawn this soon after, when they fit at the same zoom


def renderer_for(timeline):
    from video_renderer import Renderer
    renderer = object.__new__(Renderer)
    renderer.timeline = timeline
    renderer.width, renderer.height = timeline['canvas']['width'], timeline['canvas']['height']
    renderer.fps = timeline['canvas'].get('fps', 30)
    return renderer


def caption_top(page, height):
    """Screen y where the page's captions begin (the frame bottom when it has none)."""
    tops = [event['y'] for event in page['events'] if event['caption']]
    return min(tops) if tops else height


def is_overlay(event):
    return 'recipe' in event


def element_box(renderer, event, index, time):
    """Screen-unit board box of an element at a moment (parallax shift and dolly scale included)."""
    if is_overlay(event):
        width, height = event['width'], event['height']
    else:
        metadata = renderer.timeline['assets'][event['asset']]
        scale = float(event.get('scale', 1.))
        width, height = metadata['width'] / scale, metadata['height'] / scale
    box = np.array([event['x'], event['y'], event['x'] + width, event['y'] + height], float)
    if id(event) in renderer.warped(index) or (is_overlay(event) and event.get('depth')):
        shift, factor, pivot = renderer.warp(event, index, time)
        box = np.r_[pivot + (box[:2] - pivot) * factor, pivot + (box[2:] - pivot) * factor] + np.r_[shift, shift]
    return box


def visible_rect(center, zoom, width, height, top_of_captions, margin=MARGIN):
    """Board rect a viewer can see clearly: inside the frame by a margin (screen px), above the caption band. Where the
    frame reaches the page edge the margin shrinks to what is left of the page: no camera could show more there."""
    half = np.array([width, height]) / (2 * zoom)
    low, high = center - half, center + half
    margin = margin / zoom
    left, top = low + np.minimum(margin, np.maximum(low, 0))
    right = high[0] - min(margin, max(width - high[0], 0))
    if top_of_captions < height:
        bottom = center[1] + (top_of_captions - height / 2) / zoom - margin
    else:
        bottom = high[1] - min(margin, max(height - high[1], 0))
    return np.array([left, top, right, bottom])


def overflow(box, rect):
    """How far (board px) a box sticks out of a rect; 0 when wholly inside."""
    return float(max(rect[0] - box[0], rect[1] - box[1], box[2] - rect[2], box[3] - rect[3], 0.))


def drawn_events(page):
    """Elements a viewer watches appear: drawn elements, and board overlays while they animate in (a box, a callout,
    printed matter)."""
    return ([event for event in page['events'] if not event['caption'] and event['end'] > event['start']]
            + [overlay for overlay in page.get('overlays') or () if overlay.get('space') == 'board' and overlay['end'] > overlay['start']])


def is_picture(event):
    return event.get('role') == 'illustration' and event.get('pen', True)


def watched(renderer, event, index, time, progress):
    """What must be visible while an element is drawn: a word, line or mark as a whole; for a picture, where the pen is
    (a push-in may frame part of a big picture on purpose, but never away from the strokes being drawn)."""
    if is_picture(event):
        tip = renderer.event_tip(event, progress)
        return np.r_[tip, tip]
    return element_box(renderer, event, index, time)


def overflow_at(renderer, event, index, progress, center, zoom, top_of_captions):
    time = event['start'] + (event['end'] - event['start']) * progress
    margin = TIP_MARGIN if is_picture(event) else 0. if is_overlay(event) else MARGIN   # an overlay box has its own padding
    return overflow(watched(renderer, event, index, time, progress), visible_rect(center, zoom, renderer.width, renderer.height, top_of_captions, margin))


def check_page(renderer, index):
    """[(event, worst overflow px, moment, zoom, visible at its start)] of elements drawn outside the clear view."""
    page = renderer.timeline['pages'][index]
    width, height = renderer.width, renderer.height
    top_of_captions = caption_top(page, height)
    problems = []
    page_view = np.array([width / 2, height / 2])
    for event in drawn_events(page):
        if is_overlay(event) and overflow_at(renderer, event, index, 0., page_view, 1., top_of_captions) > 1.:
            continue   # an overlay the whole page cannot hold is a backdrop or an effect, not something to frame
        worst, when, zoom_then, first_ok = 0., None, 1., True
        samples = max(SAMPLES, math.ceil((event['end'] - event['start']) / STEP) + 1)
        for k in range(samples):
            progress = k / (samples - 1)
            time = event['start'] + (event['end'] - event['start']) * progress
            center, zoom, *_ = renderer.camera_track(index, time, steady=True)
            amount = overflow_at(renderer, event, index, progress, center, zoom, top_of_captions)
            if k == 0 and amount > 1.:
                first_ok = False
            if amount > worst:
                worst, when, zoom_then = amount, time, zoom
        if worst > 1.:
            problems.append((event, worst, when, zoom_then, first_ok))
    return problems


def framing_key(renderer, index, event, at, view, style='centre'):
    """A camera key at a page moment that brings the element into the clear view (above the captions), from the view
    (centre, zoom) the camera holds then. Styles:
    - nudge: the view shifted just far enough, so what it already shows mostly stays;
    - centre: the element in the middle, at the current zoom when it fits, pulling back only as far as needed;
    - widen: pulled back just far enough to hold what the view shows and the element together.
    Elements drawn soon after join the frame while they fit at the same zoom, so one move serves a run of labels
    instead of chasing each. None when the style has nothing to offer."""
    page = renderer.timeline['pages'][index]
    width, height = renderer.width, renderer.height
    top_of_captions = caption_top(page, height)
    centre_now, zoom_now = np.asarray(view[0], float), float(view[1])

    def fits(box):
        return min((width - 2 * MARGIN) / max(box[2] - box[0], 1.), (top_of_captions - 2 * MARGIN) / max(box[3] - box[1], 1.))

    def clear_centre(box, zoom):
        """Camera centre that puts a box in the middle of the clear area, which ends at the captions, not the frame."""
        return np.array([(box[0] + box[2]) / 2, (box[1] + box[3]) / 2 - (top_of_captions / 2 - height / 2) / zoom])

    box = element_box(renderer, event, index, event['start'])
    zoom = max(1., min(zoom_now, fits(box)))
    for other in sorted(drawn_events(page), key=lambda item: item['start']):
        if event['start'] < other['start'] <= event['end'] + GROUP_SECONDS:
            more = element_box(renderer, other, index, other['start'])
            union = np.r_[np.minimum(box[:2], more[:2]), np.maximum(box[2:], more[2:])]
            if fits(union) < zoom:
                break
            box = union
    rect = visible_rect(centre_now, zoom_now, width, height, top_of_captions)
    if style == 'nudge':
        if zoom < zoom_now - 1e-6:
            return None   # it does not fit at the current zoom
        centre = centre_now + np.maximum(box[2:] - rect[2:], 0) - np.maximum(rect[:2] - box[:2], 0)
    elif style == 'widen':
        both = np.r_[np.minimum(rect[:2], box[:2]), np.maximum(rect[2:], box[2:])]
        zoom = max(1., min(zoom_now, fits(both)))
        if zoom >= zoom_now - 1e-6:
            return None   # both fit at the current zoom: a nudge does it
        centre = clear_centre(both, zoom)
    else:
        centre = clear_centre(box, zoom)
    centre = renderer.clamp_view(centre, zoom)
    return {'at': round(max(0., at), 3), 'move': 'pan', 'center': [round(float(centre[0]), 1), round(float(centre[1]), 1)],
            'zoom': round(float(zoom), 3), 'seconds': MOVE_SECONDS, 'ease': 'inout_sine', 'auto': 'framing'}


def numeric_at(page, key):
    at = key.get('at', 0)
    if isinstance(at, str):
        beats = {beat['id']: beat['start'] - page['start'] for beat in page['beats']}
        return beats[at[5:]]
    return float(at)


def in_dolly(page, local):
    """True while a dolly zoom (a key with a subject) is the latest key: a framing move would break it."""
    latest = None
    for key in page.get('camera') or []:
        if numeric_at(page, key) <= local:
            latest = key
    return bool(latest and latest.get('subject'))


def move_seconds(key):
    import motion
    return float(motion.camera_key(key).get('seconds', .8))


def wait_for_pen(page, keys, start, end):
    """Designed moves that would begin while an element is still being drawn wait until the pen is done. Later moves
    keep their times (they are cued to words) unless the move before them would still be running; then they follow it
    after a short hold. A move that can no longer land before the page's last moment is dropped, except the last move
    (it hands over to the page turn).
    The page's opening frame (a key at 0) never moves. Returns the wait of the first move (0 when nothing waited)."""
    inside = [key for key in keys if max(start, 0.) < numeric_at(page, key) < end and key.get('auto') != 'framing']
    if not inside:
        return 0.
    latest = page['end'] - page['start'] - .3
    first = min(numeric_at(page, key) for key in inside)
    shift = end + .1 - first
    designed = sorted((key for key in keys if key.get('auto') != 'framing' and numeric_at(page, key) >= first), key=lambda key: numeric_at(page, key))
    cursor, dropped = end + .1, []
    for number, key in enumerate(designed):
        at = max(numeric_at(page, key), cursor)
        if number < len(designed) - 1 and at + move_seconds(key) > latest:
            dropped.append(id(key))
            continue
        key['at'] = round(min(at, latest), 3)
        cursor = at + move_seconds(key) + HOLD
    keys[:] = [key for key in keys if id(key) not in dropped]
    return round(shift, 3)


def name_of(event):
    return event['recipe'] if is_overlay(event) else event['asset']


def page_score(timeline, index):
    """How far a page's elements stray out of view: what the pen draws first, overlays second."""
    problems = check_page(renderer_for(timeline), index)
    return (sum(item[1] for item in problems if not is_overlay(item[0])), sum(item[1] for item in problems if is_overlay(item[0])))


def better(score, than):
    return score[0] < than[0] - .5 or (score[0] <= than[0] + .5 and score[1] < than[1] - .5)


def fixes(timeline, index, event):
    """[(keys, wait, framing key, style)] to try for one element: designed moves wait for the pen, and a framing key
    (nudge, centre, widen) on top of the waited or the designed moves. Least intrusive first: ties go to it."""
    page = timeline['pages'][index]
    start, end = event['start'] - page['start'], event['end'] - page['start']
    designed = [dict(key) for key in page['camera']]
    waited = [dict(key) for key in page['camera']]
    wait = wait_for_pen(page, waited, start - LEAD, end)
    options = [(waited, wait, None, None)] if wait else []
    at = max(0., start - LEAD)
    for keys, shift in ([(waited, wait)] if wait else []) + [(designed, 0.)]:
        page['camera'] = keys
        renderer = renderer_for(timeline)
        view = renderer.camera_track(index, page['start'] + at, steady=True)[:2]
        for style in ('nudge', 'centre', 'widen'):
            key = framing_key(renderer, index, event, at, view, style)
            if key:
                kept = [item for item in keys if not (item.get('auto') == 'framing' and abs(numeric_at(page, item) - key['at']) < 1e-6)]
                options.append((kept + [key], shift, key, style))
    page['camera'] = designed
    return options


def keep_drawing_in_view(timeline):
    """Make every drawn element visible while it is drawn (and every board overlay while it arrives), trying the fixes
    above one element at a time. Returns a report of what changed and what could not be fixed."""
    report = {'adjustments': [], 'unfixable': []}
    for index, page in enumerate(timeline['pages']):
        if page.get('camera'):
            given_up = set()
            for _ in range(ROUNDS):
                problems = check_page(renderer_for(timeline), index)
                fixable = [item for item in problems if id(item[0]) not in given_up and not in_dolly(page, item[0]['start'] - page['start'])]
                if not fixable:
                    break
                event, amount, *_ = min(fixable, key=lambda item: item[0]['start'])
                designed, current, best = page['camera'], page_score(timeline, index), None
                for keys, wait, key, style in fixes(timeline, index, event):
                    page['camera'] = sorted(keys, key=lambda item: numeric_at(page, item))
                    score = page_score(timeline, index)
                    if better(score, current) and (best is None or better(score, best[0])):
                        best = (score, page['camera'], wait, key, style)
                page['camera'] = designed
                if best is None:
                    given_up.add(id(event))   # no fix makes the page better: keep the designed moves and report it
                    continue
                _, page['camera'], wait, key, style = best
                action = {'page': index + 1, 'asset': name_of(event), 'role': event.get('role', 'overlay'), 'overflow_px': round(amount, 1)}
                if wait:
                    action['moves_waited_seconds'] = wait
                if key:
                    action.update(framed_at=key['at'], framing=style, center=key['center'], zoom=key['zoom'])
                report['adjustments'].append(action)
        for event, amount, when, _, _ in check_page(renderer_for(timeline), index):
            report['unfixable'].append({'page': index + 1, 'asset': name_of(event), 'role': event.get('role', 'overlay'), 'overflow_px': round(amount, 1),
                                        'at': round(when, 2), 'reason': 'no camera move shows it without losing something being drawn (it sits under '
                                                                         'the captions or off the page, or inside a dolly zoom); move or retime it'})
    return report
