# Confidence calibration and current course implementation plan

> **For agentic workers:** Use superpowers:subagent-driven-development to implement and review these independent tasks. Publication is already authorized by the user.

**Goal:** Add a measured, optional confidence-calibration feature to native NetMamba+ inference, test it on the GB10, and publish one updated hour-long course with matching PDF, PowerPoint, transcript, and complete file guide.

**Architecture:** Fit one positive temperature for each frozen checkpoint using only `data-valid.json`. Keep the original raw predictions and logits, add calibrated scores and an optional accept/defer field, and bind the fitted artifact to its checkpoint and inference configuration. Advance the active course to v4 while verifying v3 against its immutable release snapshot.

**Tech stack:** Standard-library Python for calibration and tests; the existing pinned PyTorch/CUDA/Mamba environment for inference; existing Andrew neural narration, Pillow/FFmpeg video, python-pptx and ReportLab document builders.

**Spec:** The complete implementation and measurement contract is recorded below. The council review is `ESCALATED / UNRATIFIED`; these are directly authorized implementation decisions, not a ratified artifact.

## Global constraints

- Preserve all three original checkpoints, seed results, raw-data boundaries, and v3 release asset bytes.
- Fit on the 1,040 validation rows only. Disclose checkpoint-selection reuse, five exact train/validation overlaps, zero exact validation/test overlaps, and unknown capture/pretraining independence.
- Predeclare temperature range `[0.05, 20.0]`, validation NLL minimization, and a fixed calibrated-confidence acceptance threshold of `0.90` before scaled test evaluation. The threshold is an illustrative policy, not an optimized or validated operational safety level.
- Measure all three checkpoints on the same 1,041 frozen test rows. Report paired NLL (primary), multiclass Brier (mean sum over classes), 15 equal-width-bin ECE, class accuracy, and accepted/deferred counts with denominators. Empty accepted-set error is null.
- This is a retrospective study on already-seen data, not independent confirmation. Publish unfavorable outcomes and do not claim accuracy, latency, paper, NPU, or SmartNIC improvement without measurements.
- Prediction without calibration retains its original fields and computations; record truthful changed source hashes and the observed FP16 numerical tolerances. Labels never enter the model forward call.
- Reject malformed, nonfinite, incompatible, or changed calibration artifacts explicitly. An abstention threshold requires calibration. No additional package dependency for portable tests.
- Keep one current approximately 60-minute video, its PDF/PPT/transcript aligned, and all files explained in one current guide. Preserve historical artifacts and explicit pending human full-watch review.

## Task 1: Calibration math, artifact, and validation-only fitting

**Files:** Create `calibration.py`, `tools/calibrate.py`, `tests/test_calibration.py`.

**Interface:** `calibration.make_binding(manifest)` returns a stable checkpoint/class/config/upstream/runtime compatibility object; `validate_artifact(artifact, expected_binding)` rejects incompatible or malformed documents and returns the validated artifact; `calibrated_scores(logits, temperature)`, `fit_temperature(logits, labels)`, `classification_metrics(logits, labels, temperature=1.0, threshold=None)`, and `validate_threshold(value)` are pure standard-library functions. The artifact has `schema_version: 1`, `method: "temperature_scaling"`, `temperature`, `binding`, `fit`, and `validation` fields. The fit CLI writes `calibration.json` and an execution manifest to a fresh output directory; it must never read `data-test.json`.

- [ ] Write and run analytic tests before implementation: four correct and one incorrect binary margin-2 samples have optimum `T = 2 / log(4)`; T=1 matches existing softmax; positive T preserves argmax; malformed/nonfinite inputs and class/hash mismatches fail; no accepted rows produce null error.
- [ ] Implement deterministic bounded fitting and validated artifact application, then run `python3 -m unittest tests.test_calibration -v`.
- [ ] Implement the native validation-only CLI with checkpoint/class/source integrity checks, finite output checks, row-order/count checks including partial batches, targets discarded before forward, and captured source/runtime hashes.

## Task 2: Predictor integration and actual GB10 measurements

**Files:** Modify `predict.py`, `tests/test_predict.py`; create `docs/customer/confidence-calibration.md` and `docs/customer/evidence/calibration/` receipts.

**Interface:** Add `--calibration PATH` and `--abstain-threshold FLOAT`. Preserve existing prediction fields and append `calibrated_scores` plus optional `decision` (`accept` or `defer`). Bind the artifact identity and threshold in the execution manifest.

- [ ] Write rejection and no-label-forward tests, then integrate the pure helpers from Task 1.
- [ ] Freeze this protocol and hash before fitting; run validation fitting separately for seeds 0, 1, and 2, then paired raw/calibrated test inference on the real GB10.
- [ ] Publish exact commands, runtimes, artifact hashes, per-seed and aggregate outcomes, and the actual baseline CUDA operator/full-model checks. Preserve observed small historical FP16 logit differences and zero class disagreements.
- [ ] Run the portable suite, CLI checks, negative artifact cases, native inference, and relevant CUDA/model checks. Resolve concrete failures before making completion claims.

## Task 3: Versioned media tooling and historical verification

**Files:** Modify the existing narration, video/document/page builders and verifiers under `tools/`, their relevant tests, and CI invocation only as needed; add a v4 verifier entry point if it avoids weakening v3 verification.

**Interface:** Builders accept explicit source/media paths; v4 becomes the current default after the source exists. Historical v3 verification uses immutable Git snapshot `71290440e917105ffa094402d94e24d7e29a3549` and checks its recorded assets and references without executing code from that revision. Current v4 coverage must match the full current tracked/untracked nonignored inventory, not a filtered subset.

- [ ] Test version selection, stale source/reference rejection, historical byte drift rejection, and current inventory omissions before changing the checks.
- [ ] Parameterize version identities without relaxing source, reference, scene, caption, timing, review, or artifact integrity checks.
- [ ] Keep v3 source, coverage, guide snapshot and release assets immutable; do not falsify review records to make a verifier pass.

## Task 4: Current teaching materials and publication

**Files:** Create `docs/customer/video-course-v4-source.json`, v4 coverage/audit/review records and `docs/customer/demo/video/v4/` outputs; update the active watch page, current guide, README, customer instructions and relevant evidence indexes.

- [ ] Codex authors a bounded replacement of roughly five minutes covering the improvement, measured outcomes, GB10 tests and limits. Retain the paper, both CSVs, native inputs/outputs, every repository area, setup/use/tests, IDS demo and hardware discussion.
- [ ] Reuse only identity-verified unchanged Andrew audio; regenerate changed scenes. Correct the old arXiv pronunciation in the spoken text. Render the complete single video, captions, editable narration notes, slide PDF and searchable handbook.
- [ ] Review source claims against actual evidence, every slide and file-guide mapping; run media decoding, frame/caption/timing/ASR checks, document checks and local browser playback. Record automated checks separately from pending human review.
- [ ] Commit and push; run all six platform/Python CI jobs, publish a separate v4 release, deploy the active Pages video, anonymously hash-check downloads and test public playback. Preserve old release bytes and the retired `/course/` 404.
- [ ] Resend the current video, PDF and PowerPoint links with the actual measured improvement and remaining limitations.

## Review record

The calibration-data evidence was read directly after the council's bounded pack omitted it. The validation data is eligible for this explicitly limited retrospective study; it is not an independent calibration holdout. The full v3 verifier was also inspected directly. The implementation must preserve its checks through explicit current-versus-historical version handling. Neither finding changes the council's unratified outcome.
