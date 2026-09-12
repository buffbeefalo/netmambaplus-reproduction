"""Build the pinned native extensions for GB10 without editing upstream."""

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import repro

CAUSAL_COMMIT = "d1ab53ddf93b868502da96ad82c5fc0b270911f5"
SETUP_HASHES = {
    "mamba": "fa756a5a882e49bf16623c24aa992b0f4e47325a118d33f6dbcf2bc344f51fe7",
    "causal": "f3745009d556062678a91b673081d2f52f0018557be84dcf95bd4876312e70a1",
}


def patch_file(path, expected_hash, transform):
    original = path.read_bytes()
    digest = hashlib.sha256(original).hexdigest()
    if digest != expected_hash:
        raise ValueError(f"Unexpected patch preimage: {path.name}")
    changed = transform(original.decode("utf-8"))
    if changed == original.decode("utf-8"):
        raise ValueError(f"Patch made no change: {path.name}")
    path.write_text(changed, encoding="utf-8")
    return {"file": path.name, "before_sha256": digest,
            "after_sha256": repro.sha256_file(path)}


def architecture_patch(text):
    start = text.index('    cc_flag.append("-gencode")')
    end = text.index("    # HACK:", start)
    expected = ['arch=compute_70,code=sm_70', 'arch=compute_80,code=sm_80',
                'arch=compute_90,code=sm_90']
    if any(text[start:end].count(item) != 1 for item in expected):
        raise ValueError("Unexpected original architecture list")
    return text[:start] + '    cc_flag.extend(["-gencode", "arch=compute_121,code=sm_121"])\n\n' + text[end:]


def cub_patch(text):
    if text.count("cub::LaneId()") != 1 or text.count("cub::CTA_SYNC()") != 3:
        raise ValueError("Unexpected CUB API call count")
    return (text.replace("#include <cub/config.cuh>", "#include <cub/config.cuh>\n#include <cuda/ptx>")
            .replace("cub::LaneId()", "cuda::ptx::get_sreg_laneid()")
            .replace("cub::CTA_SYNC()", "__syncthreads()"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream", type=Path, default=repro.DEFAULT_UPSTREAM)
    parser.add_argument("--build-root", type=Path, required=True,
                        help="New directory for disposable source copies and build evidence")
    args = parser.parse_args()
    if sys.prefix == sys.base_prefix:
        parser.error("Run this inside the isolated research virtual environment")
    if platform.machine() != "aarch64":
        parser.error("This build profile targets aarch64 GB10 only")
    import torch
    if torch.__version__ != "2.9.1+cu130" or torch.cuda.get_device_capability() != (12, 1):
        parser.error("This measured profile requires Torch 2.9.1+cu130 and compute capability 12.1")
    integrity = repro.verify_upstream(args.upstream, repro.load_config(repro.DEFAULT_CONFIG))
    build = args.build_root.resolve()
    source = args.upstream.resolve()
    if build == source or source in build.parents:
        parser.error("Build directory must be outside the verified upstream checkout")
    build.mkdir(parents=True, exist_ok=False)

    mamba = build / "mamba"
    causal = build / "causal-conv1d"
    shutil.copytree(source / "mamba-1p1p1", mamba)
    subprocess.run(["git", "clone", "--no-checkout", "https://github.com/Dao-AILab/causal-conv1d.git",
                    str(causal)], check=True)
    subprocess.run(["git", "-C", str(causal), "checkout", "--detach", CAUSAL_COMMIT], check=True)
    if repro.git(causal, "rev-parse", "HEAD").strip() != CAUSAL_COMMIT:
        raise ValueError("Causal-convolution source pin mismatch")

    patches = []
    for label, directory in (("mamba", mamba), ("causal", causal)):
        row = patch_file(directory / "setup.py", SETUP_HASHES[label], architecture_patch)
        row["package"] = label
        patches.append(row)
    original_reverse = source / "mamba-1p1p1/csrc/selective_scan/reverse_scan.cuh"
    row = patch_file(mamba / "csrc/selective_scan/reverse_scan.cuh",
                     repro.sha256_file(original_reverse), cub_patch)
    row["package"] = "mamba"
    row["reference"] = "https://nvidia.github.io/cccl/cccl/3.0_migration_guide.html"
    patches.append(row)
    evidence = {"upstream": integrity, "causal_commit": CAUSAL_COMMIT,
                "patches": patches, "status": "building"}
    repro.atomic_json(build / "build-report.json", evidence)
    environment = dict(os.environ, MAX_JOBS="2", MAMBA_FORCE_BUILD="TRUE",
                       CAUSAL_CONV1D_FORCE_BUILD="TRUE")
    for name, directory in (("causal", causal), ("mamba", mamba)):
        command = [sys.executable, "-m", "pip", "install", "--no-cache-dir", "--no-build-isolation",
                   "--no-deps", "--force-reinstall", str(directory)]
        with (build / f"{name}-build.log").open("w") as log:
            result = subprocess.run(command, env=environment, stdout=log, stderr=subprocess.STDOUT)
        if result.returncode:
            evidence.update(status="failed", failed_package=name, exit_code=result.returncode)
            repro.atomic_json(build / "build-report.json", evidence)
            raise RuntimeError(f"{name} build failed; inspect {build / (name + '-build.log')}")

    installed = Path(importlib.metadata.distribution("mamba-ssm").locate_file("mamba_ssm"))
    originals = sorted((source / "mamba-1p1p1/mamba_ssm").rglob("*.py"))
    matches = []
    for original in originals:
        relative = original.relative_to(source / "mamba-1p1p1/mamba_ssm")
        if original.read_bytes() != (installed / relative).read_bytes():
            raise RuntimeError(f"Installed fork Python source differs: {relative}")
        matches.append({"file": str(relative), "sha256": repro.sha256_file(original)})
    repro.verify_upstream(source, repro.load_config(repro.DEFAULT_CONFIG))
    evidence.update(status="built", installed_mamba_python_sources=matches,
                    limitation="Run check_gpu_runtime.py next; build success alone does not prove numerical correctness.")
    repro.atomic_json(build / "build-report.json", evidence)
    print(f"Built both extensions; {len(matches)} installed Mamba Python sources match upstream.")


if __name__ == "__main__":
    main()
