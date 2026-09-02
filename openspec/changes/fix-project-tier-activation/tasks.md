## 1. Regression Coverage

- [x] 1.1 Add an effective-registry regression test proving a path-scoped project lane stays inactive for unmatched paths, activates for matched paths, and a predicate-free project lane stays active.
- [x] 1.2 Run the focused regression test before implementation and record the expected failure.

## 2. Registry Implementation

- [x] 2.1 Update effective-registry activation so only base and dynamic lanes bypass path predicates while project and scope lanes share the existing glob matching behavior.
- [x] 2.2 Run the focused regression test and confirm all project activation cases pass.

## 3. Specification and Verification

- [x] 3.1 Confirm the implementation and regression coverage remain synchronized with the lane-registry delta while the change is active.
- [x] 3.2 Run strict validation for this OpenSpec change.
- [x] 3.3 Run Ruff lint and formatting checks.
- [x] 3.4 Run the ty type-check gate.
- [x] 3.5 Run the complete non-live pytest suite.
- [x] 3.6 Validate all OpenSpec specifications.
