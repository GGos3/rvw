## Purpose

Defines the secret-free, reproducible Cloudflare Worker and Sandbox infrastructure scaffold that can run the A0 spike and later host the rvw GitHub App execution plane.

## ADDED Requirements

### Requirement: Cloud layout and environment contracts are explicit

The repository MUST contain the documented `cloud/` Worker, Sandbox image, driver, Terraform, and GitHub App manifest layout. Wrangler MUST define default local development plus `spike` and `prod` environments; `spike` MUST use Sandbox instance type `standard-2`, at most two instances, and class `RvwSandbox`, while `prod` MUST use the same class and at most ten instances.

#### Scenario: Configuration is inspected offline
- **WHEN** a maintainer runs Wrangler validation or dry-run for `spike` and `prod`
- **THEN** both environments resolve their declared bindings and limits without requiring Cloudflare credentials

### Requirement: Cloud source contains no credentials

No Cloudflare, GitHub, or Codex secret value, token, private key, or generated auth file MUST be committed. Runtime credentials MUST be represented only by secret bindings or documented operator commands.

#### Scenario: Repository is scanned for secrets
- **WHEN** source, configuration, image build inputs, and manifests are reviewed
- **THEN** no credential value is present and all secret references are placeholders or runtime names

### Requirement: Sandbox egress injects credentials at the proxy boundary

The Worker MUST export the SDK `ContainerProxy` integration and configure `outboundByHost` for the non-secret `CODEX_PROXY_HOST` (default `codex.nekos.me`). It MUST inject the `CODEX_API_KEY` Bearer credential into proxied requests, while the sandbox environment receives only placeholder credential values and never the real key.

#### Scenario: Proxied Codex request is made
- **WHEN** a Sandbox request targets the configured proxy host
- **THEN** the Worker supplies the Bearer secret at egress and the sandbox-visible environment contains no real credential

### Requirement: Spike controls fail closed by environment

The `/start`, `/status`, `/result`, and `/destroy` A0 endpoints MUST be available only when `RVW_ENV` is `spike`; any other environment MUST return HTTP 404 for those paths. `GET /healthz` MUST remain available and return the Worker version and environment.

#### Scenario: Production receives a spike request
- **WHEN** a request targets `/start`, `/status`, `/result`, or `/destroy` with `RVW_ENV=prod`
- **THEN** the Worker returns 404 without starting or mutating a Sandbox

### Requirement: Offline verification gates are reproducible

CI MUST run cloud npm install and TypeScript checks, Wrangler dry-runs for `spike` and `prod`, Terraform format/init-without-backend/validate, a cloud Docker build, and a Python packaging check proving distributions exclude `cloud/`. These gates MUST not require cloud credentials.

#### Scenario: Pull request runs cloud gates
- **WHEN** CI executes on a repository without Cloudflare secrets
- **THEN** every cloud validation gate completes using local or dry-run behavior

### Requirement: Cloud release deployment is opt-in and ordered

The tag release workflow MUST include a `deploy-cloud` job after shared `gates`, gated by repository variable `vars.RVW_CLOUD_DEPLOY == 'true'`. It MUST deploy the production Worker with Cloudflare secrets first and apply Terraform only after Worker deployment succeeds.

#### Scenario: Cloud deployment remains disabled
- **WHEN** the repository variable is not exactly `true`
- **THEN** the release workflow skips cloud deployment while other release jobs remain eligible

### Requirement: GitHub App contract is declared

The manifest MUST declare app name `rvw`, permissions `checks:write`, `pull_requests:write`, `contents:read`, `metadata:read`, events `pull_request`, `check_suite`, `installation`, and `installation_repositories`, and a configurable webhook URL placeholder.

#### Scenario: Manifest is used for registration
- **WHEN** an owner opens the documented manifest flow
- **THEN** GitHub presents exactly the declared permissions and events with a replaceable webhook URL
