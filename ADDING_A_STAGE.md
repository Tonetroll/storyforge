# Adding a Stage

This repo is a **multi-stage engine**, not a single generator. A *stage* is one
step in the pipeline (`idea`, then `topic-theme`, `story-structure`, …). The
engine — the directory, the four roles (generator / evaluator / iterator /
reevaluator), the gate → score → iterate → park/ready loop, naming, logging,
the review CSV, the router, and the learning loop — is **generic**. To add a
stage you touch exactly four things and never edit the engine.

## The uniform stage interface

Every stage's three signatures follow the same shape, so the engine stays generic:

```
generator:  (brief, standard)                     -> <content fields> + topic
gate:       (<content fields>, criteria)          -> verdict, score_1..N, failed_checks, why
iterator:   (<content fields>, critique, standard) -> improved_<content field> ...
```

Where the data flows:
- A first/upstream stage gets its `brief` from you (`--brief`) or its own topic generator.
- A downstream stage's `brief` is built from the **accepted** artifact of the stage before it (see Step 4).
- The gate scores each check `0..its weight`; the weights must sum to `100`. Any check at `0` = REJECT.

---

## Step 1 — Write the two MD standards  (YOUR part)

```
rules/standards/<stage>_generator.md   # what to produce + how; the bar
rules/standards/<stage>_evaluator.md   # the gate: the checks, their weights (sum to 100), verdict rule
```

This is the only creative/IP part. Everything below is mechanical and derived from these.

## Step 2 — Add three signatures  (pipeline/signatures.py)

Replace the EXAMPLE field names with your stage's real fields.

```python
class GenerateTitle(dspy.Signature):
    """<mirror your <stage>_generator.md standard here>"""
    brief = dspy.InputField(desc="What this stage receives (the accepted upstream artifact, rendered).")
    standard = dspy.InputField(desc="The generator standard (rules/standards/<stage>_generator.md).")
    headline = dspy.OutputField(desc="...")            # your content fields
    thumbnail_concept = dspy.OutputField(desc="...")
    topic = dspy.OutputField(desc="3-6 words naming what this is about, for the filename.")

class GateTitle(dspy.Signature):
    """<mirror your <stage>_evaluator.md gate here>"""
    headline = dspy.InputField()                       # same content fields as inputs
    thumbnail_concept = dspy.InputField()
    criteria = dspy.InputField(desc="The gate criteria + weights.")
    verdict = dspy.OutputField(desc="Exactly 'PASS' or 'REJECT'. REJECT if any check scores 0.")
    score_1 = dspy.OutputField(desc="Check 1: integer 0-<weight>. 0 = absent.")
    score_2 = dspy.OutputField(desc="Check 2: integer 0-<weight>.")
    # ... one score_k per criterion; count must match the weights in Step 3
    failed_checks = dspy.OutputField(desc="If REJECT: failing check numbers + one line each. Else 'none'.")
    why = dspy.OutputField(desc="One line.")

class IterateTitle(dspy.Signature):
    """<how to improve a passing artifact>"""
    headline = dspy.InputField()
    thumbnail_concept = dspy.InputField()
    critique = dspy.InputField(desc="The gate's why + weak points.")
    standard = dspy.InputField()
    improved_headline = dspy.OutputField(desc="...")        # improved_<each content field>
    improved_thumbnail_concept = dspy.OutputField(desc="...")
```

## Step 3 — Register the stage  (pipeline/stages.py)

```python
TITLE = Stage(
    name="title",
    content_label="TITLE + THUMBNAIL",
    gen_sig=S.GenerateTitle, gate_sig=S.GateTitle, iter_sig=S.IterateTitle,
    content_fields=["headline", "thumbnail_concept"],   # the judged + stored fields
    topic_field="topic",
    weights={1: 40, 2: 30, 3: 30},                      # MUST sum to 100; one entry per score_k
    labels={1: "...", 2: "...", 3: "..."},
    gen_standard_file="title_generator.md",
    eval_standard_file="title_evaluator.md",
    upstream="idea",                                    # None for a first/upstream stage
    build_brief=lambda rec: (                            # how the accepted upstream artifact becomes this brief
        f"Idea: {rec['content']['one_liner']}\n"
        f"Resolution: {rec['content']['resolution']}\n"
        "Write a title + thumbnail that opens this loop WITHOUT revealing the resolution."
    ),
)

STAGES = {IDEA.name: IDEA, TITLE.name: TITLE}           # add it to the registry
```

## Step 4 — (downstream stages only) the handoff

The `build_brief` above is the whole handoff: it turns the *accepted* artifact of
`upstream` into this stage's `brief`. The engine finds the latest accepted
upstream artifact automatically. An upstream/first stage sets `upstream=None`,
`build_brief=None`, and takes its `brief` from `--brief` (or its own generator).

---

## Run it

```
python run.py generate --stage title              # downstream: pulls the accepted idea automatically
python run.py generate --stage topic --brief "…"  # upstream: takes a seed
python run.py manual   --stage title              # hand-authored content + scores (no API keys)
python run.py learn    --stage title              # retrain this stage's generator from accepted examples
```

## What you DO NOT touch

The engine. None of these change when you add a stage:
`orchestrator.py`, `naming.py`, `logging_setup.py`, `render.py`, `router.py`,
`metric.py`, `generator.py`, `evaluator.py`, `iterator.py`, `reevaluator.py`,
and `config.py` (thresholds/paths only — per-stage weights live in `stages.py`).
