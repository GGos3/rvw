---
lane: hygiene
tier: base
cost: normal
severity_cap: blocker
validation: pending
---

# hygiene

Find mechanical hygiene defects: code slop, critical test/CI mistakes, and
dependency-manifest drift. Report only defects visible in the changed code and
its immediate context. Do not report style preferences.

## Code slop

Mechanical hygiene defects and lazy shortcuts that erode a codebase.

- `slop/sot-violation` — a value/shape/constant that has a declared source of
  truth (schema file, registry, config module, generated artifact) is
  re-declared, hand-copied, or shadowed instead of imported/derived from the SoT.
- `slop/typing-bypass` — `as any`, `# type: ignore`, unchecked casts, loosening
  a type to silence the checker instead of fixing the shape.
- `slop/untraceable-fallback` — a fallback/catch path that swallows the original
  error or produces a state that cannot be debugged or traced back to its cause
  (no log, no error chaining, silent default).
- `slop/excessive-fallback` — fallback chains guarding conditions that cannot
  legitimately occur, or fallbacks for required dependencies that should fail
  fast instead.
- `slop/name-guess-fallback` — purposeless alias fallbacks that try several
  spellings of the same field (`createAt ?? createdAt ?? created_at`) instead of
  fixing the producer or mapping at one declared boundary.
- `slop/duplicate-object-key`, `slop/dead-assignment`,
  `slop/copy-paste-remnant`, `slop/both-paths-kept` — mechanical remnants:
  duplicated keys/declarations, values overwritten before use, leftover
  copy-paste artifacts, old and new code paths both kept alive.

## Test / CI integrity

Find CRITICAL mistakes in tests and CI configuration. Minor imperfections are
explicitly out of scope: assume a small flaw is acceptable until it can cause
a real incident.

`test-ci/critical-flaw` — report only defects in these classes:

- a test that can never fail (asserts a tautology, mocks the unit under test,
  swallows its own assertion errors)
- a test asserting the wrong behavior (would keep passing if the feature broke)
- CI gates that fail open: steps whose failure does not fail the job,
  `continue-on-error` on a correctness gate, exit codes masked by pipes
- coverage theater: the changed behavior's failure mode has no test at all
  while superficially related tests exist
- CI running against the wrong artifact (stale build, wrong branch/base,
  cache poisoning the gate)
- secrets/credentials exposure through CI logs or test fixtures

If a finding does not fit these classes, it is minor by definition — do not
report it.

## Dependency manifests

Only applies when the diff touches a dependency manifest (package.json,
pyproject.toml, go.mod, Cargo.toml, Gemfile, ...); report nothing from this
section otherwise.

- `deps/unused-added` — a library added to the manifest in this change but
  never imported or used by the changed code.
- `deps/orphaned-remaining` — this change removes the last real usage of a
  library but leaves it in the manifest, or removes a feature while its
  now-unused supporting dependency stays behind.

Verify by searching for imports/usages, not by assumption. Lockfile-only churn
is not a finding.

## rule: slop/sot-violation

The rule is defined by the lane guidance above.

## rule: slop/typing-bypass

The rule is defined by the lane guidance above.

## rule: slop/untraceable-fallback

The rule is defined by the lane guidance above.

## rule: slop/excessive-fallback

The rule is defined by the lane guidance above.

## rule: slop/name-guess-fallback

The rule is defined by the lane guidance above.

## rule: slop/duplicate-object-key

The rule is defined by the lane guidance above.

## rule: slop/dead-assignment

The rule is defined by the lane guidance above.

## rule: slop/copy-paste-remnant

The rule is defined by the lane guidance above.

## rule: slop/both-paths-kept

The rule is defined by the lane guidance above.

## rule: test-ci/critical-flaw

The rule is defined by the lane guidance above.

## rule: deps/unused-added

The rule is defined by the lane guidance above.

## rule: deps/orphaned-remaining

The rule is defined by the lane guidance above.
