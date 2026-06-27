# 🧩 TODO 12 — Promote scratch files into long-term memory

Scratch notes are short-term. **Continual learning** starts when the agent *promotes* them into
long-term memory: a scheduled in-database **producer** (`stage_scratch_for_promotion`, written for
you) chunks pending files into a `promotion_queue`; your job is the **consumer** that drains that
queue into OAMP. This is the bridge from a working file on the scratchpad to a durable, recallable
memory the agent can use in any future session.

### What to implement
Fill in `drain_promotion_queue_to_oamp(limit=500)` (keep `promote_file_to_memory`, which stages then
calls you):
1. Read unconsumed rows: `fetch_rows(conn, "SELECT id, path, chunk FROM promotion_queue WHERE
   consumed='N' FETCH FIRST :k ROWS ONLY", {"k": limit})`.
2. For each row, write it to long-term memory and mark it done: `mem.remember(r["CHUNK"])` (OAMP
   `add_memory`, with fact-extraction), then `execute_sql(conn, "UPDATE promotion_queue SET
   consumed='Y' WHERE id=:i", {"i": r["ID"]})`.
3. Mark each distinct source file promoted: for `p` in `{r["PATH"] for r in rows}`,
   `UPDATE agent_scratch SET promoted='Y' WHERE path=:p`. Return `len(rows)`.

> 💡 Producer/consumer split: the producer runs on a `DBMS_SCHEDULER` job (hourly), the consumer is
> this function. Decoupling them is what lets promotion happen continuously in the background — the
> agent keeps learning from its own scratch work without you orchestrating it.

## ✅ Solution

Replace the placeholder cell with this, then run the **`✅ TODO 12 check`** cell:

```python
def drain_promotion_queue_to_oamp(limit=500):
    rows = fetch_rows(conn, "SELECT id, path, chunk FROM promotion_queue WHERE consumed='N' FETCH FIRST :k ROWS ONLY",
                      {"k": limit})
    for r in rows:
        mem.remember(r["CHUNK"])                       # OAMP add_memory (extraction applies)
        execute_sql(conn, "UPDATE promotion_queue SET consumed='Y' WHERE id=:i", {"i": r["ID"]})
    for p in {r["PATH"] for r in rows}:
        execute_sql(conn, "UPDATE agent_scratch SET promoted='Y' WHERE path=:p", {"p": p})
    return len(rows)

def promote_file_to_memory(path):
    execute_sql(conn, "BEGIN stage_scratch_for_promotion; END;")   # stage everything pending (incl. this file)
    n = drain_promotion_queue_to_oamp()
    return {"promoted_chunks": n, "path": path}

print("Consumer ready: drain_promotion_queue_to_oamp + promote_file_to_memory.")
```

_Generated from `total_recall_complete.ipynb` — the exact reference implementation._
