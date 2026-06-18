"""Central configuration for the DSPy idea pipeline.

Everything tunable lives here: the project-name token, which LLM runs which
stage, the scoring thresholds, and all filesystem paths. Nothing in this folder
reaches outside it.
"""

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
BASE_DIR        = Path(__file__).resolve().parent
RULES_DIR       = BASE_DIR / "rules"
STANDARDS_DIR   = RULES_DIR / "standards"
CHANNELS_DIR    = BASE_DIR / "channels"   # one profile per channel (audience + character/voice)
INSTRUCTIONS_DIR = BASE_DIR / "instructions"
EXAMPLES_DIR    = BASE_DIR / "examples"
OUTPUTS_DIR     = BASE_DIR / "outputs" / "ideas"
CANDIDATES_DIR  = OUTPUTS_DIR / "candidates"
ACCEPTED_DIR    = OUTPUTS_DIR / "accepted"
REJECTED_DIR    = OUTPUTS_DIR / "rejected"
ARCHIVED_DIR    = OUTPUTS_DIR / "archived"
PARKED_DIR      = OUTPUTS_DIR / "parked"
LOGS_DIR        = BASE_DIR / "logs"
METRICS_DIR     = BASE_DIR / "metrics"
METRICS_FILE    = METRICS_DIR / "scores.jsonl"
REVIEW_DIR      = BASE_DIR / "review"
REVIEW_FILE     = REVIEW_DIR / "human_review.csv"
MEMORY_DIR      = BASE_DIR / "memory"
TRAINSET_FILE   = MEMORY_DIR / "trainset.jsonl"
COMPILED_DIR    = MEMORY_DIR / "compiled"
RUN_INDEX_FILE  = MEMORY_DIR / "run_index.jsonl"
