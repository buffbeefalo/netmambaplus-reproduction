"""Rebuild the display from immutable prediction records without GPU execution."""

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import replay
import repro


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    record = json.loads(args.predictions.read_text())
    mapping = repro.validate_mapping(record["class_mapping"])
    if record["kind"] != "recorded_native_test_inference":
        raise ValueError("Expected a saved native inference record")
    rows = record["predictions"]
    checked = replay.metrics_from_predictions([row["label"] for row in rows],
                                             [row["prediction"] for row in rows], len(mapping))
    if checked["confusion_matrix"] != record["independent_metrics"]["confusion_matrix"]:
        raise ValueError("Prediction inventory disagrees with its stored confusion matrix")
    args.output.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(args.predictions, args.output / "predictions.json")
    (args.output / "index.html").write_text(replay.render_html(record), encoding="utf-8")
    repro.atomic_json(args.output / "render-manifest.json", {
        "status": "rendered", "created_at": repro.timestamp(),
        "predictions_sha256": repro.sha256_file(args.predictions),
        "html_sha256": repro.sha256_file(args.output / "index.html"),
        "renderer_sha256": repro.sha256_file(ROOT / "replay.py"),
        "tool_sha256": repro.sha256_file(__file__),
        "checkpoint_sha256": record["checkpoint_sha256"],
        "scope": "Display-only rebuild; prediction record copied byte-for-byte and no model inference or retuning performed"}, overwrite=False)


if __name__ == "__main__":
    main()
