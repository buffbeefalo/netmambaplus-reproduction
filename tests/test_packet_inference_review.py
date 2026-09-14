"""Portable checks reject corrupted inference evidence even after reindexing."""

import gzip
import hashlib
import json
import math
import copy
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import packet_study as study
from tools import review_packet_inference as review


class Evidence:
    def __init__(self, root, cic_count=50, unsw_count=10):
        self.root = root
        (root / 'unlabeled').mkdir()
        (root / 'joint_pretrained').mkdir()
        self.manifest = {'sources': {}}
        self.protocol = {'source_sha256': {'cic': 'a' * 64, 'unsw': 'b' * 64},
                         'class_mapping': {'benign': 0, 'attack': 1}, 'inference_batch_size': 128,
                         'code_sha256': {name: hashlib.sha256(('historical ' + name).encode()).hexdigest()
                                         for name in ['packet_data.py', 'packet_model.py',
                                                      'tools/predict_packets.py', 'tools/train_packet_model.py']}}
        self.metadata = {'class_mapping': self.protocol['class_mapping'],
                         'study_metadata': {'arm': 'joint_pretrained', 'sources': ['cic', 'unsw'],
                                            'step': 1000, 'source_sha256': self.protocol['source_sha256']}}
        self.checkpoint = {'path': 'joint_pretrained/checkpoint-step-01000.pth',
                           'bytes': 123, 'sha256': 'c' * 64, 'step': 1000}
        self.predictions = {}
        self.receipts = {}
        total = cic_count + unsw_count
        self.agreement = {'status': 'class_predictions_verified', 'rows': total,
                          'relative_tolerance': 1e-4, 'absolute_tolerance': 1e-6,
                          'strict_logit_tolerance_passed': False, 'sources': {},
                          'settings': {'NVIDIA_TF32_OVERRIDE': '0', 'batch_size': 128,
                                       'torch.backends.cuda.matmul.allow_tf32': False,
                                       'torch.backends.cudnn.allow_tf32': False,
                                       'batch_grouping': 'Each source separately, identical to measured evaluation'}}
        for source, count in [('cic', cic_count), ('unsw', unsw_count)]:
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
        self.receipts['default'] = self.receipt(total)
        self.write('manifest.json', self.manifest)
        self.protocol['data_manifest_sha256'] = study.sha256(root / 'manifest.json')
        self.write('protocol.json', self.protocol)
        self.metadata['study_metadata'].update(data_manifest_sha256=self.protocol['data_manifest_sha256'],
                                               protocol_sha256=study.sha256(root / 'protocol.json'))
        self.write('frozen-checkpoints.json', {'protocol_sha256': study.sha256(root / 'protocol.json'),
                   'selected_checkpoints': {'joint_pretrained': self.checkpoint}})
        self.write('joint_pretrained/training-receipt.json', {'selected_checkpoint': self.checkpoint})
        for name, failures in [('default', 39), ('override-only', 8)]:
            summary = {'status': 'numerical_tolerance_failed', 'rows': total, 'class_agreements': total,
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
                'code_sha256': {name: self.protocol['code_sha256'][name] for name in
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

    def rebind_protocol(self):
        self.write('protocol.json', self.protocol)
        digest = study.sha256(self.root / 'protocol.json')
        self.metadata['study_metadata']['protocol_sha256'] = digest
        frozen = study.read_json(self.root / 'frozen-checkpoints.json')
        frozen['protocol_sha256'] = digest
        self.write('frozen-checkpoints.json', frozen)
        self.sync()

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

    def add_post_study(self):
        receipt = copy.deepcopy(self.receipts['default'])
        receipt.update(status='capped', all_rows_predicted=False, max_rows=128, predicted_rows=128)
        receipt['code_sha256']['tools/predict_packets.py'] = hashlib.sha256(b'portable predictor').hexdigest()
        predictions = copy.deepcopy(self.predictions['cic'][:128])
        for i, record in enumerate(predictions):
            record['logits'] = [0.005, 2.0 + (2e-6 if i == 5 else 0)]
            weights = [math.exp(v - max(record['logits'])) for v in record['logits']]
            record['probabilities'] = [v / sum(weights) for v in weights]
            record['probability'] = record['probabilities'][record['class_index']]
        self.post = {'status': 'class_predictions_verified',
                     'historical_implementation_revision': '7eeb4980eea9fd5ad17bfacd29ed88687cb3e1e5',
                     'receipt': receipt, 'predictions': predictions,
                     'comparison': {'relative_tolerance': 1e-4, 'absolute_tolerance': 1e-6,
                                    'rows': 128, 'class_agreements': 128, 'failed_rows': [],
                                    'strict_logit_tolerance_passed': True,
                                    'maximum_absolute_logit_difference': abs(2.0 + 2e-6 - 2.0)}}
        self.sync_post()

    def sync_post(self, update_predictions_hash=True):
        if update_predictions_hash:
            fields = ['row_id', 'payload_sha256', 'class_index', 'class_name', 'logits',
                      'probabilities', 'probability', 'probability_kind']
            raw = ''.join(json.dumps({k: r[k] for k in fields}, separators=(',', ':'), allow_nan=False) + '\n'
                          for r in self.post['predictions']).encode()
            self.post['receipt']['predictions'] = {'path': 'predictions.jsonl', 'bytes': len(raw),
                                                   'sha256': hashlib.sha256(raw).hexdigest()}
        self.write('post-study-io-check.json', self.post)
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
        self.assertEqual(result['post_study_io'], {'status': 'not_recorded'})

    def test_changed_compressed_bytes_fail_hash(self):
        path = self.root / 'unlabeled/cic-predictions.jsonl.gz'
        path.write_bytes(path.read_bytes() + b'x')
        with self.assertRaises(ValueError): review.verify(self.root)

    def test_historical_protocol_hashes_survive_newer_current_implementation(self):
        with tempfile.TemporaryDirectory() as directory:
            current = Path(directory)
            for name, historical in self.evidence.receipts['cic']['code_sha256'].items():
                path = current / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('# A later portable implementation.\n')
                self.assertNotEqual(study.sha256(path), historical)
            with mock.patch.object(review, 'ROOT', current):
                self.assertEqual(review.verify(self.root)['class_agreements'], 60)

    def test_receipt_implementation_drift_is_rejected_with_fresh_hashes(self):
        self.evidence.receipts['cic']['code_sha256']['tools/predict_packets.py'] = '0' * 64
        self.evidence.sync()
        with self.assertRaisesRegex(ValueError, 'implementation hash mismatch'):
            review.verify(self.root)

    def test_missing_or_malformed_protocol_implementation_hashes_are_rejected(self):
        valid = self.evidence.protocol['code_sha256'].copy()
        missing_predictor = {name: digest for name, digest in valid.items() if name != 'tools/predict_packets.py'}
        cases = [None, [], {}, missing_predictor, valid | {'tools/predict_packets.py': None},
                 valid | {'tools/predict_packets.py': 'not-a-digest'},
                 valid | {'tools/predict_packets.py': 'F' * 64}]
        for binding in cases:
            with self.subTest(binding=binding):
                self.evidence.protocol['code_sha256'] = binding
                self.evidence.rebind_protocol()
                with self.assertRaisesRegex(ValueError, 'protocol implementation'):
                    review.verify(self.root)
        del self.evidence.protocol['code_sha256']
        self.evidence.rebind_protocol()
        with self.assertRaisesRegex(ValueError, 'protocol implementation'):
            review.verify(self.root)

    def test_changed_protocol_implementation_hash_is_rejected_against_retained_receipts(self):
        self.evidence.protocol['code_sha256']['tools/predict_packets.py'] = '0' * 64
        self.evidence.rebind_protocol()
        with self.assertRaisesRegex(ValueError, 'implementation hash mismatch'):
            review.verify(self.root)

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


class PostStudyIOReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.evidence = Evidence(self.root, cic_count=150)
        self.evidence.add_post_study()

    def test_capped_check_preserves_original_full_test_numeric_failure(self):
        result = review.verify(self.root)
        self.assertEqual(result['rows'], 160)
        self.assertFalse(result['strict_logit_tolerance_passed'])
        post = result['post_study_io']
        self.assertEqual(post['class_agreements'], 128)
        self.assertEqual(post['validated_rows'], 160)
        self.assertTrue(post['strict_logit_tolerance_passed'])
        self.assertEqual(post['status'], 'class_predictions_verified')

    def test_embedded_jsonl_hash_must_reconstruct_exactly(self):
        self.evidence.post['receipt']['predictions']['sha256'] = '0' * 64
        self.evidence.sync_post(update_predictions_hash=False)
        with self.assertRaisesRegex(ValueError, 'prediction fingerprint'):
            review.verify_post_study_io(self.root)

    def test_capped_receipt_must_validate_entire_original_input(self):
        self.evidence.post['receipt']['validated_rows'] = 128
        self.evidence.sync_post()
        with self.assertRaises(ValueError): review.verify_post_study_io(self.root)

    def test_checkpoint_and_full_input_identities_cannot_change(self):
        for field in ['checkpoint', 'input']:
            with self.subTest(field=field):
                original = self.evidence.post['receipt'][field]['sha256']
                self.evidence.post['receipt'][field]['sha256'] = '0' * 64
                self.evidence.sync_post()
                with self.assertRaises(ValueError): review.verify_post_study_io(self.root)
                self.evidence.post['receipt'][field]['sha256'] = original

    def test_post_study_record_must_match_evidence_index(self):
        path = self.root / 'post-study-io-check.json'
        path.write_bytes(path.read_bytes() + b' ')
        with self.assertRaisesRegex(ValueError, 'Artifact fingerprint mismatch'):
            review.verify_post_study_io(self.root)

    def test_payload_prefix_must_match_primary_records(self):
        self.evidence.post['predictions'][0]['payload_sha256'] = '0' * 64
        self.evidence.sync_post()
        with self.assertRaises(ValueError): review.verify_post_study_io(self.root)

    def test_new_predictor_cannot_change_model_code_declaration(self):
        self.evidence.post['receipt']['code_sha256']['packet_model.py'] = '0' * 64
        self.evidence.sync_post()
        with self.assertRaises(ValueError): review.verify_post_study_io(self.root)

    def test_embedded_class_and_probability_are_checked(self):
        for field, value in [('class_name', 'benign'), ('probability', 0.5)]:
            with self.subTest(field=field):
                original = self.evidence.post['predictions'][0][field]
                self.evidence.post['predictions'][0][field] = value
                self.evidence.sync_post()
                with self.assertRaises(ValueError): review.verify_post_study_io(self.root)
                self.evidence.post['predictions'][0][field] = original

    def test_changed_comparison_maximum_or_pass_flag_is_rejected(self):
        for field, value in [('maximum_absolute_logit_difference', 0.0),
                             ('strict_logit_tolerance_passed', False)]:
            with self.subTest(field=field):
                original = self.evidence.post['comparison'][field]
                self.evidence.post['comparison'][field] = value
                self.evidence.sync_post()
                with self.assertRaises(ValueError): review.verify_post_study_io(self.root)
                self.evidence.post['comparison'][field] = original


if __name__ == '__main__':
    unittest.main()
