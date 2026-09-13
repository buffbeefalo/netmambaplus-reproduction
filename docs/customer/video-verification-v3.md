# NetMamba+ — the complete one-hour course

[Watch the course](https://buffbeefalo.github.io/netmambaplus-reproduction/video/) · [Download the MP4](https://github.com/buffbeefalo/netmambaplus-reproduction/releases/download/course-video-v3/NetMambaPlus-one-hour-course.mp4) · [PowerPoint with speaker notes](demo/video/v3/NetMambaPlus-course-slides.pptx) · [PDF handbook](demo/video/v3/NetMambaPlus-course-handbook.pdf) · [PDF slides](demo/video/v3/NetMambaPlus-course-slides.pdf) · [Transcript](demo/video/v3/transcript.md)

This is **one continuous 60:00 course**, with 12 chapters, 96 teaching scenes and a new voice: **Microsoft Andrew Multilingual Neural**. Codex wrote the explanation, designed the visuals, directed production and reviewed the resulting artifacts. The speech service renders the supplied text; a local language model did not write this lesson. Offline speech recognition was used afterward as a fallible audit tool.

The course starts with packets, headers, payloads and flows, then explains the attached paper, both CSVs, the compatible data used for training, the original model, the added repository tools, measured results, setup, tests, downloads, the recorded demo and the hardware roadmap. The [67-page handbook](demo/video/v3/NetMambaPlus-course-handbook.pdf) contains the complete script and an appendix explaining **all 341 repository files**. The PowerPoint has **96 slides with editable speaker notes**. Its pictures match the video's base teaching frames; individual diagram objects are not editable PowerPoint shapes.

The scientific result remains a **measured reproduction attempt**: three completed fine-tuning runs averaged **86.65%**, versus the paper's **97.50%, which was not reproduced**. This video production did not run another training experiment. Model execution, dataset independence, live IDS operation and NPU/SmartNIC deployment have different evidence and limitations, explained in the course.

## Use it for the handoff

Open the watch page and press Play. The chapter controls let you revisit a topic; the complete transcript below the player reflows on smaller screens. Download the MP4 for an offline meeting. Open the PowerPoint's Notes view for the matching narration, or use the searchable PDF handbook while explaining the repository. Viewing these files needs no GPU, Python environment or AI account.

The course allocates **56:40 to explanations and scene transitions**, plus **3:20 of announced practice**. The final practice lasts 90 seconds and is followed by a worked closing explanation. Pause longer whenever you need. There is one promoted lesson; the equivalent VP9/Opus file is an internal browser playback copy of the same MP4. Both are 1920×1080 at 30 frames per second.

| Your question | Start here | What the course establishes |
|---|---|---|
| What was tried and what works? | 00:00; 30:00; 34:46 | Original-source execution on GB10, short pretraining, three full fine-tuning runs, strict evaluation, inference and recorded replay, with evidence boundaries. |
| How do training and inference work? | 20:06; 25:00 | Three input views, normalization, 443 tokens, four Mamba blocks, masked reconstruction, labeled fine-tuning, validation selection and frozen inference. |
| What data goes in and comes out? | 09:59; 15:00; 20:06 | Both packet CSVs, their fields and labels, their incompatibility with unproven flow grouping, native CICIoT2022 flow objects and six output scores. |
| What was reproduced versus reported? | 04:43; 34:46 | Every seed, the mean and sample spread, unreproduced paper accuracy, protocol differences and overlap/pretraining-exposure limits. |
| What could a simple IDS demo look like? | 39:33 | Actual recorded replay controls, saved predictions and a concrete confident-looking error. Live capture and alert policy remain additional work. |
| How could it map to an NPU/SmartNIC? | 53:53 | Proposed capture, flow preparation and inference responsibilities; measured model-only timing; actual graph-export failure and target validation steps. |
| What remains missing? | 53:53; closing explanation | Compatible live extraction, independent traffic validation, calibration, operational alerting, operator portability and inherited asset terms. |

Setup and testing begin at **44:01**. The file-by-file route begins at **48:49**. [Every file and download](../repository-walkthrough.md) has an individual entry; [the paper and both datasets explained](paper-and-data-explained.md) supplies deeper paper-section and label detail. The video explains the systems and worked examples, while the companion carries the complete filename inventory.

## What was actually checked

The [structured audit](../research/video-audit-v3.json), [coverage map](video-course-v3-coverage.json) and [artifact manifest](demo/video/v3/manifest.json) distinguish measurements, Codex review and pending human acceptance. These records preserve failures and the corrections that followed them.

| Check | Observed result |
|---|---|
| Complete MP4 decoding | All 108,000 video frames and the complete audio stream decode; measured duration **3600.000 seconds**. |
| Complete browser-copy decoding | All 108,000 frames and complete audio decode; measured container duration **3600.008 seconds**. |
| Encoded audio | MP4 **−16.4 LUFS**, **−0.9 dBFS true peak**; browser copy **−16.4 LUFS**, **−0.8 dBFS true peak**. No clipping. Every silence of at least three seconds falls within the declared practice windows, allowing one second for speech tails and padding. |
| Static and encoded pictures | All **96** base visuals reviewed individually; **239** exact-index MP4 samples match the expected picture, timed motion and captions. Another **20** browser-copy samples match the MP4 within the recorded compression tolerance. |
| Captions and scientific quantities | All **1,073 VTT/SRT cues** match the source text and scene windows. **13** required quantities match pinned evidence, units, rounding and scene attribution. |
| Independent encoded speech | All **84** spoken passages transcribed and reviewed; all chapters represented. Timing diagnostics classify **734** speech cues within half a second of the ASR reference and **327** as uncertain, plus **12** practice cues. No confirmed actionable timing correction emerged from the investigated flags. |
| Documents | All **96** PPT notes and images match; all **96** PDF slide images match. The **67-page** handbook preserves all **84** full narrations and **341** complete file entries, with **707** link annotations. Representative actual pages are readable without clipping; PDF/PPT UTC metadata is corrected. |
| Browser controls | Picture and audio playback, all **12** keyboard chapter seeks, near-end playback, all captions, exact MP4 download bytes, and no horizontal overflow at **320, 390, 768 and 1440 pixels**. |
| Historical evidence | All **133** protected original files and the protected v2 artifacts retain their recorded bytes. The archived HTML lesson only received the reviewed file-guide reference refresh; its lessons and answers are unchanged. The retired `/course/` route remains excluded from deployment. |

The complete local suite, portable checks, CI and publication results are recorded with their precise revisions in the structured audit. Portable checks verify code and evidence on their stated systems; they do not establish native model execution on every operating system or GPU.

The new animations show packet grouping, the byte layout, token assembly, training stages, code emphasis, measured-result reveals and a real recording of the replay controls. Frame checks include chapter transitions, important quantities, technical identifiers, caption areas, practice countdowns and recorded-clip boundaries. The screen recording is labeled as a replay of saved predictions; it does not imply live network inference.

## Review limits and useful precision

**A human has not watched and listened to the complete final hour or accepted every caption.** Automated decoding, source review and speech recognition do not establish subjective voice quality or perfect pronunciation. The speech audit retains a notable `arXiv`/“AR14” recognition ambiguity at **04:52–04:53**, plus other uncertain words and acronyms. The visible paper identifier and captions are correct. These uncertainties are not certified pronunciation passes.

The lesson's general definition of an embedding is simplified. In the pinned implementation, the size and interval base value encodings use fixed sine/cosine functions; learned position and modality components are then added. See [the original value-encoding implementation](https://github.com/wangtz19/NetMambaPlus/blob/eec9483e2f0fb84ca22982b9de8149bc3a8b1ad2/src/models/common.py#L82) and the [tensor explanation](../lesson.md). This distinction does not change the reported token or parameter counts.

The handbook prints the file guide's Mermaid block as readable source text rather than a rendered diagram. Its surrounding explanation, links and file descriptions remain present. The course video supplies the teaching diagrams. Speech generation pins the `edge-tts` client to **7.2.7**, but Microsoft does not expose an immutable provider-model revision; new service calls are not promised to produce byte-identical speech. Recorded output hashes identify the actual voice files used here.

## Set up, test or rebuild

For ordinary repository checks, use Python 3.10 or later. These commands do not train a model or require CUDA:

```bash
git clone https://github.com/buffbeefalo/netmambaplus-reproduction.git
cd netmambaplus-reproduction
python -m unittest discover -s tests -v
python tools/verify_package.py
python tools/verify_course_video.py
python tools/verify_video_course_v3.py
python tools/build_video_page.py --check
```

For actual model execution, follow the [support matrix](../support-matrix.md) and [runbook](runbook.md). Compatible Linux/NVIDIA hardware, compiled CUDA extensions and separately acquired verified research assets are required. CPU evidence checks passing on Windows or macOS do not mean the original CUDA classifier runs natively there.

To repeat the MP4 decode/audio measurement, install FFmpeg and choose a fresh output directory:

```bash
python tools/verify_course_video.py --decode-output runs/my-video-check --ffmpeg ffmpeg --ffprobe ffprobe
```

The browser option needs `requirements/browser.txt` and Playwright Chromium:

```bash
python tools/verify_course_video.py --browser-output runs/my-browser-check --url https://buffbeefalo.github.io/netmambaplus-reproduction/video/
```

Production was executed on Linux with Python 3.12, DejaVu fonts, FFmpeg with libass/libx264/libvpx/libopus, and the pinned packages in `requirements/video-neural.txt` and `requirements/video-documents.txt`. A new voice request needs network access. The commands below describe rebuilding; a source edit also requires genuine content review and fresh acceptance records before publication.

```bash
python -m pip install -r requirements/video-neural.txt -r requirements/video-documents.txt
python tools/narrate_video_neural.py --output runs/video-course/v3-neural/tts --ffmpeg ffmpeg
python tools/build_course_video.py --ffmpeg ffmpeg
python tools/build_course_video.py --webm-only --ffmpeg ffmpeg
python tools/build_video_documents.py
python tools/build_video_page.py
```

Use a separate work and output directory for a preview; `--narration-dir` can read the full speech cache without overwriting its schedule. The speech adapter makes one bounded request per uncached scene, retains word timing and exact output identities, and stops on a failed attempt. Renderer and document checks reject stale source or frame hashes. The browser encoding preserves 1080p/30 fps and uses the documented screen-content compression profile to stay below the Git single-file ceiling. Regenerating media alone does not manufacture a passed coverage or review receipt.

## Council and publication contract

The Fable/Astra council established the v3 design and acceptance contract in run **`50d233f3-7cf9-4433-a7c6-46a28a949039`**, outcome **CONSENSUS / RATIFIED**. Its exact canonical [decision JSON](../research/video-v3-council-decision.json) has SHA-256 **`ccf15591f6d9ad08151aca425c47ce17a75e6bc72b5da2a8e05af0c4098c98ea`**.

> Build one Codex-authored, chaptered v3 full course targeting 60 minutes, with acceptance based on 58–65 minutes of measured playback. Use a worked journey supported by a complete file-level companion, substantive paper coverage and explanations of both CSVs. Author modular chapters and assemble one continuous course. Complete the mandatory read-only preflight before edits; this draft does not establish that the uninspected pipeline satisfies its requirements. Stage and verify before replacing current navigation. Preserve historical releases, protected evidence and the retired /course/ route. Human full-watch and all-caption acceptance remain explicitly pending and are not, by themselves, publication blockers under this new v3 standard. Known material defects block publication. Ordinary root implementation proceeds under standing authorization without approval pauses; binaries and external publication are outside broker file delivery.

This is a design decision, not mutual final-media certification. Codex performed the scoped implementation and independent agent reviews under the standing implementation authorization; no broker `DELIVERED` outcome is claimed. Earlier council outcomes, including the v2 escalated quality review, remain historical. The original protected customer landing document remains unchanged; the root README and this new receipt provide the current course route.

The additive **`course-video-v3`** release is a prerelease and does not replace the original customer release as GitHub's `latest` destination. Earlier video releases and original customer attachments remain unchanged. The old customer ZIP retains its original snapshot; the new course downloads and current repository provide this later work. The structured audit records anonymous download hashes, public browser checks and the tested release revision when publication verification completes.
