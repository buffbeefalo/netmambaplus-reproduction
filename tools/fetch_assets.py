"""Acquire the pinned authors' research assets, checking every byte before use."""

import argparse
import hashlib
import io
import json
import os
import sys
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import repro


def acquire(target, specification):
    target = Path(target)
    expected_size, expected_hash = specification["bytes"], specification["sha256"]
    if target.exists() or target.is_symlink():
        if (target.is_symlink() or not target.is_file() or target.stat().st_size != expected_size
                or repro.sha256_file(target) != expected_hash):
            raise ValueError(f"Existing asset differs; preserved without overwrite: {target}")
        return "already_verified"
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=".download-", dir=target.parent)
    temporary = Path(temporary_name)
    try:
        if "content" in specification:
            source = io.BytesIO(json.dumps(specification["content"], indent=2).encode("utf-8"))
        else:
            source = urllib.request.urlopen(specification["url"], timeout=90)
        digest, total = hashlib.sha256(), 0
        with os.fdopen(descriptor, "wb") as stream, source:
            descriptor = None
            while block := source.read(1024 * 1024):
                total += len(block)
                if total > expected_size:
                    raise ValueError(f"Download exceeds recorded size: {target.name}")
                stream.write(block)
                digest.update(block)
            stream.flush()
            os.fsync(stream.fileno())
        if total != expected_size or digest.hexdigest() != expected_hash:
            raise ValueError(f"Asset size or SHA-256 mismatch: {target.name}")
        os.link(temporary, target)
        return "generated_and_verified" if "content" in specification else "downloaded_and_verified"
    finally:
        if descriptor is not None:
            os.close(descriptor)
        temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "assets")
    args = parser.parse_args()
    inventory = json.loads((ROOT / "configs/assets.json").read_text())
    results = []
    for name, specification in inventory["files"].items():
        target = args.output / name
        status = acquire(target, specification)
        print(f"{status}: {name}")
        results.append({"path": name, "status": status, "sha256": specification["sha256"],
                        "bytes": specification["bytes"]})
    repro.atomic_json(args.output / "acquisition.json", {
        "created_at": repro.timestamp(), "source_inventory_sha256": repro.sha256_file(ROOT / "configs/assets.json"),
        "files": results, "license_note": inventory["license_note"]})


if __name__ == "__main__":
    main()
