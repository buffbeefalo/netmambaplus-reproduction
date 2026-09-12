"""Rehearse the slide-aligned guide in a real browser and save a dated receipt."""

import argparse
import datetime
import hashlib
import json
from pathlib import Path

from build_customer_package import CUSTOMER, data_and_tokens, substitute


def main():
    from playwright.sync_api import sync_playwright

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", help="Hosted guide URL; defaults to the local offline file")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    _, _, tokens, _, _ = data_and_tokens()
    source = json.loads(substitute((CUSTOMER / "presentation-source.json").read_text(), tokens))
    guide = CUSTOMER / "demo/guide.html"
    url = args.url or guide.as_uri()
    errors, widths = [], []
    with sync_playwright() as runtime:
        browser = runtime.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page(viewport={"width": 1440, "height": 1000}, reduced_motion="reduce")
        page.on("pageerror", lambda error: errors.append(str(error)))
        response = page.goto(url, wait_until="load")
        if args.url:
            if response is None or response.status != 200 or response.body() != guide.read_bytes():
                raise ValueError("Hosted guide is not the reviewed local artifact")
        if page.locator("section.lesson").count() != len(source["slides"]):
            raise ValueError("Guide slide inventory differs from the deck")
        for n, slide in enumerate(source["slides"], 1):
            section = page.locator(f"#slide-{n}")
            if section.locator("h2").inner_text() != slide["title"].replace("\n", " "):
                raise ValueError(f"Guide title differs at slide {n}")
            section.locator("summary").click()
            if section.locator("details p").inner_text() != slide["notes"]:
                raise ValueError(f"Guide script differs at slide {n}")
            section.locator("summary").click()
        missing = page.evaluate("""() => [...document.querySelectorAll('a[href^="#"]')]
            .map(a => a.getAttribute('href').slice(1)).filter(id => !document.getElementById(id))""")
        if missing:
            raise ValueError(f"Missing guide anchors: {missing}")
        for width in (320, 390, 768, 1440):
            page.set_viewport_size({"width": width, "height": 1000})
            page.evaluate("window.scrollTo(0, 0)")
            overflow = page.evaluate("document.documentElement.scrollWidth > window.innerWidth")
            if overflow:
                raise ValueError(f"Horizontal page overflow at width {width}")
            widths.append({"width": width, "horizontal_overflow": False})
            if width in (390, 1440):
                page.screenshot(path=str(args.output / f"guide-{width}.png"))
        page.keyboard.press("Control+Home")
        page.keyboard.press("Tab")
        focused = page.locator(":focus")
        if focused.get_attribute("href") != "#main":
            page.goto(url, wait_until="load")
            page.keyboard.press("Tab")
            if page.locator(":focus").get_attribute("href") != "#main":
                raise ValueError("Skip link is not reachable as the first keyboard stop")
        page.keyboard.press("Enter")
        if not page.url.endswith("#main"):
            raise ValueError("Keyboard skip link did not activate")
        if errors:
            raise ValueError(f"Browser errors: {errors}")
        result = {"status": "passed", "checked_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  "url": url, "browser": browser.version, "guide_sections": len(source["slides"]),
                  "questions": len(source["questions"]), "viewport_checks": widths,
                  "checks": ["all titles", "all speaker scripts", "all script disclosures open/close",
                             "all internal anchors", "keyboard skip link", "no JavaScript errors"],
                  "html_sha256": hashlib.sha256(guide.read_bytes()).hexdigest()}
        browser.close()
    (args.output / "browser-check.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
