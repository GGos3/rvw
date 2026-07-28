# Release automation context

## Purpose and scope

This capability governs repository release preparation and publication rather than rvw's runtime review pipeline. Normative behavior is in [spec.md](spec.md).

## Key decisions

- The 2026-07-28 v0.2.0 incident demonstrated that manually updating `src/rvw/_version.py` while leaving `pyproject.toml` stale can rebuild an already-published distribution. release-please now writes every version surface, with `tests/test_version_sync.py` retaining a regression guard.
- The release-please manifest starts at the already-published `0.2.0`, so automation proposes only later versions.
- GitHub does not start a new workflow from a tag or release created with the repository `GITHUB_TOKEN`. The release-please job therefore calls `release.yml` as a reusable workflow when `release_created` is true instead of relying on the tag event.
- `release.yml` remains tag-triggerable for emergency operation. Both entry points resolve one explicit release tag, check out that tag, run the same gates, and compare the tag against package and runtime versions before building.
- PyPI publication remains in the `pypi` GitHub environment and uses OIDC trusted publishing. `skip-existing` makes an identical PAT-triggered duplicate run harmless, but version mismatches still fail before build.
- release-please creates the GitHub Release before the reusable publication chain runs. The final job uploads artifacts to that release, while the emergency tag path creates the release when it does not exist.

## Operational constraints

- `RELEASE_PLEASE_TOKEN` is optional. Without it, release preparation and publishing work using `github.token` plus the direct reusable call. A PAT can cause release-please-authored events, including release PR checks, to trigger normally.
- `CHANGELOG.md` is generated and maintained by release-please and must not be manually edited.
- Required repository labels are administrative GitHub state and are not created by these files.
- The PyPI trusted publisher must continue to authorize the `pypi` environment and `.github/workflows/release.yml`.

## Excluded infrastructure

rvw has no Docker or Bun release surfaces and does not carry beta-channel, Windows-startup, all-contributors, or Codex-review-label automation. Its own `rvw gate` is the required review path.

## Historical note

Before this change, a `v*` push independently ran gates, built the package, published to PyPI, and then created a GitHub Release. Version updates and changelog preparation were manual, and the version check inspected only `src/rvw/_version.py`. The synchronized release PR and dual package/runtime validation replace that split contract.
