"""Naming + status protocol.

Filename: <slug>_<NUMBER>_v<VERSION>_<STATUS>.json
where <slug> is what the idea is ABOUT (kebab-case), so artifacts are findable
instead of a generic repeated prefix.
Example:  elevator-mirror-practiced-fine_0002_v02_revised.json

Status state machine:
    candidate -> revised -> ready_for_review        (pipeline)
    ready_for_review -> accepted | rejected | revise (human review)
    accepted -> promoted        rejected -> archived  revise -> (back to iterator)
Terminal: promoted, killed, archived
"""

import re
from pathlib import Path

# Status vocabulary
PIPELINE_STATUSES = {"candidate", "revised", "ready_for_review", "parked"}
REVIEW_STATUSES = {"accepted", "rejected", "revise"}
TERMINAL_STATUSES = {"promoted", "archived", "killed"}
ALL_STATUSES = PIPELINE_STATUSES | REVIEW_STATUSES | TERMINAL_STATUSES

# Allowed transitions (status -> set of next statuses)
# "parked" = passed the gate but could not reach TARGET_SCORE within MAX_ITER;
# set aside (not killed) so we can learn from near-misses.
TRANSITIONS = {
    "candidate": {"revised", "ready_for_review", "parked"},
    "revised": {"revised", "ready_for_review", "parked"},
    "ready_for_review": {"accepted", "rejected", "revise"},
    "parked": {"revised", "killed"},
    "accepted": {"promoted", "killed"},
    "rejected": {"archived"},
    "revise": {"revised", "ready_for_review"},
    "promoted": set(),
    "archived": set(),
    "killed": set(),
}

_NAME_RE = re.compile(
    r"^(?P<slug>[a-z0-9-]+)_(?P<number>\d{4})_v(?P<version>\d{2})_(?P<status>[a-z_]+)$"
)


def slugify(text: str, max_words: int = 6, max_len: int = 60) -> str:
    """Make a findable, filesystem-safe kebab slug from what the idea is about."""
    text = str(text).lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    words = [w for w in re.split(r"[\s-]+", text) if w]
    slug = "-".join(words[:max_words])[:max_len].strip("-")
    return slug or "untitled"


def format_name(slug: str, number: int, version: int, status: str) -> str:
    """Build a base filename (no extension): <slug>_<NNNN>_v<VV>_<status>."""
    if status not in ALL_STATUSES:
        raise ValueError(f"Unknown status '{status}'. Allowed: {sorted(ALL_STATUSES)}")
    return f"{slug}_{number:04d}_v{version:02d}_{status}"


def parse_name(name: str) -> dict:
    """Parse a base filename (extension stripped) into its parts."""
    stem = Path(name).stem
    m = _NAME_RE.match(stem)
    if not m:
        raise ValueError(f"'{name}' does not match the naming protocol.")
    d = m.groupdict()
    d["number"] = int(d["number"])
    d["version"] = int(d["version"])
    return d


def can_transition(current: str, nxt: str) -> bool:
    return nxt in TRANSITIONS.get(current, set())


def next_number(search_dirs) -> int:
    """Next global asset NUMBER, scanning existing files across the given dirs."""
    highest = 0
    for d in search_dirs:
        d = Path(d)
        if not d.exists():
            continue
        for f in d.glob("*.json"):
            try:
                parts = parse_name(f.name)
            except ValueError:
                continue
            highest = max(highest, parts["number"])
    return highest + 1
