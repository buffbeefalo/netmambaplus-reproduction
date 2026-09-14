"""Check packet evidence, slide content, notes, script and reviewed PDF identity.

This portable check does not render PDF/PowerPoint or certify visual quality.
Run review_packet_study.py separately to audit the underlying experiment.
"""

import argparse
import hashlib
import json
import posixpath
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from build_packet_briefing import content, script_text


DRAWING = "http://schemas.openxmlformats.org/drawingml/2006/main"
PRESENTATION = "http://schemas.openxmlformats.org/presentationml/2006/main"
RELATIONSHIP = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
FILES = {
    "NetMambaPlus-packet-addendum.pdf", "NetMambaPlus-packet-addendum.pptx",
    "packet-addendum-source.json", "packet-addendum-script.md",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def normalize(text):
    return " ".join(text.split())


def xml_text(element):
    paragraphs = []
    for paragraph in element.iter("{" + DRAWING + "}p"):
        paragraphs.append("".join(node.text or "" for node in paragraph.iter("{" + DRAWING + "}t")))
    return normalize(" ".join(paragraphs))


def relationships(archive, part):
    parent, name = posixpath.split(part)
    tree = ET.fromstring(archive.read(posixpath.join(parent, "_rels", name + ".rels")))
    result = {}
    for item in tree:
        identifier = item.attrib["Id"]
        require(identifier not in result, "Duplicate PowerPoint relationship")
        target = item.attrib["Target"]
        if target.startswith("/"):
            target = target[1:]
        else:
            target = posixpath.join(parent, target)
        target = posixpath.normpath(target)
        result[identifier] = (item.attrib["Type"], target, item.get("TargetMode", "Internal"))
    return result


def internal_target(relation, kind):
    type_uri, target, mode = relation
    require(type_uri == RELATIONSHIP + "/" + kind and mode == "Internal" and
            target.startswith("ppt/") and "\\" not in target,
            "Invalid internal PowerPoint " + kind + " relationship")
    return target


def verify_deck(path, slides):
    with zipfile.ZipFile(path) as archive:
        require(len(archive.namelist()) == len(set(archive.namelist())), "Duplicate PowerPoint ZIP member")
        presentation = ET.fromstring(archive.read("ppt/presentation.xml"))
        ids = presentation.findall("{" + PRESENTATION + "}sldIdLst/{" + PRESENTATION + "}sldId")
        require(len(ids) == len(slides), "PowerPoint slide count differs from source")
        links = relationships(archive, "ppt/presentation.xml")
        for index, (identifier, item) in enumerate(zip(ids, slides), 1):
            slide_path = internal_target(links[identifier.attrib["{" + RELATIONSHIP + "}id"]], "slide")
            slide = ET.fromstring(archive.read(slide_path))
            expected = ["NETMAMBA+ / PACKET STUDY", item["title"], item["subtitle"]]
            if "table" in item:
                expected.extend(cell for row in item["table"] for cell in row)
                expected.append(item["caveat"])
            else:
                expected.extend(item["lines"])
            expected.append(f"Packet adaptation · GB10 evidence · original flow results unchanged {index} / {len(slides)}")
            require(xml_text(slide) == normalize(" ".join(expected)), f"PowerPoint slide {index} content differs from source")
            notes_links = [value for value in relationships(archive, slide_path).values()
                           if value[0] == RELATIONSHIP + "/notesSlide"]
            require(len(notes_links) == 1, f"PowerPoint slide {index} notes relationship missing or ambiguous")
            notes = ET.fromstring(archive.read(internal_target(notes_links[0], "notesSlide")))
            require(xml_text(notes) == normalize(item["notes"]), f"PowerPoint slide {index} notes differ from source")


def verify(evidence, documents):
    evidence, documents = Path(evidence), Path(documents)
    slides = content(evidence)
    source = json.loads((documents / "packet-addendum-source.json").read_text(encoding="utf-8"))
    require(source == slides, "Packet source differs from completed evidence and current generator")
    script = (documents / "packet-addendum-script.md").read_text(encoding="utf-8")
    require(script == script_text(slides), "Packet presenter script differs from source")
    verify_deck(documents / "NetMambaPlus-packet-addendum.pptx", slides)
    receipt = json.loads((documents / "verification.json").read_text(encoding="utf-8"))
    require(receipt["status"] == "document_content_verified" and receipt["slides"] == len(slides) and
            receipt["pdf_pages_rendered"] == len(slides), "Missing matching packet document review")
    require(set(receipt["files"]) == FILES, "Packet reviewed file inventory differs")
    for name in sorted(FILES):
        data = (documents / name).read_bytes()
        record = receipt["files"][name]
        require(record["sha256"] == hashlib.sha256(data).hexdigest() and record["bytes"] == len(data),
                "Packet reviewed file identity differs: " + name)
    return {"status": "passed", "slides": len(slides), "source_matches_completed_evidence": True,
            "powerpoint_content_and_notes": "match shared source in presentation order",
            "presenter_script": "matches shared source", "reviewed_file_identities": len(FILES),
            "pdf_check": "reviewed file identity only", "powerpoint_rendered": False,
            "limit": "Content consistency and recorded file identities; no fresh visual, video or model execution certification."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, default=ROOT / "docs/customer/evidence/packet-study")
    parser.add_argument("--documents", type=Path, default=ROOT / "docs/customer/packet-addendum")
    args = parser.parse_args()
    try:
        result = verify(args.evidence, args.documents)
    except (ValueError, OSError, KeyError, TypeError, zipfile.BadZipFile, ET.ParseError) as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
