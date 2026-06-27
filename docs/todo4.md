# 🧩 TODO 4 — Grep the agent's scratch memory

A scratch filesystem is only useful if the agent can **search** it. `grep_files` is the agent-facing
tool that scans every scratch file line by line for a pattern — the same `grep` reflex you have at a
shell, but over memory that lives in the database. It builds directly on the `ScratchFS` you just
wrote (`fs.list` to enumerate, `fs.read` to open).

### What to implement
Fill in `grep_files(pattern, root="/", ignorecase=True)` (keep the other file tools):
1. `import re`; compile the pattern: `rx = re.compile(pattern, re.IGNORECASE if ignorecase else 0)`.
2. For each `p` in `fs.list(root)`, read it and walk the lines with `enumerate(fs.read(p).splitlines(),
   1)` (1-based). When `rx.search(line)` matches, append `{"path": p, "line": i, "text":
   line.strip()[:200]}`.
3. Wrap each file in `try/except` and `continue` past unreadable ones. Return the list of hits.

> 💡 Tools the agent calls are just Python functions returning plain data — here a list of
> match dicts. Searching memory is itself a tool: the agent greps its own notes the way you grep a
> codebase.

## ✅ Solution

Replace the placeholder cell with this, then run the **`✅ TODO 4 check`** cell:

```python
def write_file(path, content):
    """Agent tool: create or overwrite a scratch file (the agent's short-term memory)."""
    fs.write(path, content)
    return {"written": fs._abs(path), "bytes": len(content)}

def append_file(path, content):
    """Agent tool: append to a scratch file, creating it if needed."""
    fs.append(path, content)
    return {"appended": fs._abs(path)}

def read_file(path):
    return fs.read(path)

def tail_file(path, n=20):
    return "\n".join(fs.read(path).splitlines()[-n:])

def grep_files(pattern, root="/", ignorecase=True):
    import re
    rx = re.compile(pattern, re.IGNORECASE if ignorecase else 0)
    hits = []
    for p in fs.list(root):
        try:
            for i, line in enumerate(fs.read(p).splitlines(), 1):
                if rx.search(line):
                    hits.append({"path": p, "line": i, "text": line.strip()[:200]})
        except Exception:
            continue
    return hits

def list_files(root="/"):
    return fs.list(root)

print("File tools ready: write_file, append_file, read_file, tail_file, grep_files, list_files")
```

_Generated from `total_recall_complete.ipynb` — the exact reference implementation._
