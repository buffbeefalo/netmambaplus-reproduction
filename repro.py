"""Native-flow validation and invocation of the pinned NetMamba+ implementation."""

import argparse
import hashlib
import importlib.metadata
import itertools
import json
import math
import os
import platform
import re
import runpy
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_CONFIG = ROOT / "configs/ciciot2022.json"
DEFAULT_UPSTREAM = ROOT / "upstream/NetMambaPlus"
CORE_FILES = {"src/pre-train.py", "src/fine-tune.py", "src/engine_mm.py",
              "src/util/loader_data.py", "src/util/loader_model.py",
              "src/util/arg_pre_train.py", "src/util/arg_fine_tune.py"}
IMPORTABLE_SUFFIXES = {".py", ".pyw", ".pyc", ".pyo", ".so", ".pyd", ".zip", ".egg", ".pth"}
ENV_KEYS = ("CUDA_VISIBLE_DEVICES", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "PYTHONPATH",
            "WORLD_SIZE", "RANK", "LOCAL_RANK", "SLURM_PROCID",
            "TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD", "CUBLAS_WORKSPACE_CONFIG", "TRITON_PTXAS_PATH")


class ReproError(ValueError):
    pass


def sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_document(path):
    path = Path(path)
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, ValueError) as error:
        raise ReproError(f"Cannot read JSON {path}: {error}") from error
    return value, {"path": str(path.resolve()), "sha256": hashlib.sha256(raw).hexdigest(),
                   "bytes": len(raw)}


def atomic_json(path, value, *, overwrite=True):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=f".{path.name}.", delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(value, stream, indent=2, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        if overwrite:
            os.replace(temporary, path)
        else:
            try:
                os.link(temporary, path)
            except FileExistsError as error:
                raise ReproError(f"Refusing to replace existing file: {path}") from error
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def load_config(path):
    config, _ = read_document(path)
    try:
        upstream = config["upstream"]
        valid = (config["schema_version"] == 1
                 and re.fullmatch(r"[0-9a-f]{40}", upstream["commit"])
                 and set(upstream["sha256"]) == CORE_FILES
                 and all(re.fullmatch(r"[0-9a-f]{64}", h) for h in upstream["sha256"].values())
                 and isinstance(config["common"], dict)
                 and isinstance(config["pretrain"], dict)
                 and isinstance(config["finetune"], dict))
    except (KeyError, TypeError):
        valid = False
    if not valid:
        raise ReproError("Invalid configuration: require schema 1, a commit and seven core SHA-256 values")
    return config


def validate_mapping(mapping, expected_classes=None):
    if not isinstance(mapping, dict) or not mapping:
        raise ReproError("name_to_idx must be a nonempty object")
    if any(not isinstance(k, str) or not k or type(v) is not int for k, v in mapping.items()):
        raise ReproError("Class names must be nonempty strings and class indices must be integers")
    if sorted(mapping.values()) != list(range(len(mapping))):
        raise ReproError("Class mapping must be one-to-one with contiguous indices starting at zero")
    if expected_classes is not None and len(mapping) != expected_classes:
        raise ReproError(f"This preset requires {expected_classes} classes; found {len(mapping)}")
    return dict(mapping)


def numeric_sequence(value, field, nonnegative=False):
    if not isinstance(value, str):
        raise ReproError(f"{field} must be a space-separated numeric string")
    try:
        values = [float(token) for token in value.split(" ")]
    except ValueError as error:
        raise ReproError(f"{field} does not match the native literal-space numeric format") from error
    if any(not math.isfinite(v) or (nonnegative and v < 0) for v in values):
        raise ReproError(f"{field} requires finite {'nonnegative ' if nonnegative else ''}values")
    return values


def validate_record(row, mapping, size_key):
    if not isinstance(row, dict):
        raise ReproError("A flow must be a JSON object")
    packets = row.get("data")
    if not isinstance(packets, list) or any(not isinstance(p, str) for p in packets):
        raise ReproError("data must be a list of integer-byte strings")
    for packet in packets:
        try:
            values = [int(token) for token in packet.split()]
        except ValueError as error:
            raise ReproError("data contains a non-integer packet byte") from error
        if any(v < 0 or v > 255 for v in values):
            raise ReproError("Packet bytes must be in [0, 255]")
    sizes = numeric_sequence(row.get(size_key), size_key)
    intervals = numeric_sequence(row.get("intervals"), "intervals", nonnegative=True)
    if len(sizes) != len(intervals):
        raise ReproError("Size and interval sequences must have equal lengths")
    label, name = row.get("label"), row.get("name")
    if type(label) is not int or not isinstance(name, str) or mapping.get(name) != label:
        raise ReproError("Flow label/name conflicts with metadata.json name_to_idx")
    if "num_packet" in row and (type(row["num_packet"]) is not int or row["num_packet"] < 0):
        raise ReproError("num_packet, when present, must be a nonnegative integer")
    identifier = row.get("pcap_file")
    if identifier is not None and not isinstance(identifier, str):
        raise ReproError("pcap_file, when present, must be a string")
    raw = json.dumps([packets, row[size_key], row["intervals"]],
                     ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return identifier or None, hashlib.sha256(raw).hexdigest()


def data_paths(directory, stage):
    directory = Path(directory).resolve()
    if stage == "pretrain":
        preferred = directory / "data-train.json"
        return {"train": preferred if preferred.is_file() else directory / "data.json"}
    if stage == "evaluate":
        return {"test": directory / "data-test.json"}
    if stage == "finetune":
        return {s: directory / f"data-{s}.json" for s in ("train", "valid", "test")}
    raise ReproError(f"Unknown validation stage: {stage}")


def stage_parameters(config, stage):
    if stage not in ("pretrain", "finetune", "evaluate"):
        raise ReproError(f"Unknown execution stage: {stage}")
    section = "pretrain" if stage == "pretrain" else "finetune"
    return {**config["common"], **config[section]}


def validate_data(directory, stage, config):
    directory = Path(directory).resolve()
    metadata, metadata_file = read_document(directory / "metadata.json")
    if not isinstance(metadata, dict):
        raise ReproError("metadata.json must contain an object")
    mapping = validate_mapping(metadata.get("name_to_idx"), config["dataset"].get("expected_classes"))
    size_key = stage_parameters(config, stage).get("size_key", "sizes")
    if size_key not in ("sizes", "signed_sizes"):
        raise ReproError("size_key must be sizes or signed_sizes")
    report = {"stage": stage, "class_mapping": mapping, "size_key": size_key,
              "files": {"metadata.json": metadata_file}, "splits": {}, "raw_input_overlaps": {},
              "identity_limit": "Recorded identifiers and exact raw-input equality do not prove capture independence."}
    identities, fingerprints = {}, {}
    for split, path in data_paths(directory, stage).items():
        rows, file_info = read_document(path)
        if not isinstance(rows, list) or not rows:
            raise ReproError(f"{path.name} must be a nonempty JSON array of flows")
        report["files"][path.name] = file_info
        ids, hashes, labels, hash_labels = [], Counter(), Counter(), {}
        for index, row in enumerate(rows):
            try:
                identifier, fingerprint = validate_record(row, mapping, size_key)
            except ReproError as error:
                raise ReproError(f"{path.name} record {index}: {error}") from error
            if identifier is not None:
                ids.append(identifier)
            hashes[fingerprint] += 1
            labels[str(row["label"])] += 1
            hash_labels.setdefault(fingerprint, set()).add(row["label"])
        identities[split] = set(ids)
        fingerprints[split] = (hashes, hash_labels)
        report["splits"][split] = {"rows": len(rows), "class_counts": dict(labels),
            "identifier_rows": len(ids), "unique_identifiers": len(set(ids)),
            "unique_raw_inputs": len(hashes), "duplicate_excess": len(rows) - len(hashes),
            "conflicting_raw_input_groups": sum(len(v) > 1 for v in hash_labels.values())}
    for left, right in itertools.combinations(fingerprints, 2):
        overlap = identities[left] & identities[right]
        if overlap:
            raise ReproError(f"{left}/{right} share {len(overlap)} recorded pcap_file identifiers")
        a, a_labels = fingerprints[left]
        b, b_labels = fingerprints[right]
        shared = a.keys() & b.keys()
        report["raw_input_overlaps"][f"{left}_{right}"] = {
            "shared_raw_inputs": len(shared), "left_rows": sum(a[h] for h in shared),
            "right_rows": sum(b[h] for h in shared),
            "conflicting_shared_input_groups": sum(len(a_labels[h] | b_labels[h]) > 1 for h in shared)}
    return report


def git(upstream, *arguments):
    try:
        result = subprocess.run(["git", "-C", str(upstream), *arguments], check=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.stdout.decode("utf-8")
    except (OSError, subprocess.CalledProcessError) as error:
        raise ReproError(f"Git checkout check failed ({arguments[0]}): {error}") from error


def verify_upstream(upstream, config):
    upstream = Path(upstream).resolve()
    pin = config["upstream"]["commit"]
    if Path(git(upstream, "rev-parse", "--show-toplevel").strip()).resolve() != upstream:
        raise ReproError("Upstream path is not the root of its own Git checkout")
    if git(upstream, "rev-parse", "HEAD").strip() != pin:
        raise ReproError(f"Upstream must be at exact commit {pin}")
    if git(upstream, "status", "--porcelain=v1", "--untracked-files=no").strip():
        raise ReproError("Upstream has modified tracked contents")
    tracked = set()
    for entry in git(upstream, "ls-tree", "-r", "-z", "--full-tree", "HEAD").split("\0"):
        if not entry:
            continue
        meta, name = entry.split("\t", 1)
        mode, kind, digest = meta.split()
        file = upstream / name
        if kind != "blob" or mode not in ("100644", "100755") or file.is_symlink():
            raise ReproError(f"Unsupported upstream entry: {name}")
        try:
            raw = file.read_bytes()
        except OSError as error:
            raise ReproError(f"Missing tracked upstream file: {name}") from error
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        if actual != digest:
            raise ReproError(f"Tracked upstream content differs from its Git object: {name}")
        tracked.add(name)
    for folder, directories, files in os.walk(upstream, followlinks=False):
        if Path(folder) == upstream:
            directories[:] = [d for d in directories if d != ".git"]
        for name in directories:
            if (Path(folder) / name).is_symlink():
                raise ReproError(f"Additional upstream directory symlink: {name}")
        for name in files:
            file = Path(folder) / name
            relative = file.relative_to(upstream).as_posix()
            if relative not in tracked and (file.suffix.lower() in IMPORTABLE_SUFFIXES or file.is_symlink()):
                raise ReproError(f"Additional importable upstream file: {relative}")
    for name, expected in config["upstream"]["sha256"].items():
        if name not in tracked or sha256_file(upstream / name) != expected:
            raise ReproError(f"Core upstream SHA-256 mismatch: {name}")
    return {"commit": pin, "core_sha256": dict(config["upstream"]["sha256"]),
            "tracked_files_verified": len(tracked)}


def fetch(upstream, config):
    upstream = Path(upstream).resolve()
    if not upstream.exists():
        upstream.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "--no-checkout", "--", config["upstream"]["url"],
                        str(upstream)], check=True)
        git(upstream, "checkout", "--detach", config["upstream"]["commit"])
    return verify_upstream(upstream, config)


def check_single_process(config):
    if config["common"].get("world_size", 1) != 1:
        raise ReproError("This harness supports the single-process preset only")
    if os.environ.get("WORLD_SIZE", "1") != "1" or any(
            key in os.environ for key in ("RANK", "LOCAL_RANK", "SLURM_PROCID")):
        raise ReproError("Distributed-launch environment conflicts with the single-process preset")


def build_native(args, config, report):
    upstream = Path(args.upstream).resolve()
    integrity = verify_upstream(upstream, config)
    check_single_process(config)
    stage = "pretrain" if args.command == "pretrain" else "finetune"
    parameters = stage_parameters(config, args.command)
    if parameters.get("world_size", 1) != 1:
        raise ReproError("Stage configuration conflicts with single-process execution")
    output = Path(args.output).resolve()
    parameters.update(data_path=str(Path(args.data).resolve()), output_dir=str(output),
                      log_dir=str(output / "logs"), device=args.device)
    if args.num_workers is not None:
        parameters["num_workers"] = args.num_workers
    if args.seed is not None:
        parameters["seed"] = args.seed
    if stage == "finetune":
        checkpoint = Path(args.checkpoint).resolve()
        parameters.update(finetune=str(checkpoint), nb_classes=len(report["class_mapping"]),
                          ckpt_dir=str(checkpoint.parent if args.command == "evaluate" else output))
    native_argv = []
    negative_flags = {"if_amp": "--no_amp", "pin_mem": "--no_pin_mem"}
    for key, value in parameters.items():
        if value is None:
            continue
        if isinstance(value, bool):
            if value:
                native_argv.append("--" + key)
            elif key in negative_flags:
                native_argv.append(negative_flags[key])
        else:
            native_argv.extend(["--" + key, str(value)])
    sys.dont_write_bytecode = True
    parser_file = upstream / "src/util" / ("arg_pre_train.py" if stage == "pretrain" else "arg_fine_tune.py")
    parser = runpy.run_path(str(parser_file))["get_args_parser"]()
    try:
        native = parser.parse_args(native_argv)
    except SystemExit as error:
        raise ReproError(f"Native parser rejected arguments (exit {error.code})") from error
    for key, value in parameters.items():
        if value is not None and getattr(native, key, object()) != value:
            raise ReproError(f"Native parser did not preserve requested setting {key}")
    script = upstream / "src" / ("pre-train.py" if stage == "pretrain" else "fine-tune.py")
    return native, native_argv, [sys.executable, "-u", str(script), *native_argv], integrity


def checkpoint_provenance(checkpoint, digest, mapping, explicit=None):
    unknown = {"class_order": "unknown", "training_history": "unknown", "source": None}
    source = Path(explicit).resolve() if explicit else Path(checkpoint).parent / "manifest.json"
    if not source.is_file():
        if explicit:
            raise ReproError(f"Explicit checkpoint provenance is missing: {source}")
        return unknown
    document, source_info = read_document(source)
    if not isinstance(document, dict):
        raise ReproError("Checkpoint provenance must be an object")
    binding = document.get("produced_checkpoint")
    if binding is not None and (document.get("status") != "succeeded" or document.get("stage") != "finetune"):
        if explicit:
            raise ReproError("Checkpoint provenance does not describe successful fine-tuning")
        return {**unknown, "source": str(source), "source_file": source_info,
                "note": "Checkpoint entry is not from a successful fine-tuning manifest"}
    if binding is None and "checkpoint_sha256" in document:
        binding = {"sha256": document["checkpoint_sha256"], "class_mapping": document.get("class_mapping")}
    if not isinstance(binding, dict) or binding.get("sha256") != digest:
        if explicit:
            raise ReproError("Explicit provenance is not bound to this checkpoint SHA-256")
        return {**unknown, "source": str(source), "source_file": source_info,
                "note": "No matching checkpoint hash binding"}
    bound_mapping = validate_mapping(binding.get("class_mapping"))
    if bound_mapping != mapping:
        raise ReproError("Checkpoint-bound class mapping conflicts with test metadata")
    return {"class_order": "hash_bound", "training_history": "unknown",
            "source": str(source), "source_file": source_info,
            "checkpoint_sha256": digest, "class_mapping": bound_mapping,
            "note": "Hash binding is recorded provenance, not independent authentication of its claims."}


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def runtime_information():
    versions = {}
    for name in ("torch", "torchvision", "numpy", "timm", "mamba-ssm", "causal-conv1d", "flash-attn",
                 "scikit-learn", "scipy", "pillow", "triton", "einops"):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    return {"python": sys.version, "executable": sys.executable, "platform": platform.platform(),
            "machine": platform.machine(), "packages": versions,
            "environment": {k: os.environ[k] for k in ENV_KEYS if k in os.environ}}


def begin_manifest(args):
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    path = output / "manifest.json"
    if any(output.iterdir()):
        raise ReproError(f"Output is not empty; choose a fresh output directory: {output}")
    manifest = {"schema_version": 1, "stage": args.command, "status": "preflight",
                "created_at": timestamp(), "updated_at": timestamp(), "execution_attempted": False,
                "request": {k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()},
                "runtime": runtime_information(),
                "harness_sha256": {name: sha256_file(ROOT / name) for name in ("repro.py", "evaluate.py")},
                "error": None}
    atomic_json(path, manifest, overwrite=False)
    return path, manifest


def prepare(args, manifest):
    config = load_config(args.config)
    manifest.update(configuration=config, configuration_sha256=sha256_file(args.config),
                    configuration_provenance=config.get("provenance", {}))
    report = validate_data(args.data, args.command, config)
    manifest.update(validation=report, class_mapping=report["class_mapping"], input_files=report["files"])
    checkpoint = None
    if args.command in ("finetune", "evaluate"):
        if not args.checkpoint:
            raise ReproError("A checkpoint is required for fine-tuning and evaluation")
        checkpoint = Path(args.checkpoint).resolve()
        if not checkpoint.is_file():
            raise ReproError(f"Checkpoint does not exist: {checkpoint}")
        manifest["input_checkpoint"] = {"path": str(checkpoint), "sha256": sha256_file(checkpoint)}
    native, native_argv, command, integrity = build_native(args, config, report)
    manifest.update(upstream=integrity, native_args=vars(native).copy(), native_argv=native_argv,
                    argv=command, cwd=str(Path(args.upstream).resolve() / "src"))
    if args.command == "evaluate":
        manifest["cwd"] = str(Path.cwd())
        manifest["argv"] = [sys.executable, str(ROOT / "evaluate.py"), *execution_options(args)]
        manifest["checkpoint_provenance"] = checkpoint_provenance(
            checkpoint, manifest["input_checkpoint"]["sha256"], report["class_mapping"], args.provenance)
    return {"args": args, "native": native, "report": report, "command": command,
            "checkpoint": checkpoint, "manifest": manifest}


def execution_options(args):
    result = ["--config", str(Path(args.config).resolve()), "--upstream", str(Path(args.upstream).resolve()),
              "--data", str(Path(args.data).resolve()), "--output", str(Path(args.output).resolve()),
              "--device", args.device]
    for option in ("checkpoint", "provenance"):
        value = getattr(args, option, None)
        if value:
            result.extend(["--" + option, str(Path(value).resolve())])
    for option in ("seed", "num_workers"):
        value = getattr(args, option, None)
        if value is not None:
            result.extend(["--" + option.replace("_", "-"), str(value)])
    return result


def run_stage(args, evaluation_fn=None):
    path, manifest = None, None
    try:
        path, manifest = begin_manifest(args)
        prepared = prepare(args, manifest)
        if args.dry_run:
            manifest.update(status="dry_run", updated_at=timestamp(), exit_code=0)
            atomic_json(path, manifest)
            print(f"Dry run: no model execution. Manifest: {path}")
            return 0
        manifest.update(status="running", updated_at=timestamp(), execution_attempted=True)
        atomic_json(path, manifest)
        if args.command == "evaluate":
            if evaluation_fn is None:
                raise ReproError("Actual evaluation must use the separate evaluate.py entry point")
            metrics = evaluation_fn(prepared)
            metrics_path = path.parent / "metrics.json"
            atomic_json(metrics_path, metrics)
            manifest["metrics_file"] = {"path": str(metrics_path), "sha256": sha256_file(metrics_path)}
        else:
            log = path.parent / "native.log"
            manifest["native_log"] = str(log)
            atomic_json(path, manifest)
            environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
            with log.open("w", encoding="utf-8") as stream:
                result = subprocess.run(prepared["command"], cwd=manifest["cwd"], env=environment,
                                        stdout=stream, stderr=subprocess.STDOUT, check=False)
            manifest["native_exit_code"] = result.returncode
            if result.returncode != 0:
                raise ReproError(f"Native process exited {result.returncode}; see {log}")
            if args.command == "finetune":
                best = path.parent / "checkpoint-best.pth"
                if not best.is_file():
                    raise ReproError("Fine-tuning exited without checkpoint-best.pth")
                manifest["produced_checkpoint"] = {"path": str(best), "sha256": sha256_file(best),
                                                   "class_mapping": manifest["class_mapping"]}
        for item in manifest["input_files"].values():
            if sha256_file(item["path"]) != item["sha256"]:
                raise ReproError(f"Input changed during execution: {item['path']}")
        if prepared["checkpoint"] and sha256_file(prepared["checkpoint"]) != manifest["input_checkpoint"]["sha256"]:
            raise ReproError("Input checkpoint changed during execution")
        manifest.update(status="succeeded", updated_at=timestamp(), exit_code=0)
        atomic_json(path, manifest)
        print(f"Completed {args.command}. Manifest: {path}")
        return 0
    except (Exception, KeyboardInterrupt) as error:
        code = 130 if isinstance(error, KeyboardInterrupt) else 1
        if manifest is not None:
            manifest.update(status="failed" if manifest["execution_attempted"] else "preflight_failed",
                            updated_at=timestamp(), exit_code=code,
                            error={"type": type(error).__name__, "message": str(error)})
            try:
                atomic_json(path, manifest)
            except (OSError, ValueError) as write_error:
                print(f"Cannot write failure manifest: {write_error}", file=sys.stderr)
        else:
            print(f"Cannot initialize manifest: {error}", file=sys.stderr)
        print(f"{args.command} failed: {error}", file=sys.stderr)
        return code


def cli_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for stage in ("fetch", "validate", "pretrain", "finetune", "evaluate"):
        command = commands.add_parser(stage)
        command.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
        command.add_argument("--upstream", type=Path, default=DEFAULT_UPSTREAM)
        if stage == "fetch":
            continue
        command.add_argument("--data", type=Path, required=True)
        if stage == "validate":
            command.add_argument("--stage", choices=("pretrain", "finetune", "evaluate"), default="finetune")
            command.add_argument("--report", type=Path, help="Write to a new file; never replace an existing file")
            continue
        command.add_argument("--output", type=Path, required=True,
                             help="New or empty directory to be owned exclusively by this run")
        command.add_argument("--checkpoint", type=Path)
        command.add_argument("--provenance", type=Path)
        command.add_argument("--dry-run", action="store_true")
        command.add_argument("--device", default="cuda")
        command.add_argument("--num-workers", type=int)
        command.add_argument("--seed", type=int)
    return parser


def main(argv=None):
    args = cli_parser().parse_args(argv)
    try:
        if args.command == "fetch":
            print(json.dumps(fetch(args.upstream, load_config(args.config)), indent=2))
            return 0
        if args.command == "validate":
            report = validate_data(args.data, args.stage, load_config(args.config))
            if args.report:
                atomic_json(args.report, report, overwrite=False)
            print(json.dumps(report, indent=2, allow_nan=False))
            return 0
        if args.command == "evaluate" and not args.dry_run:
            try:
                return subprocess.run([sys.executable, str(ROOT / "evaluate.py"), *execution_options(args)],
                                      env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"), check=False).returncode
            except OSError as error:
                def unavailable(_):
                    raise ReproError(f"Cannot launch evaluate.py: {error}")
                return run_stage(args, evaluation_fn=unavailable)
        return run_stage(args)
    except (Exception, KeyboardInterrupt) as error:
        print(f"{args.command} failed: {error}", file=sys.stderr)
        return 130 if isinstance(error, KeyboardInterrupt) else 1


if __name__ == "__main__":
    raise SystemExit(main())
