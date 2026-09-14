# Incorporate both uploaded CSVs into NetMamba+ — implementation plan

> For agentic workers: use the subagent-driven-development workflow for the independent data and native-model tasks; root integrates and executes the experiment. User authorization covers implementation, tests and publication without another approval pause.

**Goal:** Both complete uploaded CSVs feed a working, measured packet-classification adaptation of the original NetMamba+ encoder, including joint training and saved-model inference.

**Architecture:** Preserve one row as one packet payload. The original classifier uses 1,500 bytes, stride four and zero numeric-sequence tokens; its two constant learned prefixes remain explicit. A new binary head predicts the CSV-supplied benign/attack label. The original six-class flow experiment and historical media retain their meanings.

**Tech stack:** Standard-library contracts/tests and offline evidence verification; optional NumPy/Pandas preparation and the existing checked PyTorch/CUDA GB10 environment for model execution.

**Spec and authority:** Latest user clarification requires actual incorporation into the model. `runs/packet-connection/model-candidate.md` was a non-voting candidate, supported by source evidence and actual GB10 probes. Both councils ended ESCALATED / UNRATIFIED; their complete records are preserved under `docs/research/packet-model-council.json` and `packet-connection-council.json`. Source and checkpoint audits resolved the technical questions before the measured protocol was frozen. This is directly authorized implementation under the current council policy, not consensus or broker-delivered work.

## Global constraints

- Preserve original upstream commit `eec9483e2f0fb84ca22982b9de8149bc3a8b1ad2` and the existing flow commands/checkpoints.
- No invented flows, headers, packet ordering, timing units or harmless-padding claims.
- Validate all 1,500 numeric byte values before uint8 conversion; retain stored zeros.
- Primary inputs exclude labels, dataset identity, TTL, recorded length, protocol and undocumented delta.
- Explicit label map: CIC `BENIGN` / UNSW `normal` = 0; only the enumerated remaining source labels = 1; unknown labels fail.
- Globally group identical payloads across both sources before assigning splits. Preserve and report contradictory labels and giant groups.
- Raw packets, caches and inherited model weights remain local. Publish reproducible commands, aggregate measurements and evidence.
- Actual training protocol is frozen before the measured fits; no final-test-driven tuning. Report failed transfer as a result.
- Review affected lessons and preserve versioned video/PDF/PPT as historical editions, with a clear addendum and honest inventory verification.

## Task 1: canonical packet data

Own `packet_data.py` and `tests/test_packet_data.py` only. Standard-library import must work without ML dependencies.

Interfaces:

- `LABELS`: ordered source-to-original-label lists for `cic` and `unsw`.
- `binary_label(source, label) -> int`: exact mapping with rejection of unknown source/label.
- `validate_payload(values) -> bytes`: exactly 1,500 integer-valued slots in [0,255]; reject booleans, malformed/nonfinite/fractional values.
- `payload_hash(payload: bytes) -> str`: SHA-256 of the canonical 1,500 bytes.
- `split_for_hash(hex_digest, seed=17) -> int`: global label/source-independent SHA-256 seeded assignment, 0=train,1=validation,2=test, target group fractions 70/15/15.
- `prepare(cic_path, unsw_path, output, *, seed=17, max_train_groups=100000, max_eval_groups=20000) -> dict`: fresh-output-only full-file scan, source hashes and exact expected schema, byte validation, original row metadata retained locally; grouped arrays and report below. CLI exposes the same arguments.

Per-source output subdirectories `cic/` and `unsw/` contain `payload.npy` (G,1500 uint8), `hashes.npy` (G V32), `counts.npy` (G,2 int64), `subtypes.npy` (G,K int64 in LABELS order), `split.npy` (G uint8), `selected.npy` (G bool), and local row metadata CSV retaining original row identity/labels/metadata/group association. Groups sorted by hash. `manifest.json` records all source/output fingerprints, support, conflicts, limits and schema version. Select groups within each source/split by fixed hash order up to the declared cap; do not select by outcomes. Shared hashes must retain the same split even when source labels conflict.

- [x] Write/run meaningful negative tests for malformed bytes, schema/label drift and leakage-producing split changes.
- [x] Implement preparation and grouped counts without dropping contradictory examples.
- [x] Run focused tests and a tiny end-to-end fixture with duplicates spanning sources.
- [x] Root reviews, runs full preparation on both uploads and verifies arithmetic/disjointness.

## Task 2: native model adapter and strict checkpoints

Own `packet_model.py` and `tests/test_packet_model.py` only. Avoid importing Torch at module import time.

Interfaces:

- `build_model(upstream, *, initialization=None, seed=0, device='cuda') -> (model, provenance)`: verify pinned original source; construct unchanged `fuse3_mamba_classifier(arr_length=1500,stride_size=4,seq_len=0,num_classes=2,drop_path_rate=0.1)`. If initialization is supplied, require the registered pretraining hash, transfer every compatible trunk state with explicit decoder exclusions and map positions `[20,41] + range(42,417) + [442]`; keep a newly initialized binary head. Return JSON-safe provenance.
- `forward_payload(model, payload_tensor) -> dict`: accept uint8 (B,1500), normalize to [-1,1], create empty numeric tensors, call native forward. Never consume metadata or labels.
- `save_checkpoint(path, model, provenance, study_metadata) -> dict`: a new safe tensor/basic-JSON packet checkpoint with input contract, source/init mapping, data/protocol identities and file hash. Do not overwrite an existing path.
- `load_checkpoint(path, upstream, *, device='cuda') -> (model, metadata)`: require the packet format and exact contract, strict tensor reload, eval mode; reject flow checkpoints, changed contracts or incompatible source. Never silently omit mismatches.

- [x] Write/run contract rejection tests before implementing.
- [x] Implement explicit source/initialization/position/head provenance.
- [x] Run CPU contract tests and actual GB10 real-payload forward/backward/roundtrip probes; retain failures.
- [x] Root independently reviews native linkage and executes its own integration checks.

## Task 3: measured joint/source training, inference and controls

Root owns `tools/train_packet_model.py`, `tools/predict_packets.py`, `tools/review_packet_study.py`, study config/evidence and their tests. Import Task 1/2 interfaces exactly; send interface changes to both implementers before using them.

- [x] Freeze split/config/source identities and the final council outcome before measured training.
- [x] Use selected groups with binary target distributions from their real label counts; group-uniform supervised loss retains contradictory labels.
- [x] Include a joint model trained on both sources. Use equal source contributions in joint batches and disclose this weighting.
- [x] Execute source-specific and scratch controls within the frozen budget, with validation-only selection, strict saved-model inference, per-source and reciprocal testing. Record actual optimizer steps, parameter changes, observed source contributions and incomplete runs.
- [x] Publish row-weighted and group-weighted confusion counts/accuracy/balanced accuracy/F1/false-positive rate/attack recall and original-label slices. Label the independence, padding, pretraining-exposure and scope limits.
- [x] Verify arithmetic independently; test rejection of stale or inconsistent evidence.

## Task 4: integrate, explain and publish

- [x] Add a plain-language packet-study guide and commands explaining exactly how each original file now contributes, model changes, measured results and limitations.
- [x] Update current README/paper-data explanation and every-file guide. Preserve the original flow/video scientific records and verify historical snapshots by immutable Git identity where references have evolved.
- [x] Run focused tests, all existing tests, package/course/calibration/history checks and the new offline study verifier.
- [x] Independent code/claim review, fix concrete findings, commit/push, confirm actual CI and published links; do not claim unexecuted platforms or GPU backends.

## Execution rulings

- Direct authorized work proceeds while council deliberation completes; no consensus or experiment success is inferred from a candidate.
- Global grouping is source- and label-independent. Exact-payload isolation is measurable; physical flow/capture independence is unknown.
- The existing four/eight-row synthetic-target probes establish mechanics only and their weights never initialize the measured study.

## Publication and final verification

The measured experiment was published at `7eeb4980eea9fd5ad17bfacd29ed88687cb3e1e5`. Its first hosted run exposed real portability defects; those failures remain in [run 34813689942](https://github.com/buffbeefalo/netmambaplus-reproduction/actions/runs/34813689942). The file-identity/path corrections and their regression tests were published at `9d39a6b6a17a06452b0208bf3683abb531674e0d`.

All six Linux/Windows/macOS × Python 3.10/3.12 jobs passed in [run 34814784033](https://github.com/buffbeefalo/netmambaplus-reproduction/actions/runs/34814784033); [Pages run 34814784089](https://github.com/buffbeefalo/netmambaplus-reproduction/actions/runs/34814784089) deployed successfully. Public report/setup/PDF/PPT/script, evidence index, capped regression and full guide downloads were checked against local SHA-256 identities. The active video page links the packet addendum; the retired `/course/` route still returns 404.

Local verification discovered 412 tests, with 376 passes and 36 optional skips. The separate 17-test native packet suite passed on GB10, and independent scikit-learn arithmetic matched all six neural models and nine controls. The new 128-row GB10 I/O regression also passed; it does not replace the frozen full-test numerical limitations. These hosted checks validate portable software and public arithmetic, not native inference on every OS, NPU, SmartNIC or physical GPU.
