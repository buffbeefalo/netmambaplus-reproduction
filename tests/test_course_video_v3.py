"""Offline acceptance boundaries; fixture media are identities, never decode claims."""

import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


TOOL = Path(__file__).resolve().parents[1] / "tools/verify_video_course_v3.py"
if TOOL.exists():
    SPEC = importlib.util.spec_from_file_location("verify_video_course_v3", TOOL)
    verifier = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(verifier)
else:
    verifier = None


CLUSTERS = ["orientation", "paper", "cic-csv", "unsw-csv", "features", "learning",
            "code", "results", "demo", "setup", "repository", "hardware"]
PAPER_SECTIONS = ["abstract", "I", "II", "III", "IV", "V", "VI", "VII"] + [
    "VIII-" + letter for letter in "ABCDEFGHIJ"] + ["IX"]
SOURCE = "docs/customer/video-course-v3-source.json"
MEDIA = "media/v3/media-manifest.json"
COVERAGE = "docs/customer/video-course-v3-coverage.json"
CSV = "docs/customer/evidence/uploaded-csv-profile.json"
NATIVE = "docs/customer/evidence/native-data-validation.json"
RESULTS = "docs/customer/evidence/results.json"
PORTABILITY = "docs/portability-evidence.json"
PURPOSE = "This chapter explains the purpose of a research training example."
RELATIONSHIP = "It connects input preparation to recorded model evidence and operational limits."
EXAMPLE = "For example, a packet needs a grouping rule before becoming a flow."


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


class CourseFixture:
    def __init__(self, root, chapter_seconds=300, version=3):
        self.root = root
        self.write(CSV, {"files": [
            {"file": "CICIDS2017.csv", "rows": 1410255, "sha256": "a" * 64},
            {"file": "UNSW.csv", "rows": 79881, "sha256": "b" * 64}]})
        self.write(NATIVE, {"splits": {"train": {"rows": 8323},
                                      "valid": {"rows": 1040}, "test": {"rows": 1041}}})
        self.write(RESULTS, {"seeds": [
            {"seed": 0, "metrics": {"accuracy": 0.9125840537944284}},
            {"seed": 1, "metrics": {"accuracy": 0.840537944284342}},
            {"seed": 2, "metrics": {"accuracy": 0.8463016330451489}}],
            "aggregate": {"accuracy": {"mean": 0.8664745437079732,
                                       "sample_standard_deviation": 0.04003586164106568}},
            "paper_ciciot2022_table_iv": {"accuracy": 0.975}})
        self.write(PORTABILITY, {"complete_classifier": {"tokens": 443, "parameter_count": 1870080}})
        claim_specs = [
            ("cic_csv_rows", CSV, "/files/0/rows", "rows", "rows", 0, "1410255", "CICIDS2017", "cic-csv"),
            ("unsw_csv_rows", CSV, "/files/1/rows", "rows", "rows", 0, "79881", "UNSW", "unsw-csv"),
            ("native_train_flows", NATIVE, "/splits/train/rows", "flows", "flows", 0, "8323", "Training", "features"),
            ("native_validation_flows", NATIVE, "/splits/valid/rows", "flows", "flows", 0, "1040", "Validation", "features"),
            ("native_test_flows", NATIVE, "/splits/test/rows", "flows", "flows", 0, "1041", "Test", "features"),
            ("classifier_tokens", PORTABILITY, "/complete_classifier/tokens", "tokens", "tokens", 0, "443", "Classifier", "features"),
            ("classifier_parameters", PORTABILITY, "/complete_classifier/parameter_count", "parameters", "parameters", 0, "1870080", "Classifier", "features"),
            ("seed0_accuracy", RESULTS, "/seeds/0/metrics/accuracy", "ratio", "percent", 2, "91.26", "Seed 0", "results"),
            ("seed1_accuracy", RESULTS, "/seeds/1/metrics/accuracy", "ratio", "percent", 2, "84.05", "Seed 1", "results"),
            ("seed2_accuracy", RESULTS, "/seeds/2/metrics/accuracy", "ratio", "percent", 2, "84.63", "Seed 2", "results"),
            ("mean_accuracy", RESULTS, "/aggregate/accuracy/mean", "ratio", "percent", 2, "86.65", "Mean", "results"),
            ("accuracy_sample_sd", RESULTS, "/aggregate/accuracy/sample_standard_deviation", "ratio", "percentage_points", 2, "4.00", "Sample SD", "results"),
            ("paper_accuracy", RESULTS, "/paper_ciciot2022_table_iv/accuracy", "ratio", "percent", 2, "97.50", "Paper", "paper"),
        ]
        self.source = {"schema_version": 1, "release_tag": f"course-video-v{version}",
                       "target_seconds": 12 * chapter_seconds, "max_practice_seconds": 240,
                       "chapters": [], "claims": []}
        self.claims = []
        for c in CLUSTERS:
            self.source["chapters"].append({"id": c, "seconds": chapter_seconds, "scenes": [
                {"id": c + "-spoken", "kind": "cards", "title": c,
                 "bullets": [], "narration": " ".join([PURPOSE, RELATIONSHIP, EXAMPLE])},
                {"id": c + "-pause", "kind": "pause", "title": "Practice",
                 "bullets": ["Explain the example, then compare it with the worked answer."],
                 "narration": "", "seconds": 20}]})
        for key, file, pointer, source_unit, unit, decimals, expected, subject, chapter in claim_specs:
            display = f"{subject}: {expected} {unit.replace('_', ' ')}"
            spoken = f"{subject} is {expected} {unit.replace('_', ' ')}."
            scene = next(c for c in self.source["chapters"] if c["id"] == chapter)["scenes"][0]
            scene["bullets"].append(display)
            scene["narration"] += " " + spoken
            self.source["claims"].append({"id": key, "scene_id": scene["id"],
                "display_phrase": display, "spoken_phrase": spoken})
            self.claims.append({"id": key, "evidence": self.ref(file), "pointer": pointer,
                "source_unit": source_unit, "unit": unit, "decimals": decimals,
                "expected": expected})
        self.write(SOURCE, self.source)
        self.source_hash = digest(root / SOURCE)
        self.media = {"source_sha256": self.source_hash, "release_tag": f"course-video-v{version}",
                      "scheduled_seconds": 12 * chapter_seconds, "scenes": [], "chapters": [],
                      "artifacts": {}, "caption_cues": []}
        narration_records, frames = [], []
        for i, chapter in enumerate(self.source["chapters"]):
            start = i * chapter_seconds
            self.media["chapters"].append({"id": chapter["id"], "start": start, "end": start + chapter_seconds})
            for j, scene in enumerate(chapter["scenes"]):
                a = start if j == 0 else start + chapter_seconds - 20
                b = start + chapter_seconds - 20 if j == 0 else start + chapter_seconds
                frame = "media/v3/frames/" + scene["id"] + ".png"
                self.write(frame, b"test frame identity: " + scene["id"].encode())
                identity = self.ref(frame)
                frames.append({"scene_id": scene["id"], **identity})
                record = {**copy.deepcopy(scene), "chapter_id": chapter["id"], "start": a, "end": b,
                          "visuals": [identity]}
                if j == 0:
                    raw_hash = hashlib.sha256((scene["id"] + " raw").encode()).hexdigest()
                    final = {"sha256": hashlib.sha256((scene["id"] + " final").encode()).hexdigest(),
                             "samples": (b - a) * 48000, "sample_rate": 48000,
                             "scope": "timed PCM production intermediate; encoded MP4 is public"}
                    record["audio"] = {"wav_sha256": raw_hash, "samples": (b - a) * 48000, "sample_rate": 48000}
                    record["final_audio"] = final
                    narration_records.append({"id": scene["id"], **record["audio"], "final_audio": final})
                    self.media["caption_cues"].append({"start": a, "end": b, "text": scene["narration"]})
                self.media["scenes"].append(record)
        self.write("media/v3/narration-manifest.json", {"source_sha256": self.source_hash, "scenes": narration_records})
        self.write("media/v3/companion-manifest.json", {"source_sha256": self.source_hash, "frames": frames})
        self.write("media/v3/motion-manifest.json", {"source_sha256": self.source_hash, "status": "built"})
        self.write("media/v3/video.mp4", b"test media identity; no actual decoding is performed by this test")
        vtt = ["WEBVTT", ""]
        for cue in self.media["caption_cues"]:
            def stamp(x):
                return f"{int(x)//3600:02}:{int(x)%3600//60:02}:{int(x)%60:02}.000"
            vtt.extend([f"{stamp(cue['start'])} --> {stamp(cue['end'])}", cue["text"], ""])
        self.write("media/v3/captions.vtt", "\n".join(vtt))
        for filename in ["video.mp4", "captions.vtt", "narration-manifest.json", "companion-manifest.json", "motion-manifest.json"]:
            file = root / "media/v3" / filename
            self.media["artifacts"][filename] = {"sha256": digest(file), "bytes": file.stat().st_size}
        self.media["media_name"] = "video.mp4"
        self.write(MEDIA, self.media)
        checks = {}
        for kind in ["decode", "browser", "captions", "claims", "rendered_samples"]:
            path = "checks/" + kind + ".json"
            self.write(path, {"status": "passed", "source_sha256": self.source_hash,
                "manifest_sha256": digest(root / MEDIA),
                "measured_seconds": 12 * chapter_seconds,
                "artifacts": [self.ref("media/v3/video.mp4"), self.ref("media/v3/captions.vtt")],
                "method": "Fixture attestation tests record verification; it does not claim a real video review.",
                "categories": ["technical_terms", "identifiers", "numbers", "chapter_transitions"],
                "known_material_defects": []})
            checks[kind] = self.ref(path)
        paper = "docs/customer/paper-guide.md"
        self.write(paper, "# Paper guide\n\n## All sections\n\n" + EXAMPLE + "\n")
        self.coverage = {"schema_version": version, "source": self.ref(SOURCE),
            "media_manifest": self.ref(MEDIA), "inventory": [], "exclusions": [],
            "clusters": [{"id": c, "scene_ids": [c + "-spoken", c + "-pause"],
                "purpose": PURPOSE, "relationship": RELATIONSHIP, "example": EXAMPLE,
                "review": self.review()} for c in CLUSTERS],
            "paper": {"version": "2601.21792v1", "guide": self.ref(paper), "sections": [
                {"id": p, "scene_ids": ["paper-spoken"], "companion_anchor": "all-sections",
                 "explanation": EXAMPLE, "depth": "companion"} for p in PAPER_SECTIONS]},
            "csv_profiles": [{"file": f, "profile": self.ref(CSV), "source_sha256": raw,
                "scene_ids": [scene + "-spoken"], "explanation": EXAMPLE} for f, raw, scene in [
                    ("CICIDS2017.csv", "a" * 64, "cic-csv"), ("UNSW.csv", "b" * 64, "unsw-csv")]],
            "claims": self.claims,
            "reviews": {"content": {**self.review(), "scene_ids": self.scene_ids(),
                                      "scope": ["script", "worked_answers"]},
                        "visuals": {**self.review(), "manifest_sha256": digest(root / MEDIA),
                                    "items": [{"scene_id": s["id"], "status": "passed", "frames": s["visuals"]}
                                              for s in self.media["scenes"]]},
                        "human_full_watch": {"status": "pending", "reason": "No human full watch was performed."},
                        "all_caption_acceptance": {"status": "pending", "reason": "No complete human caption acceptance was performed."}},
            "checks": checks, "known_material_defects": []}
        self.inventory = sorted([p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()] +
                                [COVERAGE, "docs/repository-walkthrough.md"])
        guide = "# File companion\n\n## Files\n\n" + "\n".join(
            f"- [{p}](../{p}): This file supplies evidence and connects the worked example to its recorded source."
            for p in self.inventory) + "\n"
        self.write("docs/repository-walkthrough.md", guide)
        self.coverage["companion"] = self.ref("docs/repository-walkthrough.md")
        self.coverage["inventory"] = [{"path": p, "scene_id": "repository-spoken", "companion_anchor": "files"}
                                       for p in self.inventory]
        self.coverage["inventory_sha256"] = hashlib.sha256(canonical(self.inventory)).hexdigest()
        self.save()

    def review(self):
        return {"status": "passed", "reviewer": "Codex", "source_sha256": self.source_hash,
                "method": "Reviewed the full source text and worked explanations against the cited evidence."}

    def scene_ids(self):
        return [s["id"] for c in self.source["chapters"] for s in c["scenes"]]

    def write(self, path, value):
        p = self.root / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(value if isinstance(value, bytes) else
                      (value.encode() if isinstance(value, str) else canonical(value)))

    def ref(self, path):
        return {"path": path, "sha256": digest(self.root / path)}

    def save(self):
        self.write(COVERAGE, self.coverage)

    def run(self, content=False):
        self.save()
        return verifier.verify_coverage(self.root, manifest_path=MEDIA, inventory=self.inventory, content_only=content)


class CourseVideoV3Tests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(verifier, "The v3 coverage/readiness verifier has not been implemented")
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.f = CourseFixture(Path(self.tmp.name))

    def reject(self, phrase, content=False):
        with self.assertRaisesRegex(ValueError, phrase):
            self.f.run(content)

    def test_public_readiness_accepts_pending_human_reviews_without_wav_cache(self):
        result = self.f.run()
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["level"], "readiness")
        self.assertEqual(result["human_full_watch"], "pending")

    def test_content_mode_can_report_unbuilt_media_without_readiness(self):
        self.f.coverage["media_manifest"] = None
        result = self.f.run(content=True)
        self.assertEqual(result["level"], "content")
        self.assertFalse(result["media_checked"])
        self.reject("media", content=False)

    def test_content_mode_with_timing_does_not_require_browser_acceptance(self):
        self.f.coverage["checks"].pop("browser")
        self.f.coverage["reviews"].pop("visuals")
        result = self.f.run(content=True)
        self.assertEqual(result["level"], "content")
        self.assertTrue(result["media_checked"])

    def test_missing_or_duplicate_inventory_path_fails(self):
        original = copy.deepcopy(self.f.coverage["inventory"])
        self.f.coverage["inventory"].pop()
        self.reject("inventory")
        self.f.coverage["inventory"] = original + [original[0]]
        self.reject("inventory")

    def test_companion_anchor_must_contain_the_actual_file_link(self):
        self.f.coverage["inventory"][0]["companion_anchor"] = "absent"
        self.reject("anchor")

    def test_explicit_anchor_before_linked_heading_is_a_valid_entry(self):
        p = self.f.coverage["inventory"][0]["path"]
        guide = self.f.root / "docs/repository-walkthrough.md"
        with guide.open("a") as stream:
            stream.write(f'\n<a id="file-explicit"></a>\n\n### [{p}](../{p})\n\n{EXAMPLE}\n')
        self.f.coverage["companion"] = self.f.ref("docs/repository-walkthrough.md")
        self.f.coverage["inventory"][0]["companion_anchor"] = "file-explicit"
        self.assertEqual(self.f.run()["status"], "passed")

    def test_malformed_review_container_is_rejected_cleanly(self):
        self.f.coverage["reviews"] = []
        self.reject("review")

    def test_invented_exclusion_cannot_hide_a_required_file(self):
        self.f.coverage["exclusions"] = [{"path": SOURCE, "kind": "ignored", "reason": EXAMPLE}]
        self.reject("exclusion")

    def test_each_cluster_requires_substantive_source_bound_review(self):
        self.f.coverage["clusters"][0]["example"] = "see link"
        self.reject("example")
        self.f.coverage["clusters"][0]["example"] = EXAMPLE
        self.f.coverage["clusters"][0]["review"]["source_sha256"] = "0" * 64
        self.reject("review")

    def test_missing_major_paper_section_fails(self):
        self.f.coverage["paper"]["sections"].pop()
        self.reject("paper")

    def test_csv_profile_hash_and_raw_input_identity_are_required(self):
        self.f.coverage["csv_profiles"][0]["source_sha256"] = "0" * 64
        self.reject("CSV")

    def test_unit_conversion_and_half_up_rounding_are_explicit(self):
        self.assertEqual(verifier.convert_quantity("0.9125840537944284", "ratio", "percent", 2), "91.26")
        self.assertEqual(verifier.convert_quantity("0.04003586164106568", "ratio", "percentage_points", 2), "4.00")
        self.assertEqual(verifier.convert_quantity("1.005", "percent", "percent", 2), "1.01")
        with self.assertRaises(ValueError):
            verifier.convert_quantity(1410255, "rows", "flows", 0)

    def test_missing_claim_and_wrong_units_fail(self):
        saved = self.f.coverage["claims"].pop()
        self.reject("claim")
        self.f.coverage["claims"].append(saved)
        self.f.coverage["claims"][0]["unit"] = "flows"
        self.reject("unit")

    def test_claim_cannot_be_reattributed_to_another_seed_pointer(self):
        claim = next(x for x in self.f.coverage["claims"] if x["id"] == "seed0_accuracy")
        claim["pointer"] = "/seeds/1/metrics/accuracy"
        self.reject("claim.*evidence|claim.*pointer")

    def test_seed_identity_in_evidence_must_match_the_claim_subject(self):
        evidence = json.loads((self.f.root / RESULTS).read_text())
        evidence["seeds"][0]["seed"] = 1
        self.f.write(RESULTS, evidence)
        for claim in self.f.coverage["claims"]:
            if claim["evidence"]["path"] == RESULTS:
                claim["evidence"] = self.f.ref(RESULTS)
        scenes = {s["id"]: s for c in self.f.source["chapters"] for s in c["scenes"]}
        with self.assertRaisesRegex(ValueError, "subject|seed identity"):
            verifier.check_claims(self.f.root, self.f.coverage, self.f.source, scenes)

    def test_claim_expected_number_must_follow_declared_rounding(self):
        self.f.coverage["claims"][-1]["expected"] = "97.49"
        self.reject("expected")

    def test_source_claim_phrase_must_occur_in_its_designated_scene(self):
        self.f.source["claims"][0]["scene_id"] = "paper-spoken"
        scenes = {s["id"]: s for c in self.f.source["chapters"] for s in c["scenes"]}
        with self.assertRaisesRegex(ValueError, "display_phrase"):
            verifier.check_claims(self.f.root, self.f.coverage, self.f.source, scenes)

    def test_hidden_scene_metadata_cannot_count_as_a_visible_claim(self):
        scenes = {s["id"]: s for c in self.f.source["chapters"] for s in c["scenes"]}
        scene = scenes["cic-csv-spoken"]
        scene["private_audit_note"] = scene["bullets"].pop()
        with self.assertRaisesRegex(ValueError, "display_phrase"):
            verifier.check_claims(self.f.root, self.f.coverage, self.f.source, scenes)

    def test_content_review_must_cover_every_scene(self):
        self.f.coverage["reviews"]["content"]["scene_ids"].pop()
        self.reject("content review")

    def test_manifest_source_hash_and_version_cannot_be_stale(self):
        self.f.media["source_sha256"] = "0" * 64
        self.f.write(MEDIA, self.f.media)
        self.f.coverage["media_manifest"] = self.f.ref(MEDIA)
        self.reject("source")

    def test_legacy_source_cannot_satisfy_v3_coverage(self):
        self.f.source["release_tag"] = "course-video-v2"
        self.f.write(SOURCE, self.f.source)
        self.f.coverage["source"] = self.f.ref(SOURCE)
        self.reject("v3")

    def test_final_audio_metadata_must_match_frozen_public_narration_receipt(self):
        self.f.media["scenes"][0]["final_audio"]["sha256"] = "0" * 64
        self.f.write(MEDIA, self.f.media)
        self.f.coverage["media_manifest"] = self.f.ref(MEDIA)
        self.reject("audio")

    def test_visual_review_must_match_every_final_frame_hash(self):
        self.f.coverage["reviews"]["visuals"]["items"][0]["frames"][0]["sha256"] = "0" * 64
        self.reject("visual")

    def test_missing_required_browser_check_blocks_readiness(self):
        self.f.coverage["checks"].pop("browser")
        self.reject("browser")

    def test_technical_check_must_bind_the_same_encoded_media(self):
        record = self.f.root / "checks/decode.json"
        value = json.loads(record.read_text())
        value["artifacts"][0]["sha256"] = "0" * 64
        self.f.write("checks/decode.json", value)
        self.f.coverage["checks"]["decode"] = self.f.ref("checks/decode.json")
        self.reject("hash|artifact")

    def test_decode_duration_cannot_be_replaced_by_scheduled_duration(self):
        record = json.loads((self.f.root / "checks/decode.json").read_text())
        record["measured_seconds"] = 3590
        self.f.write("checks/decode.json", record)
        self.f.coverage["checks"]["decode"] = self.f.ref("checks/decode.json")
        self.reject("decode.*duration|measured.*duration")

    def test_invalid_caption_timing_is_rejected(self):
        self.f.media["caption_cues"][1]["start"] = 1
        self.f.write(MEDIA, self.f.media)
        self.f.coverage["media_manifest"] = self.f.ref(MEDIA)
        self.reject("caption")

    def test_declared_practice_caption_is_not_mistaken_for_missing_narration(self):
        scene = self.f.media["scenes"][1]
        cue = {"start": scene["start"], "end": scene["end"], "scene": scene["id"],
               "text": "[Practice pause: 20 seconds] " + " ".join(scene["bullets"])}
        self.f.media["caption_cues"].insert(1, cue)
        verifier.check_caption_text(self.f.media["caption_cues"], self.f.media["scenes"],
                                    {s["id"]: s for c in self.f.source["chapters"] for s in c["scenes"]}, {})

    def test_arbitrary_spoken_caption_during_silent_practice_is_rejected(self):
        scene = self.f.media["scenes"][1]
        self.f.media["caption_cues"].insert(1, {"start": scene["start"], "end": scene["end"],
                                                "text": "The model achieved a fictional perfect accuracy."})
        with self.assertRaisesRegex(ValueError, "practice|caption"):
            verifier.check_caption_text(self.f.media["caption_cues"], self.f.media["scenes"],
                                        {s["id"]: s for c in self.f.source["chapters"] for s in c["scenes"]}, {})

    def test_practice_time_cannot_satisfy_spoken_duration_minimum(self):
        self.f.media["scenes"][0]["end"] = 100
        self.f.media["scenes"][1]["start"] = 100
        self.f.media["scenes"][1]["seconds"] = 200
        self.f.write(MEDIA, self.f.media)
        self.f.coverage["media_manifest"] = self.f.ref(MEDIA)
        self.reject("spoken|pause|source|audio")

    def test_source_driven_duration_accepts_3540_seconds(self):
        with tempfile.TemporaryDirectory() as d:
            fixture = CourseFixture(Path(d), chapter_seconds=295)
            result = fixture.run()
            self.assertEqual(result["measured_seconds"], 3540)

    def test_known_material_defect_and_fabricated_human_pass_fail(self):
        self.f.coverage["known_material_defects"] = ["Missing narration at the final transition"]
        self.reject("material")
        self.f.coverage["known_material_defects"] = []
        self.f.coverage["reviews"]["human_full_watch"]["status"] = "passed"
        self.reject("human")


if __name__ == "__main__":
    unittest.main()
