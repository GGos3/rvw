## Context

The current runtime already has a VALID/INVALID result boundary and persisted retry-attempt coverage, but invalid reasons are legacy free-form strings, final runtime diagnostics are not carried into discovery coverage, discovery has no aggregate terminal status, outcome persistence is an unchecked dataclass, and pipeline failures can stop before a report or machine summary exists.

## Goals / Non-Goals

**Goals:**

- Establish one typed terminal summary used by persistence, Markdown, and CLI JSON.
- Preserve successful discovery work while preventing partial execution from appearing complete.
- Make absence of valid adjudicator output an error boundary rather than a vote source.
- Reuse persisted expensive stages for re-adjudication without destroying prior successful artifacts on failure.

**Non-Goals:**

- Change runtime concurrency, deadlines, host-global slot gating, retries, lane selection, prompts based on size, or publication policy.
- Diagnose gateway behavior or edit the external lane registry.
- Add build provenance, change the PEP 517 backend, or alter release/version metadata.

## Decisions

### Use a typed run summary as the shared status contract

`run.json` will hold a schema-versioned `RunSummary` with terminal status, structured failed lanes, coverage totals, and an optional adjudication error. It begins as `running` while work is active and is replaced atomically at each terminal transition. The review JSON payload is derived from this model, and report rendering receives it, avoiding independently inferred status.

Terminal meanings are fixed: `complete` has no final invalid discovery execution and no requested-stage infrastructure error; `degraded` has at least one valid and one invalid discovery execution; `failed` has planned discovery executions but none valid, or a requested adjudication pass with no valid response after retry. Intentionally omitted adjudication due to no `--repo-dir` does not itself degrade otherwise complete discovery.

Alternative considered: infer status from aggregate counts at presentation time. This was rejected because it leaves persisted artifacts without a single auditable decision and cannot carry adjudication diagnostics.

### Normalize failure categories without discarding diagnostics

Runtime output failures use the closed values `missing`, `empty`, `unparseable`, and `schema-invalid`; process and completion failures remain separately normalized. Structured details retain replica, chunk, artifact directory, exit code when known, output and log paths/sizes, and spawn details when available. Lane failure entries group final invalid executions by lane while coverage remains the exact per-run record.

Current `RunCoverage.attempts` remains the ordered history for initial and replacement waves. The new final `diagnostic` field coexists with it: `attempts` validates attempt sequencing and final-status agreement, while `diagnostic` validates that only an invalid final run carries diagnostics.

Alternative considered: expose only existing `invalid_reason` strings. This was rejected because parameterized strings are hard for automation to branch on and currently conflate missing and empty artifacts.

### Adjudication requires at least one valid response per required pass

The existing one-retry policy remains. After it, zero valid results raises a typed `AdjudicationInfrastructureError` containing every failed attempt. The current replacement prompt still receives prior invalid reasons. Voting is never called with zero valid responses. Runtime UNCERTAIN reasons are validated as nonblank; synthesized omission, coercion, and tie reasons use explicit stable text. Outcome becomes a strict model with a validator requiring a nonblank reason for every final UNCERTAIN verdict.

The pipeline catches only this expected infrastructure failure, writes a failed summary and an explicitly failed unadjudicated report from preserved merge output, and returns a controlled system-error result. Unexpected exceptions continue to surface normally. Current discovery/adjudication replica separation, concurrency, deadline, host-gate propagation, and the shared reviewed-diff projection remain unchanged.

### Re-adjudication calls the stage directly and writes only after success

The command requires `--run` and `--repo-dir`, with optional `--out`, `--replicas`, `--concurrency`, and `--deadline` settings consistent with runtime-executing commands. It loads `target.json`, `discover.json`, then `merge.json` in that order and invokes the same adjudicator with a timestamped runtime-attempt directory beneath the run. Discovery is never called. Outcome and report are replaced only after a valid outcome is available; a failed attempt updates only the run summary error and retains the previous outcome/report. File replacement uses temporary siblings plus rename so readers never observe partial JSON.

Alternative considered: resume the entire common pipeline. This was rejected because it would create a new run and repeat discovery, defeating recovery.

## Risks / Trade-offs

- [Existing consumers expect four review JSON keys] → Treat the added status fields as an intentional contract expansion and retain the existing count fields.
- [A single invalid replica makes an otherwise useful replicated lane degraded] → Preserve all valid findings and exact coverage while making reduced confidence explicit.
- [Old runs lack `run.json` and diagnostics] → Derive status from strict persisted coverage when loading legacy runs and leave unavailable diagnostics absent rather than inventing them.
- [Re-adjudication can fail while an older outcome exists] → Mark the failed attempt in the run summary while retaining the previous outcome/report; replace outcome/report only after success, so the terminal summary remains the authority.

## Migration Plan

Implement additive readers for legacy discovery/outcome artifacts, then begin writing `run.json` for new runs. Existing JSON stage artifacts remain readable. No packaging or provenance migration is part of this change.
