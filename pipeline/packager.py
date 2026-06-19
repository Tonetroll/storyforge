"""Assemble a video's publish-ready deliverables into ONE clean package doc.

The per-stage artifacts keep their full genealogy (brief + BUILT ON + gate) for
review. This is the opposite: the publish view -- title, thumbnail, description,
script, nothing else -- ready to paste into YouTube or hand to production.

v1 packages the LATEST deliverable of each kind in the channel (the most recent
video). Multi-video lineage matching is a later enhancement.
"""

import json

import config
from pipeline import naming, render, stages


def _latest(paths, stage_name: str):
    """Most recent artifact for a stage, across this channel's candidates + accepted."""
    best = None
    for d in (paths.accepted, paths.candidates):
        if not d.exists():
            continue
        for f in d.glob("*.json"):
            try:
                rec = json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                continue
            if rec.get("stage") == stage_name and (best is None or rec.get("number", 0) > best.get("number", 0)):
                best = rec
    return best


def build_package(channel: str, script_stage: str = "script"):
    paths = config.paths_for(channel)
    pkg = _latest(paths, "packaging")
    desc = _latest(paths, "description")
    scr = _latest(paths, script_stage)
    if not (pkg or desc or scr):
        print(f"No deliverables found for channel '{paths.root.name}'. Run the chain first.")
        return None

    title = (pkg or {}).get("content", {}).get("title", "(no title yet)")
    bar = "=" * 60
    lines = [bar, f"  VIDEO PACKAGE -- {paths.root.name}", bar, "", "TITLE", f"  {title}", ""]
    if pkg:
        c = pkg.get("content", {})
        lines += ["THUMBNAIL",
                  f"  Concept: {c.get('thumbnail_concept', '')}", "",
                  f"  Image prompt: {c.get('thumbnail_prompt', '')}", ""]
    if desc:
        lines += ["DESCRIPTION",
                  render._prose_lines(desc.get("content", {}), stages.get_stage("description")), ""]
    if scr:
        st = stages.get_stage(scr.get("stage", "script"))
        lines += [f"SCRIPT ({scr.get('stage')})",
                  render._prose_lines(scr.get("content", {}), st), ""]
    lines.append(bar)
    text = "\n".join(lines)

    out_dir = paths.candidates.parent / "packages"   # channels/<name>/outputs/packages/
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = naming.slugify(title) or "video"
    out = out_dir / f"{slug}.md"
    out.write_text(text, encoding="utf-8")
    return out
