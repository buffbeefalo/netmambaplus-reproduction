"""Exercise the packet lesson's drawing and motion contracts without Pillow."""

import copy
import math
from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
try:
    import packet_video_motion as packet
except ModuleNotFoundError:
    packet = None


CARD_COUNTS = {
    'packet-input': 4,
    'packet-encoder': 5,
    'packet-training': 4,
    'packet-split': 4,
    'repo-sync': 3,
}


class Drawing:
    """Record the renderer's output boundary, with the ImageDraw call protocol."""

    def __init__(self):
        self.geometry = []
        self.text = []

    def rounded_rectangle(self, box, **kwargs):
        self.geometry.append(tuple(box))

    def rectangle(self, box, **kwargs):
        self.geometry.append(tuple(box))

    def line(self, points, **kwargs):
        self.geometry.append(tuple(points))

    def polygon(self, points, **kwargs):
        self.geometry.append(tuple(value for pair in points for value in pair))

    def ellipse(self, box, **kwargs):
        self.geometry.append(tuple(box))

    def put(self, text, x, y, width, size=36, color=None, bold=False,
            mono=False, max_bottom=835):
        if y + len(str(text).split('\n')) * (size + 12) > max_bottom:
            raise ValueError('Explicit text lines do not fit their reserved region')
        self.text.append(str(text))
        self.geometry.append((x, y, x + width, min(max_bottom, y + size)))


class PacketMotionTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(packet, 'The packet-specific diagram and motion module is missing')

    def scene(self, kind='packet-encoder', duration=20):
        return {'id': 'packet-scene', 'kind': kind, 'start': 10.0,
                'end': 10.0 + duration, 'tempo': 1.0}

    def events(self, scene, phrase_time=None):
        result = []

        def emit(owner, start, end, tags, shape, meaning):
            self.assertIs(owner, scene)
            result.append({'start': start, 'end': end, 'tags': tags,
                           'shape': shape, 'meaning': meaning})

        handled = packet.animation_events(scene, phrase_time, emit)
        return handled, result

    def test_unknown_scene_delegates_without_drawing_or_timing_access(self):
        drawing = Drawing()
        scene = {'kind': 'legacy-scene'}
        self.assertFalse(packet.draw_diagram(scene, drawing, drawing.put))
        self.assertEqual(drawing.geometry, [])
        self.assertEqual(self.events(scene), (False, []))

    def test_all_scene_geometry_stays_inside_the_teaching_area(self):
        for kind in CARD_COUNTS:
            with self.subTest(kind=kind):
                drawing = Drawing()
                self.assertTrue(packet.draw_diagram(self.scene(kind), drawing, drawing.put))
                self.assertGreater(len(drawing.geometry), 10)
                for points in drawing.geometry:
                    for x, y in zip(points[::2], points[1::2]):
                        self.assertTrue(90 <= x <= 1830, (kind, points))
                        self.assertTrue(285 <= y <= 835, (kind, points))

    def test_drawn_dimensions_and_labels_come_from_scene_data(self):
        scene = self.scene()
        scene['diagram'] = {
            'cards': [
                {'title': 'Payload', 'detail': '1,500 bytes'},
                {'title': 'Group / embed', 'detail': '4 bytes → 375 vectors'},
                {'title': 'Assemble', 'detail': '+ 3 learned positions\n378 × 256'},
                {'title': 'Encoder', 'detail': '4 Mamba blocks'},
                {'title': 'Classifier', 'detail': '2 logits'},
            ],
            'note': 'Evidence-bound packet encoder, custom fixture.',
            'labels': {'eyebrow': 'CUSTOM PACKET ENCODER'},
        }
        drawing = Drawing()
        packet.draw_diagram(scene, drawing, drawing.put)
        for card in scene['diagram']['cards']:
            self.assertIn(card['title'], drawing.text)
            self.assertIn(card['detail'], drawing.text)
        self.assertIn(scene['diagram']['note'], drawing.text)
        self.assertIn('CUSTOM PACKET ENCODER', drawing.text)
        self.assertNotRegex(' '.join(drawing.text), r'443|1,600|six category|Flow A')

    def test_missing_scientific_values_do_not_fall_back_to_flow_dimensions(self):
        drawing = Drawing()
        for kind in CARD_COUNTS:
            packet.draw_diagram(self.scene(kind), drawing, drawing.put)
        self.assertNotRegex(' '.join(drawing.text), r'443|1,600|six category|5 × 320|Flow A')

    def test_input_cards_reserve_space_for_two_supplied_detail_lines(self):
        scene = self.scene('packet-input')
        scene['diagram'] = {'cards': [
            {'title': title, 'detail': 'First supplied line\nSecond supplied line'}
            for title in ('CSV files', 'Payload', 'Metadata', 'Classifier')]}
        drawing = Drawing()
        self.assertTrue(packet.draw_diagram(scene, drawing, drawing.put))

    def test_partial_card_schema_is_rejected_before_drawing(self):
        scene = self.scene()
        scene['diagram'] = {'cards': [{'title': 'Misleading partial diagram'}]}
        drawing = Drawing()
        with self.assertRaisesRegex(ValueError, 'cards'):
            packet.draw_diagram(scene, drawing, drawing.put)
        self.assertEqual(drawing.geometry, [])

    def test_each_scene_has_explanatory_motion_within_finite_scene_bounds(self):
        for kind in CARD_COUNTS:
            for duration in (1 / 30, 0.3, 20, 200):
                with self.subTest(kind=kind, duration=duration):
                    handled, events = self.events(self.scene(kind, duration))
                    self.assertTrue(handled)
                    self.assertGreater(len(events), CARD_COUNTS[kind])
                    self.assertTrue(any('\\move(' in e['tags'] for e in events))
                    self.assertTrue(any('\\t(' in e['tags'] for e in events))
                    for item in events:
                        self.assertTrue(math.isfinite(item['start']))
                        self.assertTrue(math.isfinite(item['end']))
                        self.assertLessEqual(10, item['start'])
                        self.assertLess(item['start'], item['end'])
                        self.assertLessEqual(item['end'], 10 + duration)
                        self.assertIn('illustrative', item['meaning'].lower())

    def test_focus_highlights_honor_each_narration_anchor(self):
        for kind, count in CARD_COUNTS.items():
            with self.subTest(kind=kind):
                scene = self.scene(kind)
                scene['focus_phrases'] = [f'narration {i}' for i in range(count)]
                anchors = {phrase: 11 + i * 2 for i, phrase in enumerate(scene['focus_phrases'])}
                calls = []

                def phrase_time(owner, phrase):
                    self.assertIs(owner, scene)
                    calls.append(phrase)
                    return anchors[phrase]

                _, events = self.events(scene, phrase_time)
                highlights = [e for e in events if 'emphasis' in e['meaning']]
                self.assertEqual(calls, scene['focus_phrases'])
                self.assertEqual([e['start'] for e in highlights], list(anchors.values()))

    def test_invalid_focus_count_fails_before_emitting_partial_motion(self):
        scene = self.scene()
        scene['focus_phrases'] = ['one anchor']
        events = []
        with self.assertRaisesRegex(ValueError, 'focus'):
            packet.animation_events(scene, lambda *_: 11, lambda *args: events.append(args))
        self.assertEqual(events, [])

    def test_unresolvable_focus_phrase_is_not_replaced_by_fallback_time(self):
        scene = self.scene('repo-sync')
        scene['focus_phrases'] = ['source', 'missing phrase', 'client']
        events = []

        def phrase_time(owner, phrase):
            if phrase == 'missing phrase':
                raise ValueError('Animation phrase must identify one narration passage')
            return 12

        with self.assertRaisesRegex(ValueError, 'phrase'):
            packet.animation_events(scene, phrase_time, lambda *args: events.append(args))
        self.assertEqual(events, [])

    def test_nonfinite_or_out_of_scene_anchor_is_rejected_before_emission(self):
        scene = self.scene('repo-sync')
        scene['focus_phrases'] = ['source', 'gate', 'client']
        for value in (float('nan'), float('inf'), 9.99, 30, 31):
            with self.subTest(value=value):
                emitted = []
                with self.assertRaisesRegex(ValueError, 'anchor|focus'):
                    packet.animation_events(scene, lambda *_: value,
                                            lambda *args: emitted.append(args))
                self.assertEqual(emitted, [])

    def test_invalid_scene_interval_is_rejected(self):
        for start, end in ((10, 10), (10, 9), (float('nan'), 20),
                           (10, float('inf')), (-1, 10)):
            with self.subTest(start=start, end=end):
                scene = self.scene()
                scene.update(start=start, end=end)
                with self.assertRaisesRegex(ValueError, 'scene'):
                    self.events(scene)

    def test_motion_coordinates_and_clip_regions_stay_inside_teaching_area(self):
        for kind in CARD_COUNTS:
            _, events = self.events(self.scene(kind))
            for item in events:
                for command, values in re.findall(r'\\(pos|move|clip)\(([^)]+)\)', item['tags']):
                    coordinates = [float(value) for value in values.split(',')]
                    for x, y in zip(coordinates[::2], coordinates[1::2]):
                        self.assertTrue(90 <= x <= 1830, (kind, command, coordinates))
                        self.assertTrue(285 <= y <= 835, (kind, command, coordinates))

    def test_scene_data_is_unchanged_by_draw_and_animation(self):
        scene = self.scene('repo-sync')
        scene['diagram'] = {'cards': [{'title': str(i), 'detail': 'supplied'} for i in range(3)]}
        scene['focus_phrases'] = ['source', 'gate', 'client']
        original = copy.deepcopy(scene)
        drawing = Drawing()
        packet.draw_diagram(scene, drawing, drawing.put)
        self.events(scene, lambda *_: 12)
        self.assertEqual(scene, original)

    def test_input_motion_separates_metadata_from_the_model_path(self):
        _, events = self.events(self.scene('packet-input'))
        meanings = ' '.join(e['meaning'].lower() for e in events)
        self.assertIn('payload', meanings)
        self.assertIn('metadata', meanings)
        self.assertIn('audit', meanings)
        self.assertNotRegex(meanings, r'metadata (enters|to|into) (the )?(classifier|model)')

    def test_training_motion_explains_labels_loss_and_parameter_update(self):
        _, events = self.events(self.scene('packet-training'))
        meanings = ' '.join(e['meaning'].lower() for e in events)
        for concept in ('forward', 'label', 'loss', 'backward', 'gradient', 'update'):
            self.assertIn(concept, meanings)
        self.assertNotIn('accuracy rises', meanings)

    def test_split_motion_preserves_groups_without_inventing_flows(self):
        _, events = self.events(self.scene('packet-split'))
        meanings = ' '.join(e['meaning'].lower() for e in events)
        self.assertIn('duplicate', meanings)
        self.assertIn('train', meanings)
        self.assertIn('validation', meanings)
        self.assertIn('test', meanings)
        self.assertNotIn('flow', meanings)

    def test_repository_motion_depicts_the_same_code_through_export(self):
        _, events = self.events(self.scene('repo-sync'))
        meanings = ' '.join(e['meaning'].lower() for e in events)
        for concept in ('source', 'tests', 'export', 'client', 'same packet code'):
            self.assertIn(concept, meanings)


if __name__ == '__main__':
    unittest.main()
