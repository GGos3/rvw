## ADDED Requirements

### Requirement: Container consumers pin a versioned image reference

The reusable review workflow MUST require its caller to provide an image reference and
MUST NOT supply a floating default image. Target-repository guidance MUST show a
release-version tag pin so image upgrades remain an explicit caller change. Building or
publishing that image in the release workflow is outside this requirement.

#### Scenario: Target repository adopts the workflow

- **WHEN** a target repository creates its thin `pull_request_target` caller
- **THEN** the caller supplies an explicit release-version image tag rather than inheriting a mutable image default from rvw
