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
    generous. Score each of the thirteen checks 0..its max by HOW STRONGLY it is met.
    Each check judges ONE thing only. A check scoring 0 = absent = REJECT. Otherwise PASS."""

    one_liner = dspy.InputField()
    resolution = dspy.InputField()
    reaction_1 = dspy.InputField()
    reaction_2 = dspy.InputField()
    viewer_action = dspy.InputField()
    criteria = dspy.InputField(desc="The gate: the thirteen checks, their weights, and the verdict rule.")
    verdict = dspy.OutputField(desc="Exactly 'PASS' or 'REJECT'. REJECT if ANY check scores 0.")
    score_1 = dspy.OutputField(desc="Check 1 pull-in emotion real & strong (LOL/WTF/WOW): integer 0-18. 0 = absent.")
    score_2 = dspy.OutputField(desc="Check 2 resolution emotion real & strong (Aah/Oooh/Finally): integer 0-18. 0 = absent.")
    score_3 = dspy.OutputField(desc="Check 3 the pull-in and resolution emotions are DISTINCT from each other: integer 0-16. 0 = same emotion twice or one missing.")
    score_4 = dspy.OutputField(desc="Check 4 resolution lands the desire/belief WHY beneath the event, not just the WHAT: integer 0-5. 0 = names only the event.")
    score_5 = dspy.OutputField(desc="Check 5 runs INSIDE-OUT: the felt belief is EXPRESSED and that expression realizes the desire (carries even when the outcome doesn't); dock proving/permission/validation-seeking: integer 0-3. 0 = absent.")
    score_6 = dspy.OutputField(desc="Check 6 desire is the CONSTANT, belief the variable -- resistance dims belief then the desire RESURFACES; dock a desire that dies and returns: integer 0-3. 0 = absent.")
    score_7 = dspy.OutputField(desc="Check 7 belief shown on a SPECTRUM, not flipped binary; dock binary believe/don't: integer 0-2. 0 = absent.")
    score_8 = dspy.OutputField(desc="Check 8 a self-oriented motive on the EGO->AUTHENTIC axis; dock him CARRYING others: integer 0-2. 0 = absent.")
    score_9 = dspy.OutputField(desc="Check 9 others pulled in by MIRRORING (his pursuit serves THEIR OWN desire, carried WITH him); dock others acting FOR him or won by ego/false promise: integer 0-2. 0 = absent.")
    score_10 = dspy.OutputField(desc="Check 10 identity treated as self-made -- owned belief OR his own ceding to others' opinions; dock identity handed down from outside: integer 0-1. 0 = absent.")
    score_11 = dspy.OutputField(desc="Check 11 exactly one viewer action: integer 0-8. 0 = none or more than one.")
    score_12 = dspy.OutputField(desc="Check 12 open loop -- premise doesn't give away the answer: integer 0-12. 0 = gives it away.")
    score_13 = dspy.OutputField(desc="Check 13 one-liner concrete & speakable <4s: integer 0-10. 0 = abstract or too long.")
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
    criteria = dspy.InputField(desc="The gate: the twelve checks, their weights, and the verdict rule.")
    verdict = dspy.OutputField(desc="Exactly 'PASS' or 'REJECT'. REJECT if ANY check scores 0.")
    score_1 = dspy.OutputField(desc="Check 1 character engine -- desire/fear/misbelief all defined, concrete, causally linked (misbelief feeds fear; fear blocks desire): integer 0-25. 0 = absent.")
    score_2 = dspy.OutputField(desc="Check 2 character arc closes -- the Act-1 misbelief is exactly what's overcome in Recovery; the protagonist visibly changes: integer 0-10. 0 = absent.")
    score_3 = dspy.OutputField(desc="Check 3 desire stays constant -- dock if the arc runs on the desire leaving and returning (only belief/clarity rises and falls; Recovery is the desire resurfacing): integer 0-5. 0 = absent.")
    score_4 = dspy.OutputField(desc="Check 4 ego toward authentic -- dock if the change is learning to carry/care-for others or earning the world's verdict rather than ego toward authentically expressing his own desire: integer 0-5. 0 = absent.")
    score_5 = dspy.OutputField(desc="Check 5 team mirrors, not shouldered -- if a team turns with him it must be mutual mirroring, not him shouldering them: integer 0-5. 0 = absent.")
    score_6 = dspy.OutputField(desc="Check 6 midpoint reversal -- a true reversal: everything changes; reactionary-hero flips to action-hero, not a minor bump: integer 0-15. 0 = absent.")
    score_7 = dspy.OutputField(desc="Check 7 disaster blindsides -- foreshadowed for the reader but blindsides the protagonist: integer 0-8. 0 = absent.")
    score_8 = dspy.OutputField(desc="Check 8 dark moment re-triggers fear -- the dark moment re-triggers the SPECIFIC fear from check 1: integer 0-7. 0 = absent.")
    score_9 = dspy.OutputField(desc="Check 9 structural completeness -- every beat present and in order across the 3 acts/loops; pinch points escalate the opposition: integer 0-10. 0 = absent.")
    score_10 = dspy.OutputField(desc="Check 10 hook grabs the inner conflict: integer 0-5. 0 = absent.")
    score_11 = dspy.OutputField(desc="Check 11 resolution lands the WHY -- wraps loose ends and satisfies AND lands the desire+belief that drove it, not just the WHAT: integer 0-5. 0 = absent.")
    score_12 = dspy.OutputField(desc="Check 12 the Dance -- every beat follows the last by THEREFORE (a consequence) or BUT (a reversal), never AND THEN: integer 0-15. 0 = 'and then' detail-piling (KILL check: a 0 rejects the story).")
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
    criteria = dspy.InputField(desc="The gate: the fourteen checks, their weights, and the verdict rule.")
    verdict = dspy.OutputField(desc="Exactly 'PASS' or 'REJECT'. REJECT if ANY check scores 0.")
    score_1 = dspy.OutputField(desc="Check 1 stance, not a topic -- a statement/argument ABOUT the topic, not a single word or broad subject: integer 0-25. 0 = it's still a topic/single word.")
    score_2 = dspy.OutputField(desc="Check 2 genuine tension (non-yes/no) -- a hard non-yes/no question or real contradiction: integer 0-9. 0 = no real contradiction / yes-no answerable.")
    score_3 = dspy.OutputField(desc="Check 3 tension is desire vs belief -- the pull between what someone DESIRES and what they BELIEVE, not a surface event/plot puzzle: integer 0-6. 0 = absent.")
    score_4 = dspy.OutputField(desc="Check 4 constant desire, variable belief -- dock a wavering desire (tension lives in the swinging BELIEF) or a settled desire framed as 'returning' rather than resurfacing: integer 0-5. 0 = absent.")
    score_5 = dspy.OutputField(desc="Check 5 spectrum of belief -- dock if everyone is flattened to one shared belief instead of a spectrum: integer 0-5. 0 = absent.")
    score_6 = dspy.OutputField(desc="Check 6 implies a start->end belief-shift -- arc-ready (feeds misbelief -> Recovery) and names the DESIRE driving it: integer 0-9. 0 = no start->end belief.")
    score_7 = dspy.OutputField(desc="Check 7 felt -> self acts (not willed/forced) -- the shift is FELT and drives the character's OWN action first; dock a willed/forced shift or one held only by loyalty/obligation: integer 0-5. 0 = absent.")
    score_8 = dspy.OutputField(desc="Check 8 others read authenticity -> it carries -- others respond to the visible action + readable feeling by its authenticity and it CARRIES them; dock one driven by outside validation: integer 0-4. 0 = absent.")
    score_9 = dspy.OutputField(desc="Check 9 expressing, not proving -- dock one framed as PROVING/earning worth rather than EXPRESSING a felt belief: integer 0-4. 0 = absent.")
    score_10 = dspy.OutputField(desc="Check 10 mirroring, not carrying -- dock if the carry runs through the protagonist CARRYING the others rather than MIRRORING (others join by mirroring the desire): integer 0-3. 0 = absent.")
    score_11 = dspy.OutputField(desc="Check 11 not a moral -- no slogan, no instruction, no soapbox: integer 0-8. 0 = preachy instruction/slogan.")
    score_12 = dspy.OutputField(desc="Check 12 invites reflection: integer 0-7. 0 = absent.")
    score_13 = dspy.OutputField(desc="Check 13 universal through the specific -- a human truth grounded in this idea, not an abstraction: integer 0-5. 0 = absent.")
    score_14 = dspy.OutputField(desc="Check 14 one center of gravity -- a single coherent core idea (multiple threads ok, but centered): integer 0-5. 0 = absent.")
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
    score_1 = dspy.OutputField(desc="R1 value established early -- what the character values / has to lose is clear before it's threatened (in the setup): 0 or 12.")
    score_2 = dspy.OutputField(desc="R2 ticking clock / urgency -- a time limit or immediate pressure (in the build-up): 0 or 12.")
    score_3 = dspy.OutputField(desc="R3 tough choice / no-win -- a moral dilemma between two unfavorable options (at a plot point): 0 or 12.")
    score_4 = dspy.OutputField(desc="R4 personal consequences -- affects the character's life, safety, or relationships, not just external events: 0 or 12.")
    score_5 = dspy.OutputField(desc="R5 no safety nets -- no plot armor; mistakes carry consequences: 0 or 12.")
    score_6 = dspy.OutputField(desc="G1a deeper need tied -- external goal tied to a deeper psychological/emotional need; stakes land the desire-vs-belief at risk (the WHY beneath the event): integer 0-8.")
    score_7 = dspy.OutputField(desc="G1b threat on belief, not desire -- dock when the threat is aimed at the desire itself (desire 'dies'/'comes back') instead of the belief/clarity that it's reachable: integer 0-5.")
    score_8 = dspy.OutputField(desc="G1c belief on a spectrum -- dock when everyone's belief moves in lockstep instead of sitting at different points: integer 0-4.")
    score_9 = dspy.OutputField(desc="G1d express, not prove -- dock when stakes ride on PROVING the want for the crowd's verdict rather than losing the chance to EXPRESS it authentically: integer 0-4.")
    score_10 = dspy.OutputField(desc="G1e team mirror, not carrying -- dock when team stakes make him responsible for carrying others rather than the mutual mirror lifting or breaking: integer 0-4.")
    score_11 = dspy.OutputField(desc="G2 specific & relatable -- the stakes are specific to the audience avatar, not generic: integer 0-15.")
    score_12 = dspy.OutputField(desc="G3 the Dance -- every beat follows the last by THEREFORE or BUT, never AND THEN: integer 0-15. 0 = 'and then' detail-piling (KILL check: a 0 rejects regardless of total).")
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
    score_7 = dspy.OutputField(desc="L4 the Dance -- every beat follows the last by THEREFORE or BUT, never AND THEN: integer 0-15. 0 = 'and then' detail-piling (KILL check: a 0 rejects regardless of total).")
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
    score_1 = dspy.OutputField(desc="Delivery - stakes -- the stakes are dramatized across the two parts (verify against THE STORY PACKAGE): integer 0-8.")
    score_2 = dspy.OutputField(desc="Delivery - belief-shift -- the theme's belief-shift is dramatized across the two parts (verify against the package): integer 0-8.")
    score_3 = dspy.OutputField(desc="Delivery - arc & hook -- the structure's arc and hook are dramatized across the two parts (verify against the package): integer 0-8.")
    score_4 = dspy.OutputField(desc="Part 1 opens a loop -- a visual question we need answered: 0 or 10.")
    score_5 = dspy.OutputField(desc="Head fake - earned reversal -- part 2 pays off with an earned reversal, not just the surface event; withhold if the turn has no visible desire/belief: 0 or 8.")
    score_6 = dspy.OutputField(desc="WHY readable - desire-image -- a constant desire-image carries across both parts: 0 or 7.")
    score_7 = dspy.OutputField(desc="WHY readable - belief shifts visually -- what visibly shifts is belief, clouded in part 1, resurfacing in part 2; withhold if desire is narrated as 'returning': 0 or 7.")
    score_8 = dspy.OutputField(desc="Belief on a spectrum -- withhold if belief flips absolute (doubt->certainty) instead of moving along a spectrum: 0 or 5.")
    score_9 = dspy.OutputField(desc="Expressed, not performed -- withhold if he performs the want for a crowd's verdict instead of expressing it: 0 or 5.")
    score_10 = dspy.OutputField(desc="Team turn = mirroring -- withhold if a team's turn is asserted in dialogue rather than shown as mirroring (others catching the same fire in frame): 0 or 5.")
    score_11 = dspy.OutputField(desc="Parts chain -- part 1 makes us need part 2; no dead beat between: integer 0-9.")
    score_12 = dspy.OutputField(desc="Visual & image-generatable -- each part is a clear, shootable image in proper screenplay form (slugline / action / dialogue): integer 0-12.")
    score_13 = dspy.OutputField(desc="Concrete & dramatic -- real action and dialogue, not narration or interiority: integer 0-8.")
    score_14 = dspy.OutputField(desc="The Dance -- every beat follows the last by THEREFORE or BUT, never AND THEN: integer 0-15. 0 = 'and then' detail-piling (KILL check: a 0 rejects regardless of total).")
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
    criteria = dspy.InputField(desc="The 11 weighted checks + the verdict rule.")
    verdict = dspy.OutputField(desc="'PASS' or 'REJECT' (the engine decides by the floor; report your read).")
    score_1 = dspy.OutputField(desc="Above-fold hook -- first line (<~120 chars) stands alone as a second hook: curiosity/tension reinforcing the title's promise: integer 0-20.")
    score_2 = dspy.OutputField(desc="Hook no summary/spoil -- the first line does NOT summarize or spoil: integer 0-5.")
    score_3 = dspy.OutputField(desc="Names the wound -- names the audience's emotional state/wound so the right viewer thinks 'that's me'; specific, mirrors not labels: integer 0-8.")
    score_4 = dspy.OutputField(desc="Lands the WHY -- highest when it lands the desire-vs-belief tension beneath the feeling, not just the surface state: integer 0-8.")
    score_5 = dspy.OutputField(desc="Authentic desire -- dock when the desire is staged as ego-performance rather than the authentic want the viewer would privately own: integer 0-5.")
    score_6 = dspy.OutputField(desc="Belief not fixed -- dock if it pins one fixed belief-state as if every viewer shares it, or treats the desire as something the video gives them: integer 0-4.")
    score_7 = dspy.OutputField(desc="No spoiler -- doesn't reveal the resolution; leaves the loop open (check against the package): integer 0-8.")
    score_8 = dspy.OutputField(desc="No overpromise -- promises only what the story actually delivers (check against the package): integer 0-7.")
    score_9 = dspy.OutputField(desc="Repels anti-audience -- the framing signals who it is NOT for, so the wrong viewer self-selects out: integer 0-10.")
    score_10 = dspy.OutputField(desc="Algorithm signal -- uses the natural terms the target audience would search/recognize; no keyword-stuffing: integer 0-15.")
    score_11 = dspy.OutputField(desc="Tight, plain, ~600 chars -- a few lines, front-loaded, plain language, no jargon/fluff (~600 chars target): integer 0-10.")
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
