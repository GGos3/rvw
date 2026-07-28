"""Regression contracts for automated and emergency release entry points."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_release_workflow_is_reusable_and_keeps_tag_trigger() -> None:
    workflow = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")

    assert "workflow_call:" in workflow
    assert 'tags: ["v*"]' in workflow
    assert "RELEASE_TAG: ${{ inputs.tag || github.ref_name }}" in workflow
    assert "ref: ${{ env.RELEASE_TAG }}" in workflow
    assert 'TAG_VERSION="${RELEASE_TAG#v}"' in workflow
    assert 'tomllib.load(open("pyproject.toml", "rb"))["project"]["version"]' in workflow
    assert "from rvw._version import __version__" in workflow
    assert "id-token: write" in workflow


def test_release_please_calls_release_chain_without_tag_event() -> None:
    workflow = (ROOT / ".github/workflows/release-please.yml").read_text(encoding="utf-8")

    assert "secrets.RELEASE_PLEASE_TOKEN || github.token" in workflow
    assert "steps.release.outputs.release_created" in workflow
    assert "steps.release.outputs.tag_name" in workflow
    assert "needs.release-please.outputs.release_created == 'true'" in workflow
    assert "uses: ./.github/workflows/release.yml" in workflow
    assert "id-token: write" in workflow


def test_release_assets_handle_preexisting_release() -> None:
    workflow = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")

    assert 'gh release view "$RELEASE_TAG"' in workflow
    assert 'gh release upload "$RELEASE_TAG" dist/* --clobber' in workflow
    assert 'gh release create "$RELEASE_TAG" dist/*' in workflow
