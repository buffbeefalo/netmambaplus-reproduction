# Customer package — NetMamba+

Prepared for Tuesday, **15 September 2026**. Start with the plain-language guide, then use the matching 16-slide presentation, eight-page briefing and recorded-inference demo. The technical evidence and commands are available below for review.

| Open or download | Purpose |
|---|---|
| [Plain-language field guide](https://buffbeefalo.github.io/netmambaplus-reproduction/guide.html) · [Offline page](demo/guide.html) | Every slide explained for a reader new to networking and machine learning, with the matching script and glossary |
| [Simple setup, usage and testing](quickstart.md) | Choose a browser-only, CPU-verification or GPU-execution route; see expected outputs and actual test results |
| [Paper, datasets and authors’ repo comparison](upstream-comparison.md) | What the research is about, what each dataset contains and exactly what this project adds |
| [Seven-question presentation map](answers.md) · [Acceptance review](acceptance.md) | Locate each answer in the slides, script, guide and briefing; inspect evidence and limits |
| [Briefing PDF](NetMambaPlus-customer-briefing.pdf) · [Readable Markdown](briefing.md) | Short explanation of the model, experiment, results and remaining work |
| [PowerPoint](NetMambaPlus-customer-slides.pptx) · [Slide PDF](NetMambaPlus-customer-slides.pdf) | Editable presentation with speaker notes |
| [Browser demo](https://buffbeefalo.github.io/netmambaplus-reproduction/) · [Offline HTML download](https://raw.githubusercontent.com/buffbeefalo/netmambaplus-reproduction/main/docs/customer/demo/index.html) | Replay of actual saved-classifier predictions; opens without CUDA |
| [Recorded walkthrough](demo/recorded-demo.webm) · [Screenshot](demo/replay-screenshot.png) | Clearly labeled presentation backups |
| [Complete customer ZIP](https://github.com/buffbeefalo/netmambaplus-reproduction/releases/latest/download/netmambaplus-customer-package.zip) | Downloadable copy of the package for the meeting |
| [Results and errors](results.md) · [Machine-readable results](evidence/results.json) | All three seeds, per-class scores, curves, checkpoint hashes and timing |
| [Talk track](talk-track.md) · [Customer questions](questions.md) | Help explaining the work without memorizing the code |
| [Runbook](runbook.md) · [Teaching lesson](../lesson.md) | Reproduce the setup, training, inference and document build |
| [Research record](../research/research-record.md) | Reviewed AI-assisted findings, sources, failed attempts and council scope |
| [IDS / hardware roadmap](hardware-roadmap.md) | What a live IDS and NPU/SmartNIC port still require |
| [Verification record](verification.md) · [Artifact index](evidence/artifact-index.json) · [SHA-256 checksums](SHA256SUMS) | What was checked and how to verify the files |
| [Final council review and corrections](../research/final-council-review.md) | Exact outcome, decision hash, acceptance conditions and their evidence limits |

If GitHub shows a binary preview page, use its download button. The release ZIP contains the files for offline use. The hosted demo and downloaded HTML both display recorded predictions; display speed does not measure inference speed.

## Completion checklist

| Requested or implied deliverable | Evidence / status |
|---|---|
| Explain the original three files and their connection | Full CSV metadata scans and the [research record](../research/research-record.md); packet-to-flow mismatch made explicit |
| Run actual training | Three 120-epoch source-based fine-tuning runs; [results and logs](results.md) |
| Exercise NetMamba+ masked pretraining | 132-update training-only functional run; [native record](evidence/pretrain-functional/manifest.json) |
| Save and verify trained classifiers | Selected-checkpoint hashes, optimizer counters, changed parameters and model-only export provenance in [results.json](evidence/results.json) |
| Run inference from saved weights | Native final test, fresh strict evaluation and replay agree; [seed-0 strict result](evidence/seed0/eval/metrics.json) |
| Predict on flows without known labels | Working `predict.py`; [measured agreement check](evidence/unlabeled-inference-agreement.json) |
| Make setup reproducible | Automated native build rehearsed in a second environment; [build record](evidence/runtime/build-report.json) and [numerical checks](evidence/runtime/rehearsal-numerical-check.json) |
| Provide a usable demonstration | [Replay](https://buffbeefalo.github.io/netmambaplus-reproduction/), [recording](demo/recorded-demo.webm) and [browser checks](evidence/browser-check.json) |
| Separate measured and paper results | All-seed metrics and explicit configuration differences in [results](results.md) and [briefing](briefing.md) |
| Explain inputs, training and outputs simply | [Briefing](briefing.md), [slides](NetMambaPlus-customer-slides.pptx), [lesson](../lesson.md) and [talk track](talk-track.md) |
| Provide a nontechnical page that follows the PPT/script | [Field guide](demo/guide.html), generated in the same slide order with matching speaker script |
| Make setup, use and test outcomes simple | [Quickstart](quickstart.md), slides 14–15 and briefing page 7 |
| Explain changes from the authors’ repo and the paper/data | [Comparison](upstream-comparison.md), slide 13 and briefing page 8 |
| Measure inference cost | Synchronized model-only latency samples in [benchmark evidence](evidence/benchmark/metrics.json) |
| Investigate accelerator portability | Actual [Torch export probe](evidence/export-probe/metrics.json), operator inventory and [hardware roadmap](hardware-roadmap.md) |
| Share research and editable material | [Research record](../research/research-record.md), [slide source](presentation-source.json), [briefing source](briefing-source.md) and [generator](../../tools/build_customer_package.py) |
| Audit and publish reviewable files | [Verification record](verification.md), CPU CI, checksums, public repository and release bundle |

“Completed training” means the declared source schedule actually ran. It does not mean the paper's complete scientific experiment was reproduced. The short pretraining run is a functional check, not a replacement for the paper's Browser/Kitsune corpus.

## What remains outside the completed measurement

The exact original pretraining corpus/history, all paper datasets and ablations, a verified live capture-to-tensor adapter, independent customer-traffic validation, calibrated alert policy and actual NPU/SmartNIC deployment remain unestablished. The six benchmark classes do not provide general attack coverage. Official split overlaps and unknown earlier checkpoint exposure accompany every accuracy claim.

Raw packet data, upstream source and original weights remain external author-distributed assets. The saved local model-only classifier exports retain their provenance, but inherited redistribution/commercial terms remain unresolved. This package publishes the result evidence and commands to reproduce training; it does not mirror those research assets or confer new rights over them.

The council's exact plan decision and hash are in the research record. That review is separate from the subsequent deterministic checks and does not certify the final model independently. The historical unratified audit remains a dated record.
