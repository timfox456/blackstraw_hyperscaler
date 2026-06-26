import os
from google.adk.agents import Agent
from google.adk.tools import FunctionTool

try:
    from ..tools import send_message_tool
except (ImportError, ValueError):
    from tools import send_message_tool

ROLE_DESCRIPTION = (
    "You are the Circana Pricing & Assortment Orchestrator. Your job is to identify and analyze "
    "portfolio pricing changes and customer loss. Delegate to 'PricingOpportunitiesAgent' using your "
    "send_message_tool to search transaction records. CRITICAL: You MUST print the exact <a2ui-json> XML block "
    "returned by the specialist agent verbatim at the end of your response under all circumstances. Do not omit the widget."
)

pricing_assortment_orchestrator = Agent(
    name="PricingAssortmentOrchestrator",
    model=os.environ.get("GOOGLE_GENAI_MODEL", "gemini-2.5-flash"),
    description="Orchestrator that analyzes price increases and shopper attrition tables.",
    instruction=ROLE_DESCRIPTION,
    tools=[FunctionTool(send_message_tool)]
)

def get_agent_card(host: str, port: int) -> "AgentCard":
    from a2a.types import AgentCard, AgentSkill, AgentCapabilities, TransportProtocol
    skills = [
        AgentSkill(
            id='pricing-assortment-internal-skill',
            name='Internal Pricing Assortment Analysis',
            description='Identifies pricing opportunities and shopper attrition.',
            tags=['pricing'],
            examples=['Identify products with high attrition.'],
        )
    ]
    return AgentCard(
        name='PricingAssortmentOrchestrator',
        description='Orchestrator that analyzes price increases and shopper attrition tables.',
        url=f'http://{host}:{port}/',
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=False),
        skills=skills,
        preferred_transport=TransportProtocol.http_json,
    )
