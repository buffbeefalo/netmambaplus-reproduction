import json
import math
import unittest

try:
    import replay
except ModuleNotFoundError:
    replay = None


class ReplayChecks(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(replay, "The measured replay implementation is missing")

    def test_metrics_keep_confusion_orientation_and_macro_weighted_distinct(self):
        result = replay.metrics_from_predictions([0, 0, 0, 0, 1, 1, 2],
                                                 [0, 0, 0, 1, 1, 2, 0], 3)
        self.assertEqual(result["confusion_matrix"], [[3, 1, 0], [0, 1, 1], [1, 0, 0]])
        self.assertEqual(result["support"], [4, 2, 1])
        self.assertAlmostEqual(result["accuracy"], 4/7)
        self.assertAlmostEqual(result["weighted_f1"], 4/7)
        self.assertAlmostEqual(result["macro_f1"], 5/12)

    def test_absent_classes_and_no_predictions_have_explicit_zero_scores(self):
        result = replay.metrics_from_predictions([0, 0], [1, 1], 3)
        self.assertEqual(result["support"], [2, 0, 0])
        self.assertEqual(result["f1_per_class"], [0, 0, 0])
        self.assertEqual(result["macro_f1"], 0)

    def test_bad_prediction_inventory_is_rejected(self):
        for labels, predictions in [([], []), ([0], []), ([0], [2]), ([True], [0]), ([-1], [0])]:
            with self.subTest(labels=labels, predictions=predictions):
                with self.assertRaises(ValueError):
                    replay.metrics_from_predictions(labels, predictions, 2)

    def test_softmax_is_finite_and_shift_invariant(self):
        left = replay.probabilities([1000, 1001, 999])
        right = replay.probabilities([0, 1, -1])
        self.assertAlmostEqual(sum(left), 1)
        for a, b in zip(left, right):
            self.assertAlmostEqual(a, b)
        with self.assertRaises(ValueError):
            replay.probabilities([0, float("nan")])

    def test_html_embeds_results_without_executable_class_names(self):
        hostile = '</script><script>alert("class name")</script>'
        page = replay.render_html({"class_mapping": {hostile: 0}, "predictions": []})
        self.assertNotIn(hostile, page)
        self.assertIn("Recorded inference replay", page)
        self.assertIn("not live packet capture", page)
        self.assertIn("\\u003c/script", page)


if __name__ == "__main__":
    unittest.main()
