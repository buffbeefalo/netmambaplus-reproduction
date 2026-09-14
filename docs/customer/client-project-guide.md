# Understand and explain the client project

**There is one supported workflow: the model trained from both supplied packet CSVs.** This guide explains the complete client delivery, from the PDF and data to training, prediction, testing, demonstration and maintenance. It assumes no networking or machine-learning background.

We built and exercised a NetMamba+ **packet adaptation** on NVIDIA GB10. It learns the supplied benign/attack labels from packet bytes. The client uses the validation-selected **joint pretrained** model, meaning one classifier trained with examples from both CICIDS2017 and UNSW. The experiment includes other packet models and simple controls to test that choice; they are comparison evidence within this workflow.

The project includes runnable code, measured results, verification and an offline evidence viewer. It is not a live intrusion-detection service, and its packet scores do not reproduce the paper's original flow accuracy.

**Jump to:** [The starting files](#starting-files) · [Inputs and outputs](#model) · [Training](#training) · [Results](#results) · [Actual tests](#tests) · [Setup and use](#setup) · [Demo](#demo) · [Every component](#components) · [Changes from the authors](#upstream) · [Updates](#updates) · [Hardware](#hardware) · [Remaining work](#remaining-work) · [Handoff](#handoff).

## Which repository should I send?

| Edition | Purpose |
|---|---|
| [netmambaplus-client](https://github.com/buffbeefalo/netmambaplus-client) | Concise executable delivery: packet training/prediction, setup, tests and measured packet evidence |
| [netmambaplus-reproduction](https://github.com/buffbeefalo/netmambaplus-reproduction) | Development source and full explanation: shared implementation/evidence, this guide, research records, teaching material and publishing tools |

Send the client repository **and this page**. For a particular filename or download, use the [every-file walkthrough](../repository-walkthrough.md). The client omits videos, slide decks, presenter scripts and long explanations. Its executable Python programs remain necessary to run the model.

The client has a separate Git history and receives verified exports from this reproduction repo. Its [CLIENT_MANIFEST.json](https://github.com/buffbeefalo/netmambaplus-client/blob/main/CLIENT_MANIFEST.json) identifies its source revision and all delivered files. Raw CSVs, authors' source and model weights are separate acquisitions; a code download does not include a ready-trained classifier.

<a id="starting-files"></a>
## 1. What were the PDF and two CSVs?

| Supplied file | What it is | What we did with it |
|---|---|---|
| `2601.21792v1.pdf` | The NetMamba+ research paper: architecture, learning method and authors' experiments | Read its method, compared the pinned source implementation and established how this packet adaptation differs |
| `Payload_data_CICIDS2017.csv` | 1,410,255 packet rows with 15 supplied labels | Profiled and fully validated it, grouped duplicate payloads, and used selected groups for supervised packet training |
| `Payload_data_UNSW.csv` | 79,881 packet rows with 10 supplied labels | Performed the same checks and combined its selected groups with CIC in joint training |

The PDF provides the research method. It is not fed into the traffic classifier. The CSVs are text tables, not a database server. Each row contains **1,500 ordered payload-byte slots**, followed by `ttl`, `total_len`, `protocol`, `t_delta` and `label`: 1,505 columns in total. A byte is an integer from 0 to 255; payload means the packet content represented by the export. The four metadata fields describe recorded properties; the label is the supplied training answer.

We first profiled counts, labels and metadata. Later preparation separately validated **all 1,490,136 rows and 2,235,204,000 payload-byte cells**. This accounts for every row but does not mean every row contributed to a training update. [Original profile](evidence/uploaded-csv-profile.json); [packet preparation manifest](evidence/packet-study/manifest.json).

A **packet** is one unit sent over a network. A **flow** groups related packets using a defined connection identity and order. The paper combines flow bytes, sizes and timing sequences. The CSVs lack the verified connections, ordering and extraction history needed to reconstruct those flows. Five adjacent rows cannot be assumed to belong together. Their `t_delta` field also lacks established timing semantics.

We therefore use each row's stored bytes directly in an explicit packet adaptation. We do not invent missing flow inputs. The [paper and data explanation](paper-and-data-explained.md) lists every label/count, explains each column and walks through the major parts of the PDF. Earlier experiments with a separate CICIoT2022 flow release remain historical research, not a second client workflow. CICIoT2022 and CICIDS2017 are different datasets.

<a id="model"></a>
## 2. What enters the model and what comes out?

| Part | Actual packet implementation |
|---|---|
| One observation | One packet's 1,500 stored payload bytes |
| Normalization | Convert bytes to floating-point values using `byte / 127.5 - 1` |
| Learned representation | Four bytes per vector: 375 byte vectors plus three summary/prefix positions = 378 tokens |
| Encoder | Four original Mamba blocks; each token is a vector of 256 numbers |
| Classifier | A new two-class head; 1,852,416 model parameters in total |
| Prediction | Two logits, benign/attack class, uncalibrated probabilities and a completion receipt |

A **token** here is a learned numerical vector representing part of the input, not a word. Mamba scans the sequence while updating a learned numerical state. Summary vectors feed the **head**, the final layer producing the two scores. This model is a numerical traffic classifier; it does not call Codex, Claude or another chat service to classify packets. Its internal state is not an implemented live network-connection cache.

The size and interval inputs contain **zero observations**. Two associated prefixes remain learned components, but are not supplied metadata. TTL, recorded length, protocol, time delta, dataset identity and labels never enter the neural forward call. Stored zeros remain because the export does not reliably establish which values are padding. The separate metadata controls use different input features and help interpret the neural results. [Exact architecture and learned-position mapping](packet-model-study.md#from-one-row-to-one-prediction).

CIC's `BENIGN` and UNSW's `normal` map to class 0, benign. Other explicitly registered source labels map to class 1, attack. Unknown labels fail validation. This connects both datasets through a binary target without pretending their original attack names have identical meanings or independently adjudicating their annotations.

A **logit** is a raw score. Softmax converts the two logits into positive scores that sum to one; the largest chooses the class. `tools/predict_packets.py` writes `class_name`, `logits` and `probabilities`, along with row/payload identity. A high model score is not a proven probability of malicious traffic on a customer's network. These packet scores have not been calibrated. An unlabeled input cannot produce an accuracy measurement.

<a id="training"></a>
## 3. How do training and inference work?

Training changes the model's weights using examples. Inference freezes a selected set of weights and applies them to new inputs. A **checkpoint** stores those weights and the metadata needed to interpret them.

The paper's learning approach first reconstructs deliberately hidden input content during **masked pretraining**, then learns labeled categories during **supervised fine-tuning**. Our packet model starts with the authors' released pretrained encoder weights and a fresh binary head. Fifty compatible trunk tensors are transferred, 31 reconstruction-related tensors are excluded, and the packet positions are mapped explicitly. The complete earlier training history/exposure of the released checkpoint is unknown; we do not claim to recreate the paper's full pretraining corpus.

The recorded packet study compares CIC-only, UNSW-only and joint training, each with pretrained and scratch initialization: **six models**. Scratch means starting with fresh weights. All six completed 1,000 optimizer updates with batches of 64 groups and one model seed. Joint batches contained 32 groups from each source. The client prediction uses the validation-selected joint pretrained checkpoint; the other arms test transfer and initialization effects.

Training groups change weights. Validation groups select the checkpoint. Test groups measure the selected model afterward. Validation every 100 updates selected the earliest best group-weighted macro-F1 checkpoint; all choices froze before final tests. Macro-F1 averages a measure of precision/recall across classes. An **update** changes weights using a batch; an **epoch** is a pass over a training dataset. This study samples with replacement, so 1,000 updates does not mean 1,000 epochs or a pass over every original row. A **seed** records random choices.

Preparation groups identical payload bytes by SHA-256 and assigns each global group to training, validation or test, targeting 70/15/15 with split seed 17. Source-specific caps then select groups without consulting labels. There are 478,044 globally distinct payloads; ten occur in both files and nine of those have conflicting binary labels. Contradictory labels remain as proportions: nine benign rows and one attack row give a 90%/10% target. Exact grouping prevents identical inputs crossing partitions but cannot prove independent captures or eliminate near duplicates. [Protocol and complete support/sampling counts](packet-model-study.md).

A **manifest** records input/configuration identities and produced artifacts. A **SHA-256 hash** identifies exact bytes; it detects changed files but cannot prove their contents are true. Training receipts record achieved updates and selected checkpoints. Strict checkpoint loading rejects incompatible weights and metadata. A command requesting 1,000 updates is not evidence that those updates completed.

<a id="results"></a>
## 4. What actually worked and what were the results?

| Completed work | Recorded outcome | Interpretation |
|---|---|---|
| Both-source native training | Joint pretrained: **97.56% CIC / 94.29% UNSW group-weighted balanced accuracy** | The delivered packet model, measured on its selected test groups |
| Six native comparisons | All completed 1,000 updates; source-only scratch selections made constant-class decisions at 50% balanced accuracy | Completed training includes weak outcomes |
| Nine simple controls | All completed; UNSW-only metadata control reached **99.34%** there | The neural model was not uniformly best |
| Saved-model unlabeled inference | All 25,930 predicted classes agreed with primary joint-model evaluation | Successful class reproduction, with two strict logit-comparison failures retained |
| Offline packet demo | Displays both joint-model test sets, original label counts and source-specific metrics | Recorded evidence; no new model inference in the browser |

**Balanced accuracy** averages benign and attack recall, so one common class does not dominate the headline. **Group weighting** gives each distinct payload total weight one, divided across conflicting labels. Row weighting gives every original CSV row one vote. The joint model's row-weighted balanced accuracy was 96.31% / 89.24%; repeated rows change the result. The [complete report](packet-model-study.md#results-and-limits) gives all six models, nine controls, confusion matrices, false positives, ranking metrics and subtype support.

Joint training gained 1.07 percentage points on UNSW and lost 1.11 on CIC against the corresponding pretrained source-only models. CIC-to-UNSW transfer was weak: the CIC-only pretrained model scored 53.73% on UNSW. These are single-seed observations, not evidence of a statistically robust general improvement. The selected CIC test set has no PortScan rows and only four DDoS rows.

The paper reports 97.50% **flow accuracy under different conditions**. That is not the same input, task or metric as these packet balanced-accuracy scores. Earlier separate source-based flow experiments averaged 86.65% accuracy; those historical results did not match the paper either. The packet study does not establish an improvement over that flow benchmark. [Paper/source comparison](upstream-comparison.md).

<a id="tests"></a>
## 5. What was actually tested?

Software checks and native GPU checks establish different things. **CI** means automated checks run by GitHub; a green portable job does not mean GPU training ran again.

| Check | Actual scope |
|---|---|
| Packet preparation and protocol tests | Accepted/rejected schemas, byte validity, label mapping, duplicate grouping, prepared-file integrity, split/budget bindings |
| Saved-evidence reviewer | Recomputes all native/control results and checks training completion, checkpoint selection, file identities and held-out membership |
| Fresh packet-specific GB10 gate | **17 native packet tests passed, zero skipped** using two prepared payloads per source; includes transfer, shapes, gradients, an optimizer update and strict checkpoint roundtrip |
| Packet demo checks | Preserve contradictory labels and group/row arithmetic; handle finite logits, ties, duplicate IDs, safe embedded data and existing output protection |
| Export/publication checks | Fresh standalone client package, required dependency closure, file hashes, drift rejection, managed removal and verified publication |
| Hosted platform CI | Linux x86-64, Windows x86-64 and macOS ARM64, each with Python 3.10 and 3.12; portable checks, with explicit optional skips |

The new native gate is a functional test using synthetic loss targets on stored bytes. It does not retrain the six-arm study or measure new accuracy. Its command is `tools/check_packet_runtime.py`; its receipt/log/probe report distinguish actual execution from skipped checks.

The [earlier client delivery audit](../research/client-edition-validation.json) records the previous two-route edition's counts and GB10 rechecks, including a separate capped packet comparison: all 20,000 CIC input rows validated, first 128 predicted, all classes matched, but **76 of 128 strict logit comparisons failed**, with maximum absolute difference 0.006159305572509766. That is separate from the original full 25,930-group inference comparison, which retained **two** strict failures. Both used declared relative tolerance `1e-4` and absolute tolerance `1e-6`. Do not combine those counts or claim all numerical comparisons passed.

A first earlier native-test invocation used the wrong cache directory and failed before native execution; its log and the corrected pass were retained. New packet setup accepts the prepared directory directly, avoiding that manual cache-path choice. The [current source CI](https://github.com/buffbeefalo/netmambaplus-reproduction/actions/workflows/ci.yml) and [client CI](https://github.com/buffbeefalo/netmambaplus-client/actions/workflows/ci.yml) identify each checked revision; old test totals do not describe the new smaller client export. Successful evidence verification confirms the retained record, including known failures.

<a id="setup"></a>
## 6. How does someone set it up and use it?

First check the client and open its recorded demo. Git and Python 3.10 or 3.12 are sufficient; use `python3` if that is your interpreter's name.

```text
git clone https://github.com/buffbeefalo/netmambaplus-client.git
cd netmambaplus-client
python -m unittest discover -s tests -v
python tools/verify_client.py
python tools/render_packet_demo.py --output runs/packet-demo-new
```

The suite should end with `OK` and state its skips. The verifier must exit successfully. Open `runs/packet-demo-new/index.html`. Use fresh output paths to preserve earlier records. A client source ZIP also supports these checks. Full reproduction-repo historical video checks require a full Git clone.

For fresh model execution, follow the ordered [client SETUP.md](https://github.com/buffbeefalo/netmambaplus-client/blob/main/SETUP.md), or this repo's [packet setup](packet-study-setup.md). There is one sequence:

1. Install the checked Linux/CUDA/Python environment, fetch the pinned authors' source and pretrained initialization, build the extensions and pass numerical checks. The packet asset inventory downloads only the initialization, not a flow dataset.
2. Supply both original labeled CSVs to `packet_data.py`. Review `manifest.json`, including both registered-source matches. Run the packet-specific native gate against the prepared output.
3. Freeze the protocol, fit controls, run the six-arm packet study, and evaluate the frozen controls. Inspect completed receipts and the validation-selected checkpoints.
4. Read `selected_checkpoints.joint_pretrained` from `frozen-checkpoints.json`. Pass that checkpoint and an unlabeled packet CSV to `tools/predict_packets.py`.
5. Inspect `predictions.jsonl` and `receipt.json`. Recompute saved study evidence and use the packet demo to explain the recorded result.

The measured neural runtime is Linux ARM64 / GB10, Python 3.12, Torch 2.9.1+cu130 and CUDA toolkit 13.0. A GPU driver alone does not install the compiler toolkit. Other physical GPUs need their own build/numerical/packet gates. CPU/native Windows/macOS/NPU/SmartNIC model execution is not established. [Platform details](../support-matrix.md).

The unlabeled CSV must contain `payload_byte_1` through `payload_byte_1500`, optionally followed by the four metadata columns. It must not contain `label`; create a separate unlabeled copy. No flow assembly is involved. `--max-rows 128` limits prediction but still validates the whole input; the receipt explicitly reports capped coverage. Preserve the checkpoint's provenance. The released pretraining file is initialization for training, not a substitute for the trained joint classifier.

<a id="demo"></a>
## 7. What should I demonstrate?

Open the [packet evidence viewer](https://buffbeefalo.github.io/netmambaplus-reproduction/) or the locally generated page. Switch between **CICIDS2017** and **UNSW**, then choose **Any label disagreement** or **Conflicting supplied labels**. Filter benign/attack decisions or a payload-hash prefix, and select a hash to inspect its logits.

Each displayed row is a **distinct payload group**, not necessarily one original CSV row. The benign/attack label counts show how many original rows carry each annotation. A prediction can disagree with some labels within one contradictory group. The cards always describe the complete selected source test; filtering the table does not recompute or replace the reported benchmark score.

Explain that these are all 20,000 CIC and 5,930 UNSW held-out groups for the selected joint model. The browser reads bundled predictions without running the model or capturing traffic. For a live model demonstration on the checked GPU, run the separate prediction command on an already formatted unlabeled CSV and inspect the actual output receipt. That command is fresh inference, still without a live capture/alert service.

<a id="components"></a>
## 8. What does every part of the client do?

| Part | Responsibility |
|---|---|
| Client `README.md`, `SETUP.md`, `RESULTS.md`, `NOTICE.md` | Orientation, ordered execution commands, measured outcomes and inherited-asset attribution/boundaries |
| [packet_data.py](../../packet_data.py) | Full CSV validation, label mapping, duplicate grouping, deterministic partitioning and prepared arrays |
| [packet_model.py](../../packet_model.py) | Native encoder configuration, pretrained-state/position transfer, byte input contract and strict binary checkpoints |
| [packet_study.py](../../packet_study.py) | Shared artifact checks and group/row metric arithmetic |
| [repro.py](../../repro.py) | Internal source/identity helpers and the supported `fetch` operation; its historical flow orchestration is not part of this client workflow |
| [configs/packet-study.json](../../configs/packet-study.json) | The declared measured packet experiment settings |
| [configs/packet-assets.json](../../configs/packet-assets.json) | The pretrained initialization's expected bytes, hash and acquisition location |
| [configs/ciciot2022.json](../../configs/ciciot2022.json) | Retained internal configuration needed by source-fetch/build identity checks; it does not make flow training a supported client path |
| [requirements/gb10.txt](../../requirements/gb10.txt) | Pinned research dependencies for the tested native environment |
| [Asset fetcher](../../tools/fetch_assets.py), [CUDA builder](../../tools/build_cuda.py), [GB10 build helpers](../../tools/build_gb10.py) | Verify/acquire external assets and build native extensions in disposable copies |
| [Numerical check](../../tools/check_gpu_runtime.py), [packet runtime gate](../../tools/check_packet_runtime.py), [runtime recorder](../../tools/capture_runtime.py) | Exercise native operations/model behavior and record the environment; distinguish actual execution from portable checks |
| [Protocol freezer](../../tools/freeze_packet_protocol.py), [trainer](../../tools/train_packet_model.py), [controls](../../tools/packet_controls.py) | Freeze choices before training, execute six packet comparisons and fit/evaluate nine simple controls |
| [Packet predictor](../../tools/predict_packets.py), [CSV profiler](../../tools/profile_csvs.py) | Predict unlabeled packet bytes with receipts, and inspect CSV metadata |
| [Client verifier](../../tools/verify_client.py), [packet reviewer](../../tools/review_packet_study.py), [control reviewer](../../tools/review_packet_controls.py), [inference reviewer](../../tools/review_packet_inference.py) | Check delivery inventory and independently recompute retained packet evidence |
| [Packet demo renderer](../../tools/render_packet_demo.py) | Verify evidence and build the self-contained recorded viewer and its receipt |
| [Packet evidence directory](evidence/packet-study), [original CSV profile](evidence/uploaded-csv-profile.json) | Complete records, logs, selected checkpoint identities, predictions, controls and known failures |
| [Tests](../../tests) | Regression cases; the client exports its relevant dependency-complete subset, including the native packet suite |
| Client `.github/workflows/ci.yml`, `CLIENT_MANIFEST.json`, `.gitignore`, `.gitattributes` | Automated checks, delivered-file provenance, excluded local outputs and exact-byte checkout behavior |

To explain **any particular client file**, find its path in `CLIENT_MANIFEST.json`, read `source_path`, and search that source path in the [every-file walkthrough](../repository-walkthrough.md). Client `SETUP.md`, for example, comes from `client/SETUP.md.in`; `packet_model.py` keeps its original source path/bytes. The manifest's `source_commit` lets you inspect the exact delivered source if current prose has advanced.

In the full reproduction repo, [client templates](../../client), the [explicit selection](../../configs/client-manifest.json), export/publish programs and [publication workflow](../../.github/workflows/client-sync.yml) manage delivery. Customer/research folders explain the work and retain historical media/evidence. Local `assets/`, `upstream/`, virtual environments and `runs/` hold acquired/generated files and are not automatically published. The walkthrough explains each source file, recurring artifact and release download individually.

<a id="upstream"></a>
## 9. What changed compared with the authors' repo and paper?

The authors supplied NetMamba+'s architecture, loader, native training code and released research assets. We fetch source commit `eec9483e2f0fb84ca22982b9de8149bc3a8b1ad2` and verify its 103 tracked files plus seven additional core hashes. We do not claim to have invented NetMamba+.

Our packet addition changes the observation to one packet, retains 1,500 stored bytes, maps 378 learned positions, supplies empty size/time sequences and uses a new binary head. It reuses the native encoder implementation. We added CSV validation/grouping, frozen controlled experiments, strict unlabeled inference/receipts, GB10 compatibility builds, evidence reviewers, tests, the recorded packet demo and the maintained client delivery. [Detailed upstream comparison](upstream-comparison.md).

The paper also discusses full masked pretraining and other flow/class-balancing experiments. Those are research context, not additional supported routes in this handoff. The inherited checkpoint's full history remains unknown. The single-route migration preserves the existing packet protocol, model code and scientific evidence; changing setup or documentation is not new accuracy evidence.

<a id="updates"></a>
## 10. How do both repos stay updated?

Make implementation changes in **netmambaplus-reproduction**. Edit concise client documents in its `client/*.md.in` templates. After a source `main` push passes CI, the publication workflow checks that exact revision, exports the selected files, tests the client package and publishes an ordinary client commit. Client CI then verifies it.

This source-to-client mechanism has executed successfully. [Maintenance and actual update records](../research/client-edition.md). Independent edits to managed client files stop synchronization for review. New runtime files need explicit selection. Changes only to excluded teaching material can leave the client unchanged, so its source marker may precede the reproduction repo's newest commit.

Record commit IDs and use the manifest to establish what was delivered. If an update fails, inspect source CI or **Publish client edition** and follow the maintenance record; do not erase failures or bypass drift checks. Model/data changes require new measured evidence; a packaging change does not.

<a id="hardware"></a>
## 11. What could an IDS, NPU or SmartNIC deployment look like?

A live IDS needs capture, verified byte extraction, bounded queues, continuous model inference, a validated alert policy and monitoring. The packet CSVs do not establish enough extraction/padding provenance to claim a verified capture-to-model pipeline today. Start by comparing an extractor with a reviewed reference capture and expected byte tensors.

A **SmartNIC/DPU** could be investigated for traffic steering and packet processing; host/DPU software could manage extraction and queues. A GPU, or a future compatible **NPU** (neural processor), could run the classifier. Device names or advertised TOPS do not guarantee support for Mamba's custom operations.

The adaptation still uses custom CUDA convolution/scan and fused normalization. The earlier flow model's strict graph-export probe failed at a custom convolution; no successful packet graph export, NPU compilation or SmartNIC model execution is established. Choose an exact target, implement supported operators, compare logits and per-class behavior with the frozen GPU model, then measure complete-system latency, drops, memory and power. The [hardware roadmap](hardware-roadmap.md) explains these prospective components and the earlier measured blocker. No live capture or blocking is included in the current demo.

<a id="remaining-work"></a>
## 12. What is missing or uncertain?

| Gap | Why it matters |
|---|---|
| Exact paper reproduction | Packet adaptation and packet balanced accuracy are a different task from the paper's original flow benchmark |
| Independent data/provenance | Payload hashing prevents exact cross-partition duplicates; capture independence, near duplicates and prior pretrained exposure remain unknown |
| General performance | One model seed, capped subsets, weak transfer, stronger metadata control and sparse attack-subtype support limit claims |
| Numerical repeatability | Classes agreed in retained comparisons, but the separately recorded strict score failures remain |
| Confidence and unknown threats | Packet confidence is uncalibrated; customer evaluation, unknown-attack handling and operational thresholds are absent |
| Live IDS and deployment | Capture/extraction semantics, streaming, alert/blocking service and complete-system measurements are unfinished |
| Other neural backends | Native CPU/Windows/macOS, other physical GPUs, NPU and SmartNIC execution are unimplemented or unvalidated |
| Inherited assets | External datasets/weights have unresolved redistribution/commercial terms in the project record; see client [NOTICE.md](https://github.com/buffbeefalo/netmambaplus-client/blob/main/NOTICE.md) |
| Historical teaching media | The preserved v4 course predates packet training/client packaging; it is not this workflow's tutorial, and human full-watch/all-caption acceptance remains pending |

Council discussions are research records, not execution evidence. The original client architecture review was ESCALATED / UNRATIFIED. The single-route review's Claude call failed with provider HTTP 529 and the run was ABORTED; it did not produce consensus. Direct implementation and tests do not change those outcomes.

<a id="handoff"></a>
## 13. What should I say and send?

A short explanation you can reuse:

> We built a packet classifier using the NetMamba+ encoder. The supplied CICIDS2017 and UNSW CSVs provide stored packet bytes and benign/attack targets. Our joint model trains on groups from both sources and predicts unlabeled packets. Real GB10 training, saved-model inference and evidence checks are recorded. It scored 97.56% and 94.29% group-balanced accuracy on the selected source test sets, with important control results and limitations. The client repo contains the runnable delivery; the reproduction repo explains it. Live IDS or accelerator deployment would be further work.

Before sending:

1. Share the [client repo](https://github.com/buffbeefalo/netmambaplus-client) and this page. Record its commit, source manifest and checked CI revision.
2. Explain the inputs, training/inference distinction, actual packet scores and test limitations. Show both sources and label disagreements in the demo.
3. Provide [SETUP.md](https://github.com/buffbeefalo/netmambaplus-client/blob/main/SETUP.md) and the [every-file walkthrough](../repository-walkthrough.md). Establish which external CSVs, weights and hardware the recipient has before expecting fresh execution.
4. For slides, use the [packet PDF, PowerPoint and matching script](README.md). Earlier flow/calibration video and documents are historical background, not the current CSV setup guide.
5. Keep the remaining-work table with the result. Select an independent customer dataset and a concrete next integration/hardware test before making deployment claims.

The [acceptance map](acceptance.md) connects these explanations to the seven original customer questions and their retained evidence.
