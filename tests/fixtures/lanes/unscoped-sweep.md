---
lane: unscoped-sweep
tier: base
cost: heavy
rules:
  - unscoped/security
  - unscoped/correctness
  - unscoped/contract
  - unscoped/scope-creep
severity_cap: warning
covered_by_others: inject
---

# unscoped-sweep

Find important security, correctness, contract, and scope defects that are not
covered by the other active lanes.
