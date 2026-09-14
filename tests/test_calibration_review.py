import copy
import json
import math
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

try:
    from tools import review_calibration
except ImportError:
    review_calibration = None


class PairedCalibrationReviewTests(unittest.TestCase):
    def test_paired_review_preserves_class_and_reports_both_metrics(self):
        self.assertIsNotNone(review_calibration, 'The calibration study needs a reproducible reviewer')
        import calibration
        import predict
        mapping = {'first': 0, 'second': 1}
        rows = predict.format_predictions([[2., 0.], [0., 2.]], [0, 1], mapping,
                                          expected_rows=2, temperature=2., threshold=0.9)
        current = {'class_mapping': mapping, 'predictions': rows}
        truth = {'class_mapping': mapping, 'predictions': [
            {'row': 0, 'label': 0, 'prediction': 0, 'logits': [2., 0.]},
            {'row': 1, 'label': 0, 'prediction': 1, 'logits': [0., 2.]}]}
        result = review_calibration.paired_metrics(current, truth, 2., 0.9, 2)
        self.assertEqual(result['raw']['correct'], result['calibrated']['correct'])
        self.assertEqual(result['class_disagreements_with_historical'], 0)
        self.assertEqual(result['calibrated']['accepted'], 0)
        self.assertIsNone(result['calibrated']['accepted_error_rate'])
        self.assertLess(result['delta_calibrated_minus_raw']['nll'], 0)
        self.assertEqual(result['calibrated'], calibration.classification_metrics(
            [[2., 0.], [0., 2.]], [0, 0], 2., 0.9, predictions=[0, 1]))

        for mutation in ('order', 'dropped_row', 'score', 'policy', 'class_mapping'):
            bad = copy.deepcopy(current)
            if mutation == 'order': bad['predictions'].reverse()
            elif mutation == 'dropped_row': bad['predictions'].pop()
            elif mutation == 'score': bad['predictions'][0]['calibrated_scores'][0] = 0.99
            elif mutation == 'policy': bad['predictions'][0]['decision'] = 'accept'
            else: bad['class_mapping'] = {'second': 0, 'first': 1}
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                review_calibration.paired_metrics(bad, truth, 2., 0.9, 2)

        for mutation in ('extra_class', 'nonfinite_history', 'wrong_class_name', 'invalid_history_prediction'):
            bad, bad_truth = copy.deepcopy(current), copy.deepcopy(truth)
            if mutation == 'extra_class':
                bad['class_mapping']['third'] = bad_truth['class_mapping']['third'] = 2
            elif mutation == 'nonfinite_history':
                bad_truth['predictions'][0]['logits'][1] = float('nan')
            elif mutation == 'wrong_class_name':
                bad['predictions'][0]['class_name'] = 'wrong category'
            else:
                bad_truth['predictions'][0]['prediction'] = True
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                review_calibration.paired_metrics(bad, bad_truth, 2., 0.9, 2)


class CompleteCalibrationReviewTests(unittest.TestCase):
    """Tiny file-backed three-seed records; no raw flows, Torch, or GPU fixtures."""

    def setUp(self):
        import calibration
        import predict
        try:
            from test_calibration import artifact_fixture, manifest_fixture
        except ImportError:
            from tests.test_calibration import artifact_fixture, manifest_fixture
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.evidence = self.root / 'docs/customer/evidence/calibration'
        self.write('protocol.json', {
            'schema_version': 1, 'protocol_frozen_before_scaled_test_evaluation': True,
            'frozen_at': '2026-01-01T00:00:00+00:00',
            'seeds': [{'seed': seed, 'checkpoint_sha256': f'{seed + 10:064x}'} for seed in range(3)],
            'fit': {'sha256': '1' * 64, 'rows': 5},
            'evaluation': {'sha256': '5' * 64, 'rows': 2},
            'policy': {'threshold': 0.9}, 'limitations': ['Synthetic test records only.']})
        validation_logits, validation_labels = [[2., 0.]] * 5, [0, 0, 0, 0, 1]
        temperature = 2 / math.log(4)  # Analytic optimum: four correct margins out of five.
        for seed in range(3):
            fit = manifest_fixture()
            fit['input_checkpoint']['sha256'] = f'{seed + 10:064x}'
            inference = copy.deepcopy(fit)
            artifact = artifact_fixture(calibration.make_binding(fit))
            artifact['temperature'] = artifact['fit']['temperature'] = temperature
            artifact['fit'].update(
                logits_sha256=review_calibration.observation_hash(validation_logits),
                labels_sha256=review_calibration.observation_hash(validation_labels),
                raw_metrics=calibration.classification_metrics(validation_logits, validation_labels),
                calibrated_metrics=calibration.classification_metrics(validation_logits, validation_labels,
                                                                       temperature, 0.9))
            artifact_path = self.write(f'seed{seed}/calibration.json', artifact)
            artifact_hash = review_calibration.repro.sha256_file(artifact_path)
            predictions = {'class_mapping': fit['class_mapping'],
                'checkpoint_sha256': fit['input_checkpoint']['sha256'],
                'source': {'sha256': '5' * 64},
                'predictions': predict.format_predictions([[2., 0.], [0., 2.]], [0, 1],
                    fit['class_mapping'], expected_rows=2, temperature=temperature, threshold=0.9)}
            prediction_path = self.write(f'seed{seed}/predictions.json', predictions)
            fit.update(status='succeeded', created_at='2026-01-01T00:01:00+00:00',
                updated_at='2026-01-01T00:02:00+00:00',
                calibration_artifact={'sha256': artifact_hash},
                input_files={'data-valid.json': {'sha256': '1' * 64}},
                validation_observations={'logits': validation_logits, 'labels': validation_labels})
            inference.update(status='succeeded', created_at='2026-01-01T00:03:00+00:00',
                updated_at='2026-01-01T00:04:00+00:00',
                metrics_file={'sha256': review_calibration.repro.sha256_file(prediction_path)},
                calibration={'file': {'sha256': artifact_hash}, 'abstain_threshold': 0.9})
            self.write(f'seed{seed}/fit-manifest.json', fit)
            self.write(f'seed{seed}/prediction-manifest.json', inference)
            self.write(f'../seed{seed}/replay/predictions.json', {
                'class_mapping': fit['class_mapping'], 'test_sha256': '5' * 64,
                'checkpoint_sha256': fit['input_checkpoint']['sha256'], 'predictions': [
                    {'row': 0, 'label': 0, 'prediction': 0, 'logits': [2., 0.]},
                    {'row': 1, 'label': seed % 2, 'prediction': 1, 'logits': [0., 2.]}]})
        # Only source-reference location changes; all reads, hashes and numerical checks are real.
        self.tool_path = self.root / 'tools/review_calibration.py'
        self.tool_path.parent.mkdir(parents=True)
        self.tool_path.write_bytes(Path(review_calibration.__file__).read_bytes())
        (self.root / 'calibration.py').write_bytes(Path(calibration.__file__).read_bytes())

    def write(self, name, document):
        path = self.evidence / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(document, allow_nan=False), encoding='utf-8')
        return path

    def read(self, name):
        return json.loads((self.evidence / name).read_text(encoding='utf-8'))

    def review(self):
        with patch.object(review_calibration, '__file__', str(self.tool_path)):
            return review_calibration.review(self.evidence, root=self.root)

    def rebind_predictions(self, seed=0):
        name = f'seed{seed}/prediction-manifest.json'
        manifest = self.read(name)
        manifest['metrics_file']['sha256'] = review_calibration.repro.sha256_file(
            self.evidence / f'seed{seed}/predictions.json')
        self.write(name, manifest)

    def test_complete_three_seed_fixture_has_hand_checked_aggregate(self):
        result = self.review()
        self.assertEqual([seed['seed'] for seed in result['seeds']], [0, 1, 2])
        self.assertAlmostEqual(result['aggregate']['raw']['accuracy']['mean'], 2 / 3)
        self.assertAlmostEqual(result['aggregate']['raw']['accuracy']['sample_standard_deviation'], math.sqrt(1 / 12))
        self.assertAlmostEqual(result['aggregate']['raw']['nll']['mean'], math.log1p(math.exp(-2)) + 2 / 3)

    def test_timezone_offsets_are_compared_as_instants(self):
        manifest = self.read('seed0/prediction-manifest.json')
        manifest['created_at'] = '2026-01-01T03:03:00+03:00'
        self.write('seed0/prediction-manifest.json', manifest)
        self.assertEqual(len(self.review()['seeds']), 3)

    def test_rejects_fit_started_after_test_with_backwards_end(self):
        manifest = self.read('seed0/fit-manifest.json')
        manifest['created_at'] = '2026-01-01T00:05:00+00:00'
        self.write('seed0/fit-manifest.json', manifest)
        with self.assertRaises(ValueError):
            self.review()

    def test_rejects_inference_finished_before_it_started(self):
        manifest = self.read('seed0/prediction-manifest.json')
        manifest['updated_at'] = '2026-01-01T00:02:00+00:00'
        self.write('seed0/prediction-manifest.json', manifest)
        with self.assertRaises(ValueError):
            self.review()

    def test_rejects_timezone_naive_receipts_even_when_all_use_same_clock(self):
        protocol = self.read('protocol.json')
        protocol['frozen_at'] = protocol['frozen_at'].removesuffix('+00:00')
        self.write('protocol.json', protocol)
        for seed in range(3):
            for kind in ('fit-manifest', 'prediction-manifest'):
                name = f'seed{seed}/{kind}.json'
                manifest = self.read(name)
                for key in ('created_at', 'updated_at'):
                    manifest[key] = manifest[key].removesuffix('+00:00')
                self.write(name, manifest)
        with self.assertRaises(ValueError):
            self.review()

    def test_rejects_fit_that_finishes_after_first_test_starts(self):
        manifest = self.read('seed2/fit-manifest.json')
        manifest['updated_at'] = '2026-01-01T00:04:00+00:00'
        self.write('seed2/fit-manifest.json', manifest)
        with self.assertRaises(ValueError):
            self.review()

    def test_rejects_prediction_checkpoint_conflicting_with_its_manifest(self):
        document = self.read('seed0/predictions.json')
        document['checkpoint_sha256'] = 'e' * 64
        self.write('seed0/predictions.json', document)
        self.rebind_predictions()
        with self.assertRaises(ValueError):
            self.review()

    def test_rejects_paired_class_names_conflicting_with_bound_manifest(self):
        mapping = {'renamed-first': 0, 'renamed-second': 1}
        for name in ('seed0/predictions.json', '../seed0/replay/predictions.json'):
            document = self.read(name)
            document['class_mapping'] = mapping
            if name.startswith('seed0/'):
                for row in document['predictions']:
                    row['class_name'] = ('renamed-first', 'renamed-second')[row['prediction']]
            self.write(name, document)
        self.rebind_predictions()
        with self.assertRaises(ValueError):
            self.review()

    def test_rejects_prediction_file_with_stale_recorded_hash(self):
        document = self.read('seed0/predictions.json')
        document['note'] = 'File changed after the receipt.'
        self.write('seed0/predictions.json', document)
        with self.assertRaises(ValueError):
            self.review()

    def test_rejects_changed_validation_observations(self):
        manifest = self.read('seed0/fit-manifest.json')
        manifest['validation_observations']['labels'][0] = 1
        self.write('seed0/fit-manifest.json', manifest)
        with self.assertRaises(ValueError):
            self.review()


if __name__ == '__main__':
    unittest.main()
