"""Packet lesson cards and narration-aligned ASS motion, with no import dependencies.

Integration::

    if packet_video_motion.draw_diagram(scene, draw, put):
        ...  # This scene has been drawn; skip legacy diagram dispatch.
    if packet_video_motion.animation_events(scene, phrase_time, emit):
        ...  # Motion emitted; skip legacy motion dispatch for this scene.

``put`` has the signature used by build_course_video.render_scene. ``emit`` is
``emit(scene, start, end, ass_tags, ass_shape, meaning)``. ``phrase_time`` takes
``(scene, phrase)`` and returns an absolute, tempo-adjusted narration time.
Neither function mutates the supplied scene. Unknown kinds return False.

Optional scene['diagram'] supplies {'cards': [{'title': ..., 'detail': ...}],
'note': ..., 'labels': {...}}. Cards and focus_phrases follow this fixed order:

* packet-input: CSV rows, payload, metadata, classifier (four cards).
* packet-encoder: bytes, group/embed, assembled sequence, blocks, logits (five).
* packet-training: forward, loss, backward, update (four).
* packet-split: duplicate grouping, train, validation, test (four).
* repo-sync: source repository, tests/export, client repository (three).

Scientific numbers belong in the supplied card details; qualitative defaults
contain no asserted dimensions, measurements, class counts, or dataset sizes.
Optional labels: 'eyebrow' (all kinds), 'payload_route' and 'metadata_route'
(input), 'learned' (encoder), 'labels' (training), 'identity' (repo-sync).
Keep card titles short; details are laid out with explicit lower bounds so the
renderer rejects overflow instead of clipping a scientific label silently.

ASS vector shapes occupy reserved diagram margins, icon areas, and connectors.
Only hollow borders are progressively revealed: no mask covers labels, evidence,
or numerical values. Motion is illustrative and works with the 30 fps renderer;
it does not simulate measured training, live inference, or a current test run.
"""

import math


INK = '#172c3a'
TEAL = '#126e68'
BLUE = '#d9e9ed'
CORAL = '#b14c36'
PURPLE = '#61579a'
MUTED = '#465a63'
WHITE = '#ffffff'
ASS_TEAL = '686E12'
ASS_CORAL = '364CB1'
ASS_PURPLE = '9A5761'

_LAYOUTS = {
    'packet-input': {
        'boxes': ((100, 350, 635, 744), (790, 350, 1260, 530),
                  (790, 585, 1260, 765), (1420, 350, 1820, 530)),
        'cards': (('CSV rows', 'Source files retain their declared labels'),
                  ('Payload', 'Byte values become model input'),
                  ('Metadata', 'Context retained for the audit'),
                  ('Classifier', 'Receives payload features')),
        'eyebrow': 'ONE ROW, SEPARATE RESPONSIBILITIES',
        'note': 'Illustrative data path: payload enters the classifier; metadata stays outside the model.',
        'concepts': ('CSV rows', 'payload model input', 'metadata audit context', 'classifier input'),
    },
    'packet-encoder': {
        'boxes': tuple((100 + 350 * i, 370, 420 + 350 * i, 752) for i in range(5)),
        'cards': (('Payload bytes', 'Retained bytes from a packet'),
                  ('Group / embed', 'Byte groups become vectors'),
                  ('Sequence', 'Payload vectors + learned positions'),
                  ('Mamba blocks', 'Transform the assembled sequence'),
                  ('Class logits', 'Scores for the supplied classes')),
        'eyebrow': 'THE PACKET ENCODER, STAGE BY STAGE',
        'note': 'Schematic tensor path. Scientific dimensions are supplied by the lesson evidence.',
        'concepts': ('payload bytes', 'grouping and embedding', 'sequence and learned positions',
                     'Mamba blocks', 'class logits'),
    },
    'packet-training': {
        'boxes': ((100, 350, 800, 523), (1120, 350, 1820, 523),
                  (1120, 610, 1820, 783), (100, 610, 800, 783)),
        'cards': (('Forward', 'Payload features produce class scores'),
                  ('Loss', 'Compare scores with supplied labels'),
                  ('Backward', 'Loss produces parameter gradients'),
                  ('Update', 'The optimizer changes model weights')),
        'eyebrow': 'WHAT CHANGES WHEN THE MODEL LEARNS',
        'note': 'Illustrative training cycle: labels affect loss; metadata stays outside the model input.',
        'concepts': ('forward computation', 'labels and loss', 'backward gradients', 'parameter update'),
    },
    'packet-split': {
        'boxes': ((100, 350, 635, 755), (880, 350, 1820, 475),
                  (880, 490, 1820, 615), (880, 630, 1820, 755)),
        'cards': (('Exact payload groups', 'Keep identical payloads together in the global split'),
                  ('Train', 'Groups assigned to learning'),
                  ('Validation', 'Different groups for model selection'),
                  ('Test', 'Different groups for held-out evaluation')),
        'eyebrow': 'SPLIT GROUPS, KEEP DUPLICATES TOGETHER',
        'note': 'Illustrative allocation: each exact-duplicate payload group belongs to one split only.',
        'concepts': ('exact duplicate grouping', 'train groups', 'validation groups', 'test groups'),
    },
    'repo-sync': {
        'boxes': ((100, 375, 590, 755), (715, 375, 1205, 755), (1330, 375, 1820, 755)),
        'cards': (('Source repository', 'Develop the packet implementation'),
                  ('Tests / export', 'Check and export the shared code'),
                  ('Client repository', 'Receive the same packet implementation')),
        'eyebrow': 'ONE PACKET IMPLEMENTATION, TWO REPOSITORIES',
        'note': 'Illustrative maintenance path. The receiving repository uses the same exported packet code.',
        'concepts': ('source repository', 'automated tests and export', 'client repository'),
    },
}

DIAGRAMS = frozenset(_LAYOUTS)


def _content(scene):
    layout = _LAYOUTS[scene['kind']]
    diagram = scene.get('diagram', {})
    if not isinstance(diagram, dict):
        raise ValueError('Packet diagram must be an object')
    cards = diagram.get('cards')
    if cards is None:
        cards = [{'title': title, 'detail': detail} for title, detail in layout['cards']]
    if (not isinstance(cards, (list, tuple)) or len(cards) != len(layout['boxes'])
            or any(not isinstance(card, dict)
                   or not isinstance(card.get('title'), str)
                   or not isinstance(card.get('detail'), str) for card in cards)):
        raise ValueError('Packet diagram cards must supply a title and detail for every stage')
    labels = diagram.get('labels', {})
    if not isinstance(labels, dict) or any(not isinstance(value, str) for value in labels.values()):
        raise ValueError('Packet diagram labels must contain text')
    note = diagram.get('note', layout['note'])
    if not isinstance(note, str):
        raise ValueError('Packet diagram note must contain text')
    return layout, cards, labels, note


def _arrow(draw, origin, destination, color=TEAL, width=4):
    x, y = origin
    right, bottom = destination
    length = math.hypot(right - x, bottom - y)
    dx, dy = (right - x) / length, (bottom - y) / length
    draw.line((x, y, right, bottom), fill=color, width=width)
    draw.polygon(((right, bottom), (right - 12 * dx + 6 * dy, bottom - 12 * dy - 6 * dx),
                  (right - 12 * dx - 6 * dy, bottom - 12 * dy + 6 * dx)), fill=color)


def _card(draw, put, box, card, color=TEAL, *, size=29, detail_bottom=None):
    x, y, right, bottom = box
    draw.rounded_rectangle(box, radius=18, fill=WHITE, outline=BLUE, width=3)
    draw.rectangle((x + 22, y + 20, x + 28, bottom - 20), fill=color)
    put(card['title'], x + 47, y + 20, right - x - 67, size, color, True,
        max_bottom=y + 90)
    put(card['detail'], x + 47, y + 84, right - x - 67, 26, INK,
        max_bottom=detail_bottom if detail_bottom is not None else bottom - 13)


def _stack(draw, x, y, color=TEAL):
    """A symbolic grouped object; the stripes do not encode a measured count."""
    draw.rounded_rectangle((x + 8, y - 8, x + 74, y + 26), radius=5, fill=WHITE, outline=color, width=2)
    draw.rounded_rectangle((x + 4, y - 4, x + 70, y + 30), radius=5, fill=WHITE, outline=color, width=2)
    draw.rounded_rectangle((x, y, x + 66, y + 34), radius=5, fill=color)


def draw_diagram(scene, draw, put):
    """Draw one supported scene and return True; leave unknown scenes untouched."""
    kind = scene.get('kind')
    if kind not in DIAGRAMS:
        return False
    layout, cards, labels, note = _content(scene)
    boxes = layout['boxes']
    put(labels.get('eyebrow', layout['eyebrow']), 100, 291, 1720, 23, MUTED, True)

    if kind == 'packet-input':
        for i, (box, card) in enumerate(zip(boxes, cards)):
            _card(draw, put, box, card, CORAL if i == 2 else TEAL,
                  detail_bottom=565 if i == 0 else None)
        # Two symbolic CSV rows separate payload fields from metadata fields.
        for y in (607, 672):
            draw.rounded_rectangle((145, y - 7, 591, y + 38), radius=6, fill=BLUE)
            draw.rectangle((159, y + 3, 365, y + 26), fill=TEAL)
            draw.rectangle((379, y + 3, 575, y + 26), fill=CORAL)
        _arrow(draw, (650, 430), (770, 430))
        _arrow(draw, (650, 670), (770, 670), CORAL)
        _arrow(draw, (1275, 430), (1400, 430))
        put(labels.get('payload_route', 'MODEL INPUT'), 802, 545, 455, 22, TEAL, True)
        put(labels.get('metadata_route', 'AUDIT CONTEXT ONLY'), 1434, 628, 368, 23, CORAL, True)
        # This terminal stop has no connector to the classifier.
        draw.line((1310, 654, 1370, 654), fill=CORAL, width=4)
        draw.line((1370, 640, 1370, 668), fill=CORAL, width=4)
    elif kind == 'packet-encoder':
        for box, card in zip(boxes, cards):
            _card(draw, put, box, card, size=26, detail_bottom=609)
        for i in range(4):
            _arrow(draw, (280 + i * 350, 685), (588 + i * 350, 685), '#8aadb0')
        for i, x in enumerate((224, 574, 924, 1274, 1624)):
            if i in (0, 2):
                _stack(draw, x, 670)
            elif i == 1:
                draw.rounded_rectangle((x + 12, 654, x + 52, 716), radius=5, fill=TEAL)
                draw.line((x + 21, 665, x + 43, 665), fill=WHITE, width=3)
                draw.line((x + 21, 677, x + 43, 677), fill=WHITE, width=3)
            elif i == 3:
                draw.rounded_rectangle((x, 654, x + 74, 716), radius=9, fill=BLUE, outline=TEAL, width=3)
                draw.line((x + 12, 686, x + 24, 668, x + 46, 699, x + 62, 681), fill=TEAL, width=4)
            else:
                draw.line((x + 4, 708, x + 70, 708), fill=BLUE, width=4)
                draw.rectangle((x + 15, 663, x + 28, 708), fill=TEAL)
                draw.rectangle((x + 42, 685, x + 55, 708), fill=TEAL)
        put(labels.get('learned', 'LEARNED'), 846, 613, 218, 21, PURPLE, True)
        _arrow(draw, (959, 642), (959, 664), PURPLE, 3)
    elif kind == 'packet-training':
        for box, card in zip(boxes, cards):
            _card(draw, put, box, card, detail_bottom=box[3] - 12)
        _arrow(draw, (820, 475), (1100, 475))
        _arrow(draw, (1470, 540), (1470, 591))
        _arrow(draw, (1100, 692), (820, 692))
        _arrow(draw, (450, 591), (450, 540))
        draw.rounded_rectangle((837, 350, 1083, 407), radius=10, fill=WHITE, outline=PURPLE, width=2)
        put(labels.get('labels', 'Known label'), 851, 361, 220, 24, PURPLE, True, max_bottom=401)
        _arrow(draw, (1090, 379), (1110, 379), PURPLE, 3)
    elif kind == 'packet-split':
        _card(draw, put, boxes[0], cards[0], detail_bottom=565)
        for index, color in enumerate((TEAL, CORAL, PURPLE)):
            _stack(draw, 175 + index * 139, 652, color)
        for index, (box, card, color) in enumerate(zip(boxes[1:], cards[1:], (TEAL, CORAL, PURPLE))):
            x, y, right, bottom = box
            draw.rounded_rectangle(box, radius=18, fill=WHITE, outline=BLUE, width=3)
            draw.rectangle((x + 22, y + 20, x + 28, bottom - 20), fill=color)
            put(card['title'], x + 47, y + 14, 688, 28, color, True, max_bottom=y + 60)
            put(card['detail'], x + 47, y + 62, 755, 24, INK, max_bottom=bottom - 10)
            _stack(draw, 1719, y + 47, color)
            _arrow(draw, (651, 606 + index * 26), (860, y + 62), color)
    else:  # repo-sync
        for box, card in zip(boxes, cards):
            _card(draw, put, box, card, size=28, detail_bottom=615)
        for x in (307, 922, 1537):
            _stack(draw, x, 669)
        _arrow(draw, (392, 686), (905, 686), '#8aadb0')
        _arrow(draw, (1007, 686), (1520, 686), '#8aadb0')
        put(labels.get('identity', 'SAME PACKET CODE'), 762, 625, 413, 23, TEAL, True)
    put(note, 100, 797, 1720, 23, MUTED, max_bottom=834)
    return True


def _ring(box):
    x, y, right, bottom = box
    width, height = right - x, bottom - y
    # Opposite winding removes the interior, so this can never hide card text.
    return (f'm 0 0 l {width} 0 l {width} {height} l 0 {height} l 0 0 '
            f'm 5 5 l 5 {height - 5} l {width - 5} {height - 5} '
            f'l {width - 5} 5 l 5 5')


_CHIP = 'm 0 0 l 18 0 l 18 14 l 0 14'
_GROUP = ('m 0 0 l 32 0 l 32 10 l 0 10 '
          'm 4 14 l 36 14 l 36 24 l 4 24 '
          'm 8 28 l 40 28 l 40 38 l 8 38')
_VECTOR = 'm 0 0 l 16 0 l 16 42 l 0 42'


def animation_events(scene, phrase_time, emit):
    """Emit bounded motion for one scene, returning whether its kind is handled.

    Supplied focus phrases must resolve successfully; a bad narration anchor is
    an error, never a request to invent a time. All validation precedes emission.
    Without anchors, focus starts are spread through 6–82% of the scene. Shape
    travel and border reveals share those anchors and scale for short scenes.
    """
    kind = scene.get('kind')
    if kind not in DIAGRAMS:
        return False
    layout, _, _, _ = _content(scene)
    start, end = scene['start'], scene['end']
    if (not isinstance(start, (int, float)) or not isinstance(end, (int, float))
            or not math.isfinite(start) or not math.isfinite(end) or start < 0 or start >= end):
        raise ValueError('Packet animation needs a finite, positive scene interval')
    duration = end - start
    boxes = layout['boxes']
    phrases = scene.get('focus_phrases', [])
    if phrases and (not isinstance(phrases, (list, tuple)) or len(phrases) != len(boxes)):
        raise ValueError('Packet animation focus count does not match its diagram')
    if phrases:
        if not callable(phrase_time):
            raise ValueError('Packet focus phrases require narration timing')
        anchors = [phrase_time(scene, phrase) for phrase in phrases]
        if any(not isinstance(anchor, (int, float)) or not math.isfinite(anchor)
               or not start <= anchor < end for anchor in anchors):
            raise ValueError('Packet focus anchor extends outside its scene')
    else:
        anchors = [start + duration * (0.06 + 0.76 * i / max(1, len(boxes) - 1))
                   for i in range(len(boxes))]

    pending = []
    emphasis_length = min(6.0, duration / (len(boxes) + 1))

    def add(begin, length, tags, shape, meaning):
        stop = min(end, begin + length)
        if start <= begin < stop <= end:
            pending.append((scene, begin, stop, tags, shape,
                            'Illustrative ' + meaning + '; not live inference or measured execution.'))

    def travel(index, origin, destination, meaning, color=ASS_TEAL, shape=_CHIP, offset=0.0):
        begin = anchors[index] + min(duration * offset, (end - anchors[index]) * 0.2)
        length = min(1.8, duration * 0.075, (end - begin) * 0.8)
        x, y = origin
        right, bottom = destination
        tags = (f'\\an7\\move({x},{y},{right},{bottom})\\p1\\c&H{color}&\\bord0'
                '\\shad0')
        add(begin, length, tags, shape, meaning)

    for index, (box, concept) in enumerate(zip(boxes, layout['concepts'])):
        x, y, right, bottom = box
        begin = anchors[index]
        stop = min(end, begin + emphasis_length)
        reveal_ms = max(1, round(min(0.55, (stop - begin) * 0.35) * 1000))
        tags = (f'\\an7\\pos({x},{y})\\p1\\c&H{ASS_TEAL}&\\bord0\\shad0'
                f'\\clip({x},{y},{x},{bottom})'
                f'\\t(0,{reveal_ms},\\clip({x},{y},{right},{bottom}))')
        add(begin, emphasis_length, tags, _ring(box), 'narration emphasis: ' + concept)

    if kind == 'packet-input':
        travel(1, (650, 423), (751, 423), 'payload selected from CSV rows for model input')
        travel(2, (650, 663), (751, 663), 'metadata retained on its separate audit branch', ASS_CORAL)
        travel(3, (1275, 423), (1381, 423), 'payload features entering the classifier')
    elif kind == 'packet-encoder':
        travel(0, (265, 662), (568, 662), 'payload byte groups reaching the embedding stage', shape=_GROUP)
        travel(1, (620, 656), (913, 656), 'embedded payload vectors joining the sequence', shape=_VECTOR)
        travel(2, (951, 642), (951, 666), 'learned positions joining the payload sequence', ASS_PURPLE)
        travel(2, (972, 664), (1268, 664), 'assembled sequence entering the Mamba blocks', shape=_GROUP, offset=0.025)
        travel(3, (1355, 664), (1611, 664), 'transformed representation reaching the class logits', shape=_VECTOR)
    elif kind == 'packet-training':
        travel(0, (820, 467), (1080, 467), 'forward scores passed to loss computation', shape=_VECTOR)
        travel(1, (1090, 372), (1102, 372), 'supplied label affecting loss', ASS_PURPLE)
        travel(1, (1461, 540), (1461, 577), 'loss starting backward computation')
        travel(2, (1080, 684), (820, 684), 'backward gradients reaching the optimizer update')
        travel(3, (441, 577), (441, 540), 'updated parameters returning to the next forward pass')
    elif kind == 'packet-split':
        for index, (target, color) in enumerate(zip(('train', 'validation', 'test'),
                                                   (ASS_TEAL, ASS_CORAL, ASS_PURPLE))):
            travel(index + 1, (651, 595 + index * 26), (832, 398 + index * 140),
                   'an exact duplicate payload group allocated intact to ' + target + ' only',
                   color, _GROUP)
    else:
        travel(0, (392, 669), (878, 669),
               'same packet code moving from the source repository to automated tests and export', shape=_GROUP)
        travel(1, (1007, 669), (1493, 669),
               'same packet code exported to the client repository after the declared checks', shape=_GROUP)

    for event in pending:
        emit(*event)
    return True
