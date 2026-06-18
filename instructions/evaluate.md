# SOP — Evaluate

**Goal:** score an artifact honestly against the criteria, on a separate LLM.

**The rule:** the evaluator runs on a **different provider** than the generator
(`config.EVALUATOR_LM`). It never grades work it produced. The orchestrator
refuses to run if this is violated.

**Criteria source:** `rules/standards/*.md` is concatenated and passed in as the
rubric (`run.py:load_criteria`). The rubric is also mirrored into
`pipeline/signatures.py:EvaluateArtifact`.

**Output:** integer score 0–100 + per-criterion breakdown + reasons. Scores are
parsed defensively (`pipeline/evaluator.py:parse_score`) and written to every
artifact JSON and to `metrics/scores.jsonl`.
