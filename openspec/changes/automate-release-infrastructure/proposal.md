## Why

The v0.2.0 release exposed a split version source of truth: the runtime version changed while the package metadata did not, so the release workflow built and attempted to republish a stale artifact. Release preparation and repository maintenance need automation that keeps every version surface synchronized and preserves the existing verified OIDC publishing path.

## What Changes

- Add release-please automation that derives versions from Conventional Commits and synchronizes `pyproject.toml`, `src/rvw/_version.py`, and the rvw package entry in `uv.lock`.
- Convert the existing gated build, PyPI trusted publish, and GitHub release chain into a reusable workflow invoked directly after release-please creates a release, while preserving the emergency tag-push entry point.
- Add Dependabot, stale-item handling, path-based PR labeling, contribution and security policies, ownership, and issue/PR templates tailored to rvw.
- Require contributors to use Conventional Commits, OpenSpec changes for behavioral work, and the rvw PR gate; reserve `CHANGELOG.md` updates for release-please.

## Capabilities

### New Capabilities

- `release-automation`: Automated version synchronization, release creation, gated artifact building, OIDC publication, emergency tag releases, and repository release policy.

### Modified Capabilities

None.

## Impact

The change affects GitHub Actions workflows and repository configuration, package version metadata annotations, contribution policy, and release specifications. It adds no runtime dependency, does not change the rvw CLI or external review registry, and requires no PyPI credential beyond the existing trusted-publishing environment.
