"""Generated-path filtering and hard size guards for review diffs."""

from __future__ import annotations

import ast
import fnmatch
import re
import shlex
from collections.abc import Sequence
from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict

DEFAULT_GENERATED_GLOBS = [
    "**/runtime-snapshots/**",
    "**/*.generated.*",
    "**/generated/**",
    "**/*.lock",
    "**/package-lock.json",
    "**/bun.lockb",
    "**/pnpm-lock.yaml",
    "**/dist/**",
    "**/__snapshots__/**",
]
"""Generated-file globs; a future registry may override this default list."""

_DIFF_HEADER = re.compile(r"^diff --git .+$", re.MULTILINE)
_OLD_FILE_HEADER = re.compile(r"^--- (?P<path>.+)$", re.MULTILINE)
_NEW_FILE_HEADER = re.compile(r"^\+\+\+ (?P<path>.+)$", re.MULTILINE)


class DiffBudgetReport(BaseModel):
    """Character accounting and file-level exclusions for one review diff."""

    model_config = ConfigDict(extra="forbid")

    kept_files: list[str]
    excluded_files: list[str]
    excluded_reason: dict[str, str]
    kept_chars: int
    excluded_chars: int


class DiffBudgetExceeded(RuntimeError):
    """The non-excluded review diff still exceeds its aggregate hard limit."""

    def __init__(
        self,
        *,
        total_chars: int,
        max_total_chars: int,
        offenders: list[tuple[str, int]],
    ) -> None:
        self.total_chars = total_chars
        self.max_total_chars = max_total_chars
        self.offenders = offenders
        detail = ", ".join(f"{path} ({size} chars)" for path, size in offenders)
        super().__init__(
            f"review diff is {total_chars} chars after exclusions, exceeding the "
            f"{max_total_chars}-char total budget; top offenders: {detail}"
        )


@dataclass(frozen=True)
class DiffFileSegment:
    """One complete per-file unified-diff segment."""

    file: str
    text: str


def _header_path(raw: str) -> str | None:
    path = raw.split("\t", maxsplit=1)[0]
    if path == "/dev/null":
        return None
    if path.startswith('"') and path.endswith('"'):
        decoded = ast.literal_eval(path)
        if isinstance(decoded, str):
            path = decoded
    if path.startswith(("a/", "b/")):
        return path[2:]
    return path


def _segment_path(segment: str) -> str:
    old_match = _OLD_FILE_HEADER.search(segment)
    new_match = _NEW_FILE_HEADER.search(segment)
    old_path = _header_path(old_match.group("path")) if old_match else None
    new_path = _header_path(new_match.group("path")) if new_match else None
    if new_path or old_path:
        return new_path or old_path or ""

    first_line = next(
        (line for line in segment.splitlines() if line.startswith("diff --git ")),
        None,
    )
    if first_line is not None:
        parts = shlex.split(first_line)
        if len(parts) >= 4:
            fallback = _header_path(parts[3])
            if fallback is not None:
                return fallback
    raise ValueError("unified diff segment has no identifiable file path")


def split_diff_files(diff: str) -> list[DiffFileSegment]:
    """Split a unified diff into complete file segments with exact accounting."""

    if not diff:
        return []
    starts = [match.start() for match in _DIFF_HEADER.finditer(diff)]
    if not starts:
        starts = [match.start() for match in _OLD_FILE_HEADER.finditer(diff)]
    if not starts:
        raise ValueError("diff contains no per-file headers")

    chunks: list[str] = []
    for index, start in enumerate(starts):
        segment_start = 0 if index == 0 else start
        segment_end = starts[index + 1] if index + 1 < len(starts) else len(diff)
        chunks.append(diff[segment_start:segment_end])

    combined: dict[str, str] = {}
    for chunk in chunks:
        path = _segment_path(chunk)
        combined[path] = f"{combined.get(path, '')}{chunk}"
    return [DiffFileSegment(file=path, text=text) for path, text in combined.items()]


def _matches_generated_glob(path: str, patterns: Sequence[str]) -> bool:
    for pattern in patterns:
        if fnmatch.fnmatchcase(path, pattern):
            return True
        if pattern.startswith("**/") and fnmatch.fnmatchcase(path, pattern[3:]):
            return True
    return False


def apply_diff_budget(
    diff: str,
    *,
    generated_globs: Sequence[str] = DEFAULT_GENERATED_GLOBS,
    max_file_chars: int = 200_000,
    max_total_chars: int = 400_000,
) -> tuple[str, DiffBudgetReport]:
    """Filter generated/oversize files, then enforce the aggregate diff limit."""

    if max_file_chars < 0 or max_total_chars < 0:
        raise ValueError("diff budget limits must be non-negative")

    segments = split_diff_files(diff)
    kept: list[DiffFileSegment] = []
    excluded: list[DiffFileSegment] = []
    reasons: dict[str, str] = {}
    for segment in segments:
        if _matches_generated_glob(segment.file, generated_globs):
            excluded.append(segment)
            reasons[segment.file] = "generated-path"
        elif len(segment.text) > max_file_chars:
            excluded.append(segment)
            reasons[segment.file] = "oversize-file"
        else:
            kept.append(segment)

    kept_chars = sum(len(segment.text) for segment in kept)
    if kept_chars > max_total_chars:
        offenders = sorted(
            ((segment.file, len(segment.text)) for segment in kept),
            key=lambda item: (-item[1], item[0]),
        )
        raise DiffBudgetExceeded(
            total_chars=kept_chars,
            max_total_chars=max_total_chars,
            offenders=offenders,
        )

    report = DiffBudgetReport(
        kept_files=[segment.file for segment in kept],
        excluded_files=[segment.file for segment in excluded],
        excluded_reason=reasons,
        kept_chars=kept_chars,
        excluded_chars=sum(len(segment.text) for segment in excluded),
    )
    filtered = "".join(segment.text for segment in kept)
    if excluded:
        paths = ", ".join(segment.file for segment in excluded)
        header = (
            f"# rvw: {len(excluded)} files excluded from review diff "
            f"(generated/oversize): {paths}\n"
        )
        filtered = f"{header}{filtered}"
    return filtered, report


__all__ = [
    "DEFAULT_GENERATED_GLOBS",
    "DiffBudgetExceeded",
    "DiffBudgetReport",
    "DiffFileSegment",
    "apply_diff_budget",
    "split_diff_files",
]
