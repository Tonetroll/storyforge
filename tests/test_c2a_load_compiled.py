"""C2a: a compiled (optimized) generator must be LOADED at runtime.

The defect: learn.py saves an optimized generator to
paths.compiled / f"{stage.name}_generator.json" (state-only), but
orchestrator.build_modules always built a FRESH Generator(stage.gen_sig) and
NEVER loaded the compiled state. Learning therefore had zero effect on
production.

Required behavior:
  - LIVE mode only (dry_run is False AND scripted is None): if `paths` is given
    and the compiled file exists, load it into the generator so bootstrapped
    demos reach production.
  - After loading, the generator's LM must still be set (dspy load can wipe the
    per-predictor .lm via reset_copy()), so build_modules must re-affirm it.
  - dry_run and scripted modes must NEVER load compiled (they use DummyLM and the
    demos would be meaningless/harmful).

These tests are hermetic: orchestrator.dspy.LM is monkeypatched to a DummyLM
factory so the LIVE branch never constructs a real client / needs an API key.
"""

import dspy
from dspy.utils.dummies import DummyLM

import config
from pipeline import orchestrator, stages
from pipeline.generator import Generator


# --- helpers ----------------------------------------------------------------
PLANTED_ONE_LINER = "PLANTED-DEMO-ONE-LINER"


def _demo_value(demo, field):
    """A loaded demo may be a dict or a dspy.Example -- read either."""
    if isinstance(demo, dict):
        return demo.get(field)
    if hasattr(demo, "get"):
        try:
            return demo.get(field)
        except Exception:
            pass
    return getattr(demo, field, None)


def _write_compiled(stage, paths):
    """Build a valid compiled generator file with a planted demo and save it
    (state-only) to paths.compiled / <stage>_generator.json -- exactly where
    learn.py writes it. Saved with NO LM set so dump_state stays hermetic."""
    g = Generator(stage.gen_sig)
    demo = dspy.Example(
        brief="planted brief", standard="planted standard",
        one_liner=PLANTED_ONE_LINER, resolution="R",
        reaction_1="WTF", reaction_2="Aah", viewer_action="Reflect", topic="planted topic",
    )
    g.generate.predict.demos = [demo]
    paths.compiled.mkdir(parents=True, exist_ok=True)
    out = paths.compiled / f"{stage.name}_generator.json"
    g.save(str(out), save_program=False)
    return out


def _stub_dspy_lm(monkeypatch):
    """Make orchestrator's dspy.LM(...) return a DummyLM with a .model so the
    LIVE branch in build_modules never constructs a real network client."""
    counter = {"n": 0}

    def _factory(**kwargs):
        counter["n"] += 1
        lm = DummyLM([{"reasoning": "r", "one_liner": "x", "resolution": "x",
                       "reaction_1": "WTF", "reaction_2": "Aah",
                       "viewer_action": "Reflect", "topic": "t"}] * 5)
        # distinct model strings so assert_separation passes (gen vs eval)
        lm.model = f"stub/lm-{counter['n']}"
        return lm

    monkeypatch.setattr(orchestrator.dspy, "LM", _factory)


# --- tests ------------------------------------------------------------------
def test_live_loads_compiled_demo_and_keeps_lm(channel_ws, monkeypatch):
    """With a compiled file present, LIVE build_modules loads it: the planted
    demo is on the generator's predictor AND get_lm() is still set."""
    paths = channel_ws["paths"]
    stage = stages.get_stage("idea")
    _write_compiled(stage, paths)
    _stub_dspy_lm(monkeypatch)

    generator, *_ = orchestrator.build_modules(
        stage, dry_run=False, scripted=None, paths=paths
    )

    demos = generator.generate.predict.demos
    assert demos, "compiled demo was not loaded onto the generator"
    assert any(_demo_value(d, "one_liner") == PLANTED_ONE_LINER for d in demos), (
        f"planted demo not present after load; got {[_demo_value(d, 'one_liner') for d in demos]}"
    )
    # CRITICAL: load must not leave the generator un-callable -- LM re-affirmed.
    assert generator.get_lm() is not None, "generator LM was wiped by load (not re-affirmed)"


def test_live_no_compiled_file_is_fresh(channel_ws, monkeypatch):
    """No compiled file -> build_modules does not error and the generator has no
    bootstrapped demos (a fresh student)."""
    paths = channel_ws["paths"]
    stage = stages.get_stage("idea")
    # ensure no compiled file exists
    assert not (paths.compiled / f"{stage.name}_generator.json").exists()
    _stub_dspy_lm(monkeypatch)

    generator, *_ = orchestrator.build_modules(
        stage, dry_run=False, scripted=None, paths=paths
    )
    assert not generator.generate.predict.demos, "fresh generator should have no demos"
    assert generator.get_lm() is not None


def test_dry_run_never_loads_compiled(channel_ws):
    """dry_run must NOT load compiled even when the file exists (DummyLM path)."""
    paths = channel_ws["paths"]
    stage = stages.get_stage("idea")
    _write_compiled(stage, paths)   # file present...

    generator, *_ = orchestrator.build_modules(
        stage, dry_run=True, scripted=None, paths=paths
    )
    demos = generator.generate.predict.demos
    assert not any(_demo_value(d, "one_liner") == PLANTED_ONE_LINER for d in demos), (
        "dry_run wrongly loaded the compiled demo"
    )


def test_scripted_never_loads_compiled(channel_ws):
    """scripted/manual must NOT load compiled even when the file exists."""
    paths = channel_ws["paths"]
    stage = stages.get_stage("idea")
    _write_compiled(stage, paths)   # file present...

    scripted = {
        "gen_answers": [{"reasoning": "r", "one_liner": "x", "resolution": "x",
                         "reaction_1": "WTF", "reaction_2": "Aah",
                         "viewer_action": "Reflect", "topic": "t"}],
        "eval_answers": [{"reasoning": "r", "verdict": "PASS", "failed_checks": "none",
                          "why": "ok", "score_1": "25", "score_2": "25", "score_3": "20",
                          "score_4": "10", "score_5": "10", "score_6": "10"}],
    }
    generator, *_ = orchestrator.build_modules(
        stage, dry_run=False, scripted=scripted, paths=paths
    )
    demos = generator.generate.predict.demos
    assert not any(_demo_value(d, "one_liner") == PLANTED_ONE_LINER for d in demos), (
        "scripted run wrongly loaded the compiled demo"
    )
