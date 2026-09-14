"""Run the native packet-model checks on verified prepared bytes from both CSVs."""

import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import packet_study as study


def test_summary(result):
    return {'tests_run': result.testsRun, 'skipped': len(result.skipped),
            'failures': len(result.failures), 'errors': len(result.errors),
            'passed': result.testsRun >= 17 and not result.skipped and not result.failures and not result.errors}


def execute(data, upstream, initialization, output):
    data, upstream = Path(data).resolve(), Path(upstream).resolve()
    initialization, output = Path(initialization).resolve(), Path(output).absolute()
    if output.exists() or output.is_symlink():
        raise FileExistsError('Choose a fresh packet runtime output directory')
    output.mkdir(parents=True, exist_ok=False)
    receipt = {'status': 'running', 'scope': 'Native packet functional checks; synthetic loss targets, no benchmark training',
               'data': str(data), 'upstream': str(upstream), 'initialization': str(initialization),
               'runner_sha256': study.sha256(Path(__file__)),
               'test_source_sha256': study.sha256(ROOT / 'tests/test_packet_model.py')}
    try:
        from tools.train_packet_model import load_data
        import numpy as np
        arrays, manifest = load_data(data)
        receipt['data_manifest_sha256'] = study.sha256(data / 'manifest.json')
        receipt['source_sha256'] = {name: manifest['sources'][name]['sha256'] for name in ('cic', 'unsw')}
        receipt['initialization_sha256'] = study.sha256(initialization)
        if any(len(arrays[name]['payload']) < 2 for name in ('cic', 'unsw')):
            raise ValueError('The runtime gate requires at least two prepared payloads per source')
        with tempfile.TemporaryDirectory(prefix='netmamba-packet-runtime-') as temporary:
            cache = Path(temporary)
            for name in ('cic', 'unsw'):
                np.save(cache / f'{name}-payload.npy', np.asarray(arrays[name]['payload'][:2]), allow_pickle=False)
            variables = {'PACKET_MODEL_NATIVE_TESTS': '1', 'PACKET_MODEL_UPSTREAM': str(upstream),
                         'PACKET_MODEL_PRETRAIN': str(initialization), 'PACKET_MODEL_PAYLOAD_CACHE': str(cache),
                         'PACKET_MODEL_PROBE_REPORT': str(output / 'model-probe.json')}
            before = {key: os.environ.get(key) for key in variables}
            os.environ.update(variables)
            try:
                spec = importlib.util.spec_from_file_location('packet_runtime_suite', ROOT / 'tests/test_packet_model.py')
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                suite = unittest.defaultTestLoader.loadTestsFromModule(module)
                with (output / 'tests.log').open('w', encoding='utf-8') as log:
                    result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
                receipt['tests'] = test_summary(result)
            finally:
                for key, previous in before.items():
                    if previous is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = previous
        load_data(data)
        if study.sha256(data / 'manifest.json') != receipt['data_manifest_sha256']:
            raise ValueError('Prepared data manifest changed during the runtime check')
        if not receipt['tests']['passed']:
            raise ValueError('Native packet tests failed, skipped, or did not all execute; inspect tests.log')
        probe = study.read_json(output / 'model-probe.json')
        if probe.get('status') != 'passed' or probe.get('checkpoint_roundtrip_exact') is not True:
            raise ValueError('Missing successful native packet model probe')
        receipt['model_probe'] = study.artifact(output, output / 'model-probe.json')
        receipt['status'] = 'passed'
    except Exception as error:
        receipt['status'] = 'failed'
        receipt['error'] = f'{type(error).__name__}: {error}'
    if (output / 'tests.log').exists():
        receipt['test_log'] = study.artifact(output, output / 'tests.log')
    study.write_json(output / 'receipt.json', receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', required=True, type=Path, help='Prepared output from packet_data.py')
    parser.add_argument('--upstream', type=Path, default=ROOT / 'upstream/NetMambaPlus')
    parser.add_argument('--initialization', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    receipt = execute(args.data, args.upstream, args.initialization, args.output)
    print(json.dumps(receipt, indent=2))
    return 0 if receipt['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
