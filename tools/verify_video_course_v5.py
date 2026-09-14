"""Verify the current two-CSV v5 lesson and its published companion artifacts.

The default requires final media, documents and six bound audit receipts.
--source-only checks the lesson, all primary facts, code-backed dimensions and
topic coverage while production is underway; it never claims media acceptance.
Neither mode runs neural inference or substitutes for a human watch-through.
"""

import argparse
import ast
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import posixpath
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

from build_course import ROOT
from build_course_video import publication, reference_paths, validate
from narrate_course_video import load_source
from verify_course_video import verify_files
from verify_video_course_v3 import artifact, digest, local, normalized, read, require

SOURCE = Path('docs/customer/video-course-v5-source.json')
MEDIA = Path('docs/customer/demo/video/v5')
AUDITS = Path('docs/research/video-v5')
CHAPTERS = ('orientation', 'paper', 'cic-csv', 'unsw-csv', 'features', 'learning',
            'code', 'results', 'demo', 'setup', 'repository', 'hardware')
QUESTIONS = {'tried', 'learning', 'inputs', 'results', 'demo', 'hardware', 'gaps'}
DIAGRAMS = {'packet-input', 'packet-encoder', 'packet-training', 'packet-split', 'repo-sync'}
DOCUMENTS = {'NetMambaPlus-course-slides.pptx', 'NetMambaPlus-course-slides.pdf',
             'NetMambaPlus-course-handbook.pdf'}
AUDIT_KINDS = ('decode', 'browser', 'captions', 'claims', 'rendered_samples', 'documents')
FACT_NAMES = set('''cic_rows cic_groups cic_train cic_validation cic_test
unsw_rows unsw_groups unsw_train unsw_validation unsw_test global_rows global_groups
shared shared_conflicts cic_portscan_test_rows cic_ddos_test_rows payload_bytes csv_columns
parameters copied_tensors excluded_tensors updates batch validation_interval unsw_metadata
agreement_rows original_logit_failures client_validated client_predicted client_matching
client_logit_failures native_tests client_suite client_passed client_skipped client_windows_skipped'''.split())
FACT_NAMES.update(f'arm{arm}_{source}_{weight}' for arm in range(6)
                  for source in ('cic', 'unsw') for weight in ('group', 'row'))

# These test semantic topic presence across complete teaching scenes, not exact
# prose or narration spelling. Exact scientific quantities are checked separately.
TOPICS = {
    'orientation': (r'netmambaplus.reproduction', r'netmambaplus.client', r'joint.pretrained', r'csv'),
    'paper': (r'state.space|selective', r'pretrain', r'reconstruct|hidden', r'flow', r'packet'),
    'cic-csv': (r'ttl|time.to.live', r'total.len|total.length', r'protocol', r't.delta|time.delta', r'label'),
    'unsw-csv': (r'hash|fingerprint', r'conflict|disagree', r'seed', r'near.duplicate|capture'),
    'features': (r'prefix', r'causal|earlier.positions', r'metadata', r'outside|ignored', r'learned|trainable'),
    'learning': (r'replacement', r'validation', r'checkpoint', r'loss', r'scratch'),
    'code': (r'receipt', r'unlabeled', r'metadata', r'payload', r'cap', r'uncalibrated'),
    'results': (r'balanced.accuracy', r'row.weight', r'group.weight', r'control', r'pretrain', r'seed'),
    'demo': (r'recorded|saved', r'browser|viewer', r'live|current.network', r'fresh', r'conflict|disagree'),
    'setup': (r'cuda', r'gpu', r'toolkit', r'skip', r'native'),
    'repository': (r'manifest', r'export', r'source', r'client', r'template', r'video|teaching'),
    'hardware': (r'n.p.u|npu|neural.processing', r'smart.n.i.c|smartnic', r'capture',
                 r'unknown.attack', r'confidence|calibrat', r'independent', r'seed'),
}


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings(item)


def teaching_text(chapter):
    fields = {'title', 'narration', 'bullets', 'note', 'table_note', 'code', 'rows', 'columns', 'diagram'}
    return normalized(' '.join(text for scene in chapter['scenes']
                               for key, value in scene.items() if key in fields
                               for text in strings(value))).lower()


def fact_routes():
    """Bind all sixty reviewed quantities to their primary JSON locations."""
    manifest = 'docs/customer/evidence/packet-study/manifest.json'
    results = 'docs/customer/evidence/packet-study/results.json'
    audit = 'docs/research/packet-checks/client-export.json'
    routes = {}
    for source in ('cic', 'unsw'):
        for name in ('rows', 'groups'):
            routes[f'{source}_{name}'] = (manifest, f'/sources/{source}/{name}')
        for split in ('train', 'validation', 'test'):
            routes[f'{source}_{split}'] = (manifest, f'/sources/{source}/splits/{split}/selected_groups')
    for name, pointer in {'global_rows': '/global/rows', 'global_groups': '/global/groups',
                          'shared': '/global/shared_groups',
                          'shared_conflicts': '/global/shared_binary_conflicting_groups',
                          'cic_portscan_test_rows': '/sources/cic/splits/test/selected_label_counts/PortScan',
                          'cic_ddos_test_rows': '/sources/cic/splits/test/selected_label_counts/DDoS'}.items():
        routes[name] = (manifest, pointer)
    for arm in range(6):
        for source in ('cic', 'unsw'):
            for weight in ('group', 'row'):
                routes[f'arm{arm}_{source}_{weight}'] = (results,
                    f'/results/{arm}/tests/{source}/metrics/{weight}_weighted/balanced_accuracy')
    profile = 'docs/customer/evidence/uploaded-csv-profile.json'
    routes.update(payload_bytes=(profile, '/files/0/payload_byte_columns'),
                  csv_columns=(profile, '/files/0/columns'),
                  parameters=('docs/research/packet-checks/native-model-probe.json', '/provenance/parameter_count'))
    for name, pointer in [('copied_tensors', '/state_counts/copied_or_mapped'),
                          ('excluded_tensors', '/state_counts/excluded')]:
        routes[name] = ('docs/customer/evidence/packet-study/initialization-audit.json', pointer)
    for name, pointer in [('updates', '/steps'), ('batch', '/batch_size'),
                          ('validation_interval', '/validation_interval')]:
        routes[name] = ('docs/customer/evidence/packet-study/protocol.json', pointer)
    routes['unsw_metadata'] = ('docs/customer/evidence/packet-study/controls/evaluation/results.json',
                              '/results/8/tests/unsw/metrics/group_weighted/balanced_accuracy')
    for name, pointer in [('agreement_rows', '/rows'),
                          ('original_logit_failures', '/sources/cic/strict_logit_tolerance_failures')]:
        routes[name] = ('docs/customer/evidence/packet-study/unlabeled/agreement.json', pointer)
    for name, pointer in {
        'client_validated': '/native_packet_inference/receipt/validated_rows',
        'client_predicted': '/native_packet_inference/receipt/predicted_rows',
        'client_matching': '/native_packet_inference/comparison/matching_classes',
        'client_logit_failures': '/native_packet_inference/comparison/logit_tolerance_failures',
        'native_tests': '/native_packet_gate/receipt/tests/tests_run',
        'client_suite': '/publication/platform_counts/client/tests_per_job',
        'client_passed': '/publication/platform_counts/client/linux_macos_passed',
        'client_skipped': '/publication/platform_counts/client/linux_macos_skipped',
        'client_windows_skipped': '/publication/platform_counts/client/windows_skipped',
    }.items():
        routes[name] = (audit, pointer)
    return routes


def check_architecture(root, source):
    """Read literal model contracts without importing Torch or executing a model."""
    path = local(root, 'packet_model.py')
    tree = ast.parse(path.read_text(encoding='utf-8'))
    literals = {}
    position_expression = None
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in {'ARCHITECTURE', 'INPUT_CONTRACT', 'STATE_SHAPES', 'DECODER_EXCLUSIONS'}:
                literals[name] = ast.literal_eval(node.value)
            elif name == 'POSITION_INDICES':
                position_expression = node.value
    architecture = literals['ARCHITECTURE']
    expected = {'arr_length': 1500, 'stride_size': 4, 'seq_len': 0, 'num_classes': 2,
                'embed_dim': 256, 'encoder_depth': 4, 'cls_fusion': 'add', 'head_bias': False}
    require(all(architecture.get(key) == value for key, value in expected.items()),
            'Packet architecture dimensions differ from the reviewed v5 lesson')
    contract = literals['INPUT_CONTRACT']
    require(contract.get('shape') == ['B', 1500] and contract.get('dtype') == 'uint8'
            and contract.get('normalization') == 'float32(payload)/127.5-1'
            and contract.get('numeric_sequence_lengths') == {'size': 0, 'iat': 0}
            and contract.get('metadata_used') == [] and contract.get('retained_zero_bytes') is True
            and contract.get('learned_input_independent_prefixes') == 2,
            'Packet architecture input contract has changed')
    shapes = literals['STATE_SHAPES']
    require(shapes.get('pos_embed') == (1, 378, 256)
            and shapes.get('byte_embed.proj.weight') == (256, 1, 4)
            and shapes.get('head.weight') == (2, 256), 'Packet architecture tensor dimensions changed')
    require(isinstance(position_expression, ast.Tuple), 'Missing packet position mapping')
    indices = []
    for expression in position_expression.elts:
        if isinstance(expression, ast.Starred):
            call = expression.value
            require(isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
                    and call.func.id == 'range' and len(call.args) == 2 and not call.keywords,
                    'Unsupported packet position mapping expression')
            start, stop = (ast.literal_eval(value) for value in call.args)
            require(type(start) is int and type(stop) is int and 0 <= start < stop <= 443,
                    'Invalid packet position mapping range')
            indices.extend(range(start, stop))
        else:
            value = ast.literal_eval(expression)
            require(type(value) is int, 'Invalid packet position index')
            indices.append(value)
    require(indices == [20, 41, *range(42, 417), 442], 'Packet position mapping differs from the reviewed coordinates')
    probe = read(local(root, 'docs/research/packet-checks/native-model-probe.json'))
    initialization = probe['provenance']['initialization']
    table = initialization.get('position_table', {})
    audit = read(local(root, 'docs/customer/evidence/packet-study/initialization-audit.json'))
    require(initialization.get('position_indices') == indices == audit.get('position_indices')
            and table.get('source_shape') == [1, 443, 256] and table.get('target_shape') == [1, 378, 256]
            and table.get('parameterization') == 'learned' and table.get('trainable') is True,
            'Native position evidence differs from the selected learned table')
    # The declared four encoder blocks expand a literal per-block shape table.
    # Reading that table verifies the total parameter and copied-tensor counts.
    prefix = path.read_text(encoding='utf-8').split('PRETRAIN_STATE_SHAPES =', 1)[0]
    loops = [node for node in ast.parse(prefix).body if isinstance(node, ast.For)]
    require(len(loops) == 1, 'Packet architecture shape declaration needs review')
    loop = loops[0]
    require(isinstance(loop.iter, ast.Call) and isinstance(loop.iter.func, ast.Name)
            and loop.iter.func.id == 'range' and len(loop.iter.args) == 1,
            'Packet architecture block declaration changed')
    depth = ast.literal_eval(loop.iter.args[0])
    inner = next(node for node in loop.body if isinstance(node, ast.For))
    per_block = ast.literal_eval(inner.iter.func.value)
    require(depth == 4, 'Packet architecture encoder depth changed')
    for index in range(depth):
        shapes.update({f'encoder_blocks.{index}.{name}': shape for name, shape in per_block.items()})
    count = sum(math.prod(shape) for shape in shapes.values())
    facts = source['course']['facts']
    require(count == 1852416 == facts['parameters']['expected'], 'Packet architecture parameter count changed')
    require(len(shapes) - 1 == facts['copied_tensors']['expected'] == 50
            and len(literals['DECODER_EXCLUSIONS']) == facts['excluded_tensors']['expected'] == 31,
            'Packet architecture transfer counts changed')
    encoders = [scene for chapter in source['chapters'] for scene in chapter['scenes']
                if scene['kind'] == 'packet-encoder']
    for scene in encoders:
        cards = scene.get('diagram', {}).get('cards', [])
        numbers = [[int(value.replace(',', '')) for value in re.findall(r'\d[\d,]*', card['title'] + ' ' + card['detail'])]
                   for card in cards]
        require(numbers == [[1500], [4, 375], [3, 378, 256], [4], [2]],
                'Packet encoder diagram dimensions differ from the code')
    return {'payload_bytes': 1500, 'byte_vectors': 375, 'tokens': 378,
            'embedding_width': 256, 'blocks': 4, 'classes': 2, 'parameters': count,
            'position_indices': len(indices), 'source_position_table': 443}


def verify_source(source_path=None, *, root=ROOT):
    root = Path(root).resolve()
    path = Path(source_path or root / SOURCE).resolve()
    require(path.is_relative_to(root), 'The lesson source must be inside the repository root')
    raw = read(path)
    require(raw.get('workflow') == 'two-csv-packet-v1', 'V5 requires the two-CSV packet workflow')
    facts = raw.get('course', {}).get('facts', {})
    require(set(facts) == FACT_NAMES and len(facts) == 60, 'Incomplete 60-fact coverage')
    for name, (file, pointer) in fact_routes().items():
        require((facts[name].get('file'), facts[name].get('pointer')) == (file, pointer),
                f'Changed primary fact location: {name}')
    source = load_source(path, root=root)  # Resolves and checks every primary value, including unused facts.
    require(source.get('release_tag') == 'course-video-v5'
            and source.get('media_name') == 'NetMambaPlus-CSV-workflow-course.mp4',
            'V5 publication must select the packet video')
    require(type(source.get('target_seconds')) is int and 3000 <= source['target_seconds'] <= 3600,
            'V5 duration must be between fifty and sixty minutes')
    validate(source, root)
    chapters = source['chapters']
    require(tuple(chapter['id'] for chapter in chapters) == CHAPTERS, 'V5 needs all twelve ordered chapters')
    questions = source.get('customer_questions', {})
    require(set(questions) == QUESTIONS and all(isinstance(ids, list) and ids
            and len(ids) == len(set(ids)) and set(ids) <= set(CHAPTERS) for ids in questions.values()),
            'Missing or invalid seven-question coverage')
    scenes = [scene for chapter in chapters for scene in chapter['scenes']]
    kinds = {scene['kind'] for scene in scenes}
    require(DIAGRAMS <= kinds, 'Missing required instructional diagram kinds')
    for chapter in chapters:
        spoken = [scene for scene in chapter['scenes'] if scene['kind'] != 'pause']
        require(len(chapter['scenes']) == 8 and len(spoken) == 7
                and chapter['scenes'][-1]['kind'] == 'pause',
                'Each v5 chapter needs seven narrated scenes and its declared pause')
        require(all(len(scene['narration'].split()) >= 60 for scene in spoken),
                f'Incomplete narrated topic coverage: {chapter["id"]}')
        text = teaching_text(chapter)
        require(all(re.search(pattern, text) for pattern in TOPICS[chapter['id']]),
                f'Missing teaching topic or limitation: {chapter["id"]}')
    summary = source.get('summary', '').lower()
    require(all(term in summary for term in ('csv', 'packet', 'repositories', 'balanced accuracy', 'flow'))
            and re.search(r'not.reproduced|different.task', summary)
            and all(f'{facts[key]["expected"] * 100:.2f}%' in summary
                    for key in ('arm4_cic_group', 'arm4_unsw_group')),
            'Publication summary must describe the packet results and their different flow scope')
    result_text = teaching_text(next(c for c in chapters if c['id'] == 'results'))
    require('99.34%' in result_text, 'The stronger UNSW metadata control is missing')
    replay_scenes = [scene for chapter in chapters for scene in chapter['scenes']
                     if 'prediction-agreement' in scene['references'] and 'client-audit' in scene['references']]
    require(any(all(value in ' '.join(strings(scene)) for value in ('25,930', '20,000', '128', '76'))
                and re.search(r'\b2 rows\b', ' '.join(strings(scene))) for scene in replay_scenes),
            'Both original and fresh replay scopes must remain separately visible')
    refs = reference_paths(source, source['course'], root)
    used = {key for scene in scenes for key in scene['references']}
    require(used <= set(refs), 'Unknown lesson evidence reference')
    require({'project-guide', 'client-setup', 'walkthrough'} <= used, 'Missing guide source bindings')
    require(all(refs.get(key) == value for key, value in {
        'project-guide': 'docs/customer/client-project-guide.md',
        'client-setup': 'client/SETUP.md.in',
        'walkthrough': 'docs/repository-walkthrough.md',
    }.items()), 'Changed guide source binding')
    identities = {key: {'path': refs[key], 'sha256': digest(local(root, refs[key]))} for key in sorted(used)}
    architecture = check_architecture(root, source)
    return {'status': 'passed', 'source_path': path.relative_to(root).as_posix(),
            'source_sha256': digest(path), 'chapters': 12, 'scenes': len(scenes), 'spoken_scenes': 84,
            'fact_bindings': len(facts), 'diagram_kinds': sorted(DIAGRAMS), 'architecture': architecture,
            'references': identities, 'media_checked': False,
            'scope': 'Primary facts, code-backed dimensions and topic presence; full content review and media checks are separate.'}


def check_publication(source, manifest):
    require(publication(source) == publication(manifest), 'Media publication summary or metadata differs from its source')
    require(manifest.get('scheduled_seconds') == source['target_seconds']
            and 3000 <= manifest['scheduled_seconds'] <= 3600, 'Media duration differs from the v5 lesson')


def zip_target(base, target):
    require(isinstance(target, str) and target and '\\' not in target and ':' not in target
            and not target.startswith('/'), 'Unsafe presentation relationship')
    result = posixpath.normpath(posixpath.join(posixpath.dirname(base), target))
    require(not result.startswith('../') and result != '..', 'Escaping presentation relationship')
    return result


def relationships(archive, part):
    path = PurePosixPath(part)
    relative = str(path.parent / '_rels' / (path.name + '.rels'))
    root = ET.fromstring(archive.read(relative))
    result = {}
    for element in root:
        require(element.get('TargetMode') != 'External', 'External presentation relationship is not accepted')
        key = element.get('Id')
        require(key and key not in result, 'Duplicate presentation relationship')
        result[key] = (element.get('Type', ''), zip_target(part, element.get('Target')))
    return result


def check_pptx_notes(path, scenes, source_hash, *, frame_hashes=None):
    """Inspect actual OOXML slide relationships, notes and optional image bytes."""
    p = 'http://schemas.openxmlformats.org/presentationml/2006/main'
    r = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
    a = 'http://schemas.openxmlformats.org/drawingml/2006/main'
    with zipfile.ZipFile(path) as archive:
        require(len(archive.namelist()) == len(set(archive.namelist())), 'Duplicate presentation ZIP entries')
        presentation = ET.fromstring(archive.read('ppt/presentation.xml'))
        ids = presentation.findall(f'{{{p}}}sldIdLst/{{{p}}}sldId')
        require(len(ids) == len(scenes), 'Presentation slide count differs from the selected source')
        order = relationships(archive, 'ppt/presentation.xml')
        slide_parts = [order[item.get(f'{{{r}}}id')][1] for item in ids]
        require(len(set(slide_parts)) == len(scenes), 'Repeated presentation slide relationships')
        for scene, part in zip(scenes, slide_parts):
            links = relationships(archive, part)
            notes = [target for kind, target in links.values() if kind.endswith('/notesSlide')]
            require(len(notes) == 1, 'Each slide needs one source-bound notes part')
            text = normalized(' '.join(ET.fromstring(archive.read(notes[0])).itertext()))
            require(re.findall(r'Source SHA-256:\s*([0-9a-f]{64})', text) == [source_hash],
                    'Presentation notes have a missing or stale source hash')
            expected = scene['narration'] or f"Practice for {scene['seconds']} seconds: " + ' '.join(scene['bullets'])
            require(normalized(expected) in text, f'Presentation narration notes drifted: {scene["id"]}')
            if frame_hashes is not None:
                slide = ET.fromstring(archive.read(part))
                pictures = slide.findall(f'.//{{{a}}}blip')
                require(len(pictures) == 1, 'Each slide must contain its one rendered frame')
                target = links[pictures[0].get(f'{{{r}}}embed')][1]
                require(hashlib.sha256(archive.read(target)).hexdigest() == frame_hashes[scene['id']],
                        f'Presentation image differs from rendered scene: {scene["id"]}')
    return {'slides': len(scenes), 'spoken_scenes': sum(bool(scene['narration']) for scene in scenes)}


def verify_documents(directory, source_path, *, root=ROOT, manifest=None):
    root, directory, source_path = Path(root).resolve(), Path(directory).resolve(), Path(source_path).resolve()
    record = read(directory / 'companion-manifest.json')
    require(record.get('schema_version') == 1 and record.get('source_sha256') == digest(source_path),
            'Companion source binding has a missing or stale source hash')
    require(record.get('walkthrough_sha256') == digest(local(root, 'docs/repository-walkthrough.md')),
            'Companion walkthrough guide hash is stale')
    source = load_source(source_path, root=root)
    scenes = [scene for chapter in source['chapters'] for scene in chapter['scenes']]
    require(record.get('slide_count') == len(scenes) == 96 and record.get('spoken_scenes') == 84,
            'Companion documents must contain all 96 slides and 84 narrated scenes')
    require(set(record.get('artifacts', {})) == DOCUMENTS, 'Required companion documents are missing')
    for name, identity in record['artifacts'].items():
        path = artifact(root, {**identity, 'path': (directory / name).relative_to(root).as_posix()}, 'companion')
        require(type(identity.get('bytes')) is int and identity['bytes'] == path.stat().st_size,
                'Companion document size changed')
        if name.endswith('.pdf'):
            require(path.read_bytes()[:5] == b'%PDF-', 'Invalid companion PDF header')
    frames = record.get('frames', [])
    require([frame.get('scene_id') for frame in frames] == [scene['id'] for scene in scenes],
            'Companion frame order or source coverage changed')
    frame_hashes = {}
    for scene, frame in zip(scenes, frames):
        path = artifact(root, frame, 'companion frame')
        frame_hashes[scene['id']] = frame['sha256']
        require(record.get('slide_images', {}).get(path.name) == frame['sha256'], 'Companion image identity changed')
    if manifest is not None:
        require(len(manifest['scenes']) == len(scenes), 'Media and companion scenes disagree')
        for scene in manifest['scenes']:
            visuals = scene.get('visuals', [])
            require(len(visuals) == 1 and visuals[0]['sha256'] == frame_hashes[scene['id']],
                    'Companion frame differs from the video scene')
    notes = check_pptx_notes(directory / 'NetMambaPlus-course-slides.pptx', scenes,
                             digest(source_path), frame_hashes=frame_hashes)
    return {'status': 'passed', **notes, 'source_sha256': record['source_sha256'],
            'walkthrough_sha256': record['walkthrough_sha256'], 'artifacts': record['artifacts']}


def check_audit(kind, record, directory, source_path, *, root=ROOT):
    root, directory, source_path = Path(root).resolve(), Path(directory).resolve(), Path(source_path).resolve()
    manifest_path = directory / 'media-manifest.json'
    manifest = read(manifest_path)
    require(kind in AUDIT_KINDS and record.get('schema_version') == 1 and record.get('status') == 'passed',
            f'Missing successful final {kind} audit')
    require(record.get('source_sha256') == digest(source_path)
            and record.get('manifest_sha256') == digest(manifest_path), f'Stale final {kind} source or manifest hash')
    require(record.get('known_material_defects') == [], f'Unresolved material defects in {kind} audit')
    require(isinstance(record.get('method'), str) and record['method'].strip(), f'Missing {kind} audit method')
    try:
        completed = datetime.fromisoformat(record['completed_at'].replace('Z', '+00:00'))
        require(completed.utcoffset() is not None, f'{kind} audit needs a timezone-bearing completion time')
    except (KeyError, AttributeError, TypeError, ValueError) as error:
        raise ValueError(f'Missing or invalid final {kind} completion time') from error
    required = {(directory / name).relative_to(root).as_posix()
                for name in (manifest['media_name'], 'captions.vtt')}
    if kind == 'documents':
        required.update((directory / name).relative_to(root).as_posix()
                        for name in DOCUMENTS | {'companion-manifest.json'})
    entries = record.get('artifacts')
    require(isinstance(entries, list) and entries, f'Missing final {kind} artifact bindings')
    bound = set()
    for entry in entries:
        path = artifact(root, entry, f'{kind} audit')
        relative = path.relative_to(root).as_posix()
        require(relative not in bound, f'Duplicate {kind} artifact binding')
        bound.add(relative)
    require(required <= bound, f'Final {kind} audit does not bind its required artifacts')
    evidence = record.get('evidence')
    require(isinstance(evidence, list) and evidence, f'Missing supporting raw evidence for {kind} audit')
    for entry in evidence:
        path = artifact(root, entry, f'{kind} raw evidence')
        require(path.suffix == '.json' and path != manifest_path and path != source_path
                and path.parent != root / AUDITS, f'{kind} requires separate raw evidence, not another wrapper')
        raw = read(path)
        require(isinstance(raw, dict) and raw, f'Empty raw {kind} evidence')
    if kind == 'decode':
        duration = record.get('measured_seconds')
        require(type(duration) in (int, float) and math.isfinite(duration)
                and 3000 <= duration <= 3600 and abs(duration - manifest['scheduled_seconds']) <= 1,
                'Actual decoded duration differs from the fifty-to-sixty-minute lesson')
    if kind == 'rendered_samples':
        require(set(record.get('categories', [])) >= {'technical_terms', 'identifiers', 'numbers', 'chapter_transitions'},
                'Rendered review lacks the required sample categories')
    return {'status': 'passed', 'scope': 'Audit status, source, artifact and supporting-record bindings; no new perceptual review.'}


def verify(*, source_path=None, media_dir=None, audit_dir=None, root=ROOT, source_only=False):
    root = Path(root).resolve()
    source_path = Path(source_path or root / SOURCE).resolve()
    result = verify_source(source_path, root=root)
    if source_only:
        return result
    directory = Path(media_dir or root / MEDIA).resolve()
    audits = Path(audit_dir or root / AUDITS).resolve()
    require(directory.is_relative_to(root) and audits.is_relative_to(root), 'V5 artifacts must stay inside the repository root')
    source = load_source(source_path, root=root)
    manifest, files = verify_files(directory, source_path, reference_root=root, repository_root=root)
    check_publication(source, manifest)
    required = DOCUMENTS | {'companion-manifest.json', 'motion-manifest.json', 'narration-manifest.json',
                            publication(source)['webm_name']}
    require(required <= set(manifest['artifacts']), 'Required published v5 companion downloads are missing')
    documents = verify_documents(directory, source_path, root=root, manifest=manifest)
    narration = read(directory / 'narration-manifest.json')
    motion = read(directory / 'motion-manifest.json')
    require(narration.get('source_sha256') == result['source_sha256'] and narration.get('complete') is True
            and motion.get('source_sha256') == result['source_sha256'] and motion.get('enabled') is True,
            'Narration or instructional motion has a stale source binding or is incomplete')
    require({scene.get('id') for scene in narration.get('scenes', [])}
            == {scene['id'] for chapter in source['chapters'] for scene in chapter['scenes'] if scene['narration']},
            'Narration does not cover every spoken source scene')
    reports = {}
    for kind in AUDIT_KINDS:
        path = audits / (kind + '.json')
        require(path.is_file(), f'Missing final {kind} audit receipt: {path.relative_to(root)}')
        require(path.relative_to(directory).as_posix() not in manifest['artifacts']
                if path.is_relative_to(directory) else True, 'Final audits must not create circular media-manifest hashes')
        reports[kind] = check_audit(kind, read(path), directory, source_path, root=root)
    require(source_path.read_bytes() and digest(source_path) == result['source_sha256'], 'Lesson changed during verification')
    return {**result, 'media_checked': True, 'files': files, 'documents': documents, 'audits': reports,
            'scope': 'V5 source, artifact, caption, document and final audit-record checks; no new GPU execution or human full watch.'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--source', type=Path)
    parser.add_argument('--media-dir', type=Path)
    parser.add_argument('--audit-dir', type=Path)
    parser.add_argument('--source-only', action='store_true', help='Check source and primary evidence; do not claim media acceptance')
    args = parser.parse_args(argv)
    try:
        result = verify(root=args.root, source_path=args.source, media_dir=args.media_dir,
                        audit_dir=args.audit_dir, source_only=args.source_only)
    except (ValueError, OSError, KeyError, TypeError, StopIteration, SyntaxError, zipfile.BadZipFile, ET.ParseError) as error:
        print(f'V5 verification failed: {error}', file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
