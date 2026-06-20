"""Scaffold a new channel: a self-contained production line under channels/<name>/.

Creates the directory tree (outputs / logs / metrics / review / memory / seeds),
copies the positioning template into profile.md for you to fill, and drops an
empty seed queue + a fresh review inbox. Idempotent: re-running won't clobber an
existing profile or seeds.
"""

import config


def create_channel(name: str) -> dict:
    name = name.strip().strip("/\\")
    if not name or name.startswith("_"):
        raise ValueError(f"Invalid channel name '{name}'. Use a plain name like 'demo-sports'.")
    P = config.paths_for(name)
    existed = P.profile.exists()

    for d in P.output_dirs() + [P.logs, P.compiled, P.metrics_file.parent,
                                P.review_file.parent, P.seeds.parent]:
        d.mkdir(parents=True, exist_ok=True)

    if not P.profile.exists():
        template = (config.CHANNELS_DIR / "_TEMPLATE" / "profile.md").read_text(encoding="utf-8")
        P.profile.write_text(template, encoding="utf-8")
    if not P.seeds.exists():
        P.seeds.write_text(
            "# Write your ideas here -- one idea per line, in plain words.\n"
            "# The channel is the workspace, so you don't name it per line.\n",
            encoding="utf-8")
    if not P.review_file.exists():
        P.review_file.write_text(
            "# Review journal\n\n"
            "Reviews happen in conversation with Claude, not here. This file is the\n"
            "permanent, append-only record of each verdict + the reasoning behind it.\n"
            "Don't hand-edit it -- Claude writes an entry every time you review.\n",
            encoding="utf-8")

    return {"channel": name, "root": str(P.root), "already_existed": existed,
            "profile": str(P.profile), "seeds": str(P.seeds)}
