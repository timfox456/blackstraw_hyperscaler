import logging
import asyncio
import json
import uuid
from typing import Dict, Any, List, Optional
from agents.client_agents import ResolutionAgentClient
from tools.mcp_adapter import MCPToolsAdapter

logger = logging.getLogger("orchestrator")

class LiquidActivationOrchestrator:
    def __init__(self, client: ResolutionAgentClient, mcp_client: MCPToolsAdapter):
        self.client = client
        self.mcp_client = mcp_client

    def _resolve_measure_tuple(self, query: str) -> Dict[str, Any]:
        """Resolves the measureId, name, fullPath, and type from the query text using compact JSON serialization."""
        query_lower = query.lower()
        if "units" in query_lower or "unit sales" in query_lower:
            measure_data = {
                "id": "666048692",
                "name": "Unit Sales",
                "fullPath": "Measures.Product Purchase : FOLDER.Unit Sales",
                "measureType": "Units",
                "dimensionName": "Measures",
                "leaf": True
            }
            return {
                "measureType": "Units",
                "measureId": "666048692",
                "name": "Unit Sales",
                "fullPath": "Measures.Product Purchase : FOLDER.Unit Sales",
                "measureObj": json.dumps(measure_data, separators=(',', ':'))
            }
        elif "trips" in query_lower or "product trips" in query_lower:
            measure_data = {
                "id": "666048694",
                "name": "Product Trips",
                "fullPath": "Measures.Product Purchase : FOLDER.Shopper Dependent Measures.Product Trips",
                "measureType": "Trips",
                "dimensionName": "Measures",
                "leaf": True
            }
            return {
                "measureType": "Trips",
                "measureId": "666048694",
                "name": "Product Trips",
                "fullPath": "Measures.Product Purchase : FOLDER.Shopper Dependent Measures.Product Trips",
                "measureObj": json.dumps(measure_data, separators=(',', ':'))
            }
        else:
            # Default to Dollars
            measure_data = {
                "id": "666048709",
                "name": "Dollar Sales",
                "fullPath": "Measures.Household Groups.Dollar Sales",
                "measureType": "Dollars",
                "dimensionName": "Measures",
                "leaf": True
            }
            return {
                "measureType": "Dollars",
                "measureId": "666048709",
                "name": "Dollar Sales",
                "fullPath": "Measures.Household Groups.Dollar Sales",
                "measureObj": json.dumps(measure_data, separators=(',', ':'))
            }

    def _extract_entity_queries(self, query: str) -> tuple[str, str]:
        """Extracts the specific product concept and time concept from the user query."""
        query_lower = query.lower()
        prod_query = "COCA COLA CO LOW CALORIE SOFT DRINKS"
        time_query = "Latest 13 weeks"

        # Extract product query (text between 'for' and 'in')
        if "for " in query:
            start_idx = query.index("for ") + 4
            if " in the" in query:
                end_idx = query.index(" in the")
                prod_query = query[start_idx:end_idx].strip()
            elif " in " in query:
                end_idx = query.index(" in ")
                prod_query = query[start_idx:end_idx].strip()
            else:
                prod_query = query[start_idx:].strip()

        # Extract time query (text starting with 'latest' or 'weekly' or 'fiscal')
        for term in ["in the ", "in ", "latest ", "fiscal "]:
            if term in query_lower:
                idx = query_lower.index(term)
                offset = 0 if term in ["latest ", "fiscal "] else len(term)
                time_query = query[idx + offset:].strip()
                break

        logger.info(f"Parsed Entities from Query -> Product Concept: '{prod_query}' | Time Concept: '{time_query}'")
        return prod_query, time_query

    async def run_turn(self, query: str, model_id: str) -> Dict[str, Any]:
        logger.info(f"--- STARTING ACTIVATION ORCHESTRATION TURN for query: '{query}' | model_id: {model_id} ---")

        # 0. Extract clean entity sub-queries
        product_query, time_query = self._extract_entity_queries(query)

        # 1. Parallel Hierarchy Resolution (Phase 1)
        logger.info("Executing Phase 1: Parallel Hierarchy Resolution...")
        prod_hier_task = self.client.resolve_product_hierarchy(product_query, model_id)
        time_hier_task = self.client.resolve_time_hierarchy(time_query, model_id)
        
        prod_hier_res, time_hier_res = await asyncio.gather(prod_hier_task, time_hier_task)

        # Extract nested result block
        prod_result = prod_hier_res.get("result", {}) or {}
        time_result = time_hier_res.get("result", {}) or {}

        prod_hier_id = prod_result.get("hierarchy_id")
        time_hier_id = time_result.get("id")

        if not prod_hier_id:
            raise ValueError(f"Product hierarchy resolution returned empty/null ID: {prod_hier_id}. Full response: {prod_hier_res}")

        if not time_hier_id:
            raise ValueError(f"Time hierarchy resolution returned empty/null ID: {time_hier_id}. Full response: {time_hier_res}")

        logger.info(f"Hierarchy ID Results -> Product: {prod_hier_id} | Time: {time_hier_id}")

        # 2. Parallel Entity Resolution (Phase 2)
        logger.info("Executing Phase 2: Parallel Entity Resolution...")
        prod_entity_task = self.client.resolve_product_entity(product_query, model_id, prod_hier_id)
        time_entity_task = self.client.resolve_time_entity(time_query, model_id, time_hier_id)

        prod_entity_res, time_entity_res = await asyncio.gather(prod_entity_task, time_entity_task)

        # Extract nested result block
        prod_entity_result = prod_entity_res.get("result", {}) or {}
        time_entity_result = time_entity_res.get("result", {}) or {}

        prod_members = prod_entity_result.get("members", [])
        time_members = time_entity_result.get("members", [])

        if not prod_members:
            raise ValueError(f"Product entity resolution returned empty members. Full response: {prod_entity_res}")

        if not time_members:
            raise ValueError(f"Time entity resolution returned empty members. Full response: {time_entity_res}")

        logger.info(f"Resolved {len(prod_members)} product members and {len(time_members)} time members.")

        # 3. Resolve Audience Metadata from MCP tools
        logger.info("Querying MCP audience metadata...")
        metadata = await self.mcp_client.get_audience_metadata()
        
        # Resolve target audience type and definitionId
        audience_types = metadata.get("types", [])
        resolved_type = "Verified"
        resolved_definition_id = 1

        if audience_types:
            for t in audience_types:
                if t.get("type", "").lower() == "verified":
                    resolved_type = t.get("type")
                    definitions = t.get("definitions", [])
                    if definitions:
                        resolved_definition_id = definitions[0].get("definitionId", resolved_definition_id)
                    break

        logger.info(f"Resolved Audience Type: '{resolved_type}' | Definition ID: {resolved_definition_id}")

        # 4. Map entities to MCP Sizing Batch payload format
        audience_products = []
        for pm in prod_members:
            audience_products.append({
                "productId": pm.get("id"),
                "productName": pm.get("name"),
                "fullPath": pm.get("fullPath"),
                "productType": "Product"
            })

        audience_times = []
        for tm in time_members:
            # Construct timeObj JSON string with compact serialization
            time_obj = {
                "id": tm.get("id"),
                "name": tm.get("name"),
                "levelName": time_entity_result.get("levelId", "Year_444_12") or "Year_444_12",
                "dispLevelName": time_entity_result.get("levelName", "Year_444_12") or "Year_444_12",
                "fullPath": tm.get("fullPath")
            }
            audience_times.append({
                "timeId": tm.get("id"),
                "name": tm.get("name"),
                "fullPath": tm.get("fullPath"),
                "timeObj": json.dumps(time_obj, separators=(',', ':'))
            })

        # Resolve measure specs
        measure_specs = self._resolve_measure_tuple(query)
        audience_measures = [{
            "audienceType": resolved_type.lower(),
            "fullPath": measure_specs["fullPath"],
            "measureId": measure_specs["measureId"],
            "measureObj": measure_specs["measureObj"],
            "measureType": measure_specs["measureType"],
            "name": measure_specs["name"],
            "operator": ">",
            "value": "0"
        }]

        # Generate short unique suffix
        uuid_suffix = uuid.uuid4().hex[:8]

        # Construct batch definition
        batch_payload = {
            "audiences": [{
                "audienceAttribute": [],
                "audienceMeasures": audience_measures,
                "audienceProducts": audience_products,
                "audienceTimes": audience_times,
                "author": "Vijay Kallepalli",
                "changeFlag": "N",
                "definitionId": resolved_definition_id,
                "description": "a2a_sizing_batch_audience",
                "isBase": "true",
                "name": f"a2a_sizing_audience_{uuid_suffix}",
                "refreshType": "one-time",
                "scheduleId": "",
                "status": "draft",
                "type": resolved_type.lower()
            }],
            "author": "Vijay Kallepalli",
            "description": "Orchestrator A2A sizing run",
            "destinations": [],
            "mode": "size",
            "name": f"Orchestrator A2A Sizing Batch {uuid_suffix}",
            "refreshType": "one-time",
            "state": "Size-Estimate",
            "status": "draft"
        }

        # 5. Submit sizing batch
        logger.info("Submitting sizing batch to MCP server...")
        batch_res = await self.mcp_client.create_size_batch(batch_payload)
        batch_id = batch_res.get("id")

        if not batch_id:
            raise ValueError(f"Failed to create sizing batch. Response payload: {batch_res}")

        logger.info(f"Sizing batch created successfully. Batch ID: {batch_id}. Starting polling loop...")

        # 6. Polling loop: Poll every 10 seconds for 3 minutes (18 attempts)
        max_attempts = 18
        polling_interval = 10.0
        for attempt in range(1, max_attempts + 1):
            await asyncio.sleep(polling_interval)
            status_res = await self.mcp_client.get_batch_status(batch_id)
            batch_status = status_res.get("status")
            logger.info(f"Polling Attempt {attempt}/{max_attempts} | Batch Status: '{batch_status}'")

            if batch_status == "sized":
                logger.info("Batch successfully sized!")
                return status_res

        raise TimeoutError(f"Batch sizing timed out after {max_attempts * polling_interval} seconds.")
