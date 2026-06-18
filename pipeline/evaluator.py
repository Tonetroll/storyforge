"""Evaluator / gate stage (generic). Runs on Provider B (a DIFFERENT provider
from the generator/iterator) so it cannot inflate work it did not produce.

Grades each criterion 0..its weight, sums to the 0-100 quality score in code,
and sets the verdict: any criterion at 0 = absent = REJECT. Weights come from the
stage, so the same code serves any number of criteria.
"""

import re

import dspy

import config


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
    return "REJECT"  # default-deny


class Evaluator(dspy.Module):
    def __init__(self, gate_sig, weights: dict):
        super().__init__()
        self.gate = dspy.ChainOfThought(gate_sig)
        self.weights = weights  # {criterion_number: max_points}

    def forward(self, content: dict, criteria: str) -> dspy.Prediction:
        o = self.gate(**content, criteria=criteria)
        breakdown = {}
        for k, weight in self.weights.items():
            breakdown[k] = max(0, min(parse_int(getattr(o, f"score_{k}")), weight))
        total = sum(breakdown.values())

        verdict = normalize_verdict(o.verdict)
        if any(v == 0 for v in breakdown.values()):
            verdict = "REJECT"
        score = total if verdict == "PASS" else 0

        return dspy.Prediction(
            verdict=verdict,
            score=score,
            breakdown=breakdown,
            failed_checks=getattr(o, "failed_checks", ""),
            why=getattr(o, "why", ""),
        )
