# 🧩 TODO 16 — Skills as searchable memory

**Skills** are read in two levels: a cheap **manifest** (name + description for the few relevant
skills) that always rides in context, and the **full body**, loaded on demand only when the agent
commits to using one. Same HNSW-over-a-registry pattern as the toolbox — and the same `save_skill`
write side you just built feeds it.

### What to implement
Fill in two functions (keep `build_skill_manifest` between them):
- `retrieve_skills(query, k=5)` — level 1, like `retrieve_tools` but over `agent_skills`: select
  `name, description, VECTOR_DISTANCE(embedding, VECTOR_EMBEDDING({CFG['EMBED_MODEL']} USING :q AS DATA), COSINE) dist`,
  `ORDER BY dist FETCH APPROX FIRST :k ROWS ONLY`; return `fetch_rows(conn, sql, {"q": query, "k": k})`.
- `load_skill(name)` — level 2: `fetch_rows(conn, "SELECT name, description, skill_md, tools_used, sha,
  source_url FROM agent_skills WHERE name=:n", {"n": name})`; return `r[0]` if found, else
  `{"error": "no such skill"}`.

> 💡 Two levels = context economy. The manifest is small enough to always carry; the full playbook
> (which can be long) is fetched only when needed. The agent reads *that it has* a skill before it
> pays to read the skill.

## ✅ Solution

Replace the placeholder cell with this, then run the **`✅ TODO 16 check`** cell:

```python
def retrieve_skills(query, k=5):                   # level 1: HNSW over the skillbox
    return fetch_rows(conn, f'''SELECT name, description,
                   VECTOR_DISTANCE(embedding, VECTOR_EMBEDDING({CFG['EMBED_MODEL']} USING :q AS DATA), COSINE) dist
                   FROM agent_skills ORDER BY dist FETCH APPROX FIRST :k ROWS ONLY''', {"q": query, "k": k})

def build_skill_manifest(query, k=5):
    rows = retrieve_skills(query, k=k)
    return "\n".join(f"- {r['NAME']}: {r['DESCRIPTION']}" for r in rows) or "(no skills yet)"

def load_skill(name):                              # level 2: the full SKILL.md body, on demand
    r = fetch_rows(conn, "SELECT name, description, skill_md, tools_used, sha, source_url FROM agent_skills WHERE name=:n",
                   {"n": name})
    return r[0] if r else {"error": "no such skill"}

print("Skill retrieval ready: manifest (L1) + load_skill (L2).")
```

_Generated from `total_recall_complete.ipynb` — the exact reference implementation._
