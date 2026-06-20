# SOP — Route

**Goal:** apply the decisions in `review/human_review.csv`.

**Run:** `python run.py route`

**What happens** (per reviewed row):
| status | moves artifact to | side effect |
|---|---|---|
| accepted | `outputs/accepted/` (status → `promoted`) | appends to `memory/trainset.jsonl` |
| rejected | `outputs/rejected/` (status → `archived`) | — |
| revise | stays in `candidates/` | re-run the loop on it |

The reviewed artifact JSON gets the review (score/reason/next_action) embedded
before it is moved, so the why travels with the asset.
