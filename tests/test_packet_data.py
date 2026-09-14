"""Packet contracts run without ML packages; preparation fixtures use NumPy if present."""

import csv
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
try:
    import packet_data as packet
except ModuleNotFoundError as error:
    if error.name != "packet_data":
        raise
    packet = None

HAS_NUMPY = importlib.util.find_spec("numpy") is not None
HEADER = [f"payload_byte_{index}" for index in range(1, 1501)] + [
    "ttl", "total_len", "protocol", "t_delta", "label"
]


def payload(tag=0):
    return tag.to_bytes(2, "big") + bytes(1498)


def write_source(path, rows, *, header=None):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(HEADER if header is None else header)
        for values, label in rows:
            writer.writerow(list(values) + ["064", "23400", "tcp", "-0.000013", label])


class PacketContractTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(packet, "packet_data module is not implemented")

    def test_import_and_cli_help_need_only_standard_library(self):
        result = subprocess.run(
            [sys.executable, "-S", str(ROOT / "packet_data.py"), "--help"],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--max-eval-groups", result.stdout)
        result = subprocess.run(
            [sys.executable, "-S", "-c", "import packet_data; import sys; "
             "assert 'numpy' not in sys.modules; assert 'pandas' not in sys.modules"],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_all_observed_labels_map_explicitly(self):
        profile = json.loads((ROOT / "docs/customer/evidence/uploaded-csv-profile.json").read_text())
        for source, record in zip(("cic", "unsw"), profile["files"]):
            labels = [entry["label"] for entry in record["labels"]]
            self.assertEqual(list(packet.LABELS[source]), labels)
            for index, label in enumerate(labels):
                self.assertEqual(packet.binary_label(source, label), int(index != 0))

    def test_unknown_source_or_label_cannot_become_an_attack(self):
        for source, label in [("other", "BENIGN"), ("cic", "normal"),
                              ("unsw", "BENIGN"), ("cic", "BENIGN "),
                              ("cic", "benign"), ("unsw", "new_attack"),
                              (None, "normal"), ("unsw", None)]:
            with self.subTest(source=source, label=label), self.assertRaises(ValueError):
                packet.binary_label(source, label)

    def test_integer_valued_slots_keep_all_stored_zeros(self):
        values = [0, "255", 1.0, Decimal("2.000"), "3e0", "0.000"] + [0] * 1494
        self.assertEqual(packet.validate_payload(values), bytes([0, 255, 1, 2, 3]) + bytes(1495))
        self.assertEqual(packet.validate_payload(payload(7)), payload(7))

    def test_payload_shape_must_be_exactly_1500(self):
        for value in [[], [0] * 1499, [0] * 1501, "0" * 1500, None]:
            with self.subTest(value_type=type(value).__name__), self.assertRaises(ValueError):
                packet.validate_payload(value)

    def test_invalid_slots_cannot_be_cast_or_rounded_into_valid_bytes(self):
        invalid = [True, False, None, "", "bad", "1_0", "nan", "NaN", "inf", "-inf",
                   float("nan"), float("inf"), -1, 256, 1.5, "1.5",
                   "1.00000000000000000001", "255.00000000000000000001",
                   "1e-9999", Decimal("0.0000000000000000001"), complex(1, 0)]
        for value in invalid:
            with self.subTest(value=repr(value)), self.assertRaises(ValueError):
                packet.validate_payload([value] + [0] * 1499)

    def test_payload_identity_is_sha256_of_exact_bytes(self):
        self.assertEqual(packet.payload_hash(payload()),
                         "6249da5c681dd8a542b8e38150a3026e02385d590a9dd94f4f83940fd856ee73")
        self.assertNotEqual(packet.payload_hash(payload(1)), packet.payload_hash(payload(2)))
        for invalid in [b"", b"0" * 1499, [0] * 1500, "0" * 1500]:
            with self.subTest(kind=type(invalid).__name__), self.assertRaises(ValueError):
                packet.payload_hash(invalid)

    def test_split_has_fixed_vectors_for_all_three_partitions(self):
        vectors = {
            "6249da5c681dd8a542b8e38150a3026e02385d590a9dd94f4f83940fd856ee73": 2,
            "14faebeb8396ce5e53c4875369c64e8816dbc575dfdd2a6b695fa9cd7b40a6d1": 0,
            "f07d2f2f5f1e28b9f334f66177b650371eba9379f81283937c366ca80a8247ec": 1,
        }
        for digest, expected in vectors.items():
            self.assertEqual(packet.split_for_hash(digest), expected)
            self.assertEqual(packet.split_for_hash(digest, seed=17), expected)

    def test_invalid_digest_and_seed_fail_before_assignment(self):
        for digest in [None, "", "f" * 63, "g" * 64, "F" * 64, "0 " * 32, bytes(32)]:
            with self.subTest(digest=repr(digest)), self.assertRaises(ValueError):
                packet.split_for_hash(digest)
        for seed in [True, False, -1, 17.0, "17", None]:
            with self.subTest(seed=seed), self.assertRaises(ValueError):
                packet.split_for_hash("0" * 64, seed=seed)

    def test_caps_are_validated_before_dependencies_or_files(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            for key in ["max_train_groups", "max_eval_groups"]:
                for cap in [True, False, 0, -1, 1.5, "2", None]:
                    with self.subTest(key=key, cap=cap), self.assertRaises(ValueError):
                        packet.prepare(base / "missing-cic", base / "missing-unsw",
                                       base / "output", **{key: cap})
                    self.assertFalse((base / "output").exists())

    def test_existing_outputs_and_broken_symlinks_are_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            output = base / "output"
            output.mkdir()
            sentinel = output / "manifest.json"
            sentinel.write_text("prior result")
            with self.assertRaises(FileExistsError):
                packet.prepare(base / "missing-cic", base / "missing-unsw", output)
            self.assertEqual(sentinel.read_text(), "prior result")
            link = base / "link"
            link.symlink_to(base / "missing-target")
            with self.assertRaises(FileExistsError):
                packet.prepare(base / "missing-cic", base / "missing-unsw", link)
            self.assertTrue(link.is_symlink())


@unittest.skipUnless(HAS_NUMPY, "NumPy is optional; contract tests remain dependency-free")
class PacketPreparationTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(packet, "packet_data module is not implemented")
        import numpy as np
        self.np = np
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.cic = self.base / "cic.csv"
        self.unsw = self.base / "unsw.csv"
        self.rows = {
            "cic": [(payload(tag), "BENIGN" if tag % 2 == 0 else "DoS Hulk") for tag in range(16)]
                   + [(payload(0), "DoS Hulk"), (payload(0), "DoS Hulk")],
            "unsw": [(payload(tag), "generic" if tag % 2 == 0 else "normal") for tag in range(16)]
                    + [(payload(0), "normal")],
        }
        self.write()

    def write(self):
        write_source(self.cic, self.rows["cic"])
        write_source(self.unsw, self.rows["unsw"])

    def prepare(self, name="prepared", **options):
        output = self.base / name
        manifest = packet.prepare(self.cic, self.unsw, output, **options)
        arrays = {
            source: {name: self.np.load(output / source / f"{name}.npy", allow_pickle=False)
                     for name in ("payload", "hashes", "counts", "subtypes", "split", "selected")}
            for source in ("cic", "unsw")
        }
        return output, manifest, arrays

    def test_cross_source_duplicates_and_conflicting_labels_retain_every_count(self):
        output, manifest, arrays = self.prepare()
        self.assertEqual(manifest, json.loads((output / "manifest.json").read_text()))
        for source, rows, binary in [("cic", 18, [8, 10]), ("unsw", 17, [9, 8])]:
            with self.subTest(source=source):
                data = arrays[source]
                self.assertEqual(data["payload"].shape, (16, 1500))
                self.assertEqual(data["payload"].dtype, self.np.dtype("uint8"))
                self.assertEqual(data["hashes"].dtype, self.np.dtype("V32"))
                self.assertEqual(data["counts"].dtype, self.np.dtype("int64"))
                self.assertEqual(data["subtypes"].shape, (16, len(packet.LABELS[source])))
                self.assertEqual(data["subtypes"].dtype, self.np.dtype("int64"))
                self.assertEqual(data["split"].dtype, self.np.dtype("uint8"))
                self.assertEqual(data["selected"].dtype, self.np.dtype("bool"))
                self.assertEqual(data["counts"].sum(axis=0).tolist(), binary)
                self.assertEqual(int(data["subtypes"].sum()), rows)
                self.assertTrue(data["selected"].all())
                hashes = [value.tobytes() for value in data["hashes"]]
                self.assertEqual(hashes, sorted(hashes))
                for index, values in enumerate(data["payload"]):
                    self.assertEqual(hashlib.sha256(values.tobytes()).digest(), hashes[index])
                zero = hashes.index(hashlib.sha256(payload(0)).digest())
                expected = [1, 2] if source == "cic" else [1, 1]
                self.assertEqual(data["counts"][zero].tolist(), expected)
                record = manifest["sources"][source]
                self.assertEqual(record["rows"], rows)
                self.assertEqual(record["groups"], 16)
                self.assertEqual(record["binary_counts"], binary)
                self.assertEqual(record["binary_conflicting_groups"], 1)
        self.assertEqual(arrays["cic"]["hashes"].tolist(), arrays["unsw"]["hashes"].tolist())
        self.assertEqual(arrays["cic"]["split"].tolist(), arrays["unsw"]["split"].tolist())
        self.assertEqual(manifest["global"]["groups"], 16)
        self.assertEqual(manifest["global"]["rows"], 35)
        self.assertEqual(manifest["global"]["shared_groups"], 16)
        self.assertEqual(manifest["global"]["shared_binary_conflicting_groups"], 16)
        self.assertEqual(manifest["global"]["largest_group_rows"], 5)

    def test_original_row_metadata_remains_traceable_and_lexically_unchanged(self):
        output, _, arrays = self.prepare()
        with (output / "cic/metadata.csv").open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 18)
        for index, row in enumerate(rows):
            self.assertEqual(int(row["row_id"]), index)
            self.assertEqual(row["label"], self.rows["cic"][index][1])
            self.assertEqual(row["ttl"], "064")
            self.assertEqual(row["total_len"], "23400")
            self.assertEqual(row["t_delta"], "-0.000013")
            self.assertEqual(row["payload_sha256"], hashlib.sha256(self.rows["cic"][index][0]).hexdigest())
        self.assertEqual(rows[0]["payload_sha256"], rows[-1]["payload_sha256"])
        self.assertEqual(arrays["cic"]["payload"].shape[1], 1500)

    def test_caps_choose_fixed_hash_order_and_report_exact_membership_and_support(self):
        output, manifest, arrays = self.prepare(max_train_groups=2, max_eval_groups=1)
        for source in ("cic", "unsw"):
            data = arrays[source]
            selected_tags = sorted(int.from_bytes(row[:2].tobytes(), "big")
                                   for row in data["payload"][data["selected"]])
            self.assertEqual(selected_tags, [1, 2, 6, 11])
            for split, name, expected_groups in [(0, "train", 2), (1, "validation", 1), (2, "test", 1)]:
                mask = (data["split"] == split) & data["selected"]
                expected_hash = hashlib.sha256(b"".join(value.tobytes() for value in data["hashes"][mask])).hexdigest()
                record = manifest["sources"][source]["splits"][name]
                self.assertEqual(record["selected_groups"], expected_groups)
                self.assertEqual(record["selected_rows"], expected_groups)
                self.assertEqual(record["selected_binary_counts"], data["counts"][mask].sum(axis=0).tolist())
                self.assertEqual(record["selected_membership_sha256"], expected_hash)
            for filename, record in manifest["sources"][source]["files"].items():
                path = output / record["path"]
                self.assertEqual(path, output / source / filename)
                self.assertEqual(record["bytes"], path.stat().st_size)
                self.assertEqual(record["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
            source_path = self.cic if source == "cic" else self.unsw
            self.assertEqual(manifest["sources"][source]["sha256"], hashlib.sha256(source_path.read_bytes()).hexdigest())

    def test_source_labels_metadata_row_order_and_duplicates_cannot_change_split_or_selection(self):
        _, _, original = self.prepare("original", max_train_groups=2, max_eval_groups=1)
        self.rows["cic"] = [(values, "Heartbleed") for values, _ in reversed(self.rows["cic"])]
        self.rows["unsw"] = [(values, "worms") for values, _ in reversed(self.rows["unsw"])]
        self.rows["cic"] += [(payload(6), "BENIGN")] * 20
        self.write()
        self.cic.write_text(self.cic.read_text().replace(",064,23400,tcp,-0.000013,", ",255,1,undocumented,99999,"))
        _, _, changed = self.prepare("changed", max_train_groups=2, max_eval_groups=1)
        for source in ("cic", "unsw"):
            for name in ("payload", "hashes", "split", "selected"):
                self.assertTrue(self.np.array_equal(original[source][name], changed[source][name]), (source, name))
        self.assertTrue(self.np.array_equal(changed["cic"]["split"], changed["unsw"]["split"]))

    def test_schema_drift_unknown_labels_and_row_width_errors_fail(self):
        cases = [
            (HEADER[:-1], [(payload(), "BENIGN")]),
            (["payload_byte_2"] + HEADER[1:], [(payload(), "BENIGN")]),
            (HEADER[::-1], [(payload(), "BENIGN")]),
            (HEADER, [(payload(), "new_attack")]),
            (HEADER, [(payload()[:-1], "BENIGN")]),
            (HEADER, [(payload() + b"\x00", "BENIGN")]),
        ]
        for index, (header, rows) in enumerate(cases):
            write_source(self.cic, rows, header=header)
            output = self.base / f"invalid-{index}"
            with self.subTest(index=index), self.assertRaises(ValueError):
                packet.prepare(self.cic, self.unsw, output)
            self.assertFalse((output / "manifest.json").exists())

    def test_preparation_validates_every_slot_before_uint8_cast(self):
        for index, value in enumerate(["nan", "inf", "-inf", "False", "bad", "", -1, 256,
                                       "1.5", "1.00000000000000000001", "1e-9999"]):
            row = [0] * 1500
            row[-1] = value
            write_source(self.cic, [(row, "BENIGN")])
            output = self.base / f"bad-payload-{index}"
            with self.subTest(value=value), self.assertRaises(ValueError):
                packet.prepare(self.cic, self.unsw, output)
            self.assertFalse((output / "manifest.json").exists())

    def test_empty_source_is_rejected(self):
        write_source(self.cic, [])
        with self.assertRaises(ValueError):
            packet.prepare(self.cic, self.unsw, self.base / "empty")

    def test_cli_prepares_both_sources_with_declared_caps(self):
        output = self.base / "cli"
        result = subprocess.run(
            [sys.executable, str(ROOT / "packet_data.py"), "--cic", str(self.cic),
             "--unsw", str(self.unsw), "--output", str(output), "--seed", "17",
             "--max-train-groups", "2", "--max-eval-groups", "1"],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        manifest = json.loads((output / "manifest.json").read_text())
        self.assertEqual(manifest["sources"]["cic"]["rows"], 18)
        self.assertEqual(manifest["sources"]["unsw"]["rows"], 17)
        self.assertEqual(manifest["sources"]["cic"]["splits"]["train"]["selected_groups"], 2)


if __name__ == "__main__":
    unittest.main()
