"""Iterator stage (generic). Runs on Provider A. Improves a PASSING artifact
using the gate's critique. Returns the improved content as a dict keyed by the
stage's content fields (maps improved_<field> back to <field>)."""

import dspy


class Iterator(dspy.Module):
    def __init__(self, iter_sig, content_fields: list):
        super().__init__()
        self.iterate = dspy.ChainOfThought(iter_sig)
        self.content_fields = content_fields

    def forward(self, content: dict, critique: str, standard: str) -> dict:
        o = self.iterate(**content, critique=critique, standard=standard)
        return {f: getattr(o, f"improved_{f}") for f in self.content_fields}
