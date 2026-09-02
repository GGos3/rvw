## MODIFIED Requirements

### Requirement: Lane documents are single-file rule bundles

A new-format lane MUST be one Markdown file with YAML frontmatter containing
`lane`, `tier`, `cost`, optional `severity_cap`, optional `when.paths`, and
optional `validation`/`covered_by_others`, followed by a Markdown body. Rule IDs
MUST be derived only from `## rule: <id>` headings. A `rules:` frontmatter key is
an error when rule headings are present; duplicate IDs and empty rule bodies are
errors. `when.repo` is not accepted in the new format.

#### Scenario: Rule headings are authoritative

- **WHEN** a lane body contains `## rule: api/contract` and no frontmatter `rules` key
- **THEN** loading returns `rules == ["api/contract"]`

#### Scenario: Stale double declaration fails

- **WHEN** a lane contains both a `rules:` frontmatter key and one or more `## rule:` headings
- **THEN** loading fails with a machine-readable stale-rules error

### Requirement: Common lanes are packaged defaults

The package MUST ship the current base, scope, and dynamic lanes as data in the
new format. Scope activation globs MUST live in each lane's `when.paths`
frontmatter, including root-level glob twins where required by fnmatch.

#### Scenario: Packaged scope lane activates by its own paths

- **WHEN** a packaged scope lane declares `when.paths: ["**/*.tsx", "*.tsx"]` and a changed path is `View.tsx`
- **THEN** the lane activates without consulting `layers.yaml`

### Requirement: Repository rules are loaded from the resolved base

For a target repository, the loader MUST discover `.rvw/lanes/**/*.md` and the
optional `.rvw/policies/auto.yaml` from the same resolved base revision used for
the target diff. It MUST NOT read those paths from the working tree or PR head
by default. Project lanes are bound by residing in `.rvw/` and are
unconditional. `--allow-worktree-rules` MAY opt into working-tree reads and MUST
stamp run metadata and rendered reports with a clear non-SoT warning.

#### Scenario: Working-tree rule changes are ignored by default

- **WHEN** a project lane exists only in the working tree and the target base revision does not contain it
- **THEN** the lane is absent from the effective set

#### Scenario: Explicit worktree escape hatch is visible

- **WHEN** a review uses `--allow-worktree-rules`
- **THEN** working-tree lanes may activate and run/report metadata contains a non-SoT warning

### Requirement: Effective source precedence is explicit

The effective lane set MUST contain packaged defaults, base-ref repository
project lanes, and lanes from the deprecated external registry when it exists.
On lane-id collision precedence MUST be repository `.rvw/` over external over
packaged. The external loader MUST continue to read the old `layers.yaml` and
old frontmatter format unchanged and MUST emit a deprecation warning naming
`.rvw/` as its replacement.

#### Scenario: Repository lane overrides a packaged collision

- **WHEN** the same lane ID is present in package data and `.rvw/lanes/`
- **THEN** the repository document is selected and the packaged document is ignored

### Requirement: Activation semantics remain stable

Base and dynamic lanes MUST always activate. New-format scope lanes MUST
activate when at least one changed path matches at least one `when.paths` glob;
new-format project lanes MUST always activate. Existing tier ordering, cost,
severity caps, and downstream execution semantics MUST remain unchanged.

#### Scenario: Scope path mismatch does not activate

- **WHEN** a new-format scope lane matches `src/**/*.py` but the diff changes only `README.md`
- **THEN** the lane is not active

### Requirement: Lane lint is machine-readable

`rvw lanes lint` MUST validate packaged lanes, repository lanes, or an explicit
path for frontmatter schema, unknown keys, stale `rules:`, duplicate rule IDs,
empty rule bodies, and duplicate lane IDs across sources. It MUST emit stable
failure reason codes and exit 0 when valid or 1 when invalid.

#### Scenario: Lint reports duplicate IDs

- **WHEN** two selected lane files declare the same lane ID or a file repeats a rule heading ID
- **THEN** `rvw lanes lint` exits 1 and emits the corresponding stable reason code in machine-readable output
