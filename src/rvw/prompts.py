"""Pure prompt construction for review lane runs."""

from __future__ import annotations

from rvw.lane import Lane
from rvw.schema import Tier

_UNVERIFIED_BRIEF_NOTE = (
    "NOTE: brief derived from PR title/body — UNVERIFIED claim of intent (treat mismatches "
    "as findings, not errors)."
)


def build_lane_prompt(
    lane: Lane,
    *,
    diff: str,
    brief: str | None,
    brief_source: str | None,
    covered_rules: dict[str, list[str]],
) -> str:
    """Build one lane prompt without performing I/O."""

    sections = [f"# Lane: {lane.id}\n\n{lane.prompt_body}"]

    if lane.covered_by_others == "inject":
        other_rules = [
            (lane_id, rules) for lane_id, rules in covered_rules.items() if lane_id != lane.id
        ]
        covered_lines = ["## Already covered by other lanes — do NOT re-report these classes"]
        if other_rules:
            for lane_id, rules in other_rules:
                covered_lines.append(f"- {lane_id}: {', '.join(f'`{rule}`' for rule in rules)}")
        else:
            covered_lines.append("- None")
        sections.append("\n".join(covered_lines))

    if lane.tier is Tier.DYNAMIC:
        brief_lines = ["## Review brief"]
        if brief:
            brief_lines.append(brief)
            if brief_source == "pr_body":
                brief_lines.append(_UNVERIFIED_BRIEF_NOTE)
        else:
            brief_lines.append("BRIEF UNAVAILABLE — mark findings inconclusive")
        sections.append("\n\n".join(brief_lines))

    sections.append(f"## Unified diff under review\n\n```diff\n{diff}```")
    declared_rules = ", ".join(f"`{rule}`" for rule in lane.rules)
    sections.append(
        "## Output instructions\n\n"
        "Report every finding as structured output. Each `rule_id` must be one of this "
        f"lane's declared rules: {declared_rules}. The output schema enforces the allowed "
        "rule identifiers; use `file` and NEW-file `line` numbers from the diff. "
        "Do not modify files."
    )
    return "\n\n".join(sections)


__all__: list[str] = ["build_lane_prompt"]
