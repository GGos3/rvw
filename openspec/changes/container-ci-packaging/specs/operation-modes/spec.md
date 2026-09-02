## MODIFIED Requirements

### Requirement: Packaging exposes the rvw CLI

The project MUST package as the PyPI distribution `rvw`, MUST require Python 3.12 or
newer, and MUST expose the Typer app at the `rvw` console entry point through the
uv-managed build. The project container MUST install that distribution from repository
source, include the distribution's packaged common lanes, and expose the same console
entry point as its argument-preserving container entry point.

#### Scenario: Installed package is invoked

- **WHEN** the distribution is installed in a supported Python environment
- **THEN** the `rvw` command resolves to `rvw.cli:app`

#### Scenario: Containerized package is invoked

- **WHEN** a caller starts the project image with `auto --target <sha> --repo-dir <checkout>`
- **THEN** the image invokes the installed `rvw` console entry point with those arguments and packaged common lanes available

## ADDED Requirements

### Requirement: CI composition preserves auto and publication semantics

A containerized GitHub Actions invocation of `rvw auto` MUST retain the ordinary
deterministic PASS/BLOCK exit contract and COMMENT-only publication behavior. The CI
composition MUST NOT convert a BLOCK status to success, emit an approval, or make COMMENT
publication the check result.

#### Scenario: CI auto finds policy blockers

- **WHEN** containerized auto evaluation returns BLOCK and publishes finding narratives
- **THEN** the workflow job fails from auto's exit status and the published review remains a COMMENT
