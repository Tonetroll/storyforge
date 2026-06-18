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
