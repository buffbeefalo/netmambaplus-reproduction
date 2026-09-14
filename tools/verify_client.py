"""Check client identities and recorded packet evidence without media or Git history."""

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

LOCAL_DIRECTORIES = {".git", "upstream", ".evidence", "data", "datasets", "checkpoints", "runs",
                     "output", "outputs", "logs", "artifacts", "assets", ".venv", ".venv-cuda",
                     ".venv-gb10", "venv", "build-gb10", ".pytest_cache"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    def invalid(value):
        raise ValueError(f"Nonfinite JSON value: {value}")
    return json.loads(path.read_text(encoding="utf-8"), parse_constant=invalid)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def local(root, name):
    require(isinstance(name, str) and name and "\\" not in name and ":" not in name,
            f"Invalid inventory path: {name!r}")
    parts = PurePosixPath(name)
    require(not parts.is_absolute() and parts.as_posix() == name and
            all(p not in (".", "..") and p.lower() != ".git" for p in parts.parts), f"Unsafe path: {name}")
    path = root / name
    require(path.resolve().is_relative_to(root) and path.is_file() and not path.is_symlink(),
            f"Missing or unsafe file: {name}")
    parent = path.parent
    while parent != root:
        require(not parent.is_symlink(), f"Symlink directory: {name}")
        parent = parent.parent
    return path


def verify_inventory(root):
    root = Path(root).resolve()
    manifest = read(root / "CLIENT_MANIFEST.json")
    require(manifest.get("schema") == 1 and
            manifest.get("source_repository") == "https://github.com/buffbeefalo/netmambaplus-reproduction",
            "Invalid client provenance")
    for key, size in (("source_commit", 40), ("selection_sha256", 64), ("exporter_sha256", 64)):
        require(bool(re.fullmatch(r"[0-9a-f]{" + str(size) + "}", manifest.get(key, ""))),
                f"Invalid {key}")
    files = manifest["files"]
    require(isinstance(files, dict) and files, "Empty client inventory")
    for name, item in files.items():
        path = local(root, name)
        require(path.stat().st_size == item["bytes"] and digest(path) == item["sha256"],
                f"Delivered file differs from manifest: {name}")
    actual = set()
    for directory, directories, names in os.walk(root):
        base = Path(directory)
        directories[:] = [d for d in directories if d != "__pycache__" and
                           not (base == root and d in LOCAL_DIRECTORIES)]
        for d in directories:
            require(not (base / d).is_symlink(), f"Unexpected symlink directory: {base / d}")
        for name in names:
            if name.endswith((".pyc", ".pyo")):
                continue
            actual.add((base / name).relative_to(root).as_posix())
    require(actual == set(files) | {"CLIENT_MANIFEST.json"},
            "Client inventory differs: " + str(sorted(actual ^ (set(files) | {"CLIENT_MANIFEST.json"}))))
    return {"files": len(files), "source_commit": manifest["source_commit"]}


def verify_packet(root):
    from tools.review_packet_study import verify
    return verify(Path(root).resolve() / "docs/customer/evidence/packet-study")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--inventory-only", action="store_true")
    args = parser.parse_args()
    try:
        result = {"status": "passed", "inventory": verify_inventory(args.root)}
        if not args.inventory_only:
            result["packet_evidence"] = verify_packet(args.root)
        result["scope"] = "Offline file/hash and saved-evidence checks; no new GPU execution or authenticity signature."
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print(f"Client verification failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
