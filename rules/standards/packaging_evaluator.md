# PACKAGING — EVALUATOR (12 weighted criteria)

Score each of the 12 criteria against its weight: award the full points or zero,
nothing in between. These criteria come from real click-through data (winning
thumbnails got 10% or higher click-through; losers under 5%). A higher total
means more clickable. Each criterion is ONE single, atomic test. The weights add
up to 100.

## THE 12 CRITERIA

### Visual

**Criterion 1 — Q1 visual anchor (9pt)**
The thumbnail has one clear anchor — the single thing the eye lands on first.
That anchor is a face showing a strong emotional expression, AND/OR a bold
graphic, icon, or product that immediately pulls the eye. Award the points only
if there are NO AI-generation artifacts: extra hands or fingers, melted or warped
text, garbled logos. Any such artifact makes the image look fake and fails the
criterion outright, because it instantly destroys the viewer's trust.

**Criterion 2 — Q2 emotion/intrigue (9pt)**
The thumbnail carries strong emotion (shock, excitement, curiosity) OR visual
intrigue created by contrast, mystery, or an unexpected element — and that
emotion reads as the WHY beneath the event, not just the event itself. The "WHY"
is the desire the person is chasing and the belief driving them: the visible pull
of wanting something and believing (or doubting) they can get it. The expression
must reach the emotional extreme the title's claim implies — a pleasant, neutral,
or "corporate" expression fails even when a face is present, and a big claim needs
shock, awe, or alarm rather than a mild smile. Dock the points when the emotion is
manufactured hype or ego-bait instead of the genuine value: a face or title
performing for the world's approval ("look how impressive this is"), shock the
video never pays off, or intensity with no real desire underneath it. Do NOT dock
honest intensity — a real want dialed up is fine; only flag a pull that is faked
or detached from what the video actually delivers. For a thumbnail with no face
(ambient or graphic), the equivalent is a named emotional target that the image
visibly delivers.

**Criterion 3 — Q3 directional cues (9pt)**
When a person is present, the thumbnail has eye contact with the viewer (the face
looking straight out) PLUS a separate cue that points the eye — gaze direction, a
pointing finger, an arrow, or the layout's flow — leading the eye toward the title
or the key element. A gaze aimed at an object inside the image does NOT count as
eye contact; you need both the eye contact and the separate cue. When there is no
human (an ambient or graphic thumbnail), the layout's flow must lead the eye to
the focal element.

**Criterion 4 — Q4 text readability (9pt)**
Any text on the thumbnail is legible at thumbnail size: bold font, high contrast,
four words maximum. Word count is a hard gate, not a preference. And text that
blends into the background fails regardless of how few words it is — it must sit on
a contrasting zone or carry a drop-shadow or outline to stay readable.

**Criterion 5 — Q5 background (8pt)**
For a tutorial, the background is clean and uncluttered — dark, simple, blurred —
so the subject pops off it. For a story, the background is the transformed setting
the story ends in. Either way, it fails if the background competes with the anchor
for the viewer's attention.

**Criterion 6 — Q6 visual hierarchy (8pt)**
The thumbnail has a clear visual hierarchy: you instantly know what to look at
first, second, and third, without having to hunt for it.

**Criterion 7 — Q7 shows result (8pt)**
The thumbnail shows a result, transformation, or payoff — the after-state once the
change has happened — not just the process or a neutral image. Show that
after-state visibly, but leave the mechanism unrevealed (that's Criterion 9). A
thumbnail that shows only the process, with no payoff visible, fails.

**Criterion 8 — Q8 logos/icons (8pt)**
The thumbnail has at least one recognizable, legible anchor object that signals
what the transformation is about — a platform logo, brand icon, tool, product,
known figure, or the payoff itself. It fails if there is no recognizable thing for
the viewer to latch onto.

### Title

**Criterion 9 — Q9 title curiosity gap (8pt)**
The title is an open loop — it implies something surprising, counterintuitive, or
hidden that the viewer needs to watch to see. And that loop turns on the WHY
beneath the event (the tension between someone's desire and their belief), so the
viewer feels the pull of wanting and believing rather than just being told what
happened. Leave the mechanism unrevealed so that clicking is what resolves the
gap; a title or thumbnail that gives away the whole answer fails this criterion.

**Criterion 10 — Q10 title specific outcome (8pt)**
The title promises a specific outcome, transformation, or result — not just a
topic. The bar is specific and concrete (a number, a named result, a
transformation), and it is NOT a command verb. Reward a concrete payoff
("$31K/Month Secret", "15 Titles: Get Millions of Views"); reject a vague
topic-statement ("The Self-Improvement Loop", "YouTube Growth Hacks").

**Criterion 11 — Q11 title payoff clarity (8pt)**
Even when the title is intriguing, the payoff is clear enough that viewers know
what they're actually going to get by watching.

**Criterion 12 — Q12 title accessible language (8pt)**
The title uses plain language a non-expert understands, with no jargon and no
insider terms.

## SCORING (your tiers)

| Weighted total | Meaning |
|---|---|
| 80-100 | Strong package — high confidence / likely high CTR |
| 60-79 | Mid-tier — likely needs one fix |
| 30-59 | Weak — thumbnail or title needs a rework |
| 0-29 | Low confidence — likely to underperform |

**Clickbait check (post-publish):** if the score is 80+ but AVD% (average view
duration) is under 15%, the packaging is misleading — fix the title to match what
the video actually delivers.

## VERDICT (floor)

- **PASS if the weighted total clears the floor (>= 60)** — then iterate toward target.
- **REJECT below the floor (< 60)** — too few criteria met to perform.

This gate also enforces the shared craft doctrine, on top of the 12 scores above:
the Dance still rules the click. REJECT or dock packaging whose title strings its
beats with "and then" — detail-piling a sequence of events — instead of turning on
a "therefore" (a consequence) or a "but" (a reversal) that opens a real loop. And
dock work that TELLS the feeling outright (announcing the emotion or the moral)
instead of posing it so the click is what uncovers it. A title or thumbnail that
preaches the payoff, or merely lists what happened, fails the spirit of the gate
even when boxes are checked.

## OUTPUT (use exactly)

```
VERDICT: PASS | REJECT
Score 1 (Q1 visual anchor /9): ____
Score 2 (Q2 emotion/intrigue /9): ____
Score 3 (Q3 directional cues /9): ____
Score 4 (Q4 text readability /9): ____
Score 5 (Q5 background /8): ____
Score 6 (Q6 visual hierarchy /8): ____
Score 7 (Q7 shows result /8): ____
Score 8 (Q8 logos/icons /8): ____
Score 9 (Q9 title curiosity gap /8): ____
Score 10 (Q10 title specific outcome /8): ____
Score 11 (Q11 title payoff clarity /8): ____
Score 12 (Q12 title accessible language /8): ____
TOTAL (/100): ____
Why: <one line>
If REJECT — failed_checks: <which criteria numbers + one line each>
```
