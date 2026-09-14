# Current project acceptance and seven-question map

This map covers the original flow experiment, its confidence-calibration extension and the later packet adaptation. **Executed** means a command produced retained evidence. **Explained** means a topic is taught; it does not mean a proposed deployment was implemented. Historical counts remain in their dated records. The [cleanup audit](../research/accuracy-cleanup.md) records fresh checks against the current repository.

## The seven customer questions

| Question | Current answer | Where to present it |
|---|---|---|
| What did you try, and what works now? | Native flow training/inference, flow calibration, both-CSV packet training and unlabeled packet inference, with saved evidence and a recorded replay | [Packet slides/script 1, 4–7](packet-addendum/packet-addendum-script.md); [v4 course map](video-verification-v4.md#seven-questions) |
| How do training and inference work? | Reconstruction pretraining learns representations; supervised training fits labels; validation selects weights; inference freezes them | Packet slides 3–4; v4 paper/training chapters; [paper/data guide](paper-and-data-explained.md) |
| What goes in and what comes out? | Flow route: bytes + sizes + intervals → six classes. Packet route: one row's 1,500 bytes → benign/attack logits and uncalibrated scores | Packet slides 2–3; [flow runbook](runbook.md); [packet setup](packet-study-setup.md) |
| What did we reproduce versus the paper? | Three source-based flow runs averaged 86.65% accuracy, versus the paper's 97.50%. Packet results are a separate one-seed adaptation with six native arms and nine controls | Packet slides 4–6; [flow results](results.md); [packet report](packet-model-study.md); [upstream comparison](upstream-comparison.md) |
| What could a simple IDS demo look like? | The browser replays measured flow predictions. A CLI prototype can classify formatted unlabeled packets and log outputs for review. Live capture and blocking are absent | Packet slides 7–8; v4 demo chapter; [working replay](demo/index.html) |
| How could this map to an NPU / SmartNIC? | Packet handling, buffering and supported neural operators would need an explicit port and end-to-end validation | Packet slide 8; v4 hardware chapter; [hardware roadmap](hardware-roadmap.md) |
| What is missing or not working? | Exact paper reproduction, verified live flow joins, independent customer validation, packet calibration, unknown-attack handling, graph export and target-accelerator execution | Packet slides 6–8; v4 limitations; boundaries below |

Each packet slide's notes appear in both the [PowerPoint](packet-addendum/NetMambaPlus-packet-addendum.pptx) and [script](packet-addendum/packet-addendum-script.md); the [PDF](packet-addendum/NetMambaPlus-packet-addendum.pdf) matches its slide content. The v4 video/handbook/slides explain the earlier flow/calibration edition. They do not explain the later packet training. The original [16-slide question map](answers.md) remains a historical companion, not the complete current map.

## Requirements, executed evidence and limits

| Requirement | Evidence and actual result | Boundary |
|---|---|---|
| Explain the paper and both CSVs | [Plain-language guide](paper-and-data-explained.md), [comparison](upstream-comparison.md), original metadata profile and later packet manifest | Missing flow identity/order is disclosed; familiar filenames do not prove export provenance |
| Connect both CSVs to the model | [Packet study inventory](evidence/packet-study/index.json): all 1,490,136 rows / 2,235,204,000 byte cells validated; global exact-payload grouping and partitioning | One-packet adaptation, not invented flows; near duplicates and capture independence remain unknown |
| Perform real packet training | Six native runs each completed 1,000 updates; nine controls completed, including six converged logistic fits | One model seed, capped subsets and replacement sampling. Selected checkpoint update counts differ from completed training counts |
| Inspect all packet outcomes | [Native results](evidence/packet-study/results.json) and [control results](evidence/packet-study/controls/evaluation/results.json), recomputed from retained predictions | Group and row weighting are separate. UNSW metadata control outperforms native models there; CIC selected test has no PortScan and four DDoS rows |
| Run saved packet inference without labels | 25,930 classes agreed; complete input validation and checkpoint/code receipts retained | Two strict CIC logit comparisons fail in the matched FP32 replay. Later portability recheck predicted 128 rows while validating the full input; it is not a new full inference claim |
| Establish original native flow inputs | [Native validation](evidence/native-data-validation.json): all 10,404 flows, six-class mapping and known split overlaps | CICIoT2022 is a separate dataset from CICIDS2017; exact raw overlaps do not establish capture independence |
| Preserve the original source and execute flow training | 103 upstream files pinned; [three 120-epoch / 7,920-update runs](evidence/results.json), strict evaluation and model-only export checks | Source batch/rate differ from the paper; full pretraining history and prior exposure remain unknown |
| Exercise masked pretraining | Separate training-only two-epoch / 132-update functional check | Does not reproduce full Browser/Kitsune pretraining; its weights did not initialize the main flow runs |
| Improve confidence handling | [Calibration evidence](evidence/calibration/results.json): mean NLL 0.4416 → 0.4172; ECE 7.03% → 3.82%; predicted classes unchanged | Retrospective flow confidence, not accuracy improvement. Fixed 0.90 threshold admits more errors as coverage rises; no operational or packet calibration claim |
| Build and test on GB10 | Native extension builds, seven numerical comparisons and complete-model execution in [portability evidence](../portability-evidence.json); separate real packet training | Other physical GPUs and native CPU/Windows/macOS/NPU/SmartNIC execution remain unvalidated |
| Support other systems | [Six hosted OS/Python jobs](https://github.com/buffbeefalo/netmambaplus-reproduction/actions/runs/34815032176) at the published baseline; [current support matrix](../support-matrix.md) | Portable harness/evidence checks, not neural training on those systems |
| Provide a demonstration and teaching materials | Recorded replay, v4 one-hour video, matching handbook/PDF/PPT/transcript, packet addendum and [every-file guide](../repository-walkthrough.md) | Video is the earlier edition. Actual media checks are recorded; human full-watch/all-caption acceptance remains pending |
| Make setup and tests understandable | [Current quickstart](quickstart.md), separate flow/packet instructions and fresh [audit](../research/accuracy-cleanup.md) | Full Git history is needed for current historical video verification; an old ZIP is a different edition |
| Keep presentations aligned with evidence | Original package checks plus `verify_packet_briefing.py`: result-derived source, slide order/content, attached notes, script and reviewed PDF identities | Portable checker does not render PowerPoint, reread PDF layout or certify video quality |
| Share research and use council | [Research record](../research/research-record.md), preserved run outcomes and [cleanup council result](../research/accuracy-cleanup-council.json) | Latest cleanup council is ESCALATED / UNRATIFIED. Direct checks and corrections do not turn it into consensus |
| Publish accessible files | Public repository, Pages, versioned course downloads and explicitly historical customer ZIP | Use the [customer index](README.md) to choose the right edition; raw research assets and weights remain external |

## What the current checks establish

The standard-library suite tests concrete acceptance and failure behavior in data preparation, identity checks, training orchestration, strict inference, calibration, evidence arithmetic, document consistency and historical media verification. Optional numerical/native tests run only in suitable environments. GitHub CI reports each revision's test totals separately.

The retained GPU logs and checkpoints establish that the recorded training occurred. CPU verification recomputes those records; it does not train again. The cleanup audit rechecks raw-source identities and prepared-array integrity locally, independently recomputes the saved packet scores, verifies the downloaded historical ZIP, and reviews current documentation. It preserves the experiment and media bytes.

## Remaining work is not marked complete

The paper's 97.50% result and complete scientific protocol were not reproduced. Live capture, verified flow extraction from these CSVs, independent customer-traffic evaluation, packet confidence calibration, general unknown-attack detection, operational alert/blocking policy and NPU/SmartNIC deployment remain missing. The strict Torch graph-export probe failed on the custom causal convolution. Inherited asset redistribution/commercial terms remain unresolved.

A finite audit establishes the listed behaviors and measurements, not universal bug-freedom or coverage of every upstream option, device, input or operational network.
