# SOP — Generate

**Goal:** produce a fresh artifact from a brief and score it independently.

**Run:** `python run.py generate --brief "your brief"` (add `--dry-run` for an
offline, no-key wiring test).

**What happens:**
1. Generator (Provider A) writes v01 from the brief.
2. Evaluator (Provider B, independent) scores it 0–100.
3. The loop iterates (see `iterate.md`) until target/cap.
4. The best version gets a final reevaluation and is saved as `ready_for_review`.

**Outputs:** versioned JSON in `outputs/candidates/`, a run log in `logs/`,
score rows in `metrics/scores.jsonl`.

**Standards:** generation is bound by `pipeline/signatures.py:GenerateArtifact`.
Edit its `OutputField(desc=...)` to match `rules/standards/`.
