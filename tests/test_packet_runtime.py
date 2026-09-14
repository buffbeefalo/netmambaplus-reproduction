"""Native packet gating must not report skipped or unexecuted work as passed."""

import importlib
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest


class PacketRuntimeTests(unittest.TestCase):
    def runtime(self):
        try:
            return importlib.import_module('tools.check_packet_runtime')
        except ModuleNotFoundError as error:
            if error.name != 'tools.check_packet_runtime':
                raise
            self.fail('The packet runtime gate is missing')

    def test_skipped_empty_and_failed_suites_cannot_pass_the_native_gate(self):
        module = self.runtime()
        for count, skipped, failures in [(0, [], []), (17, [('test', 'no GPU')], []),
                                         (17, [], [('test', 'wrong result')])]:
            result = SimpleNamespace(testsRun=count, skipped=skipped, failures=failures, errors=[])
            self.assertFalse(module.test_summary(result)['passed'])

    def test_completed_native_suite_reports_achieved_counts(self):
        result = SimpleNamespace(testsRun=17, skipped=[], failures=[], errors=[])
        summary = self.runtime().test_summary(result)
        self.assertTrue(summary['passed'])
        self.assertEqual(summary['tests_run'], 17)
        self.assertEqual(summary['skipped'], 0)

    def test_existing_output_is_preserved_before_loading_dependencies(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'keep').write_text('evidence', encoding='utf-8')
            with self.assertRaises(FileExistsError):
                self.runtime().execute(root/'missing', root/'upstream', root/'weights', root)
            self.assertEqual((root/'keep').read_text(), 'evidence')


if __name__ == '__main__':
    unittest.main()
