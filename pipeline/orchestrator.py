"""The orchestrator: a gate + score HYBRID for Step 1.

1. Enforce the #1 rule (evaluator on a separate LM) or refuse to run.
2. GATE: generate an idea, run the six-check gate. REJECT -> write it to
   rejected/ and bring a brand-new idea (up to MAX_GEN_ATTEMPTS). PASS -> assign
   a story id ST-#### and proceed.
3. SCORE + ITERATE: push the passing idea higher (iterator -> reevaluator) while
   it is below TARGET_SCORE, up to MAX_ITER attempts. If it reaches the target, a
   final independent reevaluation marks it ready_for_review. If it cannot reach
   the target within MAX_ITER, it is PARKED (set aside to learn from, not killed).
"""

import json
from datetime import datetime, timezone

import dspy

import config
from pipeline import logging_setup, naming, render
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


def _dummy_lms():
    """Two independent stub LMs for an offline, zero-cost dry run.

    Demonstrates the hybrid + parking: the first idea is REJECTED at the gate, a
    new idea PASSES (72), iteration lifts it to 80/86/88 but never reaches the
    95 target within MAX_ITER -> it is PARKED.
    """
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
    # (verdict, [score_1..score_6], reaction_2, failed_checks). Totals: 0(rej),72,80,86,88,95.
    eval_specs = [
        ("REJECT", [25, 0, 0, 10, 10, 10], "none", "2,3: resolution missing; emotions not distinct"),
        ("PASS", [20, 18, 14, 8, 6, 6], "Aah", "none"),
        ("PASS", [22, 20, 16, 8, 7, 7], "Aah", "none"),
        ("PASS", [23, 22, 17, 8, 8, 8], "Aah", "none"),
        ("PASS", [24, 22, 18, 8, 8, 8], "Aah", "none"),
        ("PASS", [25, 24, 19, 9, 9, 9], "Aah", "none"),
    ]
    eval_answers = []
    for (v, scores, r2, fc) in eval_specs:
        d = {"reasoning": "judging", "verdict": v, "reaction_1": "WTF", "reaction_2": r2,
             "viewer_action": "Reflect", "failed_checks": fc, "why": "gate decision"}
        for i, s in enumerate(scores, start=1):
            d[f"score_{i}"] = str(s)
        eval_answers.append(d)
    lm_a, lm_b = DummyLM(gen_answers), DummyLM(eval_answers)
    lm_a.model, lm_b.model = "dummy/generator-A", "dummy/evaluator-B"
    return lm_a, lm_b


def build_modules(dry_run: bool = False, scripted: dict = None):
    generator, evaluator, iterator, reevaluator = Generator(), Evaluator(), Iterator(), Reevaluator()
    if scripted is not None:
        # MANUAL mode: hand-authored idea + scores stand in for the LLMs.
        from dspy.utils.dummies import DummyLM
        lm_a = DummyLM(scripted["gen_answers"])
        lm_b = DummyLM(scripted["eval_answers"])
        lm_a.model, lm_b.model = "manual/generator", "manual/evaluator"
    elif dry_run:
        lm_a, lm_b = _dummy_lms()
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
# Helpers
# ---------------------------------------------------------------------------
def _idea_dict(pred) -> dict:
    return {"one_liner": pred.one_liner, "resolution": pred.resolution,
            "reaction_1": pred.reaction_1, "reaction_2": pred.reaction_2,
            "viewer_action": pred.viewer_action}


def _save_artifact(*, slug, number, version, status, brief, idea, gate, story_id,
                   gen_model, eval_model, dest_dir, parent_version=None):
    dest_dir.mkdir(parents=True, exist_ok=True)
    base = naming.format_name(slug, number, version, status)
    asset_id = f"{slug}_{number:04d}"
    record = {
        "asset_id": asset_id,
        "story_id": story_id,
        "slug": slug,
        "number": number,
        "version": version,
        "status": status,
        "parent_version": parent_version,
        "brief": brief,
        "idea": idea,
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
    # Human-readable twin for the review step.
    (dest_dir / f"{base}.txt").write_text(render.to_text(record), encoding="utf-8")
    return path, asset_id


# ---------------------------------------------------------------------------
# The hybrid loop
# ---------------------------------------------------------------------------
def run(brief: str, gen_standard: str, eval_criteria: str, dry_run: bool = False, scripted: dict = None) -> dict:
    run_id = logging_setup.next_run_id()
    log = logging_setup.get_run_logger(run_id)
    mode = "MANUAL (your content + scores)" if scripted else ("DRY-RUN (stub LMs)" if dry_run else "LIVE")
    log.info("mode=%s", mode)

    generator, evaluator, iterator, reevaluator = build_modules(dry_run=dry_run, scripted=scripted)
    gen_model = getattr(generator.get_lm(), "model", "DummyLM(A)")
    eval_model = getattr(evaluator.get_lm(), "model", "DummyLM(B)")
    log.info("generator/iterator LM = %s | evaluator/reevaluator LM = %s", gen_model, eval_model)
    log.info("SEPARATION OK: evaluator LM is distinct from generator LM.")

    def _metric_row(asset_id, version, status, gate):
        logging_setup.write_metric({
            "run_id": run_id, "asset_id": asset_id,
            "version": version, "status": status,
            "verdict": getattr(gate, "verdict", None), "score": getattr(gate, "score", None),
            "generator_lm": gen_model, "evaluator_lm": eval_model,
        })

    # --- GATE: generate until one PASSES (reject -> brand-new idea) ---------
    passed = None
    for attempt in range(1, config.MAX_GEN_ATTEMPTS + 1):
        number = naming.next_number(
            [config.CANDIDATES_DIR, config.ACCEPTED_DIR, config.REJECTED_DIR,
             config.ARCHIVED_DIR, config.PARKED_DIR],
        )
        gen_pred = generator(brief=brief, standard=gen_standard)
        idea = _idea_dict(gen_pred)
        slug = naming.slugify(getattr(gen_pred, "topic", "") or idea["one_liner"])
        log.info("[attempt %d] generating '%s' (%s_%04d)...", attempt, idea["one_liner"], slug, number)
        gate = evaluator(idea=idea, criteria=eval_criteria)
        if gate.verdict == "PASS":
            story_id = f"ST-{number:04d}"
            path, asset_id = _save_artifact(slug=slug, number=number, version=1, status="candidate",
                                            brief=brief, idea=idea, gate=gate, story_id=story_id,
                                            gen_model=gen_model, eval_model=eval_model,
                                            dest_dir=config.CANDIDATES_DIR)
            _metric_row(asset_id, 1, "candidate", gate)
            log.info("    PASS -> %s (%s) score %d", story_id, path.name, gate.score)
            passed = {"number": number, "slug": slug, "story_id": story_id, "idea": idea, "gate": gate}
            break
        else:
            path, asset_id = _save_artifact(slug=slug, number=number, version=1, status="rejected",
                                            brief=brief, idea=idea, gate=gate, story_id=None,
                                            gen_model=gen_model, eval_model=eval_model,
                                            dest_dir=config.REJECTED_DIR)
            _metric_row(asset_id, 1, "rejected", gate)
            log.info("    REJECT -> %s | failed: %s", path.name, gate.failed_checks)

    if passed is None:
        log.info("NO IDEA PASSED THE GATE in %d attempts. Bring a new brief or loosen nothing.",
                 config.MAX_GEN_ATTEMPTS)
        logging_setup.append_run_index({"run_id": run_id, "mode": mode, "result": "no_pass",
                                        "attempts": config.MAX_GEN_ATTEMPTS})
        log.info("=== run %04d complete (no pass) ===", run_id)
        return {"result": "no_pass", "attempts": config.MAX_GEN_ATTEMPTS, "run_id": run_id}

    # --- SCORE + ITERATE the passing idea ----------------------------------
    number, slug, story_id = passed["number"], passed["slug"], passed["story_id"]
    idea, gate = passed["idea"], passed["gate"]
    version = 1
    best = {"version": 1, "score": gate.score, "idea": idea, "gate": gate}

    iterations = 0
    while best["score"] < config.TARGET_SCORE and iterations < config.MAX_ITER:
        iterations += 1
        parent = version
        version += 1
        critique = f"{gate.why}\nPush higher; current weak points: {gate.failed_checks}"
        log.info("[v%02d] iteration %d/%d on %s to raise score...", version, iterations, config.MAX_ITER, story_id)
        idea = _idea_dict(iterator(idea=idea, critique=critique, standard=gen_standard))
        gate = reevaluator(idea=idea, criteria=eval_criteria)
        path, asset_id = _save_artifact(slug=slug, number=number, version=version, status="revised", brief=brief,
                                        idea=idea, gate=gate, story_id=story_id, gen_model=gen_model,
                                        eval_model=eval_model, dest_dir=config.CANDIDATES_DIR, parent_version=parent)
        _metric_row(asset_id, version, "revised", gate)
        log.info("[v%02d] %s scored %d (verdict %s)", version, path.name, gate.score, gate.verdict)
        if gate.verdict != "PASS":
            log.info("    iteration regressed to REJECT -- keeping best v%02d.", best["version"])
            break
        if gate.score > best["score"]:
            best = {"version": version, "score": gate.score, "idea": idea, "gate": gate}

    # --- finalize: reached target -> ready_for_review, else PARK -----------
    final_version = version + 1
    if best["score"] >= config.TARGET_SCORE:
        log.info("reached target (%d >= %d). Final reevaluation of best v%02d...",
                 best["score"], config.TARGET_SCORE, best["version"])
        final_gate = reevaluator(idea=best["idea"], criteria=eval_criteria)
        path, asset_id = _save_artifact(slug=slug, number=number, version=final_version, status="ready_for_review",
                                        brief=brief, idea=best["idea"], gate=final_gate, story_id=story_id,
                                        gen_model=gen_model, eval_model=eval_model,
                                        dest_dir=config.CANDIDATES_DIR, parent_version=best["version"])
        _metric_row(asset_id, final_version, "ready_for_review", final_gate)
        outcome, final_score = "ready_for_review", final_gate.score
        log.info("READY FOR REVIEW: %s (%s) | final score %d", path.name, story_id, final_gate.score)
    else:
        path, asset_id = _save_artifact(slug=slug, number=number, version=final_version, status="parked",
                                        brief=brief, idea=best["idea"], gate=best["gate"], story_id=story_id,
                                        gen_model=gen_model, eval_model=eval_model,
                                        dest_dir=config.PARKED_DIR, parent_version=best["version"])
        _metric_row(asset_id, final_version, "parked", best["gate"])
        outcome, final_score = "parked", best["score"]
        log.info("PARKED: %s (%s) | best %d < target %d after %d iterations",
                 path.name, story_id, best["score"], config.TARGET_SCORE, iterations)

    logging_setup.append_run_index({
        "run_id": run_id, "asset_id": asset_id, "story_id": story_id, "mode": mode,
        "outcome": outcome, "versions": final_version, "best_score": best["score"],
        "final_score": final_score, "target": config.TARGET_SCORE, "artifact": path.name,
    })
    log.info("=== run %04d complete (%s) ===", run_id, outcome)
    return {"asset_id": asset_id, "story_id": story_id, "outcome": outcome, "artifact": str(path),
            "final_score": final_score, "best_score": best["score"],
            "versions": final_version, "run_id": run_id}
