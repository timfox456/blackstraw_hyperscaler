import os
from google.adk.agents import Agent
from google.adk.tools import FunctionTool

try:
    from ..tools import get_loyalty_options_tool, launch_campaign_tool
except (ImportError, ValueError):
    from tools import get_loyalty_options_tool, launch_campaign_tool

loyalty_campaign_orchestrator = Agent(
    name="LoyaltyCampaignOrchestrator",
    model=os.environ.get("GOOGLE_GENAI_MODEL", "gemini-2.5-flash"),
    description="Orchestrator for personalization campaigns and loyalty rewards.",
    instruction="You are the loyalty campaign orchestrator. First call get_loyalty_options_tool to fetch campaign metrics and dashboard, then call launch_campaign_tool to activate the personalized campaign. You MUST copy and print the exact <a2ui-json> XML block returned by get_loyalty_options_tool verbatim in your response without altering any character.",
    tools=[FunctionTool(get_loyalty_options_tool), FunctionTool(launch_campaign_tool)]
)

def get_agent_card(host: str, port: int) -> "AgentCard":
    from a2a.types import AgentCard, AgentSkill, AgentCapabilities, TransportProtocol
    skills = [
        AgentSkill(
            id='loyalty-campaign-internal-skill',
            name='Internal Loyalty Campaign Customization',
            description='Builds personalization rewards and launches campaign dashboards.',
            tags=['loyalty', 'personalization'],
            examples=['Launch loyalty personalization campaign for Diet Pepsi.'],
        )
    ]
    return AgentCard(
        name='LoyaltyCampaignOrchestrator',
        description='Orchestrator for personalization campaigns and loyalty rewards.',
        url=f'http://{host}:{port}/',
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=False),
        skills=skills,
        preferred_transport=TransportProtocol.http_json,
    )
