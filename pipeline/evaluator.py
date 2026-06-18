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
    def __init__(self, gate_sig, weights: dict, penalty_points: int = 0, verdict_floor=None):
        super().__init__()
        self.gate = dspy.ChainOfThought(gate_sig)
        self.weights = weights              # {criterion_number: max_points}
        self.penalty_points = penalty_points  # e.g. jargon penalty; 0 = no penalty
        self.verdict_floor = verdict_floor    # None = all-pass mode; int = PASS if score >= floor

    def forward(self, content: dict, criteria: str) -> dspy.Prediction:
        o = self.gate(**content, criteria=criteria)
        breakdown = {}
        for k, weight in self.weights.items():
            # binary rules are graded 0-or-weight by instruction; graded ones 0..weight.
            breakdown[k] = max(0, min(parse_int(getattr(o, f"score_{k}")), weight))
        total = sum(breakdown.values())

        # Optional penalty (e.g. jargon flag from the gate).
        penalty = 0
        if self.penalty_points and str(getattr(o, "jargon", "")).strip().lower() in ("true", "yes", "1"):
            penalty = self.penalty_points
        total = max(0, total - penalty)

        if self.verdict_floor is not None:
            # Hybrid / ratio style: PASS if it clears the floor (a missing rule costs points, doesn't auto-kill).
            verdict = "PASS" if total >= self.verdict_floor else "REJECT"
            score = total
        else:
            # All-pass style: any criterion at 0 = absent = REJECT.
            verdict = normalize_verdict(o.verdict)
            if any(v == 0 for v in breakdown.values()):
                verdict = "REJECT"
            score = total if verdict == "PASS" else 0

        return dspy.Prediction(
            verdict=verdict,
            score=score,
            breakdown=breakdown,
            penalty=penalty,
            failed_checks=getattr(o, "failed_checks", ""),
            why=getattr(o, "why", ""),
        )
