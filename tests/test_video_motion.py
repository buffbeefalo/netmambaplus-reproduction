"""Guard timing provenance and recorded-demo boundaries in teaching animations."""
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from video_motion import animation_events, phrase_time
from build_course_video import motion_clip
import build_course_video
from build_video_documents import paragraph_text


class MotionTests(unittest.TestCase):
    def scene(self):
        return {'id':'learning-example', 'kind':'training-loop', 'start':20, 'end':60,
                'tempo':0.9, 'bullets':['Forward', 'Loss', 'Backward', 'Update'],
                'audio':{'cues':[{'text':'First calculate the forward pass.', 'start':0.5, 'end':3},
                                 {'text':'Next compare the loss.', 'start':4, 'end':6}]}}

    def test_emphasis_uses_the_measured_cue_after_audio_tempo(self):
        self.assertAlmostEqual(phrase_time(self.scene(), 'compare the loss'), 20 + 4/0.9)
        with self.assertRaises(ValueError):
            phrase_time(self.scene(), 'an absent concept')

    def test_all_animations_stay_inside_their_scene_and_legacy_can_disable(self):
        scene = self.scene()
        lines, records = animation_events([scene], [], True)
        self.assertGreater(len(lines), 1)
        self.assertTrue(all(scene['start'] <= r['start'] < r['end'] <= scene['end'] for r in records))
        self.assertEqual(animation_events([scene], [], False), ([], []))

    def test_recorded_clip_requires_original_bytes_safe_geometry_and_available_time(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root/'capture.webm').write_bytes(b'identity-only fixture; not playable media')
            scene = self.scene()
            scene['motion_clip'] = {'path':'capture.webm', 'sha256':hashlib.sha256((root/'capture.webm').read_bytes()).hexdigest(),
                                    'start_seconds':1,'trim_start_seconds':0,'duration_seconds':8,
                                    'x':100,'y':300,'width':1600,'height':500}
            self.assertEqual(motion_clip(scene, root), (root/'capture.webm').resolve())
            scene['motion_clip']['duration_seconds'] = 50
            with self.assertRaisesRegex(ValueError, 'outside'):
                motion_clip(scene, root)
            scene['motion_clip']['duration_seconds'] = 8
            scene['motion_clip']['y'] = 500
            with self.assertRaisesRegex(ValueError, 'area'):
                motion_clip(scene, root)
            scene['motion_clip']['y'] = 300
            (root/'capture.webm').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'checksum'):
                motion_clip(scene, root)

    def test_handbook_links_preserve_fragments_without_unresolved_pdf_bookmarks(self):
        text = paragraph_text('<a id="file-example"></a>[Jump](#example) and [Guide](support-matrix.md#gpu)')
        self.assertNotIn('&lt;a', text)
        self.assertIn('docs/repository-walkthrough.md#example', text)
        self.assertIn('docs/support-matrix.md#gpu', text)
        self.assertNotIn('href="#', text)

    def test_inserted_capture_preserves_exact_scene_frame_budget(self):
        scene = {'frames':1075, 'motion_clip':{'start_seconds':8, 'duration_seconds':7.4}}
        self.assertEqual(build_course_video.clip_frame_plan(scene,30), (240,222,613))
        scene['motion_clip']['duration_seconds']=7.401
        with self.assertRaises(ValueError):
            build_course_video.clip_frame_plan(scene,30)
        scene['motion_clip']['duration_seconds']=40
        with self.assertRaises(ValueError):
            build_course_video.clip_frame_plan(scene,30)


if __name__ == '__main__':
    unittest.main()
