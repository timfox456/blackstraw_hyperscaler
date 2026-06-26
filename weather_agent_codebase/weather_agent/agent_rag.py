"""Standalone RAG-only weather agent.

ADK constraint: ``VertexAiRagRetrieval`` must be the only tool on its
agent and cannot be combined with other tools, so this agent ships
separately from ``weather_agent/agent.py`` (which carries the
``get_weather`` / ``set_persona`` / ``analyze_weather_image`` /
MCP-fetch tools).

The corpus is created (or reused) on import via
``create_or_get_rag_corpus()`` so this module is self-contained.
"""

from __future__ import annotations

import os
import sys

# Make project-root packages importable when bundled into a Reasoning Engine.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.adk.agents.llm_agent import Agent

from gcp.retrieval.weather_rag import (
    RAG_CORPUS_RESOURCE_NAME,
    build_rag_retrieval_tool,
    create_or_get_rag_corpus,
)


# Ensure the RAG corpus exists before we wire up the tool. ``RAG_CORPUS_RESOURCE_NAME``
# is empty until ``create_or_get_rag_corpus()`` runs, so we always call it at
# import time (the function itself is idempotent).
_corpus_resource_name = RAG_CORPUS_RESOURCE_NAME or create_or_get_rag_corpus()


root_agent = Agent(
    model="gemini-2.5-flash",
    name="weather_rag_agent",
    description="Weather knowledge agent backed by a Vertex AI RAG corpus.",
    instruction=(
        "You are a weather knowledge assistant. "
        "Use the retrieve_weather_knowledge tool to answer questions about "
        "weather patterns and conditions."
    ),
    tools=[build_rag_retrieval_tool(_corpus_resource_name)],
)
