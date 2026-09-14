"""Reject drift between measured packet results and the customer documents."""

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/verify_packet_briefing.py"
PPTX = "NetMambaPlus-packet-addendum.pptx"
PDF = "NetMambaPlus-packet-addendum.pdf"
SOURCE = "packet-addendum-source.json"
SCRIPT = "packet-addendum-script.md"


class PacketBriefingTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.documents = self.root / "documents"
        self.evidence = self.root / "evidence"
        shutil.copytree(ROOT / "docs/customer/packet-addendum", self.documents)
        for relative in ("results.json", "manifest.json", "controls/evaluation/results.json"):
            target = self.evidence / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / "docs/customer/evidence/packet-study" / relative, target)

    def write_json(self, path, value):
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")

    def update_receipt(self, name):
        path = self.documents / "verification.json"
        receipt = json.loads(path.read_text(encoding="utf-8"))
        data = (self.documents / name).read_bytes()
        receipt["files"][name] = {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
        self.write_json(path, receipt)

    def change_zip(self, name, transform):
        path = self.documents / PPTX
        with zipfile.ZipFile(path) as archive:
            contents = {item.filename: archive.read(item) for item in archive.infolist()}
        contents[name] = transform(contents[name])
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
            for member, data in contents.items():
                archive.writestr(member, data)
        self.update_receipt(PPTX)

    def run_check(self):
        return subprocess.run([sys.executable, str(TOOL), "--evidence", str(self.evidence),
                               "--documents", str(self.documents)], capture_output=True,
                              text=True, encoding="utf-8", check=False)

    def assert_rejected(self, fragment):
        result = self.run_check()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "failed")
        self.assertIn(fragment, report["error"])

    def test_published_documents_match_evidence_without_ml_or_office(self):
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["slides"], 8)
        self.assertEqual(report["powerpoint_rendered"], False)
        self.assertEqual(report["pdf_check"], "reviewed file identity only")

    def test_rehashing_a_wrong_visible_result_does_not_make_it_valid(self):
        self.change_zip("ppt/slides/slide5.xml", lambda data: data.replace(b"97.56%", b"99.99%"))
        self.assert_rejected("slide 5 content")

    def test_rehashing_a_stale_shared_source_does_not_make_it_valid(self):
        path = self.documents / SOURCE
        source = json.loads(path.read_text(encoding="utf-8"))
        source[4]["table"][5][1] = "99.99%"
        self.write_json(path, source)
        self.update_receipt(SOURCE)
        self.assert_rejected("source differs from completed evidence")

    def test_changed_measurements_require_new_document_content(self):
        path = self.evidence / "results.json"
        results = json.loads(path.read_text(encoding="utf-8"))
        results["results"][0]["tests"]["cic"]["metrics"]["group_weighted"]["balanced_accuracy"] = 0.1
        self.write_json(path, results)
        self.assert_rejected("source differs from completed evidence")

    def test_rehashing_changed_script_is_rejected(self):
        path = self.documents / SCRIPT
        path.write_text(path.read_text(encoding="utf-8").replace("two CIC rows", "zero CIC rows"),
                        encoding="utf-8")
        self.update_receipt(SCRIPT)
        self.assert_rejected("presenter script")

    def test_changed_speaker_notes_are_rejected_after_rehash(self):
        self.change_zip("ppt/notesSlides/notesSlide7.xml",
                        lambda data: data.replace(b"two CIC rows", b"zero CIC rows"))
        self.assert_rejected("slide 7 notes")

    def test_deck_order_is_read_from_presentation_relationships(self):
        def reverse(data):
            tree = ET.fromstring(data)
            slides = tree.find("{http://schemas.openxmlformats.org/presentationml/2006/main}sldIdLst")
            slides[:] = list(reversed(list(slides)))
            return ET.tostring(tree, encoding="utf-8")
        self.change_zip("ppt/presentation.xml", reverse)
        self.assert_rejected("slide 1 content")

    def test_notes_must_be_attached_to_the_correct_slide(self):
        self.change_zip("ppt/slides/_rels/slide1.xml.rels",
                        lambda data: data.replace(b"notesSlide1.xml", b"notesSlide2.xml"))
        self.assert_rejected("slide 1 notes")

    def test_changed_pdf_requires_a_new_reviewed_identity(self):
        with (self.documents / PDF).open("ab") as stream:
            stream.write(b"changed")
        self.assert_rejected("reviewed file identity")

    def test_receipt_cannot_omit_a_required_document(self):
        path = self.documents / "verification.json"
        receipt = json.loads(path.read_text(encoding="utf-8"))
        del receipt["files"][PDF]
        self.write_json(path, receipt)
        self.assert_rejected("reviewed file inventory")


if __name__ == "__main__":
    unittest.main()
