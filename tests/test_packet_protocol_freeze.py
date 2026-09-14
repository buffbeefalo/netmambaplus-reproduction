"""Protocol freezing must bind the original uploads before any measured fit."""

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import packet_data
from tools import freeze_packet_protocol as freezing
from tools import train_packet_model as training


class PacketProtocolFreezeTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.data = self.root / "prepared"
        self.data.mkdir()
        self.output = self.root / "protocol.json"
        self.manifest = {"schema_version": 1, "status": "prepared", "labels": copy.deepcopy(packet_data.LABELS),
                         "sources": {source: {"sha256": digest, "matches_registered_source": True} for source, digest in
                                     packet_data.REGISTERED_SOURCE_HASHES.items()}}
        self.save_manifest()

    def save_manifest(self):
        (self.data / "manifest.json").write_text(json.dumps(self.manifest))

    def test_freeze_binds_bytes_and_the_six_prespecified_comparisons(self):
        protocol = freezing.freeze(self.data, self.output)
        self.assertEqual(protocol, json.loads(self.output.read_text()))
        self.assertEqual(protocol["purpose"], "measured")
        self.assertEqual(protocol["data_manifest_sha256"], hashlib.sha256(
            (self.data / "manifest.json").read_bytes()).hexdigest())
        self.assertEqual(protocol["arms"], [
            {"name": "cic_pretrained", "sources": ["cic"], "initialization": "pretrained"},
            {"name": "cic_scratch", "sources": ["cic"], "initialization": "scratch"},
            {"name": "unsw_pretrained", "sources": ["unsw"], "initialization": "pretrained"},
            {"name": "unsw_scratch", "sources": ["unsw"], "initialization": "scratch"},
            {"name": "joint_pretrained", "sources": ["cic", "unsw"], "initialization": "pretrained"},
            {"name": "joint_scratch", "sources": ["cic", "unsw"], "initialization": "scratch"},
        ])
        self.assertEqual((protocol["steps"], protocol["batch_size"], protocol["validation_interval"]),
                         (1000, 64, 100))
        for name in ("packet_data.py", "packet_model.py", "packet_study.py", "tools/train_packet_model.py"):
            self.assertEqual(protocol["code_sha256"][name], hashlib.sha256((freezing.ROOT / name).read_bytes()).hexdigest())
        training.check_protocol(protocol, self.data)

    def test_measured_freeze_rejects_a_different_input_export(self):
        self.manifest["sources"]["cic"]["sha256"] = "f" * 64
        self.save_manifest()
        with self.assertRaisesRegex(ValueError, "source|upload|registered"):
            freezing.freeze(self.data, self.output)
        self.assertFalse(self.output.exists())

    def test_measured_freeze_requires_the_successful_original_source_identity_check(self):
        self.manifest["sources"]["unsw"]["matches_registered_source"] = False
        self.save_manifest()
        with self.assertRaisesRegex(ValueError, "source|CSV|registered"):
            freezing.freeze(self.data, self.output)
        self.assertFalse(self.output.exists())

    def test_incomplete_preparation_and_invalid_budgets_do_not_create_protocols(self):
        self.manifest["status"] = "preparing"
        self.save_manifest()
        with self.assertRaisesRegex(ValueError, "incomplete"):
            freezing.freeze(self.data, self.output)
        self.assertFalse(self.output.exists())
        self.manifest["status"] = "prepared"
        self.save_manifest()
        for steps in (True, 0, 99, 101, 1100, 100.0):
            with self.subTest(steps=steps), self.assertRaises(ValueError):
                freezing.freeze(self.data, self.output, steps=steps)
            self.assertFalse(self.output.exists())

    def test_existing_protocol_is_never_overwritten(self):
        original = b"Existing frozen protocol\n"
        self.output.write_bytes(original)
        with self.assertRaises(FileExistsError):
            freezing.freeze(self.data, self.output)
        self.assertEqual(self.output.read_bytes(), original)

    def test_timing_budget_mismatch_cannot_silently_change_the_protocol(self):
        timing = self.root / "timing.json"
        timing.write_text(json.dumps({"chosen_updates_per_arm": 200}))
        with self.assertRaisesRegex(ValueError, "timing"):
            freezing.freeze(self.data, self.output, steps=100, timing=timing)
        self.assertFalse(self.output.exists())

    def test_trainer_rejects_a_changed_manifest_after_freezing(self):
        protocol = freezing.freeze(self.data, self.output)
        self.manifest["notes"] = "Data identity changed after the protocol was written"
        self.save_manifest()
        with self.assertRaisesRegex(ValueError, "manifest changed"):
            training.check_protocol(protocol, self.data)

    def test_trainer_rejects_missing_and_mismatched_code_fingerprints(self):
        protocol = freezing.freeze(self.data, self.output)
        original = copy.deepcopy(protocol)
        protocol["code_sha256"].pop("packet_data.py")
        with self.assertRaisesRegex(ValueError, "complete study implementation"):
            training.check_protocol(protocol, self.data)
        protocol = original
        protocol["code_sha256"]["packet_data.py"] = "f" * 64
        with self.assertRaisesRegex(ValueError, "implementation changed"):
            training.check_protocol(protocol, self.data)


if __name__ == "__main__":
    unittest.main()
