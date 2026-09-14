"""Export an explicit, committed client snapshot without copying Git history."""

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SPEC = "configs/client-manifest.json"
MANIFEST = "CLIENT_MANIFEST.json"
SOURCE_URL = "https://github.com/buffbeefalo/netmambaplus-reproduction"
EVIDENCE = "docs/customer/evidence/"
EVIDENCE_SUFFIXES = {".json", ".jsonl", ".log", ".txt", ".gz"}


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.PIPE)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def safe_path(name):
    if not isinstance(name, str) or not name or "\\" in name or ":" in name:
        raise ValueError(f"Unsafe path: {name!r}")
    path = PurePosixPath(name)
    if path.is_absolute() or path.as_posix() != name or any(
            part in (".", "..") or part.lower() == ".git" for part in path.parts):
        raise ValueError(f"Unsafe path: {name!r}")
    return path


def allowed_destination(name):
    path = safe_path(name)
    if any(re.search(r"video|course|presentation|narrat|talk-track", p, re.I) for p in path.parts):
        raise ValueError(f"Excluded presentation path: {name}")
    if name in {"README.md", "SETUP.md", "RESULTS.md", "NOTICE.md", ".gitignore",
                ".gitattributes", ".github/workflows/ci.yml"}:
        return
    if name.startswith(EVIDENCE) and path.suffix in EVIDENCE_SUFFIXES:
        return
    if name == "docs/portability-evidence.json" or name == "requirements/gb10.txt":
        return
    if path.suffix == ".py" and (len(path.parts) == 1 or
                                  len(path.parts) == 2 and path.parts[0] in ("tools", "tests")):
        return
    if len(path.parts) == 2 and path.parts[0] == "configs" and path.suffix == ".json":
        return
    raise ValueError(f"Excluded destination: {name}")


def snapshot(source, revision):
    source = Path(source).resolve()
    if revision.startswith("-"):
        raise ValueError("Revision cannot be a Git option")
    commit = git(source, "rev-parse", "--verify", revision + "^{commit}").decode().strip()
    tree = {}
    for record in git(source, "ls-tree", "-rz", "--full-tree", commit).split(b"\0"):
        if record:
            metadata, path = record.split(b"\t", 1)
            mode, kind, oid = metadata.decode().split()
            tree[path.decode("utf-8")] = (mode, kind, oid)

    def read(name):
        safe_path(name)
        if name not in tree:
            raise ValueError(f"Required committed file is missing: {name}")
        mode, kind, oid = tree[name]
        if kind != "blob" or mode not in ("100644", "100755"):
            raise ValueError(f"Only regular files can be exported: {name}")
        return git(source, "cat-file", "blob", oid)

    spec_raw = read(SPEC)
    spec = json.loads(spec_raw)
    if spec.get("schema") != 1 or not isinstance(spec.get("files"), list) or not isinstance(spec.get("templates"), dict):
        raise ValueError("Invalid client selection manifest")
    for name in tree:
        if name.startswith(EVIDENCE) and PurePosixPath(name).suffix not in EVIDENCE_SUFFIXES:
            raise ValueError(f"Unexpected evidence file type: {name}")
    selected = {}
    for name in spec["files"]:
        allowed_destination(name)
        if name in selected:
            raise ValueError(f"Duplicate destination: {name}")
        selected[name] = name
    for destination, origin in spec["templates"].items():
        allowed_destination(destination)
        safe_path(origin)
        if destination in selected or not origin.startswith("client/") or not origin.endswith(".in"):
            raise ValueError(f"Invalid template mapping: {destination}")
        selected[destination] = origin
    if len({name.casefold() for name in selected}) != len(selected):
        raise ValueError("Destination paths collide on case-insensitive filesystems")
    content, inventory = {}, {}
    for destination, origin in sorted(selected.items()):
        raw = read(origin)
        content[destination] = raw
        inventory[destination] = {"source_path": origin, "bytes": len(raw), "sha256": digest(raw),
                                  "mode": tree[origin][0]}
    manifest = {"schema": 1, "source_repository": SOURCE_URL, "source_commit": commit,
                "selection_sha256": digest(spec_raw),
                "exporter_sha256": digest(read("tools/export_client.py")), "files": inventory}
    content[MANIFEST] = canonical(manifest)
    return manifest, content


def export(source, revision, output):
    output = Path(output)
    if output.exists() or output.is_symlink():
        raise ValueError(f"Output already exists: {output}")
    manifest, content = snapshot(source, revision)
    output.mkdir(parents=True, exist_ok=False)
    for name, raw in content.items():
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        target.chmod(0o755 if manifest["files"].get(name, {}).get("mode") == "100755" else 0o644)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT)
    parser.add_argument("--revision", default="HEAD")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        manifest = export(args.source, args.revision, args.output)
        print(json.dumps({"source_commit": manifest["source_commit"], "files": len(manifest["files"]),
                          "output": str(args.output)}))
        return 0
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        print(f"Client export refused: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
