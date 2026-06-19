"""Central configuration for the DSPy idea pipeline.

Everything tunable lives here: the project-name token, which LLM runs which
stage, the scoring thresholds, and all filesystem paths. Nothing in this folder
reaches outside it.
"""

from dataclasses import dataclass
from pathlib import Path

# ---------------------------------------------------------------------------
# Identity
# ---------------------------------------------------------------------------
# PROJECT_NAME is the token that prefixes every artifact filename
# (PROJECTNAME_MODULE_NNNN_vVV_status.json). Named from the CORE of the idea:
# this pipeline gates STORIES (information is not a story). The gate assigns a
# story id "ST-####" on PASS, derived from the asset number.
PROJECT_NAME = "STORY"

# Default artifact module/type token. Extensible later (e.g. "HOOK", "TITLE").
DEFAULT_MODULE = "IDEA"

# ---------------------------------------------------------------------------
# LLM assignments  --  THE #1 RULE: the evaluator is a DIFFERENT PROVIDER from
# the generator/iterator, so it cannot inflate its own work. Two API keys.
# (model string, temperature, max_tokens)
# ---------------------------------------------------------------------------
GENERATOR_LM   = {"model": "anthropic/claude-opus-4-8", "temperature": 0.9, "max_tokens": 4000}
ITERATOR_LM    = {"model": "anthropic/claude-opus-4-8", "temperature": 0.7, "max_tokens": 4000}
EVALUATOR_LM   = {"model": "openai/gpt-4o",             "temperature": 0.0, "max_tokens": 1500}
REEVALUATOR_LM = {"model": "openai/gpt-4o",             "temperature": 0.0, "max_tokens": 1500}

# ---------------------------------------------------------------------------
# Loop / scoring policy
# ---------------------------------------------------------------------------
SCORE_SCALE      = 100   # scores are integers 0..100 (applied to ideas that PASS the gate)
TARGET_SCORE     = 95    # iterate any passing idea scoring BELOW this (set 100 to always iterate to the cap)
MAX_ITER         = 3     # max iteration attempts; if still below target after these, the idea is PARKED
MAX_GEN_ATTEMPTS = 5     # gate: regenerate a NEW idea up to this many times until one PASSES

# Per-criterion weights + labels now live PER STAGE in pipeline/stages.py
# (each stage defines its own checks; weights must sum to SCORE_SCALE).

# ---------------------------------------------------------------------------
# Paths (all relative to this folder -- never outside it)
# ---------------------------------------------------------------------------
# SHARED across every channel: the engine reads these once. The craft standards
# are the same bar for all channels; only the audience (a channel's profile) and
# its data differ.
BASE_DIR        = Path(__file__).resolve().parent
RULES_DIR       = BASE_DIR / "rules"
STANDARDS_DIR   = RULES_DIR / "standards"
CHANNELS_DIR    = BASE_DIR / "channels"   # one self-contained workspace per channel
INSTRUCTIONS_DIR = BASE_DIR / "instructions"
EXAMPLES_DIR    = BASE_DIR / "examples"


# PER-CHANNEL: each channel is its own production line under channels/<name>/.
# paths_for(name) resolves the whole workspace; the engine threads it through a run.
@dataclass
class ChannelPaths:
    root: Path
    profile: Path
    seeds: Path
    candidates: Path
    accepted: Path
    rejected: Path
    archived: Path
    parked: Path
    logs: Path
    metrics_file: Path
    review_file: Path
    memory: Path
    trainset_file: Path
    compiled: Path
    run_index_file: Path

    def output_dirs(self):
        return [self.candidates, self.accepted, self.rejected, self.archived, self.parked]


def paths_for(channel: str) -> ChannelPaths:
    """A channel name -> its self-contained workspace. No channel -> a shared
    '_sandbox' workspace (dry/smoke runs land there, not in a real channel)."""
    root = CHANNELS_DIR / (channel or "_sandbox")
    out = root / "outputs"
    mem = root / "memory"
    return ChannelPaths(
        root=root,
        profile=root / "profile.md",
        seeds=root / "seeds" / "briefs.jsonl",
        candidates=out / "candidates",
        accepted=out / "accepted",
        rejected=out / "rejected",
        archived=out / "archived",
        parked=out / "parked",
        logs=root / "logs",
        metrics_file=root / "metrics" / "scores.jsonl",
        review_file=root / "review" / "human_review.csv",
        memory=mem,
        trainset_file=mem / "trainset.jsonl",
        compiled=mem / "compiled",
        run_index_file=mem / "run_index.jsonl",
    )
