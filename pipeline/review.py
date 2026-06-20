"""Review queue (deterministic, read-only): what awaits Tone's verdict.

The filesystem IS the queue. After a run, a `ready_for_review` artifact (in
candidates/) is the machine's PASS; a `parked` artifact is what the machine
fell short on. Both await Tone's verdict until she rules on them -- they can't
hide. This module SURFACES that queue and shows the machine's verdict + score
for each, so a human/machine divergence is visible, and flags which already have
an entry in the review journal (review/human_review.md).

It changes NOTHING. Recording verdicts, routing lessons to the gate, and
promoting/rejecting artifacts is the `review-logging` skill's job (the part that
must verify understanding + amplification before it edits any standard).
"""

import json

import config


def _load(f):
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        return None


def _entry(rec: dict, location: str) -> dict:
    return {
        "asset_id": rec.get("asset_id"),
        "story_id": rec.get("story_id"),
        "stage": rec.get("stage"),
        "score": rec.get("score"),
        "machine_verdict": rec.get("verdict"),
        # "passed" = the gate approved it (>=target); "parked" = it fell short.
        "machine_outcome": "passed" if location == "candidates" else "parked",
        "location": location,
    }


def review_queue(channel: str = None) -> dict:
    """Returns {channel, pending, reviewed}. pending = awaiting Tone's verdict;
    reviewed = already has an entry in the journal. Both lists carry the machine
    verdict+score so overrides are visible."""
    paths = config.paths_for(channel)
    journal = paths.review_file.read_text(encoding="utf-8") if paths.review_file.exists() else ""
    pending, reviewed = [], []

    def _bucket(entry):
        seen = bool(entry["asset_id"]) and entry["asset_id"] in journal
        (reviewed if seen else pending).append(entry)

    # Machine PASSES live in candidates/ as ready_for_review.
    if paths.candidates.exists():
        for f in sorted(paths.candidates.glob("*.json")):
            rec = _load(f)
            if rec and rec.get("status") == "ready_for_review":
                _bucket(_entry(rec, "candidates"))
    # Machine SHORTFALLS live in parked/ -- surfaced so Tone can overrule the gate.
    if paths.parked.exists():
        for f in sorted(paths.parked.glob("*.json")):
            rec = _load(f)
            if rec:
                _bucket(_entry(rec, "parked"))
    return {"channel": channel, "pending": pending, "reviewed": reviewed}


def _fmt(e: dict) -> str:
    tag = "PASS" if e["machine_outcome"] == "passed" else "PARK"
    score = e["score"] if e["score"] is not None else "?"
    note = "" if e["machine_outcome"] == "passed" else "   (machine fell short -- you can overrule)"
    return f"  [{tag} {str(score):>3}] {str(e['stage']):<11} {e['asset_id']} ({e['story_id']}) -> {e['location']}/{note}"


def print_queue(channel: str = None) -> dict:
    q = review_queue(channel)
    print(f"\nREVIEW QUEUE -- channel: {channel or '_sandbox'}")
    print(f"  pending: {len(q['pending'])} | already reviewed: {len(q['reviewed'])}\n")
    if q["pending"]:
        print("PENDING (awaiting your verdict):")
        for e in q["pending"]:
            print(_fmt(e))
    else:
        print("PENDING: nothing awaiting review.")
    if q["reviewed"]:
        print("\nALREADY REVIEWED (logged in human_review.md):")
        for e in q["reviewed"]:
            print(f"  [done] {str(e['stage']):<11} {e['asset_id']} ({e['story_id']})")
    return q
