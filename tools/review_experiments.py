"""Verify completed runs, export model-only checkpoints and collect measured results."""

import argparse
import copy
import json
import math
import statistics
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import evaluate
import repro


def read(path):
    return json.loads(path.read_text())


def check_real_flow_gradients(runtime, model, manifest):
    torch = runtime.torch
    from engine_mm import get_data_processors, get_model_forward_fn
    native = SimpleNamespace(**manifest["native_args"])
    train_path = Path(native.data_path) / "data-train.json"
    loader, _ = runtime.loader(native, str(train_path))
    disposable = copy.deepcopy(model).to("cuda").train()
    inputs = get_data_processors()[native.dataset_type](next(iter(loader)), torch.device("cuda"))
    logits = get_model_forward_fn()[native.dataset_type](disposable, inputs)["logits"]
    loss = torch.nn.functional.cross_entropy(logits, inputs["targets"], label_smoothing=native.smoothing)
    loss.backward()
    gradients = [parameter.grad for parameter in disposable.parameters() if parameter.grad is not None]
    if not gradients or not torch.isfinite(loss).item() or not all(torch.isfinite(value).all().item() for value in gradients):
        raise ValueError("Real-flow backward check produced nonfinite loss or gradients")
    before = disposable.head.weight.detach().clone()
    optimizer = torch.optim.AdamW(disposable.parameters(), lr=.001, weight_decay=native.weight_decay)
    optimizer.step()
    changed = not torch.equal(before, disposable.head.weight)
    finite = all(torch.isfinite(parameter).all().item() for parameter in disposable.parameters())
    if not changed or not finite:
        raise ValueError("Real-flow optimizer check did not update a finite classifier")
    return {"status": "passed", "batch_rows": int(inputs["targets"].shape[0]), "loss": loss.item(),
            "parameters_with_finite_gradients": len(gradients), "all_updated_parameters_finite": finite,
            "head_updated": changed, "training_file_sha256": repro.sha256_file(train_path),
            "scope": "One additional training-only batch on a disposable copy of the selected classifier; not included in the 120-epoch budget and never used for test results or export"}


def review(seed, runs, pretrained, export):
    directory = runs / f"ciciot-ft-seed{seed}"
    manifest = read(directory / "manifest.json")
    if manifest["status"] != "succeeded" or manifest["native_args"]["seed"] != seed:
        raise ValueError(f"Seed {seed} has not completed successfully")
    if repro.sha256_file(pretrained) != manifest["input_checkpoint"]["sha256"]:
        raise ValueError("Transferred-parameter comparison uses a different pretraining checkpoint")
    for name, digest in manifest["harness_sha256"].items():
        if repro.sha256_file(ROOT / name) != digest:
            raise ValueError(f"Harness changed since training: {name}")
    train, native_test = read(directory / "train_stats.json"), read(directory / "test_stats.json")
    curve = [json.loads(line) for line in (directory / "log.txt").read_text().splitlines()]
    if train["epochs"] != 120 or [row["epoch"] for row in curve] != list(range(120)):
        raise ValueError(f"Seed {seed} did not log the complete declared budget")
    if any(not math.isfinite(value) for row in curve for value in row.values() if isinstance(value, float)):
        raise ValueError("Nonfinite training/validation history")
    best = max(curve, key=lambda row: row["valid_acc"])
    if best["epoch"] != train["best_epoch"] or best["valid_acc"] != train["best_valid_acc"]:
        raise ValueError("Saved validation selection disagrees with epoch history")
    strict = read(runs / f"ciciot-eval-seed{seed}" / "metrics.json")["metrics"]
    replay = read(runs / f"ciciot-replay-seed{seed}" / "predictions.json")
    for name in (f"ciciot-eval-seed{seed}", f"ciciot-replay-seed{seed}"):
        evaluation_manifest = read(runs / name / "manifest.json")
        if (evaluation_manifest["status"] != "succeeded"
                or evaluation_manifest["input_checkpoint"]["sha256"] != manifest["produced_checkpoint"]["sha256"]):
            raise ValueError(f"Evaluation is incomplete or uses another checkpoint: {name}")
    if not native_test["cm"] == strict["cm"] == replay["independent_metrics"]["confusion_matrix"]:
        raise ValueError("Native, fresh strict and independently recomputed test confusion matrices disagree")
    for name in ("acc", "weighted_pre", "weighted_rec", "weighted_f1"):
        if not math.isclose(native_test[name], strict[name], abs_tol=1e-10, rel_tol=1e-10):
            raise ValueError(f"Fresh-process metric disagreement: {name}")
    checkpoint_path = directory / "checkpoint-best.pth"
    checkpoint_hash = repro.sha256_file(checkpoint_path)
    if checkpoint_hash != manifest["produced_checkpoint"]["sha256"]:
        raise ValueError("Selected classifier differs from the recorded checkpoint hash")
    if replay["checkpoint_sha256"] != checkpoint_hash:
        raise ValueError("Prediction inventory belongs to another classifier")
    runtime = evaluate.load_runtime(manifest["request"]["upstream"])
    torch = runtime.torch
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    model = runtime.classifier(SimpleNamespace(**manifest["native_args"]))
    model.load_state_dict(checkpoint["model"], strict=True)
    if checkpoint["epoch"] != best["epoch"]:
        raise ValueError("Checkpoint epoch differs from validation selection")
    if any(not torch.isfinite(value).all().item() for value in checkpoint["model"].values()):
        raise ValueError("Nonfinite saved model weights")
    source = torch.load(pretrained, map_location="cpu", weights_only=True)["model"]
    changes = []
    for name, parameter in model.named_parameters():
        if name in source and tuple(parameter.shape) == tuple(source[name].shape):
            difference = (parameter.detach() - source[name]).abs().max().item()
            if difference > 0:
                changes.append({"parameter": name, "max_absolute_change": difference})
    if not changes:
        raise ValueError("No transferred encoder parameter changed during fine-tuning")
    batches = math.ceil(manifest["validation"]["splits"]["train"]["rows"] / manifest["native_args"]["batch_size"])
    steps = sorted({int(value["step"]) for value in checkpoint["optimizer"]["state"].values()})
    if steps != [(best["epoch"] + 1) * batches]:
        raise ValueError(f"Saved AdamW update counters disagree with completed batches: {steps}")
    gradient_check = check_real_flow_gradients(runtime, model, manifest)
    export.mkdir(parents=True, exist_ok=True)
    model_path = export / f"seed{seed}-classifier.pth"
    if model_path.exists():
        raise ValueError(f"Export already exists: {model_path}")
    torch.save({"model": checkpoint["model"]}, model_path)
    loaded = torch.load(model_path, map_location="cpu", weights_only=True)
    model.load_state_dict(loaded["model"], strict=True)
    if not all(torch.equal(value, loaded["model"][key]) for key, value in checkpoint["model"].items()):
        raise ValueError("Export changed model tensors")
    provenance = {"checkpoint_sha256": repro.sha256_file(model_path), "class_mapping": manifest["class_mapping"],
                  "source_checkpoint_sha256": checkpoint_hash, "source_manifest_sha256": repro.sha256_file(directory / "manifest.json"),
                  "pretraining_input_sha256": manifest["input_checkpoint"]["sha256"],
                  "upstream_commit": manifest["configuration"]["upstream"]["commit"],
                  "seed": seed, "selected_epoch_zero_based": best["epoch"],
                  "export": "Model tensors only, bitwise identical to the selected training checkpoint; no optimizer or executable Namespace payload",
                  "training_history": "Recorded downstream fine-tuning; full history of the authors' pretraining checkpoint remains unknown"}
    repro.atomic_json(export / f"seed{seed}-provenance.json", provenance, overwrite=False)
    return {"seed": seed, "completed_epochs": train["epochs"], "batches_per_epoch": batches,
            "optimizer_updates_from_completed_batches": train["epochs"] * batches,
            "selected_epoch_zero_based": best["epoch"], "selected_checkpoint_optimizer_steps": steps[0],
            "best_validation_accuracy": best["valid_acc"], "training_elapsed_seconds_shared_gpu": train["total_time"],
            "train_loss_first_epoch": curve[0]["train_loss"], "train_loss_last_epoch": curve[-1]["train_loss"],
            "metrics": replay["independent_metrics"], "fresh_strict_metrics_agree": True,
            "checkpoint_sha256": checkpoint_hash, "export_sha256": provenance["checkpoint_sha256"],
            "transferred_parameters_changed": changes, "all_saved_weights_finite": True,
            "real_flow_gradient_check": gradient_check,
            "export_tensors_bitwise_identical": True, "curve": curve}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=Path, default=ROOT / "runs")
    parser.add_argument("--pretrained", type=Path, required=True)
    parser.add_argument("--export", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.export.exists():
        parser.error("Choose new result and export destinations")
    rows = [review(seed, args.runs, args.pretrained, args.export) for seed in (0, 1, 2)]
    aggregate = {}
    for metric in ("accuracy", "weighted_f1", "macro_f1"):
        values = [row["metrics"][metric] for row in rows]
        aggregate[metric] = {"mean": statistics.mean(values), "sample_standard_deviation": statistics.stdev(values),
                             "min": min(values), "max": max(values)}
    result = {"created_at": repro.timestamp(), "reviewer_sha256": repro.sha256_file(__file__), "seeds": rows,
              "aggregate": aggregate, "demo_seed": 0, "paper_ciciot2022_table_iv": {"accuracy": 0.9750, "f1": 0.9750},
              "comparison_limit": "Source-based fine-tuning on a GB10 port; different batch/rate/runtime and opaque pretraining history prevent an exact paper reproduction claim.",
              "test_reuse": "Native final pass, strict fresh-process pass and replay use the same fixed test set to verify execution; they are not independent holdouts or model-selection rounds."}
    repro.atomic_json(args.output, result, overwrite=False)
    print(json.dumps({"aggregate": aggregate, "seeds": [row["seed"] for row in rows]}, indent=2))


if __name__ == "__main__":
    main()
