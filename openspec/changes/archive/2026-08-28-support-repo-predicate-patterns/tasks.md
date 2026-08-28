## 1. Regression Coverage

- [x] 1.1 Add activation tests for a legacy exact repository string, the APIFuse provider-family glob incident, list-OR matches, and repository mismatches.
- [x] 1.2 Add combined repository/path tests proving the predicates retain AND semantics.
- [x] 1.3 Add schema tests proving repository pattern lists are accepted while invalid non-string shapes remain rejected.
- [x] 1.4 Run the focused registry tests and record the expected pre-implementation failure.

## 2. Registry Implementation

- [x] 2.1 Extend `LayerPredicate.repo` to accept a strict string or list of strings.
- [x] 2.2 Match single and list repository predicates with case-sensitive `fnmatch.fnmatchcase` OR semantics without path normalization.
- [x] 2.3 Run the focused registry tests and confirm the implementation satisfies the regression cases.

## 3. Verification

- [x] 3.1 Run Ruff lint and formatting checks.
- [x] 3.2 Run the ty type-check gate.
- [x] 3.3 Run the complete non-live pytest suite.
- [x] 3.4 Validate the OpenSpec specifications.
