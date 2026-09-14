import copy
import math
import unittest

import packet_study


class PacketMetricTests(unittest.TestCase):
    def setUp(self):
        self.records = [
            {'id': 'a' * 64, 'counts': [3, 1], 'logits': [0.0, 2.0]},
            {'id': 'b' * 64, 'counts': [0, 2], 'logits': [2.0, 0.0]},
        ]

    def test_mixed_label_groups_preserve_all_labels(self):
        result = packet_study.evaluate_records(self.records)
        self.assertEqual(result['groups'], 2)
        self.assertEqual(result['rows'], 6)
        self.assertEqual(result['row_weighted']['confusion_matrix'], [[0, 3], [2, 1]])
        self.assertAlmostEqual(result['row_weighted']['macro_f1'], 1 / 7)

    def test_group_weighting_prevents_duplicate_mass_from_counting_as_new_groups(self):
        result = packet_study.evaluate_records(self.records)
        self.assertEqual(result['group_weighted']['confusion_matrix'], [[0, .75], [1, .25]])
        self.assertAlmostEqual(result['group_weighted']['balanced_accuracy'], .1)
        self.assertAlmostEqual(result['group_weighted']['macro_f1'], 1 / 9)

    def test_duplicate_group_records_are_rejected(self):
        with self.assertRaises(ValueError):
            packet_study.evaluate_records(self.records + [self.records[0]])

    def test_empty_groups_are_rejected(self):
        self.records[0]['counts'] = [0, 0]
        with self.assertRaises(ValueError):
            packet_study.evaluate_records(self.records)

    def test_fractional_negative_or_boolean_counts_are_rejected(self):
        for counts in ([1.5, 1], [-1, 2], [True, 1]):
            with self.subTest(counts=counts), self.assertRaises(ValueError):
                packet_study.evaluate_records([{'id': 'a'*64, 'counts': counts, 'logits': [0,1]}])

    def test_nonfinite_or_wrong_sized_logits_are_rejected(self):
        for logits in ([0,math.nan], [0,math.inf], [0], [0,1,2], [False,1]):
            with self.subTest(logits=logits), self.assertRaises(ValueError):
                packet_study.evaluate_records([{'id':'a'*64,'counts':[1,1],'logits':logits}])

    def test_tie_uses_class_zero_like_native_argmax(self):
        result = packet_study.evaluate_records([{'id':'a'*64,'counts':[1,1],'logits':[0,0]}])
        self.assertEqual(result['row_weighted']['confusion_matrix'], [[1,0],[1,0]])

    def test_original_labels_must_reconcile_with_binary_counts(self):
        records = copy.deepcopy(self.records)
        records[0]['subtypes'] = [2,2]
        records[1]['subtypes'] = [0,2]
        with self.assertRaises(ValueError):
            packet_study.evaluate_records(records, original_labels=['normal','dos'], normal_label='normal')

    def test_original_label_slices_keep_conflicting_targets(self):
        records=copy.deepcopy(self.records)
        records[0]['subtypes']=[3,1]
        records[1]['subtypes']=[0,2]
        result=packet_study.evaluate_records(records, original_labels=['normal','dos'], normal_label='normal')
        self.assertEqual(result['original_labels']['normal']['rows'],3)
        self.assertEqual(result['original_labels']['normal']['correct'],0)
        self.assertEqual(result['original_labels']['dos']['correct'],1)

    def test_absent_class_metric_is_explicitly_undefined(self):
        result=packet_study.evaluate_records([{'id':'a'*64,'counts':[0,2],'logits':[0,1]}])
        self.assertIsNone(result['row_weighted']['balanced_accuracy'])
        self.assertIsNone(result['row_weighted']['benign_false_positive_rate'])

    def test_ranking_metrics_retain_conflicts_and_score_ties(self):
        result = packet_study.evaluate_records(self.records)
        self.assertAlmostEqual(result['row_weighted']['auroc'], 1 / 6)
        self.assertAlmostEqual(result['row_weighted']['attack_average_precision'], 5 / 12)
        self.assertAlmostEqual(result['group_weighted']['auroc'], .1)
        tied = copy.deepcopy(self.records)
        tied[1]['logits'] = tied[0]['logits']
        result = packet_study.evaluate_records(tied)
        self.assertAlmostEqual(result['row_weighted']['auroc'], .5)
        self.assertAlmostEqual(result['row_weighted']['attack_average_precision'], .5)

    def test_conflicting_slice_is_explicit(self):
        result = packet_study.evaluate_records(self.records)
        self.assertEqual(result['conflicting_slice']['rows'], 4)
        self.assertEqual(result['conflicting_slice']['row_weighted']['confusion_matrix'], [[0,3],[0,1]])


if __name__ == '__main__':
    unittest.main()
