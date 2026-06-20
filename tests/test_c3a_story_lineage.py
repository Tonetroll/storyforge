"""C3a: every artifact of ONE video should share a single ST-#### story id,
threaded from the idea stage through every downstream stage -- instead of each
stage minting its own id from its own asset number."""

import json

from pipeline import chain


def _records(paths):
    recs = []
    for d in paths.output_dirs():
        if not d.exists():
            continue
        for f in d.glob("*.json"):
            recs.append(json.loads(f.read_text(encoding="utf-8")))
    return recs


def test_one_story_id_across_the_whole_video(channel_ws):
    chain.run_chain("A lighthouse keeper's last night.",
                    channel=channel_ws["channel"], dry_run=True)
    ids = [r["story_id"] for r in _records(channel_ws["paths"]) if r.get("story_id")]
    assert ids, "no artifacts with a story_id were produced"
    assert len(set(ids)) == 1, (
        f"expected ONE shared story id for the whole video, got {sorted(set(ids))}"
    )


def test_formats_share_the_id_but_stay_separable(channel_ws):
    """The video's four script formats carry the SAME story id (one video) but
    remain distinguishable by their `stage` (short / long / screenplay / podcast)."""
    chain.run_chain("A lighthouse keeper's last night.",
                    channel=channel_ws["channel"], dry_run=True)
    recs = _records(channel_ws["paths"])
    script_stages = {"script", "script_long", "script_screenplay", "script_podcast"}
    by_stage = {r["stage"]: r["story_id"] for r in recs if r.get("stage") in script_stages}
    # all four formats were produced...
    assert script_stages.issubset(by_stage), f"missing formats: {script_stages - set(by_stage)}"
    # ...they all share the one video id...
    assert len(set(by_stage.values())) == 1, f"formats disagree on story id: {by_stage}"
    # ...and they are still SEPARATE artifacts (distinct stages == distinct formats).
    assert len(by_stage) == 4
