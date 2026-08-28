"""Strict terminal status contract shared by persistence, CLI JSON, and reports."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from rvw.adjudicate import AdjudicationAttempt
from rvw.discover import DiscoverResult
from rvw.runtimes import RunDiagnostic


class ReviewStatus(StrEnum):
    RUNNING = "running"
    COMPLETE = "complete"
    DEGRADED = "degraded"
    FAILED = "failed"


class CoverageTotals(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    dispatched: int = Field(ge=0)
    valid: int = Field(ge=0)
    findings: int = Field(ge=0)


class LaneFailure(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    replica: int = Field(ge=1)
    chunk: int = Field(ge=1)
    reason: str
    diagnostic: RunDiagnostic | None = None

    @model_validator(mode="after")
    def _reason_must_not_be_blank(self) -> LaneFailure:
        if not self.reason.strip():
            raise ValueError("lane failure reason must not be blank")
        return self


class FailedLane(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    lane_id: str
    failures: list[LaneFailure]


class RunError(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    stage: str
    reason: str
    message: str
    attempts: list[AdjudicationAttempt] = Field(default_factory=list)


class RunSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: int = Field(default=1, ge=1)
    run_id: str
    status: ReviewStatus
    failed_lanes: list[FailedLane]
    coverage_totals: CoverageTotals
    error: RunError | None


def coverage_totals(discovered: DiscoverResult) -> CoverageTotals:
    return CoverageTotals(
        dispatched=sum(item.dispatched for item in discovered.coverage),
        valid=sum(item.valid for item in discovered.coverage),
        findings=sum(item.findings for item in discovered.coverage),
    )


def failed_lanes(discovered: DiscoverResult) -> list[FailedLane]:
    failed: list[FailedLane] = []
    for lane in discovered.coverage:
        failures = [
            LaneFailure(
                replica=run.replica,
                chunk=run.chunk,
                reason=run.invalid_reason or "unknown",
                diagnostic=run.diagnostic,
            )
            for run in lane.runs
            if not run.valid
        ]
        if failures:
            failed.append(FailedLane(lane_id=lane.lane_id, failures=failures))
    return failed


def summarize_run(
    run_id: str,
    discovered: DiscoverResult,
    *,
    error: RunError | None = None,
) -> RunSummary:
    totals = coverage_totals(discovered)
    failures = failed_lanes(discovered)
    if error is not None or (failures and totals.valid == 0):
        status = ReviewStatus.FAILED
    elif failures:
        status = ReviewStatus.DEGRADED
    else:
        status = ReviewStatus.COMPLETE
    return RunSummary(
        run_id=run_id,
        status=status,
        failed_lanes=failures,
        coverage_totals=totals,
        error=error,
    )


def running_summary(run_id: str) -> RunSummary:
    return RunSummary(
        run_id=run_id,
        status=ReviewStatus.RUNNING,
        failed_lanes=[],
        coverage_totals=CoverageTotals(dispatched=0, valid=0, findings=0),
        error=None,
    )


__all__ = [
    "CoverageTotals",
    "FailedLane",
    "LaneFailure",
    "ReviewStatus",
    "RunError",
    "RunSummary",
    "coverage_totals",
    "failed_lanes",
    "running_summary",
    "summarize_run",
]
