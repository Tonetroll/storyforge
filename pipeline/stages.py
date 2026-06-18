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


# Pipeline order: idea -> theme -> structure
STAGES = {IDEA.name: IDEA, THEME.name: THEME, STORY.name: STORY}


def get_stage(name: str) -> Stage:
    if name not in STAGES:
        raise ValueError(f"Unknown stage '{name}'. Known: {sorted(STAGES)}")
    return STAGES[name]
