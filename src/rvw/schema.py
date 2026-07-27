"""Wire and disk models. See DECISIONS.md ADR-003, ADR-004."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

SCHEMA_VERSION = 1


class Severity(StrEnum):
    BLOCKER = "blocker"
    WARNING = "warning"
    SUGGESTION = "suggestion"


class Verdict(StrEnum):
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"
    UNCERTAIN = "UNCERTAIN"


class Tier(StrEnum):
    BASE = "base"
    PROJECT = "project"
    SCOPE = "scope"
    DYNAMIC = "dynamic"


class Finding(BaseModel):
    """One defect claim from one lane. Adjudication unit (ADR-003 D1)."""

    model_config = ConfigDict(extra="forbid")

    schema_version: int = Field(default=SCHEMA_VERSION, ge=1)
    rule_id: str
    file: str
    hunk_id: str
    line: int | None = None
    severity: Severity
    body: str
    anchorable: bool = False
    verdict: Verdict | None = None
    verdict_reason: str | None = None


class LaneOutput(BaseModel):
    """Strict JSON contract a runtime must satisfy (ADR-004 D5)."""

    model_config = ConfigDict(extra="forbid")

    verdict: str
    findings: list[Finding] = Field(  # pyright: ignore[reportUnknownVariableType]
        default_factory=list
    )


def finding_schema() -> dict[str, Any]:
    return Finding.model_json_schema()


def lane_output_schema() -> dict[str, Any]:
    return LaneOutput.model_json_schema()
