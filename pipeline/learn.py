"""The learning loop (generic over a stage): your real decisions retrain a
stage's generator.

Reads memory/trainset.jsonl (accepted artifacts, written by the router), keeps
the rows for this stage, turns each into a dspy.Example, and runs a DSPy
optimizer. The compiled program is saved to memory/compiled/<stage>_generator.json.
Scoring uses the SEPARATE evaluator (pipeline/metric.py), so the #1 rule holds.
"""

import json

import dspy
from dspy.teleprompt import BootstrapFewShot

import config
from pipeline import stages
from pipeline.generator import Generator
from pipeline.evaluator import Evaluator
from pipeline.metric import make_metric


def _read_standard(filename: str, fallback: str) -> str:
    path = config.STANDARDS_DIR / filename
    return path.read_text(encoding="utf-8") if path.exists() else fallback


def load_trainset(stage, gen_standard: str):
    if not config.TRAINSET_FILE.exists():
        return []
    examples = []
    with open(config.TRAINSET_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if row.get("stage") and row["stage"] != stage.name:
                continue
            content = row.get("content", {})
            fields = {fld: content.get(fld, "") for fld in stage.content_fields}
            examples.append(
                dspy.Example(brief=row.get("brief", ""), standard=gen_standard, **fields)
                .with_inputs("brief", "standard")
            )
    return examples


def compile_generator(stage_name: str = "idea", dry_run: bool = False):
    stage = stages.get_stage(stage_name)
    gen_standard = _read_standard(stage.gen_standard_file, "PLACEHOLDER generator standard.")
    eval_criteria = _read_standard(stage.eval_standard_file, "PLACEHOLDER gate criteria.")

    trainset = load_trainset(stage, gen_standard)
    if not trainset:
        print(f"No accepted '{stage.name}' examples in memory/trainset.jsonl yet -- nothing to learn from.")
        return None

    generator = Generator(stage.gen_sig)
    evaluator = Evaluator(stage.gate_sig, stage.weights)
    if dry_run:
        from dspy.utils.dummies import DummyLM
        gen_a = {"reasoning": "r", stage.topic_field: "t"}
        for fld in stage.content_fields:
            gen_a[fld] = "x"
            gen_a[f"improved_{fld}"] = "x"
        eval_a = {"reasoning": "r", "verdict": "PASS", "failed_checks": "none", "why": "good"}
        for k, w in stage.weights.items():
            eval_a[f"score_{k}"] = str(w)
        gen_lm = DummyLM([gen_a] * 50)
        eval_lm = DummyLM([eval_a] * 50)
        gen_lm.model, eval_lm.model = "manual/generator", "manual/evaluator"
    else:
        gen_lm = dspy.LM(**config.GENERATOR_LM)
        eval_lm = dspy.LM(**config.EVALUATOR_LM)

    # reset_copy() of the student wipes per-predictor .lm, so set a global default.
    dspy.configure(lm=gen_lm)
    generator.set_lm(gen_lm)
    evaluator.set_lm(eval_lm)

    metric = make_metric(evaluator, eval_criteria, stage.content_fields)
    optimizer = BootstrapFewShot(metric=metric, max_bootstrapped_demos=4, max_rounds=2)
    print(f"Compiling '{stage.name}' generator on {len(trainset)} accepted example(s)...")
    compiled = optimizer.compile(student=generator, trainset=trainset)

    config.COMPILED_DIR.mkdir(parents=True, exist_ok=True)
    out = config.COMPILED_DIR / f"{stage.name}_generator.json"
    compiled.save(str(out), save_program=False)
    print(f"Saved compiled generator -> {out.relative_to(config.BASE_DIR)}")
    return out
