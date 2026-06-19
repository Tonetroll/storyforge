"""The orchestrator: a generic gate + score hybrid, run over any Stage.

1. Enforce the #1 rule (evaluator on a separate LM) or refuse to run.
2. GATE: generate, run the gate. REJECT -> write to rejected/ and bring a new
   one (up to MAX_GEN_ATTEMPTS). PASS -> assign a story id ST-#### and proceed.
3. SCORE + ITERATE the passing artifact (iterator -> reevaluator) up to MAX_ITER.
   Reaches TARGET_SCORE -> final reevaluation -> ready_for_review. Else -> parked.
"""

import json
import re
from datetime import datetime, timezone

import dspy

import config
from pipeline import logging_setup, naming, render, stages
from pipeline.generator import Generator
from pipeline.evaluator import Evaluator
from pipeline.iterator import Iterator
from pipeline.reevaluator import Reevaluator


# ---------------------------------------------------------------------------
# LM wiring + the separation guarantee
# ---------------------------------------------------------------------------
def assert_separation(gen_lm, eval_lm) -> None:
    """THE #1 RULE. Refuse to run if generator and evaluator share an LM."""
    if gen_lm is eval_lm:
        raise RuntimeError("SEPARATION VIOLATED: generator and evaluator share the same LM instance.")
    gen_model = getattr(gen_lm, "model", None)
    eval_model = getattr(eval_lm, "model", None)
    if gen_model is not None and gen_model == eval_model:
        raise RuntimeError(
            f"SEPARATION VIOLATED: evaluator must be a different model than the generator "
            f"(both are '{gen_model}'). Fix EVALUATOR_LM in config.py."
        )


def _idea_dummy_lms():
    """Two independent stub LMs for an offline idea-stage smoke run (--dry-run)."""
    from dspy.utils.dummies import DummyLM

    topics = ["dogs tilt heads to hear", "elevator mirror practiced fine",
              "midnight train last ticket", "barista remembers every order",
              "lighthouse keeper final night", "old map hidden room",
              "silent phone rings once", "last bus driver secret"]
    gen_answers = [
        {"reasoning": "drafting", "topic": topics[i - 1], "one_liner": f"DRY-RUN open loop {i}",
         "resolution": f"DRY-RUN payoff {i}", "reaction_1": "WTF", "reaction_2": "Aah",
         "viewer_action": "Reflect", "improved_one_liner": f"DRY-RUN sharper open loop {i}",
         "improved_resolution": f"DRY-RUN stronger payoff {i}", "improved_reaction_1": "WTF",
         "improved_reaction_2": "Aah", "improved_viewer_action": "Reflect"}
        for i in range(1, 9)
    ]
    eval_specs = [
        ("REJECT", [25, 0, 0, 10, 10, 10], "2,3: resolution missing; emotions not distinct"),
        ("PASS", [20, 18, 14, 8, 6, 6], "none"),
        ("PASS", [22, 20, 16, 8, 7, 7], "none"),
        ("PASS", [23, 22, 17, 8, 8, 8], "none"),
        ("PASS", [24, 22, 18, 8, 8, 8], "none"),
        ("PASS", [25, 24, 19, 9, 9, 9], "none"),
    ]
    eval_answers = []
    for (v, scores, fc) in eval_specs:
        d = {"reasoning": "judging", "verdict": v, "failed_checks": fc, "why": "gate decision"}
        for i, s in enumerate(scores, start=1):
            d[f"score_{i}"] = str(s)
        eval_answers.append(d)
    lm_a, lm_b = DummyLM(gen_answers), DummyLM(eval_answers)
    lm_a.model, lm_b.model = "dummy/generator-A", "dummy/evaluator-B"
    return lm_a, lm_b


def build_modules(stage, dry_run: bool = False, scripted: dict = None):
    generator = Generator(stage.gen_sig)
    iterator = Iterator(stage.iter_sig, stage.content_fields)
    evaluator = Evaluator(stage.gate_sig, stage.weights, stage.penalty_points, stage.verdict_floor)
    reevaluator = Reevaluator(stage.gate_sig, stage.weights, stage.penalty_points, stage.verdict_floor)
    if scripted is not None:
        from dspy.utils.dummies import DummyLM
        lm_a = DummyLM(scripted["gen_answers"])
        lm_b = DummyLM(scripted["eval_answers"])
        lm_a.model, lm_b.model = "manual/generator", "manual/evaluator"
    elif dry_run:
        lm_a, lm_b = _idea_dummy_lms()
    else:
        lm_a = dspy.LM(**config.GENERATOR_LM)
        lm_b = dspy.LM(**config.EVALUATOR_LM)
    generator.set_lm(lm_a)
    iterator.set_lm(lm_a)
    evaluator.set_lm(lm_b)
    reevaluator.set_lm(lm_b)
    assert_separation(generator.get_lm(), evaluator.get_lm())
    return generator, evaluator, iterator, reevaluator


# ---------------------------------------------------------------------------
# Standards + upstream handoff
# ---------------------------------------------------------------------------
def _read_standard(filename: str, fallback: str) -> str:
    path = config.STANDARDS_DIR / filename
    return path.read_text(encoding="utf-8") if path.exists() else fallback


def _extract_spine(text: str) -> str:
    """The tight positioning block between the SPINE markers (fed to EVERY stage).
    Old profiles without markers -> the whole doc is the spine (back-compatible)."""
    m = re.search(r"<!--\s*SPINE:START\s*-->(.*?)<!--\s*SPINE:END\s*-->", text, re.DOTALL | re.IGNORECASE)
    return m.group(1) if m else text


def _load_craft() -> str:
    """The shared, genre-agnostic craft doctrine, injected into every generator."""
    p = config.CRAFT_PRINCIPLES
    return p.read_text(encoding="utf-8").strip() if p.exists() else ""


def _load_channel(channel: str):
    """Returns (spine, full) for a channel profile. spine = the positioning block fed
    to every stage; full = the whole profile fed to the deep stages only. HTML
    comments (the meta note + markers) are stripped so they never reach a prompt."""
    if not channel:
        return "", ""
    path = config.CHANNELS_DIR / channel / "profile.md"
    if not path.exists():
        return "", ""
    raw = path.read_text(encoding="utf-8")
    strip = lambda t: re.sub(r"<!--.*?-->", "", t, flags=re.DOTALL).strip()
    return strip(_extract_spine(raw)), strip(raw)


def _assembly_text(assembly: dict) -> str:
    """Render the accumulated package as plain text (for a gate's delivery check)."""
    parts = []
    for stage_name, content in (assembly or {}).items():
        parts.append(f"[{stage_name}]")
        for k, v in (content or {}).items():
            parts.append(f"  {k}: {v}")
    return "\n".join(parts)


def _latest_accepted(stage_name: str, accepted_dir):
    """Most recent promoted/accepted artifact for the given stage, in THIS channel."""
    best = None
    if not accepted_dir.exists():
        return None
    for f in accepted_dir.glob("*.json"):
        try:
            rec = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        if rec.get("stage") == stage_name:
            if best is None or (rec.get("number", 0) > best.get("number", 0)):
                best = rec
    return best


def _resolve_upstream(stage, brief, paths):
    """Returns (brief, assembly). assembly = the structured content of EVERY prior
    accepted stage, so each artifact carries the growing package (no gathering later)."""
    if not stage.upstream:
        return brief, {}
    rec = _latest_accepted(stage.upstream, paths.accepted)
    if rec is None:
        raise RuntimeError(f"No accepted '{stage.upstream}' artifact to feed stage '{stage.name}'.")
    assembly = {**(rec.get("assembly") or {}), stage.upstream: rec.get("content", {})}
    return stage.build_brief(rec), assembly


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _content(pred, stage) -> dict:
    return {f: getattr(pred, f) for f in stage.content_fields}


def _save_artifact(*, stage, slug, number, version, status, brief, content, gate, story_id,
                   gen_model, eval_model, dest_dir, assembly=None, channel=None, parent_version=None):
    dest_dir.mkdir(parents=True, exist_ok=True)
    base = naming.format_name(slug, number, version, status)
    asset_id = f"{slug}_{number:04d}"
    record = {
        "asset_id": asset_id,
        "story_id": story_id,
        "stage": stage.name,
        "slug": slug,
        "number": number,
        "version": version,
        "status": status,
        "parent_version": parent_version,
        "brief": brief,
        "content": content,
        "assembly": assembly or {},
        "channel": channel,
        "verdict": getattr(gate, "verdict", None) if gate else None,
        "score": getattr(gate, "score", None) if gate else None,
        "breakdown": getattr(gate, "breakdown", None) if gate else None,
        "failed_checks": getattr(gate, "failed_checks", None) if gate else None,
        "why": getattr(gate, "why", None) if gate else None,
        "generator_model": gen_model,
        "evaluator_model": eval_model,
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    path = dest_dir / f"{base}.json"
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    (dest_dir / f"{base}.txt").write_text(render.to_text(record, stage), encoding="utf-8")
    return path, asset_id


# ---------------------------------------------------------------------------
# The hybrid loop (generic over a stage)
# ---------------------------------------------------------------------------
def run(stage_name: str = "idea", brief: str = None, dry_run: bool = False, scripted: dict = None,
        channel: str = None) -> dict:
    stage = stages.get_stage(stage_name)
    paths = config.paths_for(channel)          # this channel's self-contained workspace
    run_id = logging_setup.next_run_id(paths)
    log = logging_setup.get_run_logger(run_id, paths)
    mode = "MANUAL (your content + scores)" if scripted else ("DRY-RUN (stub LMs)" if dry_run else "LIVE")
    log.info("mode=%s | stage=%s | channel=%s", mode, stage.name, channel or "(none)")

    gen_standard = _read_standard(stage.gen_standard_file,
                                  "PLACEHOLDER: produce a complete artifact per the standard.")
    eval_criteria = _read_standard(stage.eval_standard_file,
                                   "PLACEHOLDER: PASS only if every check is met; score each 0..its weight.")
    # The channel profile (audience + character/voice) rides into every generator/iterator
    # via the standard, so every stage stays on-audience and in-voice. Gates stay scoped.
    spine, full = _load_channel(channel)
    audience = full if stage.deep_channel else spine   # deep stages (idea/theme/story) get the whole doc
    craft = _load_craft()                              # shared craft, every genre
    layers = []
    if audience:
        layers.append("CHANNEL (who this is for + the voice to write in):\n" + audience)
    if craft:
        layers.append("CRAFT (universal craft -- applies to every genre):\n" + craft)
    layers.append("=== STAGE STANDARD ===\n" + gen_standard)
    gen_standard = "\n\n".join(layers)
    brief, assembly = _resolve_upstream(stage, brief, paths)
    # The one cross-stage gate: give the script's gate the whole package to verify delivery.
    if stage.gate_reads_package and assembly:
        eval_criteria = ("THE STORY PACKAGE (the script MUST deliver all of this):\n"
                         f"{_assembly_text(assembly)}\n\n=== GATE CRITERIA ===\n{eval_criteria}")

    generator, evaluator, iterator, reevaluator = build_modules(stage, dry_run=dry_run, scripted=scripted)
    gen_model = getattr(generator.get_lm(), "model", "?")
    eval_model = getattr(evaluator.get_lm(), "model", "?")
    log.info("generator/iterator LM = %s | evaluator/reevaluator LM = %s", gen_model, eval_model)
    log.info("SEPARATION OK: evaluator LM is distinct from generator LM.")

    def _metric_row(asset_id, version, status, gate):
        logging_setup.write_metric(paths, {
            "run_id": run_id, "stage": stage.name, "asset_id": asset_id, "version": version,
            "status": status, "verdict": getattr(gate, "verdict", None), "score": getattr(gate, "score", None),
            "generator_lm": gen_model, "evaluator_lm": eval_model,
        })

    search_dirs = paths.output_dirs()

    # --- GATE: generate until one PASSES (reject -> brand-new one) ---------
    passed = None
    for attempt in range(1, config.MAX_GEN_ATTEMPTS + 1):
        number = naming.next_number(search_dirs)
        pred = generator(brief=brief, standard=gen_standard)
        content = _content(pred, stage)
        slug = naming.slugify(getattr(pred, stage.topic_field, "") or next(iter(content.values()), ""))
        first_field = content.get(stage.content_fields[0], "")
        log.info("[attempt %d] generating '%s' (%s_%04d)...", attempt, first_field, slug, number)
        gate = evaluator(content=content, criteria=eval_criteria)
        if gate.verdict == "PASS":
            story_id = f"ST-{number:04d}"
            path, asset_id = _save_artifact(stage=stage, assembly=assembly, channel=channel, slug=slug, number=number, version=1,
                                            status="candidate", brief=brief, content=content, gate=gate,
                                            story_id=story_id, gen_model=gen_model, eval_model=eval_model,
                                            dest_dir=paths.candidates)
            _metric_row(asset_id, 1, "candidate", gate)
            log.info("    PASS -> %s (%s) score %d", story_id, path.name, gate.score)
            passed = {"number": number, "slug": slug, "story_id": story_id, "content": content, "gate": gate}
            break
        else:
            path, asset_id = _save_artifact(stage=stage, assembly=assembly, channel=channel, slug=slug, number=number, version=1,
                                            status="rejected", brief=brief, content=content, gate=gate,
                                            story_id=None, gen_model=gen_model, eval_model=eval_model,
                                            dest_dir=paths.rejected)
            _metric_row(asset_id, 1, "rejected", gate)
            log.info("    REJECT -> %s | failed: %s", path.name, gate.failed_checks)

    if passed is None:
        log.info("NO ARTIFACT PASSED THE GATE in %d attempts.", config.MAX_GEN_ATTEMPTS)
        logging_setup.append_run_index(paths, {"run_id": run_id, "stage": stage.name, "mode": mode,
                                               "result": "no_pass", "attempts": config.MAX_GEN_ATTEMPTS})
        log.info("=== run %04d complete (no pass) ===", run_id)
        return {"result": "no_pass", "stage": stage.name, "attempts": config.MAX_GEN_ATTEMPTS, "run_id": run_id}

    # --- SCORE + ITERATE the passing artifact ------------------------------
    number, slug, story_id = passed["number"], passed["slug"], passed["story_id"]
    content, gate = passed["content"], passed["gate"]
    version = 1
    best = {"version": 1, "score": gate.score, "content": content, "gate": gate}

    iterations = 0
    while best["score"] < config.TARGET_SCORE and iterations < config.MAX_ITER:
        iterations += 1
        parent = version
        version += 1
        critique = f"{gate.why}\nPush higher; current weak points: {gate.failed_checks}"
        log.info("[v%02d] iteration %d/%d on %s to raise score...", version, iterations, config.MAX_ITER, story_id)
        content = iterator(content=content, critique=critique, standard=gen_standard)
        gate = reevaluator(content=content, criteria=eval_criteria)
        path, asset_id = _save_artifact(stage=stage, assembly=assembly, channel=channel, slug=slug, number=number, version=version,
                                        status="revised", brief=brief, content=content, gate=gate,
                                        story_id=story_id, gen_model=gen_model, eval_model=eval_model,
                                        dest_dir=paths.candidates, parent_version=parent)
        _metric_row(asset_id, version, "revised", gate)
        log.info("[v%02d] %s scored %d (verdict %s)", version, path.name, gate.score, gate.verdict)
        if gate.verdict != "PASS":
            log.info("    iteration regressed to REJECT -- keeping best v%02d.", best["version"])
            break
        if gate.score > best["score"]:
            best = {"version": version, "score": gate.score, "content": content, "gate": gate}

    # --- finalize: reached target -> ready_for_review, else PARK -----------
    final_version = version + 1
    if best["score"] >= config.TARGET_SCORE:
        log.info("reached target (%d >= %d). Final reevaluation of best v%02d...",
                 best["score"], config.TARGET_SCORE, best["version"])
        final_gate = reevaluator(content=best["content"], criteria=eval_criteria)
        path, asset_id = _save_artifact(stage=stage, assembly=assembly, channel=channel, slug=slug, number=number, version=final_version,
                                        status="ready_for_review", brief=brief, content=best["content"],
                                        gate=final_gate, story_id=story_id, gen_model=gen_model,
                                        eval_model=eval_model, dest_dir=paths.candidates,
                                        parent_version=best["version"])
        _metric_row(asset_id, final_version, "ready_for_review", final_gate)
        outcome, final_score = "ready_for_review", final_gate.score
        log.info("READY FOR REVIEW: %s (%s) | final score %d", path.name, story_id, final_gate.score)
    else:
        path, asset_id = _save_artifact(stage=stage, assembly=assembly, channel=channel, slug=slug, number=number, version=final_version,
                                        status="parked", brief=brief, content=best["content"],
                                        gate=best["gate"], story_id=story_id, gen_model=gen_model,
                                        eval_model=eval_model, dest_dir=paths.parked,
                                        parent_version=best["version"])
        _metric_row(asset_id, final_version, "parked", best["gate"])
        outcome, final_score = "parked", best["score"]
        log.info("PARKED: %s (%s) | best %d < target %d after %d iterations",
                 path.name, story_id, best["score"], config.TARGET_SCORE, iterations)

    logging_setup.append_run_index(paths, {
        "run_id": run_id, "stage": stage.name, "asset_id": asset_id, "story_id": story_id, "mode": mode,
        "outcome": outcome, "versions": final_version, "best_score": best["score"],
        "final_score": final_score, "target": config.TARGET_SCORE, "artifact": path.name,
    })
    log.info("=== run %04d complete (%s) ===", run_id, outcome)
    return {"asset_id": asset_id, "stage": stage.name, "story_id": story_id, "outcome": outcome,
            "artifact": str(path), "final_score": final_score, "best_score": best["score"],
            "versions": final_version, "run_id": run_id}
