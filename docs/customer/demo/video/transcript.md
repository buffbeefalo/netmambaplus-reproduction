# NetMamba+ — 30-minute video transcript

Locally synthesized narration. This video explains recorded experiments; it does not perform new training or live capture.

Runtime: 30:00, including 3:00 of labeled practice pauses and a 90-second teach-back. Captions use measured sentence audio boundaries; within-sentence breaks are proportional estimates.

## 00:00:00 — The paper and the purpose

### 00:00:00 — NetMamba+: A measured reproduction attempt

Welcome. This thirty minute course explains Net Mamba Plus, the experiment that actually ran, and what you can responsibly tell a customer. We will follow the data into training and inference, inspect real results, and work through one actual prediction error. Short practice pauses are included in the running time. At the end, you will have ninety seconds to explain the project aloud. The narration uses a local synthetic voice. The experiment records, not the voice or the AI discussion, are the evidence.

On screen: Understand the system · Explain the actual evidence · Keep the limitations with the result

Evidence: [answers](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/answers.md), [results](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/results.json)

### 00:00:33 — A classifier is one part of an IDS

Start with three words. A packet is one small network message. A flow groups related packets into a conversation. An intrusion detection system, or I D S, observes traffic and raises alerts for investigation. A classifier assigns categories. It does not automatically supply packet capture, connection grouping, an alert policy, or blocking. A G P U accelerates numerical operations; it does not fill in these missing system components.

On screen: Packet: one network message · Flow: related packets in order · IDS: observation, classification and an alert policy

Evidence: [comparison](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/upstream-comparison.md)

### 00:01:04 — What the plus means

The paper combines three views of the same flow: byte content, packet sizes, and time gaps. Combining these views is what multimodal means here. Mamba processes a sequence by updating a numerical state. It is not a chatbot. The earlier Net Mamba model used bytes alone. Our measured work exercises the multimodal Net Mamba Plus classifier on a G B ten graphics processor.

On screen: Bytes describe content · Sizes describe packet length · Intervals describe timing

Evidence: [comparison](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/upstream-comparison.md)

### 00:01:31 — First decision

If the classifier runs successfully, have we demonstrated a complete live intrusion detection system? Take eight seconds.

On screen: Does classifier success establish a complete live IDS?

Evidence: [answers](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/answers.md), [results](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/results.json), [comparison](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/upstream-comparison.md)

### 00:01:39 — Your turn · 8 seconds

**Practice pause: 8 seconds.** Does a working classifier establish a complete live IDS?

On screen: Does a working classifier establish a complete live IDS?

Evidence: [answers](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/answers.md), [results](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/results.json), [comparison](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/upstream-comparison.md)

### 00:01:47 — Keep the system boundary visible

No. Classifier execution is one tested component. The capture to alert system still needs implementation and validation. Keep that boundary visible throughout the presentation.

On screen: Working: native classifier and recorded replay · Still needed: capture, extraction and operational alerting

Evidence: [hardware](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/hardware-roadmap.md)

## 00:02:00 — The paper, the CSVs and compatible flows

### 00:02:00 — The three starting files

The three supplied files have different roles. The P D F is the research paper. It describes methods and reports results; it is not itself a ready to train dataset. The C I C I D S twenty seventeen C S V contains 1,410,255 packet rows and fifteen labels. The U N S W C S V contains 79,881 packet rows and ten labels. A C S V is a text table with rows and columns, not a running database server. We inspected the supplied exports and recorded their file identities.

On screen: Paper v1: research proposal and reported results · CICIDS2017 CSV: 1,410,255 packet rows · UNSW CSV: 79,881 packet rows

Evidence: [csv](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/uploaded-csv-profile.json), [comparison](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/upstream-comparison.md)

### 00:02:41 — What one CSV row contains

Both exports have fifteen hundred payload byte columns, plus five metadata fields. T T L relates to a packet’s remaining hop allowance. Total length describes recorded packet length. Protocol identifies a protocol. Time delta records a time difference. Label supplies the known example category. These fields do not establish which connection each packet belongs to, its direction, or its order within that connection. The C I C I D S scan found negative time differences, and the timing units and per-flow interpretation remain unestablished. We profiled metadata; we did not train a packet classifier or numerically validate every payload value.

On screen: 1,500 payload-byte columns · TTL, total length, protocol, time delta, label · No established flow identity or packet order

Evidence: [csv](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/uploaded-csv-profile.json)

### 00:03:26 — Why five neighboring rows are insufficient

Imagine a spreadsheet whose next five rows come from three different conversations. Stacking those rows changes the example into something that never occurred on the network. Five neighboring rows are therefore not evidence of one five-packet flow. Payload fields also cannot reconstruct missing headers. A packet classifier trained directly on these exports could be useful, but it would be a different experiment. Reproducing the native input representation requires established grouping, direction, ordering, byte extraction and timing.

On screen: Row order is not connection identity · Missing headers cannot be recovered from payload alone · A packet classifier would be a separate adaptation

Evidence: [comparison](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/upstream-comparison.md)

### 00:04:01 — The data actually used

Instead, we acquired the authors’ processed C I C I O T twenty twenty-two flow release. This is a different dataset from C I C I D S twenty seventeen. It contains 8,323 training flows, 1,040 validation flows, and 1,041 test flows. Training examples teach the model’s weights. Validation selects a candidate checkpoint. The test split measures that selected classifier. The six categories include Flood and R T S P Brute Force, plus four categories describing Internet of Things device or power activity.

On screen: CICIoT2022 is a different dataset · 8,323 train · 1,040 validation · 1,041 test · Six native categories

Evidence: [native](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/native-data-validation.json)

### 00:04:41 — Native input is a defined contract

The native files are J S O N arrays of flow records. In this release, data contains packet-byte strings; sizes and intervals are space-separated numeric strings. The loader parses them into numerical tensors. Metadata defines which category each class index means. Labels are known answers for training or evaluation, not legitimate prediction features. The code checks types, ranges and consistency before launch. A validated stored record still does not prove that an upstream packet extractor created it correctly.

On screen: data: a list of packet-byte strings · sizes / intervals: space-separated numeric strings · Metadata and provenance define class meanings

Evidence: [native](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/native-data-validation.json), [contract](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/harness-reference.md)

### 00:05:16 — Input decision

A colleague gives you five adjacent rows from one uploaded C S V and asks you to classify them as a flow. Would you proceed? Use the next twelve seconds to identify the missing facts.

On screen: Can five adjacent packet rows be passed as one native flow?

Evidence: [csv](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/uploaded-csv-profile.json), [comparison](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/upstream-comparison.md), [native](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/native-data-validation.json)

### 00:05:29 — Your turn · 12 seconds

**Practice pause: 12 seconds.** What establishes relatedness, direction, ordering and extraction?

On screen: What establishes relatedness, direction, ordering and extraction?

Evidence: [csv](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/uploaded-csv-profile.json), [comparison](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/upstream-comparison.md), [native](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/native-data-validation.json)

### 00:05:41 — Answer: establish compatibility first

Do not assume those rows form a flow. Use the compatible released records, or establish and validate an extractor. This is the connection between the paper and the two uploaded tables: they address related traffic analysis, but their units of observation are not interchangeable.

On screen: Use the compatible released flows · Or validate a real packet-to-flow adapter

Evidence: [comparison](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/upstream-comparison.md)

## 00:06:00 — Preprocessing, training and inference

### 00:06:00 — Three views become tensors

Now follow one valid flow through the original loader. The byte view keeps up to five packets, with three hundred twenty stored bytes per packet. That gives sixteen hundred values. The paper describes each packet region as eighty header bytes plus two hundred forty payload bytes. Released flows already contain this extraction. Short records are padded; long ones are truncated. The measured byte tensor has batch size by one by one by sixteen hundred as its dimensions. The two other views retain the first twenty sizes and the first twenty time gaps.

On screen: 5 packets × 320 stored bytes = 1,600 values · First 20 packet sizes · First 20 arrival intervals

Evidence: [lesson](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/lesson.md)

### 00:06:38 — Normalization changes the numerical scale

The byte transformation divides by two hundred fifty-five, then uses a mean and standard deviation of one half. A zero byte therefore becomes minus one, and two hundred fifty-five becomes plus one. Sizes are clipped between zero and fifteen hundred. A padding size of fifteen hundred and one is also clipped to fifteen hundred, so that boundary cannot reliably identify padding. For a nonnegative gap x, the loader uses one plus x divided by two plus x. Zero becomes one half; one becomes two thirds. Padded infinite gaps map to one inside the loader.

On screen: Byte 0 → −1; byte 255 → +1 · Sizes clipped to 0–1,500 · Gap x → (1+x)/(2+x)

Evidence: [lesson](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/lesson.md)

### 00:07:19 — The classifier reads 443 tokens

For classification, groups of four bytes create four hundred byte tokens. Add twenty size tokens, twenty interval tokens and three summary tokens, for four hundred forty-three input tokens. A token here is a numerical input unit, not a word in a chatbot. Position and modality information identify its location and type. Four Mamba blocks process the sequence. Three modality summaries are added, then a classification layer produces six raw outputs called logits. The model’s internal state belongs to this input computation. It is not an implemented cache of live network connections.

On screen: 443 tokens from the three flow views · Four Mamba blocks process the sequence · Three summaries added → six logits

Evidence: [lesson](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/lesson.md), [comparison](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/upstream-comparison.md)

### 00:08:02 — Two learning stages, different targets

During pretraining, the model learns to reconstruct deliberately hidden input features. The source preset masks ninety percent of byte strides and fifteen percent each of sizes and intervals. Reconstruction provides a learning signal without attack-category targets. Fine-tuning then learns the six labeled categories. A loss measures error; an optimizer changes weights to reduce that error. An epoch is a pass through the training loader. Our short pretraining check completed one hundred thirty-two updates. The three main fine-tuning runs instead began from the authors’ released pretrained checkpoint, not from our short-check checkpoint.

On screen: Pretrain: reconstruct masked flow features · Fine-tune: predict known categories · Main runs start from released pretrained weights

Evidence: [lesson](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/lesson.md), [transfer](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/checkpoint-transfer.json)

### 00:08:46 — Inference freezes the learned classifier

After training, inference freezes the learned weights. It uses flow features and a selected checkpoint to produce logits. Softmax turns the logits into normalized display scores; the largest output selects a category. A checkpoint-bound mapping supplies the category names. Without known labels, prediction cannot measure accuracy. With labels, evaluation compares the predictions against those known answers. Validation chooses the checkpoint; test labels must not be used to choose a better-looking model or to supply prediction features.

On screen: Flow features + saved checkpoint → logits · Softmax → display scores; argmax → class · Known labels are needed to measure accuracy

Evidence: [runbook](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/runbook.md), [contract](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/harness-reference.md)

### 00:09:24 — Trace the lifecycle

Trace the lifecycle aloud. When do weights change, when is a checkpoint selected, and when are known test labels used? Take twelve seconds.

On screen: When should weights change? · When are known test labels used?

Evidence: [lesson](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/lesson.md), [comparison](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/upstream-comparison.md), [transfer](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/checkpoint-transfer.json)

### 00:09:34 — Your turn · 12 seconds

**Practice pause: 12 seconds.** Train → select using validation → freeze → test or predict

On screen: Train → select using validation → freeze → test or predict

Evidence: [lesson](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/lesson.md), [comparison](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/upstream-comparison.md), [transfer](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/checkpoint-transfer.json)

### 00:09:46 — Answer: separate learning from measurement

Training updates the weights. Validation selects the candidate. Inference freezes it. Test labels are used afterward for measurement. This separation is central to a defensible experiment.

On screen: Training updates weights · Validation selects · Inference freezes; test labels score afterward

Evidence: [lesson](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/lesson.md)

## 00:10:00 — The authors’ code and this repository

### 00:10:00 — Original model, checked execution wrapper

The authors’ repository provides the neural model, tensor loader and training engines. Our repository fetches a pinned commit and verifies source identity. The model and loader stay unchanged. For G B ten and C U D A thirteen, separate native-extension build copies receive recorded compiler and architecture compatibility edits. This is a compatibility port, not proof of an identical paper environment.

On screen: Pinned authors’ model, loader and engines · GB10 compatibility changes in build copies · Validation, provenance and evidence around execution

Evidence: [comparison](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/upstream-comparison.md), [config](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/configs/ciciot2022.json)

### 00:10:29 — Follow the main entry points

Think of the wrapper as the lab’s coordinator. The reproduction launcher validates the source and inputs, resolves settings, starts the original training program, and saves a run manifest. The evaluation entry point strictly reloads a classifier and scores the native test split. The prediction entry point handles already assembled flows without known labels. The replay entry point records outputs, independently recomputes metrics, and creates a browser display. These tools share preparation checks while keeping their execution jobs distinct.

On screen: repro.py: acquire, validate and launch · evaluate.py: labeled test measurement · predict.py: unlabeled classification · replay.py: save and display predictions

Evidence: [comparison](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/upstream-comparison.md)

### 00:11:06 — Find the recipe, record and explanation

Configuration files describe the source pin, assets and experiment recipe. Requirements describe parts of the runtime. Tools build, measure, review and publish outputs. Tests check important acceptance and failure behavior. The evidence folder holds actual manifests, logs, predictions and hashes. Customer documents translate those records into a presentation. Research documents preserve curated findings and council decisions; they are not a raw private chat dump. The complete file walkthrough explains every tracked file and download, so you can find the exact record behind a question.

On screen: configs/ and requirements/: recipe and runtime · tools/ and tests/: execution checks · docs/customer/evidence/: measured records · docs/research/: curated findings and council records

Evidence: [walkthrough](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/repository-walkthrough.md)

### 00:11:48 — A manifest is a lab notebook

A manifest records what was requested, which source and data were used, the checkpoint identity, class mapping and completion status. A hash is a fingerprint of exact file bytes. It helps detect drift; it does not prove scientific correctness or usage rights. Keep a checkpoint with its successful manifest or export provenance. Choose a fresh output directory each time so new work does not overwrite earlier evidence. Raw data, downloaded source and trained weights remain separate local research assets.

On screen: Which source, data and checkpoint? · Which settings and class mapping? · Did the run actually complete?

Evidence: [contract](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/harness-reference.md), [runbook](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/runbook.md)

### 00:12:22 — Repository decision

Which description should you use: we replaced the authors’ model, or we wrapped pinned original code and ported its native builds? Take ten seconds and name the wrapper’s main additions.

On screen: Did we replace the authors’ model, or wrap and verify its execution?

Evidence: [comparison](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/upstream-comparison.md), [config](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/configs/ciciot2022.json), [walkthrough](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/repository-walkthrough.md)

### 00:12:34 — Your turn · 10 seconds

**Practice pause: 10 seconds.** Name the original pieces and the added checks.

On screen: Name the original pieces and the added checks.

Evidence: [comparison](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/upstream-comparison.md), [config](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/configs/ciciot2022.json), [walkthrough](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/repository-walkthrough.md)

### 00:12:44 — Answer: explain the actual changes

The second description is correct. We added a checked execution route, inference tools, measurements, provenance and teaching materials around the original model. Compiler compatibility changes do not establish exact paper reproduction.

On screen: Original model and loader · Added validation, measurement, provenance and presentation

Evidence: [comparison](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/upstream-comparison.md)

## 00:13:00 — Actual results versus the paper

### 00:13:00 — Three complete fine-tuning runs

Now separate things that were executed from things that were proposed. All three declared fine-tuning seeds completed 120 epochs and 7,920 optimizer updates each. A seed controls random choices, such as initialization and sample order. These were three runs on the same dataset split, not three independent datasets. Validation accuracy selected each best checkpoint. The selected classifier was then reloaded for test evaluation. Logs and optimizer records support the completed budgets; the recipe alone would not prove that the work finished.

On screen: Seeds 0, 1 and 2 all retained · 120 epochs per run · 7,920 optimizer updates per run

Evidence: [results](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/results.json)

### 00:13:40 — Show every seed, not only the best one

The test accuracies were 91.26% for seed zero, 84.05% for seed one, and 84.63% for seed two. Their mean was 86.65%. We retained every seed rather than hiding the weaker runs. Seed zero was chosen for the demonstration in advance, not selected afterward because it had the best score. You can show that run to make the demo concrete, but you should report the three-run mean when describing the experiment.

On screen: Seed 0: 91.26% · Seed 1: 84.05% · Seed 2: 84.63% · Mean: 86.65%

Evidence: [results](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/results.json)

### 00:14:14 — Understand the metrics

Accuracy is the fraction of examples classified correctly. Precision asks how often a predicted category is right; recall asks how many true examples of that category were found. F one balances precision and recall. Macro F one gives classes equal weight; weighted F one weights their support. A confusion matrix shows true categories against predicted categories so aggregate scores do not hide the mistakes. The sample standard deviation across accuracy results was 4.00 percentage points. It is a descriptive spread, not a confidence interval and not a promise about customer traffic.

On screen: Accuracy: fraction correct · F1: balance of precision and recall · Confusion matrix: which categories were confused?

Evidence: [results](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/results.json)

### 00:14:55 — The paper’s result was not reproduced

The paper reports 97.50% accuracy for this benchmark under different conditions. We did not reproduce that result. Source-based fine-tuning used batch size one hundred twenty-eight and an effective learning rate of zero point zero zero one on G B ten. The paper describes batch sixty-four, rate zero point zero zero two, and A one hundred hardware. The full pretraining history of the released checkpoint is unknown. We did not repeat the paper’s full one hundred fifty thousand step pretraining. The cause of the accuracy gap has not been isolated; it would be speculation to attribute all of it to one difference.

On screen: Paper Table IV: 97.50% · Our mean: 86.65% · Different runtime and source-based training settings

Evidence: [results](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/results.json), [comparison](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/upstream-comparison.md)

### 00:15:38 — Repeatability has practical limits

The input audit found five raw-input overlaps between training and validation and six between training and test. Physical independence and the released checkpoint’s previous exposure remain unestablished. These findings belong beside the metrics. Repeating an evaluation on the same test data checks repeatability; it does not create an independent validation set. Independent customer traffic, with reviewed incident labels, is still needed before operational accuracy or false-alert rates can be claimed.

On screen: Raw-input overlaps: 5 train/validation, 6 train/test · Original pretraining exposure remains unknown · Same-test rechecks are not independent validation

Evidence: [native](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/native-data-validation.json), [verification](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/verification.md)

### 00:16:12 — Choose the customer sentence

Choose the sentence you would say to the customer. We reproduced the paper’s ninety-seven point five percent result. Or, three runs averaged 86.65% on the released split, and exact paper reproduction remains open. Take twelve seconds to include one reason the comparison has limits.

On screen: A. We reproduced 97.50% · B. Three runs averaged 86.65%; exact paper reproduction remains open

Evidence: [results](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/results.json), [comparison](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/upstream-comparison.md), [native](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/native-data-validation.json)

### 00:16:33 — Your turn · 12 seconds

**Practice pause: 12 seconds.** State the measured result and one comparison limitation.

On screen: State the measured result and one comparison limitation.

Evidence: [results](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/results.json), [comparison](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/upstream-comparison.md), [native](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/native-data-validation.json)

### 00:16:45 — Answer: retain the conditions

The second sentence is defensible. Keep the runtime, data split, source settings and unknown pretraining history with the result. Avoid turning the best seed, a spread statistic, or repeated testing into a stronger claim.

On screen: Report the mean, all seeds and the unresolved gap

Evidence: [results](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/results.json)

## 00:17:00 — Investigate a recorded prediction

### 00:17:00 — What the working demo actually does

The working browser demonstration displays predictions recorded from a real seed zero G P U inference run. Across one thousand forty-one labeled test flows, nine hundred fifty predictions were correct and ninety-one were incorrect. The page can replay these records, filter them and show mistakes. Opening it does not run the neural model again, inspect your computer’s traffic, or block packets. Its speed control changes the pace of the display. It is unrelated to model inference latency or network throughput.

On screen: 1,041 recorded seed-0 predictions · 950 correct · 91 incorrect · Replay pace is a display setting

Evidence: [prediction](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/seed0/replay/predictions.json), [verification](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/verification.md)

### 00:17:36 — Six categories are not universal attack coverage

The release’s class mapping contains Flood, R T S P Brute Force, Audio, Other, Cameras and Home Automation under their recorded names. The last four describe device or power activity. This is not a universal benign, malicious, and unknown-attack system. The replay has four hundred two predictions in the two attack categories. That does not mean four hundred two verified operational alerts. An alert policy must account for traffic context, uncertainty, unknown activity and the cost of false alarms. None of that can be inferred merely from a class label.

On screen: Two attack categories; four IoT activity categories · 402 predictions in attack categories · No calibrated operational alert policy

Evidence: [prediction](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/seed0/replay/predictions.json), [hardware](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/hardware-roadmap.md)

### 00:18:17 — Read row 635 before judging it

Consider the actual saved row numbered six hundred thirty-five. Its highest-scoring category is class one, R T S P Brute Force, with a display score of 84.43%. The other five scores are visible beside it. First identify what the model predicted. Then distinguish that prediction from what actually happened. The six scores sum to one after softmax, but this normalization does not establish calibration. A high score says the model favors one of these classes; it does not prove an eighty-four percent chance that a customer experienced an attack.

On screen: Prediction: class 1, RTSP Brute Force · Top display score: 84.43% · Known label will be revealed next

Evidence: [prediction](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/seed0/replay/predictions.json)

### 00:18:59 — A confident-looking error

Now reveal the known dataset label: class three, Other. The prediction disagrees with that label, so this is a recorded classification error. We deliberately selected it to examine a mistake, not to estimate how often such mistakes occur. One row cannot establish an operational false-positive rate. The example is useful because the score looked confident even though the labeled answer was different. In a real deployment, an analyst would need traffic context and a validated alert policy. Neither the classifier nor this video verifies that an attack occurred.

On screen: Known dataset label: class 3, Other · Prediction and labeled answer disagree · One example is not a false-positive-rate estimate

Evidence: [prediction](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/seed0/replay/predictions.json)

### 00:19:39 — Try the explanation yourself

Use the next eighteen seconds to explain this row to a customer in three sentences. Say what the model predicted, name the known dataset label, and state what the score cannot establish. Do not call the score a calibrated attack probability, and do not extrapolate a false-alert rate from this one example.

On screen: What was predicted? · What was the known label? · What does the score fail to establish?

Evidence: [prediction](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/seed0/replay/predictions.json), [verification](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/verification.md), [hardware](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/hardware-roadmap.md)

### 00:20:00 — Your turn · 18 seconds

**Practice pause: 18 seconds.** Explain the predicted class, known label and score limitation.

On screen: Explain the predicted class, known label and score limitation.

Evidence: [prediction](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/seed0/replay/predictions.json), [verification](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/verification.md), [hardware](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/hardware-roadmap.md)

### 00:20:18 — A defensible explanation

A good explanation is: the model predicted R T S P Brute Force, but the dataset labeled this flow as Other. The 84.43% display score is not an established probability of attack. This recorded mistake shows why operational use needs independent validation and an alert policy. You can reproduce the display from the saved prediction file without rerunning the model. For fresh predictions, use the separate G P U route and a provenance-bound checkpoint. Keep recorded replay, new model execution and live traffic monitoring distinct in the meeting.

On screen: Predicted RTSP Brute Force; labeled Other · 84.43% is an uncalibrated display score · Investigate before turning predictions into operational action

Evidence: [prediction](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/seed0/replay/predictions.json), [runbook](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/runbook.md)

## 00:21:00 — Set up, use and verify the project

### 00:21:00 — Choose the smallest useful setup

You do not need to install the research stack just to understand or present this work. The browser course, recorded replay, P D F and PowerPoint are the viewing route. A second route uses Python three point ten or newer to check the harness and published evidence on a C P U. The third route builds the tested G B ten environment for new model execution. Keeping these routes separate saves time and prevents a common mistake: thinking that opening a presentation or passing a C P U test has rerun the neural experiment.

On screen: Watch or present: browser or document viewer · Verify saved evidence: Python 3.10+ · Train or predict: tested GB10/CUDA environment

Evidence: [quickstart](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/quickstart.md)

### 00:21:35 — Run the CPU checks

Clone the repository, enter the project folder and run the unit-test command shown on screen. Then run the package verifier and course verifier. The test suite should finish with O K, and the verifiers should report passed for their deterministic checks. The audited release recorded fifty-four harness tests. The interactive course added seventeen more, bringing that snapshot to seventy-one. Video verification is recorded separately. These are checks of the code and delivered artifacts; they do not download new training data or repeat the G P U training runs.

On screen: python3 -m unittest discover -s tests -v · python3 tools/verify_package.py · python3 tools/verify_course.py

Evidence: [quickstart](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/quickstart.md), [verification](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/verification.md)

### 00:22:12 — What verification proves

The package verifier recomputes metrics from saved predictions, compares model identities, checks hashes, and verifies that presentation material agrees with its source. Two separately built native environments also passed seven numerical checks each. Strict saved-model evaluations agreed for all three seeds. A full seed zero unlabeled recheck matched all one thousand forty-one predicted classes and logits in that run. These results support execution and repeatability under recorded conditions. If a file or checksum differs, preserve the failure and investigate. Blindly regenerating checksums would only replace the fingerprint; it would not validate the changed claim.

On screen: Recompute metrics from saved predictions · Check hashes and checkpoint meanings · Reject mismatches; preserve the failure

Evidence: [verification](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/verification.md)

### 00:22:58 — The route for new model execution

For new execution, follow the tested runbook in order. Acquire pinned source and assets, validate the native flows, build the two custom extensions, and run numerical checks. Then train, evaluate or predict. The tested route used an arm sixty-four Python environment, G B ten, and a recorded C U D A compiler and driver stack. It is not a universal Windows, C P U model, or N P U setup. Prediction accepts assembled native flow records, not the supplied packet C S Vs. Use new output directories and retain class-mapping provenance with every moved checkpoint.

On screen: Fetch pinned source and research assets · Validate → build → numerical checks → train · Evaluate labeled flows or predict unlabeled native flows

Evidence: [runbook](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/runbook.md)

### 00:23:38 — Find every download and its purpose

The existing audited release includes the complete package zip, briefing P D F, slide P D F, editable PowerPoint, a checksum list, a release inventory, and a verification receipt. The inventory names files; hashes identify their bytes; the receipt records actual delivery checks. The package does not contain raw research data or inherited model weights. The file walkthrough explains every tracked item and release download. This narrated video is a later deliverable with its own media checks, transcript and captions. A successful download is not a new accuracy experiment.

On screen: PDF / PPTX / script: explain and present · ZIP: code, documents and recorded evidence · Inventory + checksums + receipt: identity and tested delivery

Evidence: [walkthrough](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/repository-walkthrough.md)

### 00:24:18 — Choose a verification route

A colleague with an ordinary laptop wants to check how the reported scores were calculated. Which route is sufficient? Take ten seconds. Distinguish rechecking saved evidence from generating new model predictions.

On screen: A laptop user wants to check the reported scores. · Which route is sufficient?

Evidence: [quickstart](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/quickstart.md), [verification](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/verification.md), [runbook](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/runbook.md)

### 00:24:32 — Your turn · 10 seconds

**Practice pause: 10 seconds.** Saved metrics check or fresh GPU inference?

On screen: Saved metrics check or fresh GPU inference?

Evidence: [quickstart](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/quickstart.md), [verification](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/verification.md), [runbook](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/runbook.md)

### 00:24:42 — Answer: use the evidence route

Use Python, the C P U tests and the package verifier to inspect saved evidence. Fresh predictions require the tested runtime, compatible flows and a trained classifier. Setup and training are follow-up tasks; they are not hidden inside this thirty minute video.

On screen: CPU tests and the package verifier · GPU setup only for new execution

Evidence: [quickstart](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/quickstart.md)

## 00:25:00 — IDS, NPU and SmartNIC: what remains

### 00:25:00 — A proposed capture-to-alert system

A working live I D S would need capture, connection grouping, compatible tensors, inference, a validated alert policy and analyst review. The source extraction helpers have hardcoded paths and a missing helper module; a reliable live extraction path has not been established. A smart network card, or data processing unit, could handle packet steering and some flow preparation. A graphics processor or supported neural processing unit could run the classifier. This is a proposed division of work, not a tested deployment.

On screen: Capture and flow grouping · Compatible tensors and inference · Validated alert policy and analyst review

Evidence: [hardware](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/hardware-roadmap.md)

### 00:25:36 — Portability must be measured

Eager G P U inference worked. The tested Torch graph-capture path failed at a custom causal-convolution operator. Saving model-only weights did not solve graph export, and no N P U compiler or SmartNIC deployment was tested. The batch-one model-only median was about zero point eight eight milliseconds. That excludes capture, flow waiting, preprocessing and transfers. It is not end-to-end I D S latency. The paper’s separate online throughput example concerns byte-only Net Mamba, not our multimodal system. Replacing that operation creates a new candidate implementation. It must match reference predictions before its speed or power numbers are useful.

On screen: Eager GPU inference works · Tested graph capture blocked at a custom CUDA operator · No NPU compiler or SmartNIC deployment tested

Evidence: [export](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/export-probe/metrics.json), [benchmark](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/benchmark/metrics.json), [comparison](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/upstream-comparison.md)

### 00:26:22 — Hardware decision

Does G P U execution establish N P U deployment or live-system readiness? Take eight seconds and name the next required test.

On screen: Does GPU success establish NPU or live IDS readiness?

Evidence: [hardware](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/hardware-roadmap.md), [export](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/export-probe/metrics.json), [benchmark](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/benchmark/metrics.json)

### 00:26:32 — Your turn · 8 seconds

**Practice pause: 8 seconds.** Name a compatibility or end-to-end validation step.

On screen: Name a compatibility or end-to-end validation step.

Evidence: [hardware](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/hardware-roadmap.md), [export](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/export-probe/metrics.json), [benchmark](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/benchmark/metrics.json)

### 00:26:40 — Next work has explicit acceptance criteria

No. Establish compatible extraction, independent traffic validation, calibrated alerting, and target-operator support. Compare outputs and measure the complete system. Inherited data and code terms also remain unresolved. These are future milestones, not completed claims.

On screen: Validate extraction on independent traffic · Port unsupported operators and compare outputs · Measure the full system; resolve inherited asset terms

Evidence: [hardware](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/hardware-roadmap.md)

## 00:27:00 — Your two-minute customer explanation

### 00:27:00 — Your turn: explain the project

Now explain the project aloud as if you were speaking to the customer. You have ninety seconds. Describe the flow inputs and how learning differs from inference. State the three-run mean and distinguish it from the paper’s result. Explain what the recorded demonstration proves and why its error matters. Name the checks that support execution, point to their records, and keep live-system and accelerator work separate. The on-screen prompts will stay visible while you speak. This is practice, not a certification.

On screen: What works and what data it uses · How training differs from inference · Actual mean versus the paper · Recorded demo, evidence and remaining work

Evidence: [answers](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/answers.md)

### 00:27:33 — Customer teach-back · 90 seconds

**Practice pause: 90 seconds.** Inputs and lifecycle Measured results versus the paper Demo, evidence and limitations

On screen: Inputs and lifecycle · Measured results versus the paper · Demo, evidence and limitations

Evidence: [answers](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/answers.md)

### 00:29:03 — Review, correct, then present

A concise explanation could be: We ran the original multimodal classifier on compatible released flows. Training changed its weights; inference used a frozen checkpoint. Three fine-tuning runs averaged 86.65%, below the paper’s 97.50%. The recorded demonstration includes mistakes and does not establish a live detector. Logs, saved predictions and repeatable checks support the measured execution. Capture, independent traffic validation and accelerator porting remain future work. Check your explanation against those points and correct one weak claim. A timer cannot certify understanding. The repository contains the script, captions, actual experiment evidence and setup instructions. Use those records to support the presentation.

On screen: Did you cover all five points? · Correct one inflated or unclear claim · Use the repo evidence during follow-up questions

Evidence: [answers](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/answers.md)
