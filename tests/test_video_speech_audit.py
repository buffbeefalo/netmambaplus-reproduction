"""Cheap input-integrity checks; these fixtures make no ASR success claim."""

import hashlib
import importlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
try:
    audit = importlib.import_module("audit_video_speech")
except ModuleNotFoundError:
    audit = None


class SpeechAuditInputTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(audit, "speech audit helper is missing")
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.media = self.root / "lesson.mp4"
        self.media.write_bytes(b"fixture; not a playable video")
        self.source = self.root / "source.json"
        self.source.write_text(json.dumps({"chapters": [{"scenes": [
            {"id": "intro", "narration": "Explain a packet."},
            {"id": "pause", "narration": ""}]}]}))
        self.manifest = self.root / "manifest.json"
        self.value = {
            "source_path": "source.json",
            "source_sha256": self.digest(self.source),
            "media_name": self.media.name,
            "artifacts": {self.media.name: {"sha256": self.digest(self.media),
                                           "bytes": self.media.stat().st_size}},
            "scheduled_seconds": 3,
            "scenes": [{"id": "intro", "start": 0, "end": 2,
                        "narration": "Explain a packet."},
                       {"id": "pause", "start": 2, "end": 3, "narration": ""}],
        }
        self.save()

    @staticmethod
    def digest(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def save(self):
        self.manifest.write_text(json.dumps(self.value))

    def validate(self, expected=1):
        return audit.validate_inputs(self.media, self.manifest, expected, root=self.root)

    def test_valid_input_binding_only(self):
        bound = self.validate()
        self.assertEqual(len(bound.scenes), 1)
        audit.check_unchanged(bound)

    def test_rejects_changed_media(self):
        self.media.write_bytes(b"modified")
        with self.assertRaisesRegex(ValueError, "media"):
            self.validate()

    def test_rejects_changed_source(self):
        self.source.write_text("{}")
        with self.assertRaisesRegex(ValueError, "source"):
            self.validate()

    def test_rejects_source_narration_mismatch(self):
        self.value["scenes"][0]["narration"] = "Different content."
        self.save()
        with self.assertRaisesRegex(ValueError, "source"):
            self.validate()

    def test_rejects_wrong_scene_count(self):
        for count in (0, -1, 2, True):
            with self.subTest(count=count), self.assertRaises(ValueError):
                self.validate(count)

    def test_rejects_invalid_bounds(self):
        for start, end in [(-1, 2), (2, 2), (2, 1), (0, 4),
                           (float("nan"), 2), (0, float("inf")), (False, 2)]:
            with self.subTest(start=start, end=end):
                self.value["scenes"][0].update(start=start, end=end)
                self.save()
                with self.assertRaises(ValueError):
                    self.validate()

    def test_rejects_overlap_and_duplicate_ids(self):
        self.value["scenes"][1]["start"] = 1
        self.save()
        with self.assertRaisesRegex(ValueError, "overlap"):
            self.validate()
        self.value["scenes"][1].update(start=2, id="intro")
        self.save()
        with self.assertRaisesRegex(ValueError, "scene"):
            self.validate()

    def test_rechecks_all_input_bindings(self):
        for name in ("media", "source", "manifest"):
            with self.subTest(name=name):
                bound = self.validate()
                path = getattr(self, name)
                original = path.read_bytes()
                path.write_bytes(original + b" ")
                with self.assertRaisesRegex(ValueError, "changed"):
                    audit.check_unchanged(bound)
                path.write_bytes(original)

    def test_rejects_decoded_audio_shorter_than_scene(self):
        bound = self.validate()
        with self.assertRaisesRegex(ValueError, "decoded audio"):
            audit.check_audio_bounds(bound.scenes, 16000)


if __name__ == "__main__":
    unittest.main()
