# release-automation

## Purpose

Define synchronized release preparation, verified automated and emergency release entry points, trusted PyPI publication, and repository release policy.

## Requirements

### Requirement: Release preparation synchronizes every version surface

The project MUST use release-please with the Python release type to derive releases from Conventional Commits, update `CHANGELOG.md`, and synchronize the versions in `pyproject.toml`, `src/rvw/_version.py`, and the root `rvw` package entry in `uv.lock`.

#### Scenario: Release PR is prepared

- **WHEN** releasable Conventional Commits accumulate on `main`
- **THEN** release-please opens or updates a release PR in which every checked-in rvw version surface has the same proposed version

### Requirement: Automated releases use a personal access token

The release-please workflow MUST authenticate with the `RELEASE_PLEASE_TOKEN` personal access token so that the tags it pushes trigger the tag-event release workflow, and it MUST NOT fall back to the repository `github.token` or publish through a reusable-workflow call.

#### Scenario: Release PR is merged

- **WHEN** a release PR is merged and release-please pushes the version tag with the personal access token
- **THEN** the pushed tag itself triggers the release workflow without any workflow-call chain

#### Scenario: PyPI trusted publishing rejects reusable callers

- **WHEN** the publish job requests its OIDC identity token
- **THEN** the token claims identify the tag-triggered release workflow itself, which PyPI trusted publishing accepts, rather than a reusable workflow invocation, which PyPI rejects

### Requirement: Automated and emergency releases share one verified chain

The release workflow MUST be triggered by pushed `v*` tags as its only entry point, whether release-please or a maintainer pushes the tag, and every release MUST run the same gates, tag-to-package version checks, build, PyPI publish, and GitHub release-asset stages.

#### Scenario: Release-please creates a release

- **WHEN** release-please pushes a release tag after the release PR merges
- **THEN** the tag-triggered release workflow runs the full chain and grants the OIDC publication job `id-token: write`

#### Scenario: Maintainer pushes an emergency tag

- **WHEN** a maintainer pushes a correctly synchronized `vX.Y.Z` tag
- **THEN** the tag-triggered workflow executes the same release chain using `vX.Y.Z` as its release tag

### Requirement: Release builds fail closed on version mismatch

The release workflow MUST verify that its normalized tag version matches both Python package metadata and the rvw runtime version before building or publishing artifacts.

#### Scenario: Checked-in versions diverge

- **WHEN** the release tag, `pyproject.toml` version, and runtime `__version__` are not identical after removing the tag's `v` prefix
- **THEN** the release workflow exits nonzero before building or publishing

### Requirement: PyPI publication uses trusted publishing

The release workflow MUST publish the built distribution from the protected `pypi` environment with GitHub OIDC and MUST NOT require a PyPI API token.

#### Scenario: Verified build is published

- **WHEN** release gates and version verification pass and the distribution builds successfully
- **THEN** the publish job requests an OIDC identity token and uploads the artifact through PyPI trusted publishing

### Requirement: Changelog and commit policy support deterministic releases

The contribution policy MUST require Conventional Commits with `fix` producing patch intent, `feat` producing minor intent, and `feat!` or a `BREAKING CHANGE` footer producing major intent, and MUST reserve direct `CHANGELOG.md` edits for release-please.

#### Scenario: Contributor prepares a behavioral pull request

- **WHEN** a contributor proposes behavioral work
- **THEN** the contribution guidance requires an OpenSpec change, a Conventional Commit, green CI, a clean `rvw gate --target <pr>` review, and a mergeable clean state

### Requirement: Repository maintenance automation stays scoped to rvw

The repository MUST configure weekly uv and GitHub Actions dependency updates, conservative stale handling with `pinned` and `security` exemptions, and path-based labels for code, tests, OpenSpec, and GitHub configuration without adding unrelated Docker, Bun, beta-channel, Windows-startup, all-contributors, or Codex-review automation.

#### Scenario: Weekly maintenance runs

- **WHEN** scheduled repository maintenance executes
- **THEN** it considers only rvw's Python and GitHub Actions dependencies and preserves protected issues and pull requests from stale closure
