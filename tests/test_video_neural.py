"""Offline checks for text-bound service captions and reusable audio evidence."""
import asyncio
import hashlib
import json
import sys
import tempfile
import types
import unittest
import wave
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
try:
    import narrate_video_neural as neural
except ModuleNotFoundError:
    neural = None


def event(text, start, seconds):
    return {'type': 'WordBoundary', 'text': text,
            'offset': round(start * 10_000_000), 'duration': round(seconds * 10_000_000)}


class WordCaptionTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(neural, 'The neural narration implementation is missing')

    def test_preserves_original_punctuation_and_real_sentence_bounds(self):
        words = [event('Hello', .1, .2), event('world', .4, .3),
                 event('Then', 1.1, .2), event('go', 1.4, .2)]
        cues = neural.word_cues('“Hello, world!” Then go.', words, 2)
        self.assertEqual(cues, [
            {'text': '“Hello, world!”', 'start': .1, 'end': .7},
            {'text': 'Then go.', 'start': 1.1, 'end': 1.6}])

    def test_acronym_service_merging_and_splitting_does_not_invent_word_times(self):
        words = [event('RTSP', .1, .5), event('and', .7, .1),
                 event('G', .9, .1), event('P', 1.1, .1), event('U', 1.3, .1)]
        cues = neural.word_cues('R T S P and GPU.', words, 2)
        self.assertEqual(cues, [{'text': 'R T S P and GPU.', 'start': .1, 'end': 1.4}])

    def test_group_limits_use_original_text_and_service_word_edges(self):
        text = ' '.join(['one'] * 30) + '.'
        cues = neural.word_cues(text, [event('one', i*.3, .2) for i in range(30)], 10)
        self.assertEqual([len(x['text'].split()) for x in cues], [14, 14, 2])
        self.assertEqual(' '.join(x['text'] for x in cues), text)
        self.assertLessEqual(max(len(x['text']) for x in cues), 65)
        self.assertAlmostEqual(cues[1]['start'], 4.2)
        self.assertAlmostEqual(cues[0]['end'], 4.1)

    def test_does_not_split_a_service_boundary_to_satisfy_caption_size(self):
        with self.assertRaisesRegex(ValueError, 'boundary|caption'):
            neural.word_cues(' '.join(['one'] * 16), [event('one'*16, .1, 2)], 3)

    def test_rejects_truncated_changed_extra_or_unpronounced_words(self):
        for text, words in [
            ('Hello world.', [event('Hello', .1, .2)]),
            ('Hello world.', [event('Hello', .1, .2),event('there', .4, .2)]),
            ('Hello.', [event('Hello', .1, .2),event('again', .4, .2)]),
            ('97.50 percent.', [event('ninety', .1, .2),event('seven', .4, .2)])]:
            with self.subTest(text=text, words=words):
                with self.assertRaisesRegex(ValueError, 'alignment'):
                    neural.word_cues(text, words, 2)

    def test_rejects_empty_nonfinite_backward_overlapping_or_outside_audio(self):
        bad = [[], [event('Hello', -.1, .2)], [event('Hello', .1, 0)],
               [event('Hello', 1.9, .2)],
               [{'type':'WordBoundary','text':'Hello','offset':float('nan'),'duration':1}],
               [event('Hello', .4, .5),event('world', .3, .1)],
               [event('Hello', .1, .5),event('world', .4, .3)]]
        for words in bad:
            with self.subTest(words=words):
                with self.assertRaises(ValueError):
                    neural.word_cues('Hello world.' if len(words)==2 else 'Hello.', words, 2)
        for duration in [0, -1, float('nan'), float('inf')]:
            with self.assertRaises(ValueError):
                neural.word_cues('Hello.', [event('Hello', .1, .2)], duration)

    def test_fingerprint_changes_with_narration_voice_client_or_conversion(self):
        voice = {'engine':'edge-tts','voice':'Andrew','rate':'+0%', 'client_version':'7.2.7'}
        original = neural.fingerprint('Hello.', voice, 'converter-a')
        alternatives = [neural.fingerprint('Hello!', voice, 'converter-a'),
                        neural.fingerprint('Hello.', dict(voice, rate='-5%'), 'converter-a'),
                        neural.fingerprint('Hello.', dict(voice, client_version='next'), 'converter-a'),
                        neural.fingerprint('Hello.', voice, 'converter-b')]
        self.assertEqual(len(set([original] + alternatives)), 5)

    def test_cache_rejects_tampered_audio_and_captions_without_network(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            wav = folder/'scene.wav'
            with wave.open(str(wav), 'wb') as f:
                f.setnchannels(1);f.setsampwidth(2);f.setframerate(24000)
                f.writeframes(b'\x01\x00' * 24000)
            (folder/'scene.mp3').write_bytes(b'stored-mp3-evidence')
            events = [event('Hello', .1, .2)]
            (folder/'scene.words.json').write_text(json.dumps(events))
            record = {'id':'scene', 'input_sha256':'fingerprint', 'wav':'scene.wav',
                      'mp3':'scene.mp3', 'word_events':'scene.words.json',
                      'seconds':1.0, 'samples':24000, 'sample_rate':24000,
                      'cues':[{'text':'Hello.','start':.1,'end':.3}]}
            for key in ['wav', 'mp3', 'word_events']:
                record[key+'_sha256'] = hashlib.sha256((folder/record[key]).read_bytes()).hexdigest()
            (folder/'scene.json').write_text(json.dumps(record))
            self.assertEqual(neural.cached_record(folder,'scene','fingerprint','Hello.'), record)
            self.assertIsNone(neural.cached_record(folder,'scene','changed','Hello.'))
            record['cues'][0]['text']='Invented.'
            (folder/'scene.json').write_text(json.dumps(record))
            with self.assertRaisesRegex(ValueError, 'cache|Cache'):
                neural.cached_record(folder,'scene','fingerprint','Hello.')
            record['cues'][0]['text']='Hello.'
            (folder/'scene.json').write_text(json.dumps(record))
            (folder/'scene.mp3').write_bytes(b'tampered')
            with self.assertRaisesRegex(ValueError, 'cache|Cache'):
                neural.cached_record(folder,'scene','fingerprint','Hello.')


class SingleRequestTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.assertIsNotNone(neural, 'The neural narration implementation is missing')

    async def test_one_request_failure_is_propagated_and_never_retried(self):
        class Communication:
            texts = [b'Hello.']
            state = {'stream_was_called':False}
            calls = 0
            async def _Communicate__stream(self):
                self.calls += 1
                raise RuntimeError('service rejected request')
                yield
        communication = Communication()
        with self.assertRaisesRegex(RuntimeError, 'service rejected'):
            async for _ in neural.stream_once(communication):
                self.fail('Failure must not become invented output')
        self.assertEqual(communication.calls,1)

    async def test_long_service_input_is_rejected_before_any_request(self):
        class Communication:
            texts = [b'part one',b'part two']
            state = {'stream_was_called':False}
            async def _Communicate__stream(self):
                raise AssertionError('No call allowed for split input')
                yield
        with self.assertRaisesRegex(ValueError, 'single|chunk'):
            async for _ in neural.stream_once(Communication()):
                self.fail('No output expected')


class RunContractTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.assertIsNotNone(neural, 'The neural narration implementation is missing')
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.folder = Path(self.temporary.name)
        self.source_file = self.folder/'source.json'
        self.source_file.write_text('{}')
        self.converter = self.folder/'ffmpeg'
        self.converter.write_bytes(b'converter identity')
        self.source = {'voice': {'engine':'edge-tts','voice':'en-US-AndrewMultilingualNeural',
            'rate':'+0%','synthetic':True,'client_version':'7.2.7',
            'provider_model_revision':'unavailable'}, 'chapters':[{'scenes':[
                {'id':'first','narration':'Hello.'}, {'id':'second','narration':'World.'}]}]}
        self.args = types.SimpleNamespace(output=self.folder/'tts', ffmpeg=self.converter,
                                          only_scene=None, timeout=1)
        for target, replacement in [('SOURCE',self.source_file), ('load_source',lambda *args:self.source)]:
            context = patch.object(neural,target,replacement)
            context.start();self.addCleanup(context.stop)

    async def test_service_failure_is_logged_and_stops_before_another_scene(self):
        class Communication:
            calls = 0
            def __init__(self, text, **kwargs):
                self.texts = [text.encode()]
                self.state = {'stream_was_called':False}
            async def _Communicate__stream(self):
                Communication.calls += 1
                raise RuntimeError('recorded transport failure')
                yield
        dependency = types.SimpleNamespace(__version__='7.2.7',Communicate=Communication)
        with patch.dict(sys.modules,edge_tts=dependency):
            with self.assertRaisesRegex(RuntimeError,'transport failure'):
                await neural.run(self.args)
        failures = [json.loads(line) for line in (self.args.output/'failures.jsonl').read_text().splitlines()]
        self.assertEqual(len(failures),1)
        self.assertEqual(failures[0]['scene'],'first')
        self.assertFalse(failures[0]['automatic_retry'])
        self.assertEqual(Communication.calls,1)
        self.assertFalse((self.args.output/'narration.json').exists())
        self.assertFalse((self.args.output/'first.json').exists())

    async def test_source_drift_is_logged_without_publishing_a_full_manifest(self):
        def changed_cache(output, scene_id, identity, text):
            self.source_file.write_text('{"changed":true}')
            return {'id':scene_id,'seconds':1}
        with patch.object(neural,'cached_record',changed_cache):
            with self.assertRaisesRegex(ValueError,'source changed'):
                await neural.run(self.args)
        self.assertFalse((self.args.output/'narration.json').exists())
        self.assertTrue((self.args.output/'failures.jsonl').is_file())

    async def test_single_scene_sample_never_becomes_the_complete_manifest(self):
        self.args.only_scene='first'
        with patch.object(neural,'cached_record',return_value={'id':'first','seconds':1}):
            await neural.run(self.args)
        record=json.loads((self.args.output/'narration-first.json').read_text())
        self.assertFalse(record['complete'])
        self.assertEqual([x['id'] for x in record['scenes']],['first'])
        self.assertIsNone(record['voices_sha256'])
        self.assertFalse((self.args.output/'narration.json').exists())

    async def test_empty_spoken_source_is_rejected(self):
        self.source['chapters'][0]['scenes']=[]
        with self.assertRaisesRegex(ValueError,'spoken|empty'):
            await neural.run(self.args)

    async def test_explicit_source_is_loaded_and_bound_without_changing_cache_identity(self):
        selected = self.folder / 'selected.json'
        selected.write_text('{"explicit":true}')
        self.args.source = selected
        self.args.only_scene = 'first'
        with patch.object(neural, 'load_source', return_value=self.source) as loader:
            with patch.object(neural, 'cached_record', return_value={'id':'first','seconds':1}):
                await neural.run(self.args)
        loader.assert_called_once_with(selected)
        record = json.loads((self.args.output / 'narration-first.json').read_text())
        self.assertEqual(record['source_sha256'], neural.digest(selected))

    async def test_selected_source_drift_does_not_use_default_source_guard(self):
        self.args.source = self.folder / 'selected.json'
        self.args.source.write_text('{}')
        def changed_cache(output, scene_id, identity, text):
            self.args.source.write_text('{"changed":true}')
            return {'id':scene_id,'seconds':1}
        with patch.object(neural, 'cached_record', changed_cache):
            with self.assertRaisesRegex(ValueError, 'source changed'):
                await neural.run(self.args)
        self.assertFalse((self.args.output / 'narration.json').exists())


if __name__ == '__main__':
    unittest.main()
