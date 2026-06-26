import os
import json
from google.adk.agents import Agent
from google.adk.tools import FunctionTool

def simulate_scaling_tool(audience_id: str) -> str:
    """Simulates looking up look-alike expansion configurations and scaling factors.
    
    Args:
        audience_id: The identifier of the base audience.
    """
    return json.dumps({
        "status": "Scaled",
        "audience_id": audience_id,
        "scaled_audience_id": f"{audience_id}-SCALED",
        "expansion_multiplier": 3.42,
        "message": "Scale (STUB): Successfully performed lookalike lookups. Segment scaled by 3.42x."
    }, indent=2)

ROLE_DESCRIPTION = (
    "You are the Circana Scale Agent. Your job is to simulate the lookalike expansion. "
    "Call simulate_scaling_tool with the given audience_id and return the scaled_audience_id."
)

scale_agent = Agent(
    name="AudienceScaleAgent",
    model=os.environ.get("GOOGLE_GENAI_MODEL", "gemini-2.5-flash"),
    description="Specialized Audience Scale Agent for look-alike cohort expansion.",
    instruction=ROLE_DESCRIPTION,
    tools=[FunctionTool(simulate_scaling_tool)]
)

def get_agent_card(host: str, port: int) -> "AgentCard":
    from a2a.types import AgentCard, AgentSkill, AgentCapabilities, TransportProtocol
    skills = [
        AgentSkill(
            id='scale-agent-internal-skill',
            name='Audience Segment Scaling',
            description='Performs look-alike model expansion for base customer segments.',
            tags=['scale'],
            examples=['Scale cohort segment AUD-DIET-PEPSI-12PK-999.'],
        )
    ]
    return AgentCard(
        name='AudienceScaleAgent',
        description='Specialized Scale Agent for look-alike cohort expansion.',
        url=f'http://{host}:{port}/',
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=False),
        skills=skills,
        preferred_transport=TransportProtocol.http_json,
    )
