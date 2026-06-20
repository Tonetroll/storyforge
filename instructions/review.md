# SOP — Human Review

**Goal:** turn your judgement into structured data the pipeline reads back.

**How:** open `review/human_review.csv` and add a row per artifact you judge:

```
asset_id,module,version,score,status,reason,next_action
elevator-mirror-practiced-fine_0001,IDEA,v03,88,accepted,funny + clear payoff,promote
generic-monday-motivation_0002,IDEA,v02,72,rejected,too generic,archive
slow-open-strong-finish_0003,IDEA,v04,80,revise,strong but slow open,rerun
```

- **status** must be one of: `accepted`, `rejected`, `revise`.
- **reason** is the most valuable field — it is why the decision was made.
- **next_action** is free-form routing intent (`promote` / `archive` / `rerun`).

Then run the router (`route.md`). Accepted rows feed the learning loop.
