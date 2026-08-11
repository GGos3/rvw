from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import rvw.build_backend as build_backend
import rvw.provenance as provenance_module
from rvw.provenance import BuildProvenance, current_build_provenance, stale_install_warning


def test_current_build_has_deterministic_identity_without_fabricated_source_facts() -> None:
    first = current_build_provenance()
    second = current_build_provenance()

    assert first == second
    assert first.build_id.startswith("sha256:")
    assert len(first.build_id.removeprefix("sha256:")) == 64
    if first.source_commit is None:
        assert first.source_dirty is None
        assert first.built_at is None


def test_build_backend_embeds_commit_dirty_state_timestamp_and_build_id(
    monkeypatch,
) -> None:
    def fake_git(args: list[str]) -> str | None:
        if args == ["rev-parse", "HEAD"]:
            return "a" * 40
        raise AssertionError(args)

    monkeypatch.setattr(build_backend, "_git", fake_git)
    monkeypatch.setattr(build_backend, "_git_status_dirty", lambda: True)

    generated = build_backend._generated_provenance()

    assert generated is not None
    assert f"SOURCE_COMMIT: str | None = {'a' * 40!r}" in generated
    assert "SOURCE_DIRTY: bool | None = True" in generated
    assert "BUILT_AT: str | None = '" in generated
    assert "BUILD_ID: str | None = 'sha256:" in generated


def test_stale_warning_requires_provable_clean_commit(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        provenance_module,
        "current_build_provenance",
        lambda: BuildProvenance(
            version="0.4.1",
            build_id="sha256:" + "0" * 64,
            source_commit=None,
            source_dirty=None,
            built_at=None,
        ),
    )

    def forbidden_distribution(name: str):
        raise AssertionError(f"unverifiable build consulted installation source: {name}")

    monkeypatch.setattr(provenance_module, "distribution", forbidden_distribution)

    assert stale_install_warning() is None


def test_stale_warning_names_proven_descendant_and_concrete_reinstall(
    monkeypatch, tmp_path: Path
) -> None:
    source = tmp_path / "source checkout"
    source.mkdir()
    installed = "a" * 40
    head = "b" * 40
    monkeypatch.setattr(
        provenance_module,
        "current_build_provenance",
        lambda: BuildProvenance(
            version="0.4.1",
            build_id="sha256:" + "1" * 64,
            source_commit=installed,
            source_dirty=False,
            built_at="2026-08-11T00:00:00Z",
        ),
    )

    class Distribution:
        def read_text(self, name: str) -> str:
            assert name == "direct_url.json"
            return json.dumps({"url": source.as_uri()})

    monkeypatch.setattr(provenance_module, "distribution", lambda name: Distribution())
    calls: list[list[str]] = []

    def fake_run(command: list[str], **kwargs: object):
        del kwargs
        calls.append(command)
        if command[1:3] == ["rev-parse", "HEAD"]:
            return SimpleNamespace(stdout=f"{head}\n", returncode=0)
        assert command[1:3] == ["merge-base", "--is-ancestor"]
        return SimpleNamespace(stdout="", returncode=0)

    monkeypatch.setattr(provenance_module.subprocess, "run", fake_run)

    warning = stale_install_warning()

    assert warning is not None
    assert installed in warning
    assert head in warning
    assert f"uv tool install --reinstall --from '{source}' rvw" in warning
    assert len(calls) == 2


def test_embedded_provenance_context_restores_source_fallback(monkeypatch) -> None:
    path = Path(build_backend._PROVENANCE_MODULE)
    before = path.read_bytes()
    monkeypatch.setattr(
        build_backend,
        "_generated_provenance",
        lambda: "BUILD_ID = 'temporary-build'\n",
    )

    with build_backend._embedded_provenance():
        assert path.read_text(encoding="utf-8") == "BUILD_ID = 'temporary-build'\n"

    assert path.read_bytes() == before
