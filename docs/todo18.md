# 🧩 TODO 18 — Harvest recurring workflows into skills

The agent should not promote *every* one-off into a skill — only the patterns that **repeat** and
**work**. `harvest_skills` is that policy, and it is the engine of continual learning: it selects
workflows that are recurring (`occurrences >= min`), recent, and reliable (`successes > failures`),
and promotes each via the function you just wrote. Run it on a schedule and the agent grows its own
skill library from lived experience — no human curation.

### What to implement
Fill in `harvest_skills()` (keep `HARVEST_KNOBS` above it):
1. Select the qualifying workflows: `SELECT id FROM agent_workflow WHERE promoted='N' AND occurrences
   >= :m AND last_seen >= SYSTIMESTAMP - :d AND successes > failures ORDER BY successes DESC,
   occurrences DESC`, binding `m=HARVEST_KNOBS["min_occurrences"]`, `d=HARVEST_KNOBS["recency_days"]`.
2. Promote each and collect the names:
   `return [promote_workflow_to_skill(c["ID"]).get("promoted_skill") for c in candidates]`.

> 💡 The thresholds are the *governance* of learning. `occurrences >= 3` ignores flukes;
> `successes > failures` ignores patterns that don't actually work; the recency window forgets stale
> habits. Continual learning without a policy like this just accumulates noise.

## ✅ Solution

Replace the placeholder cell with this, then run the **`✅ TODO 18 check`** cell:

```python
HARVEST_KNOBS = {"min_occurrences": 3, "recency_days": 30}

def harvest_skills():
    candidates = fetch_rows(conn, '''SELECT id FROM agent_workflow
        WHERE promoted='N' AND occurrences >= :m AND last_seen >= SYSTIMESTAMP - :d
          AND successes > failures
        ORDER BY successes DESC, occurrences DESC''',
        {"m": HARVEST_KNOBS["min_occurrences"], "d": HARVEST_KNOBS["recency_days"]})
    return [promote_workflow_to_skill(c["ID"]).get("promoted_skill") for c in candidates]

print("Harvester ready: harvest_skills() promotes only recurring, reliable workflows.")
```

_Generated from `total_recall_complete.ipynb` — the exact reference implementation._
