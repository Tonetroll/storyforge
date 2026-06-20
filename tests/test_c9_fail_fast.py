"""C9: in LIVE mode, fail fast (before any LM call) when a required stage
standard file is missing OR a NAMED channel has no profile.md.

The defect: _read_standard returned a PLACEHOLDER string for a missing standard,
and _load_channel returned ("","") for a NAMED channel whose profile.md is
missing. A LIVE run then silently proceeded to make paid LLM calls with no real
standard/profile -- a known costly failure.

Required behavior: raise a clear error in LIVE mode only (dry_run is False AND
scripted is None) BEFORE building modules. Preserve current behavior for
dry_run, scripted/manual runs, and the legitimate "no channel" (channel falsy)
case -- those must NOT raise.

LIVE-mode tests must raise during standard/profile loading and so must NOT need
API keys -- they never reach build_modules.
"""

import pytest

import config
from pipeline import orchestrator
from tests.conftest import make_scripted, _gen_answer, _eval_answer
from pipeline import stages


# ---------------------------------------------------------------------------
# LIVE mode: must raise (red before the fix).
# ---------------------------------------------------------------------------
def test_live_missing_channel_profile_raises(channel_ws, monkeypatch):
    """A named channel that does not exist -> raise naming the missing profile,
    before any LM is built (no API keys required)."""
    # Sentinel: if build_modules is reached, the test should fail loudly rather
    # than try to construct real LMs.
    monkeypatch.setattr(orchestrator, "build_modules",
                        lambda *a, **k: pytest.fail("build_modules reached -- guard did not fail fast"))

    with pytest.raises((FileNotFoundError, RuntimeError)) as exc:
        orchestrator.run(stage_name="idea", channel="does-not-exist-xyz",
                         dry_run=False, scripted=None)
    msg = str(exc.value).lower()
    assert "profile" in msg, f"error should name the missing profile, got: {exc.value}"


def test_live_missing_standard_raises(channel_ws, monkeypatch, tmp_path):
    """A missing stage standard file in live mode -> raise before LM construction.
    Point STANDARDS_DIR at an empty tmp dir so every standard is absent."""
    empty_standards = tmp_path / "empty_standards"
    empty_standards.mkdir()
    monkeypatch.setattr(config, "STANDARDS_DIR", empty_standards)
    monkeypatch.setattr(orchestrator, "build_modules",
                        lambda *a, **k: pytest.fail("build_modules reached -- guard did not fail fast"))

    # Use the scaffolded channel (its profile exists) so the failure is unambiguously
    # the missing STANDARD, not the profile.
    with pytest.raises((FileNotFoundError, RuntimeError)) as exc:
        orchestrator.run(stage_name="idea", channel=channel_ws["channel"],
                         dry_run=False, scripted=None)
    msg = str(exc.value).lower()
    assert "standard" in msg, f"error should name the missing standard, got: {exc.value}"


# ---------------------------------------------------------------------------
# NON-regression: these must NOT raise (use offline paths, no real LMs).
# ---------------------------------------------------------------------------
def test_dry_run_missing_profile_does_not_raise(channel_ws):
    """dry_run with a missing profile must still run offline (no raise)."""
    res = orchestrator.run(stage_name="idea", brief="x", channel="no-such-channel",
                           dry_run=True, scripted=None)
    assert res.get("run_id") is not None


def test_scripted_missing_profile_does_not_raise(channel_ws):
    """A scripted/manual run with a missing profile must still run offline."""
    stage = stages.get_stage("idea")
    scripted = make_scripted(stage, eval_answers=[
        _eval_answer(stage, {1: 25, 2: 25, 3: 20, 4: 9, 5: 9, 6: 7}, verdict="PASS"),
        _eval_answer(stage, {1: 25, 2: 25, 3: 20, 4: 9, 5: 9, 6: 7}, verdict="PASS"),
    ])
    res = orchestrator.run(stage_name="idea", brief="x", channel="no-such-channel",
                           dry_run=False, scripted=scripted)
    assert res["outcome"] == "ready_for_review"


def test_no_channel_live_does_not_raise_on_profile(channel_ws, monkeypatch):
    """channel=None is the legitimate sandbox case: the missing-profile guard must
    NOT fire. (We still stub build_modules so no real LM is constructed; the point
    is the profile guard does not raise for a falsy channel.)"""
    sentinel = {}

    def _fake_build(stage, dry_run=False, scripted=None):
        sentinel["built"] = True
        raise RuntimeError("STOP-AFTER-GUARD")  # prove we got PAST the profile guard

    monkeypatch.setattr(orchestrator, "build_modules", _fake_build)
    with pytest.raises(RuntimeError) as exc:
        orchestrator.run(stage_name="idea", brief="x", channel=None,
                         dry_run=False, scripted=None)
    # It must reach build_modules (i.e. pass the profile guard), not raise on profile.
    assert sentinel.get("built") is True
    assert "STOP-AFTER-GUARD" in str(exc.value)
