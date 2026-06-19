"""Entry point for the DSPy pipeline. Every command takes a --stage (default
"idea"), so the same engine runs any stage in pipeline/stages.py.

    python run.py generate --stage idea --brief "..."   # live (needs API keys)
    python run.py generate --dry-run                     # offline idea-stage smoke test
    python run.py manual --stage idea                    # hand-authored content (no keys)
    python run.py chain --seeds seeds/briefs.jsonl       # whole pipeline, review at the end
    python run.py chain --brief "..." --dry-run          # plumbing smoke test (no keys)
    python run.py route                                  # apply human_review.csv decisions
    python run.py learn --stage idea                     # retrain a stage's generator
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
    c.add_argument("--seeds", default="seeds/briefs.jsonl", help="JSONL of {brief, channel} seeds")
    c.add_argument("--brief", default=None, help="run a single brief instead of the seeds file")
    c.add_argument("--channel", default=None, help="channel profile folder in channels/<name>/")
    c.add_argument("--dry-run", action="store_true", help="placeholder content, no keys (plumbing test)")

    sub.add_parser("route", help="apply review/human_review.csv decisions")

    l = sub.add_parser("learn", help="retrain a stage's generator from accepted examples")
    l.add_argument("--stage", default="idea")
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
            results = chain.run_seeds(args.seeds, dry_run=args.dry_run)
        print("\n================ RUN-THROUGH SUMMARY ================")
        for r in results:
            print(f"\nseed: {r['brief'][:70]}")
            for s in r["trail"]:
                mark = "OK " if s["outcome"] == "ready_for_review" else "STOP"
                print(f"  [{mark}] {s['stage']:<10} {s['outcome']:<16} score={s['score']}")
            if r["stopped_at"]:
                print(f"  >> WEAK LINK: stopped at '{r['stopped_at']}' ({r['reason']}) - review/fix this stage.")
            else:
                print(f"  >> reached deliverables: {', '.join(d['stage'] for d in r['deliverables'])} - ready for your review.")
    elif command == "learn":
        from pipeline import learn
        learn.compile_generator(stage_name=args.stage, dry_run=getattr(args, "dry_run", False))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
