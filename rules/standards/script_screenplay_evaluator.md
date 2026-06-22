# SCRIPT — EVALUATOR (gate, two-part screenplay)

Strict inspection. You are judging the same three things every script is judged on —
**delivery** (does it carry the package the earlier stages built), **the addiction
loop** (does it open a question and pay it off so the viewer needs the next part), and
**craft** (is it written well and shootable) — but for the TWO-PART SCREENPLAY format.
Each criterion below is one self-contained test: judge it on its own, and award the
points only when that exact condition is met. Jargon (clinical or AI-sounding wording)
costs a penalty.

## SCORING (each test stands alone; the checks total 100, then subtract the penalty)

| # | Check | Points |
|---|---|---|
| 1 | **Delivery — stakes** — The stakes are dramatized (played out in action on screen, not summarized) across the two parts. Check them against THE STORY PACKAGE above — the stakes there must actually appear in the scenes. | 0–6 |
| 2 | **Delivery — belief-shift** — The theme's belief-shift is dramatized across the two parts. "Belief-shift" = what the protagonist believes at the start and at the end; the old belief is never broken by an event — it shifts through the character's own reflection. Check it against THE STORY PACKAGE above. | 0–6 |
| 3 | **Delivery — arc & hook** — The structure's arc and the hook are both dramatized across the two parts. Check them against THE STORY PACKAGE above. | 0–8 |
| 4 | **Part 1 opens a loop** — Part 1 raises a visual question the viewer needs answered (a loop). This is all-or-nothing: award the full points or zero, nothing in between. | 0 or 7 |
| 5 | **Head fake — earned reversal** — Part 2 pays off with a reversal that surprises but, in hindsight, Part 1 already made it make sense — not just the surface event. All-or-nothing. Award zero if the turn is only a plot event with no visible desire or belief underneath it (you can see *what* happened but not the wanting/believing that drove it). | 0 or 6 |
| 6 | **WHY readable — desire-image** — The WHY is readable on screen: one constant desire-image (a recurring look, object, or place that shows the character's steady want) carries across both parts. All-or-nothing. | 0 or 7 |
| 7 | **WHY readable — belief shifts visually** — What visibly changes on screen is belief, not desire: in Part 1 the belief is clouded by emotional resistance (a flinch, a turning-away, a stalled body), and in Part 2 it resurfaces. All-or-nothing. Award zero if the desire is narrated as "returning" rather than shown resurfacing on its own. | 0 or 7 |
| 8 | **Belief on a spectrum** — Belief moves along a range (more sure / less sure / wavering / steadying), not as an on/off flip. All-or-nothing. Award zero if belief flips absolutely (from total doubt straight to total certainty) instead of sliding along the spectrum. | 0 or 5 |
| 9 | **Expressed, not performed** — The character acts on the want for its own sake (expressing it from the inside out), not by performing it for a crowd to win their verdict or look impressive. All-or-nothing. Award zero if he performs the want for a crowd's approval instead of expressing it. | 0 or 5 |
| 10 | **Team turn = mirroring** — If a team turns with him, it is *shown* as mirroring — others catching the same fire in the frame (eyes lifting, a step falling into rhythm), drawn there on their own. All-or-nothing. Award zero if the team's turn is merely asserted in dialogue (a line claims they turned) rather than shown as mirroring. | 0 or 5 |
| 11 | **Parts chain** — The two parts chain together: the end of Part 1 makes the viewer need Part 2, with no dead beat (no flat, unhooked moment) at the cut between them. | 0–6 |
| 12 | **Visual & image-generatable** — Each part is a clear, shootable image written in proper screenplay form (slugline / action / dialogue) — something an artist could turn into a single picture. | 0–9 |
| 13 | **Concrete & dramatic** — It uses real action and dialogue on the page, not narration or interiority (not telling us what a character thinks or feels inside). | 0–8 |
| 14 | **the Dance** — every beat follows the last by THEREFORE (a consequence) or BUT (a reversal), never AND THEN. Score 0 if the beats are 'and then' detail-piling instead of cause-and-reversal. | 0–15 |
| **penalty** | **P1 Jargon** — clinical or AI-sounding words are present. | **−15** |

Add up the points from criteria 1–14, then subtract the jargon penalty if it applies.

## VERDICT (floor)

- **PASS if the score clears the floor (60)** — then keep iterating toward a higher target.
- **REJECT below the floor (under 60)** — it fails because it doesn't deliver the package, the two parts don't form a loop, or it isn't shootable.
- **the Dance (criterion #14) is a KILL check** — if it scores 0 the artifact is REJECTED regardless of whether the total clears the floor. The engine enforces this.

This gate also enforces the shared craft doctrine — in particular the Dance. REJECT (or dock) work whose beats connect by "and then" (detail-piling that lets the viewer drift between the two scenes) instead of "therefore" (consequence) or "but" (reversal), and work that TELLS the feeling outright instead of uncovering it bit by bit through the images. The feeling must be set up and left to surface on screen, never announced.

## OUTPUT (use exactly)

```
VERDICT: PASS | REJECT
Score 1 (delivery — stakes /6): ____
Score 2 (delivery — belief-shift /6): ____
Score 3 (delivery — arc & hook /8): ____
Score 4 (part 1 opens a loop /7): ____
Score 5 (head fake — earned reversal /6): ____
Score 6 (WHY readable — desire-image /7): ____
Score 7 (WHY readable — belief shifts visually /7): ____
Score 8 (belief on a spectrum /5): ____
Score 9 (expressed, not performed /5): ____
Score 10 (team turn = mirroring /5): ____
Score 11 (parts chain /6): ____
Score 12 (visual & image-generatable /9): ____
Score 13 (concrete & dramatic /8): ____
Score 14 (the Dance /15): ____
JARGON present (true/false): ____
TOTAL after penalty (/100): ____
Why: <one line>
If REJECT — failed checks: <numbers + one line each>
```
