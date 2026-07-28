# AGENTS

## Source of truth

- OpenSpec is the behavioral SSOT.
- Main specifications: `openspec/specs/<capability>/spec.md`
- Rationale and evidence: adjacent `context.md`
- Active behavior changes: `openspec/changes/<slug>/`
- `README.md` is a public overview, not the normative contract.

## OpenSpec-first workflow

1. Read the relevant main specs and context before editing behavior.
2. For behavior, CLI, schema, contract, or policy changes, create
   `openspec/changes/<slug>/` before code.
3. Implement from the change tasks and use TDD for behavioral work.
4. Keep code, tests, and the resulting main specs synchronized.
5. Run `openspec validate --specs` before handoff.
6. Archive only after the change is implemented and verified.

Documentation-only corrections that do not change behavior may update main
spec/context files directly. Keep `spec.md` requirements-only; place rationale,
measurements, examples, history, and operational notes in `context.md`.

## Environment

- Python 3.12+; dependencies and commands are managed with uv.
- The CLI package uses Typer, Pydantic v2, PyYAML, and Rich.
- The runtime review registry is `~/.hermes/review/`.
- That registry is the runtime SoT and is versioned outside this repository.

## Verification gates

Run every gate as a bare command so pipes cannot mask exit codes:

```bash
uv run ruff check .
uv run ruff format --check .
uv run ty check
uv run pytest -q -m "not live"
openspec validate --specs
```

Do not pipe a gate through `head`, `tail`, `tee`, `grep`, or another command
when using its exit status as evidence.

## Tests and implementation

- Write a failing regression test before a behavioral fix, then implement the
  smallest change that makes it pass.
- Keep unit tests deterministic and offline.
- Tests that invoke a real Codex CLI or require credentials use
  `@pytest.mark.live` and are excluded from the default gate.
- Never weaken assertions to accommodate nondeterministic live output; assert
  stable contracts and known defects instead of exact incidental counts.
- Preserve strict Pydantic schemas and machine-readable failure reasons.

Executor delegation may be used for bounded implementation tasks. Give an
executor the relevant OpenSpec change and tests, then independently inspect its
diff and rerun the bare gates before accepting the result.

## Scope and safety

- Do not edit the external registry unless the task explicitly includes it.
- Do not commit credentials, runtime artifacts, or `/tmp/rvw/` outputs.
- Do not commit or publish unless the user explicitly asks.
