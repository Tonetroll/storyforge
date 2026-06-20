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

# The sequential spine: each feeds the next.
SEQUENCE = ["idea", "theme", "story", "stakebake"]
# The four script formats, each generated off the accepted stakebake (owner is
# evaluating which format fits -- keep all four). These are terminal outputs.
SCRIPT_FORMATS = ["script", "script_long", "script_screenplay", "script_podcast"]
# Built off the PROMOTED long-form script (it holds the whole story), AFTER the
# scripts -- NOT off the stakebake. A short doesn't even need a thumbnail.
OFF_SCRIPT = ["packaging", "description"]
# The long-form script packaging/description depend on; only a ready artifact is promotable.
OFF_SCRIPT_SOURCE = "script_long"


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
    """Drive one brief through the whole pipeline for ONE channel.

    Flow:
      idea -> theme -> story -> stakebake   (the spine: promote each on target, stop
                                             at the first weak link)
      -> script, script_long, script_screenplay, script_podcast
                                            (all four script formats, each off the
                                             accepted stakebake -- terminal outputs)
      -> [promote script_long]              (only if it reached ready_for_review)
      -> packaging, description             (both built off the PROMOTED long-form
                                             script, which holds the whole story)

    The four scripts are INDEPENDENT siblings: attempt all even if one fails. Then,
    because packaging/description build off the long-form script, the chain promotes
    script_long (a ready artifact is required to promote) and runs them off it.

    EDGE CASE: if script_long did NOT reach ready_for_review it cannot be promoted,
    so packaging/description cannot be built -- they are SKIPPED (not run), recorded
    in incomplete_deliverables with a skipped_reason, and the chain does not raise
    (it never lets the orchestrator hit its "No accepted 'script_long'" error).

    Returns where it stopped (if the spine stalled) and the terminal deliverables
    left for review, plus incomplete_deliverables (anything not ready_for_review)."""
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

    made = []
    incomplete = []

    # --- the four script formats, each off the accepted stakebake (terminal) -------
    # INDEPENDENT siblings: attempt ALL even if one fails; honestly report any that
    # did not reach ready_for_review. Track script_long: packaging/description need it.
    script_long_res = None
    for name in SCRIPT_FORMATS:
        stage = stages.get_stage(name)
        scripted = _scripted_for(stage) if dry_run else None
        res = orchestrator.run(stage_name=name, brief=None, channel=channel, scripted=scripted)
        step = {"stage": name, "outcome": res.get("outcome"),
                "score": res.get("final_score"), "artifact": res.get("artifact")}
        trail.append(step)
        made.append(step)
        if res.get("outcome") != "ready_for_review":
            incomplete.append(name)
        if name == OFF_SCRIPT_SOURCE:
            script_long_res = res

    # --- packaging + description, built off the PROMOTED long-form script ----------
    # Only a ready artifact is promotable. If script_long did not reach
    # ready_for_review, it cannot be promoted -> packaging/description cannot be built.
    # Detect that BEFORE calling run for them (so the orchestrator never raises its
    # "No accepted 'script_long'" error), skip them, and report them honestly.
    skipped_reason = None
    long_form_ready = (script_long_res is not None
                       and script_long_res.get("outcome") == "ready_for_review")
    if long_form_ready:
        _promote(script_long_res["artifact"], paths)
        for name in OFF_SCRIPT:
            stage = stages.get_stage(name)
            scripted = _scripted_for(stage) if dry_run else None
            res = orchestrator.run(stage_name=name, brief=None, channel=channel, scripted=scripted)
            step = {"stage": name, "outcome": res.get("outcome"),
                    "score": res.get("final_score"), "artifact": res.get("artifact")}
            trail.append(step)
            made.append(step)
            if res.get("outcome") != "ready_for_review":
                incomplete.append(name)
    else:
        skipped_reason = ("long-form script did not reach ready_for_review -- "
                          "packaging and description cannot be built off it.")
        for name in OFF_SCRIPT:
            trail.append({"stage": name, "outcome": "skipped",
                          "score": None, "artifact": None, "skipped_reason": skipped_reason})
            incomplete.append(name)

    result = {"brief": brief, "channel": channel, "stopped_at": None,
              "trail": trail, "deliverables": made,
              "incomplete_deliverables": incomplete}
    if skipped_reason:
        result["skipped_reason"] = skipped_reason
    return result


def _brief_from_line(line: str) -> str:
    """A seed line is a plain-text idea (the norm). Legacy JSON ({"brief": "..."})
    is still accepted so older seed files keep working.

    A line that starts with "{" is treated as JSON: a null/missing/empty/whitespace
    "brief" yields "" (the caller skips it -- never the literal string "None"), and
    a line that fails to parse as JSON raises ValueError so the caller can warn and
    skip it rather than feeding broken JSON to the generator as raw text."""
    if line.startswith("{"):
        obj = json.loads(line)  # malformed JSON raises ValueError -> caller warns + skips
        value = obj.get("brief")
        return str(value).strip() if value is not None else ""
    return line


def run_channel(channel: str, dry_run: bool = False) -> list:
    """Run every seed in THIS channel's queue (channels/<channel>/seeds/seeds.txt)
    through the full chain, one complete chain at a time. Each line is a plain-text
    idea (legacy JSON {'brief': ...} still works); the channel is the workspace."""
    paths = config.paths_for(channel)
    if not paths.seeds.exists():
        raise FileNotFoundError(
            f"No seed file for channel '{paths.root.name}' at {paths.seeds}. "
            f"Run `python run.py new-channel {channel}` first, then add ideas to its seeds/seeds.txt.")
    results = []
    for line in paths.seeds.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("//"):
            continue
        try:
            brief = _brief_from_line(line)
        except ValueError as e:
            snippet = line if len(line) <= 120 else line[:117] + "..."
            print(f"[run_channel] SKIPPING malformed JSON seed line: {snippet!r} ({e})")
            continue
        if brief:
            results.append(run_chain(brief, channel=channel, dry_run=dry_run))
    return results
