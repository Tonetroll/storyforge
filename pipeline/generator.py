"""Generator stage. Runs on Provider A. Produces a structured STORY idea (the
five gate-ready fields) from a brief + the generator standard."""

import dspy

from pipeline.signatures import GenerateStoryIdea


class Generator(dspy.Module):
    def __init__(self):
        super().__init__()
        self.generate = dspy.ChainOfThought(GenerateStoryIdea)

    def forward(self, brief: str, standard: str) -> dspy.Prediction:
        o = self.generate(brief=brief, standard=standard)
        return dspy.Prediction(
            one_liner=o.one_liner,
            resolution=o.resolution,
            reaction_1=o.reaction_1,
            reaction_2=o.reaction_2,
            viewer_action=o.viewer_action,
            topic=o.topic,
        )
