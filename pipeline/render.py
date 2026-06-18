"""Render an artifact record as human-readable plain text.

Every artifact is saved twice: <name>.json (for the pipeline) and <name>.txt
(for you, at the review step). This builds the .txt.
"""

import config


def _breakdown_lines(breakdown) -> str:
    if not breakdown:
        return "    (not scored)"
    out = []
    for k in sorted(config.CRITERION_WEIGHTS):
        pts = breakdown.get(k, breakdown.get(str(k), 0))
        out.append(f"    {k}. {config.CRITERION_LABELS[k]}: {pts} / {config.CRITERION_WEIGHTS[k]}")
    return "\n".join(out)


def to_text(record: dict) -> str:
    idea = record.get("idea", {}) or {}
    bar = "=" * 70
    return "\n".join([
        bar,
        f"  {record.get('slug', '?')}   |   {record.get('story_id') or '(no id)'}   |   "
        f"v{record.get('version', 0):02d}   |   {str(record.get('status', '')).upper()}",
        bar,
        "",
        f"BRIEF:  {record.get('brief', '')}",
        "",
        "THE IDEA",
        "  One-liner (open loop):",
        f"    {idea.get('one_liner', '')}",
        "",
        "  Resolution (payoff):",
        f"    {idea.get('resolution', '')}",
        "",
        f"  Pull-in emotion (#1):    {idea.get('reaction_1', '')}",
        f"  Resolution emotion (#2): {idea.get('reaction_2', '')}",
        f"  Viewer action:           {idea.get('viewer_action', '')}",
        "",
        "GATE",
        f"  Verdict:  {record.get('verdict', '')}",
        f"  Score:    {record.get('score', '')} / 100",
        "",
        "  Breakdown:",
        _breakdown_lines(record.get("breakdown")),
        "",
        f"  Why:  {record.get('why', '')}",
        f"  Failed checks:  {record.get('failed_checks', '')}",
        "",
        "LINEAGE",
        f"  parent version:  {record.get('parent_version')}",
        f"  generator: {record.get('generator_model', '')}   evaluator: {record.get('evaluator_model', '')}",
        f"  created:   {record.get('ts', '')}",
        bar,
        "",
    ])
