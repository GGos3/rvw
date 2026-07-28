from pathlib import Path

import pytest
from pydantic import ValidationError

from rvw.registry import TIER_ORDER, LayerPredicate, Registry, load_registry

FIXTURE = Path(__file__).parent / "fixtures" / "layers_minimal.yaml"


def test_base_layer_always_activates() -> None:
    reg = load_registry(FIXTURE)
    active = reg.activate(repo="unrelated/repo", changed_paths=["README.md"])
    assert "base" in [layer.id for layer in active]


def test_plain_repo_predicate_retains_exact_match_behavior() -> None:
    reg = load_registry(FIXTURE)
    matching_ids = [
        layer.id for layer in reg.activate(repo="clawroid/bori", changed_paths=["x.ts"])
    ]
    mismatching_ids = [
        layer.id for layer in reg.activate(repo="clawroid/bori-tools", changed_paths=["x.ts"])
    ]

    assert "project/bori" in matching_ids
    assert "project/bori" not in mismatching_ids


def test_apifuse_provider_repo_matches_project_glob_regression() -> None:
    # 2026-07-28 incident: this provider missed the project lane when repo was exact-only.
    reg = Registry.model_validate(
        {
            "layers": [
                {
                    "id": "project/apifuse",
                    "tier": "project",
                    "when": {"repo": "APIFuseHQ/apifuse-provider-*"},
                    "lanes": ["apifuse/sdk-reinvention"],
                }
            ]
        }
    )

    ids = [
        layer.id
        for layer in reg.activate(
            repo="APIFuseHQ/apifuse-provider-tabelog", changed_paths=["index.ts"]
        )
    ]

    assert ids == ["project/apifuse"]


@pytest.mark.parametrize("repo", ["APIFuseHQ/apifuse", "APIFuseHQ/apifuse-provider-tabelog"])
def test_repo_pattern_list_uses_or_semantics(repo: str) -> None:
    reg = Registry.model_validate(
        {
            "layers": [
                {
                    "id": "project/apifuse",
                    "tier": "project",
                    "when": {
                        "repo": [
                            "APIFuseHQ/apifuse",
                            "APIFuseHQ/apifuse-provider-*",
                        ]
                    },
                    "lanes": ["apifuse/sdk-reinvention"],
                }
            ]
        }
    )

    assert [layer.id for layer in reg.activate(repo, ["index.ts"])] == ["project/apifuse"]


def test_repo_patterns_that_do_not_match_do_not_activate() -> None:
    reg = Registry.model_validate(
        {
            "layers": [
                {
                    "id": "project/apifuse",
                    "tier": "project",
                    "when": {
                        "repo": [
                            "APIFuseHQ/apifuse",
                            "APIFuseHQ/apifuse-provider-*",
                        ]
                    },
                    "lanes": ["apifuse/sdk-reinvention"],
                }
            ]
        }
    )

    assert reg.activate("other/repo", ["index.ts"]) == []


def test_repo_glob_matching_is_case_sensitive() -> None:
    reg = Registry.model_validate(
        {
            "layers": [
                {
                    "id": "project/apifuse",
                    "tier": "project",
                    "when": {"repo": "APIFuseHQ/apifuse-provider-*"},
                    "lanes": ["apifuse/sdk-reinvention"],
                }
            ]
        }
    )

    assert reg.activate("apifusehq/apifuse-provider-tabelog", ["index.ts"]) == []


def test_repo_and_paths_predicates_use_and_semantics() -> None:
    reg = Registry.model_validate(
        {
            "layers": [
                {
                    "id": "scope/apifuse/provider",
                    "tier": "scope",
                    "when": {
                        "repo": "APIFuseHQ/apifuse-provider-*",
                        "paths": ["src/**"],
                    },
                    "lanes": ["apifuse/sdk-reinvention"],
                }
            ]
        }
    )

    assert [
        layer.id for layer in reg.activate("APIFuseHQ/apifuse-provider-tabelog", ["src/client.ts"])
    ] == ["scope/apifuse/provider"]
    assert reg.activate("APIFuseHQ/apifuse-provider-tabelog", ["README.md"]) == []
    assert reg.activate("other/repo", ["src/client.ts"]) == []


def test_repo_predicate_schema_accepts_string_lists() -> None:
    predicate = LayerPredicate.model_validate(
        {"repo": ["APIFuseHQ/apifuse", "APIFuseHQ/apifuse-provider-*"]}
    )

    assert predicate.repo == [
        "APIFuseHQ/apifuse",
        "APIFuseHQ/apifuse-provider-*",
    ]


@pytest.mark.parametrize("repo", [1, ["owner/repo", 1]])
def test_repo_predicate_schema_rejects_non_string_shapes(repo: object) -> None:
    with pytest.raises(ValidationError):
        LayerPredicate.model_validate({"repo": repo})


def test_scope_layer_requires_path_match() -> None:
    reg = load_registry(FIXTURE)
    off = reg.activate(repo="clawroid/bori", changed_paths=["apps/web/page.tsx"])
    on = reg.activate(repo="clawroid/bori", changed_paths=["apps/agent-backend/src/agent.ts"])
    assert "scope/bori/agent" not in [layer.id for layer in off]
    assert "scope/bori/agent" in [layer.id for layer in on]


def test_dynamic_layer_always_activates() -> None:
    reg = load_registry(FIXTURE)
    ids = [layer.id for layer in reg.activate(repo="any/repo", changed_paths=["a.py"])]
    assert "dynamic" in ids


def test_activation_is_tier_ordered() -> None:
    reg = load_registry(FIXTURE)
    tiers = [
        layer.tier
        for layer in reg.activate(
            repo="clawroid/bori", changed_paths=["apps/agent-backend/src/agent.ts"]
        )
    ]
    assert tiers == sorted(tiers, key=TIER_ORDER.index)
