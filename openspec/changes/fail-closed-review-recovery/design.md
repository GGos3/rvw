## Context

The current runtime already has a VALID/INVALID result boundary, but invalid reasons are legacy free-form strings, discovery has no aggregate terminal status, outcome persistence is an unchecked dataclass, and pipeline failures can stop before a report or machine summary exists. The uv build backend packages static source files and the semantic version is intentionally unchanged between ordinary source installs.

## Goals / Non-Goals

**Goals:**

- Establish one typed terminal summary used by persistence, Markdown, and CLI JSON.
- Preserve successful discovery work while preventing partial execution from appearing complete.
- Make absence of valid adjudicator output an error boundary rather than a vote source.
- Reuse persisted expensive stages for re-adjudication.
- Identify installed artifacts using build-time facts, including explicit unknown values.

**Non-Goals:**

- Change runtime concurrency, retries, lane selection, prompts based on size, or publication policy.
- Diagnose gateway behavior or edit the external lane registry.
- Make stale-build detection fatal or perform Git subprocesses on every CLI command.

## Decisions

### Use a typed run summary as the shared status contract

`run.json` will hold a schema-versioned `RunSummary` with terminal status, structured failed lanes, coverage totals, optional adjudication error, and build provenance. It begins as non-terminal while work is active and is replaced atomically at each terminal transition. The review JSON payload is derived from this model, and report rendering receives it, avoiding independently inferred status.

Terminal meanings are fixed: `complete` has no final invalid discovery execution and no requested-stage infrastructure error; `degraded` has at least one valid and one invalid discovery execution; `failed` has no valid planned discovery execution or a requested adjudication pass with no valid response after retry. Intentionally omitted adjudication due to no `--repo-dir` does not itself degrade otherwise complete discovery.

Alternative considered: infer status from aggregate counts at presentation time. This was rejected because it leaves persisted artifacts without a single auditable decision and cannot carry adjudication diagnostics.

### Normalize failure categories without discarding diagnostics

Runtime output failures use the closed values `missing`, `empty`, `unparseable`, and `schema-invalid`; process failures remain separately normalized. Structured details retain replica, chunk, artifact directory, exit code when known, and log path/size. Lane failure entries group final invalid executions by lane while coverage remains the exact per-run record.

Alternative considered: expose only existing `invalid_reason` strings. This was rejected because parameterized strings are hard for automation to branch on and currently conflate missing and empty artifacts.

### Adjudication requires at least one valid response per required pass

The existing one-retry policy remains. After it, zero valid results raises a typed `AdjudicationInfrastructureError` containing attempt details. Voting is never called with zero valid responses. Runtime UNCERTAIN reasons are validated as nonblank; synthesized omission, coercion, and tie reasons use explicit stable text. Outcome becomes a strict model with a validator requiring a nonblank reason for every final UNCERTAIN verdict.

The pipeline catches only this expected infrastructure failure, writes a failed summary and an explicitly failed unadjudicated report from preserved merge output, and returns a controlled system-error result. Unexpected exceptions continue to surface normally.

### Re-adjudication calls the stage directly and writes only after success

The command requires `--run`, `--repo-dir`, and optionally `--out`/`--replicas`. It loads `target.json`, `discover.json`, then `merge.json` in that order and invokes the same adjudicator with a timestamped runtime-attempt directory beneath the run. Discovery is never called. Outcome, report, and final summary are written only after a valid outcome is available; file replacement uses temporary siblings plus rename so readers never observe partial JSON.

Alternative considered: resume the entire common pipeline. This was rejected because it would create a new run and repeat discovery, defeating recovery.

### Generate and embed provenance at PEP 517 build time

A small in-tree backend wrapper will compute a deterministic SHA-256 build identifier over packaged source inputs, query Git once during build, record the commit only when available, record whether the source was dirty, and capture a UTC build timestamp. It temporarily supplies a generated provenance module while delegating wheel/sdist creation to `uv_build`; a checked-in unknown fallback keeps direct source imports honest. Runtime commands only read constants and never shell out for basic provenance.

Best-effort stale detection is limited to environments where embedded clean-commit provenance and an associated local source checkout can establish ancestry. If those facts are unavailable, rvw records provenance but does not warn. Any comparison is performed once when creating a run, not on every command.

Alternative considered: read the local checkout HEAD at runtime and call it the build commit. This was rejected because a checkout may advance after installation and would fabricate provenance.

## Risks / Trade-offs

- [Existing consumers expect four review JSON keys] → Treat the added status fields as an intentional contract expansion, retain the existing count fields, and document exact values.
- [A single invalid replica makes an otherwise useful replicated lane degraded] → Preserve all valid findings and exact coverage while making reduced confidence explicit.
- [Custom build wrapping adds packaging complexity] → Keep delegation thin, test wheel contents and provenance, and retain uv_build as the actual packager.
- [Old runs lack `run.json` and embedded provenance] → Derive failure status from strict persisted coverage when loading legacy runs and label provenance unknown; never backfill a guessed commit.
- [Re-adjudication can fail while an older outcome exists] → Mark the run failed in its summary and replace outcome/report only together after success, so the terminal summary remains the authority.

## Migration Plan

Implement additive readers for legacy discovery/outcome artifacts, then begin writing `run.json` for new runs. Validate a locally built wheel, install it in an isolated location, and verify version/run provenance before local commits. Rollback removes the new summary/provenance reader and restores the direct uv_build backend; existing JSON stage artifacts remain readable.
