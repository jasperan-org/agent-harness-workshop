# 🧩 TODO 15 — Save a SHA-versioned skill

A **skill** is a `SKILL.md` playbook the agent can reuse — *procedural memory*. `save_skill` is the
write primitive: it stores the skill text, an **embedding** of it (so it is retrievable by meaning),
and a **SHA** of the body — the fingerprint that later lets `refresh_skills_from_source` notice when
an externally-sourced skill has changed. It is an UPSERT, so saving the same name twice updates it in
place rather than erroring.

### What to implement
Fill in `save_skill(name, description, skill_md, tools_used, source_workflow_id=None, source_url=None)`
(keep the table DDL and `create_hnsw_index` above it):
1. `sha = hashlib.sha256(skill_md.encode("utf-8")).hexdigest()`.
2. `MERGE INTO agent_skills … WHEN MATCHED THEN UPDATE SET description=:d, sha=:sha, source_url=:url,
   skill_md=:b, tools_used=:t, source_workflow_id=:w, updated_at=SYSTIMESTAMP, embedding =
   VECTOR_EMBEDDING({CFG['EMBED_MODEL']} USING :emb AS DATA) WHEN NOT MATCHED THEN INSERT (…) VALUES
   (…, VECTOR_EMBEDDING({CFG['EMBED_MODEL']} USING :emb AS DATA))`, binding `t=",".join(tools_used or
   [])` and `emb=f"{name}: {description}"`.
3. `return sha`.

> 💡 Embedding `f"{name}: {description}"` (not the whole body) keeps the skill's *index* about what it
> is *for* — so `retrieve_skills` matches on task intent, while the full `skill_md` is fetched only
> when the agent commits to using it.

## ✅ Solution

Replace the placeholder cell with this, then run the **`✅ TODO 15 check`** cell:

```python
create_table(conn, f'''CREATE TABLE agent_skills (
  name VARCHAR2(120) PRIMARY KEY, description VARCHAR2(600),
  sha VARCHAR2(64), source_url VARCHAR2(600),
  skill_md CLOB, tools_used VARCHAR2(600), source_workflow_id RAW(16),
  embedding VECTOR({CFG['VECTOR_DIM']}, FLOAT32),
  created_at TIMESTAMP DEFAULT SYSTIMESTAMP, updated_at TIMESTAMP DEFAULT SYSTIMESTAMP)''')
create_hnsw_index("agent_skills")

def save_skill(name, description, skill_md, tools_used, source_workflow_id=None, source_url=None):
    sha = hashlib.sha256(skill_md.encode("utf-8")).hexdigest()
    execute_sql(conn, f'''MERGE INTO agent_skills d USING (SELECT :n AS name FROM dual) s ON (d.name = s.name)
        WHEN MATCHED THEN UPDATE SET description=:d, sha=:sha, source_url=:url, skill_md=:b,
            tools_used=:t, source_workflow_id=:w, updated_at=SYSTIMESTAMP,
            embedding = VECTOR_EMBEDDING({CFG['EMBED_MODEL']} USING :emb AS DATA)
        WHEN NOT MATCHED THEN INSERT (name, description, sha, source_url, skill_md, tools_used,
            source_workflow_id, embedding)
            VALUES (:n,:d,:sha,:url,:b,:t,:w, VECTOR_EMBEDDING({CFG['EMBED_MODEL']} USING :emb AS DATA))''',
      {"n": name, "d": description, "sha": sha, "url": source_url, "b": skill_md,
       "t": ",".join(tools_used or []), "w": source_workflow_id, "emb": f"{name}: {description}"})
    return sha

print("Skillbox ready: agent_skills table + save_skill (SHA-versioned).")
```

_Generated from `total_recall_complete.ipynb` — the exact reference implementation._
