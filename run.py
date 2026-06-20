"""Entry point for the DSPy pipeline. Every run is scoped to a --channel (its own
self-contained workspace under channels/<name>/); the same engine runs any stage.

    python run.py new-channel demo-sports                # scaffold a channel workspace
    python run.py chain --channel demo-sports            # whole pipeline over that channel's seeds
    python run.py chain --channel demo-sports --brief "..." --dry-run  # plumbing smoke test (no keys)
    python run.py generate --channel demo-sports --stage idea --brief "..."   # one stage, live
    python run.py manual   --channel demo-sports --stage idea  # hand-authored content (no keys)
    python run.py route    --channel demo-sports         # apply that channel's human_review.csv
    python run.py learn    --channel demo-sports --stage idea  # retrain that channel's generator
"""

import argparse
import json
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


def main():
    parser = argparse.ArgumentParser(description="DSPy story pipeline")
    sub = parser.add_subparsers(dest="command")

    g = sub.add_parser("generate", help="run a stage end to end (gate -> score -> iterate)")
    g.add_argument("--stage", default="idea")
    g.add_argument("--brief", default="A rough seed to turn into a story.")
    g.add_argument("--dry-run", action="store_true", help="offline stub LMs, no API keys")
    g.add_argument("--channel", default=None, help="channel profile folder in channels/<name>/")

    m = sub.add_parser("manual", help="run hand-authored content + scores through the real pipeline")
    m.add_argument("--stage", default="idea")
    m.add_argument("--file", default="manual_input.json")
    m.add_argument("--channel", default=None, help="channel profile folder in channels/<name>/")

    c = sub.add_parser("chain", help="run the whole pipeline through to deliverables; stop at the weak link")
    c.add_argument("--channel", default=None, help="the channel workspace to run (channels/<name>/)")
    c.add_argument("--brief", default=None, help="run a single brief instead of the channel's seed queue")
    c.add_argument("--dry-run", action="store_true", help="placeholder content, no keys (plumbing test)")

    nc = sub.add_parser("new-channel", help="scaffold a new channel workspace under channels/<name>/")
    nc.add_argument("name", help="the channel name, e.g. demo-sports")

    pk = sub.add_parser("package", help="assemble a video's deliverables into one publish-ready doc")
    pk.add_argument("--channel", default=None, help="the channel workspace to package")
    pk.add_argument("--script", default="script", help="which script format to include (default: script)")

    r = sub.add_parser("route", help="(legacy) batch-apply a review file; reviews now happen in chat")
    r.add_argument("--channel", default=None, help="the channel workspace to route")

    rv = sub.add_parser("review", help="show what's awaiting your review (passes + parked), with the machine verdict per item")
    rv.add_argument("--channel", default=None, help="the channel workspace to review")
    rv.add_argument("--all", action="store_true", help="summarize pending reviews across all channels")

    l = sub.add_parser("learn", help="retrain a channel's stage generator from its accepted examples")
    l.add_argument("--stage", default="idea")
    l.add_argument("--channel", default=None, help="the channel workspace to learn from")
    l.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()
    command = args.command or "generate"

    if command == "generate":
        from pipeline import orchestrator
        result = orchestrator.run(stage_name=args.stage, brief=args.brief,
                                  dry_run=getattr(args, "dry_run", False), channel=args.channel)
        print("\nRESULT:", result)
    elif command == "manual":
        from pipeline import orchestrator
        data = json.loads(Path(args.file).read_text(encoding="utf-8"))
        result = orchestrator.run(
            stage_name=args.stage,
            brief=data.get("brief", "manual test"),
            scripted={"gen_answers": data["gen_answers"], "eval_answers": data["eval_answers"]},
            channel=args.channel,
        )
        print("\nRESULT:", result)
    elif command == "chain":
        from pipeline import chain
        if args.brief:
            results = [chain.run_chain(args.brief, channel=args.channel, dry_run=args.dry_run)]
        else:
            results = chain.run_channel(args.channel, dry_run=args.dry_run)
        print(f"\n================ RUN-THROUGH SUMMARY (channel: {args.channel or '_sandbox'}) ================")
        for r in results:
            print(f"\nseed: {r['brief'][:70]}")
            for s in r["trail"]:
                mark = "OK " if s["outcome"] == "ready_for_review" else "STOP"
                print(f"  [{mark}] {s['stage']:<10} {s['outcome']:<16} score={s['score']}")
            if r["stopped_at"]:
                print(f"  >> WEAK LINK: stopped at '{r['stopped_at']}' ({r['reason']}) - review/fix this stage.")
            else:
                print(f"  >> reached deliverables: {', '.join(d['stage'] for d in r['deliverables'])} - ready for your review.")
    elif command == "new-channel":
        from pipeline import channel_setup
        info = channel_setup.create_channel(args.name)
        verb = "already exists" if info["already_existed"] else "created"
        print(f"Channel '{info['channel']}' {verb} at {info['root']}")
        print(f"  1. Fill the audience: {info['profile']}")
        print(f"  2. Add ideas:        {info['seeds']}")
        print(f"  3. Run it:           python run.py chain --channel {info['channel']}")
    elif command == "package":
        from pipeline import packager
        out = packager.build_package(args.channel, script_stage=args.script)
        if out:
            print(f"Video package written -> {out}")
    elif command == "route":
        from pipeline import router
        print(f"Routing reviewed artifacts for channel '{args.channel or '_sandbox'}'...")
        router.route_all(channel=args.channel)
    elif command == "review":
        from pipeline import review
        if getattr(args, "all", False):
            review.print_all_pending()
        else:
            review.print_queue(args.channel)
    elif command == "learn":
        from pipeline import learn
        learn.compile_generator(stage_name=args.stage, channel=args.channel,
                                dry_run=getattr(args, "dry_run", False))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
