# The paper and the two packet CSVs, explained

This guide explains what the three supplied files contain, how NetMamba+ turns traffic into model inputs, and which experiment this repository actually ran. You do not need a machine-learning background. **The PDF describes the authors’ research; the two CSVs are packet exports; the measured classifier used a separate release of CICIoT2022 flows.**

The paper is Tongze Wang and colleagues’ [*NetMamba+: A Framework of Pre-trained Models for Efficient and Accurate Network Traffic Classification*, arXiv 2601.21792v1](https://arxiv.org/abs/2601.21792v1), dated 29 January 2026. Its 16 PDF pages are linked below. The code reference throughout this guide is [the authors’ repository at commit `eec9483e2f0fb84ca22982b9de8149bc3a8b1ad2`](https://github.com/wangtz19/NetMambaPlus/tree/eec9483e2f0fb84ca22982b9de8149bc3a8b1ad2). A commit identifies a particular source version, so later upstream edits do not silently change this reference.

## 1. What arrived in the three files

| Supplied file | What it contains | Its role here |
|---|---|---|
| `2601.21792v1.pdf` | The research paper: methods, experiments, comparisons and limitations | Explains the proposed approach and the authors’ reported results |
| `Payload_data_CICIDS2017.csv` | 1,410,255 packet rows, 1,505 columns, 15 labels | Inspected for compatibility with the original model’s input contract |
| `Payload_data_UNSW.csv` | 79,881 packet rows, 1,505 columns, 10 labels | The same compatibility investigation |

A CSV is a text table: the first record names the columns and later records contain values. It is not a running database server, a trained model or a packet-capture program. These files do not need to be imported into a database to understand their schema.

The published [full CSV metadata profile](evidence/uploaded-csv-profile.json) names the two exports `CICIDS2017.csv` and `UNSW.csv`. Their hashes identify the supplied files despite those shortened names. It records full-file row counts, label counts and metadata aggregates. It does **not** establish exhaustive numerical validity of all payload cells, and neither export was used to train the reported classifier. A familiar dataset name in a filename does not establish the export’s complete production history.

## 2. Read a CSV row without confusing its fields

Both files have exactly the same header order. Columns 1 through 1,500 are named `payload_byte_1`, `payload_byte_2`, and so on through `payload_byte_1500`, with every integer suffix present in increasing order. The final five headers are exactly `ttl`, `total_len`, `protocol`, `t_delta`, `label`.

| Column position | Exact header or complete naming rule | Meaning and limit |
|---|---|---|
| 1–1,500 | `payload_byte_1` through `payload_byte_1500` | Ordered slots in the exported packet payload representation. They are 1,500 positions in one example, not 1,500 separate examples. These columns do not establish a complete header-plus-payload capture. |
| 1,501 | `ttl` | The recorded time-to-live field, associated with packet lifetime across a network. It does not identify a connection or establish packet order. |
| 1,502 | `total_len` | A recorded packet length. It is not automatically the number of meaningful stored payload slots or the length of a reconstructed flow. |
| 1,503 | `protocol` | A recorded protocol category, such as `tcp` or `udp`. A protocol says how traffic is carried; an attack label describes a different property. |
| 1,504 | `t_delta` | A recorded time difference. This export alone does not establish its units, reference event or interpretation within a flow. |
| 1,505 | `label` | The supplied category for the example. This is the answer a supervised classifier would learn to predict; it must not be given to the model as an input feature. |

There are therefore 1,504 fields before the target label: 1,500 byte positions and four metadata fields. Calling all 1,505 columns “integer byte features” would be wrong: protocol and label values are text, and time differences can be fractional. The native NetMamba+ loader also does not accept these 1,504 fields as a ready-made input vector.

These ranges come from the complete metadata scan, aggregated across its per-label records:

| Observed metadata | CICIDS2017 export | UNSW export |
|---|---:|---:|
| Distinct stored protocol categories | 2 | 41 |
| `ttl` minimum → maximum | 1 → 255 | 0 → 255 |
| `total_len` minimum → maximum | 41 → 23,400 | 24 → 1,508 |
| `t_delta` minimum → maximum | −0.000018 → 58.352796 | 0 → 0.030455 |

These are descriptions of these exports, not universal limits of network traffic. The negative CICIDS2017 time minimum is also a concrete incompatibility with this repository’s requirement for finite, nonnegative native intervals. Taking an absolute value would change the data without establishing what the original field meant. The profile does not provide the missing timing provenance. [Evidence: CSV metadata profile](evidence/uploaded-csv-profile.json); [native input validation](../../repro.py).

### Every CICIDS2017 label and count

The spellings, capitalization and en dashes below are the stored labels. Counts sum to **1,410,255**. They are counts of exported packet rows, not native flows or correctly classified examples. [Full profile](evidence/uploaded-csv-profile.json).

| Stored label | Rows |
|---|---:|
| `BENIGN` | 362,108 |
| `DoS Hulk` | 250,000 |
| `DDoS` | 241,405 |
| `DoS GoldenEye` | 128,122 |
| `DoS slowloris` | 121,097 |
| `Infiltration` | 115,007 |
| `DoS Slowhttptest` | 80,542 |
| `SSH-Patator` | 48,165 |
| `FTP-Patator` | 31,843 |
| `Heartbleed` | 13,486 |
| `Web Attack – Brute Force` | 11,754 |
| `Web Attack – XSS` | 3,341 |
| `Bot` | 2,543 |
| `PortScan` | 830 |
| `Web Attack – Sql Injection` | 12 |

### Every UNSW label and count

Counts sum to **79,881**. Lowercase `normal` belongs to this export’s label vocabulary; it is not literally the same stored label as uppercase `BENIGN`. Likewise, labels from the two tables do not become interchangeable merely because their names sound related. [Full profile](evidence/uploaded-csv-profile.json).

| Stored label | Rows |
|---|---:|
| `normal` | 21,000 |
| `generic` | 17,580 |
| `exploits` | 13,992 |
| `fuzzers` | 12,722 |
| `reconnaissance` | 7,562 |
| `dos` | 3,397 |
| `backdoor` | 1,239 |
| `analysis` | 1,208 |
| `shellcode` | 1,088 |
| `worms` | 93 |

The tables illustrate **class imbalance**: some categories have many more examples than others. For example, the first export has 362,108 `BENIGN` rows and only 12 `Web Attack – Sql Injection` rows. A single overall score can conceal poor performance on a small category. Counts alone do not tell us how any classifier performs, and the paper’s class-balancing experiments were not run on these exports.

## 3. Why packets cannot simply be renamed flows

A **packet** is one unit sent across a network. A **flow** groups related packets according to an explicit rule. For a TCP connection, a common starting point is the source address, destination address, source port, destination port and protocol. An extraction procedure must also decide how to treat reverse-direction packets, timeouts and ordering.

For a deliberately fictional example, imagine TCP packets from “Host A, port 51000” to “Host B, port 443.” A reply travels in the opposite direction. Whether the reply joins the same record depends on the chosen flow definition. Another packet from Host A using port 51001 is not automatically part of the first connection. These are illustrative names and numbers, not observations from either supplied CSV.

Both exports lack source and destination addresses, source and destination ports, a flow identifier, and established packet order within a flow. Those omissions are recorded in the [metadata profile](evidence/uploaded-csv-profile.json). Five adjacent rows might concern unrelated conversations. Equal labels, protocols or lengths do not recover the missing connection identity. A scalar `t_delta` cannot resolve that ambiguity.

The paper’s byte representation also reserves **80 header bytes and 240 payload bytes per packet**. A table of payload slots does not automatically supply the missing headers. A compatible adapter would need evidence for grouping, direction, order, byte extraction, interval units and padding. No such CSV-to-native-flow adapter was established here. See [paper page 5](https://arxiv.org/pdf/2601.21792v1#page=5) and the pinned [packet-feature preparation code](https://github.com/wangtz19/NetMambaPlus/blob/eec9483e2f0fb84ca22982b9de8149bc3a8b1ad2/dataset_scripts/dataset_mm_uni_common.py).

Training a classifier directly on these packet tables is a possible separate research task. It would change the unit of prediction and preprocessing, so its results would describe a packet-level adaptation. They would not be the native flow experiment documented below.

## 4. A route through all major parts of the PDF

The page links use physical PDF page numbers. Start with Figure 1 on page 4 for the overall process, then read the representation on page 5 before tackling the equations. The table covers all major sections, including experiments this repository did not reproduce.

| Paper section | Page anchors | What to learn from it |
|---|---|---|
| Abstract and I. Introduction | [1–2](https://arxiv.org/pdf/2601.21792v1#page=1) | The authors want traffic classification that combines accuracy with efficient processing. The opening claims describe their research contribution. |
| II. Related Work, A–D; Table I | [2–3](https://arxiv.org/pdf/2601.21792v1#page=2) | Earlier Transformers, Mamba work, traffic representations and long-tailed classification. “Long-tailed” means many examples in common categories and relatively few in others. Table I compares representation choices. |
| III. Preliminaries; equations 1–2 | [3–4](https://arxiv.org/pdf/2601.21792v1#page=3) | State-space models carry a numerical state through a sequence. Mamba’s input-dependent selection changes how information is retained and used. The continuous/discrete equations explain that mechanism. |
| IV. Framework Overview; Figure 1 | [4–5](https://arxiv.org/pdf/2601.21792v1#page=4) | Prepare traffic representations, pretrain by reconstructing hidden content, then fine-tune for labels. Dashed boxes identify pluggable components. |
| V. Traffic Representation | [5](https://arxiv.org/pdf/2601.21792v1#page=5) | Five steps: split flows, parse packets, crop/pad/concatenate bytes, form byte strides, and construct size/time sequences. These steps define what an example means. |
| VI. Model Details, A–D; Algorithm 1 and equations 3–13 | [6–8](https://arxiv.org/pdf/2601.21792v1#page=6) | Turn inputs into vectors, process them with the encoder, reconstruct missing values during pretraining, and learn categories during fine-tuning. The optional distribution-aware loss changes the treatment of imbalanced classes. |
| VII. Online System Implementation; Figure 2 | [8](https://arxiv.org/pdf/2601.21792v1#page=8) | Capture and flow extraction feed a GPU classifier through shared memory; Redis and Flask make results available. These surrounding services are part of the authors’ prototype. |
| VIII-A. Experimental Setup; Tables II–III | [8–10](https://arxiv.org/pdf/2601.21792v1#page=8) | Datasets, baselines, metrics, hardware and hyperparameters define the conditions under which the reported results apply. |
| VIII-B–C. Overall Performance and Efficiency; Tables IV–V, Figures 3–5 | [10–12](https://arxiv.org/pdf/2601.21792v1#page=10) | Compare accuracy and resource/speed results. Check each model’s input unit, batch size and hardware before comparing numbers. |
| VIII-D–F. Representation, multimodal and LDA ablations; Tables VI–VIII, Figures 6–7 | [12–13](https://arxiv.org/pdf/2601.21792v1#page=12) | An ablation removes or changes a component to investigate its contribution. These tests concern byte choices, the three input modalities and the optional long-tail method. |
| VIII-G–H. Few-shot and out-of-distribution tests; Figure 8 and Table IX | [13–14](https://arxiv.org/pdf/2601.21792v1#page=13) | Study limited labeled training data and examples unlike the training distribution. The novelty-detection evaluation uses different outputs and metrics from ordinary category accuracy. |
| VIII-I–J. Real-World Deployment and Discussion; Figure 9 | [14](https://arxiv.org/pdf/2601.21792v1#page=14) | Report the online prototype and discuss limitations, including degradation when a chronological split changes the traffic distribution. |
| IX. Conclusion, references and biographies | [15–16](https://arxiv.org/pdf/2601.21792v1#page=15) | Review the claimed contributions and future directions, then follow the cited research. These pages do not add another executed experiment in this repository. |

### The three central ideas

**Efficient sequence processing.** A model sees a sequence of numerical input units and produces a representation of the traffic. NetMamba uses Mamba blocks; NetTrans is a separate FlashAttention-based alternative. NetMamba+ does not mean an attention layer was added to Mamba. The paper distinguishes byte-only NetMamba from the multimodal NetMamba+ implementation. [Pages 6–9](https://arxiv.org/pdf/2601.21792v1#page=6).

**Several views of the same traffic.** Content bytes, packet sizes and arrival intervals can carry different information. Here “multimodal” means those three traffic views. It does not mean image/audio chat. A model can use size and timing patterns even when it cannot interpret content as readable text. [Representation and embeddings, pages 5–6](https://arxiv.org/pdf/2601.21792v1#page=5).

**Optional long-tail treatment.** The paper’s label-distribution-aware, or LDA, approach adjusts weighting and class-dependent margins during supervised learning. A loss is the number that measures the model’s training error; changing its weighting can change how much rare categories influence updates. This optional mechanism does not create missing labels or repair an incompatible input schema. The paper disables it unless stated otherwise; the recorded native runs have `class_balance=false` and `ldam=false`. [Paper pages 7–9](https://arxiv.org/pdf/2601.21792v1#page=7); [seed-0 resolved arguments](evidence/seed0/training/manifest.json).

### Read the experiments as separate questions

Table II names **Browser and Kitsune for pretraining** and ten downstream datasets: CipherSpectrum, CSTNET-TLS1.3, CrossNet2021A, CP-Android, CP-iOS, CICIoT2022, USTC-TFC2016, ISCXVPN2016, DataCon2021-p1 and Huawei-VPN. They span application, attack, malware and VPN classification. Neither supplied packet CSV is a Table II dataset. This repository’s three main training runs cover the six-class CICIoT2022 release, not that entire research program. [Table II, page 9](https://arxiv.org/pdf/2601.21792v1#page=9).

For the main CICIoT2022 comparison, **Table IV reports NetMamba+ accuracy and weighted F1 of 97.50%**. Byte-only NetMamba’s row is 97.79%; those are different models. NetMamba+ is not the best entry in every column. The discussion also qualifies comparisons with TFE-GNN because it excludes flows without payloads. Read the main table and its surrounding text together. [Pages 10–11](https://arxiv.org/pdf/2601.21792v1#page=10).

The efficiency comparisons depend on the test conditions. The paper’s 1.7-times comparison with YaTC is at batch size 64; Figure 4 uses a base-two logarithmic batch-size axis. Its throughput definition counts packets for ET-BERT and flows for the other models. A bare “samples per second” comparison hides that difference. [Pages 10–12](https://arxiv.org/pdf/2601.21792v1#page=10).

The few-shot experiment varies the amount of labeled training data; Figure 8’s 10%, 40%, 70% and 100% refer to portions of the training subset, which is itself 80% of all data. The out-of-distribution experiment asks whether unfamiliar traffic can be identified using a separate entropy/threshold procedure. Its AUROC and false-positive rate at 95% true-positive rate describe detection tradeoffs, not six-class accuracy. The current prediction command does not implement that experiment. [Pages 13–14](https://arxiv.org/pdf/2601.21792v1#page=13).

Finally, the paper’s online measurements concern a **byte-only NetMamba prototype** using CPU capture/flow processing and an A30 GPU classifier. The reported means are 261.87 Mb/s throughput and 3.15 seconds of batch latency. Those seconds include the prototype’s batching behavior; they are not one flow’s neural forward-pass time. The repository’s GB10 model timing and browser replay measure different activities. [Prototype, page 8](https://arxiv.org/pdf/2601.21792v1#page=8); [deployment and discussion, page 14](https://arxiv.org/pdf/2601.21792v1#page=14).

## 5. The native dataset actually used

**CICIDS2017 and CICIoT2022 are different datasets.** The selected native release contains 10,404 already assembled flow records, divided into 8,323 training, 1,040 validation and 1,041 test examples. The repository verifies the release files and their six-category mapping. [Native data validation](evidence/native-data-validation.json).

| Class index | Exact native class name | Train | Validation | Test |
|---|---|---:|---:|---:|
| 0 | `6-Attacks-1-Flood` | 1,600 | 200 | 200 |
| 1 | `6-Attacks-2-RTSP Brute Force` | 1,600 | 200 | 200 |
| 2 | `1-Power-Audio` | 1,600 | 200 | 200 |
| 3 | `1-Power-Other` | 323 | 40 | 41 |
| 4 | `1-Power-Cameras` | 1,600 | 200 | 200 |
| 5 | `1-Power-Home Automation` | 1,600 | 200 | 200 |
| **Total** | | **8,323** | **1,040** | **1,041** |

The last four names refer to IoT device/power activity categories. This classifier has six categories, not six attack types, and no separate “unknown attack” output. A saved model must travel with its class mapping: output position 3 means `1-Power-Other` here, regardless of which category happens to be fourth in another file.

Training examples update the learned weights. Validation examples help select a checkpoint while training proceeds. Test examples provide the final held-out measurement. The split is preserved as released. The published validation also finds five exact stored inputs shared between training/validation and six shared between training/test. Recorded identifiers and raw-input comparisons cannot prove independence of the underlying captures, and they do not establish all possible collisions after preprocessing. [Split and overlap evidence](evidence/native-data-validation.json).

### One illustrative native input

The following is a **synthetic schema example** for prediction, deliberately containing only two short packet representations. It is not a real capture, training example or accuracy result:

```json
[
  {
    "data": ["0 127 255 64", "10 20"],
    "sizes": "64 96",
    "intervals": "0 0.002"
  }
]
```

`data` is a list of packet byte strings, while `sizes` and `intervals` are space-separated numeric strings. Training records also carry the native `label` and `name`, with a matching `metadata.json`. Prediction does not need a known answer: [predict.py](../../predict.py) supplies temporary metadata required by the original loader, then discards targets before the model forward pass. A prediction without labels has no measured accuracy.

The sample demonstrates the container and padding rules only. It does not demonstrate that the numbers came from a correctly grouped or parsed connection. In particular, the loader receives already prepared packet strings; it does not reconstruct the paper’s 80-byte header and 240-byte payload allocation from this abbreviated example.

## 6. Follow one flow into the configured classifier

The [configuration](../../configs/ciciot2022.json) selects the original `fuse3_mamba_classifier` and `byte_size_interval` dataset. The authors own the [model factory](https://github.com/wangtz19/NetMambaPlus/blob/eec9483e2f0fb84ca22982b9de8149bc3a8b1ad2/src/util/loader_model.py) and [tensor loader](https://github.com/wangtz19/NetMambaPlus/blob/eec9483e2f0fb84ca22982b9de8149bc3a8b1ad2/src/util/loader_data.py); this repository’s wrapper validates inputs, resolves the native arguments and records execution.

1. **Create a fixed byte array.** Keep at most the first five packet strings. Truncate or zero-pad each to 320 byte values, then pad missing packets. This makes 5 × 320 = 1,600 values. The loader represents them as a one-row grayscale array for its tensor transform: a batch has shape `[B, 1, 1, 1600]`, where B is the number of flows. The model flattens the row for one-dimensional strides. This storage shape does not turn traffic into a photograph.
2. **Normalize bytes.** The native transform divides by 255, subtracts 0.5 and divides by 0.5: `2 × byte / 255 − 1`. Byte 0 becomes −1 and byte 255 becomes 1. The model therefore receives transformed numbers, not printable text or the original CSV row.
3. **Prepare sizes and intervals.** Select at most 20 of each. The chosen `sizes` path clamps sizes into 0–1,500; its initial padding value 1,501 is also clamped to 1,500. Intervals use `(1 + x) / (2 + x)` for finite inputs; zero becomes 0.5, and the loader’s infinite padding maps to 1. The interval formula is discussed more precisely in the optional notes below.
4. **Make tokens.** A token here is one numerical vector the sequence model processes. Four adjacent normalized bytes form one stride, which a learned projection maps to 256 numbers. Thus 1,600 / 4 = 400 byte tokens. Sizes and intervals each contribute 20 vectors using the original value embedding. These tokens are not language-model words.
5. **Process and classify.** Three learned summary tokens bring the total to 400 + 20 + 20 + 3 = **443 tokens**. The source concatenates size, interval and byte sequences, then runs four Mamba blocks of width 256. It sums the three summary-position vectors and applies a single bias-free linear classification layer to produce six raw scores, called **logits**.

The selected classifier has **1,870,080 learned parameters**—the numerical values training can adjust. Its active Mamba setting is `bimamba_type="none"`, the original unidirectional branch. The full-model runtime receipt checks the complete 443-token, four-block classifier; it does not use a reduced substitute. [Loader transformations](https://github.com/wangtz19/NetMambaPlus/blob/eec9483e2f0fb84ca22982b9de8149bc3a8b1ad2/src/util/loader_data.py#L165-L249); [model assembly and head](https://github.com/wangtz19/NetMambaPlus/blob/eec9483e2f0fb84ca22982b9de8149bc3a8b1ad2/src/models/models_net_mamba_fuse3.py#L127-L288); [parameter transfer evidence](evidence/checkpoint-transfer.json); [complete-model execution receipt](../portability-evidence.json).

## 7. Pretraining, fine-tuning and saved evidence

**Pretraining** hides some input content and learns to reconstruct it. The source preset masks byte strides and size/interval entries, and reconstruction decoders provide the learning signal. The target is the hidden input content; attack-category labels are not the reconstruction target. The paper describes large-scale pretraining on Browser and Kitsune. [Model design, pages 6–8](https://arxiv.org/pdf/2601.21792v1#page=6).

**Fine-tuning** starts from transferred weights and learns the six labeled categories. The released `fuse3_mamba.pth` is the initialization for the three main runs. The transfer check finds compatible encoder shapes, extra reconstruction-decoder keys and a missing classifier `head.weight`, as expected when moving from reconstruction to classification. The new head is learned during fine-tuning. This initial transfer permits those intentional differences; a later strict reload of a saved classifier requires its expected state to match. [Transfer evidence](evidence/checkpoint-transfer.json); [original fine-tuning program](https://github.com/wangtz19/NetMambaPlus/blob/eec9483e2f0fb84ca22982b9de8149bc3a8b1ad2/src/fine-tune.py).

A **batch** is a group of examples processed together. An **optimizer update** adjusts weights using the training error’s gradients. An **epoch** is a pass through the training loader. A **seed** controls sources of randomness, such as initialization and sampling; it does not guarantee identical results on every machine.

The repository also ran a separate short masked-pretraining check on CICIoT2022 training data. Its configuration requested 100 steps, but the original program completes whole epochs: 66 batches per epoch produced **132 updates across two epochs**. Its saved step-130 checkpoint contains **131 updates**, because step numbering starts at zero. That checkpoint is not the initialization used for the three main fine-tuning results, and this short run does not recreate Browser/Kitsune pretraining. [Functional run manifest](evidence/pretrain-functional/manifest.json), [epoch statistics](evidence/pretrain-functional/train_stats.json), [native log](evidence/pretrain-functional/native.log), [execution explanation](../lesson.md#read-the-new-training-and-demo-evidence).

These artifacts answer different questions:

| Artifact | What it establishes |
|---|---|
| Configuration | Which settings were requested; it does not prove they executed |
| Manifest | Recorded arguments, input identities, source/runtime details and execution status |
| Training logs and optimizer state | Evidence of epochs and updates actually performed |
| Checkpoint | Saved model tensors and, for a training checkpoint, additional run state |
| Model-only export | The classifier tensors in another packaging form, with separate provenance; it is not a newly trained model |
| Saved predictions | Outputs for identified inputs; with true labels, they support recomputing metrics |

A checksum can establish that two files have the same bytes. It cannot establish the full historical corpus or training process behind an inherited checkpoint. The authors’ released weights have a verified identity, while their complete prior training history remains unresolved. [Measured result provenance](evidence/results.json); [research record](../research/research-record.md).

## 8. Paper settings and this repository’s results

Read each row as a comparison of reported or recorded conditions, not as a claim that the experiments are equivalent. The paper’s paragraph is not a complete independently verified executable recipe. [Paper setup, page 9](https://arxiv.org/pdf/2601.21792v1#page=9); [source-based configuration](../../configs/ciciot2022.json); [recorded seed-0 execution](evidence/seed0/training/manifest.json).

| Item | Paper report | This repository |
|---|---|---|
| Main pretraining source | Browser and Kitsune | Released pretrained weights initialize the main runs; complete inherited history is unknown |
| Pretraining budget | 150,000 steps, batch 128 | Selected source preset requests 100,000; that full preset was not executed here. The separate functional check completed 132 updates |
| Fine-tuning batch size | 64 | 128, one process, accumulation 1 |
| Fine-tuning duration | 120 epochs | 120 epochs and 7,920 updates per seed |
| Fine-tuning learning rate | Paragraph reports 0.002 | `blr=0.002`; native scaling produces an effective maximum rate of 0.001 for this preset |
| Checkpoint selection | Best validation accuracy | Best validation accuracy; final test follows selection |
| Main offline runtime | PyTorch 2.1.1; four A100 40 GB GPUs | PyTorch 2.9.1+cu130 on GB10; compiler compatibility changes are recorded separately |
| Scope | Ten downstream datasets and additional analyses | Three seeds on the released six-class CICIoT2022 split, plus documented functional/runtime checks |

The native learning-rate formula is `lr = blr × (batch_size × accumulation × world_size) / 256`. With 128 × 1 × 1 examples per update, `0.002 × 128 / 256 = 0.001`. The schedule changes the rate during training; the value shown here is not a claim that every update used 0.001. [Original rate resolution](https://github.com/wangtz19/NetMambaPlus/blob/eec9483e2f0fb84ca22982b9de8149bc3a8b1ad2/src/fine-tune.py#L144-L160).

| Result | Accuracy | Weighted F1 | Macro F1 |
|---|---:|---:|---:|
| Paper Table IV, NetMamba+ CICIoT2022 | 97.50% | 97.50% | Not reported in that comparison |
| Recorded seed 0 | 91.26% | 91.26% | 91.58% |
| Recorded seed 1 | 84.05% | 84.08% | 84.86% |
| Recorded seed 2 | 84.63% | 84.67% | 85.38% |
| Mean of the three recorded seeds | **86.65%** | **86.67%** | **87.27%** |

The main runs completed, but they **did not reproduce the paper’s 97.50% result**. The settings/runtime differences and unresolved inherited pretraining history prevent a controlled equivalence claim. Seed 0 was selected for the demo before final test scores; all three results remain visible. Re-running strict inference and recomputing metrics verifies the frozen results on the same test set. It does not create an independent holdout. [Complete measured results](results.md); [machine-readable results](evidence/results.json).

### What the scores mean

**Accuracy** is the fraction of test examples with the correct top prediction. For one category, **precision** asks how many predictions of that category were right; **recall** asks how many real examples of that category were found. **F1** combines precision and recall. Weighted F1 weights categories by their true support; macro F1 gives all six categories equal weight. **Support** is the number of true examples of a category—41 for Power–Other in this test split, versus 200 for each other category.

A confusion matrix makes mistakes visible: rows are true categories and columns are predicted categories. For seed 0, 25 of the 200 Power–Cameras examples were predicted as Power–Home Automation. The displayed replay retains these errors. [Per-class results and confusion matrix](results.md#per-class-seed-0-results).

Inference converts logits into normalized class scores and reports the selected class. Those scores are not established probabilities of operational safety. The current six-category model does not establish an unknown-attack detector, a confidence estimate validated on independent customer traffic or a production false-alert rate. Watching the replay faster does not run the neural model faster: the browser is presenting stored predictions.

## 9. Where the repository fits

The original model and tensor loader remain in the verified upstream checkout. [repro.py](../../repro.py) checks source, data and settings before launching the native training program. [evaluate.py](../../evaluate.py) strictly reloads the saved classifier for labeled evaluation. [predict.py](../../predict.py) handles already assembled flows without labels. [replay.py](../../replay.py) records predictions and builds their browser presentation. None of these commands supplies the authors’ live packet-capture prototype.

Presentation, evidence verification and neural execution have different requirements. The recorded demo can be viewed in a browser. Portable Python checks run on the documented Linux, Windows and macOS combinations. Actual model training and inference are measured on NVIDIA GB10; a generalized Linux NVIDIA CUDA build route is provided, but other physical GPU configurations remain unverified. CPU-only and native Windows/macOS model execution are not implemented by this work. The [support matrix](../support-matrix.md) contains the current setup commands and boundaries; the [execution receipt](../portability-evidence.json) contains actual build, numerical and full-classifier checks.

The full-classifier runtime check uses explicitly synthetic native-schema fixtures to verify loss, gradients, an optimizer update, strict reload and inference. It is a functionality test with no dataset-accuracy claim. The separate frozen seed-0 inference comparison reproduces the saved real-data outputs; it does not retrain the classifier. Use the [runbook](runbook.md) for the recorded training/evaluation workflow and the [repository walkthrough](../repository-walkthrough.md) for the wider file inventory.

## 10. Optional technical notes for reading paper and source together

### Table III’s 401 and the classifier’s 443

[Table III on page 10](https://arxiv.org/pdf/2601.21792v1#page=10) prints total sequence length 401 and visible length 41. Four hundred byte strides plus one byte summary token give 401. The configured multimodal classifier also includes 20 sizes, 20 intervals and their two summary tokens, giving **443**. Its source constructs that complete layout and disables masking during classification. Use 443 when explaining this executed classifier, and identify the paper’s 401 as the table’s reported quantity. [Source dimensions](https://github.com/wangtz19/NetMambaPlus/blob/eec9483e2f0fb84ca22982b9de8149bc3a8b1ad2/src/models/models_net_mamba_fuse3.py#L45-L60); [classification path](https://github.com/wangtz19/NetMambaPlus/blob/eec9483e2f0fb84ca22982b9de8149bc3a8b1ad2/src/models/models_net_mamba_fuse3.py#L260-L276).

### The interval formula’s notation discrepancy

On [page 5](https://arxiv.org/pdf/2601.21792v1#page=5), the printed expression names `sigmoid(log(x))` but equates it to `1 / (1 + 1 / (1 + x))`. Those are different expressions. The fraction equals **`sigmoid(log(1 + x))`**, or `(1 + x) / (2 + x)` for finite nonnegative x. The [native loader](https://github.com/wangtz19/NetMambaPlus/blob/eec9483e2f0fb84ca22982b9de8149bc3a8b1ad2/src/util/loader_data.py#L179-L180) implements the fraction and comments it as `sigmoid(log(1 + x))`. Therefore x = 0 becomes 0.5 and x = 1 becomes two-thirds. Padding uses the limiting value 1. This explains the source behavior without silently treating the two printed formulas as equivalent.

### A source-level masking helper check gives 39 retained byte tokens

The original [random-masking helper](https://github.com/wangtz19/NetMambaPlus/blob/eec9483e2f0fb84ca22982b9de8149bc3a8b1ad2/src/models/common.py#L144-L171) computes `int(N * (1 - mask_ratio))`. With N = 400 and ratio = 0.9, Python floating-point arithmetic produces `39.99999999999999` before integer truncation, so the helper keeps **39** byte tokens, not the idealized arithmetic result of 40.

A fresh source-level check called that original helper with a synthetic tensor of shape `[1, 400, 256]` and confirmed a retained shape of `[1, 39, 256]`, with 361 masked byte positions. Following the source’s subsequent assembly gives **82 pretraining encoder tokens**: 39 visible bytes + one byte summary + 21 size positions + 21 interval positions. Size and interval masking replaces values while retaining their sequence positions. This is a helper observation and an inference from the assembly code; it is **not** a measurement of a complete training run’s internal tensor. The 443-token unmasked classifier is unaffected. A CPU helper call also does not establish a CPU backend for the complete CUDA model.

### Masking and classification use different mechanisms

The selected source uses size mask ID 1,502 and interval mask value 0 during reconstruction. These are different from ordinary size padding, which is clamped to 1,500, and ordinary zero intervals, which normalize to 0.5. The paper’s broad description of hiding input content is useful conceptually; the source defines the exact sentinels. Likewise, although the paper describes a classification MLP, the selected additive-fusion classifier uses a single bias-free linear head. [Mask constants](https://github.com/wangtz19/NetMambaPlus/blob/eec9483e2f0fb84ca22982b9de8149bc3a8b1ad2/src/models/common.py#L174-L178); [masking and fusion source](https://github.com/wangtz19/NetMambaPlus/blob/eec9483e2f0fb84ca22982b9de8149bc3a8b1ad2/src/models/models_net_mamba_fuse3.py).

## File identities and evidence access

These SHA-256 fingerprints identify the supplied files discussed here. The public CSV profile contains the export identities and aggregate evidence; it does not redistribute the raw exports. The official versioned paper and pinned upstream links above provide the research sources.

| Supplied file | SHA-256 |
|---|---|
| `2601.21792v1.pdf` | `463af8b34989214e7c64d4d783d67f11fe4e6ef084128254c63335dca3e5df29` |
| `Payload_data_CICIDS2017.csv` | `2ac7ee140ae5a5d0d8df0d550434580c056ed9458977bfcc33706c872d390d6e` |
| `Payload_data_UNSW.csv` | `39616dd8e397673500ed6c51a09fe5638c29d27454467d8aef925ca79a295f01` |

For the main evidence trail, open the [CSV profile](evidence/uploaded-csv-profile.json), [native flow validation](evidence/native-data-validation.json), [configuration](../../configs/ciciot2022.json), [checkpoint-transfer record](evidence/checkpoint-transfer.json), [results](evidence/results.json) and [hardware execution receipt](../portability-evidence.json). Each supports a different part of the explanation; none alone proves the whole scientific experiment.
