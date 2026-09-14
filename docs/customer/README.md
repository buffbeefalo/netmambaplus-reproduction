# Customer package — start here

This project has **two measured NetMamba+ experiments** and a confidence-calibration extension. The original experiment classifies six kinds of CICIoT2022 **flows**. The newer experiment trains the native encoder on both supplied **packet CSVs** and predicts their supplied benign/attack labels. Neither is a deployed live IDS, and the paper's 97.50% result was not reproduced.

For a customer handoff, send the **packet PDF, PowerPoint and script together with the v4 course**. The course explains the paper, the original flow experiment and calibration; it predates the packet training. A current repository download contains both sets of material. The older release ZIP is an archived edition.

| Start with | What it explains |
|---|---|
| [The paper and both CSVs, in plain language](paper-and-data-explained.md) | What the supplied files contain and how each is used |
| [Setup, use and tests](quickstart.md) | Browser viewing, portable evidence checks and actual CUDA execution |
| [Every file and every download](../repository-walkthrough.md) | One searchable guide to the current repository, local assets and archived releases |
| [Current acceptance and seven-question map](acceptance.md) | What works, the supporting evidence and remaining gaps |
| [Cleanup and accuracy audit](../research/accuracy-cleanup.md) | Corrections, fresh checks and the council's actual outcome |

## Current packet study: both uploaded CSVs

| Read or download | Purpose |
|---|---|
| [Eight-slide PDF](packet-addendum/NetMambaPlus-packet-addendum.pdf) · [PowerPoint](packet-addendum/NetMambaPlus-packet-addendum.pptx) · [Matching script](packet-addendum/packet-addendum-script.md) | Present the CSV integration, architecture changes, measured results and limitations |
| [Study report](packet-model-study.md) · [Setup and unlabeled prediction](packet-study-setup.md) | Repeat preparation, fixed-budget training, controls and saved-model inference |
| [Indexed evidence](evidence/packet-study/index.json) · [Document review](packet-addendum/verification.json) | Inspect every retained comparison and the reviewed presentation identities |

All **1,490,136 rows** and their **2,235,204,000 byte cells** were validated. Six native GPU models each completed **1,000 updates**: CIC-only, UNSW-only and joint training, each with pretrained and scratch initialization. The joint pretrained model scored **97.56% / 94.29% group-weighted balanced accuracy** on the CIC / UNSW test subsets. These are packet-study metrics, not the original flow accuracy or paper scores. A metadata-only control reached **99.34% on UNSW**, and cross-source transfer was weak.

All **25,930** held-out predicted classes agreed in a separate saved-model check. Two CIC rows still failed the declared strict logit tolerance in the matched FP32 comparison. Those failures are retained. The study uses one model seed, capped subsets, exact-payload grouping and unknown prior checkpoint exposure; it does not establish independent-capture or customer-network performance.

## Preserved v4 course: original flows and calibration

| Read or download | Scope |
|---|---|
| [Watch the one-hour video](https://buffbeefalo.github.io/netmambaplus-reproduction/video/) · [Download MP4](https://github.com/buffbeefalo/netmambaplus-reproduction/releases/download/course-video-v4/NetMambaPlus-one-hour-course.mp4) | Flows and calibration; no later packet-training lesson |
| [Handbook PDF](demo/video/v4/NetMambaPlus-course-handbook.pdf) · [PowerPoint](demo/video/v4/NetMambaPlus-course-slides.pptx) · [Slide PDF](demo/video/v4/NetMambaPlus-course-slides.pdf) · [Transcript](demo/video/v4/transcript.md) | Matching historical course documents and script |
| [Video checks and review limits](video-verification-v4.md) | Actual media checks; human full-watch/all-caption acceptance remains pending |
| [Original flow results](results.md) · [Confidence calibration](confidence-calibration.md) | Three complete 120-epoch runs; separate retrospective confidence measurements |
| [Recorded browser demo](https://buffbeefalo.github.io/netmambaplus-reproduction/) · [Offline replay](demo/index.html) | Original uncalibrated seed-0 flow predictions, including errors; playback only |
| [Flow runbook](runbook.md) · [Hardware support](../support-matrix.md) | Repeat native flow training and inference in the checked CUDA runtime |

Flow test accuracies were **91.26%, 84.05% and 84.63%**, averaging **86.65%**. The separate 132-update masked-pretraining run was a functional check; the three classifiers instead started from the authors' released pretrained weights. Optional flow calibration improved retrospective score metrics while leaving every predicted class unchanged. At the illustrative 0.90 accept/defer threshold, seed-0 accepted errors increased from 9 to 37 as more predictions were accepted. It is not a validated operational alert policy.

## Earlier customer presentation: archived scope

The original **16-slide deck, eight-page briefing, field guide and release ZIP** describe the original flow experiment before calibration and packet training. Their measurements remain valid within that scope. Use the material above for the complete current handoff.

| Historical item | Matching explanation |
|---|---|
| [Briefing PDF](NetMambaPlus-customer-briefing.pdf) · [Markdown](briefing.md) | Original flow experiment |
| [PowerPoint](NetMambaPlus-customer-slides.pptx) · [Slide PDF](NetMambaPlus-customer-slides.pdf) · [Script](talk-track.md) | Original 16-slide presentation |
| [Slide-by-slide field guide](https://buffbeefalo.github.io/netmambaplus-reproduction/guide.html) · [Question map](answers.md) | Same historical slide order and speaker text |
| [Versioned release ZIP](https://github.com/buffbeefalo/netmambaplus-reproduction/releases/download/customer-2026-09-15-audited/netmambaplus-customer-package.zip) · [Dated verification](verification.md) | Frozen audited edition, with its original test counts; not today's full repository |

GitHub's binary preview has a download button. Download the desired PDF/PPT/MP4 and script before an offline meeting. Viewing needs no Python, CUDA, API key or chat subscription. Fresh inference requires a compatible GPU environment and separately acquired or locally trained weights.

## What remains missing

Exact paper-level reproduction, full original pretraining provenance, verified packet-to-flow joins, live capture and blocking, independent customer evaluation, calibrated packet confidence, unknown-attack handling, graph export, and NPU/SmartNIC execution remain unestablished. The [upstream comparison](upstream-comparison.md) and [hardware roadmap](hardware-roadmap.md) explain these boundaries.

Raw CSVs, original upstream source and inherited weights are external research assets, with unresolved redistribution/commercial terms. The public repository contains reproducible commands and result evidence; it does not redistribute those assets or confer new rights. Council records are preserved by run and outcome. An audit discussion is separate from an executed training or hardware test.
