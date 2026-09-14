"""Bind a packet-study protocol to prepared data and the current implementation."""

import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import packet_data
import packet_study as study

CODE = ('packet_data.py', 'packet_model.py', 'packet_study.py',
        'tools/train_packet_model.py', 'tools/freeze_packet_protocol.py',
        'tools/predict_packets.py')


def freeze(data, output, *, steps=1000, timing=None):
    if type(steps) is not int or steps not in range(100, 1001, 100):
        raise ValueError('Choose 100 through 1000 updates, in multiples of 100, before training')
    manifest = study.read_json(Path(data) / 'manifest.json')
    if manifest.get('status') != 'prepared':
        raise ValueError('Data preparation is incomplete')
    for source, expected in packet_data.REGISTERED_SOURCE_HASHES.items():
        observed = manifest['sources'][source]
        if observed.get('sha256') != expected or observed.get('matches_registered_source') is not True:
            raise ValueError('Measured study requires the registered original CSV: ' + source)
    protocol = {
        'kind': 'netmambaplus_packet_study_v1', 'purpose': 'measured',
        'frozen_at': datetime.now(timezone.utc).isoformat(),
        'data_manifest_sha256': study.sha256(Path(data) / 'manifest.json'),
        'source_sha256': {s: manifest['sources'][s]['sha256'] for s in ('cic', 'unsw')},
        'code_sha256': {p: study.sha256(ROOT / p) for p in CODE},
        'steps': steps, 'seed': 0, 'batch_size': 64, 'validation_interval': 100,
        'inference_batch_size': 128, 'cpu_threads': 2,
        'maximum_gpu_wall_seconds': 3600, 'gradient_clip_norm': 1.0,
        'optimizer': {'encoder_lr': .0001, 'head_lr': .001, 'weight_decay': .05},
        'precision': 'float32, no autocast, no TF32', 'schedule': 'constant learning rates',
        'labels': packet_data.LABELS,
        'class_mapping': {'benign': 0, 'attack': 1},
        'loss': 'Mean cross-entropy over each payload group observed binary-label proportions',
        'sampling': 'Uniform selected training groups with replacement; joint batches split equally by source',
        'selection': 'Validation group-weighted macro-F1; earliest tie; joint mean of the two source scores',
        'prediction': 'Native argmax; exact tie class 0; probabilities uncalibrated',
        'positions': 'Learned native 443-position table, same 378-index remap for released and fresh scratch tables; transfer includes positional weights',
        'controls': {'types': ['group_majority', 'byte_histogram_linear', 'group_metadata_linear'],
                     'code_binding': 'Separate control implementation digest frozen in the control fit manifest before its test inference',
                     'fit_partition': 'selected train only', 'C': 1, 'max_iter': 1000, 'tol': .0001,
                     'solver': 'lbfgs', 'scaler': 'training groups only',
                     'metadata': 'Group means ttl,total_len,t_delta; protocol fractions 1,6,17,other; no source feature'},
        'arms': [{'name': name + '_' + initialization, 'sources': sources,
                  'initialization': initialization}
                 for name, sources in (('cic', ['cic']), ('unsw', ['unsw']), ('joint', ['cic', 'unsw']))
                 for initialization in ('pretrained', 'scratch')],
        'limitations': ['Single seed and fixed update budget',
            'Exact payload separation does not establish independent captures or near-duplicate separation',
            'Released pretraining exposure is not established',
            'Supplied labels are not independently adjudicated operational maliciousness',
            'No claim about original flow benchmark improvement or production IDS readiness'],
    }
    if timing is not None:
        observation = study.read_json(timing)
        if steps != observation['chosen_updates_per_arm']:
            raise ValueError('Update budget differs from timing-only selection')
        protocol['timing_only_calibration'] = {'sha256': study.sha256(timing), 'observation': observation}
    study.write_json(output, protocol)
    return protocol


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--steps', type=int, default=1000)
    parser.add_argument('--timing', type=Path)
    args = parser.parse_args()
    freeze(args.data, args.output, steps=args.steps, timing=args.timing)
    print('Frozen protocol:', args.output, study.sha256(args.output))


if __name__ == '__main__':
    main()
