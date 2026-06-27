# 🧩 TODO 7 — Chunk text into overlapping windows

You cannot embed a 50-page document as one vector — meaning would smear into mush, and retrieval would hand
back the whole document instead of the relevant passage. So you **chunk**: split into windows small enough to
carry one idea. Good chunking is what makes retrieval **precise** (you get the paragraph, not the book), keeps
each embedding **high-signal**, and respects the model's **context budget** on the way back in.

### Chunking techniques (a quick map)
- **Fixed-size by words/tokens, with overlap** — what we build here. Simple, predictable, model-agnostic; the
  overlap stops an idea that straddles a boundary from being lost. The honest default.
- **Sentence / paragraph** — split on natural boundaries so a chunk is a whole thought. Better coherence,
  variable size.
- **Recursive** — try paragraphs, then sentences, then words, splitting further only when a piece is too big.
  The common production default (e.g. LangChain's `RecursiveCharacterTextSplitter`).
- **Semantic** — start a new chunk where the embedding *meaning* shifts. Highest quality, highest cost.
- **Structure-aware** — split on Markdown headings, code fences, or table rows when the document has structure.

We use fixed-size word windows with overlap because it is the clearest teaching artifact and needs no extra
dependencies — the *technique* matters more than the splitter.

### What to implement
Fill in `chunk_words(text, size=200, overlap=20)`:
1. `words = text.split()`. If `len(words) <= size`, return `[text]` (nothing to split).
2. Otherwise walk a sliding window: starting at `i = 0`, append `" ".join(words[i:i + size])`, then
   step `i += size - overlap`, until `i >= len(words)`. Return the list.

> 💡 The step is `size - overlap`, **not** `size` — that is what makes consecutive windows share
> their last/first `overlap` words. Set `overlap = 0` and you get hard cuts; a small overlap keeps
> ideas that cross a boundary retrievable from either chunk.

## ✅ Solution

Replace the placeholder cell with this, then run the **`✅ TODO 7 check`** cell:

```python
def chunk_words(text, size=200, overlap=20):
    """Split text into overlapping word windows (one idea per chunk)."""
    words = text.split()
    if len(words) <= size:
        return [text]
    out, i = [], 0
    while i < len(words):
        out.append(" ".join(words[i:i + size]))
        i += size - overlap
    return out
```

_Generated from `total_recall_complete.ipynb` — the exact reference implementation._
