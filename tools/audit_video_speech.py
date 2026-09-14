"""Offline, hash-bound ASR of every spoken passage in an encoded video.

Requires an already cached faster-whisper small.en model, numpy and ffmpeg.
ASR similarity is supplementary evidence, not pronunciation or human acceptance.
"""

import argparse
from dataclasses import dataclass
import difflib
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import time
import wave

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_RATE = 16000


def sha(path):
    """Hash large media without loading it into memory."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


@dataclass(frozen=True)
class BoundInputs:
    media: Path
    manifest_path: Path
    source_path: Path
    media_hash: str
    manifest_raw: bytes
    source_hash: str
    scenes: list


def finite_seconds(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a finite number")
    if not math.isfinite(value):
        raise ValueError(f"{label} must be a finite number")
    return value


def validate_inputs(media, manifest_path, expected_scenes, *, root=ROOT):
    """Bind media, manifest and the selected lesson before importing ASR."""
    if type(expected_scenes) is not int or expected_scenes <= 0:
        raise ValueError("expected scene count must be a positive integer")
    media, manifest_path = Path(media), Path(manifest_path)
    raw = manifest_path.read_bytes()
    manifest = json.loads(raw)
    media_name = manifest["media_name"]
    if media.name != media_name:
        raise ValueError("media filename differs from manifest media_name")
    artifact = manifest["artifacts"][media_name]
    media_hash = sha(media)
    if media_hash != artifact["sha256"] or media.stat().st_size != artifact["bytes"]:
        raise ValueError("media hash or size differs from manifest")
    source_path = Path(root) / manifest["source_path"]
    source_raw = source_path.read_bytes()
    source_hash = hashlib.sha256(source_raw).hexdigest()
    if source_hash != manifest["source_sha256"]:
        raise ValueError("source hash differs from manifest")
    source = json.loads(source_raw)
    expected = [(s["id"], s.get("narration", ""))
                for c in source["chapters"] for s in c["scenes"]]
    scenes = manifest["scenes"]
    if not isinstance(scenes, list) or not scenes:
        raise ValueError("manifest must contain scenes")
    duration = finite_seconds(manifest["scheduled_seconds"], "scheduled duration")
    seen, previous_end = set(), 0
    for scene in scenes:
        scene_id = scene["id"]
        if not isinstance(scene_id, str) or not scene_id or scene_id in seen:
            raise ValueError("scene IDs must be unique nonempty strings")
        seen.add(scene_id)
        if not isinstance(scene["narration"], str):
            raise ValueError(f"scene {scene_id} narration must be text")
        start = finite_seconds(scene["start"], f"scene {scene_id} start")
        end = finite_seconds(scene["end"], f"scene {scene_id} end")
        if not 0 <= start < end <= duration:
            raise ValueError(f"scene {scene_id} has invalid bounds")
        if start < previous_end - 1e-6:
            raise ValueError(f"scene {scene_id} overlaps the previous scene")
        previous_end = end
    if [(s["id"], s["narration"]) for s in scenes] != expected:
        raise ValueError("manifest scene IDs or narration differ from source")
    spoken = [s for s in scenes if s["narration"].strip()]
    if len(spoken) != expected_scenes:
        raise ValueError(f"expected {expected_scenes} spoken scenes; found {len(spoken)}")
    bound = BoundInputs(media, manifest_path, source_path, media_hash, raw,
                        source_hash, spoken)
    check_unchanged(bound)
    return bound


def check_unchanged(bound):
    """Never issue a completion receipt for inputs changed during the audit."""
    if sha(bound.media) != bound.media_hash:
        raise ValueError("media changed during audit")
    if bound.manifest_path.read_bytes() != bound.manifest_raw:
        raise ValueError("manifest changed during audit")
    if sha(bound.source_path) != bound.source_hash:
        raise ValueError("source changed during audit")


def check_audio_bounds(scenes, sample_count):
    for scene in scenes:
        start, end = (round(scene[key] * SAMPLE_RATE) for key in ("start", "end"))
        if not 0 <= start < end <= sample_count:
            raise ValueError(f"scene {scene['id']} exceeds decoded audio bounds")


def write_json(path, value):
    """Replace a progress receipt atomically so readers never see partial JSON."""
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n",
                         encoding="utf-8")
    temporary.replace(path)


def transcribe_scene(model, samples, scene):
    start = scene["start"]
    chunk = samples[round(start * SAMPLE_RATE):round(scene["end"] * SAMPLE_RATE)]
    segments, _ = model.transcribe(
        chunk, language="en", beam_size=5, word_timestamps=True,
        vad_filter=False, condition_on_previous_text=False)
    segments = list(segments)
    heard = " ".join(segment.text.strip() for segment in segments)
    words = [{"start": round(word.start + start, 3),
              "end": round(word.end + start, 3), "word": word.word,
              "probability": word.probability}
             for segment in segments for word in (segment.words or [])]
    expected_words = re.findall(r"[a-z0-9]+", scene["narration"].lower())
    heard_words = re.findall(r"[a-z0-9]+", heard.lower())
    return {
        "scene": scene["id"], "start": start, "end": scene["end"],
        "expected_narration": scene["narration"], "recognized_text": heard,
        "word_similarity": difflib.SequenceMatcher(
            a=expected_words, b=heard_words, autojunk=False).ratio(),
        "words": words,
        "segments": [{"start": round(segment.start + start, 3),
                      "end": round(segment.end + start, 3), "text": segment.text,
                      "avg_logprob": segment.avg_logprob,
                      "no_speech_prob": segment.no_speech_prob}
                     for segment in segments],
    }


def run_audit(args):
    bound = validate_inputs(args.media, args.manifest, args.expected_scenes)
    if not args.model_dir.is_dir():
        raise ValueError("model directory must already exist; downloads are disabled")
    # Optional heavy dependencies are unnecessary for the integrity checks above.
    import numpy as np
    from faster_whisper import WhisperModel

    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "manifest-input.json").write_bytes(bound.manifest_raw)
    per_scene = args.output / "scenes"
    per_scene.mkdir()
    audio = args.output / "encoded-audio-16k.wav"
    subprocess.run([
        args.ffmpeg, "-v", "error", "-xerror", "-nostdin", "-i", str(args.media),
        "-map", "0:a:0", "-ar", str(SAMPLE_RATE), "-ac", "1", "-c:a", "pcm_s16le",
        str(audio)], check=True)
    with wave.open(str(audio), "rb") as stream:
        if (stream.getframerate(), stream.getnchannels(), stream.getsampwidth()) != (SAMPLE_RATE, 1, 2):
            raise ValueError("decoded audio must be mono sixteen-bit PCM at sixteen kilohertz")
        samples = np.frombuffer(stream.readframes(stream.getnframes()), dtype="<i2")
        samples = samples.astype(np.float32) / 32768
    check_audio_bounds(bound.scenes, len(samples))
    model = WhisperModel("small.en", device="cpu", compute_type="int8", cpu_threads=8,
                         download_root=str(args.model_dir), local_files_only=True)
    rows, began = [], time.monotonic()
    target = args.output / "speech-audit.json"
    write_json(target, {"status": "running", "scenes": rows})
    for index, scene in enumerate(bound.scenes, 1):
        print(f"TRANSCRIBING {index}/{len(bound.scenes)} {scene['id']}", flush=True)
        row = transcribe_scene(model, samples, scene)
        rows.append(row)
        write_json(per_scene / f"{index:03d}.json", row)
        write_json(target, {"status": "running", "scenes": rows})
        print(scene["id"], round(row["word_similarity"], 3), row["recognized_text"], flush=True)
    check_unchanged(bound)
    record = {
        "status": "supplementary_automated_audit_complete",
        "model": "Systran/faster-whisper-small.en", "device": "CPU int8, eight threads",
        "local_files_only": True, "mp4_sha256": bound.media_hash,
        "source_sha256": bound.source_hash,
        "manifest_sha256": hashlib.sha256(bound.manifest_raw).hexdigest(),
        "decoded_audio_sha256": sha(audio), "helper_sha256": sha(Path(__file__)),
        "elapsed_seconds": time.monotonic() - began, "scenes": rows,
        "scope": f"Every one of {len(rows)} spoken passages transcribed independently from "
                 "the actual encoded media. ASR can misrecognize words/numbers and does not "
                 "establish human listening, pronunciation acceptance or timing acceptance.",
    }
    write_json(target, record)
    print("COMPLETE", len(rows), record["elapsed_seconds"], flush=True)
    return record


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("media", "manifest", "output", "model-dir"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--ffmpeg", required=True)
    parser.add_argument("--expected-scenes", type=int, required=True)
    args = parser.parse_args(argv)
    try:
        run_audit(args)
    except (OSError, ValueError, KeyError, TypeError, ImportError, RuntimeError,
            subprocess.CalledProcessError) as error:
        print(f"Speech audit failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
