# Public client edition

The [client repository](https://github.com/buffbeefalo/netmambaplus-client) is the concise executable delivery. The [source repository](https://github.com/buffbeefalo/netmambaplus-reproduction) remains the development, research and learning edition. The client has a fresh Git root; no teaching-media history is copied.

## Content and source of truth

[The explicit selection](../../configs/client-manifest.json) retains flow and packet model harnesses, training/inference programs, controls, calibration, CUDA setup, relevant tests and all 155 files in the scientific evidence subtree. Shared source/evidence bytes are unchanged. Client-specific README, setup, results, notice and CI come from the source's `client/` templates. No raw CSV, inherited weights, upstream source, video, presentation deck, presenter script, course or file-by-file walkthrough is exported.

`CLIENT_MANIFEST.json` in the client records the source commit, selection/exporter hashes and each delivered file's source path, size, mode and SHA-256. This is traceability, not a cryptographic authenticity signature or evidence of a new experiment. Original scientific indexes remain unchanged and retain their own scope.

Make code and client-document changes in this source repository. The client accepts issue reports, but editing its managed files independently stops synchronization. After reviewing such changes, port them upstream and deliberately restore the client to its recorded snapshot; do not remove the drift checks or force-push to clear an error.

## Automatic updates

The [publication workflow](../../.github/workflows/client-sync.yml) reacts to successful **CPU verification** runs from canonical source `main` pushes. It validates the exact tested SHA against remote `main`, rejects pull-request and stale events, and serializes publication. Manual **Run workflow** recovery performs the same eligibility checks.

The preparation job uses read access: it regenerates the expected previous client snapshot, rejects drift/rollback, stages the new export and runs the client tests plus scientific verifiers. A separate publisher receives only a verified archive and a dedicated SSH deploy key restricted to the client repo. It runs trusted packaging code, not exported model/test programs. The publisher rechecks source eligibility and the destination tip, verifies archive/file hashes, and makes an ordinary fast-forward commit. A concurrent destination update stops publication.

The source secret is named `CLIENT_REPO_DEPLOY_KEY`; its private value is never committed. Removing that secret or its matching client deploy key stops automatic publication. Client CI has read-only permissions and runs on pushes, pull requests, manual dispatch and a weekly schedule. Source-driven synchronization does not depend on the schedule. GitHub may disable inactive scheduled public workflows; normal push-triggered verification remains the primary mechanism. See GitHub's [workflow event reference](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows) and [deploy-key documentation](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/managing-deploy-keys).

Changes affecting only excluded teaching materials produce no client commit. The manifest therefore identifies the source revision of the last delivered content, which can legitimately precede the latest teaching-only source commit. New runtime files require an explicit selection review before they are exported.

## Local checks

```text
python -m unittest discover -s tests -p "test_client*.py" -v
python tools/check_client_export.py
```

The second command reads committed `HEAD`, not uncommitted edits. It builds a fresh temporary client tree with no source history, runs the retained tests, verifies original flow evidence, calibration and packet results, and generates the offline replay. To check another committed revision, pass `--revision <commit>`.

Regression cases cover immutable source bytes, deterministic output, missing/unsafe/symlink/media paths, executable modes, destination drift, source rollback, managed deletion, excluded-only no-ops, eligibility rejection, archive identity and competing pushes to a real local bare remote. A successful saved-evidence audit preserves the two packet numerical-comparison failures; it does not relabel them as passing native comparisons.

The source's affected lesson was reviewed: its flow explanation remains valid and now distinguishes the concise client delivery from the learning edition. The shared content-review and video queues contained no NetMamba entry during this review. Unrelated pending/failed jobs were left unchanged. No video regeneration is claimed for this packaging change.

## Council review

The [raw council result](client-edition-council.json), run `014bd2af-67d8-4b25-a4cf-6c0b54d92ee7`, is **ESCALATED / UNRATIFIED**, with `mutual: false` and no decision hash. Its file SHA-256 is `1bd338e488f0f1d3977797b5aff8c033bb0871119430ccf2340ba1161176c8e8`. Both seats favored the source-triggered export architecture; the bounded evidence pack omitted files needed to freeze the runnable inventory and scientific check list. No replacement council was launched to evade that limit.

The ordinary session inspected the full omitted files and tested the complete export directly. The retained closure includes `build_cuda.py` and its `build_gb10.py` dependency, asset configuration/fetching, pinned requirements and the dependency-complete test subset. Named scientific checks are original flow artifact identities, training completion/checkpoint binding, per-prediction scores, confusion matrices and aggregates; the unchanged calibration reviewer; and the unchanged packet reviewer with controls and unlabeled inference. That resolves implementation acceptance through direct evidence, without changing the council outcome or claiming broker delivery.

## Executed delivery checks

The [validation receipt](client-edition-validation.json) binds the initial client root `633bc9e3397f876ed940ed8d500eadded1d508f5` to source `4c3a523c8b36e4ac25641d2a7115fa28fe1857c6`. The source suite discovered 458 tests locally: 422 passed, 36 skipped. The exported client discovered 267: 231 passed, 36 skipped locally. All six hosted client jobs passed; Windows reported 37 skips and Linux/macOS 36. All six source jobs also passed, including isolated client export verification.

Fresh checks ran from the client checkout in the existing GB10 environment: 17 packet-model cases with native tests enabled, all seven native operator comparisons, and the complete 1,870,080-parameter flow classifier's synthetic optimizer/update/reload test passed. The first packet-test invocation used the wrong cache directory and failed before native execution; its log remains published with the corrected pass. This required an invocation-path correction, not a model change.

Both prediction programs also executed from the client checkout. Flow inference reproduced all 1,041 class decisions and all saved logits exactly in this invocation. Packet inference validated all 20,000 CIC input rows and predicted the first 128, preserving all 128 classes. **76 of those 128 packet rows failed the strict raw-logit comparison** (`math.isclose`, relative tolerance 1e-4 and absolute tolerance 1e-6); the maximum absolute difference was 0.006159305572509766. This new capped comparison remains separate from the original study's full-test comparison with two failures. These checks use existing data/checkpoints and do not create new benchmark or training results.

The client carries 218 files, approximately 29.95 MB before Git compression, including the same 155 scientific evidence files. Its initial history contains one fresh root and no source ancestry, video, PDF, PowerPoint, captions, raw CSV or checkpoint blob. The private deploy key was stored in the source Actions secret and its local generation copy removed; client force-push and deletion settings are disabled. The live workflow run history records subsequent publication and no-op checks.

## Live update proof

Source commit `f4c011080f904543350c8dfd3f1c63da7f208e0d` added concise verification links to the client README template. Its [six source CI jobs passed](https://github.com/buffbeefalo/netmambaplus-reproduction/actions/runs/34824123213), then the [automatic publication workflow](https://github.com/buffbeefalo/netmambaplus-reproduction/actions/runs/34824453115) completed both preparation and isolated publication. It created client commit `7b92200247e0b5f810a040bf2610ef5c718f1e9e` as one ordinary child of the initial client root. [All six client CI jobs then passed](https://github.com/buffbeefalo/netmambaplus-client/actions/runs/34824528959).

The exact client diff was `README.md` plus `CLIENT_MANIFEST.json`. The manifest identifies the source commit above; all 155 scientific files retained identical bytes. Both client history trees were inspected and contained no excluded media, raw CSVs or checkpoints. Anonymous downloads of the new README and manifest matched their committed bytes.

The earlier [matching-snapshot workflow](https://github.com/buffbeefalo/netmambaplus-reproduction/actions/runs/34823766263) completed preparation and all client checks, reported `changed: false`, and skipped the publisher without creating a commit. The local regression suite separately tests excluded-only source changes, forged destination manifests, source rollback and real competing pushes. Final source-side audit/plan updates are intentionally excluded from the client payload; its source marker advances only when delivered content or export policy changes.
