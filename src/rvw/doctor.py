"""Recent run-store health metrics (ADR-005)."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict

from rvw.schema import Verdict
from rvw.store import RunHandle, RunStore, StageMissing


class LaneStat(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lane_id: str
    runs: int
    invalid: int
    findings: int
    other_rate: float


class AdjStat(BaseModel):
    model_config = ConfigDict(extra="forbid")

    groups: int
    confirmed: int
    rejected: int
    uncertain_unresolved: int
    rejection_rate: float
    coerced_rejections: int


class DoctorReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    runs_scanned: int
    lanes: list[LaneStat]
    adjudication: AdjStat | None


@dataclass
class _LaneCounts:
    runs: int = 0
    invalid: int = 0
    findings: int = 0
    other: int = 0


def diagnose(store: RunStore, *, last: int = 20) -> DoctorReport:
    """Aggregate health statistics from the newest discover-bearing runs."""

    if last < 1:
        raise ValueError("last must be at least 1")
    if not store.root.is_dir():
        return DoctorReport(runs_scanned=0, lanes=[], adjudication=None)

    candidates = [
        path
        for path in store.root.iterdir()
        if path.is_dir() and (path / "discover.json").is_file()
    ]
    selected = sorted(candidates, key=lambda path: (-path.stat().st_mtime_ns, path.name))[:last]
    lane_counts: dict[str, _LaneCounts] = defaultdict(_LaneCounts)
    groups = confirmed = rejected = uncertain_unresolved = coerced_rejections = 0
    outcomes_found = 0

    for run_dir in selected:
        run = RunHandle(run_id=run_dir.name, dir=run_dir)
        discovered = run.load_discover()
        for coverage in discovered.coverage:
            counts = lane_counts[coverage.lane_id]
            counts.runs += coverage.dispatched
            counts.invalid += coverage.dispatched - coverage.valid
        for finding in discovered.findings:
            counts = lane_counts[finding.lane_id]
            counts.findings += 1
            counts.other += finding.rule_id.endswith("/other")

        try:
            outcome = run.load_outcome()
        except StageMissing:
            continue
        outcomes_found += 1
        groups += len(outcome.verdicts)
        confirmed += sum(verdict is Verdict.CONFIRMED for verdict in outcome.verdicts.values())
        rejected += sum(verdict is Verdict.REJECTED for verdict in outcome.verdicts.values())
        uncertain_unresolved += len(outcome.unresolved)
        coerced_rejections += outcome.coerced_rejections

    lanes = [
        LaneStat(
            lane_id=lane_id,
            runs=counts.runs,
            invalid=counts.invalid,
            findings=counts.findings,
            other_rate=counts.other / counts.findings if counts.findings else 0.0,
        )
        for lane_id, counts in sorted(lane_counts.items())
    ]
    adjudication = None
    if outcomes_found:
        adjudication = AdjStat(
            groups=groups,
            confirmed=confirmed,
            rejected=rejected,
            uncertain_unresolved=uncertain_unresolved,
            rejection_rate=rejected / groups if groups else 0.0,
            coerced_rejections=coerced_rejections,
        )
    return DoctorReport(
        runs_scanned=len(selected),
        lanes=lanes,
        adjudication=adjudication,
    )


__all__ = ["AdjStat", "DoctorReport", "LaneStat", "diagnose"]
