"""Check recorded packet-display arithmetic and failure behavior."""

import importlib
import json
from pathlib import Path
import tempfile
import unittest


class PacketDemoTests(unittest.TestCase):
    def demo(self):
        try:
            return importlib.import_module('tools.render_packet_demo')
        except ModuleNotFoundError as error:
            if error.name != 'tools.render_packet_demo':
                raise
            self.fail('The packet-specific recorded demo is missing')

    def records(self):
        return [{'id': 'a' * 64, 'counts': [9, 1], 'logits': [2, 0]},
                {'id': 'b' * 64, 'counts': [0, 1], 'logits': [0, 2]}]

    def test_conflicting_labels_keep_both_counts_and_group_weighting(self):
        result = self.demo().source_view('cic', self.records())
        self.assertEqual(result['groups'], 2)
        self.assertEqual(result['rows'], 11)
        self.assertEqual(result['conflicting_groups'], 1)
        self.assertEqual(result['disagreement_groups'], 1)
        self.assertEqual(result['incorrect_rows'], 1)
        self.assertAlmostEqual(result['metrics']['group_weighted']['accuracy'], .95)
        self.assertAlmostEqual(result['metrics']['row_weighted']['accuracy'], 10 / 11)
        self.assertEqual(result['predictions'][0]['counts'], [9, 1])

    def test_tie_uses_the_same_benign_class_as_packet_inference(self):
        result = self.demo().source_view('unsw', [{'id': 'c' * 64, 'counts': [1, 0], 'logits': [0, 0]}])
        self.assertEqual(result['predictions'][0]['prediction'], 0)
        self.assertEqual(result['predictions'][0]['probability'], .5)

    def test_invalid_logits_and_duplicate_groups_are_rejected(self):
        module = self.demo()
        records = self.records()
        with self.assertRaises(ValueError):
            module.source_view('cic', records + records[:1])
        records[0]['logits'] = [float('nan'), 0]
        with self.assertRaises(ValueError):
            module.source_view('cic', records)

    def test_embedded_json_cannot_close_the_script_element(self):
        encoded = self.demo().script_json({'value': '</script><img src=x onerror=alert(1)>&'})
        self.assertNotIn('<', encoded)
        self.assertNotIn('>', encoded)
        self.assertEqual(json.loads(encoded)['value'], '</script><img src=x onerror=alert(1)>&')

    def test_existing_output_is_preserved_before_evidence_access(self):
        module = self.demo()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'existing'
            output.mkdir()
            (output / 'keep.txt').write_text('keep', encoding='utf-8')
            with self.assertRaises(FileExistsError):
                module.build(Path(directory) / 'missing-evidence', output)
            self.assertEqual((output / 'keep.txt').read_text(), 'keep')


if __name__ == '__main__':
    unittest.main()
