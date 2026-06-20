# Project Rules — the doctrine

These are the standing rules for this pipeline. They override convenience. This
folder is a closed system: no code reads or writes outside it, and no data comes
from anywhere except the inputs placed here.

## A multi-stage engine
This is a reusable engine, not a single generator. Each pipeline step is a
"stage" registered in `pipeline/stages.py` (`idea`, then `topic-theme`,
`story-structure`, …). The engine — the four roles, the gate → score → iterate
loop, naming, logging, review, and learning — is generic; a stage is defined by
its standards MD, its signatures, and one registry entry. To add one, see
`ADDING_A_STAGE.md`. The rules below apply to every stage.

## 1. Evaluator independence (the #1 rule)
The **evaluator and reevaluator run on a different LLM provider** than the
generator and iterator. They must never share an LM instance or model. The
orchestrator asserts this at startup (`assert_separation`) and **refuses to run**
if violated. This is what keeps scores honest — the judge never grades its own work.

- Provider A (generator, iterator): set in `config.GENERATOR_LM` / `ITERATOR_LM`.
- Provider B (evaluator, reevaluator): set in `config.EVALUATOR_LM` / `REEVALUATOR_LM`.

## 2. Standards are machine-enforced
Written standards live in `rules/standards/*.md` (human-readable) **and** are
mirrored into the DSPy Signature docstrings + `OutputField(desc=...)` in
`pipeline/signatures.py` (model-enforced). The two must say the same thing.

## 3. Versioned, never overwritten
Every iteration writes a new file. Nothing is destroyed. Status lives in the
filename.

## 4. Naming protocol
`<slug>_<NUMBER>_v<VERSION>_<STATUS>.json` — e.g. `elevator-mirror-practiced-fine_0002_v02_revised.json`
- slug = kebab-case of what the idea is ABOUT (`naming.slugify`)
- NUMBER = `0001` per asset, VERSION = `v01` per iteration

## 5. Status state machine
```
candidate -> revised -> ready_for_review          (pipeline)
ready_for_review -> accepted | rejected | revise   (human review)
accepted -> promoted     rejected -> archived      revise -> back to iterator
```
Terminal: promoted, archived, killed.

## 6. Stop criteria (config-tunable)
Iterate until score ≥ `TARGET_SCORE` (95), OR `MAX_ITER` (3) reached. Then a final
independent reevaluation marks the best version `ready_for_review`.

## 7. Routing table (`pipeline/router.py`)
| review status | action | destination | side effect |
|---|---|---|---|
| accepted | promote | `outputs/accepted/` | append to `memory/trainset.jsonl` |
| rejected | archive | `outputs/rejected/` | — |
| revise | rerun | stays in `candidates/` | re-enters the loop |

## 8. The learning loop
`pipeline/learn.py` reads `memory/trainset.jsonl` (accepted artifacts) and
compiles a better generator via a DSPy optimizer, scored by the **separate**
evaluator. The system learns from your real decisions, not just AI scoring.
