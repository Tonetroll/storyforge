"""Run-through mode (review at the end).

Feed a brief, run the whole pipeline, and AUTO-PROMOTE each stage that hits its
target so the next stage can pull it - no human-review CSV between stages. The
chain STOPS at the first stage that parks below target (the weak link), so a test
run shows you exactly where the pipeline stalls. The terminal deliverables (script,
packaging) are left at ready_for_review for your single end-of-run review.

This is the second of two modes. The first (gate at every stage) still works
exactly as before: run one stage, fill review/human_review.csv, route, repeat.
Nothing here changes the engine - auto-promote is a copy into accepted/ that the
human accept would otherwise do, MINUS the trainset write (auto-promotes are not
human-accepted examples, so they must not retrain the generator).
"""

import json
from pathlib import Path

import config
from pipeline import orchestrator, naming, render, stages

# The sequential spine: each feeds the next. Then the terminal deliverables off stakebake.
SEQUENCE = ["idea", "theme", "story", "stakebake"]
DELIVERABLES = ["script", "packaging", "description"]


def _promote(artifact_path: str, paths) -> Path:
    """Copy a ready_for_review artifact into THIS channel's accepted/ as 'promoted'
    so downstream can pull it. NOT added to the channel's trainset.jsonl - that is
    reserved for the examples YOU accept by hand."""
    src = Path(artifact_path)
    record = json.loads(src.read_text(encoding="utf-8"))
    parts = naming.parse_name(src.name)
    new_base = naming.format_name(parts["slug"], parts["number"], parts["version"], "promoted")
    record["status"] = "promoted"
    record["auto_promoted"] = True
    paths.accepted.mkdir(parents=True, exist_ok=True)
    dest = paths.accepted / f"{new_base}.json"
    dest.write_text(json.dumps(record, indent=2), encoding="utf-8")
    stage = stages.get_stage(record.get("stage", "idea"))
    (paths.accepted / f"{new_base}.txt").write_text(render.to_text(record, stage), encoding="utf-8")
    src.unlink(missing_ok=True)
    src.with_suffix(".txt").unlink(missing_ok=True)
    return dest


def _scripted_for(stage) -> dict:
    """Generic placeholder content + full scores so a stage passes in dry mode.
    Introspects each signature's REAL output fields (so per-stage extras like
    stakebake's `stakes_added` or a hybrid gate's `jargon` are filled), exercising
    the WIRING end to end (handoff, auto-promote, naming) without API keys. The
    content is '[dry ...]', not real - it only proves the plumbing."""
    gen = {"reasoning": "dry"}
    for name in stage.gen_sig.output_fields:
        gen[name] = f"dry {stage.name}" if name == stage.topic_field else f"[dry {stage.name}:{name}]"

    ev = {"reasoning": "dry"}
    for name in stage.gate_sig.output_fields:
        if name == "verdict":
            ev[name] = "PASS"
        elif name == "failed_checks":
            ev[name] = "none"
        elif name == "why":
            ev[name] = "dry pass"
        elif name == "jargon":
            ev[name] = "false"           # not in (true/yes/1) -> no penalty
        elif name.startswith("score_"):
            ev[name] = str(stage.weights.get(int(name.split("_")[1]), 0))
        else:
            ev[name] = "dry"
    return {"gen_answers": [gen] * config.MAX_GEN_ATTEMPTS,
            "eval_answers": [ev] * (config.MAX_ITER + 3)}


def run_chain(brief: str, channel: str = None, dry_run: bool = False, deliverables=None) -> dict:
    """Drive one brief through the whole pipeline for ONE channel. Returns where it
    stopped (if it did) and the terminal deliverables left for review."""
    deliverables = deliverables or DELIVERABLES
    paths = config.paths_for(channel)
    trail = []

    # --- the sequential spine: promote each on target, stop at the first weak link ---
    for i, name in enumerate(SEQUENCE):
        stage = stages.get_stage(name)
        scripted = _scripted_for(stage) if dry_run else None
        res = orchestrator.run(stage_name=name, brief=(brief if i == 0 else None),
                               channel=channel, scripted=scripted)
        step = {"stage": name, "outcome": res.get("outcome"),
                "score": res.get("final_score"), "artifact": res.get("artifact")}
        trail.append(step)
        if res.get("outcome") != "ready_for_review":
            return {"brief": brief, "channel": channel, "stopped_at": name,
                    "reason": res.get("outcome"), "trail": trail, "deliverables": []}
        _promote(res["artifact"], paths)

    # --- terminal deliverables off the accepted stakebake (left at ready_for_review) ---
    made = []
    for name in deliverables:
        stage = stages.get_stage(name)
        scripted = _scripted_for(stage) if dry_run else None
        res = orchestrator.run(stage_name=name, brief=None, channel=channel, scripted=scripted)
        step = {"stage": name, "outcome": res.get("outcome"),
                "score": res.get("final_score"), "artifact": res.get("artifact")}
        trail.append(step)
        made.append(step)

    return {"brief": brief, "channel": channel, "stopped_at": None,
            "trail": trail, "deliverables": made}


def _brief_from_line(line: str) -> str:
    """A seed line is a plain-text idea (the norm). Legacy JSON ({"brief": "..."})
    is still accepted so older seed files keep working."""
    if line.startswith("{"):
        try:
            return str(json.loads(line).get("brief", "")).strip()
        except ValueError:
            pass
    return line


def run_channel(channel: str, dry_run: bool = False) -> list:
    """Run every seed in THIS channel's queue (channels/<channel>/seeds/briefs.jsonl)
    through the full chain, one complete chain at a time. Each line is a plain-text
    idea (legacy JSON {'brief': ...} still works); the channel is the workspace."""
    paths = config.paths_for(channel)
    if not paths.seeds.exists():
        raise FileNotFoundError(
            f"No seed file for channel '{paths.root.name}' at {paths.seeds}. "
            f"Run `python run.py new-channel {channel}` first, then add ideas to its seeds/briefs.jsonl.")
    results = []
    for line in paths.seeds.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("//"):
            continue
        brief = _brief_from_line(line)
        if brief:
            results.append(run_chain(brief, channel=channel, dry_run=dry_run))
    return results
