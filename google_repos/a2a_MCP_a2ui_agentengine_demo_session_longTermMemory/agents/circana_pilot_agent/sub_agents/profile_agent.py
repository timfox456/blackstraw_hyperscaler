import os
from google.adk.agents import Agent
from google.adk.tools import FunctionTool

try:
    from ..tools import profile_audience_tool
except (ImportError, ValueError):
    from tools import profile_audience_tool

ROLE_DESCRIPTION = (
    "You are the Circana Profile Agent. Your job is to compile the demographic and geographic audience profile. "
    "Call profile_audience_tool to compile demographic breakdown metrics and return the result. "
    "CRITICAL: You MUST output the exact <a2ui-json> block returned by the tool verbatim at the end of your response. "
    "Do not modify or omit the XML tags or JSON content."
)

profile_agent = Agent(
    name="AudienceProfileAgent",
    model="gemini-2.5-flash",
    description="Specialized Audience Profile Agent for compiling demographic breakdown metrics.",
    instruction=ROLE_DESCRIPTION,
    tools=[FunctionTool(profile_audience_tool)]
)

def get_agent_card(host: str, port: int) -> "AgentCard":
    from a2a.types import AgentCard, AgentSkill, AgentCapabilities, TransportProtocol
    skills = [
        AgentSkill(
            id='profile-agent-internal-skill',
            name='Audience Demographic Profiling',
            description='Compiles demographic and geographic breakdown metrics for audience segments.',
            tags=['profile'],
            examples=['Compile demographic breakdown and audience profile for this segment.'],
        )
    ]
    return AgentCard(
        name='AudienceProfileAgent',
        description='Specialized Audience Profile Agent for compiling demographic breakdown metrics and audience profile.',
        url=f'http://{host}:{port}/',
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=False),
        skills=skills,
        preferred_transport=TransportProtocol.http_json,
    )
