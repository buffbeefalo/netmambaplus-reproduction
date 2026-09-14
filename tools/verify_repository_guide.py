"""Check individual guide entries for every current tracked/nonignored file.

Each entry is a Markdown table row with one unique <a id="file-..."></a>
anchor, one local file link in its first cell, and a description in its second.
Ordinary links, directory summaries and historical course inventories do not
count as entries. This structural check makes no video or prose-review claim.
"""

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlsplit

from verify_video_course_v3 import canonical, discover_inventory, local, normalized, require


ROOT = Path(__file__).resolve().parents[1]
GUIDE = "docs/repository-walkthrough.md"
ANCHOR = re.compile(r'<a\s+(?:id|name)=["\'](file-[^"\']+)["\'][^>]*>')
LINK = re.compile(r'(?<!!)\[[^\]\n]+\]\((?:<([^>\n]+)>|([^\s)\n]+))(?:\s+[^)]*)?\)')


def visible_lines(text):
    """Ignore commented or fenced examples that are not rendered file entries."""
    fence = None
    for number, line in enumerate(re.sub(r"<!--.*?(?:-->|$)", "", text, flags=re.S).splitlines(), 1):
        marker = re.match(r"^\s{0,3}(`{3,}|~{3,})(.*)$", line)
        if marker:
            run, rest = marker.groups()
            if fence is None:
                fence = run
            elif run[0] == fence[0] and len(run) >= len(fence) and not rest.strip():
                fence = None
            continue
        if fence is None and not line.startswith(("    ", "\t")):
            yield number, line


def verify(root=ROOT, *, guide_path=GUIDE):
    root = Path(root).resolve()
    inventory = discover_inventory(root)
    for path in inventory:
        local(root, path)
    guide = local(root, guide_path)
    entries, anchors = {}, set()
    for number, line in visible_lines(guide.read_text(encoding="utf-8")):
        found = ANCHOR.findall(line)
        if not found:
            continue
        require(len(found) == 1, f"Guide line {number} must have one individual file anchor")
        anchor = found[0]
        require(anchor not in anchors, "Duplicate guide anchor: " + anchor)
        anchors.add(anchor)
        cells = re.split(r"(?<!\\)\|", line.strip())
        require(line.lstrip().startswith("|") and len(cells) >= 4 and ANCHOR.search(cells[1]),
                f"Guide file entry at line {number} must use a table row with a description")
        links = LINK.findall(cells[1])
        require(len(links) == 1, f"Guide entry {anchor} must have exactly one file link")
        target = urlsplit(links[0][0] or links[0][1])
        require(not target.scheme and not target.netloc and bool(target.path) and not target.query,
                f"Guide entry {anchor} needs a local repository file link")
        path = (guide.parent / unquote(target.path)).resolve()
        require(path.is_relative_to(root) and path.is_file(),
                f"Guide entry {anchor} has a missing or unsafe file link")
        relative = path.relative_to(root).as_posix()
        require(relative not in entries, "Duplicate guide file entry: " + relative)
        description = normalized(re.sub(r"<[^>]+>", "", cells[2]))
        require(bool(re.search(r"\w", description)), f"Missing guide description for {relative}")
        entries[relative] = anchor
    missing, extra = sorted(set(inventory) - set(entries)), sorted(set(entries) - set(inventory))
    require(not missing and not extra,
            "Current guide inventory mismatch: " + json.dumps({"missing": missing, "extra": extra}))
    return {"status": "passed", "level": "repository-guide", "guide": guide_path,
            "inventory_files": len(inventory), "guide_entries": len(entries),
            "inventory_sha256": hashlib.sha256(canonical(inventory)).hexdigest(),
            "inventory_scope": "Current tracked and nonignored repository files",
            "video_coverage": "not checked",
            "limit": "Individual links and nonempty descriptions are checked; prose accuracy and human content review are not established."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--guide", default=GUIDE, help="Repository-relative Markdown guide path")
    args = parser.parse_args()
    try:
        result = verify(args.root, guide_path=args.guide)
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
