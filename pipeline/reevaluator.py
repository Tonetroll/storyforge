"""Reevaluator stage. The final independent score after iteration. Same rubric
as the Evaluator and bound to the SAME separate provider (Provider B), but a
distinct module instance so the final judgement is its own call."""

from pipeline.evaluator import Evaluator


class Reevaluator(Evaluator):
    """Identical behaviour to Evaluator; named separately for clarity in the
    pipeline and so it can carry its own LM binding / logging identity."""
    pass
