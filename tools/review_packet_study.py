"""Recompute published packet outcomes and check their retained training evidence."""

import argparse
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import packet_data
import packet_study as study


def compare(actual, expected, location='result'):
    if type(expected) is dict:
        if type(actual) is not dict or set(actual) != set(expected):
            raise ValueError('Object fields differ: ' + location)
        for key in expected:
            compare(actual[key], expected[key], location + '.' + key)
    elif type(expected) is list:
        if type(actual) is not list or len(actual) != len(expected):
            raise ValueError('List size differs: ' + location)
        for index, (left, right) in enumerate(zip(actual, expected)):
            compare(left, right, f'{location}[{index}]')
    elif type(expected) in (int, float):
        if type(actual) not in (int, float) or not math.isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-10):
            raise ValueError('Numeric result differs: ' + location)
    elif type(actual) is not type(expected) or actual != expected:
        raise ValueError('Result differs: ' + location)


def independent_metrics(records, expected):
    """Use scikit-learn's separate metric implementations on expanded weighted targets."""
    import numpy as np
    from sklearn import metrics
    targets, scores, predictions, row_weights, group_weights = [], [], [], [], []
    for item in records:
        margin = item['logits'][1] - item['logits'][0]
        total = sum(item['counts'])
        for truth, count in enumerate(item['counts']):
            if count:
                targets.append(truth); scores.append(margin); predictions.append(int(margin > 0))
                row_weights.append(count); group_weights.append(count / total)
    for name, weights in (('row_weighted', row_weights), ('group_weighted', group_weights)):
        matrix = metrics.confusion_matrix(targets, predictions, labels=[0, 1], sample_weight=weights)
        observed = {
            'confusion_matrix': matrix.tolist(),
            'accuracy': metrics.accuracy_score(targets, predictions, sample_weight=weights),
            'balanced_accuracy': metrics.balanced_accuracy_score(targets, predictions, sample_weight=weights),
            'macro_f1': metrics.f1_score(targets, predictions, labels=[0,1], average='macro', sample_weight=weights),
            'auroc': metrics.roc_auc_score(targets, scores, sample_weight=weights),
            'attack_average_precision': metrics.average_precision_score(targets, scores, sample_weight=weights),
        }
        for metric, value in observed.items():
            compare(value if isinstance(value, list) else float(value), expected[name][metric], name + '.' + metric)


def verify(root, *, independent=False):
    root = Path(root)
    index = study.read_json(root / 'index.json')
    references = index['files']
    paths = [item['path'] for item in references]
    actual_paths = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and p != root / 'index.json'}
    if len(set(paths)) != len(paths) or set(paths) != actual_paths:
        raise ValueError('Packet evidence inventory is incomplete or duplicated')
    for reference in references:
        study.verify_artifact(root, reference)
    protocol = study.read_json(root / 'protocol.json')
    manifest = study.read_json(root / 'manifest.json')
    results = study.read_json(root / 'results.json')
    if results['status'] != 'completed' or len(results['results']) != 6:
        raise ValueError('Six completed native packet arms are required')
    protocol_hash = study.sha256(root / 'protocol.json')
    if results['protocol_sha256'] != protocol_hash or results['data_manifest_sha256'] != study.sha256(root / 'manifest.json'):
        raise ValueError('Results are not bound to the retained data/protocol')
    frozen = study.read_json(study.verify_artifact(root, results['frozen_checkpoints']))
    if frozen['protocol_sha256'] != protocol_hash:
        raise ValueError('Checkpoint selection uses a different protocol')
    if [r['arm'] for r in results['results']] != protocol['arms']:
        raise ValueError('Reported arms differ from the frozen protocol')
    replays = groups = rows = 0
    training = {}
    for item in results['results']:
        arm = item['arm']['name']
        receipt = study.read_json(study.verify_artifact(root, item['training_receipt']))
        training[arm] = receipt
        if (receipt['steps'] != protocol['steps'] or receipt['steps'] < 100
                or receipt['optimizer_step_range'] != [protocol['steps']] * 2
                or receipt['optimizer_parameter_states'] != 51):
            raise ValueError('Incomplete achieved optimizer budget: ' + arm)
        compare(item['selected_checkpoint'], frozen['selected_checkpoints'][arm])
        compare(item['selected_checkpoint'], receipt['selected_checkpoint'])
        history = receipt['validation_history']
        if [v['step'] for v in history] != list(range(protocol['validation_interval'], protocol['steps'] + 1, protocol['validation_interval'])):
            raise ValueError('Validation cadence differs from the protocol')
        for observation in history:
            if set(observation['sources']) != set(item['arm']['sources']):
                raise ValueError('Validation used an undeclared source')
            score = sum(m['group_weighted']['macro_f1'] for m in observation['sources'].values()) / len(observation['sources'])
            compare(observation['selection_score'], score, arm + '.selection_score')
        best = max(history, key=lambda v: v['selection_score'])
        if item['selected_checkpoint']['step'] != best['step']:
            raise ValueError('Checkpoint was not selected by the declared earliest-best rule')
        log = study.verify_artifact(root, receipt['training_log'])
        observations = [json.loads(line) for line in log.read_text().splitlines()]
        if [v['step'] for v in observations] != list(range(1, protocol['steps'] + 1)):
            raise ValueError('Optimizer log is incomplete')
        if any(not math.isfinite(v['loss']) or not math.isfinite(v['unclipped_gradient_norm']) for v in observations):
            raise ValueError('Training log contains nonfinite values')
        if set(item['tests']) != {'cic', 'unsw'}:
            raise ValueError('Both source tests are required')
        for source, test in item['tests'].items():
            path = study.verify_artifact(root, test['predictions'])
            records = list(study.prediction_records(path))
            measured = study.evaluate_records(records, original_labels=packet_data.LABELS[source],
                normal_label=packet_data.LABELS[source][0])
            compare(measured, test['metrics'])
            support = manifest['sources'][source]['splits']['test']
            if measured['groups'] != support['selected_groups'] or measured['rows'] != support['selected_rows']:
                raise ValueError('Test predictions do not cover the declared selected split')
            compare(measured['row_weighted']['support'], support['selected_binary_counts'])
            compare({label: summary['rows'] for label, summary in measured['original_labels'].items()},
                    support['selected_label_counts'])
            import hashlib
            membership = hashlib.sha256(b''.join(bytes.fromhex(r['id']) for r in records)).hexdigest()
            if membership != support['selected_membership_sha256']:
                raise ValueError('Test prediction membership differs from the frozen split')
            if independent:
                independent_metrics(records, measured)
            replays += 1; groups += measured['groups']; rows += measured['rows']
    for name in ('cic', 'unsw', 'joint'):
        left, right = (training[name + '_' + init] for init in ('pretrained', 'scratch'))
        if left['initial_parameter_sha256']['head.weight'] != right['initial_parameter_sha256']['head.weight']:
            raise ValueError('Paired classifiers had different starting heads')
        compare(left['group_presentations'], right['group_presentations'])
        compare(left['distinct_training_groups_observed'], right['distinct_training_groups_observed'])
        compare(left['training_batch_stream_sha256'], right['training_batch_stream_sha256'])
    from tools.review_packet_controls import verify as verify_controls
    controls = verify_controls(root, independent=independent)
    from tools.review_packet_inference import verify as verify_inference
    inference = verify_inference(root)
    return {'status': 'passed', 'native_arms': 6, 'prediction_sets_recomputed': replays,
            'group_predictions_recomputed': groups, 'row_weighted_predictions_represented': rows,
            'independent_sklearn_metrics': independent,
            'controls': controls,
            'unlabeled_inference': inference,
            'scope': 'Offline artifact and arithmetic verification; does not rerun GPU training or establish capture independence.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, default=ROOT / 'docs/customer/evidence/packet-study')
    parser.add_argument('--independent', action='store_true', help='Also compare with scikit-learn (requires ML environment)')
    args = parser.parse_args()
    print(json.dumps(verify(args.evidence, independent=args.independent), indent=2))


if __name__ == '__main__':
    main()
