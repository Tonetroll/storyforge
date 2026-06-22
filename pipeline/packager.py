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


SCRIPT_STAGES = ["script", "script_long", "script_screenplay", "script_podcast"]
_SCRIPT_TITLES = {
    "script": "SHORT-FORM SCRIPT",
    "script_long": "LONG-FORM NARRATION SCRIPT",
    "script_screenplay": "SCREENPLAY",
    "script_podcast": "PODCAST",
}


_SCRIPT_FILES = {
    "script": "short-script.txt",
    "script_long": "long-script.txt",
    "script_screenplay": "screenplay.txt",
    "script_podcast": "podcast.txt",
}


def build_package(channel: str, script_stage: str = None):
    """Assemble the latest video's deliverables into a per-video FOLDER, with each
    format a SEPARATE, clearly-named file -- because each one heads to a different
    production line, so they stay separate (not one combined doc). Returns the folder
    path. (script_stage is accepted for back-compat and ignored -- every format is written.)"""
    paths = config.paths_for(channel)
    pkg = _latest(paths, "packaging")
    desc = _latest(paths, "description")
    scripts = {s: _latest(paths, s) for s in SCRIPT_STAGES}
    present = [r for r in [pkg, desc, *scripts.values()] if r]
    if not present:
        print(f"No deliverables found for channel '{paths.root.name}'. Run the chain first.")
        return None

    story_id = present[0].get("story_id") or "video"
    title = (pkg or {}).get("content", {}).get("title", "")
    slug = naming.slugify(title) or "video"
    folder = paths.candidates.parent / "packages" / f"{story_id}_{slug}"   # one folder per video
    folder.mkdir(parents=True, exist_ok=True)

    def _write(filename, header, body):
        (folder / filename).write_text(f"{header}\n{'=' * len(header)}\n\n{body}\n", encoding="utf-8")

    # Title + thumbnail -> its own file.
    if pkg:
        c = pkg.get("content", {})
        _write("title-and-thumbnail.txt", f"TITLE + THUMBNAIL  ({story_id})",
               f"TITLE:\n  {c.get('title', '')}\n\n"
               f"THUMBNAIL CONCEPT:\n  {c.get('thumbnail_concept', '')}\n\n"
               f"IMAGE PROMPT:\n  {c.get('thumbnail_prompt', '')}")

    # Each script format -> its own clearly-tagged file (different production lines).
    for s in SCRIPT_STAGES:
        r = scripts.get(s)
        if r:
            _write(_SCRIPT_FILES[s], f"{_SCRIPT_TITLES[s]}  ({story_id})",
                   render._prose_lines(r.get("content", {}), stages.get_stage(s)))

    if desc:
        _write("description.txt", f"YOUTUBE DESCRIPTION  ({story_id})",
               render._prose_lines(desc.get("content", {}), stages.get_stage("description")))

    return folder
