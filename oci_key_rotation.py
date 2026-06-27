"""OCI Generative AI API-key rotation: random start + failover across up to N keys.

Why
---
A workshop with ~180 attendees sharing OCI GenAI keys can hit rate limits (HTTP
429) at peak. This module spreads the load and self-heals:

  * Each PROCESS (an attendee's notebook kernel, or an app worker) picks a RANDOM
    starting key, so the cohort fans out across the keys instead of all hitting
    key #1.
  * On a rate-limit / auth / transient error, the active key ADVANCES to the next
    one (wrapping) and the call is retried. Once a working key is found it sticks.

Keys come from the environment, so they inject automatically in Codespaces:

    OCI_GENAI_API_KEY      (key 1 — also the single-key env var name)
    OCI_GENAI_API_KEY_2
    OCI_GENAI_API_KEY_3
    OCI_GENAI_API_KEY_4    (any number of slots supported)

Other env: OCI_GENAI_ENDPOINT (host, no /v1 needed), LLM_MODEL (the OCI model id).

This is shared by the notebook (via workshop_setup.py) and the appbook
(app/backend/core/llm_client.py) so both fail over across the same key set.
"""

from __future__ import annotations

import os
import random
import time
from typing import Any, Callable


def load_oci_keys() -> list[str]:
    """Collect OCI GenAI keys from env, in order, de-duplicated, placeholders skipped."""
    found: list[str] = []
    for name in ("OCI_GENAI_API_KEY", "OCI_GENAI_API_KEY_1"):
        v = (os.environ.get(name) or "").strip()
        if v and "REPLACE_ME" not in v and "NOT_SET" not in v:
            found.append(v)
            break
    i = 2
    while i <= 8:
        v = (os.environ.get(f"OCI_GENAI_API_KEY_{i}") or "").strip()
        if v and "REPLACE_ME" not in v and "NOT_SET" not in v:
            found.append(v)
        i += 1
    seen, keys = set(), []
    for k in found:
        if k not in seen:
            seen.add(k)
            keys.append(k)
    return keys


def is_rate_limit_error(exc: BaseException) -> bool:
    """True for failures worth failing OVER on: 429s, quota/throttle, transient auth/conn."""
    status = getattr(exc, "status_code", None) or getattr(exc, "code", None)
    if status in (429, 401, 403, 500, 502, 503, 504, "429"):
        return True
    m = str(exc).lower()
    needles = ("429", "rate limit", "too many requests", "quota", "throttl",
               "temporarily", "overloaded", "service unavailable",
               "unauthorized", "forbidden", "connection", "timeout")
    return any(n in m for n in needles)


class KeyRotator:
    """Random starting key + sticky failover. One per process."""

    def __init__(self, keys: list[str], seed: Any | None = None):
        if not keys:
            raise RuntimeError(
                "No OCI GenAI API keys found. Set OCI_GENAI_API_KEY (and optionally "
                "OCI_GENAI_API_KEY_2..4) as Codespaces secrets or env vars."
            )
        self.keys = keys
        self._idx = random.Random(seed).randrange(len(keys))  # RANDOM start

    def current(self) -> str:
        return self.keys[self._idx]

    def current_index(self) -> int:
        return self._idx

    def advance(self) -> str:
        self._idx = (self._idx + 1) % len(self.keys)
        return self.keys[self._idx]

    def __len__(self) -> int:
        return len(self.keys)


def call_with_failover(
    make_client: Callable[[str], Any],
    do_call: Callable[[Any], Any],
    rotator: KeyRotator,
    *,
    base_delay: float = 0.8,
    on_event: Callable[[str], None] | None = None,
) -> Any:
    """Run do_call(make_client(active_key)); on a rate-limit/transient error, back off,
    advance to the next key, rebuild the client, and retry (≈ one sweep of all keys)."""
    n = len(rotator)
    last = None
    for attempt in range(n * 2):
        try:
            return do_call(make_client(rotator.current()))
        except BaseException as e:  # noqa: BLE001 — re-raised below
            last = e
            if not is_rate_limit_error(e) or attempt == n * 2 - 1:
                raise
            rotator.advance()
            if on_event:
                on_event(f"[key-rotation] switching to key #{rotator.current_index() + 1} "
                         f"of {n} after {type(e).__name__}")
            time.sleep(base_delay * (2 ** min(attempt, 4)))
    raise last  # pragma: no cover


async def call_with_failover_async(
    make_client: Callable[[str], Any],
    do_call: Callable[[Any], Any],
    rotator: KeyRotator,
    *,
    base_delay: float = 0.8,
    on_event: Callable[[str], None] | None = None,
) -> Any:
    """Async variant of call_with_failover (do_call returns an awaitable)."""
    import asyncio
    n = len(rotator)
    last = None
    for attempt in range(n * 2):
        try:
            return await do_call(make_client(rotator.current()))
        except BaseException as e:  # noqa: BLE001
            last = e
            if not is_rate_limit_error(e) or attempt == n * 2 - 1:
                raise
            rotator.advance()
            if on_event:
                on_event(f"[key-rotation] switching to key #{rotator.current_index() + 1} "
                         f"of {n} after {type(e).__name__}")
            await asyncio.sleep(base_delay * (2 ** min(attempt, 4)))
    raise last  # pragma: no cover
