import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import build_cuda


class CudaBuildChecks(unittest.TestCase):
    def profile(self):
        return {"system": "Linux", "machine": "x86_64", "isolated_environment": True,
                "python_version": [3, 12], "torch": "2.9.1+cu130", "torch_cuda": "13.0",
                "cuda_available": True, "device": 0, "compute_capability": [8, 0],
                "nvcc_version": "Cuda compilation tools, release 13.0, V13.0.88",
                "nvcc_targets": "sm_75\nsm_80\nsm_121\n"}

    def test_compiler_target_matches_selected_gpu_on_both_host_architectures(self):
        self.assertEqual(build_cuda.validate_profile(self.profile()), "80")
        info = self.profile()
        info.update(machine="aarch64", compute_capability=[12, 1])
        self.assertEqual(build_cuda.validate_profile(info), "121")

    def test_unsupported_profiles_are_rejected(self):
        for key, value in [("system", "Windows"), ("machine", "riscv64"),
                           ("isolated_environment", False), ("python_version", [3, 10]),
                           ("torch", "2.9.1+cpu"), ("torch_cuda", "12.8"),
                           ("cuda_available", False), ("compute_capability", [9, 0]),
                           ("nvcc_version", "release 12.8, V12.8.0")]:
            with self.subTest(key=key):
                info = self.profile()
                info[key] = value
                with self.assertRaises(ValueError):
                    build_cuda.validate_profile(info)

    def test_architecture_patch_preserves_surrounding_setup_and_has_one_target(self):
        text = 'before\n    cc_flag.append("-gencode")\n    cc_flag.append("arch=compute_70,code=sm_70")\n    cc_flag.append("arch=compute_80,code=sm_80")\n    cc_flag.append("arch=compute_90,code=sm_90")\n    # HACK:\nafter\n'
        result = build_cuda.architecture_patch(text, "80")
        self.assertTrue(result.startswith("before\n"))
        self.assertTrue(result.endswith("    # HACK:\nafter\n"))
        self.assertEqual(result.count("arch=compute_80,code=sm_80"), 1)
        self.assertNotIn("compute_70", result)
        with self.assertRaises(ValueError):
            build_cuda.architecture_patch(text, "80;bad")

    def test_patch_preimage_mismatch_preserves_original(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "setup.py"
            path.write_text("unexpected", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "preimage"):
                build_cuda.gb10.patch_file(path, "0" * 64, lambda _: "changed")
            self.assertEqual(path.read_text(encoding="utf-8"), "unexpected")

    def test_unsafe_build_location_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory).resolve() / "upstream"
            for target in [source, source / "build"]:
                with self.assertRaisesRegex(ValueError, "outside"):
                    build_cuda.check_build_location(source, target)

    def test_failed_preflight_never_launches_install_and_retains_reason(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory).resolve()
            args = SimpleNamespace(upstream=base / "upstream", build_root=base / "build", device=0, max_jobs=2)
            info = self.profile()
            info["cuda_available"] = False
            with patch.object(build_cuda, "probe_runtime", return_value=info), patch.object(build_cuda.subprocess, "run") as launched:
                self.assertEqual(build_cuda.execute(args), 1)
            launched.assert_not_called()
            record = json.loads((args.build_root / "build-report.json").read_text(encoding="utf-8"))
            self.assertEqual(record["status"], "failed")
            self.assertEqual(record["failed_stage"], "preflight")
            self.assertIn("CUDA", record["error"])

    def test_failed_process_is_logged_and_stops_following_work(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "build.log"
            with patch.object(build_cuda.subprocess, "run", return_value=SimpleNamespace(returncode=7)):
                with self.assertRaises(subprocess.CalledProcessError):
                    build_cuda.logged_run(["compiler", "--example"], log, {})
            self.assertTrue(log.is_file())

    def test_installed_source_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            source, installed = Path(directory) / "source", Path(directory) / "installed"
            source.mkdir()
            installed.mkdir()
            (source / "module.py").write_text("original", encoding="utf-8")
            (installed / "module.py").write_text("altered", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "differs"):
                build_cuda.verify_installed_sources(source, installed)

    def test_observed_extension_flags_must_match_requested_target(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "build.ninja"
            path.write_text("cuda_cflags = -gencode arch=compute_80,code=sm_80\n", encoding="utf-8")
            self.assertEqual(build_cuda.observed_targets(Path(directory), "80"), ["arch=compute_80,code=sm_80"])
            with self.assertRaisesRegex(RuntimeError, "target"):
                build_cuda.observed_targets(Path(directory), "121")

    def test_distutils_compiler_log_establishes_actual_flags_without_ninja(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "compile.log"
            path.write_text("/cuda/bin/nvcc -c example.cu -gencode arch=compute_121,code=sm_121\n", encoding="utf-8")
            self.assertEqual(build_cuda.observed_targets(Path(directory), "121", log=path),
                             ["arch=compute_121,code=sm_121"])


if __name__ == "__main__":
    unittest.main()
