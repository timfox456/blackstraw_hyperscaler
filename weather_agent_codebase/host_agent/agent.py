"""Host orchestrator agent (PDF Pathway A: deployed to Reasoning Engine).

Delegates weather queries to the remote Weather Forecast Agent via A2A.

Distributed tracing:
  - OTel spans for the LLM call + tool execution (`gen_ai.*` semconv).
  - W3C `traceparent` header injected on every A2A HTTPS call so when the
    receiving Reasoning Engine starts extracting it, the two agents'
    traces merge into a single trace ID.
  - `gen_ai.conversation.id` correlation attribute set on both sides
    (today's mechanism: filter Cloud Trace by this attribute to see the
    cross-agent hop).
"""

from __future__ import annotations

import json
import os
import sys

# Make project-root packages importable when bundled into a Reasoning Engine.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import google.auth
import google.auth.transport.requests
import requests
import vertexai
from google.adk.agents.llm_agent import Agent

try:
    from gcp.observability.otel_setup import start_tool_span
    from gcp.observability.context_propagation import (
        begin_a2a_call,
        wrap_user_id_with_conversation,
    )
except Exception:  # pragma: no cover
    def start_tool_span(_):  # type: ignore
        from contextlib import nullcontext
        return nullcontext()

    def begin_a2a_call(**_):  # type: ignore
        return "no-otel", {}

    def wrap_user_id_with_conversation(user_id, _):  # type: ignore
        return user_id


PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "gemini-enterprise-app-499621")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
WEATHER_AGENT_RE_ID = os.environ.get(
    "WEATHER_AGENT_REASONING_ENGINE_ID", "7321857386325475328"
)

vertexai.init(project=PROJECT_ID, location=LOCATION)


def get_weather_from_remote(location: str) -> str:
    """Calls the remote Weather Agent (Reasoning Engine) over A2A."""
    with start_tool_span("get_weather_from_remote") as span:
        if span is not None and hasattr(span, "set_attribute"):
            span.set_attribute("weather.location", location)
            span.set_attribute("gen_ai.agent.downstream", "weather_agent")

        # Begin the A2A call: generate (or inherit) a conversation_id, stamp
        # it on the current span, and prep W3C-injected outbound headers.
        conv_id, propagation_headers = begin_a2a_call(downstream_agent="weather_agent")

        creds, _ = google.auth.default()
        creds.refresh(google.auth.transport.requests.Request())
        token = creds.token

        base_url = (
            f"https://{LOCATION}-aiplatform.googleapis.com/v1beta1/projects/"
            f"{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{WEATHER_AGENT_RE_ID}"
        )
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            **propagation_headers,  # W3C traceparent / tracestate
        }

        # Pack the conversation_id into the ADK user_id so the receiving
        # agent's tool can recover it from its session and tag its own spans.
        wrapped_user = wrap_user_id_with_conversation("host-user", conv_id)

        session_resp = requests.post(
            f"{base_url}:query",
            headers=headers,
            json={
                "class_method": "create_session",
                "input": {"user_id": wrapped_user},
            },
            timeout=30,
        )
        session_resp.raise_for_status()
        session_id = session_resp.json()["output"]["id"]

        body = {
            "class_method": "stream_query",
            "input": {
                "user_id": wrapped_user,
                "session_id": session_id,
                "message": f"What is the weather in {location}?",
            },
        }
        resp = requests.post(f"{base_url}:streamQuery", headers=headers, json=body, timeout=60)
        resp.raise_for_status()

        for line in resp.text.strip().split("\n"):
            if not line:
                continue
            try:
                event = json.loads(line)
                if "content" in event:
                    for part in event["content"].get("parts", []):
                        if "text" in part:
                            return part["text"]
            except Exception:
                continue
        return "Could not get weather."


host_agent = Agent(
    model="gemini-2.5-flash",
    name="host_agent",
    description="Orchestrator that delegates weather queries to a remote weather agent.",
    instruction="You are an orchestrator. Use get_weather_from_remote to answer weather questions.",
    tools=[get_weather_from_remote],
)

root_agent = host_agent
