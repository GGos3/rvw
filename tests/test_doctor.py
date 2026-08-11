from __future__ import annotations

import json
import os
from pathlib import Path

from rvw.doctor import diagnose
from rvw.store import RunStore


def write_run(
    root: Path,
    name: str,
    *,
    findings: list[dict[str, object]],
    coverage: list[dict[str, object]],
    outcome: dict[str, object] | None = None,
    mtime: int = 1,
) -> None:
    run = root / name
    run.mkdir(parents=True)
    (run / "discover.json").write_text(
        json.dumps({"findings": findings, "coverage": coverage, "budget": None}),
        encoding="utf-8",
    )
    if outcome is not None:
        (run / "outcome.json").write_text(json.dumps(outcome), encoding="utf-8")
    os.utime(run, (mtime, mtime))


def finding(lane_id: str, rule_id: str) -> dict[str, object]:
    return {
        "schema_version": 1,
        "rule_id": rule_id,
        "file": "a.py",
        "hunk_id": "a.py:1",
        "line": 1,
        "severity": "warning",
        "body": "body",
        "anchorable": True,
        "verdict": None,
        "verdict_reason": None,
        "lane_id": lane_id,
        "replica": 1,
    }


def outcome(
    verdicts: dict[str, str],
    *,
    unresolved: list[str] | None = None,
    coerced: int = 0,
) -> dict[str, object]:
    return {
        "verdicts": verdicts,
        "reasons": {
            key: "requires manual verification"
            for key, verdict in verdicts.items()
            if verdict == "UNCERTAIN"
        },
        "evidence": {},
        "replica_votes": {},
        "unresolved": unresolved or [],
        "coerced_rejections": coerced,
    }


def coverage(lane_id: str, *, dispatched: int, valid: int, findings: int) -> dict[str, object]:
    return {
        "lane_id": lane_id,
        "dispatched": dispatched,
        "valid": valid,
        "findings": findings,
        "runs": [
            {
                "replica": replica,
                "chunk": 1,
                "valid": replica <= valid,
                "findings": findings if replica == 1 else 0,
                "invalid_reason": None if replica <= valid else "scripted_invalid",
            }
            for replica in range(1, dispatched + 1)
        ],
    }


def test_empty_store(tmp_path: Path) -> None:
    report = diagnose(RunStore(tmp_path))
    assert report.runs_scanned == 0
    assert report.lanes == []
    assert report.adjudication is None


def test_counts_lane_health_and_adjudication(tmp_path: Path) -> None:
    write_run(
        tmp_path,
        "one",
        findings=[finding("lane-a", "lane/rule"), finding("lane-a", "lane/other")],
        coverage=[coverage("lane-a", dispatched=3, valid=2, findings=2)],
        outcome=outcome(
            {"confirmed": "CONFIRMED", "rejected": "REJECTED", "uncertain": "UNCERTAIN"},
            unresolved=["uncertain"],
            coerced=2,
        ),
        mtime=1,
    )
    write_run(
        tmp_path,
        "two",
        findings=[finding("lane-b", "b/other")],
        coverage=[
            coverage("lane-a", dispatched=3, valid=3, findings=0),
            coverage("lane-b", dispatched=2, valid=1, findings=1),
        ],
        outcome=outcome({"confirmed-2": "CONFIRMED"}),
        mtime=2,
    )
    report = diagnose(RunStore(tmp_path))
    assert report.runs_scanned == 2
    assert [stat.lane_id for stat in report.lanes] == ["lane-a", "lane-b"]
    assert report.lanes[0].model_dump() == {
        "lane_id": "lane-a",
        "runs": 6,
        "invalid": 1,
        "findings": 2,
        "other_rate": 0.5,
    }
    assert report.lanes[1].other_rate == 1.0
    assert report.adjudication is not None
    assert report.adjudication.model_dump() == {
        "groups": 4,
        "confirmed": 2,
        "rejected": 1,
        "uncertain_unresolved": 1,
        "rejection_rate": 0.25,
        "coerced_rejections": 2,
    }


def test_partial_runs_and_last_n_by_directory_mtime(tmp_path: Path) -> None:
    write_run(
        tmp_path,
        "old",
        findings=[finding("old", "old/other")],
        coverage=[coverage("old", dispatched=1, valid=0, findings=0)],
        mtime=1,
    )
    write_run(
        tmp_path,
        "new",
        findings=[],
        coverage=[coverage("new", dispatched=3, valid=3, findings=0)],
        mtime=2,
    )
    incomplete = tmp_path / "newest-without-discover"
    incomplete.mkdir()
    os.utime(incomplete, (3, 3))
    report = diagnose(RunStore(tmp_path), last=1)
    assert report.runs_scanned == 1
    assert [stat.lane_id for stat in report.lanes] == ["new"]
    assert report.adjudication is None
