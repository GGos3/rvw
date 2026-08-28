## Why

An installed rvw executable currently identifies only its semantic version. A
source checkout can move ahead of the installed artifact without any durable
way to prove which code produced a run, and consulting Git at runtime would
make the identity mutable and unverifiable.

## What Changes

- Add build-time provenance constants and a thin PEP 517 backend that embeds a
  deterministic source digest plus only build-time-verifiable Git facts.
- Add a frozen, strict `BuildProvenance` model, cached runtime accessor, honest
  version label, and a guarded stale-install warning.
- Persist build identity in every `RunSummary`, expose it in review JSON and
  reports, and emit the stale-install warning once when a new pipeline run is
  created.
- Add deterministic tests for schema, identity, stale detection, and backend
  rewriting, without changing fail-closed status derivation.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `operation-modes`: expose honest build identity and stale-install guidance.
- `reporting`: persist immutable build identity alongside every run summary.

## Impact

Affected files are the PEP 517 build configuration and wrapper, provenance and
summary/report/CLI integration, and their offline tests and OpenSpec deltas.
Review status, failed-lane derivation, adjudication retry, package version,
release automation, and the external runtime registry remain unchanged.
