## ADDED Requirements

### Requirement: No-valid-output adjudication fails as infrastructure

An adjudication pass MUST fail with a run-level adjudication infrastructure error when its initial and one retry wave contain no valid outputs. The error MUST identify the pass and each attempted replica with its normalized failure reason and available exit or log diagnostics, and no outcome with a populated verdict map MAY be produced from that pass.

#### Scenario: Empty responses survive the retry

- **WHEN** every initial and retry adjudicator response is absent or zero bytes
- **THEN** adjudication fails with attempt diagnostics and produces no synthetic UNCERTAIN verdicts

#### Scenario: Expanded pass has no valid output

- **WHEN** initial valid votes require expanded adjudication and both expanded waves contain no valid output
- **THEN** the entire adjudication stage fails instead of publishing the initial map as a completed outcome

### Requirement: UNCERTAIN always explains uncertainty

Every runtime UNCERTAIN item and every persisted final UNCERTAIN verdict MUST carry a non-empty reason. Omitted candidates, unsupported rejections coerced to UNCERTAIN, and no-majority votes MUST receive explicit machine-generated reasons when a valid model reason is unavailable.

#### Scenario: Adjudicator emits an empty UNCERTAIN reason

- **WHEN** an adjudication response contains an UNCERTAIN item whose reason is empty or whitespace-only
- **THEN** strict schema validation marks that response invalid

#### Scenario: Valid response omits a candidate

- **WHEN** a valid response omits one supplied candidate
- **THEN** its UNCERTAIN vote carries a non-empty omission reason
