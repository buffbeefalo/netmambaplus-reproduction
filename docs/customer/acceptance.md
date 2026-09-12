# Project acceptance and audit map

This checklist maps the requested work to deliverables, executed checks and limits. “Executed” means a command ran and produced the retained result. “Explained” means a requested topic is covered; it does not mean a future integration was built. The [seven-question map](answers.md) locates the answers in the PowerPoint, presenter script, guide and briefing.

## Requested deliverables

| Requirement | Deliverable and actual check | Status / boundary |
|---|---|---|
| Analyze the paper and two uploaded CSVs | [Research record](../research/research-record.md), [CSV profile](evidence/uploaded-csv-profile.json), [comparison](upstream-comparison.md); complete-file parsing and metadata aggregation | Executed. Payload values were not exhaustively numerically validated; no packet classifier was trained. |
| Establish native flow inputs for NetMamba+ | [Validation](audit-evidence/data-validation.json) checks all 10,404 CICIoT2022 flows, mapping, hashes and overlap | Executed. The uploaded packet CSVs are not used as fictional flows. |
| Preserve and explain the original model | `repro.py fetch` verifies all 103 tracked upstream files and seven core pins; [comparison](upstream-comparison.md), slide 13, briefing page 8 | Executed / explained. The model and loader remain original; runtime compatibility edits are in build copies. |
| Perform real training | Three 120-epoch, 7,920-update fine-tuning runs in [original results](evidence/results.json), logs and manifests | Executed. The main full runs were retained and audited; document updates did not trigger new full training or retuning. |
| Exercise NetMamba+ pretraining | Original and [fresh audit run](audit-evidence/pretrain/manifest.json): training-only reconstruction, two epochs, 132 updates | Executed functional check. Full Browser/Kitsune pretraining is not reproduced. |
| Verify saved classifiers and class meanings | Three native/strict/replay comparisons, [export evaluations](audit-evidence/index.json), checkpoint hashes and class-bound export provenance | Executed. Exact paper scores and prior checkpoint exposure remain unestablished. |
| Run inference without known labels | [Full unlabeled agreement](audit-evidence/unlabeled-agreement.json) and fresh inference manifest/outputs | Executed: the predicted labels and logits for all 1,041 flows matched seed 0 in this run. Input is already assembled native flow JSON. |
| Provide a working demo and meeting backups | [Replay](demo/index.html), [video](demo/recorded-demo.webm), screenshots and [public browser checks](audit-evidence/public-browser.json) | Executed recorded-inference demo. No live capture, packet blocking or calibrated alert policy. |
| Explain training, inputs, outputs and reproduced versus paper results | Slides 1–7, eight-page briefing, [script](talk-track.md), [question map](answers.md), shared slide source | Explained with actual metrics and scope. All three seeds are reported. |
| Explain simple IDS and accelerator mapping | Slides 9–12, [hardware roadmap](hardware-roadmap.md), original and [fresh export probe](audit-evidence/export-probe/metrics.json) | GPU execution measured. Live pipeline and NPU/SmartNIC execution remain future work. |
| Measure model inference cost | Original and [repeat benchmark](audit-evidence/benchmark/metrics.json): 20 warmups + 100 synchronized samples per batch | Executed model-only timings. Capture, waiting, transfers and alert handling are excluded. |
| Share AI-assisted research accessibly | [Reviewed research record](../research/research-record.md) with sources, decisions and failed attempts | Delivered as curated findings, not private raw transcripts. |
| Provide a nontechnical page aligned to the PPT/script | [Field guide](demo/guide.html), glossary, everyday comparisons and exact slide speaker scripts | Generated from the same 16-slide source; verifier checks alignment. Browser/visual checks are recorded in verification. |
| Make setup, use and test results simple | [Quickstart](quickstart.md), [runbook](runbook.md), slides 14–15, briefing page 7 | Browser, CPU and GPU paths are distinguished. Two native builds and a fresh dependency-install rehearsal are recorded. |
| Make all files available through GitHub | Public repo, Pages and release ZIP with PDF/PPT/video/evidence | Revision-specific verification is required. Prior public checks establish the earlier release only; consult the final receipt attached to the release you download for its commit, hashes and anonymous-download results. |
| Audit all parts and use council to seek improvements | This map, [verification record](verification.md), code review, test evidence and final council review | Council findings and resulting corrections are recorded separately from experimental evidence; council review is not independent GPU certification. |

## Code and tool coverage

| Component | Verification performed |
|---|---|
| `repro.py`, source pin and parsers | CPU source-drift/extra-file and native-parser tests; fresh full checkout verification; real pretraining and main fine-tuning |
| Data/settings/manifest handling | CPU malformed/nonfinite inputs, mapping, stage isolation, collision and overwrite rejection; full native data validation |
| `evaluate.py` | Strict-load failure and test-only isolation tests; actual saved-checkpoint evaluation in both runtime builds; fresh evaluations of all three exports |
| `predict.py` | Label-adaptation and failure tests; 128-flow original check and 1,041-flow fresh unlabeled inference |
| `replay.py` | Independent metric and HTML-escaping tests; all-seed prediction recomputation; actual browser controls and layout checks |
| Asset acquisition | Hash/atomic-output/reuse failure tests; pinned original assets acquired and validated; raw assets kept outside publication |
| GB10 build / runtime tools | Native extensions rebuilt in a second environment; seven numerical checks in each build, repeated during this audit; fresh dependency-install commands |
| Experiment collector / exports | Full epoch logs, finite changed weights, checkpoint selection, actual optimizer counters, additional disposable-copy gradient checks and tensor-identical exports |
| Benchmark / export probe | Both commands executed originally and again during this audit; every timing sample and the actual export failure retained |
| Presentation / guide generators | Rendered PDF/PPT, speaker-note matching, guide-source equality, question coverage, local links, unresolved-token and package-hash checks; visual review |
| CI and Pages workflows | CPU tests/verifier on Python 3.10/3.12; successful Pages deployment and anonymous download checks bound to published revisions |

No finite audit proves that software has no bugs. The checks establish these specific claims and failure behaviors; they do not validate every optional upstream setting, GPU architecture, malicious input, operating system or operational network.

## Improvements made during the final audit

- Added a plain-language, offline field guide with the same slide order and script as the deck.
- Added a three-route quickstart, expected outputs, troubleshooting, a seven-question crosswalk and an explicit authors’ repository/dataset comparison.
- Expanded the presentation to 16 slides and the briefing to eight pages with setup, test results and source differences.
- Added automatic detection of guide, speaker-note and answer-map drift. Kept original training/model/prediction evidence unchanged.
- Added a rendered-PDF page-count gate after correcting an extra reference-only page; bound the page map to actual PDF hashes and tested rejection of an incorrect count.
- Rechecked every model-only export and all unlabeled seed-0 predictions; repeated native numerical checks, masked-pretraining execution, model timing and the export probe.
- Corrected the lesson’s stale pointer to the duplicate-counting reference and reviewed the affected teaching material.

## Remaining work is not marked complete

Paper-level scientific reproduction, full pretraining provenance, all paper datasets/ablations, compatible live capture, independently evaluated customer traffic, calibrated confidence, unknown-attack handling, operational alert/blocking policy, target NPU/SmartNIC execution and inherited asset rights remain unresolved. The repository makes these gaps inspectable; it does not rename them as completed tests.
