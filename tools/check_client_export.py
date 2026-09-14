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
                    [sys.executable, "packet_data.py", "--help"],
                    [sys.executable, "tools/predict_packets.py", "--help"],
                    [sys.executable, "tools/check_packet_runtime.py", "--help"],
                    [sys.executable, "tools/verify_client.py"],
                    [sys.executable, "tools/render_packet_demo.py", "--output", "runs/demo"]]
        forbidden = {"predict.py", "evaluate.py", "replay.py", "calibration.py", "configs/assets.json",
                     "tools/render_replay.py", "tools/calibrate.py", "tools/check_model_runtime.py"}
        if forbidden.intersection(manifest['files']):
            raise ValueError('The client export includes an unsupported flow workflow')
        evidence = [name for name in manifest['files'] if name.startswith('docs/customer/evidence/')]
        if any('/packet-study/' not in name and not name.endswith('/uploaded-csv-profile.json') for name in evidence):
            raise ValueError('The client export includes non-packet scientific evidence')
        for command in commands:
            subprocess.run(command, cwd=root, check=True)
        print(json.dumps({"status": "passed", "source_commit": manifest["source_commit"],
                          "payload_files": len(manifest["files"]), "commands": len(commands),
                          "scope": "Fresh packet-only client export; offline tests/evidence/demo only"}))


if __name__ == "__main__":
    main()
