# Run the packet study

Read [what this experiment means](packet-model-study.md) first. Commands below run from the repository root and use fresh output paths. Keep raw CSVs, prepared arrays and inherited weights local.

## 1. Check Python and prepare the research runtime

Portable contract tests need Python 3.10 or newer:

```bash
python3 -m unittest discover -s tests -p 'test_packet*.py' -v
```

Optional numerical/native tests may be skipped. Passing this command does not execute a CPU neural-model backend.

For training, first complete the [CUDA installation, extension build and numerical/model gates](../support-matrix.md#build-the-model-dependencies-on-linux-with-an-nvidia-gpu). The checked native environment is Linux ARM64 on NVIDIA GB10 with Python 3.12, Torch 2.9.1+cu130 and CUDA 13.0. Other physical model backends remain unverified. Then activate that environment and fetch the pinned source and original assets:

```bash
source .venv-cuda/bin/activate
export CUDA_HOME=/usr/local/cuda-13.0
export PATH="$CUDA_HOME/bin:$PATH"
export TRITON_PTXAS_PATH="$CUDA_HOME/bin/ptxas"
export PYTHONDONTWRITEBYTECODE=1
python repro.py fetch
python tools/fetch_assets.py --output assets
```

Use your actual environment/toolkit paths. The asset fetcher checks sizes and hashes; it also downloads the original flow assets. The packet initialization is `assets/checkpoints/fuse3_mamba.pth`.

## 2. Prepare both original CSVs and freeze this run

Replace the two input paths with your local uploads:

```bash
python packet_data.py \
  --cic /path/to/CICIDS2017.csv --unsw /path/to/UNSW.csv \
  --output runs/packet-data-new --seed 17 \
  --max-train-groups 100000 --max-eval-groups 20000
python tools/freeze_packet_protocol.py \
  --data runs/packet-data-new --output runs/packet-protocol-new.json --steps 1000
```

Inspect `manifest.json`: both `matches_registered_source` values should be true when reproducing the uploaded-file study. It records source hashes, all-row support, selected membership and local output hashes.

[configs/packet-study.json](../../configs/packet-study.json) records the completed study’s frozen protocol. The freezer above creates your own protocol bound to your fresh manifest and current implementation. Freeze the budget before measured training; preserve any failed run and use new paths for another attempt.

## 3. Freeze controls, then train and evaluate

First fit all nine controls using training groups only. This command binds them to your protocol before control test inference:

```bash
PACKET_PROTOCOL_SHA="$(python -c 'import hashlib; from pathlib import Path; print(hashlib.sha256(Path("runs/packet-protocol-new.json").read_bytes()).hexdigest())')"
python tools/packet_controls.py fit \
  --data runs/packet-data-new --output runs/packet-controls-new \
  --protocol-sha256 "$PACKET_PROTOCOL_SHA"
```

Then run the six native models:

```bash
python tools/train_packet_model.py \
  --data runs/packet-data-new --protocol runs/packet-protocol-new.json \
  --output runs/packet-study-new --upstream upstream/NetMambaPlus \
  --initialization assets/checkpoints/fuse3_mamba.pth
```

The runner trains all six arms, selects checkpoints using validation, and performs both source tests after selection freezes. Inspect training receipts, `frozen-checkpoints.json`, `results.json`, and any `failure.json`. The requested budget is not proof that it completed.

Evaluate the already frozen controls using the same output directory; this creates its new `evaluation/` subdirectory:

```bash
python tools/packet_controls.py evaluate \
  --data runs/packet-data-new --output runs/packet-controls-new
```

Check `frozen-controls.json` and `evaluation/results.json`, including convergence records. The published run completed all nine controls; its six logistic fits converged. Interpret these alongside the native results, especially the strong UNSW metadata control.

## 4. Predict an unlabeled CSV

Use the joint model’s selected checkpoint path from `frozen-checkpoints.json`, relative to `runs/packet-study-new`. Substitute that actual file below:

```bash
python tools/predict_packets.py \
  --checkpoint path/to/selected-packet-checkpoint.pth \
  --csv /path/to/unlabeled-packets.csv --output runs/packet-predictions-new \
  --upstream upstream/NetMambaPlus --batch-size 64
```

The header must contain exactly `payload_byte_1` through `payload_byte_1500`, optionally followed by `ttl,total_len,protocol,t_delta`. Create a separate unlabeled copy if necessary: a `label` column is rejected. No flow assembly is required.

`predictions.jsonl` contains row identity, payload hash, two logits, class and uncalibrated probabilities. All 25,930 held-out classes agreed with the recorded joint-model evaluation in the separate native check. Small raw-score differences remain across CUDA executions; the report preserves the exact failed numerical comparisons. Do not require bit-identical logits across backends or reuse the original flow-model calibration. `receipt.json` binds input, checkpoint, code and training provenance. Optional `--max-rows 128` limits predictions while still validating and hashing the entire CSV; the receipt reports capped coverage. Failures retain explicitly incomplete outputs.

## 5. Recheck published evidence offline

Run the checks against the published indexed evidence bundle:

```bash
python3 tools/review_packet_study.py --evidence docs/customer/evidence/packet-study
python tools/review_packet_study.py --evidence docs/customer/evidence/packet-study --independent
```

The first command checks file identities, training completion, test membership, arithmetic and retained unlabeled inference without a GPU. It reports the two strict numerical-comparison failures while confirming every predicted class. The optional second uses NumPy/scikit-learn for separate metric comparisons. Neither retrains models or proves independent captures.

## Recorded checks for this addition

The complete local suite discovered 395 tests: 359 passed and 36 optional numerical/native checks were skipped in the standard-library environment. Separately, all 17 packet-model tests passed in the checked GB10 environment, including native transfer, gradient and checkpoint checks. Independent scikit-learn arithmetic matched all 12 neural-model test sets and 18 control test sets. Original package, calibration, course/video history and watch-page checks also passed; the every-file guide covered 604 files.

These software checks accompany the six completed training runs and full saved-model inference; they are not replacements for those experiments. GitHub's [verification runs](https://github.com/buffbeefalo/netmambaplus-reproduction/actions/workflows/ci.yml) report portable tests separately for Linux, Windows and macOS. They do not test native GPU training on those hosted systems.
