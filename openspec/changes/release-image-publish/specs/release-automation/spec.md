## MODIFIED Requirements

### Requirement: Automated and emergency releases share one verified chain

The release workflow MUST be triggered by pushed `v*` tags as its only entry point,
whether release-please or a maintainer pushes the tag, and every release MUST run the
same gates, tag-to-package version checks, build, PyPI publish, GitHub release-asset,
and GHCR image-publication behavior. PyPI and GHCR publication MUST proceed independently
after their shared gates so failure of either publication path does not prevent the
other path from running.

#### Scenario: Release-please creates a release

- **WHEN** release-please pushes a release tag after the release PR merges
- **THEN** the tag-triggered release workflow runs the full chain, grants the PyPI publication job `id-token: write`, and grants only the GHCR publication job `packages: write`

#### Scenario: Maintainer pushes an emergency tag

- **WHEN** a maintainer pushes a correctly synchronized `vX.Y.Z` tag
- **THEN** the tag-triggered workflow executes the same PyPI and GHCR release behavior using `vX.Y.Z` as its release tag

### Requirement: Container consumers pin a versioned image reference

The reusable review workflow MUST require its caller to provide an image reference and
MUST NOT supply a floating default image. Target-repository guidance MUST show both a
release-version tag pin for explicit upgrades and an immutable digest pin derived from
release output.

#### Scenario: Target repository adopts the workflow

- **WHEN** a target repository creates its thin `pull_request_target` caller
- **THEN** the caller supplies an explicit release-version image tag or its published digest rather than inheriting a mutable image default from rvw

## ADDED Requirements

### Requirement: Release tags publish traceable GHCR images

After release gates pass, the tag-triggered workflow MUST build the checked-out release
tag without persisting checkout credentials or using Codex or PyPI credentials,
authenticate to GHCR with the job-scoped `GITHUB_TOKEN`, and publish the same image as
both `ghcr.io/soju06/rvw:v<version>` and `ghcr.io/soju06/rvw:latest`. The GHCR job MUST
receive job-scoped `contents: read` and `packages: write` permissions, and no other
release job MUST receive `packages: write`. The job MUST expose the registry-reported
digest as a job output and record a digest-pinnable image reference in its run summary
or release notes.

#### Scenario: Release image publication succeeds

- **WHEN** shared release gates and image version verification pass for tag `vX.Y.Z`
- **THEN** GHCR receives tags `vX.Y.Z` and `latest` for the same image digest and the workflow exposes `ghcr.io/soju06/rvw@sha256:<digest>` to consumers

#### Scenario: Image publication fails independently

- **WHEN** the GHCR build or push fails after shared gates
- **THEN** its job fails without cancelling, skipping, or blocking the independent PyPI build and publication path
