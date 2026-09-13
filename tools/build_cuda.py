"""Build the pinned CUDA 13 extensions for a selected Linux NVIDIA GPU."""

import argparse
import importlib.metadata
import importlib.util
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

import build_gb10 as gb10

repro = gb10.repro


def validate_profile(info):
    if info["system"] != "Linux" or info["machine"] not in {"x86_64", "aarch64"}:
        raise ValueError("Native model builds require Linux x86_64 or aarch64")
    if not info["isolated_environment"]:
        raise ValueError("Use an isolated research virtual environment")
    if list(info["python_version"]) != [3, 12]:
        raise ValueError("This bounded build profile requires Python 3.12")
    if info["torch"] != "2.9.1+cu130" or info["torch_cuda"] != "13.0":
        raise ValueError("Install Torch 2.9.1+cu130 for this pinned CUDA 13.0 profile")
    if not info["cuda_available"]:
        raise ValueError("CUDA is unavailable; this is not a CPU model backend")
    if not re.search(r"release 13\.0(?:,|\s)", info["nvcc_version"]):
        raise ValueError("The extension compiler must be CUDA toolkit 13.0")
    capability = info["compute_capability"]
    if (len(capability) != 2 or any(type(x) is not int or x < 0 for x in capability)
            or capability[0] < 7 or capability[1] > 9):
        raise ValueError("Invalid selected GPU compute capability")
    target = f"{capability[0]}{capability[1]}"
    if f"sm_{target}" not in info["nvcc_targets"].split():
        raise ValueError(f"nvcc cannot compile the selected GPU target sm_{target}")
    return target


def probe_runtime(device):
    info = {"system": platform.system(), "machine": platform.machine(),
            "isolated_environment": sys.prefix != sys.base_prefix,
            "python_version": list(sys.version_info[:2]), "python": sys.version,
            "executable": sys.executable, "device": device}
    if info["system"] != "Linux" or not info["isolated_environment"]:
        raise ValueError("Use a Linux research virtual environment; CPU/macOS/Windows model execution is not implemented")
    import torch
    from torch.utils.cpp_extension import CUDA_HOME
    info.update(torch=torch.__version__, torch_cuda=torch.version.cuda,
                cuda_available=torch.cuda.is_available(), cuda_home=CUDA_HOME)
    if not info["cuda_available"]:
        raise ValueError("CUDA is unavailable; check the NVIDIA driver and CUDA Torch installation")
    if device < 0 or device >= torch.cuda.device_count():
        raise ValueError("Selected CUDA device does not exist among visible GPUs")
    if not CUDA_HOME or not (Path(CUDA_HOME) / "bin/nvcc").is_file():
        raise ValueError("CUDA_HOME must identify a complete toolkit with bin/nvcc")
    nvcc = str(Path(CUDA_HOME) / "bin/nvcc")
    info.update(gpu=torch.cuda.get_device_name(device),
                compute_capability=list(torch.cuda.get_device_capability(device)),
                nvcc_path=nvcc,
                nvcc_version=subprocess.check_output([nvcc, "--version"], text=True),
                nvcc_targets=subprocess.check_output([nvcc, "--list-gpu-code"], text=True),
                torch_compiled_targets=torch.cuda.get_arch_list())
    validate_profile(info)
    info["torch_cuda_sanity_sum"] = float(torch.ones(8, device=f"cuda:{device}").sum().item())
    return info


def architecture_patch(text, target):
    if not re.fullmatch(r"[1-9][0-9]{1,2}", target):
        raise ValueError("Invalid CUDA architecture target")
    return gb10.architecture_patch(text).replace("arch=compute_121,code=sm_121",
                                                 f"arch=compute_{target},code=sm_{target}")


def check_build_location(source, build):
    source, build = source.resolve(), build.resolve()
    if build == source or source in build.parents:
        raise ValueError("Build directory must be outside the verified upstream checkout")


def logged_run(command, log, environment):
    with log.open("w", encoding="utf-8", newline="\n") as stream:
        result = subprocess.run(command, env=environment, stdout=stream, stderr=subprocess.STDOUT)
    if result.returncode:
        raise subprocess.CalledProcessError(result.returncode, command)


def verify_installed_sources(source, installed):
    matches = []
    for original in sorted(source.rglob("*.py")):
        relative = original.relative_to(source)
        candidate = installed / relative
        if not candidate.is_file() or candidate.read_bytes() != original.read_bytes():
            raise RuntimeError(f"Installed fork Python source differs: {relative}")
        matches.append({"file": relative.as_posix(), "sha256": repro.sha256_file(original)})
    if not matches:
        raise RuntimeError("No original Python sources were checked")
    return matches


def observed_targets(directory, target, log=None):
    observed = set()
    if log is not None:
        for line in log.read_text(encoding="utf-8").splitlines():
            if "nvcc" in line and ".cu" in line:
                observed.update(re.findall(r"arch=compute_[0-9]+,code=sm_[0-9]+", line))
    else:
        for path in directory.rglob("build.ninja"):
            observed.update(re.findall(r"arch=compute_[0-9]+,code=sm_[0-9]+", path.read_text(encoding="utf-8")))
    expected = {f"arch=compute_{target},code=sm_{target}"}
    if observed != expected:
        raise RuntimeError(f"Actual extension target flags differ: expected {sorted(expected)}, observed {sorted(observed)}")
    return sorted(observed)


def execute(args):
    source, build = args.upstream.resolve(), args.build_root.resolve()
    check_build_location(source, build)
    if not 1 <= args.max_jobs <= 8:
        raise ValueError("Choose between one and eight build jobs")
    build.mkdir(parents=True, exist_ok=False)
    report = {"schema_version": 1, "status": "building", "stage": "preflight",
              "builder_sha256": repro.sha256_file(Path(__file__)), "commands": [],
              "scope": "Native extension build for the recorded GPU only; numerical and complete-model execution checks are separate."}
    repro.atomic_json(build / "build-report.json", report)
    try:
        report["runtime"] = probe_runtime(args.device)
        target = validate_profile(report["runtime"])
        report["requested_extension_target"] = f"sm_{target}"
        report["stage"] = "source_verification"
        report["upstream"] = repro.verify_upstream(source, repro.load_config(repro.DEFAULT_CONFIG))
        mamba, causal = build / "mamba", build / "causal-conv1d"
        shutil.copytree(source / "mamba-1p1p1", mamba)
        report["stage"] = "causal_source_acquisition"
        environment = dict(os.environ, MAX_JOBS=str(args.max_jobs), MAMBA_FORCE_BUILD="TRUE",
                           CAUSAL_CONV1D_FORCE_BUILD="TRUE", MAMBA_SKIP_CUDA_BUILD="FALSE",
                           CAUSAL_CONV1D_SKIP_CUDA_BUILD="FALSE", PYTHONDONTWRITEBYTECODE="1")
        environment["PATH"] = str(Path(sys.executable).parent) + os.pathsep + environment.get("PATH", "")
        for command in (["git", "clone", "--no-checkout", "https://github.com/Dao-AILab/causal-conv1d.git", str(causal)],
                        ["git", "-C", str(causal), "checkout", "--detach", gb10.CAUSAL_COMMIT]):
            report["commands"].append(command)
            logged_run(command, build / f"source-{len(report['commands'])}.log", environment)
        if repro.git(causal, "rev-parse", "HEAD").strip() != gb10.CAUSAL_COMMIT:
            raise ValueError("Causal-convolution source pin mismatch")
        report["causal_commit"] = gb10.CAUSAL_COMMIT
        report["stage"] = "compatibility_patches"
        patches = []
        for label, directory in (("mamba", mamba), ("causal", causal)):
            change = gb10.patch_file(directory / "setup.py", gb10.SETUP_HASHES[label],
                                     lambda text: architecture_patch(text, target))
            patches.append(dict(change, package=label))
        reverse = "csrc/selective_scan/reverse_scan.cuh"
        change = gb10.patch_file(mamba / reverse, repro.sha256_file(source / "mamba-1p1p1" / reverse), gb10.cub_patch)
        patches.append(dict(change, package="mamba"))
        report["patches"] = patches
        report["actual_extension_gencode_flags"] = {}
        for name, directory in (("causal", causal), ("mamba", mamba)):
            report["stage"] = f"build_{name}"
            command = [sys.executable, "-m", "pip", "install", "--verbose", "--no-cache-dir",
                       "--no-build-isolation", "--no-deps", "--force-reinstall", str(directory)]
            report["commands"].append(command)
            repro.atomic_json(build / "build-report.json", report)
            logged_run(command, build / f"{name}-build.log", environment)
            report["actual_extension_gencode_flags"][name] = observed_targets(directory, target, build / f"{name}-build.log")
        report["stage"] = "installed_source_verification"
        installed = Path(importlib.metadata.distribution("mamba-ssm").locate_file("mamba_ssm"))
        report["installed_mamba_python_sources"] = verify_installed_sources(source / "mamba-1p1p1/mamba_ssm", installed)
        report["extension_files"] = {}
        for name in ("causal_conv1d_cuda", "selective_scan_cuda"):
            spec = importlib.util.find_spec(name)
            if spec is None or not spec.origin:
                raise RuntimeError(f"Missing installed extension: {name}")
            report["extension_files"][name] = {"path": spec.origin, "sha256": repro.sha256_file(Path(spec.origin))}
        repro.verify_upstream(source, repro.load_config(repro.DEFAULT_CONFIG))
        report.update(status="built", stage="complete",
                      next_check="Run tools/check_gpu_runtime.py and complete-model training/reload/inference checks on this same GPU before claiming execution support.")
        repro.atomic_json(build / "build-report.json", report)
        print(f"Built pinned extensions for sm_{target}. Actual flags and source identities: {build / 'build-report.json'}")
        return 0
    except Exception as error:
        report.update(status="failed", failed_stage=report["stage"], error=f"{type(error).__name__}: {error}")
        if isinstance(error, subprocess.CalledProcessError):
            report["exit_code"] = error.returncode
        repro.atomic_json(build / "build-report.json", report)
        print(f"CUDA build failed: {error}. See {build / 'build-report.json'}", file=sys.stderr)
        return 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream", type=Path, default=repro.DEFAULT_UPSTREAM)
    parser.add_argument("--build-root", type=Path, required=True, help="Fresh directory outside pinned upstream")
    parser.add_argument("--device", type=int, default=0, help="Index among visible CUDA devices; builds for this GPU only")
    parser.add_argument("--max-jobs", type=int, default=2)
    args = parser.parse_args()
    try:
        return execute(args)
    except (ValueError, OSError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    raise SystemExit(main())
