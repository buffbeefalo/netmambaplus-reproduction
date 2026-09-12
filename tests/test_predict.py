import copy
import unittest

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


if __name__ == "__main__":
    unittest.main()
