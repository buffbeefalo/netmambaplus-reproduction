import copy
import contextlib
import hashlib
import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

try:
    import calibration
except ModuleNotFoundError:
    calibration = None

try:
    from tools import calibrate
except ImportError:
    calibrate = None


def manifest_fixture():
    return {
        "configuration_sha256": "a" * 64,
        "input_checkpoint": {"path": "/checkpoint.pth", "sha256": "b" * 64},
        "class_mapping": {"first": 0, "second": 1},
        "upstream": {"commit": "c" * 40, "core_sha256": {"src/model.py": "d" * 64},
                     "tracked_files_verified": 3},
        "native_args": {"model": "classifier", "dataset_type": "byte_size_interval",
                        "num_packet": 5, "num_packet_byte": 320, "seq_len": 20,
                        "stride_size": 4, "size_key": "sizes", "nb_classes": 2,
                        "device": "cuda", "batch_size": 128, "num_workers": 0,
                        "data_path": "/data", "output_dir": "/output",
                        "finetune": "/checkpoint.pth", "ckpt_dir": "/checkpoints"},
        "runtime": {"python": "3.12.3 (build details)", "executable": "/python",
                    "packages": {"torch": "2.6.0", "numpy": "2.0.0", "flash-attn": None}},
        "inference_runtime": {"device_type": "cuda", "autocast_enabled": True,
                              "autocast_dtype": "float16", "model_mode": "eval",
                              "gradient_mode": "inference_mode"},
    }


def artifact_fixture(binding):
    return {
        "schema_version": 1, "method": "temperature_scaling", "temperature": 1.5,
        "binding": copy.deepcopy(binding),
        "fit": {"split": "valid", "objective": "nll", "temperature_bounds": [0.05, 20.0],
                "temperature": 1.5, "rows": 5, "data_sha256": "1" * 64,
                "metadata_sha256": "2" * 64, "logits_sha256": "3" * 64,
                "labels_sha256": "4" * 64, "policy_threshold": 0.9},
        "validation": {"rows": 5, "independent_holdout": False,
                       "checkpoint_selection_reuse": True,
                       "known_train_validation_overlap_rows": 5,
                       "known_validation_test_overlap_rows": 0,
                       "limitations": ["Retrospective fixture; no independence claim."]},
    }


class CalibrationMathTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(calibration, "Calibration implementation is missing")

    def test_binary_margin_optimum_has_analytic_temperature(self):
        # Four correct and one incorrect margin-2 observations have p(correct)=4/5.
        logits = [[2.0, 0.0]] * 5
        labels = [0, 0, 0, 0, 1]
        temperature = calibration.fit_temperature(logits, labels)
        self.assertAlmostEqual(temperature, 2.0 / math.log(4.0), places=9)
        metrics = calibration.classification_metrics(logits, labels, temperature)
        self.assertAlmostEqual(metrics["nll"], -0.8 * math.log(0.8) - 0.2 * math.log(0.2))
        self.assertAlmostEqual(metrics["accuracy"], 0.8)
        self.assertAlmostEqual(metrics["brier"], 0.32)
        self.assertLess(metrics["ece"], 1e-12)

    def test_unit_temperature_matches_existing_softmax_exactly(self):
        import replay
        for row in ([1.0, 3.0, -2.0], [10000.0, 10000.0], [-20.5, 4.5, 0.0]):
            self.assertEqual(calibration.calibrated_scores(row, 1.0), replay.probabilities(row))

    def test_temperature_preserves_argmax_and_input_objects(self):
        logits = [[-2.0, 6.0, 1.0], [4.0, 0.0, -3.0]]
        before = copy.deepcopy(logits)
        for t in (0.05, 0.5, 1.0, 20.0):
            for row in logits:
                scores = calibration.calibrated_scores(row, t)
                self.assertEqual(max(range(3), key=row.__getitem__),
                                 max(range(3), key=scores.__getitem__))
                self.assertAlmostEqual(sum(scores), 1.0)
        self.assertEqual(logits, before)

    def test_optimizer_handles_both_bounds_and_uninformative_logits(self):
        self.assertEqual(calibration.fit_temperature([[2.0, 0.0]], [0]), 0.05)
        self.assertEqual(calibration.fit_temperature([[2.0, 0.0]], [1]), 20.0)
        self.assertEqual(calibration.fit_temperature([[7.0, 7.0], [0.0, 0.0]], [0, 1]), 1.0)

    def test_nll_does_not_take_log_of_underflowed_probability(self):
        result = calibration.classification_metrics([[1000.0, -1000.0]], [1])
        self.assertEqual(result["nll"], 2000.0)
        self.assertEqual(result["brier"], 2.0)
        self.assertEqual(result["ece"], 1.0)

    def test_ece_is_weighted_by_bin_rows_and_brier_sums_classes(self):
        logits = [[math.log(4), 0], [math.log(4), 0], [0, 0]]
        result = calibration.classification_metrics(logits, [0, 1, 0], threshold=0.75)
        self.assertAlmostEqual(result["ece"], (2 * 0.3 + 0.5) / 3)
        self.assertAlmostEqual(result["brier"], (0.08 + 1.28 + 0.5) / 3)
        self.assertEqual((result["rows"], result["correct"], result["accepted"],
                          result["deferred"], result["accepted_errors"]), (3, 2, 2, 1, 1))
        self.assertEqual(result["accepted_error_rate"], 0.5)
        self.assertAlmostEqual(result["coverage"], 2 / 3)

    def test_empty_accepted_error_is_null_and_threshold_is_inclusive(self):
        result = calibration.classification_metrics([[0, 0]], [1], threshold=0.9)
        self.assertEqual((result["accepted"], result["deferred"]), (0, 1))
        self.assertIsNone(result["accepted_error_rate"])
        self.assertEqual(calibration.classification_metrics([[0, 0]], [0], threshold=0.5)["accepted"], 1)
        self.assertIsNone(calibration.classification_metrics([[0, 0]], [0])["accepted"])

    def test_explicit_native_maximizer_preserves_exact_tie_accuracy(self):
        result = calibration.classification_metrics([[1, 1]], [1], threshold=0.5, predictions=[1])
        self.assertEqual((result["correct"], result["accepted_errors"]), (1, 0))
        for invalid in ([], [True], [2]):
            with self.subTest(predictions=invalid), self.assertRaises(ValueError):
                calibration.classification_metrics([[1, 1]], [1], predictions=invalid)
        with self.assertRaises(ValueError):
            calibration.classification_metrics([[2, 1]], [1], predictions=[1])

    def test_malformed_rows_labels_temperatures_and_thresholds_fail(self):
        for bad in ([], [True, 0], [float("nan"), 0], [float("inf"), 0], ["2", 0]):
            with self.subTest(logits=bad), self.assertRaises(ValueError):
                calibration.calibrated_scores(bad, 1)
        for rows, labels in (([], []), ([[1, 0]], []), ([[1, 0]], [2]),
                             ([[1, 0]], [True]), ([[1, 0]], [0.0]),
                             ([[1, 0], [1]], [0, 0]), ([[1]], [0])):
            with self.subTest(rows=rows, labels=labels), self.assertRaises(ValueError):
                calibration.fit_temperature(rows, labels)
        for t in (0, -1, True, float("nan"), float("inf"), "1"):
            with self.subTest(temperature=t), self.assertRaises(ValueError):
                calibration.calibrated_scores([1, 0], t)
        for threshold in (-0.1, 1.1, True, None, "0.9", float("nan"), float("inf")):
            with self.subTest(threshold=threshold), self.assertRaises(ValueError):
                calibration.validate_threshold(threshold)


class CalibrationArtifactTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(calibration, "Calibration implementation is missing")
        self.manifest = manifest_fixture()
        self.binding = calibration.make_binding(self.manifest)
        self.artifact = artifact_fixture(self.binding)

    def test_binding_ignores_execution_locations_and_worker_settings(self):
        relocated = copy.deepcopy(self.manifest)
        relocated["input_checkpoint"]["path"] = "/relocated/model.pth"
        relocated["runtime"]["executable"] = "/another/python"
        for key in ("data_path", "output_dir", "finetune", "ckpt_dir"):
            relocated["native_args"][key] = "/another/location"
        relocated["native_args"].update(batch_size=16, num_workers=8)
        self.assertEqual(calibration.make_binding(relocated), self.binding)

    def test_checkpoint_class_config_upstream_and_precision_changes_are_rejected(self):
        for key in ("checkpoint", "classes", "configuration", "upstream", "package", "precision"):
            changed = copy.deepcopy(self.manifest)
            if key == "checkpoint": changed["input_checkpoint"]["sha256"] = "f" * 64
            if key == "classes": changed["class_mapping"] = {"first": 1, "second": 0}
            if key == "configuration": changed["configuration_sha256"] = "f" * 64
            if key == "upstream": changed["upstream"]["core_sha256"]["src/model.py"] = "f" * 64
            if key == "package": changed["runtime"]["packages"]["torch"] = "3.0.0"
            if key == "precision": changed["inference_runtime"]["autocast_dtype"] = "bfloat16"
            with self.subTest(key=key), self.assertRaises(ValueError):
                calibration.validate_artifact(self.artifact, calibration.make_binding(changed))

    def test_malformed_artifact_and_inconsistent_fit_records_are_rejected(self):
        mutations = [lambda a: a.update(schema_version=True),
                     lambda a: a.update(method="other"),
                     lambda a: a.update(temperature=float("nan")),
                     lambda a: a.update(temperature=25),
                     lambda a: a.update(temperature=2),
                     lambda a: a["fit"].update(split="test"),
                     lambda a: a["fit"].update(temperature_bounds=[0.1, 20.0]),
                     lambda a: a["fit"].update(rows=0),
                     lambda a: a["fit"].update(data_sha256="bad"),
                     lambda a: a["validation"].update(rows=6),
                     lambda a: a["validation"].update(known_train_validation_overlap_rows=-1),
                     lambda a: a["fit"].update(extra_metric=float("inf"))]
        for mutate in mutations:
            invalid = copy.deepcopy(self.artifact)
            mutate(invalid)
            with self.subTest(artifact=invalid), self.assertRaises(ValueError):
                calibration.validate_artifact(invalid, self.binding)

    def test_validated_artifact_is_detached_and_unknown_provenance_stays_unknown(self):
        self.artifact["validation"].update(checkpoint_selection_reuse=None,
            known_train_validation_overlap_rows=None, known_validation_test_overlap_rows=None)
        result = calibration.validate_artifact(self.artifact, self.binding)
        result["fit"]["rows"] = 999
        self.assertEqual(self.artifact["fit"]["rows"], 5)
        self.assertIsNone(result["validation"]["checkpoint_selection_reuse"])


class FakeTensor:
    def __init__(self, values):
        self.values = values
        self.ndim = 2 if values and isinstance(values[0], list) else 1
        self.shape = (len(values), len(values[0])) if self.ndim == 2 else (len(values),)

    def detach(self): return self
    def cpu(self): return self
    def tolist(self): return copy.deepcopy(self.values)


class SequentialFixture:
    def __init__(self, count): self.count = count
    def __iter__(self): return iter(range(self.count))


class DatasetFixture(list):
    ratio = 1.0


class CalibrationFitterTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(calibrate, "Validation-only fitting command is missing")
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.data = Path(self.temporary.name)
        self.mapping = {"first": 0, "second": 1}
        self.rows = [{"data": [str(i + 1)], "sizes": "64", "intervals": "0",
                      "label": i % 2, "name": ("first", "second")[i % 2],
                      "pcap_file": f"row-{i}"} for i in range(3)]
        self.write("metadata.json", {"name_to_idx": self.mapping})
        self.write("data-valid.json", self.rows)
        self.evidence = {"stage": "finetune", "class_mapping": self.mapping, "size_key": "sizes",
                         "files": {name: {"sha256": self.hash(name), "bytes": (self.data / name).stat().st_size}
                                   for name in ("metadata.json", "data-valid.json")},
                         "splits": {"valid": {"rows": 3, "class_counts": {"0": 2, "1": 1}}},
                         "raw_input_overlaps": {"train_valid": {"right_rows": 1},
                                                "valid_test": {"left_rows": 0}}}
        self.evidence_path = self.write("evidence.json", self.evidence)
        self.config = {"dataset": {"expected_classes": 2}, "common": {"size_key": "sizes"},
                       "finetune": {}}

    def write(self, name, value):
        path = self.data / name
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def hash(self, name):
        return hashlib.sha256((self.data / name).read_bytes()).hexdigest()

    def prepared_and_runtime(self):
        report, rows = calibrate.validate_validation_data(self.data, self.config, self.evidence_path)
        native = SimpleNamespace(device="cuda", dataset_type="byte_size_interval", batch_size=2,
                                 data_ratio=1.0)
        checkpoint = self.data / "model.pth"
        checkpoint.write_bytes(b"fixture checkpoint")
        prepared = {"args": SimpleNamespace(data=self.data, upstream=self.data), "native": native,
                    "report": report, "rows": rows, "checkpoint": checkpoint,
                    "manifest": {"class_mapping": self.mapping, "input_files": report["files"],
                                 "input_checkpoint": {"path": str(checkpoint), "sha256": self.hash("model.pth")}}}
        dataset = DatasetFixture(rows)
        dataset.data = rows
        sampler = SequentialFixture(3)

        class Loader(list):
            pass

        loader = Loader([{"x_byte": FakeTensor([[2, 0], [0, 2]]), "targets": FakeTensor([0, 1])},
                         {"x_byte": FakeTensor([[1, 0]]), "targets": FakeTensor([0])}])
        loader.dataset, loader.sampler, loader.batch_size, loader.drop_last = dataset, sampler, 2, False
        loader.batch_sampler = SimpleNamespace(sampler=sampler, drop_last=False, batch_size=2)

        class Model:
            def load_state_dict(self, state, strict):
                if strict is not True: raise AssertionError("Checkpoint loading must be strict")
            def to(self, device): return self
            def eval(self): return self

        def load_data(args, path, **kwargs):
            if Path(path).name != "data-valid.json":
                raise AssertionError("Fitter attempted to load a non-validation split")
            if kwargs != {"data_ratio": 1.0, "random_sampler": False, "class_idx": None}:
                raise AssertionError("Native loader must explicitly preserve all rows")
            return loader, {0: "first", 1: "second"}

        torch = SimpleNamespace(cuda=SimpleNamespace(is_available=lambda: True),
            device=lambda value: value, float16="float16", load=lambda *a, **k: {"model": {}},
            inference_mode=contextlib.nullcontext, autocast=lambda *a, **k: contextlib.nullcontext(),
            utils=SimpleNamespace(data=SimpleNamespace(SequentialSampler=SequentialFixture)))
        runtime = SimpleNamespace(torch=torch, classifier=lambda args: Model(), loader=load_data)
        def forward(model, inputs):
            if "targets" in inputs: raise AssertionError("Labels entered model forward")
            return {"logits": inputs["x_byte"]}
        return prepared, runtime, loader, {"byte_size_interval": lambda batch, device: dict(batch)}, {"byte_size_interval": forward}

    def test_validation_preflight_reads_no_train_or_test_and_binds_evidence(self):
        # These split files deliberately do not exist: a stage-wide validation would fail.
        report, rows = calibrate.validate_validation_data(self.data, self.config, self.evidence_path)
        self.assertEqual(rows, self.rows)
        self.assertEqual(report["splits"]["valid"]["rows"], 3)
        self.assertEqual(set(report["files"]), {"metadata.json", "data-valid.json", "data-evidence.json"})
        self.rows[0]["sizes"] = "99"
        self.write("data-valid.json", self.rows)
        with self.assertRaises(ValueError):
            calibrate.validate_validation_data(self.data, self.config, self.evidence_path)

    def test_data_evidence_row_counts_class_order_and_label_counts_cannot_drift(self):
        for field in ("rows", "classes", "counts"):
            evidence = copy.deepcopy(self.evidence)
            if field == "rows": evidence["splits"]["valid"]["rows"] = 2
            if field == "classes": evidence["class_mapping"] = {"first": 1, "second": 0}
            if field == "counts": evidence["splits"]["valid"]["class_counts"] = {"0": 1, "1": 2}
            self.write("evidence.json", evidence)
            with self.subTest(field=field), self.assertRaises(ValueError):
                calibrate.validate_validation_data(self.data, self.config, self.evidence_path)

    def test_native_collection_discards_targets_and_preserves_partial_batch(self):
        prepared, runtime, _, processors, forwards = self.prepared_and_runtime()
        logits, labels, audit = calibrate.collect_validation_logits(prepared, runtime, processors, forwards)
        self.assertEqual(logits, [[2, 0], [0, 2], [1, 0]])
        self.assertEqual(labels, [0, 1, 0])
        self.assertEqual(audit["batch_sizes"], [2, 1])
        self.assertEqual(audit["full_batches"], 1)
        self.assertEqual(audit["partial_batch_rows"], 1)

    def test_sampler_subset_drop_last_label_order_and_short_output_are_rejected(self):
        for failure in ("sampler", "ratio", "drop_last", "labels", "short_output"):
            prepared, runtime, loader, processors, forwards = self.prepared_and_runtime()
            if failure == "sampler": loader.sampler = [2, 1, 0]
            if failure == "ratio": prepared["native"].data_ratio = 0.5
            if failure == "drop_last": loader.drop_last = True
            if failure == "labels": loader[0]["targets"] = FakeTensor([1, 0])
            if failure == "short_output": loader[0]["x_byte"] = FakeTensor([[2, 0]])
            with self.subTest(failure=failure), self.assertRaises(ValueError):
                calibrate.collect_validation_logits(prepared, runtime, processors, forwards)

    def test_changed_validation_input_is_rejected_before_execution(self):
        prepared, _, _, _, _ = self.prepared_and_runtime()
        self.write("data-valid.json", self.rows + self.rows[:1])
        with self.assertRaises(ValueError):
            calibrate.assert_unchanged(prepared)

    def test_help_is_available_without_loading_the_native_runtime(self):
        result = subprocess.run([sys.executable, str(Path(calibrate.__file__)), "--help"],
                                text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--data-evidence", result.stdout)


if __name__ == "__main__":
    unittest.main()
