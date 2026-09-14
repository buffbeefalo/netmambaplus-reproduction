"""Recompute the paired three-checkpoint calibration study from published records.

This reads saved predictions and labels, needs no CUDA or raw flow data, and
rechecks temperatures from saved validation logits, never from test labels.
Run --check to verify the published summary within the stated floating-point tolerance.
"""

import argparse
import hashlib
import json
import math
import statistics
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import calibration
import repro


def require(condition, message):
    if not condition:
        raise ValueError(message)


def equivalent(actual, expected):
    if isinstance(actual, dict) and isinstance(expected, dict):
        return actual.keys() == expected.keys() and all(equivalent(actual[key], expected[key]) for key in actual)
    if isinstance(actual, list) and isinstance(expected, list):
        return len(actual) == len(expected) and all(equivalent(a, b) for a, b in zip(actual, expected))
    if type(actual) is float and type(expected) is float:
        return math.isfinite(actual) and math.isfinite(expected) and math.isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-12)
    return type(actual) is type(expected) and actual == expected


def observation_hash(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=True, allow_nan=False,
                                     separators=(',', ':')).encode('utf-8')).hexdigest()


def instant(value):
    require(isinstance(value, str), 'Receipt timestamp must be an ISO 8601 string')
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    require(parsed.utcoffset() is not None, 'Receipt timestamp must include its UTC offset')
    return parsed


def paired_metrics(current, truth, temperature, threshold, expected_rows):
    mapping = repro.validate_mapping(current['class_mapping'])
    require(mapping == repro.validate_mapping(truth['class_mapping']), 'Paired class meanings differ')
    inverse = {index: name for name, index in mapping.items()}
    rows, known = current['predictions'], truth['predictions']
    require(len(rows) == len(known) == expected_rows, 'Paired row counts differ')
    logits, labels, predictions, differences = [], [], [], []
    disagreements = 0
    for index, (row, reference) in enumerate(zip(rows, known)):
        require(row['row'] == reference['row'] == index, 'Paired row order differs')
        require(len(row['logits']) == len(reference['logits']) == len(mapping),
                'Paired logit dimensions differ from the class mapping')
        calibration.calibrated_scores(reference['logits'], 1.0)
        previous = reference['prediction']
        require(type(previous) is int and previous in inverse
                and reference['logits'][previous] == max(reference['logits']), 'Invalid historical prediction')
        raw = calibration.calibrated_scores(row['logits'], 1.0)
        scaled = calibration.calibrated_scores(row['logits'], temperature)
        for key, expected in [('scores', raw), ('calibrated_scores', scaled)]:
            observed = row[key]
            require(len(observed) == len(expected) and all(
                type(a) in (int, float) and math.isfinite(a) and abs(a - b) <= 1e-12
                for a, b in zip(observed, expected)), f'Incorrect saved {key} at row {index}')
        prediction = row['prediction']
        require(type(prediction) is int and 0 <= prediction < len(raw), 'Invalid predicted class')
        require(row['class_name'] == inverse[prediction], 'Predicted class name conflicts with its mapping')
        require(row['logits'][prediction] == max(row['logits']), 'Prediction is not a maximum logit')
        require(row['decision'] == ('accept' if scaled[prediction] >= threshold else 'defer'),
                f'Incorrect saved review policy at row {index}')
        require(len(row['logits']) == len(reference['logits']), 'Historical logit dimensions differ')
        differences.extend(abs(a - b) for a, b in zip(row['logits'], reference['logits']))
        disagreements += prediction != reference['prediction']
        logits.append(row['logits'])
        labels.append(reference['label'])
        predictions.append(prediction)
    raw = calibration.classification_metrics(logits, labels, 1.0, threshold, predictions=predictions)
    scaled = calibration.classification_metrics(logits, labels, temperature, threshold, predictions=predictions)
    require(raw['correct'] == scaled['correct'], 'Temperature changed class accuracy')
    return {'raw': raw, 'calibrated': scaled,
            'delta_calibrated_minus_raw': {key: scaled[key] - raw[key] for key in ('nll', 'brier', 'ece', 'accuracy', 'coverage')},
            'class_disagreements_with_historical': disagreements,
            'historical_logit_comparison': {'values': len(differences),
                'different_values': sum(value != 0 for value in differences),
                'maximum_absolute_difference': max(differences)},
            'score_check_absolute_tolerance': 1e-12}


def review(evidence, root=ROOT):
    evidence = Path(evidence).resolve()
    root = Path(root).resolve()
    def load(path):
        document, _ = repro.read_document(path)
        return document
    def reference(path):
        path = Path(path).resolve()
        return {'path': path.relative_to(root).as_posix(), 'sha256': repro.sha256_file(path)}
    protocol_path = evidence / 'protocol.json'
    protocol = load(protocol_path)
    require(protocol['schema_version'] == 1 and protocol['protocol_frozen_before_scaled_test_evaluation'] is True,
            'Missing fixed study protocol')
    require([s['seed'] for s in protocol['seeds']] == [0, 1, 2], 'The study requires all three original seeds')
    threshold = calibration.validate_threshold(protocol['policy']['threshold'])
    require(threshold == calibration.DEFAULT_THRESHOLD, 'Study threshold differs from its fixed protocol')
    fit_finished, inference_started, records = [], [], []
    frozen_at = instant(protocol['frozen_at'])
    for seed_spec in protocol['seeds']:
        seed = seed_spec['seed']
        directory = evidence / f'seed{seed}'
        paths = {key: directory / name for key, name in {
            'calibration': 'calibration.json', 'fit_manifest': 'fit-manifest.json',
            'predictions': 'predictions.json', 'prediction_manifest': 'prediction-manifest.json'}.items()}
        documents = {key: load(path) for key, path in paths.items()}
        artifact = documents['calibration']
        manifest = documents['prediction_manifest']
        fit_manifest = documents['fit_manifest']
        require(manifest['status'] == fit_manifest['status'] == 'succeeded', 'A model invocation did not succeed')
        require(repro.sha256_file(paths['predictions']) == manifest['metrics_file']['sha256'], 'Prediction receipt hash differs')
        require(manifest['input_checkpoint']['sha256'] == seed_spec['checkpoint_sha256'], 'Study checkpoint changed')
        require(documents['predictions']['checkpoint_sha256'] == seed_spec['checkpoint_sha256'],
                'Prediction document checkpoint differs from its bound manifest')
        require(documents['predictions']['class_mapping'] == manifest['class_mapping'],
                'Prediction document class meanings differ from its bound manifest')
        calibration.validate_artifact(artifact, calibration.make_binding(manifest))
        calibration.validate_artifact(artifact, calibration.make_binding(fit_manifest))
        require(fit_manifest['calibration_artifact']['sha256'] == repro.sha256_file(paths['calibration']),
                'Fitting receipt does not bind this calibration file')
        require(manifest['calibration']['file']['sha256'] == repro.sha256_file(paths['calibration']), 'Calibrator receipt hash differs')
        require(artifact['fit']['data_sha256'] == protocol['fit']['sha256']
                and artifact['fit']['rows'] == protocol['fit']['rows'], 'Fitting split differs from protocol')
        require(fit_manifest['input_files']['data-valid.json']['sha256'] == protocol['fit']['sha256'],
                'Executed fitting input differs from the fixed validation split')
        observations = fit_manifest['validation_observations']
        for name in ('logits', 'labels'):
            require(len(observations[name]) == protocol['fit']['rows']
                    and observation_hash(observations[name]) == artifact['fit'][name + '_sha256'],
                    'Validation observations differ from the fitted artifact')
        fitted_again = calibration.fit_temperature(observations['logits'], observations['labels'])
        require(equivalent(fitted_again, float(artifact['temperature'])), 'Temperature cannot be reproduced from validation observations')
        for key, temperature, cutoff in [('raw_metrics', 1.0, None),
                                         ('calibrated_metrics', artifact['temperature'], threshold)]:
            require(equivalent(calibration.classification_metrics(observations['logits'], observations['labels'],
                                                                  temperature, cutoff), artifact['fit'][key]),
                    'Recorded validation metrics cannot be reproduced')
        require(manifest['calibration']['abstain_threshold'] == threshold, 'Executed threshold differs from protocol')
        require(documents['predictions']['source']['sha256'] == protocol['evaluation']['sha256'], 'Predicted flow file differs')
        fit_start, fit_end = instant(fit_manifest['created_at']), instant(fit_manifest['updated_at'])
        prediction_start, prediction_end = instant(manifest['created_at']), instant(manifest['updated_at'])
        require(fit_start <= fit_end and prediction_start <= prediction_end,
                'A completed invocation has an end time before its start time')
        fit_finished.append(fit_end)
        inference_started.append(prediction_start)
        require(frozen_at <= fit_start, 'Fitting predates the frozen protocol')
        historical_path = root / f'docs/customer/evidence/seed{seed}/replay/predictions.json'
        truth = load(historical_path)
        require(truth['test_sha256'] == protocol['evaluation']['sha256'], 'Recorded ground truth belongs to different test data')
        require(truth['checkpoint_sha256'] == seed_spec['checkpoint_sha256'], 'Historical checkpoint differs')
        result = paired_metrics(documents['predictions'], truth, artifact['temperature'], threshold,
                                protocol['evaluation']['rows'])
        records.append({'seed': seed, 'temperature': artifact['temperature'],
                        'inputs': {key: reference(path) for key, path in paths.items()},
                        'recorded_ground_truth': reference(historical_path), **result})
    require(max(fit_finished) <= min(inference_started), 'Not all calibrators were frozen before test inference')
    aggregate = {}
    for kind in ('raw', 'calibrated', 'delta_calibrated_minus_raw'):
        aggregate[kind] = {}
        for metric in ('nll', 'brier', 'ece', 'accuracy', 'coverage'):
            values = [record[kind][metric] for record in records]
            aggregate[kind][metric] = {'mean': statistics.mean(values),
                                       'sample_standard_deviation': statistics.stdev(values)}
    return {'schema_version': 1, 'kind': 'retrospective_paired_temperature_scaling_study',
            'protocol': reference(protocol_path), 'seeds': records, 'aggregate': aggregate,
            'metric_units': {'nll': 'mean negative log-likelihood, natural logs; lower is better',
                'brier': 'mean sum of squared probability errors over classes; lower is better',
                'ece': '15 equal-width confidence bins, fraction; lower is better',
                'accuracy': 'correct / all rows', 'coverage': 'accepted / all rows',
                'accepted_error_rate': 'wrong accepted / accepted; null if denominator is zero'},
            'method': 'Paired raw/scaled scores from identical fresh native logits; labels read only by this retrospective reviewer from hash-bound published test records.',
            'time_order': 'Protocol precedes fitting; all three calibration fits finish before any of the three calibrated test invocations.',
            'numerical_recheck_tolerance': {'relative': 1e-10, 'absolute': 1e-12,
                                           'scope': 'Recomputed floating-point quantities only; file hashes, integers and structure must match exactly.'},
            'limits': protocol['limitations'],
            'reviewer': reference(Path(__file__).resolve()), 'calibration_math': reference(root / 'calibration.py')}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, default=ROOT / 'docs/customer/evidence/calibration')
    parser.add_argument('--check', action='store_true', help='Compare recomputed results with results.json without writing')
    args = parser.parse_args(argv)
    try:
        result = review(args.evidence)
        output = args.evidence / 'results.json'
        if args.check:
            require(equivalent(repro.read_document(output)[0], result), 'Published calibration summary is stale or differs from its records')
            print('Calibration evidence check passed: all three checkpoints, paired metrics, hashes and fixed policy.')
        else:
            repro.atomic_json(output, result, overwrite=False)
            print(f'Calibration summary: {output}')
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f'Calibration review failed: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
