# SOP — Human Review

**Goal:** turn your judgement into changes the pipeline actually learns from.

**How:** review happens in conversation with Claude — you give the verdict and
your reasoning; Claude records it and routes the lesson into the system. Pass/
fail isn't enough; the reasoning is the point. The most valuable case is when you
REJECT something the gate APPROVED — that means the gate's standard is wrong, and
the lesson is routed to fix it, so the next run catches what you caught.

Every verdict is written to `review/human_review.md` — an append-only journal of
what you decided and why. Claude writes it; don't hand-edit it.

Before any lesson changes a standard / profile / craft file, Claude first plays
back its understanding and the amplification (what it changes, and for which
scope — this stage / this channel / all channels) and waits for your yes.

**Legacy:** the old CSV + `route` batch path still exists for back-compat but is
not how you review. See the `review-logging` skill.
