"""Evaluator / gate stage. Runs on Provider B (a DIFFERENT provider from the
generator and iterator) so it cannot inflate work it did not produce.

It grades each of the six checks 0..its weight (config.CRITERION_WEIGHTS), sums
them deterministically in code to the 0-100 quality score, and sets the verdict:
a criterion scoring 0 = absent = gate REJECT. The separation is the #1 rule and
is enforced at startup in orchestrator.py.
"""

import re

import dspy

import config
from pipeline.signatures import GateStoryIdea


def parse_int(raw) -> int:
    if isinstance(raw, (int, float)):
        return int(raw)
    match = re.search(r"-?\d+", str(raw))
    return int(match.group()) if match else 0


def normalize_verdict(raw) -> str:
    text = str(raw).strip().upper()
    if "REJECT" in text:
        return "REJECT"
    if "PASS" in text:
        return "PASS"
    return "REJECT"  # default-deny: anything unclear fails the gate


class Evaluator(dspy.Module):
    def __init__(self):
        super().__init__()
        self.gate = dspy.ChainOfThought(GateStoryIdea)

    def forward(self, idea: dict, criteria: str) -> dspy.Prediction:
        o = self.gate(
            one_liner=idea["one_liner"],
            resolution=idea["resolution"],
            proposed_reaction_1=idea["reaction_1"],
            proposed_reaction_2=idea["reaction_2"],
            proposed_viewer_action=idea["viewer_action"],
            criteria=criteria,
        )
        # Grade each criterion 0..weight, then sum to the 0-100 quality score.
        breakdown = {}
        for k, weight in config.CRITERION_WEIGHTS.items():
            pts = max(0, min(parse_int(getattr(o, f"score_{k}")), weight))
            breakdown[k] = pts
        total = sum(breakdown.values())

        # Verdict: the gate is binary. Any criterion at 0 = absent = REJECT,
        # regardless of what the model wrote in `verdict` (default-deny).
        verdict = normalize_verdict(o.verdict)
        if any(v == 0 for v in breakdown.values()):
            verdict = "REJECT"
        score = total if verdict == "PASS" else 0

        return dspy.Prediction(
            verdict=verdict,
            score=score,
            breakdown=breakdown,
            reaction_1=o.reaction_1,
            reaction_2=o.reaction_2,
            viewer_action=o.viewer_action,
            failed_checks=o.failed_checks,
            why=o.why,
        )
