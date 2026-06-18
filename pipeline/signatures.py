"""DSPy Signatures = the machine-enforced contract for the STORY gate.

The written standards live in rules/standards/generator.md and evaluator.md and
are passed in at runtime as `standard` / `criteria`, so editing the MD changes
behaviour without touching this file. These signatures define the SHAPE of an
idea: the five gate-ready fields, the gate verdict, and the revision.
"""

import dspy


class GenerateStoryIdea(dspy.Signature):
    """Generate ONE story idea from the brief, following the standard.

    A story evokes two DIFFERENT emotions: a pull-in that opens a loop and a
    resolution that closes it. Information is not a story. Output both halves --
    the open-loop one-liner AND the resolution (the payoff). Never leave the
    resolution blank. Do not write a beautiful sentence that tells instead of
    opens; that has zero curiosity and nobody watches it."""

    brief = dspy.InputField(desc="The seed/brief: what to make a story idea about.")
    standard = dspy.InputField(desc="The generator standard the idea MUST satisfy (rules/standards/generator.md).")
    one_liner = dspy.OutputField(desc="The open loop. Concrete, speakable in under 4 seconds, no abstraction. Does NOT give away the answer.")
    resolution = dspy.OutputField(desc="The payoff that closes the loop toward the end. Defined, never blank.")
    reaction_1 = dspy.OutputField(desc="Pull-in emotion, one of: LOL / WTF / WOW.")
    reaction_2 = dspy.OutputField(desc="Resolution emotion, one of: Aah / Oooh / Finally. MUST be different from reaction_1.")
    viewer_action = dspy.OutputField(desc="Exactly ONE: Do / Sale / Sign-up / Save / Share / Try / Apply / Reflect.")
    topic = dspy.OutputField(desc="3-6 words naming what THIS specific story is about, used for the filename. Concrete subject (e.g. 'trump hides world cup crash'). NEVER generic words like 'story', 'idea', or 'video'.")


class GateStoryIdea(dspy.Signature):
    """You are a strict, impartial gate. You did NOT write this idea; do not be
    generous. Judge it against the six checks. ALL six YES = PASS; ANY no =
    REJECT. On PASS, also rate how strong it is (0-100) -- merely passing is ~60,
    exceptional is ~95. On REJECT, score is 0 and you name the failing checks."""

    one_liner = dspy.InputField(desc="The idea's open-loop one-liner.")
    resolution = dspy.InputField(desc="The idea's stated resolution / payoff.")
    proposed_reaction_1 = dspy.InputField(desc="The generator's claimed pull-in emotion.")
    proposed_reaction_2 = dspy.InputField(desc="The generator's claimed resolution emotion.")
    proposed_viewer_action = dspy.InputField(desc="The generator's claimed single viewer action.")
    criteria = dspy.InputField(desc="The evaluator gate: the six checks + verdict rules (rules/standards/evaluator.md).")
    verdict = dspy.OutputField(desc="Exactly 'PASS' or 'REJECT'. REJECT if ANY criterion is absent (scores 0).")
    score_1 = dspy.OutputField(desc="Check 1 pull-in emotion: integer 0-25 by how strong/real the pull-in is. 0 = absent.")
    score_2 = dspy.OutputField(desc="Check 2 resolution emotion: integer 0-25 by how strong/real the resolution is. 0 = absent.")
    score_3 = dspy.OutputField(desc="Check 3 two DIFFERENT emotions: integer 0-20. 0 = same emotion twice, or one missing.")
    score_4 = dspy.OutputField(desc="Check 4 exactly one viewer action: integer 0-10. 0 = none, or more than one.")
    score_5 = dspy.OutputField(desc="Check 5 open loop: integer 0-10. 0 = the premise gives away the answer.")
    score_6 = dspy.OutputField(desc="Check 6 concrete & speakable in <4s: integer 0-10. 0 = abstract or too long.")
    reaction_1 = dspy.OutputField(desc="Your own read of the pull-in emotion (LOL/WTF/WOW), or 'none'.")
    reaction_2 = dspy.OutputField(desc="Your own read of the resolution emotion (Aah/Oooh/Finally), or 'none'.")
    viewer_action = dspy.OutputField(desc="The single viewer action you read, or 'none'.")
    failed_checks = dspy.OutputField(desc="If REJECT: the failing check numbers + one line each. If PASS: 'none'.")
    why = dspy.OutputField(desc="One line.")


class IterateStoryIdea(dspy.Signature):
    """Improve a PASSING idea using the gate's critique to push the score higher.
    Keep what already works; sharpen the hook, deepen the payoff, tighten the
    one-liner. Do not break what passed."""

    one_liner = dspy.InputField()
    resolution = dspy.InputField()
    reaction_1 = dspy.InputField()
    reaction_2 = dspy.InputField()
    viewer_action = dspy.InputField()
    critique = dspy.InputField(desc="The gate's why + weak points to push higher.")
    standard = dspy.InputField(desc="The generator standard to hold to (rules/standards/generator.md).")
    improved_one_liner = dspy.OutputField(desc="Sharper open-loop one-liner, still <4s and concrete.")
    improved_resolution = dspy.OutputField(desc="Stronger payoff that closes the loop.")
    improved_reaction_1 = dspy.OutputField(desc="Pull-in emotion (LOL/WTF/WOW).")
    improved_reaction_2 = dspy.OutputField(desc="Resolution emotion (Aah/Oooh/Finally), different from reaction_1.")
    improved_viewer_action = dspy.OutputField(desc="Exactly ONE viewer action.")
