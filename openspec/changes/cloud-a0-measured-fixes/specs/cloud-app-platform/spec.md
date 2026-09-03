## MODIFIED Requirements

### Requirement: Sandbox egress injects credentials at the proxy boundary

The Worker MUST export the SDK `ContainerProxy` integration, explicitly enable
HTTPS interception on its Sandbox subclass, and configure `outboundByHost` for
the non-secret `CODEX_PROXY_HOST` (default `codex.nekos.me`). It MUST inject the
`CODEX_API_KEY` Bearer credential into proxied requests and emit a structured
injection event that contains the hostname but no credential or authorization
header value. The explicit environment passed when starting the sandbox review
process MUST contain only a placeholder `CODEX_API_KEY` and the proxy
`CODEX_BASE_URL`; inherited `RVW_CODEX_DEFAULT_BASE_URL` and
`RVW_CODEX_SANDBOX` values MUST be unset before review commands run.

#### Scenario: Proxied Codex request is made

- **WHEN** a Sandbox request targets the configured proxy host
- **THEN** HTTPS interception invokes the Worker egress hook, the Worker
  supplies the Bearer secret and logs only the injection event and hostname,
  and the sandbox-visible credential remains a placeholder

### Requirement: Spike controls fail closed by environment

The `/start`, `/status`, `/result`, and `/destroy` A0 endpoints MUST be
available only when `RVW_ENV` is `spike`; any other environment MUST return
HTTP 404 for those paths. `GET /healthz` MUST remain available and return the
Worker version and environment. `/start` MUST accept a validated HTTPS GitHub
repository URL and a 7-to-40-character lowercase hexadecimal commit SHA and
MUST return HTTP 400 without creating a sandbox when either input is invalid.
`/result` MUST read review artifacts from `/workspace/result/`.

#### Scenario: Production receives a spike request

- **WHEN** a request targets a spike path with `RVW_ENV=prod`
- **THEN** the Worker returns 404 without starting or mutating a Sandbox

#### Scenario: A maintainer measures an explicit repository commit

- **WHEN** the spike driver starts a review with a valid HTTPS repository URL
  and full or short commit SHA
- **THEN** the Worker runs that repository target and returns the artifacts
  written under `/workspace/result/`

#### Scenario: Invalid target input is rejected

- **WHEN** `/start` receives a missing or invalid repository URL or commit SHA
- **THEN** the Worker returns HTTP 400 without creating a sandbox

### Requirement: A0 driver reports observation outcomes truthfully

The spike driver MUST accept an observer deadline parameter that defaults to 25
minutes. It MUST exit non-zero when no completion marker is observed or when
the review process exit code is non-zero. Its final summary MUST distinguish a
review still running at the observer deadline from a transport failure, and it
MUST state that reaching the observer deadline while still running is not
evidence that the review itself failed.

#### Scenario: Healthy review outlives its observer

- **WHEN** status remains running when the configured observer deadline expires
- **THEN** the driver exits non-zero and reports an observer deadline outcome,
  not a review failure or transport failure

### Requirement: Offline verification gates are reproducible

CI MUST run cloud npm install, Worker unit tests, and TypeScript checks,
Wrangler dry-runs for `spike` and `prod`, Terraform
format/init-without-backend/validate, a cloud Docker build, and a Python
packaging check proving distributions exclude `cloud/`. These gates MUST not
require cloud credentials.

#### Scenario: Pull request runs cloud gates

- **WHEN** CI executes on a repository without Cloudflare secrets
- **THEN** every cloud validation gate, including Worker unit tests, completes
  using local or dry-run behavior
