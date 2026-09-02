## MODIFIED Requirements

### Requirement: Codex execution is read-only and bounded

The Codex adapter SHALL invoke `codex exec` directly and MUST expose distinct
tool-less and agentic execution modes under the same explicit typed model and
reasoning policy. Every mode MUST pass `--sandbox` with the value selected by
`RVW_CODEX_SANDBOX`, which MUST accept only `read-only` or
`danger-full-access`, MUST default to `read-only`, and MUST reject any other
value before spawning Codex. Tool-less mode MUST disable shell, browser,
computer, app, plugin, image, multi-agent, and collaboration tools, disable
rule loading and persisted sessions, and use strict structured output. Agentic
mode MUST disable multi-agent and collaboration modes while retaining source
exploration for agentic discovery and explicitly expanded adjudication. The
project container MUST select `danger-full-access` because measured nested
bubblewrap namespace creation is unavailable there; this fallback MUST NOT
change the host default, and the read-only-mounted container MUST remain the
isolation boundary. The adapter SHALL never invoke `codex exec review`. The
adapter MUST capture its newly created process group before awaiting the
runtime and enforce each configured deadline by cancelling its process-owning
task. That task MUST terminate the complete captured process group with TERM,
wait no more than five seconds for the group to disappear, and escalate to
KILL. After KILL, it MUST wait no more than a further five seconds for the
captured group to disappear. If the group still exists or cannot be verified
because a probe receives `EPERM`, it MUST record persistent or unverified
cleanup in the run log and return so the original cancellation or timeout
classification can continue. Runtime identity and usage MUST record the
selected mode so resume cannot reuse a result from another mode. The initial
default policy MUST be `gpt-5.6-sol` with `max` reasoning effort.

#### Scenario: Tool-less inline discovery execution

- **WHEN** inline DISCOVER starts a lane replica
- **THEN** its Codex command disables shell and other interactive tools, writes
  no persisted Codex session, and records zero tool calls in usage

#### Scenario: Agentic discovery execution

- **WHEN** agentic DISCOVER starts a lane replica in its verified checkout
- **THEN** its Codex command uses bounded agentic read-only mode and can inspect
  the provisioned checkout

#### Scenario: Initial adjudication execution

- **WHEN** an initial adjudication pass evaluates candidates from the supplied
  reviewed diff
- **THEN** its Codex command uses tool-less read-only mode

#### Scenario: Expanded adjudication execution

- **WHEN** an initially UNCERTAIN candidate starts its one expanded pass
- **THEN** its Codex command uses agentic read-only mode and can inspect the
  provisioned checkout

#### Scenario: Host runtime uses its default sandbox

- **WHEN** rvw executes Codex without `RVW_CODEX_SANDBOX`
- **THEN** plain Codex execution receives `--sandbox read-only`

#### Scenario: Container runtime uses its measured fallback

- **WHEN** the project container executes Codex with `RVW_CODEX_SANDBOX=danger-full-access`
- **THEN** plain Codex execution receives `--sandbox danger-full-access` inside the container boundary

#### Scenario: Sandbox selector is unsupported

- **WHEN** `RVW_CODEX_SANDBOX` contains any other value
- **THEN** runtime execution fails before Codex is spawned

#### Scenario: Deadline expires

- **WHEN** a run exceeds its configured deadline
- **THEN** RVW terminates and reaps the full runtime process group and classifies
  the run INVALID with reason `exit_nonzero:124`

#### Scenario: Runtime leader exits before its child

- **WHEN** TERM ends the runtime leader but a child in its captured process group
  remains alive
- **THEN** RVW detects the surviving group during the grace period, sends KILL,
  and returns after the group exits

#### Scenario: Process group persists after KILL

- **WHEN** the captured process group still appears to exist for five seconds
  after RVW sends KILL
- **THEN** RVW records a persistent-cleanup marker and does not wait
  indefinitely before returning the original cancellation or timeout result

#### Scenario: Process group cannot be verified after KILL

- **WHEN** the post-KILL process-group probe receives `EPERM`
- **THEN** RVW records an unverified-cleanup marker and returns the original
  cancellation or timeout result without propagating the probe exception

#### Scenario: Ambient configuration requests a different policy

- **WHEN** a host config selects another model or reasoning effort
- **THEN** an RVW Codex invocation still carries `--model gpt-5.6-sol` and an
  explicit `model_reasoning_effort="max"` override

#### Scenario: Discovery uses structured output

- **WHEN** a lane runtime is invoked
- **THEN** plain `codex exec` receives the lane's closed-enum output schema and custom prompt
