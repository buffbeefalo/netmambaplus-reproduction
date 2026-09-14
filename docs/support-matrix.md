# Run the project on another machine

**Current workflow:** Use the [packet setup](customer/packet-study-setup.md) for both CSVs, checkpoint-only acquisition and the packet-specific native gate. The original flow build/model receipts below are historical compatibility evidence, not a second client route.

You can present the project, recheck its evidence, or run new neural-model experiments. Those are three different setups. Start with the smallest route that does the job.

| Machine / activity | Current status | Evidence and limits |
|---|---|---|
| Browser or document viewer | The video, recorded demo, transcript, PDF and PowerPoint are available without CUDA or Python. | Actual Chromium playback, seeking, captions, downloads and phone-width layouts were checked. This does not execute the neural model. |
| Linux x86-64, Windows x86-64 and macOS ARM64; Python 3.10 / 3.12 | The Python tools and saved-evidence checks passed on all six hosted combinations. | [Workflow run 34815032176](https://github.com/buffbeefalo/netmambaplus-reproduction/actions/runs/34815032176), commit `c90153e4e5048cb29af9ea8ff7dbd38820b96dc1`: 412 discovered tests per job, with optional numerical/native skips, plus package/packet/video checks. See the [cleanup audit](research/accuracy-cleanup.md) for the newer revision. These jobs do not train or run the neural model. |
| Linux ARM64 + NVIDIA GB10 | Both the original flow model and the packet adaptation have measured training and inference evidence. | Three 120-epoch flow runs; six 1,000-update packet runs; strict inference and numerical checks. Follow the [packet setup](customer/packet-study-setup.md); earlier flow records remain historical. The generalized builder has a separate execution receipt below. |
| Other Linux x86-64 / ARM64 + NVIDIA CUDA GPUs | A generalized source-build route is provided; additional physical GPU configurations remain unverified. | The new builder detects the selected GPU and checks compiler support. Each machine must pass the numerical and complete-model gates below before it is called tested. |
| CPU-only model execution, native Windows/macOS model execution, AMD/Intel GPUs, Apple MPS, NPU or SmartNIC | Not implemented or validated by this work. | The pinned model uses CUDA extensions and fused Triton normalization. Passing the portable Python checks does not establish these execution backends. |

The original GB10 recipe and historical measurements are unchanged. A CUDA wheel, a successful compilation, and a successful model run establish different things; preserve their separate records.

## Present or recheck saved results

For viewing, open the [video](https://buffbeefalo.github.io/netmambaplus-reproduction/video/) or [recorded demo](https://buffbeefalo.github.io/netmambaplus-reproduction/). Download the MP4, PDF or PowerPoint for offline presentation. The demo replays saved predictions.

For the portable checks, install Git and Python 3.10 or 3.12, then use a terminal:

```text
git clone https://github.com/buffbeefalo/netmambaplus-reproduction.git
cd netmambaplus-reproduction
python -m unittest discover -s tests -v
python tools/verify_package.py
python tools/review_packet_study.py
python tools/verify_packet_briefing.py
python tools/verify_repository_guide.py
python tools/verify_course_video.py
python tools/verify_video_course_v4.py
python tools/review_calibration.py --check
python tools/build_video_page.py --check
```

On a system where the command is named `python3`, use that name instead of `python`. Use a full Git clone: historical video checks need the pinned release objects, which a source ZIP does not contain. For an existing shallow clone, fetch them with `git fetch --unshallow origin`. No Python packages or research-data downloads are needed for these checks. The unit tests should end with `OK`; optional native/numerical tests may be skipped. The verifiers should exit successfully. The workflow is the record of the test count for its particular commit.

The packet evidence checker preserves two strict raw-score tolerance failures while confirming all 25,930 predicted classes. Successful evidence verification means the saved measurements and those limitations agree; it does not erase the failures or run a new GPU experiment. The briefing checker validates current content and reviewed file identities without rendering PowerPoint.

The first cross-platform workflow exposed Windows UTF-8/newline problems and temporary-directory aliases on macOS and Windows. The fixes use explicit UTF-8, preserve committed document/configuration bytes, keep checksum paths in repository notation and resolve temporary paths. Six additional regressions test those failure modes. The original failed workflow remains [available](https://github.com/buffbeefalo/netmambaplus-reproduction/actions/runs/34746175880); its failure was not hidden by skipping platforms.

## Build the model dependencies on Linux with an NVIDIA GPU

For the complete current sequence use [packet setup](customer/packet-study-setup.md). The recipe and full-flow checks preserved below describe the earlier compatibility audit. To acquire its old data, explicitly pass `--inventory configs/assets.json`; the default fetcher now acquires packet initialization only.

This is a bounded Python 3.12 / Torch 2.9.1+cu130 / CUDA toolkit 13.0 profile. It is not an installer for arbitrary CUDA versions. The NVIDIA driver must support this CUDA runtime, and the toolkit must provide `nvcc` and `ptxas`. The selected GPU must be usable by Torch and appear in `nvcc --list-gpu-code`. The builder prechecks the Python/Torch/CUDA profile, Torch GPU execution and nvcc target support before downloading or installing native extensions. It does not separately probe ptxas; confirm that executable is present before the numerical and model checks.

The Torch/torchvision pairing and CUDA index follow [PyTorch's versioned installation instructions](https://pytorch.org/get-started/previous-versions/#v291). Compiler target discovery uses NVIDIA's [`nvcc --list-gpu-code` interface](https://docs.nvidia.com/cuda/cuda-compiler-driver-nvcc/index.html#list-gpu-code-code-ls).

```bash
python3.12 -m venv .venv-cuda
source .venv-cuda/bin/activate
python -m pip install torch==2.9.1 torchvision==0.24.1 --index-url https://download.pytorch.org/whl/cu130
python -m pip install -r requirements/gb10.txt setuptools==78.1.0 wheel==0.48.0

export CUDA_HOME=/usr/local/cuda-13.0
export PATH="$CUDA_HOME/bin:$PATH"
export TRITON_PTXAS_PATH="$CUDA_HOME/bin/ptxas"
export PYTHONDONTWRITEBYTECODE=1
export TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1
export OMP_NUM_THREADS=4

python repro.py fetch
python tools/build_cuda.py --build-root runs/cuda-build-new
python tools/check_gpu_runtime.py --output runs/cuda-ops-new.json
python tools/check_model_runtime.py --output runs/cuda-model-new --build-report runs/cuda-build-new/build-report.json
```

Adjust `CUDA_HOME` to the actual CUDA 13.0 toolkit directory. The Torch environment is isolated; the native builder installs only the two pinned extensions with dependency resolution disabled. The `TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD` setting is retained for the old upstream checkpoint format; use only the hash-verified research assets and locally produced checkpoints documented here.

`build_cuda.py` replaces the GB10-only host/GPU restriction with selected-device checks. It retains the original Mamba Python code and source pins, applies the same verified CUDA 13 compatibility patches in fresh disposable copies, forces local compilation of the authors' fork, and records the compiler's actual `-gencode` flags. `torch.cuda.get_arch_list()` is recorded separately because it describes Torch itself, not these extensions. The original `build_gb10.py` remains available unchanged.

The default device is visible CUDA device 0. To select another physical GPU consistently for building and execution, set `CUDA_VISIBLE_DEVICES` before all commands. `--device` can select a builder target among visible GPUs, but it does not redirect subsequent training commands. Each build produces code for its selected GPU architecture only; do not copy its native binaries to a different architecture and assume they will run.

Use fresh output paths. A failed preflight or build writes `build-report.json` with the failed stage and reason; inspect that record and the adjacent logs. The first local generalized-build attempt compiled successfully with the distutils fallback but could not find a Ninja recipe for its flag audit. The corrected audit reads actual compiler commands and the builder exposes its virtual environment's executable directory to child processes. The failed attempt remains retained as evidence.

The numerical checker compares forward and backward calculations against reference paths. The complete-model smoke exercises the original configured classifier, an optimizer update, strict checkpoint reload and inference on synthetic native-format fixtures. It is a functionality check with no accuracy claim. It does not substitute for the recorded real-data experiments or validation on customer traffic.

After both checks pass, acquire and validate the separately hosted research assets:

```bash
python tools/fetch_assets.py --output assets
python repro.py validate --data assets/data/ciciot2022 --report runs/data-validation-new.json
```

Then follow the [runbook's training, evaluation and prediction commands](customer/runbook.md#3-exercise-masked-pretraining) for the original flow experiment, or the [packet setup guide](customer/packet-study-setup.md) for the supplied CSVs. The original flow route retains its native data contract and six-class mapping; the packet route uses 1,500 bytes, empty size/IAT sequences and a separate two-class head. Raw CSV rows are not interchangeable with native flow records, and the two routes need their corresponding checkpoints. Keep classifier checkpoints with their class-mapping provenance when moving to another checked runtime.

The old package warnings remain documented: a `buildtools` dependency warning, the cuSPARSELt SBSA tag warning on ARM, and Torch's reported architecture-range warning on GB10. This guide does not claim a warning-free `pip check`. Other hardware may expose additional compiler, memory or operator constraints; failed checks must remain visible.

## Why there is no CPU model fallback

The fork contains some pure-Torch reference formulas, but normal imports also load `causal_conv1d_cuda` and `selective_scan_cuda`. Its slow Mamba path still calls the CUDA scan, and the configured model requests fused Triton normalization. Simply choosing `cpu` or disabling the fast path does not provide complete CPU execution. Actual CPU attempts failed at CUDA-only operations.

A CPU port would need a complete import/dispatch implementation preserving every active model branch, preprocessing rule and checkpoint tensor, followed by full-model output and gradient comparisons and train/reload/inference checks. No reduced model or operator-only example is shipped as a substitute. This backend is deferred; its feasibility is not ruled out.

The [portability council review](research/portability-council-review.json), run `351368de-51fc-4e53-a962-bf38dbe53453`, ended **ESCALATED / UNRATIFIED**, with no mutually ratified decision hash. It could not settle the complete CPU integration from its available evidence. Its result is preserved exactly. The ordinary session's source review, CUDA implementation and platform fixes are directly authorized work; they do not turn that outcome into consensus. The [video quality review](research/video-quality-review.json) remains a separate historical record with its human-review limits.

## Current execution receipt

On 2026-09-13, the generalized builder and both execution gates passed in a separate Python environment on the same NVIDIA GB10: Linux ARM64, Python 3.12.3, Torch 2.9.1+cu130 and CUDA toolkit 13.0.88. The [machine-readable receipt](portability-evidence.json) records the source, configuration, tools, installed extensions and retained local evidence by SHA-256.

| Gate | Observed result |
|---|---|
| Native extension build | Both extensions compiled with actual `arch=compute_121,code=sm_121` flags. All 14 installed Mamba Python files matched the pinned upstream source. The complete-model checker matched both installed extension hashes to the completed build report. |
| Numerical comparisons | All seven forward/backward cases passed their recorded tolerances: convolution and selective scan at lengths 83 and 443, fused RMS normalization, and FP32/FP16 Mamba fast-versus-slow checks. |
| Complete classifier | The original 1,870,080-parameter model processed six synthetic fixtures. All four 256-wide blocks received all 443 tokens. FP32 loss was finite (`2.112807`); all 51 parameter tensors had finite gradients and changed after one AdamW step. The original Mamba branches and fast paths were preserved. |
| Strict checkpoint reload and inference | All 51 saved state tensors reloaded strictly. CUDA FP16 autocast produced finite six-class outputs of shape `[6, 6]`, normalized scores and exactly matching logits before and after reload. |
| Frozen seed-0 classifier | Fresh strict inference reproduced all 1,041 published predictions and all 6,246 saved logits exactly, with maximum absolute logit difference `0`. Input, checkpoint and class-mapping bindings matched. |

The first build attempt remains disclosed in the receipt: causal convolution compiled and installed, but the builder stopped at its compiler-flag audit because it found no Ninja recipe. That attempt did not reach Mamba compilation. The corrected audit reads the actual compiler log, and a fresh build completed both extensions before the checks above.

The six-fixture update is a functionality check; it does not run the 120-epoch protocol or establish dataset accuracy. The seed-0 comparison reexecutes a frozen result without retraining or tuning. These results establish execution on this recorded GB10 configuration; additional physical GPU configurations remain unverified.


## Confidence update and fresh GB10 rechecks

The current [confidence-calibration addition](customer/confidence-calibration.md) was fitted and executed on the same GB10 environment on 2026-09-13/14 UTC. All three saved classifiers processed all 1,040 validation flows before any calibrated test inference began, then each processed all 1,041 test flows. The published [three-seed report](customer/evidence/calibration/results.json) can be recomputed using the CPU-only command above, including its artifact identities, complete-row accounting and validation/test chronology.

Mean test NLL decreased from 0.4416 to 0.4172, Brier score from 0.2035 to 0.2012, and 15-bin ECE from 7.03% to 3.82%. All 3,123 class decisions matched their original records. These are retrospective confidence results on the released split; validation also selected the original checkpoints. At the fixed illustrative 0.90 threshold, more predictions and more mistakes were accepted. This does not validate a customer alert policy.

The [fresh GB10 baseline receipt](customer/evidence/calibration/gb10-baseline-audit.json) records another pass of all seven operator comparisons and the complete-model update/reload check. Fresh seed-0 runs preserved all 1,041 class decisions but showed small FP16 logit differences, up to 0.00390625 in the recorded comparisons. The earlier exact-match execution receipt above remains an observation of that particular run; it is not a universal bitwise-reproducibility guarantee. The [default-path check](customer/evidence/calibration/default-path-check.json) confirms that ordinary prediction still preserves its original output fields and class decisions.

Calibration fitting and new flow inference use the checked CUDA model environment. Recomputing the saved confidence report uses only Python's standard library. Neither route adds CPU neural-model execution, an independently tested second physical GPU, or NPU/SmartNIC deployment. The final workflow records the current portable test count; historical workflow counts above refer to their own commits.
