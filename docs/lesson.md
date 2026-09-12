# Understand and defend a NetMamba+ experiment

The [README](../README.md) contains commands, acquisition links and the current evidence record. This lesson explains what those commands mean. Its references and exercises were reviewed against this repository's CLI and tests; it does not claim external course publication or video generation.

## Start with the unit of observation

A **packet** is one message fragment on a network. A **flow** groups packets using an established connection rule and ordering. A traffic classifier learns a relationship between an observation and a target class. Changing the observation changes the task, even if the model keeps the same name.

The supplied Payload-Byte CSVs expose individual packet payloads, TTL, total length, protocol and a time-difference field. They do not retain sufficient connection identity and order to reconstruct the original flows. Five neighboring rows are not evidence of a five-packet connection. The time-difference column alone does not establish same-flow arrival intervals.

NetMamba+ uses three views of a flow: byte content, packet sizes and packet arrival intervals. A packet-only implementation on the CSVs would be a useful separate adaptation, but it could not support a claim of reproducing this flow representation. The authors' processed CICIoT2022 release gives this repository compatible native inputs to begin testing. This is a different dataset from CICIDS2017.

## Follow one flow into the model

In the supplied preset, the [original loader](https://github.com/wangtz19/NetMambaPlus/blob/eec9483e2f0fb84ca22982b9de8149bc3a8b1ad2/src/util/loader_data.py) takes at most five packets with 320 stored bytes per packet. The paper describes those 320 bytes as an extracted 80-byte header region and 240-byte payload region. The JSON must already contain that extraction; our harness cannot recover missing headers from a payload export.

Five times 320 gives a fixed 1,600-byte representation. Short packets and short flows are padded, and excess bytes/packets are truncated by upstream. The measured byte tensor shape is `[B, 1, 1, 1600]`, where B is batch size. The model flattens it to `[B, 1, 1600]` for four-byte stride embedding. Its image-style transformation divides bytes by 255 and normalizes with mean 0.5 and standard deviation 0.5. Thus an input byte of zero maps to -1, and 255 maps to +1 after this normalization. The harness delegates these operations rather than maintaining a second implementation.

Sizes and intervals use their first twenty entries, again with native padding/truncation. The unsigned-size path clips to the range 0–1500. Its padding value 1501 is subsequently clipped to 1500; a size at that boundary is therefore not a reliable indicator of padding. For nonnegative interval x, the loader implements `(1+x)/(2+x)`: zero becomes 0.5, one becomes two-thirds, and very large values approach 1. Padded infinite intervals become 1 inside the loader. Raw JSON intervals must remain finite; padding is the loader's job. Units and extraction provenance still matter because the same number can mean different durations in different exports.

The [fused Mamba model](https://github.com/wangtz19/NetMambaPlus/blob/eec9483e2f0fb84ca22982b9de8149bc3a8b1ad2/src/models/models_net_mamba_fuse3.py) embeds four-byte strides, producing 400 byte tokens before masking. It embeds the twenty sizes and twenty intervals too. Learned position and modality indicators tell the model where each token belongs and what it represents. The pinned model appends a summary token to each modality and concatenates sizes, intervals and bytes for its sequence encoder. A Mamba block updates a learned state while scanning the sequence; the state update depends on the input. The model can combine evidence from content and timing instead of treating every packet as unrelated.

## Separate the two learning stages

During **pretraining**, the model reconstructs deliberately hidden portions of the input. With the source preset, it masks 90% of byte strides and 15% each of size and interval entries. Predicting missing content gives the encoder a learning signal without attack-category targets. This stage has reconstruction decoders and produces a pretraining checkpoint.

During **fine-tuning**, the model learns labeled traffic categories. A classifier head turns the learned representation into one score per class. The original [fine-tuning program](https://github.com/wangtz19/NetMambaPlus/blob/eec9483e2f0fb84ca22982b9de8149bc3a8b1ad2/src/fine-tune.py) transfers compatible pretrained weights using its own intended transfer-learning behavior. It learns the classifier on training data, evaluates validation data after epochs, and saves the classifier with the best validation accuracy.

That best classifier is then evaluated on test data by the native fine-tuner. Validation answers which candidate to select. Test data estimates how the selected candidate performs on the held-out benchmark. Repeatedly changing settings because of test results turns the test set into another selection set and weakens that estimate.

The released `fuse3_mamba.pth` was initially examined without Torch deserialization. The current GPU work additionally loaded the trusted, hash-checked file and verified compatibility: the classifier head is missing as expected, reconstruction parameters are extra, and matching encoder shapes agree. Its saved step/epoch fields still do not establish the full training corpus or earlier history. The [research record](research/research-record.md) and [measured results](customer/results.md) distinguish successful downstream execution from unknown pretraining provenance.

## Why metadata and strict loading matter

Consider two six-output models. One assigns index 0 to Flood and index 1 to RTSP Brute Force; another reverses them. Their weight shapes can be identical while their predictions have different meanings. Successfully loading tensor shapes is insufficient to establish class semantics.

`metadata.json` defines the class name to integer mapping. The harness checks a one-to-one contiguous mapping, checks every row against it and derives `nb_classes` from it. The default CICIoT2022 preset requires six entries. Size/interval arrays may be shorter or longer than twenty; requiring exactly twenty at the JSON boundary would reject records the original loader deliberately supports.

Successful fine-tuning records the selected checkpoint's SHA-256 and its class mapping. Separate evaluation can use that hash-bound record to compare checkpoint semantics with test metadata. A digest identifies exact file bytes; it does not prove a provenance author's statements. An unbound or absent record leaves class-order provenance unknown. An explicitly supplied wrong digest or established mapping conflict fails.

Strict evaluation has a different purpose from transfer learning. It loads `checkpoint["model"]` with `strict=True` and refuses missing, extra or incompatible model weights. Replacing a mismatched head would create a different classifier, so this path does not attempt it. It also checks the native loader's returned `idx2label` mapping instead of assuming its tuple contains only a DataLoader.

## Know which files each stage can see

| Stage | Data files read and hashed by validation | What happens next |
|---|---|---|
| Pretrain | Metadata and `data-train.json`, or `data.json` if the preferred file is absent | Original reconstruction training |
| Fine-tune | Metadata, train, validation and test JSON | Original training, selection and final test |
| Evaluate | Metadata and test JSON only | Strict loading and one test-loader evaluation |

The separate evaluator also reads the requested checkpoint and optional provenance. It never enters `fine-tune.py`'s `main`, which would pull in the broader training workflow. It directly calls the original classifier factory, loader and [evaluation engine](https://github.com/wangtz19/NetMambaPlus/blob/eec9483e2f0fb84ca22982b9de8149bc3a8b1ad2/src/engine_mm.py).

The engine contains an unconditional `torch.cuda.amp.autocast()` context. The source preset's `--no_amp` flag does not turn that context off. Changing it would alter the numeric execution being reproduced. This repository preserves it and makes no claim that CPU execution yields equivalent results.

The harness first verifies the upstream checkout, then obtains each namespace through the real [pretraining parser](https://github.com/wangtz19/NetMambaPlus/blob/eec9483e2f0fb84ca22982b9de8149bc3a8b1ad2/src/util/arg_pre_train.py) or [fine-tuning parser](https://github.com/wangtz19/NetMambaPlus/blob/eec9483e2f0fb84ca22982b9de8149bc3a8b1ad2/src/util/arg_fine_tune.py). Keeping the full parsed namespace preserves defaults used deep inside the native loader, model and engine. Dry runs inspect these interfaces without importing the research stack or executing a model.

Validation and invocation share the stage-settings resolver: stage-specific settings override `common`, and evaluation inherits fine-tuning settings. If a stage selects `signed_sizes`, that is the field validation checks and the duplicate audit fingerprints. Certifying `sizes` while the model reads `signed_sizes` would give false confidence in the inputs.

Source integrity also depends on installation. The bundled Mamba installer can download a stock wheel with the same version number, even though the native model needs constructor arguments from the bundled fork. Follow the README's forced local-build command and installed-source comparison. A matching version string alone is insufficient, and matching Python files still does not establish successful CUDA execution.

## Read an experiment record

`manifest.json` is a structured lab notebook. Its source hashes identify the checked implementation, input hashes identify the measured files, `native_args` records the parsed configuration, and runtime fields describe part of the environment. Training writes native logs; separate evaluation writes the full returned metric dictionary to `metrics.json`.

A recorded validation requires a new report filename and refuses to overwrite existing files. Each model run requires a new or empty output directory, claimed by creating its first manifest atomically. Concurrent starts cannot both own it. This keeps old checkpoints and results from becoming mixed with a new experiment. A refused output location stays unchanged; the diagnostic is printed instead of writing another manifest over existing work.

The statuses carry different claims. `dry_run` means inputs and arguments passed preflight. `failed` means execution was attempted and did not complete successfully. `succeeded` means this invocation completed its checks; it does not assert that the result matches the paper. A remaining `running` record may indicate a hard interruption and must not be counted as a successful experiment.

Accuracy is the fraction of correct predictions. Precision measures how often a predicted class is correct; recall measures how much of a class was found. F1 combines precision and recall. Weighted F1 weights class F1 values by their support, meaning the number of true examples per class. The confusion matrix reveals which classes were confused. Keep the native metrics together: a high overall number can hide a weak rare class. Nonfinite values are serialized as `null` and listed by path instead of producing invalid JSON or silently disappearing.

## Understand the limits of duplicate checks

Two distinct filenames may contain identical model inputs. Therefore checking `pcap_file` overlap is useful but insufficient. The harness also fingerprints the exact raw byte strings, size string and interval string, excluding the label and filename. The counting formula and file hashes are in the README.

Intake found five train/validation and six train/test shared raw inputs in the released CICIoT2022 files; the implemented validator confirmed them. No recorded cross-split file identifiers overlapped. These observations do not establish whether the original captures were independent, and padding/truncation can collapse additional distinct raw records into identical transformed inputs. The harness reports what it can establish and preserves the official split.

A separate capture-grouped or deduplicated evaluation could test sensitivity to these overlaps, but it would answer an additional question on a changed sample. Label that experiment separately instead of silently replacing the primary reproduction data.

## Distinguish a recipe from a result

The [paper](https://arxiv.org/abs/2601.21792v1) describes 150,000 pretraining steps and a fine-tuning batch size of 64. The selected released-source recipe uses 100,000 steps and batch size 128. Its native learning-rate scaling divides effective batch size by 256. With one process and accumulation 1, `blr=0.001` gives a conditional initial rate of 0.0005; `blr=0.002` gives 0.001. The model's actual schedule is still owned by upstream.

The current fine-tuning runs exercised the source settings and recorded the effective rate. A parser dry run alone would establish only that settings are accepted. Unit tests establish harness behavior under controlled fixtures. A real GPU experiment establishes behavior in its recorded environment. The current three-seed GB10 results therefore support a source-based compatibility-port experiment; they do not erase the paper's batch/rate differences or establish its pretraining history.

## Read the new training and demo evidence

The [customer package](customer/README.md) records actual masked pretraining, full fine-tuning, strict saved-classifier inference and the browser replay. Read its [runbook](customer/runbook.md) alongside the commands. The short masked-pretraining configuration requests 100 steps, but the original source executes complete epochs: 66 batches per epoch produce 132 completed updates across two epochs. The saved step-130 checkpoint contains 131 updates, not the final 132. Requested steps, completed updates and saved-checkpoint updates are different quantities.

The fine-tuner's per-epoch message says “test samples” even though its supplied loader is validation. Read the call site, not just the printed label. Its selected checkpoint uses the exact `valid_acc` field. The subsequent real test pass, separate strict evaluator and recorded prediction pass all use that same selected model. Repeating them verifies execution agreement on the same fixed test set; it does not create three independent generalization tests.

`replay.py` recomputes accuracy, per-class precision/recall/F1, weighted F1 and macro F1 from the saved labels and predictions. Macro F1 weights each of the six classes equally. Weighted F1 weights them by their true support. Try the deliberately imbalanced fixture:

```bash
python3 -m unittest discover -s tests -k test_metrics_keep_confusion_orientation_and_macro_weighted_distinct -v
```

The confusion matrix uses true classes as rows and predicted classes as columns. Looking only at weighted metrics can obscure a weak rare class. The real experiment's smallest test class has 41 examples while each other class has 200; retain that support when explaining a percentage.

`predict.py` supports flows without ground-truth labels. It adapts only the native loader's required label/name fields in a temporary copy, discards those targets before model forward, and emits predictions without accuracy metrics. It never creates flow identity, missing headers or arrival order from packet CSV rows. The original byte/size/interval transformations still belong to the native loader. Its output is a six-class prediction, not an operational decision to block traffic.

The replay page displays recorded outputs of that model family; changing playback speed does not rerun inference or change its measured latency. The benchmark times synchronized GPU model execution separately from capture and preprocessing. The [hardware roadmap](customer/hardware-roadmap.md) explains the additional work needed for a live IDS, NPU or SmartNIC.

## Four exercises requiring no downloads

Run these commands from the repository root. Each test intentionally creates temporary examples, asserts the expected behavior and cleans up. A test reporting `OK` can mean it successfully rejected bad data; it does not mean that the bad data was accepted.

1. **Find a malformed flow.** Read `DataTests.test_invalid_records` in [the test file](../tests/test_repro.py), predict which rule each case violates, then run:

   ```bash
   python3 -m unittest discover -s tests -k test_invalid_records -v
   ```

   A byte of 256 is outside the byte range; a negative interval violates chronological arrival semantics; a size/interval length mismatch breaks the paired sequence contract. The double-space example is rejected because the native numeric parser splits on a literal space.

2. **Swap class meanings.** Read `ProvenanceTests.test_explicit_hash_binding_and_conflicts`. Both swapped classes retain valid indices, but the checkpoint's meaning no longer matches the test metadata:

   ```bash
   python3 -m unittest discover -s tests -k test_explicit_hash_binding_and_conflicts -v
   ```

3. **Distinguish identity from content.** The duplicate fixture uses different filenames with identical input strings. Predict the shared-input count before running:

   ```bash
   python3 -m unittest discover -s tests -k test_duplicate_reporting_does_not_mutate_data -v
   ```

   The test reports one shared raw-input group and verifies that every original JSON byte remains unchanged. Different provenance labels do not make the content unique.

4. **Refuse an incompatible classifier.** A model stub raises a shape-mismatch error. The test requires one strict load attempt, no fallback and a failed manifest:

   ```bash
   python3 -m unittest discover -s tests -k test_incompatible_checkpoint_fails_without_fallback -v
   python3 -m unittest discover -s tests -k test_strict_test_only_execution_and_complete_metrics -v
   ```

   The second test removes training/validation files and installs access traps, verifies the original evaluator interface and checks complete metric serialization. These are interface tests with stubs, not Torch or CUDA integration tests.

To repeat the real experiment, follow the customer runbook's acquisition, tested GB10 environment, validation, training and inference sequence. Freeze the comparison protocol before viewing test performance, retain every run manifest and report the uncertainties alongside the measured result. These lesson sources and references were reviewed for the customer package; no external course publication, shared coverage reset or video refresh is claimed.
