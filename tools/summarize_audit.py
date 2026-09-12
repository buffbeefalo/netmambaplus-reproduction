"""Produce a compact council/reviewer evidence pack from retained numeric records."""

import argparse
import datetime
import hashlib
import json
import statistics
import subprocess
from pathlib import Path

from verify_package import ROOT, CUSTOMER, EVIDENCE, read, verify


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Choose a new output file")
    checked = verify()
    tests = subprocess.run(["python3", "-m", "unittest", "discover", "-s", "tests", "-v"],
                           cwd=ROOT, capture_output=True, text=True, check=True)
    audit = CUSTOMER / "audit-evidence"
    results = read(EVIDENCE / "results.json")
    seeds = []
    mapping = read(audit / "export-seed0/metrics.json")["class_mapping"]
    sources = [EVIDENCE / "results.json", CUSTOMER / "document-check.json", audit / "guide/browser-check.json"]
    for row in results["seeds"]:
        seed = row["seed"]
        path = audit / f"export-seed{seed}/metrics.json"
        fresh = read(path)
        if fresh["class_mapping"] != mapping:
            raise ValueError("Fresh class meanings differ between seeds")
        seeds.append({"seed": seed, "epochs": row["completed_epochs"],
                      "updates": row["optimizer_updates_from_completed_batches"],
                      "accuracy": row["metrics"]["accuracy"], "weighted_f1": row["metrics"]["weighted_f1"],
                      "macro_f1": row["metrics"]["macro_f1"],
                      "fresh_export_accuracy": fresh["metrics"]["acc"],
                      "fresh_confusion_matrix_agrees": fresh["metrics"]["cm"] == row["metrics"]["confusion_matrix"],
                      "fresh_class_mapping_agrees": True})
        sources.append(path)
    agreement = read(audit / "unlabeled-agreement.json")
    document = read(CUSTOMER / "document-check.json")
    browser = read(audit / "guide/browser-check.json")
    source = read(CUSTOMER / "presentation-source.json")
    result = {
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "method": "stdlib package verification; actual unittest subprocess; extraction of primary JSON values",
        "scope": "Compact reported execution evidence, not independent GPU certification or a final publication receipt",
        "prior_review": {"run": "2a7c8d6d-c445-47a7-a755-7ef151db3bcc", "state": "ESCALATED",
                         "mutual": False, "unresolved_in_pack": "Primary numbers and checker implementations were excluded from its bounded pack; historical/final publication wording was corrected afterward"},
        "tests": {"exit_code": tests.returncode, "summary": tests.stderr.strip().splitlines()[-3:]},
        "verification": {k: v for k, v in checked.items() if k != "audit_artifacts"},
        "class_mapping": mapping, "test_support": results["seeds"][0]["metrics"]["support"],
        "seeds": seeds,
        "mean_accuracy": statistics.mean(s["accuracy"] for s in seeds),
        "accuracy_sample_sd": statistics.stdev(s["accuracy"] for s in seeds),
        "definitions": "accuracy = correct / rows; weighted F1 uses true class support; macro F1 equally weights six classes",
        "full_unlabeled_recheck": {k: agreement[k] for k in ("status", "rows", "prediction_agreement", "max_absolute_logit_difference")},
        "runtime_rechecks": {name: {"status": read(audit / name)["status"], "checks": len(read(audit / name)["checks"])}
                             for name in ("runtime-main.json", "runtime-rehearsal.json")},
        "pretrain_recheck": read(audit / "pretrain/train_stats.json"),
        "export_probe": {"status": read(audit / "export-probe/metrics.json")["export_status"],
                         "eager_output_shape": read(audit / "export-probe/metrics.json")["eager_output_shape"]},
        "documents": document,
        "guide": {k: browser[k] for k in ("status", "guide_sections", "questions", "checks", "viewport_checks", "html_sha256")},
        "question_map": [{k: q[k] for k in ("id", "slides", "briefing_pages")} for q in source["questions"]],
        "cpu_route": {"platform_executed": "Linux", "commands": ["python3 -m unittest discover -s tests -v", "python3 tools/verify_package.py"],
                      "needs_gpu_or_assets": False, "windows_macos_tested": False},
        "pending_publication": "After corrections, commit/push, pass CI/Pages, create a new release and match anonymous downloads to commit and bytes; attach release-verification.json. Prior release receipts do not certify the new revision.",
        "limits": ["Paper 97.50% not reproduced; measured mean is 86.65%", "Full original pretraining exposure unknown; short PT check only", "Five train/valid and six train/test stored-input overlaps", "Packet CSVs lack established flow identity/order; not classifier inputs", "No live capture/alert policy, independent customer validation or NPU/SmartNIC execution", "Model-only timings exclude packet handling; inherited asset rights unresolved"],
        "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(f"Wrote compact primary evidence to {args.output}")


if __name__ == "__main__":
    main()
