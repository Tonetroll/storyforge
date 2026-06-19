# PACKAGING — EVALUATOR (12 binary criteria)

Score each of the 12 questions YES (full points) or NO (0). Derived from real CTR
data (winners >=10% CTR vs losers <5%). Higher = more clickable. Each question is
worth an equal share of 100; the total is the YES count scaled to 100.

## The 12 Binary Eval Questions

### Visual
- **Q1 — Visual Anchor:** a clear anchor — a face with strong emotional expression, AND/OR a bold graphic/icon/product that immediately draws the eye?
- **Q2 — Emotion or Intrigue:** strong emotion (shock, excitement, curiosity) OR visual intrigue through contrast, mystery, or unexpected elements?
- **Q3 — Directional Cues:** the subject looking at the object, gaze direction, pointing, arrows, layout flow — guiding the eye toward the title or key element?
- **Q4 — Text Readability:** any text legible at thumbnail size (bold font, high contrast, max 4 words)?
- **Q5 — Background:** if tutorial — clean/uncluttered (dark, simple, blurred) so the subject pops; if a story — the transformed setting.
- **Q6 — Visual Hierarchy:** clear hierarchy — you instantly know what to look at first, second, third?
- **Q7 — Shows Result:** shows a result, transformation, or payoff — not just the process or a neutral image?
- **Q8 — Logos or Icons:** recognizable platform logos, brand icons, tools, symbols that signal what the transformation is about?

### Title
- **Q9 — Curiosity Gap:** an open loop — implies something surprising, counterintuitive, or hidden the viewer needs to see?
- **Q10 — Specific Outcome:** promises a specific outcome/transformation/result — not just a topic?
- **Q11 — Payoff Clarity:** even if intriguing, is the payoff clear enough that viewers know what they're getting?
- **Q12 — Accessible Language:** plain language a non-expert understands, no jargon or insider terms?

## Scoring (your tiers)

| YES count | Meaning |
|---|---|
| 10-12 | Strong package — high confidence / likely high CTR |
| 7-9 | Mid-tier — likely needs one fix |
| 4-6 | Weak — thumbnail or title needs a rework |
| 0-3 | Low confidence — likely to underperform |

**Clickbait check (post-publish):** if the score is 8+ but AVD% is under 15%, the
packaging is misleading — fix the title to match what the video delivers.

## VERDICT (floor)

- **PASS if the score clears the floor (60 ≈ 7-8 YES)**; iterate toward target.
- **REJECT below the floor** — too few criteria met to perform.

## OUTPUT (use exactly)

```
VERDICT: PASS | REJECT
Q1 visual anchor: 0/1
Q2 emotion or intrigue: 0/1
Q3 directional cues: 0/1
Q4 text readability: 0/1
Q5 background: 0/1
Q6 visual hierarchy: 0/1
Q7 shows result: 0/1
Q8 logos or icons: 0/1
Q9 curiosity gap: 0/1
Q10 specific outcome: 0/1
Q11 payoff clarity: 0/1
Q12 accessible language: 0/1
TOTAL (YES count, /12): ____
Why: <one line>
If REJECT — failed checks: <which Q numbers + one line each>
```
