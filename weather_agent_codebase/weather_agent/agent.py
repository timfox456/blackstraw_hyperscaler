from __future__ import annotations

import os
import sys
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.adk.agents.llm_agent import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioConnectionParams, StdioServerParameters

try:
    from google.adk.tools import ToolContext  # type: ignore
except Exception:
    ToolContext = None  # type: ignore

try:
    from gcp.observability.otel_setup import start_tool_span
    from gcp.observability.context_propagation import (
        tag_current_span_with_conversation,
        unwrap_conversation_from_user_id,
    )
except Exception:
    def start_tool_span(_):  # type: ignore
        from contextlib import nullcontext
        return nullcontext()

    def tag_current_span_with_conversation(_):  # type: ignore
        return None

    def unwrap_conversation_from_user_id(_):  # type: ignore
        return None, "anon"


# Prompt version tracking — manually set when deploying a new instruction version
PROMPT_ID = "7282778269173153792"
PROMPT_VERSION = "1"


def _extract_conversation_id(tool_context) -> Optional[str]:
    if tool_context is None:
        return None
    user_id = None
    for path in ("session", "_invocation_context"):
        obj = getattr(tool_context, path, None)
        if obj is None:
            continue
        if hasattr(obj, "user_id"):
            user_id = obj.user_id
            break
        if hasattr(obj, "session") and hasattr(obj.session, "user_id"):
            user_id = obj.session.user_id
            break
    conv_id, _ = unwrap_conversation_from_user_id(user_id)
    return conv_id


def get_weather(location: str, tool_context=None) -> str:
    """Returns simulated weather for a location."""
    with start_tool_span("get_weather") as span:
        conv_id = _extract_conversation_id(tool_context)
        tag_current_span_with_conversation(conv_id)

        if span is not None and hasattr(span, "set_attribute"):
            span.set_attribute("weather.location", location)
            if conv_id:
                span.set_attribute("gen_ai.conversation.id", conv_id)

        if span is not None and hasattr(span, "set_attribute"):
            span.set_attribute("prompt.id", PROMPT_ID)
            span.set_attribute("prompt.version", PROMPT_VERSION)

        if "chicago" in location.lower():
            return "It's 75 degrees and sunny in Chicago."
        if "miami" in location.lower():
            return "It's 90 degrees and humid in Miami."
        return f"It's 72 degrees and partly cloudy in {location}."


def set_persona(persona: str, tool_context=None) -> str:
    """Switches the agent's response persona.

    Args:
        persona: The persona to adopt. Options: weatherman, scientist, casual.
    """
    with start_tool_span("set_persona") as span:
        conv_id = _extract_conversation_id(tool_context)
        tag_current_span_with_conversation(conv_id)

        if span is not None and hasattr(span, "set_attribute"):
            span.set_attribute("persona.requested", persona)
            if conv_id:
                span.set_attribute("gen_ai.conversation.id", conv_id)

        if span is not None and hasattr(span, "set_attribute"):
            span.set_attribute("prompt.id", PROMPT_ID)
            span.set_attribute("prompt.version", PROMPT_VERSION)

        personas = {
            "weatherman": (
                "You are an enthusiastic TV weatherman. Use dramatic language, "
                "exclamation points, and meteorological terms. Always sign off "
                "with 'Back to you in the studio!'"
            ),
            "scientist": (
                "You are a dry, precise meteorological scientist. Cite atmospheric "
                "pressure, humidity, and dew points. Be technical and unemotional."
            ),
            "casual": (
                "You are a chill friend texting weather updates. Use slang, "
                "abbreviations, keep it super short."
            ),
        }

        result = personas.get(
            persona.lower(),
            f"Unknown persona: {persona}. Available: weatherman, scientist, casual"
        )

        if span is not None and hasattr(span, "set_attribute"):
            span.set_attribute("persona.applied", persona.lower() in personas)

        return result


def analyze_weather_image(image_description: str, tool_context=None) -> str:
    """Analyzes a weather-related image and provides commentary.

    Args:
        image_description: Description or content extracted from the image.
    """
    with start_tool_span("analyze_weather_image") as span:
        conv_id = _extract_conversation_id(tool_context)
        tag_current_span_with_conversation(conv_id)

        if span is not None and hasattr(span, "set_attribute"):
            span.set_attribute("gen_ai.tool.name", "analyze_weather_image")
            span.set_attribute("attachment.type", "image")
            if conv_id:
                span.set_attribute("gen_ai.conversation.id", conv_id)

        if span is not None and hasattr(span, "set_attribute"):
            span.set_attribute("prompt.id", PROMPT_ID)
            span.set_attribute("prompt.version", PROMPT_VERSION)

        return (
            f"Based on the image showing '{image_description}', the weather appears "
            "to match current conditions. Cloud and precipitation patterns suggest "
            "ongoing atmospheric activity."
        )

def dream_consolidate(session_summary: str, turn_count: int, tool_context=None) -> str:
    """Background memory consolidation (dreaming). Summarizes conversation history
    into a compact memory snapshot and emits a discrete trace event.

    Args:
        session_summary: A brief summary of what has been discussed so far.
        turn_count: Number of turns in the current session.
    """
    with start_tool_span("memory_dreaming") as span:
        conv_id = _extract_conversation_id(tool_context)
        tag_current_span_with_conversation(conv_id)

        if span is not None and hasattr(span, "set_attribute"):
            span.set_attribute("gen_ai.operation.name", "memory_dreaming")
            span.set_attribute("memory.turn_count", turn_count)
            span.set_attribute("memory.summary_length", len(session_summary))
            span.set_attribute("memory.consolidation_type", "dreaming")
            span.set_attribute("prompt.id", PROMPT_ID)
            span.set_attribute("prompt.version", PROMPT_VERSION)
            if conv_id:
                span.set_attribute("gen_ai.conversation.id", conv_id)

        return f"Memory consolidated: {session_summary[:200]}... ({turn_count} turns compacted)"


root_agent = Agent(
    model="gemini-2.5-flash",
    name="weather_agent",
    description="Provides weather information for any location.",
    instruction=(
        "You are a helpful weather assistant. "
        "Use the get_weather tool to answer weather questions. "
        "Use the set_persona tool when the user asks you to change your style or persona. "
        "Use the analyze_weather_image tool when the user shares an image or describes weather conditions visually. "
        "Use the fetch tool to retrieve weather information from URLs when asked. "
        "Use the dream_consolidate tool after every 3 turns to summarize the conversation so far — pass a brief summary and the turn count. "
        "After switching persona, adopt that style immediately in your next response."
    ),
    tools=[get_weather, set_persona, analyze_weather_image, dream_consolidate,
        MCPToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command="npx",
                    args=["-y", "@modelcontextprotocol/server-fetch"],
                )
            )
        ),
    ],
)