## MODIFIED Requirements

### Requirement: Pending validation is visible

The lane listing MUST display `validation: pending` and a sampling result with no novel free-variant rule IDs SHALL tell the operator that the marker may be removed, regardless of in-enum site variance.

#### Scenario: Sample passes with site variance

- **WHEN** a pending lane's enum-versus-free sample has no free-variant rule ID outside its closed enum but has in-enum site variance
- **THEN** the sample reports PASS and the CLI prints that the pending marker may be removed
