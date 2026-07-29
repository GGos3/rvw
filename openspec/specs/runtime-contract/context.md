# Runtime contract context

## Purpose and scope

This capability defines the machine boundary between rvw and a model runtime. It covers schema generation, Codex invocation, artifact validation, and the general `execute_raw` seam. Normative behavior is in [spec.md](spec.md).

## Key decisions and measured basis

- ADR-004 replaced prose parsing with strict JSON and stable hunk enrichment. A prompt that explicitly requested an outside rule still obeyed the API-level enum schema, demonstrating that structured-output enforcement dominates prompt wording.
- Chunked discovery keeps `r<replica>` as the leaf directory required by the adapter. Multi-chunk runs add an inspectable `c<chunk>` parent, while one-chunk discovery and sampling retain their previous artifact paths.
- The enum-versus-free fixture produced five findings in each condition with near-identical text. Both missed the same deep defects, so rule scope—not the ID enum—was the suppressing factor; ADR-005 added sweep coverage rather than weakening IDs.
- OpenAI strict output rejects object schemas whose `required` array omits defaulted properties. The implementation rewrites both root and item schemas so every property is required.
- The four-part validity contract prevents a zero exit or parseable partial artifact from being silently treated as PASS. On the PR #1119 smoke, all 39 discovery runs were valid; the complete discovery/adjudication walls were about 410s and 197s.

## Constraints

- Completion detection currently depends on the literal Codex log marker `tokens used`.
- The adapter targets POSIX `timeout` and invokes Codex without a shell.
- Runtime wire findings require an integer line; only enriched findings can later carry `line: null` in persisted models.
- The namespace for `/other` comes from the first rule's prefix, so mixed-prefix lane rules are poorly defined.
- Read-only sandboxing controls Codex filesystem writes but the adapter itself writes runtime artifacts.

## Failure modes

- Codex log wording changes can classify otherwise complete runs as `no_completion_marker`.
- Spawn failures, nonzero exits, missing artifacts, JSON parse errors, and schema validation errors are distinct invalid reasons.
- A validator that raises an unexpected exception type is not normalized into an invalid result.
- Schema files are self-contained by replacing Pydantic `$defs`; future nested models need the same care.

## Concrete example

For a warning-capped lane with rules `unscoped/security` and `unscoped/correctness`, the generated finding item permits rule IDs:

```json
["unscoped/security", "unscoped/correctness", "unscoped/other"]
```

and severities:

```json
["warning", "suggestion"]
```

If Codex exits 0 and writes conforming JSON but its run log is truncated before `tokens used`, rvw records an INVALID result with `invalid_reason: "no_completion_marker"` and exposes no output to discovery.

## Historical deltas

ADR-004 said arbitrary out-of-enum IDs would be coerced to `<lane>/other`. The current implementation instead prevents them through the generated schema and rejects any value outside the declared set plus `/other`; it does not rewrite an arbitrary returned string. ADR-004 also described `Finding` as the runtime contract, while the implementation now has the narrower `RuntimeFinding`/`RuntimeLaneOutput` wire types and enriches them downstream.
