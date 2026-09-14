"""Current inventories and immutable historical releases remain separate gates."""

import copy
import hashlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from contextlib import redirect_stdout
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import build_course_video as build
import build_video_documents as documents
import build_video_page as page
import narrate_course_video as narration
from tests.test_course_video_v3 import CourseFixture, COVERAGE, MEDIA, SOURCE, verifier


CALIBRATION = "docs/customer/evidence/calibration/results.json"
CALIBRATION_SPECS = [
    ("calibration_raw_nll", "/aggregate/raw/nll/mean", "nll", "nll", 4, "0.4416"),
    ("calibration_scaled_nll", "/aggregate/calibrated/nll/mean", "nll", "nll", 4, "0.4172"),
    ("calibration_raw_brier", "/aggregate/raw/brier/mean", "brier", "brier", 4, "0.2035"),
    ("calibration_scaled_brier", "/aggregate/calibrated/brier/mean", "brier", "brier", 4, "0.2012"),
    ("calibration_raw_ece", "/aggregate/raw/ece/mean", "ratio", "percent", 2, "7.03"),
    ("calibration_scaled_ece", "/aggregate/calibrated/ece/mean", "ratio", "percent", 2, "3.82"),
    ("calibration_seed0_raw_accepted", "/seeds/0/raw/accepted", "flows", "flows", 0, "620"),
    ("calibration_seed0_scaled_accepted", "/seeds/0/calibrated/accepted", "flows", "flows", 0, "893"),
    ("calibration_seed0_raw_errors", "/seeds/0/raw/accepted_errors", "flows", "flows", 0, "9"),
    ("calibration_seed0_scaled_errors", "/seeds/0/calibrated/accepted_errors", "flows", "flows", 0, "37"),
]


def v4_fixture(root):
    """Extend only the temporary v4 fixture; these are not production audit receipts."""
    path = root / CALIBRATION
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "aggregate": {"raw": {"nll": {"mean": 0.441571}, "brier": {"mean": 0.203498}, "ece": {"mean": 0.070281}},
                      "calibrated": {"nll": {"mean": 0.417214}, "brier": {"mean": 0.201235}, "ece": {"mean": 0.038232}}},
        "seeds": [{"seed": 0, "raw": {"accepted": 620, "accepted_errors": 9},
                   "calibrated": {"accepted": 893, "accepted_errors": 37}}]}))
    fixture = CourseFixture(root, version=4)
    original_source_hash = fixture.source_hash
    scenes = {s["id"]: s for c in fixture.source["chapters"] for s in c["scenes"]}
    for name, pointer, source_unit, unit, decimals, expected in CALIBRATION_SPECS:
        scene = scenes["demo-spoken" if "seed0" in name else "results-spoken"]
        phrase = f"{name.replace('_', ' ')}: {expected} {unit.upper() if unit == 'nll' else unit.title()}."
        scene["bullets"].append(phrase)
        scene["narration"] += " " + phrase
        fixture.source["claims"].append({"id": name, "scene_id": scene["id"],
                                        "display_phrase": phrase, "spoken_phrase": phrase})
        fixture.coverage["claims"].append({"id": name, "evidence": fixture.ref(CALIBRATION),
            "pointer": pointer, "source_unit": source_unit, "unit": unit, "decimals": decimals, "expected": expected})
    fixture.write(SOURCE, fixture.source)
    fixture.source_hash = build.digest(root / SOURCE)
    fixture.media["source_sha256"] = fixture.source_hash
    for scene in fixture.media["scenes"]:
        scene.update(copy.deepcopy(scenes[scene["id"]]))
    for cue, scene in zip(fixture.media["caption_cues"], [s for s in scenes.values() if s["narration"]]):
        cue["text"] = scene["narration"]
    vtt = ["WEBVTT", ""]
    for cue in fixture.media["caption_cues"]:
        def stamp(seconds):
            return f"{int(seconds)//3600:02}:{int(seconds)%3600//60:02}:{int(seconds)%60:02}.000"
        vtt.extend([f"{stamp(cue['start'])} --> {stamp(cue['end'])}", cue["text"], ""])
    fixture.write("media/v3/captions.vtt", "\n".join(vtt))
    for name in ("narration-manifest.json", "companion-manifest.json", "motion-manifest.json"):
        value = json.loads((root / "media/v3" / name).read_text())
        value["source_sha256"] = fixture.source_hash
        fixture.write("media/v3/" + name, value)
    for name in fixture.media["artifacts"]:
        path = root / "media/v3" / name
        fixture.media["artifacts"][name] = {"sha256": build.digest(path), "bytes": path.stat().st_size}
    fixture.write(MEDIA, fixture.media)

    def rebind(value):
        if isinstance(value, list):
            return [rebind(item) for item in value]
        if not isinstance(value, dict):
            return value
        value = {key: rebind(item) for key, item in value.items()}
        if value.get("source_sha256") == original_source_hash:
            value["source_sha256"] = fixture.source_hash
        if "manifest_sha256" in value:
            value["manifest_sha256"] = build.digest(root / MEDIA)
        if "path" in value and "sha256" in value:
            value["sha256"] = build.digest(root / value["path"])
        return value
    for record in fixture.coverage["checks"].values():
        fixture.write(record["path"], rebind(json.loads((root / record["path"]).read_text())))
    fixture.coverage = rebind(fixture.coverage)
    fixture.save()
    return fixture


class VersionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.root), *args], stderr=subprocess.PIPE).decode().strip()

    def commit(self):
        self.git("init", "-q")
        self.git("add", ".")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                 "-c", "commit.gpgsign=false", "commit", "-qm", "Immutable fixture")
        return self.git("rev-parse", "HEAD")

    def test_current_defaults_and_schema_select_v4(self):
        self.assertEqual(narration.SOURCE.name, "video-course-v4-source.json")
        self.assertEqual(build.DESTINATION.name, "v4")
        self.assertEqual(build.DEFAULT_WORK.name, "v4-neural")
        schema = verifier.schema_requirements(version=4)
        self.assertEqual(schema["schema_version"], 4)
        self.assertTrue(schema["source"].endswith("video-course-v4-source.json"))
        self.assertTrue(schema["coverage"].endswith("video-course-v4-coverage.json"))
        self.assertEqual(schema["human_review_status"], "pending")

    def test_v4_uses_all_existing_strict_checks_and_rejects_v3(self):
        fixture = v4_fixture(self.root)
        def run():
            fixture.save()
            return verifier.verify_coverage(self.root, source_path=SOURCE, coverage_path=COVERAGE,
                manifest_path=MEDIA, inventory=fixture.inventory, version=4)
        self.assertEqual(run()["status"], "passed")
        fixture.coverage["checks"].pop("browser")
        with self.assertRaisesRegex(ValueError, "browser"):
            run()
        fixture.coverage["schema_version"] = 3
        with self.assertRaisesRegex(ValueError, "version.*4"):
            run()

    def test_current_inventory_includes_new_nonignored_files(self):
        fixture = v4_fixture(self.root)
        self.commit()
        (self.root / "new-untracked-tool.py").write_text("# Must be explained\n")
        with self.assertRaisesRegex(ValueError, "inventory"):
            verifier.verify_coverage(self.root, source_path=SOURCE, coverage_path=COVERAGE,
                                     manifest_path=MEDIA, version=4)

    def test_missing_current_media_never_grants_readiness(self):
        fixture = v4_fixture(self.root)
        fixture.coverage["media_manifest"] = None
        fixture.save()
        options = dict(source_path=SOURCE, coverage_path=COVERAGE, manifest_path=MEDIA,
                       inventory=fixture.inventory, version=4)
        self.assertFalse(verifier.verify_coverage(self.root, content_only=True, **options)["media_checked"])
        with self.assertRaisesRegex(ValueError, "readiness"):
            verifier.verify_coverage(self.root, **options)

    def test_historical_guide_uses_pinned_bytes_and_never_executes_snapshot_code(self):
        sentinel = self.root / "executed.txt"
        (self.root / "dangerous.py").write_text("raise RuntimeError('Never execute snapshot code')\n")
        fixture = CourseFixture(self.root)
        revision = self.commit()
        (self.root / "docs/repository-walkthrough.md").write_text("New current guide\n")
        with verifier.historical_snapshot(self.root, revision=revision) as (snapshot, inventory):
            self.assertEqual(inventory, fixture.inventory)
            result = verifier.verify_coverage(snapshot, source_path=SOURCE, coverage_path=COVERAGE,
                manifest_path=MEDIA, inventory=inventory, ignored_paths=set())
            self.assertEqual(result["status"], "passed")
        self.assertFalse(sentinel.exists())
        with self.assertRaisesRegex(ValueError, "companion hash"):
            fixture.run()

    def test_historical_source_coverage_and_assets_cannot_be_rebound(self):
        asset = self.root / "docs/customer/demo/video/v3/video.mp4"
        asset.parent.mkdir(parents=True)
        asset.write_bytes(b"Original release")
        CourseFixture(self.root)
        revision = self.commit()
        for path in [self.root / SOURCE, self.root / COVERAGE, asset]:
            original = path.read_bytes()
            path.write_bytes(original + b" ")
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, "Historical v3.*drift"):
                with verifier.historical_snapshot(self.root, revision=revision):
                    self.fail("Drift was not rejected before verification")
            path.write_bytes(original)

    def test_historical_drift_during_verification_is_rejected(self):
        CourseFixture(self.root)
        revision = self.commit()
        with self.assertRaisesRegex(ValueError, "Historical v3.*drift"):
            with verifier.historical_snapshot(self.root, revision=revision):
                path = self.root / SOURCE
                path.write_bytes(path.read_bytes() + b" ")

    def test_missing_or_mutable_historical_revision_is_rejected(self):
        (self.root / "README.md").write_text("Fixture\n")
        self.commit()
        for revision in ["HEAD", "0" * 40]:
            with self.subTest(revision=revision), self.assertRaises((ValueError, subprocess.SubprocessError)):
                with verifier.historical_snapshot(self.root, revision=revision):
                    self.fail("No immutable snapshot exists")

    def test_explicit_source_and_its_reference_root_are_used(self):
        course = self.root / "docs/customer/course-source.json"
        course.parent.mkdir(parents=True)
        course.write_text(json.dumps({"facts": {}, "references": {}}))
        selected = self.root / "selected.json"
        selected.write_text(json.dumps({"fact_bindings_sha256": hashlib.sha256(b"{}").hexdigest(),
                                        "title": "The explicitly selected lesson"}))
        self.assertEqual(narration.load_source(selected, root=self.root)["title"],
                         "The explicitly selected lesson")

    def test_selected_source_and_current_reference_hashes_are_mandatory(self):
        course = self.root / "docs/customer/course-source.json"
        course.parent.mkdir(parents=True)
        course.write_text(json.dumps({"facts": {}, "references": {}}))
        reference = self.root / "README.md"
        reference.write_text("Current reference\n")
        selected = self.root / "selected.json"
        selected.write_text(json.dumps({"fact_bindings_sha256": hashlib.sha256(b"{}").hexdigest(),
            "release_tag": "course-video-v4", "extra_references": {"notes": "README.md"},
            "chapters": [{"scenes": [{"references": ["notes"]}]}]}))
        manifest = {"source_path": "selected.json", "source_sha256": build.digest(selected),
            "release_tag": "course-video-v4", "references": {
                "notes": {"path": "README.md", "sha256": build.digest(reference)}}}
        build.check_source_binding(manifest, selected, root=self.root)
        original = selected.read_bytes()
        selected.write_bytes(original + b" ")
        with self.assertRaisesRegex(ValueError, "source"):
            build.check_source_binding(manifest, selected, root=self.root)
        selected.write_bytes(original)
        reference.write_text("Reference changed after rendering\n")
        with self.assertRaisesRegex(ValueError, "reference"):
            build.check_source_binding(manifest, selected, root=self.root)

    def test_page_uses_selected_version_for_media_and_verification_links(self):
        from tests.test_course_video import VideoTests
        manifest = VideoTests().hour_manifest()
        manifest["release_tag"] = "course-video-v4"
        rendered = page.render(manifest)
        self.assertIn('src="v4/measured-course.mp4"', rendered)
        self.assertIn("video-verification-v4.md", rendered)
        manifest["release_tag"] = "course-video-v3"
        self.assertIn('src="v3/measured-course.mp4"', page.render(manifest))

    def test_documents_cli_forwards_explicit_source_and_output_paths(self):
        selected = self.root / "selected.json"
        output, work = self.root / "media", self.root / "work"
        arguments = ["build_video_documents.py", "--source", str(selected),
                     "--work-dir", str(work), "--output", str(output)]
        with patch.object(sys, "argv", arguments), patch.object(documents, "build") as builder:
            documents.main()
        builder.assert_called_once_with(work.resolve(), output.resolve(), selected.resolve())

    def test_documents_and_page_reject_stale_selected_source_before_writing(self):
        selected = self.root / "selected.json"
        selected.write_text('{}')
        media = self.root / "media"
        media.mkdir()
        manifest = {"release_tag": "course-video-v4", "source_path": "selected.json",
                    "source_sha256": "0" * 64}
        (media / "media-manifest.json").write_text(json.dumps(manifest))
        with patch.object(documents, "ROOT", self.root), patch.dict(sys.modules, {"pptx": None}):
            with self.assertRaisesRegex(ValueError, "source"):
                documents.build(self.root / "work", media, selected)
        output = self.root / "page.html"
        arguments = ["build_video_page.py", "--source", str(selected),
                     "--media-dir", str(media), "--output", str(output)]
        with patch.object(sys, "argv", arguments), patch.object(page, "ROOT", self.root):
            with self.assertRaisesRegex(ValueError, "source"), redirect_stdout(io.StringIO()):
                page.main()
        self.assertFalse(output.exists())
        self.assertEqual([p.name for p in media.iterdir()], ["media-manifest.json"])


class CalibrationClaimTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.fixture = v4_fixture(self.root)

    def check(self):
        scenes = {s["id"]: s for c in self.fixture.source["chapters"] for s in c["scenes"]}
        return verifier.check_claims(self.root, self.fixture.coverage, self.fixture.source, scenes, version=4)

    def claim(self, name):
        return next(c for c in self.fixture.coverage["claims"] if c["id"] == name)

    def test_v4_schema_adds_exact_calibration_pointers_without_changing_v3(self):
        old = verifier.schema_requirements(version=3)["claims"]
        current = verifier.schema_requirements(version=4)["claims"]
        self.assertEqual(len(old), 13)
        self.assertEqual(len(current), 23)
        self.assertEqual({key: current[key] for key in old}, old)
        for name, pointer, source_unit, unit, _, _ in CALIBRATION_SPECS:
            self.assertNotIn(name, old)
            self.assertEqual(current[name], {"file": CALIBRATION, "pointer": pointer,
                                             "source_unit": source_unit, "unit": unit})
        self.assertEqual(len(self.check()), 23)

    def test_old_v3_claims_do_not_satisfy_current_v4(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = CourseFixture(Path(temporary))
            scenes = {s["id"]: s for c in fixture.source["chapters"] for s in c["scenes"]}
            self.assertEqual(len(verifier.check_claims(fixture.root, fixture.coverage, fixture.source, scenes)), 13)
            with self.assertRaisesRegex(ValueError, "required claim"):
                verifier.check_claims(fixture.root, fixture.coverage, fixture.source, scenes, version=4)

    def test_removing_a_calibration_claim_from_both_documents_is_rejected(self):
        for document in (self.fixture.source, self.fixture.coverage):
            document["claims"] = [c for c in document["claims"] if c["id"] != "calibration_seed0_scaled_errors"]
        with self.assertRaisesRegex(ValueError, "required claim"):
            self.check()

    def test_metric_units_are_exact_and_cannot_be_scaled_like_ratios(self):
        self.assertEqual(verifier.convert_quantity(0.441571, "nll", "nll", 4), "0.4416")
        self.assertEqual(verifier.convert_quantity(0.203498, "brier", "brier", 4), "0.2035")
        for source_unit, unit in (("nll", "percent"), ("nll", "brier"), ("brier", "nll")):
            with self.subTest(source_unit=source_unit, unit=unit), self.assertRaisesRegex(ValueError, "units"):
                verifier.convert_quantity(0.2, source_unit, unit, 4)
        self.claim("calibration_raw_nll")["unit"] = "ratio"
        with self.assertRaisesRegex(ValueError, "units"):
            self.check()

    def test_alternate_metric_pointer_and_copied_evidence_file_are_rejected(self):
        claim = self.claim("calibration_raw_nll")
        original = claim["pointer"]
        claim["pointer"] = "/aggregate/calibrated/nll/mean"
        with self.assertRaisesRegex(ValueError, "pointer.*misattributed"):
            self.check()
        claim["pointer"] = original
        self.fixture.write("copied-results.json", (self.root / CALIBRATION).read_bytes())
        claim["evidence"] = self.fixture.ref("copied-results.json")
        with self.assertRaisesRegex(ValueError, "pointer.*misattributed"):
            self.check()

    def test_seed_zero_counts_reject_relabelled_seed_identity(self):
        for identity in (1, False):
            evidence = json.loads((self.root / CALIBRATION).read_text())
            evidence["seeds"][0]["seed"] = identity
            self.fixture.write(CALIBRATION, evidence)
            for name, *_ in CALIBRATION_SPECS:
                self.claim(name)["evidence"] = self.fixture.ref(CALIBRATION)
            with self.subTest(identity=identity), self.assertRaisesRegex(ValueError, "seed identity"):
                self.check()

    def test_reported_rounding_and_visible_value_remain_bound_to_evidence(self):
        claim = self.claim("calibration_raw_nll")
        claim["expected"] = "0.9999"
        with self.assertRaisesRegex(ValueError, "rounded claim"):
            self.check()
        claim["expected"] = "0.4416"
        binding = next(c for c in self.fixture.source["claims"] if c["id"] == claim["id"])
        scene = next(s for c in self.fixture.source["chapters"] for s in c["scenes"] if s["id"] == binding["scene_id"])
        original = binding["display_phrase"]
        changed = original.replace("0.4416", "0.9999")
        binding["display_phrase"] = changed
        scene["bullets"] = [changed if text == original else text for text in scene["bullets"]]
        with self.assertRaisesRegex(ValueError, "Displayed claim number differs"):
            self.check()


if __name__ == "__main__":
    unittest.main()
