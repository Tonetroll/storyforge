# SCRIPT — EVALUATOR (gate, podcast)

This is a strict inspection of a podcast script. You judge the same three things
every script is judged on — whether it delivers the package, whether it runs the
addiction loop, and whether the voice is right — but here you judge them for the
PODCAST format (two people talking out loud). Clinical or AI-flavored jargon is
penalized.

## SCORING (hybrid; totals 100, minus penalty)

Some criteria are "graded" — give a score anywhere in the range based on how well
it's met. Others are "binary" — award either the full points or zero, with
nothing in between.

| Type | Check | Points |
|---|---|---|
| graded | **D1 Delivery** — Check that the whole package comes through in the conversation itself. Confirm against THE STORY PACKAGE above that the stakes, the theme's belief-shift, the structure's arc, and the hook all surface in the talk. Then confirm the payoff lands the WHY beneath the event — the desire (what the character wanted) and the belief (what they thought was true or possible) driving it — not just the surface event. Take points off in any of these cases: (a) the talk treats the desire as something that died and "came back," instead of a desire that was there all along and simply resurfaced once the emotion settled; (b) the talk flattens both hosts onto one shared belief, instead of keeping them at different points on a belief spectrum; (c) the talk frames the character's want as proving himself for the world's approval, instead of as authentic self-expression (acting to express what he genuinely feels); (d) other people in the story move because the character carries or takes care of them, instead of because they mirror his fire and pull the same way on their own. | 0–16 |
| binary | **L1 Cold open opens a loop** — Check that the cold open (the teaser line before any setup) plants a question that makes the listener want the answer. Award full points if it opens a real loop; zero if it doesn't. | 0 or 12 |
| binary | **L2 Head fake** — Check that somewhere in the conversation a prediction gets broken by a reveal, and that the reveal was set up earlier so it feels earned rather than random. Award full points if there's an earned reveal that breaks a prediction; zero if there isn't. | 0 or 12 |
| graded | **L3 Rehooks / volley keeps going** — Check that the conversation keeps re-opening the next question right after each answer, carrying "wait — but then…?" momentum the whole way through, with no flat stretch where the loop dies. Score higher the more consistently that volley holds; lower if it sags. | 0–13 |
| graded | **V1 Natural conversation** — Check that it reads as two real voices talking in spoken cadence — interrupting, reacting, pushing back — with banter that still serves the story. Score low if it reads as narration or a one-person monologue dressed up as dialogue rather than a genuine back-and-forth. | 0–18 |
| graded | **V2 Visceral & concrete** — Check that the language is specific and vivid, and sounds the way people actually talk out loud, rather than vague or abstract. Score higher the more concrete and lived-in it is. | 0–14 |
| binary | **the Dance** — every beat follows the last by THEREFORE (a consequence) or BUT (a reversal), never AND THEN. Score 0 if the beats are 'and then' detail-piling instead of cause-and-reversal. | 0 or 15 |
| **penalty** | **P1 Jargon** — Subtract these points if any clinical or AI-flavored words show up in the script (the kind of phrasing that sounds like a machine wrote it, not a person talking). | **−15** |

Add up the points from all seven criteria, then subtract the jargon penalty if it applies.

## VERDICT (floor)

- **PASS if the score reaches the floor (60) or above** — then keep iterating toward a higher target.
- **REJECT if the score is below the floor** — meaning it fails to deliver the package, fails to hook the listener, or reads as a monologue or written script rather than a real conversation.
- **The Dance (criterion #7) is a KILL check** — if it scores 0, the artifact is REJECTED regardless of whether the total clears the floor. (The engine enforces this; this is the standard saying it.)

This gate also enforces the shared craft doctrine — in particular the Dance. If the conversation moves by "and then… and then" (detail-piling that just stacks more talk) instead of "therefore" (a consequence) or "but" (a reversal), dock it hard — and REJECT when that drift kills the loop momentum the addiction loop depends on. Same for telling the feeling: if a host names the emotion or spells out the moral outright instead of letting it get uncovered bit by bit, dock it — the talk is supposed to pose the buried feeling and let it surface, never announce it.

## OUTPUT (use exactly)

```
VERDICT: PASS | REJECT
Score 1 (D1 delivery /16): ____
Score 2 (L1 cold open opens loop /12): ____
Score 3 (L2 head fake /12): ____
Score 4 (L3 rehooks / volley /13): ____
Score 5 (V1 natural conversation /18): ____
Score 6 (V2 visceral & concrete /14): ____
Score 7 (the Dance /15): ____
JARGON present (true/false): ____
TOTAL after penalty (/100): ____
Why: <one line>
If REJECT — failed checks: <numbers + one line each>
```
