"""Current file entries are checked independently of historical video coverage."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


TOOL = Path(__file__).resolve().parents[1] / "tools/verify_repository_guide.py"
GUIDE = "docs/repository-walkthrough.md"


class RepositoryGuideTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.git("init", "-q")
        self.write("README.md", "Current project instructions\n")
        self.rows = [
            '| <a id="file-readme-md"></a>[README.md](../README.md) | Explains how to start the current project. |',
            '| <a id="file-docs-repository-walkthrough-md"></a>[This guide](repository-walkthrough.md) | Explains each current file and when to use it. |',
        ]
        self.save_guide()
        self.git("add", ".")

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.root), *args], stderr=subprocess.PIPE)

    def write(self, path, value):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(value)

    def save_guide(self, extra=""):
        self.write(GUIDE, "# Current files\n\n| File | Purpose |\n|---|---|\n" +
                   "\n".join(self.rows) + "\n" + extra)

    def run_guide(self):
        return subprocess.run([sys.executable, str(TOOL), "--root", str(self.root)],
                              capture_output=True, text=True, check=False)

    def assert_rejected(self, fragment):
        result = self.run_guide()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        record = json.loads(result.stdout)
        self.assertEqual(record["status"], "failed")
        self.assertIn(fragment, record["error"])

    def test_cli_accepts_individual_current_entries_without_course_evidence(self):
        result = self.run_guide()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        record = json.loads(result.stdout)
        self.assertEqual(record["inventory_files"], 2)
        self.assertEqual(record["guide_entries"], 2)
        self.assertEqual(record["video_coverage"], "not checked")
        self.assertIn("current", record["inventory_scope"].lower())

    def test_untracked_file_needs_an_individual_entry_even_with_an_incidental_link(self):
        self.write("packet.py", "# New implementation\n")
        self.save_guide("An incidental [packet link](../packet.py) does not explain the file.\n")
        self.assert_rejected("packet.py")

    def test_ignored_local_files_do_not_need_entries_but_ignored_tracked_files_do(self):
        self.write(".gitignore", "*.bin\n")
        self.write("cache.bin", "Local cache\n")
        self.rows.append('| <a id="file-gitignore"></a>[.gitignore](../.gitignore) | Identifies local inputs and caches excluded from Git. |')
        self.save_guide()
        result = self.run_guide()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.git("add", "-f", "cache.bin")
        self.assert_rejected("cache.bin")

    def test_a_deleted_tracked_file_is_rejected_even_if_its_entry_remains(self):
        (self.root / "README.md").unlink()
        self.assert_rejected("README.md")

    def test_removing_the_file_anchor_cannot_leave_an_incidental_table_link(self):
        self.rows[0] = '| [README.md](../README.md) | Explains how to start the current project. |'
        self.save_guide()
        self.assert_rejected("README.md")

    def test_hidden_examples_cannot_count_as_rendered_file_entries(self):
        original = self.rows.pop(0)
        for wrapped in [f"```markdown\n{original}\n```", f"<!--\n{original}\n-->",
                        f"<!--\n{original}", "    " + original]:
            with self.subTest(example=wrapped[:12]):
                self.save_guide("\n" + wrapped + "\n")
                self.assert_rejected("README.md")

    def test_duplicate_file_paths_and_duplicate_anchor_ids_are_rejected(self):
        self.rows.append('| <a id="file-another-readme"></a>[README.md](../README.md) | Repeats the same file instead of another entry. |')
        self.save_guide()
        self.assert_rejected("Duplicate guide file entry")
        self.rows.pop()
        self.rows[1] = self.rows[1].replace("file-docs-repository-walkthrough-md", "file-readme-md")
        self.save_guide()
        self.assert_rejected("Duplicate guide anchor")

    def test_two_file_links_in_one_entry_cannot_cover_two_files(self):
        self.write("packet.py", "# New implementation\n")
        self.rows[0] = self.rows[0].replace(" | Explains", " and [packet.py](../packet.py) | Explains")
        self.save_guide()
        self.assert_rejected("one file link")

    def test_a_bare_link_without_a_description_is_rejected(self):
        self.rows[0] = '| <a id="file-readme-md"></a>[README.md](../README.md) | |'
        self.save_guide()
        self.assert_rejected("description")

    def test_entry_cannot_use_an_external_or_directory_link(self):
        for target in ["https://example.invalid/README.md", "../", "#file-readme-md"]:
            with self.subTest(target=target):
                self.rows[0] = f'| <a id="file-readme-md"></a>[README.md]({target}) | Explains how to start the current project. |'
                self.save_guide()
                self.assert_rejected("file")

    def test_entry_cannot_include_an_ignored_extra_path(self):
        self.write(".gitignore", "cache.bin\n")
        self.write("cache.bin", "Local cache\n")
        self.rows.extend([
            '| <a id="file-gitignore"></a>[.gitignore](../.gitignore) | Identifies local inputs and caches excluded from Git. |',
            '| <a id="file-cache"></a>[cache.bin](../cache.bin) | This cache is not a current repository file. |',
        ])
        self.save_guide()
        self.assert_rejected("extra")

    def test_url_encoded_file_names_resolve_to_the_individual_current_path(self):
        self.write("packet notes.md", "Current packet study explanation\n")
        self.rows.append('| <a id="file-packet-notes"></a>[Packet notes](../packet%20notes.md) | Explains how the packet study uses both original files. |')
        self.save_guide()
        result = self.run_guide()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["inventory_files"], 3)


if __name__ == "__main__":
    unittest.main()
