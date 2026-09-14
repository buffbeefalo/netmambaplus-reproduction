"""Offline control evidence must establish more than matching file hashes."""

import gzip
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import packet_data
import packet_study as study
from tools import packet_controls as controls


class ControlEvidenceReviewTests(unittest.TestCase):
    def setUp(self):
        from tools import review_packet_controls
        self.review = review_packet_controls
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.control_root = self.root / "controls"
        (self.control_root / "models").mkdir(parents=True)
        (self.control_root / "evaluation").mkdir()
        self.records = {}
        sources = {}
        for source, identity, train_groups in (("cic", "a" * 64, 2), ("unsw", "b" * 64, 1)):
            labels = packet_data.LABELS[source]
            subtype_counts = [3, 1] + [0] * (len(labels) - 2)
            self.records[source] = {"id": identity, "counts": [3, 1], "subtypes": subtype_counts}
            sources[source] = {"sha256": ("c" if source == "cic" else "d") * 64,
                "splits": {"train": {"selected_groups": train_groups}, "test": {
                    "selected_groups": 1, "selected_rows": 4, "selected_binary_counts": [3, 1],
                    "selected_label_counts": dict(zip(labels, subtype_counts)),
                    "selected_membership_sha256": hashlib.sha256(bytes.fromhex(identity)).hexdigest()}}}
        manifest = {"labels": packet_data.LABELS, "sources": sources}
        study.write_json(self.root / "manifest.json", manifest)
        code = {name: "e" * 64 for name in controls.CODE_FILES}
        code["tools/packet_controls.py"] = study.sha256(controls.__file__)
        protocol = {"data_manifest_sha256": study.sha256(self.root / "manifest.json"),
                    "source_sha256": {source: sources[source]["sha256"] for source in sources},
                    "code_sha256": {name: value for name, value in code.items() if name != "tools/packet_controls.py"},
                    "controls": {"C": 1, "solver": "lbfgs", "max_iter": 1000, "tol": 1e-4}}
        study.write_json(self.root / "protocol.json", protocol)
        self.binding = {"data_manifest_sha256": protocol["data_manifest_sha256"],
                        "source_sha256": protocol["source_sha256"], "code_sha256": code,
                        "protocol_sha256": study.sha256(self.root / "protocol.json")}
        models, convergence, results = {}, {}, []
        for arm, fitting_sources in controls.ARMS.items():
            groups = {source: sources[source]["splits"]["train"]["selected_groups"] for source in fitting_sources}
            total = sum(groups.values())
            for kind in controls.KINDS:
                name = f"{arm}_{kind}"
                names = ([] if kind == "majority" else list(controls.METADATA_FEATURES)
                         if kind == "metadata_linear" else [f"byte_fraction_{index}" for index in range(256)])
                model = {"schema_version": 1, "name": name, "kind": kind,
                    "training_sources": fitting_sources, "classes": [0, 1], "binding": self.binding,
                    "training_groups": groups, "source_total_weight": {source: total / len(groups) for source in groups},
                    "training_class_mass": [.75 * total, .25 * total], "feature_names": names,
                    "coef": [0.] * len(names), "intercept": -1. if kind == "majority" else .25,
                    "settings": {} if kind == "majority" else controls.LOGISTIC_SETTINGS,
                    "scaler": None if kind == "majority" else {"mean": [0.] * len(names),
                        "var": [0.] * len(names), "scale": [1.] * len(names), "n_samples_seen": total},
                    "convergence": {"converged": True, "n_iter": [] if kind == "majority" else [1], "warnings": []}}
                model_path = self.control_root / "models" / f"{name}.json"
                study.write_json(model_path, model)
                models[name] = study.artifact(self.control_root, model_path)
                convergence[name] = model["convergence"]
                tests = {}
                for source in controls.SOURCES:
                    record = {**self.records[source], "logits": [0., model["intercept"]]}
                    path = self.control_root / "evaluation" / f"{name}-test-{source}.jsonl.gz"
                    self.write_records(path, [record])
                    tests[source] = {"predictions": study.artifact(self.control_root, path),
                        "metrics": study.evaluate_records([record], original_labels=packet_data.LABELS[source],
                                                           normal_label=packet_data.LABELS[source][0])}
                results.append({"name": name, "kind": kind, "training_sources": fitting_sources,
                                "model": models[name], "convergence": model["convergence"], "tests": tests})
        frozen = {"schema_version": 1, "kind": "netmambaplus_packet_controls_v1", "status": "frozen", "fit_only": True,
                  **self.binding, "models": models, "convergence": convergence,
                  "training_groups": {source: sources[source]["splits"]["train"]["selected_groups"] for source in sources},
                  "feature_contract": controls.FEATURE_CONTRACT}
        study.write_json(self.control_root / "frozen-controls.json", frozen)
        report = {"schema_version": 1, "status": "completed", **self.binding,
                  "frozen_controls": study.artifact(self.control_root, self.control_root / "frozen-controls.json"),
                  "feature_contract": controls.FEATURE_CONTRACT, "results": results}
        study.write_json(self.control_root / "evaluation/results.json", report)

    def write_records(self, path, records):
        with gzip.open(path, "wt") as stream:
            for record in records:
                stream.write(json.dumps(record) + "\n")

    def replace(self, path, document):
        path.write_text(json.dumps(document, allow_nan=False), encoding="utf-8")

    def change_prediction(self, change, model_index=0):
        path = self.control_root / "evaluation/results.json"
        report = study.read_json(path)
        descriptor = report["results"][model_index]["tests"]["cic"]["predictions"]
        records_path = self.control_root / descriptor["path"]
        records = list(study.prediction_records(records_path))
        change(records[0])
        self.write_records(records_path, records)
        report["results"][model_index]["tests"]["cic"]["predictions"] = study.artifact(self.control_root, records_path)
        self.replace(path, report)

    def change_model(self, name, change):
        model_path = self.control_root / "models" / f"{name}.json"
        model = study.read_json(model_path)
        change(model)
        self.replace(model_path, model)
        descriptor = study.artifact(self.control_root, model_path)
        frozen_path = self.control_root / "frozen-controls.json"
        frozen = study.read_json(frozen_path)
        frozen["models"][name] = descriptor
        frozen["convergence"][name] = model["convergence"]
        self.replace(frozen_path, frozen)
        report_path = self.control_root / "evaluation/results.json"
        report = study.read_json(report_path)
        for result in report["results"]:
            if result["name"] == name:
                result["model"] = descriptor
                result["convergence"] = model["convergence"]
        report["frozen_controls"] = study.artifact(self.control_root, frozen_path)
        self.replace(report_path, report)

    def test_complete_control_evidence_verifies_without_ml_packages(self):
        result = self.review.verify(self.root)
        self.assertEqual(result["status"], "verified")
        self.assertEqual(result["models"], 9)
        self.assertEqual(result["test_sets"], 18)

    def test_updated_hash_does_not_hide_changed_truth(self):
        self.change_prediction(lambda record: record.update(subtypes=[2, 2] + record["subtypes"][2:]))
        with self.assertRaises(ValueError):
            self.review.verify(self.root)

    def test_updated_hash_does_not_hide_changed_predictions_or_metrics(self):
        self.change_prediction(lambda record: record.update(logits=[0., -3.]), model_index=1)
        with self.assertRaises(ValueError):
            self.review.verify(self.root)

    def test_reported_metrics_are_recomputed(self):
        path = self.control_root / "evaluation/results.json"
        report = study.read_json(path)
        report["results"][0]["tests"]["cic"]["metrics"]["row_weighted"]["accuracy"] = .123
        self.replace(path, report)
        with self.assertRaisesRegex(ValueError, "metrics"):
            self.review.verify(self.root)

    def test_frozen_source_weights_must_match_selected_training_groups(self):
        self.change_model("joint_metadata_linear", lambda model: model["source_total_weight"].update(unsw=1.))
        with self.assertRaisesRegex(ValueError, "source weight"):
            self.review.verify(self.root)

    def test_nonconvergence_remains_visible_in_verified_summary(self):
        self.change_model("joint_metadata_linear", lambda model: model.update(convergence={
            "converged": False, "n_iter": [1000], "warnings": [
                {"category": "ConvergenceWarning", "message": "iteration limit reached"}]}))
        result = self.review.verify(self.root)
        self.assertEqual(result["status"], "verified_with_convergence_warnings")
        self.assertFalse(result["convergence"]["all_converged"])
        self.assertEqual(result["convergence"]["warning_count"], 1)

    def test_independent_checker_failure_is_not_silently_ignored(self):
        from tools import review_packet_study
        with patch.object(review_packet_study, "independent_metrics",
                          side_effect=ValueError("independent arithmetic rejected evidence")):
            with self.assertRaisesRegex(ValueError, "independent arithmetic"):
                self.review.verify(self.root, independent=True)

    def test_replaced_group_identity_fails_manifest_membership(self):
        self.change_prediction(lambda record: record.update(id="f" * 64))
        with self.assertRaisesRegex(ValueError, "membership"):
            self.review.verify(self.root)

    def test_incomplete_model_inventory_is_rejected(self):
        path = self.control_root / "evaluation/results.json"
        report = study.read_json(path)
        report["results"].pop()
        self.replace(path, report)
        with self.assertRaisesRegex(ValueError, "nine"):
            self.review.verify(self.root)

    def test_manifest_aggregate_truth_totals_are_checked(self):
        self.change_prediction(lambda record: record.update(counts=[4, 1], subtypes=[4, 1] + record["subtypes"][2:]))
        with self.assertRaises(ValueError):
            self.review.verify(self.root)


if __name__ == "__main__":
    unittest.main()
