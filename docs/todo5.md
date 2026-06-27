# 🧩 TODO 5 — In-database embeddings for the vector store

`OracleEmbeddings` can compute vectors in two very different places. With `provider="database"`, text is
embedded **inside Oracle** by the ONNX model you loaded in Part 1 (`VECTOR_EMBEDDING(...)`), so the data never
leaves the database and the query shares one vector space with the stored documents. The alternative is to
call an **external** embedding service over the network — another key, another vendor, your text leaving the box.

### What to implement
Set `params["provider"]` to **`"database"`**. The check confirms a probe text embeds to a 384-dim vector
entirely in Oracle.

> 💡 "Oracle everywhere" is the thesis of this workshop: embeddings, retrieval, memory, **and** the LLM all run
> against the database. Choosing the `database` provider is the first brick.

## ✅ Solution

Replace the placeholder cell with this, then run the **`✅ TODO 5 check`** cell:

```python
from langchain_oracledb.embeddings import OracleEmbeddings

# Embeddings computed IN the database by the loaded ONNX model (provider="database").
db_embeddings = OracleEmbeddings(
    conn=conn,
    params={"provider": "database", "model": CFG["EMBED_MODEL"]})
print("Embedder ready (in-database) | dim:", len(db_embeddings.embed_query("probe")))
```

_Generated from `total_recall_complete.ipynb` — the exact reference implementation._
