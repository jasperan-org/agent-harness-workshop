# 🧩 TODO 13 — Make tools retrievable by meaning

An agent with 50 tools cannot put all 50 schemas in every prompt — that is wasted context and worse
decisions. Instead we store each tool's **JSON schema + an embedding of its description** in the
`agent_tools` table, indexed with **HNSW**, and retrieve only the handful relevant to the current
request. This is *just-in-time tools*: the toolbox is memory, searched by meaning.

### What to implement
Fill in `retrieve_tools(query, k=6)` — one SQL query against `agent_tools`:
1. Embed the query **in the database** and rank by cosine distance:
   `VECTOR_DISTANCE(embedding, VECTOR_EMBEDDING({CFG['EMBED_MODEL']} USING :q AS DATA), COSINE) dist`.
2. Select `name, description, tool_schema, ... dist`, `ORDER BY dist`, and
   `FETCH APPROX FIRST :k ROWS ONLY` (the `APPROX` keyword tells Oracle to use the HNSW index).
3. Return the rows via `fetch_rows(conn, sql, {"q": query, "k": k})`.

> 💡 `FETCH APPROX FIRST … ROWS ONLY` is what turns a brute-force distance scan into an
> index-accelerated nearest-neighbour search. The same one-line pattern powers tool, skill, and
> workflow retrieval throughout the harness.

## ✅ Solution

Replace the placeholder cell with this, then run the **`✅ TODO 13 check`** cell:

```python
def retrieve_tools(query, k=6):
    return fetch_rows(conn, f'''SELECT name, description, tool_schema,
                   VECTOR_DISTANCE(embedding, VECTOR_EMBEDDING({CFG['EMBED_MODEL']} USING :q AS DATA), COSINE) dist
                   FROM agent_tools ORDER BY dist FETCH APPROX FIRST :k ROWS ONLY''', {"q": query, "k": k})

print("retrieve_tools (HNSW search over the toolbox) ready.")
```

_Generated from `total_recall_complete.ipynb` — the exact reference implementation._
