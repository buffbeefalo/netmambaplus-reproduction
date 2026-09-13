"""Build a scheduled narrated course from local speech, evidence and diagrams."""

import argparse
import hashlib
import html
import json
import math
import re
import shutil
import subprocess
import textwrap
import wave
from pathlib import Path, PurePosixPath

from build_course import ROOT, fact_values, read
from narrate_course_video import SOURCE, canonical, digest, load_source
from video_motion import draw_diagram, animation_events

FPS = 10
RATE = 24000
LEGACY_DESTINATION = ROOT / "docs/customer/demo/video"
DESTINATION = LEGACY_DESTINATION / "v3"
MEDIA_NAME = "NetMambaPlus-30-minute-course.mp4"
WEBM_NAME = "NetMambaPlus-30-minute-course.webm"
DEFAULT_TITLE = "NetMamba+ — the 30-minute video course"
DEFAULT_WORK = ROOT / "runs/video-course/v3-neural"


def publication(record):
    """Resolve publication fields, including defaults for the original v2 manifest."""
    result = {"media_name": record.get("media_name", MEDIA_NAME),
              "release_tag": record.get("release_tag", "course-video-v2"),
              "title": record.get("title", DEFAULT_TITLE),
              "production": record.get("production", {})}
    if not isinstance(result["media_name"], str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*\.mp4", result["media_name"]):
        raise ValueError("media_name must be a path-safe MP4 basename")
    if not isinstance(result["release_tag"], str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", result["release_tag"]):
        raise ValueError("release_tag must be path-safe")
    if not isinstance(result["title"], str) or not result["title"].strip():
        raise ValueError("The course needs a publication title")
    if not isinstance(result["production"], dict) or any(
            not isinstance(k, str) or not k.strip() or not isinstance(v, str) or not v.strip()
            for k, v in result["production"].items()):
        raise ValueError("production must map credit labels to nonempty text")
    result["webm_name"] = str(Path(result["media_name"]).with_suffix(".webm"))
    return result


def frame_rate(source):
    fps = source.get("render_fps", FPS)
    if type(fps) is not int or not 1 <= fps <= 60 or RATE % fps:
        raise ValueError("render_fps must be an integer from 1 to 60 that divides the audio sample rate")
    return fps


def chapter_schedule(source):
    target = source["target_seconds"]
    if type(target) is not int or target <= 0 or not source["chapters"]:
        raise ValueError("The video needs a positive integer target and chapters")
    chapters, names, cursor = [], set(), 0
    for chapter in source["chapters"]:
        if (not isinstance(chapter["id"], str) or not re.fullmatch(r"[a-z0-9-]+", chapter["id"])
                or chapter["id"] in names or not isinstance(chapter["title"], str) or not chapter["title"].strip()):
            raise ValueError("Chapters need unique path-safe identifiers and titles")
        if type(chapter["seconds"]) is not int or chapter["seconds"] <= 0:
            raise ValueError("Chapter durations must be positive integer seconds")
        names.add(chapter["id"])
        chapters.append({"id": chapter["id"], "title": chapter["title"],
                         "start": cursor, "end": cursor + chapter["seconds"]})
        cursor += chapter["seconds"]
    if cursor != target:
        raise ValueError("Chapter durations must sum to the declared target_seconds")
    return chapters


def local_reference(relative, root=ROOT):
    if (not isinstance(relative, str) or not relative or "\\" in relative or ":" in relative
            or PurePosixPath(relative).is_absolute() or ".." in PurePosixPath(relative).parts
            or PurePosixPath(relative).as_posix() != relative):
        raise ValueError("References must be repository-relative POSIX paths")
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError(f"Missing or escaping repository reference: {relative}")
    return path


def image_path(scene, root=ROOT):
    path = local_reference(scene["image"], root)
    expected = scene.get("image_sha256", "")
    if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected) or digest(path) != expected:
        raise ValueError(f"Image checksum mismatch: {scene['id']}")
    return path


def motion_clip(scene, root=ROOT):
    clip = scene.get("motion_clip")
    if clip is None:
        return None
    path = local_reference(clip["path"], root)
    if digest(path) != clip["sha256"]:
        raise ValueError("Recorded clip checksum mismatch: " + scene["id"])
    for key in ("start_seconds", "trim_start_seconds", "duration_seconds", "x", "y", "width", "height"):
        value = clip[key]
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            raise ValueError("Invalid recorded clip geometry or timing")
    if (clip["duration_seconds"] <= 0 or clip["width"] <= 0 or clip["height"] <= 0
            or clip["x"] + clip["width"] > 1830 or clip["y"] + clip["height"] > 835
            or clip["x"] < 90 or clip["y"] < 285):
        raise ValueError("Recorded clip exceeds the teaching area")
    if "end" in scene and clip["start_seconds"] + clip["duration_seconds"] > scene["end"] - scene["start"]:
        raise ValueError("Recorded clip extends outside its scene")
    return path


def validate_visual(scene, root=ROOT):
    motion_clip(scene, root)
    kind = scene["kind"]
    if kind == "code" and "code" in scene:
        if not isinstance(scene["code"], str) or not scene["code"].strip():
            raise ValueError("Code scenes need nonempty code text")
    elif kind == "table":
        columns, rows = scene.get("columns"), scene.get("rows")
        if (not isinstance(columns, list) or not columns or any(not isinstance(c, str) or not c.strip() for c in columns)
                or not isinstance(rows, list) or not 1 <= len(rows) <= 6
                or any(not isinstance(row, list) or len(row) != len(columns)
                       or any(not isinstance(cell, str) for cell in row) for row in rows)):
            raise ValueError("Tables need text columns and one to six complete text rows")
        widths = scene.get("widths", [1] * len(columns))
        if (not isinstance(widths, list) or len(widths) != len(columns)
                or any(type(w) not in (int, float) or not math.isfinite(w) or w <= 0 for w in widths)
                or not math.isfinite(sum(widths))):
            raise ValueError("Table widths must be positive finite weights, one per column")
    elif kind == "image":
        image_path(scene, root)


def reference_paths(source, course, root=ROOT):
    references = {key: value["path"] for key, value in course["references"].items()}
    references.update(contract="docs/harness-reference.md", support="docs/support-matrix.md")
    for key, value in source.get("extra_references", {}).items():
        if key in references and references[key] != value:
            raise ValueError(f"Extra reference remaps an existing evidence key: {key}")
        local_reference(value, root)
        references[key] = value
    return references


def validate(source, root=ROOT):
    chapter_schedule(source)
    publication(source)
    frame_rate(source)
    maximum = source.get("max_practice_seconds", 180)
    if type(maximum) is not int or maximum < 0:
        raise ValueError("max_practice_seconds must be a nonnegative integer")
    extras = source.get("extra_references", {})
    if not isinstance(extras, dict) or any(not isinstance(k, str) or not re.fullmatch(r"[a-z0-9-]+", k) for k in extras):
        raise ValueError("extra_references must map path-safe keys to local files")
    for relative in extras.values():
        local_reference(relative, root)
    names = set()
    practice = 0
    for chapter in source["chapters"]:
        pauses = 0
        for scene in chapter["scenes"]:
            if scene["id"] in names or not re.fullmatch(r"[a-z0-9-]+", scene["id"]):
                raise ValueError("Scene identifiers must be unique and path-safe")
            names.add(scene["id"])
            if not scene["bullets"] or not scene["references"]:
                raise ValueError("Every scene needs visible teaching and evidence references")
            validate_visual(scene, root)
            if scene["kind"] == "pause":
                if scene["narration"] or type(scene.get("seconds")) is not int or scene["seconds"] <= 0:
                    raise ValueError("Practice pauses need an explicit positive duration and no speech")
                pauses += scene["seconds"]
            elif not scene["narration"].strip():
                raise ValueError("Teaching scenes cannot be unexplained silent holds")
        if pauses >= chapter["seconds"] or not pauses:
            raise ValueError("Each chapter needs both narration and intentional practice")
        practice += pauses
    if practice > maximum:
        raise ValueError("Declared practice exceeds max_practice_seconds")


def allocate_frames(weights, frames):
    if not weights or any(not math.isfinite(w) or w <= 0 for w in weights):
        raise ValueError("Speech durations must be positive and finite")
    ideals = [frames * w / sum(weights) for w in weights]
    result = [int(n) for n in ideals]
    for index in sorted(range(len(weights)), key=lambda i: ideals[i] - result[i], reverse=True)[:frames - sum(result)]:
        result[index] += 1
    if not all(result):
        raise ValueError("Too few video frames for the teaching scenes")
    return result


def timeline(source, narration, source_path=SOURCE):
    validate(source)
    fps = frame_rate(source)
    if narration["source_sha256"] != digest(source_path):
        raise ValueError("Narration is stale; regenerate it from the reviewed source")
    records = {r["id"]: r for r in narration["scenes"]}
    chapters, scenes, cursor = [], [], 0
    for number, chapter in enumerate(source["chapters"], 1):
        start = cursor
        spoken = [s for s in chapter["scenes"] if s["kind"] != "pause"]
        budget = chapter["seconds"] - sum(s.get("seconds", 0) for s in chapter["scenes"] if s["kind"] == "pause")
        weights = [records[s["id"]]["seconds"] for s in spoken]
        allocation = dict(zip((s["id"] for s in spoken), allocate_frames(weights, budget * fps)))
        for original in chapter["scenes"]:
            scene = dict(original)
            frames = scene["seconds"] * fps if scene["kind"] == "pause" else allocation[scene["id"]]
            scene.update(start=cursor / fps, end=(cursor + frames) / fps, frames=frames,
                         chapter=number, chapter_id=chapter["id"], chapter_title=chapter["title"],
                         chapter_count=len(source["chapters"]))
            if scene["kind"] != "pause":
                scene["tempo"] = records[scene["id"]]["seconds"] / (frames / fps)
                if not 0.8 <= scene["tempo"] <= 1.0:
                    raise ValueError(f"Unnatural speech pacing for {scene['id']}: {scene['tempo']:.3f}; revise narration")
                scene["audio"] = records[scene["id"]]
            scenes.append(scene)
            cursor += frames
        chapters.append({"id": chapter["id"], "title": chapter["title"],
                         "start": start / fps, "end": cursor / fps})
    if cursor != source["target_seconds"] * fps:
        raise ValueError("Timeline drift")
    return chapters, scenes


def timecode(seconds, separator="."):
    millis = round(seconds * 1000)
    hours, rest = divmod(millis, 3600000)
    minutes, rest = divmod(rest, 60000)
    secs, ms = divmod(rest, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02}{separator}{ms:03}"


def display_time(seconds):
    stamp = timecode(seconds).split(".", 1)[0]
    return stamp[3:] if seconds < 3600 else stamp


def production_credit(metadata):
    return " · ".join(f"{label.replace('_', ' ').capitalize()}: {value}"
                      for label, value in metadata["production"].items())


def caption_cues(scenes):
    cues = []
    for scene in scenes:
        if scene["kind"] == "pause":
            cues.append({"start": scene["start"], "end": scene["end"], "scene": scene["id"],
                         "text": f"[Practice pause: {scene['seconds']} seconds] " + " ".join(scene["bullets"])})
            continue
        boundaries = {}
        for sentence in scene["audio"]["cues"]:
            chunks = textwrap.wrap(sentence["text"], width=86, break_long_words=False, break_on_hyphens=False)
            weight = sum(len(x) for x in chunks)
            start = scene["start"] + sentence["start"] / scene["tempo"]
            end = min(scene["end"], scene["start"] + sentence["end"] / scene["tempo"])
            cursor = start
            for index, chunk in enumerate(chunks):
                next_time = min(end, cursor + (end - start) * len(chunk) / weight)
                cues.append({"start": cursor, "end": next_time, "scene": scene["id"], "text": chunk})
                if index + 1 < len(chunks):
                    boundaries.setdefault((chunk, chunks[index + 1]), []).append(len(cues) - 1)
                cursor = next_time
        applied = set()
        for anchor in scene.get("caption_boundary_overrides", []):
            matches = boundaries.get((anchor["left_text"], anchor["right_text"]), [])
            if anchor["wav_sha256"] != scene["audio"]["wav_sha256"] or len(matches) != 1:
                raise ValueError(f"Stale or ambiguous caption audio anchor: {scene['id']}")
            index = matches[0]
            boundary = scene["start"] + anchor["raw_seconds"] / scene["tempo"]
            if (index in applied or not math.isfinite(boundary)
                    or not cues[index]["start"] < boundary < cues[index + 1]["end"]):
                raise ValueError(f"Invalid caption audio anchor: {scene['id']}")
            cues[index]["end"] = cues[index + 1]["start"] = boundary
            applied.add(index)
    return cues


def ass_time(seconds):
    cs = round(seconds * 100)
    hours, rest = divmod(cs, 360000)
    mins, rest = divmod(rest, 6000)
    sec, frac = divmod(rest, 100)
    return f"{hours}:{mins:02}:{sec:02}.{frac:02}"


def write_captions(cues, scenes, work, destination, *, animate=False, chapters=None):
    srt, vtt = [], ["WEBVTT", ""]
    ass = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1920", "PlayResY: 1080",
           "WrapStyle: 0", "[V4+ Styles]",
           "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
           "Style: Speech,DejaVu Sans,38,&H00FFFFFF,&H00FFFFFF,&H00221B13,&H00221B13,0,0,0,0,100,100,0,0,3,14,0,2,140,140,45,1",
           "Style: Practice,DejaVu Sans,45,&H005F503B,&H005F503B,&H00F3F6F8,&H00F3F6F8,-1,0,0,0,100,100,0,0,1,0,0,2,100,100,45,1",
           "Style: Motion,DejaVu Sans,20,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1",
           "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    pause_ids = {s["id"] for s in scenes if s["kind"] == "pause"}
    for index, cue in enumerate(cues, 1):
        wrapped = "\n".join(textwrap.wrap(cue["text"], width=48, break_long_words=False, break_on_hyphens=False))
        srt.extend([str(index), f"{timecode(cue['start'], ',')} --> {timecode(cue['end'], ',')}", wrapped, ""])
        vtt.extend([f"{timecode(cue['start'])} --> {timecode(cue['end'])}", html.escape(wrapped), ""])
        if cue["scene"] not in pause_ids:
            text = wrapped.replace("\\", "＼").replace("{", "(").replace("}", ")").replace("\n", "\\N")
            ass.append(f"Dialogue: 0,{ass_time(cue['start'])},{ass_time(cue['end'])},Speech,,0,0,0,,{text}")
    for scene in scenes:
        if scene["kind"] == "pause":
            for second in range(scene["seconds"]):
                remaining = scene["seconds"] - second
                text = f"Practice time  |  {remaining // 60:02}:{remaining % 60:02} remaining"
                ass.append(f"Dialogue: 1,{ass_time(scene['start'] + second)},{ass_time(scene['start'] + second + 1)},Practice,,0,0,0,,{text}")
    (destination / "captions.srt").write_text("\n".join(srt).rstrip() + "\n", encoding="utf-8", newline="\n")
    (destination / "captions.vtt").write_text("\n".join(vtt).rstrip() + "\n", encoding="utf-8", newline="\n")
    motion_lines, motion_records = animation_events(scenes, chapters or [], animate)
    ass.extend(motion_lines)
    (destination / "motion-manifest.json").write_text(json.dumps({"events": motion_records, "enabled": animate, "scope": "Illustrative instructional motion and emphasis; no live inference is depicted."}, indent=2) + "\n", encoding="utf-8", newline="\n")
    (work / "captions.ass").write_text("\n".join(ass) + "\n", encoding="utf-8", newline="\n")


def render_scene(scene, path, facts, demo, root=ROOT):
    from PIL import Image, ImageDraw, ImageFont
    validate_visual(scene, root)
    fonts = Path("/usr/share/fonts/truetype/dejavu")
    bg, ink, muted, teal, blue, coral = "#f8f6ef", "#172c3a", "#465a63", "#126e68", "#d9e9ed", "#b14c36"
    image = Image.new("RGB", (1920, 1080), bg)
    draw = ImageDraw.Draw(image)

    def font(size, bold=False, mono=False):
        return ImageFont.truetype(str(fonts / ("DejaVuSansMono.ttf" if mono else "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf")), size)

    def lines_for(text, width, size, bold=False, mono=False):
        selected = font(size, bold, mono)
        lines = []
        for paragraph in str(text).split("\n"):
            line = ""
            for word in paragraph.split():
                if draw.textlength(word, font=selected) > width:
                    raise ValueError(f"Visual width overflow in {scene['id']}: {word}")
                candidate = (line + " " + word).strip()
                if line and draw.textlength(candidate, font=selected) > width:
                    lines.append(line)
                    line = word
                else:
                    line = candidate
            lines.append(line)
        return lines

    def put(text, x, y, width, size=36, color=ink, bold=False, mono=False, max_bottom=835):
        selected = font(size, bold, mono)
        lines = lines_for(text, width, size, bold, mono)
        height = len(lines) * (size + 12)
        if y + height > max_bottom:
            raise ValueError(f"Visual overflow in {scene['id']}: {text}")
        for line in lines:
            draw.text((x, y), line, font=selected, fill=color)
            y += size + 12
        return y

    draw.rectangle((0, 0, 1920, 15), fill=teal)
    put("NETMAMBA+  /  REPRODUCTION LAB", 90, 54, 980, 25, teal, True)
    chapter_count = scene.get("chapter_count")
    if chapter_count is None:  # Compatibility with stored v2 scene records.
        chapter_count = len(load_source()["chapters"])
    put(f"{scene['chapter']:02} / {chapter_count:02}   ·   {display_time(scene['start'])}", 1400, 54, 430, 25, muted)
    put(scene["title"], 90, 132, 1730, 56, ink, True, max_bottom=285)
    kind, bullets = scene["kind"], scene["bullets"]
    if draw_diagram(scene, draw, put):
        pass
    elif kind == "results":
        for index, key in enumerate(["seed0", "seed1", "seed2", "mean_accuracy"]):
            y = 325 + index * 105
            value = float(facts[key].strip("%"))
            put("Mean" if index == 3 else f"Seed {index}", 95, y + 12, 240, 34, ink, index == 3)
            draw.rounded_rectangle((370, y, 1550, y + 66), radius=10, fill=blue)
            draw.rounded_rectangle((370, y, 370 + 1180 * value / 100, y + 66), radius=10, fill=teal if index == 3 else "#497884")
            put(facts[key], 1610, y + 10, 240, 40, ink, True)
        put("Recorded test accuracy · same 1,041-flow test set · sample SD 4.00 percentage points", 95, 780, 1750, 25, muted)
    elif kind == "matrix":
        record = read(ROOT / "docs/customer/evidence/seed0/replay/predictions.json")
        matrix = record["independent_metrics"]["confusion_matrix"]
        labels = ["Flood", "RTSP Brute Force", "Audio", "Other", "Cameras", "Home Automation"]
        put("Seed 0 · each cell counts labeled test flows", 95, 266, 1700, 30, muted)
        for column in range(6):
            put(str(column), 478 + column * 88, 311, 70, 28, ink, True)
        for row, label in enumerate(labels):
            y = 360 + row * 68
            put(f"{row}  {label}", 95, y + 13, 355, 26, ink)
            for column, count in enumerate(matrix[row]):
                x = 454 + column * 88
                dark = row == column and count >= 100
                draw.rectangle((x, y, x + 85, y + 64), fill=teal if dark else blue)
                put(str(count), x + 13, y + 14, 70, 27, "#ffffff" if dark else ink, True)
        put("Rows: known category · Columns: predicted category (same numbers)", 95, 795, 1720, 25, muted)
        for index, bullet in enumerate(bullets):
            put(bullet, 1070, 350 + index * 135, 735, 32)
    elif kind == "comparison":
        for x, label, value, color in [(90, "Paper Table IV", facts["paper_accuracy"], muted), (990, "Our three-seed mean", facts["mean_accuracy"], teal)]:
            draw.rounded_rectangle((x, 325, x + 830, 690), radius=24, fill="#ffffff", outline=blue, width=3)
            put(label, x + 40, 365, 750, 35, color)
            put(value, x + 40, 445, 750, 100, color, True)
        put("Different runtime and training settings. The cause of the gap remains unresolved.", 95, 752, 1740, 31, coral)
    elif kind in ("prediction-hidden", "prediction-reveal"):
        row = demo["expected"]
        labels = ["Flood", "RTSP Brute Force", "Audio", "Other", "Cameras", "Home Automation"]
        for index, (label, score) in enumerate(zip(labels, row["scores"])):
            y = 330 + index * 70
            put(f"{index}  {label}", 95, y, 470, 28, ink, index == row["prediction"])
            width = max(12, score * 650)
            draw.rounded_rectangle((600, y, 600 + width, y + 43), radius=5, fill=teal if index == row["prediction"] else "#97b7be")
            put(f"{score * 100:.2f}%", 1300, y, 230, 28)
        label = "Known label: reveal next" if kind.endswith("hidden") else "Known label: 3 — Other. Prediction is wrong."
        put(label, 95, 775, 1700, 32, coral, True)
    elif kind == "code" and "code" in scene:
        draw.rounded_rectangle((90, 310, 1280, 820), radius=22, fill=ink)
        selected = font(26, mono=True)
        lines = scene["code"].expandtabs(4).splitlines()
        if len(lines) * 38 > 466 or any(draw.textlength(line, font=selected) > 1102 for line in lines):
            raise ValueError(f"Code visual overflow in {scene['id']}; shorten the excerpt")
        for index, line in enumerate(lines):
            draw.text((134, 332 + index * 38), line, font=selected, fill=bg)
        y = 327
        for bullet in bullets:
            y = put(bullet, 1320, y, 500, 30) + 25
    elif kind == "table":
        weights = scene.get("widths", [1] * len(scene["columns"]))
        widths = [1730 * weight / sum(weights) for weight in weights]
        table = [scene["columns"], *scene["rows"]]
        heights = [max(len(lines_for(cell, width - 36, 26, bold=index == 0)) * 38 + 20
                       for cell, width in zip(row, widths)) for index, row in enumerate(table)]
        if sum(heights) > 440:
            raise ValueError(f"Table visual overflow in {scene['id']}; shorten the cells")
        y = 300
        for index, (row, height) in enumerate(zip(table, heights)):
            x = 90
            for cell, width in zip(row, widths):
                draw.rectangle((x, y, x + width, y + height), fill=teal if index == 0 else "#ffffff", outline=blue, width=2)
                put(cell, x + 18, y + 10, width - 36, 26, "#ffffff" if index == 0 else ink,
                    index == 0, max_bottom=y + height)
                x += width
            y += height
        put(" · ".join(bullets), 95, y + 24, 1720, 28, muted)
    elif kind == "image":
        with Image.open(image_path(scene, root)) as original:
            picture = original.convert("RGBA")
        if scene.get("image_layout") == "wide":
            scale = min(1720 / picture.width, 410 / picture.height)
            picture = picture.resize((round(picture.width * scale), round(picture.height * scale)), Image.Resampling.LANCZOS)
            x, y = 95 + (1720 - picture.width) // 2, 300 + (410 - picture.height) // 2
            image.paste(picture, (x, y), picture)
            put(" · ".join(bullets), 95, 735, 1720, 28)
        else:
            picture.thumbnail((1190, 510), Image.Resampling.LANCZOS)
            x, y = 90 + (1190 - picture.width) // 2, 310 + (510 - picture.height) // 2
            image.paste(picture, (x, y), picture)
            y = 327
            for bullet in bullets:
                y = put(bullet, 1320, y, 500, 30) + 25
    elif scene["id"] == "inputs-05":
        sample = '{\n  "data": ["69 0 0 64", "69 0 0 52"],\n  "sizes": "64 52",\n  "intervals": "0 0.001",\n  "label": 0, "name": "6-Attacks-1-Flood"\n}'
        draw.rounded_rectangle((90, 310, 1820, 735), radius=22, fill=ink)
        put(sample, 135, 343, 1640, 37, "#f8f6ef", mono=True)
        put("Synthetic schema illustration · not a captured flow or an extractor", 95, 770, 1740, 29, coral)
    elif kind in ("flow", "views") and len(bullets) == 3:
        for index, bullet in enumerate(bullets):
            x = 90 + index * 590
            draw.rounded_rectangle((x, 360, x + 530, 675), radius=24, fill="#ffffff", outline=blue, width=3)
            put(f"0{index + 1}", x + 30, 385, 400, 35, teal, True)
            put(bullet, x + 30, 458, 470, 37, ink, True)
            if index < 2 and kind == "flow":
                put("→", x + 540, 472, 70, 50, teal)
        note = scene.get("note", "Three parallel feature views from the same flow." if kind == "views" else "Follow the direction; each stage has a defined input and output.")
        put(note, 95, 745, 1750, 30, muted)
    else:
        rows = len(bullets)
        height = min(122, 460 // rows)
        for index, bullet in enumerate(bullets):
            y = 330 + index * height
            draw.rounded_rectangle((90, y, 1820, y + height - 17), radius=16, fill="#ffffff", outline=blue, width=2)
            marker = "?" if kind == "question" else "✓" if kind == "answer" else f"{index + 1:02}"
            put(marker, 120, y + 20, 100, 33, teal, True)
            put(bullet, 215, y + 19, 1570, 33, ink, kind in ("title", "answer"))
        if kind == "pause":
            put("Speak or write your answer. The lesson resumes automatically.", 95, 750, 1700, 29, muted)
    draw.line((90, 850, 1820, 850), fill=blue, width=2)
    put("Evidence: " + " · ".join(scene["references"]) + "   |   Links and full text in the transcript", 95, 867, 1750, 22, muted, max_bottom=910)
    image.save(path)


def run(command):
    subprocess.run([str(x) for x in command], check=True)


def clip_frame_plan(scene, fps):
    clip = scene["motion_clip"]
    counts = [clip["start_seconds"] * fps, clip["duration_seconds"] * fps]
    if any(not math.isfinite(n) or n < 0 or abs(n - round(n)) > 1e-7 for n in counts):
        raise ValueError("Recorded clip boundaries must align to whole video frames")
    before, count = [round(n) for n in counts]
    after = scene["frames"] - before - count
    if count <= 0 or after < 0:
        raise ValueError("Recorded clip exceeds its scene frame budget")
    return before, count, after


def scene_frame_entries(scene, frame, work, ffmpeg, fps):
    if not scene.get("motion_clip"):
        sequence = [(frame, scene["frames"])]
    else:
        from PIL import Image, ImageDraw
        clip = scene["motion_clip"]
        before, count, after = clip_frame_plan(scene, fps)
        folder = work / "motion-frames" / scene["id"]
        folder.mkdir(parents=True, exist_ok=True)
        for old in folder.glob("decoded-*.png"):
            old.unlink()
        run([ffmpeg, "-v", "error", "-y", "-ss", str(clip["trim_start_seconds"]),
             "-i", motion_clip(scene), "-vf", f"fps={fps},scale={clip['width']}:{clip['height']}",
             "-frames:v", str(count), "-threads", "2", folder / "decoded-%04d.png"])
        decoded = sorted(folder.glob("decoded-*.png"))
        if len(decoded) != count:
            raise ValueError("Recorded source ended before its declared clip frame count")
        with Image.open(frame) as original:
            background = original.convert("RGB")
        sequence = [(frame, before)] if before else []
        for index, path in enumerate(decoded, 1):
            composite = background.copy()
            ImageDraw.Draw(composite).rectangle((90, 285, 1830, 835), fill=background.getpixel((0, 200)))
            with Image.open(path) as recorded:
                if recorded.size != (clip["width"], clip["height"]):
                    raise ValueError("Unexpected recorded clip frame geometry")
                composite.paste(recorded, (clip["x"], clip["y"]))
            target = folder / f"composite-{index:04d}.png"
            composite.save(target)
            sequence.append((target, 1))
        if after:
            sequence.append((frame, after))
        scene["recorded_clip_frame_count"] = count
        scene["recorded_clip_composites_sha256"] = hashlib.sha256(canonical(
            [{"frame": index, "sha256": digest(path)} for index, (path, frames) in enumerate(sequence) if path != frame])).hexdigest()
    lines = []
    for path, count in sequence:
        lines.extend([f"file '{path.relative_to(work).as_posix()}'", f"option framerate {fps}",
                      f"duration {count / fps:.9f}"])
    return lines


def build(args):
    work, destination = args.work_dir.resolve(), args.output.resolve()
    work.mkdir(parents=True, exist_ok=True)
    destination.mkdir(parents=True, exist_ok=True)
    source_hash = digest(args.source)
    source = load_source(args.source)
    if digest(args.source) != source_hash:
        raise ValueError("Source changed while loading the build")
    metadata = publication(source)
    fps = frame_rate(source)
    narration_dir = (getattr(args, "narration_dir", None) or work / "tts").resolve()
    narration = read(narration_dir / "narration.json")
    preview = getattr(args, "preview_chapter", None)
    if preview:
        validate(source)
        selected = next((c for c in source["chapters"] if c["id"] == preview), None)
        if selected is None:
            raise ValueError("Unknown preview chapter")
        source = dict(source, chapters=[selected], target_seconds=selected["seconds"])
    chapters, scenes = timeline(source, narration, args.source)
    course = read(ROOT / "docs/customer/course-source.json")
    facts = fact_values(course)
    references = reference_paths(source, course)
    reference_identities = {k: {"path": p, "sha256": digest(ROOT / p)} for k, p in references.items()
                            if any(k in s["references"] for s in scenes)}
    for scene in scenes:
        for key in scene["references"]:
            if key not in references:
                raise ValueError(f"Missing video reference: {key}")
            local_reference(references[key])
    cues = caption_cues(scenes)
    write_captions(cues, scenes, work, destination, animate=source.get("animation", {}).get("enabled", False), chapters=chapters)
    motion_record = read(destination / "motion-manifest.json")
    motion_record["source_sha256"] = source_hash
    motion_record["recorded_clips"] = [{"scene": s["id"], **s["motion_clip"]} for s in scenes if s.get("motion_clip")]
    (destination / "motion-manifest.json").write_text(json.dumps(motion_record, indent=2) + "\n", encoding="utf-8", newline="\n")
    caption_method = ("Speech-service word boundaries mapped through the final audio timing; independent encoded-audio checks are reported separately."
                      if source["voice"].get("engine") == "edge-tts" else "Measured sentence audio boundaries and proportional within-sentence breaks, with source-bound corrections for independently measured timing defects.")
    practice_seconds = sum(s["seconds"] for s in scenes if s["kind"] == "pause")
    transcript = [f"# {metadata['title']} — transcript", "",
                  "Synthetic narration rendered from reviewed text. This video explains recorded experiments; it does not perform new training or live capture.", "",
                  f"Runtime: {display_time(source['target_seconds'])}, including {display_time(practice_seconds)} of labeled practice pauses. Caption timing: {caption_method} Full human listening and caption-alignment review remain pending.", ""]
    if metadata["production"]:
        transcript.extend([production_credit(metadata), ""])
    for number, chapter in enumerate(chapters, 1):
        transcript.extend([f"## {timecode(chapter['start']).split('.', 1)[0]} — {chapter['title']}", ""])
        for scene in (s for s in scenes if s["chapter"] == number):
            transcript.extend([f"### {timecode(scene['start']).split('.', 1)[0]} — {scene['title'].replace(chr(10), ': ')}", ""])
            if scene["kind"] == "pause":
                transcript.append(f"**Practice pause: {scene['seconds']} seconds.** " + " ".join(scene["bullets"]))
            else:
                transcript.append(scene["narration"])
            transcript.extend(["", "On screen: " + " · ".join(scene["bullets"]), "",
                               "Evidence: " + ", ".join(f"[{key}](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/{references[key]})" for key in scene["references"]), ""])
    (destination / "transcript.md").write_text("\n".join(transcript).rstrip() + "\n", encoding="utf-8", newline="\n")
    (destination / "chapters.json").write_text(json.dumps(chapters, indent=2) + "\n", encoding="utf-8", newline="\n")
    frames_dir, audio_dir = work / "frames", work / "timed-audio"
    frames_dir.mkdir(exist_ok=True)
    audio_dir.mkdir(exist_ok=True)
    published_frames = destination / "frames"
    published_frames.mkdir(exist_ok=True)
    concat = ["ffconcat version 1.0"]
    with wave.open(str(work / "narration-timed.wav"), "wb") as total:
        total.setparams((1, 2, RATE, 0, "NONE", "not compressed"))
        for scene in scenes:
            frame = frames_dir / (scene["id"] + ".png")
            render_scene(scene, frame, facts, course["demo"])
            published_frame = published_frames / frame.name
            shutil.copyfile(frame, published_frame)
            scene["visuals"] = [{"path": published_frame.relative_to(ROOT).as_posix(), "sha256": digest(frame)}]
            if scene["id"] == scenes[0]["id"]:
                (destination / "poster.png").write_bytes(frame.read_bytes())
            concat.extend(scene_frame_entries(scene, frame, work, args.ffmpeg, fps))
            samples = scene["frames"] * RATE // fps
            if scene["kind"] == "pause":
                total.writeframes(b"\x00\x00" * samples)
            else:
                record = scene["audio"]
                wav = narration_dir / record["wav"]
                if digest(wav) != record["wav_sha256"]:
                    raise ValueError(f"Narration audio changed: {scene['id']}")
                timed = audio_dir / wav.name
                run([args.ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", wav,
                     "-af", f"atempo={scene['tempo']:.9f},apad,atrim=end_sample={samples}",
                     "-ar", str(RATE), "-ac", "1", "-c:a", "pcm_s16le", timed])
                with wave.open(str(timed), "rb") as audio:
                    if audio.getnframes() != samples or audio.getframerate() != RATE:
                        raise ValueError("Timed audio duration mismatch")
                    total.writeframes(audio.readframes(samples))
                scene["final_audio"] = {"sha256": digest(timed), "samples": samples, "sample_rate": RATE,
                                         "scope": "timed PCM production intermediate; encoded MP4 is public"}
                record["final_audio"] = scene["final_audio"]
            print(f"Rendered {scene['id']}: {scene['end'] - scene['start']:.1f}s", flush=True)
    concat.extend([f"file 'frames/{scenes[-1]['id']}.png'", f"option framerate {fps}"])
    (work / "frames.ffconcat").write_text("\n".join(concat) + "\n", encoding="utf-8", newline="\n")
    def escape_metadata(value):
        return re.sub(r"([\\=;#\n])", r"\\\1", value)

    media_metadata = [";FFMETADATA1", "title=" + escape_metadata(metadata["title"]),
                      "comment=" + escape_metadata(production_credit(metadata) or "Synthetic narration; recorded research results, not live inference.")]
    for chapter in chapters:
        media_metadata.extend(["[CHAPTER]", "TIMEBASE=1/1000", f"START={round(chapter['start'] * 1000)}",
                               f"END={round(chapter['end'] * 1000)}", "title=" + escape_metadata(chapter["title"])])
    (work / "chapters.ffmetadata").write_text("\n".join(media_metadata) + "\n", encoding="utf-8", newline="\n")
    narration["timed_audio"] = {"sha256": digest(work / "narration-timed.wav"), "sample_rate": RATE,
                                "samples": source["target_seconds"] * RATE,
                                "scope": "Concatenated timed PCM before final loudness normalization and AAC encoding"}
    (destination / "narration-manifest.json").write_text(json.dumps(narration, indent=2) + "\n", encoding="utf-8", newline="\n")
    media = destination / metadata["media_name"]
    command = [args.ffmpeg, "-hide_banner", "-loglevel", "warning", "-stats", "-y",
         "-safe", "0", "-i", work / "frames.ffconcat", "-i", work / "narration-timed.wav",
         "-i", work / "chapters.ffmetadata"]
    command.extend(["-vf", f"fps={fps},ass={work / 'captions.ass'}", "-map", "0:v:0", "-map", "1:a:0", "-map_metadata", "2",
         "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
         "-c:v", "libx264", "-preset", "medium", "-tune", "stillimage", "-crf", "23",
         "-pix_fmt", "yuv420p", "-threads", "8", "-g", str(fps * 10), "-c:a", "aac", "-b:a", "96k",
         "-ar", "48000", "-movflags", "+faststart", "-t", str(source["target_seconds"]), media])
    run(command)
    if digest(args.source) != source_hash or any(digest(ROOT / r["path"]) != r["sha256"] for r in reference_identities.values()):
        raise ValueError("Source or references changed during video build; review and rebuild before publication")
    inventory = {p.name: {"bytes": p.stat().st_size, "sha256": digest(p)} for p in [media, destination / "captions.srt", destination / "captions.vtt", destination / "transcript.md", destination / "chapters.json", destination / "poster.png", destination / "motion-manifest.json", destination / "narration-manifest.json"]}
    record = {"schema_version": 1, "source_sha256": source_hash, "source_path": args.source.resolve().relative_to(ROOT).as_posix(), "source_course_commit": source["source_course_commit"],
              "caption_timing_method": caption_method, "animation": source.get("animation", {"enabled": False}),
              "voice": source["voice"], "voices_sha256": narration["voices_sha256"], "fps": fps,
              "scheduled_seconds": source["target_seconds"], "max_practice_seconds": source.get("max_practice_seconds", 180),
              **{key: value for key, value in metadata.items() if key != "webm_name"},
              "practice_seconds": practice_seconds, "chapters": chapters,
              "scenes": [dict({k: v for k, v in s.items() if k != "audio"},
                              **({"audio": {key: s["audio"][key] for key in ("wav_sha256", "samples", "sample_rate")}}
                                 if s.get("audio") else {})) for s in scenes], "caption_cues": cues,
              "references": reference_identities,
              "artifacts": inventory, "status": "built; encoded-media verification is separate"}
    if preview:
        record["preview_chapter"] = preview
    (destination / "media-manifest.json").write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"media": str(media), "bytes": media.stat().st_size, "sha256": digest(media)}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--work-dir", type=Path, default=DEFAULT_WORK)
    parser.add_argument("--narration-dir", type=Path, help="Read-only narration cache; defaults to WORK/tts")
    parser.add_argument("--output", type=Path, default=DESTINATION)
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--preview-chapter", help="Build one chapter in an explicitly isolated output directory before the complete render")
    parser.add_argument("--webm-only", action="store_true", help="Add a VP9/Opus browser fallback from the existing checked MP4")
    args = parser.parse_args()
    if args.preview_chapter and args.output.resolve() == DESTINATION.resolve():
        parser.error("A preview requires an explicit separate --output directory")
    if args.preview_chapter and args.work_dir.resolve() == DEFAULT_WORK.resolve():
        parser.error("A preview requires a separate --work-dir; use --narration-dir to read the full speech cache")
    if args.webm_only:
        manifest = read(args.output / "media-manifest.json")
        from verify_course_video import check_schedule
        source = load_source(args.source)
        check_schedule(source, manifest)
        if manifest["source_sha256"] != digest(args.source):
            raise ValueError("Video narration source has changed")
        metadata = publication(manifest)
        media = args.output / metadata["media_name"]
        if digest(media) != manifest["artifacts"][media.name]["sha256"]:
            raise ValueError("MP4 has changed before browser fallback encoding")
        webm = args.output / metadata["webm_name"]
        run([args.ffmpeg, "-hide_banner", "-loglevel", "warning", "-stats", "-y", "-i", media,
             "-map", "0:v:0", "-map", "0:a:0", "-map_metadata", "0", "-c:v", "libvpx-vp9",
             "-row-mt", "1", "-tile-columns", "2", "-cpu-used", "6", "-deadline", "realtime",
             "-threads", "8", "-crf", "46", "-tune-content", "screen", "-b:v", "0",
             "-c:a", "libopus", "-b:a", "80k", webm])
        if webm.stat().st_size >= 100 * 1024 * 1024:
            raise ValueError("Browser encoding exceeds the repository's 100 MiB single-file ceiling")
        manifest["artifacts"][webm.name] = {"bytes": webm.stat().st_size, "sha256": digest(webm)}
        manifest["browser_fallback"] = {"source_mp4_sha256": digest(media), "codec": "VP9/Opus",
                                        "encoding": {"crf": 46, "tune_content": "screen", "deadline": "realtime",
                                                     "cpu_used": 6, "audio_bitrate": "80k"},
                                        "reason": "The tested open-source Chromium build does not include H.264/AAC decoding"}
        (args.output / "media-manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    else:
        build(args)


if __name__ == "__main__":
    main()
