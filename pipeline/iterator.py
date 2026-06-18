"""Iterator stage. Runs on Provider A. Improves a PASSING idea using the gate's
critique to push the score higher. Distinct from the evaluator on purpose."""

import dspy

from pipeline.signatures import IterateStoryIdea


class Iterator(dspy.Module):
    def __init__(self):
        super().__init__()
        self.iterate = dspy.ChainOfThought(IterateStoryIdea)

    def forward(self, idea: dict, critique: str, standard: str) -> dspy.Prediction:
        o = self.iterate(
            one_liner=idea["one_liner"],
            resolution=idea["resolution"],
            reaction_1=idea["reaction_1"],
            reaction_2=idea["reaction_2"],
            viewer_action=idea["viewer_action"],
            critique=critique,
            standard=standard,
        )
        return dspy.Prediction(
            one_liner=o.improved_one_liner,
            resolution=o.improved_resolution,
            reaction_1=o.improved_reaction_1,
            reaction_2=o.improved_reaction_2,
            viewer_action=o.improved_viewer_action,
        )
