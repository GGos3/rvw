## ADDED Requirements

### Requirement: Release publication preserves the container build contract

The release workflow MUST build the image from the checked-out tag with
`RVW_IMAGE_VERSION` set to the normalized release version and `CODEX_BASE_URL` set to
the documented empty, non-personal default. It MUST verify that the normalized tag,
package metadata, and runtime version agree before pushing the image, and the build MUST
NOT receive a Codex credential, PyPI credential, or personal endpoint.

#### Scenario: Tagged image is built

- **WHEN** release tag `vX.Y.Z` reaches the image publication job
- **THEN** the image is built from that tagged source with `RVW_IMAGE_VERSION=X.Y.Z` and an empty `CODEX_BASE_URL`

#### Scenario: Release versions diverge

- **WHEN** the normalized tag version does not match package metadata or the runtime version
- **THEN** image publication exits nonzero before the image build or registry push
