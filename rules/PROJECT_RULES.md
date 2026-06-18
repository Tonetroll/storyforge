# Project Rules — the doctrine

These are the standing rules for this pipeline. They override convenience. This
folder is a closed system: no code reads or writes outside it, and no data comes
from anywhere except the inputs placed here.

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
`PROJECTNAME_MODULE_NUMBER_VERSION_STATUS.json` — e.g. `CORE_IDEA_0001_v02_revised.json`
- PROJECTNAME = the core-idea token (`config.PROJECT_NAME`)
- MODULE = artifact type (`IDEA`, extensible)
- NUMBER = `0001` per asset, VERSION = `v01` per iteration

## 5. Status state machine
```
candidate -> revised -> ready_for_review          (pipeline)
ready_for_review -> accepted | rejected | revise   (human review)
accepted -> promoted     rejected -> archived      revise -> back to iterator
```
Terminal: promoted, archived, killed.

## 6. Stop criteria (config-tunable)
Iterate until score ≥ `TARGET_SCORE` (90), OR `MAX_ITER` (5) reached, OR plateau
(no `MIN_IMPROVEMENT`=2 pt gain over `PLATEAU_ROUNDS`=2 rounds). Then a final
independent reevaluation marks the best version `ready_for_review`.

## 7. Routing table (`pipeline/router.py`)
| review status | action | destination | side effect |
|---|---|---|---|
| accepted | promote | `outputs/ideas/accepted/` | append to `memory/trainset.jsonl` |
| rejected | archive | `outputs/ideas/rejected/` | — |
| revise | rerun | stays in `candidates/` | re-enters the loop |

## 8. The learning loop
`pipeline/learn.py` reads `memory/trainset.jsonl` (accepted artifacts) and
compiles a better generator via a DSPy optimizer, scored by the **separate**
evaluator. The system learns from your real decisions, not just AI scoring.
