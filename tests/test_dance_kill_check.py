"""The Dance is a KILL check on the beat stages: if it scores 0, the artifact is
REJECTED even when the rest of the score clears the floor. This is the mechanism
that stops 'and then' beat-piling from sneaking through a floor-based gate.

Hermetic: the gate runs on a DummyLM, no network/keys.
"""

from dspy.utils.dummies import DummyLM

from pipeline import stages
from pipeline.evaluator import Evaluator

SCRIPT_FIELDS = ["hook", "body", "payoff", "cta", "loop_notes"]


def _script_gate_answer(dance_score: int, verdict: str = "PASS") -> dict:
    """A GateScript answer: every non-Dance check full, the Dance (score_7) set to
    dance_score, jargon false. With the Dance full the total is 100; with it 0 the
    rest still totals 85 (well past the floor of 60)."""
    full = {1: 16, 2: 12, 3: 12, 4: 13, 5: 18, 6: 14, 7: 15}
    a = {"reasoning": "t", "verdict": verdict, "failed_checks": "none", "why": "t", "jargon": "false"}
    for k in range(1, 8):
        a[f"score_{k}"] = str(dance_score if k == 7 else full[k])
    return a


def _evaluator_for(stage):
    return Evaluator(stage.gate_sig, stage.weights, stage.penalty_points,
                     stage.verdict_floor, stage.kill_checks)


def test_dance_zero_kills_even_past_the_floor():
    """script is a floor stage (PASS at 60). Dance=0 with everything else full =
    total 85 >= 60, but the Dance is a kill check, so the verdict MUST be REJECT."""
    stage = stages.get_stage("script")
    assert stage.kill_checks == (7,), "script should mark the Dance (criterion 7) as a kill check"
    ev = _evaluator_for(stage)
    ev.set_lm(DummyLM([_script_gate_answer(dance_score=0)]))
    out = ev(content={f: "x" for f in SCRIPT_FIELDS}, criteria="c")
    assert out.verdict == "REJECT", (
        f"Dance=0 must kill the script even though the total ({out.score}) clears the floor"
    )
    assert out.breakdown[7] == 0


def test_dance_full_passes_on_floor_stage():
    """Control: with the Dance satisfied, a full-marks script passes."""
    stage = stages.get_stage("script")
    ev = _evaluator_for(stage)
    ev.set_lm(DummyLM([_script_gate_answer(dance_score=15)]))
    out = ev(content={f: "x" for f in SCRIPT_FIELDS}, criteria="c")
    assert out.verdict == "PASS", f"a clean script (Dance full) should pass; got {out.verdict}"
    assert out.score == 100


def test_all_beat_stages_mark_the_dance_as_kill():
    """Every beat stage carries the Dance as a kill check on its last criterion."""
    expected = {"story": (12,), "script": (7,),
                "script_long": (7,), "script_podcast": (7,), "script_screenplay": (14,)}
    for name, kc in expected.items():
        assert stages.get_stage(name).kill_checks == kc, f"{name} kill_checks should be {kc}"
    # stakebake re-colours existing beats with stakes; the Dance is NOT a kill there.
    assert stages.get_stage("stakebake").kill_checks == (), "stakebake should carry no Dance kill"
