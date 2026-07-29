## Context

Sampling accepts either a source file or an already-produced unified diff. `_fixture_diff` currently treats both as source files and always shells out to `git diff --no-index /dev/null`, so an existing multi-file diff becomes one new-file segment whose size is the whole fixture. The shared budget planner intentionally returns one empty chunk when every segment is excluded; both `sample_lane` and `discover` currently dispatch that exclusion-only chunk, allowing zero-finding output to look successful.

## Goals / Non-Goals

**Goals:**

- Preserve an existing unified diff byte-for-byte as the input to budgeting and chunking.
- Preserve source-file fixture conversion through `git diff --no-index`.
- Make zero retained review characters a typed, inspectable failure before runtime dispatch in sampling and discovery.
- Map the sampling failure to the user-error exit class and structured JSON when `--json` is requested.

**Non-Goals:**

- Change generated-path patterns or the 200,000/400,000 character limits.
- Reject partially excluded diffs that still retain reviewable characters.
- Modify the external lane registry or sampling verdict values.

## Decisions

1. `_fixture_diff` reads the fixture as UTF-8 and returns it directly only when its first line begins with `diff --git ` or `--- `. Those are the two header shapes accepted by `split_diff_files`; all other fixtures continue through the existing Git conversion. A non-UTF-8 fixture falls back to Git conversion to avoid narrowing the old source-file behavior.

2. The diff-budget module exposes a typed empty-review error carrying a stable error code and `excluded_reason` mapping, plus a small assertion helper over `DiffBudgetReport`. Sampling labels the source `fixture`; discovery labels it `target`. Keeping this distinct from `apply_diff_budget` preserves the planner's useful accounting result and lets callers decide whether a zero-kept plan is permissible.

3. `sample_lane` and `discover` assert `kept_chars > 0` immediately after budgeting and before prompt construction or dispatch. This is the earliest point with complete exclusion reasons and guarantees no model call can convert absent coverage into PASS.

4. Sample CLI JSON failures contain `error`, `message`, and `excluded_reason`; human output uses the same deterministic message and exits 2. Review/auto/gate command paths also translate the typed discovery error rather than exposing an unhandled exception.

## Risks / Trade-offs

- [A source file whose literal first line begins with a diff header is treated as a diff] → This explicit marker is the requested input contract and remains validated by the existing parser during budgeting.
- [Preamble text before a unified diff is not passed through] → Detection intentionally requires the header at the start, matching the stated fixture contract.
- [All-generated or all-oversized production changes now stop reviews that previously ran exclusion-only prompts] → This is the intended fail-closed behavior; structured reasons tell operators what was excluded.
