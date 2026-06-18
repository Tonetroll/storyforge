"""Router: turns human review decisions into system actions.

Reads review/human_review.csv (columns: asset_id | module | version | score |
status | reason | next_action) and routes each reviewed artifact:

    status=accepted -> move to outputs/ideas/accepted/, promote to memory/trainset.jsonl
    status=rejected -> move to outputs/ideas/rejected/  (then archived)
    status=revise   -> leave in candidates for another orchestrator pass

The next_action column is free-form routing intent you can extend (e.g.
"promote", "archive", "rerun"); it is logged so the system records the why.
"""

import csv
import json
import shutil
from datetime import datetime, timezone

import config
from pipeline import naming, render


def _load_reviews():
    if not config.REVIEW_FILE.exists():
        return []
    with open(config.REVIEW_FILE, newline="", encoding="utf-8") as f:
        return [row for row in csv.DictReader(f)]


def _find_artifact(asset_id: str, version: str):
    """Locate the artifact file for an asset_id + version in candidates/."""
    want_version = int(str(version).lstrip("vV"))
    for f in config.CANDIDATES_DIR.glob("*.json"):
        try:
            parts = naming.parse_name(f.name)
        except ValueError:
            continue
        this_asset = f"{parts['slug']}_{parts['number']:04d}"
        if this_asset == asset_id and parts["version"] == want_version:
            return f, parts
    return None, None


def _promote_to_trainset(record: dict, review: dict) -> None:
    """Accepted artifact becomes a training example for the generator."""
    config.MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    example = {
        "brief": record.get("brief", ""),
        "idea": record.get("idea", {}),
        "story_id": record.get("story_id"),
        "human_score": review.get("score"),
        "reason": review.get("reason"),
        "asset_id": review.get("asset_id"),
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    with open(config.TRAINSET_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(example) + "\n")


def route_all(verbose: bool = True) -> list:
    actions = []
    for review in _load_reviews():
        status = (review.get("status") or "").strip().lower()
        asset_id = (review.get("asset_id") or "").strip()
        version = (review.get("version") or "").strip()
        if status not in naming.REVIEW_STATUSES:
            continue
        src, parts = _find_artifact(asset_id, version)
        if src is None:
            actions.append({"asset_id": asset_id, "version": version, "result": "artifact_not_found"})
            continue
        record = json.loads(src.read_text(encoding="utf-8"))

        if status == "accepted":
            dest_dir, new_status = config.ACCEPTED_DIR, "promoted"
            _promote_to_trainset(record, review)
        elif status == "rejected":
            dest_dir, new_status = config.REJECTED_DIR, "archived"
        else:  # revise
            actions.append({"asset_id": asset_id, "version": version, "result": "left_for_revision",
                            "next_action": review.get("next_action")})
            continue

        dest_dir.mkdir(parents=True, exist_ok=True)
        new_base = naming.format_name(parts["slug"], parts["number"], parts["version"], new_status)
        record["status"] = new_status
        record["review"] = {"score": review.get("score"), "reason": review.get("reason"),
                            "next_action": review.get("next_action")}
        dest = dest_dir / f"{new_base}.json"
        dest.write_text(json.dumps(record, indent=2), encoding="utf-8")
        (dest_dir / f"{new_base}.txt").write_text(render.to_text(record), encoding="utf-8")
        src.unlink()
        src.with_suffix(".txt").unlink(missing_ok=True)
        actions.append({"asset_id": asset_id, "version": version, "result": new_status,
                        "moved_to": str(dest.relative_to(config.BASE_DIR)),
                        "next_action": review.get("next_action")})

    if verbose:
        for a in actions:
            print(f"  {a.get('asset_id')} {a.get('version')} -> {a.get('result')}"
                  + (f" ({a['moved_to']})" if a.get("moved_to") else ""))
    return actions
