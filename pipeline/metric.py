"""The metric DSPy's optimizer/Evaluate use.

Contract (verified, evaluate.py:172): metric(example, prediction, trace=None) -> float|bool.
We score with the SEPARATE evaluator (the gate) so optimization is judged by the
independent provider too -- the #1 rule holds even while the system learns.
A REJECT scores 0; a PASS scores its 0-100 normalized to 0..1.
"""

import config


def make_metric(evaluator, criteria: str):
    """Bind an evaluator (gate) instance + criteria into a DSPy-shaped metric."""

    def metric(example, prediction, trace=None):
        idea = {
            "one_liner": getattr(prediction, "one_liner", ""),
            "resolution": getattr(prediction, "resolution", ""),
            "reaction_1": getattr(prediction, "reaction_1", ""),
            "reaction_2": getattr(prediction, "reaction_2", ""),
            "viewer_action": getattr(prediction, "viewer_action", ""),
        }
        gate = evaluator(idea=idea, criteria=criteria)
        score01 = gate.score / float(config.SCORE_SCALE)
        # Inside an optimizer (trace is set), demand a real PASS at/above target.
        if trace is not None:
            return gate.verdict == "PASS" and score01 >= (config.TARGET_SCORE / float(config.SCORE_SCALE))
        return score01

    return metric
