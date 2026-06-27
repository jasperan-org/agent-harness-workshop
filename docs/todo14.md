# 🧩 TODO 14 — A safe, read-only SQL tool

A **tool** is how the agent acts on the world: a plain Python function the model can call. `run_sql`
lets the agent *explore* the warehouse and *validate* a query before turning it into a materialized
view — but it must be **read-only**, so a guard rejects anything that is not a single, safe `SELECT`.
State only ever changes through the deliberate, audited `author_materialized_view` path.

### What to implement
Fill in `run_sql(sql, max_rows=200)` (keep `list_sources`, the `_FORBIDDEN` regex, and
`author_materialized_view`):
1. **One statement only** — reject if there is a `;` inside the trimmed body:
   `if ";" in sql.strip().rstrip(";"): return {"error": "one statement only"}`.
2. **SELECT / WITH only** — `if not sql.strip().upper().startswith(("SELECT", "WITH")): return {"error": "SELECT/WITH only"}`.
3. **No write/DDL keyword** — `if _FORBIDDEN.search(sql): return {"error": "write/DDL keyword rejected ..."}`.
4. **Run it** and cap the rows: `try: return {"rows": fetch_rows(conn, sql)[:max_rows]}` /
   `except Exception as e: return {"error": str(e).splitlines()[0]}`.

> 💡 Tools return plain data (here a dict) — that is what gets fed back to the model as the tool
> result. The read-only guard is a guardrail you hand the agent; the database's own privileges are
> the real boundary behind it.

## ✅ Solution

Replace the placeholder cell with this, then run the **`✅ TODO 14 check`** cell:

```python
import re as _re

def list_sources():
    rows = fetch_rows(conn, "SELECT table_name FROM user_tables WHERE table_name IN "
                            "('CUSTOMERS','PRODUCTS','ORDERS','ORDER_ITEMS') ORDER BY table_name")
    return [r["TABLE_NAME"] for r in rows] + ["V_REVENUE (view)"]

_FORBIDDEN = _re.compile(r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|MERGE|GRANT|CREATE)\b", _re.I)
def run_sql(sql, max_rows=200):
    if ";" in sql.strip().rstrip(";"):
        return {"error": "one statement only"}
    if not sql.strip().upper().startswith(("SELECT", "WITH")):
        return {"error": "SELECT/WITH only"}
    if _FORBIDDEN.search(sql):
        return {"error": "write/DDL keyword rejected (app-level filter; DB enforces the real boundary)"}
    try:
        return {"rows": fetch_rows(conn, sql)[:max_rows]}
    except Exception as e:
        return {"error": str(e).splitlines()[0]}

def author_materialized_view(name, select_sql):
    chk = run_sql(select_sql, max_rows=1)
    if "error" in chk:
        return {"error": "select failed: " + chk["error"]}
    ddl_idempotent(conn, f"DROP MATERIALIZED VIEW {name}")
    ddl_idempotent(conn, f"CREATE MATERIALIZED VIEW {name} BUILD IMMEDIATE REFRESH COMPLETE ON DEMAND AS {select_sql}")
    return {"created": name}

print("Domain tools ready: list_sources, run_sql (read-only), author_materialized_view.")
```

_Generated from `total_recall_complete.ipynb` — the exact reference implementation._
