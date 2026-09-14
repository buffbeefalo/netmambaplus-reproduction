"""Mutation checks for v5 lesson and document verification; no encoded-media claims."""

import copy
import hashlib
import importlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from xml.sax.saxutils import escape
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
try:
    verifier = importlib.import_module('verify_video_course_v5')
except ModuleNotFoundError as error:
    if error.name != 'verify_video_course_v5':
        raise
    verifier = None

SOURCE = Path('docs/customer/video-course-v5-source.json')
MEDIA = Path('docs/customer/demo/video/v5')


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class PacketVideoVerificationTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(verifier, 'The dedicated v5 verifier is missing')
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.raw = json.loads((ROOT / SOURCE).read_text(encoding='utf-8'))
        paths = {SOURCE.as_posix(), 'packet_model.py', 'packet_data.py',
                 'docs/repository-walkthrough.md', 'docs/harness-reference.md'}
        paths.update(value['file'] for value in self.raw['course']['facts'].values())
        paths.update(value['path'] for value in self.raw['course']['references'].values())
        paths.update(self.raw.get('extra_references', {}).values())
        for chapter in self.raw['chapters']:
            for scene in chapter['scenes']:
                if 'image' in scene:
                    paths.add(scene['image'])
                if 'motion_clip' in scene:
                    paths.add(scene['motion_clip']['path'])
        for relative in paths:
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        self.source = self.root / SOURCE

    def save_source(self):
        write_json(self.source, self.raw)

    def test_source_only_checks_real_primary_evidence_without_media(self):
        result = verifier.verify(source_path=self.source, root=self.root, source_only=True)
        self.assertEqual(result['status'], 'passed')
        self.assertEqual((result['chapters'], result['scenes'], result['spoken_scenes']), (12, 96, 84))
        self.assertEqual(result['fact_bindings'], 60)
        self.assertFalse(result['media_checked'])

    def test_a_changed_primary_quantity_is_rejected(self):
        path = self.root / 'docs/customer/evidence/packet-study/manifest.json'
        value = json.loads(path.read_text())
        value['global']['groups'] += 1
        write_json(path, value)
        with self.assertRaisesRegex(ValueError, 'Evidence disagreement|primary fact'):
            verifier.verify_source(self.source, root=self.root)

    def test_missing_fact_is_not_hidden_by_rehashing_the_contract(self):
        del self.raw['course']['facts']['arm0_cic_row']
        self.raw['fact_bindings_sha256'] = hashlib.sha256(json.dumps(
            self.raw['course']['facts'], sort_keys=True, separators=(',', ':'),
            ensure_ascii=False).encode()).hexdigest()
        self.save_source()
        with self.assertRaisesRegex(ValueError, '60|fact.*coverage'):
            verifier.verify_source(self.source, root=self.root)

    def test_another_workflow_cannot_fall_back_to_historical_facts(self):
        self.raw['workflow'] = 'historical-flow'
        self.save_source()
        with self.assertRaisesRegex(ValueError, 'workflow'):
            verifier.verify_source(self.source, root=self.root)

    def test_missing_question_coverage_is_rejected(self):
        self.raw['customer_questions']['hardware'] = []
        self.save_source()
        with self.assertRaisesRegex(ValueError, 'question|coverage'):
            verifier.verify_source(self.source, root=self.root)

    def test_missing_limitations_cannot_pass_on_chapter_titles_alone(self):
        chapter = next(c for c in self.raw['chapters'] if c['id'] == 'hardware')
        for scene in chapter['scenes']:
            scene.update(title='A generic explanation', bullets=['A general point'],
                         narration=('This example discusses the project in general terms. ' * 12
                                    if scene['kind'] != 'pause' else ''))
            scene.pop('note', None)
        self.save_source()
        with self.assertRaisesRegex(ValueError, 'topic|hardware|limitation'):
            verifier.verify_source(self.source, root=self.root)

    def test_source_summary_cannot_replace_packet_results_with_a_flow_claim(self):
        self.raw['summary'] = 'The original flow benchmark was fully reproduced.'
        self.save_source()
        with self.assertRaisesRegex(ValueError, 'summary|packet'):
            verifier.verify_source(self.source, root=self.root)

    def test_media_summary_must_match_the_selected_source(self):
        source = verifier.load_source(self.source, root=self.root)
        manifest = {key: copy.deepcopy(source[key]) for key in
                    ['title', 'summary', 'production', 'media_name', 'release_tag']}
        manifest['scheduled_seconds'] = source['target_seconds']
        verifier.check_publication(source, manifest)
        manifest['summary'] = 'A result from the historical flow experiment.'
        with self.assertRaisesRegex(ValueError, 'publication|summary'):
            verifier.check_publication(source, manifest)

    def test_missing_diagram_cannot_be_replaced_by_an_unanimated_card(self):
        for chapter in self.raw['chapters']:
            for scene in chapter['scenes']:
                if scene['kind'] == 'packet-encoder':
                    scene['kind'] = 'cards'
        self.save_source()
        with self.assertRaisesRegex(ValueError, 'diagram'):
            verifier.verify_source(self.source, root=self.root)

    def test_architecture_dimensions_follow_code_and_the_native_probe(self):
        path = self.root / 'packet_model.py'
        text = path.read_text()
        self.assertIn('"embed_dim": 256', text)
        path.write_text(text.replace('"embed_dim": 256', '"embed_dim": 128', 1))
        with self.assertRaisesRegex(ValueError, 'architecture|dimension'):
            verifier.verify_source(self.source, root=self.root)

    def test_position_indices_must_match_the_native_initialization_evidence(self):
        path = self.root / 'packet_model.py'
        text = path.read_text()
        self.assertIn('POSITION_INDICES = (20, 41,', text)
        path.write_text(text.replace('POSITION_INDICES = (20, 41,', 'POSITION_INDICES = (19, 41,', 1))
        with self.assertRaisesRegex(ValueError, 'position'):
            verifier.verify_source(self.source, root=self.root)

    def test_native_position_source_table_cannot_drift_from_443(self):
        path = self.root / 'docs/research/packet-checks/native-model-probe.json'
        value = json.loads(path.read_text())
        value['provenance']['initialization']['position_table']['source_shape'][1] = 442
        write_json(path, value)
        with self.assertRaisesRegex(ValueError, 'position'):
            verifier.verify_source(self.source, root=self.root)

    def test_project_guide_cannot_be_replaced_by_another_reference(self):
        self.raw['course']['references']['project-guide']['path'] = 'docs/customer/packet-model-study.md'
        self.save_source()
        with self.assertRaisesRegex(ValueError, 'guide.*binding'):
            verifier.verify_source(self.source, root=self.root)

    def test_default_mode_fails_when_final_media_is_missing(self):
        with self.assertRaises((ValueError, FileNotFoundError)):
            verifier.verify(source_path=self.source, root=self.root)

    def test_document_receipt_requires_the_selected_source_hash(self):
        directory = self.root / MEDIA
        directory.mkdir(parents=True, exist_ok=True)
        write_json(directory / 'companion-manifest.json', {'schema_version': 1})
        with self.assertRaisesRegex(ValueError, 'source.*hash|source binding'):
            verifier.verify_documents(directory, self.source, root=self.root)

    def test_document_receipt_rejects_a_stale_walkthrough(self):
        directory = self.root / MEDIA
        directory.mkdir(parents=True, exist_ok=True)
        write_json(directory / 'companion-manifest.json', {
            'schema_version': 1, 'source_sha256': sha(self.source),
            'walkthrough_sha256': '0' * 64})
        with self.assertRaisesRegex(ValueError, 'walkthrough|guide'):
            verifier.verify_documents(directory, self.source, root=self.root)

    def test_final_receipt_cannot_claim_success_without_bound_raw_evidence(self):
        directory = self.root / MEDIA
        directory.mkdir(parents=True, exist_ok=True)
        for name in ['fixture.mp4', 'captions.vtt']:
            (directory / name).write_bytes(b'fixture identity only; not encoded media')
        manifest = {'media_name': 'fixture.mp4', 'scheduled_seconds': 3500}
        manifest_path = directory / 'media-manifest.json'
        write_json(manifest_path, manifest)
        report = {'schema_version': 1, 'status': 'passed',
                  'completed_at': '2026-09-14T12:00:00+00:00', 'method': 'Fixture for a rejected empty audit.',
                  'source_sha256': sha(self.source), 'manifest_sha256': sha(manifest_path),
                  'known_material_defects': [], 'artifacts': [
                      {'path': (MEDIA / name).as_posix(), 'sha256': sha(directory / name)}
                      for name in ['fixture.mp4', 'captions.vtt']]}
        with self.assertRaisesRegex(ValueError, 'raw evidence|supporting evidence'):
            verifier.check_audit('browser', report, directory, self.source, root=self.root)


class PacketNotesTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(verifier, 'The dedicated v5 verifier is missing')
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'fixture.pptx'
        self.scenes = [{'id': 'explain', 'title': 'One packet', 'kind': 'cards',
                        'narration': 'One packet supplies stored bytes to the model.', 'bullets': ['Packet bytes']},
                       {'id': 'practice', 'title': 'Explain it', 'kind': 'pause', 'seconds': 10,
                        'narration': '', 'bullets': ['Explain the packet input.']}]

    def write_deck(self, *, source_hash='a' * 64, speech=None):
        # A hand-built OOXML fixture exercises ZIP relationships and note content.
        # It is deliberately not a rendered or accepted production presentation.
        p = 'http://schemas.openxmlformats.org/presentationml/2006/main'
        a = 'http://schemas.openxmlformats.org/drawingml/2006/main'
        r = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
        package = 'http://schemas.openxmlformats.org/package/2006/relationships'
        with zipfile.ZipFile(self.path, 'w') as archive:
            archive.writestr('ppt/presentation.xml', f'<p:presentation xmlns:p="{p}" xmlns:r="{r}"><p:sldIdLst><p:sldId id="256" r:id="rId1"/><p:sldId id="257" r:id="rId2"/></p:sldIdLst></p:presentation>')
            archive.writestr('ppt/_rels/presentation.xml.rels', f'<Relationships xmlns="{package}">' + ''.join(f'<Relationship Id="rId{i}" Type="{r}/slide" Target="slides/slide{i}.xml"/>' for i in [1, 2]) + '</Relationships>')
            for i, scene in enumerate(self.scenes, 1):
                body = (speech if i == 1 and speech is not None else scene['narration']) or 'Practice for 10 seconds: Explain the packet input.'
                archive.writestr(f'ppt/slides/slide{i}.xml', f'<p:sld xmlns:p="{p}"/>')
                archive.writestr(f'ppt/slides/_rels/slide{i}.xml.rels', f'<Relationships xmlns="{package}"><Relationship Id="notes" Type="{r}/notesSlide" Target="../notesSlides/notesSlide{i}.xml"/></Relationships>')
                archive.writestr(f'ppt/notesSlides/notesSlide{i}.xml', f'<p:notes xmlns:p="{p}" xmlns:a="{a}"><a:p><a:r><a:t>{escape(body)}</a:t></a:r></a:p><a:p><a:r><a:t>Source SHA-256: {source_hash}</a:t></a:r></a:p></p:notes>')

    def test_notes_match_each_scene_through_real_zip_relationships(self):
        self.write_deck()
        result = verifier.check_pptx_notes(self.path, self.scenes, 'a' * 64)
        self.assertEqual(result, {'slides': 2, 'spoken_scenes': 1})

    def test_notes_cannot_keep_an_old_lesson_hash(self):
        self.write_deck(source_hash='b' * 64)
        with self.assertRaisesRegex(ValueError, 'source.*hash|source binding'):
            verifier.check_pptx_notes(self.path, self.scenes, 'a' * 64)

    def test_note_text_cannot_drift_while_retaining_a_current_hash(self):
        self.write_deck(speech='An unrelated old narration about flows.')
        with self.assertRaisesRegex(ValueError, 'narration|notes'):
            verifier.check_pptx_notes(self.path, self.scenes, 'a' * 64)


if __name__ == '__main__':
    unittest.main()
