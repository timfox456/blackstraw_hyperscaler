import os
from google.adk.agents import Agent

markdown_optimization_orchestrator = Agent(
    name="MarkdownOptimizationOrchestrator",
    model=os.environ.get("GOOGLE_GENAI_MODEL", "gemini-2.5-flash"),
    description="Orchestrator for markdown scheduling and inventory clearances.",
    instruction="You are a dummy markdown orchestrator. Do not invoke tools. Prompt the user that markdown optimization flows are stubbed."
)
