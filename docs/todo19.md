# 🧩 TODO 19 — The agent loop

The capstone. An agent is not one model call — it is a **loop**, and `run_agent` is it. It ties
together everything you built: it **records** the user turn, **assembles** working memory (the OAMP
**context card**), runs the compiled LangGraph **state graph** (assemble context → call model → run
tools → persist), and then **closes the learning loop** by capturing whether the trajectory
succeeded as a reusable workflow — the very workflows the later promote/harvest TODOs turn into skills.

### What to implement
Fill in `run_agent(text, thread_id="main", stream=False)`:
1. **Record + perceive** — `mem.add_turn(thread_id, "user", text)`, then
   `card = mem.context_card(thread_id) or ""` (OAMP working memory, computed once per turn).
2. **Seed the state** — `state = {"messages": [HumanMessage(content=text)], "thread_id": thread_id,
   "iterations": 0, "started_at": _time.time(), "card": card}` and
   `cfg = {"configurable": {"thread_id": thread_id}, "recursion_limit": 50}`.
3. **Run the graph** — `out = graph.invoke(state, cfg)` (or iterate `graph.stream(state, cfg)` when
   `stream=True`).
4. **Close the loop** — pull the final answer
   (`next((m.content for m in reversed(out["messages"]) if isinstance(m, AIMessage) and m.content), "")`),
   collect the tools used from the messages' `tool_calls`, call
   `mem.capture_workflow(text, [...], tools_used, success=bool(final))`, and `return out`.

The full reference is below — read it, then build the loop yourself.

> 💡 This one function is the entire "agent framework." No black box: you own context assembly
> (*context engineering*), tool retrieval, the model call, durable graph state, and the learning
> feedback that makes the agent *get better* with use.

## ✅ Solution

Replace the placeholder cell with this, then run the **`✅ TODO 19 check`** cell:

```python
def run_agent(text, thread_id="main", stream=False):
    mem.add_turn(thread_id, "user", text)

    card = mem.context_card(thread_id) or ""        # OAMP working memory, computed once per user turn

    state = {"messages": [HumanMessage(content=text)], "thread_id": thread_id,
             "iterations": 0, "started_at": _time.time(), "card": card}

    cfg = {"configurable": {"thread_id": thread_id}, "recursion_limit": 50}

    if stream:
        last = None
        for ev in graph.stream(state, cfg):
            for node, payload in ev.items():
                print("  [node]", node); last = payload
        out = last
    else:
        out = graph.invoke(state, cfg)

    # Close the learning loop: record whether this trajectory produced an answer.
    final = next((m.content for m in reversed(out["messages"]) if isinstance(m, AIMessage) and m.content), "")
    tools_used = sorted({c["name"] for m in out["messages"] for c in (getattr(m, "tool_calls", None) or [])})
    # Capture the tools used in agent trajectory
    mem.capture_workflow(text, [{"tool": t} for t in tools_used], tools_used, success=bool(final))

    return out

print("Agent graph compiled. run_agent records trajectory outcomes.")
```

_Generated from `total_recall_complete.ipynb` — the exact reference implementation._
