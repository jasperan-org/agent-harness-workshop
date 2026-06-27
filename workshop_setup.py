"""Workshop plumbing — kept out of the notebook so you focus on the harness, not the boilerplate.

Your Codespace already provisioned everything this connects to: `scripts/seed_oracle.py` created the
least-privilege ``AGENT`` user with the grants the later layers need and loaded the in-database
embedder, and ``.devcontainer/`` started Oracle and set your credentials + model config as environment
variables. Importing this module reads that environment, **connects you as the AGENT user**, and hands
back the config plus the few SQL helpers the rest of the notebook builds on:

    from workshop_setup import CFG, conn, fetch_rows, execute_sql, ddl_idempotent, create_table

You never run ``docker``, type a password, create a user, or load a model — that all happened when the
Codespace was set up. (Running locally? Run ``python scripts/seed_oracle.py`` once first — see the README.)
"""
from __future__ import annotations

import json
import os
import re
import time

import oracledb

# Return CLOB as str and BLOB as bytes directly (simpler, and avoids cursor-lifetime LOB issues).
oracledb.defaults.fetch_lobs = False

CFG = {
    "DSN": os.environ.get("ORA_DSN", "localhost:1521/FREEPDB1"),
    "AGENT_USER": os.environ.get("ORA_AGENT_USER", "AGENT"),
    # Models loaded INTO the database by the Codespace (scripts/seed_oracle.py).
    "EMBED_MODEL": os.environ.get("EMBED_MODEL", "ALL_MINILM_L12_V2"),  # in-DB ONNX embedder, 384-dim
    "RERANK_MODEL": os.environ.get("RERANK_MODEL", "RERANK_XENC"),  # in-DB cross-encoder (optional)
    "VECTOR_DIM": int(os.environ.get("VECTOR_DIM", "384")),
    # Chat model: OCI Generative AI via its OpenAI-compatible endpoint, so the WHOLE stack —
    # embeddings, retrieval, memory, AND the LLM — runs on Oracle. LLM_PROVIDER=openai uses OpenAI direct.
    "LLM_PROVIDER": os.environ.get("LLM_PROVIDER", "oci"),  # "oci" | "openai"
    "LLM_MODEL": os.environ.get("LLM_MODEL", "xai.grok-4-1-fast-reasoning"),
    "OCI_GENAI_ENDPOINT": os.environ.get(
        "OCI_GENAI_ENDPOINT", "https://inference.generativeai.us-phoenix-1.oci.oraclecloud.com"
    ),
    "OCI_GENAI_API_KEY": os.environ.get("OCI_GENAI_API_KEY", ""),
    # Cognitive memory (OAMP).
    "OAMP_PREFIX": os.environ.get("OAMP_PREFIX", "OAMP_"),
    "OAMP_EXTRACT": os.environ.get("OAMP_EXTRACT", "1") == "1",
    "DBFS_MOUNT": os.environ.get("DBFS_MOUNT", "/scratch"),
    # Off by default: the notebook and the appbook share one AGENT schema, so a re-run never wipes the
    # live app's tables. Set RESET_ON_RUN=1 (against a private database) to rebuild from a clean slate.
    "RESET_ON_RUN": os.environ.get("RESET_ON_RUN", "0") == "1",
}

# --- OCI key rotation: random start + failover across up to 4 keys -----------------------------
# For large cohorts (~180 attendees), on-demand OCI inference can 429 at peak. We load every
# OCI_GENAI_API_KEY[_2/_3/_4] present, give each kernel a RANDOM starting key, and fail over to the
# next key on a rate-limit / auth / transient error. With a single key set, this is a no-op wrapper.
from oci_key_rotation import KeyRotator, call_with_failover, load_oci_keys  # noqa: E402

_OCI_KEYS = load_oci_keys()
OCI_ROTATOR = KeyRotator(_OCI_KEYS) if _OCI_KEYS else None
# Keep CFG["OCI_GENAI_API_KEY"] populated (back-compat for any code that reads it directly).
if OCI_ROTATOR is not None:
    CFG["OCI_GENAI_API_KEY"] = OCI_ROTATOR.current()
CFG["OCI_KEY_COUNT"] = len(_OCI_KEYS)


def make_rotating_chat_model(**chat_kwargs):
    """A LangChain chat Runnable (ChatOpenAI under the hood) that fails over across the OCI keys.

    Drop-in for the notebook's make_chat_model "oci" branch. invoke() and bind_tools(...).invoke()
    both route through the failover wrapper. Honours base_url/model from CFG.
    """
    from langchain_openai import ChatOpenAI
    if OCI_ROTATOR is None:
        raise RuntimeError("OCI_GENAI_API_KEY is not set (no keys to rotate).")
    base_url = CFG["OCI_GENAI_ENDPOINT"]
    model = chat_kwargs.pop("model", CFG["LLM_MODEL"])

    def _client(key):
        return ChatOpenAI(model=model, base_url=base_url, api_key=key, **chat_kwargs)

    class _RotatingChat:
        def __init__(self, tools=None):
            self._tools = tools

        def _make(self, key):
            c = _client(key)
            return c.bind_tools(self._tools) if self._tools else c

        def invoke(self, *a, **k):
            return call_with_failover(self._make, lambda c: c.invoke(*a, **k),
                                      OCI_ROTATOR, on_event=lambda m: print(" ", m))

        def bind_tools(self, tools, **k):
            return _RotatingChat(tools=tools)

        def __getattr__(self, name):
            return getattr(_client(OCI_ROTATOR.current()), name)

    return _RotatingChat()


def make_rotating_oamp_llm():
    """An OAMP Llm-compatible object that fails over across the OCI keys (for fact extraction)."""
    from oracleagentmemory.core.llms import Llm
    if OCI_ROTATOR is None:
        raise RuntimeError("OCI_GENAI_API_KEY is not set (no keys to rotate).")
    base_url = CFG["OCI_GENAI_ENDPOINT"]
    model = f"openai/{CFG['LLM_MODEL']}"

    def _llm(key):
        return Llm(model, api_base=base_url, api_key=key)

    class _RotatingOAMPLlm:
        def generate(self, *a, **k):
            return call_with_failover(_llm, lambda l: l.generate(*a, **k),
                                      OCI_ROTATOR, on_event=lambda m: print(" ", m))

        async def generate_async(self, *a, **k):
            import asyncio  # noqa: F401
            n = len(OCI_ROTATOR)
            last = None
            for attempt in range(n * 2):
                try:
                    return await _llm(OCI_ROTATOR.current()).generate_async(*a, **k)
                except BaseException as e:  # noqa: BLE001
                    last = e
                    from oci_key_rotation import is_rate_limit_error
                    if not is_rate_limit_error(e) or attempt == n * 2 - 1:
                        raise
                    OCI_ROTATOR.advance()
            raise last

        def __getattr__(self, name):
            return getattr(_llm(OCI_ROTATOR.current()), name)

    return _RotatingOAMPLlm()


AGENT = CFG["AGENT_USER"]
AGENT_PWD = os.environ.get("ORA_AGENT_PWD", "AgentPw_2026")


# --- a resilient connection helper (containers take a moment to accept connections) ---
def connect_with_retry(user, password, dsn, mode=None, attempts=10, base_delay=2.0):
    last = None
    for i in range(attempts):
        try:
            kw = dict(user=user, password=password, dsn=dsn)
            if mode is not None:
                kw["mode"] = mode
            return oracledb.connect(**kw)
        except Exception as e:
            last = e
            wait = min(base_delay * (2**i), 15.0)
            print(f"  connect attempt {i + 1}/{attempts} failed ({e.__class__.__name__}); retrying in {wait:.0f}s")
            time.sleep(wait)
    raise last


# --- three small SQL helpers, used everywhere in the notebook ---
def fetch_rows(conn, sql, params=None):
    """Run a query; return a list of {COLUMN_NAME: value} dict rows."""
    cur = conn.cursor()
    try:
        cur.execute(sql, params or {})
        if cur.description is None:
            return []
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]
    finally:
        cur.close()


def execute_sql(conn, sql, params=None, many=False, commit=True):
    """Run DML/DDL and commit. many=True batches an executemany insert."""
    cur = conn.cursor()
    try:
        if many:
            cur.executemany(sql, params or [])
        else:
            cur.execute(sql, params or {})
        if commit:
            conn.commit()
    finally:
        cur.close()


def ddl_idempotent(conn, sql, ignore_codes=("ORA-00955", "ORA-01920", "ORA-00942",
                                            "ORA-01430", "ORA-02260", "ORA-01408",
                                            "ORA-00001", "ORA-29879", "ORA-29833",
                                            "ORA-12003", "ORA-00904", "ORA-02264")):
    """Run CREATE/DROP DDL, swallowing the 'already exists' / 'does not exist' family of errors."""
    try:
        execute_sql(conn, sql)
        return True
    except Exception as e:
        if any(code in str(e) for code in ignore_codes):
            return False
        raise


def _parse_columns(ddl):
    """Yield (col_name, add_safe_def) for each top-level column in a CREATE TABLE statement.
    Skips table-level constraints and strips inline PK / UNIQUE / NOT NULL / REFERENCES, so each
    definition is safe to use in ALTER TABLE ADD against a table that already holds rows."""
    ddl = re.sub(r'--[^\n]*', '', ddl)                         # drop -- line comments
    start = ddl.index('(', re.search(r'CREATE\s+TABLE', ddl, re.I).end())
    depth = 0
    for i in range(start, len(ddl)):                           # walk to the matching ')'
        if ddl[i] == '(': depth += 1
        elif ddl[i] == ')':
            depth -= 1
            if depth == 0: break
    parts, buf, d, q = [], [], 0, False                        # split on top-level commas only
    for ch in ddl[start + 1:i]:
        if ch == "'": q = not q
        if not q:
            if ch == '(': d += 1
            elif ch == ')': d -= 1
            elif ch == ',' and d == 0:
                parts.append(''.join(buf)); buf = []; continue
        buf.append(ch)
    if ''.join(buf).strip(): parts.append(''.join(buf))
    for p in parts:
        toks = p.split()
        if not toks or toks[0].upper() in ('PRIMARY', 'FOREIGN', 'CONSTRAINT', 'UNIQUE', 'CHECK'):
            continue                                           # table-level constraint, not a column
        defn = p.strip()
        defn = re.sub(r'\s+PRIMARY\s+KEY', '', defn, flags=re.I)
        defn = re.sub(r'\s+UNIQUE', '', defn, flags=re.I)
        defn = re.sub(r'\s+NOT\s+NULL', '', defn, flags=re.I)
        defn = re.sub(r'\s+REFERENCES\s+[A-Za-z0-9_$]+(\s*\([^)]*\))?', '', defn, flags=re.I)
        yield toks[0].strip('"'), defn.strip()


def create_table(conn, ddl):
    """CREATE TABLE that self-heals schema drift: builds the table when absent, and when it already
    exists ADDs any columns the DDL declares that the live table is missing (non-destructive)."""
    table = re.search(r'CREATE\s+TABLE\s+"?([A-Za-z0-9_$]+)"?', ddl, re.I).group(1).upper()
    existed = bool(fetch_rows(conn, "SELECT 1 FROM user_tables WHERE table_name=:t", {"t": table}))
    ddl_idempotent(conn, ddl)
    if existed:
        live = {c["COLUMN_NAME"] for c in fetch_rows(conn,
            "SELECT column_name FROM user_tab_columns WHERE table_name=:t", {"t": table})}
        for name, coldef in _parse_columns(ddl):
            if name.upper() not in live:
                execute_sql(conn, f"ALTER TABLE {table} ADD ({coldef})")
                print(f"  + reconciled {table}.{name} (schema drift healed)")
    return table


def reset_agent_schema(conn):
    """Drop everything this notebook creates, preserving the loaded ONNX models (DM$* tables)."""
    def run(sql):
        try:
            execute_sql(conn, sql)
        except Exception:
            pass

    def names(sql):
        return [list(r.values())[0] for r in fetch_rows(conn, sql)]
    for j in names("SELECT job_name FROM user_scheduler_jobs"):
        run(f"BEGIN DBMS_SCHEDULER.DROP_JOB('{j}', force=>TRUE); END;")
    for mv in names("SELECT mview_name FROM user_mviews"):
        run(f"DROP MATERIALIZED VIEW {mv}")
    for v in names("SELECT view_name FROM user_views"):
        run(f"DROP VIEW {v}")
    for p in names("SELECT object_name FROM user_objects WHERE object_type='PROCEDURE'"):
        run(f"DROP PROCEDURE {p}")
    for t in names("SELECT table_name FROM user_tables WHERE table_name NOT LIKE 'DM$%'"):
        run(f'DROP TABLE "{t}" CASCADE CONSTRAINTS PURGE')
    try:
        for d in names("SELECT name FROM user_domains"):
            run(f"DROP DOMAIN {d}")
    except Exception:
        pass


def _model_loaded(conn, name):
    return bool(fetch_rows(conn, "SELECT 1 FROM user_mining_models WHERE model_name=:m", {"m": name.upper()}))


# --- connect once, on import: this is the "ready to go" the notebook depends on ---
conn = connect_with_retry(AGENT, AGENT_PWD, CFG["DSN"])
if CFG["RESET_ON_RUN"]:
    reset_agent_schema(conn)

# The Codespace loads only the embedder by default; the rerank rung falls back to hybrid order unless
# the optional reranker is also loaded. This records which case you're in (used by Part 3's TODO).
RERANK_AVAILABLE = _model_loaded(conn, CFG["RERANK_MODEL"])

if not _model_loaded(conn, CFG["EMBED_MODEL"]):
    print(f"⚠ The embedder '{CFG['EMBED_MODEL']}' is not loaded in {AGENT}. In a Codespace this is "
          f"automatic; locally, run `python scripts/seed_oracle.py` once. (See the README.)")

__all__ = ["CFG", "conn", "AGENT", "AGENT_PWD", "connect_with_retry", "fetch_rows", "execute_sql",
           "ddl_idempotent", "create_table", "reset_agent_schema", "RERANK_AVAILABLE",
           "OCI_ROTATOR", "make_rotating_chat_model", "make_rotating_oamp_llm"]
