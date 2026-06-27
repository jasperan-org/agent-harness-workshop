# 🧩 TODO 9 — Fuse keyword + vector results with Reciprocal Rank Fusion

Now you have two rankings that disagree — keyword (exact terms) and vector (meaning) — and need *one*
list. The trick is **Reciprocal Rank Fusion (RRF)**: ignore the raw, incomparable scores and use only
each row's **rank** in each list. A row earns `1/(c + rank)` from every list it appears in, and those
contributions **add up** — so anything found by *both* methods rises to the top.

### What to implement
Fill in `reciprocal_rank_fusion(ranked_lists, c=60)` (keep `hybrid_search` below it):
1. Walk every list; for each row at position `rank` (0-based), add `1.0 / (c + rank + 1)` to that
   row's running score, keyed by `row["ID"]`. Keep a `row_by_id` map so you can return the full row.
2. Sort the IDs by fused score, **highest first**.
3. Return the rows in that order, each tagged with its score:
   `dict(row_by_id[rid], rrf=round(score, 5))`.

> 💡 RRF needs no training and no score normalisation — it only trusts *ordering*. That is why it
> fuses a cosine-distance list and a keyword-relevance list, whose scores are on totally different
> scales, without either one drowning out the other.

## ✅ Solution

Replace the placeholder cell with this, then run the **`✅ TODO 9 check`** cell:

```python
def reciprocal_rank_fusion(ranked_lists, c=60):
    """Merge several ranked lists into one. Each row earns 1/(c+rank) from every list it appears in, so rows
    found by more than one method add up and rise. Returns rows sorted best-first, each tagged with 'rrf'."""
    fused, row_by_id = {}, {}
    for rows in ranked_lists:
        for rank, row in enumerate(rows):
            rid = row["ID"]
            row_by_id[rid] = row
            fused[rid] = fused.get(rid, 0.0) + 1.0 / (c + rank + 1)
    best_first = sorted(fused, key=fused.get, reverse=True)
    return [dict(row_by_id[rid], rrf=round(fused[rid], 5)) for rid in best_first]

def hybrid_search(query, namespace=None, k=5, pool=20):
    """Run keyword + vector over a candidate pool, then fuse with RRF and keep the top k."""
    vector_hits = vector_search(query, namespace, pool)
    keyword_hits = keyword_search(query, namespace, pool)
    return reciprocal_rank_fusion([vector_hits, keyword_hits])[:k]

print("Rung 4 ready: hybrid_search, built on a reusable reciprocal_rank_fusion helper.")
```

_Generated from `total_recall_complete.ipynb` — the exact reference implementation._
