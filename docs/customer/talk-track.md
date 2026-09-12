# Presenter talk track

Use slides 1–8 for the core walkthrough; keep the remaining technical detail available for questions.

## Slide 1 · NetMamba+ from source to a measured demo

Start with the evidence boundary. We ran the original multimodal Mamba classifier and native training workflow on a GB10. The results belong to a documented source-based protocol, which differs from the paper's environment and batch/rate settings. The customer demo is backed by a real saved classifier. Do not call this a validated production IDS or claim the paper's 97.50 percent accuracy as our result.

## Slide 2 · From an untested harness to GPU evidence

The initial repository had standard-library tests and parser dry runs only. The old native extensions did not build directly on CUDA 13. The compatibility fixes affect compiler targets, removed CUB APIs and the assembler path; the original model and loader checkout stays unchanged. Both the first build and the automated rebuild passed numerical checks. A short pretraining run exercises reconstruction learning; it does not recreate the paper's entire pretraining history.

## Slide 3 · One prediction describes one flow

The plus sign is material: NetMamba+ combines byte content, sizes and timing. The CSVs contain 1,500 payload-byte columns per packet, plus TTL, length, protocol, time delta and label. Full scans found 1,410,255 CICIDS2017 rows and 79,881 UNSW rows, but no flow identifiers or established packet grouping. We therefore used the authors' separate CICIoT2022 flow release. The six outputs are Flood, RTSP Brute Force and four IoT power/device categories, not a universal benign/malicious decision.

## Slide 4 · Three stages, three different questions

Pretraining masks 90 percent of byte strides and 15 percent of each sequence modality in the selected recipe. The paper reports Browser and Kitsune pretraining; its exact corpus and checkpoint history have not been established here. Our short training-only functional run proves that the reconstruction path executes and learns on downstream data. Main fine-tuning begins from the released pretraining weights. Inference does not update weights or consume the benchmark label as a model feature. Softmax confidence is uncalibrated.

## Slide 5 · The source recipe differs from the paper

The source preset runs 120 epochs with batch 128 and a base learning-rate parameter of 0.002. Native scaling gives a maximum effective rate of 0.001 for one process and accumulation one. The paper specifies batch 64 and rate 0.002. We used seeds zero, one and two and report them all. Five exact stored raw inputs overlap train and validation; six overlap train and test. Unknown earlier checkpoint exposure and physical capture independence remain limitations. Repeated strict evaluation checks the same frozen test result, not another independent holdout.

## Slide 6 · Report every seed and name the metric

Accuracy is correct predictions divided by test rows. Weighted F1 weights each class by its number of true examples. Macro F1 treats every class equally, so a small weak class can lower macro F1 more strongly. The table reports all three declared seeds; the mean and sample standard deviation describe seed variability on the same dataset, not uncertainty across customer networks. The paper number is not our measurement and is not a directly controlled comparison. The full source-based experiment and strict re-evaluation are complete even if their scores do not match the paper.

## Slide 7 · Make the errors visible

Walk through one off-diagonal cell as a concrete mistake: the row says what the dataset label was, and the column says what the classifier predicted. Diagonal cells are correct. These six classes mix two attacks with four IoT categories. A high aggregate score cannot establish coverage of other attacks or acceptable false alerts on a real network. The full prediction inventory preserves errors; no examples were removed to improve the display.

## Slide 8 · Replay actual saved-classifier predictions

Open the HTML before the meeting. Press Play replay, then Show all, then select Prediction errors. The six class meanings and checkpoint hash are embedded with the measurements. This is a recorded inference demonstration, not live network traffic. The same repo contains commands to rerun actual GPU inference using the trained checkpoint. Raw packet payloads are not embedded in the presentation page.

## Slide 9 · Time the model and state what is excluded

The benchmark uses the frozen seed-zero classifier at batch sizes one, sixteen and one hundred twenty-eight, after training has finished. Each timing synchronizes CUDA before and after the model call. Show median and 95th-percentile batch latency, plus flows per second computed from mean time. Do not convert these figures into network line rate. The paper's 261.87 Mb/s and 3.15-second prototype figures concern its byte-only NetMamba online system on other hardware, not this model-only measurement.

## Slide 10 · The next build is a capture-to-alert system

A deployable IDS requires capture, a bounded flow cache, exact feature extraction, a model queue, an alert policy and monitoring. The authors' extraction helpers have hardcoded paths and a missing common-module dependency, so we do not present them as turnkey live capture. Measure packet loss, queue delays, active-flow memory and false alerts on independent traffic. Mamba's internal sequence state is per model input; it is not already a persistent online connection cache.

## Slide 11 · Split packet handling from neural inference

A SmartNIC is not automatically a neural accelerator. DOCA Flow describes packet match/action and steering capabilities. For an AI NPU, Intel Core Ultra through OpenVINO is one example to investigate, not an already supported target. The custom CUDA Mamba operations need a supported graph or replacement kernels. Parameter storage alone is about 7.48 MB in FP32; total memory includes buffers, activations and workspaces. TOPS does not predict latency for an input-dependent recurrence. Our export probe only tests one Torch graph-capture route.

## Slide 12 · A measured research baseline to build from

This sentence is the safe summary to repeat: We trained and tested the original NetMamba+ classifier on the authors' compatible CICIoT2022 flows using a documented GB10 compatibility port, and can show the measured results and replay. It is not an exact reproduction of all paper results and not a production IDS. The remaining work is concrete: pretraining provenance, independent traffic, a compatible online extractor, operational alert validation and actual deployment on the chosen device.

## Slide 13 · Every measured claim has a saved artifact

The AI research is shared as a reviewed research record, not a raw private conversation. The focused council reviewed the staged plan; it did not independently certify later experiment results, and an older unratified audit remains historical. The command line tools and full measured records let a reviewer inspect the work directly. Third-party data and original weights remain externally obtained assets; hashes and acquisition instructions are included.
