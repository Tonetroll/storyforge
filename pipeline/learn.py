"""The learning loop: your real decisions retrain the generator.

Reads memory/trainset.jsonl (accepted ideas, written by the router), turns each
into a dspy.Example with the five story fields, and runs a DSPy optimizer to
compile a better generator. The compiled program is saved to memory/compiled/
as JSON state (verified API: program.save(path, save_program=False)).

Scoring during optimization uses the SEPARATE evaluator/gate (pipeline/metric.py),
so the #1 rule holds even while the system learns.
"""

import json

import dspy
from dspy.teleprompt import BootstrapFewShot

import config
from pipeline.generator import Generator
from pipeline.evaluator import Evaluator
from pipeline.metric import make_metric


def load_trainset(gen_standard: str):
    if not config.TRAINSET_FILE.exists():
        return []
    examples = []
    with open(config.TRAINSET_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            idea = row.get("idea", {})
            examples.append(
                dspy.Example(
                    brief=row.get("brief", ""),
                    standard=gen_standard,
                    one_liner=idea.get("one_liner", ""),
                    resolution=idea.get("resolution", ""),
                    reaction_1=idea.get("reaction_1", ""),
                    reaction_2=idea.get("reaction_2", ""),
                    viewer_action=idea.get("viewer_action", ""),
                ).with_inputs("brief", "standard")
            )
    return examples


def compile_generator(gen_standard: str, eval_criteria: str, dry_run: bool = False):
    trainset = load_trainset(gen_standard)
    if not trainset:
        print("No accepted examples in memory/trainset.jsonl yet -- nothing to learn from.")
        print("Accept some ideas via review + router first.")
        return None

    generator = Generator()
    evaluator = Evaluator()
    if dry_run:
        from dspy.utils.dummies import DummyLM
        gen_lm = DummyLM([{"reasoning": "r", "one_liner": "x", "resolution": "y",
                           "reaction_1": "WTF", "reaction_2": "Aah", "viewer_action": "Reflect"}] * 50)
        eval_lm = DummyLM([{"reasoning": "r", "verdict": "PASS", "score": "95", "reaction_1": "WTF",
                            "reaction_2": "Aah", "viewer_action": "Reflect", "failed_checks": "none",
                            "why": "good"}] * 50)
        gen_lm.model, eval_lm.model = "dummy/generator-A", "dummy/evaluator-B"
    else:
        gen_lm = dspy.LM(**config.GENERATOR_LM)
        eval_lm = dspy.LM(**config.EVALUATOR_LM)

    # The optimizer's reset_copy() of the student wipes per-predictor .lm, so set a
    # global default (the generator's). The evaluator keeps its own bound LM via
    # set_lm and resolves it before the default, so the #1 rule still holds.
    dspy.configure(lm=gen_lm)
    generator.set_lm(gen_lm)
    evaluator.set_lm(eval_lm)

    metric = make_metric(evaluator, eval_criteria)
    optimizer = BootstrapFewShot(metric=metric, max_bootstrapped_demos=4, max_rounds=2)
    print(f"Compiling generator on {len(trainset)} accepted example(s)...")
    compiled = optimizer.compile(student=generator, trainset=trainset)

    config.COMPILED_DIR.mkdir(parents=True, exist_ok=True)
    out = config.COMPILED_DIR / "generator.json"
    compiled.save(str(out), save_program=False)
    print(f"Saved compiled generator -> {out.relative_to(config.BASE_DIR)}")
    return out
