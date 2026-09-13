"""Exercise the complete pinned classifier on synthetic schema fixtures using CUDA.

This checks execution, gradients, a weight update, and strict checkpoint reload.
It does not measure CICIoT2022 accuracy, reproduce training, or provide a CPU backend.
"""

import argparse
import hashlib
import importlib
import importlib.metadata
import json
import random
import sys
from pathlib import Path
from types import SimpleNamespace

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import repro

SAMPLES = 6
EXPECTED_MODEL = {"parameter_count": 1870080, "encoder_blocks": 4,
                  "embedding_width": 256, "tokens": 443, "classes": 6}
SCOPE = ("Synthetic schema fixtures only: one CUDA FP32 optimizer update and CUDA FP16 "
         "autocast inference with the complete pinned classifier. Random initialization; "
         "no real dataset, accuracy result, pretrained weights, or training-history claim.")


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def validate_recipe(config):
    expected = repro.load_config(repro.DEFAULT_CONFIG)
    for section in ("upstream", "common", "finetune"):
        if config.get(section) != expected[section]:
            raise ValueError(f"This check requires the complete configured CICIoT2022 {section} preset")
    if config.get("dataset", {}).get("expected_classes") != EXPECTED_MODEL["classes"]:
        raise ValueError("This check requires the configured six-class classifier")


def write_fixtures(directory):
    directory.mkdir(parents=True, exist_ok=False)
    mapping = {f"synthetic-class-{index}": index for index in range(SAMPLES)}
    rows = []
    for index in range(SAMPLES):
        packets = [" ".join(str((index * 41 + packet * 13 + byte) % 256)
                            for byte in range(7 if index == 0 else 320 + index))
                   for packet in range(index + 1)]
        count = 3 + 4 * index
        sizes = [-1, 1501] + [64 + (index + item) * 17 for item in range(count - 2)]
        intervals = [0.0] + [(index + item + 1) / 1000 for item in range(count - 1)]
        rows.append({"data": packets, "sizes": " ".join(map(str, sizes)),
                     "intervals": " ".join(map(str, intervals)), "label": index,
                     "name": f"synthetic-class-{index}", "num_packet": len(packets),
                     "pcap_file": f"synthetic-schema-fixture-{index}.pcap"})
    repro.atomic_json(directory / "metadata.json", {"name_to_idx": mapping,
                      "synthetic_only": True, "description": SCOPE}, overwrite=False)
    repro.atomic_json(directory / "data-test.json", rows, overwrite=False)
    return rows


def validate_build_binding(document, extensions):
    if document.get("status") != "built":
        raise ValueError("The supplied build report does not describe a completed build")
    recorded = document.get("extension_files", {})
    if set(recorded) != set(extensions) or any(
            recorded[name].get("sha256") != item["sha256"] for name, item in extensions.items()):
        raise ValueError("Installed extension hashes do not match the supplied build report")


def installed_mamba_sources(upstream):
    originals = upstream / "mamba-1p1p1/mamba_ssm"
    installed = Path(importlib.metadata.distribution("mamba-ssm").locate_file("mamba_ssm"))
    inventory = []
    for source in sorted(originals.rglob("*.py")):
        relative = source.relative_to(originals)
        actual = installed / relative
        require(actual.is_file() and source.read_bytes() == actual.read_bytes(),
                f"Installed Mamba Python source differs: {relative}")
        inventory.append({"file": relative.as_posix(), "sha256": repro.sha256_file(actual)})
    require(bool(inventory), "No pinned Mamba Python sources found")
    return {"directory": str(installed), "files": inventory}


def model_information(model):
    dimensions = {"parameter_count": sum(parameter.numel() for parameter in model.parameters()),
                  "encoder_blocks": len(model.encoder_blocks), "embedding_width": model.embed_dim,
                  "tokens": model.pos_embed.shape[1], "classes": model.num_classes}
    require(dimensions == EXPECTED_MODEL, f"Complete configured classifier differs: {dimensions}")
    mixers = [{"module": name, "bimamba_type": module.bimamba_type,
               "use_fast_path": module.use_fast_path, "d_model": module.d_model,
               "d_state": module.d_state, "d_conv": module.d_conv, "expand": module.expand}
              for name, module in model.named_modules() if hasattr(module, "bimamba_type")]
    require(len(mixers) == 4, "Expected four original Mamba mixers")
    return {**dimensions, "trainable_parameter_count": sum(
            parameter.numel() for parameter in model.parameters() if parameter.requires_grad),
            "factory": "util.loader_model.get_model_classifier", "class": type(model).__name__,
            "module": type(model).__module__, "active_mamba_modules": mixers}


def checked_forward(model, inputs, forward_model, torch):
    """Observe the real block inputs without replacing any model operation."""
    observed = {}

    def observer(name):
        def capture(module, values):
            observed[name] = {"shape": list(values[0].shape), "dtype": str(values[0].dtype)}
        return capture

    handles = [block.register_forward_pre_hook(observer(f"encoder_blocks.{index}"))
               for index, block in enumerate(model.encoder_blocks)]
    try:
        logits = forward_model(model, inputs)["logits"]
    finally:
        for handle in handles:
            handle.remove()
    require(len(observed) == 4 and all(item["shape"] == [SAMPLES, 443, 256]
                                      for item in observed.values()),
            f"Full 443-token sequence did not traverse all four blocks: {observed}")
    require(list(logits.shape) == [SAMPLES, 6] and bool(torch.isfinite(logits).all()),
            "Classifier logits must be finite with shape [6, 6]")
    return logits, observed


def execute(args):
    output, upstream = args.output.resolve(), args.upstream.resolve()
    if output == upstream or upstream in output.parents:
        raise ValueError("Choose an output directory outside the pinned upstream tree")
    output.mkdir(parents=True, exist_ok=False)
    manifest_path = output / "manifest.json"
    record = {"schema_version": 1, "status": "running", "stage": "configuration",
              "created_at": repro.timestamp(), "synthetic_only": True, "scope": SCOPE,
              "request": {key: str(value) if isinstance(value, Path) else value
                          for key, value in vars(args).items()}, "checks": {},
              "tool_sha256": repro.sha256_file(Path(__file__)), "seed": args.seed}

    def stage(name):
        record.update(stage=name, updated_at=repro.timestamp())
        repro.atomic_json(manifest_path, record)

    stage("configuration")
    try:
        if not 0 <= args.seed < 2**32 or args.device < 0:
            raise ValueError("Seed must be in [0, 2**32) and CUDA device index must be nonnegative")
        config = repro.load_config(args.config)
        validate_recipe(config)
        record["config"] = {"file": str(args.config.resolve()), "sha256": repro.sha256_file(args.config)}
        record["harness_sha256"] = {name: repro.sha256_file(ROOT / name)
                                    for name in ("repro.py", "tools/build_cuda.py", "tools/build_gb10.py")}
        stage("source_verification")
        record["upstream"] = repro.verify_upstream(upstream, config)
        repro.check_single_process(config)
        record["checks"]["upstream_pin_and_clean_sources"] = True

        stage("synthetic_inputs_and_native_arguments")
        directory = output / "synthetic-inputs"
        rows = write_fixtures(directory)
        validation = repro.validate_data(directory, "evaluate", config)
        checkpoint = output / "checkpoint-synthetic.pth"
        request = SimpleNamespace(command="evaluate", upstream=upstream, data=directory, output=output,
                                  checkpoint=checkpoint, device=f"cuda:{args.device}", num_workers=0,
                                  seed=args.seed)
        native, native_argv, _, _ = repro.build_native(request, config, validation)
        record["native_arguments"] = vars(native).copy()
        record["native_argv"] = native_argv
        record["native_argument_scope"] = (
            "Original fine-tuning parser resolved through repro.build_native. The checkpoint path is "
            "an output placeholder; no initialization checkpoint is loaded. The original epoch loop is "
            "not launched. Smoke overrides: six-row loader batch, zero workers, requested device/seed.")
        record["inputs"] = {"synthetic_only": True, "validation": validation,
                            "raw_sizes": [{"packet_count": len(row["data"]),
                                           "bytes_per_packet": [len(packet.split()) for packet in row["data"]],
                                           "sizes_count": len(row["sizes"].split()),
                                           "intervals_count": len(row["intervals"].split())} for row in rows],
                            "smoke_batch_size": SAMPLES, "configured_batch_size": native.batch_size}

        stage("runtime_and_extension_verification")
        record["installed_mamba_python_sources"] = installed_mamba_sources(upstream)
        import torch
        import numpy as np

        require(torch.cuda.is_available(), "CUDA is required; this tool has no CPU fallback")
        require(args.device < torch.cuda.device_count(), "Selected CUDA device is not visible")
        torch.cuda.set_device(args.device)
        device = torch.device(f"cuda:{args.device}")
        runtime = repro.runtime_information()
        runtime.update(torch_cuda=torch.version.cuda, cuda_device_index=args.device,
                       cuda_device=torch.cuda.get_device_name(device),
                       compute_capability=list(torch.cuda.get_device_capability(device)),
                       torch_compiled_architectures=torch.cuda.get_arch_list(),
                       python_executable_sha256=repro.sha256_file(Path(sys.executable).resolve()),
                       cudnn_benchmark=torch.backends.cudnn.benchmark,
                       matmul_allow_tf32=torch.backends.cuda.matmul.allow_tf32,
                       cudnn_allow_tf32=torch.backends.cudnn.allow_tf32)
        record["runtime"] = runtime
        record["runtime_sha256"] = hashlib.sha256(json.dumps(runtime, sort_keys=True).encode()).hexdigest()
        extensions = {}
        for name in ("causal_conv1d_cuda", "selective_scan_cuda"):
            module = importlib.import_module(name)
            path = Path(module.__file__)
            extensions[name] = {"file": str(path), "bytes": path.stat().st_size,
                                "sha256": repro.sha256_file(path)}
        record["compiled_extensions"] = extensions
        record["build_report"] = None
        if args.build_report is not None:
            document = json.loads(args.build_report.read_text(encoding="utf-8"))
            validate_build_binding(document, extensions)
            record["build_report"] = {"file": str(args.build_report.resolve()),
                                      "sha256": repro.sha256_file(args.build_report),
                                      "builder_sha256": document.get("builder_sha256"),
                                      "requested_extension_target": document.get("requested_extension_target"),
                                      "extension_hashes_match": True}
        record["builder_hash_scope"] = (
            "harness_sha256 records builder source files observed at check time. Only a supplied "
            "completed build report binds installed extension bytes to recorded build provenance.")
        record["checks"]["installed_mamba_matches_verified_upstream"] = True

        stage("native_loader_and_complete_classifier")
        random.seed(args.seed)
        np.random.seed(args.seed)
        torch.manual_seed(args.seed)
        torch.cuda.manual_seed_all(args.seed)
        sys.path.insert(0, str(upstream / "src"))
        from util.loader_data import get_data_loader
        from util.loader_model import get_model_classifier
        from util.lr_decay import param_groups_lrd
        from engine_mm import get_data_processors, get_model_forward_fn

        for name, relative in {"util.loader_data": "src/util/loader_data.py",
                               "util.loader_model": "src/util/loader_model.py",
                               "util.lr_decay": "src/util/lr_decay.py", "engine_mm": "src/engine_mm.py",
                               "models.models_net_mamba_fuse3": "src/models/models_net_mamba_fuse3.py"}.items():
            require(Path(sys.modules[name].__file__).resolve() == (upstream / relative).resolve(),
                    f"Imported native module is outside its verified source location: {name}")
        installed = Path(record["installed_mamba_python_sources"]["directory"]).resolve()
        for name, module in list(sys.modules.items()):
            if name == "mamba_ssm" or name.startswith("mamba_ssm."):
                filename = getattr(module, "__file__", None)
                require(filename is not None and Path(filename).resolve().is_relative_to(installed),
                        f"Imported Mamba module is outside the verified installation: {name}")

        loader, labels = get_data_loader(native, str(directory / "data-test.json"),
                                        batch_size=SAMPLES, random_sampler=False)
        require(labels == {value: key for key, value in validation["class_mapping"].items()},
                "Original loader class mapping differs from synthetic metadata")
        require(len(loader) == 1, "Synthetic fixture must produce exactly one complete batch")
        inputs = get_data_processors()[native.dataset_type](next(iter(loader)), device)
        shapes = {key: list(value.shape) for key, value in inputs.items()}
        require(shapes == {"x_byte": [SAMPLES, 1, 1, 1600], "x_size": [SAMPLES, 20],
                           "x_interval": [SAMPLES, 20], "targets": [SAMPLES]},
                f"Original loader produced unexpected input shapes: {shapes}")
        require(all(bool(torch.isfinite(value).all()) for value in inputs.values()),
                "Original loader produced nonfinite inputs")
        record["inputs"].update(tensor_shapes=shapes, tensor_dtypes={
            key: str(value.dtype) for key, value in inputs.items()}, loader="util.loader_data.get_data_loader")
        model = get_model_classifier(native).to(device)
        record["model"] = model_information(model)
        require(all(parameter.dtype == torch.float32 for parameter in model.parameters()),
                "Native FP32 training requires FP32 model parameters")
        record["loaded_upstream_source_sha256"] = {}
        for module in list(sys.modules.values()):
            filename = getattr(module, "__file__", None)
            if filename and Path(filename).resolve().is_relative_to(upstream):
                path = Path(filename).resolve()
                record["loaded_upstream_source_sha256"][str(path.relative_to(upstream))] = repro.sha256_file(path)
        record["checks"]["native_loader_and_complete_model_dimensions"] = True

        stage("fp32_training_step")
        model.train()
        forward_model = get_model_forward_fn()[native.dataset_type]
        groups = param_groups_lrd(model, native.weight_decay, model.no_weight_decay(), native.layer_decay)
        learning_rate = native.lr if native.lr is not None else native.blr * SAMPLES * native.accum_iter / 256
        for group in groups:
            group["lr"] = learning_rate * group["lr_scale"]
        optimizer = torch.optim.AdamW(groups, lr=learning_rate)
        record["optimizer"] = {"class": "torch.optim.AdamW", "group_factory": "util.lr_decay.param_groups_lrd",
                               "learning_rate": learning_rate, "step_count": 0,
                               "parameter_group_learning_rates": [group["lr"] for group in optimizer.param_groups],
                               "weight_decay": native.weight_decay, "layer_decay": native.layer_decay,
                               "scope": "One standalone step: native AdamW groups and layer scales; base rate "
                                        "scaled to six synthetic rows. No warmup or epoch schedule is simulated."}
        optimizer.zero_grad(set_to_none=True)
        logits, trace = checked_forward(model, inputs, forward_model, torch)
        require(logits.dtype == torch.float32, "Training logits must use native FP32 without autocast")
        loss = torch.nn.CrossEntropyLoss(label_smoothing=native.smoothing)(logits, inputs["targets"])
        require(bool(torch.isfinite(loss)), "Training loss is nonfinite")
        loss.backward()
        gradients, before = {}, {}
        for name, parameter in model.named_parameters():
            if not parameter.requires_grad:
                continue
            require(parameter.grad is not None, f"Missing model parameter gradient: {name}")
            require(bool(torch.isfinite(parameter.grad).all()), f"Nonfinite model parameter gradient: {name}")
            gradients[name] = {"elements": parameter.numel(), "max_abs_gradient": float(parameter.grad.abs().max())}
            before[name] = parameter.detach().clone()
        active = [name for name, value in gradients.items() if value["max_abs_gradient"] > 0]
        required_prefixes = ["head."] + [f"encoder_blocks.{index}." for index in range(4)]
        require(all(any(name.startswith(prefix) for name in active) for prefix in required_prefixes),
                "Nonzero gradients must reach the head and every encoder block")
        optimizer.step()
        torch.cuda.synchronize(device)
        changed = []
        for name, parameter in model.named_parameters():
            require(bool(torch.isfinite(parameter).all()), f"Nonfinite parameter after optimizer step: {name}")
            if name in before and not torch.equal(before[name], parameter.detach()):
                changed.append(name)
        require(all(any(name.startswith(prefix) for name in changed) for prefix in required_prefixes),
                "Optimizer step must change the head and every encoder block")
        record["training"] = {"dtype": str(logits.dtype), "autocast": False, "loss": float(loss.detach()),
                              "label_smoothing": native.smoothing, "block_inputs": trace,
                              "parameter_gradients": gradients, "changed_parameter_names": changed,
                              "parameter_tensors_with_gradients": len(gradients),
                              "changed_parameter_tensors": len(changed),
                              "elements_in_changed_parameter_tensors": sum(before[name].numel() for name in changed)}
        record["optimizer"]["step_count"] = 1
        record["checks"].update(finite_fp32_loss=True, finite_parameter_gradients=True,
                                 nonzero_gradient_each_encoder_and_head=True, real_optimizer_update=True)
        optimizer.zero_grad(set_to_none=True)
        del before, logits, loss

        stage("checkpoint_save_and_strict_reload")
        state = {name: value.detach().cpu() for name, value in model.state_dict().items()}
        with checkpoint.open("xb") as stream:
            torch.save({"model": state, "synthetic_only": True, "scope": SCOPE}, stream)
        saved = torch.load(checkpoint, map_location="cpu", weights_only=True)
        reloaded = get_model_classifier(native)
        result = reloaded.load_state_dict(saved["model"], strict=True)
        require(not result.missing_keys and not result.unexpected_keys, "Strict reload reported incompatible keys")
        require(all(torch.equal(value, reloaded.state_dict()[name]) for name, value in state.items()),
                "Strictly reloaded state differs from saved tensors")
        require(model_information(reloaded) == record["model"], "Reloaded model architecture differs")
        reloaded.to(device)
        record["checkpoint"] = {"file": checkpoint.name, "sha256": repro.sha256_file(checkpoint),
                                "bytes": checkpoint.stat().st_size, "state_tensors": len(state),
                                "strict": True, "weights_only_load": True, "synthetic_only": True,
                                "scope": "One synthetic optimizer step from random initialization; model weights only, "
                                         "not a published checkpoint or resumable training state."}
        record["checks"]["strict_checkpoint_reload_and_identical_state"] = True

        stage("autocast_inference")
        model.eval()
        reloaded.eval()
        with torch.inference_mode(), torch.autocast("cuda", dtype=torch.float16):
            reference, original_trace = checked_forward(model, inputs, forward_model, torch)
            actual, reloaded_trace = checked_forward(reloaded, inputs, forward_model, torch)
        torch.testing.assert_close(actual, reference, rtol=0, atol=0)
        require(actual.dtype == torch.float16, "CUDA autocast inference logits must use FP16")
        scores = actual.float().softmax(dim=-1)
        require(bool(torch.isfinite(scores).all()) and bool(((scores >= 0) & (scores <= 1)).all()),
                "Synthetic inference scores must be finite and in [0, 1]")
        torch.testing.assert_close(scores.sum(-1), torch.ones(SAMPLES, device=device), rtol=1e-6, atol=1e-6)
        record["inference"] = {"autocast": "cuda:float16", "logits_dtype": str(actual.dtype),
                               "logits_shape": list(actual.shape), "class_order": [labels[i] for i in range(6)],
                               "logits": actual.float().cpu().tolist(), "class_scores": scores.cpu().tolist(),
                               "predicted_class_indices": scores.argmax(-1).cpu().tolist(),
                               "score_scope": "Softmax outputs for synthetic fixtures; no calibration or accuracy claim.",
                               "block_inputs_before_reload": original_trace,
                               "block_inputs_after_reload": reloaded_trace,
                               "reload_max_abs_logit_difference": float((actual - reference).abs().max())}
        record["checks"].update(finite_autocast_inference=True, normalized_six_class_scores=True,
                                 identical_inference_after_strict_reload=True)
        torch.cuda.synchronize(device)
        repro.verify_upstream(upstream, config)
        record["checks"]["upstream_unchanged_after_execution"] = True
        record["status"] = "passed"
        stage("complete")
        print(f"Passed complete 1,870,080-parameter CUDA classifier check on synthetic fixtures: {manifest_path}")
        return 0
    except (Exception, KeyboardInterrupt) as error:
        record.update(status="failed", failed_stage=record["stage"],
                      error=f"{type(error).__name__}: {error}", updated_at=repro.timestamp())
        repro.atomic_json(manifest_path, record)
        print(f"Complete-model check failed at {record['stage']}: {error}. See {manifest_path}", file=sys.stderr)
        return 130 if isinstance(error, KeyboardInterrupt) else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="New output directory outside pinned upstream")
    parser.add_argument("--upstream", type=Path, default=repro.DEFAULT_UPSTREAM)
    parser.add_argument("--config", type=Path, default=repro.DEFAULT_CONFIG,
                        help="Configuration preserving the complete recorded common and finetune preset")
    parser.add_argument("--device", type=int, default=0, help="Index among visible CUDA devices")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--build-report", type=Path, help="Optional completed build_cuda.py report to bind extension hashes")
    args = parser.parse_args()
    try:
        return execute(args)
    except (OSError, ValueError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    raise SystemExit(main())
