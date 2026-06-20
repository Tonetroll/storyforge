"""C2b: optimization must grade demos with the SAME gate as runtime.

The defect: learn.compile_generator built `Evaluator(stage.gate_sig, stage.weights)`
-- omitting penalty_points and verdict_floor -- so during BootstrapFewShot the
gate ran the all-pass branch with NO penalty, while runtime
(orchestrator.build_modules) builds the full hybrid gate
`Evaluator(gate_sig, weights, penalty_points, verdict_floor)`. Training selected
demos under different rules than production grading.

Required: learn.py must construct the evaluator with the stage's FULL gate config,
identical to runtime.

We use the `stakebake` stage on purpose: it has penalty_points=15 and
verdict_floor=60, so the missing args are observable (idea has 0 / None and would
hide the bug). Hermetic: dry_run=True (DummyLM), Evaluator is replaced by a
capture-shim subclass that records its constructor args.
"""

import json

import config
from pipeline import learn, stages


def test_compile_builds_evaluator_with_full_gate_config(channel_ws, monkeypatch):
    channel = channel_ws["channel"]
    paths = channel_ws["paths"]
    stage = stages.get_stage("stakebake")

    captured = {}
    RealEvaluator = learn.Evaluator

    class CaptureEvaluator(RealEvaluator):
        def __init__(self, *args, **kwargs):
            captured["args"] = args
            captured["kwargs"] = kwargs
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(learn, "Evaluator", CaptureEvaluator)

    # Non-empty trainset for this stage so compile proceeds past the early return.
    paths.memory.mkdir(parents=True, exist_ok=True)
    content = {f: f"[{f}]" for f in stage.content_fields}
    row = {"stage": stage.name, "brief": "a test brief", "content": content}
    paths.trainset_file.write_text(json.dumps(row) + "\n", encoding="utf-8")

    out = learn.compile_generator(stage_name="stakebake", channel=channel, dry_run=True)

    # The evaluator must be constructed identically to runtime:
    # (gate_sig, weights, penalty_points, verdict_floor).
    pos = list(captured["args"]) + [
        captured["kwargs"].get(k) for k in ("gate_sig", "weights", "penalty_points", "verdict_floor")
        if k in captured["kwargs"]
    ]
    # Normalize to four ordered values regardless of positional/keyword mix.
    def _arg(idx, name):
        if len(captured["args"]) > idx:
            return captured["args"][idx]
        return captured["kwargs"].get(name)

    assert _arg(0, "gate_sig") is stage.gate_sig
    assert _arg(1, "weights") == stage.weights
    assert _arg(2, "penalty_points") == stage.penalty_points == 15, (
        f"penalty_points not threaded; got {_arg(2, 'penalty_points')}"
    )
    assert _arg(3, "verdict_floor") == stage.verdict_floor == 60, (
        f"verdict_floor not threaded; got {_arg(3, 'verdict_floor')}"
    )

    # And the compiled file was written to ws_paths.compiled (dry_run completes green).
    assert out is not None, "compile returned None -- it did not finish"
    expected = paths.compiled / f"{stage.name}_generator.json"
    assert expected.exists(), f"compiled file not written to {expected}"
