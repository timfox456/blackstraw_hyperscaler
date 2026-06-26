import os
from google.adk.agents import Agent
from google.adk.tools import FunctionTool

try:
    from ..tools import size_audience_tool
except (ImportError, ValueError):
    from tools import size_audience_tool

ROLE_DESCRIPTION = (
    "You are the Circana Size Agent. Your job is to size the cohort across channels. "
    "Call size_audience_tool to compile reach metrics and return the result. "
    "CRITICAL: You MUST output the exact <a2ui-json> block returned by the tool verbatim at the end of your response. "
    "Do not modify or omit the XML tags or JSON content."
)

size_agent = Agent(
    name="AudienceSizeAgent",
    model=os.environ.get("GOOGLE_GENAI_MODEL", "gemini-2.5-flash"),
    description="Specialized Audience Size Agent for compiling target reach metrics.",
    instruction=ROLE_DESCRIPTION,
    tools=[FunctionTool(size_audience_tool)]
)

def get_agent_card(host: str, port: int) -> "AgentCard":
    from a2a.types import AgentCard, AgentSkill, AgentCapabilities, TransportProtocol
    skills = [
        AgentSkill(
            id='size-agent-internal-skill',
            name='Audience Segment Sizing',
            description='Calculates matching households and active reach across marketing channels.',
            tags=['size'],
            examples=['Size segment AUD-DIET-PEPSI-12PK-999.'],
        )
    ]
    return AgentCard(
        name='AudienceSizeAgent',
        description='Specialized Audience Size Agent wrapping the audience sizing tool.',
        url=f'http://{host}:{port}/',
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=False),
        skills=skills,
        preferred_transport=TransportProtocol.http_json,
    )
