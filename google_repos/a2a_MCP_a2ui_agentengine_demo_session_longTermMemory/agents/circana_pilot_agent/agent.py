import os
import logging
from google.adk.agents import Agent
from google.adk.tools import FunctionTool, load_artifacts
from a2ui.schema.manager import A2uiSchemaManager
from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.common_modifiers import remove_strict_validation
from a2ui.schema.constants import VERSION_0_8

logger = logging.getLogger(__name__)

# Relative / absolute fallbacks for importing tools
try:
    from .tools import send_message_tool
except ImportError:
    from tools import send_message_tool

ROLE_DESCRIPTION = "You are the Circana AI Pilot Coordinator. Your job is to orchestrate a multi-agent retail analysis and activation pipeline. You delegate tasks to specialized remote agents via your send_message_tool, coordinate pricing analysis, shopper cohort building, match sizing, and segment activation."

WORKFLOW_DESCRIPTION = """
Follow these operational phases carefully:
Phase A: Pricing Assortment & Product Selection
1. When the user asks to identify products with high buyer attrition or lost households, delegate the analysis task to the remote agent "PricingAssortmentOrchestrator" by calling your send_message_tool.
2. The tool returns the analysis summary and stages the interactive A2UI components automatically. Do NOT output any <a2ui-json> tags or table JSON widgets yourself.
3. Stop and wait for user selection feedback.

Phase B: Audience Sizing and Activation Pipeline
4. When the user selects a product (e.g. from table callback button clicks), delegate the building and sizing sequence to the remote agent "LiquidActivateOrchestrator" by calling your send_message_tool.
5. When the user asks to size the audience or clicks "Yes, size it" (e.g. actionId 'size_audience'), delegate the sizing task to the remote agent "LiquidActivateOrchestrator" by calling your send_message_tool.
6. The tool returns the sizing metrics and stages the interactive A2UI components automatically. Do NOT output any <a2ui-json> tags or table JSON widgets yourself.
7. When the user asks for a demographic profile, audience breakdown, or demographic distribution, delegate the profiling task to the remote agent "AudienceProfileAgent" by calling your send_message_tool.
8. The tool returns the demographic profile <a2ui-json> XML block. You MUST copy and print this block exactly as-is verbatim to render the demographic profile dashboard.

Phase C: Target Channel Activation
6. When the user submits activation partners (e.g., clicking "Activate Audience Segment"), confirm that the export has been initiated successfully.

Phase D: Loyalty personalization campaign
7. When the user wants to customize or initiate a loyalty/rewards campaign for the selected cohort, delegate the task to the remote agent "LoyaltyCampaignOrchestrator" by calling your send_message_tool.
8. The tool returns the loyalty manager <a2ui-json> XML block. You MUST copy and print this block exactly as-is verbatim to render the loyalty campaign dashboard.
9. When the user launches the campaign (e.g., clicking "Launch Loyalty Campaign"), confirm that the campaign has been launched successfully.
"""

UI_DESCRIPTION = """
CRITICAL A2UI RULES:
- Always copy and print any <a2ui-json> tag block returned by your tools exactly as-is.
- NEVER generate, invent, or output any generic JSON table widgets (e.g. {"type": "table"}).
"""

def create_agent() -> Agent:
    schema_manager = A2uiSchemaManager(
        version=VERSION_0_8,
        catalogs=[
            BasicCatalog.get_config(
                version=VERSION_0_8,
                examples_path=os.path.join(
                    os.path.dirname(__file__), "examples/0.8"
                ),
            )
        ],
        schema_modifiers=[remove_strict_validation],
    )

    instruction = schema_manager.generate_system_prompt(
        role_description=ROLE_DESCRIPTION,
        workflow_description=WORKFLOW_DESCRIPTION,
        ui_description=UI_DESCRIPTION,
        include_schema=False,
        include_examples=False,
        validate_examples=False,
    )

    supervisor_agent = Agent(
        name="CircanaPilotSupervisor",
        model=os.environ.get("GOOGLE_GENAI_MODEL", "gemini-2.5-flash"),
        description="Root coordinator supervising the Circana multi-agent retail system.",
        instruction=instruction,
        tools=[
            load_artifacts,
            FunctionTool(send_message_tool)
        ]
    )

    return supervisor_agent

_root_agent = None

def get_agent() -> Agent:
    global _root_agent
    if _root_agent is None:
        _root_agent = create_agent()
    return _root_agent

root_agent = get_agent()

def get_agent_card(host: str, port: int) -> "AgentCard":
    from a2a.types import AgentCard, AgentSkill, AgentCapabilities, TransportProtocol
    skills = [
        AgentSkill(
            id='circana-pricing-opportunity-skill',
            name='Pricing Opportunity Analysis',
            description='Identifies portfolio products with buyer attrition due to 52-week price changes and returns an interactive A2UI cohort table.',
            tags=['pricing', 'attrition'],
            examples=['Identify products with buyer attrition due to price increases.'],
        ),
        AgentSkill(
            id='circana-cohort-activation-skill',
            name='Cohort Sizing and Activation',
            description='Materializes customer cohorts and calculates channel match sizing for LiveRamp and Google Ads.',
            tags=['cohort', 'activation', 'sizing'],
            examples=['Select cohort for Diet Pepsi 12pk and activate it.'],
        ),
        AgentSkill(
            id='circana-loyalty-campaign-skill',
            name='Loyalty Personalization Campaign',
            description='Configures and launches loyalty personalization rewards campaign for target customer cohorts.',
            tags=['loyalty', 'personalization', 'campaign'],
            examples=['Initiate loyalty rewards personalization campaign for Diet Pepsi cohort.'],
        ),
        AgentSkill(
            id='circana-decoy-survey-skill',
            name='Consumer Survey Planner',
            description='Designs consumer sentiment research surveys to measure brand awareness metrics.',
            tags=['survey', 'market-research'],
            examples=['Draft a brand health survey for soft drink categories.'],
        ),
        AgentSkill(
            id='circana-decoy-analytics-skill',
            name='Multi-Channel Attribution Analytics',
            description='Performs multi-channel media mix modeling and marketing cost attribution analysis.',
            tags=['analytics', 'attribution'],
            examples=['Calculate ROI for television advertising campaigns.'],
        ),
        AgentSkill(
            id='circana-decoy-brainwave-skill',
            name='Cognitive Ad Testing',
            description='Measures viewer cognitive response and emotional resonance to advertisement content.',
            tags=['brainwave', 'neuromarketing'],
            examples=['Analyze engagement score for pepsi teaser video.'],
        ),
        AgentSkill(
            id='circana-decoy-synapse-skill',
            name='Logistics Supply Chain Optimization',
            description='Minimizes shipping cost and optimizes warehouse distribution routing paths.',
            tags=['supply-chain', 'logistics'],
            examples=['Optimize supply route for Chicago distribution center.'],
        ),
    ]
    return AgentCard(
        name='CircanaPilotSupervisor',
        description='Expert A2UI agent coordinating retail portfolio pricing audits and customer segment activation pipelines.',
        url=f'http://{host}:{port}/',
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=True),
        skills=skills,
        preferred_transport=TransportProtocol.http_json,
    )

