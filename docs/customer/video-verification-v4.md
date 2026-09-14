# Current video, presentation and GB10 verification

The v4 course explains the original reproduction and the new confidence-calibration experiment in one continuous 60-minute lesson. The [watch page](https://buffbeefalo.github.io/netmambaplus-reproduction/video/) includes the transcript, chapter controls and downloads. The matching [PowerPoint](demo/video/v4/NetMambaPlus-course-slides.pptx) has 96 slide images with editable narration notes; the [slide PDF](demo/video/v4/NetMambaPlus-course-slides.pdf) follows the same order. The [searchable handbook](demo/video/v4/NetMambaPlus-course-handbook.pdf) includes the script and complete [file guide](../repository-walkthrough.md).

Codex authored and produced the lesson. Microsoft Andrew Multilingual neural speech renders the text through edge-tts; the provider's model revision is unavailable. Local speech recognition is an independent diagnostic applied to the finished encoding, not the author of the lesson. No completed human full watch/listen-through or universal caption/pronunciation acceptance is claimed.

## Seven questions

Slide numbers count all 96 slides, including the labeled exercises. The video, script and PDF use the same chapter sequence; PDF handbook page numbers differ because the script and file descriptions are searchable prose.

| Customer question | Video location and matching PowerPoint / slide PDF | Explanation |
|---|---|---|
| What did you try, and what works now? | Learning 24:46, slides 41–48; code 29:43, slides 49–56; results 34:26, slides 57–64 | Short pretraining check, three completed fine-tunes, strict native inference, fresh GB10 functionality gates and the new calibrated predictions. |
| How do training and inference work? | Flow inputs 19:55, slides 33–40; learning 24:46, slides 41–48 | Original preprocessing and Mamba blocks; learning updates weights, inference reads frozen weights; calibration fits a separate scalar using validation labels. |
| What data goes in and comes out? | CSVs 09:55 and 14:53, slides 17–32; flow inputs 19:55, slides 33–40; demo 39:21, slides 65–72 | Packet CSVs versus actual native flows; bytes, sizes and intervals; six logits, raw scores, optional calibrated scores and accept/defer output. |
| Which results were actually reproduced? | Paper 04:41, slides 9–16; results 34:26, slides 57–64 | Actual 86.65% mean accuracy versus the paper's unreproduced 97.50%; retrospective confidence improvements leave class decisions unchanged. |
| What could a simple IDS demo look like? | Demo 39:21, slides 65–72 | Replay a saved prediction, reveal a real error, and show the separate calibrated CLI. Live capture, operational response and independent customer testing remain necessary. |
| How might it map to an NPU or SmartNIC? | Hardware 53:50, slides 89–96 | Proposed packet handling, flow assembly, compatible inference backend and host policy; model-only timings and failed graph export retain their limits. |
| What is missing or not working? | Results 34:26; setup 44:00, slides 73–80; hardware 53:50, slides 89–96 | Full pretraining and paper accuracy, independent data, unknown attacks, live extraction, CPU/NPU/SmartNIC model execution and additional physical GPU validation. |

The repository chapter starts at **48:45**, slides **81–88**. It explains every repository area and each type of download. The handbook's appendix gives an individual entry for every file; the video does not read hundreds of filenames aloud. The archived 16-slide customer package and its original answer map remain historical, separately labeled materials.

## What changed in this edition

The new [calibration guide](confidence-calibration.md) describes the implemented feature, exact measurements, commands and limits. Compared with upstream and the previous teaching edition, this release adds a validation-only temperature fitter, checkpoint/runtime compatibility checks, optional calibrated inference and a reproducible three-seed report. The native architecture, feature loader and saved trained weights remain unchanged.

All three calibrators were frozen before any calibrated test inference. On the released test split, mean NLL improved from **0.4416 to 0.4172**, Brier score from **0.2035 to 0.2012**, and 15-bin ECE from **7.03% to 3.82%**. All **3,123** class decisions matched the historical predictions. The fixed 0.90 example accepted more predictions and more errors: seed 0 changed from 620 accepted / 9 wrong to 893 accepted / 37 wrong. Validation also selected the original checkpoints, so this is retrospective evidence, not independent customer reliability or a validated alert policy.

The [fresh GB10 receipt](evidence/calibration/gb10-baseline-audit.json) records all seven numerical comparisons and complete-model update/reload checks. The [default prediction check](evidence/calibration/default-path-check.json) preserves the original output contract. New inference retained all class decisions but showed small FP16 logit differences; a universal bitwise guarantee would be incorrect. The historical three 120-epoch runs remain the training results; calibration does not create three new full training runs.

The revised narration fixes the embedding explanation and removes the stale claim that no calibration procedure exists. Results and policy examples now show the actual gain and its downside. Chapter times were rebalanced to keep the voice at natural speed. Earlier v3 assets remain unchanged and have a separate historical verifier. Python source bytes are now preserved across Git checkouts: a Windows-style newline conversion was shown to break the report's implementation fingerprints, then the same checkout simulation passed with the new Git attribute. This is a portability fix to evidence verification, not a change to the classifier.

## Verification status

The [complete v4 audit](../research/video-audit-v4.json) binds the final script, media and exported documents to their exact SHA-256 hashes. Its technical and content checks have deliberately bounded scopes:

- Both finished video formats decoded for the full hour: 108,000 frames at 30 fps. Audio measured −16.4 LUFS with peaks below clipping; the long quiet intervals matched the announced exercises. There were 249 exact-index MP4 frame comparisons and 20 WebM comparisons. Codex also inspected all 96 static slides and 49 actual encoded frames covering chapter transitions, changed scenes and the recorded demo.
- A real Chromium browser played picture and audio, loaded all 1,083 captions, navigated all 12 chapters by keyboard, sought near the end, downloaded matching MP4 bytes and passed layout checks at widths 320, 390, 768 and 1440. This does not establish support in every browser.
- All 84 spoken passages were independently transcribed from the finished MP4 and read against the script. All 23 required numerical claims were checked against the published evidence, displays and captions. Machine timing analysis retains 339 uncertain cues and eight flagged boundaries; waveform measurements did not independently confirm an actionable defect. One continuous-number boundary remains unresolved. Human listening, pronunciation approval and acceptance of every caption remain pending.
- The 96-slide PowerPoint, its notes, the 96-page slide PDF and searchable handbook passed content and identity checks. The handbook contains all 84 narrations and 494 individual file descriptions. Selected rendered document pages were visually reviewed. An isolated evidence paragraph was kept with its preceding text; some blank space remains on that page.

The history also preserves the WebM job's observed outer exit code 143 after a complete artifact was registered. Its signal cause is unknown. Independent full-file decoding, hash checks and actual browser playback establish the delivered file's usability; the nonzero process observation has not been relabeled as a successful process exit. A one-frame exercise-counter remnant at the closing transition clears before narration and remains recorded as a minor cosmetic observation.

All **226 automated tests** and the 11-command local verification set passed on the GB10 host. That set includes the calibration arithmetic, current and historical video evidence, original package, archived lesson, generated watch page and whitespace checks. These portable checks run on the CPU; the separate GB10 receipts above demonstrate actual CUDA kernels, a complete classifier weight update/reload and real flow inference. Fresh-checkout, CI and publication observations are recorded separately in the same audit. A scoped pass does not claim paper-level accuracy, a production IDS, a completed human full watch, or execution on untested hardware.

## Recheck it yourself

Use the [setup and support matrix](../support-matrix.md) to choose presentation, portable evidence checks or real GPU execution. After cloning the repository, the standard-library checks are:

```bash
python3 -m unittest discover -s tests -v
python3 tools/verify_package.py
python3 tools/review_calibration.py --check
python3 tools/verify_course_video.py
python3 tools/verify_video_course_v4.py
python3 tools/verify_video_course_v3.py
python3 tools/build_video_page.py --check
```

Use `python` if that is the executable name on your system. The v3 check deliberately reads the immutable historical Git snapshot; the v4 check covers the current inventory, lesson and evidence. A complete Git clone is required for historical verification. CPU checks do not run the neural model. The calibration guide and support matrix provide the separately tested GPU commands and runtime requirements.

The [council record](../research/improvement-council-review.json) ended **ESCALATED / UNRATIFIED**, with no mutual decision hash. Subsequent direct review, implementation and measurements are separately recorded. They do not convert that bounded council outcome into consensus or independent certification.
