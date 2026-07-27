import pytest
from pydantic import ValidationError

from rvw.schema import SCHEMA_VERSION, Finding, RuntimeFinding, Severity


def test_runtime_finding_has_exact_wire_fields() -> None:
    raw = {
        "rule_id": "slop/dup",
        "file": "a.ts",
        "line": 4,
        "severity": Severity.WARNING,
        "body": "x",
    }

    finding = RuntimeFinding.model_validate(raw)

    assert finding.model_dump() == raw
    with pytest.raises(ValidationError):
        RuntimeFinding.model_validate({**raw, "hunk_id": "a.ts@@-1,4+1,6@@"})


def test_finding_requires_known_severity() -> None:
    with pytest.raises(ValidationError):
        Finding(
            rule_id="slop/dup",
            file="a.ts",
            hunk_id="a.ts@@-1,4+1,6@@",
            line=4,
            severity="catastrophic",  # pyright: ignore[reportArgumentType]
            body="x",  # type: ignore[arg-type]
        )


def test_finding_carries_schema_version() -> None:
    f = Finding(
        rule_id="slop/dup",
        file="a.ts",
        hunk_id="a.ts@@-1,4+1,6@@",
        line=4,
        severity=Severity.WARNING,
        body="x",
    )
    assert f.schema_version == SCHEMA_VERSION
    assert f.verdict is None


def test_finding_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        Finding(
            rule_id="slop/dup",
            file="a.ts",
            hunk_id="a.ts@@-1,4+1,6@@",
            line=4,
            severity=Severity.WARNING,
            body="x",
            bogus=1,  # type: ignore[call-arg]
        )
