"""Central configuration for the DSPy idea pipeline.

Everything tunable lives here: the project-name token, which LLM runs which
stage, the scoring thresholds, and all filesystem paths. Nothing in this folder
reaches outside it.
"""

import os
from dataclasses import dataclass
from pathlib import Path

# ---------------------------------------------------------------------------
# Identity
# ---------------------------------------------------------------------------
# PROJECT_NAME prefixes each run's LOG file (e.g. STORY_run_0001.log). Artifact
# filenames are slug-based (<slug>_<NNNN>_v<VV>_<status>.json), not project-prefixed.
# This pipeline gates STORIES (information is not a story); the gate assigns a
# story id "ST-####" on PASS, derived from the asset number.
PROJECT_NAME = "STORY"

# Default artifact module/type token. Extensible later (e.g. "HOOK", "TITLE").
DEFAULT_MODULE = "IDEA"

# ---------------------------------------------------------------------------
# LLM assignments  --  THE #1 RULE: the evaluator is a DIFFERENT PROVIDER from
# the generator/iterator, so it cannot inflate its own work. Two API keys.
# (model string, temperature, max_tokens)
# ---------------------------------------------------------------------------
# Provider A (generator/iterator) = Z.ai GLM via the GLM Coding Plan (OpenAI-compatible
#   endpoint). The model name (glm-5.2) and key are yours; we point at the coding endpoint
#   so the connector reaches the model your plan actually serves.
# Provider B (evaluator/reevaluator) = OpenRouter, concrete model. (The connector can't use
#   OpenRouter @preset/ references -- known LiteLLM limitation -- so we name the model directly.)
#   Reads OPENROUTER_API_KEY from .env.
# Different providers -> the judge can't grade its own work (the #1 rule, enforced in orchestrator.py).
ZAI_CODING_BASE = "https://api.z.ai/api/coding/paas/v4"   # GLM Coding Plan, OpenAI-compatible
ZAI_API_KEY     = os.getenv("ZAI_API_KEY")
GENERATOR_LM   = {"model": "openai/glm-5.2", "api_base": ZAI_CODING_BASE, "api_key": ZAI_API_KEY, "temperature": 0.9, "max_tokens": 32000}
ITERATOR_LM    = {"model": "openai/glm-5.2", "api_base": ZAI_CODING_BASE, "api_key": ZAI_API_KEY, "temperature": 0.7, "max_tokens": 32000}
EVALUATOR_LM   = {"model": "openrouter/google/gemma-3-27b-it", "temperature": 0.0, "max_tokens": 8192}
REEVALUATOR_LM = {"model": "openrouter/google/gemma-3-27b-it", "temperature": 0.0, "max_tokens": 8192}

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

# The CRAFT layer: genre-agnostic craft, shared by every channel and stage.
CRAFT_DIR       = BASE_DIR / "craft"
CRAFT_PRINCIPLES = CRAFT_DIR / "principles.md"   # doctrine, injected into every generator
CRAFT_TRAINSET  = CRAFT_DIR / "trainset.jsonl"   # shared craft-exemplary examples (grows over time)


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
    '_sandbox' workspace (dry/smoke runs land there, not in a real channel).

    Guards against path traversal: a truthy channel may not contain a path
    separator or a '..' component, nor be an absolute path -- otherwise the
    workspace could escape channels/. CHANNELS_DIR is read dynamically (tests
    monkeypatch it), and we confirm the resolved root stays inside it."""
    if channel:
        if ("/" in channel or "\\" in channel
                or ".." in Path(channel).parts
                or Path(channel).is_absolute()):
            raise ValueError(
                f"Invalid channel name '{channel}': must not contain a path "
                f"separator, a '..' component, or be an absolute path."
            )
    channels_dir = CHANNELS_DIR  # read at call time; tests monkeypatch this
    root = channels_dir / (channel or "_sandbox")
    # Defense in depth: the resolved root must stay inside channels_dir.
    resolved_root, resolved_base = root.resolve(), channels_dir.resolve()
    if resolved_root != resolved_base and resolved_base not in resolved_root.parents:
        raise ValueError(
            f"Invalid channel name '{channel}': resolves outside the channels "
            f"directory ({resolved_root})."
        )
    out = root / "outputs"
    mem = root / "memory"
    return ChannelPaths(
        root=root,
        profile=root / "profile.md",
        seeds=root / "seeds" / "seeds.txt",
        candidates=out / "drafts",
        accepted=out / "accepted",
        rejected=out / "rejected",
        archived=out / "archived",
        parked=out / "parked",
        logs=root / "logs",
        metrics_file=root / "metrics" / "scores.jsonl",
        review_file=root / "review" / "human_review.md",
        memory=mem,
        trainset_file=mem / "trainset.jsonl",
        compiled=mem / "compiled",
        run_index_file=mem / "run_index.jsonl",
    )
