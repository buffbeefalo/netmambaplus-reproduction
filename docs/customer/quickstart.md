# Quickstart — the two-CSV packet workflow

There is one supported model workflow: prepare both CSVs, train the packet adaptation, and use its validation-selected joint pretrained checkpoint for benign/attack prediction. Start with the [client project explanation](client-project-guide.md); the ordered execution recipe is [packet-study-setup.md](packet-study-setup.md).

## Check the client and view saved predictions

Install Git and Python 3.10 or 3.12, then run:

```text
git clone https://github.com/buffbeefalo/netmambaplus-client.git
cd netmambaplus-client
python -m unittest discover -s tests -v
python tools/verify_client.py
python tools/render_packet_demo.py --output runs/packet-demo-new
```

Use `python3` if that is your interpreter's name. The suite should end with `OK`, with optional skips stated. All verifiers must exit successfully. Open `runs/packet-demo-new/index.html`. These steps need no GPU, private CSVs, model weights or API key. A client source ZIP also works.

The viewer contains the joint model's 20,000 CIC and 5,930 UNSW test groups. Switch source, inspect label disagreements and click a payload hash to see logits. It replays saved evidence; it does not capture traffic, make fresh predictions or block packets. Filters change the displayed groups, while headline cards retain the complete selected-source metrics.

## Run the actual model

Follow [the packet setup](packet-study-setup.md) in order:

1. Install the measured Linux/CUDA environment; fetch verified authors' source and the packet pretrained initialization, build native extensions and pass numerical checks.
2. Provide both labeled CSVs locally; run preparation and the packet-specific native runtime gate. The gate must actually pass its native tests without skips.
3. Freeze the protocol, fit controls, run the six-arm packet study, then evaluate frozen controls. These comparisons support the one joint-model workflow.
4. Use `selected_checkpoints.joint_pretrained` from the resulting checkpoint index to predict an unlabeled packet CSV.
5. Inspect achieved receipts and outputs; keep fresh output directories and failures for review.

The model reads 1,500 stored bytes. The prediction CSV may additionally contain the four metadata columns but must not contain `label`. Metadata never enters the native forward pass. A capped prediction still validates the entire input. No accuracy can be measured without ground truth.

## Test scope and common problems

Portable CI covers Linux x86-64, Windows x86-64 and macOS ARM64 with Python 3.10/3.12. Actual neural training/inference is measured on Linux ARM64 / GB10, not those hosted CPU jobs. Other physical GPUs need their own build/numerical/packet checks. [Platform details](../support-matrix.md).

| Problem | Action |
|---|---|
| An output directory already exists | Choose a fresh path; preserve previous evidence |
| Asset/input/checkpoint hash mismatch | Inspect the mismatched file and recorded identity; do not bypass verification |
| `nvcc` or `ptxas` is missing | Install the compiler toolkit and use the documented toolkit environment variables |
| Native gate reports failure/skips | Read its `receipt.json` and `tests.log`; do not report native execution as passed |
| Prediction rejects the CSV | Check ordered payload headers, optional metadata and absence of `label` |
| A full reproduction history check cannot find Git objects | Use a full source clone; client ZIP checks do not require that history |

The saved-evidence reviewer preserves two original strict logit failures, and the separate [earlier client GB10 receipt](../research/client-edition-validation.json) preserves 76 failures in a capped 128-row check. Complete class agreement does not erase numerical differences. Regenerating a checksum cannot establish correctness.

The [packet PDF/PPT/script](README.md) and [client guide](client-project-guide.md) explain the current handoff. Earlier flow/calibration video and documents are labeled historical.
