"""Acceptance failures for the separately published, evidence-bound course."""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build_course
import verify_course


class CourseTests(unittest.TestCase):
    def setUp(self):
        self.source = json.loads(build_course.SOURCE.read_text(encoding="utf-8"))

    def test_current_course_and_render_pass(self):
        report = verify_course.verify(self.source)
        self.assertEqual(report["planned_seconds"], 1800)
        self.assertEqual(report["teaching_seconds"], 1050)
        self.assertEqual(report["practice_seconds"], 750)
        self.assertEqual(build_course.OUTPUT.read_bytes(), build_course.render(self.source).encode("utf-8"))

    def test_timing_drift_is_rejected(self):
        self.source["segments"][0]["seconds"] -= 1
        with self.assertRaisesRegex(ValueError, "budget"):
            verify_course.verify(self.source)

    def test_changed_measurement_is_rejected(self):
        self.source["facts"]["mean_accuracy"]["expected"] = 0.975
        with self.assertRaisesRegex(ValueError, "Evidence disagreement"):
            verify_course.verify(self.source)

    def test_missing_required_topic_is_rejected(self):
        for segment in self.source["segments"]:
            segment["topics"] = [x for x in segment["topics"] if x != "hardware"]
        with self.assertRaisesRegex(ValueError, "Required topics"):
            verify_course.verify(self.source)

    def test_broken_repository_reference_is_rejected(self):
        self.source["resources"][0]["path"] = "docs/does-not-exist.md"
        with self.assertRaisesRegex(ValueError, "reference"):
            verify_course.verify(self.source)

    def test_external_resource_cannot_consume_core_time(self):
        self.source["resources"][0]["counted_seconds"] = 60
        with self.assertRaisesRegex(ValueError, "Optional"):
            verify_course.verify(self.source)

    def test_invalid_answer_key_is_rejected(self):
        self.source["segments"][0]["activity"]["questions"][0]["correct"] = 99
        with self.assertRaisesRegex(ValueError, "answer key"):
            verify_course.verify(self.source)

    def test_excessive_reading_load_is_rejected(self):
        self.source["segments"][0]["teaching"].append({"type": "p", "text": "word " * 500})
        with self.assertRaisesRegex(ValueError, "Reading load"):
            verify_course.verify(self.source)

    def test_recorded_demo_is_bound_to_primary_prediction(self):
        self.source["demo"]["expected"]["prediction"] = 0
        with self.assertRaisesRegex(ValueError, "Recorded demo"):
            verify_course.verify(self.source)

    def test_unknown_fact_token_is_rejected(self):
        self.source["segments"][0]["teaching"][0]["text"] += " {{invented_result}}"
        with self.assertRaisesRegex(ValueError, "Unknown fact"):
            verify_course.verify(self.source)

    def test_path_escape_is_rejected(self):
        self.source["resources"][0]["path"] = "../outside.md"
        with self.assertRaisesRegex(ValueError, "reference"):
            verify_course.verify(self.source)

    def test_no_runtime_network_dependency_or_hidden_answers(self):
        html = build_course.render(self.source)
        self.assertNotIn("<iframe", html)
        self.assertNotIn("<script src=", html)
        self.assertNotIn("fetch(", html)
        self.assertIn("<noscript>", html)
        self.assertEqual(html.count('class="answer-key"'), 8)
        self.assertIn("This is self-assessment, not independent certification.", html)

    def test_absent_activity_time_is_rejected(self):
        self.source["segments"][1]["action_seconds"] = 0
        with self.assertRaisesRegex(ValueError, "action time"):
            verify_course.verify(self.source)

    def test_broken_deployed_link_is_rejected(self):
        self.source["resources"][2]["url"] = "../missing-course-target.html"
        with self.assertRaisesRegex(ValueError, "Broken deployed link"):
            verify_course.verify(self.source)

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
                shutil.copyfile(ROOT / name, target)
            output = fixture / build_course.OUTPUT.relative_to(ROOT)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text("Stale HTML", encoding="utf-8", newline="\n")
            with self.assertRaisesRegex(ValueError, "render is stale"):
                verify_course.verify(self.source, root=fixture, check_record=False)

    def pending_record(self):
        return dict(schema_version=1, fully_verified=False,
                    source_sha256=verify_course.digest(build_course.SOURCE),
                    html_sha256=verify_course.digest(build_course.OUTPUT),
                    checks={name: {"status": "pending", "detail": "Not yet performed"}
                            for name in verify_course.RECORD_FIELDS})

    def test_pending_receipts_cannot_be_claimed_as_complete(self):
        record = self.pending_record()
        rendered = build_course.render(self.source)
        self.assertEqual(len(verify_course.verify_record(record, self.source, rendered)), 5)
        record["fully_verified"] = True
        with self.assertRaisesRegex(ValueError, "Pending checks"):
            verify_course.verify_record(record, self.source, rendered)

    def test_automation_cannot_count_as_a_human_rehearsal(self):
        record = self.pending_record()
        record["checks"]["human_rehearsal"] = {
            "status": "passed", "detail": "Automated click-through", "receipt": {"method": "browser"}}
        with self.assertRaisesRegex(ValueError, "Human rehearsal"):
            verify_course.verify_record(record, self.source, build_course.render(self.source))


if __name__ == "__main__":
    unittest.main()
