"""Acceptance failures for the separately published, evidence-bound course."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build_course
import verify_course
import verify_video_course_v3 as course_history


class CourseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        context = course_history.historical_snapshot(ROOT, version=4)
        cls.root, _ = context.__enter__()
        cls.addClassCleanup(context.__exit__, None, None, None)

    def setUp(self):
        self.source = json.loads((self.root / build_course.SOURCE.relative_to(ROOT)).read_text(encoding="utf-8"))

    def test_historical_fixture_course_and_render_pass(self):
        report = verify_course.verify(self.source, root=self.root)
        self.assertEqual(report["planned_seconds"], 1800)
        self.assertEqual(report["teaching_seconds"], 1050)
        self.assertEqual(report["practice_seconds"], 750)
        self.assertEqual((self.root / build_course.OUTPUT.relative_to(ROOT)).read_bytes(), build_course.render(self.source, root=self.root).encode("utf-8"))

    def test_timing_drift_is_rejected(self):
        self.source["segments"][0]["seconds"] -= 1
        with self.assertRaisesRegex(ValueError, "budget"):
            verify_course.verify(self.source, root=self.root)

    def test_changed_measurement_is_rejected(self):
        self.source["facts"]["mean_accuracy"]["expected"] = 0.975
        with self.assertRaisesRegex(ValueError, "Evidence disagreement"):
            verify_course.verify(self.source, root=self.root)

    def test_missing_required_topic_is_rejected(self):
        for segment in self.source["segments"]:
            segment["topics"] = [x for x in segment["topics"] if x != "hardware"]
        with self.assertRaisesRegex(ValueError, "Required topics"):
            verify_course.verify(self.source, root=self.root)

    def test_broken_repository_reference_is_rejected(self):
        self.source["resources"][0]["path"] = "docs/does-not-exist.md"
        with self.assertRaisesRegex(ValueError, "reference"):
            verify_course.verify(self.source, root=self.root)

    def test_external_resource_cannot_consume_core_time(self):
        self.source["resources"][0]["counted_seconds"] = 60
        with self.assertRaisesRegex(ValueError, "Optional"):
            verify_course.verify(self.source, root=self.root)

    def test_invalid_answer_key_is_rejected(self):
        self.source["segments"][0]["activity"]["questions"][0]["correct"] = 99
        with self.assertRaisesRegex(ValueError, "answer key"):
            verify_course.verify(self.source, root=self.root)

    def test_excessive_reading_load_is_rejected(self):
        self.source["segments"][0]["teaching"].append({"type": "p", "text": "word " * 500})
        with self.assertRaisesRegex(ValueError, "Reading load"):
            verify_course.verify(self.source, root=self.root)

    def test_recorded_demo_is_bound_to_primary_prediction(self):
        self.source["demo"]["expected"]["prediction"] = 0
        with self.assertRaisesRegex(ValueError, "Recorded demo"):
            verify_course.verify(self.source, root=self.root)

    def test_unknown_fact_token_is_rejected(self):
        self.source["segments"][0]["teaching"][0]["text"] += " {{invented_result}}"
        with self.assertRaisesRegex(ValueError, "Unknown fact"):
            verify_course.verify(self.source, root=self.root)

    def test_path_escape_is_rejected(self):
        self.source["resources"][0]["path"] = "../outside.md"
        with self.assertRaisesRegex(ValueError, "reference"):
            verify_course.verify(self.source, root=self.root)

    def test_no_runtime_network_dependency_or_hidden_answers(self):
        html = build_course.render(self.source, root=self.root)
        self.assertNotIn("<iframe", html)
        self.assertNotIn("<script src=", html)
        self.assertNotIn("fetch(", html)
        self.assertIn("<noscript>", html)
        self.assertEqual(html.count('class="answer-key"'), 8)
        self.assertIn("This is self-assessment, not independent certification.", html)

    def test_absent_activity_time_is_rejected(self):
        self.source["segments"][1]["action_seconds"] = 0
        with self.assertRaisesRegex(ValueError, "action time"):
            verify_course.verify(self.source, root=self.root)

    def test_broken_deployed_link_is_rejected(self):
        self.source["resources"][2]["url"] = "../missing-course-target.html"
        with self.assertRaisesRegex(ValueError, "Broken deployed link"):
            verify_course.verify(self.source, root=self.root)

    def test_stale_html_is_rejected_in_isolated_fixture(self):
        paths = {x["path"] for x in self.source["references"].values()}
        paths.update(self.source["protected_artifacts"])
        paths.update(line.split("  ", 1)[1] for line in self.source["protected_checksum_inventory"]["text"].splitlines())
        paths.update(x["path"] for x in self.source["resources"] if x.get("path"))
        paths.add(build_course.SOURCE.relative_to(ROOT).as_posix())
        paths.add("docs/customer/demo/video/index.html")
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary)
            for name in paths:
                target = fixture / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(self.root / name, target)
            output = fixture / build_course.OUTPUT.relative_to(ROOT)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text("Stale HTML", encoding="utf-8", newline="\n")
            with self.assertRaisesRegex(ValueError, "render is stale"):
                verify_course.verify(self.source, root=fixture, check_record=False)

    def pending_record(self):
        return dict(schema_version=1, fully_verified=False,
                    source_sha256=verify_course.digest(self.root / build_course.SOURCE.relative_to(ROOT)),
                    html_sha256=verify_course.digest(self.root / build_course.OUTPUT.relative_to(ROOT)),
                    checks={name: {"status": "pending", "detail": "Not yet performed"}
                            for name in verify_course.RECORD_FIELDS})

    def test_pending_receipts_cannot_be_claimed_as_complete(self):
        record = self.pending_record()
        rendered = build_course.render(self.source, root=self.root)
        self.assertEqual(len(verify_course.verify_record(record, self.source, rendered, root=self.root)), 5)
        record["fully_verified"] = True
        with self.assertRaisesRegex(ValueError, "Pending checks"):
            verify_course.verify_record(record, self.source, rendered, root=self.root)

    def test_automation_cannot_count_as_a_human_rehearsal(self):
        record = self.pending_record()
        record["checks"]["human_rehearsal"] = {
            "status": "passed", "detail": "Automated click-through", "receipt": {"method": "browser"}}
        with self.assertRaisesRegex(ValueError, "Human rehearsal"):
            verify_course.verify_record(record, self.source, build_course.render(self.source, root=self.root), root=self.root)

    def test_default_verification_reports_the_preserved_edition(self):
        result = verify_course.verify()
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["reference_revision"], course_history.V4_REVISION)
        self.assertEqual(result["historical_release_bytes"], "unchanged")
        self.assertEqual(result["current_repository_coverage"], "not checked")

    def test_builder_check_verifies_history_without_rewriting_the_retired_course(self):
        paths = [build_course.SOURCE, build_course.OUTPUT, verify_course.RECORD]
        before = {path: path.read_bytes() for path in paths}
        result = subprocess.run([sys.executable, str(ROOT / "tools/build_course.py"), "--check"],
                                capture_output=True, text=True, encoding="utf-8", check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["reference_revision"], course_history.V4_REVISION)
        self.assertEqual(report["historical_release_bytes"], "unchanged")
        self.assertEqual(report["current_repository_coverage"], "not checked")
        self.assertEqual({path: path.read_bytes() for path in paths}, before)

    def test_explicit_root_reads_its_own_source_without_ignoring_mutation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / build_course.SOURCE.relative_to(ROOT)
            source.parent.mkdir(parents=True)
            source.write_text('{"schema_version": 99}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Unsupported course schema"):
                verify_course.verify(root=root)


class HistoricalCourseProtectionTests(unittest.TestCase):
    def setUp(self):
        import subprocess
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.paths = [build_course.SOURCE.relative_to(ROOT).as_posix(),
                      build_course.OUTPUT.relative_to(ROOT).as_posix(),
                      verify_course.RECORD.relative_to(ROOT).as_posix()]
        for name in self.paths + ["docs/customer/upstream-comparison.md"]:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"Preserved course bytes\n")
        def git(*arguments):
            return subprocess.check_output(["git", "-C", str(self.root), *arguments], stderr=subprocess.PIPE).decode().strip()
        git("init", "-q")
        git("add", ".")
        git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
            "-c", "commit.gpgsign=false", "commit", "-qm", "Historical course fixture")
        self.revision = git("rev-parse", "HEAD")

    def test_historical_course_rejects_changed_source_html_and_receipt(self):
        for name in self.paths:
            path = self.root / name
            path.write_bytes(b"Changed bytes\n")
            with (self.subTest(path=name), patch.object(course_history, "V4_REVISION", self.revision),
                  self.assertRaisesRegex(ValueError, "Historical interactive course byte drift")):
                with verify_course.historical_course_snapshot(self.root):
                    self.fail("Changed course bytes were accepted")
            path.write_bytes(b"Preserved course bytes\n")

    def test_historical_course_rejects_extra_archived_assets(self):
        extra = self.root / "docs/customer/demo/course/new.js"
        extra.write_bytes(b"New archived asset")
        with (patch.object(course_history, "V4_REVISION", self.revision),
              self.assertRaisesRegex(ValueError, "Historical interactive course inventory drift")):
            with verify_course.historical_course_snapshot(self.root):
                self.fail("Added historical course asset was accepted")

    def test_reference_evolution_uses_archived_bytes_and_detects_midcheck_drift(self):
        shared = self.root / "docs/customer/upstream-comparison.md"
        shared.write_bytes(b"Current packet comparison\n")
        with patch.object(course_history, "V4_REVISION", self.revision):
            with verify_course.historical_course_snapshot(self.root) as snapshot:
                self.assertEqual((snapshot / shared.relative_to(self.root)).read_bytes(), b"Preserved course bytes\n")
            with self.assertRaisesRegex(ValueError, "Historical interactive course byte drift"):
                with verify_course.historical_course_snapshot(self.root):
                    (self.root / self.paths[1]).write_bytes(b"Changed during verification\n")


if __name__ == "__main__":
    unittest.main()
