# Client delivery — one supported CSV workflow

The [client repository](https://github.com/buffbeefalo/netmambaplus-client) delivers the joint pretrained **packet adaptation using both supplied CSVs**. The [full client guide](../customer/client-project-guide.md) explains the paper, data, model, setup, actual tests, each component and handoff. This reproduction repo is the development and learning source.

## Current contents and dependency choices

The [explicit selection](../../configs/client-manifest.json) exports 117 source paths and six client templates: **124 delivered files including CLIENT_MANIFEST.json**. It retains all **75 packet-study evidence files**, the CSV profile, packet code/tests, native build/runtime tools and acquisition helpers. It excludes flow prediction/evaluation/replay, calibration, flow datasets/evidence and teaching media from the current client tree.

`packet_model.py` imports `repro.py` for verified upstream identity and file hashing. The native builders also depend on that module and its default source configuration, `configs/ciciot2022.json`. These remain internal dependencies. Their historical flow orchestration is not a supported client route. Keeping these helpers avoids changing the frozen packet implementation merely to reorganize packaging.

Default acquisition now uses [configs/packet-assets.json](../../configs/packet-assets.json), containing only the pinned pretrained initialization. The fetcher supports explicit asset selection and a separate inventory for historical research use. The active setup does not download a flow dataset. Raw CSVs and locally trained packet checkpoints remain external; inherited asset terms are unchanged.

The client verifier retains strict delivered-file inventory checks, then recomputes the complete packet study, controls and unlabeled comparison. Its demo renders recorded joint-model groups from both sources with the original group/row weighting and contradictory label counts. The new packet-specific native gate takes the verified prepared directory and requires actual native tests without skips.

## Automatic updates

The [publication workflow](../../.github/workflows/client-sync.yml) reacts to successful **CPU verification** runs from canonical source `main` pushes. It checks the exact tested SHA against current remote main, rejects PR/stale events and serializes publication. Manual **Run workflow** recovery uses the same rules.

The preparation job has read access: it regenerates the previous source snapshot, rejects destination drift/rollback, stages selected additions/updates/removals, runs client tests/evidence verification and generates the packet demo. A separate publisher receives only the checked archive and a dedicated client-repo SSH deploy key. It rechecks source eligibility and destination tip, verifies hashes, and makes an ordinary fast-forward commit without executing exported model/test programs with the write key. Concurrent client edits stop publication.

The source Actions secret is `CLIENT_REPO_DEPLOY_KEY`; its private value is never committed. Client CI is read-only and runs on pushes, PRs, manual dispatch and a weekly schedule. Source-driven updates do not depend on the schedule. Edit client prose through source `client/*.md.in` templates; new runtime files require selection review. Do not force-push or delete drift checks to clear an error.

Excluded-only teaching edits produce no client commit. The manifest's source marker can therefore precede the latest source commit. The move to packets removes the old flow files from the current client tree by the existing managed-deletion path; earlier client commits retain their history.

## Verification and records

```text
python -m unittest discover -s tests -p "test_client*.py" -v
python tools/check_client_export.py
```

The exporter check reads **committed HEAD**, not uncommitted files. It builds a fresh no-Git client tree, rejects flow entry points/evidence, runs the retained suite, checks packet CLIs and full evidence, and generates the offline packet demo. Use `--revision <commit>` to specify another candidate.

The [single-workflow audit](packet-only-handoff.md) records new source/client checks and publication. Raw [packet runtime receipt](packet-checks/native-receipt.json), [test log](packet-checks/native-tests.log), [model probe](packet-checks/native-model-probe.json), [acquisition record](packet-checks/acquisition.json) and [browser checks](packet-checks/browser.json) support their exact scopes. No new six-arm training or scientific accuracy result is claimed.

The model's frozen packet protocol and scientific evidence are unchanged. The original full packet comparison retains two strict logit failures. The [earlier client audit](client-edition-validation.json) separately retains 76 failures in its capped 128-row check despite class agreement. Recomputing evidence does not erase either scope.

## Council review

Single-workflow council run `f53037cd-44e6-4b36-9930-8d7abaaace81` ended **ABORTED**, after Claude's position call returned HTTP 529 server overload. The [raw review record](packet-only-council.json) retains the state, failure and Astra's non-mutual position. No provider retry/replacement or consensus claim was made. Direct implementation uses the user's standing authorization.

The original client architecture council ended ESCALATED / UNRATIFIED. Its historical record remains unchanged; neither direct implementation nor later tests turn it into consensus. Shared lesson references were reviewed for the single packet workflow. Historical flow/video material stays labeled and its frozen coverage is not updated to imply new video content.

## Live update proof

The [initial delivery and successful source-to-client update](client-edition-initial.md#live-update-proof) are historical proof of the publication mechanism. That earlier edition included two model routes and 218 files; its test counts and native receipts belong to that scope. Current packet-only publication is recorded in the [single-workflow audit](packet-only-handoff.md), and the [Actions history](https://github.com/buffbeefalo/netmambaplus-reproduction/actions/workflows/client-sync.yml) shows subsequent runs.
