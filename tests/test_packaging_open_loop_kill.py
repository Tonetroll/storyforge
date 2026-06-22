"""The open loop is a KILL check on packaging: if the title/thumbnail resolves the
loop (Criterion 9 scores 0), the package is REJECTED even when the rest of the
score clears the floor. Curiosity is the whole point of the package -- giving the
answer away kills the click, however pretty the thumbnail.

Hermetic: the gate runs on a DummyLM, no network/keys.
"""

from dspy.utils.dummies import DummyLM

from pipeline import stages
from pipeline.evaluator import Evaluator

PKG_FIELDS = ["title", "thumbnail_concept", "thumbnail_prompt"]


def _pkg_gate_answer(loop_score: int, verdict: str = "PASS") -> dict:
    """A GatePackaging answer: every non-loop check full, the open-loop (score_9) set
    to loop_score. With the loop full the total is 100; with it 0 the rest still
    totals 89 (well past the floor of 60)."""
    w = stages.get_stage("packaging").weights
    a = {"reasoning": "t", "verdict": verdict, "failed_checks": "none", "why": "t"}
    for k in w:
        a[f"score_{k}"] = str(loop_score if k == 9 else w[k])
    return a


def _evaluator_for(stage):
    return Evaluator(stage.gate_sig, stage.weights, stage.penalty_points,
                     stage.verdict_floor, stage.kill_checks)


def test_packaging_marks_open_loop_as_kill():
    """The open loop (criterion 9) is the packaging kill check."""
    assert stages.get_stage("packaging").kill_checks == (9,), \
        "packaging should mark the open loop (criterion 9) as a kill check"


def test_resolved_loop_kills_even_past_the_floor():
    """packaging is a floor stage (PASS at 60). Loop=0 with everything else full =
    total 89 >= 60, but the loop is a kill check, so the verdict MUST be REJECT."""
    stage = stages.get_stage("packaging")
    ev = _evaluator_for(stage)
    ev.set_lm(DummyLM([_pkg_gate_answer(loop_score=0)]))
    out = ev(content={f: "x" for f in PKG_FIELDS}, criteria="c")
    assert out.verdict == "REJECT", (
        f"a resolved loop must kill the package even though the total ({out.score}) clears the floor"
    )
    assert out.breakdown[9] == 0


def test_open_loop_passes_on_floor_stage():
    """Control: with the loop left open, a full-marks package passes."""
    stage = stages.get_stage("packaging")
    ev = _evaluator_for(stage)
    ev.set_lm(DummyLM([_pkg_gate_answer(loop_score=stage.weights[9])]))
    out = ev(content={f: "x" for f in PKG_FIELDS}, criteria="c")
    assert out.verdict == "PASS", f"a clean package (loop open) should pass; got {out.verdict}"
    assert out.score == 100
