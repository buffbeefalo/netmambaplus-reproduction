"""Exercise the real publisher against a temporary bare remote, without credentials."""

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

TOOL = Path(__file__).resolve().parents[1] / "tools/publish_client.py"


class ClientPublicationTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(TOOL.exists(), "Archive publisher has not been implemented")
        spec = importlib.util.spec_from_file_location("publish_client", TOOL)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.client = self.root / "client"
        self.remote = self.root / "remote.git"
        self.git(self.root, "init", "--bare", "--initial-branch=main", str(self.remote))
        self.git(self.root, "clone", str(self.remote), str(self.client))
        self.write_delivery("a" * 40, b"first\n")
        self.git(self.client, "add", "--all")
        self.git(self.client, "commit", "-m", "Initial delivery")
        self.git(self.client, "push", "origin", "main")
        self.head = self.git(self.client, "rev-parse", "HEAD")
        self.prepared = self.root / "prepared"
        self.git(self.root, "clone", str(self.remote), str(self.prepared))
        self.write_delivery("b" * 40, b"second\n", self.prepared)
        self.archive = self.root / "delivery.tar.gz"
        self.receipt = self.module.pack(self.prepared, self.archive)

    def git(self, root, *args):
        return subprocess.check_output(["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                                        "-c", "core.autocrlf=false", "-C", str(root), *args],
                                       text=True, stderr=subprocess.PIPE).strip()

    def write_delivery(self, revision, raw, root=None):
        root = root or self.client
        (root / "README.md").write_bytes(raw)
        manifest = {"schema": 1, "source_repository": "https://github.com/buffbeefalo/netmambaplus-reproduction",
                    "source_commit": revision, "files": {"README.md": {"sha256": hashlib.sha256(raw).hexdigest(),
                                                                         "bytes": len(raw), "mode": "100644"}}}
        (root / "CLIENT_MANIFEST.json").write_text(json.dumps(manifest), encoding="utf-8")

    def publish(self, **kwargs):
        options = dict(client=self.client, archive=self.archive, archive_sha=self.receipt["archive_sha"],
                       client_head=self.head, source_sha="b" * 40, expected_remote=str(self.remote))
        options.update(kwargs)
        return self.module.publish(**options)

    def test_checked_delivery_pushes_one_fast_forward_commit(self):
        result = self.publish()
        self.assertEqual(self.git(self.remote, "rev-parse", "main"), result["client_commit"])
        self.assertEqual(self.git(self.remote, "rev-parse", "main^"), self.head)
        self.assertEqual(self.git(self.remote, "show", "main:README.md"), "second")

    def test_competing_remote_commit_is_preserved(self):
        other = self.root / "other"
        self.git(self.root, "clone", str(self.remote), str(other))
        (other / "client-note.txt").write_bytes(b"keep this\n")
        self.git(other, "add", "--all")
        self.git(other, "commit", "-m", "Competing delivery")
        self.git(other, "push", "origin", "main")
        tip = self.git(self.remote, "rev-parse", "main")
        with self.assertRaises(ValueError):
            self.publish()
        self.assertEqual(self.git(self.remote, "rev-parse", "main"), tip)
        self.assertEqual((self.client / "README.md").read_bytes(), b"first\n")

    def test_archive_hash_mismatch_does_not_push(self):
        with self.assertRaises(ValueError):
            self.publish(archive_sha="0" * 64)
        self.assertEqual(self.git(self.remote, "rev-parse", "main"), self.head)

    def test_wrong_source_revision_does_not_push(self):
        with self.assertRaises(ValueError):
            self.publish(source_sha="c" * 40)
        self.assertEqual(self.git(self.remote, "rev-parse", "main"), self.head)

    def test_wrong_remote_is_rejected(self):
        with self.assertRaises(ValueError):
            self.publish(expected_remote="git@github.com:someone/other.git")
        self.assertEqual(self.git(self.remote, "rev-parse", "main"), self.head)

    def test_unchanged_client_does_not_emit_an_archive(self):
        destination = self.root / "no-change.tar.gz"
        result = self.module.pack(self.client, destination)
        self.assertFalse(result["changed"])
        self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
