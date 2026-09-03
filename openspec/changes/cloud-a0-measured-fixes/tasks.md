## 1. Worker regression contract

- [x] 1.1 Add failing unit tests for target validation, process environment
  construction, and result artifact paths.
- [x] 1.2 Implement explicit HTTPS interception, validated repository/SHA
  input, isolated process environment, correct artifact paths, and secret-free
  injection logging.
- [x] 1.3 Remove the duplicate Codex base URL template setting.

## 2. Driver and retained documentation

- [x] 2.1 Make the observer deadline configurable and make driver exit/status
  semantics distinguish success, review failure, missing completion, a healthy
  review at deadline, and transport failure.
- [x] 2.2 Document rollout readiness, three-resource cleanup, driver semantics,
  and the measured A0 facts in the capability context.
- [x] 2.3 Make the unrelated local-HEAD fallback test fixture independent of
  the repository's own HEAD shape.

## 3. Verification

- [x] 3.1 Wire the Worker unit test runner into the cloud CI job.
- [x] 3.2 Run all repository, OpenSpec, actionlint, cloud, Wrangler dry-run, and
  Docker gates requested by the change.
