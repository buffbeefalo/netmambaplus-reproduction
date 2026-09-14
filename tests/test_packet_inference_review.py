"""Portable checks reject corrupted inference evidence even after reindexing."""

import gzip
import hashlib
import json
import math
from pathlib import Path
import tempfile
import unittest

import packet_study as study
from tools import review_packet_inference as review


class Evidence:
    def __init__(self, root):
        self.root = root
        (root / 'unlabeled').mkdir()
        (root / 'joint_pretrained').mkdir()
        self.manifest = {'sources': {}}
        self.protocol = {'source_sha256': {'cic': 'a' * 64, 'unsw': 'b' * 64},
                         'class_mapping': {'benign': 0, 'attack': 1}, 'inference_batch_size': 128}
        self.metadata = {'class_mapping': self.protocol['class_mapping'],
                         'study_metadata': {'arm': 'joint_pretrained', 'sources': ['cic', 'unsw'],
                                            'step': 1000, 'source_sha256': self.protocol['source_sha256']}}
        self.checkpoint = {'path': 'joint_pretrained/checkpoint-step-01000.pth',
                           'bytes': 123, 'sha256': 'c' * 64, 'step': 1000}
        self.predictions = {}
        self.receipts = {}
        self.agreement = {'status': 'class_predictions_verified', 'rows': 60,
                          'relative_tolerance': 1e-4, 'absolute_tolerance': 1e-6,
                          'strict_logit_tolerance_passed': False, 'sources': {},
                          'settings': {'NVIDIA_TF32_OVERRIDE': '0', 'batch_size': 128,
                                       'torch.backends.cuda.matmul.allow_tf32': False,
                                       'torch.backends.cudnn.allow_tf32': False,
                                       'batch_grouping': 'Each source separately, identical to measured evaluation'}}
        for source, count in [('cic', 50), ('unsw', 10)]:
            refs, preds = [], []
            for i in range(count):
                identity = hashlib.sha256(f'{source}-{i}'.encode()).hexdigest()
                refs.append({'id': identity, 'logits': [0.005, 2.0]})
            refs.sort(key=lambda r: r['id'])
            for i, record in enumerate(refs):
                # Passes NumPy's additive bound but fails the recorded math.isclose bound.
                logits = [0.005 + 1.2e-6 if source == 'cic' and i == 3 else 0.005, 2.0]
                weights = [math.exp(v - max(logits)) for v in logits]
                probabilities = [v / sum(weights) for v in weights]
                preds.append({'row_id': i, 'payload_sha256': record['id'],
                              'class_index': 1, 'class_name': 'attack', 'logits': logits,
                              'probabilities': probabilities, 'probability': probabilities[1],
                              'probability_kind': 'uncalibrated_softmax'})
            self.predictions[source] = preds
            self.compressed('joint_pretrained/test-' + source + '.jsonl.gz', refs)
            membership = hashlib.sha256(b''.join(bytes.fromhex(r['id']) for r in refs)).hexdigest()
            self.manifest['sources'][source] = {'splits': {'test': {
                'selected_groups': count, 'selected_membership_sha256': membership}}}
            self.agreement['sources'][source] = {'rows': count, 'class_agreements': count,
                'failed_rows': [3] if source == 'cic' else [],
                'strict_logit_tolerance_failures': int(source == 'cic'),
                'maximum_absolute_logit_difference': abs(0.005 + 1.2e-6 - 0.005) if source == 'cic' else 0.0}
            self.receipts[source] = self.receipt(count)
        self.receipts['default'] = self.receipt(60)
        self.write('manifest.json', self.manifest)
        self.protocol['data_manifest_sha256'] = study.sha256(root / 'manifest.json')
        self.write('protocol.json', self.protocol)
        self.metadata['study_metadata'].update(data_manifest_sha256=self.protocol['data_manifest_sha256'],
                                               protocol_sha256=study.sha256(root / 'protocol.json'))
        self.write('frozen-checkpoints.json', {'protocol_sha256': study.sha256(root / 'protocol.json'),
                   'selected_checkpoints': {'joint_pretrained': self.checkpoint}})
        self.write('joint_pretrained/training-receipt.json', {'selected_checkpoint': self.checkpoint})
        for name, failures in [('default', 39), ('override-only', 8)]:
            summary = {'status': 'numerical_tolerance_failed', 'rows': 60, 'class_agreements': 60,
                       'relative_tolerance': 1e-4, 'absolute_tolerance': 1e-6,
                       'logit_tolerance_failures': failures, 'failed_rows': list(range(failures)),
                       'maximum_absolute_logit_difference': 0.001}
            if name == 'override-only': summary['environment'] = {'NVIDIA_TF32_OVERRIDE': '0'}
            self.write('unlabeled/' + name + '-comparison.json', summary)
        self.sync()

    def receipt(self, count):
        return {'kind': 'netmambaplus_unlabeled_packet_inference_v1', 'schema_version': 1,
                'status': 'complete', 'stage': 'finished', 'input_rows': count,
                'validated_rows': count, 'predicted_rows': count, 'batch_size': 128,
                'all_rows_predicted': True, 'counts_finalized': True,
                'input_fully_validated': True, 'max_rows': None, 'ignored_metadata_columns': [],
                'class_mapping': self.protocol['class_mapping'], 'probability_kind': 'uncalibrated_softmax',
                'checkpoint': {k: self.checkpoint[k] for k in ['path', 'bytes', 'sha256']},
                'checkpoint_metadata': self.metadata,
                'code_sha256': {name: study.sha256(review.ROOT / name) for name in
                               ['packet_data.py', 'packet_model.py', 'tools/predict_packets.py']},
                'input': {'path': '/private/input.csv', 'bytes': 1, 'sha256': 'd' * 64,
                          'sha256_scope': 'entire_file'},
                'predictions': {'path': 'predictions.jsonl', 'bytes': 1, 'sha256': 'e' * 64}}

    def write(self, name, data):
        (self.root / name).write_text(json.dumps(data, sort_keys=True) + '\n')

    def compressed(self, name, records):
        raw = ''.join(json.dumps(r) + '\n' for r in records).encode()
        (self.root / name).write_bytes(gzip.compress(raw, mtime=0))
        return {'path': 'predictions.jsonl', 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

    def reindex(self):
        self.write('index.json', {'files': [study.artifact(self.root, p) for p in sorted(self.root.rglob('*'))
                                          if p.is_file() and p.name != 'index.json']})

    def sync(self):
        for source in ['cic', 'unsw']:
            name = 'unlabeled/' + source + '-predictions.jsonl.gz'
            self.receipts[source]['predictions'] = self.compressed(name, self.predictions[source])
            self.write('unlabeled/' + source + '-receipt.json', self.receipts[source])
            self.agreement['sources'][source]['compressed_predictions'] = study.artifact(
                self.root / 'unlabeled', self.root / name)
            self.agreement['sources'][source]['receipt'] = study.artifact(self.root / 'unlabeled',
                self.root / 'unlabeled' / (source + '-receipt.json'))
        self.write('unlabeled/default-receipt.json', self.receipts['default'])
        self.write('unlabeled/agreement.json', self.agreement)
        self.reindex()


class InferenceReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.evidence = Evidence(self.root)

    def test_class_agreement_does_not_hide_strict_numeric_failure(self):
        result = review.verify(self.root)
        self.assertEqual(result['status'], 'class_predictions_verified')
        self.assertEqual(result['class_agreements'], 60)
        self.assertFalse(result['strict_logit_tolerance_passed'])
        self.assertEqual(result['sources']['cic']['failed_rows'], [3])
        self.assertEqual(result['prior_comparisons']['default']['logit_tolerance_failures'], 39)

    def test_changed_compressed_bytes_fail_hash(self):
        path = self.root / 'unlabeled/cic-predictions.jsonl.gz'
        path.write_bytes(path.read_bytes() + b'x')
        with self.assertRaises(ValueError): review.verify(self.root)

    def test_false_class_rejected_with_fresh_hashes(self):
        self.evidence.predictions['cic'][0]['class_index'] = 0
        self.evidence.sync()
        with self.assertRaises(ValueError): review.verify(self.root)

    def test_wrong_softmax_rejected_with_fresh_hashes(self):
        self.evidence.predictions['cic'][0]['probabilities'] = [0.5, 0.5]
        self.evidence.sync()
        with self.assertRaises(ValueError): review.verify(self.root)

    def test_wrong_row_or_payload_rejected(self):
        self.evidence.predictions['unsw'][0]['payload_sha256'] = '0' * 64
        self.evidence.sync()
        with self.assertRaises(ValueError): review.verify(self.root)

    def test_receipt_uncompressed_hash_is_verified(self):
        self.evidence.receipts['cic']['predictions']['sha256'] = '0' * 64
        self.evidence.write('unlabeled/cic-receipt.json', self.evidence.receipts['cic'])
        self.evidence.agreement['sources']['cic']['receipt'] = study.artifact(self.root / 'unlabeled',
            self.root / 'unlabeled/cic-receipt.json')
        self.evidence.write('unlabeled/agreement.json', self.evidence.agreement)
        self.evidence.reindex()
        with self.assertRaises(ValueError): review.verify(self.root)

    def test_receipt_checkpoint_binding_rejected(self):
        self.evidence.receipts['cic']['checkpoint']['sha256'] = '0' * 64
        self.evidence.sync()
        with self.assertRaises(ValueError): review.verify(self.root)

    def test_tolerance_cannot_be_loosened(self):
        self.evidence.agreement['absolute_tolerance'] = 1e-3
        self.evidence.sync()
        with self.assertRaises(ValueError): review.verify(self.root)

    def test_tolerance_pass_cannot_be_claimed(self):
        self.evidence.agreement['strict_logit_tolerance_passed'] = True
        self.evidence.sync()
        with self.assertRaises(ValueError): review.verify(self.root)

    def test_prior_failure_summary_cannot_lose_rows(self):
        path = self.root / 'unlabeled/default-comparison.json'
        data = study.read_json(path)
        data['failed_rows'].pop()
        self.evidence.write('unlabeled/default-comparison.json', data)
        self.evidence.reindex()
        with self.assertRaises(ValueError): review.verify(self.root)


if __name__ == '__main__':
    unittest.main()
