"""Reject modified, incomplete and unsafe delivered inventories."""

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ClientVerificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        raw = b"Client instructions\n"
        (self.root / "README.md").write_bytes(raw)
        self.manifest = {"schema": 1,
                         "source_repository": "https://github.com/buffbeefalo/netmambaplus-reproduction",
                         "source_commit": "a" * 40, "selection_sha256": "b" * 64,
                         "exporter_sha256": "c" * 64,
                         "files": {"README.md": {"source_path": "client/README.md.in",
                                                   "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}}}
        self.save()

    def save(self):
        (self.root / "CLIENT_MANIFEST.json").write_text(json.dumps(self.manifest), encoding="utf-8")

    def check(self):
        return subprocess.run([sys.executable, str(ROOT / "tools/verify_client.py"),
                               "--root", str(self.root), "--inventory-only"],
                              text=True, capture_output=True)

    def test_complete_source_zip_inventory_passes_without_git(self):
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_modified_delivered_bytes_are_rejected(self):
        (self.root / "README.md").write_bytes(b"changed\n")
        self.assertNotEqual(self.check().returncode, 0)

    def test_omitted_file_is_rejected(self):
        (self.root / "README.md").unlink()
        self.assertNotEqual(self.check().returncode, 0)

    def test_unlisted_file_is_rejected(self):
        (self.root / "unlisted.mp4").write_bytes(b"excluded media")
        self.assertNotEqual(self.check().returncode, 0)

    def test_local_runtime_outputs_do_not_invalidate_delivery(self):
        (self.root / "runs").mkdir()
        (self.root / "runs/results.json").write_bytes(b"{}")
        self.assertEqual(self.check().returncode, 0)

    def test_unsafe_inventory_path_is_rejected(self):
        self.manifest["files"]["../README.md"] = self.manifest["files"].pop("README.md")
        self.save()
        self.assertNotEqual(self.check().returncode, 0)

    def test_invalid_source_identity_is_rejected(self):
        self.manifest["source_commit"] = "main"
        self.save()
        self.assertNotEqual(self.check().returncode, 0)


class ClientFlowEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        origin = ROOT / "docs/customer/evidence"
        self.evidence = self.root / "docs/customer/evidence"
        self.evidence.mkdir(parents=True)
        self.index = json.loads((origin / "artifact-index.json").read_bytes())
        for item in self.index["files"]:
            path = self.evidence / item["path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(origin / item["path"], path)
        shutil.copyfile(origin / "artifact-index.json", self.evidence / "artifact-index.json")
        spec = importlib.util.spec_from_file_location("client_flow_verifier", ROOT / "tools/verify_client.py")
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def corrupt_and_reindex(self, key, value):
        path = self.evidence / "results.json"
        data = json.loads(path.read_bytes())
        if key == "accuracy":
            data["seeds"][0]["metrics"][key] = value
        else:
            data["seeds"][0][key] = value
        path.write_text(json.dumps(data), encoding="utf-8")
        for item in self.index["files"]:
            if item["path"] == "results.json":
                item.update(bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        (self.evidence / "artifact-index.json").write_text(json.dumps(self.index), encoding="utf-8")

    def test_reindexed_false_accuracy_is_rejected_by_prediction_arithmetic(self):
        self.module.verify_flow(self.root)
        self.corrupt_and_reindex("accuracy", 1.0)
        with self.assertRaisesRegex(ValueError, "metric disagreement"):
            self.module.verify_flow(self.root)

    def test_reindexed_incomplete_training_is_rejected(self):
        self.module.verify_flow(self.root)
        self.corrupt_and_reindex("completed_epochs", 1)
        with self.assertRaisesRegex(ValueError, "Incomplete flow training"):
            self.module.verify_flow(self.root)


if __name__ == "__main__":
    unittest.main()
