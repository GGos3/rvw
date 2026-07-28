# rvw project

`rvw` is a layered, replicated, self-adjudicating code-review orchestrator. It resolves a review target, activates registry-defined review lanes, dispatches replicated Codex runs, deterministically merges their findings, adjudicates candidates against a checkout, renders a file-first report, and can publish a GitHub COMMENT review or evaluate a CI policy.

The runtime registry is intentionally external at `~/.hermes/review/`; this repository contains the Python package and its behavioral source of truth. `README.md` remains the public overview, while normative behavior lives under `openspec/specs/` and proposed behavior changes live under `openspec/changes/`.

## Technology

- Python 3.12+ managed with uv
- Typer CLI, Pydantic v2 models, PyYAML, and Rich
- Codex CLI as the read-only review runtime
- pytest, ruff, and ty for verification

## Documentation model

Each capability has a `spec.md` containing testable requirements only. Rationale, measurements, historical decisions, constraints, failure modes, and examples belong in the adjacent `context.md`. Any behavior, contract, schema, or CLI change starts as an OpenSpec change before implementation.
