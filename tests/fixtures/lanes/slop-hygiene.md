---
lane: slop-hygiene
tier: base
cost: normal
rules:
  - slop/duplicate-object-key
  - slop/duplicate-declaration
  - slop/dead-assignment
  - slop/copy-paste-remnant
  - slop/both-paths-kept
  - slop/needless-wrapper-alias
severity_cap: blocker
---

# slop-hygiene

Find mechanical hygiene defects: duplicated object keys, duplicated
declarations, dead assignments shadowed by later writes, copy-paste remnants,
both-old-and-new-path-kept artifacts, and needless wrapper aliases.
