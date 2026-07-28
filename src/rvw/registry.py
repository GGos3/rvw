"""Typed registry loading and layer activation."""

from __future__ import annotations

import fnmatch
import posixpath
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict

from rvw.schema import Tier

TIER_ORDER = (Tier.BASE, Tier.PROJECT, Tier.SCOPE, Tier.DYNAMIC)


def _glob_match(path: str, pattern: str) -> bool:
    """Match normalized POSIX paths, allowing ``**`` to cross directories.

    For example, ``apps/agent-backend/**`` matches any file beneath that
    directory, at any depth.
    """

    normalized_path = posixpath.normpath(path.replace("\\", "/"))
    normalized_pattern = posixpath.normpath(pattern.replace("\\", "/"))
    return fnmatch.fnmatchcase(normalized_path, normalized_pattern)


def _repo_match(repo: str, patterns: str | list[str]) -> bool:
    """Match a repository against one or more case-sensitive glob patterns."""

    if isinstance(patterns, str):
        patterns = [patterns]
    return any(fnmatch.fnmatchcase(repo, pattern) for pattern in patterns)


class LayerPredicate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    repo: str | list[str] | None = None
    paths: list[str] | None = None


class Layer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    tier: Tier
    lanes: list[str]
    when: LayerPredicate | None = None


class Registry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    layers: list[Layer]

    def activate(self, repo: str, changed_paths: list[str]) -> list[Layer]:
        """Return activated layers in fixed tier order."""

        active = [
            layer
            for layer in self.layers
            if layer.when is None
            or (
                (layer.when.repo is None or _repo_match(repo, layer.when.repo))
                and (
                    layer.when.paths is None
                    or any(
                        _glob_match(path, pattern)
                        for path in changed_paths
                        for pattern in layer.when.paths
                    )
                )
            )
        ]
        return sorted(active, key=lambda layer: TIER_ORDER.index(layer.tier))


def load_registry(path: Path) -> Registry:
    """Load and validate a YAML layer registry."""

    return Registry.model_validate(yaml.safe_load(path.read_text()))
