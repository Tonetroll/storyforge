"""The review queue is deterministic and read-only: it surfaces every artifact
awaiting Tone's verdict -- machine PASSES (ready_for_review) AND machine
SHORTFALLS (parked, so she can overrule the gate) -- and drops ones already
logged in the journal. It must never miss a parked item or change anything."""

import json

from pipeline import review


def _write(d, name, rec):
    d.mkdir(parents=True, exist_ok=True)
    (d / name).write_text(json.dumps(rec), encoding="utf-8")


def test_queue_surfaces_ready_and_parked_not_intermediate(channel_ws):
    paths = channel_ws["paths"]
    _write(paths.candidates, "a_0001_v03_ready_for_review.json",
           {"asset_id": "a_0001", "story_id": "ST-0001", "stage": "idea",
            "score": 96, "verdict": "PASS", "status": "ready_for_review"})
    # an intermediate candidate version must NOT appear in the queue
    _write(paths.candidates, "a_0001_v01_candidate.json",
           {"asset_id": "a_0001", "story_id": "ST-0001", "stage": "idea",
            "score": 80, "verdict": "PASS", "status": "candidate"})
    # a parked artifact MUST appear (machine fell short; Tone can overrule)
    _write(paths.parked, "b_0002_v04_parked.json",
           {"asset_id": "b_0002", "story_id": "ST-0001", "stage": "packaging",
            "score": 78, "verdict": "PASS", "status": "parked"})

    q = review.review_queue(channel_ws["channel"])
    by_id = {e["asset_id"]: e for e in q["pending"]}
    assert set(by_id) == {"a_0001", "b_0002"}              # intermediate excluded
    assert by_id["a_0001"]["machine_outcome"] == "passed"
    assert by_id["b_0002"]["machine_outcome"] == "parked"  # surfaced, not hidden
    assert by_id["a_0001"]["score"] == 96


def test_logged_items_leave_pending(channel_ws):
    paths = channel_ws["paths"]
    _write(paths.candidates, "a_0001_v03_ready_for_review.json",
           {"asset_id": "a_0001", "story_id": "ST-0001", "stage": "idea",
            "score": 96, "verdict": "PASS", "status": "ready_for_review"})
    paths.review_file.parent.mkdir(parents=True, exist_ok=True)
    paths.review_file.write_text("# Review journal\n\n## idea -- a_0001\nverdict: accept\n",
                                 encoding="utf-8")

    q = review.review_queue(channel_ws["channel"])
    assert q["pending"] == []
    assert [e["asset_id"] for e in q["reviewed"]] == ["a_0001"]


def test_all_channels_pending_lists_channel_with_pending(channel_ws):
    paths = channel_ws["paths"]
    _write(paths.candidates, "a_0001_v03_ready_for_review.json",
           {"asset_id": "a_0001", "story_id": "ST-0001", "stage": "idea",
            "score": 96, "verdict": "PASS", "status": "ready_for_review"})
    rows = review.all_channels_pending()
    assert any(r["channel"] == channel_ws["channel"] and len(r["pending"]) == 1
               for r in rows)
