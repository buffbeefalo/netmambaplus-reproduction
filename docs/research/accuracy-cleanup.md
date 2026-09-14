# Repository cleanup and accuracy audit — 14 September 2026

The published baseline was commit `c90153e4e5048cb29af9ea8ff7dbd38820b96dc1`. The main defect was inconsistent current-facing documentation: older setup instructions and CSV-profiling statements looked like the complete current status. The recorded packet metrics and presentation values matched their evidence when rechecked. This cleanup corrects navigation and scope, adds a presentation regression check, and preserves the original experiments and media.

Start with the [current customer index](../customer/README.md), [quickstart](../customer/quickstart.md), [seven-question acceptance map](../customer/acceptance.md) and [every-file guide](../repository-walkthrough.md). The [machine-readable audit evidence](accuracy-cleanup-evidence.json) retains the concrete checks, downloaded ZIP identity and versioned handoff manifest. All 13 listed presentation/media/script files matched their recorded Git editions byte for byte.

## Corrections applied

| Finding | Applied correction |
|---|---|
| Customer index advertised only the old 16-slide package | Replaced it with a current index separating packet, flow/calibration and archived flow-only editions |
| Quickstart said 54 tests and untested Windows/macOS, and treated a ZIP as equivalent to current Git history | Added four current routes; linked actual six-platform CI; explained optional skips, full-clone requirements and the older ZIP's scope |
| Acceptance and FAQ still said the CSVs had not trained a classifier | Updated them with completed packet training, nine controls, real inference and exact numerical limits |
| Paper/data and upstream-comparison bodies described only the original metadata scans | Integrated the later full byte validation, packet adapter, two-class head, training/control results and distinction from the original flows |
| Support matrix linked the earlier 94-test revision | Linked the published 412-test baseline and current audit; added packet execution and presentation checks without claiming a new physical platform |
| Root README and file guide called now-current instructions frozen | Corrected those descriptions, shortened the main download table and added individual entries for every new audit/checker file |
| New packet presentation lacked a portable result-to-document regression gate | Added `tools/verify_packet_briefing.py` and ten negative/positive tests; included it in six-platform CI |
| The README's `build_course.py --check` compared current reference prose with an old hash | Reused the existing immutable historical verifier for check mode, preserving exact source/HTML/receipt protection and the retired route; added a real CLI regression and CI command |
| Generic final-review links could imply the historical ratification covered later work | Identified each review by experiment and date; preserved every council outcome |
| Hardware FAQ omitted the implemented calibration and packet routes | Added those scopes, preserved unimplemented deployment boundaries and rechecked NVIDIA's GPUNetIO documentation |

The packet document checker follows the actual PowerPoint presentation order and attached speaker-note relationships, compares all visible slide text and the script with evidence-derived source, and verifies the reviewed PDF/PPT/source/script fingerprints. Its regression cases reject stale measurements, wrong visible scores, changed notes/scripts, reordered slides, misattached notes, a modified PDF and an incomplete receipt. Refreshing hashes alone cannot make those content mismatches pass. The checker does not render PowerPoint or independently establish PDF visual quality.

A complete README-command rehearsal exposed the course-builder failure `Evidence reference hash changed: comparison`. The existing historical verifier already handled current-reference changes correctly; the builder was passing an explicit current source and bypassing that path. Check mode now uses the existing historical entry point. The new regression failed with that original error before the fix and verifies successful historical checking without changing the retired source, HTML or receipt afterward. Rendering behavior outside check mode remains strict about its supplied source.

## Evidence rechecked

The starting standard-library suite passed **412 tests discovered: 376 passed, 36 optional checks skipped**. The final local suite passed **423 tests discovered: 387 passed, 36 optional checks skipped**, in 22.011 seconds. This includes ten new presentation cases and one historical-builder CLI regression. All **eleven repository verification commands** passed, and the every-file guide covered **610 files**. The linked audit evidence records the commands, results and code identities; GitHub CI checks published revisions separately. A skip is not a native GPU pass.

| Check | Observed result and limit |
|---|---|
| Raw source identities | Rehashed both actual uploaded CSVs: 4,910,831,729 and 270,111,802 bytes; SHA-256 identities match the registered inputs |
| Prepared data integrity | Revalidated every prepared array's identity, shape, payload hash, split membership and selected support; 438,886 CIC and 39,168 UNSW per-source groups |
| Native packet metrics | Recomputed all 12 test sets across six models from retained predictions; separate NumPy/scikit-learn calculations agree |
| Controls and comparable populations | Recomputed all 18 control test sets; source membership and group/row counts checked; all nine controls completed and six logistic fits converged |
| Headline packet values | Exact JSON values round to 97.56% joint-pretrained CIC, 94.29% joint-pretrained UNSW, and 99.34% UNSW-only metadata control on UNSW, all with one total weight per distinct payload within source |
| Completion versus selection | All six native runs completed 1,000 updates. CIC/UNSW scratch selected step 100; the other four selected step 1,000. Rehashed all six local selected checkpoint files |
| Saved unlabeled inference evidence | All 25,930 classes agree. The matched FP32 record retains two strict CIC logit-tolerance failures; the later 128-row portability check remains separately scoped |
| Packet PDF/PPT/script | All eight source titles and result cells matched the actual PDF text and PPTX XML; all eight attached notes matched the script; four artifact identities matched the reviewed receipt |
| Original package, calibration, historical courses/videos and active page | Existing verification commands rerun; original scientific/media records retain their own scopes. No fresh full video decode or human full-watch acceptance is claimed by this cleanup |
| Paper | Re-extracted the supplied v1 PDF and checked the recorded pretraining/fine-tuning settings, 97.50% Table IV result and separate byte-only online prototype figures |
| Hardware documentation | NVIDIA's current [GPUNetIO documentation](https://docs.nvidia.com/doca/sdk/doca-gpunetio/) still identifies DGX Spark as lacking GPUDirect RDMA and documents a CPU/GPU memory/proxy route; that route was not executed in this project |

The raw CSV hashes bind this audit to the earlier exhaustive byte validation; this cleanup does not claim a second raw-cell parsing/training experiment. Recomputing saved measurements checks their arithmetic and consistency, not independence from the original captures or a checkpoint's unknown pretraining exposure. The evidence reviewer checks recorded provenance; arbitrary coordinated rewriting of every underlying record would not create independent proof of execution.

## Actual inspection of the historical download

The advertised release ZIP was anonymously downloaded from the explicit `customer-2026-09-15-audited` tag. Its **3,634,849 bytes** have SHA-256 **`dc81df8442ac29f81a5a27e4a4f7ec277e76709204d3204aeb8cacea22ad9b8a`**, matching the published release inventory and checksum.

Its 214 ZIP entries contain **173 tracked files**, directories and a `SOURCE-COMMIT.txt` marker. Every tracked file matched Git revision **`17b4aaebcf9327ae9967ca45ddfaf16325766993`** byte for byte; all **133 embedded package checksums** matched. No historical code was executed during inspection. This ZIP contains neither the later calibration addition, the one-hour v4 course nor the packet study. Current download links label that edition explicitly; the separately checked current packet documents remain directly available through the repository.

## Council findings and direct resolution

Run **`7b5313e7-d426-4af7-a5ca-35db5cb14288`**, Claude Fable 5/high and GPT-6 Astra/max, ended **ESCALATED / UNRATIFIED**, with `mutual: false` and no decision hash. The exact [result JSON](accuracy-cleanup-council.json) has file SHA-256 **`7c6553eff9bb319ec88b81f86d581532f43832b92404f5ccfff751e45981b5f1`**. This is an artifact fingerprint, not a ratified decision hash.

Both seats favored focused corrections and preserving historical files. They could not establish packet metric integrity, bounded reproducibility and the ZIP's edition/contents from their bounded evidence pack. Requests for primary result and setup files were excluded by the pack budget. They identified verification gaps, not a demonstrated wrong score or broken download.

The ordinary session directly addressed those gaps: independent recomputation of all packet/control populations, source/setup/checkpoint and inference-receipt review, and actual ZIP member/hash inspection. These actions use the user's implementation authorization. They do not change the council record, constitute consensus, or claim broker delivery. No replacement council or provider-stop bypass was used.

## Retention and remaining limits

The audited baseline contained 605 tracked files and approximately 533 MB of working-tree file bytes, mostly media. No tracked temporary/bytecode junk was found. Earlier videos, their two browser encodings, the original deck/briefing/scripts, frozen protocols and result records have provenance and reference consumers, so they were retained. No Git history was rewritten, raw data or checkpoints deleted, or unrelated work changed. The cleanup improves the current entry points; it does not claim to shrink Git history.

The source and shared lesson references were reviewed for the updated packet/current-status explanations. The shared pending-content and video-refresh queues were inspected; unrelated pending work and historical video coverage baselines were left intact. The published `/course/` route remains retired. The v4 video still predates packet training; send its matching documents with the packet addendum. Human full-watch/all-caption acceptance remains pending.

The project still does **not** establish exact paper reproduction, live capture/blocking, verified flow joins from these exports, independent customer-network performance, calibrated packet confidence, universal attack coverage or NPU/SmartNIC execution. The two strict packet logit failures, source/split limitations, stronger metadata control and failed graph-export probe remain visible.
