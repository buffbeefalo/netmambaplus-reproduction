"""Train-only packet controls, frozen separately before any test inference.

Metadata controls average ttl, total_len and t_delta within each payload group
and count protocol fractions. This sacrifices row-specific metadata variation
to retain the native study's group unit. t_delta units remain unverified.
Metadata is used only by this explicit control, never by the native model.
"""

import argparse
import csv
from decimal import Decimal, InvalidOperation
import gzip
import json
import math
import os
from pathlib import Path
import re
import sys
import warnings

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import packet_study as study

SOURCES = ("cic", "unsw")
ARMS = {"cic": ["cic"], "unsw": ["unsw"], "joint": ["cic", "unsw"]}
KINDS = ("majority", "byte_histogram_linear", "metadata_linear")
METADATA_FEATURES = ["mean_ttl", "mean_total_len", "mean_t_delta",
                     "fraction_protocol_1", "fraction_protocol_6", "fraction_protocol_17",
                     "fraction_protocol_other"]
LOGISTIC_SETTINGS = {"C": 1.0, "solver": "lbfgs", "max_iter": 1000, "tol": 1e-4,
                     "penalty": "l2", "fit_intercept": True}
CODE_FILES = ("packet_data.py", "packet_study.py", "tools/train_packet_model.py", "tools/packet_controls.py")
KNOWN_PROTOCOL_NAMES = frozenset((
    "arp", "ax.25", "crtp", "crudp", "dgp", "egp", "emcon", "etherip", "fc", "fire",
    "ggp", "gmtp", "gre", "hmp", "ib", "icmp", "ipip", "iplt", "ipv6", "leaf-2",
    "micp", "mobile", "nvp", "ospf", "others", "pim", "pipe", "rdp", "rsvp", "sccopmce",
    "sctp", "secure-vmtp", "sep", "snp", "sps", "sun-nd", "swipe", "tcp", "udp", "unas", "vmtp",
))
FEATURE_CONTRACT = {
    "unit": "selected unique stored-payload group within source and split",
    "byte_histogram_linear": "256 byte-count fractions across all 1500 stored bytes, retaining zeros",
    "metadata_linear": METADATA_FEATURES,
    "metadata_aggregation": "Arithmetic means and protocol fractions over original rows in each payload group; row-specific variation is sacrificed to retain the same group unit.",
    "t_delta_units": "unverified",
    "excluded_inputs": ["label", "binary_label", "source identity", "payload identity", "row identity"],
    "fitting": "Selected split 0 groups only; no validation/test fitting or model selection",
    "weighting": "Group-uniform soft targets counts/sum(counts); each joint source has weight n_total/(2*n_source) per group, including the training scaler.",
    "majority": "Constant class chosen by weighted training group-target mass; ties choose benign",
    "protocol_interpretation": {
        "named_bins": {name: {"icmp": 1, "tcp": 6, "udp": 17}.get(name, "other")
                       for name in sorted(KNOWN_PROTOCOL_NAMES)},
        "numeric_tokens": "Finite exact integers in [0,255]; names outside the observed allowlist are rejected",
        "parser_correction": "The initial integral-only parser stopped before fitting because the exports use named protocols. A full metadata vocabulary audit established these 41 names; fixed 1/6/17/other features and fitting settings did not change.",
    },
}


def _metadata_values(ttl, total_len, protocol, t_delta):
    try:
        values = [float(ttl), float(total_len), float(t_delta)]
    except (ValueError, TypeError, InvalidOperation, OverflowError) as error:
        raise ValueError("Metadata must be numeric and finite") from error
    if not all(math.isfinite(value) for value in values):
        raise ValueError("Metadata must be numeric and finite")
    if isinstance(protocol, str) and protocol in KNOWN_PROTOCOL_NAMES:
        categories = [float(protocol == value) for value in ("icmp", "tcp", "udp")]
    else:
        try:
            number = Decimal(protocol)
        except (ValueError, TypeError, InvalidOperation) as error:
            raise ValueError("Metadata protocol must be an allowed name or integer") from error
        if not number.is_finite() or number != number.to_integral_value() or not 0 <= number <= 255:
            raise ValueError("Metadata protocol must be a finite integer in [0,255]")
        categories = [float(number == value) for value in (1, 6, 17)]
    return values + categories + [float(not any(categories))]


def _load_data(directory):
    import numpy as np
    import packet_data
    from tools import train_packet_model
    data, manifest = train_packet_model.load_data(directory)
    if manifest.get("labels") != packet_data.LABELS:
        raise ValueError("Prepared label mapping changed")
    names = {"payload.npy", "hashes.npy", "counts.npy", "subtypes.npy", "split.npy", "selected.npy", "metadata.csv"}
    for source in SOURCES:
        arrays = data[source]
        references = manifest["sources"][source]["files"]
        if set(references) != names or any(reference["path"] != f"{source}/{name}"
                                           for name, reference in references.items()):
            raise ValueError("Prepared source file contract changed")
        groups = len(arrays["hashes"])
        if (arrays["hashes"].shape != (groups,) or arrays["hashes"].dtype != np.dtype("V32")
                or len(np.unique(arrays["hashes"])) != groups
                or arrays["split"].shape != (groups,) or arrays["split"].dtype != np.uint8
                or arrays["selected"].shape != (groups,) or arrays["selected"].dtype != np.bool_
                or np.any(arrays["split"] > 2)):
            raise ValueError("Prepared group identity/split contract changed")
        counts, subtypes = arrays["counts"], arrays["subtypes"]
        if (counts.dtype != np.int64 or subtypes.dtype != np.int64
                or np.any(counts < 0) or np.any(subtypes < 0)
                or not np.array_equal(counts[:, 0], subtypes[:, 0])
                or not np.array_equal(counts[:, 1], subtypes[:, 1:].sum(axis=1))):
            raise ValueError("Prepared binary and original-label counts do not reconcile")
    return data, manifest


def _histograms(payload, indices):
    import numpy as np
    if payload.ndim != 2 or payload.shape[1] != 1500 or payload.dtype != np.uint8:
        raise ValueError("Histogram control requires uint8 payloads with 1500 bytes")
    features = np.empty((len(indices), 256), dtype=np.float64)
    for position, index in enumerate(indices):
        features[position] = np.bincount(payload[index], minlength=256) / 1500.0
    return features


def _metadata_features(directory, source, arrays, indices):
    """Validate every metadata row; aggregate features only for requested groups."""
    import numpy as np
    import packet_data
    groups = {value.tobytes().hex(): index for index, value in enumerate(arrays["hashes"])}
    selected = {int(index): position for position, index in enumerate(indices)}
    features = np.zeros((len(indices), len(METADATA_FEATURES)), dtype=np.float64)
    seen = np.zeros_like(arrays["subtypes"], dtype=np.int64)
    labels = {label: index for index, label in enumerate(packet_data.LABELS[source])}
    path = Path(directory) / source / "metadata.csv"
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.reader(stream, strict=True)
        expected = ["source", "row_id", "payload_sha256", *packet_data.METADATA_COLUMNS, "binary_label"]
        if next(reader, None) != expected:
            raise ValueError("Metadata header does not match prepared row schema")
        for row_id, row in enumerate(reader):
            if len(row) != 9 or row[0] != source or row[1] != str(row_id):
                raise ValueError("Metadata source or row identity does not reconcile")
            if row[2] not in groups or row[7] not in labels:
                raise ValueError("Metadata payload or label is absent from prepared groups")
            label_index = labels[row[7]]
            if row[8] != str(int(label_index != 0)):
                raise ValueError("Metadata binary label conflicts with the original label")
            values = _metadata_values(row[3], row[4], row[5], row[6])
            index = groups[row[2]]
            seen[index, label_index] += 1
            position = selected.get(index)
            if position is not None:
                features[position] += values
    if not np.array_equal(seen, arrays["subtypes"]):
        raise ValueError("Metadata row/label counts do not reconcile with prepared groups")
    features /= arrays["counts"][indices].sum(axis=1, keepdims=True)
    if not np.isfinite(features).all():
        raise ValueError("Aggregated metadata features are nonfinite")
    return features


def _source_weights(lengths):
    import numpy as np
    if not lengths or any(type(length) is not int or length <= 0 for length in lengths):
        raise ValueError("Each fitting source requires nonempty training groups")
    total = sum(lengths)
    return np.concatenate([np.full(length, total / (len(lengths) * length), dtype=np.float64)
                           for length in lengths])


def _soft_training_rows(features, counts, weights):
    import numpy as np
    if (features.ndim != 2 or counts.shape != (len(features), 2)
            or weights.shape != (len(features),) or not np.issubdtype(counts.dtype, np.integer)
            or np.any(counts < 0) or np.any(counts.sum(axis=1) <= 0)
            or not np.isfinite(features).all() or not np.isfinite(weights).all() or np.any(weights <= 0)):
        raise ValueError("Invalid finite features, group counts or source weights")
    fractions = counts / counts.sum(axis=1, keepdims=True)
    return (np.repeat(features, 2, axis=0), np.tile([0, 1], len(features)),
            (fractions * weights[:, None]).reshape(-1))


def _binding(directory, manifest, protocol_sha256):
    return {"protocol_sha256": protocol_sha256,
            "data_manifest_sha256": study.sha256(Path(directory) / "manifest.json"),
            "source_sha256": {source: manifest["sources"][source]["sha256"] for source in SOURCES},
            "code_sha256": {name: study.sha256(ROOT / name) for name in CODE_FILES}}


def _check_binding(directory, manifest, expected):
    actual = _binding(directory, manifest, expected["protocol_sha256"])
    if actual != expected:
        raise ValueError("Frozen controls data or implementation fingerprint changed")
    for source in SOURCES:
        for reference in manifest["sources"][source]["files"].values():
            study.verify_artifact(directory, reference)


def _fit_one(name, kind, sources, features, counts, weights, lengths, binding):
    import numpy as np
    import sklearn
    from sklearn.exceptions import ConvergenceWarning
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from threadpoolctl import threadpool_limits
    fractions = counts / counts.sum(axis=1, keepdims=True)
    mass = (fractions * weights[:, None]).sum(axis=0)
    model = {"schema_version": 1, "name": name, "kind": kind, "training_sources": sources,
             "classes": [0, 1], "binding": binding,
             "training_groups": dict(zip(sources, lengths)),
             "source_total_weight": {source: float(weights[sum(lengths[:i]):sum(lengths[:i + 1])].sum())
                                     for i, source in enumerate(sources)},
             "training_class_mass": mass.tolist(), "scaler": None, "coef": [],
             "intercept": float(int(mass[1] > mass[0]) - int(mass[1] < mass[0])),
             "settings": {}, "feature_names": [],
             "convergence": {"converged": True, "n_iter": [], "warnings": []},
             "runtime": {"numpy": np.__version__, "scikit_learn": sklearn.__version__, "cpu_threads": 4}}
    if kind == "majority":
        model["score_convention"] = "logits=[0, signed_training_majority_margin]; ties use 0"
        return model
    if not np.isfinite(features).all():
        raise ValueError("Control fitting features must be finite")
    model["feature_names"] = ([f"byte_fraction_{value}" for value in range(256)]
                              if kind == "byte_histogram_linear" else list(METADATA_FEATURES))
    with threadpool_limits(limits=4):
        scaler = StandardScaler().fit(features, sample_weight=weights)
        transformed = scaler.transform(features)
        x, y, sample_weights = _soft_training_rows(transformed, counts, weights)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            classifier = LogisticRegression(**LOGISTIC_SETTINGS).fit(x, y, sample_weight=sample_weights)
    if classifier.classes_.tolist() != [0, 1]:
        raise ValueError("Control classifier did not retain both binary classes")
    model.update({"settings": dict(LOGISTIC_SETTINGS),
                  "scaler": {"mean": scaler.mean_.tolist(), "var": scaler.var_.tolist(),
                             "scale": scaler.scale_.tolist(), "n_samples_seen": float(scaler.n_samples_seen_)},
                  "coef": classifier.coef_[0].tolist(), "intercept": float(classifier.intercept_[0]),
                  "convergence": {"converged": not any(issubclass(item.category, ConvergenceWarning) for item in caught),
                                  "n_iter": classifier.n_iter_.tolist(),
                                  "warnings": [{"category": item.category.__name__, "message": str(item.message)}
                                               for item in caught]},
                  "score_convention": "logits=[0, standardized_linear_decision_function]"})
    _validate_model(model, name, binding)
    return model


def _validate_model(model, name, binding):
    if (not isinstance(model, dict) or model.get("schema_version") != 1 or model.get("name") != name
            or model.get("binding") != binding or model.get("classes") != [0, 1]):
        raise ValueError("Invalid frozen control model identity or binding")
    matching = [(arm, kind) for arm in ARMS for kind in KINDS if name == f"{arm}_{kind}"]
    if len(matching) != 1:
        raise ValueError("Unknown control model")
    arm, kind = matching[0]
    if model.get("kind") != kind or model.get("training_sources") != ARMS[arm]:
        raise ValueError("Control kind or fitting sources changed")
    intercept = model.get("intercept")
    if type(intercept) not in (float, int) or not math.isfinite(intercept):
        raise ValueError("Control intercept must be finite")
    expected_names = ([] if kind == "majority" else METADATA_FEATURES if kind == "metadata_linear"
                      else [f"byte_fraction_{value}" for value in range(256)])
    if model.get("feature_names") != expected_names:
        raise ValueError("Control features changed")
    if kind == "majority":
        if model.get("coef") != [] or model.get("scaler") is not None:
            raise ValueError("Majority control must not consume features")
        return
    if model.get("settings") != LOGISTIC_SETTINGS or not isinstance(model.get("scaler"), dict):
        raise ValueError("Control logistic/scaler settings changed")
    for values in (model.get("coef"), *(model["scaler"].get(key) for key in ("mean", "var", "scale"))):
        if (not isinstance(values, list) or len(values) != len(expected_names)
                or any(type(value) not in (int, float) or not math.isfinite(value) for value in values)):
            raise ValueError("Control coefficients/scaler must have finite compatible dimensions")
    if any(value <= 0 for value in model["scaler"]["scale"]) or any(value < 0 for value in model["scaler"]["var"]):
        raise ValueError("Control scaler has invalid scale or variance")


def fit_controls(data_directory, output, protocol_sha256):
    """Fit all nine controls and freeze their portable JSON before any inference."""
    output, directory = Path(output), Path(data_directory)
    if os.path.lexists(output):
        raise FileExistsError("Choose a fresh controls output directory")
    if type(protocol_sha256) is not str or not re.fullmatch("[0-9a-f]{64}", protocol_sha256):
        raise ValueError("Controls require the frozen protocol SHA-256")
    import numpy as np
    data, manifest = _load_data(directory)
    binding = _binding(directory, manifest, protocol_sha256)
    training = {}
    for source in SOURCES:
        arrays, indices = data[source], data[source][0]
        training[source] = {"counts": np.asarray(arrays["counts"][indices]),
                            "byte_histogram_linear": _histograms(arrays["payload"], indices),
                            "metadata_linear": _metadata_features(directory, source, arrays, indices)}
    output.mkdir(parents=True)
    (output / "models").mkdir()
    models, convergence = {}, {}
    for arm, sources in ARMS.items():
        lengths = [len(training[source]["counts"]) for source in sources]
        counts = np.concatenate([training[source]["counts"] for source in sources])
        weights = _source_weights(lengths)
        for kind in KINDS:
            name = f"{arm}_{kind}"
            features = (None if kind == "majority" else
                        np.concatenate([training[source][kind] for source in sources]))
            model = _fit_one(name, kind, sources, features, counts, weights, lengths, binding)
            path = output / "models" / f"{name}.json"
            study.write_json(path, model)
            models[name] = study.artifact(output, path)
            convergence[name] = model["convergence"]
    _check_binding(directory, manifest, binding)
    frozen = {"schema_version": 1, "kind": "netmambaplus_packet_controls_v1", "status": "frozen",
              "fit_only": True, **binding, "models": models, "convergence": convergence,
              "training_groups": {source: len(data[source][0]) for source in SOURCES},
              "feature_contract": FEATURE_CONTRACT,
              "scope": "All nine training-only controls are fixed before any control validation/test inference."}
    study.write_json(output / "frozen-controls.json", frozen)
    return frozen


def _scores(model, features, count):
    import numpy as np
    if model["kind"] == "majority":
        return np.full(count, model["intercept"], dtype=np.float64)
    scaler = model["scaler"]
    values = ((features - np.asarray(scaler["mean"])) / np.asarray(scaler["scale"])) @ np.asarray(model["coef"])
    values += model["intercept"]
    if values.shape != (count,) or not np.isfinite(values).all():
        raise ValueError("Portable control inference produced nonfinite or incomplete scores")
    return values


def evaluate_controls(data_directory, output):
    """Verify the complete freeze, then evaluate every control on both source tests."""
    import packet_data
    output, directory = Path(output), Path(data_directory)
    destination = output / "evaluation"
    if os.path.lexists(destination):
        raise FileExistsError("Control evaluation output already exists")
    frozen_path = output / "frozen-controls.json"
    frozen = study.read_json(frozen_path)
    if (frozen.get("schema_version") != 1 or frozen.get("kind") != "netmambaplus_packet_controls_v1"
            or frozen.get("status") != "frozen" or frozen.get("fit_only") is not True
            or frozen.get("feature_contract") != FEATURE_CONTRACT):
        raise ValueError("All controls must be frozen before evaluation")
    names = {f"{arm}_{kind}" for arm in ARMS for kind in KINDS}
    if not isinstance(frozen.get("models"), dict) or set(frozen["models"]) != names:
        raise ValueError("Freeze must include all nine controls")
    binding = {key: frozen[key] for key in ("protocol_sha256", "data_manifest_sha256", "source_sha256", "code_sha256")}
    models = {}
    for name, descriptor in frozen["models"].items():
        model = study.read_json(study.verify_artifact(output, descriptor))
        _validate_model(model, name, binding)
        models[name] = model
    data, manifest = _load_data(directory)
    _check_binding(directory, manifest, binding)
    frozen_reference = study.artifact(output, frozen_path)
    features = {}
    for source in SOURCES:
        arrays, indices = data[source], data[source][2]
        features[source] = {"byte_histogram_linear": _histograms(arrays["payload"], indices),
                            "metadata_linear": _metadata_features(directory, source, arrays, indices)}
    destination.mkdir()
    results = []
    for name in sorted(models):
        model, tests = models[name], {}
        for source in SOURCES:
            arrays, indices = data[source], data[source][2]
            scores = _scores(model, features[source].get(model["kind"]), len(indices))
            path = destination / f"{name}-test-{source}.jsonl.gz"
            with path.open("xb") as raw, gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as zipped:
                for index, score in zip(indices, scores):
                    record = {"id": arrays["hashes"][index].tobytes().hex(),
                              "counts": arrays["counts"][index].tolist(),
                              "subtypes": arrays["subtypes"][index].tolist(), "logits": [0.0, float(score)]}
                    zipped.write((json.dumps(record, separators=(",", ":"), allow_nan=False) + "\n").encode())
            measured = study.evaluate_records(study.prediction_records(path),
                original_labels=packet_data.LABELS[source], normal_label=packet_data.LABELS[source][0])
            tests[source] = {"metrics": measured, "predictions": study.artifact(output, path),
                             "exposure": "source used for fitting" if source in model["training_sources"]
                             else "no supervised fitting on this source"}
        results.append({"name": name, "kind": model["kind"], "training_sources": model["training_sources"],
                        "model": frozen["models"][name], "convergence": model["convergence"], "tests": tests})
    study.verify_artifact(output, frozen_reference)
    _check_binding(directory, manifest, binding)
    for descriptor in frozen["models"].values():
        study.verify_artifact(output, descriptor)
    report = {"schema_version": 1, "status": "completed", **binding,
              "frozen_controls": frozen_reference, "results": results, "feature_contract": FEATURE_CONTRACT}
    study.write_json(destination / "results.json", report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("fit", "evaluate"))
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--protocol-sha256")
    args = parser.parse_args(argv)
    result = (fit_controls(args.data, args.output, args.protocol_sha256) if args.mode == "fit"
              else evaluate_controls(args.data, args.output))
    print(json.dumps({"status": result["status"], "output": str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
