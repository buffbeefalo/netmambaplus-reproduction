"""A packet lesson must load packet facts without importing historical flow facts."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from narrate_course_video import canonical, load_source
from build_course_video import publication, render_scene


class PacketVideoSourceTests(unittest.TestCase):
    def fixture(self, root):
        (root / 'packet.json').write_text(json.dumps({'groups': 12}))
        facts = {'groups': {'file': 'packet.json', 'pointer': '/groups',
                             'expected': 12, 'format': 'integer'}}
        source = {'workflow': 'two-csv-packet-v1',
                  'course': {'facts': facts, 'references': {}, 'demo': {}},
                  'fact_bindings_sha256': hashlib.sha256(canonical(facts)).hexdigest(),
                  'title': 'Packet groups: {{groups}}'}
        path = root / 'lesson.json'
        path.write_text(json.dumps(source))
        return source, path

    def test_packet_lesson_resolves_without_a_historical_course_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, path = self.fixture(root)
            self.assertEqual(load_source(path, root=root)['title'], 'Packet groups: 12')
            self.assertEqual(json.loads(path.read_text()), source)

    def test_changed_primary_packet_fact_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, path = self.fixture(root)
            (root / 'packet.json').write_text('{"groups": 13}')
            with self.assertRaisesRegex(ValueError, 'Evidence disagreement'):
                load_source(path, root=root)

    def test_changed_fact_contract_is_rejected_even_if_primary_value_matches(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, path = self.fixture(root)
            source['course']['facts']['groups']['format'] = 'text'
            path.write_text(json.dumps(source))
            with self.assertRaisesRegex(ValueError, 'fact bindings'):
                load_source(path, root=root)

    def test_unknown_workflow_does_not_fall_back_to_flow_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, path = self.fixture(root)
            source['workflow'] = 'misspelled-packet-workflow'
            path.write_text(json.dumps(source))
            with self.assertRaisesRegex(ValueError, 'Unsupported video workflow'):
                load_source(path, root=root)

    def test_publication_preserves_the_selected_lesson_summary(self):
        source = {'summary': 'Packet balanced accuracy; different task from paper flows.'}
        self.assertEqual(publication(source).get('summary'), source['summary'])
        self.assertNotIn('summary', publication({}))
        for invalid in ('', '  ', None, 42):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                publication({'summary': invalid})

    @unittest.skipUnless(importlib.util.find_spec('PIL') and
                         Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf').exists(),
                         'Actual image rendering needs the document environment and fonts')
    def test_scientific_table_note_is_drawn_and_cannot_overflow_silently(self):
        scene = {'id': 'result-fixture', 'kind': 'table', 'title': 'Result scope',
                 'chapter': 1, 'chapter_count': 12, 'start': 0,
                 'columns': ['Population', 'Observed failures'],
                 'rows': [['Fixture only', 'Two']], 'bullets': ['Controlled example'],
                 'references': ['fixture']}
        with tempfile.TemporaryDirectory() as directory:
            a, b = Path(directory) / 'a.png', Path(directory) / 'b.png'
            render_scene(scene, a, {}, {})
            scene['table_note'] = 'Scores and classes are separate comparisons.'
            render_scene(scene, b, {}, {})
            self.assertNotEqual(a.read_bytes(), b.read_bytes())
            scene['table_note'] = 'Too much supporting text ' * 300
            with self.assertRaisesRegex(ValueError, 'overflow'):
                render_scene(scene, b, {}, {})

    @unittest.skipUnless(importlib.util.find_spec('PIL') and
                         Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf').exists(),
                         'Actual image rendering needs the document environment and fonts')
    def test_capture_crop_preserves_source_identity_and_rejects_outside_pixels(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            capture = root / 'capture.png'
            Image.new('RGB', (40, 40), 'white').save(capture)
            identity = hashlib.sha256(capture.read_bytes()).hexdigest()
            scene = {'id': 'capture-fixture', 'kind': 'image', 'title': 'Actual capture',
                     'chapter': 1, 'chapter_count': 12, 'start': 0,
                     'bullets': ['Crop retains original pixels'], 'references': ['fixture'],
                     'image': 'capture.png', 'image_sha256': identity,
                     'image_crop': [0, 0, 40, 20]}
            render_scene(scene, root / 'frame.png', {}, {}, root=root)
            self.assertEqual(hashlib.sha256(capture.read_bytes()).hexdigest(), identity)
            scene['image_crop'] = [0, 0, 41, 20]
            with self.assertRaisesRegex(ValueError, 'exceeds the original'):
                render_scene(scene, root / 'frame.png', {}, {}, root=root)


if __name__ == '__main__':
    unittest.main()
