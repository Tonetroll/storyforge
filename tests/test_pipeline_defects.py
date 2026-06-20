"""TDD coverage for three verified defects in pipeline/chain.py.

No real network/LLM call is made: we monkeypatch chain.run_chain (bugs 1 & 2)
and pipeline.orchestrator.run (bug 3) to controlled stubs so we assert chain
behavior without models. Seed files are written into the isolated channel_ws's
paths.seeds.

Bug 1: a JSON object whose "brief" is null/missing/empty must be SKIPPED,
       never turned into the literal string "None" or any placeholder.
Bug 2: a line that starts with "{" but is not valid JSON must NOT be passed
       through as raw text -- it must be reported (warning) and SKIPPED, and
       the queue must CONTINUE with the remaining seeds.
Bug 3 (C8): run_chain must report deliverables that did not reach
       "ready_for_review" via a new "incomplete_deliverables" key.
"""

import pytest

from pipeline import chain


# ---------------------------------------------------------------------------
# Bug 1 & 2 -- unit tests on _brief_from_line directly.
# ---------------------------------------------------------------------------

def test_brief_from_line_plain_text_passes_through():
    assert chain._brief_from_line("a plain idea") == "a plain idea"


def test_brief_from_line_valid_json_brief():
    assert chain._brief_from_line('{"brief": "hello"}') == "hello"


def test_brief_from_line_null_brief_is_empty():
    # Bug 1: {"brief": null} must NOT become the literal "None".
    out = chain._brief_from_line('{"brief": null}')
    assert out == "", f"null brief should be empty, got {out!r}"
    assert out != "None"


def test_brief_from_line_missing_brief_is_empty():
    out = chain._brief_from_line('{"note": "no brief key"}')
    assert out == "", f"missing brief should be empty, got {out!r}"


def test_brief_from_line_whitespace_brief_is_empty():
    out = chain._brief_from_line('{"brief": "   "}')
    assert out == "", f"whitespace brief should be empty, got {out!r}"


def test_brief_from_line_malformed_json_raises():
    # Bug 2: an unclosed JSON object must NOT be returned as raw text.
    with pytest.raises(ValueError):
        chain._brief_from_line('{"brief": "x"')


# ---------------------------------------------------------------------------
# Bug 1 & 2 -- integration through run_channel with a recording stub.
# ---------------------------------------------------------------------------

def _record_run_chain(recorder):
    def _stub(brief, channel=None, dry_run=False, deliverables=None):
        recorder.append(brief)
        return {"brief": brief, "channel": channel, "stopped_at": None}
    return _stub


def test_run_channel_skips_null_empty_and_malformed(channel_ws, monkeypatch, capsys):
    paths = channel_ws["paths"]
    seeds = [
        "first plain idea",
        '{"brief": "valid json brief"}',
        '{"brief": null}',
        '{"note": "missing brief"}',
        '{"brief": "   "}',
        '{"brief": "broken',          # malformed JSON -> must warn + skip
        "idea after the broken line",  # must STILL be processed
    ]
    paths.seeds.write_text("\n".join(seeds) + "\n", encoding="utf-8")

    seen = []
    monkeypatch.setattr(chain, "run_chain", _record_run_chain(seen))

    chain.run_channel(channel=channel_ws["channel"])

    # Only the two real briefs + the line after the broken one should run.
    assert seen == ["first plain idea", "valid json brief", "idea after the broken line"], seen
    assert "None" not in seen

    # Bug 2: the malformed line must be reported visibly and name the line.
    out = capsys.readouterr().out
    assert "broken" in out, f"warning should name the offending line; got: {out!r}"


def test_run_channel_one_bad_line_does_not_kill_queue(channel_ws, monkeypatch, capsys):
    paths = channel_ws["paths"]
    seeds = ['{"oops', "good one", '{"bad', "another good one"]
    paths.seeds.write_text("\n".join(seeds) + "\n", encoding="utf-8")

    seen = []
    monkeypatch.setattr(chain, "run_chain", _record_run_chain(seen))

    chain.run_channel(channel=channel_ws["channel"])
    assert seen == ["good one", "another good one"], seen


# ---------------------------------------------------------------------------
# Bug 3 (C8) -- incomplete_deliverables in run_chain's return dict.
# ---------------------------------------------------------------------------

def _orchestrator_stub(parked_stage=None):
    """Return a fake orchestrator.run: every stage is ready_for_review except
    `parked_stage`, which returns outcome='parked'."""
    def _run(stage_name, brief=None, channel=None, scripted=None):
        outcome = "parked" if stage_name == parked_stage else "ready_for_review"
        return {
            "outcome": outcome,
            "final_score": 1.0,
            "artifact": f"/fake/{stage_name}.json",
        }
    return _run


# The full set of deliverables the chain now attempts: the four script formats
# (off the accepted stakebake) plus packaging + description (off the promoted
# script_long). When script_long itself reaches ready_for_review, all are attempted.
ALL_DELIVERABLES = chain.SCRIPT_FORMATS + chain.OFF_SCRIPT


def test_run_chain_reports_parked_deliverable(channel_ws, monkeypatch):
    from pipeline import orchestrator

    # Park packaging (an off-script deliverable). script_long still passes, so
    # packaging is still ATTEMPTED -- and parks -- so it lands in incomplete.
    monkeypatch.setattr(orchestrator, "run", _orchestrator_stub(parked_stage="packaging"))
    # _promote reads/writes real artifacts for the spine; stub it out.
    monkeypatch.setattr(chain, "_promote", lambda artifact_path, paths: None)

    result = chain.run_chain(brief="x", channel=channel_ws["channel"])

    # All deliverables attempted (none aborted): four scripts + packaging + description.
    attempted = [s["stage"] for s in result["deliverables"]]
    assert attempted == ALL_DELIVERABLES, attempted
    # The parked one is honestly reported.
    assert result["incomplete_deliverables"] == ["packaging"], result.get("incomplete_deliverables")
    # The spine still finished cleanly.
    assert result["stopped_at"] is None


def test_run_chain_clean_run_has_empty_incomplete(channel_ws, monkeypatch):
    from pipeline import orchestrator

    monkeypatch.setattr(orchestrator, "run", _orchestrator_stub(parked_stage=None))
    monkeypatch.setattr(chain, "_promote", lambda artifact_path, paths: None)

    result = chain.run_chain(brief="x", channel=channel_ws["channel"])

    assert result["incomplete_deliverables"] == [], result.get("incomplete_deliverables")
    attempted = [s["stage"] for s in result["deliverables"]]
    assert attempted == ALL_DELIVERABLES, attempted
