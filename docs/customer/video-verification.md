# The NetMamba+ course video

[Watch the video](https://buffbeefalo.github.io/netmambaplus-reproduction/video/) · [Download MP4](https://github.com/buffbeefalo/netmambaplus-reproduction/releases/download/course-video-v1/NetMambaPlus-30-minute-course.mp4) · [Versioned release](https://github.com/buffbeefalo/netmambaplus-reproduction/releases/tag/course-video-v1) · [Full transcript](demo/video/transcript.md)

This is the actual narrated course requested after the interactive HTML lesson. It is **30:00, 1080p**, with 51 spoken scenes, nine announced practice intervals, chapter navigation, captions and a reflowing transcript. There is one continuous lesson and one main MP4 download. An internal VP9/Opus playback copy serves browsers without MP4 codecs; it is the same video, not another lesson. The voice is synthesized locally with Kokoro ONNX; no online narration service or cloned customer voice was used.

The course explains existing measured experiments. Playing it does not perform training, capture traffic, or establish additional accuracy. The measured mean remains **86.65%**, compared with the paper’s unreproduced **97.50%**. A complete human listening/watch-through has **not** been performed. Automated media checks and source review do not establish that human gate, learner mastery, or complete council acceptance.

## Watch, download or present

Use this as a handoff to the person who will explain the repository onward. Watch the complete route, practice the explanation aloud, and use the evidence links when the next person asks how a claim was established. The lesson explains every part’s role and the execution process; the file walkthrough supplies the individual inventory rather than reading every filename aloud.

Open **Watch the video**, press Play and use the chapter links to seek. Download the MP4 for a meeting without internet access. Captions are already in the picture; the optional player text track and separate VTT/SRT files support other workflows. The complete transcript is visible below the player and reflows on a phone. Every substantive scene links to evidence.

The video allocates 27:00 to spoken explanation and worked answers and 3:00 of announced practice. The final practice is 90 seconds; pause the player for a longer presentation rehearsal. The retired HTML course remains archived in Git for its original evidence bindings and timing record; its public URL is excluded from deployment.

The new `course-video-v1` release is separate from `customer-2026-09-15-audited`. The historical release, original seven attachments and existing latest-release destination stay unchanged. The old customer ZIP does not contain this later video. Current repository sources and the video release provide it.

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

Setup, tests, downloads and file roles are taught at 10:00–13:00 and 21:00–25:00. The [single file walkthrough](../repository-walkthrough.md) remains the complete inventory. The narrated setup instructions preserve the historical 54-test release and 71-test HTML-course snapshot; the current suite adds seven video checks for **78 tests**.

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

## Media review, limitations and provenance

The MP4 was completely decoded, probed for both streams and chapter offsets, and measured for long silences and audio levels. All 60 scene midpoints and nine chapter-start samples were extracted from the corrected MP4. Each passed comparison both above the captions and across the complete frame, including captions, footers and practice countdowns. Expected caption overlays were rendered at the exact extracted frame timestamp; the maximum full-frame mean absolute RGB difference was 2.137 against a limit of 3.0. Negative tests use shortened, missing-audio and silent versions of the encoded file; the CPU suite also rejects invalid caption timing and checksum changes.

Local speech recognition processed the entire encoded MP4 as a supplementary check. Its text contains recognition errors and omitted phrases; it is not the authoritative transcript or a human pronunciation review. The provided transcript comes from the reviewed narration source. Captions use measured sentence-wave timings, with proportional within-sentence breaks. Complete human listening, pronunciation review and the council’s ±0.5-second distributed caption-alignment gate remain pending; no automated decoding result is substituted for them.

All new teaching layouts are project-authored diagrams and tables, plus the project’s existing measured confusion-matrix figure. No paper page, stock photograph, song or external video was embedded. The [Kokoro model card](https://huggingface.co/hexgrad/Kokoro-82M) identifies Apache-2.0 weights and permits deployment; the [ONNX engine](https://github.com/thewh1teagle/kokoro-onnx/blob/main/LICENSE) is MIT licensed. [DejaVu’s font terms](https://github.com/dejavu-fonts/dejavu-fonts/blob/master/LICENSE) permit use; font/model/engine binaries are not redistributed in the release. This review does not settle the separately documented inherited NetMamba+ source, data and checkpoint terms.

The pending course-content and video-refresh queues were inspected. No NetMamba-specific fleet entry was present; unrelated pending/failed work remains visible and unchanged. This is a repository-based video build, not a claim that the shared fleet video worker completed or that other courses are current.

## Council review

The two-seat review was **CONSENSUS / RATIFIED**, run `763a3a96-4155-4f0b-9dc4-873c1422b9dc`, Fable 5/high and Astra 6/max. Exact canonical decision SHA-256: `812de7b76131f1eb983a0d2082adefc553f01b9ea006ceffcb293e4c37d31ddd`. [Canonical decision and acceptance checks](../research/video-council-decision.json).

Implementation was performed directly under the user’s standing authorization. This review-only artifact has `delivery: null`; it was not broker `DELIVERED`. The council defined acceptance criteria before the final media existed. Its human-review requirements remain pending. The earlier static-course council and original experiment decisions remain historical and unchanged.

The subsequent final-quality review, run `d2eb183c-3f57-4c06-bb98-872ea1fd699e`, ended **ESCALATED / UNRATIFIED**, with no decision hash and no mutual final-media acceptance. The [exact result](../research/video-quality-review.json) is preserved unchanged (file SHA-256 `b019fbdc29bffb4823e76a745cd4ac2aad85ef7e1e481ebd48c8936b541a2713`). The frozen evidence omitted part of the narration and preceded the corrected CPU-suite result. The ordinary session has since reviewed the complete source and rechecked the corrected suite and actual media; this does not turn that review into consensus. Human full playback and detailed caption alignment remain open. Publication is explicitly a **mechanically checked review copy**, not a claim of final council or human acceptance. No replacement quality council was launched to bypass the stop.

A full-frame check exposed misleading arrows between the three simultaneous input views. Those arrows were removed, the row-grouping explanation became separate cards, and the classifier diagram now states the sequence precisely. The corrected video receives its own hashes and checks; earlier receipts stay historical.

Exact decision prose:

> Adopt a hybrid course video: one locally produced 1080p H.264/AAC MP4 lasting 1800 seconds ±1 second, using Kokoro ONNX narration, Chromium-rendered teaching visuals and ffmpeg encoding. Preserve chapter starts at 00:00, 02:00, 06:00, 10:00, 13:00, 17:00, 21:00, 25:00 and 27:00, finishing at 30:00. Target approximately 27–29 minutes of narrated explanation, worked examples and answers. Allow at most three minutes of justified, announced practice—a ceiling, not a quota—with visible prompts, timers and subsequent answers; invite learners to pause playback for longer work. Fit speech through script revision against measured synthesized durations, without runtime padding or accelerated narration. Deliver synchronized WebVTT captions, an accessible timestamped transcript, chapter navigation and a public watch/download page through a separate versioned release. The existing HTML and narration probe do not establish completion of the video request. Final acceptance requires the source, encoded-media, accessibility and publication checks below.

## Source-to-video crosswalk

The manifest contains every narration paragraph, visible teaching bullet, evidence reference and exact scene interval. This table gives the corresponding final encoded-video schedule.

| Time | Scene | Visible treatment | Evidence keys |
|---|---|---|---|
| 00:00–00:33 | purpose-01: NetMamba+ / A measured reproduction attempt | title | answers, results |
| 00:33–01:04 | purpose-02: A classifier is one part of an IDS | flow | comparison |
| 01:04–01:31 | purpose-03: What the plus means | cards | comparison |
| 01:31–01:39 | purpose-04: First decision | question | answers, results, comparison |
| 01:39–01:47 | purpose-05: Your turn · 8 seconds | pause | answers, results, comparison |
| 01:47–02:00 | purpose-06: Keep the system boundary visible | answer | hardware |
| 02:00–02:41 | inputs-01: The three starting files | cards | csv, comparison |
| 02:41–03:26 | inputs-02: What one CSV row contains | cards | csv |
| 03:26–04:01 | inputs-03: Why five neighboring rows are insufficient | cards | comparison |
| 04:01–04:41 | inputs-04: The data actually used | cards | native |
| 04:41–05:16 | inputs-05: Native input is a defined contract | code | native, contract |
| 05:16–05:29 | inputs-06: Input decision | question | csv, comparison, native |
| 05:29–05:41 | inputs-07: Your turn · 12 seconds | pause | csv, comparison, native |
| 05:41–06:00 | inputs-08: Answer: establish compatibility first | answer | comparison |
| 06:00–06:38 | lifecycle-01: Three views become tensors | views | lesson |
| 06:38–07:19 | lifecycle-02: Normalization changes the numerical scale | cards | lesson |
| 07:19–08:02 | lifecycle-03: The classifier reads 443 tokens | flow | lesson, comparison |
| 08:02–08:46 | lifecycle-04: Two learning stages, different targets | cards | lesson, transfer |
| 08:46–09:24 | lifecycle-05: Inference freezes the learned classifier | cards | runbook, contract |
| 09:24–09:34 | lifecycle-06: Trace the lifecycle | question | lesson, comparison, transfer |
| 09:34–09:46 | lifecycle-07: Your turn · 12 seconds | pause | lesson, comparison, transfer |
| 09:46–10:00 | lifecycle-08: Answer: separate learning from measurement | answer | lesson |
| 10:00–10:29 | repository-01: Original model, checked execution wrapper | cards | comparison, config |
| 10:29–11:06 | repository-02: Follow the main entry points | code | comparison |
| 11:06–11:48 | repository-03: Find the recipe, record and explanation | cards | walkthrough |
| 11:48–12:22 | repository-04: A manifest is a lab notebook | cards | contract, runbook |
| 12:22–12:34 | repository-05: Repository decision | question | comparison, config, walkthrough |
| 12:34–12:44 | repository-06: Your turn · 10 seconds | pause | comparison, config, walkthrough |
| 12:44–13:00 | repository-07: Answer: explain the actual changes | answer | comparison |
| 13:00–13:40 | measurements-01: Three complete fine-tuning runs | cards | results |
| 13:40–14:14 | measurements-02: Show every seed, not only the best one | results | results |
| 14:14–14:55 | measurements-03: Understand the metrics | matrix | results |
| 14:55–15:38 | measurements-04: The paper’s result was not reproduced | comparison | results, comparison |
| 15:38–16:12 | measurements-05: Repeatability has practical limits | cards | native, verification |
| 16:12–16:33 | measurements-06: Choose the customer sentence | question | results, comparison, native |
| 16:33–16:45 | measurements-07: Your turn · 12 seconds | pause | results, comparison, native |
| 16:45–17:00 | measurements-08: Answer: retain the conditions | answer | results |
| 17:00–17:36 | demo-01: What the working demo actually does | cards | prediction, verification |
| 17:36–18:17 | demo-02: Six categories are not universal attack coverage | cards | prediction, hardware |
| 18:17–18:59 | demo-03: Read row 635 before judging it | prediction-hidden | prediction |
| 18:59–19:39 | demo-04: A confident-looking error | prediction-reveal | prediction |
| 19:39–20:00 | demo-05: Try the explanation yourself | question | prediction, verification, hardware |
| 20:00–20:18 | demo-06: Your turn · 18 seconds | pause | prediction, verification, hardware |
| 20:18–21:00 | demo-07: A defensible explanation | answer | prediction, runbook |
| 21:00–21:35 | operate-01: Choose the smallest useful setup | cards | quickstart |
| 21:35–22:12 | operate-02: Run the CPU checks | code | quickstart, verification |
| 22:12–22:58 | operate-03: What verification proves | cards | verification |
| 22:58–23:38 | operate-04: The route for new model execution | flow | runbook |
| 23:38–24:18 | operate-05: Find every download and its purpose | cards | walkthrough |
| 24:18–24:32 | operate-06: Choose a verification route | question | quickstart, verification, runbook |
| 24:32–24:42 | operate-07: Your turn · 10 seconds | pause | quickstart, verification, runbook |
| 24:42–25:00 | operate-08: Answer: use the evidence route | answer | quickstart |
| 25:00–25:36 | future-01: A proposed capture-to-alert system | flow | hardware |
| 25:36–26:22 | future-02: Portability must be measured | cards | export, benchmark, comparison |
| 26:22–26:32 | future-03: Hardware decision | question | hardware, export, benchmark |
| 26:32–26:40 | future-04: Your turn · 8 seconds | pause | hardware, export, benchmark |
| 26:40–27:00 | future-05: Next work has explicit acceptance criteria | answer | hardware |
| 27:00–27:33 | teach-back-01: Your turn: explain the project | question | answers |
| 27:33–29:03 | teach-back-02: Customer teach-back · 90 seconds | pause | answers |
| 29:03–30:00 | teach-back-03: Review, correct, then present | answer | answers |

## Actual check and publication receipt

<!-- video-check-record -->
```json
{
  "schema_version": 1,
  "status": "mechanically_checked_review_copy_publication_pending",
  "completed_at": "2026-09-13T07:42:52.539556+00:00",
  "source_sha256": "4b1ac47ed54ceff5327b460dc366859de22c6c414f1edbe35827514c21f77b02",
  "media_manifest_sha256": "ad9d843f9defd331b93dd5e03b9774d51f052107b36bbd026912955676863474",
  "artifacts": {
    "NetMambaPlus-30-minute-course.mp4": {
      "bytes": 37861771,
      "sha256": "1ff19bf545fe14a4bf1f61112a1fdfd7dc107a36ca4c91a749c4f6dfaea8082b"
    },
    "captions.srt": {
      "bytes": 38036,
      "sha256": "1f7c17cd65086a7939945f70db1983182647cdaf6642c98ad95f2f9475a2e918"
    },
    "captions.vtt": {
      "bytes": 36500,
      "sha256": "5cf0504c070d40aede44c3612f7879c4deca3784fafe3001f090297a83e8047c"
    },
    "transcript.md": {
      "bytes": 47539,
      "sha256": "9dab55f2849a0371ef1f2fc7c6b511809c814d96dbcc4b716029ac32247df560"
    },
    "chapters.json": {
      "bytes": 1087,
      "sha256": "6ad2199cf458ff51499254cab4fc6ef9be4b57e7b24508f3c2379547e501764b"
    },
    "poster.png": {
      "bytes": 56780,
      "sha256": "a8ca1a7ffceccbb0e36650113dd579361dd5733ea1649da7a772a120d0b0311a"
    },
    "NetMambaPlus-30-minute-course.webm": {
      "bytes": 37049922,
      "sha256": "595b4521549956d06af104022683e3ebc0a070bdc358156687bcc04e9fab968d"
    }
  },
  "encoded_mp4": {
    "seconds": 1800.0,
    "streams": {
      "video": {
        "index": 0,
        "codec_name": "h264",
        "codec_long_name": "H.264 / AVC / MPEG-4 AVC / MPEG-4 part 10",
        "profile": "High",
        "codec_type": "video",
        "codec_tag_string": "avc1",
        "codec_tag": "0x31637661",
        "width": 1920,
        "height": 1080,
        "coded_width": 1920,
        "coded_height": 1080,
        "closed_captions": 0,
        "film_grain": 0,
        "has_b_frames": 2,
        "pix_fmt": "yuv420p",
        "level": 40,
        "chroma_location": "left",
        "field_order": "progressive",
        "refs": 1,
        "is_avc": "true",
        "nal_length_size": "4",
        "id": "0x1",
        "r_frame_rate": "10/1",
        "avg_frame_rate": "10/1",
        "time_base": "1/10240",
        "start_pts": 0,
        "start_time": "0.000000",
        "duration_ts": 18432000,
        "duration": "1800.000000",
        "bit_rate": "75131",
        "bits_per_raw_sample": "8",
        "nb_frames": "18000",
        "extradata_size": 47,
        "disposition": {
          "default": 1,
          "dub": 0,
          "original": 0,
          "comment": 0,
          "lyrics": 0,
          "karaoke": 0,
          "forced": 0,
          "hearing_impaired": 0,
          "visual_impaired": 0,
          "clean_effects": 0,
          "attached_pic": 0,
          "timed_thumbnails": 0,
          "non_diegetic": 0,
          "captions": 0,
          "descriptions": 0,
          "metadata": 0,
          "dependent": 0,
          "still_image": 0
        },
        "tags": {
          "language": "und",
          "handler_name": "VideoHandler",
          "vendor_id": "[0][0][0][0]",
          "encoder": "Lavc61.3.100 libx264"
        }
      },
      "audio": {
        "index": 1,
        "codec_name": "aac",
        "codec_long_name": "AAC (Advanced Audio Coding)",
        "profile": "LC",
        "codec_type": "audio",
        "codec_tag_string": "mp4a",
        "codec_tag": "0x6134706d",
        "sample_fmt": "fltp",
        "sample_rate": "48000",
        "channels": 1,
        "channel_layout": "mono",
        "bits_per_sample": 0,
        "initial_padding": 0,
        "id": "0x2",
        "r_frame_rate": "0/0",
        "avg_frame_rate": "0/0",
        "time_base": "1/48000",
        "start_pts": 0,
        "start_time": "0.000000",
        "duration_ts": 86400000,
        "duration": "1800.000000",
        "bit_rate": "89431",
        "nb_frames": "84376",
        "extradata_size": 5,
        "disposition": {
          "default": 1,
          "dub": 0,
          "original": 0,
          "comment": 0,
          "lyrics": 0,
          "karaoke": 0,
          "forced": 0,
          "hearing_impaired": 0,
          "visual_impaired": 0,
          "clean_effects": 0,
          "attached_pic": 0,
          "timed_thumbnails": 0,
          "non_diegetic": 0,
          "captions": 0,
          "descriptions": 0,
          "metadata": 0,
          "dependent": 0,
          "still_image": 0
        },
        "tags": {
          "language": "und",
          "handler_name": "SoundHandler",
          "vendor_id": "[0][0][0][0]"
        }
      }
    },
    "chapter_starts": [
      0.0,
      120.0,
      360.0,
      600.0,
      780.0,
      1020.0,
      1260.0,
      1500.0,
      1620.0
    ],
    "silence": {
      "intervals": [
        [
          98.967687,
          107.131917
        ],
        [
          329.430208,
          341.575187
        ],
        [
          574.058854,
          586.272542
        ],
        [
          754.026625,
          764.137521
        ],
        [
          993.135958,
          1005.236104
        ],
        [
          1200.836208,
          1218.911958
        ],
        [
          1472.229854,
          1482.336854
        ],
        [
          1592.213458,
          1600.331917
        ],
        [
          1653.367521,
          1743.512292
        ]
      ],
      "total_seconds": 181.17991900000007,
      "tolerance_seconds": 1.0,
      "parameters": {
        "threshold_db": -45,
        "minimum_seconds": 3
      }
    },
    "audio": {
      "integrated_lufs": -16.3,
      "true_peak_dbfs": -1.1,
      "rms_dbfs": -16.859345
    },
    "status": "passed",
    "completed_at": "2026-09-13T07:37:03.983662+00:00",
    "mp4_sha256": "1ff19bf545fe14a4bf1f61112a1fdfd7dc107a36ca4c91a749c4f6dfaea8082b",
    "command": [
      "/home/nvidia/learn/_video/bin/ffmpeg",
      "-hide_banner",
      "-nostats",
      "-xerror",
      "-i",
      "/home/nvidia/netmambaplus-reproduction/docs/customer/demo/video/NetMambaPlus-30-minute-course.mp4",
      "-map",
      "0:v:0",
      "-map",
      "0:a:0",
      "-af",
      "silencedetect=noise=-45dB:d=3,ebur128=peak=true:framelog=verbose,astats=reset=0",
      "-f",
      "null",
      "-"
    ],
    "decode_exit_code": 0,
    "decode_log_sha256": "10de723ed71cc30be84a7d90b5b485fda232e570a50700e2b2f1e4e50033304f",
    "human_full_playback_review": "pending; automated decode is not a listening review"
  },
  "browser_playback_copy": {
    "file": "NetMambaPlus-30-minute-course.webm",
    "sha256": "595b4521549956d06af104022683e3ebc0a070bdc358156687bcc04e9fab968d",
    "source_mp4_sha256": "1ff19bf545fe14a4bf1f61112a1fdfd7dc107a36ca4c91a749c4f6dfaea8082b",
    "seconds": 1800.008,
    "chapter_starts": [
      0.0,
      120.0,
      360.0,
      600.0,
      780.0,
      1020.0,
      1260.0,
      1500.0,
      1620.0
    ],
    "full_decode_exit_code": 0,
    "full_decode_log_sha256": "310e7cfc411b605fbe91499bf11aca5ca2761c4419d64848759d587ab36c2c87",
    "scope": "VP9/Opus internal browser encoding of the same single course."
  },
  "image_checks": {
    "status": "passed",
    "completed_at": "2026-09-13T07:40:06.320782+00:00",
    "mp4_sha256": "1ff19bf545fe14a4bf1f61112a1fdfd7dc107a36ca4c91a749c4f6dfaea8082b",
    "ass_sha256": "93abb3c46d7012d34f0091148e99ebf4812c906e3530cf73203afffba327a8d8",
    "source_manifest_sha256_at_completion": "ad9d843f9defd331b93dd5e03b9774d51f052107b36bbd026912955676863474",
    "scene_count": 60,
    "chapter_count": 9,
    "sample_count": 69,
    "frame_time_rule": "ceil(requested_scene_midpoint * 10) / 10; chapter start + 0.2",
    "timestamp_evidence": "ffmpeg showinfo first-frame PTS in both extraction and overlay render",
    "comparison": "RGB mean absolute difference over upper 850 px against uncaptioned scene PNG; bottom 230 px and full frame against PNG with exact-time ASS captions/countdown",
    "limit_mean_absolute_rgb_difference": 3.0,
    "max_mean_absolute_rgb_difference": {
      "upper_850px_vs_source": 2.161059640522876,
      "bottom_230px_vs_overlay": 2.0980042270531403,
      "full_frame_vs_overlay": 2.136776298868313
    },
    "source_or_media_drift": [],
    "failures": [],
    "human_full_playback_review": "not performed; this is deterministic frame/audio verification",
    "receipt_sha256": "cc01e4020801de726a5735ca8b847595bf3437715860d488fe0395685d28b581",
    "samples": [
      {
        "name": "scene-purpose-01",
        "extracted_frame_timestamp": "16.7",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.0776981209150325,
          "bottom_230px_vs_overlay": 2.0631634963768115,
          "full_frame_vs_overlay": 2.0746027842078187
        },
        "within_limit": true,
        "actual_png_sha256": "8cd9dc6b587a5619b64196b61fbd42dcb06d80e73964b1fb7e1fb26137e5fb22",
        "expected_png_sha256": "e904c61e8c67d232f3e00086ae8003afc37798e898c94f6a40740447ec0de006"
      },
      {
        "name": "scene-purpose-02",
        "extracted_frame_timestamp": "49",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.0956156045751633,
          "bottom_230px_vs_overlay": 2.0559699577294688,
          "full_frame_vs_overlay": 2.087172550154321
        },
        "within_limit": true,
        "actual_png_sha256": "f3604dd36c5f036bde81cf534f6bbcaf2d121989cdff19868c32dc4f4503590b",
        "expected_png_sha256": "7bacb8734b35785d6b51cbc2f3713ae7e942bededdaff956577bc8c67c799cbf"
      },
      {
        "name": "scene-purpose-03",
        "extracted_frame_timestamp": "78",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.059811683006536,
          "bottom_230px_vs_overlay": 2.064301781400966,
          "full_frame_vs_overlay": 2.060767907664609
        },
        "within_limit": true,
        "actual_png_sha256": "b15a78425072c259c8d5b7ac6703fbd0188cb13dba35da820fab201b5e8292e9",
        "expected_png_sha256": "747734356915e3a2e8835d48016b5e338d74066d3d61175a3e6f0e3f71418068"
      },
      {
        "name": "scene-purpose-04",
        "extracted_frame_timestamp": "95.3",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.039936070261438,
          "bottom_230px_vs_overlay": 2.048454106280193,
          "full_frame_vs_overlay": 2.0417500964506172
        },
        "within_limit": true,
        "actual_png_sha256": "7e57e537d76904c5203332bc24dc4a9313cca17148b02732a2c4e64afa67b6f8",
        "expected_png_sha256": "03e40d1d9f8e638dc429cb11b76aa150d00fbef4a9cf1fdb3f11df228925af6c"
      },
      {
        "name": "scene-purpose-05",
        "extracted_frame_timestamp": "103.1",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.057544117647059,
          "bottom_230px_vs_overlay": 2.0862182971014493,
          "full_frame_vs_overlay": 2.0636506558641976
        },
        "within_limit": true,
        "actual_png_sha256": "936ac41a33e8bc396ba1687f626f67446ad9e316a045b40546165f3d689380f4",
        "expected_png_sha256": "b0f16b26051dd0abb1c5b758f11275c6c8e63bb05e4c80860a54dcdbd3b83af2"
      },
      {
        "name": "scene-purpose-06",
        "extracted_frame_timestamp": "113.6",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.0650420751633987,
          "bottom_230px_vs_overlay": 2.0662281099033817,
          "full_frame_vs_overlay": 2.065294656635803
        },
        "within_limit": true,
        "actual_png_sha256": "48faa7e114a44b70c3dbabd17ed85a60f4180639685b3ffca50f0075dd3018e1",
        "expected_png_sha256": "ed462cdde5fc7d685614682025ae1e148d4fdbcec4d3d49527f613a9901527d1"
      },
      {
        "name": "scene-inputs-01",
        "extracted_frame_timestamp": "140.6",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.068034722222222,
          "bottom_230px_vs_overlay": 2.0403796799516907,
          "full_frame_vs_overlay": 2.062145222479424
        },
        "within_limit": true,
        "actual_png_sha256": "6cf18a4a952a254dc44b0dc4eabe0590ac447f2f03f1afd6f407b19ff84f1b22",
        "expected_png_sha256": "3ca89d7c2bd5a417dad326f69749b83c4c32bfdb00a6ba15a721c98ae1fb1fd0"
      },
      {
        "name": "scene-inputs-02",
        "extracted_frame_timestamp": "184",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.0708253676470587,
          "bottom_230px_vs_overlay": 2.0764696557971014,
          "full_frame_vs_overlay": 2.0720273919753085
        },
        "within_limit": true,
        "actual_png_sha256": "8868f37ccd5494813bd09d853db1fff1fd252edc12267a63190f92250d12536b",
        "expected_png_sha256": "ad9f6de1d951eafd5b25c72804ac48b6c4f384d16a1f60872f5f4a2c5e3c895e"
      },
      {
        "name": "scene-inputs-03",
        "extracted_frame_timestamp": "224.2",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.085,
          "bottom_230px_vs_overlay": 2.0705147946859905,
          "full_frame_vs_overlay": 2.0819151877572017
        },
        "within_limit": true,
        "actual_png_sha256": "2a0fb61adc0f6e6aec25431ea9ece2cab618bff645fc21955fc154528735022d",
        "expected_png_sha256": "8d546a47a49c3517212b0298fc973eb12bc358eb3dd26f2419c8d5de1424ef61"
      },
      {
        "name": "scene-inputs-04",
        "extracted_frame_timestamp": "261.4",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.0622377450980394,
          "bottom_230px_vs_overlay": 2.0397629830917876,
          "full_frame_vs_overlay": 2.0574514531893002
        },
        "within_limit": true,
        "actual_png_sha256": "7b4a91539dc764ab28eb2bd06f69de2330f10a57e7e77122bd81a4d1ee852f21",
        "expected_png_sha256": "3cece08bb6c2240390641627bccca659af802325e5620a693bf927a8f5635847"
      },
      {
        "name": "scene-inputs-05",
        "extracted_frame_timestamp": "298.9",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 1.9845537173202612,
          "bottom_230px_vs_overlay": 2.075354770531401,
          "full_frame_vs_overlay": 2.0038909786522634
        },
        "within_limit": true,
        "actual_png_sha256": "413f9510f63344324054c935f6d3e6a9dfb669580dfcf69e89bd2b2a4af01ad1",
        "expected_png_sha256": "f90ed7ad9d16dfbf5aeb4e419a23504a8f7f1ecb1a82bb1440573ca4af290079"
      },
      {
        "name": "scene-inputs-06",
        "extracted_frame_timestamp": "323.1",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.041370098039216,
          "bottom_230px_vs_overlay": 2.053476751207729,
          "full_frame_vs_overlay": 2.043948366769547
        },
        "within_limit": true,
        "actual_png_sha256": "94dce0d64cb7d3c679e742b2f8ba0146cf49eeecf7feeb5a65e2731697000275",
        "expected_png_sha256": "4cd5a4ecc9887a8ef35d95163e3011bc7d856f33e52d9d2d4f68c891a0f6ccb3"
      },
      {
        "name": "scene-inputs-07",
        "extracted_frame_timestamp": "335.5",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.073953839869281,
          "bottom_230px_vs_overlay": 2.091010718599034,
          "full_frame_vs_overlay": 2.077586323302469
        },
        "within_limit": true,
        "actual_png_sha256": "471b34859ff41c18f24ce956d0a2776ada5f1220710ba75867dabe530c22791e",
        "expected_png_sha256": "3b447ed88050d8f69c3ad2c6805bb8d649b1b84e521865de434ba1c8a0d24920"
      },
      {
        "name": "scene-inputs-08",
        "extracted_frame_timestamp": "350.8",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.062473039215686,
          "bottom_230px_vs_overlay": 2.0821588164251206,
          "full_frame_vs_overlay": 2.0666653806584363
        },
        "within_limit": true,
        "actual_png_sha256": "e6eff114bd90866dfae971cc6d4f09dd51bbbc85e6e87bb00616b45b41866fdc",
        "expected_png_sha256": "f429af44f74bbd7767d72d2e8544158d1381ddbd383ef4de935765a03a67db7d"
      },
      {
        "name": "scene-lifecycle-01",
        "extracted_frame_timestamp": "379.1",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.083593545751634,
          "bottom_230px_vs_overlay": 2.0564749396135267,
          "full_frame_vs_overlay": 2.077818287037037
        },
        "within_limit": true,
        "actual_png_sha256": "d15b8f4ac4cebaa4dd848bbf2e876f0475bb9f65f5d7b3fc9e8f311394b248d9",
        "expected_png_sha256": "5ee0c5cc36269ed385b65550f73445935e1bbd066ad021ea9cf8605f58431c57"
      },
      {
        "name": "scene-lifecycle-02",
        "extracted_frame_timestamp": "418.6",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.070323529411765,
          "bottom_230px_vs_overlay": 2.0410069444444443,
          "full_frame_vs_overlay": 2.0640801826131687
        },
        "within_limit": true,
        "actual_png_sha256": "cfdc7b55e06e3af6c45ca53d3def51972c3d6287526ea409f0f6172b3411999d",
        "expected_png_sha256": "11b8b89ab57caa62b4ac709973f38e2a92538cf7abaa4b2c5e2baee2c1035a96"
      },
      {
        "name": "scene-lifecycle-03",
        "extracted_frame_timestamp": "460.8",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.099088848039216,
          "bottom_230px_vs_overlay": 2.078809631642512,
          "full_frame_vs_overlay": 2.0947701260288065
        },
        "within_limit": true,
        "actual_png_sha256": "68370c4580292fd62f4db744323889f16cf022a75af920f945b124bae3842b1a",
        "expected_png_sha256": "e89fb164fd8d84a52c0f0e84d38b233646ddf2256c1fcabfcfdc49d8796e8a67"
      },
      {
        "name": "scene-lifecycle-04",
        "extracted_frame_timestamp": "504.7",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.080106004901961,
          "bottom_230px_vs_overlay": 2.058158967391304,
          "full_frame_vs_overlay": 2.075432098765432
        },
        "within_limit": true,
        "actual_png_sha256": "8a9656ab0c2bc952b56ae05485fd3e64f25c0d78e96d477ec7fbb6944f2dfa8f",
        "expected_png_sha256": "7535e4cf0e2c82eb6dfd58c21b2be7b3c1f7a20c3e9930ff02ae71798048d186"
      },
      {
        "name": "scene-lifecycle-05",
        "extracted_frame_timestamp": "545.7",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.082561887254902,
          "bottom_230px_vs_overlay": 2.0655804649758456,
          "full_frame_vs_overlay": 2.0789454732510286
        },
        "within_limit": true,
        "actual_png_sha256": "750a4ec4d932c915d48383dbcaacc62d61f727c76c7f416a8b629fcecd57e47e",
        "expected_png_sha256": "bb620d72a212e5614deef9170802980cf75b4c9ff647fed4165ccb92b057d81f"
      },
      {
        "name": "scene-lifecycle-06",
        "extracted_frame_timestamp": "569.5",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.0507297794117645,
          "bottom_230px_vs_overlay": 2.09174365942029,
          "full_frame_vs_overlay": 2.0594642168209876
        },
        "within_limit": true,
        "actual_png_sha256": "c701faea2dab52300f431bd0237f5ab75d4a527de34ae60adb56605893fa23c5",
        "expected_png_sha256": "6fc64a30d9e87c99f1ace8ed3f574c072cdcfc388d63890316fe6e0b43e558d8"
      },
      {
        "name": "scene-lifecycle-07",
        "extracted_frame_timestamp": "580.2",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.058276756535948,
          "bottom_230px_vs_overlay": 2.085668025362319,
          "full_frame_vs_overlay": 2.0641100823045266
        },
        "within_limit": true,
        "actual_png_sha256": "5d396c93aee4e98cf4d5d9355a1a7b199ce7c12bfeeb74b5a429d85c744ed509",
        "expected_png_sha256": "42aedf474f5c14f0e2c3a8e6445120d18f53a58f3e98094638541afa70d9af30"
      },
      {
        "name": "scene-lifecycle-08",
        "extracted_frame_timestamp": "593.1",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.0714667075163398,
          "bottom_230px_vs_overlay": 2.0509276871980675,
          "full_frame_vs_overlay": 2.067092656893004
        },
        "within_limit": true,
        "actual_png_sha256": "74a017d056f3298b2d823d915e29d88ade1650d71e489f558725f36e4bac6b58",
        "expected_png_sha256": "17e40f35409e93acacff6ddb3b3e8f28796a1f43da8a39eaa76214c038178825"
      },
      {
        "name": "scene-repository-01",
        "extracted_frame_timestamp": "614.8",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.0834636437908496,
          "bottom_230px_vs_overlay": 2.0820040760869567,
          "full_frame_vs_overlay": 2.0831528099279835
        },
        "within_limit": true,
        "actual_png_sha256": "8fe24c392aae5bbd32426575a1413af8c4998456fb45b05f0e363aad2c85b568",
        "expected_png_sha256": "0d88bbb2abb36766d6aca940b2eb7f29e8da58ffb321f61f5fb62d5376a7771e"
      },
      {
        "name": "scene-repository-02",
        "extracted_frame_timestamp": "648.2",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.11469158496732,
          "bottom_230px_vs_overlay": 2.0616319444444446,
          "full_frame_vs_overlay": 2.103391846707819
        },
        "within_limit": true,
        "actual_png_sha256": "8d5eaf39732674cfcc89decfd3946bd06d2d954b2dc89781a386d3c684922099",
        "expected_png_sha256": "d7cab0a76b8331e062a0b148702a705e3e09191842012d4791104773ae4fe141"
      },
      {
        "name": "scene-repository-03",
        "extracted_frame_timestamp": "687.5",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.1233319035947713,
          "bottom_230px_vs_overlay": 2.0570516304347826,
          "full_frame_vs_overlay": 2.109216660236626
        },
        "within_limit": true,
        "actual_png_sha256": "ea053480a60f35fea4491dc90c807280a4b31922dfe96e665f82d85451a01ba9",
        "expected_png_sha256": "1bd9688cdc941baca91a39542d0bca78509dbbb0cd1a8ce03293ab3b0a1bd88e"
      },
      {
        "name": "scene-repository-04",
        "extracted_frame_timestamp": "725.5",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.0679583333333333,
          "bottom_230px_vs_overlay": 2.0690670289855073,
          "full_frame_vs_overlay": 2.0681944444444444
        },
        "within_limit": true,
        "actual_png_sha256": "0928ba20db48e23c1dd3cc9d5f97dbc1f0cd7a13f0927bbcc2a69825c0b899d3",
        "expected_png_sha256": "63afd1001cdcc29010081ff32a046f920886576582ecb053a5d79c08c6c7fe77"
      },
      {
        "name": "scene-repository-05",
        "extracted_frame_timestamp": "748.4",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.045062295751634,
          "bottom_230px_vs_overlay": 2.0631612318840578,
          "full_frame_vs_overlay": 2.0489166988168726
        },
        "within_limit": true,
        "actual_png_sha256": "5f338dfd6b9d1c273579c7c9c0b0fac5b1e434fc3e0f9cf4debb6dd9986b5400",
        "expected_png_sha256": "ab7435629401918022946b5fe9cbba9514234d9d54d2c6775bd208c9074409af"
      },
      {
        "name": "scene-repository-06",
        "extracted_frame_timestamp": "759.1",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.057839460784314,
          "bottom_230px_vs_overlay": 2.0852362620772946,
          "full_frame_vs_overlay": 2.0636739647633746
        },
        "within_limit": true,
        "actual_png_sha256": "1b9547cdd41e4dc2e8167644a5edbd7acd4d9a24202bf1705fffa4d4982d7885",
        "expected_png_sha256": "4d5a1c6b8fcd970a2895d9c8a86a8bae0cc9569589f1301d6e182894985bb6e8"
      },
      {
        "name": "scene-repository-07",
        "extracted_frame_timestamp": "772.1",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.061905637254902,
          "bottom_230px_vs_overlay": 2.070400815217391,
          "full_frame_vs_overlay": 2.063714795524691
        },
        "within_limit": true,
        "actual_png_sha256": "875a254714ee83546f88481ace1381c249343f2d4f54c4adc5b410a4bb510fc0",
        "expected_png_sha256": "03b818cf7715e9c4510924063a814953a57284b0987645fe8c89985ff0512660"
      },
      {
        "name": "scene-measurements-01",
        "extracted_frame_timestamp": "800.1",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.0663513071895427,
          "bottom_230px_vs_overlay": 2.0610695954106277,
          "full_frame_vs_overlay": 2.0652264981995887
        },
        "within_limit": true,
        "actual_png_sha256": "3a162bccaca4c57ef4f6e7f51cd6987c4a9c0e889c8504038807ba6150572959",
        "expected_png_sha256": "f429d5f1630ed0835022879761ccab995fa4d90f3b1472a4c2ee0390e6c80d63"
      },
      {
        "name": "scene-measurements-02",
        "extracted_frame_timestamp": "837.2",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.109798815359477,
          "bottom_230px_vs_overlay": 2.052217693236715,
          "full_frame_vs_overlay": 2.0975361689814815
        },
        "within_limit": true,
        "actual_png_sha256": "ea4c72f890cbf0bbb659bcfaf4e33442a963d9fc89c59c963b4e6cde7f1afba8",
        "expected_png_sha256": "09903f213f773fec3d911bc9cf38f46b6dad9f2bfa9684e0bb3f3e0c169d3eba"
      },
      {
        "name": "scene-measurements-03",
        "extracted_frame_timestamp": "875",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 1.9870500408496732,
          "bottom_230px_vs_overlay": 2.0729521437198066,
          "full_frame_vs_overlay": 2.005344007201646
        },
        "within_limit": true,
        "actual_png_sha256": "39adc5f9ab0fd1ac84f265911b7d3bfea7294aeda7cb9ca4b871558682558c0d",
        "expected_png_sha256": "67e8aeffb8e70166bb077b89df0ff74edd789650fc2798789b2c437e451ae7e2"
      },
      {
        "name": "scene-measurements-04",
        "extracted_frame_timestamp": "917.1",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.161059640522876,
          "bottom_230px_vs_overlay": 2.0470335144927536,
          "full_frame_vs_overlay": 2.136776298868313
        },
        "within_limit": true,
        "actual_png_sha256": "12d113c5b424670fb5d5bc7927e87e8a5a1f5c9792d3d827f88c5d787545bd92",
        "expected_png_sha256": "79a64c367d38d9748a289e975ef1da72dbb4f9e409fd5a32e67fe0b17e89b66e"
      },
      {
        "name": "scene-measurements-05",
        "extracted_frame_timestamp": "955.6",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.0808135212418297,
          "bottom_230px_vs_overlay": 2.084297252415459,
          "full_frame_vs_overlay": 2.0815554269547323
        },
        "within_limit": true,
        "actual_png_sha256": "6c38ad9d6cf4376483d83070617c32f5f748d768e405d132dba8a4deaff0d981",
        "expected_png_sha256": "24e995574c2995d47b32091c1da78bddcdf9304ba1d15cde466ee03d93f1b1c9"
      },
      {
        "name": "scene-measurements-06",
        "extracted_frame_timestamp": "983",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.0615046977124183,
          "bottom_230px_vs_overlay": 2.053931914251208,
          "full_frame_vs_overlay": 2.0598919753086418
        },
        "within_limit": true,
        "actual_png_sha256": "68a710f125eed06ec4e2be83f396bcf39af1f8dcf4a8142ff2c044cfa801c438",
        "expected_png_sha256": "02c53f4a26b29e2f08b4e2b8958988382e37d654984fd89bf87fa05ecb433e92"
      },
      {
        "name": "scene-measurements-07",
        "extracted_frame_timestamp": "999.2",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.0702467320261437,
          "bottom_230px_vs_overlay": 2.0980042270531403,
          "full_frame_vs_overlay": 2.076158050411523
        },
        "within_limit": true,
        "actual_png_sha256": "02dd3a8391a08a56ed2271df267e1533b4edba57a4b2e152ea3c7ede09eb50eb",
        "expected_png_sha256": "79be08ffa3c7e74cd0353a7d9a3b92a626465a0c3d170acf9f596f0f41050515"
      },
      {
        "name": "scene-measurements-08",
        "extracted_frame_timestamp": "1012.6",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.060949754901961,
          "bottom_230px_vs_overlay": 2.0876456823671496,
          "full_frame_vs_overlay": 2.0666349987139916
        },
        "within_limit": true,
        "actual_png_sha256": "e5695d9c666025de90f1961f30551e62914122a736a1fe6e8f3a7047d896b8cd",
        "expected_png_sha256": "f75b7f8738184090605ed962c1b560297635238283a00f0cddbaf1e6160d7819"
      },
      {
        "name": "scene-demo-01",
        "extracted_frame_timestamp": "1038.2",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.0728388480392157,
          "bottom_230px_vs_overlay": 2.0734941123188406,
          "full_frame_vs_overlay": 2.0729783950617287
        },
        "within_limit": true,
        "actual_png_sha256": "8f673bf52bdd0e00e21fe417e313d8813ed4c4106c2ba12540428af7c1188719",
        "expected_png_sha256": "d8b33481439ed594c9a555c2b5fabb5833b6db73cf33b725e14f2a0ea9ee0bf6"
      },
      {
        "name": "scene-demo-02",
        "extracted_frame_timestamp": "1077",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.0817455065359476,
          "bottom_230px_vs_overlay": 2.05395606884058,
          "full_frame_vs_overlay": 2.0758273855452676
        },
        "within_limit": true,
        "actual_png_sha256": "e16dc3735c581c7c54eb9722116f6489574ffd88d45cc505b60328a5d8864d95",
        "expected_png_sha256": "7dbb0c7e387bf4bd7268b5f1fa140ed082e3c4f2a5c45e6972be85cb38f527b3"
      },
      {
        "name": "scene-demo-03",
        "extracted_frame_timestamp": "1118.3",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.0909279003267973,
          "bottom_230px_vs_overlay": 2.059523701690821,
          "full_frame_vs_overlay": 2.0842399691358025
        },
        "within_limit": true,
        "actual_png_sha256": "3b5f70bcabceed1139f13cc7dcda04bf4492113196076cd82de40ed1a6d4744f",
        "expected_png_sha256": "ac3daf54cd800ff7ce1c7b5795dbcca9cfdd4d943e1fc9cdde700ea07423aacb"
      },
      {
        "name": "scene-demo-04",
        "extracted_frame_timestamp": "1159.2",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.105609681372549,
          "bottom_230px_vs_overlay": 2.0356680253623187,
          "full_frame_vs_overlay": 2.090714699074074
        },
        "within_limit": true,
        "actual_png_sha256": "ad9cf8836fd783ad3f10a7cb50b2ce6e2d195e40e2b7635adedbef453f113f5a",
        "expected_png_sha256": "10806601c60bfd623a71fc25dbcc7269b7895091396b50149aa5bef6a27b180a"
      },
      {
        "name": "scene-demo-05",
        "extracted_frame_timestamp": "1190.1",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.06209068627451,
          "bottom_230px_vs_overlay": 2.0565526871980677,
          "full_frame_vs_overlay": 2.0609112975823045
        },
        "within_limit": true,
        "actual_png_sha256": "f7221397b6f1c80a775276aba53c69fd0f82875d2fd1b9998a16d29704c4ea03",
        "expected_png_sha256": "9420e55f926fc6c6cc7b235a57384bd255ede3deafa87212c6c295a334183476"
      },
      {
        "name": "scene-demo-06",
        "extracted_frame_timestamp": "1209.9",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.0599080882352943,
          "bottom_230px_vs_overlay": 2.0894663345410627,
          "full_frame_vs_overlay": 2.0662028999485593
        },
        "within_limit": true,
        "actual_png_sha256": "a3d2642eb465d0f7377efe119b8b1b950685f16b98b4ec42efca879148613de8",
        "expected_png_sha256": "db9ebe5603f901c3a6c100fa509def2c9af85c69a0074ee637a74e1d4e3081ea"
      },
      {
        "name": "scene-demo-07",
        "extracted_frame_timestamp": "1239.5",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.0694223856209146,
          "bottom_230px_vs_overlay": 2.0388141606280192,
          "full_frame_vs_overlay": 2.062903967335391
        },
        "within_limit": true,
        "actual_png_sha256": "f8e8f1cdbee27bbd583e2238d4267fd5ed4fb595deaa6d1d1ae9bf5a42c37927",
        "expected_png_sha256": "a673a3f1fc986d5a9cc48c11b559846382dd43daa450575f59a97b1198d1a107"
      },
      {
        "name": "scene-operate-01",
        "extracted_frame_timestamp": "1277.9",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.0745684232026145,
          "bottom_230px_vs_overlay": 2.0477309782608697,
          "full_frame_vs_overlay": 2.068853041409465
        },
        "within_limit": true,
        "actual_png_sha256": "732cac274d3ce71d98f5b68ecdc1d6f0cce0f0c9e07c140fd5e3c391e1832636",
        "expected_png_sha256": "06e5b7883b471028fc3839563f745fac9a68142e48212c85a34f59e0c10072da"
      },
      {
        "name": "scene-operate-02",
        "extracted_frame_timestamp": "1314.1",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.0603933823529412,
          "bottom_230px_vs_overlay": 2.0540413647342994,
          "full_frame_vs_overlay": 2.059040637860082
        },
        "within_limit": true,
        "actual_png_sha256": "883a06872fda293665a275c14a84230f2e22e35919eae564e1490cc602c1696d",
        "expected_png_sha256": "6287f6838c56f8011f88fe0bed8a31c86f05a99e80dccad5e10036ccd93b16e2"
      },
      {
        "name": "scene-operate-03",
        "extracted_frame_timestamp": "1355.5",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.071936070261438,
          "bottom_230px_vs_overlay": 2.08024154589372,
          "full_frame_vs_overlay": 2.073704828960905
        },
        "within_limit": true,
        "actual_png_sha256": "1dec2667d1c98ecc052bcdacdbb15d5145bbd2b660a0682e374e4438f7a752e8",
        "expected_png_sha256": "be1d01a7147f3f7cb8fc82848d1322ba873730b4e94bb2a7193c7092ddd217a0"
      },
      {
        "name": "scene-operate-04",
        "extracted_frame_timestamp": "1398.7",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.1060377859477124,
          "bottom_230px_vs_overlay": 2.0598890398550727,
          "full_frame_vs_overlay": 2.0962098122427983
        },
        "within_limit": true,
        "actual_png_sha256": "d6e23bfe3e8d75267b2f1d974360d5e72691770157791d4476ec7c345de3af34",
        "expected_png_sha256": "07cb3296f36aab94ff40b09c488be080cafeee59980e50b297c4a9fb52625268"
      },
      {
        "name": "scene-operate-05",
        "extracted_frame_timestamp": "1438.5",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.080061683006536,
          "bottom_230px_vs_overlay": 2.061651570048309,
          "full_frame_vs_overlay": 2.0761410108024694
        },
        "within_limit": true,
        "actual_png_sha256": "95bcb08422df7dd0796f4e59d03f4c20d35de592bef76f5918dda6a216f4c426",
        "expected_png_sha256": "778d8412c01e32837954689ec0d584d0ff5bed59c91dba37f82014312ea2a836"
      },
      {
        "name": "scene-operate-06",
        "extracted_frame_timestamp": "1465.3",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.056209558823529,
          "bottom_230px_vs_overlay": 2.0551758756038647,
          "full_frame_vs_overlay": 2.0559894225823045
        },
        "within_limit": true,
        "actual_png_sha256": "130c74d7d80c8635eda755ff5245af44aef4415a0c94f2771f3534385e1de10e",
        "expected_png_sha256": "641c7225e12abe2df460b285c8ec1eb6e1b7039d3083ac746c90d4317caad53d"
      },
      {
        "name": "scene-operate-07",
        "extracted_frame_timestamp": "1477.3",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.0679777369281047,
          "bottom_230px_vs_overlay": 2.094670893719807,
          "full_frame_vs_overlay": 2.0736623906893
        },
        "within_limit": true,
        "actual_png_sha256": "f5c4665938376a0f1c7f2f6fd75d23144886e981532c63e5047eff5db443186e",
        "expected_png_sha256": "14ab2614555f750ecac11ca651794c79d2e72e8d3cd0c94111088c119587527e"
      },
      {
        "name": "scene-operate-08",
        "extracted_frame_timestamp": "1491.2",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.0568666258169936,
          "bottom_230px_vs_overlay": 2.045954861111111,
          "full_frame_vs_overlay": 2.054542824074074
        },
        "within_limit": true,
        "actual_png_sha256": "0eea3e61cc469d4d30cf221308582b8dfe0d4ec7eaa35e59435e2a42550a7aae",
        "expected_png_sha256": "b2ae17b2ee5a24b098fcaf1412b9f1280e8fe58a9da218d01a50bb58bcf059c0"
      },
      {
        "name": "scene-future-01",
        "extracted_frame_timestamp": "1518.1",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.0964522058823527,
          "bottom_230px_vs_overlay": 2.064448218599034,
          "full_frame_vs_overlay": 2.0896365419238685
        },
        "within_limit": true,
        "actual_png_sha256": "afa30511671317753be2afd9cf911fe56d687cd3316d7aa333586f3d1cf2ec67",
        "expected_png_sha256": "eb4f10c937c27caf395ffa170d9ef1dc3530b870e0d80b6be6f868364efd2207"
      },
      {
        "name": "scene-future-02",
        "extracted_frame_timestamp": "1559.5",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.0751975081699343,
          "bottom_230px_vs_overlay": 2.073198218599034,
          "full_frame_vs_overlay": 2.0747717335390945
        },
        "within_limit": true,
        "actual_png_sha256": "4faf94086c0b741faa36c89cb20d0997818d75f070b92c827d7fafdc8a6eed22",
        "expected_png_sha256": "2f5f52057e490ef7dd97c3303a61e9034c6b99992bb213b04ade0ec78545a826"
      },
      {
        "name": "scene-future-03",
        "extracted_frame_timestamp": "1587.6",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.0431035539215685,
          "bottom_230px_vs_overlay": 2.049343297101449,
          "full_frame_vs_overlay": 2.044432388117284
        },
        "within_limit": true,
        "actual_png_sha256": "0a8557616925783f110e1434b83392ec8180e4c4a1cc681f95c78f4f3f31fc75",
        "expected_png_sha256": "2599b0837a881f406bdfa61a4e21900b11ebc1cb9bd67f4f31a526e04b2d18ff"
      },
      {
        "name": "scene-future-04",
        "extracted_frame_timestamp": "1596.3",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.0570539215686274,
          "bottom_230px_vs_overlay": 2.082235809178744,
          "full_frame_vs_overlay": 2.0624167309670782
        },
        "within_limit": true,
        "actual_png_sha256": "211ecc998e0f80791d7a3ddbfb57a9a4f3d45c06d822c5aa900e6a456c097e06",
        "expected_png_sha256": "31dd5617c2c9f1392bf141a16c64ef77ebd1ec64d20567b2caec8a4cb1b2a06f"
      },
      {
        "name": "scene-future-05",
        "extracted_frame_timestamp": "1610.2",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.0802638888888887,
          "bottom_230px_vs_overlay": 2.0660477053140096,
          "full_frame_vs_overlay": 2.0772363683127573
        },
        "within_limit": true,
        "actual_png_sha256": "b98362f7efde3634ecd87b28ec0ec91f42f1dc8f80172b44d2ab4a64c05ffa6c",
        "expected_png_sha256": "c82d237af8e72a7a96dfdd1c54dbb838193017bf51b183529e634eed5cea05d8"
      },
      {
        "name": "scene-teach-back-01",
        "extracted_frame_timestamp": "1636.8",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.109482434640523,
          "bottom_230px_vs_overlay": 2.063336352657005,
          "full_frame_vs_overlay": 2.099655028292181
        },
        "within_limit": true,
        "actual_png_sha256": "3f53906aa93173a1685f164efd60963c78ef4718ad019e1ec5ff78ad9e99e82f",
        "expected_png_sha256": "39ddedac8a13583cfd07b8e59fa1d3e146badd645a90c407908e17d5a60885ad"
      },
      {
        "name": "scene-teach-back-02",
        "extracted_frame_timestamp": "1698.5",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.0834197303921567,
          "bottom_230px_vs_overlay": 2.077774003623188,
          "full_frame_vs_overlay": 2.0822173996913578
        },
        "within_limit": true,
        "actual_png_sha256": "f5376b77e54165c3158f7efa773e6730da23d6ec7c7e3d0c3c56fcb4e91dc48e",
        "expected_png_sha256": "c33f8dd5c2fd7fd8166ea53c3849191d25bbfa3dee50a5cd31ecbf20c9ca32e8"
      },
      {
        "name": "scene-teach-back-03",
        "extracted_frame_timestamp": "1771.8",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.0675177696078433,
          "bottom_230px_vs_overlay": 2.093859450483092,
          "full_frame_vs_overlay": 2.073127572016461
        },
        "within_limit": true,
        "actual_png_sha256": "2d9d734706e667604e1eb27b0a11b1efc431ef348719ce93303ba4a668f131e6",
        "expected_png_sha256": "beec97c3e2b3af9822c2ad31c2bc9eb7734d6c8fa85b3f9dd032407c3822f94b"
      },
      {
        "name": "chapter-01-purpose",
        "extracted_frame_timestamp": "0.2",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.096026348039216,
          "bottom_230px_vs_overlay": 2.0531551932367154,
          "full_frame_vs_overlay": 2.086896379886831
        },
        "within_limit": true,
        "actual_png_sha256": "d2192a93c1032905df04f0e2ea2a7cf3c48433a7f23e4761a4ba74c7ce8e45a6",
        "expected_png_sha256": "886c1e333ef4d6de6b3f71f323eff1338aa5648a8eeb342e881eaddf5aa4914f"
      },
      {
        "name": "chapter-02-inputs",
        "extracted_frame_timestamp": "120.2",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.0864873366013073,
          "bottom_230px_vs_overlay": 2.072780797101449,
          "full_frame_vs_overlay": 2.0835683513374486
        },
        "within_limit": true,
        "actual_png_sha256": "82fafcd1e5be75e1b6ab59b8377bf6f3d9f3c2ab64a03476f2821af651296474",
        "expected_png_sha256": "ffa522bb9612a3e77440d5daa46f2f1e76554d2473d2289620a51b12a489b272"
      },
      {
        "name": "chapter-03-lifecycle",
        "extracted_frame_timestamp": "360.2",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.0835553513071896,
          "bottom_230px_vs_overlay": 2.0376615338164252,
          "full_frame_vs_overlay": 2.073781667952675
        },
        "within_limit": true,
        "actual_png_sha256": "04d5d4ceb046f129debfbe3570d30cd1c703868af13b8516a9ca8b0fa7136ffc",
        "expected_png_sha256": "c0ace1ddbef5a5a3ec859e29f4b29553dc53c0ed39ae97a6420a70ca8d41dce8"
      },
      {
        "name": "chapter-04-repository",
        "extracted_frame_timestamp": "600.2",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.106936683006536,
          "bottom_230px_vs_overlay": 2.0861684782608694,
          "full_frame_vs_overlay": 2.102513824588477
        },
        "within_limit": true,
        "actual_png_sha256": "6eb2af11fafb36eae6c5fac33debd6ed92ced40c9b9ce92003cc4d12431d8c5f",
        "expected_png_sha256": "7a48938aa4df4abcf090181801b3d42b2200167825e04ab24e3ccc034348a047"
      },
      {
        "name": "chapter-05-measurements",
        "extracted_frame_timestamp": "780.2",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.0785210375816994,
          "bottom_230px_vs_overlay": 2.0852619263285024,
          "full_frame_vs_overlay": 2.0799565972222225
        },
        "within_limit": true,
        "actual_png_sha256": "cc2e214eb7f86e6d27257af4cc1ce88f05cf2bba70d580c050556c672af0d293",
        "expected_png_sha256": "b4087a17cadff950b434b918562c9552f5dbbbb9da048519f414a9220328de04"
      },
      {
        "name": "chapter-06-demo",
        "extracted_frame_timestamp": "1020.2",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.0728086192810458,
          "bottom_230px_vs_overlay": 2.056941425120773,
          "full_frame_vs_overlay": 2.0694294945987655
        },
        "within_limit": true,
        "actual_png_sha256": "61c132a0f35c1226412756b660f6432b867dc3777187cf1cade727cd250b66be",
        "expected_png_sha256": "276faa68ecb4db7ae55e7c4ac7968b170e474b68bc61a2e811060f1399e1836c"
      },
      {
        "name": "chapter-07-operate",
        "extracted_frame_timestamp": "1260.2",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.0946468545751635,
          "bottom_230px_vs_overlay": 2.078562801932367,
          "full_frame_vs_overlay": 2.091221547067901
        },
        "within_limit": true,
        "actual_png_sha256": "a3a15c4b9d9a16544a65a950395f4d6ef5235720bbedff16f0ff693fdb1e0aaf",
        "expected_png_sha256": "c3c132ad979812ef586e9d7192d4759dcf9b373968a3a2a3529485137b73f2f2"
      },
      {
        "name": "chapter-08-future",
        "extracted_frame_timestamp": "1500.2",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.126423815359477,
          "bottom_230px_vs_overlay": 2.0726358695652176,
          "full_frame_vs_overlay": 2.11496897505144
        },
        "within_limit": true,
        "actual_png_sha256": "1509e45ae8f8e5711649312bf3cba82280289b39d12fd31f9f8d5a4664986e0e",
        "expected_png_sha256": "099a452ef723fddc0197f166d74b1205ca536f8a3d2cb3d1dea9cf3c59a1d2c5"
      },
      {
        "name": "chapter-09-teach-back",
        "extracted_frame_timestamp": "1620.2",
        "timestamps_equal": true,
        "mean_absolute_rgb_difference": {
          "upper_850px_vs_source": 2.109372140522876,
          "bottom_230px_vs_overlay": 2.041196407004831,
          "full_frame_vs_overlay": 2.0948532343107
        },
        "within_limit": true,
        "actual_png_sha256": "52c6be5d82feda7c61cdf9518b9b87a546219cfee31e8c23e1e02bacba5d9041",
        "expected_png_sha256": "8d703a449130d67307728b5f6d494c0d9fee841b07254496f4e460168f0aa422"
      }
    ],
    "visual_samples_reviewed": [
      "lifecycle-01",
      "inputs-05",
      "demo-04"
    ],
    "reviewer": "Codex full-frame image inspection; not human playback"
  },
  "speech_recognition": {
    "status": "supplementary_check_complete",
    "mp4_sha256": "afc302395c9606e16300ab4910c2a43da3b22c979a1dd2999cff5b88bfc3a829",
    "model": "Systran/faster-whisper-base.en",
    "segments": 239,
    "elapsed_seconds": 59.26788703002967,
    "receipt_sha256": "bf10b273c00cc53b2a64e0cf593be2f8b624f51b69e64b2b4472e9ef2ea025c9",
    "critical_csv_number_recheck": [
      {
        "start": 120.0,
        "end": 122.92,
        "text": " The three supplied files have different roles."
      },
      {
        "start": 122.92,
        "end": 125.64,
        "text": " The PDF is the research paper."
      },
      {
        "start": 125.64,
        "end": 128.72,
        "text": " It describes methods and reports results."
      },
      {
        "start": 128.72,
        "end": 131.52,
        "text": " It is not itself a ready to train data set."
      },
      {
        "start": 131.52,
        "end": 134.84,
        "text": " The CIC IDS 2017,"
      },
      {
        "start": 134.84,
        "end": 139.84,
        "text": " CSV contains 1,410,255 packet rows and 15 labels."
      },
      {
        "start": 142.88,
        "end": 147.88,
        "text": " The UN SWCSV contains 79,881 packet rows"
      },
      {
        "start": 148.36,
        "end": 151.2,
        "text": " and 10 labels."
      },
      {
        "start": 151.2,
        "end": 154.92000000000002,
        "text": " A CSV is a text table with rows and columns,"
      },
      {
        "start": 154.92000000000002,
        "end": 156.96,
        "text": " not a running database server."
      },
      {
        "start": 156.96,
        "end": 159.22,
        "text": " We inspected the supplied exports"
      },
      {
        "start": 159.22,
        "end": 161.24,
        "text": " and recorded their file identities."
      },
      {
        "start": 161.24,
        "end": 162.07999999999998,
        "text": " Both exports"
      }
    ],
    "limitations": "Recognition errors remain in ASR output; not the authoritative transcript or human listening.",
    "current_audio_identity": {
      "status": "passed",
      "mp4_sha256": "1ff19bf545fe14a4bf1f61112a1fdfd7dc107a36ca4c91a749c4f6dfaea8082b",
      "original_audio_hash": "SHA256=4e1e3d3fccddc78219d923d625cba6a229b296c77c5cb17c86d2004f464325a1",
      "current_audio_hash": "SHA256=4e1e3d3fccddc78219d923d625cba6a229b296c77c5cb17c86d2004f464325a1",
      "equal": true,
      "command": [
        "/home/nvidia/learn/_video/bin/ffmpeg",
        "-v",
        "error",
        "-i",
        "/home/nvidia/netmambaplus-reproduction/docs/customer/demo/video/NetMambaPlus-30-minute-course.mp4",
        "-map",
        "0:a",
        "-c",
        "copy",
        "-f",
        "hash",
        "-hash",
        "sha256",
        "-"
      ],
      "human_listening_review": "not performed"
    },
    "scope": "ASR ran against the preceding MP4. Its encoded AAC stream is byte-identical to the corrected MP4, as separately measured. ASR remains supplementary, with recognition errors, not human listening."
  },
  "negative_media_checks": {
    "fixtures": [
      {
        "case": "truncated",
        "status": "rejected_as_expected",
        "reason": "Truncated or overlong video"
      },
      {
        "case": "missing_audio",
        "status": "rejected_as_expected",
        "reason": "Both video and audio streams are required"
      },
      {
        "case": "silent_audio",
        "status": "rejected_as_expected",
        "reason": "Unexplained encoded silence: 0.000–1800.000s"
      }
    ],
    "tested_mp4_sha256": "afc302395c9606e16300ab4910c2a43da3b22c979a1dd2999cff5b88bfc3a829",
    "scope": "Historical negative fixtures validate the verifier on the preceding MP4; final corrected video decode is recorded separately."
  },
  "local_browser": {
    "status": "passed",
    "url": "http://127.0.0.1:8787/video/",
    "completed_at": "2026-09-13T07:37:54.562583+00:00",
    "browser": "Chromium 140.0.7339.16; Playwright 1.55.0",
    "html_sha256": "c3f336a7f92e59614292597f0b19f5ad4cd67ae0c27be0b6a4138be088313691",
    "mp4_sha256": "1ff19bf545fe14a4bf1f61112a1fdfd7dc107a36ca4c91a749c4f6dfaea8082b",
    "decoded_frames_and_audio_bytes": {
      "audio": 15263,
      "video": 14,
      "played_src": "http://127.0.0.1:8787/video/NetMambaPlus-30-minute-course.webm"
    },
    "caption_count": 413,
    "keyboard_playback": true,
    "keyboard_chapter_offsets": [
      0,
      120,
      360,
      600,
      780,
      1020,
      1260,
      1500,
      1620
    ],
    "seek_and_play_near_end": true,
    "download_bytes_equal": true,
    "served_bytes_equal": true,
    "viewport_widths_without_overflow": [
      320,
      390,
      768,
      1440
    ],
    "page_errors": [],
    "screenshots": {
      "video-390.png": "84e0df102fdd637b7849d0ce9bd7293d0780eb225b0db76760ebca32a7a3d759",
      "video-320.png": "e50eac58e245bf386242ee693f5bc2a1906bf14bd83ec57fd99df613a6aff764",
      "video-1440.png": "2347c4fb3511346aa24e85f06acb033648d109a394f9cca4210fe0db5c931b67",
      "video-768.png": "21e7505a53961fc1f1486a2642d16fc5d87997b3905f7b3ed51bb55727c10283"
    }
  },
  "human_full_playback_review": {
    "status": "pending",
    "detail": "No human reviewer identity, complete listening observations, or mastery evidence is available."
  },
  "distributed_caption_alignment": {
    "status": "pending",
    "detail": "Sentence boundaries are measured; proportional within-sentence cue breaks have not all been independently verified to ±0.5 seconds."
  },
  "publication": {
    "status": "pending"
  },
  "council": {
    "run_id": "763a3a96-4155-4f0b-9dc4-873c1422b9dc",
    "outcome": "CONSENSUS / RATIFIED",
    "decision_sha256": "812de7b76131f1eb983a0d2082adefc553f01b9ea006ceffcb293e4c37d31ddd",
    "final_media_acceptance": "Human playback and distributed caption checks remain pending; consensus is not media certification."
  },
  "cpu_tests": {
    "status": "passed",
    "detail": "78 tests passed: 54 harness, 17 archived-course, 7 video. Corrected isolated navigation fixture included.",
    "receipt": {
      "completed_at": "2026-09-13T07:42:52.539556+00:00",
      "command": "python3 -m unittest discover -s tests -v",
      "exit_code": 0,
      "tests": 78,
      "output_sha256": "e65a4fcb85fb9f895e3c5b5dceae7fbf18f1274f2d5a8f8d356ddc999417d500"
    }
  },
  "full_source_review": {
    "status": "completed",
    "reviewer": "Codex ordinary session",
    "completed_at": "2026-09-13T07:42:52.539556+00:00",
    "source_sha256": "4b1ac47ed54ceff5327b460dc366859de22c6c414f1edbe35827514c21f77b02",
    "spoken_scenes": 51,
    "scope": "Read complete resolved narration, all seven question mappings, every input and results distinction, wrapper commands, actual prediction error, and remaining IDS/NPU limits against the existing reference records. Includes sections omitted from the final council pack.",
    "reference_hashes": {
      "answers": {
        "path": "docs/customer/answers.md",
        "sha256": "e293eb26550a2c1577c689ccac845ad0321be7bbf2fd41c6aeeedbad3c5565ab"
      },
      "comparison": {
        "path": "docs/customer/upstream-comparison.md",
        "sha256": "a84e5fbffabc2b6ccc44351203b4b61f9f95dee7608765e3ef427d54e121b5ba"
      },
      "results": {
        "path": "docs/customer/evidence/results.json",
        "sha256": "ead00597c0534a10d779e83805366c1cf323d231b1f7e94e9d001272e7641f1a"
      },
      "csv": {
        "path": "docs/customer/evidence/uploaded-csv-profile.json",
        "sha256": "f6d11f8c8c2d604ed6a6f2539c9c7fb93d1279997dd89cb84873de03c0547097"
      },
      "native": {
        "path": "docs/customer/evidence/native-data-validation.json",
        "sha256": "122bc8ba9a3ba2d53400b615b7b73a2d597e21063c478a96d852b3d7a7dd96f9"
      },
      "lesson": {
        "path": "docs/lesson.md",
        "sha256": "bcd7710396fc5f088de56df470f4c8c708336790af728d7940f57bcf2b888afa"
      },
      "transfer": {
        "path": "docs/customer/evidence/checkpoint-transfer.json",
        "sha256": "819195d7d3a9aaccf534ce2cca88e3986eb56facf0891fd7cbfe27e1149b520e"
      },
      "runbook": {
        "path": "docs/customer/runbook.md",
        "sha256": "854f19228fd384888cb268db20bf005785813df5c5fd6421110d81fcb95f49a0"
      },
      "config": {
        "path": "configs/ciciot2022.json",
        "sha256": "fba589310c98ea9f8838a0a14eb9cb2d6cfd13c4c8d219c6878e7508c68cab92"
      },
      "verification": {
        "path": "docs/customer/verification.md",
        "sha256": "88948b8336c729882a2a8835f69b03489161be769d3e6a4991a7ccc7a91bebbc"
      },
      "prediction": {
        "path": "docs/customer/evidence/seed0/replay/predictions.json",
        "sha256": "307fd521ce152b0614c091c882c11a11d80ba7de3ae923624ec31e6d1f59c68a"
      },
      "quickstart": {
        "path": "docs/customer/quickstart.md",
        "sha256": "6641b5d478ef02981014bf3d8c08f3f86c147de25e93ce9efc7dac5fae5d99bf"
      },
      "hardware": {
        "path": "docs/customer/hardware-roadmap.md",
        "sha256": "99cacacf535210e6517661595f0994e3899fd59787c58872a64c35f5bdc2be18"
      },
      "export": {
        "path": "docs/customer/evidence/export-probe/metrics.json",
        "sha256": "cef8a3811b33a4d350466368c3069b1d4dd2ed43ba0ebd9b5885378ff0d9ca04"
      },
      "benchmark": {
        "path": "docs/customer/evidence/benchmark/metrics.json",
        "sha256": "1f06ba04717400b0f20a7e79f7c90e8e0d357f8bf7f2c8507ccdfc969eec0e9b"
      },
      "walkthrough": {
        "path": "docs/repository-walkthrough.md",
        "sha256": "8cb5b8c6aa2afb53e748ab552b63e944f9f896baa9dcca00eac50377b53c39a4"
      },
      "contract": {
        "path": "docs/harness-reference.md",
        "sha256": "bebbb49d3489a8bad584aa944def395ef0912d7d079e3f22b29e5af035205baa"
      }
    },
    "human_learning_review": "not performed"
  },
  "final_quality_council": {
    "run_id": "d2eb183c-3f57-4c06-bb98-872ea1fd699e",
    "state": "ESCALATED",
    "stamp": "UNRATIFIED",
    "mutual": false,
    "decision_hash": null,
    "result_file": "docs/research/video-quality-review.json",
    "result_file_sha256": "b019fbdc29bffb4823e76a745cd4ac2aad85ef7e1e481ebd48c8936b541a2713",
    "resolved_by_later_ordinary_checks": [
      "corrected CPU-suite rerun",
      "full narration source review",
      "full-frame picture/caption checks and corrected parallel-view diagram",
      "WebM actual decode and stream/chapter metadata"
    ],
    "pending": [
      "human complete listening/watch-through",
      "distributed heard-caption alignment within ±0.5 seconds"
    ],
    "publication_classification": "mechanically checked review copy, not final mutual acceptance"
  },
  "prior_content_review": {
    "status": "passed",
    "reviewer": "Codex ordinary session",
    "source_sha256": "ace0c090ab6a702a00f2092e96d88db92c442ea142471f5cfff10ad221f171d4",
    "topics": [
      "all seven customer questions",
      "packet CSV versus native flow input",
      "training/inference separation",
      "all seeds and unreproduced paper metric",
      "original repository versus wrapper",
      "actual row635 and score interpretation",
      "setup/tests/downloads",
      "live IDS and accelerator gaps",
      "practice questions and worked answers"
    ],
    "source_references": {
      "answers": {
        "path": "docs/customer/answers.md",
        "sha256": "e293eb26550a2c1577c689ccac845ad0321be7bbf2fd41c6aeeedbad3c5565ab"
      },
      "comparison": {
        "path": "docs/customer/upstream-comparison.md",
        "sha256": "a84e5fbffabc2b6ccc44351203b4b61f9f95dee7608765e3ef427d54e121b5ba"
      },
      "results": {
        "path": "docs/customer/evidence/results.json",
        "sha256": "ead00597c0534a10d779e83805366c1cf323d231b1f7e94e9d001272e7641f1a"
      },
      "csv": {
        "path": "docs/customer/evidence/uploaded-csv-profile.json",
        "sha256": "f6d11f8c8c2d604ed6a6f2539c9c7fb93d1279997dd89cb84873de03c0547097"
      },
      "native": {
        "path": "docs/customer/evidence/native-data-validation.json",
        "sha256": "122bc8ba9a3ba2d53400b615b7b73a2d597e21063c478a96d852b3d7a7dd96f9"
      },
      "lesson": {
        "path": "docs/lesson.md",
        "sha256": "bcd7710396fc5f088de56df470f4c8c708336790af728d7940f57bcf2b888afa"
      },
      "transfer": {
        "path": "docs/customer/evidence/checkpoint-transfer.json",
        "sha256": "819195d7d3a9aaccf534ce2cca88e3986eb56facf0891fd7cbfe27e1149b520e"
      },
      "runbook": {
        "path": "docs/customer/runbook.md",
        "sha256": "854f19228fd384888cb268db20bf005785813df5c5fd6421110d81fcb95f49a0"
      },
      "config": {
        "path": "configs/ciciot2022.json",
        "sha256": "fba589310c98ea9f8838a0a14eb9cb2d6cfd13c4c8d219c6878e7508c68cab92"
      },
      "verification": {
        "path": "docs/customer/verification.md",
        "sha256": "88948b8336c729882a2a8835f69b03489161be769d3e6a4991a7ccc7a91bebbc"
      },
      "prediction": {
        "path": "docs/customer/evidence/seed0/replay/predictions.json",
        "sha256": "307fd521ce152b0614c091c882c11a11d80ba7de3ae923624ec31e6d1f59c68a"
      },
      "quickstart": {
        "path": "docs/customer/quickstart.md",
        "sha256": "6641b5d478ef02981014bf3d8c08f3f86c147de25e93ce9efc7dac5fae5d99bf"
      },
      "hardware": {
        "path": "docs/customer/hardware-roadmap.md",
        "sha256": "99cacacf535210e6517661595f0994e3899fd59787c58872a64c35f5bdc2be18"
      },
      "export": {
        "path": "docs/customer/evidence/export-probe/metrics.json",
        "sha256": "cef8a3811b33a4d350466368c3069b1d4dd2ed43ba0ebd9b5885378ff0d9ca04"
      },
      "benchmark": {
        "path": "docs/customer/evidence/benchmark/metrics.json",
        "sha256": "1f06ba04717400b0f20a7e79f7c90e8e0d357f8bf7f2c8507ccdfc969eec0e9b"
      },
      "walkthrough": {
        "path": "docs/repository-walkthrough.md",
        "sha256": "4d48e57f5e4e777b262199e34a04e57bdf26225bdad67d405c0b38aa1472ac98"
      },
      "contract": {
        "path": "docs/harness-reference.md",
        "sha256": "bebbb49d3489a8bad584aa944def395ef0912d7d079e3f22b29e5af035205baa"
      }
    },
    "queues": {
      "pending-content-reviews.json": {
        "sha256": "b656ac8f9597e6b6fbf9c10f6a5af8b27d38d2aeceb1f20cbde7c2e2733eee40",
        "modified": false
      },
      "video-refresh-queue.json": {
        "sha256": "dd34d57185a23d83c42c99113eed8c144941aca1e12a80e7108d36dae672af3a",
        "modified": false
      }
    }
  },
  "content_review": {
    "status": "completed",
    "reviewer": "Codex ordinary session",
    "completed_at": "2026-09-13T07:42:52.539556+00:00",
    "source_sha256": "4b1ac47ed54ceff5327b460dc366859de22c6c414f1edbe35827514c21f77b02",
    "spoken_scenes": 51,
    "scope": "Read complete resolved narration, all seven question mappings, every input and results distinction, wrapper commands, actual prediction error, and remaining IDS/NPU limits against the existing reference records. Includes sections omitted from the final council pack.",
    "reference_hashes": {
      "answers": {
        "path": "docs/customer/answers.md",
        "sha256": "e293eb26550a2c1577c689ccac845ad0321be7bbf2fd41c6aeeedbad3c5565ab"
      },
      "comparison": {
        "path": "docs/customer/upstream-comparison.md",
        "sha256": "a84e5fbffabc2b6ccc44351203b4b61f9f95dee7608765e3ef427d54e121b5ba"
      },
      "results": {
        "path": "docs/customer/evidence/results.json",
        "sha256": "ead00597c0534a10d779e83805366c1cf323d231b1f7e94e9d001272e7641f1a"
      },
      "csv": {
        "path": "docs/customer/evidence/uploaded-csv-profile.json",
        "sha256": "f6d11f8c8c2d604ed6a6f2539c9c7fb93d1279997dd89cb84873de03c0547097"
      },
      "native": {
        "path": "docs/customer/evidence/native-data-validation.json",
        "sha256": "122bc8ba9a3ba2d53400b615b7b73a2d597e21063c478a96d852b3d7a7dd96f9"
      },
      "lesson": {
        "path": "docs/lesson.md",
        "sha256": "bcd7710396fc5f088de56df470f4c8c708336790af728d7940f57bcf2b888afa"
      },
      "transfer": {
        "path": "docs/customer/evidence/checkpoint-transfer.json",
        "sha256": "819195d7d3a9aaccf534ce2cca88e3986eb56facf0891fd7cbfe27e1149b520e"
      },
      "runbook": {
        "path": "docs/customer/runbook.md",
        "sha256": "854f19228fd384888cb268db20bf005785813df5c5fd6421110d81fcb95f49a0"
      },
      "config": {
        "path": "configs/ciciot2022.json",
        "sha256": "fba589310c98ea9f8838a0a14eb9cb2d6cfd13c4c8d219c6878e7508c68cab92"
      },
      "verification": {
        "path": "docs/customer/verification.md",
        "sha256": "88948b8336c729882a2a8835f69b03489161be769d3e6a4991a7ccc7a91bebbc"
      },
      "prediction": {
        "path": "docs/customer/evidence/seed0/replay/predictions.json",
        "sha256": "307fd521ce152b0614c091c882c11a11d80ba7de3ae923624ec31e6d1f59c68a"
      },
      "quickstart": {
        "path": "docs/customer/quickstart.md",
        "sha256": "6641b5d478ef02981014bf3d8c08f3f86c147de25e93ce9efc7dac5fae5d99bf"
      },
      "hardware": {
        "path": "docs/customer/hardware-roadmap.md",
        "sha256": "99cacacf535210e6517661595f0994e3899fd59787c58872a64c35f5bdc2be18"
      },
      "export": {
        "path": "docs/customer/evidence/export-probe/metrics.json",
        "sha256": "cef8a3811b33a4d350466368c3069b1d4dd2ed43ba0ebd9b5885378ff0d9ca04"
      },
      "benchmark": {
        "path": "docs/customer/evidence/benchmark/metrics.json",
        "sha256": "1f06ba04717400b0f20a7e79f7c90e8e0d357f8bf7f2c8507ccdfc969eec0e9b"
      },
      "walkthrough": {
        "path": "docs/repository-walkthrough.md",
        "sha256": "8cb5b8c6aa2afb53e748ab552b63e944f9f896baa9dcca00eac50377b53c39a4"
      },
      "contract": {
        "path": "docs/harness-reference.md",
        "sha256": "bebbb49d3489a8bad584aa944def395ef0912d7d079e3f22b29e5af035205baa"
      }
    },
    "human_learning_review": "not performed"
  }
}
```
