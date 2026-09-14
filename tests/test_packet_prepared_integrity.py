"""Reject prepared data that no longer proves its declared payload partition."""

import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import packet_data
from tools import train_packet_model as training
from tests.test_packet_data import payload, write_source


@unittest.skipUnless(importlib.util.find_spec("numpy"), "Prepared-data verification requires optional NumPy")
class PreparedPacketIntegrityTests(unittest.TestCase):
    def setUp(self):
        import numpy as np
        self.np = np
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.output = self.root / "prepared"
        for source, benign, attack in [("cic", "BENIGN", "DoS Hulk"), ("unsw", "normal", "generic")]:
            rows = [(payload(tag), label) for tag in range(32) for label in (benign, attack)]
            write_source(self.root / f"{source}.csv", rows)
        self.manifest = copy.deepcopy(packet_data.prepare(
            self.root / "cic.csv", self.root / "unsw.csv", self.output,
            max_train_groups=4, max_eval_groups=2))

    def save_manifest(self):
        (self.output / "manifest.json").write_text(json.dumps(self.manifest))

    def array(self, source, name):
        return self.np.load(self.output / source / f"{name}.npy", allow_pickle=False)

    def change_array(self, source, name, values, *, rebind=True):
        path = self.output / source / f"{name}.npy"
        with path.open("wb") as stream:
            self.np.save(stream, values, allow_pickle=False)
        if rebind:
            self.manifest["sources"][source]["files"][f"{name}.npy"].update(
                sha256=hashlib.sha256(path.read_bytes()).hexdigest(), bytes=path.stat().st_size,
                dtype=str(values.dtype), shape=list(values.shape))
            self.save_manifest()

    def reject(self, message):
        with self.assertRaisesRegex(ValueError, message):
            training.load_data(self.output)

    def test_real_preparation_loads_with_fixed_capped_memberships(self):
        data, manifest = training.load_data(self.output)
        self.assertEqual(manifest, self.manifest)
        for source in ("cic", "unsw"):
            self.assertEqual([len(data[source][split]) for split in (0, 1, 2)], [4, 2, 2])
            self.assertEqual(data[source]["counts"].sum(axis=0).tolist(), [32, 32])

    def test_omitting_a_payload_fingerprint_cannot_bypass_byte_drift(self):
        self.manifest["sources"]["cic"]["files"].pop("payload.npy")
        self.save_manifest()
        values = self.array("cic", "payload")
        values[0, 0] ^= 1
        self.change_array("cic", "payload", values, rebind=False)
        self.reject("file.*set|file.*inventory")

    def test_fingerprint_for_a_different_source_cannot_cover_the_loaded_path(self):
        self.manifest["sources"]["cic"]["files"]["payload.npy"] = copy.deepcopy(
            self.manifest["sources"]["unsw"]["files"]["payload.npy"])
        self.save_manifest()
        values = self.array("cic", "payload")
        values[0, 0] ^= 1
        self.change_array("cic", "payload", values, rebind=False)
        self.reject("path")

    def test_rehashed_payload_array_cannot_introduce_train_test_duplicates(self):
        splits = self.array("cic", "split")
        train = self.np.flatnonzero(splits == 0)[0]
        test = self.np.flatnonzero(splits == 2)[0]
        values = self.array("cic", "payload")
        values[train] = values[test]
        self.change_array("cic", "payload", values)
        self.reject("payload.*identity|payload.*hash")

    def test_hashes_must_be_unique_and_sorted(self):
        original = self.array("cic", "hashes")
        for duplicate in (True, False):
            values = original.copy()
            if duplicate:
                values[1] = values[0]
            else:
                values[[0, 1]] = values[[1, 0]]
            self.change_array("cic", "hashes", values)
            with self.subTest(duplicate=duplicate):
                self.reject("unique|sorted")

    def test_matching_cross_source_split_edits_still_violate_the_fixed_hash_rule(self):
        splits = self.array("cic", "split")
        index = self.np.flatnonzero(splits == 0)[-1]
        splits[index] = 2
        for source in ("cic", "unsw"):
            self.change_array(source, "split", splits)
        self.reject("split.*rule|deterministic.*split")

    def test_selection_cannot_exchange_groups_within_the_same_split(self):
        selected = self.array("cic", "selected")
        splits = self.array("cic", "split")
        chosen = self.np.flatnonzero((splits == 0) & selected)[0]
        omitted = self.np.flatnonzero((splits == 0) & ~selected)[0]
        selected[chosen], selected[omitted] = False, True
        self.change_array("cic", "selected", selected)
        self.reject("selection|selected")

    def test_count_dtypes_and_negative_counts_are_rejected_before_training(self):
        original = self.array("cic", "counts")
        for values in (original.astype(self.np.float64), original.astype(self.np.bool_),
                       self.np.tile([-1, 3], (len(original), 1))):
            self.change_array("cic", "counts", values)
            with self.subTest(dtype=str(values.dtype)):
                self.reject("dtype|negative|counts")

    def test_binary_counts_cannot_disagree_with_original_label_counts(self):
        values = self.array("cic", "counts")
        values[0] = [0, 2]
        self.change_array("cic", "counts", values)
        self.reject("subtype|original.label|binary.*counts")

    def test_array_shapes_and_declared_dtypes_are_bound(self):
        self.manifest["sources"]["cic"]["files"]["hashes.npy"]["dtype"] = "uint8"
        self.save_manifest()
        self.reject("dtype")
        self.manifest["sources"]["cic"]["files"]["hashes.npy"]["dtype"] = "|V32"
        self.save_manifest()
        self.change_array("cic", "selected", self.array("cic", "selected").reshape(-1, 1))
        self.reject("shape")

    def test_label_order_and_observed_source_identity_declarations_are_bound(self):
        original = copy.deepcopy(self.manifest)
        self.manifest["labels"]["cic"][0:2] = self.manifest["labels"]["cic"][1::-1]
        self.save_manifest()
        self.reject("label")
        self.manifest = copy.deepcopy(original)
        self.manifest["sources"]["cic"]["matches_registered_source"] = True
        self.save_manifest()
        self.reject("source.*identity|registered.*source")
        self.manifest = copy.deepcopy(original)
        self.manifest["sources"]["cic"]["registered_source_sha256"] = "f" * 64
        self.save_manifest()
        self.reject("source.*identity|registered.*source")

    def test_declared_source_and_split_support_must_match_the_arrays(self):
        original = copy.deepcopy(self.manifest)
        self.manifest["sources"]["cic"]["rows"] += 1
        self.save_manifest()
        self.reject("support|rows")
        self.manifest = copy.deepcopy(original)
        self.manifest["sources"]["cic"]["splits"]["train"]["selected_membership_sha256"] = "f" * 64
        self.save_manifest()
        self.reject("support|membership")

    def test_reloading_rejects_a_mapped_payload_changed_since_initial_verification(self):
        data, _ = training.load_data(self.output)
        index = int(data["cic"][0][0])
        values = self.array("cic", "payload")
        values[index, 0] ^= 1
        self.change_array("cic", "payload", values, rebind=False)
        self.reject("fingerprint")


if __name__ == "__main__":
    unittest.main()
