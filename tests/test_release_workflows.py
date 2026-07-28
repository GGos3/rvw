"""Regression contracts for automated and emergency release entry points.

History (2026-07-28, v0.3.0):

The first shape of this rail routed release-please -> workflow_call ->
release.yml so it could work without any PAT (GITHUB_TOKEN-created tags do
not trigger workflows). That failed in production: PyPI Trusted Publishing
rejects OIDC tokens whose claims identify a reusable workflow
("Reusable workflows are not currently supported"), so the publish job got
a 400 Invalid attestations. The rail now follows the codex-lb pattern:
release-please runs with a required RELEASE_PLEASE_TOKEN PAT, the tags it
pushes trigger release.yml directly via the tag event, and release.yml is
NOT reusable. These tests pin that shape.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_release_workflow_is_tag_triggered_and_not_reusable() -> None:
    workflow = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")

    # PyPI Trusted Publishing rejects reusable-workflow OIDC claims — the
    # publish path must be a plain tag-push workflow.
    assert "workflow_call" not in workflow
    assert 'tags: ["v*"]' in workflow
    assert "RELEASE_TAG: ${{ github.ref_name }}" in workflow
    assert "ref: ${{ env.RELEASE_TAG }}" in workflow
    assert 'TAG_VERSION="${RELEASE_TAG#v}"' in workflow
    assert 'tomllib.load(open("pyproject.toml", "rb"))["project"]["version"]' in workflow
    assert "from rvw._version import __version__" in workflow
    assert "id-token: write" in workflow


def test_release_please_uses_required_pat_and_no_call_chain() -> None:
    workflow = (ROOT / ".github/workflows/release-please.yml").read_text(encoding="utf-8")

    # A PAT is required: github.token fallback would create tags that never
    # trigger release.yml (silent-dead releases), and a workflow_call chain
    # cannot publish to PyPI (see module docstring).
    assert "secrets.RELEASE_PLEASE_TOKEN }}" in workflow
    assert "github.token" not in workflow
    assert "workflow_call" not in workflow
    assert "uses: ./.github/workflows/release.yml" not in workflow


def test_release_assets_handle_preexisting_release() -> None:
    workflow = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")

    # release-please pre-creates the GitHub release; the tag-triggered run
    # must upload assets into it instead of failing on create.
    assert 'gh release view "$RELEASE_TAG"' in workflow
    assert 'gh release upload "$RELEASE_TAG" dist/* --clobber' in workflow
    assert 'gh release create "$RELEASE_TAG" dist/*' in workflow
