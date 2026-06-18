"""Entry point for the DSPy idea pipeline.

    python run.py generate --brief "..."     # run the loop (live; needs API keys)
    python run.py generate --dry-run          # offline wiring test, no keys, no spend
    python run.py route                       # apply human_review.csv decisions
    python run.py learn                        # retrain generator from accepted examples
    python run.py learn --dry-run

Loads API keys from .env if present. Reads evaluation criteria from
rules/standards/*.md (concatenated); falls back to a placeholder until you add
your standards in Phase B.
"""

import argparse
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

import config


def _read_standard(filename: str, fallback: str) -> str:
    path = config.STANDARDS_DIR / filename
    if path.exists():
        return path.read_text(encoding="utf-8")
    return fallback


def load_generator_standard() -> str:
    """The bar the generator builds to (rules/standards/generator.md)."""
    return _read_standard("generator.md",
                          "PLACEHOLDER: generate a complete story idea with an open loop and a defined resolution.")


def load_evaluator_criteria() -> str:
    """The gate the evaluator enforces (rules/standards/evaluator.md)."""
    return _read_standard("evaluator.md",
                          "PLACEHOLDER: PASS only if the idea has two distinct emotions, one viewer action, an open loop, and a concrete <4s one-liner.")


def main():
    parser = argparse.ArgumentParser(description="DSPy idea pipeline")
    sub = parser.add_subparsers(dest="command")

    g = sub.add_parser("generate", help="run the generate->evaluate->iterate->reevaluate loop")
    g.add_argument("--brief", default="DRY-RUN brief: generate one strong idea.",
                   help="the seed/brief to generate from")
    g.add_argument("--dry-run", action="store_true", help="offline stub LMs, no API keys needed")

    m = sub.add_parser("manual", help="run hand-authored idea + scores through the real pipeline (no keys)")
    m.add_argument("--file", default="manual_input.json", help="path to the hand-authored content file")

    sub.add_parser("route", help="apply review/human_review.csv decisions")

    l = sub.add_parser("learn", help="retrain the generator from accepted examples")
    l.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()
    command = args.command or "generate"

    if command == "generate":
        from pipeline import orchestrator
        result = orchestrator.run(brief=args.brief,
                                  gen_standard=load_generator_standard(),
                                  eval_criteria=load_evaluator_criteria(),
                                  dry_run=getattr(args, "dry_run", False))
        print("\nRESULT:", result)
    elif command == "manual":
        import json
        from pathlib import Path
        from pipeline import orchestrator
        data = json.loads(Path(args.file).read_text(encoding="utf-8"))
        result = orchestrator.run(
            brief=data.get("brief", "manual test"),
            gen_standard=load_generator_standard(),
            eval_criteria=load_evaluator_criteria(),
            scripted={"gen_answers": data["gen_answers"], "eval_answers": data["eval_answers"]},
        )
        print("\nRESULT:", result)
    elif command == "route":
        from pipeline import router
        print("Routing reviewed artifacts...")
        router.route_all()
    elif command == "learn":
        from pipeline import learn
        learn.compile_generator(gen_standard=load_generator_standard(),
                                eval_criteria=load_evaluator_criteria(),
                                dry_run=getattr(args, "dry_run", False))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
