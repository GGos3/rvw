## Why

The enum/free sampling verdict currently treats replica-level site variation as a closed-rule recall failure, producing false `REVIEW` results and nonzero exits even when the free variant invents no rule IDs. Separately, the PR gate procedure remains copy-pasted shell that can omit coverage and disposition checks, review a stale checkout, or publish an unreconstructable decision; six dogfood rounds demonstrated that these invariants need to be enforced by rvw itself.

## What Changes

- Make novel free-variant rule IDs the primary sampling gap signal and report in-enum site differences separately as replica variance.
- Preserve the `PASS`/`REVIEW` sample verdict vocabulary for compatibility, while redefining `REVIEW` to mean a novel rule-ID gap only and making ordinary variance exit successfully.
- Add a fail-closed `rvw gate --target <pr>` workflow that captures immutable PR anchors, provisions and verifies a clean disposable checkout, and executes the review pipeline exactly once.
- Validate lane coverage against the activated plan and validate exactly one keyed disposition for every CONFIRMED or UNCERTAIN finding.
- Promote the existing deterministic merge group key as the stable public finding ID used by dispositions and verdict artifacts.
- Generate a reconstructable gate verdict artifact and GitHub COMMENT payload from persisted artifacts, retaining dry-run-by-default publication and the bounded 422 fallback.
- Require explicit owner-authored reasons for accepted blockers without allowing rvw to approve either the acceptance or the pull request.

## Capabilities

### New Capabilities

- `pr-gate`: Anchor-safe checkout provisioning, single review execution, coverage and disposition validation, reconstructable verdict generation, exit behavior, and COMMENT-only publication for pull-request gates.

### Modified Capabilities

- `operation-modes`: Sampling verdict and exit behavior changes from site-based review to novel-rule-ID gap detection with site variance as non-failing information.
- `lane-registry`: Pending-lane promotion is based on absence of novel free-variant rule IDs rather than absence of free-only sites.
- `finding-model`: The deterministic collapse group key becomes the documented public finding ID consumed by gate artifacts and dispositions.
- `reporting`: Gate publication adds a reconstructable verdict body while retaining the existing COMMENT-only, dry-run, and bounded fallback safety properties.

## Impact

The change affects sampling models and CLI output, merge/report identity presentation, run artifacts, target/checkout orchestration, publication payload construction, and adds gate/disposition models plus tests. It does not modify the external `~/.hermes/review/` registry, add dependencies, change GitHub review event types, or publish during tests.
