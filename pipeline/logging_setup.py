"""Logs (what happened) + metrics (how it scored).

logs/<PROJECT>_run_<NNNN>.log   -- human-readable narrative of one run
metrics/scores.jsonl            -- one JSON row per scored version
memory/run_index.jsonl          -- one JSON row per run
"""

import json
import logging
from datetime import datetime, timezone

import config


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


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
    with open(paths.metrics_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")


def append_run_index(paths, row: dict) -> None:
    paths.run_index_file.parent.mkdir(parents=True, exist_ok=True)
    row = {"ts": _now(), **row}
    with open(paths.run_index_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")
