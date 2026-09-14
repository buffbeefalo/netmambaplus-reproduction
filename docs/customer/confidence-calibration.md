# Confidence calibration: the measured addition to the reproduction

The reproduction already trained and evaluated the authors' original multimodal NetMamba+ classifier. This addition changes how its confidence scores can be used: fit one temperature for a saved classifier, produce calibrated scores during new inference, and optionally mark predictions **accept** or **defer** for review. The original predicted category, raw logits and raw softmax scores remain available.

The new code does not change the authors' model architecture, feature loader, pretrained weights, or three completed fine-tuning runs. Compared with the upstream repository and our previous release, it adds explicit calibration provenance, compatibility rejection, a review policy, and reproducible before/after confidence measurements. It is an improvement to the experiment and inference interface; a positive temperature cannot improve the model's top-class accuracy.

## What the paper and datasets have to do with this

The NetMamba+ paper proposes ways to learn representations of network traffic. Our measured model combines packet bytes, packet sizes and time intervals from a flow, then selects one of six CICIoT2022 categories. The uploaded CICIDS2017 and UNSW CSVs contain packet rows rather than established flow inputs, so we profiled those files but did not train this model on them. Their names are not interchangeable with CICIoT2022. The [paper and data explanation](paper-and-data-explained.md) walks through both CSVs and the attached PDF.

Temperature scaling is a separate post-training method; it is not a reproduced NetMamba+ paper result. The method was studied by [Guo and colleagues, *On Calibration of Modern Neural Networks*, 2017](https://proceedings.mlr.press/v70/guo17a.html). That paper does not establish our traffic-classifier outcome. The measurements linked below do.

## How it works

A logit is one of the six raw numbers emitted by the classifier. Softmax turns those numbers into six scores that sum to one. A score of 0.90 does not, by itself, establish that the prediction will be right 90% of the time on a customer's network.

The fitter chooses one positive scalar `T` to minimize validation negative log-likelihood (NLL). For each class, the calibrated score is `softmax(logits / T)`. Larger temperatures soften the scores; smaller temperatures sharpen them. Neither operation changes which original logit is largest. For example, logits `[2, 0]` produce scores approximately `[0.881, 0.119]`. With `T=2`, the scores become `[0.731, 0.269]`; the first category still wins.

The search uses 80 deterministic bisection steps on inverse temperature, with a fixed temperature range of 0.05 to 20. NLL is convex in inverse temperature, so the one-dimensional search does not require a second neural network or another full training run. The fitted JSON file binds the temperature to the checkpoint hash, class meanings, configuration, pinned source, package versions and inference precision. These hashes establish file compatibility, not independent authentication of scientific claims.

`predict.py` checks that binding before loading the GPU runtime. A mismatched, malformed, nonfinite or changed artifact fails explicitly. Without the optional arguments, predictions retain the original output fields. With calibration, each row also contains `calibrated_scores`. With a threshold, `decision` is `accept` when the score of the unchanged predicted class is at least the threshold, and `defer` otherwise. This does not block traffic, detect unknown attacks or supply a correctness guarantee.

## The experiment and its limits

The [fixed protocol](evidence/calibration/protocol.json) was written before calibration fitting and scaled test evaluation. All three original checkpoints are included. Each temperature is fitted on the same 1,040 validation flows, then tested on the same 1,041 already-published test flows. The 0.90 threshold was fixed in advance as an illustrative review policy; it was not optimized on either split.

The validation split had already been used to choose each original checkpoint. It contains five exact raw inputs also present in training. There are zero exact raw-input overlaps between validation and test. These observations do not prove independent physical captures, and the released pretraining checkpoint's earlier exposure remains unknown. The test set has been examined before. This is therefore a **retrospective post-hoc study**, not a pristine calibration holdout or independent customer-network validation.

The primary comparison is NLL: how much probability was assigned to the actual category, with confidently wrong answers penalized strongly. We also report multiclass Brier score (the mean sum of squared class-probability errors) and expected calibration error, or ECE (15 equal-width confidence bins). Lower values are better for these three measurements, but they describe different properties and need not improve together. Accuracy is separately preserved.

For the review policy, coverage is accepted predictions divided by all predictions. Accepted error is wrong accepted predictions divided by accepted predictions. An empty accepted set has an undefined error rate, recorded as JSON `null`, not zero. The report retains every seed, every denominator and unfavorable results.

The machine-readable [paired results](evidence/calibration/results.json) are recomputed by [review_calibration.py](../../tools/review_calibration.py) from the actual new predictions and hash-bound recorded test labels. That review program independently repeats the saved validation fit as a consistency check; it never fits using test labels. Raw and calibrated comparisons use identical fresh logits for each checkpoint.

## Actual paired results

All values below come from the new GB10 executions. Each row compares the same 1,041 test flows and identical logits before and after scaling. NLL and Brier are unitless scores; ECE is shown as a percentage.

| Seed | Temperature | NLL, raw → calibrated | Brier, raw → calibrated | ECE, raw → calibrated | Accuracy |
|---|---:|---:|---:|---:|---:|
| 0 | 0.786196 | 0.343189 → 0.321800 | 0.143533 → 0.141662 | 6.01% → 2.59% | 950/1,041 = 91.26% |
| 1 | 0.776998 | 0.490500 → 0.468945 | 0.231334 → 0.229815 | 6.66% → 4.01% | 875/1,041 = 84.05% |
| 2 | 0.717372 | 0.491024 → 0.460898 | 0.235626 → 0.232227 | 8.42% → 4.87% | 881/1,041 = 84.63% |

Across all three seeds, mean NLL changed from **0.4416 to 0.4172**, mean Brier from **0.2035 to 0.2012**, and mean ECE from **7.03% to 3.82%**. All three measures improved for each checkpoint. Mean accuracy stayed **86.65%**; all 3,123 class decisions across the three runs agree with their respective historical predictions. This is an observed confidence-metric improvement on this retrospective benchmark, not a gain in accuracy or proof of customer-network performance.

The fixed 0.90 threshold demonstrates a tradeoff. Sharper calibrated scores accept more rows, including additional mistakes:

| Seed | Raw accepted / deferred | Raw wrong accepted / accepted | Calibrated accepted / deferred | Calibrated wrong accepted / accepted |
|---|---:|---:|---:|---:|
| 0 | 620 / 421 | 9 / 620 = 1.45% | 893 / 148 | 37 / 893 = 4.14% |
| 1 | 542 / 499 | 7 / 542 = 1.29% | 652 / 389 | 24 / 652 = 3.68% |
| 2 | 428 / 613 | 4 / 428 = 0.93% | 588 / 453 | 17 / 588 = 2.89% |

The already-discussed mistake at JSON row 635 is a useful demonstration: its true class is Other, while the model predicts RTSP Brute Force. In the new execution its raw top-class score is 84.43%, its calibrated score is 92.30%, and the 0.90 policy marks it **accept**. Calibration did not fix that mistake. The original browser replay still shows its original uncalibrated recording.

The public seed folders contain the fitted JSON file, validation observations in the fitting manifest, fresh prediction outputs and both execution logs. `python tools/review_calibration.py --check` repeats the validation fit and all reported arithmetic without downloading flows or loading CUDA.

## Set it up and use it

Viewing the video, PDF, PowerPoint and recorded browser demo needs no GPU. Rechecking the saved calibration arithmetic needs Python 3.10 or newer and no additional packages:

```bash
python tools/review_calibration.py --check
python -m unittest discover -s tests -v
```

New model execution uses the checked CUDA environment and separately acquired native data described in the [support matrix](../support-matrix.md). Activate that environment first. Keep a checkpoint beside its training `manifest.json`, or supply `--provenance` explicitly. Use a fresh output directory for each command:

```bash
python tools/calibrate.py --data assets/data/ciciot2022 \
  --checkpoint runs/ciciot-ft-seed0/checkpoint-best.pth \
  --output runs/calibration-seed0

python predict.py --flows path/to/native-flows.json \
  --checkpoint runs/ciciot-ft-seed0/checkpoint-best.pth \
  --calibration runs/calibration-seed0/calibration.json \
  --abstain-threshold 0.90 --output runs/calibrated-predictions
```

`tools/calibrate.py` reads `metadata.json` and `data-valid.json`, plus the recorded data-validation evidence that identifies those files. It does not read the actual training or test flow files. The native loader must preserve row order, use the complete split, and include the final partial batch. Targets are removed before model forward and used separately by the fitter. The fitter records its input and output identities and rejects data that differs from its supplied validation evidence.

`predict.py` accepts a JSON array of already-assembled native flows. The byte, size and interval fields must follow the original loader contract; an arbitrary packet CSV is insufficient. Its output directory contains a run manifest and `metrics.json`, whose `predictions` list contains one result for each input row. Despite that existing filename, unlabeled inference computes no ground-truth accuracy. The calibrated file must match the model and checked runtime, including the recorded Python and package versions. If a bound identity changes on another machine, fit a new artifact in that checked environment and validate its behavior; do not edit the old binding to make it pass.

## What ran on the GB10

The [fresh baseline audit](evidence/calibration/gb10-baseline-audit.json) records seven successful optimized-versus-reference CUDA comparisons and the complete 1,870,080-parameter model's optimizer-step, strict save/reload and inference check. That complete-model check uses six synthetic native-format fixtures; it is not another 120-epoch accuracy experiment. The three original full fine-tuning runs remain the training evidence.

The [updated default-path check](evidence/calibration/default-path-check.json) records actual inference through the changed predictor with calibration disabled. It returned all 1,041 rows, retained the original output fields and preserved every class decision. Small FP16 logit differences remain visible; a universal bitwise-equality claim would be inaccurate. The pure-function regression checks independently establish unchanged raw score formatting for the same supplied logits.

Each calibrated seed record contains the actual fitting manifest, fitted artifact, prediction manifest and per-row outputs. The comparison checks source and checkpoint hashes, the chronology of fitting and inference, row order, every saved score, the threshold decision and aggregate arithmetic. All three calibrators were frozen before the three calibrated test invocations.

## A simple IDS demo and hardware path

The existing [browser replay](https://buffbeefalo.github.io/netmambaplus-reproduction/) remains a recording of original predictions, including the known mistake at JSON row 635. It does not run the new calibration feature in the browser. A working command-line demonstration runs calibrated prediction on native flows, opens the output JSON, and shows both a class and its accept/defer decision alongside the original scores. The evidence includes actual outputs, so a presentation can show recorded examples without requiring CUDA on the customer's laptop.

A future live IDS could assemble validated flows, execute the classifier, apply calibration and a separately validated review policy, then log events. The existing code does not yet supply a verified live packet-to-flow extractor or an operational alerting service. Observation mode and independently labeled customer traffic are still required before making deployment claims.

On a proposed SmartNIC/NPU system, a NIC could handle packet movement and flow assembly while a supported accelerator executes the neural network. Temperature division, softmax and the review threshold could run on the host or a verified accelerator backend. The new pure-Python implementation executes those small postprocessing steps on the host. It does not solve the failed custom-CUDA graph-export path, demonstrate NPU execution, or establish end-to-end throughput. The [hardware roadmap](hardware-roadmap.md) retains those boundaries.

## What still needs work

The paper's 97.50% comparison result and full pretraining remain unreproduced; our original three-seed mean is 86.65%. Independent calibration data, customer traffic, unknown-attack detection, live extraction, reliable operational policy and actual NPU/SmartNIC deployment remain missing. Additional physical GPUs need their own operator and complete-model execution checks; portable CPU tests do not implement a CPU model backend. Inherited data/checkpoint terms remain unresolved.

The [council record](../research/improvement-council-review.json) preserves its `ESCALATED / UNRATIFIED` outcome. Both seats conditionally converged on calibration, but the bounded review lacked material data/verifier evidence. Direct source inspection and implementation resolved those engineering gaps; they did not turn the council outcome into consensus or independent certification.

The current video, matching slide notes and handbook explain this addition alongside the original paper/data/training story. Computational media checks and Codex review remain distinct from a completed human full watch and listen-through.
