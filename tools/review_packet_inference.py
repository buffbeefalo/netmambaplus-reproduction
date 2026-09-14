"""Audit public unlabeled packet predictions without loading a model or raw CSV."""

import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import packet_study as study

RTOL, ATOL = 1e-4, 1e-6
SOURCES = ('cic', 'unsw')
CLASSES = {'benign': 0, 'attack': 1}
INFERENCE_CODE = ('packet_data.py', 'packet_model.py', 'tools/predict_packets.py')
PREDICTION_FIELDS = ('row_id', 'payload_sha256', 'class_index', 'class_name', 'logits',
                     'probabilities', 'probability', 'probability_kind')
FILES = {'agreement.json', 'cic-predictions.jsonl.gz', 'unsw-predictions.jsonl.gz',
         'cic-receipt.json', 'unsw-receipt.json', 'default-receipt.json',
         'default-comparison.json', 'override-only-comparison.json'}


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _integer(value, minimum=0):
    return type(value) is int and value >= minimum


def _number(value):
    return type(value) in (int, float) and math.isfinite(value)


def _fingerprint(descriptor):
    _require(isinstance(descriptor, dict) and _integer(descriptor.get('bytes'), 1)
             and isinstance(descriptor.get('path'), str)
             and isinstance(descriptor.get('sha256'), str)
             and re.fullmatch('[0-9a-f]{64}', descriptor['sha256']), 'Invalid artifact identity')


def _tolerances(document):
    _require(type(document.get('relative_tolerance')) is float
             and document['relative_tolerance'] == RTOL
             and type(document.get('absolute_tolerance')) is float
             and document['absolute_tolerance'] == ATOL, 'Recorded comparison tolerance changed')


def _loads(line):
    def pairs(items):
        result = {}
        for key, value in items:
            _require(key not in result, 'Duplicate prediction field')
            result[key] = value
        return result
    def reject(value):
        raise ValueError('Nonfinite prediction JSON: ' + value)
    result = json.loads(line, object_pairs_hook=pairs, parse_constant=reject)
    _require(type(result) is dict, 'Prediction must be an object')
    return result


def _logits(values):
    _require(type(values) is list and len(values) == 2 and all(_number(v) for v in values),
             'Expected two finite logits')
    return values


def _receipt(document, rows, checkpoint, metadata, protocol, protocol_hash, manifest_hash,
             *, cap=None, allow_new_predictor=False):
    _require(document.get('kind') == 'netmambaplus_unlabeled_packet_inference_v1'
             and document.get('schema_version') == 1
             and document.get('status') == ('complete' if cap is None else 'capped')
             and document.get('stage') == 'finished', 'Incomplete inference receipt')
    _require(document.get('all_rows_predicted') is (cap is None), 'Receipt prediction cap status mismatch')
    for field in ('counts_finalized', 'input_fully_validated'):
        _require(document.get(field) is True, 'Receipt did not finalize all input rows')
    for field in ('input_rows', 'validated_rows'):
        _require(_integer(document.get(field), 1) and document[field] == rows, 'Receipt row count mismatch')
    _require(_integer(document.get('predicted_rows'), 1)
             and document['predicted_rows'] == (rows if cap is None else cap), 'Receipt prediction count mismatch')
    _require(type(document.get('max_rows')) is type(cap) and document.get('max_rows') == cap
             and document.get('ignored_metadata_columns') == [],
             'Unexpected capped or metadata-bearing inference input')
    _require(document.get('class_mapping') == CLASSES
             and document.get('probability_kind') == 'uncalibrated_softmax', 'Inference class/probability contract changed')
    _require(document.get('batch_size') == protocol['inference_batch_size'], 'Inference batch size changed')
    for field in ('input', 'predictions', 'checkpoint'):
        _fingerprint(document.get(field))
    _require(document['input'].get('sha256_scope') == 'entire_file', 'Input was not fingerprinted entirely')
    _require(document['predictions']['path'] == 'predictions.jsonl', 'Unexpected receipt prediction path')
    for field in ('sha256', 'bytes'):
        _require(document['checkpoint'][field] == checkpoint[field], 'Receipt used a different frozen checkpoint')
    _require(Path(document['checkpoint']['path']).name == Path(checkpoint['path']).name,
             'Checkpoint filename differs from selected checkpoint')
    _require(document.get('checkpoint_metadata') == metadata, 'Receipts have inconsistent checkpoint metadata')
    _require(metadata.get('class_mapping') == CLASSES, 'Checkpoint class mapping changed')
    binding = metadata['study_metadata']
    _require(binding.get('arm') == 'joint_pretrained' and binding.get('sources') == list(SOURCES)
             and binding.get('step') == checkpoint['step']
             and binding.get('protocol_sha256') == protocol_hash
             and binding.get('data_manifest_sha256') == manifest_hash
             and binding.get('source_sha256') == protocol['source_sha256'], 'Inference checkpoint study binding mismatch')
    # Audit the frozen run's implementation, which can predate portable I/O fixes
    # in the current checkout. The protocol itself is hash-bound above.
    protocol_code = protocol.get('code_sha256')
    _require(type(protocol_code) is dict and all(
        isinstance(protocol_code.get(name), str) and re.fullmatch('[0-9a-f]{64}', protocol_code[name])
        for name in INFERENCE_CODE), 'Missing or malformed protocol implementation bindings')
    expected_code = {name: protocol_code[name] for name in INFERENCE_CODE}
    if allow_new_predictor:
        code = document.get('code_sha256')
        _require(type(code) is dict and set(code) == set(INFERENCE_CODE)
                 and all(isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value) for value in code.values()),
                 'Malformed post-study implementation declarations')
        _require(all(code[name] == expected_code[name] for name in INFERENCE_CODE[:2])
                 and code['tools/predict_packets.py'] != expected_code['tools/predict_packets.py'],
                 'Post-study implementation changed model/data or lacks a new predictor declaration')
    else:
        _require(document.get('code_sha256') == expected_code, 'Inference implementation hash mismatch')


def _compare_prediction(prediction, original, row):
    _require(type(prediction.get('row_id')) is int and prediction['row_id'] == row
             and prediction.get('payload_sha256') == original['id'], 'Inference payload/order mismatch')
    logits, expected = _logits(prediction['logits']), _logits(original['logits'])
    chosen = int(logits[1] > logits[0])
    _require(type(prediction.get('class_index')) is int and prediction['class_index'] == chosen
             and prediction.get('class_name') == ('benign', 'attack')[chosen], 'Class differs from logit argmax')
    _require(prediction.get('probability_kind') == 'uncalibrated_softmax', 'Wrong probability interpretation')
    probabilities = prediction.get('probabilities')
    weights = [math.exp(value - max(logits)) for value in logits]
    softmax = [value / sum(weights) for value in weights]
    _require(type(probabilities) is list and len(probabilities) == 2
             and all(_number(v) and 0 <= v <= 1 for v in probabilities)
             and all(math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12) for a, b in zip(probabilities, softmax))
             and _number(prediction.get('probability'))
             and math.isclose(prediction['probability'], softmax[chosen], rel_tol=1e-12, abs_tol=1e-12),
             'Probability differs from finite softmax')
    maximum = max(abs(a - b) for a, b in zip(logits, expected))
    # Preserve the recorded symmetric max-bound comparison, including near zero.
    failed = any(not math.isclose(a, b, rel_tol=RTOL, abs_tol=ATOL) for a, b in zip(logits, expected))
    return chosen == int(expected[1] > expected[0]), maximum, failed


def _prior(document, rows):
    _tolerances(document)
    _require(document.get('status') == 'numerical_tolerance_failed'
             and document.get('rows') == rows and document.get('class_agreements') == rows,
             'Prior comparison status/counts mismatch')
    failed = document.get('failed_rows')
    _require(type(failed) is list and failed and all(_integer(i) and i < rows for i in failed)
             and failed == sorted(set(failed))
             and document.get('logit_tolerance_failures') == len(failed), 'Prior failure row inventory mismatch')
    maximum = document.get('maximum_absolute_logit_difference')
    _require(_number(maximum) and maximum > ATOL, 'Prior comparison maximum is invalid')
    return {key: document[key] for key in ('status', 'rows', 'class_agreements', 'failed_rows',
            'logit_tolerance_failures', 'maximum_absolute_logit_difference',
            'relative_tolerance', 'absolute_tolerance')} | {
                'verification': 'Retained summary consistency only; prediction records are not public.'}


def verify(parent_evidence):
    """Check identities and classes while reporting, rather than hiding, numeric failures."""
    root = Path(parent_evidence)
    directory = root / 'unlabeled'
    inventory = study.read_json(root / 'index.json')['files']
    references = {item['path']: item for item in inventory}
    _require(len(references) == len(inventory), 'Duplicate evidence index paths')
    actual = {p.relative_to(directory).as_posix() for p in directory.rglob('*') if p.is_file()}
    _require(actual == FILES, 'Unexpected unlabeled evidence inventory')
    needed = {'unlabeled/' + name for name in FILES} | {
        'protocol.json', 'manifest.json', 'frozen-checkpoints.json',
        'joint_pretrained/training-receipt.json',
        'joint_pretrained/test-cic.jsonl.gz', 'joint_pretrained/test-unsw.jsonl.gz'}
    _require(needed <= set(references), 'Missing inference evidence index entries')
    for name in needed:
        study.verify_artifact(root, references[name])
    protocol = study.read_json(root / 'protocol.json')
    manifest = study.read_json(root / 'manifest.json')
    protocol_hash, manifest_hash = study.sha256(root / 'protocol.json'), study.sha256(root / 'manifest.json')
    _require(protocol.get('data_manifest_sha256') == manifest_hash, 'Protocol data identity mismatch')
    _require(protocol.get('class_mapping') == CLASSES and set(protocol['source_sha256']) == set(SOURCES),
             'Protocol input/class contract mismatch')
    frozen = study.read_json(root / 'frozen-checkpoints.json')
    _require(frozen.get('protocol_sha256') == protocol_hash, 'Frozen checkpoint protocol mismatch')
    checkpoint = frozen['selected_checkpoints']['joint_pretrained']
    _fingerprint(checkpoint)
    training = study.read_json(root / 'joint_pretrained/training-receipt.json')
    _require(training['selected_checkpoint'] == checkpoint, 'Training and frozen checkpoint identities differ')
    agreement = study.read_json(directory / 'agreement.json')
    _tolerances(agreement)
    _require(agreement.get('status') == 'class_predictions_verified'
             and set(agreement['sources']) == set(SOURCES), 'Inference agreement status/source mismatch')
    settings = agreement['settings']
    _require(settings.get('NVIDIA_TF32_OVERRIDE') == '0'
             and settings.get('torch.backends.cuda.matmul.allow_tf32') is False
             and settings.get('torch.backends.cudnn.allow_tf32') is False
             and settings.get('batch_size') == protocol['inference_batch_size']
             and settings.get('batch_grouping') == 'Each source separately, identical to measured evaluation',
             'Controlled comparison settings changed')
    metadata = study.read_json(directory / 'cic-receipt.json')['checkpoint_metadata']
    observed, total_rows, total_classes, total_failures = {}, 0, 0, 0
    for source in SOURCES:
        recorded = agreement['sources'][source]
        _require(recorded['receipt']['path'] == source + '-receipt.json'
                 and recorded['compressed_predictions']['path'] == source + '-predictions.jsonl.gz',
                 'Source prediction/receipt path mismatch')
        receipt = study.read_json(study.verify_artifact(directory, recorded['receipt']))
        path = study.verify_artifact(directory, recorded['compressed_predictions'])
        support = manifest['sources'][source]['splits']['test']
        count = support['selected_groups']
        _require(_integer(count, 1), 'Invalid selected test group count')
        _receipt(receipt, count, checkpoint, metadata, protocol, protocol_hash, manifest_hash)
        with gzip.open(path, 'rb') as stream:
            raw = stream.read()
        _require(len(raw) == receipt['predictions']['bytes']
                 and hashlib.sha256(raw).hexdigest() == receipt['predictions']['sha256'],
                 'Uncompressed prediction fingerprint mismatch')
        records = [_loads(line) for line in raw.decode('utf-8').splitlines()]
        with gzip.open(root / 'joint_pretrained' / ('test-' + source + '.jsonl.gz'), 'rt', encoding='utf-8') as stream:
            reference = [_loads(line) for line in stream]
        _require(len(records) == len(reference) == count, 'Inference/reference row count mismatch')
        membership = hashlib.sha256()
        previous, classes, failed, maximum = '', 0, [], 0.0
        for row, (prediction, original) in enumerate(zip(records, reference)):
            identity = original['id']
            _require(isinstance(identity, str) and re.fullmatch('[0-9a-f]{64}', identity)
                     and identity > previous, 'Reference payloads must be unique and sorted')
            previous = identity
            membership.update(bytes.fromhex(identity))
            agrees, difference, row_failed = _compare_prediction(prediction, original, row)
            classes += agrees
            maximum = max(maximum, difference)
            if row_failed:
                failed.append(row)
        _require(membership.hexdigest() == support['selected_membership_sha256'], 'Reference test membership mismatch')
        summary = {'rows': count, 'class_agreements': classes, 'failed_rows': failed,
                   'strict_logit_tolerance_failures': len(failed), 'maximum_absolute_logit_difference': maximum}
        for key, value in summary.items():
            _require(type(recorded.get(key)) is type(value) and recorded[key] == value,
                     'Recomputed inference comparison differs: ' + source + '.' + key)
        _require(classes == count, 'Unlabeled and measured class predictions differ')
        observed[source] = summary
        total_rows += count
        total_classes += classes
        total_failures += len(failed)
    _require(type(agreement.get('rows')) is int and agreement['rows'] == total_rows
             and agreement.get('strict_logit_tolerance_passed') is (total_failures == 0),
             'Agreement total or strict tolerance flag is false')
    default_receipt = study.read_json(directory / 'default-receipt.json')
    _receipt(default_receipt, total_rows, checkpoint, metadata, protocol, protocol_hash, manifest_hash)
    prior = {}
    for name in ('default', 'override-only'):
        document = study.read_json(directory / (name + '-comparison.json'))
        if name == 'override-only':
            _require(document.get('environment') == {'NVIDIA_TF32_OVERRIDE': '0'}, 'Prior override environment mismatch')
        prior[name] = _prior(document, total_rows)
    post_study_io = verify_post_study_io(root) if (root / 'post-study-io-check.json').exists() else {'status': 'not_recorded'}
    return {'status': 'class_predictions_verified', 'rows': total_rows, 'class_agreements': total_classes,
            'strict_logit_tolerance_passed': total_failures == 0,
            'strict_logit_tolerance_failures': total_failures,
            'relative_tolerance': RTOL, 'absolute_tolerance': ATOL,
            'comparison': 'math.isclose: abs(a-b) <= max(atol, rtol*max(abs(a), abs(b)))',
            'sources': observed, 'prior_comparisons': prior,
            'post_study_io': post_study_io,
            'scope': 'Offline saved-artifact and arithmetic audit. Class agreement does not imply bit-exact logits. '
                     'Raw input CSVs and checkpoint weights are not public here; their recorded identities are bound, '
                     'not independently reconstructed. Earlier comparisons have summaries only.'}


def verify_post_study_io(parent_evidence):
    """Audit the separately recorded capped regression after the predictor I/O fix."""
    root = Path(parent_evidence)
    name = 'post-study-io-check.json'
    if not (root / name).exists():
        return {'status': 'not_recorded'}
    inventory = study.read_json(root / 'index.json')['files']
    references = {item['path']: item for item in inventory}
    _require(len(references) == len(inventory), 'Duplicate evidence index paths')
    required = {name, 'protocol.json', 'manifest.json', 'frozen-checkpoints.json',
                'joint_pretrained/training-receipt.json', 'joint_pretrained/test-cic.jsonl.gz',
                'unlabeled/default-receipt.json'}
    _require(required <= set(references), 'Missing post-study evidence index entries')
    for path in required:
        study.verify_artifact(root, references[path])
    protocol = study.read_json(root / 'protocol.json')
    manifest = study.read_json(root / 'manifest.json')
    protocol_hash, manifest_hash = study.sha256(root / 'protocol.json'), study.sha256(root / 'manifest.json')
    _require(protocol.get('data_manifest_sha256') == manifest_hash, 'Protocol data identity mismatch')
    frozen = study.read_json(root / 'frozen-checkpoints.json')
    _require(frozen.get('protocol_sha256') == protocol_hash, 'Frozen checkpoint protocol mismatch')
    checkpoint = frozen['selected_checkpoints']['joint_pretrained']
    _fingerprint(checkpoint)
    training = study.read_json(root / 'joint_pretrained/training-receipt.json')
    _require(training['selected_checkpoint'] == checkpoint, 'Training and frozen checkpoint identities differ')
    rows = [manifest['sources'][source]['splits']['test']['selected_groups'] for source in SOURCES]
    cap = 128
    _require(all(_integer(count, 1) for count in rows) and rows[0] >= cap and sum(rows) > cap,
             'Post-study check exceeds the selected CIC prefix or full input')
    total = sum(rows)
    original_receipt = study.read_json(root / 'unlabeled/default-receipt.json')
    metadata = original_receipt['checkpoint_metadata']
    _receipt(original_receipt, total, checkpoint, metadata, protocol, protocol_hash, manifest_hash)
    document = study.read_json(root / name)
    _require(document.get('status') == 'class_predictions_verified'
             and isinstance(document.get('historical_implementation_revision'), str)
             and re.fullmatch('[0-9a-f]{40}', document['historical_implementation_revision']),
             'Invalid post-study status or historical implementation declaration')
    receipt = document['receipt']
    _receipt(receipt, total, checkpoint, metadata, protocol, protocol_hash, manifest_hash,
             cap=cap, allow_new_predictor=True)
    for field in ('sha256', 'bytes', 'sha256_scope'):
        _require(receipt['input'][field] == original_receipt['input'][field],
                 'Post-study input identity differs from original full input')
    predictions = document['predictions']
    _require(type(predictions) is list and len(predictions) == cap
             and all(type(record) is dict and set(record) == set(PREDICTION_FIELDS) for record in predictions),
             'Post-study embedded prediction inventory mismatch')
    # The retained JSON container sorts object keys. Restore the predictor's original
    # field insertion order and compact serializer to verify the original JSONL bytes.
    raw = ''.join(json.dumps({key: record[key] for key in PREDICTION_FIELDS},
                             separators=(',', ':'), allow_nan=False) + '\n'
                  for record in predictions).encode('utf-8')
    _require(receipt['predictions']['bytes'] == len(raw)
             and receipt['predictions']['sha256'] == hashlib.sha256(raw).hexdigest(),
             'Post-study prediction fingerprint mismatch')
    with gzip.open(root / 'joint_pretrained/test-cic.jsonl.gz', 'rt', encoding='utf-8') as stream:
        reference = [_loads(line) for line in stream]
    _require(len(reference) == rows[0], 'Primary CIC test count mismatch')
    membership, previous = hashlib.sha256(), ''
    for original in reference:
        identity = original['id']
        _require(isinstance(identity, str) and re.fullmatch('[0-9a-f]{64}', identity)
                 and identity > previous, 'Reference payloads must be unique and sorted')
        previous = identity
        membership.update(bytes.fromhex(identity))
    _require(membership.hexdigest() == manifest['sources']['cic']['splits']['test']['selected_membership_sha256'],
             'Primary CIC test membership mismatch')
    classes, maximum, failed = 0, 0.0, []
    for row, (prediction, original) in enumerate(zip(predictions, reference)):
        agrees, difference, row_failed = _compare_prediction(prediction, original, row)
        classes += agrees
        maximum = max(maximum, difference)
        if row_failed:
            failed.append(row)
    comparison = {'rows': cap, 'class_agreements': classes, 'failed_rows': failed,
                  'maximum_absolute_logit_difference': maximum,
                  'relative_tolerance': RTOL, 'absolute_tolerance': ATOL,
                  'strict_logit_tolerance_passed': not failed}
    _tolerances(document['comparison'])
    _require(set(document['comparison']) == set(comparison), 'Post-study comparison fields mismatch')
    for key, value in comparison.items():
        _require(type(document['comparison'][key]) is type(value) and document['comparison'][key] == value,
                 'Recomputed post-study comparison differs: ' + key)
    _require(classes == cap, 'Post-study class predictions differ from primary test records')
    return {'status': 'class_predictions_verified', **comparison, 'validated_rows': total,
            'inference_code_sha256': receipt['code_sha256'],
            'predictions_sha256': hashlib.sha256(raw).hexdigest(),
            'historical_implementation_revision': document['historical_implementation_revision'],
            'scope': 'Separate capped post-study I/O check on the first 128 CIC groups. Full input validation '
                     'is recorded in the bound receipt; raw CSVs are not present. The new predictor hash is '
                     'a retained declaration; model/data hashes match the frozen protocol. This check does '
                     'not replace the original full-test inference comparison or establish bit-exact replay.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, default=ROOT / 'docs/customer/evidence/packet-study')
    args = parser.parse_args()
    print(json.dumps(verify(args.evidence), indent=2))


if __name__ == '__main__':
    main()
