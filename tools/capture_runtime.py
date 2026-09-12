"""Capture a bounded runtime inventory without dumping the shell environment."""

import argparse
import importlib.metadata
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import repro


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Choose a new runtime record")
    import torch
    import causal_conv1d_cuda
    import selective_scan_cuda
    integrity = repro.verify_upstream(repro.DEFAULT_UPSTREAM, repro.load_config(repro.DEFAULT_CONFIG))
    installed = Path(importlib.metadata.distribution("mamba-ssm").locate_file("mamba_ssm"))
    originals = repro.DEFAULT_UPSTREAM / "mamba-1p1p1/mamba_ssm"
    source_inventory = []
    for source in sorted(originals.rglob("*.py")):
        relative = source.relative_to(originals)
        actual = installed / relative
        if source.read_bytes() != actual.read_bytes():
            raise ValueError(f"Installed Mamba Python file differs: {relative}")
        source_inventory.append({"file": str(relative), "sha256": repro.sha256_file(actual)})
    binaries = {}
    for module in (causal_conv1d_cuda, selective_scan_cuda):
        path = Path(module.__file__)
        binaries[module.__name__] = {"file": path.name, "bytes": path.stat().st_size, "sha256": repro.sha256_file(path)}
    packages = sorted({f"{distribution.metadata['Name']}=={distribution.version}"
                       for distribution in importlib.metadata.distributions()})
    check = subprocess.run([sys.executable, "-m", "pip", "check"], capture_output=True, text=True)
    record = {"created_at": repro.timestamp(), "capture_tool_sha256": repro.sha256_file(__file__),
              "runtime": repro.runtime_information(), "gpu": torch.cuda.get_device_name(),
              "compute_capability": list(torch.cuda.get_device_capability()), "torch_cuda": torch.version.cuda,
              "driver": subprocess.check_output(["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"], text=True).strip(),
              "compiler": subprocess.check_output(["nvcc", "--version"], text=True).strip(),
              "ptxas": subprocess.check_output(["/usr/local/cuda/bin/ptxas", "--version"], text=True).strip(),
              "gcc": subprocess.check_output(["gcc", "--version"], text=True).splitlines()[0],
              "glibc": list(platform.libc_ver()), "upstream": integrity, "installed_mamba_python": source_inventory,
              "compiled_extensions": binaries, "installed_package_inventory": packages,
              "pip_check": {"exit_code": check.returncode, "stdout": check.stdout, "stderr": check.stderr},
              "scope": "Recorded runtime and installed artifacts; package inventory is not a universal cross-platform lock or a production support guarantee."}
    repro.atomic_json(args.output, record, overwrite=False)
    print(f"Recorded {len(source_inventory)} source matches and {len(binaries)} compiled extension hashes")


if __name__ == "__main__":
    main()
