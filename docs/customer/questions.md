# Customer questions and defensible answers

**Did we actually train a model?** Yes. The original flow experiment ran three seeds for 120 epochs each, with validation-selected classifiers, complete logs, changed encoder parameters, optimizer counters and strict inference. A separate short run exercised masked reconstruction pretraining. The later [packet study](packet-model-study.md) also trained six native models for 1,000 updates each on CIC-only, UNSW-only and joint inputs, each with pretrained and scratch initialization.

**Did we reproduce the paper's 97.50% result?** No. Test accuracy was 91.26%, 84.05% and 84.63%, a mean of 86.65%. The [results table](results.md) preserves every seed. Our source-based batch/rate settings and GB10 runtime differ, and the complete prior history of the authors' checkpoint is unknown. Those differences are known limitations, not proven causes of the accuracy gap; no controlled experiment has isolated its causes.

**Did the two CSVs actually connect to the model?** Yes. The later packet adaptation validates both full files, groups identical payloads globally and trains the native NetMamba+ encoder with a two-class head. The joint model trains on both sources. Their missing flow identity/order means this is a packet experiment, not the original flow representation. The original experiment separately uses the authors' compatible CICIoT2022 flow release.

**What does the plus sign add?** NetMamba+ combines byte content, packet sizes and inter-arrival timing. The original flow preset has 443 tokens, four Mamba blocks and six output scores. The packet adaptation uses the same native encoder code but has 378 positions, empty size/timing sequences and two scores. Its two leading summaries contain no observed size/timing data. The paper's byte-only NetMamba and bidirectional NetMambaB are different variants; this packet wrapper is an explicitly separate configuration.

**What does one prediction mean?** The flow classifier chooses among Flood, RTSP Brute Force and four IoT device/power labels. The packet classifier predicts the supplied benign/attack grouping. Neither recognizes every possible attack. Packet softmax scores are uncalibrated. The separate flow-calibration extension measures retrospective confidence, not a validated probability of malicious customer traffic.

**Is the demo live?** The browser replays original recorded GPU flow predictions. Separate working commands run new inference on already assembled native flows or unlabeled packet CSVs. Neither captures or blocks live traffic. The page's playback rate is independent of model speed.

**Did every numerical comparison pass?** No. All 25,930 packet classes agreed in the full saved-model replay, but two CIC rows failed the strict raw-logit tolerance in the matched FP32 comparison. The [packet report](packet-model-study.md) retains these failures and the larger differences in earlier comparison settings. Successful evidence verification means it accurately checks this record.

**Does the video explain the latest packet model?** The v4 hour-long course explains the paper, original flow experiment and calibration. The later [packet PDF, PowerPoint and script](README.md#current-packet-study-both-uploaded-csvs) explain the CSV integration. Send both editions with their scope labels.

**Could this become an IDS?** Yes, as a development path that still needs a verified flow extractor, bounded capture/queue handling, independent traffic evaluation and an alert policy. The first useful milestone is a reviewed PCAP yielding the same tensors as the training extractor, followed by alert-only trials. Do not claim operational accuracy or false-alert rates until those trials exist.

**How fast is it?** The [benchmark](results.md#model-only-latency) records median, 95th-percentile and mean-based throughput for batches 1, 16 and 128 on this GB10. It excludes capture, flow observation time, preprocessing, data loading and transfers. Those figures cannot be converted directly into network line rate or compared with the paper's different online prototype.

**Can it run on an AI NPU or SmartNIC?** No such deployment has been demonstrated here. SmartNIC steering and flow handling are separate from neural inference. An NPU requires a specific device/compiler, support for the selective scan and other custom operations, numerical validation and an on-device benchmark. The [roadmap](hardware-roadmap.md) includes the actual Torch export-probe result and the work it leaves open.

**Can the customer use the weights commercially?** This repository does not establish that permission. It links externally distributed data and original pretrained assets and records locally trained classifier outputs. The inspected upstream root does not supply a license granting redistribution/commercial rights. Confirm applicable terms before distribution or deployment; the public harness, measurements and presentation do not settle inherited asset rights.

**What can I say in one sentence?** “We ran NetMamba+ on GB10, measured its original flow experiment and a separate adaptation trained on both supplied packet CSVs, and published the code, predictions and limitations; live IDS and accelerator deployment remain future work.”
