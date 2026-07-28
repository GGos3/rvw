## 1. Release contract and regression coverage

- [x] 1.1 Extend version synchronization regression coverage to include the rvw package entry in `uv.lock` and the release-please annotation/configuration contract.
- [x] 1.2 Add the release-please config, bootstrapped manifest, and annotated runtime version updater.

## 2. Reusable release pipeline

- [x] 2.1 Convert the gated build, tag-version validation, PyPI OIDC publish, and GitHub release stage to a tag-input reusable workflow while retaining the `v*` push trigger.
- [x] 2.2 Add the main-push release-please workflow with optional PAT fallback and a same-run reusable release call carrying explicit OIDC permission.
- [x] 2.3 Validate both automated and manual-tag workflow contracts, including existing-release artifact upload behavior.

## 3. Repository automation and hygiene

- [x] 3.1 Add scoped uv and GitHub Actions Dependabot configuration.
- [x] 3.2 Add contribution, security, ownership, pull request, and issue templates tailored to rvw and its OpenSpec/review gates.
- [x] 3.3 Add conservative stale-item automation and path-based PR labeling.

## 4. Specifications and verification

- [x] 4.1 Synchronize the release-automation main specification and adjacent context with the implemented behavior.
- [x] 4.2 Parse every added or changed workflow YAML and validate release-please JSON and version updater annotations.
- [x] 4.3 Run ruff check, ruff format check, ty, offline pytest, and OpenSpec validation as bare commands.
- [x] 4.4 Inspect the final diff for unrelated changes and confirm the external registry and codex-lb reference remain untouched.
