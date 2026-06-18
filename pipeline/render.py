"""Render an artifact record as human-readable plain text, generic over a stage.

Every artifact is saved twice: <name>.json (for the pipeline) and <name>.txt
(for you, at the review step). This builds the .txt.
"""


def _breakdown_lines(breakdown, stage) -> str:
    if not breakdown:
        return "    (not scored)"
    out = []
    for k in sorted(stage.weights):
        pts = breakdown.get(k, breakdown.get(str(k), 0))
        out.append(f"    {k}. {stage.labels[k]}: {pts} / {stage.weights[k]}")
    return "\n".join(out)


def _content_lines(content, stage) -> str:
    out = []
    for f in stage.content_fields:
        label = f.replace("_", " ").capitalize()
        out += [f"  {label}:", f"    {content.get(f, '')}", ""]
    return "\n".join(out).rstrip()


def _assembly_lines(assembly) -> str:
    """The accumulated package: every prior accepted stage's content."""
    if not assembly:
        return ""
    out = ["", "BUILT ON (the package so far):"]
    for stage_name, content in assembly.items():
        out.append(f"  [{stage_name}]")
        for k, v in (content or {}).items():
            out.append(f"    {k.replace('_', ' ').capitalize()}: {v}")
    return "\n".join(out)


def to_text(record: dict, stage) -> str:
    bar = "=" * 70
    return "\n".join([
        bar,
        f"  {record.get('slug', '?')}   |   {record.get('story_id') or '(no id)'}   |   "
        f"v{record.get('version', 0):02d}   |   {str(record.get('status', '')).upper()}",
        bar,
        "",
        f"BRIEF:  {record.get('brief', '')}",
        "",
        f"THE {stage.content_label}",
        _content_lines(record.get("content", {}) or {}, stage),
        _assembly_lines(record.get("assembly")),
        "",
        "GATE",
        f"  Verdict:  {record.get('verdict', '')}",
        f"  Score:    {record.get('score', '')} / 100",
        "",
        "  Breakdown:",
        _breakdown_lines(record.get("breakdown"), stage),
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
