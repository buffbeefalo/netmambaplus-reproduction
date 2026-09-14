"""Exercise published text and byte identities with Windows text defaults."""

import hashlib
import io
import json
import sys
import tempfile
import unittest
from contextlib import contextmanager, redirect_stdout
from pathlib import Path, PureWindowsPath
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build_course_video
import build_video_page
import verify_course
import verify_course_video
import verify_package
from verify_video_course_v3 import historical_snapshot


@contextmanager
def windows_text_defaults():
    """Keep real file I/O while emulating legacy Windows locale and newlines."""
    original = Path.open

    def open_text(path, mode="r", buffering=-1, encoding=None, errors=None, newline=None):
        if "b" not in mode:
            if encoding in (None, "locale"):
                encoding = "cp1252"
            if newline is None and any(flag in mode for flag in "wax+"):
                newline = "\r\n"
        return original(path, mode, buffering, encoding, errors, newline)

    with patch.object(Path, "open", open_text):
        yield


class PublishedTextTests(unittest.TestCase):
    def test_course_verifies_with_a_non_utf8_default_encoding(self):
        with windows_text_defaults():
            result = verify_course.verify()
        self.assertEqual(result["status"], "passed")

    def test_package_verifies_with_a_non_utf8_default_encoding(self):
        with windows_text_defaults(), patch.object(sys, "argv", ["verify_package.py"]), redirect_stdout(io.StringIO()):
            verify_package.main()

    def test_video_verifies_with_a_non_utf8_default_encoding(self):
        with windows_text_defaults(), patch.object(sys, "argv", ["build_video_page.py", "--check"]), redirect_stdout(io.StringIO()):
            _, result = verify_course_video.verify_historical_files(version=4)
            build_video_page.main()
        self.assertEqual(result["status"], "passed")

    def test_generated_captions_keep_utf8_lf_bytes(self):
        cue = {"scene": "speech", "start": 0, "end": 2, "text": "Measured \u2192 reviewed"}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            with windows_text_defaults():
                build_course_video.write_captions([cue], [], path, path)
            expected = "WEBVTT\n\n00:00:00.000 --> 00:00:02.000\nMeasured \u2192 reviewed\n".encode("utf-8")
            self.assertEqual((path / "captions.vtt").read_bytes(), expected)
            for name in ("captions.srt", "captions.ass"):
                raw = (path / name).read_bytes()
                self.assertIn("Measured \u2192 reviewed".encode("utf-8"), raw)
                self.assertNotIn(b"\r\n", raw)

    def test_generated_watch_page_keeps_utf8_lf_bytes(self):
        with historical_snapshot(ROOT, version=4) as (snapshot, _), tempfile.TemporaryDirectory() as directory:
            source = snapshot / "docs/customer/video-course-v4-source.json"
            manifest = (snapshot / "docs/customer/demo/video/v4/media-manifest.json").read_bytes()
            path = Path(directory)
            media = path / "v4"
            media.mkdir()
            (media / "media-manifest.json").write_bytes(manifest)
            expected = build_video_page.render(json.loads(manifest), media_dir=media,
                                              output=path / "index.html").encode("utf-8")
            with (patch.object(sys, "argv", ["build_video_page.py", "--media-dir", str(media),
                                             "--source", str(source),
                                             "--output", str(path / "index.html")]),
                  patch.object(build_video_page, "ROOT", snapshot),
                  windows_text_defaults(), redirect_stdout(io.StringIO())):
                build_video_page.main()
            self.assertEqual((path / "index.html").read_bytes(), expected)

    def test_written_checksums_use_posix_paths_and_utf8_lf_bytes(self):
        raw = b"reviewed\n"
        original_relative_to = Path.relative_to

        def windows_relative_to(path, *other):
            return PureWindowsPath(original_relative_to(path, *other))

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            customer = root / "docs/customer"
            customer.mkdir(parents=True)
            (customer / "review-\u03bb.md").write_bytes(raw)
            with (patch.object(verify_package, "ROOT", root),
                  patch.object(verify_package, "CUSTOMER", customer),
                  patch.object(verify_package, "verify", return_value={}),
                  patch.object(Path, "relative_to", windows_relative_to),
                  patch.object(sys, "argv", ["verify_package.py", "--write-sha256"]),
                  windows_text_defaults(), redirect_stdout(io.StringIO())):
                verify_package.main()
            expected = f"{hashlib.sha256(raw).hexdigest()}  docs/customer/review-\u03bb.md\n".encode("utf-8")
            self.assertEqual((customer / "SHA256SUMS").read_bytes(), expected)


if __name__ == "__main__":
    unittest.main()
