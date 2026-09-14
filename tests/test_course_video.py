"""Video acceptance gates reject media and caption failures on a CPU."""

import copy
import hashlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from contextlib import redirect_stderr, redirect_stdout

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from build_course_video import allocate_frames, caption_cues
import build_course_video as build
import build_video_page as page
import verify_course_video as verifier
from verify_course_video import check_probe, check_silences, check_vtt, verify_files

V2_OFFSETS = [0, 120, 360, 600, 780, 1020, 1260, 1500, 1620]
V2_SCHEDULE = {"scheduled_seconds": 1800, "chapters": [
    {"start": start, "end": end} for start, end in zip(V2_OFFSETS, V2_OFFSETS[1:] + [1800])]}

def good_probe():
    return {"format": {"duration": "1800"}, "streams": [
        {"codec_type": "video", "codec_name": "h264", "width": 1920, "height": 1080, "duration": "1800"},
        {"codec_type": "audio", "codec_name": "aac", "duration": "1800"}],
        "chapters": [{"start_time": str(start), "end_time": str(end)} for start, end in zip(V2_OFFSETS, V2_OFFSETS[1:] + [1800])]}


class VideoTests(unittest.TestCase):
    def hour_source(self):
        chapters = []
        for index, seconds in enumerate([900, 1200, 1500], 1):
            chapters.append({"id": f"chapter-{index}", "title": f"Chapter {index}", "seconds": seconds,
                "scenes": [{"id": f"speech-{index}", "kind": "cards", "title": "Measured example",
                            "bullets": ["A source-bound observation"], "references": ["notes"],
                            "narration": "An example."},
                           {"id": f"pause-{index}", "kind": "pause", "title": "Practice",
                            "bullets": ["Explain the observation"], "references": ["notes"],
                            "narration": "", "seconds": 20}]})
        return {"target_seconds": 3600, "max_practice_seconds": 240, "chapters": chapters,
                "title": "A measured course", "media_name": "measured-course.mp4",
                "release_tag": "course-video-v3", "production": {"author": "Codex", "director": "Codex"}}

    def hour_manifest(self):
        source = self.hour_source()
        manifest = {key: copy.deepcopy(source[key]) for key in
                    ("title", "media_name", "release_tag", "production", "max_practice_seconds")}
        manifest.update(scheduled_seconds=3600, practice_seconds=60,
                        chapters=[{"id": "chapter-1", "title": "Chapter 1", "start": 0, "end": 900},
                                  {"id": "chapter-2", "title": "Chapter 2", "start": 900, "end": 2100},
                                  {"id": "chapter-3", "title": "Chapter 3", "start": 2100, "end": 3600}],
                        scenes=[], references={"notes": {"path": "README.md"}},
                        artifacts={"measured-course.mp4": {"bytes": 1048576}})
        for index, (chapter, span) in enumerate(zip(source["chapters"], manifest["chapters"]), 1):
            speech, pause = copy.deepcopy(chapter["scenes"])
            speech.update(start=span["start"], end=span["end"] - 20, tempo=0.9,
                          chapter=index, chapter_title=chapter["title"])
            pause.update(start=span["end"] - 20, end=span["end"],
                         chapter=index, chapter_title=chapter["title"])
            manifest["scenes"].extend([speech, pause])
        return manifest

    def test_hour_timeline_uses_three_source_chapters_and_exact_frames(self):
        source = self.hour_source()
        narration = {"source_sha256": build.digest(build.SOURCE), "scenes": [
            {"id": f"speech-{index}", "seconds": seconds}
            for index, seconds in enumerate([792, 1062, 1332], 1)]}
        chapters, scenes = build.timeline(source, narration)
        self.assertEqual([(c["start"], c["end"]) for c in chapters], [(0, 900), (900, 2100), (2100, 3600)])
        self.assertEqual(sum(s["frames"] for s in scenes), 36000)
        self.assertEqual([s["chapter_count"] for s in scenes], [3] * 6)

    def test_animation_frame_rate_keeps_fractional_scenes_and_audio_samples_exact(self):
        source = self.hour_source()
        source["render_fps"] = 24
        extra = dict(source["chapters"][0]["scenes"][0], id="speech-extra")
        source["chapters"][0]["scenes"].insert(1, extra)
        narration = {"source_sha256": build.digest(build.SOURCE), "scenes": [
            {"id": name, "seconds": seconds} for name, seconds in
            [("speech-1", 352), ("speech-extra", 440), ("speech-2", 1062), ("speech-3", 1332)]]}
        _, scenes = build.timeline(source, narration)
        self.assertEqual(sum(s["frames"] for s in scenes), 86400)
        self.assertEqual(sum(s["frames"] * 1000 for s in scenes), 86400000)
        self.assertEqual(scenes[-1]["end"], 3600)
        self.assertNotEqual(scenes[0]["end"] * 10, round(scenes[0]["end"] * 10))
        for value in [0, 10.5, 29, 120]:
            with self.assertRaisesRegex(ValueError, "render_fps"):
                build.validate(dict(source, render_fps=value))

    def test_hour_probe_rejects_half_length_media_and_shifted_chapter_ends(self):
        manifest = self.hour_manifest()
        probe = {"format": {"duration": "3600"}, "streams": [
            {"codec_type": "video", "codec_name": "h264", "width": 1920, "height": 1080, "duration": "3600"},
            {"codec_type": "audio", "codec_name": "aac", "duration": "3600"}],
            "chapters": [{"start_time": str(c["start"]), "end_time": str(c["end"])} for c in manifest["chapters"]]}
        self.assertEqual(check_probe(probe, manifest)["seconds"], 3600)
        changed = copy.deepcopy(probe)
        changed["format"]["duration"] = "1800"
        with self.assertRaisesRegex(ValueError, "Truncated"):
            check_probe(changed, manifest)
        changed = copy.deepcopy(probe)
        changed["chapters"][0]["end_time"] = "899"
        with self.assertRaisesRegex(ValueError, "chapter"):
            check_probe(changed, manifest)
        manifest["fps"] = 30
        probe["streams"][0]["avg_frame_rate"] = "10/1"
        with self.assertRaisesRegex(ValueError, "frame rate"):
            check_probe(probe, manifest)
        probe["streams"][0]["avg_frame_rate"] = "30/1"
        self.assertEqual(check_probe(probe, manifest)["seconds"], 3600)

    def test_caption_limits_follow_declared_duration_past_minute_thirty(self):
        text = "WEBVTT\n\n00:59:00.000 --> 01:00:00.000\nMeasured result\n"
        expected = [{"start": 3540, "end": 3600, "text": "Measured result"}]
        self.assertEqual(check_vtt(text, expected, 3600), 1)
        with self.assertRaisesRegex(ValueError, "timing"):
            check_vtt(text.replace("01:00:00.000", "01:00:01.000"), expected, 3600)

    def test_source_schedule_rejects_stale_chapter_and_media_mapping(self):
        source, manifest = self.hour_source(), self.hour_manifest()
        verifier.check_schedule(source, manifest)
        cases = []
        changed = copy.deepcopy(manifest)
        changed["scenes"][0]["chapter"] = 2
        cases.append(changed)
        changed = copy.deepcopy(manifest)
        changed["chapters"][1]["title"] = "Stale chapter title"
        cases.append(changed)
        changed = copy.deepcopy(manifest)
        changed["media_name"] = "old-course.mp4"
        cases.append(changed)
        changed = copy.deepcopy(manifest)
        changed["scheduled_seconds"] = 1800
        for chapter in changed["chapters"]:
            chapter["start"] /= 2
            chapter["end"] /= 2
        for scene in changed["scenes"]:
            scene["start"] /= 2
            scene["end"] /= 2
        cases.append(changed)
        for changed in cases:
            with self.assertRaises(ValueError):
                verifier.check_schedule(source, changed)

    def test_practice_budget_is_explicit_and_defaults_to_three_minutes(self):
        source = self.hour_source()
        for chapter in source["chapters"]:
            chapter["scenes"][1]["seconds"] = 80
        build.validate(source)
        del source["max_practice_seconds"]
        with self.assertRaisesRegex(ValueError, "practice"):
            build.validate(source)

    def test_watch_page_uses_publication_fields_and_preserves_hour_timestamps(self):
        manifest = self.hour_manifest()
        manifest["scenes"][-1]["start"] = 3661
        rendered = page.render(manifest)
        for value in ["A measured course", "01:01:01", "measured-course.mp4", "measured-course.webm",
                      "course-video-v3", "Codex"]:
            self.assertIn(value, rendered)
        self.assertNotIn("30-minute", rendered)
        self.assertNotIn("90-second teach-back", rendered)

    def test_active_page_links_all_downloads_to_the_versioned_media_directory(self):
        rendered = page.render(self.hour_manifest())
        for attribute in ['src="v3/measured-course.mp4"', 'src="v3/measured-course.webm"',
                          'src="v3/captions.vtt"', 'poster="v3/poster.png"',
                          'href="v3/transcript.md"', 'href="v3/captions.vtt"',
                          'href="v3/measured-course.mp4#t=900"']:
            self.assertIn(attribute, rendered)
        self.assertIn("docs/customer/video-verification-v3.md", rendered)
        self.assertNotIn('src="measured-course.mp4"', rendered)

    def test_staged_page_uses_explicit_paths_without_changing_the_active_page(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            media = directory / "v3"
            media.mkdir()
            output = directory / "index.html"
            course = directory / "docs/customer/course-source.json"
            course.parent.mkdir(parents=True)
            course.write_text(json.dumps({"facts": {}, "references": {}}), encoding="utf-8")
            reference = directory / "README.md"
            reference.write_text("Fixture reference\n", encoding="utf-8")
            source_path = directory / "source.json"
            source = self.hour_source()
            source.update(fact_bindings_sha256=hashlib.sha256(b"{}").hexdigest(),
                          extra_references={"notes": "README.md"})
            source_path.write_text(json.dumps(source), encoding="utf-8")
            manifest = self.hour_manifest()
            manifest.update(source_path="source.json", source_sha256=build.digest(source_path))
            manifest["references"]["notes"]["sha256"] = build.digest(reference)
            (media / "media-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            active = page.WATCH_PAGE.read_bytes()
            arguments = ["build_video_page.py", "--source", str(source_path),
                         "--media-dir", str(media), "--output", str(output)]
            with patch.object(sys, "argv", arguments), patch.object(page, "ROOT", directory), redirect_stdout(io.StringIO()):
                page.main()
            self.assertEqual(output.read_bytes(), page.render(manifest).encode("utf-8"))
            self.assertEqual(page.WATCH_PAGE.read_bytes(), active)

    def test_symlink_repository_root_keeps_source_and_reference_checks(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary).resolve() / "real-root"
            directory.mkdir()
            alias = directory.parent / "aliased-root"
            try:
                alias.symlink_to(directory, target_is_directory=True)
            except OSError:
                self.skipTest("The test account cannot create directory symlinks")
            media = directory / "v3"
            media.mkdir()
            output = directory / "index.html"
            course = directory / "docs/customer/course-source.json"
            course.parent.mkdir(parents=True)
            course.write_text(json.dumps({"facts": {}, "references": {}}), encoding="utf-8")
            reference = directory / "README.md"
            reference.write_text("Fixture reference\n", encoding="utf-8")
            source_path = directory / "source.json"
            source = self.hour_source()
            source.update(fact_bindings_sha256=hashlib.sha256(b"{}").hexdigest(),
                          extra_references={"notes": "README.md"})
            source_path.write_text(json.dumps(source), encoding="utf-8")
            manifest = self.hour_manifest()
            manifest.update(source_path="source.json", source_sha256=build.digest(source_path))
            manifest["references"]["notes"]["sha256"] = build.digest(reference)
            (media / "media-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            for selected in (alias / "source.json", source_path):
                arguments = ["build_video_page.py", "--source", str(selected),
                             "--media-dir", str(alias / "v3"), "--output", str(alias / "index.html")]
                with (self.subTest(selected=selected), patch.object(sys, "argv", arguments),
                      patch.object(page, "ROOT", alias), redirect_stdout(io.StringIO())):
                    page.main()
                self.assertEqual(output.read_bytes(), page.render(manifest).encode("utf-8"))
            expected = output.read_bytes()
            for target, message in ((source_path, "Video source path or hash"),
                                    (reference, "Video reference changed")):
                original = target.read_bytes()
                target.write_bytes(original + b"\n")
                with (self.subTest(changed=target), patch.object(sys, "argv", arguments),
                      patch.object(page, "ROOT", alias), redirect_stdout(io.StringIO()),
                      self.assertRaisesRegex(ValueError, message)):
                    page.main()
                self.assertEqual(output.read_bytes(), expected)
                target.write_bytes(original)

    def test_legacy_page_requires_a_separate_output_before_writing(self):
        errors = io.StringIO()
        with patch.object(sys, "argv", ["build_video_page.py", "--legacy"]), redirect_stderr(errors):
            with self.assertRaises(SystemExit):
                page.main()
        self.assertIn("--legacy requires --output", errors.getvalue())
        active = page.WATCH_PAGE.read_bytes()
        with patch.object(sys, "argv", ["build_video_page.py", "--legacy", "--output", str(page.WATCH_PAGE)]), redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                page.main()
        self.assertEqual(page.WATCH_PAGE.read_bytes(), active)

    def test_source_identity_cannot_silently_select_the_legacy_name(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for source_path in [None, verifier.LEGACY_SOURCE.relative_to(build.ROOT).as_posix()]:
                manifest = {"source_sha256": build.digest(build.SOURCE)}
                if source_path is not None:
                    manifest["source_path"] = source_path
                (directory / "media-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
                with patch.object(verifier, "load_source", return_value=self.hour_source()):
                    with self.assertRaisesRegex(ValueError, "source path"):
                        verifier.verify_files(directory)

    def test_historical_reference_reads_pinned_bytes_without_executing_them(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            def git(*arguments):
                return subprocess.check_output(["git", "-C", str(root), *arguments], stderr=subprocess.DEVNULL).decode().strip()
            git("init")
            original = b"Historical evidence\n"
            (root / "reference.md").write_bytes(original)
            git("add", "reference.md")
            git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.test", "commit", "-m", "fixture")
            revision = git("rev-parse", "HEAD")
            (root / "reference.md").write_bytes(b"Changed evidence\n")
            self.assertEqual(verifier.reference_bytes("reference.md", root, revision), original)
            self.assertNotEqual(verifier.reference_bytes("reference.md", root), original)
            for relative in ["../reference.md", "/reference.md", "https://example.test/reference.md"]:
                with self.assertRaises(ValueError):
                    verifier.reference_bytes(relative, root, revision)
            with self.assertRaises(ValueError):
                verifier.resolve_reference_revision("HEAD", root)

    def test_table_shape_and_column_widths_are_guarded(self):
        scene = {"id": "table", "kind": "table", "columns": ["Input", "Meaning"],
                 "rows": [["bytes", "Packet content"]], "widths": [1, 2]}
        build.validate_visual(scene)
        for key, value in [("rows", [["bad"]]), ("rows", [["a", "b"]] * 7),
                           ("widths", [1]), ("widths", [0, 1]), ("widths", [float("nan"), 1])]:
            changed = dict(scene, **{key: value})
            with self.assertRaises(ValueError):
                build.validate_visual(changed)

    def test_image_and_extra_references_stay_local_and_hash_bound(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            image = root / "diagram.png"
            image.write_bytes(b"reviewed image bytes")
            scene = {"id": "picture", "kind": "image", "image": "diagram.png",
                     "image_sha256": hashlib.sha256(image.read_bytes()).hexdigest()}
            self.assertEqual(build.image_path(scene, root), image.resolve())
            with self.assertRaises(ValueError):
                build.image_path(dict(scene, image_sha256="0" * 64), root)
            for name in ["https://example.test/image.png", "../outside.png", str(image.resolve())]:
                with self.assertRaises(ValueError):
                    build.image_path(dict(scene, image=name), root)
            source = self.hour_source()
            source["extra_references"] = {"picture": "diagram.png"}
            build.validate(source, root)
            source["extra_references"] = {"picture": "../outside.png"}
            with self.assertRaises(ValueError):
                build.validate(source, root)

    def test_valid_file_hash_cannot_remap_a_source_reference(self):
        source, manifest = self.hour_source(), self.hour_manifest()
        source["extra_references"] = {"notes": "README.md"}
        manifest["source_sha256"] = build.digest(build.SOURCE)
        manifest["source_path"] = build.SOURCE.relative_to(build.ROOT).as_posix()
        wrong = "docs/harness-reference.md"
        manifest["references"]["notes"] = {"path": wrong, "sha256": build.digest(build.ROOT / wrong)}
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for name in ["measured-course.mp4", "captions.vtt", "captions.srt", "transcript.md", "chapters.json", "poster.png"]:
                path = directory / name
                path.write_bytes(b"fixture")
                manifest["artifacts"][name] = {"bytes": path.stat().st_size, "sha256": build.digest(path)}
            (directory / "media-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            with patch.object(verifier, "load_source", return_value=source):
                with self.assertRaisesRegex(ValueError, "reference mapping"):
                    verifier.verify_files(directory)

    def caption_fixture(self):
        left = "This measured sentence contains enough ordinary words to span a long first caption"
        right = "followed by a shorter second caption."
        return {"id": "timing", "kind": "teaching", "start": 100, "end": 140, "tempo": 0.8,
                "audio": {"wav_sha256": "a" * 64, "cues": [
                    {"start": 2, "end": 24, "text": left + " " + right}]},
                "caption_boundary_overrides": [{"wav_sha256": "a" * 64,
                    "left_text": left, "right_text": right, "raw_seconds": 12.0}]}

    def test_caption_audio_anchor_maps_through_scene_start_and_tempo(self):
        cues = caption_cues([self.caption_fixture()])
        self.assertEqual(len(cues), 2)
        self.assertEqual(cues[0]["start"], 102.5)
        self.assertEqual(cues[0]["end"], 115)
        self.assertEqual(cues[1]["start"], 115)
        self.assertEqual(cues[1]["end"], 130)

    def test_stale_caption_audio_or_changed_caption_words_are_rejected(self):
        for key, value in [("wav_sha256", "b" * 64), ("left_text", "Changed wording")]:
            scene = self.caption_fixture()
            scene["caption_boundary_overrides"][0][key] = value
            with self.assertRaisesRegex(ValueError, "caption.*anchor"):
                caption_cues([scene])

    def test_caption_anchor_must_be_unique_finite_and_within_its_sentence(self):
        for value in [float("nan"), float("inf"), 1, 24, 50]:
            scene = self.caption_fixture()
            scene["caption_boundary_overrides"][0]["raw_seconds"] = value
            with self.assertRaises(ValueError):
                caption_cues([scene])
        scene = self.caption_fixture()
        scene["caption_boundary_overrides"] *= 2
        with self.assertRaises(ValueError):
            caption_cues([scene])

    def test_historical_video_and_captions_match_the_pinned_reviewed_source(self):
        from verify_video_course_v3 import V3_REVISION
        manifest, result = verifier.verify_historical_files()
        self.assertEqual(result["status"], "passed")
        self.assertGreater(result["scenes"], 0)
        original_page = subprocess.check_output(["git", "--no-replace-objects", "-C", str(build.ROOT),
            "cat-file", "blob", V3_REVISION + ":docs/customer/demo/video/index.html"])
        self.assertEqual(original_page, page.render(manifest, media_dir=build.V3_DESTINATION).encode("utf-8"))

    def test_truncated_container_and_stream_are_rejected(self):
        for field in ["container", "stream"]:
            probe = good_probe()
            if field == "container":
                probe["format"]["duration"] = "30"
            else:
                probe["streams"][1]["duration"] = "30"
            with self.assertRaises(ValueError):
                check_probe(probe, V2_SCHEDULE)

    def test_missing_audio_and_drifted_chapters_are_rejected(self):
        probe = good_probe()
        self.assertEqual(check_probe(probe, V2_SCHEDULE)["seconds"], 1800)
        probe["streams"].pop()
        with self.assertRaisesRegex(ValueError, "audio"):
            check_probe(probe, V2_SCHEDULE)
        probe = good_probe()
        probe["chapters"][1]["start_time"] = "125"
        with self.assertRaisesRegex(ValueError, "chapter"):
            check_probe(probe, V2_SCHEDULE)

    def test_silent_and_unexplained_audio_are_rejected(self):
        scenes = [{"kind": "pause", "id": "practice", "start": 100, "end": 110}]
        check_silences([(99.8, 110.2)], scenes)
        for intervals in [[(0, 1800)], [(99.8, 110.2), (500, 510)], []]:
            with self.assertRaises(ValueError):
                check_silences(intervals, scenes)

    def test_invalid_caption_timing_and_altered_words_are_rejected(self):
        expected = [{"start": 0, "end": 2, "text": "Measured result"}]
        valid = "WEBVTT\n\n00:00:00.000 --> 00:00:02.000\nMeasured result\n"
        self.assertEqual(check_vtt(valid, expected), 1)
        for changed in [valid.replace("02.000", "00.000"), valid.replace("Measured", "Invented"), valid.replace("00:00:02.000", "00:30:02.000")]:
            with self.assertRaises(ValueError):
                check_vtt(changed, expected)

    def test_changed_download_bytes_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            manifest = self.hour_manifest()
            manifest["source_path"] = build.SOURCE.relative_to(build.ROOT).as_posix()
            manifest["source_sha256"] = build.digest(build.SOURCE)
            media_name = build.publication(manifest)["media_name"]
            for name in [media_name, "captions.vtt", "captions.srt", "transcript.md", "chapters.json", "poster.png"]:
                manifest["artifacts"][name] = {"bytes": 5, "sha256": "0" * 64}
            (path / "media-manifest.json").write_text(json.dumps(manifest), encoding="utf-8", newline="\n")
            (path / media_name).write_bytes(b"wrong")
            with patch.object(verifier, "load_source", return_value=self.hour_source()):
                with self.assertRaisesRegex(ValueError, "checksum"):
                    verify_files(path)

    def test_frame_allocation_is_exact_and_rejects_invalid_speech(self):
        result = allocate_frames([12.98, 41.31, 8.92], 1100)
        self.assertEqual(sum(result), 1100)
        self.assertTrue(all(n > 0 for n in result))
        for invalid in [[0, 1], [float("nan")], [-1], []]:
            with self.assertRaises(ValueError):
                allocate_frames(invalid, 100)


if __name__ == "__main__":
    unittest.main()
