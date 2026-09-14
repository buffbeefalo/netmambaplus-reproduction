"""Verify portable control evidence without raw CSVs or model inference."""

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import packet_data
import packet_study as study
from tools import packet_controls as controls


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _compare(actual, expected, location="result"):
    if isinstance(expected, dict):
        _require(isinstance(actual, dict) and set(actual) == set(expected), f"{location}: object fields differ")
        for key in expected:
            _compare(actual[key], expected[key], location + "." + key)
    elif isinstance(expected, list):
        _require(isinstance(actual, list) and len(actual) == len(expected), f"{location}: list differs")
        for index, (left, right) in enumerate(zip(actual, expected)):
            _compare(left, right, location + f"[{index}]")
    elif type(expected) in (int, float):
        _require(type(actual) in (int, float) and math.isfinite(actual)
                 and math.isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-10), f"{location}: number differs")
    else:
        _require(type(actual) is type(expected) and actual == expected, f"{location}: value differs")


def _positive_count(value, name):
    _require(type(value) is int and value > 0, f"{name}: positive integer required")
    return value


def _counts(values, length, name):
    _require(isinstance(values, list) and len(values) == length
             and all(type(value) is int and value >= 0 for value in values), f"{name}: invalid counts")
    return values


def _convergence(model):
    value = model.get("convergence")
    _require(isinstance(value, dict) and set(value) == {"converged", "n_iter", "warnings"}
             and type(value["converged"]) is bool and isinstance(value["warnings"], list),
             "Invalid control convergence record")
    for warning in value["warnings"]:
        _require(isinstance(warning, dict) and set(warning) == {"category", "message"}
                 and all(isinstance(warning[key], str) and warning[key] for key in warning),
                 "Malformed control convergence warning")
    if model["kind"] == "majority":
        _compare(value, {"converged": True, "n_iter": [], "warnings": []}, "majority convergence")
    else:
        _counts(value["n_iter"], 1, "control optimizer iterations")
        _require(value["n_iter"][0] <= controls.LOGISTIC_SETTINGS["max_iter"], "Control exceeded frozen iteration limit")
        _require(not value["converged"] or not any(warning["category"] == "ConvergenceWarning"
                                                  for warning in value["warnings"]),
                 "Control claims convergence despite a convergence warning")
    return value


def _fit_binding(model, manifest):
    sources = model["training_sources"]
    groups = {source: _positive_count(manifest["sources"][source]["splits"]["train"]["selected_groups"],
                                     "selected training groups") for source in sources}
    _require(model.get("training_groups") == groups
             and all(type(value) is int for value in model["training_groups"].values()),
             "Control fitting groups differ from prepared selected training groups")
    total = sum(groups.values())
    _compare(model.get("source_total_weight"), {source: total / len(sources) for source in sources},
             "control source weight totals")
    mass = model.get("training_class_mass")
    _require(isinstance(mass, list) and len(mass) == 2 and all(
        type(value) in (int, float) and math.isfinite(value) and value >= 0 for value in mass),
        "Control training class mass must be finite and nonnegative")
    _compare(sum(mass), total, "control training target mass")
    if model["kind"] == "majority":
        _compare(model["intercept"], int(mass[1] > mass[0]) - int(mass[1] < mass[0]), "training majority decision")
    else:
        _compare(model["scaler"].get("n_samples_seen"), total, "training scaler group weight")
    return mass


def _record_support(records, source, manifest):
    selected = manifest["sources"][source]["splits"]["test"]
    identities = [record["id"] for record in records]
    _require(identities == sorted(identities), "Control test membership must be in ascending payload order")
    membership = hashlib.sha256(b"".join(bytes.fromhex(identity) for identity in identities)).hexdigest()
    _require(membership == selected["selected_membership_sha256"], "Control selected test membership differs from manifest")
    _require(len(records) == _positive_count(selected["selected_groups"], "selected test groups"),
             "Control selected test group count differs")
    binary = [sum(record["counts"][index] for record in records) for index in (0, 1)]
    expected_binary = _counts(selected["selected_binary_counts"], 2, "selected binary support")
    _require(binary == expected_binary and sum(binary) == _positive_count(selected["selected_rows"], "selected test rows"),
             "Control selected test binary/row totals differ from manifest")
    labels = packet_data.LABELS[source]
    expected_subtypes = selected["selected_label_counts"]
    _require(isinstance(expected_subtypes, dict) and set(expected_subtypes) == set(labels),
             "Selected original-label support has incompatible labels")
    totals = [sum(record["subtypes"][index] for record in records) for index in range(len(labels))]
    _require(totals == _counts([expected_subtypes[label] for label in labels], len(labels), "selected subtype support"),
             "Control selected original-label totals differ from manifest")
    # This proves identical supplied truths across controls, not original CSV
    # truth. Raw rows and feature values are intentionally absent from evidence.
    digest = hashlib.sha256()
    for record in records:
        digest.update(json.dumps([record["id"], record["counts"], record["subtypes"]],
                                 separators=(",", ":")).encode())
    return digest.hexdigest()


def verify(parent_evidence, independent=False):
    """Check all frozen controls, inventories and saved prediction arithmetic."""
    try:
        return _verify(Path(parent_evidence), independent)
    except (KeyError, TypeError, IndexError) as error:
        raise ValueError(f"Malformed control evidence: {error}") from error


def _verify(parent, independent):
    root = parent / "controls"
    protocol_path, manifest_path = parent / "protocol.json", parent / "manifest.json"
    protocol, manifest = study.read_json(protocol_path), study.read_json(manifest_path)
    frozen_path = root / "frozen-controls.json"
    frozen, report = study.read_json(frozen_path), study.read_json(root / "evaluation/results.json")
    _require(frozen.get("schema_version") == 1 and frozen.get("kind") == "netmambaplus_packet_controls_v1"
             and frozen.get("status") == "frozen" and frozen.get("fit_only") is True,
             "Expected completed training-only control freeze")
    _require(report.get("schema_version") == 1 and report.get("status") == "completed", "Control evaluation is incomplete")
    _require(manifest.get("labels") == packet_data.LABELS, "Prepared original-label mapping differs")
    _compare(frozen.get("feature_contract"), controls.FEATURE_CONTRACT, "frozen control features")
    _compare(report.get("feature_contract"), controls.FEATURE_CONTRACT, "evaluated control features")
    for key in ("C", "solver", "max_iter", "tol"):
        _compare(protocol["controls"][key], controls.LOGISTIC_SETTINGS[key], "protocol control " + key)
    binding = {"protocol_sha256": study.sha256(protocol_path), "data_manifest_sha256": study.sha256(manifest_path),
               "source_sha256": {source: manifest["sources"][source]["sha256"] for source in controls.SOURCES},
               "code_sha256": frozen["code_sha256"]}
    _compare(protocol["data_manifest_sha256"], binding["data_manifest_sha256"], "protocol data manifest")
    _compare(protocol["source_sha256"], binding["source_sha256"], "protocol source files")
    _require(set(binding["code_sha256"]) == set(controls.CODE_FILES), "Incomplete control implementation binding")
    for name, digest in binding["code_sha256"].items():
        _require(isinstance(digest, str) and re.fullmatch("[0-9a-f]{64}", digest), "Invalid control implementation digest")
        if name == "tools/packet_controls.py":
            _compare(digest, study.sha256(controls.__file__), "control implementation")
        else:
            _compare(digest, protocol["code_sha256"][name], "shared implementation " + name)
    for key, value in binding.items():
        _compare(frozen[key], value, "frozen " + key)
        _compare(report[key], value, "reported " + key)
    _compare(report["frozen_controls"], study.artifact(root, frozen_path), "frozen control artifact")
    _compare(frozen["training_groups"], {source: manifest["sources"][source]["splits"]["train"]["selected_groups"]
                                         for source in controls.SOURCES}, "frozen training groups")
    expected_names = {f"{arm}_{kind}" for arm in controls.ARMS for kind in controls.KINDS}
    _require(isinstance(frozen.get("models"), dict) and set(frozen["models"]) == expected_names,
             "Freeze must contain exactly nine control models")
    _require(isinstance(report.get("results"), list) and len(report["results"]) == 9
             and {result["name"] for result in report["results"]} == expected_names,
             "Evaluation must contain exactly nine distinct control models")
    models, convergence, arm_mass = {}, {}, {}
    for name in sorted(expected_names):
        descriptor = frozen["models"][name]
        _require(descriptor.get("path") == f"models/{name}.json", "Control model artifact path changed")
        model = study.read_json(study.verify_artifact(root, descriptor))
        controls._validate_model(model, name, binding)
        _require(all(type(value) is int for value in model["classes"]), "Control class indices must be integers")
        mass = _fit_binding(model, manifest)
        arm = tuple(model["training_sources"])
        if arm in arm_mass:
            _compare(mass, arm_mass[arm], "control methods must use the same training target mass")
        arm_mass[arm] = mass
        models[name], convergence[name] = model, _convergence(model)
    _compare(frozen["convergence"], convergence, "frozen convergence outcomes")
    truths, prediction_paths = {}, set()
    for result in report["results"]:
        name, tests = result["name"], result["tests"]
        model = models[name]
        _compare(result["model"], frozen["models"][name], "evaluated frozen model")
        _compare(result["kind"], model["kind"], "evaluated control kind")
        _compare(result["training_sources"], model["training_sources"], "evaluated fitting sources")
        _compare(result["convergence"], convergence[name], "reported convergence outcomes")
        _require(isinstance(tests, dict) and set(tests) == set(controls.SOURCES), "Each control requires both source test sets")
        for source, evidence in tests.items():
            descriptor = evidence["predictions"]
            expected_path = f"evaluation/{name}-test-{source}.jsonl.gz"
            _require(descriptor.get("path") == expected_path, "Control prediction artifact path changed")
            prediction_paths.add(expected_path)
            records = list(study.prediction_records(study.verify_artifact(root, descriptor)))
            measured = study.evaluate_records(records, original_labels=packet_data.LABELS[source],
                                               normal_label=packet_data.LABELS[source][0])
            truth = _record_support(records, source, manifest)
            if source in truths:
                _require(truth == truths[source], "Controls disagree about supplied group truths")
            truths[source] = truth
            if model["kind"] == "majority":
                for record in records:
                    _compare(record["logits"], [0., model["intercept"]], "saved majority prediction")
            _compare(evidence["metrics"], measured, f"{name}/{source} metrics")
            if independent:
                # Import at call time so the parent reviewer can import verify
                # without a circular module dependency or mandatory sklearn.
                from tools.review_packet_study import independent_metrics
                independent_metrics(records, measured)
    _require(len(prediction_paths) == 18, "Expected exactly eighteen distinct control test sets")
    _require({path.name for path in (root / "models").glob("*.json")} == {f"{name}.json" for name in expected_names},
             "Unexpected control model files in published inventory")
    _require({path.relative_to(root).as_posix() for path in (root / "evaluation").glob("*.jsonl.gz")} == prediction_paths,
             "Unexpected control prediction files in published inventory")
    warning_count = sum(len(value["warnings"]) for value in convergence.values())
    all_converged = all(value["converged"] for value in convergence.values())
    return {"status": "verified" if all_converged and not warning_count else "verified_with_convergence_warnings",
            "models": len(models), "test_sets": len(prediction_paths), "independent": bool(independent),
            "frozen_controls_sha256": study.sha256(frozen_path),
            "convergence": {"all_converged": all_converged, "warning_count": warning_count, "models": convergence},
            "scope": "Artifact bindings, selected-group membership and supplied-label arithmetic verified. Without raw CSVs/features, this does not prove original capture independence, original label truth, fitting history, or linear-model predictions from saved weights."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--independent", action="store_true")
    args = parser.parse_args(argv)
    print(json.dumps(verify(args.evidence, args.independent), indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
