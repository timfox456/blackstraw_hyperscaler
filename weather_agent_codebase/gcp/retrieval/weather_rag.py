"""Vertex AI RAG retrieval for the weather agent evaluation.

Creates (or reuses) a Vertex AI RAG corpus called ``weather-knowledge-corpus``
in ``gemini-enterprise-app-499621 / us-central1`` and seeds it with a small
set of in-memory weather knowledge documents. Exposes a
``VertexAiRagRetrieval`` ADK tool pointed at that corpus so an agent can
answer factual weather-pattern questions backed by RAG.

ADK constraint: ``VertexAiRagRetrieval`` must be the *only* tool on its
agent (cannot be combined with other tools), which is why this module
ships its own dedicated agent in ``weather_agent/agent_rag.py``.

Public surface:

- ``RAG_CORPUS_RESOURCE_NAME``  module-level string, populated after
  ``create_or_get_rag_corpus()`` has been called.
- ``create_or_get_rag_corpus()``  idempotent: returns the existing corpus
  resource name if already provisioned, otherwise creates + seeds it.
- ``build_rag_retrieval_tool(corpus_resource_name)``  returns a fully
  configured ``VertexAiRagRetrieval`` tool.
"""

from __future__ import annotations

import os
import tempfile
from typing import Optional

import vertexai
from vertexai.preview import rag

from google.adk.tools.retrieval.vertex_ai_rag_retrieval import (
    VertexAiRagRetrieval,
)


PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "gemini-enterprise-app-499621")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
CORPUS_DISPLAY_NAME = "weather-knowledge-corpus"

# Populated by ``create_or_get_rag_corpus()``. Other modules can import this
# directly once that function has run.
RAG_CORPUS_RESOURCE_NAME: str = ""


# ---------------------------------------------------------------------------
# Seed documents (kept in-module so no external files are needed).
# ---------------------------------------------------------------------------

_WEATHER_DOCS: dict[str, str] = {
    "chicago_weather.txt": (
        "Chicago Weather Patterns\n"
        "========================\n"
        "Chicago has a humid continental climate with four distinct seasons.\n"
        "Lake Michigan exerts a strong moderating influence on the city, producing\n"
        "lake-effect snow in winter and cooling lake breezes in summer.\n\n"
        "Summer (June-August): Daytime highs typically 75-90 F with high humidity.\n"
        "Afternoon thunderstorms are common, often driven by a clash between humid\n"
        "Gulf air and cooler lake-modified air.\n\n"
        "Winter (December-February): Cold and snowy. Daytime highs of -10 to 30 F\n"
        "are common. Lake-effect snow events can dump 6-12 inches of snow in hours\n"
        "when arctic air sweeps over the relatively warmer lake surface.\n\n"
        "Spring and Fall: Highly variable. Cold fronts drive rapid temperature\n"
        "swings and severe-weather outbreaks (especially May-June).\n"
    ),
    "miami_weather.txt": (
        "Miami Weather Patterns\n"
        "======================\n"
        "Miami has a tropical monsoon climate. Temperatures stay warm year-round\n"
        "and the city sees a pronounced wet season and dry season rather than\n"
        "four traditional seasons.\n\n"
        "Wet season (May-October): Hot and humid with daytime highs of 85-95 F.\n"
        "Daily afternoon thunderstorms are typical, driven by sea-breeze\n"
        "convergence over the peninsula. Hurricane season runs June 1 through\n"
        "November 30; the most active period is mid-August through mid-October.\n\n"
        "Dry season (November-April): Mild and pleasant with highs of 70-80 F.\n"
        "Cold fronts occasionally push into south Florida bringing brief cool\n"
        "snaps. Humidity and rainfall drop sharply compared to summer.\n"
    ),
    "new_york_weather.txt": (
        "New York City Weather Patterns\n"
        "==============================\n"
        "New York City sits at the boundary between humid subtropical and humid\n"
        "continental climate zones. The Atlantic Ocean moderates temperature\n"
        "extremes year-round but also feeds nor'easter storm systems in winter.\n\n"
        "Summer (June-August): Warm and humid with highs of 75-88 F. Multi-day\n"
        "heat waves above 90 F occur several times each summer. Severe\n"
        "thunderstorms are less frequent than in the Midwest but still occur.\n\n"
        "Winter (December-February): Cold and snowy with highs of 30-45 F.\n"
        "Nor'easters can deliver 6-24 inches of snow in a single storm.\n"
        "Coastal flooding is a risk during high astronomical tides.\n\n"
        "Spring and Fall: Comfortable transitions, with foliage peak in late\n"
        "October and frequent rain in April.\n"
    ),
    "general_meteorology.txt": (
        "General Meteorology Reference\n"
        "=============================\n"
        "Atmospheric pressure: Standard sea-level pressure is 1013.25 hPa.\n"
        "High-pressure systems are associated with clear, settled weather.\n"
        "Low-pressure systems are associated with clouds, precipitation, and\n"
        "stormy conditions.\n\n"
        "Relative humidity: The amount of water vapor in the air relative to\n"
        "the maximum the air can hold at that temperature. Values above 70%\n"
        "feel muggy; values below 30% feel dry.\n\n"
        "Wind patterns: The jet stream is a fast-flowing river of air at\n"
        "~10 km altitude that steers mid-latitude storm systems. Prevailing\n"
        "westerlies dominate North American weather, moving systems west\n"
        "to east.\n\n"
        "Cloud types: Cumulus (puffy, fair-weather or thunderstorm),\n"
        "stratus (low overcast layers), cirrus (high, wispy ice clouds).\n"
        "Cumulonimbus are the towering thunderstorm clouds.\n\n"
        "Dew point: The temperature to which air must be cooled to become\n"
        "saturated. A higher dew point means more moisture in the air;\n"
        "dew points above 65 F feel humid, above 70 F feel oppressive.\n"
    ),
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _ensure_vertex_initialized() -> None:
    """Idempotent vertexai.init() so callers don't have to do it themselves."""
    vertexai.init(project=PROJECT_ID, location=LOCATION)


def _find_corpus_by_display_name(display_name: str):
    """Returns the existing corpus with the given display name, or None."""
    for corpus in rag.list_corpora():
        if getattr(corpus, "display_name", None) == display_name:
            return corpus
    return None


def _seed_corpus(corpus_resource_name: str) -> None:
    """Writes each in-memory doc to a temp file and uploads it to the corpus."""
    with tempfile.TemporaryDirectory(prefix="weather_rag_") as tmp_dir:
        for filename, content in _WEATHER_DOCS.items():
            path = os.path.join(tmp_dir, filename)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            rag.upload_file(
                corpus_name=corpus_resource_name,
                path=path,
                display_name=filename,
                description=f"Weather knowledge document: {filename}",
            )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def create_or_get_rag_corpus() -> str:
    """Idempotent: creates the corpus + seeds docs on first run, otherwise
    returns the existing resource name.

    Side effect: sets the module-level ``RAG_CORPUS_RESOURCE_NAME``.
    """
    global RAG_CORPUS_RESOURCE_NAME

    _ensure_vertex_initialized()

    existing = _find_corpus_by_display_name(CORPUS_DISPLAY_NAME)
    if existing is not None:
        RAG_CORPUS_RESOURCE_NAME = existing.name
        return existing.name

    corpus = rag.create_corpus(
        display_name=CORPUS_DISPLAY_NAME,
        backend_config=rag.RagVectorDbConfig(
            vector_db=rag.RagManagedVertexVectorSearch()
        )
    )
    _seed_corpus(corpus.name)

    RAG_CORPUS_RESOURCE_NAME = corpus.name
    return corpus.name


def build_rag_retrieval_tool(corpus_resource_name: str) -> VertexAiRagRetrieval:
    """Returns a configured ``VertexAiRagRetrieval`` tool pointed at the
    given corpus resource name.

    Settings (per evaluation spec):
        - similarity_top_k = 3
        - vector_distance_threshold = 0.5
    """
    return VertexAiRagRetrieval(
        name="retrieve_weather_knowledge",
        description=(
            "Retrieves authoritative weather knowledge from the indexed "
            "weather-knowledge-corpus. Use this tool to answer questions about "
            "regional weather patterns (Chicago, Miami, New York) and general "
            "meteorology concepts (pressure, humidity, jet stream, cloud types)."
        ),
        rag_resources=[rag.RagResource(rag_corpus=corpus_resource_name)],
        similarity_top_k=3,
        vector_distance_threshold=0.5,
    )
