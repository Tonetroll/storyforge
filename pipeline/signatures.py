"""DSPy Signatures, grouped by pipeline STAGE.

The written standards live in rules/standards/*.md and are passed in at runtime
as `standard` / `criteria`. These signatures define the SHAPE of each stage: the
generator's output fields, the gate's per-criterion scores, and the revision.

Every stage follows the same uniform interface so the engine stays generic:
  generator:  (brief, standard) -> <content fields> + topic
  gate:       (<content fields>, criteria) -> verdict, score_1..N, failed_checks, why
  iterator:   (<content fields>, critique, standard) -> improved_<content field>...
"""

import dspy


# ===========================================================================
# IDEA stage
# ===========================================================================
class GenerateIdea(dspy.Signature):
    """Generate ONE story idea from the brief, following the standard.

    A story evokes two DIFFERENT emotions: a pull-in that opens a loop and a
    resolution that closes it. Information is not a story. Output both halves --
    the open-loop one-liner AND the resolution. Never leave the resolution
    blank. Do not write a beautiful sentence that tells instead of opens."""

    brief = dspy.InputField(desc="The seed/brief: what to make a story idea about.")
    standard = dspy.InputField(desc="The generator standard the idea MUST satisfy.")
    one_liner = dspy.OutputField(desc="The open loop. Concrete, speakable in under 4 seconds, no abstraction. Does NOT give away the answer.")
    resolution = dspy.OutputField(desc="The payoff that closes the loop toward the end. Defined, never blank.")
    reaction_1 = dspy.OutputField(desc="Pull-in emotion, one of: LOL / WTF / WOW.")
    reaction_2 = dspy.OutputField(desc="Resolution emotion, one of: Aah / Oooh / Finally. MUST differ from reaction_1.")
    viewer_action = dspy.OutputField(desc="Exactly ONE: Do / Sale / Sign-up / Save / Share / Try / Apply / Reflect.")
    topic = dspy.OutputField(desc="3-6 words naming what THIS story is about, for the filename. Concrete subject. NEVER generic words like 'story', 'idea', or 'video'.")


class GateIdea(dspy.Signature):
    """You are a strict, impartial gate. You did NOT write this idea; do not be
    generous. Score each of the six checks 0..its max by HOW STRONGLY it is met.
    A check scoring 0 = absent = REJECT. Otherwise PASS."""

    one_liner = dspy.InputField()
    resolution = dspy.InputField()
    reaction_1 = dspy.InputField()
    reaction_2 = dspy.InputField()
    viewer_action = dspy.InputField()
    criteria = dspy.InputField(desc="The gate: the six checks, their weights, and the verdict rule.")
    verdict = dspy.OutputField(desc="Exactly 'PASS' or 'REJECT'. REJECT if ANY check scores 0.")
    score_1 = dspy.OutputField(desc="Check 1 pull-in emotion: integer 0-25. 0 = absent.")
    score_2 = dspy.OutputField(desc="Check 2 resolution emotion: integer 0-25. 0 = absent.")
    score_3 = dspy.OutputField(desc="Check 3 two DIFFERENT emotions: integer 0-20. 0 = same twice or one missing.")
    score_4 = dspy.OutputField(desc="Check 4 exactly one viewer action: integer 0-10. 0 = none or more than one.")
    score_5 = dspy.OutputField(desc="Check 5 open loop: integer 0-10. 0 = premise gives away the answer.")
    score_6 = dspy.OutputField(desc="Check 6 concrete & speakable <4s: integer 0-10. 0 = abstract or too long.")
    failed_checks = dspy.OutputField(desc="If REJECT: the failing check numbers + one line each. If PASS: 'none'.")
    why = dspy.OutputField(desc="One line.")


class IterateIdea(dspy.Signature):
    """Improve a PASSING idea using the gate's critique to push the score higher.
    Keep what works; sharpen the hook, deepen the payoff, tighten the one-liner."""

    one_liner = dspy.InputField()
    resolution = dspy.InputField()
    reaction_1 = dspy.InputField()
    reaction_2 = dspy.InputField()
    viewer_action = dspy.InputField()
    critique = dspy.InputField(desc="The gate's why + weak points to push higher.")
    standard = dspy.InputField(desc="The generator standard to hold to.")
    improved_one_liner = dspy.OutputField(desc="Sharper open-loop one-liner, still <4s and concrete.")
    improved_resolution = dspy.OutputField(desc="Stronger payoff that closes the loop.")
    improved_reaction_1 = dspy.OutputField(desc="Pull-in emotion (LOL/WTF/WOW).")
    improved_reaction_2 = dspy.OutputField(desc="Resolution emotion (Aah/Oooh/Finally), different from reaction_1.")
    improved_viewer_action = dspy.OutputField(desc="Exactly ONE viewer action.")


# ===========================================================================
# STORY STRUCTURE stage  (downstream of idea)
# ===========================================================================
class GenerateStory(dspy.Signature):
    """Turn the premise (an accepted idea) into a full 3-act outline driven by
    the protagonist's internal change. The misbelief named in Act 1 MUST be the
    thing overcome in Recovery. Hitting beats without an internal arc is plot,
    not story. Bullet every beat: concrete and speakable."""

    brief = dspy.InputField(desc="The accepted idea this outline is built from (the premise).")
    standard = dspy.InputField(desc="The generator standard (rules/standards/story_generator.md).")
    premise = dspy.OutputField(desc="The basic idea in one line.")
    desire = dspy.OutputField(desc="What the protagonist wants + thinks will make them happy.")
    fear = dspy.OutputField(desc="What stops them going after what would make them happy.")
    misbelief = dspy.OutputField(desc="The false thing they believe about the world, which feeds off the fear.")
    hook = dspy.OutputField(desc="Grab the reader with the protagonist's inner conflict.")
    setup = dspy.OutputField(desc="Something is about to happen to the protagonist; the reader can feel it.")
    inciting_incident = dspy.OutputField(desc="Something throws the protagonist outside their comfort zone.")
    build_up = dspy.OutputField(desc="The protagonist will have to face this thing head on.")
    plot_point_1 = dspy.OutputField(desc="A decision that determines what happens next.")
    pinch_point_1 = dspy.OutputField(desc="The opposition / antagonistic force looms in the distance.")
    pre_midpoint = dspy.OutputField(desc="In pursuit of the goal, but something stands in the way (reactionary hero).")
    midpoint = dspy.OutputField(desc="Plot twist - everything changes.")
    post_midpoint = dspy.OutputField(desc="The midpoint forces a change of gears toward the goal (action hero).")
    pinch_point_2 = dspy.OutputField(desc="The antagonist gets closer to disrupting the protagonist's life.")
    supposed_victory = dspy.OutputField(desc="The protagonist feels sure they'll win; disaster is on the way.")
    disaster = dspy.OutputField(desc="Something goes wrong. The reader saw it coming; the protagonist did not.")
    dark_moment = dspy.OutputField(desc="The protagonist feels lost; their specific fear challenges them again.")
    recovery = dspy.OutputField(desc="The protagonist overcomes the misbelief to reach the climax (the change).")
    climactic_confrontation = dspy.OutputField(desc="The protagonist faces their biggest challenge of all.")
    victory = dspy.OutputField(desc="The protagonist overcomes.")
    resolution = dspy.OutputField(desc="Loose ends wrapped; the reader is satisfied.")
    topic = dspy.OutputField(desc="3-6 words naming what this story is about, for the filename. No generic words.")


class GateStory(dspy.Signature):
    """You are a strict, impartial gate for a story outline. A structure that hits
    beats but has no internal arc is plot, not story - score it low. Grade each
    check 0..its max by how strongly it is met. A check at 0 = absent = REJECT."""

    premise = dspy.InputField()
    desire = dspy.InputField()
    fear = dspy.InputField()
    misbelief = dspy.InputField()
    hook = dspy.InputField()
    setup = dspy.InputField()
    inciting_incident = dspy.InputField()
    build_up = dspy.InputField()
    plot_point_1 = dspy.InputField()
    pinch_point_1 = dspy.InputField()
    pre_midpoint = dspy.InputField()
    midpoint = dspy.InputField()
    post_midpoint = dspy.InputField()
    pinch_point_2 = dspy.InputField()
    supposed_victory = dspy.InputField()
    disaster = dspy.InputField()
    dark_moment = dspy.InputField()
    recovery = dspy.InputField()
    climactic_confrontation = dspy.InputField()
    victory = dspy.InputField()
    resolution = dspy.InputField()
    criteria = dspy.InputField(desc="The gate: the six checks, their weights, and the verdict rule.")
    verdict = dspy.OutputField(desc="Exactly 'PASS' or 'REJECT'. REJECT if ANY check scores 0.")
    score_1 = dspy.OutputField(desc="Check 1 character engine (desire/fear/misbelief linked): integer 0-25. 0 = absent.")
    score_2 = dspy.OutputField(desc="Check 2 character arc closes (Act-1 misbelief overcome in Recovery): integer 0-20.")
    score_3 = dspy.OutputField(desc="Check 3 midpoint is a true reversal: integer 0-15.")
    score_4 = dspy.OutputField(desc="Check 4 disaster + dark moment land (foreshadowed/blindside; fear re-triggered): integer 0-15.")
    score_5 = dspy.OutputField(desc="Check 5 structural completeness (all beats, right order, pinch points escalate): integer 0-15.")
    score_6 = dspy.OutputField(desc="Check 6 hook + resolution: integer 0-10.")
    failed_checks = dspy.OutputField(desc="If REJECT: failing check numbers + one line each. If PASS: 'none'.")
    why = dspy.OutputField(desc="One line.")


class IterateStory(dspy.Signature):
    """Improve a PASSING outline using the gate's critique to raise the score.
    Keep what works; deepen the internal arc, sharpen the midpoint reversal, make
    the disaster blindside the protagonist while the reader dreads it."""

    premise = dspy.InputField()
    desire = dspy.InputField()
    fear = dspy.InputField()
    misbelief = dspy.InputField()
    hook = dspy.InputField()
    setup = dspy.InputField()
    inciting_incident = dspy.InputField()
    build_up = dspy.InputField()
    plot_point_1 = dspy.InputField()
    pinch_point_1 = dspy.InputField()
    pre_midpoint = dspy.InputField()
    midpoint = dspy.InputField()
    post_midpoint = dspy.InputField()
    pinch_point_2 = dspy.InputField()
    supposed_victory = dspy.InputField()
    disaster = dspy.InputField()
    dark_moment = dspy.InputField()
    recovery = dspy.InputField()
    climactic_confrontation = dspy.InputField()
    victory = dspy.InputField()
    resolution = dspy.InputField()
    critique = dspy.InputField(desc="The gate's why + weak points to push higher.")
    standard = dspy.InputField(desc="The generator standard to hold to.")
    improved_premise = dspy.OutputField()
    improved_desire = dspy.OutputField()
    improved_fear = dspy.OutputField()
    improved_misbelief = dspy.OutputField()
    improved_hook = dspy.OutputField()
    improved_setup = dspy.OutputField()
    improved_inciting_incident = dspy.OutputField()
    improved_build_up = dspy.OutputField()
    improved_plot_point_1 = dspy.OutputField()
    improved_pinch_point_1 = dspy.OutputField()
    improved_pre_midpoint = dspy.OutputField()
    improved_midpoint = dspy.OutputField()
    improved_post_midpoint = dspy.OutputField()
    improved_pinch_point_2 = dspy.OutputField()
    improved_supposed_victory = dspy.OutputField()
    improved_disaster = dspy.OutputField()
    improved_dark_moment = dspy.OutputField()
    improved_recovery = dspy.OutputField()
    improved_climactic_confrontation = dspy.OutputField()
    improved_victory = dspy.OutputField()
    improved_resolution = dspy.OutputField()
