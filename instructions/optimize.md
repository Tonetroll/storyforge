# SOP — Optimize / Learn

**Goal:** retrain the generator from your accepted decisions.

**Run:** `python run.py learn` (add `--dry-run` to test wiring offline).

**What happens:**
1. `memory/trainset.jsonl` (accepted artifacts, written by the router) is loaded
   into `dspy.Example` objects.
2. A DSPy optimizer (`BootstrapFewShot` by default; `MIPROv2`/`GEPA` available)
   compiles a stronger generator, scored by the **separate** evaluator.
3. The compiled program is saved to `memory/compiled/<stage>_generator.json`.

**Why it matters:** the system improves from your real verdicts, not just AI
self-scoring. Swap the optimizer in `pipeline/learn.py` as the trainset grows.
