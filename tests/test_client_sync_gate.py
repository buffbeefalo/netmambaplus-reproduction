"""Test eligibility against concrete workflow event and REST response fixtures."""

import copy
import importlib.util
from pathlib import Path
import unittest

PATH = Path(__file__).resolve().parents[1] / "tools/client_sync_gate.py"


class ClientSyncGateTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(PATH.exists(), "Publication eligibility gate has not been implemented")
        spec = importlib.util.spec_from_file_location("client_sync_gate", PATH)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.sha = "a" * 40
        self.run = {"id": 123, "path": ".github/workflows/ci.yml", "name": "CPU verification",
                    "event": "push", "status": "completed", "conclusion": "success",
                    "head_branch": "main", "head_sha": self.sha,
                    "head_repository": {"full_name": "buffbeefalo/netmambaplus-reproduction"}}
        self.event = {"workflow_run": copy.deepcopy(self.run)}

    def eligible(self, **options):
        args = {"event_name": "workflow_run", "event": self.event,
                "repository": "buffbeefalo/netmambaplus-reproduction", "ref": "refs/heads/main",
                "remote_sha": self.sha, "run": self.run}
        args.update(options)
        return self.module.eligible(**args)

    def test_verified_current_main_push_is_eligible(self):
        self.assertTrue(self.eligible())

    def test_pull_request_source_is_rejected(self):
        self.run["event"] = "pull_request"
        self.assertFalse(self.eligible())

    def test_failed_or_unfinished_verification_is_rejected(self):
        for key, value in (("conclusion", "failure"), ("conclusion", "cancelled"), ("status", "in_progress")):
            with self.subTest(value=value):
                run = {**self.run, key: value}
                self.assertFalse(self.eligible(run=run))

    def test_stale_source_is_rejected(self):
        self.assertFalse(self.eligible(remote_sha="b" * 40))

    def test_wrong_repository_branch_workflow_and_run_are_rejected(self):
        for key, value in (("head_branch", "feature"), ("path", ".github/workflows/other.yml"),
                           ("id", 999), ("head_repository", {"full_name": "someone/fork"})):
            with self.subTest(key=key):
                self.assertFalse(self.eligible(run={**self.run, key: value}))
        self.assertFalse(self.eligible(repository="someone/fork"))

    def test_manual_recovery_requires_current_verified_main(self):
        self.assertTrue(self.eligible(event_name="workflow_dispatch", event={}))
        self.assertFalse(self.eligible(event_name="workflow_dispatch", event={}, ref="refs/heads/feature"))
        self.assertFalse(self.eligible(event_name="workflow_dispatch", event={}, run={**self.run, "conclusion": "failure"}))


if __name__ == "__main__":
    unittest.main()
