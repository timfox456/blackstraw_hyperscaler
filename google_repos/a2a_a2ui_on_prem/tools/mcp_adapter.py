import logging
import httpx
from typing import Dict, Any, Optional

logger = logging.getLogger("mcp_adapter")

class MCPToolsAdapter:
    def __init__(self, base_url: str, client_id: str):
        self.base_url = base_url.rstrip("/")
        self.client_id = client_id
        # Standard headers for A2A and MCP tools compliance
        self.headers = {
            "X-Client-Id": self.client_id,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    async def get_audience_metadata(self) -> Dict[str, Any]:
        """Fetches the list of audience types and definition mappings."""
        url = f"{self.base_url}/v1/tools/get_audience_metadata"
        logger.info(f"GET {url} | Headers: {self.headers}")
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            logger.info(f"get_audience_metadata Response: {data}")
            return data

    async def create_size_batch(self, batch: Dict[str, Any]) -> Dict[str, Any]:
        """Submits a size batch with one or more audiences for processing (appends type=Size query parameter)."""
        url = f"{self.base_url}/v1/tools/create_size_batch?type=Size"
        payload = {
            "clientId": self.client_id,
            "batch": batch
        }
        logger.info(f"POST {url} | Payload keys: {list(payload.keys())} | Headers: {self.headers}")
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            logger.info(f"create_size_batch Response: {data}")
            return data

    async def get_batch_status(self, batch_id: str) -> Dict[str, Any]:
        """Polls the status of the size batch."""
        url = f"{self.base_url}/v1/tools/get_batch_status"
        params = {
            "batchId": batch_id
        }
        logger.info(f"GET {url} | Params: {params} | Headers: {self.headers}")
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            logger.info(f"get_batch_status Response: {data}")
            return data
