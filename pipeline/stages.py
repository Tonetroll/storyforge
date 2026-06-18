"""Stage registry: the pipeline as a list of reusable stages.

Each Stage fully defines one step. To add a new step you add: its three
signatures (in signatures.py), two standards MD files (in rules/standards/), and
one Stage entry here. The engine (orchestrator, scoring, naming, logging,
router, render) is generic over a Stage and needs no changes.
"""

from dataclasses import dataclass, field
from typing import Callable, Optional

from pipeline import signatures as S


@dataclass
class Stage:
    name: str                       # "idea", "title", ...
    content_label: str              # human label for the artifact, e.g. "IDEA"
    gen_sig: type                   # generator Signature
    gate_sig: type                  # evaluator/gate Signature
    iter_sig: type                  # iterator Signature
    content_fields: list            # judged + stored output field names
    topic_field: str                # which generator output names the artifact (for the slug)
    weights: dict                   # {criterion_number: max_points}  (must sum to SCORE_SCALE)
    labels: dict                    # {criterion_number: short label}
    gen_standard_file: str          # filename in rules/standards/ for the generator standard
    eval_standard_file: str         # filename in rules/standards/ for the gate criteria
    upstream: Optional[str] = None  # name of the stage whose accepted artifact feeds this one
    build_brief: Optional[Callable] = None  # (upstream_record) -> brief string
    penalty_points: int = 0         # subtracted from the score if the gate flags it (e.g. jargon); 0 = none
    verdict_floor: Optional[int] = None  # None = all-pass verdict; int = hybrid PASS if score >= floor
    gate_reads_package: bool = False  # if True, the assembled package is given to the gate (delivery check)


IDEA = Stage(
    name="idea",
    content_label="IDEA",
    gen_sig=S.GenerateIdea,
    gate_sig=S.GateIdea,
    iter_sig=S.IterateIdea,
    content_fields=["one_liner", "resolution", "reaction_1", "reaction_2", "viewer_action"],
    topic_field="topic",
    weights={1: 25, 2: 25, 3: 20, 4: 10, 5: 10, 6: 10},
    labels={
        1: "pull-in emotion (LOL/WTF/WOW)",
        2: "resolution emotion (Aah/Oooh/Finally)",
        3: "two DIFFERENT emotions",
        4: "exactly one viewer action",
        5: "open loop (premise doesn't give away the answer)",
        6: "one-liner concrete & speakable in <4s",
    },
    gen_standard_file="generator.md",
    eval_standard_file="evaluator.md",
    upstream=None,
    build_brief=None,
)


STORY = Stage(
    name="story",
    content_label="STORY STRUCTURE",
    gen_sig=S.GenerateStory,
    gate_sig=S.GateStory,
    iter_sig=S.IterateStory,
    content_fields=[
        "premise", "desire", "fear", "misbelief", "hook",
        "setup", "inciting_incident", "build_up", "plot_point_1", "pinch_point_1",
        "pre_midpoint", "midpoint", "post_midpoint", "pinch_point_2", "supposed_victory", "disaster",
        "dark_moment", "recovery", "climactic_confrontation", "victory", "resolution",
    ],
    topic_field="topic",
    weights={1: 25, 2: 20, 3: 15, 4: 15, 5: 15, 6: 10},
    labels={
        1: "character engine (desire/fear/misbelief linked)",
        2: "character arc closes (misbelief overcome in Recovery)",
        3: "midpoint is a true reversal",
        4: "disaster + dark moment land",
        5: "structural completeness (all beats, right order)",
        6: "hook + resolution",
    },
    gen_standard_file="story_generator.md",
    eval_standard_file="story_evaluator.md",
    upstream="theme",
    build_brief=lambda rec: (
        f"{rec.get('brief', '')}\n"
        f"Theme: {rec['content']['theme_statement']}\n"
        f"Central question: {rec['content']['central_question']}\n"
        f"Belief shift to dramatize: {rec['content']['belief_shift']}\n"
        "Build the 3-act outline so the protagonist's misbelief -> Recovery dramatizes this belief shift."
    ),
)


THEME = Stage(
    name="theme",
    content_label="THEME",
    gen_sig=S.GenerateTheme,
    gate_sig=S.GateTheme,
    iter_sig=S.IterateTheme,
    content_fields=["topic", "theme_statement", "central_question", "belief_shift"],
    topic_field="topic",
    weights={1: 25, 2: 20, 3: 20, 4: 15, 5: 10, 6: 10},
    labels={
        1: "stance, not a topic",
        2: "genuine tension (non-yes/no)",
        3: "implies a belief-shift",
        4: "not a moral",
        5: "universal through the specific",
        6: "one center of gravity",
    },
    gen_standard_file="theme_generator.md",
    eval_standard_file="theme_evaluator.md",
    upstream="idea",
    build_brief=lambda rec: (
        f"Accepted idea {rec.get('story_id', '')}:\n"
        f"  One-liner: {rec['content']['one_liner']}\n"
        f"  Resolution: {rec['content']['resolution']}\n"
        "Surface the theme this idea is really about."
    ),
)


STAKEBAKE = Stage(
    name="stakebake",
    content_label="STAKEBAKE (raised stakes)",
    gen_sig=S.GenerateStakebake,
    gate_sig=S.GateStakebake,
    iter_sig=S.IterateStakebake,
    content_fields=["premise", "desire", "fear", "misbelief", "hook",
                    "setup", "inciting_incident", "build_up", "plot_point_1", "pinch_point_1",
                    "pre_midpoint", "midpoint", "post_midpoint", "pinch_point_2", "supposed_victory", "disaster",
                    "dark_moment", "recovery", "climactic_confrontation", "victory", "resolution",
                    "stakes_added"],
    topic_field="topic",
    weights={1: 12, 2: 12, 3: 12, 4: 12, 5: 12, 6: 25, 7: 15},  # R1-R5 binary, G1-G2 graded; sums to 100
    labels={
        1: "value established early",
        2: "ticking clock / urgency",
        3: "tough choice / no-win",
        4: "personal consequences",
        5: "no safety nets",
        6: "emotional stakes land",
        7: "specific & relatable",
    },
    gen_standard_file="stakebake_generator.md",
    eval_standard_file="stakebake_evaluator.md",
    upstream="story",
    build_brief=lambda rec: (
        f"{rec.get('brief', '')}\n\nSTRUCTURE BEATS:\n"
        + "\n".join(f"- {k}: {v}" for k, v in (rec.get("content") or {}).items())
        + "\n\nRaise the stakes of this story per the pillars."
    ),
    penalty_points=15,    # jargon penalty
    verdict_floor=60,     # hybrid: PASS if score >= 60, iterate toward target
)


SCRIPT = Stage(
    name="script",
    content_label="SCRIPT (short-form)",
    gen_sig=S.GenerateScript,
    gate_sig=S.GateScript,
    iter_sig=S.IterateScript,
    content_fields=["hook", "body", "payoff", "cta", "loop_notes"],
    topic_field="topic",
    weights={1: 20, 2: 12, 3: 12, 4: 13, 5: 25, 6: 18},  # D1, L1, L2, L3, V1, V2; sums to 100
    labels={
        1: "delivery (stakes/theme/structure/hook)",
        2: "hook opens a loop",
        3: "head fake",
        4: "rehooks / no dead air",
        5: "tight & punchy",
        6: "visceral & speakable",
    },
    gen_standard_file="script_generator.md",
    eval_standard_file="script_evaluator.md",
    upstream="stakebake",
    build_brief=lambda rec: (
        f"{rec.get('brief', '')}\n\nRAISED-STAKES BEATS:\n"
        + "\n".join(f"- {k}: {v}" for k, v in (rec.get("content") or {}).items())
        + "\n\nWrite the short-form video script that delivers all of this."
    ),
    penalty_points=15,
    verdict_floor=60,
    gate_reads_package=True,   # the script gate reads the whole package to check delivery
)


SCRIPT_LONG = Stage(
    name="script_long",
    content_label="SCRIPT (long-form narration)",
    gen_sig=S.GenerateScript,
    gate_sig=S.GateScript,
    iter_sig=S.IterateScript,
    content_fields=["hook", "body", "payoff", "cta", "loop_notes"],
    topic_field="topic",
    weights={1: 20, 2: 12, 3: 12, 4: 13, 5: 25, 6: 18},
    labels={
        1: "delivery (stakes/theme/structure/hook)",
        2: "hook opens a loop",
        3: "head fake",
        4: "loops chain / no dead air",
        5: "immersive narration",
        6: "visceral & concrete",
    },
    gen_standard_file="script_long_generator.md",
    eval_standard_file="script_long_evaluator.md",
    upstream="stakebake",
    build_brief=lambda rec: (
        f"{rec.get('brief', '')}\n\nRAISED-STAKES BEATS:\n"
        + "\n".join(f"- {k}: {v}" for k, v in (rec.get("content") or {}).items())
        + "\n\nWrite the long-form narration script that delivers all of this."
    ),
    penalty_points=15,
    verdict_floor=60,
    gate_reads_package=True,
)


SCRIPT_SCREENPLAY = Stage(
    name="script_screenplay",
    content_label="SCREENPLAY (two-part)",
    gen_sig=S.GenerateScreenplay,
    gate_sig=S.GateScreenplay,
    iter_sig=S.IterateScreenplay,
    content_fields=["part_1", "part_2", "loop_notes"],
    topic_field="topic",
    weights={1: 20, 2: 12, 3: 12, 4: 13, 5: 25, 6: 18},
    labels={
        1: "delivery (stakes/theme/structure/hook)",
        2: "part 1 opens a loop",
        3: "head fake in part 2",
        4: "parts chain",
        5: "visual & image-generatable",
        6: "concrete & dramatic",
    },
    gen_standard_file="script_screenplay_generator.md",
    eval_standard_file="script_screenplay_evaluator.md",
    upstream="stakebake",
    build_brief=lambda rec: (
        f"{rec.get('brief', '')}\n\nRAISED-STAKES BEATS:\n"
        + "\n".join(f"- {k}: {v}" for k, v in (rec.get("content") or {}).items())
        + "\n\nWrite the two-part screenplay that delivers all of this."
    ),
    penalty_points=15,
    verdict_floor=60,
    gate_reads_package=True,
)


SCRIPT_PODCAST = Stage(
    name="script_podcast",
    content_label="SCRIPT (podcast)",
    gen_sig=S.GenerateScript,
    gate_sig=S.GateScript,
    iter_sig=S.IterateScript,
    content_fields=["hook", "body", "payoff", "cta", "loop_notes"],
    topic_field="topic",
    weights={1: 20, 2: 12, 3: 12, 4: 13, 5: 25, 6: 18},
    labels={
        1: "delivery (stakes/theme/structure/hook)",
        2: "cold open opens a loop",
        3: "head fake",
        4: "rehooks / volley",
        5: "natural conversation",
        6: "visceral & concrete",
    },
    gen_standard_file="script_podcast_generator.md",
    eval_standard_file="script_podcast_evaluator.md",
    upstream="stakebake",
    build_brief=lambda rec: (
        f"{rec.get('brief', '')}\n\nRAISED-STAKES BEATS:\n"
        + "\n".join(f"- {k}: {v}" for k, v in (rec.get("content") or {}).items())
        + "\n\nWrite the podcast conversation that delivers all of this."
    ),
    penalty_points=15,
    verdict_floor=60,
    gate_reads_package=True,
)


# Pipeline order: idea -> theme -> structure -> stakebake -> script
# Script alternates (all read the accepted stakebake):
#   script | script_long | script_screenplay | script_podcast
STAGES = {IDEA.name: IDEA, THEME.name: THEME, STORY.name: STORY, STAKEBAKE.name: STAKEBAKE,
          SCRIPT.name: SCRIPT, SCRIPT_LONG.name: SCRIPT_LONG,
          SCRIPT_SCREENPLAY.name: SCRIPT_SCREENPLAY, SCRIPT_PODCAST.name: SCRIPT_PODCAST}


def get_stage(name: str) -> Stage:
    if name not in STAGES:
        raise ValueError(f"Unknown stage '{name}'. Known: {sorted(STAGES)}")
    return STAGES[name]
