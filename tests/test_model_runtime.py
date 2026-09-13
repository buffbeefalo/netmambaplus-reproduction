import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import check_model_runtime as check


class ModelRuntimeBoundaryTests(unittest.TestCase):
    def args(self, base, **updates):
        values = dict(upstream=base / "missing-upstream", config=check.repro.DEFAULT_CONFIG,
                      output=base / "result", device=0, seed=0, build_report=None)
        values.update(updates)
        return SimpleNamespace(**values)

    def test_existing_output_is_never_reused(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            args = self.args(base)
            args.output.mkdir()
            sentinel = args.output / "manifest.json"
            sentinel.write_text("prior evidence", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                check.execute(args)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "prior evidence")

    def test_output_inside_upstream_is_rejected_without_creating_it(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            args = self.args(base)
            args.output = args.upstream / "smoke-output"
            with self.assertRaisesRegex(ValueError, "outside"):
                check.execute(args)
            self.assertFalse(args.output.exists())

    def test_missing_upstream_preserves_failure_before_cuda_import(self):
        with tempfile.TemporaryDirectory() as temporary:
            args = self.args(Path(temporary))
            self.assertEqual(check.execute(args), 1)
            report = json.loads((args.output / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "failed")
            self.assertEqual(report["failed_stage"], "source_verification")
            self.assertTrue(report["synthetic_only"])
            self.assertFalse((args.output / "checkpoint-synthetic.pth").exists())

    def test_reduced_or_non_native_recipe_is_rejected(self):
        original = check.repro.load_config(check.repro.DEFAULT_CONFIG)
        for section, key, value in [("common", "stride_size", 8), ("common", "seq_len", 10),
                                    ("common", "if_amp", True), ("finetune", "model", "tiny"),
                                    ("dataset", "expected_classes", 2)]:
            with self.subTest(key=key):
                config = copy.deepcopy(original)
                config[section][key] = value
                with self.assertRaisesRegex(ValueError, "configured"):
                    check.validate_recipe(config)

    def test_synthetic_flows_pass_real_schema_validation_for_six_classes(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "synthetic-inputs"
            check.write_fixtures(directory)
            report = check.repro.validate_data(directory, "evaluate",
                                              check.repro.load_config(check.repro.DEFAULT_CONFIG))
            self.assertEqual(len(report["class_mapping"]), 6)
            self.assertTrue(all(name.startswith("synthetic-class-") for name in report["class_mapping"]))
            rows = json.loads((directory / "data-test.json").read_text(encoding="utf-8"))
            self.assertEqual(len(rows), 6)
            self.assertEqual({row["label"] for row in rows}, set(range(6)))
            self.assertLess(len(rows[0]["data"]), 5)
            self.assertGreater(len(rows[-1]["data"]), 5)

    def test_builder_binding_requires_completed_matching_extensions(self):
        extensions = {"one": {"sha256": "a" * 64}}
        report = {"status": "built", "extension_files": extensions}
        check.validate_build_binding(report, extensions)
        for invalid in [{**report, "status": "failed"},
                        {**report, "extension_files": {"one": {"sha256": "b" * 64}}},
                        {**report, "extension_files": {}}]:
            with self.assertRaisesRegex(ValueError, "build report"):
                check.validate_build_binding(invalid, extensions)


if __name__ == "__main__":
    unittest.main()
