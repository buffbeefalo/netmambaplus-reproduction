# Answers and presentation map

The guide follows the same slide numbers and presenter script as the PowerPoint. Briefing page numbers refer to the rendered PDF.

| Your question | Slides / script / guide sections | Briefing PDF pages |
|---|---|---|
| What did you try, and what works now? | 1, 2, 15 | 1, 7 |
| How do NetMamba+ training and inference work? | 4, 5 | 3 |
| What data goes in and what comes out? | 3, 4 | 2 |
| What results were actually reproduced versus reported by the paper? | 5, 6, 7, 9 | 4 |
| What could a simple working IDS demo look like? | 8, 10 | 5 |
| How could this map to an AI NPU or SmartNIC? | 9, 11 | 6 |
| What is still missing or not working? | 10, 11, 12, 15 | 6, 7 |

## What did you try, and what works now?

Native GPU builds, short masked pretraining, three complete fine-tuning runs, strict saved-model inference and a recorded browser replay were executed and checked.

## How do NetMamba+ training and inference work?

Reconstruction pretraining learns an encoder; labeled fine-tuning adds six categories and selects by validation; inference freezes the selected classifier and emits six scores.

## What data goes in and what comes out?

Compatible flow bytes, packet sizes and timing go in. Six logits, display scores and a class label come out. The uploaded packet CSVs do not establish the required flows.

## What results were actually reproduced versus reported by the paper?

All three source-based training runs finished: 91.26%, 84.05% and 84.63% test accuracy, with 86.65% mean. The paper’s 97.50% and exact protocol were not reproduced.

## What could a simple working IDS demo look like?

The working browser demo replays actual classifier outputs. A live IDS would add compatible capture, flow extraction and a validated alert policy; those components remain future work.

## How could this map to an AI NPU or SmartNIC?

A NIC or DPU could handle packet steering and flow preparation, with inference on a GPU or supported NPU. GPU inference works; the tested Torch export path is blocked and no target hardware deployment was tested.

## What is still missing or not working?

Exact paper reproduction, complete pretraining provenance, live capture/extraction, independent traffic validation, calibrated alert policy and NPU/SmartNIC execution remain unestablished. Inherited asset terms remain unresolved.

## Additional requested explanations

- Paper, datasets and changes from the authors’ repository: slide 13 and [comparison](upstream-comparison.md); briefing page 8.
- Simple setup, usage and testing: slides 14–15 and [quickstart](quickstart.md); briefing page 7.
- Plain-language explanation: [slide-by-slide guide](https://buffbeefalo.github.io/netmambaplus-reproduction/guide.html), also available offline at `demo/guide.html`.
- Actual checks and their limits: [verification record](verification.md) and [acceptance review](acceptance.md).
