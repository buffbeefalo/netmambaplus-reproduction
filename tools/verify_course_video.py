"""Check video identities and captions; optionally decode and measure the actual MP4."""

import argparse
import html
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from build_course import ROOT, read
from build_course_video import DESTINATION, MEDIA_NAME, validate
from narrate_course_video import SOURCE, digest, load_source

OFFSETS = [0, 120, 360, 600, 780, 1020, 1260, 1500, 1620]


def check_probe(probe):
    duration = float(probe["format"]["duration"])
    if abs(duration - 1800) > 1:
        raise ValueError("Truncated or overlong video")
    streams = {s["codec_type"]: s for s in probe["streams"] if s["codec_type"] in ("video", "audio")}
    if set(streams) != {"video", "audio"}:
        raise ValueError("Both video and audio streams are required")
    video, audio = streams["video"], streams["audio"]
    if (video["codec_name"], video["width"], video["height"]) != ("h264", 1920, 1080) or audio["codec_name"] != "aac":
        raise ValueError("Unexpected video or audio encoding")
    if any(abs(float(s["duration"]) - 1800) > 1 or abs(float(s.get("start_time", 0))) > 0.1 for s in streams.values()):
        raise ValueError("A stream does not span the complete programme")
    starts = [float(c["start_time"]) for c in probe["chapters"]]
    if starts != OFFSETS or float(probe["chapters"][-1]["end_time"]) != 1800:
        raise ValueError("Embedded chapter markers have drifted")
    return {"seconds": duration, "streams": streams, "chapter_starts": starts}


def parse_time(value):
    hours, minutes, seconds = value.split(":")
    return 3600 * int(hours) + 60 * int(minutes) + float(seconds)


def check_vtt(text, expected):
    if not text.startswith("WEBVTT\n"):
        raise ValueError("Invalid WebVTT header")
    cues = []
    for block in text.strip().split("\n\n")[1:]:
        lines = block.splitlines()
        if not re.fullmatch(r"\d\d:\d\d:\d\d\.\d{3} --> \d\d:\d\d:\d\d\.\d{3}", lines[0]):
            raise ValueError("Invalid caption timestamp syntax")
        start, end = map(parse_time, lines[0].split(" --> "))
        if not (0 <= start < end <= 1800) or (cues and start < cues[-1]["end"] - 0.002):
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


def verify_files(directory=DESTINATION):
    manifest = read(directory / "media-manifest.json")
    source = load_source()
    validate(source)
    if manifest["source_sha256"] != digest(SOURCE):
        raise ValueError("Video narration source has changed")
    required = {MEDIA_NAME, "captions.vtt", "captions.srt", "transcript.md", "chapters.json", "poster.png"}
    if not required.issubset(manifest["artifacts"]):
        raise ValueError("Required video downloads are missing from the manifest")
    for name, identity in manifest["artifacts"].items():
        path = directory / name
        if Path(name).name != name or not path.is_file() or digest(path) != identity["sha256"] or path.stat().st_size != identity["bytes"]:
            raise ValueError(f"Video checksum mismatch: {name}")
    for reference in manifest["references"].values():
        if digest(ROOT / reference["path"]) != reference["sha256"]:
            raise ValueError(f"Video reference changed: {reference['path']}")
    if [c["start"] for c in manifest["chapters"]] != OFFSETS:
        raise ValueError("Incorrect chapter schedule")
    source_scenes = [s for c in source["chapters"] for s in c["scenes"]]
    if len(source_scenes) != len(manifest["scenes"]):
        raise ValueError("Missing video scenes")
    previous, pauses = 0, 0
    for source_scene, scene in zip(source_scenes, manifest["scenes"]):
        for key in source_scene:
            if scene[key] != source_scene[key]:
                raise ValueError(f"Narration/visual mismatch: {scene['id']}")
        if scene["start"] != previous or scene["end"] <= scene["start"]:
            raise ValueError("Scene schedule has a gap or overlap")
        previous = scene["end"]
        if scene["kind"] == "pause":
            pauses += scene["end"] - scene["start"]
        elif not 0.8 <= scene["tempo"] <= 1:
            raise ValueError("Speech was accelerated or slowed excessively")
    if previous != 1800 or pauses > 180 or pauses != manifest["practice_seconds"]:
        raise ValueError("Video or practice duration mismatch")
    if set(source["customer_questions"]) != {"tried", "learning", "inputs", "results", "demo", "hardware", "gaps"}:
        raise ValueError("Missing customer coverage")
    chapters = {c["id"] for c in source["chapters"]}
    if any(not ids or any(i not in chapters for i in ids) for ids in source["customer_questions"].values()):
        raise ValueError("Invalid customer coverage mapping")
    count = check_vtt((directory / "captions.vtt").read_text(encoding="utf-8"), manifest["caption_cues"])
    return manifest, {"status": "passed", "source_sha256": digest(SOURCE), "artifacts": manifest["artifacts"],
                      "scenes": len(manifest["scenes"]), "captions": count, "practice_seconds": pauses,
                      "scope": "Source, file identity and caption checks; encoded-media decode is a separate option."}


def measure_media(media, manifest, ffmpeg, ffprobe, output):
    output.mkdir(parents=True, exist_ok=True)
    command = [ffprobe, "-v", "error", "-show_streams", "-show_format", "-show_chapters", "-of", "json", str(media)]
    probe = json.loads(subprocess.check_output(command))
    result = check_probe(probe)
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


def browser_check(output, url):
    from playwright.sync_api import sync_playwright
    from urllib.request import urlopen
    from importlib.metadata import version
    if output.exists():
        raise ValueError("Use a fresh browser receipt directory")
    output.mkdir(parents=True)
    served = urlopen(url, timeout=30).read()
    if served != (DESTINATION / "index.html").read_bytes():
        raise ValueError("Watch page differs from the reviewed local file")
    errors, widths = [], []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1000}, accept_downloads=True)
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(url, wait_until="networkidle")
        page.wait_for_function("document.getElementById('player').readyState >= 1")
        if abs(page.eval_on_selector("#player", "v => v.duration") - 1800) > 1:
            raise ValueError("Browser media duration is incorrect")
        player = page.locator("#player")
        player.focus()
        page.keyboard.press("Space")
        page.wait_for_function("document.getElementById('player').currentTime > 1")
        decoded = player.evaluate("v => ({audio:v.webkitAudioDecodedByteCount, video:v.getVideoPlaybackQuality().totalVideoFrames, played_src:v.currentSrc})")
        if not decoded["audio"] or not decoded["video"]:
            raise ValueError("Browser did not decode both picture and audio")
        player.evaluate("v => v.pause()")
        page.locator("track").evaluate("t => t.track.mode='hidden'")
        page.wait_for_function("document.querySelector('track').readyState===2")
        caption_count = page.locator("track").evaluate("t => t.track.cues.length")
        if caption_count != len(read(DESTINATION / "media-manifest.json")["caption_cues"]):
            raise ValueError("Same-origin caption track is incomplete")
        for index, offset in enumerate(OFFSETS):
            page.locator(".chapter").nth(index).focus()
            page.keyboard.press("Enter")
            page.wait_for_function("t => !document.getElementById('player').seeking && Math.abs(document.getElementById('player').currentTime-t)<0.3", arg=offset)
        player.evaluate("v => {v.currentTime=1790;}")
        page.wait_for_function("!document.getElementById('player').seeking")
        player.focus()
        page.keyboard.press("Space")
        page.wait_for_function("document.getElementById('player').currentTime > 1791")
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
        if digest(downloaded) != digest(DESTINATION / MEDIA_NAME):
            raise ValueError("Browser MP4 download differs from the checked media")
        browser_version = browser.version
        browser.close()
    if errors:
        raise ValueError(f"Watch page errors: {errors}")
    result = {"status": "passed", "url": url, "completed_at": datetime.now(timezone.utc).isoformat(),
              "browser": f"Chromium {browser_version}; Playwright {version('playwright')}",
              "html_sha256": digest(DESTINATION / "index.html"), "mp4_sha256": digest(DESTINATION / MEDIA_NAME),
              "decoded_frames_and_audio_bytes": decoded, "caption_count": caption_count,
              "keyboard_playback": True, "keyboard_chapter_offsets": OFFSETS,
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
    args = parser.parse_args()
    manifest, result = verify_files()
    if args.decode_output:
        result["encoded_media"] = measure_media(DESTINATION / MEDIA_NAME, manifest, args.ffmpeg, args.ffprobe, args.decode_output)
    if args.browser_output:
        if not args.url:
            parser.error("--browser-output requires --url")
        result["browser"] = browser_check(args.browser_output, args.url)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
