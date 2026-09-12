"""Attempt one strict Torch graph export; record support or the actual blocker."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import evaluate
import repro


def run_probe(prepared):
    args, native, manifest = prepared["args"], prepared["native"], prepared["manifest"]
    if manifest["checkpoint_provenance"]["class_order"] != "hash_bound":
        raise repro.ReproError("Graph export probe requires checkpoint-bound class meanings")
    runtime = evaluate.load_runtime(args.upstream)
    torch = runtime.torch
    model = runtime.classifier(native)
    checkpoint = torch.load(prepared["checkpoint"], map_location="cpu", weights_only=False)
    model.load_state_dict(checkpoint["model"], strict=True)
    model.to(native.device).eval()
    loader, _ = runtime.loader(native, str(Path(args.data) / "data-test.json"))
    sample = next(iter(loader))
    inputs = tuple(value[:1].to(native.device) for value in sample[:3])

    class InferenceOnly(torch.nn.Module):
        def __init__(self, classifier):
            super().__init__()
            self.classifier = classifier

        def forward(self, byte, size, interval):
            return self.classifier(byte, size, interval)["logits"]

    wrapper = InferenceOnly(model)
    with torch.inference_mode():
        eager = wrapper(*inputs)
    if not torch.isfinite(eager).all().item():
        raise repro.ReproError("Eager inference failed before the portability probe")
    result = {"probe": "torch.export.export(strict=True), fixed single-flow input shapes",
              "checkpoint_sha256": manifest["input_checkpoint"]["sha256"],
              "probe_sha256": repro.sha256_file(__file__), "eager_output_shape": list(eager.shape),
              "input_shapes": [list(value.shape) for value in inputs],
              "scope": "A Torch graph-capture probe; no ONNX, NPU compiler, SmartNIC or hardware deployment is implied"}
    try:
        exported = torch.export.export(wrapper, inputs, strict=True)
        target = Path(args.output) / "classifier-export.pt2"
        torch.export.save(exported, target)
        result.update(export_status="captured", export_sha256=repro.sha256_file(target))
    except Exception as error:
        result.update(export_status="unsupported_in_tested_path", error_type=type(error).__name__,
                      error_message=str(error)[:16000])
    manifest["argv"] = [sys.executable, str(Path(__file__).resolve()), *repro.execution_options(args)]
    manifest["evaluation_entrypoint"] = "tools/probe_export.py"
    return result


def main(argv=None):
    args = repro.cli_parser().parse_args(["evaluate", *(sys.argv[1:] if argv is None else argv)])
    return repro.run_stage(args, evaluation_fn=run_probe)


if __name__ == "__main__":
    raise SystemExit(main())
