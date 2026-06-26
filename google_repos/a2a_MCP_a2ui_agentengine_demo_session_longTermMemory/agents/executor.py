# ADK CLI Entry bridge: references circana_pilot_agent/executor.py
try:
    from circana_pilot_agent.executor import CircanaPilotExecutor
except ImportError:
    from agents.circana_pilot_agent.executor import CircanaPilotExecutor
