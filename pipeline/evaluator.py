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
    def __init__(self, gate_sig, weights: dict, penalty_points: int = 0, verdict_floor=None, kill_checks=()):
        super().__init__()
        self.gate = dspy.ChainOfThought(gate_sig)
        self.weights = weights              # {criterion_number: max_points}
        self.penalty_points = penalty_points  # e.g. jargon penalty; 0 = no penalty
        self.verdict_floor = verdict_floor    # None = all-pass mode; int = PASS if score >= floor
        self.kill_checks = tuple(kill_checks or ())  # criteria that REJECT on a 0 even past the floor

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

        # A "kill check" REJECTS on a 0 even on a floor stage -- a must-not-fail rule
        # (e.g. the Dance) cannot be bought back by points earned on other checks.
        killed = any(breakdown.get(k, 0) == 0 for k in self.kill_checks)
        if self.verdict_floor is not None:
            # Hybrid / ratio style: PASS if it clears the floor, UNLESS a kill check scored 0.
            verdict = "PASS" if (total >= self.verdict_floor and not killed) else "REJECT"
            score = total
        else:
            # All-pass style: any criterion at 0 = absent = REJECT.
            verdict = normalize_verdict(o.verdict)
            if any(v == 0 for v in breakdown.values()):
                verdict = "REJECT"
            score = total   # always the real criteria total; the verdict carries pass/fail, so a high-quality REJECT logs honestly (not as 0)

        return dspy.Prediction(
            verdict=verdict,
            score=score,
            breakdown=breakdown,
            penalty=penalty,
            failed_checks=getattr(o, "failed_checks", ""),
            why=getattr(o, "why", ""),
        )
