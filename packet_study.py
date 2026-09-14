"""Portable arithmetic and artifact checks for the separate packet study."""

import gzip
import hashlib
import json
import math
import re
from pathlib import Path


def sha256(path):
    hasher = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            hasher.update(block)
    return hasher.hexdigest()


def read_json(path):
    def reject(value):
        raise ValueError('Nonfinite JSON number: ' + value)
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('Duplicate JSON key: ' + key)
            result[key] = value
        return result
    return json.loads(Path(path).read_text(encoding='utf-8'), parse_constant=reject,
                      object_pairs_hook=pairs)


def write_json(path, document):
    path = Path(path)
    encoded = json.dumps(document, indent=2, sort_keys=True, allow_nan=False) + '\n'
    with path.open('x', encoding='utf-8') as stream:
        stream.write(encoded)


def artifact(root, path):
    path = Path(path).resolve()
    return {'path': path.relative_to(Path(root).resolve()).as_posix(),
            'bytes': path.stat().st_size, 'sha256': sha256(path)}


def verify_artifact(root, descriptor):
    if not isinstance(descriptor, dict):
        raise ValueError('Expected artifact descriptor')
    relative = descriptor.get('path')
    if not isinstance(relative, str) or not relative or '\\' in relative:
        raise ValueError('Expected relative artifact path')
    path = Path(relative)
    if path.is_absolute() or '..' in path.parts:
        raise ValueError('Unsafe artifact path')
    root = Path(root).resolve()
    candidate = root / path
    if candidate.is_symlink() or not candidate.resolve().is_relative_to(root) or not candidate.is_file():
        raise ValueError('Missing or unsafe artifact: ' + relative)
    if (candidate.stat().st_size != descriptor.get('bytes')
            or sha256(candidate) != descriptor.get('sha256')):
        raise ValueError('Artifact fingerprint mismatch: ' + relative)
    return candidate


def prediction_records(path):
    with gzip.open(path, 'rt', encoding='utf-8') as stream:
        for line in stream:
            yield json.loads(line)


def _counts(value, length):
    if (not isinstance(value, list) or len(value) != length
            or any(type(v) is not int or v < 0 for v in value)):
        raise ValueError('Counts must be nonnegative integers of the expected dimension')
    return value


def _metrics(matrix):
    tn, fp = matrix[0]
    fn, tp = matrix[1]
    total = tn + fp + fn + tp
    if total <= 0:
        raise ValueError('Empty confusion matrix')
    normal_recall = tn / (tn + fp) if tn + fp else None
    attack_recall = tp / (tp + fn) if tp + fn else None
    normal_f1 = 2 * tn / (2 * tn + fp + fn) if 2 * tn + fp + fn else 0.0
    attack_f1 = 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0
    return {'confusion_matrix': matrix, 'accuracy': (tn + tp) / total,
            'balanced_accuracy': ((normal_recall + attack_recall) / 2
                                  if normal_recall is not None and attack_recall is not None else None),
            'macro_f1': (normal_f1 + attack_f1) / 2,
            'attack_recall': attack_recall,
            'benign_false_positive_rate': fp / (tn + fp) if tn + fp else None,
            'attack_precision': tp / (tp + fp) if tp + fp else None,
            'support': [tn + fp, fn + tp]}


def _ranking_metrics(scored, group_weighted):
    tied = {}
    for margin, counts in scored:
        normal, attack = counts
        if group_weighted:
            total = normal + attack
            normal, attack = normal / total, attack / total
        values = tied.setdefault(margin, [0.0, 0.0])
        values[0] += normal
        values[1] += attack
    negative = sum(v[0] for v in tied.values())
    positive = sum(v[1] for v in tied.values())
    below = concordant = 0.0
    for score in sorted(tied):
        normal, attack = tied[score]
        concordant += attack * (below + .5 * normal)
        below += normal
    seen_negative = seen_positive = ap = 0.0
    for score in sorted(tied, reverse=True):
        normal, attack = tied[score]
        seen_negative += normal
        seen_positive += attack
        ap += attack * seen_positive / (seen_positive + seen_negative)
    return {'auroc': concordant / (negative * positive) if negative and positive else None,
            'attack_average_precision': ap / positive if positive else None}


def evaluate_records(records, *, original_labels=None, normal_label=None):
    """Retain each group's contradictory labels in row- and group-weighted metrics."""
    row = [[0, 0], [0, 0]]
    group = [[0.0, 0.0], [0.0, 0.0]]
    identities = set()
    rows = conflicts = 0
    scored = []
    conflict_row = [[0, 0], [0, 0]]
    conflict_group = [[0.0, 0.0], [0.0, 0.0]]
    conflict_rows = 0
    slices = {}
    if original_labels is not None:
        if (not isinstance(original_labels, list) or not original_labels
                or len(set(original_labels)) != len(original_labels)
                or normal_label not in original_labels):
            raise ValueError('Invalid original-label mapping')
        slices = {label: {'rows': 0, 'correct': 0} for label in original_labels}
    for record in records:
        identity = record.get('id')
        if (not isinstance(identity, str) or not re.fullmatch('[0-9a-f]{64}', identity)
                or identity in identities):
            raise ValueError('Invalid or duplicate payload identity')
        identities.add(identity)
        counts = _counts(record.get('counts'), 2)
        total = sum(counts)
        if not total:
            raise ValueError('Empty payload group')
        logits = record.get('logits')
        if (not isinstance(logits, list) or len(logits) != 2
                or any(type(v) not in (int, float) or not math.isfinite(v) for v in logits)):
            raise ValueError('Expected two finite logits')
        prediction = int(logits[1] > logits[0])
        margin = logits[1] - logits[0]
        if not math.isfinite(margin):
            raise ValueError('Logit difference is nonfinite')
        scored.append((margin, counts))
        for truth in (0, 1):
            row[truth][prediction] += counts[truth]
            group[truth][prediction] += counts[truth] / total
            if all(counts):
                conflict_row[truth][prediction] += counts[truth]
                conflict_group[truth][prediction] += counts[truth] / total
        rows += total
        conflicts += int(all(counts))
        conflict_rows += total if all(counts) else 0
        if original_labels is not None:
            subtypes = _counts(record.get('subtypes'), len(original_labels))
            normal = subtypes[original_labels.index(normal_label)]
            if [normal, sum(subtypes) - normal] != counts:
                raise ValueError('Original labels do not reconcile with binary counts')
            for label, count in zip(original_labels, subtypes):
                slices[label]['rows'] += count
                if prediction == int(label != normal_label):
                    slices[label]['correct'] += count
    if not identities:
        raise ValueError('No predictions')
    for summary in slices.values():
        summary['recall_of_supplied_binary_target'] = (summary['correct'] / summary['rows']
                                                      if summary['rows'] else None)
    return {'groups': len(identities), 'rows': rows, 'binary_conflicting_groups': conflicts,
            'row_weighted': {**_metrics(row), **_ranking_metrics(scored, False)},
            'group_weighted': {**_metrics(group), **_ranking_metrics(scored, True)},
            'conflicting_slice': {'groups': conflicts, 'rows': conflict_rows,
                'row_weighted': _metrics(conflict_row) if conflicts else None,
                'group_weighted': _metrics(conflict_group) if conflicts else None},
            'original_labels': slices,
            'interpretation': 'Scores classify supplied packet labels. Identical stored payload groups are not independent network flows or captures.'}
