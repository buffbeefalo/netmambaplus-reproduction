import copy
import tempfile
import unittest
from pathlib import Path

import packet_study
from tools import train_packet_model as trainer


class FrozenProtocolTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.data = Path(self.temp.name)
        (self.data / 'manifest.json').write_text('{}')
        self.protocol = {
            'kind': 'netmambaplus_packet_study_v1', 'seed': 0, 'purpose': 'measured',
            'data_manifest_sha256': packet_study.sha256(self.data / 'manifest.json'),
            'source_sha256': {'cic': 'a'*64, 'unsw': 'b'*64},
            'code_sha256': {p: packet_study.sha256(trainer.ROOT / p) for p in
                ('packet_data.py', 'packet_model.py', 'packet_study.py', 'tools/train_packet_model.py')},
            'steps': 100, 'batch_size': 64, 'validation_interval': 100,
            'inference_batch_size': 128, 'cpu_threads': 2,
            'maximum_gpu_wall_seconds': 3600, 'gradient_clip_norm': 1.0,
            'optimizer': {'encoder_lr': .0001, 'head_lr': .001, 'weight_decay': .05},
            'arms': [{'name': 'cic_pretrained', 'sources': ['cic'], 'initialization': 'pretrained'}],
        }

    def test_valid_frozen_protocol(self):
        trainer.check_protocol(self.protocol, self.data)

    def test_code_fingerprint_change_rejected(self):
        self.protocol['code_sha256']['packet_data.py'] = 'c'*64
        with self.assertRaises(ValueError):
            trainer.check_protocol(self.protocol, self.data)

    def test_no_arm_can_escape_output_directory(self):
        for name in ('../escape', '/absolute', 'a/b', '', 'x\\y'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.protocol['arms'][0]['name'] = name
                trainer.check_protocol(self.protocol, self.data)

    def test_no_code_fingerprint_can_escape_repository(self):
        self.protocol['code_sha256']['../outside.py'] = 'f'*64
        with self.assertRaises(ValueError):
            trainer.check_protocol(self.protocol, self.data)

    def test_required_implementation_fingerprint_cannot_be_omitted(self):
        self.protocol['code_sha256'].pop('packet_model.py')
        with self.assertRaises(ValueError):
            trainer.check_protocol(self.protocol, self.data)

    def test_optimizer_and_resource_limits_must_be_finite_and_positive(self):
        for key, value in (('cpu_threads', True), ('seed', -1), ('gradient_clip_norm', 0),
                           ('maximum_gpu_wall_seconds', -1)):
            with self.subTest(key=key), self.assertRaises(ValueError):
                bad = copy.deepcopy(self.protocol); bad[key] = value
                trainer.check_protocol(bad, self.data)
        self.protocol['optimizer']['encoder_lr'] = float('nan')
        with self.assertRaises(ValueError):
            trainer.check_protocol(self.protocol, self.data)

    def test_measured_study_requires_at_least_100_updates(self):
        self.protocol['steps'] = self.protocol['validation_interval'] = 1
        with self.assertRaises(ValueError):
            trainer.check_protocol(self.protocol, self.data)

    def test_both_source_digests_required(self):
        self.protocol['source_sha256'].pop('unsw')
        with self.assertRaises(ValueError):
            trainer.check_protocol(self.protocol, self.data)


if __name__ == '__main__':
    unittest.main()
