# 🧩 TODO 8 — Semantic (vector) retrieval

Rung 2 of the retrieval ladder: **vector search**. Keyword search (rung 1, written for you) finds
exact terms; vector search finds **meaning** — "revenue growth" should surface a note about "the
Outdoors category driving Q3 sales" even with no shared words. The `OracleVectorStore` does the
embedding and the cosine ranking; you just call it and adapt the result to the ladder's row shape.

### What to implement
Fill in `vector_search(query, namespace=None, k=5)` (keep `keyword_search` and `_as_row`):
1. Build an optional metadata filter: `flt = {"namespace": namespace} if namespace else None`.
2. `pairs = store.similarity_search_with_score(query, k=k, filter=flt)` — each pair is
   `(Document, cosine_distance)` where **smaller distance = closer in meaning**.
3. Return `[_as_row(d, dist) for d, dist in pairs]`.

> 💡 `similarity_search_with_score` embeds the query with the **same** in-database model used to embed
> the documents — that shared model is what makes the distances meaningful. The `_as_row` adapter
> keeps vector and keyword hits in one shape so the next rung (RRF) can fuse them.

## ✅ Solution

Replace the placeholder cell with this, then run the **`✅ TODO 8 check`** cell:

```python
from langchain_oracledb.retrievers.text_search import OracleTextSearchRetriever

# Keyword retriever: Oracle Text CONTAINS search, provided by langchain_oracledb (no hand-written SQL).
# Built once over the AGENT_VSTORE text index and reused by the ladder. We pull a wide pool (k=30) and
# narrow by namespace in Python, so one retriever serves every namespace.
_keyword_retriever = OracleTextSearchRetriever(vector_store=store, k=30, fuzzy=True, return_scores=True)

def _as_row(doc, score):
    """Adapt a langchain Document to the dict-row shape the rest of the ladder already uses."""
    return {"ID": doc.id, "TEXT": doc.page_content, "META": doc.metadata, "score": score}

def keyword_search(query, namespace=None, k=5):
    docs = _keyword_retriever.invoke(query)
    if namespace:
        docs = [d for d in docs if d.metadata.get("namespace") == namespace]
    return [_as_row(d, d.metadata.get("score")) for d in docs[:k]]

def vector_search(query, namespace=None, k=5):
    # similarity_search_with_score returns (Document, cosine_distance); smaller distance = closer in meaning.
    flt = {"namespace": namespace} if namespace else None
    pairs = store.similarity_search_with_score(query, k=k, filter=flt)
    return [_as_row(d, dist) for d, dist in pairs]

print("Rungs 1-2 ready: keyword_search (OracleTextSearchRetriever) + vector_search (similarity_search_with_score).")
```

_Generated from `total_recall_complete.ipynb` — the exact reference implementation._
