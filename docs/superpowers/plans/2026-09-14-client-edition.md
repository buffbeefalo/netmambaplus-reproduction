# Client edition implementation plan

**Goal:** Publish a runnable, concise public client repository and continuously update it from the existing development repository.

**Architecture:** A reviewed explicit file list and client text templates generate a fresh-history snapshot. Shared code/evidence retains its committed bytes. Source CI verifies both editions before a dedicated client-only credential publishes an ordinary fast-forward commit. Source remains the development location; client drift blocks publication.

**Stack:** Python standard library, Git, GitHub Actions and an SSH deploy key scoped to the client repository.

**Authority and review:** The user explicitly requested creation, public visibility and ongoing updates. Council run `014bd2af-67d8-4b25-a4cf-6c0b54d92ee7` reviews the packaging and synchronization tradeoffs. Its actual outcome is retained separately; direct implementation uses the standing authorization and does not imply mutual ratification.

## Constraints

- Retain runnable flow/packet training, inference, controls, calibration, runtime checks and saved scientific evidence.
- Omit media, decks, narration/presenter scripts, teaching assets, raw data and inherited weights.
- Preserve shared scientific code and evidence bytes, including recorded failures and limitations.
- Use Python 3.10/3.12 for portable checks; do not claim a new GPU backend or new training run from packaging tests.
- Publish only verified source `main`, serialize publication, reject drift/rollback and never force-push.
- Keep the client history independent so omitted materials are absent from its earlier commits too.

## Implementation and acceptance

- [ ] Add `configs/client-manifest.json`, `client/*.in`, `tools/export_client.py` and `tools/sync_client.py`. Test real temporary Git repositories before implementation with `python3 -m unittest discover -s tests -p test_client_export.py`. Cover committed bytes, deterministic output, missing paths, symlinks, media, traversal, existing directories, managed removal, untracked/committed client drift, rollback and excluded-only no-ops.
- [ ] Add `tools/verify_client.py` for delivered-file identity and original flow-result arithmetic; reuse existing packet and calibration reviewers. Run the exported test suite and all three evidence checks in a fresh temporary directory without the original Git history.
- [ ] Extend source CI to check the generated client edition on all six OS/Python combinations. Publish only after that matrix succeeds on source `main`. Export a read-only client CI workflow with the same portable matrix.
- [ ] Review the client README, setup, results and notice against executed commands and retained evidence. Update the source README, lesson and every-file guide; inspect shared lesson-review/video queues without clearing unrelated work.
- [ ] Create `buffbeefalo/netmambaplus-client` publicly with a fresh root commit. Install its dedicated write deploy key as a source Actions secret without printing or committing private material. Protect client main from force pushes/deletion.
- [ ] Demonstrate a real source update propagating through Actions to the client. Confirm the source revision, changed file hashes, unchanged experiment bytes, fresh-history scope, client CI and a clean no-op repeat. Publish the actual run links and outcome in a source-side delivery record.
