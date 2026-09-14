"""Stage a checked client update; never commit, push or rewrite history."""

import argparse
import json
from pathlib import Path
import subprocess
import sys

from export_client import MANIFEST, ROOT, canonical, git, snapshot


def synchronize(source, revision, destination):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    git_root = Path(git(destination, "rev-parse", "--show-toplevel").decode().strip()).resolve()
    if git_root != destination or source == destination:
        raise ValueError("Destination must be its own separate Git checkout")
    if git(destination, "status", "--porcelain", "--untracked-files=all").strip():
        raise ValueError("Client checkout has uncommitted or untracked changes")
    manifest_path = destination / MANIFEST
    old = json.loads(manifest_path.read_bytes())
    old_expected, old_content = snapshot(source, old["source_commit"])
    if manifest_path.read_bytes() != canonical(old_expected):
        raise ValueError("Client provenance differs from the recorded source snapshot")
    tracked = {p.decode("utf-8") for p in git(destination, "ls-files", "-z").split(b"\0") if p}
    if tracked != set(old_content):
        raise ValueError("Client tracked-file inventory diverged from its source snapshot")
    for record in git(destination, "ls-files", "--stage", "-z").split(b"\0"):
        if record:
            metadata, name = record.split(b"\t", 1)
            expected_mode = old_expected["files"].get(name.decode("utf-8"), {}).get("mode", "100644")
            if metadata.split()[0].decode() != expected_mode:
                raise ValueError("Client file mode differs from source snapshot")
    for name, raw in old_content.items():
        path = destination / name
        if path.is_symlink() or not path.is_file() or path.read_bytes() != raw:
            raise ValueError(f"Client file differs from source snapshot: {name}")
    new, content = snapshot(source, revision)
    if subprocess.run(["git", "-C", str(source), "merge-base", "--is-ancestor",
                       old_expected["source_commit"], new["source_commit"]],
                      capture_output=True).returncode:
        raise ValueError("Source rollback or unrelated history is refused")
    if all(old_expected[k] == new[k] for k in ("files", "selection_sha256", "exporter_sha256")):
        return {"changed": False, "source_commit": old_expected["source_commit"]}
    for name in content:
        path = destination / name
        if not path.resolve().is_relative_to(destination) or path.is_symlink():
            raise ValueError(f"Unsafe client target: {name}")
        if name not in old_content and path.exists():
            raise ValueError(f"New delivery collides with a local path: {name}")
    for name in old_content.keys() - content.keys():
        (destination / name).unlink()
    for name, raw in content.items():
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        path.chmod(0o755 if new["files"].get(name, {}).get("mode") == "100755" else 0o644)
    return {"changed": True, "source_commit": new["source_commit"], "files": len(new["files"])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT)
    parser.add_argument("--revision", default="HEAD")
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(synchronize(args.source, args.revision, args.destination)))
        return 0
    except (ValueError, KeyError, OSError, subprocess.SubprocessError) as exc:
        print(f"Client update refused: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
