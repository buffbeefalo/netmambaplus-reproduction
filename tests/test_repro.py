import argparse
import copy
import hashlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
from contextlib import redirect_stderr, redirect_stdout
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import repro
import evaluate


def record(identifier="flow", label=0, length=2):
    return {"data": ["0 1 255"], "sizes": " ".join(["64"] * length),
            "intervals": " ".join(["0"] * length), "num_packet": length,
            "label": label, "name": f"class-{label}", "pcap_file": identifier}


class Workspace(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = self.root / "data"
        self.data.mkdir()
        self.mapping = {f"class-{i}": i for i in range(6)}
        self.config = repro.load_config(repro.DEFAULT_CONFIG)
        self.write("metadata.json", {"name_to_idx": self.mapping})
        for split in ("train", "valid", "test"):
            self.write(f"data-{split}.json", [record(split)])

    def write(self, name, value):
        (self.data / name).write_text(json.dumps(value), encoding="utf-8")

    def validate(self, stage="finetune"):
        return repro.validate_data(self.data, stage, self.config)


class DataTests(Workspace):
    def test_short_flows_and_long_sequences(self):
        self.write("data-train.json", [record("short"), record("long", length=25)])
        report = self.validate()
        self.assertEqual(report["splits"]["train"]["rows"], 2)
        self.assertEqual(report["class_mapping"], self.mapping)

    def test_invalid_records(self):
        cases = [{"data": ["256"]}, {"data": ["1.5"]}, {"data": "0 1"},
                 {"sizes": "nan 64"}, {"intervals": "-1 0"},
                 {"intervals": "inf 0"}, {"sizes": "1"},
                 {"sizes": "1  2"}, {"label": True}, {"name": "wrong"},
                 {"num_packet": -1}, {"pcap_file": 4}]
        for bad in cases:
            with self.subTest(bad=bad):
                row = record("train")
                row.update(bad)
                self.write("data-train.json", [row])
                with self.assertRaises(repro.ReproError):
                    self.validate()

    def test_mapping_conflicts(self):
        for mapping in ({"x": 0, "y": 0}, {"x": 1}, {"x": False}, {}):
            with self.subTest(mapping=mapping):
                self.write("metadata.json", {"name_to_idx": mapping})
                with self.assertRaises(repro.ReproError):
                    self.validate()

    def test_malformed_json(self):
        (self.data / "data-train.json").write_text("[broken", encoding="utf-8")
        with self.assertRaises(repro.ReproError):
            self.validate()

    def test_pretrain_fallback(self):
        (self.data / "data-train.json").rename(self.data / "data.json")
        report = self.validate("pretrain")
        self.assertEqual(set(report["files"]), {"metadata.json", "data.json"})
        self.write("data-train.json", [record("preferred")])
        report = self.validate("pretrain")
        self.assertIn("data-train.json", report["files"])
        self.assertNotIn("data.json", report["files"])

    def test_evaluation_reads_only_test_and_metadata(self):
        for split in ("train", "valid"):
            (self.data / f"data-{split}.json").unlink()
        original = Path.read_bytes
        def guarded(path):
            if path.name in ("data-train.json", "data-valid.json"):
                self.fail("evaluation opened a training/validation file")
            return original(path)
        with patch.object(Path, "read_bytes", guarded):
            report = self.validate("evaluate")
        self.assertEqual(set(report["files"]), {"metadata.json", "data-test.json"})

    def test_identifier_overlap_is_rejected(self):
        self.write("data-valid.json", [record("train")])
        with self.assertRaisesRegex(repro.ReproError, "pcap_file"):
            self.validate()

    def test_duplicate_reporting_does_not_mutate_data(self):
        before = {p.name: p.read_bytes() for p in self.data.iterdir()}
        report = self.validate()
        self.assertEqual(report["raw_input_overlaps"]["train_test"]["shared_raw_inputs"], 1)
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.data.iterdir()})

    def test_missing_identifiers_remain_visible(self):
        row = record()
        del row["pcap_file"]
        self.write("data-train.json", [row])
        self.assertEqual(self.validate()["splits"]["train"]["identifier_rows"], 0)

    def test_validation_uses_stage_size_key(self):
        self.config["finetune"]["size_key"] = "signed_sizes"
        for split in ("train", "valid", "test"):
            row = record(split)
            row["signed_sizes"] = "64 -64"
            del row["sizes"]
            self.write(f"data-{split}.json", [row])
        self.assertEqual(self.validate()["splits"]["test"]["rows"], 1)
        self.assertEqual(self.validate("evaluate")["splits"]["test"]["rows"], 1)
        self.config["pretrain"]["size_key"] = "signed_sizes"
        self.assertEqual(self.validate("pretrain")["splits"]["train"]["rows"], 1)

    def test_missing_stage_selected_field_is_rejected(self):
        self.config["finetune"]["size_key"] = "signed_sizes"
        with self.assertRaises(repro.ReproError):
            self.validate()

    def test_duplicate_fingerprint_uses_stage_selected_sizes(self):
        self.config["finetune"]["size_key"] = "signed_sizes"
        for index, split in enumerate(("train", "valid", "test")):
            row = record(split)
            row["sizes"] = f"{index + 1} {index + 2}"
            row["signed_sizes"] = "64 -64"
            self.write(f"data-{split}.json", [row])
        self.assertEqual(self.validate()["raw_input_overlaps"]["train_test"]["shared_raw_inputs"], 1)


class ReportTests(Workspace):
    def invoke(self, destination, config=None):
        argv = ["validate", "--data", str(self.data), "--report", str(destination)]
        if config:
            argv.extend(["--config", str(config)])
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            return repro.main(argv)

    def test_report_cannot_replace_input_data(self):
        for name in ("metadata.json", "data-train.json", "data-valid.json", "data-test.json"):
            target = self.data / name
            before = target.read_bytes()
            with self.subTest(name=name):
                try:
                    self.assertNotEqual(self.invoke(target), 0)
                    self.assertEqual(target.read_bytes(), before)
                finally:
                    target.write_bytes(before)

    def test_report_cannot_replace_configuration(self):
        target = self.root / "config.json"
        target.write_text(json.dumps(self.config), encoding="utf-8")
        before = target.read_bytes()
        self.assertNotEqual(self.invoke(target, config=target), 0)
        self.assertEqual(target.read_bytes(), before)

    def test_report_does_not_replace_a_symlink(self):
        target = self.data / "data-test.json"
        before = target.read_bytes()
        alias = self.root / "alias.json"
        alias.symlink_to(target)
        self.assertNotEqual(self.invoke(alias), 0)
        self.assertTrue(alias.is_symlink())
        self.assertEqual(target.read_bytes(), before)

    def test_report_requires_a_new_destination(self):
        target = self.root / "report.json"
        self.assertEqual(self.invoke(target), 0)
        before = target.read_bytes()
        self.assertNotEqual(self.invoke(target), 0)
        self.assertEqual(target.read_bytes(), before)


class MetricTests(unittest.TestCase):
    def test_recursive_metric_serialization(self):
        class Array:
            def tolist(self):
                return [0.5, float("nan"), [float("inf")]]
        class Scalar:
            def item(self):
                return 7
        result, paths = evaluate.serialize_metrics({"per_class": Array(), "n": Scalar(), "pair": (1, 2)})
        self.assertEqual(result, {"per_class": [0.5, None, [None]], "n": 7, "pair": [1, 2]})
        self.assertEqual(paths, ["/per_class/1", "/per_class/2/0"])
        json.dumps(result, allow_nan=False)


class CheckoutTests(Workspace):
    def setUp(self):
        super().setUp()
        self.checkout = self.root / "upstream"
        self.checkout.mkdir()
        entries = []
        self.config = copy.deepcopy(self.config)
        for name in sorted(repro.CORE_FILES):
            file = self.checkout / name
            file.parent.mkdir(parents=True, exist_ok=True)
            raw = f"# fixture: {name}\n".encode()
            file.write_bytes(raw)
            digest = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
            entries.append(f"100644 blob {digest}\t{name}\0")
            self.config["upstream"]["sha256"][name] = hashlib.sha256(raw).hexdigest()
        self.responses = {("rev-parse", "--show-toplevel"): str(self.checkout),
                          ("rev-parse", "HEAD"): self.config["upstream"]["commit"],
                          ("status", "--porcelain=v1", "--untracked-files=no"): "",
                          ("ls-tree", "-r", "-z", "--full-tree", "HEAD"): "".join(entries)}
        self.addCleanup(patch.stopall)
        patch.object(repro, "git", side_effect=lambda root, *args: self.responses[args]).start()

    def test_clean_checkout(self):
        self.assertEqual(repro.verify_upstream(self.checkout, self.config)["tracked_files_verified"], 7)

    def test_wrong_commit_is_rejected(self):
        self.responses[("rev-parse", "HEAD")] = "0" * 40
        with self.assertRaisesRegex(repro.ReproError, "exact commit"):
            repro.verify_upstream(self.checkout, self.config)

    def test_content_drift_even_if_git_status_hides_it(self):
        (self.checkout / "src/engine_mm.py").write_text("changed", encoding="utf-8")
        with self.assertRaisesRegex(repro.ReproError, "differs from its Git object"):
            repro.verify_upstream(self.checkout, self.config)

    def test_ignored_importable_addition_is_rejected(self):
        (self.checkout / ".gitignore").write_text("*.py\n", encoding="utf-8")
        (self.checkout / "src/shadow.py").write_text("pass\n", encoding="utf-8")
        with self.assertRaisesRegex(repro.ReproError, "Additional importable"):
            repro.verify_upstream(self.checkout, self.config)

    def test_core_hash_mismatch_is_rejected(self):
        self.config["upstream"]["sha256"]["src/engine_mm.py"] = "0" * 64
        with self.assertRaisesRegex(repro.ReproError, "SHA-256 mismatch"):
            repro.verify_upstream(self.checkout, self.config)


def native_parser_fixture():
    parser = argparse.ArgumentParser()
    for key in ("num_packet", "num_packet_byte", "seq_len", "stride_size", "batch_size",
                "accum_iter", "world_size", "seed", "steps", "epochs", "nb_classes", "num_workers"):
        parser.add_argument("--" + key, type=int)
    for key in ("weight_decay", "blr", "byte_mask_ratio", "size_mask_ratio", "iat_mask_ratio", "smoothing"):
        parser.add_argument("--" + key, type=float)
    for key in ("size_key", "dataset_type", "average", "model", "device"):
        parser.add_argument("--" + key)
    for key in ("data_path", "output_dir", "log_dir", "finetune", "ckpt_dir"):
        parser.add_argument("--" + key, default="/author/local/path")
    parser.add_argument("--no_amp", dest="if_amp", action="store_false")
    parser.set_defaults(extra_native_attribute="preserved", lr=None)
    return parser


class InvocationWorkspace(Workspace):
    def setUp(self):
        super().setUp()
        self.checkpoint = self.root / "input.pth"
        self.checkpoint.write_bytes(b"synthetic checkpoint; never deserialized")
        self.addCleanup(patch.stopall)
        self.integrity = patch.object(repro, "verify_upstream", return_value={"commit": "verified"}).start()
        self.parser_call = patch.object(repro.runpy, "run_path", return_value={
            "get_args_parser": native_parser_fixture}).start()
        patch.dict(os.environ, {}, clear=True).start()
        self.stdout, self.stderr = io.StringIO(), io.StringIO()
        out = redirect_stdout(self.stdout)
        err = redirect_stderr(self.stderr)
        out.__enter__()
        err.__enter__()
        self.addCleanup(out.__exit__, None, None, None)
        self.addCleanup(err.__exit__, None, None, None)

    def args(self, stage="finetune", extra=()):
        return repro.cli_parser().parse_args([stage, "--data", str(self.data), "--output",
            str(self.root / "run"), "--upstream", str(self.root / "upstream"),
            "--checkpoint", str(self.checkpoint), *extra])

    def manifest(self):
        return json.loads((self.root / "run/manifest.json").read_text())


class InvocationTests(InvocationWorkspace):
    def test_preexisting_artifacts_are_not_reused(self):
        output = self.root / "run"
        output.mkdir()
        checkpoint = output / "checkpoint-best.pth"
        checkpoint.write_bytes(b"earlier experiment")
        with patch.object(repro, "prepare") as prepare:
            self.assertNotEqual(repro.run_stage(self.args(extra=("--dry-run",))), 0)
        prepare.assert_not_called()
        self.assertEqual(list(output.iterdir()), [checkpoint])
        self.assertEqual(checkpoint.read_bytes(), b"earlier experiment")

    def test_concurrent_manifest_creation_has_one_owner(self):
        barrier = Barrier(8)
        args = self.args("pretrain")
        def create(index):
            barrier.wait(timeout=10)
            try:
                _, manifest = repro.begin_manifest(args)
                return manifest
            except (repro.ReproError, FileExistsError):
                return None
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(create, range(8)))
        winners = [value for value in results if value is not None]
        self.assertEqual(len(winners), 1)
        self.assertEqual(self.manifest(), winners[0])

    def test_actual_parser_interface_preserves_defaults_and_absolute_overrides(self):
        args = self.args(extra=("--seed", "9", "--num-workers", "0"))
        native, argv, command, _ = repro.build_native(args, self.config, self.validate())
        self.parser_call.assert_called_once_with(str(self.root / "upstream/src/util/arg_fine_tune.py"))
        self.integrity.assert_called_once()
        self.assertEqual(native.extra_native_attribute, "preserved")
        self.assertEqual((native.nb_classes, native.seed, native.num_workers), (6, 9, 0))
        self.assertEqual((native.model, native.epochs, native.batch_size), ("fuse3_mamba_classifier", 120, 128))
        self.assertEqual((native.blr, native.lr, native.if_amp), (0.002, None, False))
        self.assertIn("--no_amp", argv)
        self.assertNotIn("--lr", argv)
        for key in ("data_path", "output_dir", "log_dir", "finetune", "ckpt_dir"):
            self.assertTrue(Path(getattr(native, key)).is_absolute())
            self.assertNotIn("author/local", getattr(native, key))
        self.assertEqual(native.finetune, str(self.checkpoint))
        self.assertEqual(command[:3], [sys.executable, "-u", str(self.root / "upstream/src/fine-tune.py")])

    def test_pretraining_recipe(self):
        native, argv, command, _ = repro.build_native(self.args("pretrain"), self.config, self.validate("pretrain"))
        self.assertEqual((native.model, native.steps, native.blr), ("fuse3_mamba_pretrain", 100000, 0.001))
        self.assertEqual((native.byte_mask_ratio, native.size_mask_ratio, native.iat_mask_ratio), (0.9, 0.15, 0.15))
        self.assertNotIn("--finetune", argv)
        self.assertTrue(command[2].endswith("/src/pre-train.py"))

    def test_integrity_failure_precedes_parser_execution(self):
        self.integrity.side_effect = repro.ReproError("drift")
        with self.assertRaises(repro.ReproError):
            repro.build_native(self.args(), self.config, self.validate())
        self.parser_call.assert_not_called()

    def test_distributed_environment_rejected(self):
        for environment in ({"WORLD_SIZE": "2"}, {"RANK": "0"}, {"LOCAL_RANK": "0"}):
            with self.subTest(environment=environment), patch.dict(os.environ, environment, clear=True):
                with self.assertRaisesRegex(repro.ReproError, "Distributed"):
                    repro.build_native(self.args(), self.config, self.validate())

    def test_dry_run_does_not_execute_model(self):
        with patch.object(repro.subprocess, "run", side_effect=AssertionError("launched process")):
            self.assertEqual(repro.run_stage(self.args(extra=("--dry-run",))), 0)
        manifest = self.manifest()
        self.assertEqual(manifest["status"], "dry_run")
        self.assertFalse(manifest["execution_attempted"])
        self.assertEqual(manifest["native_args"]["extra_native_attribute"], "preserved")
        self.assertEqual(set(manifest["input_files"]), {
            "metadata.json", "data-train.json", "data-valid.json", "data-test.json"})

    def test_preflight_failure_is_recorded(self):
        self.write("data-test.json", "invalid")
        self.assertEqual(repro.run_stage(self.args()), 1)
        self.assertEqual(self.manifest()["status"], "preflight_failed")
        self.assertFalse(self.manifest()["execution_attempted"])

    def test_subprocess_failure_is_recorded(self):
        with patch.object(repro.subprocess, "run", return_value=SimpleNamespace(returncode=17)):
            self.assertEqual(repro.run_stage(self.args()), 1)
        manifest = self.manifest()
        self.assertEqual((manifest["status"], manifest["native_exit_code"]), ("failed", 17))
        self.assertIn("Native process exited 17", manifest["error"]["message"])

    def test_successful_finetuning_binds_checkpoint(self):
        def train(command, **kwargs):
            self.assertEqual(kwargs["cwd"], str(self.root / "upstream/src"))
            self.assertEqual(kwargs["env"]["PYTHONDONTWRITEBYTECODE"], "1")
            (self.root / "run/checkpoint-best.pth").write_bytes(b"trained")
            return SimpleNamespace(returncode=0)
        with patch.object(repro.subprocess, "run", side_effect=train) as process:
            self.assertEqual(repro.run_stage(self.args()), 0)
        process.assert_called_once()
        binding = self.manifest()["produced_checkpoint"]
        self.assertEqual(binding["sha256"], hashlib.sha256(b"trained").hexdigest())
        self.assertEqual(binding["class_mapping"], self.mapping)
        result = repro.checkpoint_provenance(binding["path"], binding["sha256"], self.mapping)
        self.assertEqual(result["class_order"], "hash_bound")

    def test_existing_manifest_is_never_overwritten(self):
        args = self.args(extra=("--dry-run",))
        self.assertEqual(repro.run_stage(args), 0)
        before = (self.root / "run/manifest.json").read_bytes()
        self.assertEqual(repro.run_stage(args), 1)
        self.assertEqual((self.root / "run/manifest.json").read_bytes(), before)

    def test_environment_manifest_uses_allowlist(self):
        with patch.dict(os.environ, {"SECRET_TEST_TOKEN": "excluded", "CUDA_VISIBLE_DEVICES": "0"}):
            environment = repro.runtime_information()["environment"]
        self.assertEqual(environment, {"CUDA_VISIBLE_DEVICES": "0"})


class ProvenanceTests(Workspace):
    def setUp(self):
        super().setUp()
        self.checkpoint = self.root / "classifier.pth"
        self.checkpoint.write_bytes(b"classifier")
        self.digest = repro.sha256_file(self.checkpoint)
        self.provenance = self.root / "provenance.json"

    def binding(self, digest=None, mapping=None):
        self.provenance.write_text(json.dumps({"checkpoint_sha256": digest or self.digest,
            "class_mapping": mapping or self.mapping}), encoding="utf-8")

    def test_absent_provenance_stays_unknown(self):
        result = repro.checkpoint_provenance(self.checkpoint, self.digest, self.mapping)
        self.assertEqual((result["class_order"], result["training_history"]), ("unknown", "unknown"))

    def test_explicit_hash_binding_and_conflicts(self):
        self.binding()
        result = repro.checkpoint_provenance(self.checkpoint, self.digest, self.mapping, self.provenance)
        self.assertEqual(result["class_order"], "hash_bound")
        swapped = dict(self.mapping, **{"class-0": 1, "class-1": 0})
        self.binding(mapping=swapped)
        with self.assertRaisesRegex(repro.ReproError, "conflicts"):
            repro.checkpoint_provenance(self.checkpoint, self.digest, self.mapping, self.provenance)
        self.binding(digest="0" * 64)
        with self.assertRaisesRegex(repro.ReproError, "not bound"):
            repro.checkpoint_provenance(self.checkpoint, self.digest, self.mapping, self.provenance)

    def test_failed_training_manifest_is_not_accepted_as_class_provenance(self):
        (self.root / "manifest.json").write_text(json.dumps({"stage": "finetune", "status": "failed",
            "produced_checkpoint": {"sha256": self.digest, "class_mapping": self.mapping}}), encoding="utf-8")
        result = repro.checkpoint_provenance(self.checkpoint, self.digest, self.mapping)
        self.assertEqual(result["class_order"], "unknown")


class EvaluationTests(InvocationWorkspace):
    def runtime(self):
        model = Mock()
        model.to.return_value = model
        runtime = SimpleNamespace(
            torch=SimpleNamespace(device=Mock(return_value="selected-device"),
                                  load=Mock(return_value={"model": {"head.weight": "weights"}})),
            classifier=Mock(return_value=model),
            loader=Mock(return_value=("test-loader", {"0": "class-0"})),
            engine=Mock(return_value={"acc": 0.75, "per_class": [1.0, float("nan")], "cm": [[1, 0], [0, 2]]}))
        return runtime, model

    def test_strict_test_only_execution_and_complete_metrics(self):
        for name in ("data-train.json", "data-valid.json"):
            (self.data / name).unlink()
        runtime, model = self.runtime()
        original = Path.read_bytes
        def guarded(path):
            if path.name in ("data-train.json", "data-valid.json"):
                self.fail("test evaluator accessed a training/validation split")
            return original(path)
        def evaluate_once(prepared):
            native = prepared["native"]
            result = evaluate.run_evaluation(prepared, runtime)
            runtime.classifier.assert_called_once_with(native)
            runtime.loader.assert_called_once_with(native, str(self.data / "data-test.json"))
            runtime.engine.assert_called_once_with("test-loader", model, "selected-device", native)
            return result
        with patch.object(Path, "read_bytes", guarded):
            self.assertEqual(repro.run_stage(self.args("evaluate"), evaluation_fn=evaluate_once), 0)
        runtime.torch.load.assert_called_once_with(str(self.checkpoint), map_location="cpu", weights_only=False)
        model.load_state_dict.assert_called_once_with({"head.weight": "weights"}, strict=True)
        model.to.assert_called_once_with("selected-device")
        metrics = json.loads((self.root / "run/metrics.json").read_text())
        self.assertEqual(set(metrics["metrics"]), {"acc", "per_class", "cm"})
        self.assertEqual(metrics["nonfinite_metric_paths"], ["/per_class/1"])
        self.assertEqual(metrics["checkpoint_provenance"]["class_order"], "unknown")
        self.assertEqual(self.manifest()["status"], "succeeded")
        self.assertEqual(self.manifest()["cwd"], str(Path.cwd()))

    def test_incompatible_checkpoint_fails_without_fallback(self):
        runtime, model = self.runtime()
        model.load_state_dict.side_effect = RuntimeError("head shape mismatch")
        fn = lambda prepared: evaluate.run_evaluation(prepared, runtime)
        self.assertEqual(repro.run_stage(self.args("evaluate"), evaluation_fn=fn), 1)
        model.load_state_dict.assert_called_once_with({"head.weight": "weights"}, strict=True)
        runtime.loader.assert_not_called()
        runtime.engine.assert_not_called()
        self.assertEqual(self.manifest()["status"], "failed")

    def test_missing_model_state_is_rejected(self):
        runtime, model = self.runtime()
        runtime.torch.load.return_value = {"state_dict": {}}
        fn = lambda prepared: evaluate.run_evaluation(prepared, runtime)
        self.assertEqual(repro.run_stage(self.args("evaluate"), evaluation_fn=fn), 1)
        model.load_state_dict.assert_not_called()

    def test_loader_mapping_semantic_conflict_is_rejected(self):
        runtime, model = self.runtime()
        runtime.loader.return_value = ("test-loader", {0: "class-1"})
        fn = lambda prepared: evaluate.run_evaluation(prepared, runtime)
        self.assertEqual(repro.run_stage(self.args("evaluate"), evaluation_fn=fn), 1)
        runtime.engine.assert_not_called()

    def test_runtime_import_failure_is_recorded(self):
        with patch.object(evaluate, "load_runtime", side_effect=ImportError("torch unavailable")):
            self.assertEqual(repro.run_stage(self.args("evaluate"), evaluation_fn=evaluate.run_evaluation), 1)
        self.assertEqual(self.manifest()["error"]["type"], "ImportError")

    def test_changed_input_invalidates_run(self):
        runtime, model = self.runtime()
        def changed(prepared):
            result = evaluate.run_evaluation(prepared, runtime)
            self.write("data-test.json", [record("changed", length=3)])
            return result
        self.assertEqual(repro.run_stage(self.args("evaluate"), evaluation_fn=changed), 1)
        self.assertIn("Input changed", self.manifest()["error"]["message"])


if __name__ == "__main__":
    unittest.main()
