"""TDD coverage for two verified defects in pipeline/orchestrator.py.

C5: ITERATOR_LM and REEVALUATOR_LM are declared in config but never used. The
    LIVE branch of build_modules built only GENERATOR_LM and EVALUATOR_LM, then
    ran the iterator at the generator's LM (temperature 0.9) instead of
    ITERATOR_LM (0.7), leaving REEVALUATOR_LM dead config. Fix: LIVE builds all
    FOUR LMs and wires each module to its own. dry_run/scripted must be
    UNCHANGED -- there the iterator shares the generator's DummyLM and the
    reevaluator shares the evaluator's DummyLM.

C7: single-stage --dry-run only worked for the idea stage, because the dry_run
    branch hard-coded idea's output fields. Fix: the dry-run dummy builder is
    GENERIC over the stage (introspects stage.gen_sig / stage.gate_sig output
    fields, like chain._scripted_for), so any stage's --dry-run produces answers
    that match THAT stage's signatures.

All runs are hermetic: orchestrator.dspy.LM is monkeypatched (C5) and the
dry-run path uses DummyLM (C7). No network, no API keys.
"""

import json

import config
from pipeline import orchestrator, stages
from pipeline.evaluator import parse_int


# ===========================================================================
# C5 -- four LMs, each from its own config; dry/scripted wiring unchanged.
# ===========================================================================

def _record_lm_factory():
    """A stub for orchestrator.dspy.LM that records each construction's kwargs and
    returns a tagged fake LM carrying the model string it was built from."""
    calls = []

    class _FakeLM:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            self.model = kwargs.get("model")
            self.temperature = kwargs.get("temperature")

    def _factory(**kwargs):
        calls.append(kwargs)
        return _FakeLM(**kwargs)

    return _factory, calls


def test_c5_live_builds_all_four_lms_each_from_its_own_config(channel_ws, monkeypatch):
    """LIVE build_modules constructs dspy.LM from ALL FOUR configs and wires each
    module to its own: generator<-GENERATOR_LM, iterator<-ITERATOR_LM,
    evaluator<-EVALUATOR_LM, reevaluator<-REEVALUATOR_LM."""
    paths = channel_ws["paths"]
    stage = stages.get_stage("idea")
    factory, calls = _record_lm_factory()
    monkeypatch.setattr(orchestrator.dspy, "LM", factory)

    generator, evaluator, iterator, reevaluator, _ = orchestrator.build_modules(
        stage, dry_run=False, scripted=None, paths=paths
    )

    # All four configs were used to construct an LM.
    built_temps = sorted(c.get("temperature") for c in calls)
    assert len(calls) == 4, f"expected four LM constructions, got {len(calls)}: {calls}"
    assert sorted(
        [config.GENERATOR_LM["temperature"], config.ITERATOR_LM["temperature"],
         config.EVALUATOR_LM["temperature"], config.REEVALUATOR_LM["temperature"]]
    ) == built_temps, built_temps

    # Each module wired to its OWN config (temperature is the distinguishing knob:
    # generator 0.9 vs iterator 0.7; both eval-side at 0.0 but separate instances).
    assert generator.get_lm().temperature == config.GENERATOR_LM["temperature"]
    assert iterator.get_lm().temperature == config.ITERATOR_LM["temperature"]
    assert generator.get_lm().temperature != iterator.get_lm().temperature, (
        "iterator is still running at the generator's temperature -- ITERATOR_LM unused"
    )
    assert evaluator.get_lm().temperature == config.EVALUATOR_LM["temperature"]
    assert reevaluator.get_lm().temperature == config.REEVALUATOR_LM["temperature"]

    # The reevaluator must be its OWN instance, not the evaluator's (REEVALUATOR_LM
    # was dead config before).
    assert reevaluator.get_lm() is not evaluator.get_lm(), (
        "reevaluator shares the evaluator's LM instance -- REEVALUATOR_LM unused"
    )
    # And the iterator must be its own instance, not the generator's.
    assert iterator.get_lm() is not generator.get_lm()

    # The separation guarantee still holds (generator vs evaluator).
    assert generator.get_lm().model == config.GENERATOR_LM["model"]
    assert evaluator.get_lm().model == config.EVALUATOR_LM["model"]
    assert generator.get_lm().model != evaluator.get_lm().model


def test_c5_dry_run_shares_gen_and_eval_dummy_lms(channel_ws):
    """C5 must NOT disturb dry/scripted wiring: in dry_run the iterator shares the
    generator's DummyLM and the reevaluator shares the evaluator's DummyLM."""
    paths = channel_ws["paths"]
    stage = stages.get_stage("idea")

    generator, evaluator, iterator, reevaluator, _ = orchestrator.build_modules(
        stage, dry_run=True, scripted=None, paths=paths
    )

    assert iterator.get_lm() is generator.get_lm(), "dry_run iterator should share the generator DummyLM"
    assert reevaluator.get_lm() is evaluator.get_lm(), "dry_run reevaluator should share the evaluator DummyLM"
    # Still separated gen vs eval.
    assert generator.get_lm() is not evaluator.get_lm()


def test_c5_scripted_shares_gen_and_eval_dummy_lms(channel_ws):
    """Same sharing guarantee for the scripted/manual path."""
    paths = channel_ws["paths"]
    stage = stages.get_stage("idea")
    scripted = {
        "gen_answers": [{"reasoning": "r", "one_liner": "x", "resolution": "x",
                         "reaction_1": "WTF", "reaction_2": "Aah",
                         "viewer_action": "Reflect", "topic": "t"}],
        "eval_answers": [{"reasoning": "r", "verdict": "PASS", "failed_checks": "none",
                          "why": "ok", "score_1": "25", "score_2": "25", "score_3": "20",
                          "score_4": "10", "score_5": "10", "score_6": "10"}],
    }

    generator, evaluator, iterator, reevaluator, _ = orchestrator.build_modules(
        stage, dry_run=False, scripted=scripted, paths=paths
    )

    assert iterator.get_lm() is generator.get_lm()
    assert reevaluator.get_lm() is evaluator.get_lm()
    assert generator.get_lm() is not evaluator.get_lm()


# ===========================================================================
# C7 -- the dry-run dummy builder is generic over the stage.
# ===========================================================================

NON_IDEA = "stakebake"


def test_c7_dummy_answers_are_generic_over_a_non_idea_stage(channel_ws):
    """The generalized dummy-answer builder for a NON-idea stage produces gen
    answers carrying THAT stage's gen_sig output fields and eval answers carrying
    THAT stage's gate_sig fields -- not idea's. Tested on the raw answer lists so
    the DummyLM's one-shot answer iterator is not consumed."""
    stage = stages.get_stage(NON_IDEA)

    gen_answers, eval_answers = orchestrator._stage_dummy_answers(stage)

    gen_answer = gen_answers[0]
    for f in stage.gen_sig.output_fields:
        assert f in gen_answer, f"generator dummy answer missing gen_sig field {f!r}: {list(gen_answer)}"
    # It is NOT shaped to idea (idea has one_liner; stakebake does not).
    assert "one_liner" not in gen_answer, "dry-run still produced idea-shaped generator answers"

    # The eval answers carry the stage's gate_sig fields: a PASS answer must have a
    # score_<k> for every weighted criterion, defaulted to its weight.
    pass_answer = next(a for a in eval_answers if a.get("verdict") == "PASS")
    for f in stage.gate_sig.output_fields:
        assert f in pass_answer, f"evaluator dummy answer missing gate_sig field {f!r}: {list(pass_answer)}"
    for k, weight in stage.weights.items():
        assert parse_int(pass_answer[f"score_{k}"]) == weight, (
            f"score_{k} should default to its weight {weight}"
        )


def test_c7_non_idea_generate_and_gate_parse_without_field_mismatch(channel_ws):
    """A generate + gate call on the dry-run modules for a non-idea stage parses
    cleanly (no missing-field error) and PASSes the gate -- proof the idea-shaped
    answers are gone."""
    paths = channel_ws["paths"]
    stage = stages.get_stage(NON_IDEA)

    generator, evaluator, iterator, reevaluator, _ = orchestrator.build_modules(
        stage, dry_run=True, scripted=None, paths=paths
    )

    pred = generator(brief="a brief", standard="a standard")
    content = {f: getattr(pred, f) for f in stage.content_fields}
    # Every content field is present (no field mismatch against this stage's gen_sig).
    for f in stage.content_fields:
        assert getattr(pred, f) is not None

    gate = evaluator(content=content, criteria="some criteria")
    assert gate.verdict == "PASS", f"non-idea dry gate should PASS, got {gate.verdict}"


def test_c7_idea_dry_run_still_works(channel_ws):
    """Regression: the idea dry-run path still builds modules whose generate parses
    against idea's gen_sig, and still exercises a REJECT-then-PASS gate sequence."""
    stage = stages.get_stage("idea")

    # The generalized builder still serves idea: gen answers carry idea's fields.
    gen_answers, eval_answers = orchestrator._stage_dummy_answers(stage)
    for f in stage.gen_sig.output_fields:
        assert f in gen_answers[0], f"idea gen answer missing {f!r}"
    # The reject-path exercise is preserved: the first gate answer REJECTs.
    assert eval_answers[0].get("verdict") == "REJECT", (
        f"idea dry-run should keep its REJECT-then-PASS sequence; first verdict "
        f"was {eval_answers[0].get('verdict')}"
    )

    # And build_modules(dry_run) still yields a callable generator that parses.
    generator, evaluator, *_ = orchestrator.build_modules(
        stage, dry_run=True, scripted=None, paths=channel_ws["paths"]
    )
    pred = generator(brief="a brief", standard="a standard")
    for f in stage.gen_sig.output_fields:
        assert getattr(pred, f) is not None


def test_c7_non_idea_full_dry_run_end_to_end(channel_ws):
    """Integration: a non-idea single-stage --dry-run completes end to end.

    stakebake needs an accepted upstream (story). We scaffold it by running the
    spine upstream stages in dry-run and promoting each, then run stakebake in
    dry-run and assert it reaches ready_for_review (instead of raising a
    field-mismatch error as the old idea-hard-coded dry path did)."""
    from pipeline import chain

    channel = channel_ws["channel"]
    paths = channel_ws["paths"]

    # Scaffold the upstream spine (idea -> theme -> story) via dry-run + promote.
    for name in ["idea", "theme", "story"]:
        upstream_stage = stages.get_stage(name)
        scripted = chain._scripted_for(upstream_stage)
        # Use scripted (the chain's own dry path) ONLY to plant accepted upstream
        # artifacts; the stage under test (stakebake) is run via dry_run below.
        res = orchestrator.run(stage_name=name,
                               brief=("a test brief" if name == "idea" else None),
                               channel=channel, scripted=scripted)
        assert res["outcome"] == "ready_for_review", (name, res["outcome"])
        chain._promote(res["artifact"], paths)

    # Now run the NON-idea stage as a single-stage --dry-run (the C7 code path).
    res = orchestrator.run(stage_name=NON_IDEA, brief=None, channel=channel, dry_run=True)
    assert res["outcome"] == "ready_for_review", (
        f"non-idea dry-run should complete, got {res['outcome']}"
    )
    # And the artifact really is a stakebake artifact with its own fields.
    rec = json.loads(open(res["artifact"], encoding="utf-8").read())
    assert rec["stage"] == NON_IDEA
    assert "stakes_added" in rec["content"], "stakebake-specific field missing -> wrong shape"
