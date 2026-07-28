## Context

`Registry.activate` currently compares `LayerPredicate.repo` to the target repository with string equality, while `paths` evaluates a list of patterns with `fnmatch.fnmatchcase`. A project layer therefore cannot describe a repository family such as `APIFuseHQ/apifuse-provider-*` without enumerating repositories or duplicating layers. Repository names arrive as canonical `owner/name` strings from `gh repo view --json nameWithOwner` and need no path normalization.

## Goals / Non-Goals

**Goals:**

- Accept either one repository pattern or a list of patterns in the strict Pydantic model.
- Match repository patterns case-sensitively with OR semantics within a list.
- Preserve AND semantics between repository and path predicates.
- Keep existing plain-string registry entries behaviorally compatible.

**Non-Goals:**

- Changing the external runtime registry.
- Normalizing repository separators, casing, or backslashes.
- Adding regex, negation, or richer predicate composition.

## Decisions

- Type `LayerPredicate.repo` as `str | list[str] | None`. This expresses the accepted YAML shapes directly and keeps Pydantic validation strict; arbitrary scalar or mixed-list coercion is not introduced.
- Convert a single string to a one-element sequence only while matching, then use `any(fnmatch.fnmatchcase(repo, pattern) ...)`. This keeps single and list forms on one matching path and mirrors the list-OR behavior of `paths` without copying path normalization.
- Keep repository matching and changed-path matching as separate booleans joined with AND. A layer with both conditions activates only if at least one repository pattern and at least one path pattern match.
- Use `fnmatch.fnmatchcase` directly. Unlike `fnmatch.fnmatch`, it cannot inherit platform-dependent case normalization, and a pattern without metacharacters retains exact-match behavior.

## Risks / Trade-offs

- [Existing repository strings containing glob metacharacters gain pattern meaning] → This is the requested schema contract; document it explicitly and cover plain strings as the compatibility case.
- [An empty repository pattern list can never match] → Preserve natural `any([]) == False` behavior, analogous to an empty path list, rather than adding a special case.
- [Glob matching includes fnmatch character-class syntax in addition to `*` and `?`] → Reuse Python's established fnmatch semantics consistently and avoid a second pattern language.
