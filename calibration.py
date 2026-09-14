"""Standard-library temperature scaling and checkpoint-bound artifact validation.

Temperature fitting minimizes validation NLL in the fixed [0.05, 20] range.
The optional confidence threshold is an illustrative policy, not a safety claim.
"""

import copy
import math
import re

TEMPERATURE_BOUNDS = (0.05, 20.0)
DEFAULT_THRESHOLD = 0.9
ECE_BINS = 15
FIT_ITERATIONS = 80
INFERENCE_RUNTIME = {"device_type": "cuda", "autocast_enabled": True,
                     "autocast_dtype": "float16", "model_mode": "eval",
                     "gradient_mode": "inference_mode"}
INFERENCE_ARGUMENTS = ("model", "dataset_type", "num_packet", "num_packet_byte",
                       "seq_len", "stride_size", "size_key", "nb_classes", "device")


def _number(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number")
    try:
        result = float(value)
    except (OverflowError, ValueError) as error:
        raise ValueError(f"{name} must be a finite number") from error
    if not math.isfinite(result):
        raise ValueError(f"{name} must be a finite number")
    return result


def _temperature(value):
    result = _number(value, "temperature")
    if result <= 0:
        raise ValueError("temperature must be positive")
    return result


def validate_threshold(value):
    """Return a finite threshold in [0, 1]; booleans and strings are rejected."""
    value = _number(value, "threshold")
    if not 0 <= value <= 1:
        raise ValueError("threshold must be in [0, 1]")
    return value


def _row(logits):
    if not isinstance(logits, (list, tuple)) or not logits:
        raise ValueError("logits must be a nonempty sequence")
    return [_number(value, "logit") for value in logits]


def _shifted(row, temperature):
    maximum = max(row)
    values = [(value - maximum) / temperature for value in row]
    if any(not math.isfinite(value) for value in values):
        raise ValueError("Scaled logit differences exceed finite arithmetic")
    return values


def calibrated_scores(logits, temperature):
    """Return softmax(logits / temperature) for one row without changing its input."""
    values = [math.exp(value) for value in _shifted(_row(logits), _temperature(temperature))]
    total = sum(values)
    return [value / total for value in values]


def _samples(logits, labels):
    if not isinstance(logits, (list, tuple)) or not logits:
        raise ValueError("logits must be a nonempty matrix")
    rows = [_row(row) for row in logits]
    classes = len(rows[0])
    if classes < 2 or any(len(row) != classes for row in rows):
        raise ValueError("logits must have a consistent width of at least two classes")
    if not isinstance(labels, (list, tuple)) or len(labels) != len(rows):
        raise ValueError("One label is required for every logit row")
    if any(type(label) is not int or not 0 <= label < classes for label in labels):
        raise ValueError("Labels must be integer class indices in range")
    return rows, list(labels)


def _nll(rows, labels, temperature):
    losses = []
    for row, label in zip(rows, labels):
        shifted = _shifted(row, temperature)
        losses.append(math.log(sum(math.exp(value) for value in shifted)) - shifted[label])
    result = math.fsum(loss / len(rows) for loss in losses)
    if not math.isfinite(result):
        raise ValueError("NLL exceeds finite arithmetic")
    return result


def fit_temperature(logits, labels):
    """Fit one temperature by deterministic bisection of convex NLL in inverse T.

    The derivative is mean(E_p[logit] - true_class_logit). Its derivative is
    a nonnegative variance, so bisection finds a global minimum or a bound.
    No temperature or threshold is selected using accuracy, ECE, or test data.
    """
    rows, labels = _samples(logits, labels)
    centered = [_shifted(row, 1.0) for row in rows]
    if all(all(value == 0 for value in row) for row in centered):
        return 1.0

    def derivative(inverse_temperature):
        terms = []
        for row, label in zip(centered, labels):
            scores = calibrated_scores(row, 1.0 / inverse_temperature)
            terms.append((math.fsum(p * value for p, value in zip(scores, row)) - row[label]) / len(rows))
        return math.fsum(terms)

    low, high = 1.0 / TEMPERATURE_BOUNDS[1], 1.0 / TEMPERATURE_BOUNDS[0]
    if derivative(low) >= 0:
        return TEMPERATURE_BOUNDS[1]
    if derivative(high) <= 0:
        return TEMPERATURE_BOUNDS[0]
    for _ in range(FIT_ITERATIONS):
        middle = (low + high) / 2.0
        if derivative(middle) > 0:
            high = middle
        else:
            low = middle
    fitted = 1.0 / ((low + high) / 2.0)
    # Floating-point ties should leave the unscaled model unchanged.
    return min((1.0, fitted), key=lambda t: _nll(rows, labels, t))


def classification_metrics(logits, labels, temperature=1.0, threshold=None, *, predictions=None):
    """Return NLL, mean sum-of-class Brier, 15-bin ECE and optional policy counts.

    ECE bins are [i/15, (i+1)/15), with confidence 1 included in the last bin.
    Accuracy and errors are fractions. The first maximum breaks exact ties unless
    the caller supplies native prediction indices, which must also be maxima.
    An accepted-set error rate is null when no rows are accepted.
    """
    rows, labels = _samples(logits, labels)
    temperature = _temperature(temperature)
    if predictions is None:
        predictions = [max(range(len(row)), key=row.__getitem__) for row in rows]
    elif (not isinstance(predictions, (list, tuple)) or len(predictions) != len(rows)
          or any(type(index) is not int or not 0 <= index < len(row)
                 or row[index] != max(row) for row, index in zip(rows, predictions))):
        raise ValueError("Predictions must supply one maximizing class index per row")
    if threshold is not None:
        threshold = validate_threshold(threshold)
    bins = [[] for _ in range(ECE_BINS)]
    correct, accepted, accepted_errors = 0, 0, 0
    brier = []
    for row, label, prediction in zip(rows, labels, predictions):
        scores = calibrated_scores(row, temperature)
        hit = prediction == label
        confidence = scores[prediction]
        correct += hit
        bins[min(int(confidence * ECE_BINS), ECE_BINS - 1)].append((confidence, hit))
        brier.append(math.fsum((p - (index == label)) ** 2 for index, p in enumerate(scores)))
        if threshold is not None and confidence >= threshold:
            accepted += 1
            accepted_errors += not hit
    count = len(rows)
    ece = math.fsum(abs(math.fsum(p for p, _ in group) - sum(hit for _, hit in group)) / count
                    for group in bins if group)
    return {"rows": count, "classes": len(rows[0]), "temperature": temperature,
            "accuracy": correct / count, "correct": correct, "nll": _nll(rows, labels, temperature),
            "brier": math.fsum(brier) / count, "ece": ece, "ece_bins": ECE_BINS,
            "threshold": threshold, "accepted": accepted if threshold is not None else None,
            "deferred": count - accepted if threshold is not None else None,
            "accepted_errors": accepted_errors if threshold is not None else None,
            "accepted_error_rate": accepted_errors / accepted if accepted and threshold is not None else None,
            "coverage": accepted / count if threshold is not None else None}


def _json_value(value):
    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, float) and math.isfinite(value):
        return
    if isinstance(value, list):
        for child in value:
            _json_value(child)
        return
    if isinstance(value, dict) and all(isinstance(key, str) for key in value):
        for child in value.values():
            _json_value(child)
        return
    raise ValueError("Calibration records require finite JSON values and string object keys")


def _digest(value, name, length=64):
    if not isinstance(value, str) or not re.fullmatch(f"[0-9a-f]{{{length}}}", value):
        raise ValueError(f"Invalid {name} digest")
    return value


def _binding_valid(binding):
    try:
        _json_value(binding)
        _digest(binding["configuration_sha256"], "configuration")
        _digest(binding["checkpoint_sha256"], "checkpoint")
        mapping = binding["class_mapping"]
        if (not isinstance(mapping, dict) or len(mapping) < 2
                or any(not name or type(index) is not int for name, index in mapping.items())
                or sorted(mapping.values()) != list(range(len(mapping)))):
            raise ValueError("Invalid calibration class mapping")
        upstream = binding["upstream"]
        _digest(upstream["commit"], "upstream commit", 40)
        if not isinstance(upstream["core_sha256"], dict) or not upstream["core_sha256"]:
            raise ValueError("Missing upstream source hashes")
        for path, digest in upstream["core_sha256"].items():
            if not path or path.startswith("/") or "\\" in path or ".." in path.split("/"):
                raise ValueError("Invalid repository-relative upstream path")
            _digest(digest, "upstream source")
        arguments = binding["inference_args"]
        if set(arguments) != set(INFERENCE_ARGUMENTS):
            raise ValueError("Missing inference configuration")
        for key in ("model", "dataset_type", "size_key", "device"):
            if not isinstance(arguments[key], str) or not arguments[key]:
                raise ValueError(f"Invalid inference argument {key}")
        for key in ("num_packet", "num_packet_byte", "seq_len", "stride_size", "nb_classes"):
            if type(arguments[key]) is not int or arguments[key] <= 0:
                raise ValueError(f"Invalid inference argument {key}")
        if arguments["nb_classes"] != len(mapping):
            raise ValueError("Inference class count differs from class mapping")
        precision = binding["inference_runtime"]
        if not isinstance(precision, dict) or type(precision["autocast_enabled"]) is not bool:
            raise ValueError("Missing inference precision identity")
        for key in ("device_type", "autocast_dtype", "model_mode", "gradient_mode"):
            if not isinstance(precision[key], str) or not precision[key]:
                raise ValueError("Invalid inference precision identity")
        packages = binding["runtime_packages"]
        if not isinstance(packages, dict) or not packages or "torch" not in packages:
            raise ValueError("Missing runtime package identity")
        if any(not name or (version is not None and (not isinstance(version, str) or not version))
               for name, version in packages.items()):
            raise ValueError("Invalid runtime package identity")
        if not isinstance(binding["python_version"], str) or not binding["python_version"]:
            raise ValueError("Missing Python runtime identity")
    except (KeyError, TypeError, AttributeError) as error:
        raise ValueError("Incomplete calibration compatibility binding") from error


def make_binding(manifest):
    """Select stable model/runtime compatibility identities, excluding run locations.

    Configuration bytes already bind batch settings. Worker counts, output/data
    paths and checkpoint filenames are deliberately excluded. Runtime precision
    must be recorded explicitly by the caller executing model inference.
    """
    try:
        binding = {"configuration_sha256": manifest["configuration_sha256"],
                   "checkpoint_sha256": manifest["input_checkpoint"]["sha256"],
                   "class_mapping": manifest["class_mapping"],
                   "upstream": {key: manifest["upstream"][key] for key in ("commit", "core_sha256")},
                   "inference_args": {key: manifest["native_args"][key] for key in INFERENCE_ARGUMENTS},
                   "runtime_packages": manifest["runtime"]["packages"],
                   "python_version": manifest["runtime"]["python"].split()[0],
                   "inference_runtime": manifest["inference_runtime"]}
    except (KeyError, TypeError, AttributeError, IndexError) as error:
        raise ValueError("Manifest lacks calibration compatibility identities") from error
    _binding_valid(binding)
    return copy.deepcopy(binding)


def validate_artifact(artifact, expected_binding):
    """Return a detached, validated artifact or explicitly reject its incompatibility."""
    _binding_valid(expected_binding)
    _json_value(artifact)
    try:
        if type(artifact["schema_version"]) is not int or artifact["schema_version"] != 1:
            raise ValueError("Unsupported calibration schema")
        if artifact["method"] != "temperature_scaling":
            raise ValueError("Unsupported calibration method")
        temperature = _temperature(artifact["temperature"])
        if not TEMPERATURE_BOUNDS[0] <= temperature <= TEMPERATURE_BOUNDS[1]:
            raise ValueError("Calibration temperature is outside the fixed fitting bounds")
        _binding_valid(artifact["binding"])
        if artifact["binding"] != expected_binding:
            raise ValueError("Calibration binding does not match checkpoint, classes, configuration or runtime")
        fit, validation = artifact["fit"], artifact["validation"]
        if (fit["split"] != "valid" or fit["objective"] != "nll"
                or fit["temperature_bounds"] != list(TEMPERATURE_BOUNDS)
                or _temperature(fit["temperature"]) != temperature
                or validate_threshold(fit["policy_threshold"]) != DEFAULT_THRESHOLD):
            raise ValueError("Calibration fit does not match the validation-only protocol")
        if type(fit["rows"]) is not int or fit["rows"] <= 0:
            raise ValueError("Calibration requires a positive validation row count")
        for key in ("data_sha256", "metadata_sha256", "logits_sha256", "labels_sha256"):
            _digest(fit[key], key)
        if type(validation["rows"]) is not int or validation["rows"] != fit["rows"]:
            raise ValueError("Calibration validation row count differs from fitted rows")
        for key in ("independent_holdout", "checkpoint_selection_reuse"):
            if validation[key] is not None and type(validation[key]) is not bool:
                raise ValueError(f"Invalid validation provenance flag {key}")
        for key in ("known_train_validation_overlap_rows", "known_validation_test_overlap_rows"):
            value = validation[key]
            if value is not None and (type(value) is not int or not 0 <= value <= fit["rows"]):
                raise ValueError(f"Invalid validation overlap count {key}")
        limits = validation["limitations"]
        if not isinstance(limits, list) or not limits or any(not isinstance(s, str) or not s.strip() for s in limits):
            raise ValueError("Calibration validation limitations must be disclosed")
    except (KeyError, TypeError, AttributeError) as error:
        raise ValueError("Incomplete calibration artifact") from error
    return copy.deepcopy(artifact)
