"""Render the slide-aligned, offline learning guide using only the standard library."""

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CUSTOMER = ROOT / "docs/customer"
REPO = "https://github.com/buffbeefalo/netmambaplus-reproduction"


def coverage_markdown(source):
    rows = ["| Your question | Slides / script / guide sections | Briefing PDF pages |",
            "|---|---|---|"]
    for item in source["questions"]:
        rows.append("| " + item["question"] + " | " + ", ".join(map(str, item["slides"]))
                    + " | " + ", ".join(map(str, item["briefing_pages"])) + " |")
    return "\n".join(rows)


def render(source):
    esc = html.escape
    slides = source["slides"]
    if len(source["questions"]) != 7:
        raise ValueError("The guide requires the seven customer questions")
    sections, links, questions = [], [], []
    for n, slide in enumerate(slides, 1):
        plain = slide["plain_language"]
        title = slide["title"].replace("\n", " ")
        links.append(f'<li><a href="#slide-{n}"><span>{n:02d}</span> {esc(title)}</a></li>')
        target = plain["evidence"]
        evidence = "index.html" if target == "demo/index.html" else REPO + "/blob/main/docs/customer/" + target
        sections.append(f'''<section class="lesson" id="slide-{n}" aria-labelledby="title-{n}">
<p class="eyebrow">Slide {n:02d} / {len(slides):02d}</p><h2 id="title-{n}">{esc(title)}</h2>
<p class="explanation">{esc(plain["explanation"])}</p>
<aside class="analogy"><h3>An everyday comparison</h3><p>{esc(plain["analogy"])}</p></aside>
<p class="remember"><strong>Remember this.</strong> {esc(plain["remember"])}</p>
<details><summary>Open the presenter’s script for this slide</summary><p>{esc(slide["notes"])}</p></details>
<a class="evidence" href="{esc(evidence, quote=True)}">Read the supporting record <span aria-hidden="true">↗</span></a>
</section>''')
    for item in source["questions"]:
        refs = " · ".join(f'<a href="#slide-{n}">Slide {n}</a>' for n in item["slides"])
        questions.append(f'<article id="question-{esc(item["id"])}"><h3>{esc(item["question"])}</h3>'
                         f'<p>{esc(item["answer"])}</p><p class="references">{refs}</p></article>')
    glossary = {
        "Packet": "One small unit of data sent across a network.",
        "Flow": "Related packets grouped by an established connection rule and ordering. These inputs must match the model’s training representation.",
        "Dataset / CSV": "A collection of examples / a table stored as comma-separated values. The uploaded CSV rows describe packets; the training JSON records describe flows.",
        "IDS": "Intrusion detection system: software that examines traffic and raises alerts for investigation.",
        "Model / weights": "A calculation with learned numerical settings. A checkpoint saves those settings and sometimes training state.",
        "Mamba / selective scan": "A sequence model that updates a compact numerical state while reading tokens. Its input-dependent updates decide how information is carried forward.",
        "Token / embedding": "A model input unit / its learned numerical representation. Here tokens represent byte groups, packet sizes, timing and summaries, not words.",
        "Pretraining / fine-tuning": "Learning a representation by reconstructing hidden inputs / adapting it to the six labeled categories.",
        "Epoch / update / seed": "One pass through training data / one adjustment of weights / a setting for random choices. Each main run completed 120 epochs and 7,920 updates.",
        "Batch / learning rate / loss": "A group of examples processed together / how large a learning step is / a numerical measure of error that training tries to reduce. Lower training loss alone does not prove better performance on new traffic.",
        "Validation / test": "Examples used to choose a saved model / examples used afterward to score it. Neither is a guarantee about a new customer network.",
        "Inference / logit / softmax": "Using the saved model / one raw class score / a transformation of all class scores into values that sum to one. Those values are uncalibrated here.",
        "Accuracy / precision / recall / F1": "Fraction correct / how often a predicted class is right / how many actual members of a class are found / a balance of precision and recall. Macro F1 weights classes equally; weighted F1 uses their true counts.",
        "GPU / NPU / SmartNIC / DPU": "A parallel compute accelerator / a neural compute accelerator / a programmable network card / a data-processing unit often combining networking and processor cores. They have different supported operations.",
        "CUDA / Triton / compiler": "Software used to run calculations on the NVIDIA GPU / a tool for writing GPU operations / a program that translates code into instructions a processor can execute. Old custom operations needed build changes for the tested GB10.",
        "PCAP / flow cache / calibration": "A file storing captured packets / memory holding information about ongoing flows / checking whether a score corresponds to the observed frequency of an event. These live-system and confidence checks remain future work here.",
        "Hash / provenance": "A file fingerprint / records describing where a file came from. They help check identity; they do not prove scientific quality or grant usage rights."
    }
    terms = "".join(f"<dt>{esc(k)}</dt><dd>{esc(v)}</dd>" for k, v in glossary.items())
    css = (Path(__file__).with_name("learning-guide.css")).read_text()
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Understand the NetMamba+ research, measured training, inputs, demo and limits, one slide at a time.">
<title>NetMamba+ · A field guide to the measured project</title><style>{css}</style></head>
<body><a class="skip" href="#main">Skip to the guide</a>
<header><a href="#top" class="brand">NETMAMBA<span>+</span></a><nav aria-label="Main"><a href="index.html">Open replay</a><a href="{REPO}/releases/latest">Download package</a><a href="{REPO}">Repository</a></nav></header>
<main id="main"><div id="top" class="hero"><p class="eyebrow">Customer field guide · 15 September 2026</p>
<h1>Understand the work.<br>Explain the evidence.</h1><p class="deck">A plain-language companion to the presentation and speaker script. Start here even if network security and machine learning are new to you.</p>
<div class="facts"><p><strong>3 × 120</strong><span>completed fine-tuning epochs</span></p><p><strong>86.65%</strong><span>mean test accuracy · three seeds</span></p><p><strong>Still research</strong><span>live IDS and NPU deployment remain untested</span></p></div></div>
<div class="body-grid"><aside class="toc"><nav aria-label="Guide contents"><a href="#start">Start / set up / test</a><a href="#background">Paper and datasets</a><a href="#questions">Your seven questions</a><ol>{''.join(links)}</ol><a href="#glossary">Plain-language glossary</a></nav></aside>
<div class="reading"><section id="start"><p class="eyebrow">Start here</p><h2>Three ways to use this project</h2>
<ol class="routes"><li><h3>Understand or present it</h3><p>Read this guide, open the <a href="index.html">recorded replay</a>, then follow the slides. In the downloaded ZIP, open <code>docs/customer/demo/guide.html</code> and <code>index.html</code>. Both work offline without Python or a GPU. Links to research records require the internet; the same records are also inside the ZIP.</p><p><a href="{REPO}/releases/latest/download/NetMambaPlus-customer-slides.pptx">PowerPoint with speaker notes</a> · <a href="{REPO}/releases/latest/download/NetMambaPlus-customer-briefing.pdf">Briefing PDF</a></p></li>
<li><h3>Check the delivered files on your computer</h3><p>Install Python 3.10 or newer. Clone or unzip the project and open a terminal in its root folder. Run:</p><pre><code>python3 -m unittest discover -s tests -v
python3 tools/verify_package.py</code></pre><p>The recorded suite passed <strong>54 tests</strong>. Expect <code>OK</code> from the first command and <code>"status": "passed"</code> from the second. These commands do not download data or run GPU training. The CPU checks were executed on Linux; Windows/macOS runs were not tested.</p></li>
<li><h3>Run the model yourself</h3><p>Follow the <a href="{REPO}/blob/main/docs/customer/runbook.md">tested GB10 runbook</a>: get the pinned source and assets → build the GPU environment → check its calculations → train a local classifier → evaluate or predict. The research weights and raw data are obtained separately; they are not in the customer ZIP. Other computers need a separately validated setup.</p></li></ol>
<p class="remember">Full commands, expected files, recovery advice and test results: <a href="{REPO}/blob/main/docs/customer/quickstart.md">simple setup / use / test guide</a>.</p></section>
<section id="background"><p class="eyebrow">Before the slides</p><h2>What are the paper and the data about?</h2>
<p>The paper studies how to recognize patterns in network traffic that may indicate attacks. <strong>NetMamba+</strong> is its model combining byte content, packet sizes and time gaps. A Mamba block scans numerical input units in sequence and updates an internal state. It is not a chatbot, and it does not need an AI chat service to classify traffic.</p>
<p>Your <strong>CICIDS2017</strong> and <strong>UNSW</strong> CSV files are labeled packet tables: 1,410,255 and 79,881 rows. Each has 1,500 payload-byte columns and five metadata columns. They help explain the data problem, but they omit the connection information needed to assemble the required flow inputs.</p>
<p>The actual training uses a different dataset: the authors’ <strong>CICIoT2022</strong> flow release, with 10,404 examples in six categories. Two categories are attacks; four describe IoT power/device activity. A label describes the dataset’s answer. It does not make these six categories a complete list of real-world threats.</p>
<p><a href="{REPO}/blob/main/docs/customer/upstream-comparison.md">Read what changed from the authors’ repository and what each dataset field means</a>.</p></section>
<section id="questions"><p class="eyebrow">Your seven questions</p><h2>Answers you can trace back</h2>{''.join(questions)}</section>
{''.join(sections)}<section id="glossary"><p class="eyebrow">Keep this beside the slides</p><h2>The vocabulary, unpacked</h2><dl>{terms}</dl></section>
<footer>Measured source-based research. The paper’s 97.50% result was not reproduced. See the <a href="{REPO}/blob/main/docs/customer/verification.md">verification record</a> for checks and remaining limits.</footer>
</div></div></main></body></html>'''


def build(source):
    (CUSTOMER / "demo/guide.html").write_text(render(source), encoding="utf-8")
    text = ["# Answers and presentation map", "",
            "The guide follows the same slide numbers and presenter script as the PowerPoint. Briefing page numbers refer to the rendered PDF.", "",
            coverage_markdown(source), ""]
    for item in source["questions"]:
        text += ["## " + item["question"], "", item["answer"], ""]
    text += ["## Additional requested explanations", "",
             "- Paper, datasets and changes from the authors’ repository: slide 13 and [comparison](upstream-comparison.md); briefing page 8.",
             "- Simple setup, usage and testing: slides 14–15 and [quickstart](quickstart.md); briefing page 7.",
             "- Plain-language explanation: [slide-by-slide guide](https://buffbeefalo.github.io/netmambaplus-reproduction/guide.html), also available offline at `demo/guide.html`.",
             "- Actual checks and their limits: [verification record](verification.md) and [acceptance review](acceptance.md).", ""]
    (CUSTOMER / "answers.md").write_text("\n".join(text), encoding="utf-8")


if __name__ == "__main__":
    from build_customer_package import data_and_tokens, substitute
    _, _, tokens, _, _ = data_and_tokens()
    build(json.loads(substitute((CUSTOMER / "presentation-source.json").read_text(), tokens)))
