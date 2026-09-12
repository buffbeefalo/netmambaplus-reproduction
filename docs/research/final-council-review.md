# Final council review and applied audit corrections

Run **5504d0bc-4a1a-4b5a-865f-0d0a9b6b6d6c** reached **CONSENSUS / RATIFIED**. Both pinned seats accepted the exact [canonical decision](final-council-decision.json); the [receipt](final-council-receipt.json) retains their recorded verdicts.

SHA-256: `18ff1e796e2fd1685df76a4a1b1b7dd5122cc06328c0f5dbf87a28a3616fed5d`

> Favor targeted verification and handoff corrections over additional research. The compact record supports reporting a measured research demo: 54 passing offline tests, three 120-epoch/7,920-update runs with 1,041 test predictions each, and mean accuracy of 86.65% with sample SD of 4.00 percentage points. Handoff remains pending focused checker inspection, final content/rendering review, redistribution-rights resolution for included assets, and fresh publication/download verification. This is reported execution evidence, not independent GPU certification or a validated production IDS.

## What the review does and does not establish

The council agreed on the research-demo scope and acceptance criteria. Its bounded excerpts did not independently establish complete checker correctness or every document’s contents. Those remained acceptance work for the implementing session; they are not silently renamed as independent council certification. The complete source, primary records and final artifacts were subsequently checked locally as described below. Publication evidence is separately attached to the release.

The earlier run **2a7c8d6d-c445-47a7-a755-7ef151db3bcc** ended **ESCALATED / UNRATIFIED**, with no mutual decision or decision hash. Its [original result](audit-council-initial-result.json) is preserved exactly. Several primary records and checker implementations had been excluded from its bounded evidence pack. A [compact primary summary](../customer/audit-evidence/primary-summary.json) and checker code supported the narrower follow-up; the initial outcome was not rewritten. The older [experiment-plan decision](council-decision.json) is a third, distinct historical record.

## Corrections and acceptance work actually performed

| Council requirement / audit finding | Action and evidence |
|---|---|
| Verify the numbers from primary records | The complete [package checker](../../tools/verify_package.py) recomputes each seed’s metrics from 1,041 retained predictions, checks six-class support, then computes cross-seed means and sample standard deviations. All comparisons passed. |
| Confirm complete unlabeled agreement | Added explicit equal-length, row-order, checkpoint, mapping, class-name and six-score checks. [Failure probes](../customer/audit-evidence/prediction-rejection-checks.json) reject malformed output copies; all real predictions pass. |
| Review complete customer content | Reviewed all 16 slides, eight briefing pages, 16 guide sections, speaker script and seven-question map. Added the actual scores to the script and used “flow predictions” to avoid implying 1,041 categories. |
| Make rendering and alignment inspectable | Fixed comparison-slide text overflow and a reference-only PDF page. Added [page-count/hash checks](../customer/document-check.json), tested rejection of the wrong count, and retained actual browser checks. |
| Preserve experimental limits | Seed 0 is distinguished from the all-seed mean; weighted/macro F1 and sample SD are explained; short pretraining is separate from main initialization. The paper score, live IDS and target accelerator deployment remain unestablished. |
| Scope performance claims correctly | Original and repeat benchmark JSON retain mean latency, batch sizes and all samples. Displayed median/p95 values are not substituted for means. Timings remain model-only, and the export conclusion remains limited to the tested Torch path. |
| Exclude inherited assets without established rights | The public inventory omits raw packet data, upstream source, original weights and local classifier exports. It publishes acquisition instructions, provenance and prediction evidence. |
| Bind public delivery to a fresh revision | Historical receipts are labeled as historical. The [new release receipt](https://github.com/buffbeefalo/netmambaplus-reproduction/releases/latest/download/release-verification.json) records the final commit, CI/Pages and anonymous-download checks. Earlier receipts do not stand in for that proof. |

The [verification record](../customer/verification.md), [acceptance map](../customer/acceptance.md) and [simple setup guide](../customer/quickstart.md) give the runnable checks and their limits. Direct implementation used the standing authorization; no broker `DELIVERED` claim is made.
