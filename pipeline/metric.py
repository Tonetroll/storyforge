"""The metric DSPy's optimizer/Evaluate use (generic over a stage's fields).

Contract (verified, evaluate.py:172): metric(example, prediction, trace=None) -> float|bool.
We score with the SEPARATE evaluator (the gate) so optimization is judged by the
independent provider too -- the #1 rule holds even while the system learns.
"""

import config


def make_metric(evaluator, criteria: str, content_fields: list):
    """Bind an evaluator (gate) + criteria + the stage's content fields."""

    def metric(example, prediction, trace=None):
        content = {f: getattr(prediction, f, "") for f in content_fields}
        gate = evaluator(content=content, criteria=criteria)
        score01 = gate.score / float(config.SCORE_SCALE)
        if trace is not None:  # inside an optimizer: demand a real PASS at/above target
            return gate.verdict == "PASS" and score01 >= (config.TARGET_SCORE / float(config.SCORE_SCALE))
        return score01

    return metric
