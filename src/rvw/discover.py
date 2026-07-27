"""DISCOVER orchestration: activate, prompt, dispatch, and enrich lane findings."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from rvw.dispatch import PlannedRun, dispatch
from rvw.hunks import hunk_for_line, is_anchorable, parse_hunks
from rvw.lane import Lane, load_lane
from rvw.prompts import build_lane_prompt
from rvw.registry import Registry
from rvw.runtimes import RunResult, RunStatus, Runtime
from rvw.schema import Finding, Tier
from rvw.target import ResolvedTarget


class _DiscoverRuntimeLane(Lane):
    """Bridge the runtime wire model until raw and enriched findings are separated."""

    def output_schema(self) -> dict[str, object]:
        schema = super().output_schema()
        properties = schema["properties"]
        findings = properties["findings"]
        items = findings["items"]
        finding_properties = items["properties"]
        finding_properties["hunk_id"] = {
            "type": "string",
            "description": "Temporary value; DISCOVER recomputes it from file and line.",
        }
        items["required"].append("hunk_id")
        return schema


class EnrichedFinding(Finding):
    """A runtime finding attributed to its lane and replica."""

    model_config = ConfigDict(extra="forbid")

    lane_id: str
    replica: int = Field(ge=1)


class LaneCoverage(BaseModel):
    """DISCOVER coverage and yield for one activated lane."""

    model_config = ConfigDict(extra="forbid")

    lane_id: str
    dispatched: int
    valid: int
    findings: int


@dataclass(frozen=True)
class DiscoverResult:
    lane_results: dict[str, list[RunResult]]
    findings: list[EnrichedFinding]
    coverage: list[LaneCoverage]


def resolve_lane_path(lanes_root: Path, lane_id: str, tier: Tier) -> Path:
    """Resolve a lane ID beneath the directory owned by its registry layer tier."""

    segments = lane_id.split("/")
    if not all(segment and segment not in {".", ".."} for segment in segments):
        raise ValueError(f"invalid lane id: {lane_id!r}")
    relative_segments = segments[1:] if segments[0] == tier.value else segments
    if not relative_segments:
        raise ValueError(f"invalid lane id: {lane_id!r}")
    attempted = lanes_root / tier.value / Path(*relative_segments).with_suffix(".md")
    if not attempted.is_file():
        raise FileNotFoundError(f"lane document not found; attempted path: {attempted}")
    return attempted


def _active_lane_owners(
    registry: Registry,
    target: ResolvedTarget,
    lane_filter: Sequence[str] | None,
) -> list[tuple[str, Tier]]:
    selected = set(lane_filter) if lane_filter is not None else None
    owners: list[tuple[str, Tier]] = []
    seen: set[str] = set()
    for layer in registry.activate(target.repo, target.changed_paths):
        for lane_id in layer.lanes:
            if (selected is None or lane_id in selected) and lane_id not in seen:
                owners.append((lane_id, layer.tier))
                seen.add(lane_id)
    return owners


def _effective_brief(
    target: ResolvedTarget,
    brief: str | None,
    brief_source: str | None,
) -> tuple[str | None, str | None]:
    del brief_source
    if brief is not None:
        return brief, "operator"
    if target.pr_title is not None or target.pr_body is not None:
        return f"{target.pr_title or ''}\n\n{target.pr_body or ''}", "pr_body"
    return None, None


async def discover(
    *,
    registry: Registry,
    lanes_root: Path,
    target: ResolvedTarget,
    runtime: Runtime,
    out_root: Path,
    brief: str | None = None,
    brief_source: str | None = None,
    replicas: int = 3,
    concurrency: int = 16,
    lane_filter: Sequence[str] | None = None,
    deadline_seconds: int = 600,
) -> DiscoverResult:
    """Run all activated lanes in one dispatch call and enrich valid findings."""

    if replicas < 1:
        raise ValueError("replicas must be at least 1")

    owners = _active_lane_owners(registry, target, lane_filter)
    lanes = [
        _DiscoverRuntimeLane.model_validate(
            load_lane(resolve_lane_path(lanes_root, lane_id, tier)).model_dump(by_alias=True)
        )
        for lane_id, tier in owners
    ]
    effective_brief, effective_brief_source = _effective_brief(target, brief, brief_source)
    covered_rules = {lane.id: lane.rules for lane in lanes}
    prompts = {
        lane.id: build_lane_prompt(
            lane,
            diff=target.diff,
            brief=effective_brief,
            brief_source=effective_brief_source,
            covered_rules=covered_rules,
        )
        for lane in lanes
    }
    planned_runs = [
        PlannedRun(lane=lane, prompt=prompts[lane.id], replica=replica)
        for lane in lanes
        for replica in range(1, replicas + 1)
    ]
    raw_results = await dispatch(
        planned_runs,
        runtime,
        out_root=out_root,
        concurrency=concurrency,
        deadline_seconds=deadline_seconds,
    )

    lane_results: dict[str, list[RunResult]] = {lane.id: [] for lane in lanes}
    for result in raw_results:
        lane_results[result.lane_id].append(result)

    hunks = parse_hunks(target.diff)
    enriched: list[EnrichedFinding] = []
    for result in raw_results:
        if result.status is not RunStatus.VALID or result.output is None:
            continue
        for finding in result.output.findings:
            hunk = (
                hunk_for_line(hunks, finding.file, finding.line)
                if finding.line is not None
                else None
            )
            anchorable = (
                is_anchorable(hunks, finding.file, finding.line)
                if finding.line is not None
                else False
            )
            enriched.append(
                EnrichedFinding.model_validate(
                    {
                        **finding.model_dump(),
                        "hunk_id": hunk.hunk_id if hunk is not None else f"{finding.file}:*",
                        "anchorable": anchorable,
                        "lane_id": result.lane_id,
                        "replica": result.replica,
                    }
                )
            )

    coverage: list[LaneCoverage] = []
    for lane in lanes:
        results = lane_results[lane.id]
        valid = sum(result.status is RunStatus.VALID for result in results)
        findings = sum(finding.lane_id == lane.id for finding in enriched)
        coverage.append(
            LaneCoverage(
                lane_id=lane.id,
                dispatched=replicas,
                valid=valid,
                findings=findings,
            )
        )

    return DiscoverResult(lane_results=lane_results, findings=enriched, coverage=coverage)


__all__: list[str] = [
    "DiscoverResult",
    "EnrichedFinding",
    "LaneCoverage",
    "discover",
    "resolve_lane_path",
]
