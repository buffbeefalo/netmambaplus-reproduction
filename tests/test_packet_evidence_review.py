"""Synthetic receipts test audit boundaries; they are not native training evidence."""

import copy
import gzip
import hashlib
import importlib.util
import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

import packet_data
import packet_study
from tools import review_packet_study as review


class EvidenceFixture:
    """Small fictional records exercise the public verifier without any model run."""
    def __init__(self, root):
        self.root = root
        self.arms = [{"name": name + "_" + initialization, "sources": sources,
                      "initialization": initialization}
                     for name, sources in (("cic", ["cic"]), ("unsw", ["unsw"]), ("joint", ["cic", "unsw"]))
                     for initialization in ("pretrained", "scratch")]
        self.protocol = {"kind": "netmambaplus_packet_study_v1", "purpose": "measured", "steps": 200,
                         "validation_interval": 100, "arms": self.arms}
        self.write("protocol.json", self.protocol)
        self.protocol_hash = self.ref("protocol.json")["sha256"]
        self.records = {}
        self.measured = {}
        support = {}
        for source in ("cic", "unsw"):
            benign = [1] + [0] * (len(packet_data.LABELS[source]) - 1)
            attack = [0, 1] + [0] * (len(packet_data.LABELS[source]) - 2)
            records = [{"id": "a" * 64, "counts": [1, 0], "subtypes": benign, "logits": [1, 0]},
                       {"id": "b" * 64, "counts": [0, 1], "subtypes": attack, "logits": [0, 1]}]
            self.records[source] = records
            self.measured[source] = self.metrics(source, records)
            support[source] = {"splits": {"test": {"selected_groups": 2, "selected_rows": 2,
                "selected_binary_counts": [1, 1],
                "selected_label_counts": {label: int(i < 2) for i, label in enumerate(packet_data.LABELS[source])},
                "selected_membership_sha256": hashlib.sha256(bytes.fromhex("a" * 64 + "b" * 64)).hexdigest()}}}
        self.write("manifest.json", {"sources": support})
        self.receipts, self.items = {}, []
        for arm in self.arms:
            name = arm["name"]
            checkpoint = {"path": name + "/private-checkpoint.pth", "sha256": "c" * 64,
                          "bytes": 1, "step": 100, "selection_score": 1.0}
            log = name + "/training.jsonl"
            self.write(log, "\n".join(json.dumps({"step": step, "loss": 1.0,
                       "unclipped_gradient_norm": 1.0}) for step in range(1, 201)) + "\n")
            receipt = {"status": "trained", "arm": arm, "steps": 200,
                "optimizer_step_range": [200, 200], "optimizer_parameter_states": 51,
                "selected_checkpoint": checkpoint,
                "validation_history": [{"step": step, "selection_score": 1.0,
                    "sources": {source: copy.deepcopy(self.measured[source]) for source in arm["sources"]}}
                    for step in (100, 200)],
                "training_log": self.ref(log), "initial_parameter_sha256": {"head.weight": "d" * 64},
                "group_presentations": {source: 10 for source in arm["sources"]},
                "distinct_training_groups_observed": {source: 2 for source in arm["sources"]},
                "training_batch_stream_sha256": "e" * 64}
            self.receipts[name] = receipt
            self.write(name + "/training-receipt.json", receipt)
            item = {"arm": arm, "selected_checkpoint": checkpoint,
                    "training_receipt": self.ref(name + "/training-receipt.json"), "tests": {}}
            for source in ("cic", "unsw"):
                path = name + "/test-" + source + ".jsonl.gz"
                self.write_predictions(path, self.records[source])
                item["tests"][source] = {"metrics": copy.deepcopy(self.measured[source]), "predictions": self.ref(path)}
            self.items.append(item)
        self.sync()

    def write(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value if isinstance(value, str) else json.dumps(value, sort_keys=True))

    def write_predictions(self, name, records):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(gzip.compress(("\n".join(json.dumps(record) for record in records) + "\n").encode(), mtime=0))

    def ref(self, name):
        path = self.root / name
        return {"path": name, "bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}

    def metrics(self, source, records):
        return packet_study.evaluate_records(records, original_labels=packet_data.LABELS[source],
                                             normal_label=packet_data.LABELS[source][0])

    def sync(self):
        for item in self.items:
            name = item["arm"]["name"]
            self.write(name + "/training-receipt.json", self.receipts[name])
            item["training_receipt"] = self.ref(name + "/training-receipt.json")
        self.write("frozen-checkpoints.json", {"protocol_sha256": self.protocol_hash,
            "selected_checkpoints": {item["arm"]["name"]: item["selected_checkpoint"] for item in self.items}})
        self.write("results.json", {"status": "completed", "protocol_sha256": self.protocol_hash,
            "data_manifest_sha256": self.ref("manifest.json")["sha256"], "results": self.items,
            "frozen_checkpoints": self.ref("frozen-checkpoints.json")})
        self.reindex()

    def reindex(self):
        names = sorted(path.relative_to(self.root).as_posix() for path in self.root.rglob("*")
                       if path.is_file() and path.name != "index.json")
        self.write("index.json", {"files": [self.ref(name) for name in names]})


class PacketEvidenceReviewTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.fixture = EvidenceFixture(self.root)

    def test_structurally_consistent_synthetic_receipts_exercise_all_prediction_sets(self):
        with patch('tools.review_packet_controls.verify', return_value={'status': 'fixture'}) as controls, \
                patch('tools.review_packet_inference.verify', return_value={'status': 'fixture'}) as inference:
            result = review.verify(self.root)
        controls.assert_called_once_with(self.root, independent=False)
        inference.assert_called_once_with(self.root)
        self.assertEqual(result["prediction_sets_recomputed"], 12)
        self.assertEqual(result["group_predictions_recomputed"], 24)
        self.assertFalse(result["independent_sklearn_metrics"])

    def test_complete_review_requires_control_evidence(self):
        with self.assertRaises(FileNotFoundError):
            review.verify(self.root)

    def test_complete_review_requires_inference_evidence(self):
        with patch('tools.review_packet_controls.verify', return_value={'status': 'fixture'}):
            with self.assertRaises(ValueError):
                review.verify(self.root)

    def test_changed_bytes_and_unlisted_files_are_rejected(self):
        (self.root / "protocol.json").write_text("{}")
        with self.assertRaisesRegex(ValueError, "fingerprint"):
            review.verify(self.root)
        self.fixture.write("protocol.json", self.fixture.protocol)
        (self.root / "unlisted.txt").write_text("Missing inventory entry\n")
        with self.assertRaisesRegex(ValueError, "inventory"):
            review.verify(self.root)

    def test_changed_metric_is_rejected_even_with_a_fresh_evidence_index(self):
        self.fixture.items[0]["tests"]["cic"]["metrics"]["row_weighted"]["accuracy"] = 0.5
        self.fixture.sync()
        with self.assertRaisesRegex(ValueError, "Numeric result differs"):
            review.verify(self.root)

    def test_prediction_ids_must_match_frozen_membership(self):
        item = self.fixture.items[0]["tests"]["cic"]
        records = copy.deepcopy(self.fixture.records["cic"])
        records[0]["id"] = "9" * 64
        path = item["predictions"]["path"]
        self.fixture.write_predictions(path, records)
        item["predictions"] = self.fixture.ref(path)
        self.fixture.sync()
        with self.assertRaisesRegex(ValueError, "membership"):
            review.verify(self.root)

    def test_test_truth_must_match_declared_support_not_only_rows_and_ids(self):
        item = self.fixture.items[0]["tests"]["cic"]
        records = copy.deepcopy(self.fixture.records["cic"])
        records[0]["counts"] = [0, 1]
        records[0]["subtypes"][0:2] = [0, 1]
        path = item["predictions"]["path"]
        self.fixture.write_predictions(path, records)
        item.update(predictions=self.fixture.ref(path), metrics=self.fixture.metrics("cic", records))
        self.fixture.sync()
        with self.assertRaisesRegex(ValueError, "support|label|truth|Numeric result differs"):
            review.verify(self.root)

    def test_original_attack_subtype_totals_cannot_change_with_binary_counts_unchanged(self):
        item = self.fixture.items[0]["tests"]["cic"]
        records = copy.deepcopy(self.fixture.records["cic"])
        records[1]["subtypes"][1:3] = [0, 1]
        path = item["predictions"]["path"]
        self.fixture.write_predictions(path, records)
        item.update(predictions=self.fixture.ref(path), metrics=self.fixture.metrics("cic", records))
        self.fixture.sync()
        with self.assertRaisesRegex(ValueError, "Numeric result differs"):
            review.verify(self.root)

    def test_selection_scores_must_follow_recorded_validation_metrics(self):
        first = self.fixture.items[0]
        receipt = self.fixture.receipts[first["arm"]["name"]]
        receipt["validation_history"][0]["selection_score"] = 0.8
        receipt["validation_history"][1]["selection_score"] = 0.7
        first["selected_checkpoint"]["selection_score"] = 0.8
        self.fixture.sync()
        with self.assertRaisesRegex(ValueError, "selection|score|Numeric result differs"):
            review.verify(self.root)

    def test_a_source_specific_arm_cannot_select_using_the_other_source(self):
        observation = self.fixture.receipts["cic_pretrained"]["validation_history"][0]
        observation["sources"]["unsw"] = observation["sources"].pop("cic")
        self.fixture.sync()
        with self.assertRaisesRegex(ValueError, "undeclared source"):
            review.verify(self.root)

    def test_later_checkpoint_cannot_win_an_exact_validation_tie(self):
        first = self.fixture.items[0]
        first["selected_checkpoint"]["step"] = 200
        self.fixture.sync()
        with self.assertRaisesRegex(ValueError, "earliest.best"):
            review.verify(self.root)

    def test_paired_arms_require_identical_batch_streams(self):
        self.fixture.receipts["cic_scratch"]["training_batch_stream_sha256"] = "f" * 64
        self.fixture.sync()
        with self.assertRaisesRegex(ValueError, "Result differs"):
            review.verify(self.root)


@unittest.skipUnless(importlib.util.find_spec("sklearn"), "Independent metric comparison requires optional scikit-learn")
class IndependentPacketMetricTests(unittest.TestCase):
    def setUp(self):
        self.records = [{"id": "a" * 64, "counts": [3, 1], "logits": [0.0, 2.0]},
                        {"id": "b" * 64, "counts": [0, 2], "logits": [2.0, 0.0]}]
        self.expected = {
            "row_weighted": {"confusion_matrix": [[0, 3], [2, 1]], "accuracy": 1 / 6,
                "balanced_accuracy": 1 / 6, "macro_f1": 1 / 7, "auroc": 1 / 6,
                "attack_average_precision": 5 / 12},
            "group_weighted": {"confusion_matrix": [[0, .75], [1, .25]], "accuracy": 1 / 8,
                "balanced_accuracy": 1 / 10, "macro_f1": 1 / 9, "auroc": 1 / 10,
                "attack_average_precision": 11 / 20},
        }

    def test_independent_library_agrees_with_hand_computed_conflicting_group_metrics(self):
        review.independent_metrics(self.records, self.expected)

    def test_independent_comparison_rejects_a_wrong_ranking_metric(self):
        self.expected["group_weighted"]["attack_average_precision"] = 0.5
        with self.assertRaisesRegex(ValueError, "average_precision"):
            review.independent_metrics(self.records, self.expected)


if __name__ == "__main__":
    unittest.main()
