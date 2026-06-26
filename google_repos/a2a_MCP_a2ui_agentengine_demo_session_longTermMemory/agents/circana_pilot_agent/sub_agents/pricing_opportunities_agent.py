import os
from google.adk.agents import Agent
from google.adk.tools import FunctionTool

try:
    from ..tools import pricing_opportunities_tool
except (ImportError, ValueError):
    from tools import pricing_opportunities_tool

ROLE_DESCRIPTION = (
    "You are the Circana Pricing Opportunities Agent. Your job is to analyze historical portfolio databases "
    "to identify high-attrition product categories. Call pricing_opportunities_tool and return the results. "
    "CRITICAL: You MUST output the exact <a2ui-json> block returned by the tool verbatim at the end of your response. "
    "Do not modify or omit the XML tags or JSON content."
)

pricing_opportunities_agent = Agent(
    name="PricingOpportunitiesAgent",
    model=os.environ.get("GOOGLE_GENAI_MODEL", "gemini-2.5-flash"),
    description="Specialist agent identifying high buyer attrition products.",
    instruction=ROLE_DESCRIPTION,
    tools=[FunctionTool(pricing_opportunities_tool)]
)

def get_agent_card(host: str, port: int) -> "AgentCard":
    from a2a.types import AgentCard, AgentSkill, AgentCapabilities, TransportProtocol
    skills = [
        AgentSkill(
            id='pricing-opportunities-internal-skill',
            name='Pricing Attrition Search',
            description='Searches retail transaction databases to detect customer loss metrics.',
            tags=['pricing'],
            examples=['Find high attrition items.'],
        )
    ]
    return AgentCard(
        name='PricingOpportunitiesAgent',
        description='Specialist agent identifying high buyer attrition products.',
        url=f'http://{host}:{port}/',
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=False),
        skills=skills,
        preferred_transport=TransportProtocol.http_json,
    )
