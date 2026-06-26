"""W3C Trace Context propagation for A2A calls.

Implements distributed tracing across the host -> weather agent handoff so
the Gemini Enterprise topology map and Cloud Trace render the cross-agent
hop as a single connected trace instead of two disjoint ones.

How it works (belt-and-suspenders):

1. **W3C traceparent header (forward-compatible).**
   `RequestsInstrumentor` auto-injects this on outbound HTTP, and we call
   `inject_w3c_context_into_headers(...)` explicitly so the
   `traceparent` / `tracestate` headers ride on every A2A call regardless
   of whether the instrumentor is active. Once Vertex AI Reasoning Engine
   inbound side extracts W3C context (already on the roadmap), the
   host->weather span becomes literally one trace ID end-to-end.

2. **`gen_ai.conversation.id` correlation attribute (works today).**
   Today the Reasoning Engine inbound side does NOT extract `traceparent`,
   so we additionally generate a per-call `conversation_id`, plumb it
   through the A2A request as the `user_id` (Reasoning Engine forwards
   that into the ADK session, where the weather agent's tool can read it
   from `ToolContext`), and tag BOTH agents' root spans with the same
   `gen_ai.conversation.id`. Cloud Trace UI lets you filter by that
   attribute to see all related traces, and the GenAI semantic conventions
   define this as the canonical correlation key for multi-turn / multi-agent
   conversations.
"""

from __future__ import annotations

import os
import uuid
from typing import Dict, Optional, Tuple

try:
    from opentelemetry import trace
    from opentelemetry.propagators.textmap import DefaultGetter, DefaultSetter
    from opentelemetry.trace.propagation.tracecontext import (
        TraceContextTextMapPropagator,
    )
except Exception:  # pragma: no cover - OTel optional at import time
    trace = None
    TraceContextTextMapPropagator = None  # type: ignore


# GenAI semantic convention key for the multi-turn/multi-agent correlation id.
CONVERSATION_ID_ATTR = "gen_ai.conversation.id"

# Prefix used when stuffing the conversation_id into the ADK `user_id`
# field so it round-trips into the receiving agent's session.
USER_ID_PREFIX = "conv-"


# ---------------------------------------------------------------------------
# Outbound (host) side
# ---------------------------------------------------------------------------

def inject_w3c_context_into_headers(headers: Dict[str, str]) -> Dict[str, str]:
    """Inject W3C traceparent + tracestate into an outbound headers dict.

    Idempotent: existing entries are preserved.
    Returns the same dict for convenient chaining.
    """
    if TraceContextTextMapPropagator is None:
        return headers
    TraceContextTextMapPropagator().inject(headers)
    return headers


def begin_a2a_call(
    *,
    downstream_agent: str,
    conversation_id: Optional[str] = None,
) -> Tuple[str, Dict[str, str]]:
    """Prep a correlation_id + headers carrier for an outbound A2A call.

    - Generates a new conversation_id if one isn't already in scope.
    - Tags the *current* OTel span with `gen_ai.conversation.id` so the
      host-side trace is queryable by it.
    - Returns (conversation_id, headers_carrier_dict).

    The returned `headers` dict can be merged into the requests.post(headers=...)
    call. It will contain `traceparent` / `tracestate` populated from the
    currently active OTel context.
    """
    conv_id = conversation_id or _conversation_id_from_current_context() or _new_conversation_id()

    if trace is not None:
        span = trace.get_current_span()
        if span is not None and span.is_recording():
            span.set_attribute(CONVERSATION_ID_ATTR, conv_id)
            span.set_attribute("gen_ai.agent.downstream", downstream_agent)

    headers: Dict[str, str] = {}
    inject_w3c_context_into_headers(headers)
    return conv_id, headers


def wrap_user_id_with_conversation(user_id: str, conversation_id: str) -> str:
    """Pack a conversation_id into the ADK `user_id` field.

    Format: ``conv-{conversation_id}__{original_user_id}``

    The receiving agent's tool can call `unwrap_conversation_from_user_id`
    on `ToolContext.session.user_id` to recover the conv_id.
    """
    safe_user = user_id or "anon"
    return f"{USER_ID_PREFIX}{conversation_id}__{safe_user}"


# ---------------------------------------------------------------------------
# Inbound (weather) side
# ---------------------------------------------------------------------------

def unwrap_conversation_from_user_id(user_id: Optional[str]) -> Tuple[Optional[str], str]:
    """Inverse of `wrap_user_id_with_conversation`.

    Returns ``(conversation_id_or_None, raw_user_id)``.
    Safe to call on user_ids that were not wrapped.
    """
    if not user_id or not user_id.startswith(USER_ID_PREFIX):
        return None, user_id or "anon"
    rest = user_id[len(USER_ID_PREFIX):]
    if "__" not in rest:
        return rest, "anon"
    conv_id, _, raw = rest.partition("__")
    return conv_id, raw or "anon"


def tag_current_span_with_conversation(conversation_id: Optional[str]) -> None:
    """Stamp `gen_ai.conversation.id` on the active span so Cloud Trace can
    join this trace with the host's via attribute filter."""
    if not conversation_id or trace is None:
        return
    span = trace.get_current_span()
    if span is not None and span.is_recording():
        span.set_attribute(CONVERSATION_ID_ATTR, conversation_id)


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------

def _new_conversation_id() -> str:
    return uuid.uuid4().hex


def _conversation_id_from_current_context() -> Optional[str]:
    """Return the conv_id already on the current span, if any."""
    if trace is None:
        return None
    span = trace.get_current_span()
    if span is None or not span.is_recording():
        return None
    # OTel SDK API doesn't expose .get_attribute publicly; we keep this
    # best-effort and fall back to None if the SDK changes.
    attrs = getattr(span, "_attributes", None)
    if attrs and CONVERSATION_ID_ATTR in attrs:
        return str(attrs[CONVERSATION_ID_ATTR])
    return None
