# The 30-minute NetMamba+ course: use, evidence and verification

[Open the course](https://buffbeefalo.github.io/netmambaplus-reproduction/course/) · [Download the standalone HTML](https://raw.githubusercontent.com/buffbeefalo/netmambaplus-reproduction/main/docs/customer/demo/course/index.html) · [Editable lesson source](course-source.json)

The course is a complete browser lesson for someone preparing to explain this project to a customer. It contains nine sections, eight objective questions with explanations, a real saved prediction error and a separate two-minute customer teach-back. Thirty minutes is a planned reading-and-practice allocation, not a measured guarantee for every learner. **A human-paced full-route rehearsal remains pending. Automated verification is separate from human learning or mastery.**

## Open, download and use it

Open the course and use **Download HTML** to save `NetMambaPlus-course.html`, then open that file locally. The raw GitHub link is an alternative: save the linked file. The essential explanations, prediction row and answer keys are embedded in that one file. There is no account, AI subscription, model call, GPU, package installation or network requirement for the core lesson. JavaScript adds immediate quiz scoring; with JavaScript disabled, native answer disclosures still work. Browser Print can make a personal PDF, including the answer keys. The existing reviewed PPTX, briefing PDF, slide PDF and presenter script remain linked through the optional resources.

Use the schedule as a guide. Read a section, answer its question, review the explanation, then move on. Do the final explanation aloud before checking the five-point rubric. Reading, elapsed time, answer reveals and self-assessment checkboxes do not award objective quiz points. Answers are visible in the file: this is a study aid, not an examination or certificate.

The current course is separate from the immutable `customer-2026-09-15-audited` release and is **not inside that historical ZIP**. That release still has seven named attachments. Its recorded 54-test result remains historical; current main adds 17 course regression tests for 71 total. The legacy quickstart preserves its audited 54-test expectation; use the current commands and receipt below for this course extension.

## The complete timed route

| Time | Lesson | Reading / practice and answer review |
|---|---|---|
| 00:00–02:00 | The paper and the purpose | 90 / 30 seconds |
| 02:00–06:00 | Three files, two different kinds of data | 180 / 60 seconds |
| 06:00–10:00 | How the model learns and predicts | 180 / 60 seconds |
| 10:00–13:00 | What we changed, and where it lives | 120 / 60 seconds |
| 13:00–17:00 | What actually ran, and what the numbers mean | 150 / 90 seconds |
| 17:00–21:00 | Investigate one real prediction | 90 / 150 seconds |
| 21:00–25:00 | Set it up, use it and check it | 150 / 90 seconds |
| 25:00–27:00 | From classifier to IDS and accelerator | 90 / 30 seconds |
| 27:00–30:00 | Explain it to the customer | 0 / 180 seconds |

**Total: 1,800 planned seconds = 1,050 teaching + 750 practice.** Required reading is budgeted at 120 words per minute. The verifier counts lesson prose, tables, essential orientation, exercise instructions/options/explanations, the saved-row display and rubric. Repeated navigation, citation labels, optional evidence inspection and optional downloads are outside the reading count. Each segment reserves actual action time; the final segment reserves 120 seconds speaking and 60 seconds for rubric review/correction. The budget has not been substituted for a human timing observation.

The current count is 1,677 teaching words and 720 practice-reading words, with 325 explicitly reserved action seconds. Remaining time within each allocation allows pausing and review. GPU setup, training, complete file-by-file reading, extended replay, narration and optional AI tutoring carry zero counted seconds.

All seven requested questions are mapped to counted explanations in `customer_questions` in the source. Additional counted topics include the paper, each CSV, authors’ code versus our wrapper, representative files, setup routes, tests, downloads, evidence and curated research. Every section also identifies the matching existing slide numbers and briefing pages. The complete file walkthrough is an optional reference; it is not a substitute for required teaching.

## Rebuild and test

From the repository root, Python 3.10 or newer is sufficient:

```bash
python3 tools/build_course.py --check
python3 tools/verify_course.py
python3 -m unittest discover -s tests -v
python3 tools/verify_package.py
```

The builder check must report an exact match; the two verifiers must report deterministic status `passed`; the current suite should finish with `Ran 71 tests` and `OK`. `fully_verified: false` and `required_real_world_checks_pending: ["human_rehearsal"]` are intentional once browser/publication checks are complete. They prevent automated success from being reported as a completed human rehearsal. These CPU checks do not retrain the model or provide a new dataset evaluation.

To edit the course, change `course-source.json`, review its claims against the cited evidence, run `python3 tools/build_course.py`, and repeat the checks. Update this source/HTML-bound verification record only after performing the named checks. The default verifier is read-only. Its negative tests catch timing drift, missing practice time/topics, overloaded reading, altered measurements/predictions, invalid answer keys, stale HTML, broken references and false completion claims.

Browser rechecks are optional for ordinary readers and require the pinned Playwright environment. To reproduce them in a separate environment:

```bash
python3 -m venv .venv-course-browser
source .venv-course-browser/bin/activate
python -m pip install -r requirements/browser.txt
python -m playwright install chromium
python tools/verify_course.py --browser-output runs/course-browser-new
```

This reuses the tested Linux browser route; OS browser dependencies may also be needed. Pick a fresh output directory under `runs/`. For a public check, add `--url https://buffbeefalo.github.io/netmambaplus-reproduction/course/`. That mode first compares served bytes, then repeats the functional checks. Offline no-JavaScript checks still use the local HTML. Screenshots and the JSON receipt are local outputs; the completed receipt is embedded below. Changing only browser automation still requires review before updating its receipt.

## Content review and limitations

The authored source and its citations were reviewed against `docs/lesson.md`, the native-flow and uploaded-CSV profiles, configuration, checkpoint transfer, actual three-seed results/predictions, the runbook, comparison, verification record and hardware roadmap. The model/loader, original training measurements and existing customer presentation are unchanged. The verifier checks all previous customer/research artifact fingerprints, not only the new HTML.

The lesson retains the 91.26%, 84.05%, 84.63% test accuracies and 86.65% mean; the paper’s 97.50% was not reproduced. It distinguishes short separate pretraining from the checkpoint used for fine-tuning, recorded replay from live inference, saved model tensors from graph export, and working GPU inference from unestablished IDS/NPU/SmartNIC execution. The selected recorded error is row 635: class 1 predicted, class 3 labeled, with an 84.43% top display score. It illustrates an error; it is not a newly measured operational false-positive rate.

The course build has no narration dependency. A local Kokoro ONNX feasibility probe did produce 13.85 seconds of speech; that probe is not course audio or a completed course video. No course narration/video was published. This does not establish that narration is infeasible. No human learning record has been fabricated.

## Review and execution receipts

The reviewed pre-course repository baseline was `1c424884cd0d691203fb94ba4da3c706eb6291e7`. A check marked `passed` below has an actual receipt; `pending` remains unresolved. Browser elapsed seconds measure automation, not reading time. Screenshot hashes identify local captures and are not claims that those PNG files are shipped in the repo.

<!-- course-check-record -->
```json
{
  "schema_version": 1,
  "fully_verified": false,
  "checks": {
    "content_review": {
      "status": "passed",
      "detail": "Reviewed the authored explanations, keys and evidence references; inspected global queues without clearing other work.",
      "receipt": {
        "reviewer": "Codex ordinary implementation session; not a human learner",
        "completed_at": "2026-09-13T05:31:38.859316+00:00",
        "baseline_commit": "1c424884cd0d691203fb94ba4da3c706eb6291e7",
        "reviewed_topics": [
          "each uploaded CSV and native flow distinction",
          "input transformations and class provenance",
          "separate short pretraining versus all-seed fine-tuning",
          "actual results and paper comparison",
          "recorded prediction error and display-score limit",
          "upstream/runtime wrapper differences",
          "setup, downloads, historical versus current test counts",
          "IDS/NPU/SmartNIC gaps",
          "question keys and teach-back rubric"
        ],
        "source_hashes": {
          "docs/lesson.md": "bcd7710396fc5f088de56df470f4c8c708336790af728d7940f57bcf2b888afa",
          "docs/customer/upstream-comparison.md": "a84e5fbffabc2b6ccc44351203b4b61f9f95dee7608765e3ef427d54e121b5ba",
          "docs/customer/evidence/results.json": "ead00597c0534a10d779e83805366c1cf323d231b1f7e94e9d001272e7641f1a",
          "docs/customer/evidence/uploaded-csv-profile.json": "f6d11f8c8c2d604ed6a6f2539c9c7fb93d1279997dd89cb84873de03c0547097",
          "docs/customer/evidence/native-data-validation.json": "122bc8ba9a3ba2d53400b615b7b73a2d597e21063c478a96d852b3d7a7dd96f9",
          "docs/customer/hardware-roadmap.md": "99cacacf535210e6517661595f0994e3899fd59787c58872a64c35f5bdc2be18",
          "docs/customer/runbook.md": "854f19228fd384888cb268db20bf005785813df5c5fd6421110d81fcb95f49a0",
          "docs/repository-walkthrough.md": "2a46c560d920bd0dd6d7d14a77513a2453bed750f780019d70a8447b5930cf33"
        },
        "global_queues": {
          "pending-content-reviews.json": {
            "observed_at": "2026-09-13T05:31:38.859316+00:00",
            "sha256": "ab8ef972ba2704c9a6379e4a46944114100a0b6c61d36b6fe973e0345a54b6fa",
            "counts": {
              "courses": 17,
              "errors": 0
            },
            "modified_by_this_task": false
          },
          "video-refresh-queue.json": {
            "observed_at": "2026-09-13T05:31:38.859316+00:00",
            "sha256": "036b4e45b6aed3c00d72137f4004dcb20aed922710962fdf35f9521a5373867a",
            "counts": {
              "jobs": 0,
              "blocked": 47
            },
            "modified_by_this_task": false
          }
        },
        "course_registration": "repository-based customer course; no fleet-course registration or video refresh"
      }
    },
    "automated_checks": {
      "status": "passed",
      "detail": "All four acceptance commands passed; 71 tests (54 original plus 17 course).",
      "receipt": {
        "completed_at": "2026-09-13T05:45:29.444880+00:00",
        "commands": [
          {
            "command": "python3 tools/build_course.py --check",
            "exit_code": 0,
            "elapsed_seconds": 0.095,
            "output_sha256": "a66ff4a2f3b5a9365f8fe7ac52ec94df7d2cd61ceb85d94b752e545fb753eaca",
            "result": "Course render matches its reviewed source and evidence."
          },
          {
            "command": "python3 tools/verify_course.py",
            "exit_code": 0,
            "elapsed_seconds": 0.072,
            "output_sha256": "ebec853e08b52d59d5b820b2bc517f0d2b3e96ac2e0284c63acc102e571ef4ba",
            "result": {
              "status": "passed"
            }
          },
          {
            "command": "python3 -m unittest discover -s tests -v",
            "exit_code": 0,
            "elapsed_seconds": 0.741,
            "output_sha256": "5f6956d00a5ff4216d1c83d866a73e791d775466f38b518e65465428bc3205fb",
            "result": "----------------------------------------------------------------------\nRan 71 tests in 0.671s\n\nOK"
          },
          {
            "command": "python3 tools/verify_package.py",
            "exit_code": 0,
            "elapsed_seconds": 0.094,
            "output_sha256": "4ab0be841e7abbfa30f2760aa02b13ddbba4b5d01c25452613e52bd726627f7b",
            "result": {
              "status": "passed"
            }
          }
        ],
        "scope": "Current course candidate including direct-download behavior; no new GPU training."
      }
    },
    "browser_checks": {
      "status": "passed",
      "detail": "Actual Chromium keyboard, quiz, offline/no-JS, four-width layout and print-answer checks.",
      "receipt": {
        "status": "passed",
        "completed_at": "2026-09-13T05:44:16.180185+00:00",
        "html_sha256": "5aa24cf4b7283f21a54dc775a3bda390516dcec191e32a7332c891045cd5e8f5",
        "browser": "Chromium 140.0.7339.16; Playwright 1.55.0",
        "passed_checks": [
          "correct_answers",
          "keyboard",
          "no_js_answers",
          "no_page_errors",
          "offline_core",
          "print_answers",
          "reveals_do_not_score",
          "rubric_separate",
          "wrong_answer_feedback"
        ],
        "viewport_widths_without_overflow": [
          320,
          390,
          768,
          1440
        ],
        "method": "automated browser functional rehearsal; not a human learning or timing study",
        "elapsed_seconds": 33.796,
        "hosted_url": null,
        "download_bytes_equal": null,
        "print_pdf_sha256": "b557c42c485940aefa839022067982edad8eee0432814b2169217dcef1942f7d",
        "screenshots": {
          "course-1440.png": "3b9d65c1fb7b244fb7636371212ce1dafdd3e07dc56d35e7bc6fab95682b346c",
          "course-320.png": "568069b407991443911234c4acd1a6a407d919d861d9df732e7da3b349d4a24a",
          "course-390.png": "545762ed2a16005895962161c31ea43f968bfb43a51e7d120cd5466b3adac713",
          "course-768.png": "c732d2d544f20925551e4826673ba79f7fe50be74feff1dd225c1cd431c897a0",
          "course-no-js.png": "0a6089b4b4c5fbbba8600c12621679436d19cef789cf46e090b199dc57e60f79",
          "recorded-example.png": "ad5cd491cd138895a08f4e4e33215d8360fd7ef21ec7d84b29bb41c556a2004b"
        },
        "print_text_check": {
          "status": "passed",
          "method": "pdftotext comparison against all eight complete explanations, the known label and final rubric.",
          "pdf_sha256": "b557c42c485940aefa839022067982edad8eee0432814b2169217dcef1942f7d"
        },
        "corrected_findings": [
          "Print CSS originally concealed closed answer panels; explicit details-content visibility fixed it.",
          "Print test originally indexed a shrinking open-details collection; stable details iteration fixed the automation.",
          "Raw GitHub download navigated to source text; same-origin download was exercised and matched the HTML bytes."
        ]
      }
    },
    "human_rehearsal": {
      "status": "pending",
      "detail": "No human has yet completed the full route with observed segment durations and teach-back. Planned timing and automated clicking are not substituted for this observation."
    },
    "publication": {
      "status": "passed",
      "detail": "Anonymous public page and same-origin download matched the reviewed HTML; hosted browser checks and both GitHub workflows passed. The historical release still has seven assets at its original commit.",
      "receipt": {
        "completed_at": "2026-09-13T05:48:30.908769+00:00",
        "url": "https://buffbeefalo.github.io/netmambaplus-reproduction/course/",
        "html_sha256": "5aa24cf4b7283f21a54dc775a3bda390516dcec191e32a7332c891045cd5e8f5",
        "served_bytes_equal": true,
        "download_bytes_equal": true,
        "course_implementation_commit": "4ff6f6bc34425dfd5072588339151c4d3d8b6ef3",
        "ci": [
          {
            "conclusion": "success",
            "databaseId": 34741084725,
            "headSha": "4ff6f6bc34425dfd5072588339151c4d3d8b6ef3",
            "name": "CPU verification",
            "status": "completed",
            "url": "https://github.com/buffbeefalo/netmambaplus-reproduction/actions/runs/34741084725"
          },
          {
            "conclusion": "success",
            "databaseId": 34741084759,
            "headSha": "4ff6f6bc34425dfd5072588339151c4d3d8b6ef3",
            "name": "Publish measured replay",
            "status": "completed",
            "url": "https://github.com/buffbeefalo/netmambaplus-reproduction/actions/runs/34741084759"
          }
        ],
        "hosted_browser": {
          "status": "passed",
          "completed_at": "2026-09-13T05:47:11.023607+00:00",
          "html_sha256": "5aa24cf4b7283f21a54dc775a3bda390516dcec191e32a7332c891045cd5e8f5",
          "browser": "Chromium 140.0.7339.16; Playwright 1.55.0",
          "passed_checks": [
            "correct_answers",
            "keyboard",
            "no_js_answers",
            "no_page_errors",
            "offline_core",
            "print_answers",
            "reveals_do_not_score",
            "rubric_separate",
            "wrong_answer_feedback"
          ],
          "viewport_widths_without_overflow": [
            320,
            390,
            768,
            1440
          ],
          "method": "automated browser functional rehearsal; not a human learning or timing study",
          "elapsed_seconds": 33.968,
          "hosted_url": "https://buffbeefalo.github.io/netmambaplus-reproduction/course/",
          "download_bytes_equal": true,
          "print_pdf_sha256": "e0297439ed9e02bfbec1daa51302cb589dbe044df9202ffb4b455c0980a2d997",
          "screenshots": {
            "course-1440.png": "3b9d65c1fb7b244fb7636371212ce1dafdd3e07dc56d35e7bc6fab95682b346c",
            "course-320.png": "568069b407991443911234c4acd1a6a407d919d861d9df732e7da3b349d4a24a",
            "course-390.png": "545762ed2a16005895962161c31ea43f968bfb43a51e7d120cd5466b3adac713",
            "course-768.png": "c732d2d544f20925551e4826673ba79f7fe50be74feff1dd225c1cd431c897a0",
            "course-no-js.png": "1a4cd555dec21589109df5129b6d82e781eb4cfb65262ca87546d1a3dbfbb516",
            "recorded-example.png": "ad5cd491cd138895a08f4e4e33215d8360fd7ef21ec7d84b29bb41c556a2004b"
          }
        },
        "preserved_release": {
          "tag": "customer-2026-09-15-audited",
          "target_commit": "17b4aaebcf9327ae9967ca45ddfaf16325766993",
          "named_assets": 7
        }
      }
    }
  },
  "source_sha256": "86dfc769fec5afcf9a59348e73caf8c9261c7d1570dfcb480e0435e9284a186e",
  "html_sha256": "5aa24cf4b7283f21a54dc775a3bda390516dcec191e32a7332c891045cd5e8f5"
}
```

## Council review and direct implementation

Run `fd14aca3-fea0-499a-9fe2-167ae5182876` reached **CONSENSUS / RATIFIED** with Claude Fable 5 at high effort and GPT-6 Astra at max effort. It compared a static course, linear walkthrough, narrated lessons, timed slide reuse and live AI tutoring. The council reviewed the design; it did not independently execute the training or certify learner understanding.

> Build a self-contained static HTML course at docs/customer/demo/course/index.html, rendered deterministically from one source. Nine counted segments provide exactly 1,800 planned seconds of explanation, practice and customer teach-back. Use six new UTF-8 files, preserve all existing audited artifacts, and publish through the existing Pages workflow. Narrated lessons with exercises remain a viable future supplement; optional references, video and AI tutoring are outside the counted course.

**Canonical decision SHA-256:** `1977587853f8b87ff60178bae953e565b6fab4897f7706a7a8749415e761958f`.

The ordinary Codex session implemented directly under Brandon’s standing implementation authorization; no broker `DELIVERED` outcome is claimed. The six new files implement the course design. Routine integration edits also added a root README link, updated the complete file walkthrough from 174 to 180 entries, and extended the current checksum index by the three new customer-document paths. These integration edits were not enumerated in the six-file council contract. They are recorded here explicitly: the existing package verifier requires an exact inventory, and the user requested discoverable documentation of every file. All old checksum entries and the frozen release contents are preserved; no historical receipt or council record was rewritten.

The exact canonical JSON is retained below so its hash can be checked independently. Hash the UTF-8 content between the code fences without adding a trailing newline.

<details><summary>Exact ratified course decision</summary>

<!-- course-council-decision -->
```json
{"changes":[{"action":"add","edit":"Create a versioned source containing these counted segments and teaching/practice seconds: paper and purpose 120 (90/30); both packet CSVs versus compatible native flows 240 (180/60); preprocessing, model, pretraining, fine-tuning and inference 240 (180/60); original versus wrapper code and repository navigation 180 (120/60); reproduced results versus paper claims 240 (150/90); recorded-inference demonstration 240 (90/150); setup, use, tests, evidence and downloads 240 (150/90); limitations and future IDS/NPU/SmartNIC work 120 (90/30); customer teach-back and correction 180 (0/180). Totals are 1,050 teaching and 750 practice seconds. Include required instructions, answer review and rubric reading within these allocations. Declare 120 words per minute as a conservative planning assumption, identify reading content and reserve actual activity time; the final activity reserves 120 seconds for speaking and 60 for rubric review and correction. Map all seven questions in answers.md and every additional requested topic to substantive counted explanations and activities. Explain each supplied CSV separately using available source evidence; do not invent missing fields or flow reconstruction. Teach native flow data, sizes and intervals; training versus inference inputs and outputs; class-mapping provenance; and labeled versus unlabeled evaluation. Include objective exercises for input discrimination, lifecycle tracing, upstream/wrapper responsibilities, results interpretation, a real recorded prediction and selection of a setup or verification route. Provide explanatory answers and a customer-explanation rubric. Embed the real prediction and necessary evidence excerpts so core activities require no external browsing. Cite factual claims and the prediction using existing repository-relative evidence paths, file hashes and precise JSON selectors or text anchors; use JSON evidence where available without assuming every claim has a JSON source. Preserve the distinctions between NetMamba and NetMamba+, three complete 120-epoch runs, 91.26/84.05/84.63 percent accuracy and 86.65 percent mean, the unreproduced paper claim of 97.50 percent, short separate pretraining, recorded replay, working GPU inference, the blocked tested export path and unestablished live IDS/NPU deployment. Explain representative files in the counted course; identify the complete file walkthrough as optional snapshot documentation. Installation, training, full replay exploration, external references and optional AI practice receive zero counted seconds.","path":"docs/customer/course-source.json","summary":"Define the complete course, timing, evidence, exercises and assessment rubric."},{"action":"add","edit":"Implement a repository-root command that reads course-source.json and its cited local evidence and writes only docs/customer/demo/course/index.html. Render scientific values through the claim records and evidence references rather than maintaining independent copies in templates. Produce deterministic UTF-8 output with embedded styles and any progressive-enhancement script, no timestamps, network requests, course-build dependencies or runtime model calls. Escape rendered content appropriately. Implement --check as a read-only comparison that exits nonzero when committed HTML differs from the exact expected render. Preserve all existing files and fail clearly on missing or invalid evidence.","path":"tools/build_course.py","summary":"Render the course deterministically using Python's standard library."},{"action":"add","edit":"Commit the renderer's complete output. Include orientation, the segment schedule, explanations, exercises, explanatory keys, source citations and the final teach-back rubric. Use semantic headings and navigation, labeled controls, visible keyboard focus, readable contrast and responsive layout without horizontal page overflow at 320 through 1440 pixels. Essential content and answers must work with JavaScript disabled; optional JavaScript may score objective answers and provide explanatory feedback. Report objective performance separately from self-assessed teach-back, with no mastery certification from time, clicks, attempts, reveals or client-side scores. Use no forced timing or autoplay. Label 30 minutes as a planned budget with variable learner pace. Clearly label the embedded prediction and any replay interaction as recorded classifier output; playback speed is not inference throughput and display scores are not established calibrated attack probabilities. Explain setup routes and expected verification outcomes without requiring installation or GPU work during the lesson. Treat the recorded 54-test count as historical; adding course tests changes the current suite count. Offer the standalone HTML as a course download and link existing downloads using verified destinations, without claiming the new course is inside the immutable historical ZIP. Keep essential learning offline; label supplementary links as optional and use valid deployed or repository URLs for files outside the Pages tree.","path":"docs/customer/demo/course/index.html","summary":"Deliver the accessible, offline-capable 30-minute learning route."},{"action":"add","edit":"Implement a read-only standard-library verifier with nonzero exits for failures. Independently require the nine segment allocations, exactly 1,800 total seconds, 1,050 teaching seconds and 750 practice seconds. Check teaching reading load and practice instructions, answer review and rubric reading at the declared 120-word-per-minute rate while preserving declared activity time, including the two-minute final explanation. Require unique identifiers, substantive core content, complete required-topic and customer-question mappings, exercises with valid answer keys and explanations, and zero counted time for optional resources. Validate factual claim references, source hashes and selectors against existing frozen repository evidence, allowing exact text anchors for non-JSON sources; reject unsupported or altered values rather than updating their evidence. Compare the embedded prediction with its actual recorded source and retain its run/checkpoint provenance. Check exact rendered-output agreement, internal anchors, deployed local targets and repository citation targets. Validate external URL syntax and declared purpose without claiming remote availability was checked offline. Validate the verification record's statuses and receipts, distinguishing automated checks from human rehearsal, browser checks and post-publication checks. Missing real-world receipts must remain pending, not silently passed. Preserve the existing protected inventory and enforce its recorded hashes without regenerating it. Keep all file access inside the repository for these sandbox checks and provide clear failure messages.","path":"tools/verify_course.py","summary":"Check timing, coverage, evidence, rendering and verification-record integrity."},{"action":"add","edit":"Add standard-library unittest coverage for valid course validation and deterministic rendering. Include negative cases for timing drift, excessive reading load, absent activity time, missing required-topic mappings, altered scientific claims, an altered recorded prediction, broken evidence references, broken deployed links, inconsistent exercise keys and stale rendered HTML. Verify that pending rehearsal or publication status cannot be reported as completed verification. Test scoring behavior independently of progress, elapsed time or answer reveals. Use isolated temporary fixtures inside the supplied staging environment; never mutate historical evidence, release inventories or the working course during tests. Preserve compatibility with Python 3.10 and the existing standard-library test-discovery command.","path":"tests/test_course.py","summary":"Test consequential course failures without adding dependencies."},{"action":"add","edit":"Create a separate course verification record identifying the reviewed source commit, relevant evidence hashes, course-source and rendered-HTML hashes, factual/content review, commands actually executed and their results. Review the affected lesson sources and references substantively; generation or source capture alone does not establish current prose. Record a real human full-route rehearsal with performer, actual segment durations, activity and answer-review completion, and deviations from the planned budget. Revise content if that rehearsal shows the intended route does not fit; never fabricate a rehearsal or infer measured duration from arithmetic. Record browser receipts for keyboard operation, widths 320/390/768/1440, disabled-JavaScript answer access, offline essential content, objective feedback and the separately self-assessed teach-back. These review, rehearsal and browser checks remain required for declaring the course fully verified; mark unavailable checks pending. After authorized publication, record the actual course URL and served HTML agreement with the reviewed artifact, distinguishing this external check from the network-disabled delivery commands. Provide the direct course URL in the publication report instead of editing an existing entry page. Record the status of pending-content-reviews.json and video-refresh-queue.json only if the ordinary calling session actually reads them; their contents were unavailable to this council. Leave unresolved reviews visible and do not alter shared queues, coverage baselines, other courses, policy, Dropout Bear or historical council records. All six contract paths are create-only: unexpected existing content or workspace drift requires evidence-based reconciliation, not overwrite.","path":"docs/customer/course-verification.md","summary":"Record genuine content review, timing, accessibility and publication evidence."}],"decision":"Build a self-contained static HTML course at docs/customer/demo/course/index.html, rendered deterministically from one source. Nine counted segments provide exactly 1,800 planned seconds of explanation, practice and customer teach-back. Use six new UTF-8 files, preserve all existing audited artifacts, and publish through the existing Pages workflow. Narrated lessons with exercises remain a viable future supplement; optional references, video and AI tutoring are outside the counted course.","delivery":{"auditor":{"context":"fresh-ephemeral","edits":false,"effort":"max","fallback":null,"model":"gpt-6-astra","provider":"codex","voting":false},"contract_version":2,"evidence_kinds":["file","grep","glob","git-log"],"executor":{"context":"fresh-ephemeral","effort":"max","fallback":null,"model":"gpt-6-astra","provider":"codex","tools":false,"voting":false},"max_attempts":2,"max_evidence_rounds_per_attempt":2,"verification":{"credentials":"excluded","fail_closed":true,"network":"disabled","sandbox":"required","writable":"staging-only"}},"dissent":"No remaining material design disagreement. Adopt Claude's nested course/index.html placement and Codex's create-only publication approach. Fresh workflow and glob evidence resolve the deployment and collision objections; avoiding existing-document edits resolves the inventory-related link-edit objection. Local video feasibility and external course-review queue contents remain unverified, without blocking this static course. This draft does not assert mutual ratification or completed implementation.","evidence_refs":["Evidence pack: Question (complete), source commit 1c424884cd0d691203fb94ba4da3c706eb6291e7","docs/customer/answers.md: customer question map, reproduced results, inputs/outputs and deployment limitations","Evidence pack: quickstart excerpt, Route 2, Route 3, How the tests have gone and Common problems","docs/customer/upstream-comparison.md: supplied partial excerpt distinguishing NetMamba, NetMamba+ and the reproduction wrapper",".github/workflows/pages.yml: Broker-fulfilled round-1 evidence; standard-library checks and upload path docs/customer/demo","Broker-fulfilled round-1 glob **/*course*: no matches","Evidence pack: excluded local video-worker request and outside-cwd video-refresh-queue request; unavailable evidence remains unknown","Immutable excerpt evidence-source-e5c0999a-0b7d-4988-8ac9-d546ead56007-round-1.md; SHA-256 fed874b995bbd10bca156620a59c65b4ecf5690f30815f080294284ba36fc92b"],"findings":[],"mode":"architect","reasons":["Static explanations with decision exercises and teach-back fit the existing delivery tree and support independent, offline study without runtime services.","Narrated slides with exercise pauses and a transcript are materially viable, but local worker feasibility receipts are unavailable. This decision does not assume video is infeasible or pedagogically ineffective.","A linear 174-file walkthrough cannot reasonably fit the requested beginner course. Timed reuse of existing slides alone lacks the proposed practice and verification; live AI tutoring lacks a deterministic core route.","Exact timing allocations, reading-load checks and genuine rehearsal evidence address different aspects of the 30-minute budget. Required topics remain inside the course, while optional reading cannot substitute for completed teaching.","The supplied Pages workflow confirms that docs/customer/demo is uploaded, and the fulfilled course glob reports no matches. A six-file create-only contract removes the need to determine whether an existing link target can safely be edited.","All delivery commands are repository-root-relative and work without network or course-build dependencies. Browser, human-rehearsal and publication receipts remain separately identified requirements for full verification."],"schema_version":2,"verify":["python3 tools/build_course.py --check","python3 tools/verify_course.py","python3 -m unittest discover -s tests -v","python3 tools/verify_package.py"]}
```

</details>

The shared pending content-review and local video queues were inspected; their counts and hashes are in the content-review receipt. This customer course is published from this repository, not registered as a separate fleet course under `~/learn`. Existing pending reviews, failed video jobs, coverage baselines, other courses and shared policy were left untouched. No Claude bulk-video refresh was launched.
