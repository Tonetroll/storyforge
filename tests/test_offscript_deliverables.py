"""TDD coverage for the restructured terminal phase of pipeline/chain.py.

The owner's design change: packaging and description must be built FROM the
finished long-form script (script_long), NOT off the stakebake. New target flow:

  idea -> theme -> story -> stakebake            (spine: promote each, stop at first weak link)
      -> script, script_long, script_screenplay, script_podcast  (all four, off stakebake)
      -> [promote script_long]
      -> packaging, description                  (both built off the promoted script_long)

No real network/LLM call is made: the full-chain test uses dry_run=True (scripted
DummyLM answers that make every stage PASS); the edge-case tests monkeypatch
pipeline.orchestrator.run to control per-stage outcomes. All runs are isolated to
the channel_ws tmp workspace.
"""

import json

import pytest

from pipeline import chain, stages


SCRIPT_FORMATS = ["script", "script_long", "script_screenplay", "script_podcast"]
OFF_SCRIPT = ["packaging", "description"]


# ---------------------------------------------------------------------------
# 1. The stage wiring: packaging + description read script_long, not stakebake.
# ---------------------------------------------------------------------------

def test_packaging_upstream_is_script_long():
    assert stages.PACKAGING.upstream == "script_long"


def test_description_upstream_is_script_long():
    assert stages.DESCRIPTION.upstream == "script_long"


def test_description_keeps_its_gate_and_deep_flags():
    # Only the input source changes; the evaluator wiring is unchanged.
    assert stages.DESCRIPTION.gate_reads_package is True
    assert stages.DESCRIPTION.deep_channel is True


def test_scripts_still_read_stakebake():
    # The four script formats are unchanged: each still reads the accepted stakebake.
    for name in SCRIPT_FORMATS:
        assert stages.get_stage(name).upstream == "stakebake", name


def test_packaging_build_brief_reads_script_content():
    # build_brief must feed the long-form script's content (hook/body/payoff/cta/
    # loop_notes), not stakebake beats. A script_long record carries that content.
    rec = {
        "brief": "BRIEF",
        "content": {"hook": "HOOKLINE", "body": "BODYTEXT",
                    "payoff": "PAYOFFTEXT", "cta": "CTATEXT", "loop_notes": "LOOPTEXT"},
    }
    brief = stages.PACKAGING.build_brief(rec)
    assert "HOOKLINE" in brief and "BODYTEXT" in brief and "PAYOFFTEXT" in brief
    # Keeps the same instructional tail.
    assert "title + thumbnail" in brief


def test_description_build_brief_reads_script_content():
    rec = {
        "brief": "BRIEF",
        "content": {"hook": "HOOKLINE", "body": "BODYTEXT",
                    "payoff": "PAYOFFTEXT", "cta": "CTATEXT", "loop_notes": "LOOPTEXT"},
    }
    brief = stages.DESCRIPTION.build_brief(rec)
    assert "HOOKLINE" in brief and "BODYTEXT" in brief


# ---------------------------------------------------------------------------
# 2. The happy path: a full dry-run chain produces all four scripts + the two
#    off-script deliverables, and packaging/description resolve script_long.
# ---------------------------------------------------------------------------

def test_full_dry_run_produces_all_scripts_and_offscript(channel_ws):
    result = chain.run_chain(brief="a test brief", channel=channel_ws["channel"], dry_run=True)

    assert result["stopped_at"] is None, result
    made = [s["stage"] for s in result["deliverables"]]
    # All four script formats AND packaging AND description were attempted.
    for name in SCRIPT_FORMATS + OFF_SCRIPT:
        assert name in made, f"{name} missing from deliverables: {made}"
    # Clean run -> nothing incomplete.
    assert result["incomplete_deliverables"] == [], result.get("incomplete_deliverables")


def test_full_dry_run_promotes_script_long_and_offscript_built_from_it(channel_ws):
    """packaging + description are built off the PROMOTED script_long, so their
    saved artifacts carry script_long in their assembly (proof of the new source)."""
    paths = channel_ws["paths"]
    result = chain.run_chain(brief="a test brief", channel=channel_ws["channel"], dry_run=True)
    assert result["stopped_at"] is None, result

    # script_long was promoted into accepted/ (only ready artifacts are promotable).
    accepted = list(paths.accepted.glob("*.json"))
    accepted_stages = {json.loads(p.read_text(encoding="utf-8")).get("stage") for p in accepted}
    assert "script_long" in accepted_stages, accepted_stages

    # The packaging + description candidate artifacts resolved script_long: its
    # content rides in their assembly under the "script_long" key.
    def _latest(stage_name):
        recs = [json.loads(p.read_text(encoding="utf-8")) for p in paths.candidates.glob("*.json")]
        recs = [r for r in recs if r.get("stage") == stage_name]
        assert recs, f"no candidate artifact for {stage_name}"
        return max(recs, key=lambda r: (r.get("number", 0), r.get("version", 0)))

    for name in OFF_SCRIPT:
        rec = _latest(name)
        assert "script_long" in (rec.get("assembly") or {}), (
            f"{name} assembly should carry script_long, got {list((rec.get('assembly') or {}).keys())}"
        )


def test_offscript_runs_after_script_long_promoted(channel_ws, monkeypatch):
    """Order guarantee: packaging + description run only AFTER script_long has been
    promoted. We record the orchestrator call order and the promote calls."""
    from pipeline import orchestrator

    events = []

    real_promote = chain._promote

    def _run(stage_name, brief=None, channel=None, scripted=None):
        events.append(("run", stage_name))
        return {"outcome": "ready_for_review", "final_score": 1.0,
                "artifact": f"/fake/{stage_name}.json"}

    def _promote(artifact_path, paths):
        # /fake/<stage>.json -> record which stage got promoted.
        name = artifact_path.split("/")[-1].replace(".json", "")
        events.append(("promote", name))
        return None

    monkeypatch.setattr(orchestrator, "run", _run)
    monkeypatch.setattr(chain, "_promote", _promote)

    chain.run_chain(brief="x", channel=channel_ws["channel"])

    promote_long = events.index(("promote", "script_long"))
    run_packaging = events.index(("run", "packaging"))
    run_description = events.index(("run", "description"))
    assert promote_long < run_packaging, events
    assert promote_long < run_description, events


# ---------------------------------------------------------------------------
# 3. The edge case: script_long did NOT reach ready_for_review -> packaging and
#    description are SKIPPED (cannot be promoted -> cannot be built), reported in
#    incomplete_deliverables with a skip reason, and the chain does not raise.
# ---------------------------------------------------------------------------

def _orchestrator_stub(parked_stage=None):
    def _run(stage_name, brief=None, channel=None, scripted=None):
        outcome = "parked" if stage_name == parked_stage else "ready_for_review"
        return {"outcome": outcome, "final_score": 1.0, "artifact": f"/fake/{stage_name}.json"}
    return _run


def test_script_long_parked_skips_offscript(channel_ws, monkeypatch):
    from pipeline import orchestrator

    monkeypatch.setattr(orchestrator, "run", _orchestrator_stub(parked_stage="script_long"))
    monkeypatch.setattr(chain, "_promote", lambda artifact_path, paths: None)

    result = chain.run_chain(brief="x", channel=channel_ws["channel"])

    # The chain did not crash and the spine finished.
    assert result["stopped_at"] is None, result
    # packaging + description were SKIPPED, not run as deliverables.
    made = [s["stage"] for s in result["deliverables"]]
    assert "packaging" not in made and "description" not in made, made
    # ...but the four scripts were still attempted (script_long is just parked).
    for name in SCRIPT_FORMATS:
        assert name in made, made
    # Both off-script deliverables are honestly reported as incomplete.
    assert "packaging" in result["incomplete_deliverables"]
    assert "description" in result["incomplete_deliverables"]
    # A skip reason is recorded naming the long-form script.
    reason = result.get("skipped_reason", "")
    assert "script" in reason.lower() and "ready_for_review" in reason, reason


def test_script_long_parked_does_not_raise_orchestrator_error(channel_ws, monkeypatch):
    """If packaging/description were (wrongly) attempted with no accepted script_long,
    orchestrator._resolve_upstream would raise 'No accepted script_long'. The chain
    must detect the parked state FIRST and never make that call."""
    from pipeline import orchestrator

    calls = []

    def _run(stage_name, brief=None, channel=None, scripted=None):
        calls.append(stage_name)
        if stage_name == "script_long":
            return {"outcome": "parked", "final_score": 0.0, "artifact": f"/fake/{stage_name}.json"}
        if stage_name in OFF_SCRIPT:
            # Simulate the real orchestrator refusing to build with no upstream.
            raise RuntimeError(f"No accepted 'script_long' artifact to feed stage '{stage_name}'.")
        return {"outcome": "ready_for_review", "final_score": 1.0, "artifact": f"/fake/{stage_name}.json"}

    monkeypatch.setattr(orchestrator, "run", _run)
    monkeypatch.setattr(chain, "_promote", lambda artifact_path, paths: None)

    # Must not raise.
    result = chain.run_chain(brief="x", channel=channel_ws["channel"])
    # Proof the chain never even called orchestrator.run for the off-script stages.
    assert "packaging" not in calls and "description" not in calls, calls
    assert result["stopped_at"] is None
