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


def _receipt(document, rows, checkpoint, metadata, protocol, protocol_hash, manifest_hash):
    _require(document.get('kind') == 'netmambaplus_unlabeled_packet_inference_v1'
             and document.get('schema_version') == 1 and document.get('status') == 'complete'
             and document.get('stage') == 'finished', 'Incomplete inference receipt')
    for field in ('all_rows_predicted', 'counts_finalized', 'input_fully_validated'):
        _require(document.get(field) is True, 'Receipt did not finalize all input rows')
    for field in ('input_rows', 'validated_rows', 'predicted_rows'):
        _require(_integer(document.get(field), 1) and document[field] == rows, 'Receipt row count mismatch')
    _require(document.get('max_rows') is None and document.get('ignored_metadata_columns') == [],
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
    expected_code = {name: study.sha256(ROOT / name) for name in
                     ('packet_data.py', 'packet_model.py', 'tools/predict_packets.py')}
    _require(document.get('code_sha256') == expected_code, 'Inference implementation hash mismatch')


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
            _require(type(prediction.get('row_id')) is int and prediction['row_id'] == row
                     and prediction.get('payload_sha256') == identity, 'Inference payload/order mismatch')
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
            classes += chosen == int(expected[1] > expected[0])
            differences = [abs(a - b) for a, b in zip(logits, expected)]
            maximum = max(maximum, *differences)
            # The retained diagnostic used Python's symmetric max-bound comparison,
            # which is stricter near zero than NumPy's additive allclose bound.
            if any(not math.isclose(a, b, rel_tol=RTOL, abs_tol=ATOL) for a, b in zip(logits, expected)):
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
    return {'status': 'class_predictions_verified', 'rows': total_rows, 'class_agreements': total_classes,
            'strict_logit_tolerance_passed': total_failures == 0,
            'strict_logit_tolerance_failures': total_failures,
            'relative_tolerance': RTOL, 'absolute_tolerance': ATOL,
            'comparison': 'math.isclose: abs(a-b) <= max(atol, rtol*max(abs(a), abs(b)))',
            'sources': observed, 'prior_comparisons': prior,
            'scope': 'Offline saved-artifact and arithmetic audit. Class agreement does not imply bit-exact logits. '
                     'Raw input CSVs and checkpoint weights are not public here; their recorded identities are bound, '
                     'not independently reconstructed. Earlier comparisons have summaries only.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, default=ROOT / 'docs/customer/evidence/packet-study')
    args = parser.parse_args()
    print(json.dumps(verify(args.evidence), indent=2))


if __name__ == '__main__':
    main()
