# Current packet-client acceptance and seven-question map

**The supported workflow uses both packet CSVs and the joint pretrained packet model.** “Executed” means retained command evidence; “explained” does not mean a proposed deployment was implemented. Read the [client project guide](client-project-guide.md) for the complete explanation and [packet setup](packet-study-setup.md) for ordered commands.

## The seven customer questions

| Question | Current answer | Evidence/explanation |
|---|---|---|
| What did you try and what works now? | Full CSV validation, native packet training, nine controls, saved-checkpoint unlabeled inference, portable checks and a recorded packet demo | [Packet report](packet-model-study.md), [client guide](client-project-guide.md#results), [indexed evidence](evidence/packet-study/index.json) |
| How do training and inference work? | Transfer compatible pretrained encoder weights; supervised updates learn binary targets; validation selects a checkpoint; inference freezes it | [Training explanation](client-project-guide.md#training), packet slides 3–4 |
| What goes in and what comes out? | One row's 1,500 bytes enters the native packet encoder; two logits, benign/attack class and uncalibrated probabilities come out | [Input/output explanation](client-project-guide.md#model), [packet predictor](../../tools/predict_packets.py) |
| What was reproduced versus the paper? | Six 1,000-update packet comparisons are a separate adaptation; joint group-balanced accuracy is 97.56% / 94.29%; no claim of the paper's 97.50% flow accuracy | [All results/controls](packet-model-study.md#results-and-limits), [upstream comparison](upstream-comparison.md) |
| What could a simple IDS demo look like? | The browser displays retained joint-model packet predictions; GPU CLI predicts formatted unlabeled CSVs | [Packet viewer](https://buffbeefalo.github.io/netmambaplus-reproduction/), [demo explanation](client-project-guide.md#demo); capture/alert/blocking service remains absent |
| How could this map to an NPU / SmartNIC? | Establish byte extraction and queue semantics, choose a target, port custom operators, then validate numerics and complete-system behavior | [Hardware roadmap](hardware-roadmap.md); no target execution claim |
| What is missing or not working? | Independent customer validation, calibrated packet confidence, unknown-attack coverage, live extraction/service, numerical repeatability and accelerator execution | [Remaining work](client-project-guide.md#remaining-work) |

The [packet PDF](packet-addendum/NetMambaPlus-packet-addendum.pdf), [PowerPoint](packet-addendum/NetMambaPlus-packet-addendum.pptx) and [matching script](packet-addendum/packet-addendum-script.md) present this packet study. The preserved v4 course and earlier flow presentations are historical background, not another client route.

## Requirements, completed evidence and limits

| Requirement | Supporting record/check | Boundary |
|---|---|---|
| Connect both CSVs to the model | All 1,490,136 rows and 2,235,204,000 byte cells validated; global identical-payload grouping; source/joint native training | Missing flow identity/order is not invented; capture/near-duplicate independence unknown |
| Perform actual training | Six native runs each completed 1,000 updates; selected checkpoints frozen before tests | One model seed, caps and replacement sampling; checkpoint selection step may precede the final achieved update |
| Preserve meaningful comparisons | Nine controls completed, six logistic fits converged; all native/control source tests retained | UNSW metadata control outperforms neural models there; selected CIC has no PortScan and four DDoS rows |
| Run unlabeled packet inference | 25,930 original classes agreed; two strict logit failures retained | Later 128-row client check has 76 failures despite complete class agreement; separate scopes stay separate |
| Check the packet model on GB10 | Native transfer/shape/gradient/update/reload tests; new prepared-directory runtime gate passed 17 cases without skips | Functional checks use synthetic loss targets; not a new full study, fresh installation or accuracy result |
| Deliver one executable client workflow | Explicit packet-only export, checkpoint-only default assets, packet verifier/demo and source-to-client synchronization | Internal shared source/identity helpers remain; historical flow code/media remain in the full source edition |
| Explain setup and every component | [Client guide](client-project-guide.md), [quickstart](quickstart.md), [setup](packet-study-setup.md), [every-file walkthrough](../repository-walkthrough.md) | Raw CSVs/weights are separate acquisitions; history-bound source checks require Git objects |
| Check the delivered software | Source/client regression suites, packet evidence arithmetic, fresh standalone export and hosted platform CI | CPU jobs do not rerun native training; counts belong to their exact revisions |
| Provide a truthful demo | Full joint-source packet groups, original label counts, conflicts and declared metrics; browser filtering and runtime errors checked | Recorded viewer, no new inference, capture, blocking or operational alert counts |
| Keep presentations consistent | Shared evidence-derived slide source, notes/script checks and reviewed PDF/PPT identities | Content checks do not certify old video coverage or a new hardware deployment |
| Preserve research history and council outcomes | Frozen scientific/media records and separately recorded review outcomes | Single-route council aborted on provider HTTP 529; no consensus was produced |

The original packet protocol, training implementation and evidence retain their recorded identities. Earlier flow experiments, calibration and media retain their historical meaning. A successful audit verifies listed behaviors and records, not universal bug-freedom or every possible input, device and customer network.
