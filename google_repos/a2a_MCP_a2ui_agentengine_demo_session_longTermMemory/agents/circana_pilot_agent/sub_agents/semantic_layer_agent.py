import os
from google.adk.agents import Agent

ROLE_DESCRIPTION = (
    "You are the Circana Semantic Layer Agent. Your job is to perform entity resolution and ontology checks. "
    "Given a conversation context, list of candidate products, and user query (such as 'go with the top one'), "
    "you resolve the correct product name (e.g. 'Diet Pepsi 12pk') and return it as a clean JSON block."
)

semantic_layer_agent = Agent(
    name="SemanticLayerAgent",
    model=os.environ.get("GOOGLE_GENAI_MODEL", "gemini-2.5-flash"),
    description="Semantic Reasoning and Entity Resolution Agent.",
    instruction=ROLE_DESCRIPTION,
    tools=[]
)

def get_agent_card(host: str, port: int) -> "AgentCard":
    from a2a.types import AgentCard, AgentSkill, AgentCapabilities, TransportProtocol
    skills = [
        AgentSkill(
            id='semantic-layer-internal-skill',
            name='Entity Resolution and Ontology Mapping',
            description='Resolves relative text references to structured database entities.',
            tags=['semantic', 'entity-resolution'],
            examples=['Resolve top product from previous analysis.'],
        )
    ]
    return AgentCard(
        name='SemanticLayerAgent',
        description='Semantic Layer Agent performing shared ontology and entity resolution.',
        url=f'http://{host}:{port}/',
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=False),
        skills=skills,
        preferred_transport=TransportProtocol.http_json,
    )
