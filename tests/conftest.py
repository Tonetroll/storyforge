"""Shared pytest fixtures + helpers for the pipeline test harness.

Every test runs in an ISOLATED channel workspace: config.CHANNELS_DIR is
monkeypatched to a tmp dir so a test never reads or writes a real channel under
channels/. No test ever makes a real network/LLM call -- runs go through the
offline paths only (dry_run=True or scripted=... , both DummyLM-backed).
"""

import sys
from pathlib import Path

import pytest

# Make the project root importable (config.py, pipeline/ live there) regardless
# of where pytest is invoked from.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config  # noqa: E402


@pytest.fixture
def channel_ws(tmp_path, monkeypatch):
    """An isolated channel workspace rooted at tmp_path.

    Points config.CHANNELS_DIR at a fresh tmp dir, scaffolds a minimal channel
    (profile.md + seeds/) so a named-channel live path has a real profile, and
    returns the channel name plus its resolved ChannelPaths. Verifies that
    config.paths_for(...) now resolves UNDER the tmp dir (proves the isolation).
    """
    channels_dir = tmp_path / "channels"
    channels_dir.mkdir()
    monkeypatch.setattr(config, "CHANNELS_DIR", channels_dir)

    channel = "test-channel"
    root = channels_dir / channel
    (root / "seeds").mkdir(parents=True)
    (root / "profile.md").write_text(
        "# Test channel\n"
        "<!-- SPINE:START -->\n"
        "For people who want a smoke-test profile. Voice: plain.\n"
        "<!-- SPINE:END -->\n"
        "Full profile body for the deep stages.\n",
        encoding="utf-8",
    )
    (root / "seeds" / "briefs.jsonl").write_text("a test brief\n", encoding="utf-8")

    paths = config.paths_for(channel)
    # The isolation guarantee: everything resolves under tmp_path, not the repo.
    assert str(paths.root).startswith(str(tmp_path)), (
        f"paths.root {paths.root} did not resolve under tmp dir {tmp_path}"
    )
    return {"channel": channel, "paths": paths, "channels_dir": channels_dir, "root": root}


# ---------------------------------------------------------------------------
# Helpers to script DummyLM gate answers for a single stage run.
# ---------------------------------------------------------------------------
def _gen_answer(stage, i: int = 1) -> dict:
    """One generator answer shaped to the stage's generator signature output
    fields (mirrors chain._scripted_for so the WIRING is identical)."""
    gen = {"reasoning": "test"}
    for name in stage.gen_sig.output_fields:
        gen[name] = f"test {stage.name}" if name == stage.topic_field else f"[test {stage.name}:{name}]"
    return gen


def _eval_answer(stage, scores: dict, verdict: str = "PASS",
                 failed_checks: str = "none", jargon: str = "false") -> dict:
    """One evaluator/reevaluator answer for the stage's gate signature.

    `scores` is {criterion_number: raw_score_str_or_int}; any criterion not
    given defaults to its full weight (a clean PASS). Set a criterion to 0 to
    force the all-pass evaluator to REJECT, or lower the total under the floor
    for a hybrid stage.
    """
    ev = {"reasoning": "test"}
    for name in stage.gate_sig.output_fields:
        if name == "verdict":
            ev[name] = verdict
        elif name == "failed_checks":
            ev[name] = failed_checks
        elif name == "why":
            ev[name] = "test"
        elif name == "jargon":
            ev[name] = jargon
        elif name.startswith("score_"):
            k = int(name.split("_")[1])
            ev[name] = str(scores.get(k, stage.weights.get(k, 0)))
        else:
            ev[name] = "test"
    return ev


def make_scripted(stage, *, gen_answers=None, eval_answers):
    """Build the scripted={...} dict orchestrator.build_modules consumes.

    gen_answers defaults to MAX_GEN_ATTEMPTS identical clean generations.
    eval_answers is the exact ORDERED sequence of gate verdicts/scores the run
    will consume: [gate, iter1, iter2, ..., final]. This is what lets a test
    force the iteration loop to PASS to target but the FINAL re-eval to REJECT.
    """
    gen_answers = gen_answers or [_gen_answer(stage)] * config.MAX_GEN_ATTEMPTS
    return {"gen_answers": gen_answers, "eval_answers": eval_answers}
