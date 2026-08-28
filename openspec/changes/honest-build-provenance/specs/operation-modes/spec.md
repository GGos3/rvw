## ADDED Requirements

### Requirement: CLI exposes honest build identity

`rvw --version` MUST show the semantic version and embedded build identifier,
MUST show source provenance only when it was captured at build time, and MUST
never claim a source commit or stale state that cannot be verified. A
source-build comparison MAY emit one non-fatal warning per run only when the
installed provenance and current source history prove the installed commit is
behind, and that warning MUST include `uv tool install --reinstall --from
<repo> rvw`.

#### Scenario: Commit provenance is unavailable

- **WHEN** the running distribution lacks verifiable build-time commit data
- **THEN** version output identifies the build without fabricating a commit and
  no ahead/behind warning is emitted

#### Scenario: Source checkout is a verified descendant

- **WHEN** local `direct_url.json` identifies a checkout whose `HEAD` is a
  descendant of the embedded clean build commit
- **THEN** a new run emits one warning containing the concrete reinstall command
  and continues normally
