## MODIFIED Requirements

### Requirement: Predicates narrow activation

A registry layer SHALL activate when it has no predicate or when every configured repository and changed-path predicate matches the target. A repository predicate MUST accept either one string pattern or a list of string patterns, MUST compare each pattern to the canonical `owner/name` repository using case-sensitive fnmatch semantics, and MUST match a list when at least one pattern matches. A changed-path predicate MUST match when at least one changed path matches at least one configured path pattern.

#### Scenario: Plain repository string retains exact-match behavior

- **WHEN** a layer names repository pattern `owner/repo`
- **THEN** it activates for repository `owner/repo` but not `owner/repository`

#### Scenario: Repository glob matches provider family

- **WHEN** a project layer names repository pattern `APIFuseHQ/apifuse-provider-*`
- **THEN** it activates for repository `APIFuseHQ/apifuse-provider-tabelog`

#### Scenario: Repository pattern list uses OR semantics

- **WHEN** a layer names repository patterns `owner/api-*` and `owner/web-*`
- **THEN** it activates for a target matching either pattern

#### Scenario: Repository patterns do not match

- **WHEN** a layer names repository patterns `owner/api-*` and `owner/web-*` but the target repository is `owner/worker`
- **THEN** that layer is not activated

#### Scenario: Repository and path predicates use AND semantics

- **WHEN** a layer names repository pattern `owner/api-*` and path pattern `src/api/**`
- **THEN** it activates only when both the repository and at least one changed path match

#### Scenario: Repository matching is case-sensitive

- **WHEN** a layer names repository pattern `APIFuseHQ/apifuse-*` but the target repository is `apifusehq/apifuse-provider-tabelog`
- **THEN** that layer is not activated

#### Scenario: Scope path does not match

- **WHEN** a scope layer names repository `owner/repo` and path `src/api/**` but the target changes only `README.md`
- **THEN** that scope layer is not activated

#### Scenario: Repo-agnostic scope matches

- **WHEN** a scope layer has only a `**/*.tsx` path predicate and the target changes `web/page.tsx`
- **THEN** that scope layer activates regardless of repository identity
