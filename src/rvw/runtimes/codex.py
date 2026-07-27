"""Read-only ``codex exec`` runtime adapter."""

from __future__ import annotations

import asyncio
import json
import re
import time
from pathlib import Path

from pydantic import ValidationError

from rvw.lane import Lane
from rvw.runtimes import RunResult, RunStatus
from rvw.schema import RuntimeLaneOutput

_REPLICA_DIRECTORY = re.compile(r"r([1-9][0-9]*)")
_COMPLETION_MARKER = "tokens used"


async def _spawn(cmd: list[str], stdin_text: str, log_path: Path) -> int:
    """Run a command without a shell and combine its output in one log."""

    with log_path.open("wb") as log_file:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=log_file,
            stderr=asyncio.subprocess.STDOUT,
        )
        await process.communicate(stdin_text.encode("utf-8"))
    if process.returncode is None:
        raise RuntimeError("subprocess completed without a return code")
    return process.returncode


def validate_output(lane: Lane, raw: object) -> RuntimeLaneOutput:
    """Validate the common output model and the lane-specific closed rule enum."""

    output = RuntimeLaneOutput.model_validate(raw)
    prefix = lane.rules[0].split("/", maxsplit=1)[0]
    allowed_rule_ids = {*lane.rules, f"{prefix}/other"}
    if any(finding.rule_id not in allowed_rule_ids for finding in output.findings):
        raise ValueError("finding rule_id is outside the lane rule enum")
    return output


def _replica_from_run_dir(run_dir: Path) -> int:
    match = _REPLICA_DIRECTORY.fullmatch(run_dir.name)
    if match is None:
        raise ValueError("run_dir must end in an r<replica> directory")
    return int(match.group(1))


class CodexRuntime:
    name = "codex-exec-ro"

    async def execute(
        self,
        *,
        lane: Lane,
        prompt: str,
        run_dir: Path,
        deadline_seconds: int,
    ) -> RunResult:
        if deadline_seconds < 1:
            raise ValueError("deadline_seconds must be at least 1")
        replica = _replica_from_run_dir(run_dir)

        run_dir.mkdir(parents=True, exist_ok=True)
        prompt_path = run_dir / "prompt.md"
        schema_path = run_dir / "schema.json"
        output_path = run_dir / "out.json"
        log_path = run_dir / "run.log"
        prompt_path.write_text(prompt, encoding="utf-8")
        schema_path.write_text(
            json.dumps(lane.output_schema(), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        output_path.unlink(missing_ok=True)

        command = [
            "timeout",
            "--foreground",
            "--signal=TERM",
            "--kill-after=30s",
            f"{deadline_seconds}s",
            "codex",
            "exec",
            "--sandbox",
            "read-only",
            "--color",
            "never",
            "-c",
            "features.multi_agent=false",
            "-c",
            "features.collaboration_modes=false",
            "--output-schema",
            str(schema_path),
            "-o",
            str(output_path),
            "-",
        ]

        started = time.perf_counter()
        try:
            exit_code = await _spawn(command, prompt, log_path)
        except OSError as error:
            return self._invalid_result(
                lane=lane,
                replica=replica,
                reason=f"spawn_error:{type(error).__name__}",
                started=started,
                run_dir=run_dir,
            )

        if exit_code != 0:
            return self._invalid_result(
                lane=lane,
                replica=replica,
                reason=f"exit_nonzero:{exit_code}",
                started=started,
                run_dir=run_dir,
            )
        if not output_path.is_file() or output_path.stat().st_size == 0:
            return self._invalid_result(
                lane=lane,
                replica=replica,
                reason="missing_artifact",
                started=started,
                run_dir=run_dir,
            )

        try:
            raw: object = json.loads(output_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return self._invalid_result(
                lane=lane,
                replica=replica,
                reason="json_parse_error",
                started=started,
                run_dir=run_dir,
            )

        try:
            output = validate_output(lane, raw)
        except (ValidationError, ValueError):
            return self._invalid_result(
                lane=lane,
                replica=replica,
                reason="schema_validation_error",
                started=started,
                run_dir=run_dir,
            )

        try:
            completed = _COMPLETION_MARKER in log_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            completed = False
        if not completed:
            return self._invalid_result(
                lane=lane,
                replica=replica,
                reason="no_completion_marker",
                started=started,
                run_dir=run_dir,
            )

        return RunResult(
            lane_id=lane.id,
            replica=replica,
            status=RunStatus.VALID,
            output=output,
            invalid_reason=None,
            wall_seconds=time.perf_counter() - started,
            artifact_dir=run_dir,
        )

    @staticmethod
    def _invalid_result(
        *,
        lane: Lane,
        replica: int,
        reason: str,
        started: float,
        run_dir: Path,
    ) -> RunResult:
        return RunResult(
            lane_id=lane.id,
            replica=replica,
            status=RunStatus.INVALID,
            output=None,
            invalid_reason=reason,
            wall_seconds=time.perf_counter() - started,
            artifact_dir=run_dir,
        )


__all__: list[str] = ["CodexRuntime", "validate_output"]
