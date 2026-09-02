## Why

rvw documents a version-pinned GHCR image for its reusable review workflow, but the
release rail currently publishes only Python and GitHub Release artifacts. Every release
tag needs to publish the documented image automatically so container consumers receive
the same continuous-delivery guarantee as PyPI consumers.

## What Changes

- Add an independent post-gates release job that builds the tagged source and publishes
  `ghcr.io/soju06/rvw:v<version>` and `ghcr.io/soju06/rvw:latest` with `GITHUB_TOKEN`.
- Expose the registry-reported image digest as a job output and run summary so consumers
  can pin an immutable image reference.
- Keep GHCR publication independent of PyPI publication after shared gates, with no Codex
  or PyPI secret required by the image build.
- Document automatic release publication, digest pinning, and the one-time GHCR package
  visibility setting.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `release-automation`: Extend every tag-triggered release with independent, digest-visible
  GHCR publication of versioned and latest image tags.
- `container-ci-packaging`: Define how the release rail builds and publishes the existing
  secret-free image using its documented version and endpoint build arguments.

## Impact

This changes `.github/workflows/release.yml`, release/container repository contract
tests, container adoption documentation, and the two synchronized OpenSpec capabilities.
It writes package versions to GHCR at release time but does not alter release-please,
PyPI trusted publishing, the external runtime registry, or target-repository settings.
