"""Predict classes for native flow records without requiring ground-truth labels."""

import argparse
import copy
import json
import sys
import tempfile
from pathlib import Path

import calibration
import evaluate
import replay
import repro


def adapt_unlabeled(rows, mapping):
    mapping = repro.validate_mapping(mapping)
    if not isinstance(rows, list) or not rows or any(not isinstance(row, dict) for row in rows):
        raise ValueError("Input must be a nonempty JSON array of native flow objects")
    placeholder_name = next(name for name, index in mapping.items() if index == 0)
    return [{**copy.deepcopy(row), "label": 0, "name": placeholder_name} for row in rows]


def forward_without_targets(process, forward, model, batch, device):
    inputs = dict(process(batch, device))
    inputs.pop("targets")
    return forward(model, inputs)


def format_predictions(logits, indices, mapping, *, expected_rows,
                       temperature=None, threshold=None):
    mapping = repro.validate_mapping(mapping)
    if len(logits) != expected_rows or len(indices) != expected_rows or expected_rows <= 0:
        raise repro.ReproError("Native prediction row count differs from the input; no partial result is accepted")
    if threshold is not None:
        threshold = calibration.validate_threshold(threshold)
        if temperature is None:
            raise repro.ReproError("An abstention threshold requires calibration")
    inverse = {index: name for name, index in mapping.items()}
    result = []
    for row, (index, values) in enumerate(zip(indices, logits)):
        if len(values) != len(mapping) or type(index) is not int or index not in inverse:
            raise repro.ReproError("Prediction class dimensions conflict with the checkpoint mapping")
        scores = replay.probabilities(values)
        if values[index] != max(values):
            raise repro.ReproError("Native predicted class is not a maximum logit")
        record = {"row": row, "prediction": index, "class_name": inverse[index],
                  "logits": values, "scores": scores}
        if temperature is not None:
            scaled = calibration.calibrated_scores(values, temperature)
            record["calibrated_scores"] = scaled
            if threshold is not None:
                record["decision"] = "accept" if scaled[index] >= threshold else "defer"
        result.append(record)
    return result


def run_prediction(prepared, source, source_path, command, *, calibration_path=None, threshold=None):
    args, native, manifest = prepared["args"], prepared["native"], prepared["manifest"]
    if manifest["checkpoint_provenance"]["class_order"] != "hash_bound":
        raise repro.ReproError("Prediction requires a checkpoint-bound class mapping")
    manifest.update(argv=command, evaluation_entrypoint="predict.py", original_unlabeled_input=source,
                    predictor_sha256=repro.sha256_file(__file__),
                    native_adapter="Temporary loader-only label/name placeholders; targets are discarded before model forward; no accuracy is computed")
    manifest["inference_runtime"] = {"device_type": "cuda", "autocast_enabled": True,
                                     "autocast_dtype": "float16", "model_mode": "eval",
                                     "gradient_mode": "inference_mode"}
    artifact = artifact_file = None
    if calibration_path is not None:
        document, artifact_file = repro.read_document(calibration_path)
        artifact = calibration.validate_artifact(document, calibration.make_binding(manifest))
        manifest["calibration"] = {"file": artifact_file, "temperature": artifact["temperature"],
                                   "abstain_threshold": threshold,
                                   "implementation_sha256": repro.sha256_file(calibration.__file__)}
    elif threshold is not None:
        raise repro.ReproError("An abstention threshold requires calibration")
    if threshold is not None:
        threshold = calibration.validate_threshold(threshold)
    runtime = evaluate.load_runtime(args.upstream)
    torch = runtime.torch
    if native.device != "cuda":
        raise repro.ReproError("This measured inference profile requires CUDA")
    from engine_mm import get_data_processors, get_model_forward_fn
    model = runtime.classifier(native)
    checkpoint = torch.load(prepared["checkpoint"], map_location="cpu", weights_only=False)
    model.load_state_dict(checkpoint["model"], strict=True)
    model.to(native.device).eval()
    loader, idx2label = runtime.loader(native, str(Path(args.data) / "data-test.json"))
    evaluate.check_loader_mapping(idx2label, manifest["class_mapping"], [0])
    if not isinstance(loader.sampler, torch.utils.data.SequentialSampler) or loader.drop_last:
        raise repro.ReproError("Prediction requires sequential row order and the final partial batch")
    process = get_data_processors()[native.dataset_type]
    forward = get_model_forward_fn()[native.dataset_type]
    logits, indices = [], []
    with torch.inference_mode(), torch.autocast("cuda", dtype=torch.float16):
        for batch in loader:
            output = forward_without_targets(process, forward, model, batch, torch.device(native.device))["logits"]
            if not torch.isfinite(output).all().item():
                raise repro.ReproError("Nonfinite prediction logits")
            logits.extend(output.cpu().tolist())
            indices.extend(output.topk(1, dim=1).indices.flatten().cpu().tolist())
    if repro.sha256_file(source_path) != source["sha256"]:
        raise repro.ReproError("Input flow file changed during inference")
    if artifact_file is not None and repro.sha256_file(calibration_path) != artifact_file["sha256"]:
        raise repro.ReproError("Calibration artifact changed during inference")
    result = {"kind": "unlabeled_native_flow_inference", "source": source,
            "checkpoint_sha256": manifest["input_checkpoint"]["sha256"],
            "class_mapping": manifest["class_mapping"],
            "predictions": format_predictions(logits, indices, manifest["class_mapping"],
                expected_rows=prepared["report"]["splits"]["test"]["rows"],
                temperature=artifact["temperature"] if artifact is not None else None, threshold=threshold),
            "interpretation": "No ground-truth metrics. Softmax scores are uncalibrated. This does not perform live capture or blocking."}
    if artifact is not None:
        result["calibration"] = manifest["calibration"]
        result["interpretation"] = (
            "No ground-truth metrics. Original logits, scores and predicted classes are retained. "
            "calibrated_scores use a checkpoint-bound validation-fitted temperature; their usefulness depends on data compatibility. "
            "An optional accept/defer decision is a review policy, not attack blocking or a guarantee of correctness.")
    return result


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
    parser.add_argument("--calibration", type=Path, help="Validation-fitted calibration.json bound to this checkpoint and runtime")
    parser.add_argument("--abstain-threshold", type=float, help="Accept only when calibrated top-class score is at least this value in [0,1]")
    args = parser.parse_args(supplied)
    try:
        if args.abstain_threshold is not None:
            calibration.validate_threshold(args.abstain_threshold)
            if args.calibration is None:
                raise repro.ReproError("--abstain-threshold requires --calibration")
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
                prepared, source, args.flows, [sys.executable, str(Path(__file__).resolve()), *supplied],
                calibration_path=args.calibration, threshold=args.abstain_threshold))
    except (OSError, ValueError) as error:
        print(f"Prediction failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
