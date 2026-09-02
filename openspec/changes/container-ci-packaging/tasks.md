## 1. Contracts and failing tests

- [x] 1.1 Add failing tests for Codex config materialization, precedence, TOML escaping, permissions, argument preservation, and secret exclusion.
- [x] 1.2 Add failing repository-contract tests for the multi-stage Dockerfile, pinned toolchain, packaged lane install, secret-free image, and required runtime tools.
- [x] 1.3 Add failing workflow-contract tests for `workflow_call`, immutable head checkout, base fetch, token mapping, read-only mount, exact auto invocation, minimal permissions, and unmasked exit status.

## 2. Container implementation

- [x] 2.1 Implement the stdlib-only container entry point and stable Codex config template.
- [x] 2.2 Add the multi-stage Dockerfile and build-context exclusions, installing rvw non-editably from source with Python 3.12, Node 24, Codex 0.152.0, and required tools.
- [x] 2.3 Build the local image and inspect its size, base/tool versions, entry-point behavior, packaged lanes, and absence of baked credentials.
- [x] 2.4 Add a tested closed sandbox selector that remains read-only on hosts and selects the measured danger-full-access fallback only in the project image.

## 3. GitHub Actions and operator documentation

- [x] 3.1 Add the reusable review workflow with required image input, immutable PR checkout, base fetch, generic secret mapping, read-only mount, and direct auto status propagation.
- [x] 3.2 Document the container working-directory convention, `pull_request_target`/CODEOWNERS trust contract, version pinning, COMMENT behavior, and exact thin caller example.
- [x] 3.3 Extend rvw's CODEOWNERS with explicit packaging and reusable-workflow ownership entries without changing any target repository.

## 4. Live container measurement

- [x] 4.1 Create two external detached bori clones at `5d4d3cb64` and run the containerized agentic review with env-only credentials and mounted evidence output.
- [x] 4.2 Record env-only authentication without `auth.json`, inner read-only sandbox behavior (or exact container-only fallback evidence), valid-lane totals, and receipt coverage in change context.

## 5. Specification synchronization and verification

- [x] 5.1 Synchronize implemented delta requirements and adjacent rationale/evidence into the main OpenSpec specs without archiving or modifying other active changes.
- [x] 5.2 Run strict change validation and `openspec validate --specs`, fixing every failure.
- [x] 5.3 Run `uv run ruff check .`, `uv run ruff format --check .`, `uv run ty check`, and `uv run pytest -q -m "not live"` as bare commands.
- [x] 5.4 Write `/tmp/rvw-phase2-report.md` with files, gates, image inspection, smoke measurements/evidence, exact caller snippet, deviations, and open questions.
- [x] 5.5 Review the complete diff, verify the branch remains stacked on `882204d`, and create one local reviewable commit without pushing or opening a PR.
