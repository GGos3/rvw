## Why

`rvw sample --fixture` currently wraps an already-unified-diff fixture in a second `/dev/null` diff, which can turn a multi-file review into one oversized file segment that is entirely excluded. Sampling then reviews no diff and can report `PASS`, making missing coverage indistinguishable from a successful gap check.

## What Changes

- Pass unified-diff fixtures directly into the shared exclusion and chunk planner while preserving the existing `/dev/null` conversion for ordinary source-file fixtures.
- Reject sampling before model dispatch when budgeting retains zero review characters, with an exit-2 machine-readable error that includes excluded paths and reasons.
- Confirm whether production discovery can reach the same zero-retained state and apply the same fail-closed invariant there if it can.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `operation-modes`: Define fixture normalization and require sampling to fail closed when no reviewable diff remains after exclusions.
- `discovery`: Require production discovery to stop before dispatch when exclusions retain no review characters.

## Impact

The change affects sample fixture loading in `rvw/cli.py`, sample/discovery diff-budget integration as applicable, CLI error serialization and exit behavior, and regression tests. It does not modify the external runtime registry or add dependencies.
