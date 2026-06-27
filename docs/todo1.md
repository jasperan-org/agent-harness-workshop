# 🧩 TODO 1 — Talk to the reasoning core

The model is the agent's **reasoning core** — the one part that actually *reasons*. Everything else in this
workshop (memory, retrieval, tools, the loop) is **harness** built around it. Before adding any of that, it is
worth feeling the raw core directly: one prompt in, one answer out, no memory and no tools.

### What to implement
Set `QUESTION` to any non-empty string and run the cell — that's the whole task; the check just confirms you
asked *something*. Try a few:
- "Explain reciprocal rank fusion to a new engineer in three sentences."
- "What's the difference between short-term and long-term memory for an agent?"
- "Write a one-line Oracle SQL that counts the rows in a table called ORDERS."

> 💡 Notice what the bare model **can't** do: it has no memory of earlier turns and can't touch your data.
> That gap is exactly what the harness fills — and what the rest of this notebook builds.

## ✅ Solution

Replace the placeholder cell with this, then run the **`✅ TODO 1 check`** cell:

```python
from langchain_core.messages import HumanMessage

# ✏️ Your turn — replace QUESTION with anything, then run this cell to ask the reasoning core directly.
# (No memory, no tools, no database access yet — just the bare model.)
QUESTION = "In two sentences, what is an agent harness, and why is the model only one part of an agent?"

try:
    answer = llm.invoke([HumanMessage(content=QUESTION)]).content
    print("Q:", QUESTION, "\n")
    print("A:", answer)
except Exception as e:
    print("Model call failed:", str(e).splitlines()[0])
    print("Make sure OCI_GENAI_API_KEY is set (see 1.3 above).")
```

_Generated from `total_recall_complete.ipynb` — the exact reference implementation._
