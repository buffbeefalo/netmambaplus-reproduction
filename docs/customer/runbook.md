# Run the measured experiment and demo

The [customer index](README.md) is the presentation entry point. The recorded HTML replay opens offline without Python or a GPU. Regenerating predictions requires the saved classifier and research runtime. Training a new classifier uses the externally acquired authors' checkpoint and data.

For the short version, use the [setup / use / test guide](quickstart.md). For background before executing commands, use the [plain-language page](demo/guide.html) and [paper/data/source comparison](upstream-comparison.md).

## 1. Clone and verify the standard-library harness

```bash
git clone https://github.com/buffbeefalo/netmambaplus-reproduction.git
cd netmambaplus-reproduction
python3 -m unittest discover -s tests -v
python3 tools/verify_package.py
python3 repro.py fetch
python3 tools/fetch_assets.py --output assets
python3 repro.py validate --data assets/data/ciciot2022 --report runs/validation-new.json
```

`fetch_assets.py` downloads four pinned authors' assets and generates metadata that is byte-identical to the inspected release. It verifies the recorded sizes and SHA-256 hashes before making each file available. Matching existing assets are reused; differing files are preserved and rejected. Assets remain outside Git. A removed or changed external release causes a visible error, not substitution of another dataset.

## 2. Build the tested GB10 environment

This profile was exercised on aarch64 Python 3.12.3, an NVIDIA GB10, driver 580.126.09 and **CUDA toolkit 13.0.88**. It is specific to that compatibility port. A driver's displayed CUDA version alone does not mean `nvcc` or development headers are installed. Check `nvcc --version` and `/usr/local/cuda/bin/ptxas --version` first. Other hardware needs a separately validated profile.

With `uv` available:

```bash
uv venv --seed --python 3.12.3 .venv-gb10
uv pip install --python .venv-gb10/bin/python torch==2.9.1 torchvision==0.24.1 --index-url https://download.pytorch.org/whl/cu130
uv pip install --python .venv-gb10/bin/python -r requirements/gb10.txt wheel==0.48.0
source .venv-gb10/bin/activate
export TRITON_PTXAS_PATH=/usr/local/cuda/bin/ptxas
export TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1
export PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=4
python tools/build_gb10.py --build-root "$PWD/build-gb10"
python tools/check_gpu_runtime.py --output runs/runtime-check-new.json
```

The build directory must be new and outside `upstream/NetMambaPlus`. The script copies the authors' Mamba fork, fetches the pinned full causal-conv1d source, applies hash-checked compiler compatibility edits, forces both source builds, verifies the installed Mamba Python files and preserves build logs. It does not modify the verified original model or loader. Set the environment variables in every new shell used for model execution.

The environment variable restoring old checkpoint loading is used only with trusted, recorded research checkpoints. Do not use arbitrary uploaded pickle checkpoints. The [research record](../research/research-record.md) documents the original packaging failures, the two retained package-check warnings, the Torch capability warning, and why GPU parity and actual training—not package version strings—support the runtime claim. This is a research setup with old dependencies.

For an x86 A100 environment, the original [upstream setup](https://github.com/wangtz19/NetMambaPlus/tree/eec9483e2f0fb84ca22982b9de8149bc3a8b1ad2) is the source reference. That separate environment was not measured here. Do not run the GB10-only architecture patch on another GPU.

## 3. Exercise masked pretraining

```bash
python repro.py pretrain --config configs/ciciot2022-pretrain-smoke.json --data assets/data/ciciot2022 --output runs/ciciot-pt-functional-new --seed 0 --num-workers 2
```

The fixed functional configuration requests 100 steps. The unmodified source runs complete epochs, so these 8,323 training flows produce 132 updates across two epochs. A checkpoint is saved at step 130 after 131 updates. This is a functional pretraining check on downstream training data. It does not use the test split and does not recreate the Browser/Kitsune pretraining corpus.

## 4. Train the classifier

```bash
python repro.py finetune --data assets/data/ciciot2022 --checkpoint assets/checkpoints/fuse3_mamba.pth --output runs/ciciot-ft-seed0 --seed 0 --num-workers 2
```

Repeat with seeds 1 and 2 and matching new output directories to reproduce the three-run protocol. Each run uses 120 epochs, batch 128 and 7,920 updates. There is no early stop based on the test set. Native validation selects `checkpoint-best.pth`, and the native program performs one final test pass afterward. Preserve `manifest.json`, `native.log`, `log.txt`, `train_stats.json`, `test_stats.json` and the checkpoint together.

For the demo, seed 0 was selected before final test scores. The three reported training runs shared one GB10; elapsed times are not isolated GPU benchmarks. A repeated seed does not promise bitwise-identical weights across hardware, libraries or scheduling.

## 5. Strictly evaluate and regenerate the replay

Use the original checkpoint beside its successful fine-tuning manifest:

```bash
python evaluate.py --data assets/data/ciciot2022 --checkpoint runs/ciciot-ft-seed0/checkpoint-best.pth --output runs/ciciot-eval-seed0 --num-workers 2
python replay.py --data assets/data/ciciot2022 --checkpoint runs/ciciot-ft-seed0/checkpoint-best.pth --output runs/ciciot-replay-seed0 --num-workers 2
```

Open `runs/ciciot-replay-seed0/index.html`. Its saved predictions come from the original classifier, native tensor loader and native evaluation engine. Metrics are also recomputed independently from the predictions. Repeat the two commands with seeds 1 and 2 for the complete result verification.

`evaluate.py` uses `strict=True`; `replay.py` additionally requires a checkpoint hash bound to the six class meanings. If a checkpoint has moved, use `--provenance` to point to its original manifest or model-export provenance JSON. Identical tensor shapes alone do not establish class order. This repeated test execution verifies the frozen result; it must not guide further tuning.

For a JSON array of native flows **without known labels**, use:

```bash
python predict.py --flows path/to/unlabeled-flows.json --checkpoint runs/ciciot-ft-seed0/checkpoint-best.pth --output runs/predictions-new
```

Each flow still needs native `data`, `sizes` and `intervals` fields. Optional label/name fields are ignored for prediction; targets are discarded before model forward. The output `metrics.json` contains logits, scores and predicted class names, with no invented accuracy. The input file and checkpoint are hashed. This command performs classification of already assembled flows; it does not reconstruct connections from the supplied packet CSVs.

## 6. Collect results and make a model-only export

After all three runs and their evaluations finish:

```bash
python tools/review_experiments.py --pretrained assets/checkpoints/fuse3_mamba.pth --export checkpoints/customer-export-new --output runs/reviewed-results-new.json
```

The collector verifies complete epoch histories, finite losses and saved weights, validation selection, actual selected-checkpoint AdamW counters, changed transferred parameters, strict-test agreement and independently computed confusion matrices. It also runs one additional training-only backward/optimizer check per seed on disposable model copies; these updates never change saved test results or exports. Model-only exports retain exactly the same tensors and strip optimizer state and the native argument namespace. Their provenance binds each new file hash to the original training checkpoint and class mapping. These exports do not establish new redistribution or commercial rights for inherited pretrained assets.

After training is no longer using the GPU, run the fixed latency measurement and graph-capture probe:

```bash
python tools/benchmark.py --data assets/data/ciciot2022 --checkpoint runs/ciciot-ft-seed0/checkpoint-best.pth --output runs/ciciot-benchmark-seed0 --num-workers 2
python tools/probe_export.py --data assets/data/ciciot2022 --checkpoint runs/ciciot-ft-seed0/checkpoint-best.pth --output runs/ciciot-export-probe-seed0 --num-workers 2
```

The benchmark uses batches 1, 16 and 128, twenty warmups and one hundred synchronized repetitions each. It excludes capture, preprocessing, loading and transfers, and reports the GPU process snapshot. The export probe can complete with `export_status: unsupported_in_tested_path`: that is an observed portability blocker, not a successful export or a failed classifier inference run.

## 7. Rebuild the presentation

```bash
uv pip install --python .venv-gb10/bin/python -r requirements/presentation.txt
python tools/build_customer_package.py
```

The generator reads the reviewed evidence shipped with this repository and editable presentation sources. It produces the PowerPoint, briefing PDF, charts, notes, Markdown result tables, seven-question map and offline learning guide. The guide uses the same slide order and exact speaker script. LibreOffice converts the deck to the corresponding slide PDF when installed. The content source and PowerPoint are both editable. Replacing the reviewed evidence with a new experiment requires reviewing every claim and limitation again.

The guide alone can be rebuilt without presentation dependencies: `python3 tools/build_learning_guide.py`. After any intentional document edit or build, review the output and refresh checksums with `python3 tools/verify_package.py --write-sha256`; then run the verifier normally. Refreshing checksums is not a content review.

To regenerate the browser recording, use a separate presentation-test environment:

```bash
uv venv .venv-browser
uv pip install --python .venv-browser/bin/python -r requirements/browser.txt
.venv-browser/bin/python -m playwright install chromium ffmpeg
.venv-browser/bin/python tools/record_demo.py --replay runs/ciciot-replay-seed0 --output runs/demo-recording-new
```

The browser rehearsal checks playback, row totals, error/attack filters, reset, page errors and desktop/mobile overflow before writing its successful verification record. The document generator also requires LibreOffice, `pdfinfo`/`pdftotext` for review, and DejaVu fonts on the Linux host; these system packages are separate from the Python requirements.

## A five-minute customer rehearsal

1. Open the slide deck and the downloaded HTML replay before the meeting. Keep the PDF and recorded demonstration beside them as backups.
2. Explain that one displayed row is one processed flow, with byte content, sizes and timing. Show where the six output classes come from.
3. Press **Play replay**, then **Show all**. Point out the classifier hash, test accuracy and macro F1. Display speed is not inference speed.
4. Select **Prediction errors** and discuss an actual confusion. Select **Attack-class predictions** and explain why these labels are narrower than a universal IDS decision.
5. Show the measured-versus-paper table and hardware roadmap. State the next experimental step: independent traffic and a tested capture-to-tensor adapter before operational IDS claims.

A customer can inspect the published replay and reports without downloading packet data or installing CUDA. Running new model inference requires the research assets and runtime described above. Full Browser/Kitsune pretraining, live capture and NPU/SmartNIC execution remain explicitly outside the completed measurement.
