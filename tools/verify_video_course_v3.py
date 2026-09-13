"""Verify v3 coverage and public readiness using only the Python standard library.

This checks evidence bindings, not the truth of a claimed human review or the
perceptual quality of a video. Media decoding/browser work is performed by the
named external checks and retained as hashed, source-bound public receipts.
Use --content before media exists; its success never means publication ready.
schema_requirements() describes required fields without manufacturing evidence.
"""

import argparse
import hashlib
import html
import json
import math
import re
import subprocess
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
SOURCE = "docs/customer/video-course-v3-source.json"
MANIFEST = "docs/customer/demo/video/v3/media-manifest.json"
COVERAGE = "docs/customer/video-course-v3-coverage.json"
CSV = "docs/customer/evidence/uploaded-csv-profile.json"
NATIVE = "docs/customer/evidence/native-data-validation.json"
RESULTS = "docs/customer/evidence/results.json"
PORTABILITY = "docs/portability-evidence.json"
CLUSTERS = ("orientation", "paper", "cic-csv", "unsw-csv", "features", "learning",
            "code", "results", "demo", "setup", "repository", "hardware")
PAPER_SECTIONS = ("abstract", "I", "II", "III", "IV", "V", "VI", "VII", *(
    "VIII-" + letter for letter in "ABCDEFGHIJ"), "IX")
REQUIRED_CHECKS = ("decode", "browser", "captions", "claims", "rendered_samples")
VISIBLE_FIELDS = ("title", "bullets", "rows", "columns", "code", "note")
# Bind scientific identities to authoritative files/selectors, rather than letting
# a coverage author silently substitute a different seed, population or quantity.
CLAIMS = {
    "cic_csv_rows": (CSV, "/files/0/rows", "rows", "rows"),
    "unsw_csv_rows": (CSV, "/files/1/rows", "rows", "rows"),
    "native_train_flows": (NATIVE, "/splits/train/rows", "flows", "flows"),
    "native_validation_flows": (NATIVE, "/splits/valid/rows", "flows", "flows"),
    "native_test_flows": (NATIVE, "/splits/test/rows", "flows", "flows"),
    "classifier_tokens": (PORTABILITY, "/complete_classifier/tokens", "tokens", "tokens"),
    "classifier_parameters": (PORTABILITY, "/complete_classifier/parameter_count", "parameters", "parameters"),
    "seed0_accuracy": (RESULTS, "/seeds/0/metrics/accuracy", "ratio", "percent"),
    "seed1_accuracy": (RESULTS, "/seeds/1/metrics/accuracy", "ratio", "percent"),
    "seed2_accuracy": (RESULTS, "/seeds/2/metrics/accuracy", "ratio", "percent"),
    "mean_accuracy": (RESULTS, "/aggregate/accuracy/mean", "ratio", "percent"),
    "accuracy_sample_sd": (RESULTS, "/aggregate/accuracy/sample_standard_deviation", "ratio", "percentage_points"),
    "paper_accuracy": (RESULTS, "/paper_ciciot2022_table_iv/accuracy", "ratio", "percent"),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def read(path):
    def pairs(items):
        value = {}
        for key, item in items:
            require(key not in value, f"Duplicate JSON key: {key}")
            value[key] = item
        return value
    def reject(value):
        raise ValueError(f"Nonfinite JSON value: {value}")
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs, parse_constant=reject)


def relative_path(value):
    require(isinstance(value, str) and value and "\\" not in value and "\x00" not in value,
            "Expected a repository-relative POSIX path")
    path = PurePosixPath(value)
    require(not path.is_absolute() and ".." not in path.parts and str(path) == value,
            f"Unsafe or noncanonical path: {value}")
    return value


def local(root, value):
    path = (root / relative_path(value)).resolve()
    require(path.is_relative_to(root.resolve()) and path.is_file(), f"Missing or unsafe artifact: {value}")
    return path


def hash_value(value, label):
    require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value), f"Invalid hash: {label}")
    return value


def artifact(root, record, label="artifact"):
    require(isinstance(record, dict), f"Missing {label} artifact record")
    path = local(root, record.get("path"))
    require(digest(path) == hash_value(record.get("sha256"), label), f"Stale {label} hash: {record['path']}")
    return path


def indexed(records, key, label):
    require(isinstance(records, list), f"Expected {label} list")
    result = {}
    for record in records:
        require(isinstance(record, dict) and isinstance(record.get(key), str) and record[key], f"Malformed {label} entry")
        require(record[key] not in result, f"Duplicate {label}: {record[key]}")
        result[record[key]] = record
    return result


def exact_ids(values, expected, label):
    require(isinstance(values, list) and all(isinstance(v, str) for v in values), f"Malformed {label}")
    require(len(values) == len(set(values)) and set(values) == set(expected), f"Incomplete or duplicate {label}")


def subset_ids(values, scenes, label):
    require(isinstance(values, list) and values and all(isinstance(v, str) for v in values), f"Missing {label} scene IDs")
    require(len(values) == len(set(values)) and set(values).issubset(scenes), f"Invalid {label} scene IDs")


def normalized(value):
    return " ".join(html.unescape(value).split())


def substantive(value, label):
    require(isinstance(value, str) and len(value.strip()) >= 40 and len(value.split()) >= 7,
            f"Missing substantive {label} text")


def pointer(value, selector):
    require(isinstance(selector, str) and (selector == "" or selector.startswith("/")), "Invalid JSON pointer")
    if selector == "":
        return value
    for token in selector[1:].split("/"):
        require(not re.search(r"~(?![01])", token), "Invalid JSON pointer escape")
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(value, list):
            require(re.fullmatch(r"0|[1-9][0-9]*", token), "Invalid JSON array pointer")
            value = value[int(token)]
        else:
            value = value[token]
    return value


def convert_quantity(value, source_unit, unit, decimals):
    require(type(decimals) is int and 0 <= decimals <= 6, "Invalid claim rounding precision")
    require(source_unit in {"ratio", "percent", "percentage_points", "rows", "flows", "tokens", "parameters", "seconds"},
            f"Unknown source unit: {source_unit}")
    require(source_unit == unit or (source_unit == "ratio" and unit in {"percent", "percentage_points"}),
            f"Incompatible units: {source_unit} to {unit}")
    require(not isinstance(value, bool) and isinstance(value, (str, int, float, Decimal)), "Claim value is not numeric")
    try:
        number = Decimal(str(value))
        require(number.is_finite(), "Nonfinite claim value")
        if source_unit != unit:
            number *= 100
        return format(number.quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_UP), f".{decimals}f")
    except InvalidOperation as exc:
        raise ValueError("Invalid numeric claim") from exc


def resolve_source(root, source):
    """Resolve the existing public course fact tokens without importing renderers."""
    if "fact_bindings_sha256" not in source:
        require("{{" not in json.dumps(source), "Unbound source fact token")
        return source
    facts = read(local(root, "docs/customer/course-source.json"))["facts"]
    require(hashlib.sha256(canonical(facts)).hexdigest() == source["fact_bindings_sha256"], "Stale source fact bindings")
    values = {}
    for name, fact in facts.items():
        actual = pointer(read(local(root, fact["file"])), fact["pointer"])
        require(actual == fact["expected"], f"Changed source fact: {name}")
        fmt = fact["format"]
        if fmt == "percent":
            values[name] = f"{actual * 100:.2f}%"
        elif fmt == "points":
            values[name] = f"{actual * 100:.2f}"
        elif fmt == "integer":
            values[name] = f"{actual:,}"
        elif fmt == "text":
            values[name] = str(actual)
        else:
            raise ValueError(f"Unknown source fact format: {fmt}")
    def visit(value):
        if isinstance(value, str):
            return re.sub(r"\{\{([a-z0-9_]+)\}\}", lambda m: values[m[1]], value)
        if isinstance(value, dict):
            return {k: visit(v) for k, v in value.items()}
        if isinstance(value, list):
            return [visit(v) for v in value]
        return value
    return visit(source)


def section(text, anchor):
    require(isinstance(anchor, str) and anchor, "Missing companion anchor")
    starts = []
    for match in re.finditer(r"^(#{1,6})\s+(.+)$|<a\s+(?:id|name)=[\"']([^\"']+)[\"'][^>]*>", text, re.M):
        name = match[3] or re.sub(r"[^\w\- ]", "", match[2].strip().lower()).replace(" ", "-")
        starts.append((match.start(), name, match.end(), bool(match[3])))
    matches = [i for i, (_, name, _, _) in enumerate(starts) if name == anchor]
    require(len(matches) == 1, f"Missing or ambiguous companion anchor: {anchor}")
    i = matches[0]
    end_index = i + 1
    if starts[i][3] and end_index < len(starts) and not starts[end_index][3]:
        between = re.sub(r"<[^>]+>", "", text[starts[i][2]:starts[end_index][0]])
        if not between.strip():
            end_index += 1  # An explicit anchor belongs to the following heading.
    return text[starts[i][0]:starts[end_index][0] if end_index < len(starts) else len(text)]


def companion_link(root, guide, anchor, path):
    body = section(guide.read_text(encoding="utf-8"), anchor)
    target = local(root, path)
    for link in re.findall(r"\]\((?:<([^>]+)>|([^\s)]+))(?:\s+[^)]*)?\)", body):
        value = unquote(link[0] or link[1]).split("#", 1)[0]
        parsed = urlsplit(value)
        if parsed.scheme:
            continue
        if (guide.parent / value).resolve() == target:
            return
    raise ValueError(f"Companion anchor {anchor} lacks a Markdown link entry for {path}")


def discover_inventory(root):
    result = subprocess.run(["git", "-C", str(root), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                            check=True, capture_output=True)
    paths = result.stdout.decode("utf-8").split("\x00")
    return sorted(set(p for p in paths if p))


def check_inventory(root, coverage, expected, ignored_paths=None):
    records = indexed(coverage.get("inventory"), "path", "inventory")
    require(set(records) == set(expected), "Repository inventory is incomplete or contains extra paths")
    require(coverage.get("inventory_sha256") == hashlib.sha256(canonical(sorted(expected))).hexdigest(), "Stale inventory snapshot hash")
    guide = artifact(root, coverage.get("companion"), "companion")
    for path, entry in records.items():
        local(root, path)
        companion_link(root, guide, entry.get("companion_anchor"), path)
    exclusions = coverage.get("exclusions")
    require(isinstance(exclusions, list), "Missing justified exclusions list")
    for entry in exclusions:
        require(isinstance(entry, dict), "Malformed exclusion")
        substantive(entry.get("reason"), "exclusion reason")
        path = relative_path(entry.get("path"))
        require(path not in records and not any(p.startswith(path + "/") for p in records), f"An exclusion hides inventoried files: {path}")
        require(entry.get("kind") in {"ignored_cache", "external_input", "generated_duplicate", "ignored"}, "Unknown exclusion kind")
        if ignored_paths is None:
            result = subprocess.run(["git", "-C", str(root), "check-ignore", "--quiet", "--", path], capture_output=True)
            ignored = result.returncode == 0
        else:
            ignored = path in ignored_paths
        require(ignored, f"Unjustified exclusion is not ignored by Git: {path}")
        require((root / path).exists(), f"Invented exclusion path does not exist: {path}")
    return records


def review(record, source_hash, label):
    require(isinstance(record, dict) and record.get("status") == "passed", f"Missing passed {label} review")
    require(record.get("source_sha256") == source_hash, f"Stale {label} review source hash")
    require(record.get("reviewer") == "Codex", f"Unexpected {label} reviewer")
    substantive(record.get("method"), label + " review method")


def strings(value):
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [s for v in value for s in strings(v)]
    if isinstance(value, dict):
        return [s for v in value.values() for s in strings(v)]
    return []


def check_claims(root, coverage, source, scenes):
    records = indexed(coverage.get("claims"), "id", "claim")
    bindings = indexed(source.get("claims"), "id", "source claim")
    require(set(records) == set(bindings) and set(CLAIMS).issubset(records), "Missing or unbound required claim")
    for name, claim in records.items():
        evidence_path = artifact(root, claim.get("evidence"), f"claim {name} evidence")
        if name in CLAIMS:
            file, selector, source_unit, unit = CLAIMS[name]
            require((claim["evidence"]["path"], claim.get("pointer")) == (file, selector), f"claim {name} evidence pointer is misattributed")
            require((claim.get("source_unit"), claim.get("unit")) == (source_unit, unit), f"Wrong claim {name} units")
        evidence = read(evidence_path)
        if name in {"seed0_accuracy", "seed1_accuracy", "seed2_accuracy"}:
            index = int(name[4])
            require(evidence["seeds"][index].get("seed") == index, f"Claim {name} subject has the wrong seed identity")
        if name in {"cic_csv_rows", "unsw_csv_rows"}:
            index, filename = (0, "CICIDS2017.csv") if name == "cic_csv_rows" else (1, "UNSW.csv")
            require(evidence["files"][index].get("file") == filename, f"Claim {name} subject has the wrong CSV identity")
        actual = pointer(evidence, claim.get("pointer"))
        expected = convert_quantity(actual, claim.get("source_unit"), claim.get("unit"), claim.get("decimals"))
        require(isinstance(claim.get("expected"), str) and claim["expected"] == expected, f"Incorrect expected rounded claim: {name}")
        binding = bindings[name]
        require(binding.get("scene_id") in scenes, f"Unknown claim scene: {name}")
        scene = scenes[binding["scene_id"]]
        visible = normalized(" ".join(strings({k: scene[k] for k in VISIBLE_FIELDS if k in scene})))
        spoken = normalized(scene.get("narration", ""))
        for field, text in [("display_phrase", visible), ("spoken_phrase", spoken)]:
            phrase = binding.get(field)
            require(isinstance(phrase, str) and len(phrase.strip()) >= 3 and normalized(phrase) in text,
                    f"Missing exact {field} for claim {name} in its designated scene")
        numbers = re.findall(r"(?<![\w.])-?\d[\d,]*(?:\.\d+)?(?![\w.])", binding["display_phrase"])
        require(any(Decimal(n.replace(",", "")) == Decimal(expected) for n in numbers), f"Displayed claim number differs: {name}")
        aliases = {"percent": ("%", "percent"), "percentage_points": ("percentage points", " pp", "points"),
                   "rows": ("rows", "packets"), "flows": ("flows",), "tokens": ("tokens",),
                   "parameters": ("parameters",), "ratio": ("ratio",), "seconds": ("seconds", " sec")}
        require(any(unit in visible.lower() for unit in aliases[claim["unit"]]), f"Missing displayed claim unit: {name}")
    return bindings


def finite(value, label):
    require(type(value) in (int, float) and math.isfinite(value), f"Invalid {label}")
    return value


def check_caption_text(cues, timed_scenes, source_scenes, bindings):
    """Bind split cues to a scene and distinguish declared practice text."""
    timeline = {s["id"]: s for s in timed_scenes}
    texts = {s: [] for s in source_scenes}
    for cue in cues:
        owners = [s for s, timed in timeline.items()
                  if cue["start"] >= timed["start"] - .002 and cue["end"] <= timed["end"] + .002]
        require(len(owners) == 1, "Caption crosses scene boundaries or has no owner")
        owner = owners[0]
        require(cue.get("scene", owner) == owner, "Caption scene attribution mismatch")
        texts[owner].append(cue["text"])
    for scene_id, scene in source_scenes.items():
        actual = normalized(" ".join(texts[scene_id]))
        if scene.get("kind") == "pause":
            expected = f"[Practice pause: {scene['seconds']} seconds] " + " ".join(scene.get("bullets", []))
            require(not actual or actual == normalized(expected), f"Undeclared practice caption: {scene_id}")
        else:
            require(actual == normalized(scene.get("narration", "")), f"Caption narration completeness differs: {scene_id}")
    for name, binding in bindings.items():
        require(normalized(binding["spoken_phrase"]) in normalized(" ".join(texts[binding["scene_id"]])),
                f"Caption claim is missing or misattributed: {name}")


def check_captions(root, manifest, media_directory, source_scenes, bindings):
    cues = manifest.get("caption_cues")
    require(isinstance(cues, list) and cues, "Missing caption cues")
    previous = 0
    for cue in cues:
        start, end = finite(cue.get("start"), "caption start"), finite(cue.get("end"), "caption end")
        require(0 <= start < end <= manifest["scheduled_seconds"] and start >= previous - .002, "Invalid caption timing or overlap")
        require(isinstance(cue.get("text"), str) and cue["text"].strip(), "Empty caption text")
        previous = end
    text = local(root, (media_directory / "captions.vtt").as_posix()).read_text(encoding="utf-8")
    require(text.startswith("WEBVTT\n"), "Invalid caption VTT header")
    parsed = []
    def seconds(value):
        h, m, s = value.split(":")
        return int(h) * 3600 + int(m) * 60 + float(s)
    for block in text.strip().split("\n\n")[1:]:
        lines = block.splitlines()
        require(lines and re.fullmatch(r"\d{2,}:[0-5]\d:[0-5]\d\.\d{3} --> \d{2,}:[0-5]\d:[0-5]\d\.\d{3}", lines[0]), "Invalid caption timestamp syntax")
        a, b = map(seconds, lines[0].split(" --> "))
        parsed.append({"start": a, "end": b, "text": html.unescape(" ".join(lines[1:]))})
    require(len(parsed) == len(cues), "Caption cue count mismatch")
    for actual, expected in zip(parsed, cues):
        require(all(abs(actual[k] - expected[k]) <= .002 for k in ("start", "end")) and
                normalized(actual["text"]) == normalized(expected["text"]), "Caption file content/timing mismatch")
    check_caption_text(cues, manifest["scenes"], source_scenes, bindings)


def check_media(root, coverage, manifest_path, source, source_hash, scenes, chapters, bindings,
                production_cache, content_only=False):
    manifest = read(manifest_path)
    manifest_hash = digest(manifest_path)
    require(manifest.get("source_sha256") == source_hash, "Media manifest source hash is stale")
    require(manifest.get("release_tag") == "course-video-v3", "Media is not the v3 version")
    duration = finite(manifest.get("scheduled_seconds"), "media duration")
    require(duration == source.get("target_seconds") and 3480 <= duration <= 3900, "Media duration does not satisfy the v3 source-driven range")
    directory = manifest_path.parent.relative_to(root)
    public = manifest.get("artifacts")
    require(isinstance(public, dict), "Missing public media artifacts")
    required = {manifest.get("media_name"), "captions.vtt", "narration-manifest.json", "motion-manifest.json", "companion-manifest.json"}
    require(None not in required and required.issubset(public), "Missing required public media artifact")
    for name, identity in public.items():
        relative_path(name)
        path = local(root, (directory / name).as_posix())
        require(path != manifest_path and path != root / COVERAGE, "Self-referential media/coverage artifact hash")
        require(digest(path) == identity.get("sha256") and path.stat().st_size == identity.get("bytes"), f"Stale public media artifact: {name}")
    timed = indexed(manifest.get("scenes"), "id", "media scene")
    require(list(timed) == list(scenes), "Media scene order or membership differs from source")
    timed_chapters = indexed(manifest.get("chapters"), "id", "media chapter")
    require(list(timed_chapters) == list(chapters), "Media chapter order differs from source")
    cursor, pauses, measured = 0, 0, {}
    for chapter_id, chapter in chapters.items():
        start, spoken = cursor, 0
        for original in chapter["scenes"]:
            entry = timed[original["id"]]
            require(entry.get("chapter_id") == chapter_id and entry.get("kind") == original.get("kind"), "Media scene chapter/kind differs from source")
            for field in ("narration", *VISIBLE_FIELDS):
                if field in original:
                    require(entry.get(field) == original[field], f"Media scene source content differs: {original['id']}")
            a, b = finite(entry.get("start"), "scene start"), finite(entry.get("end"), "scene end")
            require(a == cursor and b > a, "Non-contiguous media scene timing")
            if original.get("kind") == "pause":
                require(not original.get("narration") and b - a == original.get("seconds"), "Invalid declared practice pause")
                pauses += b - a
            else:
                require(bool(original.get("narration", "").strip()), "Missing spoken scene narration")
                spoken += b - a
            cursor = b
        minimum = chapter.get("min_spoken_seconds", 240 if chapter_id in {"paper", "features"} else 180)
        require(finite(minimum, "minimum spoken seconds") >= (240 if chapter_id in {"paper", "features"} else 180), "Spoken duration minimum cannot be weakened")
        require(spoken >= minimum, f"Insufficient measured spoken duration: {chapter_id}")
        require(timed_chapters[chapter_id].get("start") == start and timed_chapters[chapter_id].get("end") == cursor,
                f"Media chapter timing mismatch: {chapter_id}")
        measured[chapter_id] = spoken
    require(cursor == duration and pauses <= source.get("max_practice_seconds", 240), "Invalid total media/practice duration")
    result = {"media_checked": True, "timeline_seconds": duration, "spoken_seconds_by_chapter": measured,
              "practice_seconds": pauses, "manifest_sha256": manifest_hash}
    if content_only:
        result["media_scope"] = "Artifact identities and chapter/scene timing; technical readiness reviews not checked"
        return result
    # Captions are checked before review receipts so malformed actual media metadata
    # cannot be hidden behind an unrelated stale review error.
    check_captions(root, manifest, directory, scenes, bindings)
    narration = read(local(root, (directory / "narration-manifest.json").as_posix()))
    require(narration.get("source_sha256") == source_hash, "Stale narration source hash")
    audio_records = indexed(narration.get("scenes"), "id", "narration audio")
    require(set(audio_records) == {s for s, v in scenes.items() if v.get("kind") != "pause"}, "Incomplete narration audio records")
    for scene_id, record in audio_records.items():
        entry = timed[scene_id]
        raw, final = entry.get("audio", {}), entry.get("final_audio", {})
        for key in ("wav_sha256", "samples", "sample_rate"):
            require(record.get(key) == raw.get(key), f"Raw audio binding mismatch: {scene_id}")
        hash_value(raw.get("wav_sha256"), "raw audio")
        require(all(type(raw.get(k)) is int and raw[k] > 0 for k in ("samples", "sample_rate")), "Invalid raw audio sample counts")
        require(final == record.get("final_audio"), f"Final audio binding mismatch: {scene_id}")
        hash_value(final.get("sha256"), "final audio")
        require(all(type(final.get(k)) is int and final[k] > 0 for k in ("samples", "sample_rate")), "Invalid final audio sample counts")
        require(abs(final["samples"] / final["sample_rate"] - (entry["end"] - entry["start"])) <= 1 / final["sample_rate"], "Final audio duration mismatch")
        substantive(final.get("scope"), "final audio scope")
        if production_cache:
            require("path" in final and digest(local(root, final["path"])) == final["sha256"], "Missing or stale final audio production cache")
    visual_inventory = read(local(root, (directory / "companion-manifest.json").as_posix()))
    motion = read(local(root, (directory / "motion-manifest.json").as_posix()))
    require(visual_inventory.get("source_sha256") == source_hash and motion.get("source_sha256") == source_hash,
            "Stale visual/motion source hash")
    frames = visual_inventory.get("frames")
    require(isinstance(frames, list) and frames, "Missing final visual frame inventory")
    frame_map = {scene_id: [] for scene_id in scenes}
    seen_frames = set()
    for frame in frames:
        require(isinstance(frame, dict) and frame.get("scene_id") in scenes, "Unknown visual frame scene")
        require(frame.get("path") not in seen_frames, "Duplicate visual frame path")
        seen_frames.add(frame["path"])
        artifact(root, frame, "visual frame")
        frame_map[frame["scene_id"]].append({"path": frame["path"], "sha256": frame["sha256"]})
    visuals = coverage["reviews"].get("visuals")
    review(visuals, source_hash, "visual")
    require(visuals.get("manifest_sha256") == manifest_hash, "Stale visual review manifest hash")
    items = indexed(visuals.get("items"), "scene_id", "visual review")
    require(set(items) == set(scenes), "Incomplete visual review scene coverage")
    for scene_id, item in items.items():
        require(item.get("status") == "passed" and frame_map[scene_id], "Missing passed visual review")
        require(item.get("frames") == frame_map[scene_id] == timed[scene_id].get("visuals"), f"Final visual review/frame hash mismatch: {scene_id}")
    required_artifacts = {(directory / manifest["media_name"]).as_posix(), (directory / "captions.vtt").as_posix()}
    checks = coverage.get("checks", {})
    for kind in REQUIRED_CHECKS:
        require(kind in checks, f"Missing required {kind} check")
        record = read(artifact(root, checks[kind], kind + " check"))
        require(record.get("status") == "passed" and record.get("source_sha256") == source_hash and record.get("manifest_sha256") == manifest_hash,
                f"Missing passed or stale {kind} check binding")
        require(record.get("known_material_defects") == [], f"Known material defects in {kind} check")
        substantive(record.get("method"), kind + " check method")
        bound = indexed(record.get("artifacts"), "path", kind + " artifact")
        require(required_artifacts.issubset(bound), f"{kind} check does not bind encoded media and captions")
        for identity in bound.values():
            artifact(root, identity, kind + " checked artifact")
        if kind == "decode":
            seconds = finite(record.get("measured_seconds"), "decode measured duration")
            require(3480 <= seconds <= 3900 and abs(seconds - duration) <= 1,
                    "Actual decode measured duration differs from the source/media timeline")
            result["measured_seconds"] = seconds
        if kind == "rendered_samples":
            require(set(record.get("categories", [])) >= {"technical_terms", "identifiers", "numbers", "chapter_transitions"}, "Incomplete rendered sample review categories")
    result["media_scope"] = "Public artifacts, captions, audio/frame bindings and required technical review receipts"
    return result


def verify_coverage(root=ROOT, *, coverage_path=COVERAGE, source_path=SOURCE, manifest_path=MANIFEST,
                    inventory=None, ignored_paths=None, content_only=False, production_cache=False):
    """Validate real files; explicit inventory injection keeps fixtures independent of Git.

    Raises ValueError on the first invalid boundary. The coverage record itself is
    never hashed into itself or into its media manifest. No output files are written.
    """
    root = Path(root).resolve()
    coverage = read(local(root, coverage_path))
    require(isinstance(coverage, dict) and coverage.get("schema_version") == 3, "Coverage schema/version must be 3")
    require(coverage.get("known_material_defects") == [], "Known or undeclared material defects block readiness")
    source_file = artifact(root, coverage.get("source"), "source")
    require(source_file == local(root, source_path), "Coverage refers to a different source")
    source_hash = digest(source_file)
    source = resolve_source(root, read(source_file))
    require(source.get("release_tag") == "course-video-v3", "Expected v3 source version")
    chapters = indexed(source.get("chapters"), "id", "source chapter")
    require(set(chapters) == set(CLUSTERS), "Missing one of the 12 teaching clusters in source")
    scenes = indexed([s for c in chapters.values() for s in c["scenes"]], "id", "source scene")
    expected = discover_inventory(root) if inventory is None else list(inventory)
    inventory_records = check_inventory(root, coverage, expected, ignored_paths)
    for entry in inventory_records.values():
        require(entry.get("scene_id") in scenes, "Inventory references unknown scene")
    clusters = indexed(coverage.get("clusters"), "id", "teaching cluster")
    require(set(clusters) == set(CLUSTERS), "Missing required teaching cluster")
    for name, cluster in clusters.items():
        exact_ids(cluster.get("scene_ids"), [s["id"] for s in chapters[name]["scenes"]], "cluster scene coverage")
        text = normalized(" ".join(scenes[s].get("narration", "") for s in cluster["scene_ids"]))
        for field in ("purpose", "relationship", "example"):
            substantive(cluster.get(field), f"cluster {name} {field}")
            require(normalized(cluster[field]) in text, f"Cluster {name} {field} is not explained in its narration")
        require(len({cluster[k] for k in ("purpose", "relationship", "example")}) == 3, "Cluster purpose, relationship and example cannot be identical")
        review(cluster.get("review"), source_hash, "cluster " + name)
    paper = coverage.get("paper", {})
    require(isinstance(paper, dict), "Malformed paper coverage")
    require(paper.get("version") == "2601.21792v1", "Wrong paper version")
    guide = artifact(root, paper.get("guide"), "paper guide")
    sections = indexed(paper.get("sections"), "id", "paper section")
    require(set(sections) == set(PAPER_SECTIONS), "Incomplete major paper section coverage")
    for name, record in sections.items():
        subset_ids(record.get("scene_ids"), scenes, "paper " + name)
        body = section(guide.read_text(encoding="utf-8"), record.get("companion_anchor"))
        substantive(record.get("explanation"), "paper explanation")
        require(record.get("depth") in {"video", "companion"}, "Missing paper depth boundary")
        text = body if record["depth"] == "companion" else " ".join(scenes[s].get("narration", "") for s in record["scene_ids"])
        require(normalized(record["explanation"]) in normalized(text), f"Paper section {name} explanation is absent")
    profiles = indexed(coverage.get("csv_profiles"), "file", "CSV profile")
    require(set(profiles) == {"CICIDS2017.csv", "UNSW.csv"}, "Both CSV profiles are required")
    for name, record in profiles.items():
        profile_path = artifact(root, record.get("profile"), "CSV profile")
        require(record["profile"]["path"] == CSV, "CSV profile must use published full metadata evidence")
        actual = indexed(read(profile_path)["files"], "file", "CSV evidence")[name]
        require(record.get("source_sha256") == actual["sha256"], "CSV source identity mismatch")
        subset_ids(record.get("scene_ids"), scenes, "CSV " + name)
        substantive(record.get("explanation"), "CSV explanation")
        text = " ".join(scenes[s].get("narration", "") for s in record["scene_ids"])
        require(normalized(record["explanation"]) in normalized(text), "CSV explanation is absent from its narration")
    bindings = check_claims(root, coverage, source, scenes)
    reviews = coverage.get("reviews", {})
    require(isinstance(reviews, dict), "Malformed review container")
    content = reviews.get("content")
    review(content, source_hash, "content")
    exact_ids(content.get("scene_ids"), scenes, "content review scene coverage")
    require(set(content.get("scope", [])) >= {"script", "worked_answers"}, "Content review must include script and worked answers")
    for key in ("human_full_watch", "all_caption_acceptance"):
        record = reviews.get(key, {})
        require(record.get("status") == "pending" and isinstance(record.get("reason"), str) and record["reason"].strip(),
                f"The {key} human review must remain explicitly pending under the v3 standard")
    result = {"status": "passed", "level": "content" if content_only else "readiness",
              "source_sha256": source_hash, "inventory_files": len(expected), "scenes": len(scenes),
              "claims": len(bindings), "media_checked": False, "human_full_watch": "pending",
              "all_caption_acceptance": "pending",
              "limit": "Structural and hash checks verify recorded evidence; they do not independently establish teaching quality or human listening."}
    if coverage.get("media_manifest") is not None:
        path = artifact(root, coverage["media_manifest"], "media manifest")
        require(path == local(root, manifest_path), "Coverage refers to a different media manifest")
        result.update(check_media(root, coverage, path, source, source_hash, scenes, chapters, bindings,
                                 production_cache, content_only))
        require(digest(path) == result["manifest_sha256"], "Media manifest changed during verification")
    else:
        require(content_only, "Full readiness requires final media manifest and completed media reviews")
    require(digest(source_file) == source_hash, "Source changed during verification")
    return result


def schema_requirements():
    """Machine-readable contract inventory; no completed review/sample evidence."""
    return {"schema_version": 3, "source": SOURCE, "media_manifest": MANIFEST,
            "coverage": COVERAGE, "clusters": list(CLUSTERS), "paper_sections": list(PAPER_SECTIONS),
            "claims": {k: {"file": v[0], "pointer": v[1], "source_unit": v[2], "unit": v[3]} for k, v in CLAIMS.items()},
            "checks": list(REQUIRED_CHECKS), "human_review_status": "pending",
            "minimum_spoken_seconds": {c: 240 if c in {"paper", "features"} else 180 for c in CLUSTERS}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--source", default=SOURCE, help="Repository-relative source path")
    parser.add_argument("--manifest", default=MANIFEST, help="Repository-relative media manifest path")
    parser.add_argument("--coverage", default=COVERAGE, help="Repository-relative coverage path")
    parser.add_argument("--content", action="store_true", help="Check content; an absent media record never grants readiness")
    parser.add_argument("--production-cache", action="store_true", help="Also hash final PCM files using optional final_audio.path records")
    parser.add_argument("--schema", action="store_true", help="Print schema requirements, not a passing coverage template")
    args = parser.parse_args()
    try:
        result = schema_requirements() if args.schema else verify_coverage(
            args.root, coverage_path=args.coverage, source_path=args.source, manifest_path=args.manifest,
            content_only=args.content, production_cache=args.production_cache)
    except (ValueError, KeyError, TypeError, IndexError, OSError, subprocess.SubprocessError) as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
