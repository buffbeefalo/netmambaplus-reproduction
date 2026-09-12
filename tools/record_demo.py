"""Rehearse the actual inference replay in Chromium and record a video backup."""

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import repro


async def record(args):
    from playwright.async_api import async_playwright
    predictions = json.loads((args.replay / "predictions.json").read_text())
    rows = predictions["predictions"]
    expected_errors = sum(row["label"] != row["prediction"] for row in rows)
    attack_ids = {index for name, index in predictions["class_mapping"].items()
                  if name in ("6-Attacks-1-Flood", "6-Attacks-2-RTSP Brute Force")}
    expected_alerts = sum(row["prediction"] in attack_ids for row in rows)
    args.output.mkdir(parents=True, exist_ok=False)
    errors = []
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 1000},
                                            record_video_dir=str(args.output),
                                            record_video_size={"width": 1440, "height": 1000})
        page = await context.new_page()
        page.on("pageerror", lambda error: errors.append(str(error)))
        await page.goto((args.replay / "index.html").resolve().as_uri())
        await page.get_by_role("heading", name="Recorded inference replay", exact=True).wait_for()
        await page.wait_for_timeout(1500)
        await page.get_by_role("button", name="Play replay", exact=True).click()
        await page.wait_for_timeout(2200)
        await page.get_by_role("button", name="Pause replay", exact=True).click()
        displayed = await page.locator("#rows tr").count()
        if not 0 < displayed < len(rows):
            raise ValueError("Play/pause did not produce a partial measured replay")
        await page.get_by_role("button", name="Show all", exact=True).click()
        if await page.locator("#rows tr").count() != len(rows):
            raise ValueError("Show all omitted prediction rows")
        await page.screenshot(path=str(args.output / "replay-screenshot.png"), full_page=False)
        await page.wait_for_timeout(2000)
        await page.locator("#filter").select_option("errors")
        if await page.locator("#rows tr").count() != expected_errors:
            raise ValueError("Error filter disagrees with the recorded predictions")
        await page.wait_for_timeout(3000)
        await page.locator("#filter").select_option("alerts")
        if await page.locator("#rows tr").count() != expected_alerts:
            raise ValueError("Attack-class filter disagrees with the recorded predictions")
        await page.wait_for_timeout(2500)
        await page.locator("#filter").select_option("all")
        await page.get_by_role("button", name="Reset", exact=True).click()
        if await page.locator("#rows tr").count() != 0:
            raise ValueError("Reset did not clear the display")
        await page.get_by_role("button", name="Show all", exact=True).click()
        await page.wait_for_timeout(1800)
        desktop_overflow = await page.evaluate("document.documentElement.scrollWidth > window.innerWidth")
        await page.set_viewport_size({"width": 390, "height": 844})
        mobile_overflow = await page.evaluate("document.documentElement.scrollWidth > window.innerWidth")
        await page.screenshot(path=str(args.output / "replay-mobile.png"), full_page=False)
        await page.set_viewport_size({"width": 1440, "height": 1000})
        version = browser.version
        video = page.video
        await context.close()
        await video.save_as(str(args.output / "recorded-demo.webm"))
        original = await video.path()
        if Path(original).name != "recorded-demo.webm":
            Path(original).unlink()
        await browser.close()
    if errors or desktop_overflow or mobile_overflow:
        raise ValueError(f"Browser errors or horizontal page overflow: {errors}, {desktop_overflow}, {mobile_overflow}")
    evidence = {"status": "passed", "browser": version, "recorded_at": repro.timestamp(),
                "tool_sha256": repro.sha256_file(__file__),
                "html_sha256": repro.sha256_file(args.replay / "index.html"),
                "predictions_sha256": repro.sha256_file(args.replay / "predictions.json"),
                "checkpoint_sha256": predictions["checkpoint_sha256"],
                "rows": len(rows), "errors": expected_errors, "attack_class_predictions": expected_alerts,
                "checks": ["play/pause", "all rows", "error filter", "attack filter", "reset", "no browser errors",
                           "no desktop horizontal overflow", "no mobile horizontal overflow"],
                "video_sha256": repro.sha256_file(args.output / "recorded-demo.webm"),
                "scope": "Recording of actual measured inference replay; playback pacing is not model latency or live traffic"}
    repro.atomic_json(args.output / "browser-check.json", evidence, overwrite=False)
    print(json.dumps(evidence, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replay", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    asyncio.run(record(args))


if __name__ == "__main__":
    main()
