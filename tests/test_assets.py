import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import fetch_assets


class AssetChecks(unittest.TestCase):
    def test_matching_existing_asset_is_reused_without_network(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "asset"
            target.write_bytes(b"verified")
            spec = {"bytes": 8, "sha256": hashlib.sha256(b"verified").hexdigest(), "url": "https://unused"}
            with patch("urllib.request.urlopen", side_effect=AssertionError("Network was used")):
                self.assertEqual(fetch_assets.acquire(target, spec), "already_verified")

    def test_existing_mismatch_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "asset"
            target.write_bytes(b"keep")
            with self.assertRaises(ValueError):
                fetch_assets.acquire(target, {"bytes": 3, "sha256": "0" * 64, "url": "https://unused"})
            self.assertEqual(target.read_bytes(), b"keep")

    def test_download_hash_failure_never_publishes_target(self):
        import io
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "asset"
            spec = {"bytes": 3, "sha256": "0" * 64, "url": "https://example.test/asset"}
            with patch("urllib.request.urlopen", return_value=io.BytesIO(b"bad")):
                with self.assertRaises(ValueError):
                    fetch_assets.acquire(target, spec)
            self.assertFalse(target.exists())
            self.assertEqual(list(Path(directory).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
