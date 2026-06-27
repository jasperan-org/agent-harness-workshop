# 🧩 TODO 10 — Rerank the shortlist with a cross-encoder

The last rung. RRF gives a good shortlist, but it still only knows *ranks*. A **cross-encoder** reads
the query and each candidate **together** and scores true relevance — the most accurate signal, too
expensive to run over the whole corpus, perfect for re-ordering a shortlist of ~20. Here it runs
**inside the database** via `PREDICTION(...)`. Crucially, it must **degrade gracefully**: if the
reranker model is not loaded (this workshop loads only the embedder by default), fall back to the
order you were given.

### What to implement
Fill in `rerank(query, candidates, k=5)`:
1. **Fallback first:** `if not RERANK_AVAILABLE or not candidates: return [dict(c, rerank_score=None)
   for c in candidates[:k]]`.
2. Otherwise score each candidate in one query: build `docs = [str(c["TEXT"])[:2000] for c in
   candidates]`, then `fetch_rows(conn, "SELECT t.idx AS idx, PREDICTION({CFG['RERANK_MODEL']} USING
   (:q || ' [SEP] ' || t.doc) AS DATA) AS score FROM JSON_TABLE(:docs, '$[*]' COLUMNS (idx FOR
   ORDINALITY, doc VARCHAR2(4000) PATH '$')) t", {"q": query, "docs": json.dumps(docs)})`.
3. Attach scores, sort by `rerank_score` **descending**, return the top `k`.

> 💡 The retrieval ladder is now complete — keyword → vector → **RRF** → **rerank**. Each rung trades
> a little more compute for a little more precision; the graceful fallback means the ladder always
> returns *something* useful even when a rung is missing.

## ✅ Solution

Replace the placeholder cell with this, then run the **`✅ TODO 10 check`** cell:

```python
def rerank(query, candidates, k=5):
    """Cross-encoder rescoring via the in-DB reranker. Tags each row with 'rerank_score' (higher = more
    relevant) and returns them reordered by it, or the input order if the reranker is unavailable."""
    if not RERANK_AVAILABLE or not candidates:
        return [dict(c, rerank_score=None) for c in candidates[:k]]
    docs = [str(c["TEXT"])[:2000] for c in candidates]
    rows = fetch_rows(conn, f'''
        SELECT t.idx AS idx,
               PREDICTION({CFG['RERANK_MODEL']} USING (:q || ' [SEP] ' || t.doc) AS DATA) AS score
        FROM JSON_TABLE(:docs, '$[*]' COLUMNS (idx FOR ORDINALITY, doc VARCHAR2(4000) PATH '$')) t''',
        {"q": query, "docs": json.dumps(docs)})
    scored = [dict(candidates[r["IDX"] - 1], rerank_score=float(r["SCORE"])) for r in rows]
    scored.sort(key=lambda c: c["rerank_score"], reverse=True)
    return scored[:k]

print("Rung 5 ready: rerank (raw cross-encoder score; higher = more relevant).")
```

_Generated from `total_recall_complete.ipynb` — the exact reference implementation._
