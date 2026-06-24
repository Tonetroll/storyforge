# SCRIPT — EVALUATOR (gate, long-form narration)

Inspect the long-form narration strictly. You are judging the same three things
every script gate judges — whether it DELIVERS the package, whether it runs the
ADDICTION LOOP, and whether the VOICE is right — but tuned for the long-form format.
Clinical or AI-sounding jargon costs points (see the penalty).

## SCORING (hybrid; totals 100, minus penalty)

Each criterion below is ONE atomic test — it checks one thing. Score each on its own
scale, add the points together, then subtract the jargon penalty. Some criteria are
"graded" (give a score anywhere on the range) and some are "binary" (give full points
or zero, nothing in between).

### Delivery

- **D1 Package delivery (graded, 0–5)** — The narration carries the stakes, the
  theme's belief-shift (what the character believed at the start versus the end), the
  structure's arc, and the hook. Check each against THE STORY PACKAGE above — each
  must be present in the narration, not just assumed. 0 = the package is absent.

- **D2 Payoff lands the WHY (graded, 0–4)** — The payoff lands the WHY beneath the
  event — the desire the character wanted and the belief that drove them — not just
  the surface event. A payoff that reports only WHAT happened, without the wanting and
  believing underneath, scores toward 0.

- **D3 Desire constant, resurfaces (graded, 0–3)** — The desire stays constant while
  the belief that it is reachable visibly wavers under emotional resistance — a
  setback, loss, or simply not feeling it — and then resurfaces later as if it was
  always there, rather than being switched back on like a comeback. Dock a desire that
  dies and "comes back." 0 = desire vanishes and returns.

- **D4 Belief on a spectrum (graded, 0–2)** — People sit at different points of
  belief (some convinced, some doubting, some given up), not all at the same level.
  0 = everyone locked at one shared conviction.

- **D5 Authentic, not ego/proving (graded, 0–1)** — The character's drive is authentic
  self-expression (acting on what he genuinely feels, for its own sake), not ego —
  proving himself for the crowd's approval — and not him carrying or rescuing the
  others. 0 = ego/proving or carrying others.

- **D6 Team mirrors (graded, 0–1)** — Any team comes together by its people mirroring
  each other's desire (each drawn toward the same value), not by one person hauling
  them along. 0 = hauled/carried.

### The addiction loop

- **L1 Hook opens a loop (binary, 0 or 12)** — A "loop" is an unanswered question the
  viewer wants resolved; the "spine" loop is the one big question the whole piece
  will eventually answer. Award the full 12 when an early line clearly opens that
  spine question. Otherwise score zero.

- **L2 Head fake (binary, 0 or 12)** — A "head fake" is a reveal that breaks a
  prediction the viewer was led to make, and that the story set up beforehand so it
  feels earned rather than random. Award the full 12 when at least one such earned
  reveal is present. Otherwise score zero.

- **L3 Loops chain / no dead air (graded, 0–13)** — Loops should be nested and chained
  so the piece keeps moving across its full length — one question opening before the
  last fully closes. "Dead air" is a stretch where no open question is pulling the
  viewer forward and the narration sags. Lower the score toward zero wherever the
  chain goes slack and the piece drifts into dead air.

### Voice

- **V1 Immersive narration (graded, 0–18)** — The narration should flow and breathe,
  build as it goes, and give moments room to land rather than being clipped and
  rushed. Lower the score toward zero as the prose turns clipped, choppy, or stops
  building.

- **V2 Visceral & concrete (graded, 0–14)** — The narration should paint the scene
  with concrete detail, stay specific, and keep the action in the present and close.
  Lower the score toward zero as it turns vague, abstract, or removed from the scene.

### The Dance

- **The Dance (graded, 0–15)** — Every beat follows the last by THEREFORE (a
  consequence) or BUT (a reversal), never AND THEN. Score 0 if the beats are "and
  then" detail-piling instead of cause-and-reversal.

### Penalty

- **P1 Jargon (penalty, −15)** — "Jargon" here means clinical or AI-sounding words —
  language that describes the story instead of telling it. Subtract 15 if any such
  clinical or AI jargon appears anywhere in the narration.

## VERDICT (floor)

The gate also enforces the shared craft doctrine — the Dance most of all. REJECT or
dock narration whose beats connect by "and then" (detail-piling that lets the viewer
drift) instead of "therefore" (a consequence) or "but" (a reversal) that opens the
loops, and narration that TELLS the feeling outright instead of posing it and letting
it be uncovered bit by bit. This reads through the rows above — slack chains land in
L3, an announced feeling instead of an earned payoff lands in D1 — so apply it there
rather than as a separate score.

- **PASS if the score (after the penalty) reaches the floor of 60** — then keep
  iterating toward a higher target.
- **REJECT below 60** — it fails because it doesn't deliver the package, doesn't hook,
  or sags into dead air.
- **The Dance (criterion #12) is a KILL check** — if it scores 0 the artifact is
  REJECTED regardless of whether the total clears the floor. (The engine enforces this.)

## OUTPUT (use exactly)

```
VERDICT: PASS | REJECT
Score 1 (D1 package delivery /5): ____
Score 2 (D2 payoff lands the WHY /4): ____
Score 3 (D3 desire constant, resurfaces /3): ____
Score 4 (D4 belief on a spectrum /2): ____
Score 5 (D5 authentic, not ego/proving /1): ____
Score 6 (D6 team mirrors /1): ____
Score 7 (L1 hook opens loop /12): ____
Score 8 (L2 head fake /12): ____
Score 9 (L3 loops chain /13): ____
Score 10 (V1 immersive narration /18): ____
Score 11 (V2 visceral & concrete /14): ____
Score 12 (the Dance /15): ____
JARGON present (true/false): ____
TOTAL after penalty (/100): ____
Why: <one line>
If REJECT — failed checks: <numbers + one line each>
```
