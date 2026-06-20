"""Auto-cleanup: superseded draft revisions move to archived/; terminals untouched."""

import json

from pipeline import cleanup, naming


def _write(d, slug, number, version, status):
    d.mkdir(parents=True, exist_ok=True)
    base = naming.format_name(slug, number, version, status)
    (d / f"{base}.json").write_text(json.dumps({"slug": slug}), encoding="utf-8")
    (d / f"{base}.txt").write_text("x", encoding="utf-8")


def test_settled_asset_drafts_all_archived(channel_ws):
    paths = channel_ws["paths"]
    # Asset alpha: a parked terminal + 3 intermediate drafts (all superseded)
    _write(paths.candidates, "alpha", 1, 1, "candidate")
    _write(paths.candidates, "alpha", 1, 2, "revised")
    _write(paths.candidates, "alpha", 1, 3, "revised")
    _write(paths.parked, "alpha", 1, 5, "parked")

    result = cleanup.cleanup_channel(paths)

    assert not list(paths.candidates.glob("alpha_0001_*")), "settled drafts should be gone from drafts/"
    assert (paths.parked / "alpha_0001_v05_parked.json").exists(), "terminal must be untouched"
    assert {p.name for p in paths.archived.glob("alpha_0001_*.json")} == {
        "alpha_0001_v01_candidate.json",
        "alpha_0001_v02_revised.json",
        "alpha_0001_v03_revised.json",
    }


def test_inflight_asset_keeps_only_latest_draft(channel_ws):
    paths = channel_ws["paths"]
    # Asset beta: no terminal yet -> keep the latest draft, archive older
    _write(paths.candidates, "beta", 2, 1, "candidate")
    _write(paths.candidates, "beta", 2, 2, "revised")

    cleanup.cleanup_channel(paths)

    assert {p.name for p in paths.candidates.glob("beta_0002_*.json")} == {"beta_0002_v02_revised.json"}
    assert {p.name for p in paths.archived.glob("beta_0002_*.json")} == {"beta_0002_v01_candidate.json"}


def test_cleanup_moves_both_json_and_txt(channel_ws):
    paths = channel_ws["paths"]
    _write(paths.candidates, "gamma", 3, 1, "candidate")
    _write(paths.candidates, "gamma", 3, 2, "revised")
    result = cleanup.cleanup_channel(paths)
    # v01 archived = 2 files (json + txt); v02 kept
    assert result == {"archived": 2, "kept": 1}
    assert (paths.archived / "gamma_0003_v01_candidate.txt").exists()
