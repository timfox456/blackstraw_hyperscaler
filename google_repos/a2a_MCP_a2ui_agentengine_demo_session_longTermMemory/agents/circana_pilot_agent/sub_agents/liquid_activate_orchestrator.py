import os
from google.adk.agents import Agent
from google.adk.tools import FunctionTool

try:
    from ..tools import build_audience_tool, size_audience_tool, activate_audience_tool, profile_audience_tool
except (ImportError, ValueError):
    from tools import build_audience_tool, size_audience_tool, activate_audience_tool, profile_audience_tool

ROLE_DESCRIPTION = (
    "You are the Circana Liquid Activate Orchestrator. Your job is to coordinate audience construction, scaling, and sizing. "
    "When a product is selected (e.g., 'Tropicana Pure Premium'), call build_audience_tool with the product name and STOP. In your final text response after calling build_audience_tool, you MUST output exactly and ONLY: 'Selected product: <Product Name>'. Do NOT add any other sentences or call size_audience_tool yet.\n"
    "When the user confirms sizing (e.g., clicking 'Yes, size it' or asking to size), you MUST immediately call size_audience_tool with the audience ID (e.g. AUD-TROPICANA-PURE-PREMIUM-52OZ-999 or derived from the product name). Do NOT ask the user for the ID.\n"
    "If asked to profile demographic distributions, call profile_audience_tool. CRITICAL: You MUST output the exact <a2ui-json> block returned by the tool verbatim at the end of your response. Do not modify or omit the XML tags or JSON content.\n"
    "If asked to activate the segment with partners, call activate_audience_tool."
)

liquid_activate_orchestrator = Agent(
    name="LiquidActivateOrchestrator",
    model=os.environ.get("GOOGLE_GENAI_MODEL", "gemini-2.5-flash"),
    description="Orchestrator coordinating audience construction, scaling, sizing, profiling, and activation.",
    instruction=ROLE_DESCRIPTION,
    tools=[FunctionTool(build_audience_tool), FunctionTool(size_audience_tool), FunctionTool(activate_audience_tool), FunctionTool(profile_audience_tool)]
)

def get_agent_card(host: str, port: int) -> "AgentCard":
    from a2a.types import AgentCard, AgentSkill, AgentCapabilities, TransportProtocol
    skills = [
        AgentSkill(
            id='liquid-activation-internal-skill',
            name='Internal Cohort Sizing and Activation',
            description='Builds segments and calculates match sizes.',
            tags=['sizing', 'activation'],
            examples=['Size and activate Diet Pepsi segment.'],
        )
    ]
    return AgentCard(
        name='LiquidActivateOrchestrator',
        description='Orchestrator coordinating audience construction, scaling, and sizing.',
        url=f'http://{host}:{port}/',
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=False),
        skills=skills,
        preferred_transport=TransportProtocol.http_json,
    )
