"""Synthesize source-bound narration locally with Kokoro ONNX; no service calls."""

import argparse
import hashlib
import json
import os
import re
from pathlib import Path

from build_course import ROOT, TOKEN, fact_values, read

SOURCE = ROOT / "docs/customer/video-course-source.json"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def load_source():
    source = read(SOURCE)
    course = read(ROOT / "docs/customer/course-source.json")
    if hashlib.sha256(canonical(course["facts"])).hexdigest() != source["fact_bindings_sha256"]:
        raise ValueError("Video fact bindings have changed; review the video source first")
    values = fact_values(course)

    def resolve(value):
        if isinstance(value, str):
            return TOKEN.sub(lambda match: values[match[1]], value)
        if isinstance(value, list):
            return [resolve(item) for item in value]
        if isinstance(value, dict):
            return {key: resolve(item) for key, item in value.items()}
        return value

    return resolve(source)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--voices", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    os.environ.setdefault("OMP_NUM_THREADS", "4")
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "4")
    import numpy as np
    import soundfile as sf
    from kokoro_onnx import Kokoro

    source_hash = digest(SOURCE)
    source = load_source()
    voice = source["voice"]
    model_hash, voices_hash = digest(args.model), digest(args.voices)
    if model_hash != voice["model_sha256"]:
        raise ValueError("Kokoro model does not match the reviewed voice specification")
    args.output.mkdir(parents=True, exist_ok=True)
    engine = Kokoro(str(args.model), str(args.voices))
    records = []
    for chapter in source["chapters"]:
        for scene in chapter["scenes"]:
            if not scene["narration"]:
                continue
            identity = {"narration": scene["narration"], "voice": voice,
                        "voices_sha256": voices_hash, "sentence_gap_seconds": 0.28}
            fingerprint = hashlib.sha256(canonical(identity)).hexdigest()
            wav = args.output / (scene["id"] + ".wav")
            record_path = wav.with_suffix(".json")
            if record_path.exists() and wav.exists():
                previous = read(record_path)
                if previous["input_sha256"] == fingerprint and previous["wav_sha256"] == digest(wav):
                    records.append(previous)
                    print(f"Cached {scene['id']}: {previous['seconds']:.2f}s", flush=True)
                    continue
            chunks, cues, cursor = [], [], 0
            sentences = re.split(r"(?<=[.!?])\s+", scene["narration"].strip())
            sample_rate = None
            for index, sentence in enumerate(sentences):
                samples, rate = engine.create(sentence, voice=voice["voice"],
                                              speed=voice["speed"], lang="en-us")
                if sample_rate is not None and rate != sample_rate:
                    raise ValueError("Inconsistent audio sample rates")
                sample_rate = rate
                samples = np.asarray(samples, dtype=np.float32)
                if not samples.size or not np.isfinite(samples).all():
                    raise ValueError(f"Invalid synthesized audio: {scene['id']}")
                cues.append({"start": cursor / rate, "end": (cursor + len(samples)) / rate,
                             "text": sentence})
                chunks.append(samples)
                cursor += len(samples)
                if index != len(sentences) - 1:
                    gap = np.zeros(round(0.28 * rate), dtype=np.float32)
                    chunks.append(gap)
                    cursor += len(gap)
            audio = np.concatenate(chunks)
            sf.write(wav, audio, sample_rate, subtype="PCM_16")
            record = {"id": scene["id"], "input_sha256": fingerprint,
                      "wav": wav.name, "wav_sha256": digest(wav),
                      "sample_rate": sample_rate, "samples": len(audio),
                      "seconds": len(audio) / sample_rate, "cues": cues}
            record_path.write_text(json.dumps(record, indent=2) + "\n")
            records.append(record)
            print(f"Narrated {scene['id']}: {record['seconds']:.2f}s", flush=True)
    if digest(SOURCE) != source_hash:
        raise ValueError("Video source changed during synthesis; cached matching scenes can be reused")
    result = {"schema_version": 1, "source_sha256": source_hash,
              "voice": voice, "voices_sha256": voices_hash, "scenes": records}
    (args.output / "narration.json").write_text(json.dumps(result, indent=2) + "\n")
    print(f"Complete: {len(records)} scenes, {sum(x['seconds'] for x in records):.1f}s raw speech")


if __name__ == "__main__":
    main()
