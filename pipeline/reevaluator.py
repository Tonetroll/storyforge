"""Reevaluator stage (generic). The final independent score after iteration.
Same gate + weights as the Evaluator, bound to the SAME separate provider
(Provider B), but a distinct module instance so the final judgement is its own."""

from pipeline.evaluator import Evaluator


class Reevaluator(Evaluator):
    """Identical behaviour to Evaluator; named separately for clarity and its own
    LM binding / logging identity."""
    pass
