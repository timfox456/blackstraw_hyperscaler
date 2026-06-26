"""Top-level re-export so `deploy_agent_engine.py` can `from agent import root_agent`.

Switch the import below to host_agent.agent if you want to deploy the
orchestrator instead of the weather agent.
"""

from weather_agent.agent import root_agent  # noqa: F401
