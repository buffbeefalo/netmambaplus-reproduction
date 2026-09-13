"""Video acceptance gates reject media and caption failures on a CPU."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from build_course_video import allocate_frames
from verify_course_video import OFFSETS, check_probe, check_silences, check_vtt, verify_files


def good_probe():
    return {"format": {"duration": "1800"}, "streams": [
        {"codec_type": "video", "codec_name": "h264", "width": 1920, "height": 1080, "duration": "1800"},
        {"codec_type": "audio", "codec_name": "aac", "duration": "1800"}],
        "chapters": [{"start_time": str(start), "end_time": str(end)} for start, end in zip(OFFSETS, OFFSETS[1:] + [1800])]}


class VideoTests(unittest.TestCase):
    def test_committed_video_and_captions_match_reviewed_source(self):
        _, result = verify_files()
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["scenes"], 60)
        from build_video_page import render, DESTINATION
        self.assertEqual((DESTINATION / "index.html").read_bytes(), render().encode("utf-8"))

    def test_truncated_container_and_stream_are_rejected(self):
        for field in ["container", "stream"]:
            probe = good_probe()
            if field == "container":
                probe["format"]["duration"] = "30"
            else:
                probe["streams"][1]["duration"] = "30"
            with self.assertRaises(ValueError):
                check_probe(probe)

    def test_missing_audio_and_drifted_chapters_are_rejected(self):
        probe = good_probe()
        self.assertEqual(check_probe(probe)["seconds"], 1800)
        probe["streams"].pop()
        with self.assertRaisesRegex(ValueError, "audio"):
            check_probe(probe)
        probe = good_probe()
        probe["chapters"][1]["start_time"] = "125"
        with self.assertRaisesRegex(ValueError, "chapter"):
            check_probe(probe)

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
            from narrate_course_video import SOURCE, digest
            from build_course_video import MEDIA_NAME, DESTINATION
            manifest = json.loads((DESTINATION / "media-manifest.json").read_text(encoding="utf-8"))
            manifest["artifacts"][MEDIA_NAME] = {"bytes": 5, "sha256": "0" * 64}
            (path / "media-manifest.json").write_text(json.dumps(manifest), encoding="utf-8", newline="\n")
            (path / MEDIA_NAME).write_bytes(b"wrong")
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
