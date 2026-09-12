"""Check published measurements, artifact hashes and links using only stdlib."""

import argparse
import hashlib
import json
import math
import re
import statistics
import sys
import zipfile
from xml.etree import ElementTree
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
CUSTOMER = ROOT / "docs/customer"
EVIDENCE = CUSTOMER / "evidence"
sys.path.insert(0, str(ROOT))
import replay
from build_customer_package import data_and_tokens, substitute
from build_learning_guide import render, coverage_markdown


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def read(path):
    def invalid(value):
        raise ValueError(f"Nonfinite JSON value {value}: {path}")
    return json.loads(path.read_text(), parse_constant=invalid)


def close(a, b):
    if not math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-10):
        raise ValueError(f"Metric disagreement: {a} versus {b}")


def verify_teaching_material():
    _, _, tokens, _, _ = data_and_tokens()
    source = json.loads(substitute((CUSTOMER / "presentation-source.json").read_text(), tokens))
    documents = read(CUSTOMER / "document-check.json")
    if documents["status"] != "passed":
        raise ValueError("Rendered document page check did not pass")
    for name, expected in (("NetMambaPlus-customer-briefing.pdf", source["briefing_pages"]),
                           ("NetMambaPlus-customer-slides.pdf", len(source["slides"]))):
        if documents["files"][name]["pages"] != expected:
            raise ValueError("Rendered PDF page counts differ from the presentation map")
    for name, record in documents["files"].items():
        if digest(CUSTOMER / name) != record["sha256"]:
            raise ValueError("Rendered document check is stale")
    guide = (CUSTOMER / "demo/guide.html").read_text()
    if guide != render(source):
        raise ValueError("Learning guide is stale relative to the slide content or renderer")
    if len(source["questions"]) != 7 or len({q["id"] for q in source["questions"]}) != 7:
        raise ValueError("Seven distinct customer questions must be mapped")
    notes = (CUSTOMER / "talk-track.md").read_text()
    answers = (CUSTOMER / "answers.md").read_text()
    if coverage_markdown(source) not in notes or coverage_markdown(source) not in answers:
        raise ValueError("Question map is stale in the script or answers")
    for question in source["questions"]:
        if (not question["slides"] or any(n < 1 or n > len(source["slides"]) for n in question["slides"])
                or not question["briefing_pages"]
                or any(n < 1 or n > source["briefing_pages"] for n in question["briefing_pages"])
                or question["answer"] not in answers):
            raise ValueError("Customer answer or slide reference is missing")
    ns = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
    with zipfile.ZipFile(CUSTOMER / "NetMambaPlus-customer-slides.pptx") as deck:
        for index, slide in enumerate(source["slides"], 1):
            title = slide["title"].replace("\n", " ")
            heading = f"## Slide {index} · {title}"
            if heading not in notes or slide["notes"] not in notes:
                raise ValueError(f"Presenter script differs at slide {index}")
            tree = ElementTree.fromstring(deck.read(f"ppt/notesSlides/notesSlide{index}.xml"))
            text = "\n".join(node.text or "" for node in tree.findall(".//a:t", ns))
            if slide["notes"] not in text:
                raise ValueError(f"PowerPoint speaker notes differ at slide {index}")
    return len(source["slides"])


def verify_audit(results):
    audit = CUSTOMER / "audit-evidence"
    inventory = read(audit / "index.json")
    for item in inventory["files"]:
        path = (audit / item["path"]).resolve()
        if not path.is_relative_to(audit.resolve()) or digest(path) != item["sha256"]:
            raise ValueError(f"Audit artifact hash mismatch: {item['path']}")
    for row in results["seeds"]:
        seed = row["seed"]
        metrics = read(audit / f"export-seed{seed}/metrics.json")
        manifest = read(audit / f"export-seed{seed}/manifest.json")
        provenance = read(EVIDENCE / f"seed{seed}/model-export-provenance.json")
        if manifest["status"] != "succeeded":
            raise ValueError("Fresh export evaluation did not succeed")
        if metrics["metrics"]["cm"] != row["metrics"]["confusion_matrix"]:
            raise ValueError("Fresh export evaluation differs from the frozen result")
        if metrics["checkpoint_sha256"] != provenance["checkpoint_sha256"]:
            raise ValueError("Fresh evaluation used a different model-only export")
    for name in ("runtime-main.json", "runtime-rehearsal.json"):
        runtime = read(audit / name)
        if runtime["status"] != "passed" or len(runtime["checks"]) != 7 or not all(c["passed"] for c in runtime["checks"]):
            raise ValueError("Fresh numerical checks are incomplete")
    agreement = read(audit / "unlabeled-agreement.json")
    if agreement["status"] != "passed" or agreement["rows"] != 1041 or agreement["prediction_agreement"] != 1:
        raise ValueError("Full unlabeled agreement check is missing")
    prediction = read(audit / "unlabeled-export/metrics.json")
    reference = read(EVIDENCE / "seed0/replay/predictions.json")
    expected_mapping = read(EVIDENCE / "seed0/model-export-provenance.json")["class_mapping"]
    if prediction["class_mapping"] != expected_mapping:
        raise ValueError("Unlabeled inference class meanings differ from export provenance")
    names = {index: name for name, index in expected_mapping.items()}
    if (len(prediction["predictions"]) != 1041 or len(reference["predictions"]) != 1041
            or reference["checkpoint_sha256"] != agreement["reference_checkpoint_sha256"]
            or prediction["checkpoint_sha256"] != agreement["export_checkpoint_sha256"]):
        raise ValueError("Full unlabeled inference identity differs")
    for index, (actual, expected) in enumerate(zip(prediction["predictions"], reference["predictions"])):
        if actual["row"] != index or expected["row"] != index:
            raise ValueError("Full unlabeled inference row order differs")
        if actual["prediction"] != expected["prediction"] or actual["logits"] != expected["logits"]:
            raise ValueError("Full unlabeled inference differs from the recorded exact agreement")
        if actual["class_name"] != names[actual["prediction"]] or len(actual["scores"]) != 6:
            raise ValueError("Unlabeled inference class name or score vector differs")
        for expected_score, actual_score in zip(replay.probabilities(actual["logits"]), actual["scores"]):
            close(expected_score, actual_score)
    browser = read(audit / "guide/browser-check.json")
    if browser["status"] != "passed" or digest(CUSTOMER / "demo/guide.html") != browser["html_sha256"]:
        raise ValueError("Guide browser receipt is stale or unsuccessful")
    return len(inventory["files"])


def verify(allow_missing_checksums=False):
    inventory = read(EVIDENCE / "artifact-index.json")
    for item in inventory["files"]:
        path = (EVIDENCE / item["path"]).resolve()
        if not path.is_relative_to(EVIDENCE.resolve()) or digest(path) != item["sha256"]:
            raise ValueError(f"Evidence artifact hash mismatch: {item['path']}")
    results = read(EVIDENCE / "results.json")
    if [row["seed"] for row in results["seeds"]] != [0, 1, 2] or results["demo_seed"] != 0:
        raise ValueError("Published seeds differ from the declared experiment")
    for row in results["seeds"]:
        seed = row["seed"]
        folder = EVIDENCE / f"seed{seed}"
        training = read(folder / "training/manifest.json")
        record = read(folder / "replay/predictions.json")
        selected = row["checkpoint_sha256"]
        if row["completed_epochs"] != 120 or row["optimizer_updates_from_completed_batches"] != 7920:
            raise ValueError("Incomplete fine-tuning budget")
        if (training["status"] != "succeeded" or training["produced_checkpoint"]["sha256"] != selected
                or record["checkpoint_sha256"] != selected):
            raise ValueError("Training and prediction checkpoint identities disagree")
        metrics = replay.metrics_from_predictions([item["label"] for item in record["predictions"]],
                                                  [item["prediction"] for item in record["predictions"]], 6)
        if metrics["support"] != [200, 200, 200, 41, 200, 200]:
            raise ValueError("Unexpected test support")
        for item in record["predictions"]:
            if len(item["logits"]) != 6 or len(item["scores"]) != 6:
                raise ValueError("A retained prediction must contain six logits and six scores")
            if item["logits"][item["prediction"]] != max(item["logits"]):
                raise ValueError("Prediction does not select a maximum logit")
            for expected, actual in zip(replay.probabilities(item["logits"]), item["scores"]):
                close(expected, actual)
        for key in ("accuracy", "weighted_precision", "weighted_recall", "weighted_f1", "macro_f1"):
            close(metrics[key], row["metrics"][key])
        for path in (folder / "eval/metrics.json", folder / "replay/metrics.json"):
            if read(path)["metrics"]["cm"] != metrics["confusion_matrix"]:
                raise ValueError("Strict evaluation confusion matrix differs from predictions")
        if not row["all_saved_weights_finite"] or not row["export_tensors_bitwise_identical"]:
            raise ValueError("Saved-weight verification did not complete")
        if row["real_flow_gradient_check"]["status"] != "passed":
            raise ValueError("Real-flow gradient check is missing")
    for key, summary in results["aggregate"].items():
        values = [row["metrics"][key] for row in results["seeds"]]
        close(summary["mean"], statistics.mean(values))
        close(summary["sample_standard_deviation"], statistics.stdev(values))
    for filename in ("numerical-check.json", "rehearsal-numerical-check.json"):
        runtime = read(EVIDENCE / "runtime" / filename)
        if runtime["status"] != "passed" or len(runtime["checks"]) != 7 or not all(item["passed"] for item in runtime["checks"]):
            raise ValueError("Runtime numerical evidence is incomplete")
    browser = read(EVIDENCE / "browser-check.json")
    if browser["status"] != "passed" or browser["rows"] != 1041:
        raise ValueError("Browser rehearsal did not pass")
    for filename, key in (("index.html", "html_sha256"), ("predictions.json", "predictions_sha256"),
                          ("recorded-demo.webm", "video_sha256")):
        if digest(CUSTOMER / "demo" / filename) != browser[key]:
            raise ValueError("Published demo differs from the rehearsed artifact")
    if read(EVIDENCE / "unlabeled-inference-agreement.json")["status"] != "passed":
        raise ValueError("Unlabeled prediction agreement is missing")
    for name in ("NetMambaPlus-customer-briefing.pdf", "NetMambaPlus-customer-slides.pdf"):
        if not (CUSTOMER / name).read_bytes().startswith(b"%PDF-"):
            raise ValueError("Missing or invalid PDF")
    with zipfile.ZipFile(CUSTOMER / "NetMambaPlus-customer-slides.pptx") as archive:
        slides = [name for name in archive.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)]
        if len(slides) != len(read(CUSTOMER / "presentation-source.json")["slides"]):
            raise ValueError("PowerPoint slide inventory differs from the editable source")
        if any(b"@@" in archive.read(name) for name in slides):
            raise ValueError("PowerPoint contains unresolved result tokens")
    for name in ("briefing.md", "results.md", "talk-track.md"):
        if "@@" in (CUSTOMER / name).read_text():
            raise ValueError(f"Unresolved presentation token: {name}")
    missing_links = []
    for path in [ROOT / "README.md", *sorted((ROOT / "docs").rglob("*.md"))]:
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", path.read_text()):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            local = unquote(target.split("#", 1)[0].split("?", 1)[0].strip("<>"))
            target_path = (path.parent / local).resolve()
            generated_checksums = allow_missing_checksums and target_path == CUSTOMER / "SHA256SUMS"
            if local and not target_path.exists() and not generated_checksums:
                missing_links.append(f"{path.relative_to(ROOT)} -> {target}")
    if missing_links:
        raise ValueError("Broken local links:\n" + "\n".join(missing_links))
    council = ROOT / "docs/research/council-decision.json"
    if digest(council) != "8bd76460d62e804cc06ed8f4de883f8be4f4f4e6de05aa3c9bf3272a9b9ac59e":
        raise ValueError("Canonical council decision was altered")
    guide_sections = verify_teaching_material()
    audit_artifacts = verify_audit(results)
    return {"seed_runs": 3, "test_predictions_per_seed": 1041, "evidence_artifacts": len(inventory["files"]),
            "audit_artifacts": audit_artifacts, "slides": len(slides), "guide_sections": guide_sections,
            "customer_questions": 7, "runtime_checks_per_environment": 7, "local_links": "valid"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-sha256", action="store_true", help="Refresh the package checksums after reviewing final changes")
    args = parser.parse_args()
    result = verify(allow_missing_checksums=args.write_sha256)
    sums = CUSTOMER / "SHA256SUMS"
    paths = sorted(path for base in (CUSTOMER, ROOT / "docs/research") for path in base.rglob("*")
                   if path.is_file() and path != sums)
    if args.write_sha256:
        sums.write_text("".join(f"{digest(path)}  {path.relative_to(ROOT)}\n" for path in paths))
    if sums.exists():
        covered = set()
        for line in sums.read_text().splitlines():
            expected, relative = line.split("  ", 1)
            target = (ROOT / relative).resolve()
            if not target.is_relative_to(ROOT) or digest(target) != expected:
                raise ValueError(f"Package checksum mismatch: {relative}")
            covered.add(target)
        if covered != {path.resolve() for path in paths}:
            raise ValueError("Package checksums do not cover the complete customer/research file inventory")
    else:
        raise ValueError("Package SHA256SUMS is missing")
    print(json.dumps({"status": "passed", **result}, indent=2))


if __name__ == "__main__":
    main()
