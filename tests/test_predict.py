import copy
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

try:
    import predict
except ModuleNotFoundError:
    predict = None


class UnlabeledInputChecks(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(predict, "Unlabeled inference command is missing")

    def test_native_adapter_preserves_features_and_does_not_mutate_inputs(self):
        original = [{"data": ["1 2 3"], "sizes": "64", "intervals": "0", "label": 99, "name": "untrusted"}]
        before = copy.deepcopy(original)
        adapted = predict.adapt_unlabeled(original, {"first": 0, "second": 1})
        self.assertEqual(original, before)
        self.assertEqual(adapted[0]["data"], before[0]["data"])
        self.assertEqual(adapted[0]["sizes"], before[0]["sizes"])
        self.assertEqual(adapted[0]["intervals"], before[0]["intervals"])
        self.assertEqual((adapted[0]["label"], adapted[0]["name"]), (0, "first"))

    def test_single_object_or_empty_list_is_not_silently_reinterpreted(self):
        for invalid in ({"data": []}, [], [None]):
            with self.assertRaises(ValueError):
                predict.adapt_unlabeled(invalid, {"first": 0})

    def test_class_mapping_must_have_a_zero_index(self):
        with self.assertRaises(ValueError):
            predict.adapt_unlabeled([{"data": []}], {"wrong": 1})

    def test_formatted_predictions_retain_raw_outputs_when_temperature_changes(self):
        format_rows = getattr(predict, "format_predictions", None)
        self.assertTrue(callable(format_rows), "Prediction formatting must support optional calibration")
        logits = [[2.0, 0.0], [0.0, 2.0], [1.0, 1.0]]
        indices = [0, 1, 1]
        mapping = {"first": 0, "second": 1}
        raw = format_rows(logits, indices, mapping, expected_rows=3)
        scaled = format_rows(logits, indices, mapping, expected_rows=3,
                             temperature=2.0, threshold=0.8)
        self.assertEqual([row['row'] for row in scaled], [0, 1, 2])
        self.assertEqual([row['prediction'] for row in scaled], indices)
        for original, calibrated in zip(raw, scaled):
            self.assertEqual(original, {key: calibrated[key] for key in original})
            self.assertAlmostEqual(sum(calibrated['calibrated_scores']), 1.0)
        self.assertEqual([row['decision'] for row in scaled], ['defer'] * 3)
        self.assertAlmostEqual(raw[0]['scores'][0], 0.8807970779778823)
        self.assertAlmostEqual(scaled[0]['calibrated_scores'][0], 0.7310585786300049)

    def test_prediction_formatting_rejects_lost_rows_and_invalid_model_outputs(self):
        format_rows = getattr(predict, "format_predictions", None)
        self.assertTrue(callable(format_rows), "Prediction formatting must check row alignment")
        for logits, indices, count in [([[1., 0.]], [0], 2),
                                        ([[1., 0.]], [], 1),
                                        ([[1., float('nan')]], [0], 1),
                                        ([[1., 0., 2.]], [0], 1),
                                        ([[1., 0.]], [1], 1)]:
            with self.subTest(logits=logits, indices=indices, count=count), self.assertRaises(ValueError):
                format_rows(logits, indices, {"a": 0, "b": 1}, expected_rows=count)

    def test_ground_truth_never_reaches_forward(self):
        forward_unlabeled = getattr(predict, "forward_without_targets", None)
        self.assertTrue(callable(forward_unlabeled), "Native prediction must discard targets before forward")
        features = {"bytes": object(), "sizes": object(), "intervals": object(), "targets": object()}
        before = dict(features)
        def process(batch, device):
            self.assertEqual((batch, device), ("batch", "cuda"))
            return features
        def forward(model, inputs):
            self.assertNotIn("targets", inputs)
            self.assertIs(inputs['bytes'], features['bytes'])
            self.assertEqual(model, "model")
            return {"logits": "checked"}
        self.assertEqual(forward_unlabeled(process, forward, "model", "batch", "cuda"), {"logits": "checked"})
        self.assertEqual(features, before)

    def test_threshold_without_calibration_is_rejected_before_reading_inputs(self):
        with patch('predict.repro.read_document') as read, contextlib.redirect_stderr(io.StringIO()):
            try:
                result = predict.main(['--flows', 'absent.json', '--checkpoint', 'absent.pth',
                                       '--output', 'absent-output', '--abstain-threshold', '0.9'])
            except SystemExit:
                self.fail('The threshold option is not implemented')
        self.assertEqual(result, 1)
        read.assert_not_called()

    def test_incompatible_calibrator_is_rejected_before_loading_cuda_runtime(self):
        try:
            from test_calibration import artifact_fixture, manifest_fixture
        except ImportError:
            from tests.test_calibration import artifact_fixture, manifest_fixture
        import calibration
        manifest = manifest_fixture()
        artifact = artifact_fixture(calibration.make_binding(manifest))
        artifact['binding']['checkpoint_sha256'] = 'e' * 64
        manifest['checkpoint_provenance'] = {'class_order': 'hash_bound'}
        prepared = {'args': SimpleNamespace(upstream='unused'), 'native': SimpleNamespace(), 'manifest': manifest}
        with tempfile.TemporaryDirectory() as directory:
            artifact_path = Path(directory) / 'calibration.json'
            artifact_path.write_text(json.dumps(artifact), encoding='utf-8')
            with patch('predict.evaluate.load_runtime') as runtime, self.assertRaises(ValueError):
                predict.run_prediction(prepared, {}, Path('unused'), [], calibration_path=artifact_path)
            runtime.assert_not_called()


if __name__ == "__main__":
    unittest.main()
