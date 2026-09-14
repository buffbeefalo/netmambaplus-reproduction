"""Check client file identities and original flow evidence without media or Git history."""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import replay

LOCAL_DIRECTORIES = {".git", "upstream", ".evidence", "data", "datasets", "checkpoints", "runs",
                     "output", "outputs", "logs", "artifacts", "assets", ".venv", ".venv-cuda",
                     ".venv-gb10", "venv", "build-gb10", ".pytest_cache"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    def invalid(value):
        raise ValueError(f"Nonfinite JSON value: {value}")
    return json.loads(path.read_text(encoding="utf-8"), parse_constant=invalid)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def local(root, name):
    require(isinstance(name, str) and name and "\\" not in name and ":" not in name,
            f"Invalid inventory path: {name!r}")
    parts = PurePosixPath(name)
    require(not parts.is_absolute() and parts.as_posix() == name and
            all(p not in (".", "..") and p.lower() != ".git" for p in parts.parts), f"Unsafe path: {name}")
    path = root / name
    require(path.resolve().is_relative_to(root) and path.is_file() and not path.is_symlink(),
            f"Missing or unsafe file: {name}")
    parent = path.parent
    while parent != root:
        require(not parent.is_symlink(), f"Symlink directory: {name}")
        parent = parent.parent
    return path


def verify_inventory(root):
    root = Path(root).resolve()
    manifest = read(root / "CLIENT_MANIFEST.json")
    require(manifest.get("schema") == 1 and
            manifest.get("source_repository") == "https://github.com/buffbeefalo/netmambaplus-reproduction",
            "Invalid client provenance")
    for key, size in (("source_commit", 40), ("selection_sha256", 64), ("exporter_sha256", 64)):
        require(bool(re.fullmatch(r"[0-9a-f]{" + str(size) + "}", manifest.get(key, ""))),
                f"Invalid {key}")
    files = manifest["files"]
    require(isinstance(files, dict) and files, "Empty client inventory")
    for name, item in files.items():
        path = local(root, name)
        require(path.stat().st_size == item["bytes"] and digest(path) == item["sha256"],
                f"Delivered file differs from manifest: {name}")
    actual = set()
    for directory, directories, names in os.walk(root):
        base = Path(directory)
        directories[:] = [d for d in directories if d != "__pycache__" and
                           not (base == root and d in LOCAL_DIRECTORIES)]
        for d in directories:
            require(not (base / d).is_symlink(), f"Unexpected symlink directory: {base / d}")
        for name in names:
            if name.endswith((".pyc", ".pyo")):
                continue
            actual.add((base / name).relative_to(root).as_posix())
    require(actual == set(files) | {"CLIENT_MANIFEST.json"},
            "Client inventory differs: " + str(sorted(actual ^ (set(files) | {"CLIENT_MANIFEST.json"}))))
    return {"files": len(files), "source_commit": manifest["source_commit"]}


def close(left, right):
    require(math.isclose(left, right, rel_tol=1e-10, abs_tol=1e-10),
            f"Flow metric disagreement: {left} versus {right}")


def verify_flow(root):
    evidence = Path(root).resolve() / "docs/customer/evidence"
    index = read(evidence / "artifact-index.json")
    for item in index["files"]:
        path = local(evidence, item["path"])
        require(digest(path) == item["sha256"] and path.stat().st_size == item["bytes"],
                f"Flow evidence identity differs: {item['path']}")
    results = read(evidence / "results.json")
    require([row["seed"] for row in results["seeds"]] == [0, 1, 2] and results["demo_seed"] == 0,
            "Declared flow seeds differ")
    for row in results["seeds"]:
        folder = evidence / f"seed{row['seed']}"
        training = read(folder / "training/manifest.json")
        record = read(folder / "replay/predictions.json")
        require(row["completed_epochs"] == 120 and row["optimizer_updates_from_completed_batches"] == 7920,
                "Incomplete flow training budget")
        require(training["status"] == "succeeded" and
                training["produced_checkpoint"]["sha256"] == row["checkpoint_sha256"] == record["checkpoint_sha256"],
                "Training/prediction checkpoint mismatch")
        predictions = record["predictions"]
        metrics = replay.metrics_from_predictions([p["label"] for p in predictions],
                                                 [p["prediction"] for p in predictions], 6)
        require(metrics["support"] == [200, 200, 200, 41, 200, 200], "Unexpected flow test support")
        for p in predictions:
            require(len(p["logits"]) == len(p["scores"]) == 6 and
                    p["logits"][p["prediction"]] == max(p["logits"]), "Invalid flow prediction")
            for expected, actual in zip(replay.probabilities(p["logits"]), p["scores"]):
                close(expected, actual)
        for key in ("accuracy", "weighted_precision", "weighted_recall", "weighted_f1", "macro_f1"):
            close(metrics[key], row["metrics"][key])
        for kind in ("eval", "replay"):
            require(read(folder / kind / "metrics.json")["metrics"]["cm"] == metrics["confusion_matrix"],
                    "Strict flow evaluation differs from predictions")
        require(row["all_saved_weights_finite"] and row["export_tensors_bitwise_identical"] and
                row["real_flow_gradient_check"]["status"] == "passed", "Missing flow weight/gradient evidence")
    for key, summary in results["aggregate"].items():
        values = [row["metrics"][key] for row in results["seeds"]]
        close(summary["mean"], statistics.mean(values))
        close(summary["sample_standard_deviation"], statistics.stdev(values))
    for name in ("numerical-check.json", "rehearsal-numerical-check.json"):
        runtime = read(evidence / "runtime" / name)
        require(runtime["status"] == "passed" and len(runtime["checks"]) == 7 and
                all(c["passed"] for c in runtime["checks"]), "Incomplete native numerical evidence")
    return {"seeds": 3, "test_flows_per_seed": 1041, "indexed_artifacts": len(index["files"])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--inventory-only", action="store_true")
    args = parser.parse_args()
    try:
        result = {"status": "passed", "inventory": verify_inventory(args.root)}
        if not args.inventory_only:
            result["flow_evidence"] = verify_flow(args.root)
        result["scope"] = "Offline file/hash and saved-evidence checks; no new GPU execution or authenticity signature."
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print(f"Client verification failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
