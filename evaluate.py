"""Strict test-only evaluation using the pinned original classifier and engine."""

import math
import sys
from collections.abc import Mapping
from pathlib import Path
from types import SimpleNamespace

import repro


def serialize_metrics(value):
    nonfinite = []

    def convert(item, path):
        if item is None or isinstance(item, (str, bool, int)):
            return item
        if isinstance(item, float):
            if not math.isfinite(item):
                nonfinite.append(path or "/")
                return None
            return item
        if isinstance(item, Mapping):
            result = {}
            for key, child in item.items():
                if not isinstance(key, str):
                    raise repro.ReproError("Metric dictionary keys must be strings")
                escaped = key.replace("~", "~0").replace("/", "~1")
                result[key] = convert(child, path + "/" + escaped)
            return result
        if isinstance(item, (list, tuple)):
            return [convert(child, path + f"/{index}") for index, child in enumerate(item)]
        for method in ("tolist", "item"):
            function = getattr(item, method, None)
            if callable(function):
                converted = function()
                if converted is item:
                    break
                return convert(converted, path)
        raise repro.ReproError(f"Unsupported metric type at {path}: {type(item).__name__}")

    return convert(value, ""), nonfinite


def load_runtime(upstream):
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(Path(upstream).resolve() / "src"))
    import torch
    from util.loader_data import get_data_loader
    from util.loader_model import get_model_classifier
    from engine_mm import evaluate as engine_evaluate
    return SimpleNamespace(torch=torch, classifier=get_model_classifier,
                           loader=get_data_loader, engine=engine_evaluate)


def check_loader_mapping(idx2label, expected, observed_labels):
    if not isinstance(idx2label, Mapping):
        raise repro.ReproError("Native loader returned an invalid class mapping")
    normalized = {}
    inverse = {value: key for key, value in expected.items()}
    for index, name in idx2label.items():
        if isinstance(index, str) and index.isdecimal():
            index = int(index)
        if type(index) is not int or index in normalized or inverse.get(index) != name:
            raise repro.ReproError("Native loader class mapping conflicts with metadata")
        normalized[index] = name
    if not {int(label) for label in observed_labels}.issubset(normalized):
        raise repro.ReproError("Native loader mapping omits an observed test class")


def run_evaluation(prepared, runtime=None):
    args = prepared["args"]
    native = prepared["native"]
    manifest = prepared["manifest"]
    runtime = runtime or load_runtime(args.upstream)
    device = runtime.torch.device(native.device)
    model = runtime.classifier(native)
    checkpoint = runtime.torch.load(str(prepared["checkpoint"]), map_location="cpu", weights_only=False)
    if not isinstance(checkpoint, Mapping) or not isinstance(checkpoint.get("model"), Mapping):
        raise repro.ReproError("Checkpoint must contain a model state dictionary")
    model.load_state_dict(checkpoint["model"], strict=True)
    model = model.to(device)
    test_path = str(Path(args.data).resolve() / "data-test.json")
    loader, idx2label = runtime.loader(native, test_path)
    check_loader_mapping(idx2label, manifest["class_mapping"],
                         prepared["report"]["splits"]["test"]["class_counts"])
    raw_metrics = runtime.engine(loader, model, device, native)
    if not isinstance(raw_metrics, dict):
        raise repro.ReproError("Native evaluator did not return a test_state dictionary")
    metrics, paths = serialize_metrics(raw_metrics)
    return {"metrics": metrics, "nonfinite_metric_paths": paths,
            "checkpoint_sha256": manifest["input_checkpoint"]["sha256"],
            "class_mapping": manifest["class_mapping"],
            "checkpoint_provenance": manifest["checkpoint_provenance"],
            "evaluation_behavior": "Unmodified engine_mm.evaluate, including internal CUDA autocast"}


def main(argv=None):
    args = repro.cli_parser().parse_args(["evaluate", *(sys.argv[1:] if argv is None else argv)])
    return repro.run_stage(args, evaluation_fn=run_evaluation)


if __name__ == "__main__":
    raise SystemExit(main())
