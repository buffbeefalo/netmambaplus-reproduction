"""Fit temperature on data-valid.json using CUDA and matching recorded data evidence.

Only metadata.json and data-valid.json are opened from the data directory. The
separate data-evidence JSON must bind those exact bytes, class order and row counts.
Recorded overlap claims are reused with attribution; no train/test split is read
and no independent holdout, safety level or accuracy improvement is established.
"""

import argparse
import copy
import hashlib
import json
import math
import sys
import time
from collections import Counter
from collections.abc import Mapping
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import calibration
import evaluate
import repro

DEFAULT_EVIDENCE = ROOT / "docs/customer/evidence/native-data-validation.json"


def validate_validation_data(directory, config, evidence_path):
    """Return a dedicated validation report and original rows, without test access."""
    directory = Path(directory).resolve()
    metadata, metadata_info = repro.read_document(directory / "metadata.json")
    rows, valid_info = repro.read_document(directory / "data-valid.json")
    evidence, evidence_info = repro.read_document(evidence_path)
    if not isinstance(metadata, dict):
        raise repro.ReproError("metadata.json must be an object")
    mapping = repro.validate_mapping(metadata.get("name_to_idx"), config["dataset"].get("expected_classes"))
    size_key = repro.stage_parameters(config, "evaluate").get("size_key", "sizes")
    if size_key not in ("sizes", "signed_sizes"):
        raise repro.ReproError("Unsupported native size key")
    if not isinstance(rows, list) or not rows:
        raise repro.ReproError("data-valid.json must be a nonempty array of native flows")
    counts, fingerprints, identifiers = Counter(), [], []
    for index, row in enumerate(rows):
        try:
            identifier, fingerprint = repro.validate_record(row, mapping, size_key)
        except ValueError as error:
            raise repro.ReproError(f"data-valid.json record {index}: {error}") from error
        counts[str(row["label"])] += 1
        fingerprints.append(fingerprint)
        if identifier is not None:
            identifiers.append(identifier)
    try:
        if (evidence["class_mapping"] != mapping or evidence["size_key"] != size_key
                or evidence["splits"]["valid"]["rows"] != len(rows)
                or evidence["splits"]["valid"]["class_counts"] != dict(counts)):
            raise repro.ReproError("Data evidence does not match validation rows or class mapping")
        if type(evidence["splits"]["valid"]["rows"]) is not int:
            raise repro.ReproError("Data evidence has a malformed row count")
        for name, info in (("metadata.json", metadata_info), ("data-valid.json", valid_info)):
            expected = evidence["files"][name]
            if expected["sha256"] != info["sha256"] or expected["bytes"] != info["bytes"]:
                raise repro.ReproError(f"Data evidence hash or byte count differs for {name}")
        overlaps = evidence.get("raw_input_overlaps", {})
        reused = {"known_train_validation_overlap_rows": overlaps.get("train_valid", {}).get("right_rows"),
                  "known_validation_test_overlap_rows": overlaps.get("valid_test", {}).get("left_rows")}
        if any(value is not None and (type(value) is not int or not 0 <= value <= len(rows))
               for value in reused.values()):
            raise repro.ReproError("Invalid recorded validation overlap counts")
    except (KeyError, TypeError, AttributeError) as error:
        raise repro.ReproError("Data evidence must bind metadata and validation identities/counts") from error
    report = {"stage": "calibrate", "class_mapping": mapping, "size_key": size_key,
              "files": {"metadata.json": metadata_info, "data-valid.json": valid_info,
                        "data-evidence.json": evidence_info},
              "splits": {"valid": {"rows": len(rows), "class_counts": dict(counts),
                                    "unique_raw_inputs": len(set(fingerprints)),
                                    "identifier_rows": len(identifiers),
                                    "unique_identifiers": len(set(identifiers))}},
              "recorded_overlap_scope": reused,
              "row_fingerprints_sha256": json_digest(fingerprints),
              "test_data_read": False,
              "overlap_evidence_note": "Counts come from the hash-bound data-evidence document; train/test data was not read by this fitter."}
    return report, rows


def json_digest(value):
    """Identity of compact, ASCII JSON with nonfinite values forbidden."""
    return hashlib.sha256(json.dumps(value, ensure_ascii=True, allow_nan=False,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def assert_unchanged(prepared):
    manifest = prepared["manifest"]
    for info in manifest["input_files"].values():
        if repro.sha256_file(info["path"]) != info["sha256"]:
            raise repro.ReproError(f"Input changed during calibration: {info['path']}")
    checkpoint = manifest["input_checkpoint"]
    if repro.sha256_file(prepared["checkpoint"]) != checkpoint["sha256"]:
        raise repro.ReproError("Checkpoint changed during calibration")
    for name, expected in manifest.get("harness_sha256", {}).items():
        if repro.sha256_file(ROOT / name) != expected:
            raise repro.ReproError(f"Fitting source changed during calibration: {name}")


def collect_validation_logits(prepared, runtime=None, processors=None, forwards=None):
    """Collect every ordered validation row, removing targets before model forward."""
    assert_unchanged(prepared)
    args, native, manifest = prepared["args"], prepared["native"], prepared["manifest"]
    expected_labels = [row["label"] for row in prepared["rows"]]
    if native.device != "cuda" or getattr(native, "data_ratio", None) != 1.0:
        raise repro.ReproError("Calibration requires CUDA and the full validation data_ratio=1.0")
    runtime = runtime or evaluate.load_runtime(args.upstream)
    torch = runtime.torch
    if not torch.cuda.is_available():
        raise repro.ReproError("CUDA is unavailable for validation inference")
    if processors is None or forwards is None:
        from engine_mm import get_data_processors, get_model_forward_fn
        processors, forwards = get_data_processors(), get_model_forward_fn()
    process, forward = processors[native.dataset_type], forwards[native.dataset_type]
    device = torch.device(native.device)
    model = runtime.classifier(native)
    checkpoint = torch.load(str(prepared["checkpoint"]), map_location="cpu", weights_only=False)
    if not isinstance(checkpoint, Mapping) or not isinstance(checkpoint.get("model"), Mapping):
        raise repro.ReproError("Checkpoint must contain a model state dictionary")
    model.load_state_dict(checkpoint["model"], strict=True)
    model.to(device).eval()
    loader, idx2label = runtime.loader(native, str(Path(args.data).resolve() / "data-valid.json"),
                                     data_ratio=1.0, random_sampler=False, class_idx=None)
    evaluate.check_loader_mapping(idx2label, manifest["class_mapping"], expected_labels)
    count = len(expected_labels)
    if (type(loader.sampler) is not torch.utils.data.SequentialSampler
            or list(loader.sampler) != list(range(count))
            or loader.drop_last is not False or loader.batch_sampler.drop_last is not False
            or loader.batch_sampler.sampler is not loader.sampler
            or loader.batch_size != native.batch_size or loader.batch_sampler.batch_size != native.batch_size
            or type(native.batch_size) is not int or native.batch_size <= 0
            or len(loader.dataset) != count or getattr(loader.dataset, "ratio", None) != 1.0
            or len(loader) != math.ceil(count / native.batch_size)):
        raise repro.ReproError("Native loader must preserve every ordered validation row and partial batch")
    if [row["label"] for row in loader.dataset.data] != expected_labels:
        raise repro.ReproError("Native dataset label order differs from validation source")
    assert_unchanged(prepared)
    logits, labels, batch_sizes = [], [], []
    with torch.inference_mode(), torch.autocast("cuda", dtype=torch.float16):
        for batch in loader:
            inputs = process(batch, device)
            targets = inputs.pop("targets")
            if targets.ndim != 1:
                raise repro.ReproError("Native targets must have one label per validation row")
            batch_labels = targets.detach().cpu().tolist()
            expected_size = min(native.batch_size, count - len(labels))
            if (not batch_labels or len(batch_labels) != expected_size
                    or any(type(value) is not int for value in batch_labels)
                    or batch_labels != expected_labels[len(labels):len(labels) + expected_size]):
                raise repro.ReproError("Native validation batch count or label order changed")
            # The retained labels are used only for fitting/metrics, never model inputs.
            output = forward(model, inputs)["logits"]
            if output.ndim != 2 or tuple(output.shape) != (expected_size, len(manifest["class_mapping"])):
                raise repro.ReproError("Unexpected validation logit shape")
            batch_logits = output.detach().cpu().tolist()
            for row in batch_logits:
                calibration.calibrated_scores(row, 1.0)  # finite, numeric logit validation
            logits.extend(batch_logits)
            labels.extend(batch_labels)
            batch_sizes.append(expected_size)
    if len(logits) != count or labels != expected_labels:
        raise repro.ReproError("Incomplete or reordered validation inference")
    assert_unchanged(prepared)
    audit = {"expected_rows": count, "observed_rows": len(logits), "batch_size": native.batch_size,
             "batch_sizes": batch_sizes, "full_batches": sum(size == native.batch_size for size in batch_sizes),
             "partial_batch_rows": count % native.batch_size, "drop_last": False,
             "data_ratio": 1.0, "sampler": "SequentialSampler", "row_order": "source_json_order",
             "labels_match_source_order": True, "targets_removed_before_forward": True,
             "metric_tie_break": "first maximum-logit index"}
    return logits, labels, audit


def prepare(args, manifest):
    _, config_info = repro.read_document(args.config)
    config = repro.load_config(args.config)
    if repro.sha256_file(args.config) != config_info["sha256"]:
        raise repro.ReproError("Configuration changed during preflight")
    report, rows = validate_validation_data(args.data, config, args.data_evidence)
    checkpoint = Path(args.checkpoint).resolve()
    checkpoint_hash = repro.sha256_file(checkpoint)
    provenance_path = args.provenance or checkpoint.parent / "manifest.json"
    provenance = repro.checkpoint_provenance(checkpoint, checkpoint_hash, report["class_mapping"], provenance_path)
    if provenance["class_order"] != "hash_bound":
        raise repro.ReproError("Calibration requires checkpoint-bound class order")
    provenance_document, provenance_info = repro.read_document(provenance_path)
    if provenance_info["sha256"] != provenance["source_file"]["sha256"]:
        raise repro.ReproError("Checkpoint provenance changed during preflight")
    native_args = copy.copy(args)
    native_args.command = "evaluate"
    native, native_argv, _, integrity = repro.build_native(native_args, config, report)
    files = {**report["files"], "configuration.json": config_info, "checkpoint-provenance.json": provenance_info}
    manifest.update(configuration=config, configuration_sha256=config_info["sha256"],
                    validation=report, class_mapping=report["class_mapping"], input_files=files,
                    input_checkpoint={"path": str(checkpoint), "sha256": checkpoint_hash},
                    checkpoint_provenance=provenance, upstream=integrity, native_args=vars(native).copy(),
                    native_argv=native_argv, inference_runtime=dict(calibration.INFERENCE_RUNTIME),
                    protocol={"fit_split": "valid", "objective": "nll",
                              "temperature_bounds": list(calibration.TEMPERATURE_BOUNDS),
                              "policy_threshold": calibration.DEFAULT_THRESHOLD,
                              "test_data_read": False})
    training_valid = provenance_document.get("input_files", {}).get("data-valid.json", {})
    if not training_valid:
        training_valid = provenance_document.get("validation", {}).get("files", {}).get("data-valid.json", {})
    reuse = True if (provenance_document.get("stage") == "finetune"
                     and training_valid.get("sha256") == report["files"]["data-valid.json"]["sha256"]) else None
    prepared = {"args": args, "native": native, "report": report, "rows": rows,
                "checkpoint": checkpoint, "manifest": manifest, "configuration": config,
                "checkpoint_selection_reuse": reuse}
    manifest["calibration_binding"] = calibration.make_binding(manifest)
    assert_unchanged(prepared)
    return prepared


def build_artifact(prepared, logits, labels, batch_audit):
    temperature = calibration.fit_temperature(logits, labels)
    report, manifest = prepared["report"], prepared["manifest"]
    limitations = ["Retrospective validation fitting is not independent confirmation.",
                   "The recorded overlap counts come from the bound data-evidence document; this fitting run did not read train or test data.",
                   "Recorded identifiers and exact input equality do not establish capture independence; released pretraining exposure remains unknown.",
                   "The fixed 0.90 threshold illustrates an accept/defer policy; it is not an operational safety level or correctness guarantee.",
                   "A positive scalar temperature preserves maximum-logit classes; no accuracy improvement is established."]
    reuse = prepared["checkpoint_selection_reuse"]
    limitations.append("The same validation file was used during checkpoint selection; it is reused for fitting."
                       if reuse is True else "Checkpoint-selection reuse is unknown for this provenance record.")
    fit = {"split": "valid", "objective": "nll", "temperature_bounds": list(calibration.TEMPERATURE_BOUNDS),
           "temperature": temperature, "rows": len(labels),
           "optimizer": "bisection of convex NLL derivative in inverse temperature",
           "iterations_bound": calibration.FIT_ITERATIONS, "policy_threshold": calibration.DEFAULT_THRESHOLD,
           "data_sha256": report["files"]["data-valid.json"]["sha256"],
           "metadata_sha256": report["files"]["metadata.json"]["sha256"],
           "data_evidence_sha256": report["files"]["data-evidence.json"]["sha256"],
           "logits_sha256": json_digest(logits), "labels_sha256": json_digest(labels),
           "observation_hash_encoding": "UTF-8 compact ASCII JSON, separators comma/colon, allow_nan=False",
           "raw_metrics": calibration.classification_metrics(logits, labels),
           "calibrated_metrics": calibration.classification_metrics(
               logits, labels, temperature, threshold=calibration.DEFAULT_THRESHOLD)}
    artifact = {"schema_version": 1, "method": "temperature_scaling", "temperature": temperature,
                "binding": manifest["calibration_binding"], "fit": fit,
                "validation": {"rows": len(labels), "independent_holdout": False,
                               "checkpoint_selection_reuse": reuse, **report["recorded_overlap_scope"],
                               "limitations": limitations, "loader": batch_audit}}
    return calibration.validate_artifact(artifact, calibration.make_binding(manifest))


def main(argv=None):
    supplied = sys.argv[1:] if argv is None else argv
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True, help="Directory containing metadata.json and data-valid.json")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--provenance", type=Path)
    parser.add_argument("--output", type=Path, required=True, help="Fresh, exclusively owned output directory")
    parser.add_argument("--config", type=Path, default=repro.DEFAULT_CONFIG)
    parser.add_argument("--upstream", type=Path, default=repro.DEFAULT_UPSTREAM)
    parser.add_argument("--data-evidence", type=Path, default=DEFAULT_EVIDENCE,
                        help="Recorded report binding validation bytes/classes/counts and overlap scope")
    parser.add_argument("--num-workers", type=int, default=2)
    parser.add_argument("--dry-run", action="store_true", help="Validate inputs and source without loading Torch or fitting")
    parser.set_defaults(command="calibrate", device="cuda", seed=None)
    args = parser.parse_args(supplied)
    path, manifest = None, None
    started = time.monotonic()
    try:
        if args.num_workers < 0:
            raise repro.ReproError("num-workers must be nonnegative")
        path, manifest = repro.begin_manifest(args)
        manifest["harness_sha256"].update({name: repro.sha256_file(ROOT / name)
                                          for name in ("calibration.py", "tools/calibrate.py")})
        manifest["argv"] = [sys.executable, str(Path(__file__).resolve()), *supplied]
        prepared = prepare(args, manifest)
        if args.dry_run:
            manifest.update(status="dry_run", updated_at=repro.timestamp(), exit_code=0)
        else:
            manifest.update(status="running", execution_attempted=True, updated_at=repro.timestamp())
            repro.atomic_json(path, manifest)
            logits, labels, batch_audit = collect_validation_logits(prepared)
            artifact = build_artifact(prepared, logits, labels, batch_audit)
            assert_unchanged(prepared)
            if repro.verify_upstream(args.upstream, prepared["configuration"]) != manifest["upstream"]:
                raise repro.ReproError("Upstream source changed during calibration")
            artifact_path = path.parent / "calibration.json"
            repro.atomic_json(artifact_path, artifact, overwrite=False)
            manifest.update(calibration_artifact={"path": str(artifact_path), "sha256": repro.sha256_file(artifact_path)},
                            validation_observations={"logits": logits, "labels": labels,
                                                     "logits_sha256": artifact["fit"]["logits_sha256"],
                                                     "labels_sha256": artifact["fit"]["labels_sha256"]},
                            batch_audit=batch_audit, status="succeeded", updated_at=repro.timestamp(), exit_code=0)
        manifest["elapsed_seconds"] = time.monotonic() - started
        repro.atomic_json(path, manifest)
        print(f"{manifest['status']}: {path}")
        return 0
    except (Exception, KeyboardInterrupt) as error:
        code = 130 if isinstance(error, KeyboardInterrupt) else 1
        if manifest is not None:
            manifest.update(status="failed" if manifest["execution_attempted"] else "preflight_failed",
                            updated_at=repro.timestamp(), exit_code=code,
                            error={"type": type(error).__name__, "message": str(error)})
            try:
                repro.atomic_json(path, manifest)
            except (OSError, ValueError) as write_error:
                print(f"Cannot record calibration failure: {write_error}", file=sys.stderr)
        print(f"Calibration failed: {error}", file=sys.stderr)
        return code


if __name__ == "__main__":
    raise SystemExit(main())
