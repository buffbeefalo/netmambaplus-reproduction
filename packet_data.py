"""Canonical local preparation of the two uploaded packet CSVs.

Import and validation need only the standard library. Preparation imports NumPy
only when writing arrays. A completed output has a manifest.json; an interrupted
or rejected preparation may leave its fresh output directory for inspection.
All 1,500 stored bytes are retained. Metadata establishes neither flow identity
nor which zero bytes are padding, and never affects grouping or split selection.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from numbers import Integral, Real
from pathlib import Path


LABELS = {
    "cic": [
        "BENIGN", "DoS Hulk", "DDoS", "DoS GoldenEye", "DoS slowloris",
        "Infiltration", "DoS Slowhttptest", "SSH-Patator", "FTP-Patator",
        "Heartbleed", "Web Attack – Brute Force", "Web Attack – XSS", "Bot",
        "PortScan", "Web Attack – Sql Injection",
    ],
    "unsw": [
        "normal", "generic", "exploits", "fuzzers", "reconnaissance", "dos",
        "backdoor", "analysis", "shellcode", "worms",
    ],
}
PAYLOAD_LENGTH = 1500
PAYLOAD_COLUMNS = [f"payload_byte_{index}" for index in range(1, PAYLOAD_LENGTH + 1)]
METADATA_COLUMNS = ["ttl", "total_len", "protocol", "t_delta", "label"]
CSV_COLUMNS = PAYLOAD_COLUMNS + METADATA_COLUMNS
SPLIT_NAMES = ("train", "validation", "test")
REGISTERED_SOURCE_HASHES = {
    "cic": "2ac7ee140ae5a5d0d8df0d550434580c056ed9458977bfcc33706c872d390d6e",
    "unsw": "39616dd8e397673500ed6c51a09fe5638c29d27454467d8aef925ca79a295f01",
}
_CANONICAL_BYTE_TOKENS = {str(value): value for value in range(256)}
_NUMERIC_TOKEN = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?")
_HEX_DIGEST = re.compile(r"[0-9a-f]{64}")
_LABEL_INDEX = {source: {label: index for index, label in enumerate(labels)}
                for source, labels in LABELS.items()}


def binary_label(source, label) -> int:
    """Map only explicitly enumerated labels; the first source label is benign."""
    if not isinstance(source, str) or source not in _LABEL_INDEX:
        raise ValueError(f"unknown packet source: {source!r}")
    if not isinstance(label, str) or label not in _LABEL_INDEX[source]:
        raise ValueError(f"unknown {source} label: {label!r}")
    return int(_LABEL_INDEX[source][label] != 0)


def _byte_value(value) -> int:
    if isinstance(value, bool):
        raise ValueError("boolean payload slots are invalid")
    if isinstance(value, str):
        token = value.strip()
        if _NUMERIC_TOKEN.fullmatch(token) is None:
            raise ValueError("payload slots must be numeric byte values")
        try:
            value = Decimal(token)
        except InvalidOperation as error:
            raise ValueError("invalid numeric payload slot") from error
    if isinstance(value, Decimal):
        valid = value.is_finite() and 0 <= value <= 255 and value == value.to_integral_value()
    elif isinstance(value, Integral):
        valid = 0 <= value <= 255
    elif isinstance(value, Real):
        valid = math.isfinite(value) and 0 <= value <= 255 and value == int(value)
    else:
        valid = False
    if not valid:
        raise ValueError("payload slots must be finite integers in [0, 255]")
    return int(value)


def validate_payload(values) -> bytes:
    """Validate exact integer values before conversion, including decimal text."""
    if isinstance(values, str):
        raise ValueError("payload must be a sequence of 1500 byte slots")
    try:
        slots = tuple(values)
    except TypeError as error:
        raise ValueError("payload must be a sequence of 1500 byte slots") from error
    if len(slots) != PAYLOAD_LENGTH:
        raise ValueError("payload must contain exactly 1500 byte slots")
    return bytes(map(_byte_value, slots))


def payload_hash(payload: bytes) -> str:
    """SHA-256 identifies the exact canonical 1,500 stored bytes."""
    if not isinstance(payload, bytes) or len(payload) != PAYLOAD_LENGTH:
        raise ValueError("payload hash requires exactly 1500 canonical bytes")
    return hashlib.sha256(payload).hexdigest()


def _nonnegative_integer(value, name):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")


def split_for_hash(hex_digest, seed=17) -> int:
    """Assign global groups to 70/15/15 partitions without labels or sources.

    Hash the domain, decimal seed, and raw digest with NUL separators. Compare
    its first eight bytes as an unsigned big-endian integer against floor
    (2**64 * 70 / 100) and floor(2**64 * 85 / 100). This rule is platform-stable.
    """
    if not isinstance(hex_digest, str) or _HEX_DIGEST.fullmatch(hex_digest) is None:
        raise ValueError("payload digest must be 64 lowercase hexadecimal characters")
    _nonnegative_integer(seed, "seed")
    message = b"packet-data-split-v1\0" + str(seed).encode("ascii") + b"\0" + bytes.fromhex(hex_digest)
    score = int.from_bytes(hashlib.sha256(message).digest()[:8], "big")
    return 0 if score < (2**64 * 70 // 100) else (1 if score < (2**64 * 85 // 100) else 2)


class _HashingReader(io.RawIOBase):
    """Fingerprint the same raw byte stream consumed by the CSV decoder."""

    def __init__(self, raw):
        self.raw = raw
        self.digest = hashlib.sha256()
        self.bytes_read = 0

    def readable(self):
        return True

    def readinto(self, buffer):
        count = self.raw.readinto(buffer)
        if count:
            self.digest.update(memoryview(buffer)[:count])
            self.bytes_read += count
        return count


@dataclass(slots=True)
class _GlobalGroup:
    payload: bytes
    counts: list[int] = field(default_factory=lambda: [0, 0])
    source_rows: list[int] = field(default_factory=lambda: [0, 0])


def _stat_identity(value):
    return value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns


def _scan_source(source, path, directory, global_groups):
    groups = {}
    source_index = list(LABELS).index(source)
    row_count = 0
    with path.open("rb") as raw:
        before = os.fstat(raw.fileno())
        hashed = _HashingReader(raw)
        with io.TextIOWrapper(io.BufferedReader(hashed), encoding="utf-8", newline="") as stream, \
                (directory / "metadata.csv").open("x", encoding="utf-8", newline="") as metadata:
            reader = csv.reader(stream, strict=True)
            writer = csv.writer(metadata)
            writer.writerow(["source", "row_id", "payload_sha256", *METADATA_COLUMNS, "binary_label"])
            try:
                if next(reader, None) != CSV_COLUMNS:
                    raise ValueError(f"{source}: CSV header does not match the exact 1505-column schema")
                for row_id, row in enumerate(reader):
                    if len(row) != len(CSV_COLUMNS):
                        raise ValueError(f"{source} row {row_id}: expected exactly 1505 columns")
                    label = row[-1]
                    binary = binary_label(source, label)
                    slots = row[:PAYLOAD_LENGTH]
                    try:
                        # The common integer spelling takes a fast exact lookup.
                        # Other spellings receive decimal validation, never float casting.
                        canonical = bytes(map(_CANONICAL_BYTE_TOKENS.__getitem__, slots))
                    except KeyError:
                        try:
                            canonical = validate_payload(slots)
                        except ValueError as error:
                            raise ValueError(f"{source} row {row_id}: {error}") from error
                    digest = hashlib.sha256(canonical).digest()
                    global_group = global_groups.get(digest)
                    if global_group is None:
                        global_group = global_groups[digest] = _GlobalGroup(canonical)
                    elif global_group.payload != canonical:
                        raise ValueError("different payloads have the same SHA-256; grouping aborted")
                    global_group.counts[binary] += 1
                    global_group.source_rows[source_index] += 1
                    if digest not in groups:
                        groups[digest] = [0] * len(LABELS[source])
                    groups[digest][_LABEL_INDEX[source][label]] += 1
                    writer.writerow([source, row_id, digest.hex(), *row[PAYLOAD_LENGTH:], binary])
                    row_count += 1
            except (csv.Error, UnicodeError) as error:
                raise ValueError(f"{source}: malformed UTF-8 CSV near record {row_count}") from error
            after = os.fstat(raw.fileno())
            if (_stat_identity(before) != _stat_identity(after)
                    or _stat_identity(before) != _stat_identity(path.stat())
                    or hashed.bytes_read != before.st_size):
                raise ValueError(f"{source}: source changed while preparation was reading it")
    if row_count == 0:
        raise ValueError(f"{source}: CSV must contain at least one data row")
    fingerprint = {"path": str(path), "bytes": hashed.bytes_read, "sha256": hashed.digest.hexdigest()}
    return groups, fingerprint


def _file_fingerprint(path, root):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return {"path": path.relative_to(root).as_posix(), "bytes": path.stat().st_size,
            "sha256": digest.hexdigest()}


def _support(hashes, counts, subtypes, labels, mask):
    selected_counts = counts[mask]
    selected_subtypes = subtypes[mask]
    return {
        "groups": int(selected_counts.shape[0]),
        "rows": int(selected_counts.sum()),
        "binary_counts": selected_counts.sum(axis=0).tolist(),
        "label_counts": dict(zip(labels, selected_subtypes.sum(axis=0).tolist())),
        "label_group_counts": dict(zip(labels, (selected_subtypes > 0).sum(axis=0).tolist())),
        "binary_conflicting_groups": int(((selected_counts[:, 0] > 0) & (selected_counts[:, 1] > 0)).sum()),
        "membership_sha256": hashlib.sha256(hashes[mask].tobytes()).hexdigest(),
    }


def _write_source(source, groups, fingerprint, output, global_groups, np, seed, caps):
    directory = output / source
    ordered = sorted(groups)
    hashes = np.frombuffer(b"".join(ordered), dtype="V32").copy()
    subtypes = np.asarray([groups[digest] for digest in ordered], dtype=np.int64)
    counts = np.column_stack((subtypes[:, 0], subtypes[:, 1:].sum(axis=1)))
    splits = np.fromiter((split_for_hash(digest.hex(), seed=seed) for digest in ordered), dtype=np.uint8)
    selected = np.zeros(len(ordered), dtype=np.bool_)
    for index, cap in enumerate(caps):
        selected[np.flatnonzero(splits == index)[:cap]] = True

    payload_path = directory / "payload.npy"
    payload = np.lib.format.open_memmap(payload_path, mode="w+", dtype=np.uint8,
                                        shape=(len(ordered), PAYLOAD_LENGTH))
    for start in range(0, len(ordered), 4096):
        chunk = b"".join(global_groups[digest].payload for digest in ordered[start:start + 4096])
        payload[start:start + 4096] = np.frombuffer(chunk, dtype=np.uint8).reshape(-1, PAYLOAD_LENGTH)
    payload.flush()
    del payload
    arrays = {"hashes.npy": hashes, "counts.npy": counts, "subtypes.npy": subtypes,
              "split.npy": splits, "selected.npy": selected}
    for filename, array in arrays.items():
        with (directory / filename).open("xb") as stream:
            np.save(stream, array, allow_pickle=False)
    files = {}
    for filename in ["payload.npy", *arrays, "metadata.csv"]:
        files[filename] = _file_fingerprint(directory / filename, output)
        if filename == "payload.npy":
            files[filename].update(dtype="uint8", shape=[len(ordered), PAYLOAD_LENGTH])
        elif filename in arrays:
            files[filename].update(dtype=str(arrays[filename].dtype), shape=list(arrays[filename].shape))

    all_support = _support(hashes, counts, subtypes, LABELS[source], np.ones(len(ordered), dtype=bool))
    row_counts = counts.sum(axis=1)
    conflicting = (counts[:, 0] > 0) & (counts[:, 1] > 0)
    largest = np.lexsort((np.arange(len(ordered)), -row_counts))[:10]
    record = {
        **fingerprint, **all_support, "files": files,
        "registered_source_sha256": REGISTERED_SOURCE_HASHES[source],
        "matches_registered_source": fingerprint["sha256"] == REGISTERED_SOURCE_HASHES[source],
        "duplicate_rows": int(row_counts.sum() - len(ordered)),
        "payload_cells_validated": int(row_counts.sum()) * PAYLOAD_LENGTH,
        "multiclass_conflicting_groups": int(((subtypes > 0).sum(axis=1) > 1).sum()),
        "rows_in_binary_conflicting_groups": int(row_counts[conflicting].sum()),
        "largest_group_rows": int(row_counts.max()),
        "largest_groups": [
            {"payload_sha256": ordered[index].hex(), "rows": int(row_counts[index]),
             "binary_counts": counts[index].tolist(),
             "label_counts": dict(zip(LABELS[source], subtypes[index].tolist()))}
            for index in largest
        ],
        "splits": {},
    }
    for index, name in enumerate(SPLIT_NAMES):
        support = _support(hashes, counts, subtypes, LABELS[source], splits == index)
        chosen = _support(hashes, counts, subtypes, LABELS[source], (splits == index) & selected)
        support.update({f"selected_{key}": value for key, value in chosen.items()})
        record["splits"][name] = support
    return record


def _global_support(global_groups, seed):
    ordered = sorted(global_groups)
    shared = [digest for digest in ordered if all(global_groups[digest].source_rows)]
    conflicting = [digest for digest in ordered if all(global_groups[digest].counts)]
    return {
        "groups": len(ordered),
        "rows": sum(sum(group.counts) for group in global_groups.values()),
        "binary_counts": [sum(group.counts[index] for group in global_groups.values()) for index in range(2)],
        "membership_sha256": hashlib.sha256(b"".join(ordered)).hexdigest(),
        "shared_groups": len(shared),
        "shared_rows": {source: sum(global_groups[digest].source_rows[index] for digest in shared)
                        for index, source in enumerate(LABELS)},
        "binary_conflicting_groups": len(conflicting),
        "rows_in_binary_conflicting_groups": sum(sum(global_groups[digest].counts) for digest in conflicting),
        "shared_binary_conflicting_groups": sum(all(global_groups[digest].counts) for digest in shared),
        "largest_group_rows": max(sum(group.counts) for group in global_groups.values()),
        "splits": {
            name: {"groups": len(members), "membership_sha256": hashlib.sha256(b"".join(members)).hexdigest()}
            for index, name in enumerate(SPLIT_NAMES)
            for members in [[digest for digest in ordered if split_for_hash(digest.hex(), seed=seed) == index]]
        },
    }


def prepare(cic_path, unsw_path, output, *, seed=17, max_train_groups=100000, max_eval_groups=20000) -> dict:
    """Scan both complete CSVs into a new local directory and return its manifest.

    Per-source groups use global payload identities and splits, retaining both
    binary-label counts and every original-label count. Selection is the first
    capped number of hashes within each source/split; class outcomes and row
    multiplicity have no role in selection. Source fingerprints describe the
    actual inputs; matches_registered_source identifies the two original uploads
    without preventing reproducible small fixtures from using the same API.
    """
    _nonnegative_integer(seed, "seed")
    for name, value in [("max_train_groups", max_train_groups), ("max_eval_groups", max_eval_groups)]:
        _nonnegative_integer(value, name)
        if value == 0:
            raise ValueError(f"{name} must be a positive integer")
    output = Path(output).absolute()
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"output already exists: {output}")
    paths = {"cic": Path(cic_path).resolve(strict=True), "unsw": Path(unsw_path).resolve(strict=True)}
    if any(not path.is_file() for path in paths.values()):
        raise ValueError("both sources must be regular CSV files")
    try:
        import numpy as np
    except ImportError as error:
        raise RuntimeError("NumPy is required for preparation; validation and --help need only Python") from error
    output.mkdir(parents=True, exist_ok=False)
    caps = (max_train_groups, max_eval_groups, max_eval_groups)
    global_groups = {}
    sources = {}
    # The shared dictionary compares canonical bytes across sources before any
    # split/selection is emitted. Source dictionaries retain their own counts.
    scanned = {}
    for source, path in paths.items():
        directory = output / source
        directory.mkdir()
        scanned[source] = _scan_source(source, path, directory, global_groups)
    for source, (groups, fingerprint) in scanned.items():
        sources[source] = _write_source(source, groups, fingerprint, output, global_groups, np, seed, caps)
    manifest = {
        "schema_version": 1,
        "status": "prepared",
        "implementation": _file_fingerprint(Path(__file__).resolve(), Path(__file__).resolve().parent),
        "numpy_version": np.__version__,
        "sources": sources,
        "global": _global_support(global_groups, seed),
        "labels": LABELS,
        "schema": {"columns": CSV_COLUMNS, "payload_byte_columns": PAYLOAD_LENGTH,
                   "metadata_columns": METADATA_COLUMNS,
                   "row_id": "zero-based CSV data record index; header excluded"},
        "input_contract": {"unit": "one stored packet payload", "payload_length": PAYLOAD_LENGTH,
                           "dtype": "uint8", "model_inputs": ["payload"],
                           "excluded_columns": METADATA_COLUMNS, "stored_zeros": "retained"},
        "split": {"seed": seed, "names": list(SPLIT_NAMES), "target_group_fractions": [0.7, 0.15, 0.15],
                  "algorithm": "SHA256(b'packet-data-split-v1\\0' + ASCII(seed) + b'\\0' + raw payload SHA256); "
                               "first 8 bytes big-endian; thresholds floor(2**64*70/100), floor(2**64*85/100)",
                  "membership_sha256": "SHA256 of concatenated raw 32-byte payload digests in ascending order",
                  "independence": "exact payload identity only; physical flow/capture independence is unknown"},
        "selection": {"unit": "unique payload group within source and split",
                      "order": "ascending raw payload SHA256", "caps": dict(zip(SPLIT_NAMES, caps)),
                      "uses_labels_metadata_or_multiplicity": False},
        "scope": "All source rows and contradictory labels are retained locally. Group membership proves exact "
                 "stored-payload isolation, not packet, flow, capture, or attack-family identity. Metadata is "
                 "retained without inferring padding, true byte length, timing units, or packet ordering.",
    }
    with (output / "manifest.json").open("x", encoding="utf-8") as stream:
        json.dump(manifest, stream, indent=2, ensure_ascii=False, sort_keys=True)
        stream.write("\n")
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cic", required=True, type=Path)
    parser.add_argument("--unsw", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--max-train-groups", type=int, default=100000)
    parser.add_argument("--max-eval-groups", type=int, default=20000)
    args = parser.parse_args(argv)
    try:
        manifest = prepare(args.cic, args.unsw, args.output, seed=args.seed,
                           max_train_groups=args.max_train_groups, max_eval_groups=args.max_eval_groups)
    except (ValueError, OSError, RuntimeError) as error:
        parser.exit(2, f"packet preparation failed: {error}\n")
    print(json.dumps({"status": manifest["status"], "manifest": str(args.output / "manifest.json"),
                      "rows": manifest["global"]["rows"], "groups": manifest["global"]["groups"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
