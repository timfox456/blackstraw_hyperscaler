import os
import asyncio
import logging
from dotenv import load_dotenv
from agents.client_agents import ResolutionAgentClient
from tools.mcp_adapter import MCPToolsAdapter
from agents.orchestrator import LiquidActivationOrchestrator

# Configure logging to console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("run_activation_turn")

async def main():
    # Load .env file
    load_dotenv()

    model_id = os.getenv("MODEL_ID", "7920")
    
    # downstream URLs
    product_hierarchy_url = os.getenv("PRODUCT_HIERARCHY_URL")
    product_entity_url = os.getenv("PRODUCT_ENTITY_URL")
    time_hierarchy_url = os.getenv("TIME_HIERARCHY_URL")
    time_entity_url = os.getenv("TIME_ENTITY_URL")

    # MCP config
    mcp_base_url = os.getenv("MCP_TOOLS_BASE_URL")
    client_id = os.getenv("CLIENT_ID")

    logger.info("=" * 80)
    logger.info("CIRCANA MULTI-AGENT A2A ACTIVATION RUNNER")
    logger.info("=" * 80)
    logger.info(f"Model ID: {model_id}")
    logger.info(f"Client ID: {client_id}")
    logger.info(f"Product Hierarchy Endpoint: {product_hierarchy_url}")
    logger.info(f"Time Hierarchy Endpoint: {time_hierarchy_url}")
    logger.info(f"MCP Base Endpoint: {mcp_base_url}")
    logger.info("=" * 80)

    # Initialize clients
    agent_client = ResolutionAgentClient(
        product_hierarchy_url=product_hierarchy_url,
        product_entity_url=product_entity_url,
        time_hierarchy_url=time_hierarchy_url,
        time_entity_url=time_entity_url
    )
    mcp_client = MCPToolsAdapter(base_url=mcp_base_url, client_id=client_id)

    # Initialize orchestrator
    orchestrator = LiquidActivationOrchestrator(client=agent_client, mcp_client=mcp_client)

    # Use the exact query that yields valid IDs in client's curl examples
    test_query = "Create a verified audience sizing Dollar Sales > 0 for COCA COLA CO LOW CALORIE SOFT DRINKS in the latest 13 weeks"

    try:
        result = await orchestrator.run_turn(query=test_query, model_id=model_id)
        logger.info("\n" + "=" * 80)
        logger.info("ORCHESTRATION TURN COMPLETED SUCCESSFULLY!")
        logger.info("=" * 80)
        logger.info(f"Batch Sizing Result Payload:\n{result}")
        logger.info("=" * 80)
    except Exception as e:
        logger.exception("Orchestration turn failed with an exception:")

if __name__ == "__main__":
    asyncio.run(main())
