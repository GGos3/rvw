## Context

See [proposal.md](proposal.md) for motivation. Discovery currently resolves a complete target diff before activation, always applies prompt-budget filtering/chunking, and sends each chunk to `Runtime.execute` without a workdir. `execute_raw` and adjudication already support a workdir, and the PR gate already owns a detached-head checkout provisioner, but that provisioner does not establish base availability or test the three-dot diff. Planned run coverage is deliberately exact and must not be distorted by a reactive receipt audit.

The current agent prompt also injects dynamic briefs and cross-lane exclusions. The settled minimal agentic contract is stricter, so those sections remain exclusively in the legacy inline builder. Sampling remains inline because it is an enum/free comparison over a fixture rather than repository exploration.

## Goals / Non-Goals

**Goals:**

- Keep controller responsibilities deterministic: target anchors, checkout verification, hunk parsing, receipt comparison, bounded re-dispatch, and persistence.
- Let each agentic lane explore the repository autonomously using ordinary read-only structured `codex exec`.
- Preserve exact planned execution coverage and the inline path's current artifacts and tests.
- Make checkout and residual coverage failures typed and inspectable.

**Non-Goals:**

- Inferring semantic quality from a receipt or requiring every lane to emit a finding.
- Splitting lane checklists, changing adjudication prompts, or changing external registry contents.
- Supporting uncommitted or root-commit targets in agentic mode; operators use explicit inline mode for those targets.

## Decisions

### A typed mode branches before prompt budgeting

A `DiscoveryMode` string enum (`agentic`, `inline`) is passed from CLI/planning through the shared pipeline to discovery. The default is `agentic`. Inline executes the existing builder and diff-budget code unchanged. Agentic sets one logical scope, returns no budget report, and never calls the prompt-budget planner.

Alternative considered: infer mode from whether `repo_dir` is present. That makes fallback accidental, obscures persisted/planned behavior, and cannot distinguish an explicitly supplied checkout intended for adjudication from an agentic selection.

### Agentic prompts use a separate pure builder

The agentic builder renders the lane ID and Markdown body, an exact three-dot SHA scope sentence, and output instructions for strict findings plus `covered`. It accepts neither diff nor exclusion/chunk/brief inputs, making accidental diff injection structurally difficult. Inline retains the existing builder.

Alternative considered: add conditionals inside the existing builder. A separate signature gives tests and type checking a stronger no-diff boundary.

### Checkout verification is shared by provisioned and supplied workspaces

Checkout logic moves behind one reusable verifier. It checks exact HEAD, clean porcelain state, base/head commit resolvability, and successful `git diff --no-ext-diff <base>...<head> --`. The PR provisioner extends its existing head-ref fetch with the captured base, then calls that verifier. Ordinary PR review without `--repo-dir` provisions a temporary checkout; local commit review provisions a temporary local clone; supplied directories and gate/stack checkouts use the same verifier. Verification precedes run creation and runtime calls.

Failures use `CheckoutVerificationError` with stable `error_code=checkout-verification-failed` and a closed reason such as `missing-base`, `head-mismatch`, `base-unresolvable`, `head-unresolvable`, `dirty-checkout`, or `diff-uncomputable`. JSON-capable commands render this data rather than exposing an untyped subprocess exception.

Alternative considered: trust `ResolvedTarget.diff` and only set cwd. That permits the model to review a different repository state and does not meet the controller-verification contract.

### Runtime workdir is explicit at the lane execution seam

`Runtime.execute`, `PlannedRun`, and dispatch carry an optional workdir, and `CodexRuntime.execute` forwards it to `execute_raw`. Agentic planned runs require the verified checkout; inline and sampling leave it unset. The Codex command remains the existing plain `codex exec --sandbox read-only --output-schema ...` invocation.

### Receipts map to canonical controller hunks per lane

`RuntimeLaneOutput.covered` is a required list of strings. A receipt equal to a changed file covers all its hunks. A receipt whose final colon suffix is `N` or `N-M` covers hunks of the exact preceding path whose new-side range intersects that inclusive receipt range; parsing from the right preserves colons in file names. Deletion-only hunks require a whole-file receipt. Unknown or malformed receipts cover nothing and do not invalidate an otherwise schema-valid run.

Coverage is the union of VALID outputs per lane, not a global union. This makes `LaneCoverage.uncovered` attributable and prevents a broad sweep receipt from masking a scoped lane that never inspected part of its target.

### Coverage re-dispatch is one separate reactive wave

After the initial dispatch and its existing all-invalid replacement behavior, the controller computes missing hunks per lane. It selects one deterministic representative run (replica 1) for each incomplete lane and submits those representatives together beneath a distinct `coverage-redispatch/` artifact root, with ordinary invalid retry disabled for this wave. The prompt remains the same minimal agentic prompt; no hunk list is injected.

Valid coverage-wave findings and receipts are unioned with initial valid output. The planned `RunCoverage` identity set and dispatched/valid aggregates continue to describe the lane×replica initial plan, keeping gate exactness stable. `LaneCoverage.coverage_redispatched` records the reactive wave, `findings` includes findings accepted from both waves, and `uncovered` records the final canonical hunk IDs. The controller never schedules a second coverage wave.

Alternative considered: add synthetic replicas or chunks for the coverage wave. That would make a reactive audit look like planned execution, break exact gate coverage, and overload the chunk axis after agentic mode removes chunking.

### Legacy artifact compatibility is one-way

New live lane output requires `covered`. Persisted `LaneCoverage` predating this change loads with `coverage_redispatched=false` and `uncovered=[]`. Existing inline runtime fixtures and fakes are updated to emit `covered`; strict live schemas do not make the new field optional.

### Reports show gaps without silently redefining gate validity

The coverage table adds an uncovered count, and canonical uncovered IDs render immediately below the table. An agentic budget is absent, so no diff-budget line renders. Exact gate validation continues to fail on missing or invalid planned runtime identities; residual receipt gaps remain visible evidence rather than a newly invented gate-blocking rule.

## Risks / Trade-offs

- **[Receipt truth is agent-reported]** → Controller comparison detects omissions but cannot prove claimed inspection; canonical receipts and one independent retry make gaps observable without presenting them as semantic proof.
- **[One representative retry may remain incomplete]** → Persist the remaining hunk IDs instead of looping or silently claiming coverage.
- **[Automatic checkouts add local I/O]** → Temporary provisioned directories are bounded to pipeline execution; explicit `--repo-dir` can reuse an operator checkout after verification.
- **[Base SHA fetch can fail on restricted remotes]** → Fail closed with a typed reason; inline mode remains an explicit operational fallback.
- **[Agentic prompts lose dynamic and covered-rule injections]** → This is required by the settled minimal prompt contract; the lane document and repository context remain available, and inline mode preserves the older behavior.
- **[Adding `covered` breaks old runtime payload fixtures]** → Update deterministic fixtures while retaining persisted coverage defaults; structured-output enforcement is intentionally strict for new executions.

## Migration Plan

1. Add the mode, strict receipt schema, checkout verifier, workdir propagation, and deterministic tests.
2. Add agentic orchestration and bounded receipt re-dispatch while keeping inline and sampling behavior green.
3. Update coverage persistence/reporting and mode-aware gate/plan paths.
4. Synchronize the delta requirements into main specs, run both OpenSpec validations and all repository gates, and leave this change active and unarchived.
5. Roll back operationally by selecting `inline`; code rollback can remove the agentic branch without altering the preserved inline implementation.
