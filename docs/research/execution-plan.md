# Training and customer package execution plan

Prepared 11 September 2026 for the customer discussion on Tuesday, 15 September 2026.

The requested deliverable is an actual NetMamba+ training and inference experiment, a usable demonstration, and a technical explanation with PDF and editable PowerPoint files accessible through this repository. The historical harness-only evidence remains a dated record.

## Experiment commitments

- Preserve the pinned authors' model, flow loader and training algorithms. Build any required runtime compatibility changes separately, record exact patches and versions, and describe GB10 execution as a changed research environment.
- Use the released CICIoT2022 train/validation/test split without deduplication. Record input hashes and the previously observed cross-split raw-input overlap.
- Use the released pretraining checkpoint for the main fine-tuning route. Preserve its unknown full pretraining history.
- Main fine-tuning configuration: the existing source-based preset, 120 epochs, batch 128, one process, accumulation 1, base learning-rate parameter 0.002, weighted metrics, and seeds 0, 1 and 2. Select checkpoints by validation accuracy. Report every attempted run; do not select the best seed by test accuracy or change hyperparameters in response to test scores.
- Use seed 0 for the customer replay demo, selected before final test scores. Runs may share the GB10 during training; their elapsed training times are not isolated performance benchmarks. Run inference timing separately after training has finished.
- Exercise masked pretraining on training-only native flows as an explicitly labeled functional test. This does not reproduce Browser/Kitsune pretraining or certify the released checkpoint's history.
- Evaluate each completed classifier using the strict test-only entry point. Preserve native results, per-class support and the confusion matrix; independently recompute metrics from prediction records.
- Keep benchmark replay separate from packet capture, flow extraction, online IDS validation, NPU deployment and SmartNIC deployment. Do not claim capabilities that were only diagrammed.

## Work and acceptance

1. **Runtime:** inspect the original dependencies; create an isolated GB10 environment; record compiler, GPU and package versions; build the authors' Mamba fork and causal convolution; compare optimized forward/backward results with their reference operations. Keep installation failures and their corrections in the research record.
2. **Training:** validate all native inputs; run a masked-pretraining functional test; execute the declared fine-tuning runs; preserve checkpoint hashes, class mapping, epoch logs, validation selection and final test outcomes. Runtime faults may be corrected without retuning the model against test results.
3. **Inference/demo:** run strict evaluation on the validation-selected classifiers; check independent metrics and batched versus single-flow predictions; measure explicitly scoped inference latency. Provide a repeatable offline replay demonstration that displays real predictions and identifies its limits.
4. **Presentation:** write a short briefing, an editable slide deck with speaker notes, a talk track and a reviewed research history. Explain inputs/outputs, pretraining, fine-tuning, inference, measured versus paper results, demo boundaries, NPU/SmartNIC options, and remaining gaps. Every measured number must point to a saved artifact.
5. **Publication:** render and inspect the PDF/deck, run the relevant automated checks, scan the additions for secrets, review the affected lesson, and publish the documents, sources and sanitized evidence in this repository. Third-party code, datasets and checkpoints retain their original distribution requirements.

This plan is an execution record, not council ratification or a claim that the experiments have already passed.
