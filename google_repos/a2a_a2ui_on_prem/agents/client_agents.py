import logging
import httpx
from typing import Dict, List, Any, Optional

logger = logging.getLogger("client_agents")

class ResolutionAgentClient:
    def __init__(
        self,
        product_hierarchy_url: str,
        product_entity_url: str,
        time_hierarchy_url: str,
        time_entity_url: str
    ):
        self.product_hierarchy_url = product_hierarchy_url
        self.product_entity_url = product_entity_url
        self.time_hierarchy_url = time_hierarchy_url
        self.time_entity_url = time_entity_url

    async def resolve_product_hierarchy(self, query: str, model_id: str) -> Dict[str, Any]:
        """Invokes the Product Hierarchy Resolution Agent."""
        payload = {"query": query, "model_id": model_id}
        logger.info(f"POST {self.product_hierarchy_url} | Payload: {payload}")
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(self.product_hierarchy_url, json=payload)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Product Hierarchy Output: {data}")
            return data

    async def resolve_time_hierarchy(self, query: str, model_id: str) -> Dict[str, Any]:
        """Invokes the Time Hierarchy Resolution Agent."""
        payload = {"query": query, "model_id": model_id}
        logger.info(f"POST {self.time_hierarchy_url} | Payload: {payload}")
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(self.time_hierarchy_url, json=payload)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Time Hierarchy Output: {data}")
            return data

    async def resolve_product_entity(self, query: str, model_id: str, hierarchy_id: str) -> Dict[str, Any]:
        """Invokes the Product Entity Resolution Agent."""
        payload = {"query": query, "model_id": model_id, "hierarchy_id": hierarchy_id}
        logger.info(f"POST {self.product_entity_url} | Payload: {payload}")
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(self.product_entity_url, json=payload)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Product Entity Output: {data}")
            return data

    async def resolve_time_entity(self, query: str, model_id: str, hierarchy_id: str) -> Dict[str, Any]:
        """Invokes the Time Entity Resolution Agent."""
        payload = {"query": query, "model_id": model_id, "hierarchy_id": hierarchy_id}
        logger.info(f"POST {self.time_entity_url} | Payload: {payload}")
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(self.time_entity_url, json=payload)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Time Entity Output: {data}")
            return data
