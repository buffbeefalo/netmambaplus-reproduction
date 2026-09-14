"""Package verified files and publish them without executing client code."""

import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tarfile

MANIFEST = "CLIENT_MANIFEST.json"
SOURCE = "https://github.com/buffbeefalo/netmambaplus-reproduction"
REMOTE = "git@github.com:buffbeefalo/netmambaplus-client.git"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.PIPE).decode().strip()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def safe(name):
    require(isinstance(name, str) and name and "\\" not in name and ":" not in name, "Unsafe archive path")
    path = PurePosixPath(name)
    require(not path.is_absolute() and path.as_posix() == name and
            all(p not in (".", "..") and p.lower() != ".git" for p in path.parts), "Unsafe archive path")


def validate(content, source_sha=None):
    require(MANIFEST in content, "Delivery manifest is missing")
    manifest = json.loads(content[MANIFEST])
    require(manifest.get("schema") == 1 and manifest.get("source_repository") == SOURCE,
            "Invalid delivery provenance")
    require(bool(re.fullmatch(r"[0-9a-f]{40}", manifest.get("source_commit", ""))), "Invalid source revision")
    if source_sha is not None:
        require(manifest["source_commit"] == source_sha, "Archive contains a different source revision")
    require(set(content) == set(manifest["files"]) | {MANIFEST}, "Archive inventory differs from manifest")
    for name, raw in content.items():
        safe(name)
        if name != MANIFEST:
            item = manifest["files"][name]
            require(len(raw) == item["bytes"] and digest(raw) == item["sha256"], "Archive file hash mismatch: " + name)
            require(item.get("mode", "100644") in ("100644", "100755"), "Unsupported delivery mode")
    return manifest


def pack(client, archive):
    client, archive = Path(client).resolve(), Path(archive)
    head = git(client, "rev-parse", "HEAD")
    if not git(client, "status", "--porcelain", "--untracked-files=all"):
        return {"changed": False, "client_head": head}
    manifest_raw = (client / MANIFEST).read_bytes()
    manifest = json.loads(manifest_raw)
    content = {MANIFEST: manifest_raw}
    for name in manifest["files"]:
        safe(name)
        path = client / name
        require(path.resolve().is_relative_to(client) and path.is_file() and not path.is_symlink(),
                "Invalid archive source: " + name)
        content[name] = path.read_bytes()
    validate(content)
    with archive.open("xb") as raw, gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode="w") as tar:
            for name, data in sorted(content.items()):
                info = tarfile.TarInfo(name)
                info.size = len(data)
                info.mode = 0o755 if manifest["files"].get(name, {}).get("mode") == "100755" else 0o644
                tar.addfile(info, io.BytesIO(data))
    return {"changed": True, "client_head": head, "archive_sha": digest(archive.read_bytes())}


def publish(*, client, archive, archive_sha, client_head, source_sha, expected_remote=REMOTE):
    client, archive = Path(client).resolve(), Path(archive)
    require(bool(re.fullmatch(r"[0-9a-f]{40}", client_head)) and
            bool(re.fullmatch(r"[0-9a-f]{40}", source_sha)), "Invalid commit identity")
    require(git(client, "remote", "get-url", "--push", "origin") == expected_remote, "Unexpected client remote")
    require(git(client, "branch", "--show-current") == "main", "Client is not on main")
    require(git(client, "rev-parse", "HEAD") == client_head, "Client tip changed since verification")
    require(not git(client, "status", "--porcelain", "--untracked-files=all"), "Publisher checkout is not clean")
    remote_tip = git(client, "ls-remote", "origin", "refs/heads/main").split()
    require(remote_tip and remote_tip[0] == client_head, "Remote client tip changed since verification")
    raw = archive.read_bytes()
    require(digest(raw) == archive_sha, "Verified archive hash mismatch")
    content = {}
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as tar:
        for member in tar:
            safe(member.name)
            require(member.isfile() and member.name not in content, "Invalid or duplicate archive member")
            require(member.size <= 100 * 1024 * 1024, "Oversize archive member")
            content[member.name] = tar.extractfile(member).read()
    manifest = validate(content, source_sha)
    tracked = set(filter(None, git(client, "ls-files", "-z").split("\0")))
    for name in content:
        target = client / name
        require(target.resolve().is_relative_to(client) and not target.is_symlink(), "Unsafe publisher destination")
        require(name in tracked or not target.exists(), "Unmanaged destination collision")
    for name in tracked - content.keys():
        (client / name).unlink()
    for name, data in content.items():
        target = client / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        target.chmod(0o755 if manifest["files"].get(name, {}).get("mode") == "100755" else 0o644)
    git(client, "add", "--all")
    git(client, "-c", "user.name=netmambaplus-sync", "-c", "user.email=41898282+github-actions[bot]@users.noreply.github.com",
        "commit", "-m", "Sync verified source " + source_sha)
    require(git(client, "ls-remote", "origin", "refs/heads/main").split()[0] == client_head,
            "Concurrent client update; normal push refused")
    git(client, "push", "origin", "HEAD:refs/heads/main")
    return {"status": "published", "client_commit": git(client, "rev-parse", "HEAD"), "source_commit": source_sha}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("pack", "publish"):
        command = commands.add_parser(name)
        command.add_argument("--client", type=Path, required=True)
        command.add_argument("--archive", type=Path, required=True)
        if name == "pack":
            command.add_argument("--output", type=Path, required=True)
        else:
            for arg in ("archive-sha", "client-head", "source-sha"):
                command.add_argument("--" + arg, required=True)
    args = parser.parse_args()
    try:
        if args.command == "pack":
            result = pack(args.client, args.archive)
            with args.output.open("a", encoding="utf-8") as stream:
                for key, value in result.items():
                    stream.write(f"{key}={str(value).lower() if isinstance(value, bool) else value}\n")
        else:
            result = publish(client=args.client, archive=args.archive, archive_sha=args.archive_sha,
                             client_head=args.client_head, source_sha=args.source_sha)
        print(json.dumps(result))
        return 0
    except (ValueError, KeyError, OSError, subprocess.SubprocessError, tarfile.TarError) as exc:
        print(f"Client publication refused: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
