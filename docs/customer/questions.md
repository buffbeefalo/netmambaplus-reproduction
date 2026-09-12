# Customer questions and defensible answers

**Did we actually train a model?** Yes. The main experiment ran the original supervised fine-tuner for three seeds, 120 epochs each. It saved validation-selected classifiers, and the evidence includes complete epoch logs, changed encoder parameters, optimizer counters, checkpoint hashes and fresh strict inference. A separate short run also exercised masked reconstruction pretraining.

**Did we reproduce the paper's 97.50% result?** No. Test accuracy was 91.26%, 84.05% and 84.63%, a mean of 86.65%. The [results table](results.md) preserves every seed. Our source-based batch/rate settings and GB10 runtime differ, and the complete prior history of the authors' checkpoint is unknown. Those differences are known limitations, not proven causes of the accuracy gap; no controlled experiment has isolated its causes.

**Why not train directly on the two CSVs?** They contain individual packet payload vectors and metadata, but omit the identity and established ordering needed to assemble the model's flows. A packet classifier would be a separate adaptation. We used the authors' compatible CICIoT2022 flow release and retained the CSV analysis as evidence for that choice.

**What does the plus sign add?** NetMamba+ combines byte content, packet sizes and inter-arrival timing. In the tested preset these become 443 tokens before the four-block Mamba encoder. The classifier merges three modality summaries and produces six scores. The byte-only NetMamba and bidirectional NetMambaB are different variants.

**What does one prediction mean?** It chooses one of the six learned benchmark labels. Two are Flood and RTSP Brute Force; four are IoT power/device categories. It does not recognize every possible attack. A softmax score is a model confidence display, not a validated probability of malicious customer traffic.

**Is the demo live?** The browser demo replays actual recorded GPU predictions. The repo also has a working command to run new inference on already assembled native flows without ground-truth labels. Neither command performs live packet capture or blocking. The hosted page's playback rate is independent of model speed.

**Could this become an IDS?** Yes, as a development path that still needs a verified flow extractor, bounded capture/queue handling, independent traffic evaluation and an alert policy. The first useful milestone is a reviewed PCAP yielding the same tensors as the training extractor, followed by alert-only trials. Do not claim operational accuracy or false-alert rates until those trials exist.

**How fast is it?** The [benchmark](results.md#model-only-latency) records median, 95th-percentile and mean-based throughput for batches 1, 16 and 128 on this GB10. It excludes capture, flow observation time, preprocessing, data loading and transfers. Those figures cannot be converted directly into network line rate or compared with the paper's different online prototype.

**Can it run on an AI NPU or SmartNIC?** No such deployment has been demonstrated here. SmartNIC steering and flow handling are separate from neural inference. An NPU requires a specific device/compiler, support for the selective scan and other custom operations, numerical validation and an on-device benchmark. The [roadmap](hardware-roadmap.md) includes the actual Torch export-probe result and the work it leaves open.

**Can the customer use the weights commercially?** This repository does not establish that permission. It links externally distributed data and original pretrained assets and records locally trained classifier outputs. The inspected upstream root does not supply a license granting redistribution/commercial rights. Confirm applicable terms before distribution or deployment; the public harness, measurements and presentation do not settle inherited asset rights.

**What can I say in one sentence?** “We trained and tested the original NetMamba+ classifier on compatible CICIoT2022 flows using a documented GB10 runtime port, and can show its saved predictions, measured results and errors; live IDS integration and target-hardware validation are the next steps.”
