# Verification record — 12 September 2026

This record describes checks performed by the implementing session against the measured experiment and customer package. It is not an independent model certification. The focused council reviewed the experiment plan before the work; its [decision and limits](../research/research-record.md#council-decision-and-its-limits) remain separate from these results.

## What was executed and checked

| Area | Executed check and result |
|---|---|
| Original source | All 103 tracked upstream files match the pinned Git commit; seven core SHA-256 pins also match. The original model and tensor loader remain unmodified. |
| Supplied CSVs | Complete-file CSV parsing and metadata aggregation: 1,410,255 CICIDS2017 rows and 79,881 UNSW rows. Payload-byte values were not exhaustively numerically audited. |
| Compatible data | All 10,404 native flows validated again. Split counts, six-class mapping, input hashes and the disclosed five/six raw-input overlaps agree with the published record. |
| Runtime build | Native Mamba/causal-convolution extensions built on GB10. The automated build was actually repeated in a second isolated environment, with installed model Python hashes preserved. |
| Numerical GPU checks | Seven forward/backward checks passed in each environment: causal convolution and selective scan at lengths 83 and 443, fused RMS normalization, and full Mamba blocks in FP32/FP16. Declared tolerances and observed errors are recorded. |
| Masked pretraining | Training-only functional run completed 132 optimizer updates, two epochs and a saved checkpoint. It does not reproduce Browser/Kitsune pretraining. |
| Fine-tuning | Seeds 0, 1 and 2 each completed 120 epochs and 7,920 updates. Finite loss histories, changed encoder parameters, finite saved weights, validation selection and actual selected-checkpoint optimizer counters were verified. |
| Additional gradient check | A real training-only batch produced finite gradients and an optimizer head update on a disposable copy of each selected model. Saved classifiers and test outputs were unchanged. |
| Strict inference | Native final evaluation, fresh strict evaluation and replay confusion matrices agree for all seeds. Independently recomputed metrics use the retained 1,041 predictions per seed. These are repetitions on the same fixed test set. |
| Second-environment inference | Seed 0 was strictly re-evaluated using the rebuilt environment and freshly reacquired, hash-identical data. Its confusion matrix and aggregate metrics agree. |
| Unlabeled inputs | First 128 flows stripped of labels/identifiers were classified successfully. Class predictions agree 128/128; logits differ by at most 0.001953125. |
| Saved exports | Model-only local exports load strictly and preserve the selected model tensors bitwise. Export hashes and class-mapping provenance are published; inherited pretrained weights are not redistributed. |
| Model timing | After training and other local GPU checks ended: batches 1/16/128, 20 warmups and 100 synchronized samples each. All samples and exclusions are retained. This is a shared-workstation model benchmark. |
| Graph export | Eager GPU inference succeeded. Strict Torch graph capture failed on `causal_conv1d_cuda.causal_conv1d_fwd` with `Unsupported`. No ONNX/NPU compiler or target accelerator was tested. |
| Browser replay | Chromium 140.0.7339.16 with Playwright 1.55.0 passed play/pause, show-all, error/attack filtering, reset, JavaScript-error and desktop/mobile overflow checks. Corrected HTML, prediction JSON and video hashes are bound in the browser record. |
| Documents | Six-page briefing PDF and 13-slide editable PowerPoint with speaker notes; LibreOffice 24.2 rendered the matching slide PDF. All pages/slides were visually reviewed for legibility, clipping, claims and measured values. |
| CPU regression suite | 54 standard-library tests passed, including source drift, unsafe output reuse, class-mapping conflicts, strict-load failures, unlabeled adaptation, independent metrics and HTML escaping. |
| Publication hygiene | Gitleaks 8.30.1 found no secrets in the existing Git history or the reviewed source/evidence text, extracted PDF text and PowerPoint XML/notes. Raw packet data, model weights and private transcripts are excluded from the publication inventory. |
| Course material | The affected repository lesson and linked references were reviewed against the final loader, runtime and inference behavior. Shared course/video pending state was inspected; unrelated pending reviews and blocked videos were left visible. |

The [evidence index](evidence/artifact-index.json) binds 57 exact copied records to SHA-256 hashes. Browser evidence includes the successful desktop/mobile screenshots and a recording. An earlier failed mobile layout rehearsal was corrected without changing the original model predictions; the [research record](../research/research-record.md) explains that correction and the measured byte tensor shape.

## Public delivery checks

The training/customer artifacts were published in commit [`6b7767c3550137b32db24b5af158d001a6eae3c7`](https://github.com/buffbeefalo/netmambaplus-reproduction/commit/6b7767c3550137b32db24b5af158d001a6eae3c7). Its [Python 3.10/3.12 CPU CI](https://github.com/buffbeefalo/netmambaplus-reproduction/actions/runs/34682785649) and [Pages deployment](https://github.com/buffbeefalo/netmambaplus-reproduction/actions/runs/34682785650) completed successfully. The [public-download and hosted-browser receipt](publication-checks.json) records the exact artifact hashes, public URLs, workflow results and real browser checks. Later documentation-only delivery receipts do not change the measured model or prediction records.

The public HTML and recorded video, plus all three main PDF/PowerPoint files, were downloaded without repository credentials and matched the reviewed local bytes. The hosted browser passed playback controls, all/error/attack filters, mobile overflow, reset and video playback. The [customer index](README.md) links the downloadable release bundle. Git attributes preserve the original bytes of hash-bound records; native warning whitespace and generated SVG formatting are retained intentionally.

## Repeat the package checks without a GPU

From the repository root:

```bash
python3 -m unittest discover -s tests -v
python3 tools/verify_package.py
sha256sum -c docs/customer/SHA256SUMS
git diff --check
```

The package verifier recomputes metrics from every retained prediction, checks seed/completed-epoch/checkpoint identities, numerical-runtime results, replay/browser hashes, PDF/PPT structure, local document links and the unchanged council decision hash. CPU CI runs the tests and verifier on Python 3.10 and 3.12; it does not claim to repeat GPU training.

`SHA256SUMS` covers the customer and reviewed-research trees. Use `python3 tools/verify_package.py --write-sha256` only after reviewing intentional changes; rewriting checksums is not an evidence review. Rebuilding PDFs can change binary hashes even when their contents are equivalent.

## Limits retained after verification

The accuracy result is **86.65% mean**, with seed values **91.26%, 84.05%, 84.63%** and **4.00 percentage-point sample SD**. The paper's 97.50% result was not reproduced. Protocol/runtime differences and unknown pretraining history prevent an exact reproduction claim, and their causal effect on this accuracy gap has not been isolated.

The released splits have known raw-input overlap; physical capture independence, prior checkpoint exposure and performance on independent customer traffic remain unknown. The short pretraining run, offline browser replay, model-only timings and failed export probe do not establish live IDS operation, calibrated alert probabilities, line-rate packet handling, quantization or NPU/SmartNIC execution. The runtime retains the documented package and GPU-capability warnings.

Raw payloads, private chat logs, upstream source and inherited pretrained weights are not included in the public package. Third-party asset links and provenance support repeatable research; they do not establish redistribution or commercial permission.
