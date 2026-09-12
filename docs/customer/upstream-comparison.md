# The paper, the datasets and what we changed

The paper proposes a way to classify network traffic using a sequence model. The authors’ repository implements that research. **This repository adds a checked execution route, measured results and an explanation around the original model.** It is a reproduction attempt on a different runtime, with disclosed differences from the paper.

## What problem is the paper studying?

Computers communicate by sending packets. An intrusion detection system (IDS) examines traffic and raises alerts when activity may be suspicious. Machine learning offers one approach: learn patterns from examples, then classify later examples.

[Paper v1, arXiv 2601.21792](https://arxiv.org/abs/2601.21792v1) studies **NetMamba** and its multimodal extension **NetMamba+**. Mamba is a sequence model: it scans input units, updating a numerical state that carries information forward. Its updates depend on the input. It is not a chatbot and does not require an online language-model service for inference.

| Name | What it means here |
|---|---|
| NetMamba | The byte-content traffic model. The paper’s separate online prototype measurements concern this byte-only model. |
| NetMamba+ | The extension combining bytes, packet sizes and arrival intervals. This is the classifier we trained and tested. |
| Multimodal | Several views of the same traffic: content, size and timing. It does not mean image/audio chat in this project. |
| Pretraining | Hide part of the input and learn to reconstruct it. This trains a useful representation without attack-category targets. |
| Fine-tuning | Use labeled examples to learn the six downstream categories. |
| Inference | Use a saved classifier to output category scores without updating its learned weights. |

For the full classifier, 400 byte tokens, 20 size tokens, 20 timing tokens and three summary tokens form a sequence of 443. Four Mamba blocks process it. Three modality summary vectors are summed, and a classification layer produces six logits. The [briefing](briefing.md) and [lesson](../lesson.md) explain the exact input transformations.

The paper reports NetMamba+ CICIoT2022 accuracy/F1 of **97.50%** in Table IV. We measured **86.65% mean accuracy** across three runs under the documented source-based GB10 profile. The paper’s separate 261.87 Mb/s and 3.15-second online figures concern byte-only NetMamba on other hardware. Neither number is our measured NetMamba+ system performance.

## What were the two uploaded “databases”?

They are CSV tables of labeled packet examples. A CSV is a text format with columns and rows, not a running database server. Our full scans parsed the files and counted labels and metadata. They did not numerically validate every payload value or train a packet classifier.

| File / data source | Observed contents | Role in this project |
|---|---|---|
| `Payload_data_CICIDS2017.csv` | 1,410,255 packet rows; 15 distinct labels; 1,505 columns | Investigated to establish whether it can supply native flow inputs |
| `Payload_data_UNSW.csv` | 79,881 packet rows; 10 distinct labels; the same 1,505-column schema | Same compatibility investigation |
| Authors’ CICIoT2022 flow JSON release | 8,323 train + 1,040 validation + 1,041 test examples; six classes | Actual training and evaluation inputs |

**CICIDS2017 and CICIoT2022 are different datasets.** Similar names do not make their labels, examples or preprocessing interchangeable. The filenames alone do not establish the complete upstream provenance of the uploaded CSV exports; the supplied files’ own hashes and contents are what was inspected.

| Uploaded CSV field | Plain meaning | Important limitation |
|---|---|---|
| `payload_byte_1` … `payload_byte_1500` | Numeric slots representing packet payload content | Payload slots are not the native model’s ordered header-plus-payload flow representation |
| `ttl` | An IP time-to-live/hop-limit related field | It does not identify a conversation or packet order |
| `total_len` | A recorded packet length | One packet’s length is not an established per-flow size sequence |
| `protocol` | A recorded protocol identifier | A protocol by itself does not establish which connection a packet belongs to |
| `t_delta` | A recorded time difference | Its per-flow interpretation and units are not established; a negative minimum occurs in the CICIDS2017 export |
| `label` | The supplied example’s category | It is a target/annotation, not a legitimate input feature for prediction |

The exports lack source/destination addresses and ports, a flow identifier, and established packet order within a connection. Reading five adjacent rows cannot recover those missing facts. A classifier trained directly on these packet tables would be an **adaptation**, not the native NetMamba+ flow experiment.

To make compatible flow inputs from captured packets, a separate adapter must establish grouping, direction, order, byte extraction, timing units and padding. That adapter remains unverified here. The current `predict.py` accepts already assembled native flows.

The training release’s six labels are **Flood**, **RTSP Brute Force**, **Power–Audio**, **Power–Other**, **Power–Cameras** and **Power–Home Automation**. The last four are IoT device/power activity categories; this is not a general benign/malicious/unknown-attack label system. Published evidence includes the [uploaded CSV profile](evidence/uploaded-csv-profile.json) and [native flow validation](evidence/native-data-validation.json).

## What is different from the authors’ GitHub repository?

The upstream reference is [wangtz19/NetMambaPlus at commit eec9483e2f0fb84ca22982b9de8149bc3a8b1ad2](https://github.com/wangtz19/NetMambaPlus/tree/eec9483e2f0fb84ca22982b9de8149bc3a8b1ad2). Our repo downloads that commit into an ignored `upstream/NetMambaPlus` directory instead of publishing an altered copy as the authors’ source.

| Area | Authors’ source / paper | This repository and its measured behavior |
|---|---|---|
| Model and tensor loader | Native NetMamba+ implementation | Unchanged original checkout: all 103 tracked files and seven core SHA-256 pins verified |
| GPU runtime | Older Mamba/causal-convolution stack; paper uses A100 and Torch 2.1.1 | GB10, Torch 2.9.1/cu130; native extensions built from pinned sources with recorded compiler compatibility edits in disposable copies |
| Compatibility edits | Original architecture targets and older CUB calls | Build copies target `sm_121`; removed CUB lane/synchronization calls are replaced with supported equivalents; CUDA 13 assembler path is explicit |
| Fine-tuning | Released source preset differs from the paper’s batch/rate paragraph | Preserved source preset: 120 epochs, batch 128, effective maximum LR 0.001; paper reports batch 64 and LR 0.002 |
| Main initialization | Released pretraining weights; paper describes Browser/Kitsune | Same released weights initialize the three main runs; complete original corpus/history remains unknown |
| Short pretraining check | Native masked-reconstruction code | Separately exercised on CICIoT2022 training-only data: 132 updates, not full paper pretraining |
| Evaluation entry point | Native final test works; inspected standalone `--eval` path has a loader-reference problem | Separate `evaluate.py` strictly reloads the classifier and calls the original test loader/evaluation engine |
| Prediction without labels | Dataset loaders expect label/name metadata | `predict.py` supplies temporary loader metadata, discards targets before model forward, and reports predictions with no accuracy |
| Reproducibility | Research scripts and released assets | Source/data/checkpoint validation, manifests, new-output-directory protection, class-mapping provenance, CPU regression tests and CI |
| Evidence and presentation | Paper’s reported results | All measured seeds, raw training logs, predictions, timing samples, a replay, PDFs, editable slides and explanations |

The build edits address compiler/runtime compatibility. Seven optimized-versus-reference forward/backward checks in each of two built environments support the tested numerical behavior. They do not prove equivalence on every input, precision or device. Known package and GPU-capability warnings are retained in the [research record](../research/research-record.md).

We did not rewrite the architecture, infer fictional flows from the uploaded CSVs, remove difficult test examples or select the demo seed after seeing final scores. Seed 0 was fixed for the demo in advance, and all three scores remain published. Optional source LDA/class-balancing paths were not separately validated.

## Which local files do what?

| Local path | Responsibility |
|---|---|
| [repro.py](../../repro.py) | Verify original source/data/settings and launch native training with a run manifest |
| [evaluate.py](../../evaluate.py) | Reload a saved classifier strictly and measure the native test split |
| [predict.py](../../predict.py) | Classify native flow inputs without known labels |
| [replay.py](../../replay.py) | Record logits, independently recompute metrics and generate the browser replay |
| [build_gb10.py](../../tools/build_gb10.py) | Create and verify disposable native-extension build copies |
| [check_gpu_runtime.py](../../tools/check_gpu_runtime.py) | Compare native GPU calculations and gradients with reference paths |
| [review_experiments.py](../../tools/review_experiments.py) | Check epoch history, selected checkpoint, actual optimizer state and tensor-identical model exports |
| [benchmark.py](../../tools/benchmark.py) / [probe_export.py](../../tools/probe_export.py) | Measure model-only latency / exercise one strict Torch graph-export route |
| [verify_package.py](../../tools/verify_package.py) | Check retained evidence, metrics, hashes and presentation alignment without a GPU |
| [build_customer_package.py](../../tools/build_customer_package.py) / [build_learning_guide.py](../../tools/build_learning_guide.py) | Generate reviewed teaching material from shared slide content and measurements |

The raw data, original source and inherited weights remain external assets. The public package contains commands and evidence, not a grant of redistribution or commercial rights. See the [runbook](runbook.md) to repeat the work and the [acceptance review](acceptance.md) for what the checks establish.
