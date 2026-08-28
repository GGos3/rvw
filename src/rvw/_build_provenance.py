"""Fallback provenance for direct source imports; the build backend replaces these values."""

BUILD_ID: str | None = None
SOURCE_COMMIT: str | None = None
SOURCE_DIRTY: bool | None = None
BUILT_AT: str | None = None
