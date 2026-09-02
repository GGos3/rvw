"""Materialize container-local Codex configuration and execute rvw."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

DEFAULT_TEMPLATE_PATH = Path("/etc/rvw/codex-config.toml")
_RUNTIME_BASE_URL = "CODEX_BASE_URL"
_BUILD_BASE_URL = "RVW_CODEX_DEFAULT_BASE_URL"


def _toml_string(value: str) -> str:
    """Return a TOML-compatible quoted string without shell interpolation."""

    return json.dumps(value, ensure_ascii=False)


def materialize_codex_config(
    *, template_path: Path, home: Path, environ: Mapping[str, str]
) -> Path:
    """Write a secret-free per-user Codex config from the baked template."""

    config_dir = home / ".codex"
    config_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    config_dir.chmod(0o700)
    config_path = config_dir / "config.toml"

    contents = template_path.read_text(encoding="utf-8").rstrip() + "\n"
    base_url = environ.get(_RUNTIME_BASE_URL) or environ.get(_BUILD_BASE_URL)
    if base_url:
        contents += f"base_url = {_toml_string(base_url)}\n"

    descriptor, temporary_name = tempfile.mkstemp(prefix=".config.toml.", dir=config_dir)
    temporary_path = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as config_file:
            config_file.write(contents)
            config_file.flush()
            os.fsync(config_file.fileno())
        temporary_path.replace(config_path)
        config_path.chmod(0o600)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise
    return config_path


def run_entrypoint(
    argv: Sequence[str],
    *,
    template_path: Path = DEFAULT_TEMPLATE_PATH,
    environ: Mapping[str, str] = os.environ,
    execvp: Callable[[str, list[str]], object] | None = None,
) -> None:
    """Prepare Codex and replace this process with the rvw CLI."""

    home_value = environ.get("HOME")
    home = Path(home_value) if home_value else Path.home()
    materialize_codex_config(template_path=template_path, home=home, environ=environ)
    rvw_argv = ["rvw", *argv]
    executor = os.execvp if execvp is None else execvp
    executor("rvw", rvw_argv)


def main() -> None:
    """Container entry point."""

    run_entrypoint(sys.argv[1:])


if __name__ == "__main__":
    main()
