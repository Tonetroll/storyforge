"""Auto-cleanup: keep the working folders from overpopulating.

drafts/ accumulates every intermediate revision (v01..vN) of every asset, across
every run. Once an asset is SETTLED -- parked, promoted (accepted), or rejected --
its draft revisions are superseded. This MOVES superseded drafts to archived/
(never deletes -- recoverable), so drafts/ holds only live, not-yet-settled work.

Safe by construction: it only ever touches files under this channel's drafts/,
and only MOVES them into this channel's archived/. Terminals (parked/accepted/
rejected) are never touched.
"""

from pipeline import naming


def cleanup_channel(paths) -> dict:
    """Archive superseded draft revisions for a channel. Returns
    {'archived': <files moved>, 'kept': <live drafts kept>}.

    - An asset with a terminal artifact (parked/accepted/rejected) -> ALL its
      drafts are superseded -> archived.
    - An asset still in flight (no terminal yet) -> keep only its latest draft,
      archive the older revisions.
    """
    drafts = paths.candidates
    if not drafts.exists():
        return {"archived": 0, "kept": 0}

    # Assets that have reached a terminal home: all their drafts are superseded.
    settled = set()
    for d in (paths.parked, paths.accepted, paths.rejected):
        if not d.exists():
            continue
        for f in d.glob("*.json"):
            try:
                p = naming.parse_name(f.name)
            except ValueError:
                continue
            settled.add((p["slug"], p["number"]))

    # Group draft .json files by asset (slug, number).
    groups = {}
    for f in drafts.glob("*.json"):
        try:
            p = naming.parse_name(f.name)
        except ValueError:
            continue
        groups.setdefault((p["slug"], p["number"]), []).append((p["version"], f))

    archived = kept = 0
    for asset, versions in groups.items():
        versions.sort(key=lambda vf: vf[0])
        if asset in settled:
            to_archive, keep = versions, []
        else:
            to_archive, keep = versions[:-1], versions[-1:]  # keep only the latest live draft
        kept += len(keep)
        for _ver, jsonf in to_archive:
            for ext in (".json", ".txt"):
                src = jsonf.with_suffix(ext)
                if src.exists():
                    paths.archived.mkdir(parents=True, exist_ok=True)
                    src.replace(paths.archived / src.name)
                    archived += 1
    return {"archived": archived, "kept": kept}
