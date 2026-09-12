"""Measure synchronized model-only CUDA latency for the saved seed-0 classifier."""

import os
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import evaluate
import repro

WARMUP = 20
REPETITIONS = 100
BATCH_SIZES = (1, 16, 128)


def percentile(values, fraction):
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    left = int(position)
    return ordered[left] + (ordered[min(left + 1, len(ordered) - 1)] - ordered[left]) * (position - left)


def run_benchmark(prepared):
    args, native, manifest = prepared["args"], prepared["native"], prepared["manifest"]
    if manifest["checkpoint_provenance"]["class_order"] != "hash_bound":
        raise repro.ReproError("Benchmark requires a checkpoint-bound class mapping")
    runtime = evaluate.load_runtime(args.upstream)
    torch = runtime.torch
    if native.device != "cuda" or native.batch_size < max(BATCH_SIZES):
        raise repro.ReproError("This fixed benchmark needs CUDA and a native loader batch of at least 128")
    from engine_mm import get_data_processors, get_model_forward_fn
    device = torch.device(native.device)
    model = runtime.classifier(native)
    checkpoint = torch.load(str(prepared["checkpoint"]), map_location="cpu", weights_only=False)
    model.load_state_dict(checkpoint["model"], strict=True)
    model.to(device).eval()
    loader, mapping = runtime.loader(native, str(Path(args.data).resolve() / "data-test.json"))
    evaluate.check_loader_mapping(mapping, manifest["class_mapping"],
                                  prepared["report"]["splits"]["test"]["class_counts"])
    full = get_data_processors()[native.dataset_type](next(iter(loader)), device)
    forward = get_model_forward_fn()[native.dataset_type]
    inputs = {key: value[:128] for key, value in full.items() if key != "targets"}
    if next(iter(inputs.values())).shape[0] < max(BATCH_SIZES):
        raise repro.ReproError("Test data contains fewer than 128 flows")
    process_snapshot = subprocess.check_output([
        "nvidia-smi", "--query-compute-apps=pid,used_memory", "--format=csv,noheader"], text=True).strip()
    measurements = []
    with torch.inference_mode(), torch.autocast("cuda", dtype=torch.float16):
        for batch_size in BATCH_SIZES:
            selected = {key: value[:batch_size] for key, value in inputs.items()}
            for _ in range(WARMUP):
                forward(model, selected)
            elapsed = []
            for _ in range(REPETITIONS):
                torch.cuda.synchronize()
                started = time.perf_counter()
                forward(model, selected)
                torch.cuda.synchronize()
                elapsed.append((time.perf_counter() - started) * 1000)
            mean_ms = statistics.mean(elapsed)
            measurements.append({"batch_size": batch_size, "samples_ms": elapsed,
                                 "mean_ms": mean_ms, "p50_ms": percentile(elapsed, 0.5),
                                 "p95_ms": percentile(elapsed, 0.95), "min_ms": min(elapsed),
                                 "max_ms": max(elapsed), "flows_per_second_from_mean": batch_size * 1000 / mean_ms})
        batched = forward(model, inputs)["logits"]
        single = torch.cat([forward(model, {key: value[i:i+1] for key, value in inputs.items()})["logits"]
                            for i in range(128)])
    batch_prediction, single_prediction = batched.argmax(1), single.argmax(1)
    disagreement = (batch_prediction != single_prediction).nonzero().flatten().tolist()
    result = {"scope": "Model forward only; excludes capture, flow assembly, preprocessing, data loading and transfers",
              "checkpoint_sha256": manifest["input_checkpoint"]["sha256"],
              "benchmark_sha256": repro.sha256_file(__file__), "created_at": repro.timestamp(),
              "gpu": torch.cuda.get_device_name(), "compute_capability": list(torch.cuda.get_device_capability()),
              "precision": "FP32 parameters, CUDA float16 autocast, matching the native evaluator",
              "warmup_per_batch_size": WARMUP, "repetitions_per_batch_size": REPETITIONS,
              "timing": "perf_counter with torch.cuda.synchronize before and after each forward",
              "input_shapes": {key: list(value.shape) for key, value in inputs.items()},
              "own_pid": os.getpid(), "compute_process_snapshot": process_snapshot,
              "measurements": measurements,
              "batch_vs_single": {"rows": 128, "prediction_disagreement_rows_zero_based": disagreement,
                                  "agreement": (128 - len(disagreement)) / 128,
                                  "max_abs_logit_difference": (batched.float() - single.float()).abs().max().item(),
                                  "scope": "First 128 test flows, identical checkpoint, no threshold tuning"},
              "limitation": "Shared workstation; not a network line-rate, online IDS, SmartNIC, NPU or cross-hardware benchmark"}
    manifest["argv"] = [sys.executable, str(Path(__file__).resolve()), *repro.execution_options(args)]
    manifest["evaluation_entrypoint"] = "tools/benchmark.py"
    return result


def main(argv=None):
    args = repro.cli_parser().parse_args(["evaluate", *(sys.argv[1:] if argv is None else argv)])
    return repro.run_stage(args, evaluation_fn=run_benchmark)


if __name__ == "__main__":
    raise SystemExit(main())
