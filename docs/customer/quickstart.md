# Set up, use and test the project

Choose the smallest setup that does what you need. **Viewing the delivered demo requires only a browser.** Running fresh model predictions requires the tested GPU environment and a trained classifier.

| Your goal | What you need | Start here |
|---|---|---|
| Understand and present the work | A browser or PDF/PowerPoint viewer | Route 1 below |
| Check the code and delivered evidence | Python 3.10 or newer | Route 2 below |
| Train or run fresh inference | The tested GB10/CUDA setup, pinned source and external research assets | Route 3 below |

## Route 1 — open and present it

1. Open the [plain-language guide](https://buffbeefalo.github.io/netmambaplus-reproduction/guide.html). Each numbered section follows the matching slide and includes its speaker script.
2. Open the [recorded replay](https://buffbeefalo.github.io/netmambaplus-reproduction/). Press **Play replay**, **Show all**, then choose **Prediction errors**. You should see 1,041 flows in total, 91 errors and 91.26% seed-0 accuracy. The attack-class filter contains 402 predictions; it is not a count of verified operational alerts.
3. Download the [complete package ZIP](https://github.com/buffbeefalo/netmambaplus-reproduction/releases/latest/download/netmambaplus-customer-package.zip) and extract it. Inside `docs/customer`, open the PowerPoint, briefing PDF or slide PDF. The PowerPoint has speaker notes; `talk-track.md` is the same script in text form. The slide PDF preserves the reviewed font layout; the editable PPTX was rendered with LibreOffice 24.2.
4. For an offline meeting, open `docs/customer/demo/guide.html` and `docs/customer/demo/index.html` from the extracted ZIP. Keep `recorded-demo.webm` as a video backup. Supporting research links on the guide open GitHub; the corresponding documents are also included in the ZIP.

The replay displays **recorded GPU predictions**. It does not train in your browser, examine your computer’s traffic or block packets. Its speed control changes playback only. No API key, AI chat subscription, Python or GPU is needed to read the guide or view the replay.

## Route 2 — check the package without a GPU

Install Python 3.10 or newer. Get the repository with Git, or use the extracted release ZIP:

```bash
git clone https://github.com/buffbeefalo/netmambaplus-reproduction.git
cd netmambaplus-reproduction
python3 -m unittest discover -s tests -v
python3 tools/verify_package.py
```

For a ZIP, open a terminal in the extracted project folder containing `repro.py` and `tests` instead of running the first two commands. The CPU commands were executed on Linux. Windows/macOS execution was not tested; the unit suite includes creating symbolic links.

Expected outcomes:

- The test suite finishes with `Ran 54 tests` and `OK`. These are standard-library tests of the harness, including failure handling; no training data download is required.
- The package verifier prints JSON containing `"status": "passed"`, three seed runs and 1,041 retained test predictions per seed. It recomputes saved metrics, checks artifact fingerprints and verifies document alignment. It does not rerun GPU training.
- A nonzero exit or traceback means the check failed. Preserve the error and identify the affected file. Do not regenerate checksums merely to hide a mismatch; re-download the release or review the intentional change first.

Optional Linux checksum check, from the same folder:

```bash
sha256sum -c docs/customer/SHA256SUMS
```

Every listed file should report `OK`. The Python verifier checks the same package inventory and is the portable option when `sha256sum` is unavailable.

## Route 3 — train and run new predictions

Use the [tested runbook](runbook.md) in order. This route was exercised on **aarch64 Python 3.12.3, NVIDIA GB10, driver 580.126.09 and CUDA toolkit 13.0.88**. It is not a tested universal Windows, CPU, A100 or NPU setup. A CUDA-capable driver alone does not install the compiler toolkit.

| Step | Runbook section | Successful outcome |
|---|---|---|
| Fetch and validate | 1 | Pinned authors’ source and four hash-checked assets acquired; all 10,404 native flows validate |
| Build the GPU environment | 2 | Both native extensions build; numerical-check JSON says `passed` for seven checks |
| Exercise reconstruction pretraining | 3 | Two complete epochs / 132 updates; finite loss and a saved checkpoint |
| Fine-tune a classifier | 4 | 120 epochs / 7,920 updates; successful manifest and `checkpoint-best.pth` |
| Evaluate and make a replay | 5 | Strictly loaded classifier, measured metrics and a new `index.html` |
| Predict without known labels | 5 | Class names, logits and scores in `metrics.json`; no invented accuracy |
| Compare seeds, export model-only weights and measure | 6 | Complete result records, checkpoint-bound provenance, latency samples and the explicit export-probe outcome |

After completing setup and training, these are the central usage commands:

```bash
python evaluate.py --data assets/data/ciciot2022 --checkpoint runs/ciciot-ft-seed0/checkpoint-best.pth --output runs/ciciot-eval-seed0 --num-workers 2
python replay.py --data assets/data/ciciot2022 --checkpoint runs/ciciot-ft-seed0/checkpoint-best.pth --output runs/ciciot-replay-seed0 --num-workers 2
python predict.py --flows path/to/unlabeled-flows.json --checkpoint runs/ciciot-ft-seed0/checkpoint-best.pth --output runs/predictions-new
```

The last command needs your **already assembled native flow JSON**, with `data`, `sizes` and `intervals`. It does not accept the uploaded packet CSVs as if they were flows. See the [input explanation](briefing.md#what-goes-in-and-what-comes-out) and [comparison](upstream-comparison.md).

Each invocation needs a fresh output directory. Keep a checkpoint beside its successful manifest; if you move it, pass its original manifest or export provenance with `--provenance`. This binds the file to the six class meanings. Fetch the original weights and data from their recorded external sources or train your own local classifier; inherited weights are not included in the customer ZIP.

## How the tests have gone

| Check actually performed | Outcome and limit |
|---|---|
| CPU harness | 54 tests passed; Python 3.10/3.12 CI records are linked in [verification](verification.md) |
| Native GPU runtime | Seven forward/backward numerical checks passed in each of two independently built environments |
| Main training | All three seeds completed 120 epochs and 7,920 updates each |
| Saved-model inference | Native evaluation, strict fresh evaluation and independently recomputed prediction metrics agree for all three seeds |
| Model-only exports | Fresh evaluations reproduced all three original scores |
| Full unlabeled inference | Seed-0 predicted labels and logits for all 1,041 flows matched the recorded labeled-input run in this specific recheck |
| Public replay | Play/pause, speed changes, filters and reset passed; no page overflow at widths 320, 390, 768 and 1440 |
| Torch graph export | Eager GPU inference passed; strict graph capture could not trace `causal_conv1d_cuda.causal_conv1d_fwd` |

Test accuracy remains **91.26%, 84.05%, 84.63%**, averaging **86.65%**. The paper’s 97.50% result was not reproduced. Retesting a frozen model on the same test data checks repeatability; it does not create an independent validation set.

## Common problems and the next action

| Symptom | Next action |
|---|---|
| `python3` is not found | Install Python 3.10 or newer and check `python3 --version` on the tested Linux route |
| Test says a file or checksum differs | Check that you are in the project root and using one complete release; keep the failure visible |
| `nvcc` or `ptxas` is missing | Install the specified CUDA development toolkit before attempting the GB10 build |
| Assembler rejects `sm_121a` | Activate the tested environment and set `TRITON_PTXAS_PATH=/usr/local/cuda/bin/ptxas` as in the runbook |
| Source, data or checkpoint hash mismatch | Restore the pinned asset or review a deliberately new experiment; do not disable identity checks |
| Output directory already exists | Use a new run directory so old evidence is preserved |
| Checkpoint has no valid class mapping | Keep its original successful manifest or supply `--provenance`; six output dimensions alone do not establish meanings |
| Export probe reports `unsupported_in_tested_path` | This is the recorded portability limitation; it does not mean GPU inference failed |

The [verification record](verification.md), [question map](answers.md) and [acceptance review](acceptance.md) distinguish completed checks from remaining research and deployment work.
