"""The 'two copies of one contract' rule, enforced automatically.

Every stage's gate SIGNATURE (pipeline/signatures.py) must stay in sync with its
stage WEIGHTS (pipeline/stages.py): weights sum to 100; #weights == #labels ==
#gate score-fields; and each gate score_k's declared max (parsed from its desc)
equals the stage weight. This catches signature<->weights drift the instant it is
introduced, so it can never silently reappear. Hermetic: pure introspection, no
network/LLM.
"""
import re

from pipeline import stages


def _desc(field):
    extra = getattr(field, "json_schema_extra", None)
    if isinstance(extra, dict) and (extra.get("desc") or extra.get("description")):
        return extra.get("desc") or extra.get("description")
    return field.description or ""


def test_every_stage_gate_signature_matches_its_weights():
    problems = []
    for name, st in stages.STAGES.items():
        w, labels, gate = st.weights, st.labels, st.gate_sig
        score_fields = {n: f for n, f in gate.model_fields.items() if n.startswith("score_")}

        if sum(w.values()) != 100:
            problems.append(f"{name}: weights sum {sum(w.values())} != 100")
        if not (len(w) == len(labels) == len(score_fields)):
            problems.append(
                f"{name}: count mismatch weights={len(w)} labels={len(labels)} "
                f"score_fields={len(score_fields)}")
        for k, weight in w.items():
            f = score_fields.get(f"score_{k}")
            if f is None:
                problems.append(f"{name}: score_{k} missing from {gate.__name__}")
                continue
            m = re.search(r"0\s*[-–]\s*(\d+)", _desc(f))  # "0-16" / "0–16"
            if m and int(m.group(1)) != weight:
                problems.append(
                    f"{name}: {gate.__name__}.score_{k} desc max {m.group(1)} != weight {weight}")

    assert not problems, "signature<->weights drift detected:\n  " + "\n  ".join(problems)
