## 1. Specification and fixtures

- [x] 1.1 Add the lane-format, source-precedence, base-ref, escape-hatch, and lint requirements to the change spec delta.
- [x] 1.2 Port the current external base/scope/dynamic lane documents into packaged data without changing rule prose.

## 2. Parser and source loading

- [x] 2.1 Implement strict single-file lane parsing with heading-derived rule IDs and activation paths.
- [x] 2.2 Implement packaged-lane discovery and base-ref-pinned `.rvw/` tree/blob loading, including optional base-ref policy loading.
- [x] 2.3 Merge packaged, repository, and deprecated external sources with collision precedence and warnings while preserving legacy parsing.

## 3. CLI and reporting

- [x] 3.1 Route plan/review/sample/lanes commands through the effective lane set without changing execution semantics.
- [x] 3.2 Add `--allow-worktree-rules` and non-SoT metadata/report warnings.
- [x] 3.3 Add `rvw lanes lint` with machine-readable reason codes and exit status 0/1.

## 4. Tests and verification

- [x] 4.1 Add parser, precedence, base-ref, worktree-isolation, and lint regression tests.
- [x] 4.2 Run Ruff, formatting, ty, non-live pytest, and OpenSpec validation gates.
