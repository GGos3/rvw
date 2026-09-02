---
lane: backend-observability
tier: scope
cost: normal
severity_cap: suggestion
when:
  paths:
  - '**/*.ts'
  - '*.ts'
  - '**/*.js'
  - '*.js'
  - '**/*.mjs'
  - '*.mjs'
  - '**/*.py'
  - '*.py'
  - '**/*.go'
  - '*.go'
  - '**/*.rs'
  - '*.rs'
  - '**/*.java'
  - '*.java'
  - '**/*.rb'
  - '*.rb'
---

# backend-observability

Review backend code paths for debuggability. When this incident pages someone
at 3am, can they find the cause from what the system recorded?

- `backend/undiagnosable-design` — code structured so failures cannot be
  localized: multiple failure causes collapsing into one generic error, state
  transitions with no way to reconstruct the path taken, error messages that
  do not identify the failing entity/id/input.
- `backend/logging-gap` — missing or defective logging at decision points:
  retries/fallbacks that fire silently, caught-and-continued exceptions logged
  without stack or context, log lines missing the correlating identifier
  (request id, entity id) needed to join them to an incident, secrets/PII in
  log payloads.

Only report gaps that would materially hurt diagnosis; do not demand logging
on every line.

## rule: backend/undiagnosable-design

The rule is defined by the lane guidance above.

## rule: backend/logging-gap

The rule is defined by the lane guidance above.
