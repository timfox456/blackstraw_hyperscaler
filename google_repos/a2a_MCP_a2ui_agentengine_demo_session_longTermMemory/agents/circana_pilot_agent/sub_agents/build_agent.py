import os
from google.adk.agents import Agent
from google.adk.tools import FunctionTool

try:
    from ..tools import build_audience_tool
except (ImportError, ValueError):
    from tools import build_audience_tool

ROLE_DESCRIPTION = (
    "You are the Circana Build Agent. Your job is to construct the shopper cohort. "
    "Call build_audience_tool to build the cohort and return the result."
)

build_agent = Agent(
    name="AudienceBuildAgent",
    model=os.environ.get("GOOGLE_GENAI_MODEL", "gemini-2.5-flash"),
    description="Specialized Audience Build Agent for cohort construction.",
    instruction=ROLE_DESCRIPTION,
    tools=[FunctionTool(build_audience_tool)]
)

def get_agent_card(host: str, port: int) -> "AgentCard":
    from a2a.types import AgentCard, AgentSkill, AgentCapabilities, TransportProtocol
    skills = [
        AgentSkill(
            id='build-agent-internal-skill',
            name='Audience Segment Building',
            description='Constructs customer segments for specific product brands.',
            tags=['build'],
            examples=['Build segment for Diet Pepsi.'],
        )
    ]
    return AgentCard(
        name='AudienceBuildAgent',
        description='Specialized Audience Build Agent wrapping the audience building tool.',
        url=f'http://{host}:{port}/',
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=False),
        skills=skills,
        preferred_transport=TransportProtocol.http_json,
    )
