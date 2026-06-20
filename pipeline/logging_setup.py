"""Logs (what happened) + metrics (how it scored).

logs/<PROJECT>_run_<NNNN>.log   -- human-readable narrative of one run
metrics/scores.jsonl            -- one JSON row per scored version
memory/run_index.jsonl          -- one JSON row per run
"""

import json
import logging
import os
import time
from contextlib import contextmanager
from datetime import datetime, timezone

import config


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def _append_lock(target, timeout: float = 5.0, poll: float = 0.05):
    """Best-effort exclusive lock for appending to `target` (a Path), so two
    concurrent writers can't interleave/corrupt a line in the JSONL file.
    Cross-platform (an O_CREAT|O_EXCL lockfile). NEVER hangs the pipeline: if the
    lock can't be taken within `timeout` seconds (e.g. a stale lockfile left by a
    crashed run), it clears the stale lock and proceeds best-effort. Single-user,
    one-run-at-a-time use never contends; this only guards the rare overlap."""
    lockpath = target.parent / (target.name + ".lock")
    fd = None
    deadline = time.monotonic() + timeout
    while True:
        try:
            fd = os.open(str(lockpath), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            break
        except FileExistsError:
            if time.monotonic() >= deadline:
                try:
                    os.unlink(str(lockpath))          # clear a stale lock
                    fd = os.open(str(lockpath), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                except OSError:
                    fd = None                          # give up locking; still write
                break
            time.sleep(poll)
    try:
        yield
    finally:
        if fd is not None:
            os.close(fd)
            try:
                os.unlink(str(lockpath))
            except OSError:
                pass


def next_run_id(paths) -> int:
    paths.logs.mkdir(parents=True, exist_ok=True)
    highest = 0
    for f in paths.logs.glob(f"{config.PROJECT_NAME}_run_*.log"):
        digits = "".join(ch for ch in f.stem.split("_run_")[-1] if ch.isdigit())
        if digits:
            highest = max(highest, int(digits))
    return highest + 1


def get_run_logger(run_id: int, paths) -> logging.Logger:
    paths.logs.mkdir(parents=True, exist_ok=True)
    log_path = paths.logs / f"{config.PROJECT_NAME}_run_{run_id:04d}.log"
    logger = logging.getLogger(f"run_{paths.root.name}_{run_id}")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    logger.addHandler(fh)
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("  %(message)s"))
    logger.addHandler(ch)
    logger.info("=== run %04d started === project=%s channel=%s", run_id, config.PROJECT_NAME, paths.root.name)
    return logger


def write_metric(paths, row: dict) -> None:
    paths.metrics_file.parent.mkdir(parents=True, exist_ok=True)
    row = {"ts": _now(), **row}
    with _append_lock(paths.metrics_file):
        with open(paths.metrics_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")


def append_run_index(paths, row: dict) -> None:
    paths.run_index_file.parent.mkdir(parents=True, exist_ok=True)
    row = {"ts": _now(), **row}
    with _append_lock(paths.run_index_file):
        with open(paths.run_index_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")
