# Sharing audit — 7 September 2026

The audit reviewed all eight files in baseline commit [`597c7815ca957522959b43a439d826e27d702511`](https://github.com/buffbeefalo/netmambaplus-reproduction/tree/597c7815ca957522959b43a439d826e27d702511), relevant pinned upstream source, the released native data, repository history and publication settings. Four issues were corrected. The project remains an experimental reproduction harness; this audit does not establish a completed GPU experiment or reproduced paper results.

## Findings and corrections

| Priority | Demonstrated baseline behavior | Correction and evidence |
|---|---|---|
| High | A validation report directed at an input path returned success and replaced the flow array with a report object. Configuration files could also be overwritten. | [Report creation](../repro.py) now atomically requires a new destination. Regression tests verify preservation of metadata, all three splits, configuration, symbolic links and previous reports. |
| Medium | A fine-tuning override selected `signed_sizes`, but validation checked `sizes`. A dry run succeeded even though the selected field was absent; duplicate detection also used the wrong representation. | Validation and invocation now share the stage-settings resolver. The report records and fingerprints the effective size field. Tests cover signed-only inputs in all stages, missing selected fields, and the corrected overlap count. |
| High | An existing output checkpoint was accepted during preflight. In a simultaneous-start test, eight invocations all claimed one output directory. | Each run requires a new or empty directory and atomically creates its initial manifest without replacing another owner's file. Tests verify exactly one owner and preservation of earlier artifacts. No actual stale-checkpoint experiment result was observed; the correction removes the demonstrated reuse and ownership ambiguity. |
| High | The installation command did not force a source build. The bundled installer can download a stock wheel with the same version number, while the native model passes constructor arguments absent from stock Mamba 1.1.1. | The [setup instructions](../README.md#research-environment) now force the bundled build, disable the wheel cache for that installation, preserve the pinned dependency stack, and compare installed Python sources with the bundled source. The comparison was tested against a temporary matching copy of all 14 Python files and a deliberately changed module. A real GPU installation was not performed. |

The installation finding is grounded in the pinned [wheel-selection logic](https://github.com/wangtz19/NetMambaPlus/blob/eec9483e2f0fb84ca22982b9de8149bc3a8b1ad2/mamba-1p1p1/setup.py#L199), the native [Mamba factory](https://github.com/wangtz19/NetMambaPlus/blob/eec9483e2f0fb84ca22982b9de8149bc3a8b1ad2/src/models/models_mamba.py#L90), and the [stock constructor](https://github.com/state-spaces/mamba/blob/v1.1.1/mamba_ssm/modules/mamba_simple.py#L29). The official [1.1.1 release](https://github.com/state-spaces/mamba/releases/tag/v1.1.1) lists matching Python 3.10 / Torch 2.2 / CUDA 12.2 wheels, which the bundled selector targets for CUDA 12.1 Torch. A dependency-stubbed execution of the selector confirmed that its default branch downloads a wheel and `MAMBA_FORCE_BUILD=TRUE` selects the local build. No downloaded wheel or checkpoint code was executed during that check.

## Verification completed

- **43 standard-library tests pass.** The added tests first reproduced the baseline defects, then passed after the corrections. The suite includes strict checkpoint rejection, class-mapping conflicts, test-only file access, complete metric serialization, input preservation and concurrent output ownership.
- Actual native-parser dry runs pass for pretraining, fine-tuning and evaluation. They retain 42 pretraining arguments and 46 fine-tuning/evaluation arguments, with the expected stage-specific file hashes. A signed-size override on the unsigned release now fails during preflight.
- All **10,404 released CICIoT2022 flows** were revalidated: 8,323 training, 1,040 validation and 1,041 test records. Their hashes match the [README evidence record](../README.md#source-settings-paper-settings-and-observations). The five train/validation and six train/test shared raw inputs remain disclosed; the records were not changed.
- The pinned upstream checkout passes verification of all **103 tracked files** and seven explicit core SHA-256 hashes. Relevant loader, classifier, training, evaluator and installer interfaces were compared with the harness and documentation.
- Repository history was scanned with Gitleaks. No secrets were detected. All baseline tracked files were UTF-8 text; no upstream source, datasets, checkpoints, run outputs or private evidence were tracked.
- README/lesson links, CLI examples, Python 3.10 syntax, settings provenance, metric definitions and experiment limitations were reviewed. The [CI workflow](../.github/workflows/ci.yml) runs the full offline suite and help command on Python 3.10 and 3.12; consult the checks associated with the shared commit for its published result.

The implementation reviewed after correction has these SHA-256 values:

```text
repro.py                4240406e90271f9c14c9c3ad91f257b31137d422256556d09986ebaff81678c6
evaluate.py             a8db041b9f3929c7c0acfd63aac65600384e75cc2fdd4018743bdf70ee0bdca0
configs/ciciot2022.json  fba589310c98ea9f8838a0a14eb9cb2d6cfd13c4c8d219c6878e7508c68cab92
```

## Council review status

The Fable/Astra review of the baseline, run `608cb390-1195-4f2c-9ed4-059bec748f03`, ended **ESCALATED / UNRATIFIED**. Both reviewers identified the report/input and effective-size-key defects. They withheld full clearance because the bounded 24 KiB evidence pack excluded portions of the implementation, tests, CI and setup documentation. There is no mutually ratified audit decision or decision hash for that run.

The corrections and closure checks above were completed through full-file inspection and deterministic verification by the implementing assistant. They are not presented as council-approved fixes, an independent third-party certification or a completed numerical reproduction. The earlier architecture consensus is separate from this audit result.

## Limits to preserve when sharing

- Torch/CUDA execution, the GB10 installation, training convergence and checkpoint/model compatibility have not been demonstrated on a real GPU. The forced-build recipe and source check improve installation fidelity; they do not validate the compiled kernels or replace an environment lockfile.
- The paper's full pretraining corpus/history remains unestablished. Source settings differ from the paper's stated settings; both are documented separately.
- Raw-input overlap and recorded identifiers do not establish capture independence. Strict tensor loading does not prove class semantics without checkpoint-bound provenance. Pickle-based native checkpoints must come from a trusted source.
- Synthetic CPU tests verify harness behavior, not scientific accuracy, throughput, distribution-shift robustness or operational intrusion-detection performance.
- The repository is private. A recipient needs repository access to follow the GitHub link. Source/data distribution permissions remain separate from access to this harness.

The supported sharing description remains: **a tested native-flow reproduction harness with documented evidence and limitations; GPU reproduction and independent audit clearance remain open.**
