"""Contract tests plus tiny CPU fits when NumPy/scikit-learn are installed."""

import csv
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT))


class ControlContracts(unittest.TestCase):
    def setUp(self):
        import packet_controls
        self.controls = packet_controls

    def test_import_without_loading_training_dependencies(self):
        code = ("import sys; sys.path.insert(0,'tools'); import packet_controls; "
                "assert not {'numpy','sklearn','torch'}.intersection(sys.modules)")
        result = subprocess.run([sys.executable, "-S", "-c", code], cwd=ROOT,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_metadata_numeric_values_and_protocol_categories(self):
        self.assertEqual(self.controls._metadata_values("64", "1500", "6", "0.25"),
                         [64.0, 1500.0, .25, 0.0, 1.0, 0.0, 0.0])
        self.assertEqual(self.controls._metadata_values("0", "0", "99", "-1")[-4:],
                         [0.0, 0.0, 0.0, 1.0])
        for token, expected in (("icmp", [1., 0., 0., 0.]), ("tcp", [0., 1., 0., 0.]),
                                ("udp", [0., 0., 1., 0.]), ("others", [0., 0., 0., 1.]),
                                ("arp", [0., 0., 0., 1.]), ("ax.25", [0., 0., 0., 1.])):
            self.assertEqual(self.controls._metadata_values("64", "1500", token, "0")[-4:], expected)
        for values in (("nan", "1", "6", "0"), ("1", "inf", "6", "0"),
                       ("1", "1", "6.00000000000000000001", "0"),
                       ("1", "1", "nan", "0"), ("1", "1", "6", ""),
                       ("1", "1", "256", "0"), ("1", "1", "-1", "0"),
                       ("1", "1", "unknown-protocol", "0")):
            with self.subTest(values=values), self.assertRaises(ValueError):
                self.controls._metadata_values(*values)

    def test_existing_fit_output_is_preserved_without_loading_data(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "previous"
            output.mkdir()
            sentinel = output / "keep"
            sentinel.write_text("old")
            with self.assertRaises(FileExistsError):
                self.controls.fit_controls("missing", output, "a" * 64)
            self.assertEqual(sentinel.read_text(), "old")

    def test_evaluation_requires_completed_frozen_controls(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises((FileNotFoundError, ValueError)):
                self.controls.evaluate_controls("missing", temporary)


@unittest.skipUnless(importlib.util.find_spec("numpy") and importlib.util.find_spec("sklearn"),
                     "tiny CPU fits require NumPy and scikit-learn")
class ControlFits(unittest.TestCase):
    def setUp(self):
        import numpy as np
        import packet_controls
        import packet_data
        import train_packet_model
        self.np, self.controls, self.packet_data = np, packet_controls, packet_data
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        # One real group per split, with two train groups for CIC and one for
        # UNSW. Each group has both labels, preserving fractional targets.
        candidates = {0: [], 1: [], 2: []}
        for value in range(1, 256):
            payload = bytes([value]) * 1500
            split = packet_data.split_for_hash(packet_data.payload_hash(payload))
            candidates[split].append(value)
        for source in ("cic", "unsw"):
            path = self.base / f"{source}.csv"
            with path.open("w", newline="") as stream:
                writer = csv.writer(stream)
                writer.writerow(packet_data.CSV_COLUMNS)
                groups = [(0, value) for value in candidates[0][:2 if source == "cic" else 1]]
                groups += [(1, candidates[1][0]), (2, candidates[2][0])]
                for split, value in groups:
                    ttl = float(value if split == 0 else 1000000)
                    labels = [packet_data.LABELS[source][0]] * 3 + [packet_data.LABELS[source][1]]
                    for index, label in enumerate(labels):
                        writer.writerow([value] * 1500 + [ttl + index, 1500, ["icmp", "tcp", "udp", "others"][index],
                                                         index / 10, label])
        self.data_directory = self.base / "data"
        packet_data.prepare(self.base / "cic.csv", self.base / "unsw.csv", self.data_directory,
                            max_train_groups=100, max_eval_groups=100)
        self.data, self.manifest = train_packet_model.load_data(self.data_directory)

    def test_histogram_counts_stored_zeros_and_all_1500_bytes(self):
        payload = self.np.array([[0] * 750 + [255] * 750], dtype=self.np.uint8)
        result = self.controls._histograms(payload, self.np.array([0]))
        self.assertEqual(result.shape, (1, 256))
        self.assertEqual(result[0, 0], .5)
        self.assertEqual(result[0, 255], .5)
        self.assertEqual(float(result.sum()), 1.0)

    def test_group_metadata_means_and_protocol_fractions_reconcile(self):
        arrays = self.data["cic"]
        values = self.controls._metadata_features(self.data_directory, "cic", arrays, arrays[0])
        for position, index in enumerate(arrays[0]):
            self.assertAlmostEqual(values[position, 0], float(arrays["payload"][index, 0]) + 1.5)
            self.assertEqual(values[position, 1], 1500.)
            self.assertAlmostEqual(values[position, 2], .15)
            self.assertEqual(values[position, 3:].tolist(), [.25] * 4)
        metadata = self.data_directory / "cic/metadata.csv"
        with metadata.open() as stream:
            rows = list(csv.reader(stream))
        rows[1][-1] = "1"
        with metadata.open("w", newline="") as stream:
            csv.writer(stream).writerows(rows)
        with self.assertRaisesRegex(ValueError, "label"):
            self.controls._metadata_features(self.data_directory, "cic", arrays, arrays[0])

    def test_soft_targets_and_joint_source_mass_are_preserved(self):
        counts = self.np.array([[3, 1], [0, 9], [2, 2]])
        weights = self.controls._source_weights([2, 1])
        self.assertEqual(weights.tolist(), [.75, .75, 1.5])
        features = self.np.array([[1.], [2.], [3.]])
        repeated, labels, sample_weights = self.controls._soft_training_rows(features, counts, weights)
        self.assertEqual(labels.tolist(), [0, 1, 0, 1, 0, 1])
        self.assertEqual(repeated[:, 0].tolist(), [1., 1., 2., 2., 3., 3.])
        self.assertEqual(sample_weights.tolist(), [.5625, .1875, 0., .75, .75, .75])
        self.assertEqual(float(sample_weights[:4].sum()), float(sample_weights[4:].sum()))

    def test_portable_linear_scores_apply_saved_scaler_and_intercept(self):
        model = {"kind": "metadata_linear", "scaler": {"mean": [10., 2., 0., 0., 0., 0., 0.],
                 "scale": [2., 4., 1., 1., 1., 1., 1.]},
                 "coef": [2., 3., 0., 0., 0., 0., 0.], "intercept": -.5}
        features = self.np.array([[12., 4., 0., 0., 0., 0., 0.], [10., 2., 0., 0., 0., 0., 0.]])
        self.assertEqual(self.controls._scores(model, features, 2).tolist(), [3., -.5])

    def test_public_fit_interface_works_as_tools_module(self):
        command = ("from tools.packet_controls import fit_controls; import sys; "
                   "fit_controls(sys.argv[1], sys.argv[2], 'c' * 64)")
        result = subprocess.run([sys.executable, "-c", command, str(self.data_directory),
                                 str(self.base / "module-controls")], cwd=ROOT,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_train_only_freeze_portable_reload_and_strict_evaluation(self):
        output = self.base / "controls"
        frozen = self.controls.fit_controls(self.data_directory, output, "a" * 64)
        self.assertEqual(len(frozen["models"]), 9)
        self.assertFalse((output / "evaluation").exists())
        self.assertFalse(list(output.rglob("*.gz")))
        for name, descriptor in frozen["models"].items():
            model = json.loads((output / descriptor["path"]).read_text())
            self.assertEqual(model["classes"], [0, 1])
            if model["kind"] == "metadata_linear":
                self.assertLess(model["scaler"]["mean"][0], 256)
            if model["kind"] != "majority":
                self.assertTrue(model["convergence"]["converged"])
                self.assertEqual(model["settings"]["C"], 1.)
        result = self.controls.evaluate_controls(self.data_directory, output)
        self.assertEqual(len(result["results"]), 9)
        for model in result["results"]:
            self.assertEqual(set(model["tests"]), {"cic", "unsw"})
            for source, details in model["tests"].items():
                self.assertEqual(details["metrics"]["rows"], 4)
                self.assertEqual(details["metrics"]["groups"], 1)
        with self.assertRaises(FileExistsError):
            self.controls.evaluate_controls(self.data_directory, output)

    def test_changed_frozen_model_is_rejected_before_evaluation_output(self):
        output = self.base / "controls"
        frozen = self.controls.fit_controls(self.data_directory, output, "b" * 64)
        model = output / next(iter(frozen["models"].values()))["path"]
        model.write_text(model.read_text() + " ")
        with self.assertRaisesRegex(ValueError, "fingerprint"):
            self.controls.evaluate_controls(self.data_directory, output)
        self.assertFalse((output / "evaluation").exists())


if __name__ == "__main__":
    unittest.main()
