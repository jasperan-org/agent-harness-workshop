# 🧩 TODO 2 — Design the scratch table (SecureFile LOB)

The agent's scratch filesystem (next section) needs a table to live in, and every file is **one row**: a
`path` primary key and the file's bytes in a `content` **BLOB**, stored as a **SecureFile LOB** (Oracle's
modern LOB storage — fast, compressible, fully transactional). Two flags ride along — `is_dir` (a directory
marker) and `promoted` (set once a note graduates to long-term memory in Part 4) — plus an `updated_at` stamp.

### What to implement
Complete `SCRATCH_DDL` so `agent_scratch` has, besides `path`:
- `content BLOB` — the file body.
- `is_dir CHAR(1) DEFAULT 'N'` and `promoted CHAR(1) DEFAULT 'N'` — single-char flags.
- `updated_at TIMESTAMP DEFAULT SYSTIMESTAMP`.
- a `LOB (content) STORE AS SECUREFILE` clause after the column list.

> 💡 Putting files in a table (not on disk) is the whole point: they become **ACID, backed up, access-
> controlled, and searchable** — and a row can later be *promoted* straight into long-term memory.

## ✅ Solution

Replace the placeholder cell with this, then run the **`✅ TODO 2 check`** cell:

```python
SCRATCH_DDL = '''CREATE TABLE agent_scratch (
  path        VARCHAR2(400) PRIMARY KEY,
  content     BLOB,
  is_dir      CHAR(1) DEFAULT 'N',
  promoted    CHAR(1) DEFAULT 'N',            -- set once promoted to long-term memory (Part 4)
  updated_at  TIMESTAMP DEFAULT SYSTIMESTAMP
) LOB (content) STORE AS SECUREFILE'''
create_table(conn, SCRATCH_DDL)
print("agent_scratch table ready (SecureFile LOB content; one row per file).")
```

_Generated from `total_recall_complete.ipynb` — the exact reference implementation._
