"""Test a committed client export in a fresh directory without source history."""

import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from export_client import ROOT, export


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", default="HEAD")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="netmamba-client-") as directory:
        root = Path(directory) / "client"
        manifest = export(ROOT, args.revision, root)
        commands = [[sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
                    [sys.executable, "repro.py", "--help"],
                    [sys.executable, "tools/verify_client.py"],
                    [sys.executable, "tools/review_calibration.py", "--check"],
                    [sys.executable, "tools/review_packet_study.py"],
                    [sys.executable, "tools/render_replay.py", "--predictions",
                     "docs/customer/evidence/seed0/replay/predictions.json", "--output", "runs/demo"]]
        for command in commands:
            subprocess.run(command, cwd=root, check=True)
        print(json.dumps({"status": "passed", "source_commit": manifest["source_commit"],
                          "payload_files": len(manifest["files"]), "commands": len(commands),
                          "scope": "Fresh client export; offline tests/evidence/replay only"}))


if __name__ == "__main__":
    main()
