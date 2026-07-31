## 1. Disposition schema and matching domain

- [x] 1.1 Add failing tests for the optional `inherited_from` field: absent-field documents stay valid, present field round-trips through load/validate/render, `extra="forbid"` still rejects unknown keys.
- [x] 1.2 Add failing tests for the tiered matcher: exact-ID carry, unique `(file, rule_id)` prefill, ambiguity (duplicate pair on either side) yields blank, `must_fix` never carries, REJECTED groups stay non-actionable.
- [x] 1.3 Implement the `inherited_from` field and a pure matching function from (inherited verdict findings, current actionable findings) to per-finding carry outcomes.

## 2. Inheritance source loading

- [x] 2.1 Add failing tests for `--inherit` source validation: missing run, missing gate-verdict artifact, repo/PR mismatch each exit with a usage error before template writing; BLOCK-verdict source contributes its accepted records.
- [x] 2.2 Implement inherited-verdict loading (run lookup, target match check, accepted-record extraction) with machine-readable failure reasons.

## 3. Template generation and auto-proceed orchestration

- [x] 3.1 Add failing tests for template generation with inheritance: carried records contain decision/reason/provenance, prefilled records keep `must_fix`, unmatched entries stay blank.
- [x] 3.2 Add failing CLI tests: full tier-1 coverage validates and reports a verdict in one invocation with the generated document persisted; partial coverage writes the prefilled template and exits nonzero; `--inherit` composes with both `--target` and `--run`; owner re-verification failure blocks a fully carried run.
- [x] 3.3 Implement gate orchestration for inheritance: generate-with-carries, auto-proceed on full tier-1 coverage, provenance rendering in the verdict artifact.

## 4. Specs and context

- [x] 4.1 Synchronize the pr-gate main spec with the implemented contract and record the six-round non-convergence evidence in `context.md`.
- [x] 4.2 Document the unchanged-head rule (resume, never re-target) and the changed-head `--inherit` workflow in the pr-gate context.
- [x] 4.3 Run all bare gates and `openspec validate --specs`.

## 5. Fail-closed matching hardening

- [x] 5.1 Add failing tests for mixed accepted/must-fix source ambiguity, content-digest tier-one matching, changed and unknown digests, and per-entry blank reasons.
- [x] 5.2 Implement all-finding ambiguity counting, optional persisted `hunk_sha256`, digest-bound tier one, typed disposition comparisons, and blank-reason template comments.

## 6. Source and provenance integrity

- [x] 6.1 Add failing tests for traversal and symlink run IDs plus unbound, mismatched, and unmatched `inherited_from` claims.
- [x] 6.2 Harden `RunStore.open` containment and validate provenance against a matcher result recomputed from the selected inheritance source.

## 7. Inheritance failure diagnostics

- [x] 7.1 Add failing tests for console and persisted inheritance outcome summaries and actor-, permission-, and finding-specific blocker authorization failures.
- [x] 7.2 Persist and render inheritance outcome summaries and detailed blocker re-verification failures.

## 8. Remediation specification and verification

- [x] 8.1 Synchronize the delta and main pr-gate spec/context with the hardened contract.
- [x] 8.2 Run the focused regressions, all bare repository gates, `openspec validate --specs`, and `openspec validate inherit-accepted-dispositions`.

## 9. Round-2 matching and identity hardening

- [x] 9.1 Add failing regressions for ambiguity precedence over exact matching, body-digest binding, and persisted per-finding inheritance outcomes.
- [x] 9.2 Implement ambiguity-first matching, optional body digests, and per-finding inheritance diagnostics.

## 10. Round-2 run and source integrity

- [x] 10.1 Add failing CLI/store regressions for invalid run IDs, artifact symlink containment, self-inheritance, and incomplete inheritance sources.
- [x] 10.2 Implement consistent invalid-input handling, safe run-ID validation, contained artifact reads, self-reference rejection, and source-completeness validation.

## 11. Canonical hunk parsing and authorization diagnostics

- [x] 11.1 Add failing regressions for canonical hunk digest boundaries and carried-blocker authorization operational failures.
- [x] 11.2 Derive hunk digests from the canonical parser and persist authorization failures with actor and stderr context.

## 12. Round-2 specification and verification

- [x] 12.1 Synchronize the delta and main pr-gate spec/context with all round-2 requirements and rationale.
- [x] 12.2 Run focused regressions, every bare repository gate, `openspec validate --specs`, and `openspec validate inherit-accepted-dispositions`.

## 13. Round-4 regression coverage

- [x] 13.1 Add failing regressions for authorization diagnostic redaction, contained-read TOCTOU resistance, completed-verdict resume protection, all-body digest identity, no-newline hunk markers, and authorization step labels.

## 14. Round-4 hardening implementation

- [x] 14.1 Implement bounded secret-safe authorization diagnostics, resolved-path artifact reads, completed-verdict overwrite protection, order-insensitive all-body digests with empty-body invariants, linear canonical hunk parsing, and the scoped hygiene fixes.

## 15. Round-4 specification and verification

- [x] 15.1 Synchronize the delta and main pr-gate spec/context for diagnostic redaction, completed-verdict protection, and all-body digest binding.
- [x] 15.2 Run focused regressions, every bare repository gate, `openspec validate --specs`, and `openspec validate inherit-accepted-dispositions`.

## 16. Round-6 regression coverage

- [x] 16.1 Add failing regressions for atomic no-follow artifact reads, delimiter-safe body digests and migration demotion, completed-verdict protection across full inheritance, matcher invariant persistence, closed source counts and nonblank accepted reasons, Unicode format-control redaction, and scoped hygiene.

## 17. Round-6 hardening implementation

- [x] 17.1 Implement descriptor-based contained JSON reads, hash-of-hashes body identity, unconditional completed-verdict resume protection, inheritance matcher invariant persistence, source-boundary validation, format-control stripping, and the requested hygiene changes.

## 18. Round-6 specification and verification

- [x] 18.1 Synchronize the delta and main pr-gate spec/context for completed-verdict rejection, inheritance source validation, digest construction, and demotion-reason vocabulary.
- [x] 18.2 Run focused regressions, every bare repository gate, `openspec validate --specs`, and `openspec validate inherit-accepted-dispositions`.

## 19. Round-8 regression coverage

- [x] 19.1 Add failing regressions for normalize-before-redact diagnostics, typed retryable verdict lifecycle and completed-verdict republishing, pinned directory-relative artifact reads, severity-bound tier one, outcome-key equality, bounded source-validation diagnostics, empty authorization output, and the closed blank-reason vocabulary.

## 20. Round-8 hardening implementation

- [x] 20.1 Implement the round-8 redaction, lifecycle, pinned-read, inheritance-integrity, authorization-output, and vocabulary corrections.

## 21. Round-8 specification and verification

- [x] 21.1 Synchronize the delta and main pr-gate spec/context for verdict kinds and republishing, severity-bound matching, exact outcome keys, normalize-before-redact diagnostics, and pinned directory reads.
- [x] 21.2 Run focused regressions, every bare repository gate, `openspec validate --specs`, and `openspec validate inherit-accepted-dispositions`.

## 22. Round-10 regression coverage

- [x] 22.1 Add failing regressions for completed-only inheritance sources, target diagnostic redaction, base64url redaction boundaries, shared pause-marker inference, case-insensitive repository identity, field-specific mismatch details, pinned Markdown cache reads with JSON-authoritative republish rendering, and persisted publication-attempt status.

## 23. Round-10 hardening implementation

- [x] 23.1 Implement the completed-kind trust boundary, bounded target diagnostics, base64url-safe redaction, shared pause marker, canonical repository comparisons, field-specific identity diagnostics, pinned no-follow text reads, JSON-authoritative republish rendering, and redacted publication status persistence.

## 24. Round-10 specification and verification

- [x] 24.1 Synchronize the delta and main pr-gate spec/context for completed inheritance sources, JSON-authoritative republishing, and publication status artifacts.
- [x] 24.2 Run focused regressions, every bare repository gate, `openspec validate --specs`, and `openspec validate inherit-accepted-dispositions`.
