# 🧩 TODO 11 — Embed text inside the database

OAMP (the cognitive-memory layer you are about to build on) needs an **embedder**. Instead of calling
an external API or loading PyTorch, the embedding is computed **inside Oracle** by the ONNX model you
loaded in Part 1 — from Python it is one SQL call. We wrap it as an OAMP `IEmbedder` so the whole
memory system runs against the in-database model.

### What to implement
Fill in `InDBOnnxEmbedder.embed(self, texts, *, is_query=False)` (keep `__init__` and `embed_async`):
1. Build a list `out = []`.
2. For each `t` in `texts`, run one query and collect the vector:
   `fetch_rows(self.conn, f"SELECT VECTOR_EMBEDDING({self.model} USING :t AS DATA) v FROM dual", {"t": t})`
   then append `list(r[0]["V"])`.
3. Return `np.array(out, dtype=np.float32)` — a `(len(texts), 384)` matrix.

> 💡 The *same* model embeds both documents and queries — that is what makes their vectors
> comparable. Mixing models is the classic vector-search bug. (`embed_async` just calls `embed`,
> so once this works the async path works too.)

## ✅ Solution

Replace the placeholder cell with this, then run the **`✅ TODO 11 check`** cell:

```python
import numpy as np
from oracleagentmemory.core import OracleAgentMemory
from oracleagentmemory.core.llms import Llm
from oracleagentmemory.apis.embedders.embedder import IEmbedder

class InDBOnnxEmbedder(IEmbedder):
    """An OAMP embedder that computes vectors with the in-database ONNX model (no external service)."""
    def __init__(self, conn, model):
        self.conn = conn; self.model = model
    def embed(self, texts, *, is_query=False):
        out = []
        for t in texts:  # one round-trip per text; batch this at scale
            r = fetch_rows(self.conn, f"SELECT VECTOR_EMBEDDING({self.model} USING :t AS DATA) v FROM dual", {"t": t})
            out.append(list(r[0]["V"]))
        return np.array(out, dtype=np.float32)
    async def embed_async(self, texts, *, is_query=False):
        return self.embed(texts, is_query=is_query)

print("InDBOnnxEmbedder ready.")
```

_Generated from `total_recall_complete.ipynb` — the exact reference implementation._
