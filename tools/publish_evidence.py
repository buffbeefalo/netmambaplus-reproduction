"""Assemble the reviewed evidence and demo without copying raw data or weights."""

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import repro


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--model-export", type=Path, required=True)
    parser.add_argument("--build-record", type=Path, required=True)
    parser.add_argument("--recording", type=Path, required=True)
    parser.add_argument("--replay-display", type=Path, help="Optional display-only rebuild of the same prediction record")
    parser.add_argument("--runs", type=Path, default=ROOT / "runs")
    parser.add_argument("--output", type=Path, default=ROOT / "docs/customer/evidence")
    args = parser.parse_args()
    copies = [(args.results, "results.json"), (args.build_record, "runtime/build-report.json")]
    for source, target in [
        ("gb10-runtime-check.json", "runtime/numerical-check.json"),
        ("gb10-rehearsal-runtime-check.json", "runtime/rehearsal-numerical-check.json"),
        ("runtime-inventory-training.json", "runtime/training-environment.json"),
        ("runtime-inventory-rehearsal.json", "runtime/rehearsal-environment.json"),
        ("checkpoint-compatibility.json", "checkpoint-transfer.json"),
        ("uploaded-csv-profile.json", "uploaded-csv-profile.json"),
        ("customer-20260911-validation.json", "native-data-validation.json"),
        ("unlabeled-inference-agreement.json", "unlabeled-inference-agreement.json")]:
        copies.append((args.runs / source, target))
    for name in ("manifest.json", "native.log", "log.txt", "train_stats.json"):
        copies.append((args.runs / "ciciot-pt-functional" / name, "pretrain-functional/" + name))
    for seed in (0, 1, 2):
        for name in ("manifest.json", "native.log", "log.txt", "train_stats.json", "test_stats.json"):
            copies.append((args.runs / f"ciciot-ft-seed{seed}" / name, f"seed{seed}/training/{name}"))
        for kind, names in (("eval", ("manifest.json", "metrics.json")),
                            ("replay", ("manifest.json", "metrics.json", "predictions.json"))):
            for name in names:
                copies.append((args.runs / f"ciciot-{kind}-seed{seed}" / name, f"seed{seed}/{kind}/{name}"))
        copies.append((args.model_export / f"seed{seed}-provenance.json", f"seed{seed}/model-export-provenance.json"))
    for source, target in (("ciciot-benchmark-seed0", "benchmark"), ("ciciot-export-probe-seed0", "export-probe"),
                           ("ciciot-eval-rehearsal-seed0", "runtime/rehearsal-classifier-evaluation"),
                           ("ciciot-predict-seed0", "unlabeled-prediction")):
        for name in ("manifest.json", "metrics.json"):
            copies.append((args.runs / source / name, f"{target}/{name}"))
    copies.append((args.recording / "browser-check.json", "browser-check.json"))
    display = args.replay_display or args.runs / "ciciot-replay-seed0"
    if args.replay_display:
        if repro.sha256_file(display / "predictions.json") != repro.sha256_file(args.runs / "ciciot-replay-seed0/predictions.json"):
            raise ValueError("Display rebuild changed the original prediction record")
        copies.append((display / "render-manifest.json", "replay-render-manifest.json"))
    for source, target in copies:
        if not source.is_file():
            raise ValueError(f"Required evidence is missing: {source}")
        if source.name == "manifest.json" and json.loads(source.read_text())["status"] != "succeeded":
            raise ValueError(f"Required experiment did not succeed: {source}")
        if source.suffix not in (".json", ".log", ".txt"):
            raise ValueError(f"Unexpected evidence type: {source}")
    args.output.mkdir(parents=True, exist_ok=False)
    index = []
    for source, relative in copies:
        destination = args.output / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        index.append({"path": relative, "bytes": destination.stat().st_size,
                      "sha256": repro.sha256_file(destination), "original_filename": source.name,
                      "copy": "Exact bytes of the reviewed record; historical local paths may remain in commands"})
    repro.atomic_json(args.output / "artifact-index.json", {"created_at": repro.timestamp(),
                      "files": index, "scope": "Reviewed experiment evidence. No raw packet payloads, upstream source, original weights or private chat transcripts are copied."}, overwrite=False)
    demo = args.output.parent / "demo"
    demo.mkdir(exist_ok=False)
    for name in ("index.html", "predictions.json"):
        shutil.copyfile(display / name, demo / name)
    for name in ("recorded-demo.webm", "replay-screenshot.png", "replay-mobile.png", "browser-check.json"):
        shutil.copyfile(args.recording / name, demo / name)
    print(f"Published {len(copies)} evidence files and the recorded replay under {args.output.parent}")


if __name__ == "__main__":
    main()
