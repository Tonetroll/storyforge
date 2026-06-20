# SOP — Route (LEGACY)

**Goal:** the legacy batch path that applied decisions from a review file.
Reviews now happen in conversation (see the `review-logging` skill); this command
is kept for back-compat only and no-ops on the markdown journal.

**Run:** `python run.py route`

**What happens** (per reviewed row):
| status | moves artifact to | side effect |
|---|---|---|
| accepted | `outputs/accepted/` (status → `promoted`) | appends to `memory/trainset.jsonl` |
| rejected | `outputs/rejected/` (status → `archived`) | — |
| revise | stays in `candidates/` | re-run the loop on it |

The reviewed artifact JSON gets the review (score/reason/next_action) embedded
before it is moved, so the why travels with the asset.
