# Client handoff — one packet workflow

Start with **[Understand and explain the client project](client-project-guide.md)** and the concise **[client repository](https://github.com/buffbeefalo/netmambaplus-client)**. The supported workflow uses both supplied packet CSVs to train the native NetMamba+ adaptation, then predicts benign/attack with the selected joint pretrained model.

| Need | Material |
|---|---|
| Learn the complete packet workflow | [Current video](https://buffbeefalo.github.io/netmambaplus-reproduction/video/) · [Handbook PDF](demo/video/v5/NetMambaPlus-course-handbook.pdf) · [PowerPoint](demo/video/v5/NetMambaPlus-course-slides.pptx) · [Slide PDF](demo/video/v5/NetMambaPlus-course-slides.pdf) · [Transcript](demo/video/v5/transcript.md) |
| Explain the complete delivery | [Client project guide](client-project-guide.md) |
| Set up, train, predict and test | [Packet setup](packet-study-setup.md) · [Quickstart](quickstart.md) |
| Understand the supplied files | [Paper and both CSVs](paper-and-data-explained.md) · [Changes from upstream](upstream-comparison.md) |
| Present the measured packet result | [Eight-slide PDF](packet-addendum/NetMambaPlus-packet-addendum.pdf) · [PowerPoint](packet-addendum/NetMambaPlus-packet-addendum.pptx) · [Script](packet-addendum/packet-addendum-script.md) |
| Demonstrate it | [Recorded packet viewer](https://buffbeefalo.github.io/netmambaplus-reproduction/) |
| Inspect measurements and limitations | [Packet report](packet-model-study.md) · [Indexed evidence](evidence/packet-study/index.json) · [Acceptance map](acceptance.md) |
| Explain a particular file/download | [Complete repository walkthrough](../repository-walkthrough.md) |
| Maintain both repositories | [Client publication record](../research/client-edition.md) |
| Discuss future deployment | [IDS / NPU / SmartNIC roadmap](hardware-roadmap.md) |

<a id="current-packet-study-both-uploaded-csvs"></a>
## Current packet study: both uploaded CSVs

All **1,490,136 rows** and **2,235,204,000 byte cells** were validated. Six native comparison models each completed **1,000 updates**, and nine simple controls completed. The client uses the joint pretrained model, which scored **97.56% CIC / 94.29% UNSW group-weighted balanced accuracy**. The UNSW-only metadata control reached **99.34%**, above the neural models there. These are packet metrics, not the paper's original flow accuracy.

All 25,930 classes agreed in the original saved-model comparison; two strict logit comparisons failed. A later client-checkout check validated 20,000 CIC input rows and predicted 128, with all classes agreeing but 76 strict logit failures. Its [separate receipt](../research/client-edition-validation.json) does not replace the original study. One seed, capped subsets, weak transfer, sparse subtype support and unknown prior pretrained exposure constrain the claims.

The packet viewer displays the joint model's full retained test sets and label disagreements. It does not run new inference, capture traffic or block packets. Fresh inference requires the checked GPU runtime, formatted unlabeled input and a suitable locally trained checkpoint.

<a id="historical-material"></a>
## Historical material

Earlier flow/calibration experiments and media remain research history in this full reproduction repo. They are **not another supported client workflow or the current CSV tutorial**. The current handoff uses the packet guide and slides above.

<a id="preserved-v4-course-original-flows-and-calibration"></a>
### Preserved v4 course: original flows and calibration

[Historical v4 release](https://github.com/buffbeefalo/netmambaplus-reproduction/releases/tag/course-video-v4) · [MP4](https://github.com/buffbeefalo/netmambaplus-reproduction/releases/download/course-video-v4/NetMambaPlus-one-hour-course.mp4) · [Handbook](demo/video/v4/NetMambaPlus-course-handbook.pdf) · [PowerPoint](demo/video/v4/NetMambaPlus-course-slides.pptx) · [Slide PDF](demo/video/v4/NetMambaPlus-course-slides.pdf) · [Transcript](demo/video/v4/transcript.md).

These predate the packet study and client packaging. [Media checks](video-verification-v4.md) distinguish executed inspections from pending human full-watch/all-caption acceptance. [Historical flow results](results.md), [calibration study](confidence-calibration.md), [offline flow replay](demo/index.html) and [old flow runbook](runbook.md) retain their original scope. The public root now demonstrates packets.

<a id="earlier-customer-presentation-archived-scope"></a>
### Earlier customer presentation: archived scope

The original 16-slide deck, eight-page briefing and release ZIP describe the earlier flow experiment, before calibration and packet training. [Briefing PDF](NetMambaPlus-customer-briefing.pdf) · [Markdown](briefing.md) · [PowerPoint](NetMambaPlus-customer-slides.pptx) · [Slide PDF](NetMambaPlus-customer-slides.pdf) · [Script](talk-track.md) · [Field guide](demo/guide.html) · [Question map](answers.md) · [Historical ZIP](https://github.com/buffbeefalo/netmambaplus-reproduction/releases/download/customer-2026-09-15-audited/netmambaplus-customer-package.zip) · [Dated verification](verification.md).

Download the desired packet PDF/PPT/script before an offline meeting. The client ZIP supports its portable checks; a full reproduction clone is needed for historical Git-bound verification. The retired `/course/` site remains excluded from deployment.

## Boundaries

Exact paper reproduction, verified live extraction, independent customer evaluation, calibrated packet confidence, unknown-attack handling, operational alert/blocking policy and NPU/SmartNIC execution remain unestablished. Raw data and inherited weights are external assets with unresolved redistribution/commercial terms. Council outcomes remain separate from executed tests.
