"""Run a frozen, separate packet-classification study through native NetMamba+."""

import argparse
import gzip
import hashlib
import json
import math
import os
import platform
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import packet_study as study


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def load_data(directory):
    """Verify the current prepared bytes and their declared grouping before use.

    Arrays remain read-only memory maps, not immutable snapshots. Call again
    after execution to detect persisted file changes; raw CSV fingerprints are
    recorded identities, not a fresh rescan of those source files.
    """
    import hashlib
    import re
    import numpy as np
    import packet_data

    def require(condition, message):
        if not condition:
            raise ValueError(message)

    directory = Path(directory)
    manifest = study.read_json(directory / 'manifest.json')
    require(isinstance(manifest, dict) and manifest.get('status') == 'prepared'
            and type(manifest.get('schema_version')) is int and manifest['schema_version'] == 1,
            'Packet data has not completed the supported preparation format')
    require(manifest.get('labels') == packet_data.LABELS, 'Prepared original-label order changed')
    require(isinstance(manifest.get('sources'), dict) and set(manifest['sources']) == {'cic', 'unsw'},
            'Prepared source inventory must contain exactly CIC and UNSW')
    schema, contract = manifest.get('schema'), manifest.get('input_contract')
    require(isinstance(schema, dict) and schema.get('columns') == packet_data.CSV_COLUMNS
            and schema.get('metadata_columns') == packet_data.METADATA_COLUMNS
            and schema.get('payload_byte_columns') == 1500, 'Prepared CSV schema changed')
    require(isinstance(contract, dict) and contract.get('payload_length') == 1500
            and contract.get('dtype') == 'uint8' and contract.get('model_inputs') == ['payload']
            and contract.get('excluded_columns') == packet_data.METADATA_COLUMNS
            and contract.get('stored_zeros') == 'retained', 'Prepared payload input contract changed')
    split_record, selection = manifest.get('split'), manifest.get('selection')
    require(isinstance(split_record, dict) and type(split_record.get('seed')) is int
            and split_record['seed'] >= 0 and split_record.get('names') == list(packet_data.SPLIT_NAMES)
            and split_record.get('target_group_fractions') == [0.7, 0.15, 0.15],
            'Invalid deterministic split declaration')
    require(isinstance(selection, dict) and isinstance(selection.get('caps'), dict)
            and set(selection['caps']) == set(packet_data.SPLIT_NAMES)
            and all(type(value) is int and value > 0 for value in selection['caps'].values())
            and selection.get('order') == 'ascending raw payload SHA256'
            and selection.get('uses_labels_metadata_or_multiplicity') is False,
            'Invalid fixed selection caps or ordering')
    names = ('payload', 'hashes', 'counts', 'subtypes', 'split', 'selected')
    expected_files = {name + '.npy' for name in names} | {'metadata.csv'}
    dtypes = {'payload': np.dtype('uint8'), 'hashes': np.dtype('V32'), 'counts': np.dtype('int64'),
              'subtypes': np.dtype('int64'), 'split': np.dtype('uint8'), 'selected': np.dtype('bool')}
    data = {}
    for source in ('cic', 'unsw'):
        record = manifest['sources'][source]
        require(isinstance(record, dict), 'Malformed prepared source record: ' + source)
        observed = record.get('sha256')
        require(isinstance(observed, str) and re.fullmatch('[0-9a-f]{64}', observed)
                and record.get('registered_source_sha256') == packet_data.REGISTERED_SOURCE_HASHES[source]
                and type(record.get('matches_registered_source')) is bool
                and record['matches_registered_source'] == (observed == packet_data.REGISTERED_SOURCE_HASHES[source]),
                'Inconsistent registered source identity: ' + source)
        files = record.get('files')
        require(isinstance(files, dict) and set(files) == expected_files,
                'Prepared file inventory has a missing or extra file: ' + source)
        for filename, reference in files.items():
            require(isinstance(reference, dict) and reference.get('path') == f'{source}/{filename}',
                    'Prepared fingerprint path does not bind the loaded source/file: ' + source + '/' + filename)
            require(type(reference.get('bytes')) is int and reference['bytes'] > 0,
                    'Invalid prepared artifact byte count: ' + source + '/' + filename)
            study.verify_artifact(directory, reference)
        arrays = {name: np.load(directory / source / (name + '.npy'), mmap_mode='r', allow_pickle=False)
                  for name in names}
        require(arrays['hashes'].ndim == 1 and len(arrays['hashes']) > 0,
                'Prepared hashes need a nonempty one-dimensional shape')
        groups = len(arrays['hashes'])
        shapes = {'payload': (groups, 1500), 'hashes': (groups,), 'counts': (groups, 2),
                  'subtypes': (groups, len(packet_data.LABELS[source])), 'split': (groups,), 'selected': (groups,)}
        for name, array in arrays.items():
            reference = files[name + '.npy']
            require(array.dtype == dtypes[name] and reference.get('dtype') == str(array.dtype),
                    'Invalid prepared array dtype: ' + source + '/' + name)
            declared_shape = reference.get('shape')
            require(array.shape == shapes[name] and isinstance(declared_shape, list)
                    and all(type(value) is int for value in declared_shape)
                    and declared_shape == list(array.shape), 'Invalid prepared array shape: ' + source + '/' + name)
        counts, subtypes = arrays['counts'], arrays['subtypes']
        require(not np.any(counts < 0) and not np.any(subtypes < 0), 'Negative prepared label counts')
        rows = record.get('rows')
        require(type(rows) is int and 0 < rows <= np.iinfo(np.int64).max // len(packet_data.LABELS[source])
                and not np.any(counts > rows) and not np.any(subtypes > rows), 'Invalid prepared source rows/counts')
        require(np.array_equal(counts[:, 0], subtypes[:, 0])
                and np.array_equal(counts[:, 1], subtypes[:, 1:].sum(axis=1)),
                'Prepared binary counts do not reconcile with original-label subtypes')
        require(not np.any(counts.sum(axis=1) <= 0), 'Empty prepared payload group counts')
        require(sum(int(value) for value in counts.sum(axis=1)) == rows,
                'Prepared source rows do not reconcile with the array counts')
        hashes = [value.tobytes() for value in arrays['hashes']]
        require(all(left < right for left, right in zip(hashes, hashes[1:])),
                'Prepared payload identities must be unique and sorted')
        for index, expected in enumerate(hashes):
            require(hashlib.sha256(arrays['payload'][index].tobytes()).digest() == expected,
                    f'Prepared payload hash identity mismatch: {source} group {index}')
        expected_splits = np.fromiter((packet_data.split_for_hash(value.hex(), seed=split_record['seed'])
                                      for value in hashes), dtype=np.uint8, count=groups)
        require(np.array_equal(arrays['split'], expected_splits), 'Prepared split violates the deterministic hash rule')
        expected_selected = np.zeros(groups, dtype=np.bool_)
        for split, name in enumerate(packet_data.SPLIT_NAMES):
            expected_selected[np.flatnonzero(expected_splits == split)[:selection['caps'][name]]] = True
        require(np.array_equal(arrays['selected'], expected_selected), 'Prepared selection differs from fixed hash-order caps')

        def support(mask):
            chosen_counts, chosen_subtypes = counts[mask], subtypes[mask]
            return {'groups': int(mask.sum()), 'rows': int(chosen_counts.sum()),
                    'binary_counts': chosen_counts.sum(axis=0).tolist(),
                    'label_counts': dict(zip(packet_data.LABELS[source], chosen_subtypes.sum(axis=0).tolist())),
                    'label_group_counts': dict(zip(packet_data.LABELS[source], (chosen_subtypes > 0).sum(axis=0).tolist())),
                    'binary_conflicting_groups': int(np.all(chosen_counts > 0, axis=1).sum()),
                    'membership_sha256': hashlib.sha256(arrays['hashes'][mask].tobytes()).hexdigest()}

        require(all(record.get(key) == value for key, value in support(np.ones(groups, dtype=bool)).items()),
                'Prepared source support differs from the actual arrays: ' + source)
        require(isinstance(record.get('splits'), dict) and set(record['splits']) == set(packet_data.SPLIT_NAMES),
                'Prepared split support inventory changed')
        for split, name in enumerate(packet_data.SPLIT_NAMES):
            expected_support = support(arrays['split'] == split)
            expected_support.update({'selected_' + key: value for key, value in
                                     support((arrays['split'] == split) & arrays['selected']).items()})
            declared_support = record['splits'][name]
            require(isinstance(declared_support, dict)
                    and all(declared_support.get(key) == value for key, value in expected_support.items()),
                    'Prepared split support/membership differs from the actual arrays: ' + source + '/' + name)
            indices = np.flatnonzero((arrays['split'] == split) & arrays['selected'])
            if not len(indices) or np.any(arrays['counts'][indices].sum(axis=0) <= 0):
                raise ValueError(f'{source} split {split} lacks binary support')
            arrays[split] = indices
        data[source] = arrays
    common, left, right = np.intersect1d(data['cic']['hashes'], data['unsw']['hashes'],
                                        return_indices=True)
    if len(common) and np.any(data['cic']['split'][left] != data['unsw']['split'][right]):
        raise ValueError('Shared packet payloads cross source splits')
    return data, manifest


def check_protocol(protocol, data_directory):
    if protocol.get('kind') != 'netmambaplus_packet_study_v1':
        raise ValueError('Not a frozen packet-study protocol')
    if study.sha256(Path(data_directory) / 'manifest.json') != protocol['data_manifest_sha256']:
        raise ValueError('Prepared data manifest changed')
    hashes = protocol.get('code_sha256')
    required = {'packet_data.py', 'packet_model.py', 'packet_study.py', 'tools/train_packet_model.py'}
    if not isinstance(hashes, dict) or not required.issubset(hashes):
        raise ValueError('Protocol must fingerprint the complete study implementation')
    for relative, expected in hashes.items():
        path = Path(relative)
        if (not relative or path.is_absolute() or '..' in path.parts or '\\' in relative
                or not (ROOT / path).resolve().is_relative_to(ROOT)):
            raise ValueError('Unsafe protocol code path')
        if study.sha256(ROOT / relative) != expected:
            raise ValueError('Study implementation changed: ' + relative)
    for name in ('steps', 'batch_size', 'validation_interval', 'inference_batch_size', 'cpu_threads'):
        if type(protocol.get(name)) is not int or protocol[name] <= 0:
            raise ValueError('Invalid protocol integer: ' + name)
    if protocol['batch_size'] % 2 or protocol['steps'] % protocol['validation_interval']:
        raise ValueError('Joint batches must divide evenly and the final step must be validated')
    if type(protocol.get('seed')) is not int or not 0 <= protocol['seed'] < 2**63:
        raise ValueError('Invalid random seed')
    if protocol.get('purpose') not in ('measured', 'mechanical'):
        raise ValueError('Protocol must state measured or mechanical purpose')
    if protocol['purpose'] == 'measured' and protocol['steps'] < 100:
        raise ValueError('Measured packet study requires at least 100 genuine-label updates')
    for name in ('maximum_gpu_wall_seconds', 'gradient_clip_norm'):
        value = protocol.get(name)
        if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
            raise ValueError('Invalid protocol resource or gradient limit')
    optimizer = protocol.get('optimizer', {})
    for name in ('encoder_lr', 'head_lr', 'weight_decay'):
        value = optimizer.get(name)
        if (type(value) not in (int, float) or not math.isfinite(value)
                or (value < 0 if name == 'weight_decay' else value <= 0)):
            raise ValueError('Invalid AdamW parameter: ' + name)
    sources = protocol.get('source_sha256')
    if (not isinstance(sources, dict) or set(sources) != {'cic', 'unsw'}
            or any(type(value) is not str or not re.fullmatch('[0-9a-f]{64}', value)
                   for value in sources.values())):
        raise ValueError('Both actual source SHA-256 digests are required')
    arms = protocol.get('arms')
    if not isinstance(arms, list) or not arms or len({a['name'] for a in arms}) != len(arms):
        raise ValueError('Missing or duplicate study arms')
    for arm in arms:
        if (type(arm.get('name')) is not str or not re.fullmatch('[a-z][a-z0-9_]*', arm['name'])
                or arm.get('sources') not in (['cic'], ['unsw'], ['cic', 'unsw'])
                or arm.get('initialization') not in ('pretrained', 'scratch')):
            raise ValueError('Invalid source/initialization arm')


def records_from_model(model, arrays, indices, batch_size):
    import numpy as np
    import torch
    import packet_model
    model.eval()
    device = next(model.parameters()).device
    with torch.inference_mode():
        for offset in range(0, len(indices), batch_size):
            ids = indices[offset:offset + batch_size]
            payload = torch.from_numpy(np.array(arrays['payload'][ids], copy=True)).to(device)
            logits = packet_model.forward_payload(model, payload)['logits']
            if logits.shape != (len(ids), 2) or not torch.isfinite(logits).all().item():
                raise ValueError('Incomplete or nonfinite native packet inference')
            values = logits.cpu().tolist()
            for index, scores in zip(ids, values):
                yield {'id': arrays['hashes'][index].tobytes().hex(),
                       'counts': arrays['counts'][index].tolist(),
                       'subtypes': arrays['subtypes'][index].tolist(), 'logits': scores}


def evaluate(model, arrays, source, split, batch_size, destination=None):
    import packet_data
    records = records_from_model(model, arrays, arrays[split], batch_size)
    if destination is not None:
        path = Path(destination)
        with path.open('xb') as raw, gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0) as zipped:
            for record in records:
                zipped.write((json.dumps(record, separators=(',', ':'), allow_nan=False) + '\n').encode())
        records = study.prediction_records(path)
    return study.evaluate_records(records, original_labels=packet_data.LABELS[source],
                                  normal_label='BENIGN' if source == 'cic' else 'normal')


def parameter_fingerprints(model):
    import hashlib
    import torch
    hashes = {}
    for name, parameter in model.named_parameters():
        if not torch.isfinite(parameter).all().item():
            raise ValueError('Nonfinite native parameter: ' + name)
        hashes[name] = hashlib.sha256(parameter.detach().cpu().contiguous().numpy().tobytes()).hexdigest()
    return hashes


def run_arm(arm, args, protocol, protocol_hash, data, started):
    import numpy as np
    import torch
    import packet_model
    path = args.output / arm['name']
    path.mkdir()
    model, provenance = packet_model.build_model(args.upstream,
        initialization=args.initialization if arm['initialization'] == 'pretrained' else None,
        seed=protocol['seed'], device='cuda')
    initial_hashes = parameter_fingerprints(model)
    torch.manual_seed(protocol['seed'])
    optimizer = torch.optim.AdamW([
        {'params': [p for name, p in model.named_parameters() if name != 'head.weight'],
         'lr': protocol['optimizer']['encoder_lr']},
        {'params': [model.head.weight], 'lr': protocol['optimizer']['head_lr']},
    ], weight_decay=protocol['optimizer']['weight_decay'])
    generator = np.random.default_rng(protocol['seed'])
    batch_stream = hashlib.sha256()
    presentations = {source: 0 for source in arm['sources']}
    observed = {source: set() for source in arm['sources']}
    history = []
    best = None
    best_score = -1.0
    gradient_evidence = None
    train_start = time.monotonic()
    with (path / 'training.jsonl').open('x', encoding='utf-8') as log:
        for step in range(1, protocol['steps'] + 1):
            if time.monotonic() - started > protocol['maximum_gpu_wall_seconds']:
                raise RuntimeError('Frozen total GPU wall-time budget exhausted; run remains incomplete')
            model.train()
            payloads, targets = [], []
            for source in arm['sources']:
                n = protocol['batch_size'] // len(arm['sources'])
                indices = generator.choice(data[source][0], size=n, replace=True)
                batch_stream.update(source.encode('ascii') + b'\0' + data[source]['hashes'][indices].tobytes())
                counts = np.asarray(data[source]['counts'][indices], dtype=np.float64)
                targets.append(counts / counts.sum(axis=1, keepdims=True))
                payloads.append(np.asarray(data[source]['payload'][indices]))
                presentations[source] += n
                observed[source].update(int(i) for i in indices)
            payload = torch.from_numpy(np.concatenate(payloads)).cuda()
            truth = torch.tensor(np.concatenate(targets), dtype=torch.float32, device='cuda')
            optimizer.zero_grad(set_to_none=True)
            logits = packet_model.forward_payload(model, payload)['logits']
            loss = -(truth * torch.log_softmax(logits, dim=1)).sum(dim=1).mean()
            if not torch.isfinite(loss).item():
                raise ValueError('Nonfinite supervised packet loss')
            loss.backward()
            norm = torch.nn.utils.clip_grad_norm_(model.parameters(), protocol['gradient_clip_norm'],
                                                  error_if_nonfinite=True)
            if step == 1:
                norms = {name: parameter.grad.norm().item() for name, parameter in model.named_parameters()
                         if parameter.grad is not None}
                if not (norms.get('head.weight', 0) > 0 and norms.get('byte_embed.proj.weight', 0) > 0
                        and all(any(value > 0 for name, value in norms.items()
                                    if name.startswith(f'encoder_blocks.{i}.')) for i in range(4))):
                    raise ValueError('CSV targets did not backpropagate through the native encoder')
                gradient_evidence = norms
            optimizer.step()
            observation = {'step': step, 'loss': loss.item(), 'unclipped_gradient_norm': norm.item(),
                           'elapsed_seconds': time.monotonic() - train_start}
            log.write(json.dumps(observation, allow_nan=False) + '\n')
            if step % protocol['validation_interval'] == 0:
                measured = {source: evaluate(model, data[source], source, 1, protocol['inference_batch_size'])
                            for source in arm['sources']}
                score = sum(m['group_weighted']['macro_f1'] for m in measured.values()) / len(measured)
                validation = {'step': step, 'selection_score': score, 'sources': measured}
                history.append(validation)
                if score > best_score:
                    best_score = score
                    best_path = path / f'checkpoint-step-{step:05d}.pth'
                    metadata = {'data_manifest_sha256': protocol['data_manifest_sha256'],
                                'protocol_sha256': protocol_hash, 'source_sha256': protocol['source_sha256'],
                                'arm': arm['name'], 'sources': arm['sources'], 'seed': protocol['seed'],
                                'step': step, 'selection': validation}
                    packet_model.save_checkpoint(best_path, model, provenance, metadata)
                    best = {'path': best_path.relative_to(args.output).as_posix(),
                            'sha256': study.sha256(best_path), 'bytes': best_path.stat().st_size,
                            'step': step, 'selection_score': score}
                print(json.dumps({'arm': arm['name'], 'step': step, 'loss': loss.item(),
                                  'validation_group_macro_f1': score, 'best': best_score}), flush=True)
                log.flush()
    final_hashes = parameter_fingerprints(model)
    steps = [int(state['step'].item()) for state in optimizer.state.values()]
    if not steps or any(step != protocol['steps'] for step in steps):
        raise ValueError('Optimizer counters do not establish the completed budget')
    changed = [name for name in initial_hashes if initial_hashes[name] != final_hashes[name]]
    if 'head.weight' not in changed or not any(name.startswith('encoder_blocks.') for name in changed):
        raise ValueError('Supervised packet training did not change the native model')
    result = {'status': 'trained', 'arm': arm, 'steps': protocol['steps'],
              'elapsed_seconds': time.monotonic() - train_start, 'provenance': provenance,
              'group_presentations': presentations, 'distinct_training_groups_observed': {s: len(v) for s, v in observed.items()},
              'training_batch_stream_sha256': batch_stream.hexdigest(),
              'first_step_gradient_norms': gradient_evidence,
              'optimizer_step_range': [min(steps), max(steps)], 'optimizer_parameter_states': len(steps),
              'initial_parameter_sha256': initial_hashes, 'final_parameter_sha256': final_hashes,
              'changed_parameter_tensors': changed, 'validation_history': history,
              'selected_checkpoint': best, 'training_log': study.artifact(args.output, path / 'training.jsonl')}
    study.write_json(path / 'training-receipt.json', result)
    del model, optimizer
    torch.cuda.empty_cache()
    return result


def run(args):
    import numpy as np
    import torch
    import packet_model
    protocol = study.read_json(args.protocol)
    check_protocol(protocol, args.data)
    protocol_hash = study.sha256(args.protocol)
    if args.output.exists():
        raise ValueError('Choose a fresh output directory')
    data, manifest = load_data(args.data)
    for source in ('cic', 'unsw'):
        if manifest['sources'][source]['sha256'] != protocol['source_sha256'][source]:
            raise ValueError('Protocol source digest does not match prepared data: ' + source)
    args.output.mkdir(parents=True)
    study.write_json(args.output / 'protocol.json', protocol)
    torch.set_num_threads(protocol['cpu_threads'])
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    started = time.monotonic()
    runtime = {'started_at': timestamp(), 'python': platform.python_version(), 'platform': platform.platform(),
               'torch': torch.__version__, 'numpy': np.__version__, 'cuda': torch.version.cuda,
               'device': torch.cuda.get_device_name(), 'capability': list(torch.cuda.get_device_capability()),
               'precision': 'float32; autocast disabled; TF32 disabled',
               'TRITON_PTXAS_PATH': os.environ.get('TRITON_PTXAS_PATH'),
               'command': sys.argv, 'protocol_sha256': protocol_hash,
               'data_manifest_sha256': protocol['data_manifest_sha256']}
    study.write_json(args.output / 'runtime.json', runtime)
    receipts = []
    try:
        for arm in protocol['arms']:
            receipts.append(run_arm(arm, args, protocol, protocol_hash, data, started))
        frozen = {'frozen_at': timestamp(), 'protocol_sha256': protocol_hash,
                  'selected_checkpoints': {r['arm']['name']: r['selected_checkpoint'] for r in receipts},
                  'scope': 'Every validation-selected checkpoint frozen before this study performs any test inference.'}
        study.write_json(args.output / 'frozen-checkpoints.json', frozen)
        results = []
        for receipt in receipts:
            arm = receipt['arm']['name']
            selected = study.verify_artifact(args.output, receipt['selected_checkpoint'])
            model, metadata = packet_model.load_checkpoint(selected, args.upstream, device='cuda')
            if metadata['study_metadata']['protocol_sha256'] != protocol_hash:
                raise ValueError('Reloaded checkpoint is not bound to this study')
            tests = {}
            for source in ('cic', 'unsw'):
                if time.monotonic() - started > protocol['maximum_gpu_wall_seconds']:
                    raise RuntimeError('Total GPU budget exhausted before final inference')
                path = args.output / arm / f'test-{source}.jsonl.gz'
                measured = evaluate(model, data[source], source, 2, protocol['inference_batch_size'], path)
                tests[source] = {'metrics': measured, 'predictions': study.artifact(args.output, path),
                                 'exposure': 'source used for training' if source in receipt['arm']['sources'] else 'no supervised fitting on this source'}
                print(json.dumps({'arm': arm, 'test_source': source,
                                  'group_balanced_accuracy': measured['group_weighted']['balanced_accuracy'],
                                  'row_balanced_accuracy': measured['row_weighted']['balanced_accuracy']}), flush=True)
            results.append({'arm': receipt['arm'], 'selected_checkpoint': receipt['selected_checkpoint'],
                            'tests': tests, 'training_receipt': study.artifact(args.output, args.output / arm / 'training-receipt.json')})
            del model
            torch.cuda.empty_cache()
        check_protocol(protocol, args.data)
        load_data(args.data)
        if time.monotonic() - started > protocol['maximum_gpu_wall_seconds']:
            raise RuntimeError('Total GPU budget exceeded; incomplete study')
        if study.sha256(args.protocol) != protocol_hash:
            raise ValueError('Protocol changed while the study ran')
        report = {'schema_version': 1, 'status': 'completed', 'completed_at': timestamp(),
                  'elapsed_seconds': time.monotonic() - started, 'runtime': runtime,
                  'protocol_sha256': protocol_hash, 'data_manifest_sha256': protocol['data_manifest_sha256'],
                  'frozen_checkpoints': study.artifact(args.output, args.output / 'frozen-checkpoints.json'),
                  'results': results,
                  'scope': 'Real CSV-supplied binary targets trained the original NetMamba+ encoder in an explicit packet-only adaptation. All results are conditional on declared group/sampling splits. This is not the original flow benchmark, independent captures, calibrated confidence or a production IDS.'}
        study.write_json(args.output / 'results.json', report)
        print(json.dumps({'status': 'completed', 'arms': len(results), 'results': str(args.output / 'results.json')}), flush=True)
    except BaseException as error:
        failure = {'status': 'incomplete', 'failed_at': timestamp(), 'error_type': type(error).__name__,
                   'error': str(error), 'finished_training_arms': [r['arm']['name'] for r in receipts],
                   'protocol_sha256': protocol_hash, 'elapsed_seconds': time.monotonic() - started}
        study.write_json(args.output / 'failure.json', failure)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, required=True)
    parser.add_argument('--protocol', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--upstream', type=Path, default=ROOT / 'upstream/NetMambaPlus')
    parser.add_argument('--initialization', type=Path, required=True)
    args = parser.parse_args()
    run(args)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
