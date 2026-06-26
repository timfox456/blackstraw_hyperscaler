# ADK CLI Entry bridge: references circana_pilot_agent/agent.py
try:
    from circana_pilot_agent.agent import root_agent
except ImportError:
    from agents.circana_pilot_agent.agent import root_agent
