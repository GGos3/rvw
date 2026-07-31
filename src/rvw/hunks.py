"""Parse unified diff hunks and determine valid new-side anchors."""

from __future__ import annotations

import ast
import hashlib
import re

from pydantic import BaseModel, ConfigDict

_HUNK_HEADER = re.compile(
    r"^@@ -(?P<old_start>\d+)(?:,(?P<old_count>\d+))? "
    r"\+(?P<new_start>\d+)(?:,(?P<new_count>\d+))? @@"
)


class Hunk(BaseModel):
    """One unified-diff hunk and its new-side line classifications."""

    model_config = ConfigDict(extra="forbid")

    file: str
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    added_lines: set[int]
    context_lines: set[int]
    raw_text: str = ""

    @property
    def hunk_id(self) -> str:
        return (
            f"{self.file}@@-{self.old_start},{self.old_count}+{self.new_start},{self.new_count}@@"
        )


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


def _hunk_from_header(header: re.Match[str], file: str) -> Hunk:
    return Hunk(
        file=file,
        old_start=int(header.group("old_start")),
        old_count=int(header.group("old_count") or "1"),
        new_start=int(header.group("new_start")),
        new_count=int(header.group("new_count") or "1"),
        added_lines=set(),
        context_lines=set(),
    )


def parse_hunks(diff: str) -> list[Hunk]:
    """Parse all hunks in a unified diff, preserving new-side line numbers."""

    hunks: list[Hunk] = []
    old_path: str | None = None
    file: str | None = None
    active: Hunk | None = None
    active_raw_lines: list[str] = []
    active_complete = False
    previous_counted_line = False
    old_line = 0
    new_line = 0

    def finalize_active() -> None:
        nonlocal active, active_raw_lines, active_complete, previous_counted_line
        if active is not None:
            active.raw_text = "".join(active_raw_lines)
        active = None
        active_raw_lines = []
        active_complete = False
        previous_counted_line = False

    raw_lines = diff.split("\n")
    for index, raw_line in enumerate(raw_lines):
        if index == len(raw_lines) - 1:
            if not raw_line:
                break
        else:
            raw_line += "\n"
        line = raw_line.rstrip("\r\n")
        if active is not None and active_complete:
            if line.startswith("\\") and previous_counted_line:
                active_raw_lines.append(raw_line)
                finalize_active()
                continue
            finalize_active()

        header = _HUNK_HEADER.match(line)
        if header:
            if file is None:
                continue
            finalize_active()
            new_hunk = _hunk_from_header(header, file)
            active = new_hunk
            active_raw_lines = [raw_line]
            hunks.append(new_hunk)
            old_line = new_hunk.old_start
            new_line = new_hunk.new_start
            if new_hunk.old_count == 0 and new_hunk.new_count == 0:
                finalize_active()
            continue

        if active is not None:
            active_raw_lines.append(raw_line)
            if line.startswith("\\") and previous_counted_line:
                previous_counted_line = False
                continue
            if line.startswith("+"):
                active.added_lines.add(new_line)
                new_line += 1
            elif line.startswith("-"):
                old_line += 1
            elif line.startswith(" "):
                active.context_lines.add(new_line)
                old_line += 1
                new_line += 1
            previous_counted_line = line.startswith(("+", "-", " "))

            old_complete = old_line >= active.old_start + active.old_count
            new_complete = new_line >= active.new_start + active.new_count
            if old_complete and new_complete:
                active_complete = True
            continue

        if line.startswith("--- "):
            old_path = _header_path(line[4:])
            continue
        if line.startswith("+++ "):
            new_path = _header_path(line[4:])
            file = new_path or old_path
            continue
        if line.startswith("diff --git "):
            old_path = None
            file = None

    finalize_active()
    return hunks


def hunk_sha256_by_id(diff: str) -> dict[str, str]:
    """Return SHA-256 digests of exact unified-diff hunk text by canonical hunk ID."""

    return {
        hunk.hunk_id: hashlib.sha256(hunk.raw_text.encode()).hexdigest()
        for hunk in parse_hunks(diff)
    }


def hunk_for_line(hunks: list[Hunk], file: str, line: int) -> Hunk | None:
    """Return the hunk whose new-side range contains ``file:line``."""

    for hunk in hunks:
        if hunk.file == file and hunk.new_start <= line < hunk.new_start + hunk.new_count:
            return hunk
    return None


def is_anchorable(hunks: list[Hunk], file: str, line: int) -> bool:
    """Return whether ``file:line`` is an added line accepted by GitHub anchors."""

    hunk = hunk_for_line(hunks, file, line)
    return hunk is not None and line in hunk.added_lines
