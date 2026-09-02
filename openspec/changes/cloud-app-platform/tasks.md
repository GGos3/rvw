## 1. OpenSpec and repository scaffolding

- [x] 1.1 Add the cloud-app-platform main spec/context and release-automation delta, then validate the change strictly.
- [x] 1.2 Create the `cloud/` npm, TypeScript, Wrangler, Worker, Docker, driver, manifest, README, and Terraform layout.

## 2. Worker and image implementation

- [x] 2.1 Port the Sandbox subclass, ContainerProxy/outboundByHost credential injection, health endpoint, and spike lifecycle routes.
- [x] 2.2 Build the pinned Sandbox image from repository source with Node 24, Codex CLI, git/gh/ripgrep, and secret-free provider template.

## 3. Infrastructure and CI

- [x] 3.1 Add minimal pinned-provider Terraform resources and offline validation documentation.
- [x] 3.2 Add cloud CI gates and opt-in ordered deploy-cloud release job; make actionlint pass.

## 4. Verification and handoff

- [x] 4.1 Run all Python, OpenSpec, workflow, npm, Wrangler, Terraform, Docker, and packaging gates.
- [x] 4.2 Write `/tmp/rvw-cloud-iac-report.md`, inspect wheel contents, and commit the completed scaffold.
