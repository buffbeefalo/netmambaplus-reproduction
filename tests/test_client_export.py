"""Exercise publication boundaries using real temporary Git repositories."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ClientExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.source = self.base / "source"
        self.source.mkdir()
        self.client = self.base / "client"
        self.git(self.source, "init", "-b", "main")
        self.spec = {"schema": 1, "files": ["repro.py"],
                     "templates": {"README.md": "client/README.md.in"}}
        self.write("repro.py", b"print('model')\n")
        self.write("client/README.md.in", b"Client instructions\n")
        self.write("tools/export_client.py", b"# Fixture source exporter identity\n")
        self.write("private.csv", b"do not publish\n")
        self.write_spec()
        self.first = self.commit(self.source)

    def git(self, root, *args):
        return subprocess.check_output(
            ["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
             "-c", "core.autocrlf=false", "-C", str(root), *args],
            stderr=subprocess.PIPE, text=True).strip()

    def write(self, name, content):
        path = self.source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def write_spec(self):
        self.write("configs/client-manifest.json", json.dumps(self.spec).encode())

    def commit(self, root):
        self.git(root, "add", "--all")
        self.git(root, "commit", "-m", "Fixture update")
        return self.git(root, "rev-parse", "HEAD")

    def export(self, revision=None, output=None):
        return subprocess.run(
            [sys.executable, str(ROOT / "tools/export_client.py"), "--source", str(self.source),
             "--revision", revision or self.first, "--output", str(output or self.client)],
            text=True, capture_output=True)

    def initialize_client(self):
        result = self.export()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.git(self.client, "init", "-b", "main")
        self.commit(self.client)

    def sync(self, revision):
        return subprocess.run(
            [sys.executable, str(ROOT / "tools/sync_client.py"), "--source", str(self.source),
             "--destination", str(self.client), "--revision", revision],
            text=True, capture_output=True)

    def test_export_uses_committed_bytes_and_excludes_unlisted_files(self):
        self.write("repro.py", b"uncommitted edit\n")
        result = self.export()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.client / "repro.py").read_bytes(), b"print('model')\n")
        self.assertFalse((self.client / "private.csv").exists())
        manifest = json.loads((self.client / "CLIENT_MANIFEST.json").read_bytes())
        self.assertEqual(manifest["source_commit"], self.first)
        self.assertEqual(manifest["files"]["repro.py"]["sha256"],
                         hashlib.sha256(b"print('model')\n").hexdigest())

    def test_export_is_deterministic(self):
        a, b = self.client, self.base / "second"
        self.assertEqual(self.export(output=a).returncode, 0)
        self.assertEqual(self.export(output=b).returncode, 0)
        self.assertEqual((a / "CLIENT_MANIFEST.json").read_bytes(),
                         (b / "CLIENT_MANIFEST.json").read_bytes())

    def test_missing_file_refuses_to_create_output(self):
        self.spec["files"].append("missing.py")
        self.write_spec()
        result = self.export(self.commit(self.source))
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.client.exists())

    def test_media_and_unsafe_paths_cannot_be_allowlisted(self):
        for name in ("docs/customer/evidence/video.mp4", "../outside.py", ".git/config", "a\\b.py"):
            with self.subTest(name=name):
                self.spec["files"] = ["repro.py", name]
                self.write_spec()
                result = self.export(self.commit(self.source))
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(self.client.exists())

    def test_unexpected_evidence_extension_is_rejected_even_when_unlisted(self):
        self.write("docs/customer/evidence/presentation.pptx", b"not evidence\n")
        result = self.export(self.commit(self.source))
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.client.exists())

    def test_symlink_blob_is_rejected(self):
        blob = subprocess.check_output(["git", "-C", str(self.source), "hash-object", "-w", "--stdin"],
                                       input=b"private.csv\n").decode().strip()
        self.git(self.source, "update-index", "--add", "--cacheinfo", "120000", blob, "link.py")
        self.spec["files"].append("link.py")
        self.write_spec()
        self.git(self.source, "add", "configs/client-manifest.json")
        self.git(self.source, "commit", "-m", "Fixture symlink")
        result = self.export(self.git(self.source, "rev-parse", "HEAD"))
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.client.exists())

    def test_existing_output_is_preserved(self):
        self.client.mkdir()
        (self.client / "keep.txt").write_bytes(b"keep\n")
        self.assertNotEqual(self.export().returncode, 0)
        self.assertEqual((self.client / "keep.txt").read_bytes(), b"keep\n")

    def test_executable_mode_is_recorded_and_preserved(self):
        self.git(self.source, "update-index", "--chmod=+x", "repro.py")
        self.git(self.source, "commit", "-m", "Executable entry point")
        result = self.export(self.git(self.source, "rev-parse", "HEAD"))
        self.assertEqual(result.returncode, 0, result.stderr)
        manifest = json.loads((self.client / "CLIENT_MANIFEST.json").read_bytes())
        self.assertEqual(manifest["files"]["repro.py"].get("mode"), "100755")

    def test_sync_updates_shared_file_and_preserves_client_history(self):
        self.initialize_client()
        client_head = self.git(self.client, "rev-parse", "HEAD")
        self.write("repro.py", b"print('updated')\n")
        revision = self.commit(self.source)
        result = self.sync(revision)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.client / "repro.py").read_bytes(), b"print('updated')\n")
        self.assertEqual(self.git(self.client, "rev-parse", "HEAD"), client_head)
        self.assertEqual(json.loads((self.client / "CLIENT_MANIFEST.json").read_bytes())["source_commit"], revision)

    def test_excluded_only_commit_does_not_create_delivery_drift(self):
        self.initialize_client()
        before = (self.client / "CLIENT_MANIFEST.json").read_bytes()
        self.write("private.csv", b"updated excluded data\n")
        result = self.sync(self.commit(self.source))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(json.loads(result.stdout)["changed"])
        self.assertEqual((self.client / "CLIENT_MANIFEST.json").read_bytes(), before)
        self.assertEqual(self.git(self.client, "status", "--porcelain"), "")

    def test_committed_client_drift_is_rejected_even_with_forged_file_hash(self):
        self.initialize_client()
        (self.client / "repro.py").write_bytes(b"client divergence\n")
        path = self.client / "CLIENT_MANIFEST.json"
        manifest = json.loads(path.read_bytes())
        manifest["files"]["repro.py"]["sha256"] = hashlib.sha256(b"client divergence\n").hexdigest()
        manifest["files"]["repro.py"]["bytes"] = len(b"client divergence\n")
        path.write_text(json.dumps(manifest), encoding="utf-8")
        self.commit(self.client)
        self.write("repro.py", b"print('updated')\n")
        result = self.sync(self.commit(self.source))
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.client / "repro.py").read_bytes(), b"client divergence\n")

    def test_untracked_client_file_is_preserved_and_blocks_update(self):
        self.initialize_client()
        (self.client / "notes.txt").write_bytes(b"client note\n")
        result = self.sync(self.first)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.client / "notes.txt").read_bytes(), b"client note\n")

    def test_source_rollback_is_rejected(self):
        self.initialize_client()
        self.write("repro.py", b"print('second')\n")
        self.assertEqual(self.sync(self.commit(self.source)).returncode, 0)
        self.commit(self.client)
        self.assertNotEqual(self.sync(self.first).returncode, 0)

    def test_removal_only_deletes_verified_previously_managed_file(self):
        self.initialize_client()
        self.spec["files"] = []
        self.write_spec()
        result = self.sync(self.commit(self.source))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.client / "repro.py").exists())
        self.assertEqual((self.client / "README.md").read_bytes(), b"Client instructions\n")


if __name__ == "__main__":
    unittest.main()
