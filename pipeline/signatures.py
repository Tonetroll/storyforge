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
    resolution = dspy.OutputField(desc="The payoff that closes the loop toward the end. Defined, never blank. Lands the WHY beneath the event -- the desire and belief driving it -- not just the surface thing that happened.")
    reaction_1 = dspy.OutputField(desc="Pull-in emotion, one of: LOL / WTF / WOW.")
    reaction_2 = dspy.OutputField(desc="Resolution emotion, one of: Aah / Oooh / Finally. MUST differ from reaction_1.")
    viewer_action = dspy.OutputField(desc="Exactly ONE: Do / Sale / Sign-up / Save / Share / Try / Apply / Reflect.")
    topic = dspy.OutputField(desc="3-6 words naming what THIS story is about, for the filename. Concrete subject. NEVER generic words like 'story', 'idea', or 'video'.")


class GateIdea(dspy.Signature):
    """You are a strict, impartial gate. You did NOT write this idea; do not be
    generous. Score each of the seven checks 0..its max by HOW STRONGLY it is met.
    Each check judges ONE thing only. A check scoring 0 = absent = REJECT. Otherwise PASS."""

    one_liner = dspy.InputField()
    resolution = dspy.InputField()
    reaction_1 = dspy.InputField()
    reaction_2 = dspy.InputField()
    viewer_action = dspy.InputField()
    criteria = dspy.InputField(desc="The gate: the seven checks, their weights, and the verdict rule.")
    verdict = dspy.OutputField(desc="Exactly 'PASS' or 'REJECT'. REJECT if ANY check scores 0.")
    score_1 = dspy.OutputField(desc="Check 1 pull-in emotion real & strong (LOL/WTF/WOW): integer 0-18. 0 = absent.")
    score_2 = dspy.OutputField(desc="Check 2 resolution emotion real & strong (Aah/Oooh/Finally): integer 0-18. 0 = absent.")
    score_3 = dspy.OutputField(desc="Check 3 the pull-in and resolution emotions are DISTINCT from each other: integer 0-16. 0 = same emotion twice or one missing.")
    score_4 = dspy.OutputField(desc="Check 4 resolution lands the desire/belief WHY beneath the event, not just the WHAT: integer 0-18. 0 = names only the event.")
    score_5 = dspy.OutputField(desc="Check 5 exactly one viewer action: integer 0-8. 0 = none or more than one.")
    score_6 = dspy.OutputField(desc="Check 6 open loop -- premise doesn't give away the answer: integer 0-12. 0 = gives it away.")
    score_7 = dspy.OutputField(desc="Check 7 one-liner concrete & speakable <4s: integer 0-10. 0 = abstract or too long.")
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
    resolution = dspy.OutputField(desc="Loose ends wrapped; the reader is satisfied. Land the WHY beneath the event - the desire + belief that drove it - not just the WHAT that happened.")
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


# ===========================================================================
# THEME stage  (downstream of idea; feeds structure)
# ===========================================================================
class GenerateTheme(dspy.Signature):
    """Surface the THEME the accepted idea is really about. Theme is what the
    story SAYS about life - a stance or question about a topic, in tension. Not
    the topic, not a moral, not a single word. It lives in the protagonist's
    belief-shift."""

    brief = dspy.InputField(desc="The accepted idea this theme is drawn from.")
    standard = dspy.InputField(desc="The generator standard (rules/standards/theme_generator.md).")
    topic = dspy.OutputField(desc="The arena/subject (love, rivalry, identity). Broad, neutral. NOT the theme. Used for the filename.")
    theme_statement = dspy.OutputField(desc="The stance: 'This story shows that ____.' A truth/argument about the topic. Never a single word.")
    central_question = dspy.OutputField(desc="The tension: a hard, non-yes/no question the story wrestles with - the pull between what is DESIRED and what is BELIEVED.")
    belief_shift = dspy.OutputField(desc="What the protagonist believes at the START -> at the END, and what breaks the old belief. Name the DESIRE driving the shift - the WHY beneath it.")


class GateTheme(dspy.Signature):
    """You are a strict, impartial gate. The #1 failure is a topic or single word
    dressed up as a theme; the #2 is a moral. Grade each check 0..its max. A check
    at 0 = absent = REJECT."""

    topic = dspy.InputField()
    theme_statement = dspy.InputField()
    central_question = dspy.InputField()
    belief_shift = dspy.InputField()
    criteria = dspy.InputField(desc="The gate: the six checks, their weights, and the verdict rule.")
    verdict = dspy.OutputField(desc="Exactly 'PASS' or 'REJECT'. REJECT if ANY check scores 0.")
    score_1 = dspy.OutputField(desc="Check 1 stance not a topic: integer 0-25. 0 = it's still a topic/single word.")
    score_2 = dspy.OutputField(desc="Check 2 genuine tension: integer 0-20. 0 = no real contradiction / yes-no answerable.")
    score_3 = dspy.OutputField(desc="Check 3 implies a belief-shift: integer 0-20. 0 = no start->end belief.")
    score_4 = dspy.OutputField(desc="Check 4 not a moral: integer 0-15. 0 = preachy instruction/slogan.")
    score_5 = dspy.OutputField(desc="Check 5 universal through the specific: integer 0-10.")
    score_6 = dspy.OutputField(desc="Check 6 one center of gravity: integer 0-10.")
    failed_checks = dspy.OutputField(desc="If REJECT: failing check numbers + one line each. If PASS: 'none'.")
    why = dspy.OutputField(desc="One line.")


class IterateTheme(dspy.Signature):
    """Improve a PASSING theme using the gate's critique to raise the score. Push
    it further from topic toward stance, sharpen the tension, make the belief-shift
    concrete. Do not turn it into a moral."""

    topic = dspy.InputField()
    theme_statement = dspy.InputField()
    central_question = dspy.InputField()
    belief_shift = dspy.InputField()
    critique = dspy.InputField(desc="The gate's why + weak points to push higher.")
    standard = dspy.InputField(desc="The generator standard to hold to.")
    improved_topic = dspy.OutputField()
    improved_theme_statement = dspy.OutputField()
    improved_central_question = dspy.OutputField()
    improved_belief_shift = dspy.OutputField()


# ===========================================================================
# STAKEBAKE stage  (downstream of structure; rewrites the beats with stakes baked in)
# ===========================================================================
class GenerateStakebake(dspy.Signature):
    """Take the structured story and RAISE ITS STAKES by rewriting the beats so the
    stakes live INSIDE them - establish value early in the setup, impose a ticking
    clock in the build-up, force a no-win choice at a plot point, make the disaster
    carry a personal consequence with no safety net, and pay off a deeper emotional
    need in the recovery. Output the SAME beats, enhanced, plus one line naming what
    you added where. Do NOT write a separate stakes memo. No clinical/AI jargon."""

    brief = dspy.InputField(desc="The accepted structure (the full 21-beat outline) to raise the stakes of.")
    standard = dspy.InputField(desc="The generator standard (rules/standards/stakebake_generator.md).")
    topic = dspy.OutputField(desc="3-6 words naming what this is about, for the filename. No generic words.")
    premise = dspy.OutputField(desc="The premise (kept or sharpened).")
    desire = dspy.OutputField(desc="The desire - the value now made explicit.")
    fear = dspy.OutputField(desc="The fear - now concrete and under threat.")
    misbelief = dspy.OutputField(desc="The misbelief (kept).")
    hook = dspy.OutputField(desc="The hook, sharpened for stakes.")
    setup = dspy.OutputField(desc="Setup - now ESTABLISHES VALUE EARLY (what he stands to lose).")
    inciting_incident = dspy.OutputField(desc="Inciting incident, raised.")
    build_up = dspy.OutputField(desc="Build-up - now carries the TICKING CLOCK / urgency.")
    plot_point_1 = dspy.OutputField(desc="1st plot point - now a TOUGH no-win CHOICE.")
    pinch_point_1 = dspy.OutputField(desc="1st pinch point - opposition escalates.")
    pre_midpoint = dspy.OutputField(desc="Pre-midpoint, raised.")
    midpoint = dspy.OutputField(desc="Midpoint reversal, raised.")
    post_midpoint = dspy.OutputField(desc="Post-midpoint, raised.")
    pinch_point_2 = dspy.OutputField(desc="2nd pinch point - the antagonistic force closes in.")
    supposed_victory = dspy.OutputField(desc="Supposed victory - false confidence before the fall.")
    disaster = dspy.OutputField(desc="Disaster - now carries PERSONAL CONSEQUENCES with NO SAFETY NET.")
    dark_moment = dspy.OutputField(desc="Dark moment - the fear returns at full personal cost.")
    recovery = dspy.OutputField(desc="Recovery - pays off the DEEPER EMOTIONAL NEED: land the desire and belief that were at risk (the WHY beneath the event), not just the event resolving.")
    climactic_confrontation = dspy.OutputField(desc="Climax - highest stakes, irreversible.")
    victory = dspy.OutputField(desc="Victory - the win is AGENCY, not just relief.")
    resolution = dspy.OutputField(desc="Resolution - the cost paid, the meaning earned.")
    stakes_added = dspy.OutputField(desc="One short line: which pillar you put in which beat (e.g. 'clock -> build_up; no-win -> plot_point_1; personal cost -> disaster').")


class GateStakebake(dspy.Signature):
    """You are a strict inspection engine for the RAISED-STAKES beats. R1-R5 are
    binary (full points or zero). G1-G2 are graded. Flag jargon. Only inspect."""

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
    stakes_added = dspy.InputField()
    criteria = dspy.InputField(desc="The gate: the binary rules, graded checks, weights, and verdict floor.")
    verdict = dspy.OutputField(desc="'PASS' or 'REJECT' (the engine decides by the floor; report your read).")
    score_1 = dspy.OutputField(desc="R1 value established early (in the setup): 0 or 12.")
    score_2 = dspy.OutputField(desc="R2 ticking clock / urgency (in the build-up): 0 or 12.")
    score_3 = dspy.OutputField(desc="R3 tough choice / no-win dilemma (at a plot point): 0 or 12.")
    score_4 = dspy.OutputField(desc="R4 personal consequences in the disaster (life/safety/relationships): 0 or 12.")
    score_5 = dspy.OutputField(desc="R5 no safety nets (no plot armor): 0 or 12.")
    score_6 = dspy.OutputField(desc="G1 emotional stakes land (goal tied to a deeper need; stakes land the desire-vs-belief at risk, the WHY beneath the event, not just the event): integer 0-25.")
    score_7 = dspy.OutputField(desc="G2 specific & relatable (not generic): integer 0-15.")
    jargon = dspy.OutputField(desc="'true' if clinical/AI jargon is present, else 'false'.")
    failed_checks = dspy.OutputField(desc="If REJECT: failing checks + one line each. Else 'none'.")
    why = dspy.OutputField(desc="One line.")


class IterateStakebake(dspy.Signature):
    """Raise the stakes further by rewriting whatever beats are weak - add the
    missing pillar (urgency, a no-win choice, a personal cost, a removed safety net)
    into the relevant beat and deepen the emotional need. No jargon."""

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
    stakes_added = dspy.InputField()
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
    improved_stakes_added = dspy.OutputField()


# ===========================================================================
# SCRIPT stage  (downstream of stakebake; writes the short-form video script)
# ===========================================================================
class GenerateScript(dspy.Signature):
    """Write the short-form video script from the assembled story. DELIVER the
    stakes, the theme's belief-shift, the structure's arc, and the hook in the
    words. Run the addiction loop (stakes -> big question -> head fake -> rehook),
    open a loop in the first line, and write TIGHT, compact, punchy sentences.
    No clinical/AI jargon."""

    brief = dspy.InputField(desc="The assembled story (idea + theme + structure + raised-stakes beats) to script.")
    standard = dspy.InputField(desc="The generator standard (rules/standards/script_generator.md).")
    topic = dspy.OutputField(desc="3-6 words naming what this is about, for the filename. No generic words.")
    hook = dspy.OutputField(desc="The opening line(s) - opens a loop in the first 1-3 seconds.")
    body = dspy.OutputField(desc="The VO narration - the story told with the loop running (stakes/question/head-fake/rehook).")
    payoff = dspy.OutputField(desc="The line that closes the main loop and lands the theme by delivering the desire/belief WHY beneath the event, not just the event itself.")
    cta = dspy.OutputField(desc="One clear viewer action.")
    loop_notes = dspy.OutputField(desc="Where the open loops / head fakes / rehooks are.")


class GateScript(dspy.Signature):
    """You are a strict inspection engine for a short-form script. Score delivery,
    the addiction loop, and voice. Binary where marked, graded otherwise. Flag jargon."""

    hook = dspy.InputField()
    body = dspy.InputField()
    payoff = dspy.InputField()
    cta = dspy.InputField()
    loop_notes = dspy.InputField()
    criteria = dspy.InputField(desc="THE STORY PACKAGE (to verify delivery) + the gate criteria, weights, and floor.")
    verdict = dspy.OutputField(desc="'PASS' or 'REJECT' (the engine decides by the floor; report your read).")
    score_1 = dspy.OutputField(desc="D1 delivery - carries stakes/theme/structure/hook from the package, and the payoff lands the desire/belief WHY beneath the event (not just the event): integer 0-20.")
    score_2 = dspy.OutputField(desc="L1 hook opens a loop in the first line: 0 or 12.")
    score_3 = dspy.OutputField(desc="L2 head fake - earned reveal that breaks the prediction: 0 or 12.")
    score_4 = dspy.OutputField(desc="L3 rehooks / no dead air: integer 0-13.")
    score_5 = dspy.OutputField(desc="V1 voice & format fit per the format's standard (tight & punchy for short-form, immersive for long-form): integer 0-25.")
    score_6 = dspy.OutputField(desc="V2 visceral & speakable - concrete, present tense, to one viewer: integer 0-18.")
    jargon = dspy.OutputField(desc="'true' if clinical/AI jargon is present, else 'false'.")
    failed_checks = dspy.OutputField(desc="If REJECT: failing checks + one line each. Else 'none'.")
    why = dspy.OutputField(desc="One line.")


class IterateScript(dspy.Signature):
    """Tighten and sharpen the short-form script using the gate's critique. Add the
    missing loop element (a head fake, a rehook), cut filler, make every sentence
    hit harder, and make sure the package still lands. No jargon."""

    hook = dspy.InputField()
    body = dspy.InputField()
    payoff = dspy.InputField()
    cta = dspy.InputField()
    loop_notes = dspy.InputField()
    critique = dspy.InputField(desc="The gate's why + weak points to push higher.")
    standard = dspy.InputField(desc="The generator standard to hold to.")
    improved_hook = dspy.OutputField()
    improved_body = dspy.OutputField()
    improved_payoff = dspy.OutputField()
    improved_cta = dspy.OutputField()
    improved_loop_notes = dspy.OutputField()


# ===========================================================================
# SCREENPLAY stage  (a script alternate; two image-generatable parts)
# ===========================================================================
class GenerateScreenplay(dspy.Signature):
    """Write the story as a TWO-PART screenplay - two scenes, each a self-contained,
    image-generatable beat (slugline, visual action, dialogue). DELIVER the package
    (stakes, theme's belief-shift, structure's arc, hook) across the two parts, run
    the addiction loop (part 1 opens the loop / head fake; part 2 pays it off), and
    keep it visual and concrete. No clinical/AI jargon."""

    brief = dspy.InputField(desc="The assembled story (idea + theme + structure + raised-stakes beats) to dramatize.")
    standard = dspy.InputField(desc="The generator standard (rules/standards/script_screenplay_generator.md).")
    topic = dspy.OutputField(desc="3-6 words naming what this is about, for the filename. No generic words.")
    part_1 = dspy.OutputField(desc="Scene 1: slugline (INT./EXT.), visual action, dialogue. Opens the loop / sets the head fake. Image-generatable.")
    part_2 = dspy.OutputField(desc="Scene 2: slugline, visual action, dialogue. The head-fake payoff / the turn, landing the desire/belief WHY beneath the event (not just the surface reversal). Image-generatable.")
    loop_notes = dspy.OutputField(desc="Where the loop opens, the head fake, and the payoff sit across the two parts.")


class GateScreenplay(dspy.Signature):
    """You are a strict inspection engine for a two-part screenplay. Score delivery,
    the addiction loop, and the visual/format craft. Binary where marked. Flag jargon."""

    part_1 = dspy.InputField()
    part_2 = dspy.InputField()
    loop_notes = dspy.InputField()
    criteria = dspy.InputField(desc="THE STORY PACKAGE (to verify delivery) + the gate criteria, weights, and floor.")
    verdict = dspy.OutputField(desc="'PASS' or 'REJECT' (the engine decides by the floor; report your read).")
    score_1 = dspy.OutputField(desc="D1 delivery - carries stakes/theme/structure/hook from the package across the two parts: integer 0-20.")
    score_2 = dspy.OutputField(desc="L1 part 1 opens a loop: 0 or 12.")
    score_3 = dspy.OutputField(desc="L2 head fake - part 2 pays off with an earned reversal that lands the desire/belief WHY beneath the turn (not just the surface event): 0 or 12.")
    score_4 = dspy.OutputField(desc="L3 the two parts chain (part 1 -> part 2, no dead beat): integer 0-13.")
    score_5 = dspy.OutputField(desc="V1 visual & image-generatable - each part is a clear, shootable image with proper screenplay form: integer 0-25.")
    score_6 = dspy.OutputField(desc="V2 concrete & dramatic - real action and dialogue, not narration: integer 0-18.")
    jargon = dspy.OutputField(desc="'true' if clinical/AI jargon is present, else 'false'.")
    failed_checks = dspy.OutputField(desc="If REJECT: failing checks + one line each. Else 'none'.")
    why = dspy.OutputField(desc="One line.")


class IterateScreenplay(dspy.Signature):
    """Sharpen the two-part screenplay using the gate's critique. Make each part a
    cleaner, more shootable image, strengthen the loop across the two parts, and
    push the action/dialogue. No jargon."""

    part_1 = dspy.InputField()
    part_2 = dspy.InputField()
    loop_notes = dspy.InputField()
    critique = dspy.InputField(desc="The gate's why + weak points to push higher.")
    standard = dspy.InputField(desc="The generator standard to hold to.")
    improved_part_1 = dspy.OutputField()
    improved_part_2 = dspy.OutputField()
    improved_loop_notes = dspy.OutputField()


# ===========================================================================
# PACKAGING stage  (title + thumbnail; scored ONLY by the 12 thumbnail/title criteria)
# ===========================================================================
class GeneratePackaging(dspy.Signature):
    """Produce the click for the video: a title and a thumbnail (as a plain concept
    + a ready-to-use image-generation prompt), built from the story. The thumbnail
    stops the scroll; the title opens a loop AND promises a specific outcome. Plain
    language, no jargon. Follow the 12-criteria standard."""

    brief = dspy.InputField(desc="The story this video is about (idea + theme + structure + stakes).")
    standard = dspy.InputField(desc="The generator standard (rules/standards/packaging_generator.md).")
    topic = dspy.OutputField(desc="3-6 words naming what this is about, for the filename. No generic words.")
    title = dspy.OutputField(desc="The YouTube title: 5-7 words, opens a curiosity gap AND promises a specific outcome, plain language.")
    thumbnail_concept = dspy.OutputField(desc="The visual idea in plain words: the anchor (face+expression OR bold graphic), the emotion (the desire/belief WHY beneath the event, not just the surface event), the result shown, the background.")
    thumbnail_prompt = dspy.OutputField(desc="The ready-to-use image prompt (the Base Prompt filled in for this story).")


class GatePackaging(dspy.Signature):
    """You are a strict inspection engine. Score the title + thumbnail against the
    12 binary thumbnail/title criteria - each YES = full points, NO = 0. Judge the
    DESCRIBED thumbnail and the title only; do not consider the story package."""

    title = dspy.InputField()
    thumbnail_concept = dspy.InputField()
    thumbnail_prompt = dspy.InputField()
    criteria = dspy.InputField(desc="The 12 binary thumbnail/title criteria, weights, and the verdict rule.")
    verdict = dspy.OutputField(desc="'PASS' or 'REJECT' (the engine decides by the floor; report your read).")
    score_1 = dspy.OutputField(desc="Q1 visual anchor (face+expression AND/OR bold graphic): 0 or the weight.")
    score_2 = dspy.OutputField(desc="Q2 emotion or intrigue (reads as the desire/belief WHY beneath the event, not just the surface event): 0 or the weight.")
    score_3 = dspy.OutputField(desc="Q3 directional cues: 0 or the weight.")
    score_4 = dspy.OutputField(desc="Q4 text readability (bold, high-contrast, max 4 words): 0 or the weight.")
    score_5 = dspy.OutputField(desc="Q5 background (tutorial: clean; story: transformed setting): 0 or the weight.")
    score_6 = dspy.OutputField(desc="Q6 visual hierarchy: 0 or the weight.")
    score_7 = dspy.OutputField(desc="Q7 shows result/transformation: 0 or the weight.")
    score_8 = dspy.OutputField(desc="Q8 logos/icons/symbols: 0 or the weight.")
    score_9 = dspy.OutputField(desc="Q9 title curiosity gap (loop turns on the desire/belief WHY beneath the event, not just naming what happened): 0 or the weight.")
    score_10 = dspy.OutputField(desc="Q10 title specific outcome: 0 or the weight.")
    score_11 = dspy.OutputField(desc="Q11 title payoff clarity: 0 or the weight.")
    score_12 = dspy.OutputField(desc="Q12 title accessible language (no jargon): 0 or the weight.")
    failed_checks = dspy.OutputField(desc="If REJECT: failing Q numbers + one line each. Else 'none'.")
    why = dspy.OutputField(desc="One line.")


class IteratePackaging(dspy.Signature):
    """Fix the title + thumbnail to pass the criteria it failed - add the missing
    visual anchor / hierarchy / result, sharpen the title's outcome and curiosity.
    Plain language, no jargon."""

    title = dspy.InputField()
    thumbnail_concept = dspy.InputField()
    thumbnail_prompt = dspy.InputField()
    critique = dspy.InputField(desc="The gate's why + which criteria failed.")
    standard = dspy.InputField(desc="The generator standard to hold to.")
    improved_title = dspy.OutputField()
    improved_thumbnail_concept = dspy.OutputField()
    improved_thumbnail_prompt = dspy.OutputField()


# ===========================================================================
# DESCRIPTION stage  (the YouTube description: hook -> mirror -> signal)
# ===========================================================================
class GenerateDescription(dspy.Signature):
    """Write the YouTube description (a few lines, ~600 chars, 5000 max). NOT a
    summary. Job in order: a first line that is a SECOND HOOK (above the fold,
    <~120 chars, no spoiler), 1-2 lines that MIRROR the audience's wound so the
    right viewer feels seen, and a line that SIGNALS who it's for + the language
    they'd search. Follow the standard."""

    brief = dspy.InputField(desc="The story this video is about (idea + theme + structure + stakes).")
    standard = dspy.InputField(desc="The generator standard (rules/standards/description_generator.md).")
    topic = dspy.OutputField(desc="3-6 words naming what this is about, for the filename. No generic words.")
    hook_line = dspy.OutputField(desc="First line, above the fold (<~120 chars): a second hook, curiosity/tension, no spoiler.")
    mirror_lines = dspy.OutputField(desc="1-2 lines mirroring the audience's wound so the right viewer thinks 'that's me'. Land the WHY beneath the feeling: the tension between what they DESIRE and what they BELIEVE, not just the surface state. Specific, not generic.")
    audience_signal = dspy.OutputField(desc="Who it's for + the natural language they'd search; lets the right viewer self-identify and the anti-audience self-select out.")


class GateDescription(dspy.Signature):
    """You are a strict gate for a YouTube description. Score each check 0..its max.
    Reward hook + mirror; penalize summary, spoiler, audience-labeling, keyword
    stuffing, and length over 5000 chars. Use the package to verify it doesn't
    spoil or overpromise."""

    hook_line = dspy.InputField()
    mirror_lines = dspy.InputField()
    audience_signal = dspy.InputField()
    criteria = dspy.InputField(desc="The 6 weighted checks + the verdict rule.")
    verdict = dspy.OutputField(desc="'PASS' or 'REJECT' (the engine decides by the floor; report your read).")
    score_1 = dspy.OutputField(desc="Above-the-fold hook: integer 0-25.")
    score_2 = dspy.OutputField(desc="Mirrors the wound (lands the desire/belief WHY beneath the feeling, not just the surface state): integer 0-25.")
    score_3 = dspy.OutputField(desc="No spoiler / no overpromise: integer 0-15.")
    score_4 = dspy.OutputField(desc="Repels the anti-audience: integer 0-10.")
    score_5 = dspy.OutputField(desc="Algorithm signal (searchable language): integer 0-15.")
    score_6 = dspy.OutputField(desc="Tight, plain, ~600 chars (5000 max): integer 0-10.")
    failed_checks = dspy.OutputField(desc="If REJECT: failing check numbers + one line each. Else 'none'.")
    why = dspy.OutputField(desc="One line.")


class IterateDescription(dspy.Signature):
    """Improve the description against the checks it lost points on — sharpen the
    above-fold hook, deepen the wound-mirror, tighten to ~600 chars, strip any
    spoiler/overpromise/jargon. Keep it hook -> mirror -> signal."""

    hook_line = dspy.InputField()
    mirror_lines = dspy.InputField()
    audience_signal = dspy.InputField()
    critique = dspy.InputField(desc="The gate's why + which checks lost points.")
    standard = dspy.InputField(desc="The generator standard to hold to.")
    improved_hook_line = dspy.OutputField()
    improved_mirror_lines = dspy.OutputField()
    improved_audience_signal = dspy.OutputField()
