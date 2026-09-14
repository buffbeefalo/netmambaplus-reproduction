"""Render the reviewed lesson with one timed neural speech request per scene."""

import argparse
import asyncio
import datetime
import hashlib
import json
import math
import re
import subprocess
import tempfile
import unicodedata
import wave
from pathlib import Path

from narrate_course_video import SOURCE, canonical, digest, load_source

CLIENT_VERSION = "7.2.7"
CONVERSION = {"sample_rate": 24000, "channels": 1, "codec": "pcm_s16le",
              "boundary": "WordBoundary", "caption_policy": "normalized-characters-v1:65:14"}


def normalized(text):
    return "".join(c for c in unicodedata.normalize("NFKC", text).casefold() if c.isalnum())


def fingerprint(text, voice, converter):
    return hashlib.sha256(canonical({"narration": text, "voice": voice,
                                    "conversion": CONVERSION, "converter": converter})).hexdigest()


def word_cues(text, events, seconds):
    """Only cut at boundaries shared by original words and service words."""
    if not math.isfinite(seconds) or seconds <= 0 or not events or not normalized(text):
        raise ValueError("Empty or invalid audio/word timing")
    ends, cursor, previous_end = {}, 0, 0
    for index, event in enumerate(events):
        offset, duration = event.get("offset"), event.get("duration")
        if (event.get("type") != "WordBoundary" or type(offset) is not int
                or type(duration) is not int or offset < 0 or duration <= 0
                or offset < previous_end - 1000 or (offset + duration) / 1e7 > seconds + 1/24000):
            raise ValueError("Invalid, overlapping or out-of-bounds word timing")
        if not isinstance(event.get("text"), str) or not normalized(event["text"]):
            raise ValueError("Empty service word alignment")
        cursor += len(normalized(event["text"]))
        ends[cursor] = index
        previous_end = offset + duration
    if normalized(text) != "".join(normalized(e["text"]) for e in events):
        raise ValueError("Incomplete normalized character alignment; original text was not rewritten")
    original_ends, cursor = {}, 0
    for match in re.finditer(r"\S+", text):
        cursor += len(normalized(match[0]))
        original_ends[cursor] = match.end()
    atoms, position, word = [], 0, 0
    for edge in sorted(ends.keys() & original_ends.keys()):
        last = ends[edge]
        atoms.append({"text": text[position:original_ends[edge]].strip(),
                      "start": events[word]["offset"] / 1e7,
                      "end": (events[last]["offset"] + events[last]["duration"]) / 1e7})
        position, word = original_ends[edge], last + 1
    cues, group = [], None
    for atom in atoms:
        if len(atom["text"]) > 65 or len(atom["text"].split()) > 14:
            raise ValueError("No safe service word boundary within caption limits")
        combined = group["text"] + " " + atom["text"] if group else atom["text"]
        if group and (len(combined) > 65 or len(combined.split()) > 14):
            cues.append(group)
            group = None
        group = dict(atom) if group is None else dict(group, text=combined, end=atom["end"])
        if re.search(r"[.!?][\"'”’\])]*$", group["text"]):
            cues.append(group)
            group = None
    if group:
        cues.append(group)
    return cues


def wave_info(path):
    with wave.open(str(path), "rb") as audio:
        if (audio.getnchannels(), audio.getsampwidth(), audio.getframerate(), audio.getcomptype()) != (1, 2, 24000, "NONE"):
            raise ValueError("Expected 24 kHz mono PCM16 WAV")
        samples = audio.getnframes()
        if samples <= 0 or len(audio.readframes(samples)) != samples * 2:
            raise ValueError("Empty or truncated WAV")
    return {"sample_rate": 24000, "samples": samples, "seconds": samples / 24000}


def cached_record(output, scene_id, identity, text):
    path = output / (scene_id + ".json")
    if not path.exists():
        return None
    record = json.loads(path.read_text())
    if record.get("input_sha256") != identity:
        return None
    for key, suffix in [("wav", ".wav"), ("mp3", ".mp3"), ("word_events", ".words.json")]:
        file = output / (scene_id + suffix)
        if (record.get(key) != file.name or not file.is_file()
                or record.get(key + "_sha256") != digest(file)):
            raise ValueError("Changed or incomplete cached " + key + ": " + scene_id)
    info = wave_info(output / record["wav"])
    events = json.loads((output / record["word_events"]).read_text())
    if (record.get("id") != scene_id or any(record.get(k) != v for k, v in info.items())
            or record.get("cues") != word_cues(text, events, info["seconds"])):
        raise ValueError("Invalid cached narration/caption record: " + scene_id)
    return record


async def stream_once(communication):
    # The pinned client's public stream() retries HTTP 403. Deliberately bypass it.
    chunks = list(communication.texts)
    if len(chunks) != 1 or communication.state["stream_was_called"]:
        raise ValueError("Each scene must fit one fresh, single service chunk")
    communication.state.update(stream_was_called=True, partial_text=chunks[0])
    async for event in communication._Communicate__stream():
        yield event


def write_json(path, value):
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def log_failure(output, source_hash, error, scene=None, identity=None):
    with (output / "failures.jsonl").open("a", encoding="utf-8") as log:
        log.write(json.dumps({"at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "scene": scene, "source_sha256": source_hash, "input_sha256": identity,
            "error_type": type(error).__name__, "error": str(error)[:2000],
            "automatic_retry": False}) + "\n")


async def render_scene(scene, voice, output, ffmpeg, identity, timeout):
    import edge_tts  # Optional network dependency; CPU tests/imports do not need it.
    if edge_tts.__version__ != CLIENT_VERSION or voice["client_version"] != CLIENT_VERSION:
        raise ValueError("Install the exact reviewed edge-tts client version")
    with tempfile.TemporaryDirectory(prefix=scene["id"] + "-", dir=output) as directory:
        stage = Path(directory)
        mp3, wav = stage / (scene["id"] + ".mp3"), stage / (scene["id"] + ".wav")
        events = []

        async def receive():
            communication = edge_tts.Communicate(scene["narration"], voice=voice["voice"],
                rate=voice["rate"], boundary="WordBoundary", connect_timeout=10, receive_timeout=60)
            with mp3.open("wb") as audio:
                async for event in stream_once(communication):
                    if event["type"] == "audio":
                        audio.write(event["data"])
                    else:
                        events.append(event)

        await asyncio.wait_for(receive(), timeout=timeout)
        if not mp3.is_file() or not mp3.stat().st_size:
            raise ValueError("Speech service returned empty audio")
        subprocess.run([str(ffmpeg), "-v", "error", "-xerror", "-i", str(mp3),
                        "-ar", "24000", "-ac", "1", "-c:a", "pcm_s16le", str(wav)],
                       check=True, capture_output=True, timeout=60)
        info = wave_info(wav)
        cues = word_cues(scene["narration"], events, info["seconds"])
        words = stage / (scene["id"] + ".words.json")
        write_json(words, events)
        record = {"id": scene["id"], "input_sha256": identity, **info, "cues": cues,
                  "word_alignment": "Complete NFKC/casefold alphanumeric character equality",
                  "timing_basis": "Service WordBoundary offsets; not independently verified human alignment",
                  "voice": voice, "voices_sha256": None,
                  "provider_model_revision": "unavailable", "conversion": CONVERSION}
        for key, path in [("wav", wav), ("mp3", mp3), ("word_events", words)]:
            record.update({key: path.name, key + "_sha256": digest(path)})
            path.replace(output / path.name)
        write_json(output / (scene["id"] + ".json"), record)
        return record


async def run(args):
    source_path = Path(getattr(args, "source", None) or SOURCE)
    source_hash = digest(source_path)
    source = load_source(source_path)
    if digest(source_path) != source_hash:
        raise ValueError("Source changed while loading")
    voice = source["voice"]
    if (voice.get("engine") != "edge-tts" or voice.get("client_version") != CLIENT_VERSION
            or voice.get("provider_model_revision") != "unavailable" or voice.get("synthetic") is not True):
        raise ValueError("Source must declare the reviewed neural client and unavailable cloud model pin")
    converter = {"ffmpeg_sha256": digest(args.ffmpeg)}
    scenes = [s for c in source["chapters"] for s in c["scenes"] if s["narration"]]
    if not scenes:
        raise ValueError("Source has no spoken scenes")
    names = [s["id"] for s in scenes]
    if len(set(names)) != len(names) or any(not re.fullmatch(r"[a-z0-9-]+", name) for name in names):
        raise ValueError("Scene names must be unique and path-safe")
    if args.only_scene:
        if args.only_scene not in names:
            raise ValueError("Unknown spoken scene: " + args.only_scene)
        scenes = [s for s in scenes if s["id"] == args.only_scene]
    args.output.mkdir(parents=True, exist_ok=True)
    records = []
    for scene in scenes:
        identity = fingerprint(scene["narration"], voice, converter)
        try:
            if digest(source_path) != source_hash:
                raise ValueError("Video source changed during synthesis; matching caches remain reusable")
            record = cached_record(args.output, scene["id"], identity, scene["narration"])
            cached = record is not None
            if record is None:
                record = await render_scene(scene, voice, args.output, args.ffmpeg, identity, args.timeout)
            records.append(record)
            print(f"{'Cached' if cached else 'Narrated'} {scene['id']}: {record['seconds']:.2f}s", flush=True)
        except Exception as error:
            log_failure(args.output, source_hash, error, scene["id"], identity)
            raise
    if digest(source_path) != source_hash:
        error = ValueError("Video source changed during synthesis; matching scene caches remain reusable")
        log_failure(args.output, source_hash, error)
        raise error
    result = {"schema_version": 1, "source_sha256": source_hash, "voice": voice,
              "voices_sha256": None, "provider_model_revision": "unavailable", "converter": converter,
              "complete": not bool(args.only_scene), "scenes": records}
    name = "narration-" + args.only_scene + ".json" if args.only_scene else "narration.json"
    write_json(args.output / name, result)
    print(f"{'Sample' if args.only_scene else 'Complete'}: {len(records)} scenes, "
          f"{sum(x['seconds'] for x in records):.1f}s raw speech", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ffmpeg", type=Path, required=True)
    parser.add_argument("--only-scene", help="Write one scene and a partial manifest, never narration.json")
    parser.add_argument("--timeout", type=float, default=180, help="Whole service request timeout in seconds")
    args = parser.parse_args()
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("--timeout must be positive and finite")
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
