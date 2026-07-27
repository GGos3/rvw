"""Runtime contracts for executing review lanes."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Protocol

from rvw.lane import Lane
from rvw.schema import LaneOutput


class RunStatus(StrEnum):
    VALID = "valid"
    INVALID = "invalid"


@dataclass(frozen=True, slots=True)
class RunResult:
    lane_id: str
    replica: int
    status: RunStatus
    output: LaneOutput | None
    invalid_reason: str | None
    wall_seconds: float
    artifact_dir: Path

    def __post_init__(self) -> None:
        if self.replica < 1:
            raise ValueError("replica must be at least 1")
        if self.wall_seconds < 0:
            raise ValueError("wall_seconds must not be negative")
        if self.status is RunStatus.VALID:
            if self.output is None or self.invalid_reason is not None:
                raise ValueError("VALID results require output and no invalid_reason")
        elif self.output is not None or self.invalid_reason is None:
            raise ValueError("INVALID results require invalid_reason and no output")


class Runtime(Protocol):
    name: str

    async def execute(
        self,
        *,
        lane: Lane,
        prompt: str,
        run_dir: Path,
        deadline_seconds: int,
    ) -> RunResult: ...


__all__: list[str] = ["RunResult", "RunStatus", "Runtime"]
