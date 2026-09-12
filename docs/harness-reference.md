# Harness reference

This reference preserves the detailed validation and manifest contract. For the tested GPU setup, current results and presentation files, start with [the customer package](customer/README.md) and [runbook](customer/runbook.md).

## Native data contract

Each split is a nonempty JSON array of flows. This abbreviated, synthetic record illustrates the types; it is not a captured packet:

```json
{
  "data": ["69 0 0 64", "69 0 0 52"],
  "sizes": "64 52",
  "intervals": "0 0.001",
  "num_packet": 2,
  "label": 0,
  "name": "6-Attacks-1-Flood",
  "pcap_file": "example-flow-001.pcap"
}
```

`data` contains integer bytes from 0 through 255. `sizes` and `intervals` are literal-space-separated numeric strings of equal length. Sizes must be finite; intervals must be finite and nonnegative. Short flows and sequences longer than twenty are valid. The original loader determines which values are retained or padded. Optional `num_packet` is checked for a nonnegative integer but is not substituted for the actual arrays; the native loader does not use it to reconstruct missing packets.

`metadata.json` contains `name_to_idx`, an object mapping each class name to one unique integer starting at zero, without gaps. Every record's `name` and `label` must agree with it. The default preset requires six classes and derives the classifier's output count from this mapping:

| Index | Released class name |
|---|---|
| 0 | `6-Attacks-1-Flood` |
| 1 | `6-Attacks-2-RTSP Brute Force` |
| 2 | `1-Power-Audio` |
| 3 | `1-Power-Other` |
| 4 | `1-Power-Cameras` |
| 5 | `1-Power-Home Automation` |

Validate and save the report before training:

```bash
python3 repro.py validate --data data/ciciot2022 --report runs/validation.json
```

Full-split validation reads all three splits, checks labels, reports class counts and identifier coverage, and rejects shared recorded `pcap_file` identifiers across splits. Missing identifiers are reported as missing evidence; they do not establish independence.

`--report` requires a new destination: it refuses to replace any existing file, including data, configuration, earlier reports and symbolic links. Choose a new report filename when repeating a recorded validation. Validation and invocation resolve settings in the same order: `common`, followed by the selected stage's overrides. Evaluation uses the fine-tuning stage settings. The report records the effective `size_key`, and both validation and duplicate fingerprints use that field.

Raw-input fingerprints are SHA-256 of UTF-8 `json.dumps([data, sizes, intervals], ensure_ascii=False, separators=(",", ":"))`. For a custom `size_key`, that field replaces `sizes`. Labels and provenance identifiers are excluded. String formatting is retained: this measures exact stored-input equality, not equality after normalization or padding. `shared_raw_inputs` counts distinct fingerprints in both splits; `left_rows` and `right_rows` count all rows carrying those fingerprints. `duplicate_excess` is rows minus distinct fingerprints within a split. Reports never alter or deduplicate the data.


## Separate strict test evaluation

This route measures an already fine-tuned classifier. It can run with only metadata and test data present:

```bash
mkdir -p data/ciciot2022-test-only
cp data/ciciot2022/metadata.json data/ciciot2022-test-only/
cp data/ciciot2022/data-test.json data/ciciot2022-test-only/
python3 repro.py evaluate --data data/ciciot2022-test-only --checkpoint runs/ciciot-ft-seed0/checkpoint-best.pth --output runs/ciciot-eval-dry --dry-run
python3 repro.py evaluate --data data/ciciot2022-test-only --checkpoint runs/ciciot-ft-seed0/checkpoint-best.pth --output runs/ciciot-eval
```

`evaluate.py` loads checkpoint storage on CPU, requires `checkpoint["model"]`, constructs the original classifier and calls `load_state_dict(..., strict=True)`. It moves the model to the requested device, builds exactly one test loader, verifies the loader's class mapping and calls the original `engine_mm.evaluate`. It never enters the native fine-tuning `main` or reads/hashes training and validation datasets. The separate entry point also avoids the pinned fine-tuner's `--eval` branch, which references its test loader before construction.

Incompatible keys or tensor shapes cause failure; there is no head replacement or non-strict evaluation fallback. The evaluator uses the original internal CUDA autocast, even though the source preset passes `--no_amp`. That flag does not switch this evaluator to full precision.

A successful fine-tuning manifest binds `checkpoint-best.pth` to its SHA-256 and class mapping. Evaluation discovers this sibling `manifest.json` automatically. If a classifier is moved elsewhere, pass `--provenance /path/to/its/manifest.json`; an explicit mapping document may also contain `checkpoint_sha256` and `class_mapping`. Explicit hash mismatches and established class-order conflicts fail. Without a matching binding, outputs retain `class_order: "unknown"` and `training_history: "unknown"`. Hash binding records a claim about one exact file; it does not independently authenticate that claim or recover unknown pretraining history. Only load checkpoints from a trusted source: the native format uses Python pickle deserialization.

`metrics.json` preserves every key from the native test-state dictionary, including weighted metrics, per-class arrays, support and confusion matrix. NumPy-like scalars/arrays become ordinary JSON; nonfinite values become `null`, with their JSON-pointer paths recorded separately. No metric is silently discarded or replaced by a claimed result. For custom test subsets lacking classes, the unchanged native metric arrays may omit absent classes; do not blindly assign every array position to all six metadata classes.

## What each manifest establishes

Execution stages create `manifest.json` atomically before substantive preflight when the output is writable. They distinguish `preflight_failed`, `dry_run`, `running`, `succeeded` and `failed`. Each completed record includes the stage, timestamps, configuration/provenance, hashes of both harness scripts, upstream source pin and core hashes, stage-specific input hashes, class mapping, applicable checkpoint hashes, full parsed native arguments, command, working directory, selected runtime versions and exit/error details. Only an allowlist of relevant environment values is recorded.

Pretraining hashes its selected training file and metadata; fine-tuning hashes all three splits and metadata; separate evaluation hashes only test data and metadata, plus its checkpoint and available provenance information. Inputs and the checkpoint are checked again after execution. Every run requires a new or empty output directory. Pre-existing artifacts cause rejection before preflight, and atomic initial-manifest creation gives only one concurrent invocation ownership of a directory. Existing files remain untouched when ownership is refused. A hard kill or power loss can leave a `running` record; that is not success. Source checks establish the inspected checkout, not a security sandbox or proof that installed dependencies are identical.
