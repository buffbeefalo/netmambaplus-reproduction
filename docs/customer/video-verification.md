# The NetMamba+ course video

[Watch the video](https://buffbeefalo.github.io/netmambaplus-reproduction/video/) · [Download MP4](https://github.com/buffbeefalo/netmambaplus-reproduction/releases/download/course-video-v1/NetMambaPlus-30-minute-course.mp4) · [Versioned release](https://github.com/buffbeefalo/netmambaplus-reproduction/releases/tag/course-video-v1) · [Full transcript](demo/video/transcript.md)

This is the actual narrated course requested after the interactive HTML lesson. It is **30:00, 1080p**, with 51 spoken scenes, nine announced practice intervals, chapter navigation, captions and a reflowing transcript. There is one continuous lesson and one main MP4 download. An internal VP9/Opus playback copy serves browsers without MP4 codecs; it is the same video, not another lesson. The voice is synthesized locally with Kokoro ONNX; no online narration service or cloned customer voice was used.

The course explains existing measured experiments. Playing it does not perform training, capture traffic, or establish additional accuracy. The measured mean remains **86.65%**, compared with the paper’s unreproduced **97.50%**. A complete human listening/watch-through has **not** been performed. Automated media checks and source review do not establish that human gate, learner mastery, or complete council acceptance.

## Watch, download or present

Use this as a handoff to the person who will explain the repository onward. Watch the complete route, practice the explanation aloud, and use the evidence links when the next person asks how a claim was established. The lesson explains every part’s role and the execution process; the file walkthrough supplies the individual inventory rather than reading 198 filenames aloud.

Open **Watch the video**, press Play and use the chapter links to seek. Download the MP4 for a meeting without internet access. Captions are already in the picture; the optional player text track and separate VTT/SRT files support other workflows. The complete transcript is visible below the player and reflows on a phone. Every substantive scene links to evidence.

The video has 27:00 of spoken explanation and worked answers and 3:00 of announced practice. The final practice is 90 seconds; pause the player for a longer presentation rehearsal. The separate HTML course retains its original reading/practice allocation and two-minute teach-back. These are different formats, not identical timing records.

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

The MP4 was completely decoded, probed for both streams and chapter offsets, and measured for long silences and audio levels. Every scene midpoint was extracted from the encoded MP4 and compared with the intended teaching layout, excluding the caption region. Actual boundary frames and practice countdowns were also extracted. Negative tests use shortened, missing-audio and silent versions of the encoded file; the CPU suite also rejects invalid caption timing and checksum changes.

Local speech recognition processed the entire encoded MP4 as a supplementary check. Its text contains recognition errors and omitted phrases; it is not the authoritative transcript or a human pronunciation review. The provided transcript comes from the reviewed narration source. Captions use measured sentence-wave timings, with proportional within-sentence breaks. Complete human listening, pronunciation review and the council’s ±0.5-second distributed caption-alignment gate remain pending; no automated decoding result is substituted for them.

All new teaching layouts are project-authored diagrams and tables, plus the project’s existing measured confusion-matrix figure. No paper page, stock photograph, song or external video was embedded. The [Kokoro model card](https://huggingface.co/hexgrad/Kokoro-82M) identifies Apache-2.0 weights and permits deployment; the [ONNX engine](https://github.com/thewh1teagle/kokoro-onnx/blob/main/LICENSE) is MIT licensed. [DejaVu’s font terms](https://github.com/dejavu-fonts/dejavu-fonts/blob/master/LICENSE) permit use; font/model/engine binaries are not redistributed in the release. This review does not settle the separately documented inherited NetMamba+ source, data and checkpoint terms.

The pending course-content and video-refresh queues were inspected. No NetMamba-specific fleet entry was present; unrelated pending/failed work remains visible and unchanged. This is a repository-based video build, not a claim that the shared fleet video worker completed or that other courses are current.

## Council review

The two-seat review was **CONSENSUS / RATIFIED**, run `763a3a96-4155-4f0b-9dc4-873c1422b9dc`, Fable 5/high and Astra 6/max. Exact canonical decision SHA-256: `812de7b76131f1eb983a0d2082adefc553f01b9ea006ceffcb293e4c37d31ddd`. [Canonical decision and acceptance checks](../research/video-council-decision.json).

Implementation was performed directly under the user’s standing authorization. This review-only artifact has `delivery: null`; it was not broker `DELIVERED`. The council defined acceptance criteria before the final media existed. Its human-review requirements remain pending. The earlier static-course council and original experiment decisions remain historical and unchanged.

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
| 03:26–04:01 | inputs-03: Why five neighboring rows are insufficient | flow | comparison |
| 04:01–04:41 | inputs-04: The data actually used | cards | native |
| 04:41–05:16 | inputs-05: Native input is a defined contract | code | native, contract |
| 05:16–05:29 | inputs-06: Input decision | question | csv, comparison, native |
| 05:29–05:41 | inputs-07: Your turn · 12 seconds | pause | csv, comparison, native |
| 05:41–06:00 | inputs-08: Answer: establish compatibility first | answer | comparison |
| 06:00–06:38 | lifecycle-01: Three views become tensors | flow | lesson |
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
  "status": "automated_media_checks_passed_publication_pending",
  "completed_at": "2026-09-13T06:59:52.479121+00:00",
  "source_sha256": "ace0c090ab6a702a00f2092e96d88db92c442ea142471f5cfff10ad221f171d4",
  "media_manifest_sha256": "e8f776a044dee710c1c2478ba9fae72790a7fb9c7b7c3808330e38d796ffd1f3",
  "artifacts": {
    "NetMambaPlus-30-minute-course.mp4": {
      "bytes": 37869975,
      "sha256": "afc302395c9606e16300ab4910c2a43da3b22c979a1dd2999cff5b88bfc3a829"
    },
    "captions.srt": {
      "sha256": "1f7c17cd65086a7939945f70db1983182647cdaf6642c98ad95f2f9475a2e918",
      "bytes": 38036
    },
    "captions.vtt": {
      "sha256": "5cf0504c070d40aede44c3612f7879c4deca3784fafe3001f090297a83e8047c",
      "bytes": 36500
    },
    "transcript.md": {
      "sha256": "e48a599556f8b755f25c9d372ee3c2eee8dd852abbfbf106d221fe01d99b15a8",
      "bytes": 47522
    },
    "chapters.json": {
      "bytes": 1087,
      "sha256": "6ad2199cf458ff51499254cab4fc6ef9be4b57e7b24508f3c2379547e501764b"
    },
    "NetMambaPlus-30-minute-course.webm": {
      "bytes": 37055191,
      "sha256": "12bba939e07caebb06ce1c07da347078440b5b79c6448bbc423e0428d17de7ec"
    },
    "poster.png": {
      "bytes": 56780,
      "sha256": "a8ca1a7ffceccbb0e36650113dd579361dd5733ea1649da7a772a120d0b0311a"
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
        "bit_rate": "75167",
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
    "completed_at": "2026-09-13T06:44:50.737532+00:00",
    "mp4_sha256": "afc302395c9606e16300ab4910c2a43da3b22c979a1dd2999cff5b88bfc3a829",
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
    "decode_log_sha256": "75bcd6ae77f749c1d637cd307b5db5d38b4508e2d6b7f2858f5291db851c295b",
    "human_full_playback_review": "pending; automated decode is not a listening review"
  },
  "browser_playback_copy": {
    "file": "NetMambaPlus-30-minute-course.webm",
    "source_mp4_sha256": "afc302395c9606e16300ab4910c2a43da3b22c979a1dd2999cff5b88bfc3a829",
    "full_decode_exit_code": 0,
    "scope": "Compatibility encoding of the same single course."
  },
  "image_checks": {
    "status": "passed",
    "scene_midpoints_compared": 60,
    "maximum_mean_absolute_pixel_difference": 2.161059640522876,
    "limit": 3,
    "crop": [
      0,
      0,
      1920,
      850
    ],
    "chapter_boundary_samples": [
      0.2,
      120.2,
      360.2,
      600.2,
      780.2,
      1020.2,
      1260.2,
      1500.2,
      1620.2
    ],
    "receipt_sha256": "8b9e4beed3b5d5b791a11d1e9db3f90ba7bacf62039c178a50649283a97e3eb5",
    "visual_samples_reviewed": [
      "measurements-02",
      "measurements-03",
      "inputs-05",
      "demo-04",
      "teach-back-02"
    ],
    "reviewer": "Codex visual inspection; not human full playback",
    "chapter_boundary_comparisons": [
      {
        "chapter": "purpose",
        "time": 0.2,
        "mean_absolute_pixel_difference": 2.096026348039216,
        "frame_sha256": "d2192a93c1032905df04f0e2ea2a7cf3c48433a7f23e4761a4ba74c7ce8e45a6"
      },
      {
        "chapter": "inputs",
        "time": 120.2,
        "mean_absolute_pixel_difference": 2.0864873366013073,
        "frame_sha256": "82fafcd1e5be75e1b6ab59b8377bf6f3d9f3c2ab64a03476f2821af651296474"
      },
      {
        "chapter": "lifecycle",
        "time": 360.2,
        "mean_absolute_pixel_difference": 2.092038602941176,
        "frame_sha256": "e8017102b83c9ab455826cad6979c0167a68f98336c955f371091e461700a2bb"
      },
      {
        "chapter": "repository",
        "time": 600.2,
        "mean_absolute_pixel_difference": 2.083325776143791,
        "frame_sha256": "5efbc294afa7acd908bcb60fe3e6ed5f588af7ab7bdb4e0cc9fa6006820b0713"
      },
      {
        "chapter": "measurements",
        "time": 780.2,
        "mean_absolute_pixel_difference": 2.0785210375816994,
        "frame_sha256": "cc2e214eb7f86e6d27257af4cc1ce88f05cf2bba70d580c050556c672af0d293"
      },
      {
        "chapter": "demo",
        "time": 1020.2,
        "mean_absolute_pixel_difference": 2.0728086192810458,
        "frame_sha256": "61c132a0f35c1226412756b660f6432b867dc3777187cf1cade727cd250b66be"
      },
      {
        "chapter": "operate",
        "time": 1260.2,
        "mean_absolute_pixel_difference": 2.0946468545751635,
        "frame_sha256": "a3a15c4b9d9a16544a65a950395f4d6ef5235720bbedff16f0ff693fdb1e0aaf"
      },
      {
        "chapter": "future",
        "time": 1500.2,
        "mean_absolute_pixel_difference": 2.126423815359477,
        "frame_sha256": "1509e45ae8f8e5711649312bf3cba82280289b39d12fd31f9f8d5a4664986e0e"
      },
      {
        "chapter": "teach-back",
        "time": 1620.2,
        "mean_absolute_pixel_difference": 2.109372140522876,
        "frame_sha256": "52c6be5d82feda7c61cdf9518b9b87a546219cfee31e8c23e1e02bacba5d9041"
      }
    ]
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
    "limitations": "Recognition errors remain in ASR output; not the authoritative transcript or human listening."
  },
  "negative_media_checks": [
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
  "local_browser": {
    "status": "passed",
    "url": "http://127.0.0.1:8787/video/",
    "completed_at": "2026-09-13T06:58:14.896479+00:00",
    "browser": "Chromium 140.0.7339.16; Playwright 1.55.0",
    "html_sha256": "607874ee5f33af05de1f317cd9af4871795230c50019ed92abc6d700c8494ba1",
    "mp4_sha256": "afc302395c9606e16300ab4910c2a43da3b22c979a1dd2999cff5b88bfc3a829",
    "decoded_frames_and_audio_bytes": {
      "audio": 15463,
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
      "video-390.png": "e6630cb722d60f8e1757116a82f70a38253b12514f7470e425606b0428f2f36f",
      "video-320.png": "14c4f71a232c0aef1222b5dea5fdf1ee2d8f74d235aa6fa34b847ab777a4cde8",
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
  "content_review": {
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
    "detail": "78 tests passed: 54 harness, 17 interactive-course, 7 video. The isolated stale-HTML fixture now includes the new navigation target.",
    "receipt": {
      "completed_at": "2026-09-13T07:04:01.124551+00:00",
      "command": "python3 -m unittest discover -s tests -v",
      "exit_code": 0,
      "tests": 78,
      "output_sha256": "43ac81c6562f7a71d566886e7f28ccabdbd52cac59fe9bdd5a97fc664acb6795"
    }
  }
}
```
