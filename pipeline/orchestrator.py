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


def _stage_dummy_answers(stage):
    """Generic offline (--dry-run) dummy answers for ANY stage, built by
    introspecting the stage's OWN signatures (the same approach as
    chain._scripted_for) so a non-idea stage's --dry-run is fed answers shaped to
    its signature, not idea's. Returns (gen_answers, eval_answers).

    The gate sequence is REJECT-then-PASS so the dry run still exercises the
    reject path; the REJECT zeros the stage's first criterion, and every PASS
    fills each criterion with its full weight (a clean pass) and any extra gate
    fields (verdict/failed_checks/why/jargon)."""
    def _gen_answer():
        # The gen-side DummyLM is SHARED by the generator (gen_sig) AND the
        # iterator (iter_sig) in dry-run, so one answer must satisfy BOTH
        # signatures: the generator's output fields plus the iterator's
        # improved_<field> fields (else the iteration step parse-fails).
        gen = {"reasoning": "drafting"}
        for name in list(stage.gen_sig.output_fields) + list(stage.iter_sig.output_fields):
            if name == "reasoning" or name in gen:
                continue
            if name == stage.topic_field:
                gen[name] = f"DRY-RUN {stage.name}"
            else:
                gen[name] = f"DRY-RUN {stage.name}:{name}"
        return gen

    def _eval_answer(verdict, zero_first=False):
        ev = {"reasoning": "judging"}
        for name in stage.gate_sig.output_fields:
            if name == "reasoning":
                continue
            if name == "verdict":
                ev[name] = verdict
            elif name == "failed_checks":
                ev[name] = ("1: dry reject" if zero_first else "none")
            elif name == "why":
                ev[name] = "gate decision"
            elif name == "jargon":
                ev[name] = "false"            # not in (true/yes/1) -> no penalty
            elif name.startswith("score_"):
                k = int(name.split("_")[1])
                # REJECT zeros the first criterion (forces the all-pass reject);
                # everything else gets its full weight (a clean pass).
                ev[name] = "0" if (zero_first and k == min(stage.weights)) else str(stage.weights.get(k, 0))
            else:
                ev[name] = "dry"
        return ev

    gen_answers = [_gen_answer() for _ in range(config.MAX_GEN_ATTEMPTS)]
    # First gate REJECTs (exercise the reject path), then enough PASSes for the
    # remaining generate attempt + every iteration + the final re-eval.
    eval_answers = [_eval_answer("REJECT", zero_first=True)]
    eval_answers += [_eval_answer("PASS") for _ in range(config.MAX_ITER + 3)]
    return gen_answers, eval_answers


def _stage_dummy_lms(stage):
    """Two independent stub LMs for an offline single-stage smoke run (--dry-run),
    generic over the given stage (see _stage_dummy_answers)."""
    from dspy.utils.dummies import DummyLM

    gen_answers, eval_answers = _stage_dummy_answers(stage)
    lm_a, lm_b = DummyLM(gen_answers), DummyLM(eval_answers)
    lm_a.model, lm_b.model = "dummy/generator-A", "dummy/evaluator-B"
    return lm_a, lm_b


def build_modules(stage, dry_run: bool = False, scripted: dict = None, paths=None):
    generator = Generator(stage.gen_sig)
    iterator = Iterator(stage.iter_sig, stage.content_fields)
    evaluator = Evaluator(stage.gate_sig, stage.weights, stage.penalty_points, stage.verdict_floor)
    reevaluator = Reevaluator(stage.gate_sig, stage.weights, stage.penalty_points, stage.verdict_floor)
    # lm_iter/lm_reeval default to SHARING the gen-side/eval-side LM. That is the
    # correct behavior for dry_run/scripted (the dummy/scripted answers are built
    # for the gen/eval pair; building separate dummies there would be wrong). Only
    # the LIVE branch overrides them so the iterator/reevaluator run on their OWN
    # configs (C5: ITERATOR_LM temp 0.7, REEVALUATOR_LM -- previously dead config).
    if scripted is not None:
        from dspy.utils.dummies import DummyLM
        lm_a = DummyLM(scripted["gen_answers"])
        lm_b = DummyLM(scripted["eval_answers"])
        lm_a.model, lm_b.model = "manual/generator", "manual/evaluator"
        lm_iter, lm_reeval = lm_a, lm_b
    elif dry_run:
        lm_a, lm_b = _stage_dummy_lms(stage)
        lm_iter, lm_reeval = lm_a, lm_b
    else:
        lm_a = dspy.LM(**config.GENERATOR_LM)
        lm_iter = dspy.LM(**config.ITERATOR_LM)
        lm_b = dspy.LM(**config.EVALUATOR_LM)
        lm_reeval = dspy.LM(**config.REEVALUATOR_LM)
    # LIVE only (real paid run): if a compiled (optimized) generator exists for this
    # stage, load its bootstrapped demos into the FRESH student so learning actually
    # reaches production. dspy load can wipe the per-predictor .lm (learn.py's
    # reset_copy() note), so we load BEFORE set_lm and then re-affirm the LM below --
    # leaving the loaded generator callable. Never load in dry_run/scripted (DummyLM
    # demos would be meaningless/harmful). The loaded path (or None) is returned to
    # the caller (run()) so it can log it.
    loaded_compiled = None
    live = (scripted is None) and (dry_run is False)
    if live and paths is not None:
        compiled_path = paths.compiled / f"{stage.name}_generator.json"
        if compiled_path.exists():
            generator.load(str(compiled_path))
            loaded_compiled = compiled_path
    generator.set_lm(lm_a)
    iterator.set_lm(lm_iter)
    evaluator.set_lm(lm_b)
    reevaluator.set_lm(lm_reeval)
    assert_separation(generator.get_lm(), evaluator.get_lm())
    return generator, evaluator, iterator, reevaluator, loaded_compiled


# ---------------------------------------------------------------------------
# Standards + upstream handoff
# ---------------------------------------------------------------------------
def _read_standard(filename: str, fallback: str, required: bool = False) -> str:
    path = config.STANDARDS_DIR / filename
    if path.exists():
        return path.read_text(encoding="utf-8")
    if required:
        # LIVE runs: refuse to proceed with a placeholder standard -- that would
        # spend real LLM calls grading/generating against nothing.
        raise FileNotFoundError(
            f"Missing required stage standard file '{filename}' at {path}. "
            f"A live run cannot proceed without it -- create it before running."
        )
    return fallback


def _extract_spine(text: str) -> str:
    """The tight positioning block between the SPINE markers (fed to EVERY stage).
    Old profiles without markers -> the whole doc is the spine (back-compatible)."""
    m = re.search(r"<!--\s*SPINE:START\s*-->(.*?)<!--\s*SPINE:END\s*-->", text, re.DOTALL | re.IGNORECASE)
    return m.group(1) if m else text


def _load_craft() -> str:
    """The shared, genre-agnostic craft doctrine, injected into every generator."""
    p = config.CRAFT_PRINCIPLES
    return p.read_text(encoding="utf-8").strip() if p.exists() else ""


def _load_channel(channel: str, live: bool = False):
    """Returns (spine, full) for a channel profile. spine = the positioning block fed
    to every stage; full = the whole profile fed to the deep stages only. HTML
    comments (the meta note + markers) are stripped so they never reach a prompt.

    The two empty-result cases are distinct:
      - channel falsy -> the legitimate "no channel" / _sandbox case; never raises.
      - channel named but its profile.md is missing -> in a LIVE run, refuse to
        proceed (no profile == no audience/voice == wasted paid LLM calls)."""
    if not channel:
        return "", ""
    path = config.CHANNELS_DIR / channel / "profile.md"
    if not path.exists():
        if live:
            raise FileNotFoundError(
                f"Channel '{channel}' has no profile at {path}. A live run cannot "
                f"proceed without the channel profile -- create it (e.g. "
                f"`python run.py new-channel {channel}`) before running."
            )
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
    """Returns (brief, assembly, story_id). assembly = the structured content of EVERY
    prior accepted stage, so each artifact carries the growing package (no gathering
    later). story_id = the upstream artifact's story id, threaded forward so every
    stage of ONE video shares a single ST-#### (None when there is no upstream -> the
    first stage mints a fresh id). The format stays separable because each script
    format is its own stage/artifact -- they share the id but differ by `stage`."""
    if not stage.upstream:
        return brief, {}, None
    rec = _latest_accepted(stage.upstream, paths.accepted)
    if rec is None:
        raise RuntimeError(f"No accepted '{stage.upstream}' artifact to feed stage '{stage.name}'.")
    assembly = {**(rec.get("assembly") or {}), stage.upstream: rec.get("content", {})}
    return stage.build_brief(rec), assembly, rec.get("story_id")


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
def _llm_call(log, what, fn, **kwargs):
    """Run one LM call. If it throws (model not found, auth, API/timeout error),
    log the FULL traceback to this run's log file before re-raising -- so failures
    show up in the log instead of vanishing to the terminal."""
    try:
        return fn(**kwargs)
    except Exception:
        log.exception("LM CALL FAILED during %s -- this is why the run produced nothing:", what)
        raise


def run(stage_name: str = "idea", brief: str = None, dry_run: bool = False, scripted: dict = None,
        channel: str = None) -> dict:
    stage = stages.get_stage(stage_name)
    paths = config.paths_for(channel)          # this channel's self-contained workspace
    run_id = logging_setup.next_run_id(paths)
    log = logging_setup.get_run_logger(run_id, paths)
    mode = "MANUAL (your content + scores)" if scripted else ("DRY-RUN (stub LMs)" if dry_run else "LIVE")
    log.info("mode=%s | stage=%s | channel=%s", mode, stage.name, channel or "(none)")

    # LIVE = real paid LLM calls. Only then do we hard-fail on a missing standard or a
    # named-but-missing channel profile (a placeholder there means money spent on nothing).
    # dry_run / scripted (offline) and the "no channel" sandbox case keep their behavior.
    live = (dry_run is False) and (scripted is None)

    gen_standard = _read_standard(stage.gen_standard_file,
                                  "PLACEHOLDER: produce a complete artifact per the standard.",
                                  required=live)
    eval_criteria = _read_standard(stage.eval_standard_file,
                                   "PLACEHOLDER: PASS only if every check is met; score each 0..its weight.",
                                   required=live)
    # The channel profile (audience + character/voice) rides into every generator/iterator
    # via the standard, so every stage stays on-audience and in-voice. Gates stay scoped.
    spine, full = _load_channel(channel, live=live)
    audience = full if stage.deep_channel else spine   # deep stages (idea/theme/story) get the whole doc
    craft = _load_craft()                              # shared craft, every genre
    layers = []
    if audience:
        layers.append("CHANNEL (who this is for + the voice to write in):\n" + audience)
    if craft:
        layers.append("CRAFT (universal craft -- applies to every genre):\n" + craft)
    layers.append("=== STAGE STANDARD ===\n" + gen_standard)
    gen_standard = "\n\n".join(layers)
    brief, assembly, inherited_story_id = _resolve_upstream(stage, brief, paths)
    # The one cross-stage gate: give the script's gate the whole package to verify delivery.
    if stage.gate_reads_package and assembly:
        eval_criteria = ("THE STORY PACKAGE (the script MUST deliver all of this):\n"
                         f"{_assembly_text(assembly)}\n\n=== GATE CRITERIA ===\n{eval_criteria}")

    generator, evaluator, iterator, reevaluator, loaded_compiled = build_modules(
        stage, dry_run=dry_run, scripted=scripted, paths=paths)
    if loaded_compiled is not None:
        log.info("LOADED compiled generator (learned demos) <- %s", loaded_compiled)
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
        pred = _llm_call(log, "idea/content generation", generator, brief=brief, standard=gen_standard)
        content = _content(pred, stage)
        slug = naming.slugify(getattr(pred, stage.topic_field, "") or next(iter(content.values()), ""))
        first_field = content.get(stage.content_fields[0], "")
        log.info("[attempt %d] generating '%s' (%s_%04d)...", attempt, first_field, slug, number)
        gate = _llm_call(log, "gate / evaluation (the OpenRouter judge)", evaluator, content=content, criteria=eval_criteria)
        if gate.verdict == "PASS":
            # Inherit the video's id from upstream; only the first stage (no
            # upstream) mints a new one. So idea/theme/story/stakebake + all four
            # script formats + packaging + description of one video share one id.
            story_id = inherited_story_id or f"ST-{number:04d}"
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
        weak = [
            f"#{k} {stage.labels[k]} scored {gate.breakdown.get(k, 0)}/{stage.weights[k]}"
            for k in sorted(stage.weights)
            if gate.breakdown.get(k, 0) < stage.weights[k]
        ]
        critique = (
            f"Score {gate.score}/{config.SCORE_SCALE}. Raise ONLY the checks below full marks "
            f"(leave everything already at full as it is): "
            f"{'; '.join(weak) if weak else '(all checks already at full marks)'}."
        )
        log.info("[v%02d] iteration %d/%d on %s to raise score...", version, iterations, config.MAX_ITER, story_id)
        content = _llm_call(log, "iteration", iterator, content=content, critique=critique, standard=gen_standard)
        gate = _llm_call(log, "re-evaluation (the OpenRouter judge)", reevaluator, content=content, criteria=eval_criteria)
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
        final_gate = _llm_call(log, "final re-evaluation (the OpenRouter judge)", reevaluator, content=best["content"], criteria=eval_criteria)
        # Only promote when the FINAL re-eval still agrees: PASS verdict AND at/above
        # target. A regression here (REJECT, or a final score below target) must PARK,
        # not land in candidates as ready_for_review. (Mirrors the iteration loop's
        # non-PASS handling above.)
        if final_gate.verdict == "PASS" and final_gate.score >= config.TARGET_SCORE:
            path, asset_id = _save_artifact(stage=stage, assembly=assembly, channel=channel, slug=slug, number=number, version=final_version,
                                            status="ready_for_review", brief=brief, content=best["content"],
                                            gate=final_gate, story_id=story_id, gen_model=gen_model,
                                            eval_model=eval_model, dest_dir=paths.candidates,
                                            parent_version=best["version"])
            _metric_row(asset_id, final_version, "ready_for_review", final_gate)
            outcome, final_score = "ready_for_review", final_gate.score
            log.info("READY FOR REVIEW: %s (%s) | final score %d", path.name, story_id, final_gate.score)
        else:
            log.info("    final re-eval REGRESSED (verdict %s, score %d) -- parking instead of promoting.",
                     final_gate.verdict, final_gate.score)
            path, asset_id = _save_artifact(stage=stage, assembly=assembly, channel=channel, slug=slug, number=number, version=final_version,
                                            status="parked", brief=brief, content=best["content"],
                                            gate=final_gate, story_id=story_id, gen_model=gen_model,
                                            eval_model=eval_model, dest_dir=paths.parked,
                                            parent_version=best["version"])
            _metric_row(asset_id, final_version, "parked", final_gate)
            outcome, final_score = "parked", final_gate.score
            log.info("PARKED (final regression): %s (%s) | final score %d", path.name, story_id, final_gate.score)
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
