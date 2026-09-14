# Set up, use and test the current project

Choose the smallest route that does what you need. **Viewing requires only a browser or document viewer.** Checking saved evidence requires Git and Python. Fresh neural-model training and inference require the checked CUDA environment and external research assets.

| Your goal | Start here | What actually runs |
|---|---|---|
| Understand and present the project | Route 1 | Documents, video and recorded replay |
| Verify code and published measurements | Route 2 | CPU regression tests and saved-evidence arithmetic |
| Train or predict from the two CSVs | Route 3 | Native NetMamba+ packet adaptation on a GPU |
| Repeat the original flow experiment or calibration | Route 4 | Native six-class flow model on a GPU |

## Route 1 — open and present

Start with the [current customer index](README.md). Send the [packet PDF](packet-addendum/NetMambaPlus-packet-addendum.pdf), [PowerPoint](packet-addendum/NetMambaPlus-packet-addendum.pptx) and [script](packet-addendum/packet-addendum-script.md) with the [v4 one-hour course](https://buffbeefalo.github.io/netmambaplus-reproduction/video/). The course covers flows and calibration; the addendum explains the later CSV training. The [paper/data guide](paper-and-data-explained.md) starts from first principles, and the [every-file guide](../repository-walkthrough.md) explains every repository file and download.

Open the [recorded replay](https://buffbeefalo.github.io/netmambaplus-reproduction/), select **Show all**, then **Prediction errors**. It contains 1,041 original test flows, 91 errors and 91.26% seed-0 accuracy. Its 402 attack-class predictions are model outputs, not verified operational alerts. The browser does not train, capture traffic or block packets; playback speed is unrelated to inference speed. It shows the original uncalibrated flow predictions.

Download media before an offline meeting. No API key, AI subscription, Python or GPU is required to view it. The [older release ZIP](https://github.com/buffbeefalo/netmambaplus-reproduction/releases/download/customer-2026-09-15-audited/netmambaplus-customer-package.zip) contains the original customer edition; it does not contain the later calibration or packet study. For current code and complete historical verification, use Git below.

## Route 2 — check the current repository without a GPU

Install **Git and Python 3.10 or 3.12**, then run these commands from a terminal. Use `python3` instead of `python` if that is your interpreter's name.

```text
git clone https://github.com/buffbeefalo/netmambaplus-reproduction.git
cd netmambaplus-reproduction
python -m unittest discover -s tests -v
python tools/verify_package.py
python tools/review_calibration.py --check
python tools/review_packet_study.py
python tools/verify_packet_briefing.py
python tools/verify_repository_guide.py
python tools/verify_course_video.py
python tools/verify_video_course_v3.py
python tools/verify_video_course_v4.py
python tools/build_video_page.py --check
```

Use a **full Git clone**. Historical course/video checks read immutable Git versions as data. A GitHub source ZIP has no `.git` history, and a shallow clone may lack those versions. For an existing shallow clone, run `git fetch --unshallow origin`; for an ordinary existing clone, fetch its history with `git fetch origin`. The archived customer ZIP is a different, older package, not a substitute for checking current main.

These commands need no installed ML packages or private CSVs. The suite ends with `OK`; optional numerical/native tests are reported as skipped when their dependencies are unavailable. The published baseline at commit `c90153e` ran 412 tests locally: 376 passed and 36 optional checks were skipped, and [all six hosted OS/Python jobs passed](https://github.com/buffbeefalo/netmambaplus-reproduction/actions/runs/34815032176). The [current audit](../research/accuracy-cleanup.md) and [CI workflow](https://github.com/buffbeefalo/netmambaplus-reproduction/actions/workflows/ci.yml) bind newer counts to their revisions.

The verifiers must exit successfully. The packet evidence check deliberately reports **two retained strict numerical-comparison failures** alongside complete class agreement; a successful evidence audit means it verified that record, not that the original GPU differences vanished. The briefing checker verifies evidence/source/slide/script consistency and the reviewed PDF's identity; it does not render PowerPoint or watch a video.

Any nonzero exit or traceback is a failed check. Preserve the error and review the affected file. Regenerating a checksum cannot prove that a changed result is correct. These CPU checks recompute saved evidence; they do not rerun training or establish a CPU model backend.

## Route 3 — train and use both packet CSVs

Follow the [packet setup guide](packet-study-setup.md) in order. The measured model environment is Linux ARM64 on NVIDIA GB10, Python 3.12, Torch 2.9.1+cu130 and CUDA toolkit 13.0. Complete the [CUDA build and numerical/full-model gates](../support-matrix.md#build-the-model-dependencies-on-linux-with-an-nvidia-gpu) first. A GPU driver alone does not install the compiler toolkit.

| Step | Command family | Successful outcome |
|---|---|---|
| Validate and prepare both CSVs | `packet_data.py` | Full byte validation, registered source identities, duplicate-aware global split and fingerprinted local arrays |
| Freeze the experiment | `tools/freeze_packet_protocol.py` | Protocol bound to prepared data, code and declared training budget |
| Fit controls and train native models | `tools/packet_controls.py`, `tools/train_packet_model.py` | Nine fitted controls; six completed native runs; selected checkpoints frozen before test inference |
| Predict an unlabeled packet CSV | `tools/predict_packets.py` | Two logits, benign/attack class, uncalibrated scores and a completion receipt |
| Review published results | `tools/review_packet_study.py` | Recomputed metrics, test membership and retained numerical limitations |

The predictor accepts 1,500 ordered payload columns alone or with the four metadata columns; it rejects a `label` column. Metadata is not passed to the native model. Keep checkpoints with their provenance, use fresh output paths, and inspect completed receipts rather than treating requested update counts as proof of training.

All six published native models completed 1,000 updates. All nine controls completed, including six converged logistic fits. These were fixed-budget runs with replacement sampling and one model seed, not full-file epochs or a reproduction of the paper's flow benchmark. See the [study report](packet-model-study.md) for exact scores, group/row weighting and subtype support.

## Route 4 — original flows and confidence calibration

Use the [flow runbook](runbook.md) after the same checked CUDA setup. It covers source/assets, 132-update functional pretraining, three 120-epoch fine-tuning runs, strict evaluation, inference, exports and model-only timing. `predict.py` requires already assembled flow JSON with `data`, `sizes` and `intervals`; it accepts a different input and checkpoint from `tools/predict_packets.py`.

The [calibration guide](confidence-calibration.md) explains validation-fitted temperature scaling and optional accept/defer output for these frozen flow models. It preserves the predicted class. It is not implemented as packet-model calibration and does not modify the recorded browser replay.

Original flow test accuracy was **91.26%, 84.05%, 84.63%**, averaging **86.65%**; the paper's 97.50% was not reproduced. Rechecking a model on its existing test data checks repeatability, not independent validation.

## Common problems

| Symptom | Next action |
|---|---|
| Python command is missing | Install Python 3.10 or 3.12 for portable checks; try the interpreter's `python3` name |
| A historical Git snapshot is missing | Use a full clone or fetch missing history; a source ZIP cannot supply Git objects |
| File/hash check fails | Confirm one complete revision and review the mismatch; do not bypass the check |
| `nvcc` / `ptxas` is missing or rejects `sm_121a` | Use the documented CUDA 13.0 toolkit and `TRITON_PTXAS_PATH` in the support matrix |
| Output directory exists | Choose a fresh run path so earlier evidence remains available |
| Checkpoint or input contract is rejected | Use the matching packet or flow route and its provenance; their class heads and inputs differ |
| Export probe says `unsupported_in_tested_path` | This is the retained graph-export limitation; GPU eager inference was separately tested |

The [support matrix](../support-matrix.md) records actual platform coverage. Native CPU, Windows/macOS, NPU and SmartNIC model execution remain unimplemented or unvalidated. The [acceptance map](acceptance.md) separates completed work from those gaps.
