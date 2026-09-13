"""Check the course's timing, source bindings, output and honest review status."""

import argparse
import datetime
import hashlib
import json
import re
import time
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

import build_course as build

ROOT = build.ROOT
RECORD = ROOT / "docs/customer/course-verification.md"
ALLOCATIONS = [
    ("purpose", 120, 90, 30), ("inputs", 240, 180, 60),
    ("lifecycle", 240, 180, 60), ("repository", 180, 120, 60),
    ("measurements", 240, 150, 90), ("demo", 240, 90, 150),
    ("operate", 240, 150, 90), ("future", 120, 90, 30),
    ("teach-back", 180, 0, 180),
]
TOPICS = {"paper", "csvs", "tried", "learning", "inputs", "results", "demo", "hardware",
          "gaps", "upstream", "files", "setup", "tests", "downloads", "evidence", "research"}
QUESTIONS = {"tried", "learning", "inputs", "results", "demo", "hardware", "gaps"}
REQUIRED_FACTS = {"seed0", "seed1", "seed2", "mean_accuracy", "accuracy_sd", "paper_accuracy",
                  "epochs", "updates", "cic_rows", "unsw_rows", "train_rows", "valid_rows",
                  "test_rows", "source_commit", "demo_score"}
RECORD_FIELDS = {"content_review", "automated_checks", "browser_checks", "human_rehearsal", "publication"}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.hrefs = [], []
        self.runtime_network = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "a" and "href" in attrs:
            self.hrefs.append(attrs["href"])
        if tag in {"iframe", "img", "script", "audio", "video", "source"} and attrs.get("src"):
            self.runtime_network = True
        if tag == "link" and attrs.get("rel") == "stylesheet":
            self.runtime_network = True


def check_url(url, root=ROOT):
    parsed = urlparse(url)
    if parsed.scheme:
        if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
            raise ValueError(f"Invalid external URL: {url}")
        if parsed.netloc == "github.com" and parsed.path.startswith("/buffbeefalo/netmambaplus-reproduction/blob/main/"):
            build.local(unquote(parsed.path.split("/blob/main/", 1)[1]), root)
    elif not url.startswith("#"):
        target = ((root / build.OUTPUT.relative_to(ROOT)).parent / unquote(parsed.path)).resolve()
        course_target = (root / build.OUTPUT.relative_to(ROOT)).resolve()
        if (not target.is_relative_to((root / "docs/customer/demo").resolve())
                or (target != course_target and not target.is_file())):
            raise ValueError(f"Broken deployed link: {url}")
    return parsed


def verify_record(record, source, rendered, root=ROOT):
    if record.get("schema_version") != 1 or set(record.get("checks", {})) != RECORD_FIELDS:
        raise ValueError("Verification record has missing check statuses")
    if record.get("source_sha256") != digest(root / build.SOURCE.relative_to(ROOT)):
        raise ValueError("Verification record source hash is stale")
    if record.get("html_sha256") != hashlib.sha256(rendered.encode()).hexdigest():
        raise ValueError("Verification record HTML hash is stale")
    pending = []
    for name, item in record["checks"].items():
        if item.get("status") not in {"passed", "pending", "failed"}:
            raise ValueError(f"Invalid verification status: {name}")
        if not item.get("detail"):
            raise ValueError(f"Missing verification detail: {name}")
        if item["status"] != "passed":
            pending.append(name)
        elif not item.get("receipt"):
            raise ValueError(f"Passed verification requires a receipt: {name}")
    human = record["checks"]["human_rehearsal"]
    if human["status"] == "passed":
        receipt = human["receipt"]
        if (not receipt.get("human_performer") or receipt.get("method") != "human_full_route"
                or len(receipt.get("actual_segment_seconds", [])) != 9
                or any(type(x) not in (int, float) or x <= 0 for x in receipt["actual_segment_seconds"])
                or not receipt.get("activities_and_answer_review_completed")
                or not receipt.get("deviations_reviewed")):
            raise ValueError("Human rehearsal cannot be inferred from arithmetic or automation")
    for name in ("browser_checks", "publication"):
        item = record["checks"][name]
        if item["status"] == "passed" and item["receipt"].get("html_sha256") != record["html_sha256"]:
            raise ValueError(f"Stale {name} receipt")
    browser = record["checks"]["browser_checks"]
    if browser["status"] == "passed":
        receipt = browser["receipt"]
        required = {"keyboard", "offline_core", "no_js_answers", "wrong_answer_feedback",
                    "correct_answers", "reveals_do_not_score", "rubric_separate", "no_page_errors", "print_answers"}
        if (set(receipt.get("passed_checks", [])) != required
                or receipt.get("viewport_widths_without_overflow") != [320, 390, 768, 1440]
                or not receipt.get("browser") or not receipt.get("completed_at")):
            raise ValueError("Browser verification receipt is incomplete")
    if record.get("fully_verified") is not (not pending):
        raise ValueError("Pending checks cannot be reported as fully verified")
    if record["checks"]["publication"]["status"] == "passed":
        receipt = record["checks"]["publication"]["receipt"]
        if (receipt.get("url") != build.COURSE_URL or not receipt.get("served_bytes_equal")
                or not receipt.get("download_bytes_equal")):
            raise ValueError("Publication receipt must identify actual served agreement")
    return pending


def verify(source=None, root=ROOT, check_render=True, check_record=True):
    source = source if source is not None else build.read(build.SOURCE)
    if source.get("schema_version") != 1:
        raise ValueError("Unsupported course schema")
    if source.get("total_seconds") != 1800 or source.get("reading_words_per_minute") != 120:
        raise ValueError("Invalid course budget or reading assumption")
    segments = source["segments"]
    if len(segments) != 9:
        raise ValueError("Course budget requires nine segments")
    for item, expected in zip(segments, ALLOCATIONS):
        actual = tuple(item.get(key) for key in ("id", "seconds", "teaching_seconds", "practice_seconds"))
        if actual != expected or item["teaching_seconds"] + item["practice_seconds"] != item["seconds"]:
            raise ValueError(f"Segment budget disagreement: {item.get('id')}")
        if type(item.get("action_seconds")) is not int or item["action_seconds"] <= 0:
            raise ValueError("Every activity needs actual action time")
    if segments[-1]["action_seconds"] != 120:
        raise ValueError("Final activity must reserve 120 seconds speaking")
    taught = set().union(*(set(x["topics"]) for x in segments if x["teaching"]))
    if set(source.get("required_topics", [])) != TOPICS or not TOPICS <= taught:
        raise ValueError(f"Required topics missing from substantive core teaching: {TOPICS - taught}")
    mappings = source.get("customer_questions", {})
    if set(mappings) != QUESTIONS:
        raise ValueError("Required customer questions are missing")
    for topic, ids in mappings.items():
        if not ids or any(not any(s["id"] == id and s["teaching"] and topic in s["topics"] for s in segments) for id in ids):
            raise ValueError(f"Required customer question mapping is not taught: {topic}")
    if set(source["facts"]) != REQUIRED_FACTS:
        raise ValueError("Required scientific fact bindings are missing")
    used = set(build.TOKEN.findall(json.dumps(source["segments"])))
    if not REQUIRED_FACTS <= used:
        raise ValueError("Required scientific values must be rendered from evidence")
    for id, ref in source["references"].items():
        path = build.local(ref["path"], root)
        if digest(path) != ref["sha256"]:
            raise ValueError(f"Evidence reference hash changed: {id}")
        if ref["kind"] == "json":
            build.pointer(build.read(path), ref["selector"])
        elif ref["kind"] != "text" or not ref["selector"] or ref["selector"] not in path.read_text(encoding="utf-8"):
            raise ValueError(f"Evidence reference anchor missing: {id}")
    evidence_paths = {x["path"] for x in source["references"].values()}
    if any(fact["file"] not in evidence_paths for fact in source["facts"].values()):
        raise ValueError("A fact has no hash-bound evidence reference")
    for path, expected in source["protected_artifacts"].items():
        if digest(build.local(path, root)) != expected:
            raise ValueError(f"Protected artifact changed: {path}")
    inventory = source["protected_checksum_inventory"]
    if hashlib.sha256(inventory["text"].encode()).hexdigest() != inventory["sha256"]:
        raise ValueError("Protected checksum inventory identity changed")
    for line in inventory["text"].splitlines():
        expected, path = line.split("  ", 1)
        if digest(build.local(path, root)) != expected:
            raise ValueError(f"Previously audited artifact changed: {path}")
    demo = source["demo"]
    original = build.read(build.local(demo["file"], root))
    if (digest(build.local(demo["file"], root)) != demo["sha256"]
            or build.pointer(original, demo["pointer"]) != demo["expected"]
            or original["checkpoint_sha256"] != demo["checkpoint_sha256"]
            or original["class_mapping"] != demo["class_mapping"]):
        raise ValueError("Recorded demo differs from its actual source or provenance")
    all_ids = [s["id"] for s in segments]
    for segment in segments:
        if not segment["references"] or any(ref not in source["references"] for ref in segment["references"]):
            raise ValueError("Missing segment evidence reference")
        if not segment["activity"]["instruction"]:
            raise ValueError("Missing activity instructions")
        questions = segment["activity"]["questions"]
        if segment["id"] != "teach-back" and len(questions) != 1:
            raise ValueError("Each core lesson requires an objective exercise")
        for question in questions:
            all_ids.append(question["id"])
            if (not question["prompt"] or not question["explanation"] or len(question["options"]) < 2
                    or len(set(question["options"])) != len(question["options"])
                    or type(question["correct"]) is not int
                    or question["correct"] not in range(len(question["options"]))):
                raise ValueError(f"Invalid exercise answer key: {question.get('id')}")
    if len(all_ids) != len(set(all_ids)) or any(not re.fullmatch(r"[a-z][a-z0-9-]*", id) for id in all_ids):
        raise ValueError("Course identifiers must be unique and safe")
    if len(segments[-1]["activity"].get("rubric", [])) != 5:
        raise ValueError("Final customer explanation requires five rubric points")
    material = build.resolved(source, root)
    reading = []
    for index, segment in enumerate(material["segments"]):
        teaching = build.teaching_text(segment)
        if index == 0:
            teaching += " " + " ".join(material[key] for key in ("title", "subtitle", "mission", "orientation"))
            teaching += " Nine lessons. Eight questions. Seventeen and a half minutes teaching; twelve and a half minutes practice."
        practice = build.practice_text(segment)
        if segment["id"] == "demo":
            # Include the displayed row, labels, score table and reveal text in practice reading.
            parser = Text()
            parser.feed(build.demo_html(material))
            practice += " " + " ".join(parser.text)
        if segment["teaching"]:
            teaching += " Plan: reading, practice and answer review."
        tw, pw = build.words(teaching), build.words(practice)
        if tw / 2 > segment["teaching_seconds"] or pw / 2 + segment["action_seconds"] > segment["practice_seconds"]:
            raise ValueError(f"Reading load exceeds {segment['id']} budget: teaching {tw}/ {segment['teaching_seconds'] * 2} words; practice {pw}/ {(segment['practice_seconds'] - segment['action_seconds']) * 2} words")
        reading.append(dict(id=segment["id"], teaching_words=tw, practice_words=pw,
                            action_seconds=segment["action_seconds"], planned_seconds=segment["seconds"]))
    for item in source["resources"]:
        if item.get("counted_seconds") != 0 or not item.get("label"):
            raise ValueError("Optional references require zero counted seconds and a purpose")
        if item.get("path"):
            build.local(item["path"], root)
        check_url(item["url"], root)
    rendered = build.render(source, root)
    links = Links()
    links.feed(rendered)
    if len(links.ids) != len(set(links.ids)) or links.runtime_network:
        raise ValueError("Course HTML has duplicate IDs or runtime network dependencies")
    for href in links.hrefs:
        parsed = check_url(href, root)
        if href.startswith("#") and unquote(parsed.fragment) not in links.ids:
            raise ValueError(f"Broken internal anchor: {href}")
    if check_render:
        output = root / build.OUTPUT.relative_to(ROOT)
        if not output.is_file() or output.read_text(encoding="utf-8") != rendered:
            raise ValueError("Course render is stale")
    pending = []
    if check_record:
        text = (root / RECORD.relative_to(ROOT)).read_text(encoding="utf-8")
        match = re.search(r"<!-- course-check-record -->\s*```json\s*(.*?)\s*```", text, re.S)
        if not match:
            raise ValueError("Machine-readable course verification record is missing")
        pending = verify_record(json.loads(match[1]), source, rendered, root)
        council = re.search(r"<!-- course-council-decision -->\s*```json\n(.*?)\n```", text, re.S)
        if (not council or hashlib.sha256(council[1].encode()).hexdigest()
                != "1977587853f8b87ff60178bae953e565b6fab4897f7706a7a8749415e761958f"):
            raise ValueError("Course council decision is missing or altered")
    return dict(status="passed", scope="deterministic course validation; not proof of learning or a human timing rehearsal",
                planned_seconds=sum(s["seconds"] for s in segments),
                teaching_seconds=sum(s["teaching_seconds"] for s in segments),
                practice_seconds=sum(s["practice_seconds"] for s in segments),
                objective_questions=8, required_topics=len(TOPICS), reading_plan=reading,
                required_real_world_checks_pending=pending, fully_verified=check_record and not pending)


class Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []

    def handle_data(self, data):
        self.text.append(data)


def browser_check(output, url=None):
    """Optional Playwright checks; the normal verifier remains stdlib-only."""
    from playwright.sync_api import sync_playwright
    from importlib.metadata import version
    from urllib.request import urlopen

    if output.exists():
        raise ValueError("Browser output must be a fresh directory")
    output = output.resolve()
    if not output.is_relative_to((ROOT / "runs").resolve()):
        raise ValueError("Browser receipts must be written under runs/")
    if url and url != build.COURSE_URL:
        raise ValueError("Hosted browser check must use the declared course URL")
    if url:
        with urlopen(url, timeout=30) as response:
            if response.read() != build.OUTPUT.read_bytes():
                raise ValueError("Hosted course bytes differ from the reviewed file")
    output.mkdir(parents=True)
    started = time.monotonic()
    source = build.read(build.SOURCE)
    keys = {q["id"]: q["correct"] for s in source["segments"] for q in s["activity"]["questions"]}
    checks, widths, errors = [], [], []
    def require(condition, message):
        if not condition:
            raise ValueError(message)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(viewport={"width": 1440, "height": 1000}, offline=not bool(url))
        page = context.new_page()
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(url or build.OUTPUT.as_uri())
        if url:
            with page.expect_download(timeout=15000) as download_event:
                page.get_by_role("link", name="Download HTML", exact=True).click()
            download = download_event.value
            downloaded = output / "NetMambaPlus-course.html"
            download.save_as(str(downloaded))
            require(downloaded.read_bytes() == build.OUTPUT.read_bytes(), "Downloaded course bytes differ")
            page.reload()
        page.keyboard.press("Tab")
        require(page.locator(":focus").get_attribute("href") == "#course-main", "Skip link keyboard failure")
        page.keyboard.press("Enter")
        require(page.locator(":focus").get_attribute("id") == "course-main", "Skip target keyboard failure")
        page.locator("#q-purpose-0").focus()
        page.keyboard.press("Space")
        page.keyboard.press("Tab")
        page.keyboard.press("Enter")
        require("Correct." in page.locator("#q-purpose-feedback").inner_text(), "Keyboard answer failure")
        checks.append("keyboard")
        page.reload()
        for details in page.locator("details").all():
            details.locator("summary").click()
        require(page.locator("#score-status").inner_text().startswith("0 of 8 checked; 0 correct"), "Reveals awarded points")
        checks.append("reveals_do_not_score")
        page.locator("#q-purpose-1").check()
        page.locator('form[data-question="q-purpose"] button').click()
        require("Review this choice" in page.locator("#q-purpose-feedback").inner_text(), "Wrong answer feedback absent")
        require("0 correct" in page.locator("#score-status").inner_text(), "Wrong answer awarded points")
        checks.append("wrong_answer_feedback")
        for id, correct in keys.items():
            page.locator(f"#{id}-{correct}").check()
            page.locator(f'form[data-question="{id}"] button').click()
        require(page.locator("#score-status").inner_text().startswith("8 of 8 checked; 8 correct"), "Correct answer scoring failed")
        page.locator("#q-purpose-1").check()
        require(page.locator("#score-status").inner_text().startswith("7 of 8 checked; 7 correct"), "Changed answer retained old credit")
        page.locator('form[data-question="q-purpose"] button').click()
        require(page.locator("#score-status").inner_text().startswith("8 of 8 checked; 7 correct"), "Revised answer scoring failed")
        pure = page.evaluate("scoreAnswers({'q-purpose':0, 'elapsed':1800, 'rubric':true}, answerKeys)")
        require(pure == {"checked": 1, "correct": 1, "total": 8}, "Unrelated state affected objective scoring")
        checks.append("correct_answers")
        before = page.locator("#score-status").inner_text()
        for checkbox in page.locator(".rubric input").all():
            checkbox.check()
        require(page.locator("#score-status").inner_text() == before, "Rubric affected quiz score")
        require("self-assessment, not independent certification" in page.locator("#teach-back").inner_text(), "Teach-back claim missing")
        checks.append("rubric_separate")
        for width in (320, 390, 768, 1440):
            page.set_viewport_size({"width": width, "height": 1000})
            page.evaluate("window.scrollTo({top:0,left:0,behavior:'instant'})")
            page.evaluate("new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))")
            require(page.evaluate("scrollY === 0"), "Screenshot did not return to the course heading")
            require(page.evaluate("document.documentElement.scrollWidth <= innerWidth"), f"Page overflow at {width}")
            page.screenshot(path=str(output / f"course-{width}.png"))
            widths.append(width)
        page.locator("#recorded-example").screenshot(path=str(output / "recorded-example.png"))
        require(not errors, f"Page errors: {errors}")
        checks.append("no_page_errors")
        context.close()
        offline = browser.new_context(java_script_enabled=False, offline=True, viewport={"width": 390, "height": 1000})
        nojs = offline.new_page()
        requests = []
        nojs.on("request", lambda request: requests.append(request.url))
        nojs.goto(build.OUTPUT.as_uri())
        require(nojs.locator(".lesson").count() == 9, "Offline lesson missing")
        for details in nojs.locator("details").all():
            details.locator("summary").click()
            require(details.get_attribute("open") is not None, "No-JS disclosure failed")
        require(nojs.locator(".answer-key").count() == 8, "No-JS answers missing")
        require(nojs.locator("#known-label p").is_visible(), "No-JS known label missing")
        nojs.locator("#q-purpose-key summary").focus()
        nojs.keyboard.press("Enter")
        require(nojs.locator("#q-purpose-key").get_attribute("open") is None, "No-JS keyboard disclosure failed")
        require(all(x.startswith("file:") for x in requests), "Offline core made network requests")
        nojs.screenshot(path=str(output / "course-no-js.png"))
        checks.extend(["offline_core", "no_js_answers"])
        for details in nojs.locator("details").all():
            if details.get_attribute("open") is not None:
                details.locator("summary").click()
        nojs.emulate_media(media="print")
        visible = nojs.evaluate("Array.from(document.querySelectorAll('details')).every(d => getComputedStyle(d,'::details-content').contentVisibility === 'visible')")
        require(visible, "Print layout conceals closed answer panels")
        nojs.pdf(path=str(output / "course-print.pdf"), format="A4", print_background=True)
        checks.append("print_answers")
        browser_version = browser.version
        browser.close()
    receipt = dict(status="passed", completed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   html_sha256=digest(build.OUTPUT), browser=f"Chromium {browser_version}; Playwright {version('playwright')}",
                   passed_checks=sorted(checks), viewport_widths_without_overflow=widths,
                   method="automated browser functional rehearsal; not a human learning or timing study",
                   elapsed_seconds=round(time.monotonic() - started, 3),
                   hosted_url=url, download_bytes_equal=True if url else None,
                   print_pdf_sha256=digest(output / "course-print.pdf"),
                   screenshots={p.name: digest(p) for p in sorted(output.glob("*.png"))})
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8", newline="\n")
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--browser-output", type=Path, help="Optional Playwright rehearsal into a fresh runs/ directory")
    parser.add_argument("--url", help="Additionally require the public course URL to match reviewed bytes")
    args = parser.parse_args()
    try:
        if args.url and not args.browser_output:
            raise ValueError("--url requires --browser-output")
        report = browser_check(args.browser_output, args.url) if args.browser_output else verify()
        print(json.dumps(report, indent=2))
    except (ValueError, KeyError, IndexError, OSError, TypeError) as error:
        raise SystemExit(f"Course verification failed: {error}") from error


if __name__ == "__main__":
    main()
