"""Published v4 evidence stays immutable while current code and references evolve."""

import hashlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from tests.test_video_versions import v4_fixture
from tests.test_course_video_v3 import verifier
import verify_course_video as video


SOURCE = "docs/customer/video-course-v4-source.json"
COVERAGE = "docs/customer/video-course-v4-coverage.json"
MEDIA = "docs/customer/demo/video/v4/media-manifest.json"
GUIDE = "docs/repository-walkthrough.md"


def published_fixture(root):
    """Move the small existing fixture to canonical release paths and rebind it.

    The bytes are test identities, not evidence of a real media decode/review.
    """
    v4_fixture(root)
    replacements = {
        "docs/customer/video-course-v3-": "docs/customer/video-course-v4-",
        "media/v3": "docs/customer/demo/video/v4",
        "checks/": "docs/research/video-v4/",
    }

    def relocate(value):
        for old, new in replacements.items():
            value = value.replace(old, new)
        return value

    for path in [p for p in root.rglob("*") if p.is_file()]:
        data = relocate(path.read_text())
        target = root / relocate(path.relative_to(root).as_posix())
        path.unlink()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(data)

    def digest(path):
        return hashlib.sha256((root / path).read_bytes()).hexdigest()

    media = json.loads((root / MEDIA).read_text())
    for name, record in media["artifacts"].items():
        path = Path(MEDIA).parent / name
        record.update(sha256=digest(path), bytes=(root / path).stat().st_size)
    (root / MEDIA).write_text(json.dumps(media))

    def rebind(value):
        if isinstance(value, list):
            return [rebind(item) for item in value]
        if not isinstance(value, dict):
            return value
        result = {key: rebind(item) for key, item in value.items()}
        if "path" in result and "sha256" in result:
            result["sha256"] = digest(result["path"])
        if "manifest_sha256" in result:
            result["manifest_sha256"] = digest(MEDIA)
        return result

    for path in (root / "docs/research/video-v4").glob("*.json"):
        path.write_text(json.dumps(rebind(json.loads(path.read_text()))))
    coverage = rebind(json.loads((root / COVERAGE).read_text()))
    inventory = sorted(entry["path"] for entry in coverage["inventory"])
    coverage["inventory_sha256"] = hashlib.sha256(
        json.dumps(inventory, separators=(",", ":")).encode()).hexdigest()
    (root / COVERAGE).write_text(json.dumps(coverage))
    return inventory


class HistoricalV4Tests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def git(self, *args):
        return subprocess.check_output(
            ["git", "-C", str(self.root), *args], stderr=subprocess.PIPE).decode().strip()

    def commit(self):
        self.git("init", "-q")
        self.git("add", ".")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                 "-c", "commit.gpgsign=false", "commit", "-qm", "Immutable fixture")
        return self.git("rev-parse", "HEAD")

    def run_cli(self, revision, *arguments, version=4):
        output = io.StringIO()
        with patch.object(sys, "argv", ["verify_video_course.py", "--root", str(self.root), *arguments]), \
                patch.object(verifier, f"V{version}_REVISION", revision, create=True), redirect_stdout(output):
            code = verifier.main(version=version)
        return code, json.loads(output.getvalue())

    def test_default_v4_cli_checks_published_tree_and_frozen_references(self):
        inventory = published_fixture(self.root)
        revision = self.commit()
        (self.root / GUIDE).write_text("The current guide has changed.\n")
        (self.root / "new-packet-model.py").write_text("# A separate current implementation\n")
        code, result = self.run_cli(revision)
        self.assertEqual(code, 0, result)
        self.assertEqual(result["reference_revision"], revision)
        self.assertEqual(result["inventory_files"], len(inventory))
        self.assertEqual(result["historical_release_bytes"], "unchanged")
        self.assertIn("historical", result["inventory_scope"].lower())
        self.assertEqual(result["current_repository_coverage"], "not checked")

    def test_v4_byte_drift_is_rejected_in_every_protected_artifact_family(self):
        paths = [SOURCE, COVERAGE, "docs/customer/video-verification-v4.md",
                 "docs/customer/demo/video/v4/course.mp4", "docs/customer/demo/video/v4/slides.pdf",
                 "docs/research/video-v4/decode.json", "docs/research/video-audit-v4.json"]
        for name in paths:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"Archived bytes\n")
        revision = self.commit()
        for name in paths:
            path = self.root / name
            path.write_bytes(b"Modified bytes\n")
            with self.subTest(path=name), self.assertRaisesRegex(ValueError, "Historical v4 byte drift"):
                with verifier.historical_snapshot(self.root, revision=revision, version=4):
                    self.fail("Modified published bytes were accepted")
            path.write_bytes(b"Archived bytes\n")

    def test_v4_inventory_addition_and_removal_are_rejected(self):
        path = self.root / SOURCE
        path.parent.mkdir(parents=True)
        path.write_text("Archived source\n")
        revision = self.commit()
        added = self.root / "docs/research/video-v4/new-review.json"
        added.parent.mkdir(parents=True)
        added.write_text("New untracked review\n")
        with self.assertRaisesRegex(ValueError, "Historical v4 inventory drift"):
            with verifier.historical_snapshot(self.root, revision=revision, version=4):
                self.fail("Untracked release addition was accepted")
        added.unlink()
        self.git("rm", "--", SOURCE)
        with self.assertRaisesRegex(ValueError, "Historical v4 inventory drift"):
            with verifier.historical_snapshot(self.root, revision=revision, version=4):
                self.fail("Removed release source was accepted")

    def test_v4_drift_during_verification_is_rejected(self):
        path = self.root / SOURCE
        path.parent.mkdir(parents=True)
        path.write_text("Archived source\n")
        revision = self.commit()
        with self.assertRaisesRegex(ValueError, "Historical v4 byte drift"):
            with verifier.historical_snapshot(self.root, revision=revision, version=4):
                path.write_text("Changed while the snapshot was open\n")

    def test_matching_symlink_targets_cannot_replace_v3_or_v4_release_files(self):
        source_paths = ["docs/customer/video-course-v3-source.json", SOURCE]
        for name in source_paths:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("Archived source\n")
        target = self.root / "other-source.json"
        target.write_text("Archived source\n")
        revision = self.commit()
        for version, name in zip((3, 4), source_paths):
            path = self.root / name
            path.unlink()
            try:
                path.symlink_to(target)
            except OSError:
                self.skipTest("The test account cannot create symbolic links")
            with self.subTest(version=version), self.assertRaisesRegex(ValueError, "byte drift"):
                with verifier.historical_snapshot(self.root, revision=revision, version=version):
                    self.fail("A symlink replaced an immutable release file")
            path.unlink()
            path.write_text("Archived source\n")

    def test_v4_snapshot_never_executes_old_code_or_uses_replacement_commits(self):
        sentinel = self.root / "executed.txt"
        (self.root / "dangerous.py").write_text(
            f"from pathlib import Path\nPath({str(sentinel)!r}).write_text('executed')\n")
        (self.root / "README.md").write_text("Original reference\n")
        revision = self.commit()
        (self.root / "README.md").write_text("Replacement reference\n")
        replacement = self.commit()
        self.git("replace", revision, replacement)
        with verifier.historical_snapshot(self.root, revision=revision, version=4) as (snapshot, inventory):
            self.assertEqual((snapshot / "README.md").read_text(), "Original reference\n")
            self.assertEqual(inventory, ["README.md", "dangerous.py"])
        self.assertFalse(sentinel.exists())

    def test_v4_rejects_mutable_or_missing_commits(self):
        (self.root / "README.md").write_text("Fixture\n")
        self.commit()
        for revision in ["HEAD", "0" * 40]:
            with self.subTest(revision=revision), self.assertRaises((ValueError, subprocess.SubprocessError)):
                with verifier.historical_snapshot(self.root, revision=revision, version=4):
                    self.fail("An unpinned or missing commit was accepted")

    def test_v3_schema_cannot_pass_v4_historical_verification(self):
        published_fixture(self.root)
        coverage = self.root / COVERAGE
        value = json.loads(coverage.read_text())
        value["schema_version"] = 3
        coverage.write_text(json.dumps(value))
        revision = self.commit()
        code, result = self.run_cli(revision)
        self.assertEqual(code, 1)
        self.assertIn("version must be 4", result["error"])

    def test_historical_cli_rejects_cross_version_path_overrides(self):
        published_fixture(self.root)
        revision = self.commit()
        for option, other in [("--source", "docs/customer/video-course-v3-source.json"),
                              ("--coverage", "docs/customer/video-course-v3-coverage.json"),
                              ("--manifest", "docs/customer/demo/video/v3/media-manifest.json")]:
            with self.subTest(option=option):
                code, result = self.run_cli(revision, option, other)
                self.assertEqual(code, 1)
                self.assertIn("canonical v4 paths", result["error"])

    def test_current_mode_still_rejects_new_files_missing_from_video_inventory(self):
        published_fixture(self.root)
        revision = self.commit()
        (self.root / "new-packet-model.py").write_text("# Requires its own current guide entry\n")
        code, result = self.run_cli(revision, "--current")
        self.assertEqual(code, 1)
        self.assertIn("inventory", result["error"])


    def test_video_file_verifier_supplies_archived_source_and_reference_roots(self):
        published_fixture(self.root)
        original = (self.root / GUIDE).read_bytes()
        revision = self.commit()
        (self.root / GUIDE).write_text("Current packet guide", encoding="utf-8")

        def observe(directory, source_path, *, reference_root, repository_root):
            self.assertEqual(reference_root, repository_root)
            self.assertEqual(source_path, reference_root / SOURCE)
            self.assertEqual(directory, reference_root / Path(MEDIA).parent)
            self.assertEqual((reference_root / GUIDE).read_bytes(), original)
            return {}, {"status": "passed"}

        with (patch("verify_video_course_v3.V4_REVISION", revision),
              patch.object(video, "verify_files", side_effect=observe) as checker):
            _, result = video.verify_historical_files(self.root, version=4)
        checker.assert_called_once()
        self.assertEqual(result["reference_revision"], revision)
        self.assertEqual(result["historical_release_bytes"], "unchanged")
        self.assertEqual(result["current_repository_coverage"], "not checked")


class VideoCliHistoryTests(unittest.TestCase):
    def test_video_default_is_historical_v4_and_current_mode_keeps_strict_binding(self):
        with (patch.object(sys, "argv", ["verify_course_video.py"]),
              patch.object(video, "verify_historical_files", return_value=({}, {"status": "passed"})) as historical,
              patch.object(video, "verify_files") as current, redirect_stdout(io.StringIO())):
            video.main()
        historical.assert_called_once_with(version=4)
        current.assert_not_called()
        with (patch.object(sys, "argv", ["verify_course_video.py", "--current"]),
              patch.object(video, "verify_historical_files") as historical,
              patch.object(video, "verify_files", return_value=({}, {"status": "passed"})) as current,
              redirect_stdout(io.StringIO())):
            video.main()
        historical.assert_not_called()
        current.assert_called_once_with(video.DESTINATION, video.SOURCE,
                                        reference_revision=None, reference_root=None)

    def test_historical_video_cli_cannot_substitute_another_source_or_media_path(self):
        for arguments in [["--source", "docs/customer/video-course-v3-source.json"],
                          ["--media-dir", "docs/customer/demo/video/v3"],
                          ["--historical-v3", "--current"]]:
            with (self.subTest(arguments=arguments),
                  patch.object(sys, "argv", ["verify_course_video.py", *arguments]),
                  patch.object(video, "verify_files") as current,
                  patch.object(video, "verify_historical_files") as historical,
                  redirect_stdout(io.StringIO()), patch.object(sys, "stderr", io.StringIO()),
                  self.assertRaises(SystemExit) as failure):
                video.main()
            self.assertEqual(failure.exception.code, 2)
            current.assert_not_called()
            historical.assert_not_called()

    def test_historical_video_rechecks_protected_bytes_after_external_measurement(self):
        manifest = {"release_tag": "course-video-v4", "media_name": "course.mp4"}
        with (patch.object(sys, "argv", ["verify_course_video.py", "--decode-output", "unused-fixture-output"]),
              patch.object(video, "verify_historical_files", side_effect=[
                  (manifest, {"status": "passed"}), ValueError("Historical v4 byte drift")]) as historical,
              patch.object(video, "measure_media", return_value={}), redirect_stdout(io.StringIO()),
              self.assertRaisesRegex(ValueError, "Historical v4 byte drift")):
            video.main()
        self.assertEqual(historical.call_count, 2)
        self.assertTrue(all(call.kwargs == {"version": 4} for call in historical.call_args_list))


if __name__ == "__main__":
    unittest.main()
