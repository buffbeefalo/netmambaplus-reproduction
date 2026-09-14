# NetMamba+ packet addendum — presenter script

This follows the eight-slide PDF and PowerPoint. It is a later addition to the preserved v4 course.

## Slide 1: Both CSVs now train NetMamba+

Previously these CSVs were only profiled. The original reproduction trained on a separate CICIoT2022 flow release. This addition gives both uploaded CSVs a real role: their stored bytes and supplied binary labels train the original NetMamba+ encoder through a new packet adapter. It does not retroactively change the original experiment or paper result.

## Slide 2: A packet is one message fragment

Think of a flow as a conversation and a packet as one fragment of a message. The paper combines byte content with size and timing sequences. The CSV exports preserve bytes but do not provide the verified joins needed to rebuild those conversations. CICIDS2017 and CICIoT2022 are different datasets. The uploaded PDF explains the architecture; it does not establish that these particular CSV exports were its original training files.

## Slide 3: Exactly what goes into the model

All 1,500 stored slots are retained, including zeros, because the export does not reliably identify padding. TTL, total length, protocol, time delta, source identity and label never enter the native forward call. The native classifier has 378 sequence positions and 1,852,416 parameters. Its original six-class flow head is replaced by a fresh bias-free two-class head. Labels enter only the supervised loss. Softmax scores are uncalibrated, not a probability guarantee of operational danger.

## Slide 4: What training actually tests

Every model receives 64,000 sampled group presentations, with replacement. A joint model receives 32,000 presentations from each source. This is a fixed-budget experiment, not an epoch over all 1.49 million rows. NetMamba+ learns its position embeddings; pretrained positional weights are part of the transfer treatment. Scratch uses a freshly initialized native 443-position table with the same remap. The comparison has one seed and does not establish a statistically robust improvement.

## Slide 5: Measured held-out packet results

Balanced accuracy averages benign recall and attack recall. Group weighting prevents repeated identical bytes from dominating the result. Each model is evaluated on both source test partitions. For a single-source model, the opposite-source column is transfer without supervised fitting or validation selection on that source. The joint model has trained on both sources. The UNSW-only metadata control scored 99.34% on UNSW, outperforming the native models there. All scores are specific to these exports, splits, caps and fixed budget; see the report for row weighting, macro-F1, AUROC, average precision, false positives and subtype support.

## Slide 6: Why the data checks matter

Equal payload bytes do not prove these are the same physical packet or capture. Exact hashing prevents exact-input leakage, but not near duplicates or related captures. Selected CIC test support includes zero PortScan rows and only four DDoS rows, so this study cannot establish coverage for those attacks. Row-weighted results describe represented CSV rows; group-weighted results describe distinct stored inputs. Majority, byte-histogram and metadata-only linear models are diagnostic controls, not replacements for the native-model deliverable.

## Slide 7: Use it and check it

The strict predictor accepts the 1,500 payload columns alone, or those plus the four metadata columns; it rejects a label column. It validates the full file, even when an explicit row cap limits prediction. No-label inference is an actual model call, not replay. All 25,930 predicted classes agreed with the saved joint-model evaluation. Matched FP32 replay still had raw-score differences up to 0.000004411; two CIC rows failed the recorded rtol=1e-4, atol=1e-6 comparison. Those failures remain visible, so no bit-exact numerical claim is made. The public saved records allow CPU arithmetic checks without private raw CSVs. Native GPU execution was measured on GB10; other physical GPUs, NPUs and SmartNICs are not validated by these results.

## Slide 8: What you can defend

A simple IDS prototype could feed already-formatted unlabeled packet rows into the saved joint checkpoint and log predictions for analyst review. It currently does not capture, block or inspect live traffic. An eventual SmartNIC pipeline would need packet extraction, batching and a supported numerical implementation of the Mamba scan, followed by end-to-end accuracy, throughput and latency tests. The council was consulted but ended ESCALATED and UNRATIFIED; primary-source and runtime checks resolved implementation issues directly. Do not call that consensus or claim the paper’s 97.50 percent result was reproduced.
