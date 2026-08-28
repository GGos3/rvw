"""Honest build identity loaded from build-time facts or exact runtime package bytes."""

from __future__ import annotations

import hashlib
import json
import shlex
import subprocess
from functools import lru_cache
from importlib.metadata import PackageNotFoundError, distribution
from pathlib import Path
from urllib.parse import unquote, urlparse

from pydantic import BaseModel, ConfigDict

from rvw import __version__
from rvw._build_provenance import BUILD_ID, BUILT_AT, SOURCE_COMMIT, SOURCE_DIRTY


class BuildProvenance(BaseModel):
    """Immutable identity for the code that produced an artifact."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    version: str
    build_id: str
    source_commit: str | None
    source_dirty: bool | None
    built_at: str | None


def _runtime_package_id() -> str:
    package_root = Path(__file__).parent
    digest = hashlib.sha256()
    for path in sorted(package_root.rglob("*.py")):
        relative = path.relative_to(package_root).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return f"sha256:{digest.hexdigest()}"


@lru_cache(maxsize=1)
def current_build_provenance() -> BuildProvenance:
    """Return build-time provenance without consulting mutable source-control state."""

    return BuildProvenance(
        version=__version__,
        build_id=BUILD_ID or _runtime_package_id(),
        source_commit=SOURCE_COMMIT,
        source_dirty=SOURCE_DIRTY,
        built_at=BUILT_AT,
    )


def version_label() -> str:
    provenance = current_build_provenance()
    label = f"rvw {provenance.version} (build {provenance.build_id})"
    if provenance.source_commit is not None:
        if provenance.source_dirty is True:
            dirty = "+dirty"
        elif provenance.source_dirty is None:
            dirty = "+dirty-unknown"
        else:
            dirty = ""
        label += f" commit {provenance.source_commit}{dirty}"
    if provenance.built_at is not None:
        label += f" built {provenance.built_at}"
    return label


def stale_install_warning() -> str | None:
    """Warn only when embedded clean provenance and Git ancestry prove staleness."""

    provenance = current_build_provenance()
    if provenance.source_commit is None or provenance.source_dirty is not False:
        return None
    try:
        direct_url_text = distribution("rvw").read_text("direct_url.json")
    except (PackageNotFoundError, OSError):
        return None
    if direct_url_text is None:
        return None
    try:
        direct_url = json.loads(direct_url_text)
        parsed = urlparse(direct_url["url"])
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return None
    if parsed.scheme != "file" or parsed.netloc not in {"", "localhost"}:
        return None
    source = Path(unquote(parsed.path))
    if not source.is_dir():
        return None
    try:
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=source,
            check=True,
            capture_output=True,
            text=True,
            timeout=2,
        ).stdout.strip()
        if not head or head == provenance.source_commit:
            return None
        ancestry = subprocess.run(
            ["git", "merge-base", "--is-ancestor", provenance.source_commit, head],
            cwd=source,
            check=False,
            capture_output=True,
            timeout=2,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if ancestry.returncode != 0:
        return None
    return (
        f"warning: installed rvw build commit {provenance.source_commit} is behind "
        f"source checkout {source} at {head}; reinstall with: "
        f"uv tool install --reinstall --from {shlex.quote(str(source))} rvw"
    )


__all__ = [
    "BuildProvenance",
    "current_build_provenance",
    "stale_install_warning",
    "version_label",
]
