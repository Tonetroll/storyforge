"""C10: the JSONL append paths (metrics + run-index) are guarded by a
best-effort, timeout-bounded lock so concurrent writers can't interleave a
line -- and, critically, the lock can NEVER hang the pipeline (a stale lock is
stolen after the timeout). Single-user use never contends; these pin the guard."""

import json
import time

from pipeline import logging_setup


def test_write_metric_appends_valid_jsonl_and_cleans_lock(channel_ws):
    paths = channel_ws["paths"]
    logging_setup.write_metric(paths, {"run_id": 1, "score": 90})
    logging_setup.write_metric(paths, {"run_id": 2, "score": 95})
    rows = [json.loads(l) for l in paths.metrics_file.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 2
    assert rows[0]["run_id"] == 1 and rows[1]["score"] == 95
    assert all("ts" in r for r in rows)                     # ts still stamped
    lockpath = paths.metrics_file.parent / (paths.metrics_file.name + ".lock")
    assert not lockpath.exists()                            # no leftover lock


def test_append_run_index_appends_valid_jsonl_and_cleans_lock(channel_ws):
    paths = channel_ws["paths"]
    logging_setup.append_run_index(paths, {"run_id": 1, "outcome": "ready_for_review"})
    rows = [json.loads(l) for l in paths.run_index_file.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 1 and rows[0]["outcome"] == "ready_for_review"
    lockpath = paths.run_index_file.parent / (paths.run_index_file.name + ".lock")
    assert not lockpath.exists()


def test_append_lock_uncontended_holds_then_releases(tmp_path):
    target = tmp_path / "x.jsonl"
    target.write_text("", encoding="utf-8")
    lockpath = tmp_path / "x.jsonl.lock"
    with logging_setup._append_lock(target):
        assert lockpath.exists()                            # held during the block
    assert not lockpath.exists()                            # released after


def test_append_lock_stale_lock_does_not_hang(tmp_path):
    """A stale lockfile (left by a crashed run) must NOT deadlock: the lock is
    stolen once the timeout elapses, and the block still runs."""
    target = tmp_path / "x.jsonl"
    target.write_text("", encoding="utf-8")
    lockpath = tmp_path / "x.jsonl.lock"
    lockpath.write_text("", encoding="utf-8")               # simulate stale lock
    start = time.monotonic()
    reached = False
    with logging_setup._append_lock(target, timeout=0.1, poll=0.02):
        reached = True
    assert reached                                          # proceeded despite stale lock
    assert (time.monotonic() - start) < 2.0                 # bounded, did not hang
    assert not lockpath.exists()                            # stale lock cleared + released
