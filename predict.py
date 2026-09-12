"""Predict classes for native flow records without requiring ground-truth labels."""

import argparse
import copy
import json
import sys
import tempfile
from pathlib import Path

import evaluate
import replay
import repro


def adapt_unlabeled(rows, mapping):
    mapping = repro.validate_mapping(mapping)
    if not isinstance(rows, list) or not rows or any(not isinstance(row, dict) for row in rows):
        raise ValueError("Input must be a nonempty JSON array of native flow objects")
    placeholder_name = next(name for name, index in mapping.items() if index == 0)
    return [{**copy.deepcopy(row), "label": 0, "name": placeholder_name} for row in rows]


def run_prediction(prepared, source, source_path, command):
    args, native, manifest = prepared["args"], prepared["native"], prepared["manifest"]
    if manifest["checkpoint_provenance"]["class_order"] != "hash_bound":
        raise repro.ReproError("Prediction requires a checkpoint-bound class mapping")
    manifest.update(argv=command, evaluation_entrypoint="predict.py", original_unlabeled_input=source,
                    predictor_sha256=repro.sha256_file(__file__),
                    native_adapter="Temporary loader-only label/name placeholders; targets are discarded before model forward; no accuracy is computed")
    runtime = evaluate.load_runtime(args.upstream)
    torch = runtime.torch
    if native.device != "cuda":
        raise repro.ReproError("This measured inference profile requires CUDA")
    from engine_mm import get_data_processors, get_model_forward_fn
    model = runtime.classifier(native)
    checkpoint = torch.load(prepared["checkpoint"], map_location="cpu", weights_only=False)
    model.load_state_dict(checkpoint["model"], strict=True)
    model.to(native.device).eval()
    loader, _ = runtime.loader(native, str(Path(args.data) / "data-test.json"))
    process = get_data_processors()[native.dataset_type]
    forward = get_model_forward_fn()[native.dataset_type]
    logits, indices = [], []
    with torch.inference_mode(), torch.autocast("cuda", dtype=torch.float16):
        for batch in loader:
            inputs = process(batch, torch.device(native.device))
            inputs.pop("targets")
            output = forward(model, inputs)["logits"]
            if not torch.isfinite(output).all().item():
                raise repro.ReproError("Nonfinite prediction logits")
            logits.extend(output.cpu().tolist())
            indices.extend(output.topk(1, dim=1).indices.flatten().cpu().tolist())
    if repro.sha256_file(source_path) != source["sha256"]:
        raise repro.ReproError("Input flow file changed during inference")
    inverse = {index: name for name, index in manifest["class_mapping"].items()}
    return {"kind": "unlabeled_native_flow_inference", "source": source,
            "checkpoint_sha256": manifest["input_checkpoint"]["sha256"],
            "class_mapping": manifest["class_mapping"],
            "predictions": [{"row": i, "prediction": index, "class_name": inverse[index],
                             "logits": values, "scores": replay.probabilities(values)}
                            for i, (index, values) in enumerate(zip(indices, logits))],
            "interpretation": "No ground-truth metrics. Softmax scores are uncalibrated. This does not perform live capture or blocking."}


def main(argv=None):
    supplied = sys.argv[1:] if argv is None else argv
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--flows", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--provenance", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=repro.DEFAULT_CONFIG)
    parser.add_argument("--upstream", type=Path, default=repro.DEFAULT_UPSTREAM)
    parser.add_argument("--num-workers", type=int, default=2)
    args = parser.parse_args(supplied)
    try:
        provenance_path = args.provenance or args.checkpoint.parent / "manifest.json"
        provenance, _ = repro.read_document(provenance_path)
        if not isinstance(provenance, dict):
            raise repro.ReproError("Checkpoint provenance must be a JSON object")
        binding_record = provenance.get("produced_checkpoint", provenance)
        if not isinstance(binding_record, dict):
            raise repro.ReproError("Checkpoint provenance has an invalid model binding")
        mapping = repro.validate_mapping(binding_record.get("class_mapping"))
        binding = repro.checkpoint_provenance(args.checkpoint, repro.sha256_file(args.checkpoint), mapping, provenance_path)
        if binding["class_order"] != "hash_bound":
            raise repro.ReproError("No hash-bound class mapping")
        rows, source = repro.read_document(args.flows)
        adapted = adapt_unlabeled(rows, mapping)
        with tempfile.TemporaryDirectory(prefix="netmamba-unlabeled-") as temporary:
            data = Path(temporary)
            repro.atomic_json(data / "metadata.json", {"name_to_idx": mapping})
            repro.atomic_json(data / "data-test.json", adapted)
            native_args = repro.cli_parser().parse_args([
                "evaluate", "--data", str(data), "--config", str(args.config),
                "--upstream", str(args.upstream), "--checkpoint", str(args.checkpoint),
                "--provenance", str(provenance_path), "--output", str(args.output),
                "--num-workers", str(args.num_workers)])
            return repro.run_stage(native_args, evaluation_fn=lambda prepared: run_prediction(
                prepared, source, args.flows, [sys.executable, str(Path(__file__).resolve()), *supplied]))
    except (OSError, ValueError) as error:
        print(f"Prediction failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
