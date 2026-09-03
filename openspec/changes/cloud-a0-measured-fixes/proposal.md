## Why

The 2026-09-02 A0 rerun measured six defects in the checked-in Cloudflare
spike: HTTPS egress interception was inactive, the Codex template produced a
duplicate TOML key, the review target was hardcoded, result retrieval used the
wrong directory, credential injection was not observable, and inherited rvw
environment defaults crossed the process boundary. The observer driver also
reported success when completion was not observed and did not distinguish a
healthy long-running review from a transport failure.

## What Changes

- Make HTTPS interception and secret-free credential injection explicit.
- Give the review process only a placeholder credential and proxy URL, and
  remove inherited rvw Codex defaults before review commands run.
- Accept a validated HTTPS repository URL and full or short commit SHA at
  `/start`, then return artifacts from the directory where the process writes.
- Make driver deadlines configurable and its exit/result summaries truthful.
- Run Worker-side regression tests in CI and retain the measured Cloudflare
  lifecycle, rollout, sandboxing, and cleanup facts in capability context.

## Impact

The behavior change is limited to the `RVW_ENV=spike` A0 path and its offline
validation. No A1 webhook, Queue, Check Runs, R2, or durable-job behavior is
introduced, and no deployment or external registry mutation is required.
