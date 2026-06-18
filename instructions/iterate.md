# SOP — Iterate

**Goal:** improve an artifact using the evaluator's critique, version by version.

**Loop:** each round the Iterator (Provider A) takes the current artifact + the
evaluator's reasons/breakdown and produces an improved version. The Reevaluator
(Provider B) re-scores it. Version increments each round (`v01 -> v02 -> ...`).

**Stop when** (config-tunable):
- score ≥ `TARGET_SCORE` (90), or
- `MAX_ITER` (5) iterations reached, or
- plateau: no `MIN_IMPROVEMENT` (2 pt) gain over `PLATEAU_ROUNDS` (2) rounds.

Then the best version is reevaluated once more and marked `ready_for_review`.
