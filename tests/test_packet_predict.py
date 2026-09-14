"""Portable inference orchestration tests; root runs the real native command."""

import contextlib
import copy
import csv
import hashlib
import importlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT))
try:
    predict = importlib.import_module("predict_packets")
except ModuleNotFoundError as error:
    if error.name != "predict_packets":
        raise
    predict = None

HEADER = [f"payload_byte_{index}" for index in range(1, 1501)]
META = ["ttl", "total_len", "protocol", "t_delta"]


def payload(tag=0):
    return bytes([tag]) + bytes(1499)


class FakeTensor:
    def __init__(self, values, dtype=None, device=None):
        self.values, self.dtype, self.device = values, dtype, device

    def detach(self):
        return self

    def cpu(self):
        return self

    def tolist(self):
        return self.values


class PacketPredictionTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(predict, "packet inference command is missing")
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.csv = self.base / "unlabeled.csv"
        self.checkpoint = self.base / "packet.pth"
        self.checkpoint.write_bytes(b"mocked packet checkpoint; no model execution")
        self.upstream = self.base / "upstream"
        self.output = self.base / "inference"
        self.write()
        self.calls = []

    def write(self, rows=None, *, header=None):
        with self.csv.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(HEADER if header is None else header)
            writer.writerows([list(payload(index)) for index in range(3)] if rows is None else rows)

    def metadata(self):
        model = predict.packet_model
        return {
            "format": "netmambaplus-packet-v1", "schema_version": 1,
            "architecture": copy.deepcopy(model.ARCHITECTURE),
            "input_contract": copy.deepcopy(model.INPUT_CONTRACT),
            "class_mapping": {"benign": 0, "attack": 1},
            "provenance": {
                "upstream": {"commit": model.SOURCE_COMMIT,
                             "model_files_sha256": dict(model.SOURCE_SHA256),
                             "tracked_files_verified": 47},
                "initialization": {"kind": "scratch", "sha256": None,
                                   "position_indices": [], "copied_state_names": [],
                                   "excluded_state_names": [], "new_state_names": sorted(model.STATE_SHAPES)},
                "seed": 17, "parameter_count": 1852416,
                "runtime": {"torch": "portable-test-double", "cuda": None},
            },
            "study_metadata": {"data_manifest_sha256": "a" * 64, "protocol_sha256": "b" * 64,
                               "source_sha256": {"cic": "c" * 64, "unsw": "d" * 64}},
            "checkpoint": {"path": str(self.checkpoint), "bytes": self.checkpoint.stat().st_size,
                           "sha256": hashlib.sha256(self.checkpoint.read_bytes()).hexdigest()},
        }

    @contextlib.contextmanager
    def runtime(self, *, forward=None, metadata=None, load_error=None):
        fake_torch = SimpleNamespace(uint8="uint8", tensor=FakeTensor,
                                     inference_mode=contextlib.nullcontext)
        model = SimpleNamespace(eval=lambda: None)

        def default_forward(actual_model, tensor):
            self.assertIs(actual_model, model)
            self.assertEqual(tensor.dtype, "uint8")
            self.assertEqual(tensor.device, "cpu")
            values = [bytes(row) for row in tensor.values]
            self.calls.extend(values)
            return {"logits": FakeTensor([[2.0, 0.0] if row[0] % 2 == 0 else [0.0, 2.0]
                                          for row in values])}

        with patch.dict(sys.modules, {"torch": fake_torch}), \
                patch.object(predict.packet_model, "load_checkpoint",
                             return_value=(model, self.metadata() if metadata is None else metadata),
                             side_effect=load_error), \
                patch.object(predict.packet_model, "forward_payload", side_effect=forward or default_forward):
            yield

    def execute(self, **options):
        return predict.execute(self.checkpoint, self.csv, self.output, self.upstream,
                               device="cpu", **options)

    def receipt(self):
        return json.loads((self.output / "receipt.json").read_text())

    def test_help_and_import_do_not_load_ml_dependencies(self):
        result = subprocess.run([sys.executable, "-S", str(ROOT / "tools/predict_packets.py"), "--help"],
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--max-rows", result.stdout)
        code = "import sys; sys.path.insert(0, 'tools'); import predict_packets; " \
               "assert not {'torch', 'numpy', 'pandas'}.intersection(sys.modules)"
        result = subprocess.run([sys.executable, "-S", "-c", code], cwd=ROOT,
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_complete_predictions_bind_checkpoint_input_and_native_study(self):
        with self.runtime():
            receipt = self.execute(batch_size=2)
        self.assertEqual(receipt, self.receipt())
        self.assertEqual(receipt["status"], "complete")
        self.assertTrue(receipt["input_fully_validated"])
        self.assertEqual((receipt["input_rows"], receipt["validated_rows"], receipt["predicted_rows"]), (3, 3, 3))
        self.assertEqual(self.calls, [payload(index) for index in range(3)])
        self.assertEqual(receipt["checkpoint_metadata"]["study_metadata"], self.metadata()["study_metadata"])
        for name, path in [("input", self.csv), ("checkpoint", self.checkpoint)]:
            self.assertEqual(receipt[name]["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
            self.assertEqual(receipt[name]["bytes"], path.stat().st_size)
        for relative, digest in receipt["code_sha256"].items():
            self.assertEqual(digest, hashlib.sha256((ROOT / relative).read_bytes()).hexdigest())
        predictions = self.output / "predictions.jsonl"
        self.assertEqual(receipt["predictions"]["sha256"], hashlib.sha256(predictions.read_bytes()).hexdigest())
        rows = [json.loads(line) for line in predictions.read_text().splitlines()]
        self.assertEqual([row["row_id"] for row in rows], [0, 1, 2])
        self.assertEqual([row["class_name"] for row in rows], ["benign", "attack", "benign"])
        for index, row in enumerate(rows):
            self.assertEqual(row["payload_sha256"], hashlib.sha256(payload(index)).hexdigest())
            self.assertEqual(row["class_index"], index % 2)
            self.assertEqual(row["probability_kind"], "uncalibrated_softmax")
            self.assertAlmostEqual(row["probability"], 0.8807970779778823)
            self.assertAlmostEqual(sum(row["probabilities"]), 1.0)
            self.assertEqual(set(row), {"row_id", "payload_sha256", "class_index", "class_name",
                                        "logits", "probability", "probabilities", "probability_kind"})
        self.assertFalse((self.output / "predictions.incomplete.jsonl").exists())

    def test_four_metadata_fields_never_change_forward_payload_or_predictions(self):
        self.write([list(payload(index)) + ["NaN", "-42", "undocumented", "inf"] for index in range(3)],
                   header=HEADER + META)
        with self.runtime():
            receipt = self.execute(batch_size=2)
        self.assertEqual(self.calls, [payload(index) for index in range(3)])
        self.assertEqual(receipt["ignored_metadata_columns"], META)
        self.assertEqual(receipt["status"], "complete")

    def test_labeled_reordered_duplicated_and_extended_headers_are_rejected(self):
        headers = [HEADER + ["label"], HEADER + META + ["label"], HEADER[::-1],
                   ["payload_byte_2"] + HEADER[1:], HEADER + ["ttl"], HEADER + ["other"]]
        for index, header in enumerate(headers):
            self.output = self.base / f"bad-header-{index}"
            self.write(header=header)
            with self.subTest(index=index), self.runtime(), self.assertRaises(ValueError):
                self.execute()
            self.assertEqual(self.receipt()["status"], "incomplete")
            self.assertEqual(self.receipt()["predicted_rows"], 0)
            self.assertFalse((self.output / "predictions.jsonl").exists())
        self.assertEqual(self.calls, [])

    def test_malformed_fractional_nonfinite_and_out_of_range_bytes_are_rejected(self):
        invalid = ["bad", "", "False", "NaN", "inf", "-inf", "1.5", -1, 256,
                   "1.00000000000000000001", "1e-9999"]
        for index, value in enumerate(invalid):
            self.output = self.base / f"bad-byte-{index}"
            self.write([[0] * 1499 + [value]])
            with self.subTest(value=value), self.runtime(), self.assertRaises(ValueError):
                self.execute()
            self.assertEqual(self.receipt()["status"], "incomplete")
            self.assertEqual(self.receipt()["predicted_rows"], 0)
        self.assertEqual(self.calls, [])

    def test_missing_and_extra_row_columns_cannot_be_silently_trimmed(self):
        for count in [1499, 1501]:
            self.output = self.base / f"bad-width-{count}"
            self.write([[0] * count])
            with self.runtime(), self.assertRaises(ValueError):
                self.execute()
            self.assertEqual(self.receipt()["predicted_rows"], 0)

    def test_explicit_cap_predicts_prefix_but_validates_and_hashes_the_full_file(self):
        with self.runtime():
            receipt = self.execute(batch_size=2, max_rows=1)
        self.assertEqual(receipt["status"], "capped")
        self.assertEqual(receipt["max_rows"], 1)
        self.assertEqual((receipt["input_rows"], receipt["validated_rows"], receipt["predicted_rows"]), (3, 3, 1))
        self.assertTrue(receipt["input_fully_validated"])
        self.assertFalse(receipt["all_rows_predicted"])
        self.assertEqual(self.calls, [payload(0)])
        self.assertEqual(receipt["input"]["sha256_scope"], "entire_file")
        self.assertEqual(receipt["input"]["sha256"], hashlib.sha256(self.csv.read_bytes()).hexdigest())

    def test_a_cap_at_or_above_file_length_does_not_claim_missing_predictions(self):
        for cap in [3, 4]:
            self.output = self.base / f"cap-{cap}"
            with self.runtime():
                receipt = self.execute(max_rows=cap)
            self.assertEqual(receipt["status"], "complete")
            self.assertTrue(receipt["all_rows_predicted"])

    def test_bad_tail_after_cap_leaves_only_explicit_partial_predictions(self):
        self.write([list(payload(0)), [0] * 1499 + ["1.5"]])
        with self.runtime(), self.assertRaises(ValueError):
            self.execute(batch_size=1, max_rows=1)
        receipt = self.receipt()
        self.assertEqual(receipt["status"], "incomplete")
        self.assertFalse(receipt["input_fully_validated"])
        self.assertEqual(receipt["predicted_rows"], 1)
        self.assertIsNone(receipt["input_rows"])
        self.assertTrue((self.output / "predictions.incomplete.jsonl").is_file())
        self.assertFalse((self.output / "predictions.jsonl").exists())

    def test_empty_source_and_checkpoint_rejection_are_recorded_as_incomplete(self):
        self.write([])
        with self.runtime(), self.assertRaises(ValueError):
            self.execute()
        self.assertEqual(self.receipt()["status"], "incomplete")
        self.output = self.base / "bad-checkpoint"
        self.write()
        with self.runtime(load_error=ValueError("Require a packet checkpoint")), self.assertRaises(ValueError):
            self.execute()
        self.assertEqual(self.receipt()["status"], "incomplete")
        self.assertEqual(self.receipt()["predicted_rows"], 0)

    def test_checkpoint_binding_mismatch_fails_before_prediction(self):
        metadata = self.metadata()
        metadata["checkpoint"]["sha256"] = "0" * 64
        with self.runtime(metadata=metadata), self.assertRaises(ValueError):
            self.execute()
        self.assertEqual(self.calls, [])
        self.assertEqual(self.receipt()["status"], "incomplete")

    def test_input_mutation_during_inference_prevents_completion(self):
        def mutate(model, tensor):
            with self.csv.open("a") as stream:
                stream.write("\n")
            return {"logits": FakeTensor([[0.0, 2.0] for _ in tensor.values])}
        with self.runtime(forward=mutate), self.assertRaises(ValueError):
            self.execute(batch_size=3)
        self.assertEqual(self.receipt()["status"], "incomplete")
        self.assertFalse((self.output / "predictions.jsonl").exists())

    def test_wrong_logit_shape_nonfinite_values_and_lost_rows_are_rejected(self):
        for logits in [[], [[1.0]], [[1.0, 0.0, 2.0]], [[float("nan"), 0.0]],
                       [[float("inf"), 0.0]], [[True, 0.0]], [["2", 0.0]]]:
            with self.subTest(logits=logits), self.assertRaises(ValueError):
                predict.format_predictions([(0, payload())], logits)
        rows = predict.format_predictions([(5, payload())], [[1000.0, -1000.0]])
        self.assertEqual(rows[0]["row_id"], 5)
        self.assertEqual(rows[0]["probabilities"], [1.0, 0.0])
        tied = predict.format_predictions([(0, payload())], [[1.0, 1.0]])
        self.assertEqual(tied[0]["class_index"], 0)

    def test_invalid_caps_and_batch_sizes_fail_before_creating_output(self):
        for key in ["batch_size", "max_rows"]:
            for value in [True, False, 0, -1, 1.5, "2"]:
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    self.execute(**{key: value})
                self.assertFalse(self.output.exists())

    def test_existing_outputs_and_broken_symlinks_are_never_overwritten(self):
        self.output.mkdir()
        sentinel = self.output / "receipt.json"
        sentinel.write_text("prior result")
        with self.assertRaises(FileExistsError):
            self.execute()
        self.assertEqual(sentinel.read_text(), "prior result")
        self.output = self.base / "broken-link"
        self.output.symlink_to(self.base / "missing")
        with self.assertRaises(FileExistsError):
            self.execute()
        self.assertTrue(self.output.is_symlink())

    def test_cli_failure_returns_nonzero_and_names_the_incomplete_receipt(self):
        self.write(header=HEADER + ["label"])
        with self.runtime(), contextlib.redirect_stderr(io.StringIO()) as error:
            result = predict.main(["--checkpoint", str(self.checkpoint), "--csv", str(self.csv),
                                   "--output", str(self.output), "--upstream", str(self.upstream)])
        self.assertEqual(result, 1)
        self.assertIn("receipt.json", error.getvalue())
        self.assertEqual(self.receipt()["status"], "incomplete")


if __name__ == "__main__":
    unittest.main()
