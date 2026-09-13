"""Render the standalone course from reviewed local sources; no dependencies."""

import argparse
import copy
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs/customer/course-source.json"
OUTPUT = ROOT / "docs/customer/demo/course/index.html"
TOKEN = re.compile(r"\{\{([a-z0-9_]+)\}\}")
REPO = "https://github.com/buffbeefalo/netmambaplus-reproduction"
COURSE_URL = "https://buffbeefalo.github.io/netmambaplus-reproduction/course/"


def read(path):
    def reject(value):
        raise ValueError(f"Nonfinite JSON: {value}")
    return json.loads(path.read_text(encoding="utf-8"), parse_constant=reject)


def pointer(value, selector):
    if selector == "/":
        return value
    if not selector.startswith("/"):
        raise ValueError(f"Invalid JSON selector: {selector}")
    for key in selector[1:].split("/"):
        key = key.replace("~1", "/").replace("~0", "~")
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value


def local(path, root=ROOT):
    target = (root / path).resolve()
    if not target.is_relative_to(root.resolve()) or not target.is_file():
        raise ValueError(f"Invalid local reference: {path}")
    return target


def fact_values(source, root=ROOT):
    values = {}
    for name, item in source["facts"].items():
        actual = pointer(read(local(item["file"], root)), item["pointer"])
        if actual != item["expected"]:
            raise ValueError(f"Evidence disagreement: {name}")
        fmt = item["format"]
        if fmt == "percent":
            values[name] = f"{actual * 100:.2f}%"
        elif fmt == "points":
            values[name] = f"{actual * 100:.2f}"
        elif fmt == "integer":
            values[name] = f"{actual:,}"
        elif fmt == "text":
            values[name] = str(actual)
        else:
            raise ValueError(f"Unknown fact format: {fmt}")
    return values


def resolved(source, root=ROOT):
    values = fact_values(source, root)
    def visit(value):
        if isinstance(value, str):
            def replace(match):
                if match[1] not in values:
                    raise ValueError(f"Unknown fact token: {match[1]}")
                return values[match[1]]
            return TOKEN.sub(replace, value)
        if isinstance(value, list):
            return [visit(x) for x in value]
        if isinstance(value, dict):
            return {k: visit(v) for k, v in value.items()}
        return value
    return visit(copy.deepcopy(source))


def words(value):
    return len(re.findall(r"\S+", value))


def teaching_text(segment):
    texts = [segment["title"]] if segment["teaching"] else []
    for block in segment["teaching"]:
        if block["type"] in ("p", "code"):
            texts.append(block["text"])
        elif block["type"] == "table":
            texts.extend(block["headers"])
            texts.extend(cell for row in block["rows"] for cell in row)
        elif block["type"] != "demo":
            raise ValueError(f"Unknown teaching block: {block['type']}")
    return " ".join(texts)


def practice_text(segment):
    activity = segment["activity"]
    texts = [activity["instruction"]]
    for question in activity["questions"]:
        texts.extend([question["prompt"], *question["options"], question["explanation"]])
        # The key repeats the correct option and adds two short UI labels.
        texts.extend([question["options"][question["correct"]], "Check answer Answer and explanation"])
    texts.extend(activity.get("rubric", []))
    texts.append(activity.get("closing", ""))
    return " ".join(texts)


def mmss(seconds):
    return f"{seconds // 60:02}:{seconds % 60:02}"


def e(value):
    return html.escape(str(value), quote=True)


STYLE = """
:root{--paper:#f5f3eb;--ink:#162b36;--muted:#485c63;--accent:#00685c;--line:#c9d2cb;--panel:#fffef9;--warm:#f0ddad}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:20px}body{margin:0;background:var(--paper);color:var(--ink);font:17px/1.62 'Trebuchet MS',Arial,sans-serif}
a{color:var(--accent);text-underline-offset:3px}a:hover{text-decoration-thickness:2px}button,input{font:inherit}button,summary,label{touch-action:manipulation}
:focus-visible{outline:3px solid #a34416;outline-offset:4px}.skip{position:absolute;top:-100px;left:14px;z-index:5;background:white;padding:12px}.skip:focus{top:12px}
.shell{max-width:1260px;margin:auto;padding:42px 40px}.eyebrow{font-size:12px;font-weight:bold;letter-spacing:.12em;text-transform:uppercase;color:var(--accent)}h1,h2{font-family:Georgia,serif;line-height:1.12;font-weight:normal;letter-spacing:-.035em}h1{font-size:clamp(40px,6vw,76px);max-width:900px;margin:15px 0 18px}h2{font-size:clamp(28px,3vw,40px);margin:8px 0 24px}h3{font-size:19px;margin:20px 0 12px}p{margin:0 0 18px}.subtitle{font-size:22px;color:var(--muted);max-width:700px}.intro{max-width:820px}.intro p{max-width:74ch}.meta{display:flex;flex-wrap:wrap;gap:8px;margin:24px 0}.pill{padding:5px 12px;border:1px solid var(--line);border-radius:4px;font-size:13px}.links{display:flex;flex-wrap:wrap;gap:14px;font-size:14px}
.layout{display:grid;grid-template-columns:240px minmax(0,1fr);gap:48px;border-top:2px solid var(--ink);margin-top:34px;padding-top:30px}aside{align-self:start;position:sticky;top:20px}nav ol{list-style:none;padding:0;margin:14px 0}nav li{border-top:1px solid var(--line)}nav a{display:block;text-decoration:none;padding:11px 2px;font-size:14px;color:var(--ink)}nav a:hover{color:var(--accent)}nav .time{font:12px/1.5 monospace;color:var(--accent);display:block}nav strong{font-weight:normal}.score{padding:14px;background:#e3ede5;font-size:14px;border-left:3px solid var(--accent);margin-top:20px}.score p{margin:0 0 8px}.fine{font-size:13px;color:var(--muted)}.lesson{padding-bottom:42px;margin-bottom:38px;border-bottom:1px solid var(--line);min-width:0}.lesson:last-child{margin-bottom:10px}.budget{font-size:13px;color:var(--muted);margin-bottom:12px}.teaching{max-width:76ch}.practice{background:var(--panel);border:1px solid var(--line);padding:24px;margin:24px 0 14px;border-radius:4px}.practice h3{margin-top:0}.practice>p{font-size:15px}fieldset{border:0;margin:0;padding:0;min-width:0}legend{font-weight:bold;margin-bottom:12px;width:100%}.option{display:flex;align-items:flex-start;gap:10px;padding:11px 12px;border:1px solid var(--line);border-radius:4px;margin:8px 0;cursor:pointer;line-height:1.45}.option:has(input:checked){border-color:var(--accent);background:#eaf3ea}.option input{flex:0 0 auto;margin-top:5px;width:18px;height:18px;accent-color:var(--accent)}button{padding:10px 15px;background:var(--accent);color:white;border:0;border-radius:4px;cursor:pointer;margin:10px 0}button:hover{background:#004e45}.js-only{display:none}.enhanced .js-only{display:inline-block}.feedback{font-size:15px;font-weight:bold;margin-top:12px}.feedback:empty{display:none}details{border-top:1px solid var(--line);margin-top:16px;padding-top:12px}summary{cursor:pointer;font-weight:bold;min-height:30px}details p{margin:12px 0 0;font-size:15px}.sources{font-size:12px;color:var(--muted);line-height:1.6;overflow-wrap:anywhere}.sources a{margin-right:12px}.table-wrap{margin:22px 0}table{border-collapse:collapse;width:100%;font-size:15px;text-align:left;table-layout:fixed}th,td{border-bottom:1px solid var(--line);padding:10px 12px;vertical-align:top;overflow-wrap:anywhere}th{background:#e3eae3;font-size:13px}td:first-child,th:first-child{width:31%}pre{white-space:pre-wrap;overflow-wrap:anywhere;word-break:break-word;background:var(--ink);color:#f5f3eb;padding:18px;border-radius:4px;font-size:13px;line-height:1.7}.saved-row{border-left:4px solid #b16c0b;padding:20px;background:#fbefd4;margin:22px 0}.saved-row h3{margin:0 0 14px}.saved-row .result{font-size:22px;margin-bottom:12px}.bar{display:block;width:100%;height:5px;background:#e0d7bc;margin-top:6px}.bar span{display:block;background:var(--accent);height:100%}.saved-row table{font-size:14px}.saved-row td:first-child{width:60%}.rubric{margin:12px 0}.rubric label{font-size:15px}.optional{padding:25px;border:1px solid var(--line);margin-top:25px}.optional ul{padding-left:20px}.optional li{padding:5px 0}.optional h2{font-size:30px}.provenance{font-size:12px;overflow-wrap:anywhere}.lesson p,.subtitle{overflow-wrap:anywhere}footer{font-size:13px;margin-top:28px;padding-top:22px;border-top:1px solid var(--line)}noscript p{background:#f0ddad;padding:15px}
@media(max-width:850px){.shell{padding:28px 24px}.layout{grid-template-columns:1fr;gap:24px}aside{position:static}nav ol{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:0 16px}.score{margin-top:12px}.layout{padding-top:15px}h1{font-size:52px}}
@media(max-width:480px){body{font-size:16px}.shell{padding:24px 16px}h1{font-size:42px}.subtitle{font-size:19px}nav ol{grid-template-columns:repeat(2,minmax(0,1fr));gap:0 12px}nav a{font-size:13px}.practice,.saved-row{padding:17px}th,td{padding:9px 6px;font-size:13px}.links{gap:10px}.option{font-size:15px;padding:11px 8px}h2{font-size:32px}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
@media print{body{background:white;font-size:11pt}.shell{padding:0}.layout{display:block;margin-top:20px}.skip,aside,.js-only,.links{display:none!important}.lesson{break-before:page;border:0;margin:0;padding:0}.practice,.saved-row{break-inside:avoid}details>*{display:block!important}details::details-content{content-visibility:visible!important;display:block!important}details{break-inside:avoid}h1{font-size:38pt}h2{font-size:25pt}.optional{break-before:page}a{color:inherit}.sources{font-size:8pt}.feedback{display:none}}
"""

SCRIPT = """
const answerKeys = ANSWER_KEYS;
function scoreAnswers(answers, keys) {
  let checked = 0, correct = 0;
  for (const [id, key] of Object.entries(keys)) {
    if (Object.prototype.hasOwnProperty.call(answers, id)) {
      checked += 1;
      if (answers[id] === key) correct += 1;
    }
  }
  return {checked, correct, total: Object.keys(keys).length};
}
(() => {
  document.documentElement.classList.add('enhanced');
  const answers = {};
  const status = document.getElementById('score-status');
  function update() {
    const result = scoreAnswers(answers, answerKeys);
    status.textContent = `${result.checked} of ${result.total} checked; ${result.correct} correct on current answers.`;
  }
  for (const form of document.querySelectorAll('form[data-question]')) {
    const id = form.dataset.question;
    const feedback = document.getElementById(`${id}-feedback`);
    form.addEventListener('submit', event => {
      event.preventDefault();
      const selected = form.querySelector('input:checked');
      if (!selected) {feedback.textContent = 'Choose an answer first.'; return;}
      answers[id] = Number(selected.value);
      feedback.textContent = answers[id] === answerKeys[id]
        ? 'Correct. Read the explanation below to check your reasoning.'
        : 'Review this choice. Read the explanation below, then try again.';
      update();
    });
    form.addEventListener('change', () => {
      delete answers[id];
      feedback.textContent = '';
      update();
    });
  }
  update();
})();
"""


def demo_html(source):
    record = source["demo"]["expected"]
    names = {value: key for key, value in source["demo"]["class_mapping"].items()}
    rows = []
    for index, score in enumerate(record["scores"]):
        label = names[index]
        rows.append(f'<tr><td>{index}: {e(label)}</td><td>{score * 100:.2f}%'
                    f'<span class="bar" aria-hidden="true"><span style="width:{score * 100:.4f}%"></span></span></td></tr>')
    return f'''<div class="saved-row" id="recorded-example">
<div class="eyebrow">Recorded inference · seed 0 · row {record['row']}</div>
<h3>Prediction: {e(names[record['prediction']])}</h3>
<p class="result">{record['scores'][record['prediction']] * 100:.2f}% display score</p>
<table><caption>Six normalized scores from the saved logits</caption><thead><tr><th scope="col">Class</th><th scope="col">Score</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
<details id="known-label"><summary>Reveal the known dataset label</summary><p>Class {record['label']}: <strong>{e(names[record['label']])}</strong>. The model prediction is incorrect for this labeled row.</p></details>
<p class="provenance">Source: {e(source['demo']['file'])} · {e(source['demo']['pointer'])}<br>Checkpoint SHA-256: {e(source['demo']['checkpoint_sha256'])}</p>
</div>'''


def render(source, root=ROOT):
    source = resolved(source, root)
    nav, sections, keys = [], [], {}
    elapsed = 0
    for number, segment in enumerate(source["segments"], 1):
        start, end = mmss(elapsed), mmss(elapsed + segment["seconds"])
        elapsed += segment["seconds"]
        id = segment["id"]
        nav.append(f'<li><a href="#{e(id)}"><span class="time">{start}–{end}</span><strong>{number:02}. {e(segment["title"])}</strong></a></li>')
        blocks = []
        for block in segment["teaching"]:
            kind = block["type"]
            if kind == "p":
                blocks.append(f'<p>{e(block["text"])}</p>')
            elif kind == "code":
                blocks.append(f'<pre><code>{e(block["text"])}</code></pre>')
            elif kind == "table":
                headers = ''.join(f'<th scope="col">{e(x)}</th>' for x in block["headers"])
                rows = ''.join('<tr>' + ''.join(f'<td>{e(x)}</td>' for x in row) + '</tr>' for row in block["rows"])
                blocks.append(f'<div class="table-wrap"><table><thead><tr>{headers}</tr></thead><tbody>{rows}</tbody></table></div>')
            elif kind == "demo":
                blocks.append(demo_html(source))
            else:
                raise ValueError(f"Unknown teaching block: {kind}")
        activity = segment["activity"]
        exercises = [f'<p>{e(activity["instruction"])}</p>']
        for question in activity["questions"]:
            qid = question["id"]
            keys[qid] = question["correct"]
            choices = ''.join(f'<label class="option" for="{e(qid)}-{index}"><input type="radio" id="{e(qid)}-{index}" name="{e(qid)}" value="{index}"><span>{e(option)}</span></label>' for index, option in enumerate(question["options"]))
            exercises.append(f'''<form data-question="{e(qid)}"><fieldset><legend>{e(question['prompt'])}</legend>{choices}</fieldset><button class="js-only" type="submit">Check answer</button><p id="{e(qid)}-feedback" class="feedback" role="status" aria-live="polite"></p></form>
<details class="answer-key" id="{e(qid)}-key"><summary>Answer and explanation</summary><p><strong>{e(question['options'][question['correct']])}</strong></p><p>{e(question['explanation'])}</p></details>''')
        if "rubric" in activity:
            exercises.append('<div class="rubric">' + ''.join(f'<label class="option" for="rubric-{index}"><input id="rubric-{index}" type="checkbox"><span>{e(item)}</span></label>' for index, item in enumerate(activity["rubric"])) + '</div>')
            exercises.append(f'<p>{e(activity["closing"])}</p>')
        citations = []
        for ref_id in segment["references"]:
            ref = source["references"][ref_id]
            citations.append(f'<a href="{REPO}/blob/main/{e(ref["path"])}" title="{e(ref["selector"])} · SHA-256 {e(ref["sha256"])}">{e(ref["label"])}</a>')
        slides = ', '.join(str(x) for x in segment["slides"])
        pages = ', '.join(str(x) for x in segment["briefing_pages"])
        sections.append(f'''<section class="lesson" id="{e(id)}" aria-labelledby="{e(id)}-title">
<div class="eyebrow">Lesson {number:02} · {start}–{end}</div>
<h2 id="{e(id)}-title">{e(segment['title'])}</h2>
<p class="budget">Plan: {segment['teaching_seconds']} seconds reading + {segment['practice_seconds']} seconds practice and answer review</p>
<div class="teaching">{''.join(blocks)}</div>
<div class="practice"><h3>{'Customer teach-back' if 'rubric' in activity else 'Try it yourself'}</h3>{''.join(exercises)}</div>
<div class="sources">Optional evidence: {''.join(citations)}<br>Presentation cross-reference: slides {slides}; briefing PDF pages {pages}. Evidence hashes and exact selectors are in the course source.</div>
</section>''')
    resources = ''.join(f'<li><a href="{e(item["url"])}">{e(item["label"])}</a></li>' for item in source["resources"])
    script = SCRIPT.replace("ANSWER_KEYS", json.dumps(keys, sort_keys=True).replace("</", "<\\/"))
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light"><meta name="description" content="A planned 30-minute, evidence-based NetMamba+ course with real prediction practice and customer teach-back."><title>{e(source['title'])}</title><style>{STYLE}</style></head>
<body><a class="skip" href="#course-main">Skip to lessons</a><div class="shell">
<header class="intro"><div class="eyebrow">A practical course · measured reproduction attempt</div><h1>{e(source['title'])}</h1><p class="subtitle">{e(source['subtitle'])}</p><p><strong>{e(source['mission'])}</strong></p><p>{e(source['orientation'])}</p>
<div class="meta"><span class="pill">9 lessons · 8 practice questions</span><span class="pill">17½ minutes teaching · 12½ minutes practice</span><span class="pill">Works offline · no AI account needed</span></div>
<div class="links"><a href="https://raw.githubusercontent.com/buffbeefalo/netmambaplus-reproduction/main/docs/customer/demo/course/index.html" download="NetMambaPlus-course.html">Download HTML (save linked file)</a><a href="{REPO}">Open the repository</a><a href="#optional">Further reading and downloads</a></div>
<noscript><p>All lessons, the saved prediction and answer keys work without JavaScript. Select answers for yourself and open “Answer and explanation” to review them. Automatic scoring is unavailable.</p></noscript></header>
<div class="layout"><aside><nav aria-label="Course schedule"><div class="eyebrow">Your 30-minute route</div><ol>{''.join(nav)}</ol></nav><div class="score"><p><strong>Objective practice</strong></p><p id="score-status" aria-live="polite">Eight questions with explanatory keys.</p><p class="fine">Practice feedback only. Reading, answer reveals and rubric checks do not award quiz points. Your final explanation is assessed separately.</p></div></aside>
<main id="course-main" tabindex="-1">{''.join(sections)}
<section class="optional" id="optional"><div class="eyebrow">After the timed course · 0 counted minutes</div><h2>Keep the evidence within reach</h2><p>These links are optional; essential learning and practice are already embedded above. External references need a connection. For a single downloaded HTML file, the full replay and slide guide also need their separate downloads.</p><ul>{resources}</ul><p class="fine">Optional AI practice: ask a local model or coding assistant to challenge your two-minute explanation using the reviewed results and limitations. Check every factual correction against the evidence; AI feedback is not certification. Installation, training, extended replay, narration and AI tutoring are outside the 30-minute plan.</p></section>
</main></div><footer>Thirty minutes is a planned allocation, not a guarantee for every learner. Reading is budgeted at 120 words per minute, with separate activity time. Automated checks do not measure human learning. See the course verification record for browser results, content review and the pending human-paced rehearsal. This course supplements the immutable audited customer release.</footer>
</div><script>{script}</script></body></html>
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Compare without changing any files")
    args = parser.parse_args()
    from verify_course import verify
    source = read(SOURCE)
    verify(source, check_render=False, check_record=False)
    output = render(source)
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != output:
            raise SystemExit("Course render is stale; review the source and run tools/build_course.py")
        print("Course render matches its reviewed source and evidence.")
    else:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(output, encoding="utf-8")
        print(str(OUTPUT.relative_to(ROOT)))


if __name__ == "__main__":
    main()
