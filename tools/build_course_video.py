"""Build the narrated 30-minute course from local speech, evidence and diagrams."""

import argparse
import hashlib
import html
import json
import math
import re
import subprocess
import textwrap
import wave
from pathlib import Path

from build_course import ROOT, fact_values, read
from narrate_course_video import SOURCE, canonical, digest, load_source

FPS = 10
RATE = 24000
DESTINATION = ROOT / "docs/customer/demo/video"
MEDIA_NAME = "NetMambaPlus-30-minute-course.mp4"
WEBM_NAME = "NetMambaPlus-30-minute-course.webm"


def validate(source):
    if source["target_seconds"] != 1800 or sum(c["seconds"] for c in source["chapters"]) != 1800:
        raise ValueError("The video must contain exactly 1,800 scheduled seconds")
    names = set()
    for chapter in source["chapters"]:
        pauses = 0
        for scene in chapter["scenes"]:
            if scene["id"] in names or not re.fullmatch(r"[a-z0-9-]+", scene["id"]):
                raise ValueError("Scene identifiers must be unique and path-safe")
            names.add(scene["id"])
            if not scene["bullets"] or not scene["references"]:
                raise ValueError("Every scene needs visible teaching and evidence references")
            if scene["kind"] == "pause":
                if scene["narration"] or not isinstance(scene.get("seconds"), int) or scene["seconds"] <= 0:
                    raise ValueError("Practice pauses need an explicit positive duration and no speech")
                pauses += scene["seconds"]
            elif not scene["narration"].strip():
                raise ValueError("Teaching scenes cannot be unexplained silent holds")
        if pauses >= chapter["seconds"] or not pauses:
            raise ValueError("Each chapter needs both narration and intentional practice")


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


def timeline(source, narration):
    validate(source)
    if narration["source_sha256"] != digest(SOURCE):
        raise ValueError("Narration is stale; regenerate it from the reviewed source")
    records = {r["id"]: r for r in narration["scenes"]}
    chapters, scenes, cursor = [], [], 0
    for number, chapter in enumerate(source["chapters"], 1):
        start = cursor
        spoken = [s for s in chapter["scenes"] if s["kind"] != "pause"]
        budget = chapter["seconds"] - sum(s.get("seconds", 0) for s in chapter["scenes"] if s["kind"] == "pause")
        weights = [records[s["id"]]["seconds"] for s in spoken]
        allocation = dict(zip((s["id"] for s in spoken), allocate_frames(weights, budget * FPS)))
        for original in chapter["scenes"]:
            scene = dict(original)
            frames = scene["seconds"] * FPS if scene["kind"] == "pause" else allocation[scene["id"]]
            scene.update(start=cursor / FPS, end=(cursor + frames) / FPS, frames=frames,
                         chapter=number, chapter_title=chapter["title"])
            if scene["kind"] != "pause":
                scene["tempo"] = records[scene["id"]]["seconds"] / (frames / FPS)
                if not 0.8 <= scene["tempo"] <= 1.0:
                    raise ValueError(f"Unnatural speech pacing for {scene['id']}: {scene['tempo']:.3f}; revise narration")
                scene["audio"] = records[scene["id"]]
            scenes.append(scene)
            cursor += frames
        chapters.append({"id": chapter["id"], "title": chapter["title"],
                         "start": start / FPS, "end": cursor / FPS})
    if cursor != 1800 * FPS:
        raise ValueError("Timeline drift")
    return chapters, scenes


def timecode(seconds, separator="."):
    millis = round(seconds * 1000)
    hours, rest = divmod(millis, 3600000)
    minutes, rest = divmod(rest, 60000)
    secs, ms = divmod(rest, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02}{separator}{ms:03}"


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


def write_captions(cues, scenes, work, destination):
    srt, vtt = [], ["WEBVTT", ""]
    ass = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1920", "PlayResY: 1080",
           "WrapStyle: 0", "[V4+ Styles]",
           "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
           "Style: Speech,DejaVu Sans,38,&H00FFFFFF,&H00FFFFFF,&H00221B13,&H00221B13,0,0,0,0,100,100,0,0,3,14,0,2,140,140,45,1",
           "Style: Practice,DejaVu Sans,45,&H005F503B,&H005F503B,&H00F3F6F8,&H00F3F6F8,-1,0,0,0,100,100,0,0,1,0,0,2,100,100,45,1",
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
    (work / "captions.ass").write_text("\n".join(ass) + "\n", encoding="utf-8", newline="\n")


def render_scene(scene, path, facts, demo):
    from PIL import Image, ImageDraw, ImageFont
    fonts = Path("/usr/share/fonts/truetype/dejavu")
    bg, ink, muted, teal, blue, coral = "#f8f6ef", "#172c3a", "#465a63", "#126e68", "#d9e9ed", "#b14c36"
    image = Image.new("RGB", (1920, 1080), bg)
    draw = ImageDraw.Draw(image)

    def font(size, bold=False, mono=False):
        return ImageFont.truetype(str(fonts / ("DejaVuSansMono.ttf" if mono else "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf")), size)

    def put(text, x, y, width, size=36, color=ink, bold=False, mono=False, max_bottom=835):
        selected = font(size, bold, mono)
        lines = []
        for paragraph in str(text).split("\n"):
            line = ""
            for word in paragraph.split():
                candidate = (line + " " + word).strip()
                if line and draw.textlength(candidate, font=selected) > width:
                    lines.append(line)
                    line = word
                else:
                    line = candidate
            lines.append(line)
        height = len(lines) * (size + 12)
        if y + height > max_bottom:
            raise ValueError(f"Visual overflow in {scene['id']}: {text}")
        for line in lines:
            draw.text((x, y), line, font=selected, fill=color)
            y += size + 12
        return y

    draw.rectangle((0, 0, 1920, 15), fill=teal)
    put("NETMAMBA+  /  REPRODUCTION LAB", 90, 54, 980, 25, teal, True)
    put(f"{scene['chapter']:02} / 09   ·   {int(scene['start']) // 60:02}:{int(scene['start']) % 60:02}", 1480, 54, 360, 25, muted)
    put(scene["title"], 90, 132, 1730, 56, ink, True)
    kind, bullets = scene["kind"], scene["bullets"]
    if kind == "results":
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
        note = "Three parallel feature views from the same flow." if kind == "views" else "Follow the direction; each stage has a defined input and output."
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


def build(args):
    work, destination = args.work_dir.resolve(), args.output.resolve()
    work.mkdir(parents=True, exist_ok=True)
    destination.mkdir(parents=True, exist_ok=True)
    source = load_source()
    narration = read(work / "tts/narration.json")
    chapters, scenes = timeline(source, narration)
    course = read(ROOT / "docs/customer/course-source.json")
    facts = fact_values(course)
    references = {key: value["path"] for key, value in course["references"].items()}
    references["contract"] = "docs/harness-reference.md"
    references["support"] = "docs/support-matrix.md"
    for scene in scenes:
        for key in scene["references"]:
            if key not in references or not (ROOT / references[key]).is_file():
                raise ValueError(f"Missing video reference: {key}")
    cues = caption_cues(scenes)
    write_captions(cues, scenes, work, destination)
    transcript = ["# NetMamba+ — 30-minute video transcript", "",
                  "Locally synthesized narration. This video explains recorded experiments; it does not perform new training or live capture.", "",
                  "Runtime: 30:00, including 3:00 of labeled practice pauses and a 90-second teach-back. Captions use measured sentence audio boundaries and proportional within-sentence breaks, with source-bound corrections for independently measured timing defects. Full human listening and caption-alignment review remain pending.", ""]
    for chapter in chapters:
        transcript.extend([f"## {timecode(chapter['start'])[:8]} — {chapter['title']}", ""])
        for scene in (s for s in scenes if s["chapter_title"] == chapter["title"]):
            transcript.extend([f"### {timecode(scene['start'])[:8]} — {scene['title'].replace(chr(10), ': ')}", ""])
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
    concat = ["ffconcat version 1.0"]
    with wave.open(str(work / "narration-timed.wav"), "wb") as total:
        total.setparams((1, 2, RATE, 0, "NONE", "not compressed"))
        for scene in scenes:
            frame = frames_dir / (scene["id"] + ".png")
            render_scene(scene, frame, facts, course["demo"])
            if scene["id"] == scenes[0]["id"]:
                (destination / "poster.png").write_bytes(frame.read_bytes())
            concat.extend([f"file 'frames/{frame.name}'", f"duration {scene['frames'] / FPS:.1f}"])
            samples = scene["frames"] * RATE // FPS
            if scene["kind"] == "pause":
                total.writeframes(b"\x00\x00" * samples)
            else:
                record = scene["audio"]
                wav = work / "tts" / record["wav"]
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
            print(f"Rendered {scene['id']}: {scene['end'] - scene['start']:.1f}s", flush=True)
    concat.append(f"file 'frames/{scenes[-1]['id']}.png'")
    (work / "frames.ffconcat").write_text("\n".join(concat) + "\n", encoding="utf-8", newline="\n")
    metadata = [";FFMETADATA1", "title=NetMamba+ — the 30-minute video course", "comment=Local synthetic narration; recorded research results, not live inference."]
    for chapter in chapters:
        metadata.extend(["[CHAPTER]", "TIMEBASE=1/1000", f"START={round(chapter['start'] * 1000)}",
                         f"END={round(chapter['end'] * 1000)}", "title=" + chapter["title"].replace("=", "\\=")])
    (work / "chapters.ffmetadata").write_text("\n".join(metadata) + "\n", encoding="utf-8", newline="\n")
    media = destination / MEDIA_NAME
    run([args.ffmpeg, "-hide_banner", "-loglevel", "warning", "-stats", "-y",
         "-safe", "0", "-i", work / "frames.ffconcat", "-i", work / "narration-timed.wav",
         "-i", work / "chapters.ffmetadata", "-map", "0:v:0", "-map", "1:a:0", "-map_metadata", "2",
         "-vf", f"fps={FPS},ass={work / 'captions.ass'}", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
         "-c:v", "libx264", "-preset", "medium", "-tune", "stillimage", "-crf", "23",
         "-pix_fmt", "yuv420p", "-threads", "8", "-g", "100", "-c:a", "aac", "-b:a", "96k",
         "-ar", "48000", "-movflags", "+faststart", "-t", "1800", media])
    inventory = {p.name: {"bytes": p.stat().st_size, "sha256": digest(p)} for p in [media, destination / "captions.srt", destination / "captions.vtt", destination / "transcript.md", destination / "chapters.json", destination / "poster.png"]}
    record = {"schema_version": 1, "source_sha256": digest(SOURCE), "source_course_commit": source["source_course_commit"],
              "voice": source["voice"], "voices_sha256": narration["voices_sha256"], "fps": FPS, "scheduled_seconds": 1800,
              "practice_seconds": sum(s["seconds"] for s in scenes if s["kind"] == "pause"), "chapters": chapters,
              "scenes": [{k: v for k, v in s.items() if k != "audio"} for s in scenes], "caption_cues": cues,
              "references": {k: {"path": p, "sha256": digest(ROOT / p)} for k, p in references.items() if any(k in s["references"] for s in scenes)},
              "artifacts": inventory, "status": "built; encoded-media verification is separate"}
    (destination / "media-manifest.json").write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"media": str(media), "bytes": media.stat().st_size, "sha256": digest(media)}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", type=Path, default=ROOT / "runs/video-course")
    parser.add_argument("--output", type=Path, default=DESTINATION)
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--webm-only", action="store_true", help="Add a VP9/Opus browser fallback from the existing checked MP4")
    args = parser.parse_args()
    if args.webm_only:
        manifest = read(args.output / "media-manifest.json")
        media = args.output / MEDIA_NAME
        if digest(media) != manifest["artifacts"][MEDIA_NAME]["sha256"]:
            raise ValueError("MP4 has changed before browser fallback encoding")
        webm = args.output / WEBM_NAME
        run([args.ffmpeg, "-hide_banner", "-loglevel", "warning", "-stats", "-y", "-i", media,
             "-map", "0:v:0", "-map", "0:a:0", "-map_metadata", "0", "-c:v", "libvpx-vp9",
             "-row-mt", "1", "-tile-columns", "2", "-cpu-used", "6", "-deadline", "realtime",
             "-threads", "8", "-crf", "32", "-b:v", "0", "-c:a", "libopus", "-b:a", "80k", webm])
        manifest["artifacts"][WEBM_NAME] = {"bytes": webm.stat().st_size, "sha256": digest(webm)}
        manifest["browser_fallback"] = {"source_mp4_sha256": digest(media), "codec": "VP9/Opus",
                                        "reason": "The tested open-source Chromium build does not include H.264/AAC decoding"}
        (args.output / "media-manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    else:
        build(args)


if __name__ == "__main__":
    main()
