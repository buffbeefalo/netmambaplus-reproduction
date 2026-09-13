# The NetMamba+ course video

[Watch the video](https://buffbeefalo.github.io/netmambaplus-reproduction/video/) · [Download MP4](https://github.com/buffbeefalo/netmambaplus-reproduction/releases/download/course-video-v2/NetMambaPlus-30-minute-course.mp4) · [Versioned release](https://github.com/buffbeefalo/netmambaplus-reproduction/releases/tag/course-video-v2) · [Full transcript](demo/video/transcript.md)

This is the actual narrated course requested after the interactive HTML lesson. It is **30:00, 1080p**, with 51 spoken scenes, nine announced practice intervals, chapter navigation, captions and a reflowing transcript. There is one continuous lesson and one main MP4 download. An internal VP9/Opus playback copy serves browsers without MP4 codecs; it is the same video, not another lesson. The voice is synthesized locally with Kokoro ONNX; no online narration service or cloned customer voice was used.

The course explains existing measured experiments. Playing it does not perform training, capture traffic, or establish additional accuracy. The measured mean remains **86.65%**, compared with the paper’s unreproduced **97.50%**. A complete human listening/watch-through has **not** been performed. Automated media checks and source review do not establish that human gate, learner mastery, or complete council acceptance.

## Watch, download or present

Use this as a handoff to the person who will explain the repository onward. Watch the complete route, practice the explanation aloud, and use the evidence links when the next person asks how a claim was established. The lesson explains every part’s role and the execution process; the file walkthrough supplies the individual inventory rather than reading every filename aloud.

Open **Watch the video**, press Play and use the chapter links to seek. Download the MP4 for a meeting without internet access. Captions are already in the picture; the optional player text track and separate VTT/SRT files support other workflows. The complete transcript is visible below the player and reflows on a phone. Every substantive scene links to evidence.

The video allocates 27:00 to spoken explanation and worked answers and 3:00 of announced practice. The final practice is 90 seconds; pause the player for a longer presentation rehearsal. The retired HTML course remains archived in Git for its original evidence bindings and timing record; its public URL is excluded from deployment.

The corrected `course-video-v2` release supersedes the earlier video review copy and is separate from `customer-2026-09-15-audited`. The historical release, original seven attachments and existing latest-release destination stay unchanged. The old customer ZIP does not contain this later video. Current repository sources and the video release provide it.

## Your seven questions

| Question | Video chapters | What is explained and shown |
|---|---|---|
| What was tried and what works? | 00:00, 10:00, 13:00 | Original classifier, GB10 compatibility wrapper, short pretraining, full three-seed fine-tuning, strict evaluation and recorded replay. |
| How do training and inference work? | 06:00–10:00 | Three input views, normalization, 443 tokens, four Mamba blocks, masked reconstruction, labeled fine-tuning, validation selection and frozen inference. |
| What data goes in and comes out? | 02:00–10:00 | Both packet CSVs versus CICIoT2022 native flows; exact string-based JSON fields; six logits, class mapping and uncalibrated scores. |
| What was reproduced versus reported in the paper? | 13:00–17:00 | Every seed: 91.26%, 84.05%, 84.63%; mean 86.65%; unreproduced 97.50%, protocol differences and overlap/exposure limits. |
| What could a working IDS demo look like? | 17:00–21:00 | Actual recorded predictions and row 635: predicted RTSP Brute Force, labeled Other, 84.43% display score. Live capture and alert policy remain missing. |
| How could this map to an NPU/SmartNIC? | 25:00–27:00 | Proposed packet/flow preparation and classifier roles, actual export failure, model-only latency exclusions and target validation steps. |
| What remains missing? | 25:00–30:00 | Compatible live extraction, independent traffic validation, calibration/alerting, operator portability and inherited asset terms. A worked customer explanation follows practice. |

Setup, tests, downloads and file roles are taught at 10:00–13:00 and 21:00–25:00. The [single file walkthrough](../repository-walkthrough.md) remains the complete inventory. Use the [current support matrix](../support-matrix.md) for setup and platform results. The original customer PDF, PowerPoint, quickstart and release ZIP preserve the earlier experiment snapshot, including its then-current 54-test count and platform limitations. The video and current setup guide describe the subsequent work; the original experiment results are unchanged.

## Recheck or rebuild

Checking the committed source, captions, hashes and page uses Python 3.10+ without installing an AI model:

```bash
python3 tools/verify_course_video.py
python3 tools/build_video_page.py --check
python3 -m unittest discover -s tests -v
python3 tools/verify_package.py
```

For a complete decode/audio recheck, install an FFmpeg build with H.264, AAC and audio-analysis support:

```bash
python3 tools/verify_course_video.py --decode-output runs/video-recheck --ffmpeg ffmpeg --ffprobe ffprobe
```

Browser checking requires the existing `requirements/browser.txt` environment and Chromium:

```bash
python tools/verify_course_video.py --browser-output runs/video-browser-recheck --url https://buffbeefalo.github.io/netmambaplus-reproduction/video/
```

Choose a fresh output directory. Ordinary viewing does not require any Python, GPU, language model or paid account.

To regenerate narration and video, use Python 3.12, the packages in `requirements/video.txt`, DejaVu fonts and FFmpeg with libx264, libvpx-vp9, libopus and libass. Obtain `kokoro-v1.0.onnx` and `voices-v1.0.bin` from the [Kokoro ONNX model release](https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0). Keep the model/voice files outside Git; their exact hashes are in the media manifest. The measured build used the existing local speech environment and separate system rendering environment; the following commands describe those roles. A fresh installation on every platform has not been tested.

```bash
python tools/narrate_course_video.py --model /path/to/kokoro-v1.0.onnx --voices /path/to/voices-v1.0.bin --output runs/video-course/tts
python tools/build_course_video.py --ffmpeg ffmpeg
python tools/build_course_video.py --webm-only --ffmpeg ffmpeg
python tools/build_video_page.py
```

`narrate_course_video.py` resolves measured-value tokens and caches only matching narration/voice/audio hashes. `build_course_video.py` fits measured speech to exact chapter frame budgets, refuses accelerated or excessively stretched speech, renders teaching diagrams with Pillow, and encodes captions/countdowns with FFmpeg. Font/codec availability is an explicit build dependency. The final picture is checked against all 60 source layouts. Chromium is used for playback/viewport verification; the diagrams themselves are drawn with Pillow, a routine implementation choice distinct from the council’s proposed Chromium slide renderer.

After editing, review the affected lesson and evidence, regenerate the changed assets, and rerun checks. Do not update fingerprints simply to make a failure disappear. The video manifest binds narration, visuals, references, timing and downloadable bytes; the separate receipt below records actual checks. Source-controlled binaries make this checkout larger; downloads remain independently available through the video release.

## Entire-video audit and corrections

The 13 September audit reviewed all **60 scenes and 51 spoken passages**, including the paper/data explanation, model lifecycle, every measured result, repository roles, setup, demonstration and hardware limitations. It examined the actual encoded video as well as the script. The [structured audit record](../research/video-audit-v2.json) records identities, methods, outcomes and remaining uncertainty. Earlier v1 evidence remains available in [its published source revision](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/1b08fdcbd455c0bb4cede931cd01196385097c7b/docs/customer/video-verification.md).

The corrected video:

- Qualifies the stored-byte extraction history: the loader expects extracted bytes, but we have not independently verified the released flow extraction history.
- Defines tensors and checkpoints in plain language and makes the interval formula easier to say aloud.
- Draws a readable confusion matrix directly from the saved seed-0 counts, with an explicit seed label and row/column meanings.
- Uses the active video/page verification commands and explains the current portable-check and CUDA execution routes.
- Calls the final practice **90 seconds** consistently with its actual countdown.
- Corrects two measured within-sentence caption transitions that were 1.078 and 1.758 seconds late. Each correction is bound to the exact source audio hash and adjacent caption text; stale or invalid anchors are rejected.

The original paper accuracy of **97.50% remains unreproduced**. The three measured fine-tuning results still average **86.65%**. The fresh generalized GB10 build subsequently passed seven numerical cases, a complete classifier optimizer-update/reload/inference check and an exact replay of all 1,041 saved seed-0 predictions and 6,246 logits. Those are execution checks; they do not create a new independent test set. See the [portability evidence](../portability-evidence.json).

| Actual check on this video | Result and scope |
|---|---|
| Complete MP4 audiovisual decode | Passed; 1,800 seconds, 1920×1080, H.264/AAC, all nine embedded chapter starts. |
| Complete WebM audiovisual decode | Passed; browser encoding of the same lesson. |
| Audio analysis | −16.3 LUFS integrated, −1.0 dBFS true peak; all nine announced practice intervals detected, no unexplained long silence. |
| Every scene and chapter boundary | 69 extracted frames passed comparison against their expected picture and exact-time captions/countdowns; maximum full-frame RGB difference 2.143 against limit 3.0. Changed teaching layouts were also visually inspected. |
| Captions and source identity | 412 ordered cues; exact source, reference and download hashes checked. Timed words are unchanged by recognition output. |
| Independent speech/caption audit | All 51 spoken scenes transcribed from encoded audio. All 89 strong paired within-sentence anchors were within 0.5 seconds; no reliable boundary exceeded one second. Uncertain matches and endpoint-estimation limits remain in the receipt. |
| Browser playback | Local Chromium passed actual decoded audio/video, keyboard play and all nine chapter links, seeking near the end, captions, download equality and widths 320/390/768/1440. The same checks also passed anonymously on the deployed public page. |
| Regression tests | Source/media disagreement, truncation, missing audio, silence, altered captions, bad checksums, invalid pacing and stale/invalid caption anchors are rejected. |
| Full human listening and ±0.5-second caption acceptance | **Not performed / not established.** No machine check or AI review is reported as human acceptance. |

The speech engine produces separately measured sentence WAVs. Long sentences use proportional caption splits except for independently measured, audio-bound corrections. Speech recognition examines every spoken scene from the encoded audio, but can mishear terminology, numbers and boundaries. It is an error detector, not the authoritative transcript or proof of pronunciation quality. The transcript is generated from the reviewed narration source. A whole-program automated audit cannot establish every remaining human-quality criterion.

One attempted revised script exceeded its chapter’s measured speech budget. The builder refused accelerated narration; the setup prose was shortened and regenerated. The final pacing is within the permitted range without acceleration. A first local browser check found the temporary test server was stopped; after starting the server, a fresh browser run passed. These setup failures are separate from the final media result and remain in the audit history.

The new layouts are project-authored diagrams and tables. No paper page, stock photograph, song or external video was embedded. [Kokoro’s model card](https://huggingface.co/hexgrad/Kokoro-82M), [ONNX engine license](https://github.com/thewh1teagle/kokoro-onnx/blob/main/LICENSE) and [DejaVu font terms](https://github.com/dejavu-fonts/dejavu-fonts/blob/master/LICENSE) document the relevant components; model, engine and font binaries are not redistributed in the release. This does not settle inherited NetMamba+ source/data/checkpoint terms.

The shared course-content and local-video queues were inspected. They contained no NetMamba-specific entry; unrelated pending and failed work was left visible. The repository’s changed lesson sources and references received a direct content review before their fingerprints were refreshed.

## Council review


The two-seat review was **CONSENSUS / RATIFIED**, run `763a3a96-4155-4f0b-9dc4-873c1422b9dc`, Fable 5/high and Astra 6/max. Exact canonical decision SHA-256: `812de7b76131f1eb983a0d2082adefc553f01b9ea006ceffcb293e4c37d31ddd`. [Canonical decision and acceptance checks](../research/video-council-decision.json).

Implementation was performed directly under the user’s standing authorization. This review-only artifact has `delivery: null`; it was not broker `DELIVERED`. The council defined acceptance criteria before the final media existed. Its human-review requirements remain pending. The earlier static-course council and original experiment decisions remain historical and unchanged.

The subsequent final-quality review, run `d2eb183c-3f57-4c06-bb98-872ea1fd699e`, ended **ESCALATED / UNRATIFIED**, with no decision hash and no mutual final-media acceptance. The [exact result](../research/video-quality-review.json) is preserved unchanged (file SHA-256 `b019fbdc29bffb4823e76a745cd4ac2aad85ef7e1e481ebd48c8936b541a2713`). The frozen evidence omitted part of the narration and preceded the corrected CPU-suite result. The ordinary session has since reviewed the complete source and rechecked the corrected suite and actual media; this does not turn that review into consensus. Human full playback and detailed caption alignment remain open. Publication is explicitly a **mechanically checked review copy**, not a claim of final council or human acceptance. No replacement quality council was launched to bypass the stop.

A full-frame check exposed misleading arrows between the three simultaneous input views. Those arrows were removed, the row-grouping explanation became separate cards, and the classifier diagram now states the sequence precisely. The corrected video receives its own hashes and checks; earlier receipts stay historical.

Exact decision prose:

> Adopt a hybrid course video: one locally produced 1080p H.264/AAC MP4 lasting 1800 seconds ±1 second, using Kokoro ONNX narration, Chromium-rendered teaching visuals and ffmpeg encoding. Preserve chapter starts at 00:00, 02:00, 06:00, 10:00, 13:00, 17:00, 21:00, 25:00 and 27:00, finishing at 30:00. Target approximately 27–29 minutes of narrated explanation, worked examples and answers. Allow at most three minutes of justified, announced practice—a ceiling, not a quota—with visible prompts, timers and subsequent answers; invite learners to pause playback for longer work. Fit speech through script revision against measured synthesized durations, without runtime padding or accelerated narration. Deliver synchronized WebVTT captions, an accessible timestamped transcript, chapter navigation and a public watch/download page through a separate versioned release. The existing HTML and narration probe do not establish completion of the video request. Final acceptance requires the source, encoded-media, accessibility and publication checks below.

## Source-to-video crosswalk

Every scene is present below. The [full transcript](demo/video/transcript.md) gives its narration, screen text and evidence links. The file walkthrough explains every individual repository file and download.

| Time | Scene | Visible treatment | Evidence keys |
|---|---|---|---|
| 00:00–00:33 | purpose-01 | NetMamba+ / A measured reproduction attempt | answers, results |
| 00:33–01:04 | purpose-02 | A classifier is one part of an IDS | comparison |
| 01:04–01:31 | purpose-03 | What the plus means | comparison |
| 01:31–01:39 | purpose-04 | First decision | answers, results, comparison |
| 01:39–01:47 | purpose-05 | Your turn · 8 seconds | answers, results, comparison |
| 01:47–02:00 | purpose-06 | Keep the system boundary visible | hardware |
| 02:00–02:41 | inputs-01 | The three starting files | csv, comparison |
| 02:41–03:26 | inputs-02 | What one CSV row contains | csv |
| 03:26–04:01 | inputs-03 | Why five neighboring rows are insufficient | comparison |
| 04:01–04:41 | inputs-04 | The data actually used | native |
| 04:41–05:16 | inputs-05 | Native input is a defined contract | native, contract |
| 05:16–05:29 | inputs-06 | Input decision | csv, comparison, native |
| 05:29–05:41 | inputs-07 | Your turn · 12 seconds | csv, comparison, native |
| 05:41–06:00 | inputs-08 | Answer: establish compatibility first | comparison |
| 06:00–06:39 | lifecycle-01 | Three views become tensors | lesson |
| 06:39–07:19 | lifecycle-02 | Normalization changes the numerical scale | lesson |
| 07:19–08:01 | lifecycle-03 | The classifier reads 443 tokens | lesson, comparison |
| 08:01–08:48 | lifecycle-04 | Two learning stages, different targets | lesson, transfer |
| 08:48–09:25 | lifecycle-05 | Inference freezes the learned classifier | runbook, contract |
| 09:25–09:34 | lifecycle-06 | Trace the lifecycle | lesson, comparison, transfer |
| 09:34–09:46 | lifecycle-07 | Your turn · 12 seconds | lesson, comparison, transfer |
| 09:46–10:00 | lifecycle-08 | Answer: separate learning from measurement | lesson |
| 10:00–10:29 | repository-01 | Original model, checked execution wrapper | comparison, config |
| 10:29–11:06 | repository-02 | Follow the main entry points | comparison |
| 11:06–11:48 | repository-03 | Find the recipe, record and explanation | walkthrough |
| 11:48–12:22 | repository-04 | A manifest is a lab notebook | contract, runbook |
| 12:22–12:34 | repository-05 | Repository decision | comparison, config, walkthrough |
| 12:34–12:44 | repository-06 | Your turn · 10 seconds | comparison, config, walkthrough |
| 12:44–13:00 | repository-07 | Answer: explain the actual changes | comparison |
| 13:00–13:40 | measurements-01 | Three complete fine-tuning runs | results |
| 13:40–14:14 | measurements-02 | Show every seed, not only the best one | results |
| 14:14–14:55 | measurements-03 | Understand the metrics | results, prediction |
| 14:55–15:38 | measurements-04 | The paper’s result was not reproduced | results, comparison |
| 15:38–16:12 | measurements-05 | Repeatability has practical limits | native, verification |
| 16:12–16:33 | measurements-06 | Choose the customer sentence | results, comparison, native |
| 16:33–16:45 | measurements-07 | Your turn · 12 seconds | results, comparison, native |
| 16:45–17:00 | measurements-08 | Answer: retain the conditions | results |
| 17:00–17:36 | demo-01 | What the working demo actually does | prediction, verification |
| 17:36–18:17 | demo-02 | Six categories are not universal attack coverage | prediction, hardware |
| 18:17–18:59 | demo-03 | Read row 635 before judging it | prediction |
| 18:59–19:39 | demo-04 | A confident-looking error | prediction |
| 19:39–20:00 | demo-05 | Try the explanation yourself | prediction, verification, hardware |
| 20:00–20:18 | demo-06 | Your turn · 18 seconds | prediction, verification, hardware |
| 20:18–21:00 | demo-07 | A defensible explanation | prediction, runbook |
| 21:00–21:33 | operate-01 | Choose the smallest useful setup | quickstart, support |
| 21:33–22:04 | operate-02 | Run the evidence and video checks | quickstart, verification, support |
| 22:04–22:51 | operate-03 | What verification proves | verification |
| 22:51–23:36 | operate-04 | The route for new model execution | runbook, support |
| 23:36–24:17 | operate-05 | Find every download and its purpose | walkthrough |
| 24:17–24:31 | operate-06 | Choose a verification route | quickstart, verification, runbook |
| 24:31–24:41 | operate-07 | Your turn · 10 seconds | quickstart, verification, runbook |
| 24:41–25:00 | operate-08 | Answer: use the evidence route | quickstart, support |
| 25:00–25:36 | future-01 | A proposed capture-to-alert system | hardware |
| 25:36–26:22 | future-02 | Portability must be measured | export, benchmark, comparison |
| 26:22–26:32 | future-03 | Hardware decision | hardware, export, benchmark |
| 26:32–26:40 | future-04 | Your turn · 8 seconds | hardware, export, benchmark |
| 26:40–27:00 | future-05 | Next work has explicit acceptance criteria | hardware |
| 27:00–27:33 | teach-back-01 | Your turn: explain the project | answers |
| 27:33–29:03 | teach-back-02 | Customer teach-back · 90 seconds | answers |
| 29:03–30:00 | teach-back-03 | Review, correct, then present | answers |

## Publication record

The [current audit JSON](../research/video-audit-v2.json) binds the checked MP4, source, captions, browser page and release downloads to exact hashes. All six v2 attachments and all seven original attachments were anonymously downloaded and hash-checked. Public playback and the retired-course 404 check passed. The [six-platform workflow](https://github.com/buffbeefalo/netmambaplus-reproduction/actions/runs/34748276261) passed all 103 tests in each job at the immutable media-release revision `89dd26909eaaa2948212e0d6c543ea30eb0b0885`. The full structured record includes all 51 recognition results and the actual local audit helper sources for inspection; it is a large machine-readable companion to this page. The original `customer-2026-09-15-audited` release and its seven files stay unchanged; its historical ZIP does not contain the later 30-minute course or portability additions. The old `/course/` site is excluded from deployment. The active watch page presents one lesson.

This remains a mechanically checked **review copy** with the human listening/caption gates stated above. Earlier council outcomes and media receipts are retained as history; later fixes do not rewrite them.
