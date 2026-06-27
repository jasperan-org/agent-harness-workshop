# 🧩 TODO 6 — Choose the vector distance strategy

A vector store ranks neighbours by a **distance strategy** — the maths that decides how "close" two embeddings
are, which is to say *what "similar" means*.

### How vector similarity is computed
Each text becomes a point in 384-dimensional space. The common strategies:
- **COSINE** — the **angle** between two vectors, ignoring length. Two texts on the same topic point the same
  *direction* even if one is longer, so cosine is the standard for **normalized text embeddings** (what
  `ALL_MINILM_L12_V2` produces). Distance = `1 − cos(θ)`; 0 means identical direction.
- **EUCLIDEAN_DISTANCE** — straight-line distance between the points; sensitive to magnitude, so it can rank by
  length as much as by meaning unless the vectors are normalized.
- **DOT_PRODUCT / MAX_INNER_PRODUCT** — angle *and* magnitude together; fast, and equal to cosine **only** when
  the vectors are unit-length.
- **JACCARD** — set overlap, for binary/sparse vectors — not dense text embeddings.

### What to implement
Pass **`DistanceStrategy.COSINE`** as `distance_strategy`. The check confirms `store.distance_strategy` is
`COSINE`.

> 💡 Rule of thumb: **normalized text embeddings → cosine.** The other strategies exist for embeddings whose
> magnitude carries meaning (recommenders, binary fingerprints), which isn't our case here.

## ✅ Solution

Replace the placeholder cell with this, then run the **`✅ TODO 6 check`** cell:

```python
from langchain_oracledb.vectorstores import OracleVS, DistanceStrategy

VSTORE_TABLE = "AGENT_VSTORE"
store = OracleVS(
    client=conn,
    embedding_function=db_embeddings,
    table_name=VSTORE_TABLE,
    distance_strategy=DistanceStrategy.COSINE)
print("OracleVS ready over", VSTORE_TABLE, "| distance:", store.distance_strategy)
```

_Generated from `total_recall_complete.ipynb` — the exact reference implementation._
