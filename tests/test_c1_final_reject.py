"""C1: a FINAL re-evaluation that REJECTs must NOT be promoted to ready_for_review.

The defect: the finalize block computed final_gate = reevaluator(...) and then
UNCONDITIONALLY saved status="ready_for_review" / outcome="ready_for_review"
without checking final_gate.verdict. Because the evaluator forces score=0 on a
REJECT (all-pass mode), a final REJECT landed in candidates/ as ready_for_review
with score 0. Required: a final REJECT must be PARKED instead.

All runs here are scripted (DummyLM) -- no network, no API keys.
"""

import json

import config
from pipeline import orchestrator, stages
from tests.conftest import make_scripted, _eval_answer, _gen_answer


def _artifacts(dest_dir):
    return list(dest_dir.glob("*.json")) if dest_dir.exists() else []


def test_final_reject_is_parked_not_promoted(channel_ws):
    """Reach target on the first PASS, then have the FINAL re-eval REJECT.
    The run must PARK, not promote."""
    channel = channel_ws["channel"]
    paths = channel_ws["paths"]
    stage = stages.get_stage("idea")

    # gate PASS at exactly TARGET_SCORE (all checks nonzero) so the iteration loop
    # does not run; then the FINAL re-eval REJECTs. Build pass_scores from the stage's
    # full weights and dock (SCORE_SCALE - TARGET_SCORE) from check 1, so it sums to
    # TARGET_SCORE at any target and every check stays nonzero (a clean all-pass PASS).
    pass_scores = dict(stage.weights)
    pass_scores[1] = stage.weights[1] - (config.SCORE_SCALE - config.TARGET_SCORE)
    assert sum(pass_scores.values()) == config.TARGET_SCORE
    assert all(v > 0 for v in pass_scores.values()), "docked check must stay > 0 for a clean PASS"
    eval_answers = [
        _eval_answer(stage, pass_scores, verdict="PASS"),
        _eval_answer(stage, {k: 0 for k in stage.weights}, verdict="REJECT",
                     failed_checks="1: regressed on final re-eval"),
    ]
    scripted = make_scripted(stage, eval_answers=eval_answers)

    res = orchestrator.run(stage_name="idea", brief="a test brief", channel=channel,
                           scripted=scripted)

    assert res["outcome"] == "parked", f"expected parked, got {res['outcome']}"
    # The promoted artifact must NOT exist in candidates as ready_for_review.
    ready = [p for p in _artifacts(paths.candidates)
             if json.loads(p.read_text(encoding="utf-8"))["status"] == "ready_for_review"]
    assert not ready, f"a final-REJECT artifact was wrongly saved ready_for_review: {ready}"
    # It must land in parked/ as a parked artifact.
    parked = [json.loads(p.read_text(encoding="utf-8")) for p in _artifacts(paths.parked)]
    assert parked, "no artifact landed in parked/"
    assert any(r["status"] == "parked" for r in parked)


def test_final_pass_still_promotes(channel_ws):
    """Happy path: final re-eval PASSes at/above target -> ready_for_review."""
    channel = channel_ws["channel"]
    paths = channel_ws["paths"]
    stage = stages.get_stage("idea")

    pass_scores = dict(stage.weights)
    pass_scores[1] = stage.weights[1] - (config.SCORE_SCALE - config.TARGET_SCORE)
    assert sum(pass_scores.values()) == config.TARGET_SCORE
    eval_answers = [
        _eval_answer(stage, pass_scores, verdict="PASS"),   # gate
        _eval_answer(stage, pass_scores, verdict="PASS"),   # final re-eval
    ]
    scripted = make_scripted(stage, eval_answers=eval_answers)

    res = orchestrator.run(stage_name="idea", brief="a test brief", channel=channel,
                           scripted=scripted)

    assert res["outcome"] == "ready_for_review", f"got {res['outcome']}"
    assert res["final_score"] == config.TARGET_SCORE
    ready = [json.loads(p.read_text(encoding="utf-8")) for p in _artifacts(paths.candidates)]
    assert any(r["status"] == "ready_for_review" for r in ready)
    assert not _artifacts(paths.parked), "happy path must not park anything"
