# Current CSV video and companion verification

The v5 lesson explains **both uploaded CSVs, the paper and both repositories through one supported packet workflow**. [Watch](https://buffbeefalo.github.io/netmambaplus-reproduction/video/) · [PowerPoint](demo/video/v5/NetMambaPlus-course-slides.pptx) · [Slide PDF](demo/video/v5/NetMambaPlus-course-slides.pdf) · [Searchable handbook](demo/video/v5/NetMambaPlus-course-handbook.pdf) · [Transcript](demo/video/v5/transcript.md).

The final local media checks passed on 2026-09-14: **60:00, 1080p, 30 fps**, complete MP4 and WebM decode, all 84 encoded speech passages transcribed and reviewed, 96 static scenes checked, and 117 encoded visual samples checked. Chromium played picture and audio, sought to all twelve chapters and near the end, loaded captions, downloaded the exact MP4, and displayed without overflow at four viewport widths. The 96-slide PowerPoint, 96-page slide PDF and 111-page handbook match the final lesson; all 796 individual guide entries are included. Read the [bound review and its limits](../research/video-v5-review.json), [six acceptance records](../research/video-v5/) and [publication record](../research/video-v5-publication.json) for exact identities, CI and live-site status.

Codex wrote and reviewed the text, directed the diagrams and assembled the video. Microsoft Andrew Multilingual neural speech renders that text through the pinned edge-tts 7.2.7 client; the provider model revision is unavailable. Local speech recognition checks encoded audio independently. It did not write the lesson. A complete human watch/listen-through and universal pronunciation acceptance are not claimed.

## What this edition changes

The previous v4 video taught historical flow/calibration work. V5 follows both CSVs into the native packet adapter and selected joint pretrained classifier. It explains the two repository roles, actual source-to-client export process, required inputs, setup, tests, results, demo and hardware limits. Old v3/v4 bytes and their historical audits remain preserved; `/course/` stays retired.

The five new animation types show payload versus ignored metadata, exact-payload grouping, the 378-token encoder, forward/loss/backward/update, and verified export from reproduction to client. Emphasis follows measured narration cues. A real recording of the offline packet viewer switches sources and inspects a saved error. That recording is a replay of measured predictions, not fresh model inference.

The same reviewed JSON source supplies the video, transcript, captions, 96 slide images and speaker notes. The handbook contains searchable narration, examples and the every-file guide. Scientific values are checked against 60 primary JSON bindings and code-derived model dimensions. Recorded Git baseline commits identify project history; the lesson's SHA-256 identifies its exact source bytes.

## Questions and where they are answered

| Question | Chapter and PowerPoint / slide-PDF pages |
|---|---|
| What was tried and what works now? | Orientation 1–8; learning 41–48; results 57–64; setup 73–80 |
| How do training and inference work? | Features 33–40; learning 41–48; code 49–56 |
| What goes in and comes out? | CIC 17–24; UNSW 25–32; features 33–40; code 49–56 |
| What was reproduced versus reported in the paper? | Paper 9–16; results 57–64 |
| What does a simple working IDS demo look like? | Demo 65–72 |
| How could it map to an NPU or SmartNIC? | Hardware 89–96 |
| What is missing or not working? | Paper 9–16; results 57–64; hardware 89–96 |
| What belongs in each repo and how do updates work? | Orientation 1–8; repository 81–88 |

The player and transcript provide the measured chapter timestamps. Every chapter ends with a labeled practice prompt; pause longer as needed. The course explains each subsystem, while the [file guide](../repository-walkthrough.md) and handbook appendix explain individual files and downloads.

## Model results retain their original scope

The selected joint pretrained model measured **97.56% CIC / 94.29% UNSW group-weighted balanced accuracy**. Six native arms each completed 1,000 updates; nine controls completed. The UNSW-only metadata control measured **99.34%**, above the neural models there. These are recorded packet-study outcomes, not new training performed by the video build or reproduction of the paper's different 97.50% flow accuracy.

The original inference comparison agreed on all 25,930 classes and retained two strict logit-comparison failures. The fresh client check validated 20,000 CIC rows, predicted 128 and agreed on all 128 classes while retaining 76 strict logit failures. The scopes stay separate throughout the lesson. A success from an evidence checker confirms that record, including its failures.

One model seed, capped groups, replacement sampling, weak transfer, sparse subtype support and unknown pretrained exposure limit generalization. Live capture/blocking, independent customer evaluation, calibrated packet confidence, operational thresholds and NPU/SmartNIC execution remain unestablished. Read the [client project guide](client-project-guide.md) and [packet report](packet-model-study.md) before presenting the measurements.

## Recheck or rebuild

A full source clone supplies historical Git-bound checks. Portable verification does not require raw CSVs, model weights or a GPU:

```text
python -m unittest discover -s tests -v
python tools/verify_video_course_v5.py
python tools/verify_repository_guide.py
python tools/build_video_page.py --check
python tools/verify_video_course_v3.py
python tools/verify_video_course_v4.py
python tools/review_packet_study.py
```

For real native execution, follow the [single packet setup](packet-study-setup.md), including the separate 17-case GB10 packet gate. Its existing native evidence is distinct from portable media tests.

A media rebuild requires the document environment (Pillow, python-pptx, ReportLab and edge-tts 7.2.7), DejaVu fonts, and FFmpeg/FFprobe with libass, H.264/AAC and VP9/Opus support. Pass actual executable paths; the command placeholders below are not literal paths. Narration generation makes speech-service requests; matching scene caches avoid repeated requests, and failures remain logged.

```text
python tools/narrate_video_neural.py \
  --source docs/customer/video-course-v5-source.json \
  --output runs/video-course/v5-packet/tts --ffmpeg /path/to/ffmpeg
python tools/build_course_video.py \
  --source docs/customer/video-course-v5-source.json \
  --work-dir runs/video-course/v5-packet/render \
  --narration-dir runs/video-course/v5-packet/tts \
  --output docs/customer/demo/video/v5 --ffmpeg /path/to/ffmpeg
python tools/build_course_video.py --webm-only \
  --source docs/customer/video-course-v5-source.json \
  --output docs/customer/demo/video/v5 --ffmpeg /path/to/ffmpeg
python tools/build_video_documents.py \
  --source docs/customer/video-course-v5-source.json \
  --work-dir runs/video-course/v5-packet/render \
  --output docs/customer/demo/video/v5
python tools/build_video_page.py
```

Independent speech checking uses the locally installed `faster-whisper` package and cached `Systran/faster-whisper-small.en` model. The recorded environment uses version 1.2.1 on CPU with int8 calculations; it does not invoke an authoring LLM or download a model during the audit. After rendering, run:

```text
python tools/audit_video_speech.py \
  --media docs/customer/demo/video/v5/NetMambaPlus-CSV-workflow-course.mp4 \
  --manifest docs/customer/demo/video/v5/media-manifest.json \
  --output runs/video-course/v5-packet/asr-new \
  --model-dir /path/to/cached-asr-models \
  --ffmpeg /path/to/ffmpeg --expected-scenes 84
```

The v5 document builder registers its three generated companions and companion manifest in the media manifest, so the subsequent page build exposes their download links. The regression check exercises this sequence with real document rendering and also confirms that archived manifests remain unchanged.

Generation alone is not acceptance. Any rebuild must rerun media decoding, word/caption inspection, visual and document review, actual browser playback, final identity checks and publication checks. The dedicated verifier fails without those separate, source-bound receipts. Use `--source-only` while editing to check source facts and topic presence without claiming media acceptance.

The [council record](../research/video-v5-council.json) remains **ESCALATED**, with no mutual decision hash. Its bounded evidence pack omitted large implementation/evidence files. Direct review of those files resolved the concrete design questions under the user's standing implementation authorization. That work does not retroactively create council consensus.
