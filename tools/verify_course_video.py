"""Check video identities and captions; optionally decode and measure the actual MP4."""

import argparse
import hashlib
import html
import json
import math
import re
import subprocess
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path, PurePosixPath

from build_course import ROOT, read
from build_course_video import (DESTINATION, LEGACY_DESTINATION, FPS, chapter_schedule, frame_rate, local_reference,
                                publication, reference_paths, validate)
from build_video_page import WATCH_PAGE
from narrate_course_video import LEGACY_SOURCE, SOURCE, digest, load_source


def resolve_reference_revision(revision, root=ROOT):
    if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-f]{7,40}", revision):
        raise ValueError("Historical references require an immutable hexadecimal Git commit")
    try:
        return subprocess.check_output(["git", "-C", str(root), "rev-parse", "--verify", revision + "^{commit}"],
                                       stderr=subprocess.PIPE).decode("ascii").strip()
    except subprocess.CalledProcessError as error:
        raise ValueError(f"Historical reference commit is unavailable: {revision}") from error


def reference_bytes(relative, root=ROOT, revision=None):
    if (not isinstance(relative, str) or not relative or "\\" in relative or ":" in relative
            or PurePosixPath(relative).is_absolute() or ".." in PurePosixPath(relative).parts
            or PurePosixPath(relative).as_posix() != relative):
        raise ValueError("References must be repository-relative POSIX paths")
    if revision is None:
        return local_reference(relative, root).read_bytes()
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("Resolve historical references to a complete commit hash first")
    try:
        return subprocess.check_output(["git", "-C", str(root), "cat-file", "blob", f"{revision}:{relative}"],
                                       stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as error:
        raise ValueError(f"Historical reference is unavailable: {relative} at {revision}") from error

def check_probe(probe, expected=None):
    if expected is None:
        source = load_source()
        expected = {"scheduled_seconds": source["target_seconds"], "chapters": chapter_schedule(source), "fps": frame_rate(source)}
    target = expected["scheduled_seconds"]
    duration = float(probe["format"]["duration"])
    if not math.isfinite(duration) or abs(duration - target) > 1:
        raise ValueError("Truncated or overlong video")
    streams = {s["codec_type"]: s for s in probe["streams"] if s["codec_type"] in ("video", "audio")}
    if set(streams) != {"video", "audio"}:
        raise ValueError("Both video and audio streams are required")
    video, audio = streams["video"], streams["audio"]
    if (video["codec_name"], video["width"], video["height"]) != ("h264", 1920, 1080) or audio["codec_name"] != "aac":
        raise ValueError("Unexpected video or audio encoding")
    if "fps" in expected and Fraction(video.get("avg_frame_rate", "0")) != expected["fps"]:
        raise ValueError("Encoded frame rate differs from the source schedule")
    if any(not math.isfinite(float(s["duration"])) or abs(float(s["duration"]) - target) > 1
           or not math.isfinite(float(s.get("start_time", 0))) or abs(float(s.get("start_time", 0))) > 0.1 for s in streams.values()):
        raise ValueError("A stream does not span the complete programme")
    starts = [float(c["start_time"]) for c in probe["chapters"]]
    spans = [(float(c["start_time"]), float(c["end_time"])) for c in probe["chapters"]]
    if spans != [(c["start"], c["end"]) for c in expected["chapters"]]:
        raise ValueError("Embedded chapter markers have drifted")
    return {"seconds": duration, "streams": streams, "chapter_starts": starts}


def parse_time(value):
    hours, minutes, seconds = value.split(":")
    return 3600 * int(hours) + 60 * int(minutes) + float(seconds)


def check_vtt(text, expected, duration=None):
    if duration is None:
        duration = load_source()["target_seconds"]
    if not text.startswith("WEBVTT\n"):
        raise ValueError("Invalid WebVTT header")
    cues = []
    for block in text.strip().split("\n\n")[1:]:
        lines = block.splitlines()
        if not lines or not re.fullmatch(r"\d{2,}:[0-5]\d:[0-5]\d\.\d{3} --> \d{2,}:[0-5]\d:[0-5]\d\.\d{3}", lines[0]):
            raise ValueError("Invalid caption timestamp syntax")
        start, end = map(parse_time, lines[0].split(" --> "))
        if not (0 <= start < end <= duration) or (cues and start < cues[-1]["end"] - 0.002):
            raise ValueError("Invalid caption timing or overlap")
        cues.append({"start": start, "end": end, "text": html.unescape(" ".join(lines[1:]))})
    if len(cues) != len(expected):
        raise ValueError("Caption count differs from the narration timeline")
    for cue, original in zip(cues, expected):
        if any(abs(cue[k] - original[k]) > 0.002 for k in ("start", "end")) or cue["text"] != original["text"]:
            raise ValueError("Caption content or timing differs from its source")
    return len(cues)


def check_silences(intervals, scenes, tolerance=1.0):
    pauses = [s for s in scenes if s["kind"] == "pause"]
    if not intervals:
        raise ValueError("Announced practice pauses were not detected in encoded audio")
    for start, end in intervals:
        if end - start >= 3 and not any(start >= p["start"] - tolerance and end <= p["end"] + tolerance for p in pauses):
            raise ValueError(f"Unexplained encoded silence: {start:.3f}–{end:.3f}s")
    for pause in pauses:
        if not any(abs(start - pause["start"]) <= tolerance and abs(end - pause["end"]) <= tolerance for start, end in intervals):
            raise ValueError(f"Practice audio does not match its declared window: {pause['id']}")
    return {"intervals": intervals, "total_seconds": sum(end - start for start, end in intervals), "tolerance_seconds": tolerance}


def check_schedule(source, manifest, reference_root=ROOT):
    """Bind media and every scene's chapter mapping to the independent lesson source."""
    validate(source, reference_root)
    if publication(source) != publication(manifest):
        raise ValueError("Video publication metadata differs from its source")
    if (manifest["scheduled_seconds"] != source["target_seconds"]
            or manifest.get("max_practice_seconds", 180) != source.get("max_practice_seconds", 180)
            or manifest.get("fps", FPS) != frame_rate(source)):
        raise ValueError("Video duration, practice budget or frame rate differs from its source")
    expected = chapter_schedule(source)
    if manifest["chapters"] != expected:
        raise ValueError("Incorrect chapter schedule")
    source_scenes = [(number, s) for number, c in enumerate(source["chapters"], 1) for s in c["scenes"]]
    if len(source_scenes) != len(manifest["scenes"]):
        raise ValueError("Missing video scenes")
    previous, pauses = 0, 0
    for (number, source_scene), scene in zip(source_scenes, manifest["scenes"]):
        chapter = expected[number - 1]
        for key in source_scene:
            if scene.get(key) != source_scene[key]:
                raise ValueError(f"Narration/visual mismatch: {scene['id']}")
        if (scene["chapter"] != number or scene["chapter_title"] != chapter["title"]
                or scene.get("chapter_id", chapter["id"]) != chapter["id"]
                or scene.get("chapter_count", len(expected)) != len(expected)):
            raise ValueError("Scene chapter mapping differs from its source")
        if (not math.isfinite(scene["start"]) or not math.isfinite(scene["end"])
                or scene["start"] != previous or scene["end"] <= scene["start"]
                or scene["start"] < chapter["start"] or scene["end"] > chapter["end"]):
            raise ValueError("Scene schedule has a gap or overlap")
        frames = (scene["end"] - scene["start"]) * frame_rate(source)
        if "frames" in scene and (abs(frames - scene["frames"]) > 0.000001 or type(scene["frames"]) is not int):
            raise ValueError("Scene frames differ from its duration")
        previous = scene["end"]
        if scene["kind"] == "pause":
            if abs(scene["end"] - scene["start"] - source_scene["seconds"]) > 0.000001:
                raise ValueError("Practice duration differs from its source")
            pauses += scene["end"] - scene["start"]
        elif not 0.8 <= scene["tempo"] <= 1:
            raise ValueError("Speech was accelerated or slowed excessively")
    if previous != source["target_seconds"] or pauses > source.get("max_practice_seconds", 180) or pauses != manifest["practice_seconds"]:
        raise ValueError("Video or practice duration mismatch")
    return pauses


def verify_files(directory=None, source_path=None, *, reference_revision=None, reference_root=None):
    directory = Path(directory or DESTINATION)
    source_path = Path(source_path or SOURCE).resolve()
    if reference_revision is not None and reference_root is not None:
        raise ValueError("Choose a reference revision or a reference snapshot root")
    reference_root = Path(reference_root or ROOT).resolve()
    revision = resolve_reference_revision(reference_revision) if reference_revision is not None else None
    manifest = read(directory / "media-manifest.json")
    source = load_source(source_path)
    validate(source, reference_root)
    expected_path = source_path.relative_to(ROOT).as_posix()
    recorded_path = manifest.get("source_path", LEGACY_SOURCE.relative_to(ROOT).as_posix())
    if recorded_path != expected_path:
        raise ValueError("Video source path differs from the selected version")
    if manifest["source_sha256"] != digest(source_path):
        raise ValueError("Video narration source has changed")
    media_name = publication(source)["media_name"]
    required = {media_name, "captions.vtt", "captions.srt", "transcript.md", "chapters.json", "poster.png"}
    if not required.issubset(manifest["artifacts"]):
        raise ValueError("Required video downloads are missing from the manifest")
    for name, identity in manifest["artifacts"].items():
        path = directory / name
        if (Path(name).name != name or "\\" in name or not path.resolve().is_relative_to(directory.resolve())
                or not path.is_file() or digest(path) != identity["sha256"] or path.stat().st_size != identity["bytes"]):
            raise ValueError(f"Video checksum mismatch: {name}")
    course = json.loads(reference_bytes("docs/customer/course-source.json", reference_root, revision))
    references = reference_paths(source, course, reference_root)
    used = {key for chapter in source["chapters"] for scene in chapter["scenes"] for key in scene["references"]}
    if set(manifest["references"]) != used:
        raise ValueError("Video reference keys differ from the source")
    for key, reference in manifest["references"].items():
        if references.get(key) != reference["path"]:
            raise ValueError(f"Video reference mapping changed: {key}")
        if hashlib.sha256(reference_bytes(reference["path"], reference_root, revision)).hexdigest() != reference["sha256"]:
            raise ValueError(f"Video reference changed: {reference['path']}")
    pauses = check_schedule(source, manifest, reference_root)
    if read(directory / "chapters.json") != manifest["chapters"]:
        raise ValueError("Chapter download differs from the source schedule")
    if set(source["customer_questions"]) != {"tried", "learning", "inputs", "results", "demo", "hardware", "gaps"}:
        raise ValueError("Missing customer coverage")
    chapters = {c["id"] for c in source["chapters"]}
    if any(not ids or any(i not in chapters for i in ids) for ids in source["customer_questions"].values()):
        raise ValueError("Invalid customer coverage mapping")
    count = check_vtt((directory / "captions.vtt").read_text(encoding="utf-8"), manifest["caption_cues"], source["target_seconds"])
    return manifest, {"status": "passed", "source_path": expected_path, "source_sha256": digest(source_path),
                      "reference_revision": revision,
                      "reference_root": str(reference_root) if revision is None else None,
                      "artifacts": manifest["artifacts"],
                      "scenes": len(manifest["scenes"]), "captions": count, "practice_seconds": pauses,
                      "scope": "Source, file identity and caption checks; encoded-media decode is a separate option."}


def measure_media(media, manifest, ffmpeg, ffprobe, output):
    output.mkdir(parents=True, exist_ok=True)
    command = [ffprobe, "-v", "error", "-show_streams", "-show_format", "-show_chapters", "-of", "json", str(media)]
    probe = json.loads(subprocess.check_output(command))
    result = check_probe(probe, manifest)
    (output / "ffprobe.json").write_text(json.dumps(probe, indent=2) + "\n", encoding="utf-8", newline="\n")
    command = [ffmpeg, "-hide_banner", "-nostats", "-xerror", "-i", str(media),
               "-map", "0:v:0", "-map", "0:a:0", "-af",
               "silencedetect=noise=-45dB:d=3,ebur128=peak=true:framelog=verbose,astats=reset=0",
               "-f", "null", "-"]
    process = subprocess.run(command, capture_output=True, text=True)
    log = process.stderr
    (output / "decode-audio.log").write_text(log, encoding="utf-8", newline="\n")
    if process.returncode:
        raise ValueError("Complete audiovisual decode failed; see decode-audio.log")
    starts = [float(x) for x in re.findall(r"silence_start: ([0-9.]+)", log)]
    ends = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", log)]
    if len(starts) != len(ends):
        raise ValueError("Unclosed silence interval")
    result["silence"] = check_silences(list(zip(starts, ends)), manifest["scenes"])
    result["silence"]["parameters"] = {"threshold_db": -45, "minimum_seconds": 3}
    loudness = re.findall(r"I:\s+(-?[0-9.]+) LUFS", log)
    peak = re.findall(r"Peak:\s+(-?[0-9.]+) dBFS", log)
    rms = re.findall(r"RMS level dB:\s+(-?[0-9.]+)", log)
    if not loudness or not peak or not rms:
        raise ValueError("Missing actual encoded-audio measurements")
    result["audio"] = {"integrated_lufs": float(loudness[-1]), "true_peak_dbfs": float(peak[-1]), "rms_dbfs": float(rms[-1])}
    if not -22 <= result["audio"]["integrated_lufs"] <= -12 or result["audio"]["true_peak_dbfs"] >= 0:
        raise ValueError("Silent, excessively quiet/loud or clipping audio")
    result.update(status="passed", completed_at=datetime.now(timezone.utc).isoformat(),
                  mp4_sha256=digest(media), command=command, decode_exit_code=process.returncode,
                  decode_log_sha256=digest(output / "decode-audio.log"),
                  human_full_playback_review="pending; automated decode is not a listening review")
    (output / "media-check.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    return result


def browser_check(output, url, manifest=None, *, media_dir=None, watch_page=None, source_path=None):
    from playwright.sync_api import sync_playwright
    media_dir = Path(media_dir or DESTINATION)
    watch_page = Path(watch_page or WATCH_PAGE)
    if manifest is None:
        manifest, _ = verify_files(media_dir, source_path)
    duration = manifest["scheduled_seconds"]
    offsets = [chapter["start"] for chapter in manifest["chapters"]]
    media_name = publication(manifest)["media_name"]
    from urllib.request import urlopen
    from importlib.metadata import version
    if output.exists():
        raise ValueError("Use a fresh browser receipt directory")
    output.mkdir(parents=True)
    served = urlopen(url, timeout=30).read()
    if served != watch_page.read_bytes():
        raise ValueError("Watch page differs from the reviewed local file")
    errors, widths = [], []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1000}, accept_downloads=True)
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(url, wait_until="networkidle")
        page.wait_for_function("document.getElementById('player').readyState >= 1")
        browser_duration = page.eval_on_selector("#player", "v => v.duration")
        if not math.isfinite(browser_duration) or abs(browser_duration - duration) > 1:
            raise ValueError("Browser media duration is incorrect")
        player = page.locator("#player")
        player.focus()
        page.keyboard.press("Space")
        progress = min(1, duration / 4)
        page.wait_for_function("t => document.getElementById('player').currentTime > t", arg=progress)
        decoded = player.evaluate("v => ({audio:v.webkitAudioDecodedByteCount, video:v.getVideoPlaybackQuality().totalVideoFrames, played_src:v.currentSrc})")
        if not decoded["audio"] or not decoded["video"]:
            raise ValueError("Browser did not decode both picture and audio")
        player.evaluate("v => v.pause()")
        page.locator("track").evaluate("t => t.track.mode='hidden'")
        page.wait_for_function("document.querySelector('track').readyState===2")
        caption_count = page.locator("track").evaluate("t => t.track.cues.length")
        if caption_count != len(manifest["caption_cues"]):
            raise ValueError("Same-origin caption track is incomplete")
        if page.locator(".chapter").count() != len(offsets):
            raise ValueError("Watch page chapter count differs from the source")
        for index, offset in enumerate(offsets):
            page.locator(".chapter").nth(index).focus()
            page.keyboard.press("Enter")
            page.wait_for_function("t => !document.getElementById('player').seeking && Math.abs(document.getElementById('player').currentTime-t)<0.3", arg=offset)
        near_end = max(0, duration - min(10, duration / 2))
        player.evaluate("(v, t) => {v.currentTime=t;}", near_end)
        page.wait_for_function("!document.getElementById('player').seeking")
        player.focus()
        page.keyboard.press("Space")
        page.wait_for_function("t => document.getElementById('player').currentTime > t", arg=near_end + progress)
        player.evaluate("v => v.pause()")
        for width in [320, 390, 768, 1440]:
            page.set_viewport_size({"width": width, "height": 1000})
            if not page.evaluate("document.documentElement.scrollWidth<=innerWidth+1"):
                raise ValueError(f"Watch page overflow at {width}px")
            widths.append(width)
            player.screenshot(path=str(output / f"video-{width}.png"))
        with page.expect_download() as event:
            page.get_by_role("link", name=re.compile("Download MP4")).click()
        download = event.value
        downloaded = Path(download.path())
        if digest(downloaded) != digest(media_dir / media_name):
            raise ValueError("Browser MP4 download differs from the checked media")
        browser_version = browser.version
        browser.close()
    if errors:
        raise ValueError(f"Watch page errors: {errors}")
    result = {"status": "passed", "url": url, "completed_at": datetime.now(timezone.utc).isoformat(),
              "browser": f"Chromium {browser_version}; Playwright {version('playwright')}",
              "html_sha256": digest(watch_page), "mp4_sha256": digest(media_dir / media_name),
              "decoded_frames_and_audio_bytes": decoded, "caption_count": caption_count,
              "keyboard_playback": True, "keyboard_chapter_offsets": offsets,
              "scheduled_seconds": duration, "near_end_seek_seconds": near_end,
              "seek_and_play_near_end": True, "download_bytes_equal": True, "served_bytes_equal": True,
              "viewport_widths_without_overflow": widths, "page_errors": errors,
              "screenshots": {p.name: digest(p) for p in output.glob("*.png")}}
    (output / "browser-check.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decode-output", type=Path)
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--ffprobe", default="ffprobe")
    parser.add_argument("--browser-output", type=Path)
    parser.add_argument("--url")
    parser.add_argument("--media-dir", type=Path)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--watch-page", type=Path, help="Local HTML whose bytes must match the browser URL")
    parser.add_argument("--legacy", action="store_true", help="Verify the preserved v2 files and source")
    parser.add_argument("--reference-revision", help="With --legacy, hash reference blobs at this immutable Git commit")
    parser.add_argument("--reference-root", type=Path, help="With --legacy, hash reference files in a historical snapshot")
    args = parser.parse_args()
    if (args.reference_revision or args.reference_root) and not args.legacy:
        parser.error("Historical reference options require --legacy; v3 checks current repository bytes")
    if args.reference_revision and args.reference_root:
        parser.error("Choose --reference-revision or --reference-root")
    if args.legacy and args.source and args.source.resolve() != LEGACY_SOURCE.resolve():
        parser.error("--legacy selects the preserved v2 source; use current mode for another source")
    if args.legacy and args.browser_output and args.watch_page is None:
        parser.error("A legacy browser check requires --watch-page for separately generated legacy HTML")
    media_dir = args.media_dir or (LEGACY_DESTINATION if args.legacy else DESTINATION)
    source_path = args.source or (LEGACY_SOURCE if args.legacy else SOURCE)
    manifest, result = verify_files(media_dir, source_path, reference_revision=args.reference_revision,
                                    reference_root=args.reference_root)
    if args.decode_output:
        result["encoded_media"] = measure_media(media_dir / publication(manifest)["media_name"], manifest, args.ffmpeg, args.ffprobe, args.decode_output)
    if args.browser_output:
        if not args.url:
            parser.error("--browser-output requires --url")
        result["browser"] = browser_check(args.browser_output, args.url, manifest,
                                          media_dir=media_dir, watch_page=args.watch_page, source_path=source_path)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
