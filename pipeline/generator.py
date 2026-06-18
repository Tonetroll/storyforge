"""Generator stage (generic). Runs on Provider A. Uniform interface across all
pipeline stages: (brief, standard) -> the stage's content fields + topic."""

import dspy


class Generator(dspy.Module):
    def __init__(self, gen_sig):
        super().__init__()
        self.generate = dspy.ChainOfThought(gen_sig)

    def forward(self, brief: str, standard: str) -> dspy.Prediction:
        return self.generate(brief=brief, standard=standard)
