"""Predict packet classes from an unlabeled CSV using a strict native checkpoint.

Accept exactly payload_byte_1 through payload_byte_1500, optionally followed by
ttl,total_len,protocol,t_delta. A label column is forbidden. The entire file is
validated and fingerprinted even when --max-rows limits model inference to a
prefix. Outputs contain no raw payloads and no ground-truth accuracy metrics.
Softmax probabilities are uncalibrated model scores.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import packet_data
import packet_model


PAYLOAD_COLUMNS = [f"payload_byte_{index}" for index in range(1, 1501)]
METADATA_COLUMNS = ["ttl", "total_len", "protocol", "t_delta"]
_BYTE_TOKENS = {str(value): value for value in range(256)}
_CLASS_NAMES = ("benign", "attack")


def _positive_integer(value, name):
    if type(value) is not int or value <= 0:
        raise ValueError(f"{name} must be a positive integer")


def _identity(value):
    return value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns


def _path_identity(path):
    # NTFS directory metadata can lag after hard-link publication. Compare the
    # current path's open file handle with the original handle instead.
    with path.open("rb") as stream:
        return _identity(os.fstat(stream.fileno()))


def _fingerprint_stream(stream, path):
    before = os.fstat(stream.fileno())
    digest = hashlib.sha256()
    count = 0
    for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
        digest.update(block)
        count += len(block)
    if (count != before.st_size or _identity(before) != _identity(os.fstat(stream.fileno()))
            or _identity(before) != _path_identity(path)):
        raise ValueError(f"File changed while fingerprinting: {path}")
    return {"path": str(path), "bytes": count, "sha256": digest.hexdigest()}


def _fingerprint(path):
    with path.open("rb") as stream:
        return _fingerprint_stream(stream, path)


def _write_receipt(output, receipt):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("w", dir=output, prefix=".receipt-", encoding="utf-8",
                                         delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(receipt, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        # Only this invocation's receipt in its exclusive output directory is replaced.
        os.replace(temporary, output / "receipt.json")
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _payload_from_row(row, row_id, width):
    if len(row) != width:
        raise ValueError(f"CSV row {row_id}: expected exactly {width} columns")
    values = row[:1500]
    try:
        # Exact validated integer tokens avoid a float cast and its rounding errors.
        return bytes(map(_BYTE_TOKENS.__getitem__, values))
    except KeyError:
        try:
            return packet_data.validate_payload(values)
        except ValueError as error:
            raise ValueError(f"CSV row {row_id}: {error}") from error


def format_predictions(batch, logits):
    """Check native row alignment and finite binary logits before exposing scores."""
    if not isinstance(logits, list) or len(logits) != len(batch) or not batch:
        raise ValueError("Native logits lost or added prediction rows")
    records = []
    for (row_id, payload), values in zip(batch, logits):
        if (not isinstance(values, list) or len(values) != 2
                or any(type(value) not in (float, int) or not math.isfinite(value) for value in values)):
            raise ValueError("Native inference requires exactly two finite numeric logits per row")
        values = [float(value) for value in values]
        maximum = max(values)
        weights = [math.exp(value - maximum) for value in values]
        total = sum(weights)
        probabilities = [value / total for value in weights]
        index = 0 if values[0] >= values[1] else 1
        records.append({
            "row_id": row_id,
            "payload_sha256": packet_data.payload_hash(payload),
            "class_index": index,
            "class_name": _CLASS_NAMES[index],
            "logits": values,
            "probabilities": probabilities,
            "probability": probabilities[index],
            "probability_kind": "uncalibrated_softmax",
        })
    return records


def _predict_batch(model, torch, batch, device, stream, receipt):
    payload = torch.tensor([list(values) for _, values in batch], dtype=torch.uint8, device=device)
    with torch.inference_mode():
        result = packet_model.forward_payload(model, payload)
    if not isinstance(result, dict) or "logits" not in result:
        raise ValueError("Native packet inference did not return logits")
    logits = result["logits"].detach().cpu().tolist()
    records = format_predictions(batch, logits)
    for record in records:
        stream.write(json.dumps(record, separators=(",", ":"), allow_nan=False) + "\n")
        receipt["predicted_rows"] += 1


def execute(checkpoint, csv_path, output, upstream, *, batch_size=64, max_rows=None, device="cuda"):
    """Run streaming inference in a fresh output directory and return its receipt.

    Successful full coverage is 'complete'; an explicitly limited prefix is
    'capped'. Exceptions propagate after recording 'incomplete'. Until success,
    both the initial receipt and predictions.incomplete.jsonl visibly identify
    unfinished work, including an external interruption that cannot be caught.
    """
    _positive_integer(batch_size, "batch_size")
    if max_rows is not None:
        _positive_integer(max_rows, "max_rows")
    if not isinstance(device, str) or not device:
        raise ValueError("device must name a Torch device")
    output = Path(output).absolute()
    if os.path.lexists(output):
        raise FileExistsError(f"Refusing to overwrite inference output: {output}")
    checkpoint = Path(checkpoint).resolve()
    csv_path = Path(csv_path).resolve()
    upstream = Path(upstream).resolve()
    output.mkdir(parents=True, exist_ok=False)
    partial = output / "predictions.incomplete.jsonl"
    complete = output / "predictions.jsonl"
    receipt = {
        "kind": "netmambaplus_unlabeled_packet_inference_v1", "schema_version": 1,
        "status": "incomplete", "stage": "initialization",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "finished_at": None, "counts_finalized": False,
        "input": {"path": str(csv_path)}, "checkpoint": {"path": str(checkpoint)},
        "upstream": str(upstream), "checkpoint_metadata": None,
        "code_sha256": {}, "batch_size": batch_size, "max_rows": max_rows, "device": device,
        "input_rows": None, "validated_rows": 0, "predicted_rows": 0,
        "input_fully_validated": False, "all_rows_predicted": False,
        "ignored_metadata_columns": [], "predictions": None,
        "probability_kind": "uncalibrated_softmax", "class_mapping": {"benign": 0, "attack": 1},
        "scope": "CSV-supplied stored payloads only. No labels, flow reconstruction, padding inference, "
                 "ground-truth metrics, calibrated risk estimates, or live traffic decisions.",
    }
    _write_receipt(output, receipt)
    try:
        receipt["stage"] = "fingerprints"
        for relative in ["tools/predict_packets.py", "packet_data.py", "packet_model.py"]:
            receipt["code_sha256"][relative] = _fingerprint(ROOT / relative)["sha256"]
        receipt["checkpoint"] = _fingerprint(checkpoint)
        model = torch = None
        batch = []
        with partial.open("x", encoding="utf-8", newline="") as destination, csv_path.open("rb") as raw:
            before = os.fstat(raw.fileno())
            receipt["input"] = {**_fingerprint_stream(raw, csv_path), "sha256_scope": "entire_file"}
            raw.seek(0)
            with io.TextIOWrapper(raw, encoding="utf-8", newline="") as source:
                reader = csv.reader(source, strict=True)
                receipt["stage"] = "input_validation"
                header = next(reader, None)
                if header not in (PAYLOAD_COLUMNS, PAYLOAD_COLUMNS + METADATA_COLUMNS):
                    raise ValueError("Require the exact unlabeled payload header, optionally followed by "
                                     "ttl,total_len,protocol,t_delta; label columns are forbidden")
                receipt["ignored_metadata_columns"] = header[1500:]
                try:
                    for row_id, row in enumerate(reader):
                        receipt["stage"] = "input_validation"
                        canonical = _payload_from_row(row, row_id, len(header))
                        receipt["validated_rows"] += 1
                        if max_rows is not None and row_id >= max_rows:
                            continue
                        batch.append((row_id, canonical))
                        if model is None:
                            receipt["stage"] = "checkpoint_loading"
                            import torch
                            model, metadata = packet_model.load_checkpoint(checkpoint, upstream, device=device)
                            binding = metadata["checkpoint"]
                            if (binding["sha256"] != receipt["checkpoint"]["sha256"]
                                    or binding["bytes"] != receipt["checkpoint"]["bytes"]):
                                raise ValueError("Loaded checkpoint does not match the fingerprinted input")
                            receipt["checkpoint_metadata"] = {key: value for key, value in metadata.items()
                                                              if key != "checkpoint"}
                            model.eval()
                        if len(batch) == batch_size or (max_rows is not None and row_id + 1 == max_rows):
                            receipt["stage"] = "inference"
                            _predict_batch(model, torch, batch, device, destination, receipt)
                            batch.clear()
                except (csv.Error, UnicodeError) as error:
                    raise ValueError("Malformed UTF-8 CSV input") from error
                if receipt["validated_rows"] == 0:
                    raise ValueError("Unlabeled CSV must contain at least one packet row")
                if (_identity(before) != _identity(os.fstat(raw.fileno()))
                        or _identity(before) != _path_identity(csv_path)):
                    raise ValueError("Input CSV changed during inference")
                receipt["input_fully_validated"] = True
                receipt["input_rows"] = receipt["validated_rows"]
            if batch:
                receipt["stage"] = "inference"
                _predict_batch(model, torch, batch, device, destination, receipt)
            destination.flush()
            os.fsync(destination.fileno())
        receipt["stage"] = "final_verification"
        if _fingerprint(checkpoint)["sha256"] != receipt["checkpoint"]["sha256"]:
            raise ValueError("Packet checkpoint changed during inference")
        # Include the final short batch in the mutation check, after its forward call.
        if _identity(before) != _path_identity(csv_path):
            raise ValueError("Input CSV changed during inference")
        for relative, digest in receipt["code_sha256"].items():
            if _fingerprint(ROOT / relative)["sha256"] != digest:
                raise ValueError(f"Inference implementation changed during execution: {relative}")
        expected = min(receipt["input_rows"], max_rows) if max_rows is not None else receipt["input_rows"]
        if receipt["predicted_rows"] != expected:
            raise ValueError("Prediction count does not match the declared input prefix")
        os.link(partial, complete)
        partial.unlink()
        receipt["predictions"] = {**_fingerprint(complete), "path": complete.name}
        receipt["all_rows_predicted"] = receipt["predicted_rows"] == receipt["input_rows"]
        receipt["status"] = "complete" if receipt["all_rows_predicted"] else "capped"
        receipt["stage"] = "finished"
        receipt["finished_at"] = datetime.now(timezone.utc).isoformat()
        receipt["counts_finalized"] = True
        _write_receipt(output, receipt)
        return receipt
    except BaseException as error:
        receipt["status"] = "incomplete"
        receipt["all_rows_predicted"] = False
        receipt["counts_finalized"] = True
        receipt["finished_at"] = datetime.now(timezone.utc).isoformat()
        receipt["error"] = {"type": type(error).__name__, "message": str(error)}
        existing = partial if partial.is_file() else complete
        if existing.is_file():
            receipt["predictions"] = {**_fingerprint(existing), "path": existing.name}
        _write_receipt(output, receipt)
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", required=True, type=Path)
    parser.add_argument("--csv", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path,
                        help="Fresh output directory for predictions.jsonl and receipt.json")
    parser.add_argument("--upstream", required=True, type=Path)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--max-rows", type=int, default=None,
                        help="Predict at most this many initial rows; still validate and hash the entire CSV")
    parser.add_argument("--device", default="cuda")
    args = parser.parse_args(argv)
    try:
        receipt = execute(args.checkpoint, args.csv, args.output, args.upstream,
                          batch_size=args.batch_size, max_rows=args.max_rows, device=args.device)
    except Exception as error:
        print(f"Packet inference failed: {error}. Any created receipt is incomplete: "
              f"{args.output / 'receipt.json'}", file=sys.stderr)
        return 1
    print(json.dumps({"status": receipt["status"], "input_rows": receipt["input_rows"],
                      "predicted_rows": receipt["predicted_rows"],
                      "receipt": str(args.output / "receipt.json")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
