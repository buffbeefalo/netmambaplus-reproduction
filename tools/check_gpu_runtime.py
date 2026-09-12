"""Compare the installed Mamba/CUDA operations with their reference paths."""

import argparse
import copy
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Choose a new output file")

    import torch
    from causal_conv1d import causal_conv1d_fn
    from causal_conv1d.causal_conv1d_interface import causal_conv1d_ref
    from mamba_ssm.modules.mamba_simple import Mamba
    from mamba_ssm.ops.selective_scan_interface import selective_scan_fn, selective_scan_ref
    from mamba_ssm.ops.triton.layernorm import rms_norm_fn

    torch.manual_seed(17)
    assert torch.cuda.is_available(), "CUDA is required"
    cases = []

    def compare(name, optimized, reference, tensors, rtol=1e-3, atol=2e-4):
        left = [x.detach().clone().requires_grad_(True) for x in tensors]
        right = [x.detach().clone().requires_grad_(True) for x in tensors]
        actual, expected = optimized(*left), reference(*right)
        torch.testing.assert_close(actual, expected, rtol=rtol, atol=atol)
        gradient = torch.randn_like(actual)
        actual.backward(gradient)
        expected.backward(gradient)
        errors = []
        for a, b in zip(left, right):
            assert a.grad is not None and b.grad is not None
            assert torch.isfinite(a.grad).all() and torch.isfinite(b.grad).all()
            torch.testing.assert_close(a.grad, b.grad, rtol=rtol, atol=atol)
            errors.append(float((a.grad - b.grad).abs().max()))
        cases.append({"name": name, "passed": True, "rtol": rtol, "atol": atol,
                      "max_abs_output_error": float((actual - expected).abs().max()),
                      "max_abs_input_gradient_error": max(errors)})

    for length in (83, 443):
        x = torch.randn(2, 64, length, device="cuda") * 0.2
        weight = torch.randn(64, 4, device="cuda") * 0.2
        bias = torch.randn(64, device="cuda") * 0.2
        compare(f"causal_conv_fp32_length_{length}",
                lambda *v: causal_conv1d_fn(*v, activation="silu"),
                lambda *v: causal_conv1d_ref(*v, activation="silu"), [x, weight, bias])

        values = [torch.randn(2, 64, length, device="cuda") * 0.2,
                  torch.randn(2, 64, length, device="cuda") * 0.2,
                  -torch.rand(64, 16, device="cuda") - 0.5,
                  torch.randn(2, 16, length, device="cuda") * 0.2,
                  torch.randn(2, 16, length, device="cuda") * 0.2,
                  torch.randn(64, device="cuda") * 0.2,
                  torch.randn(2, 64, length, device="cuda") * 0.2,
                  torch.randn(64, device="cuda") * 0.2]
        compare(f"selective_scan_fp32_length_{length}",
                lambda *v: selective_scan_fn(*v, delta_softplus=True),
                lambda *v: selective_scan_ref(*v, delta_softplus=True), values)

    x = torch.randn(2, 443, 256, device="cuda")
    residual = torch.randn_like(x)
    weight = torch.randn(256, device="cuda")
    compare("fused_rms_norm_fp32",
            lambda a, b, c: rms_norm_fn(a, c, None, residual=b, eps=1e-5),
            lambda a, b, c: (a+b) * torch.rsqrt((a+b).square().mean(-1, keepdim=True) + 1e-5) * c,
            [x, residual, weight])

    for dtype, rtol, atol in [(torch.float32, 1e-3, 2e-4), (torch.float16, 1e-2, 2e-3)]:
        fast = Mamba(d_model=256, d_state=16, d_conv=4, expand=2,
                     bimamba_type="none", if_devide_out=True).cuda().to(dtype)
        slow = copy.deepcopy(fast)
        slow.use_fast_path = False
        fast.eval()
        slow.eval()
        inp = torch.randn(2, 443, 256, device="cuda", dtype=dtype) * 0.2
        compare(f"mamba_block_{str(dtype).split('.')[-1]}", fast, slow, [inp], rtol, atol)
        param_errors = []
        for (name, a), (other, b) in zip(fast.named_parameters(), slow.named_parameters()):
            assert name == other
            assert (a.grad is None) == (b.grad is None), name
            if a.grad is not None:
                torch.testing.assert_close(a.grad, b.grad, rtol=rtol, atol=atol)
                param_errors.append(float((a.grad-b.grad).abs().max()))
        cases[-1]["max_abs_parameter_gradient_error"] = max(param_errors)

    torch.cuda.synchronize()
    packages = {}
    for package in ("torch", "torchvision", "triton", "mamba-ssm", "causal-conv1d", "numpy", "timm"):
        packages[package] = importlib.metadata.version(package)
    report = {
        "schema_version": 1, "status": "passed", "seed": 17,
        "scope": "Synthetic forward/backward parity for this installed runtime; not a benchmark accuracy result or cross-GPU equivalence proof.",
        "python": sys.version, "architecture": platform.machine(), "packages": packages,
        "gpu": torch.cuda.get_device_name(0), "compute_capability": list(torch.cuda.get_device_capability(0)),
        "torch_cuda": torch.version.cuda, "compiled_architectures": torch.cuda.get_arch_list(),
        "nvcc": subprocess.check_output(["nvcc", "--version"], text=True),
        "checker_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "checks": cases,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
