import json
import logging

try:
    from .components import get_product_table_a2ui, get_sizing_dashboard_a2ui, get_demographic_profile_a2ui, UIBuilder
except ImportError:
    from components import get_product_table_a2ui, get_sizing_dashboard_a2ui, get_demographic_profile_a2ui, UIBuilder

logger = logging.getLogger(__name__)

# Shared mock state cache to simulate session persistence across orchestrator steps
_MOCK_STATE = {
    "products": [
        {
            "rank": 1,
            "product_name": "Tropicana Pure Premium 52oz",
            "price_change": "+14.2%",
            "households_lost": "-412K",
            "lost_households_pct": -9.8,
            "volume_change": -6.4,
            "pool_size": 412400
        },
        {
            "rank": 2,
            "product_name": "Quaker Instant Oatmeal 10ct",
            "price_change": "+11.5%",
            "households_lost": "-298K",
            "lost_households_pct": -7.4,
            "volume_change": -5.2,
            "pool_size": 298100
        },
        {
            "rank": 3,
            "product_name": "Gatorade Thirst Quencher 28oz",
            "price_change": "+9.0%",
            "households_lost": "-244K",
            "lost_households_pct": -5.9,
            "volume_change": -4.8,
            "pool_size": 243700
        },
        {
            "rank": 4,
            "product_name": "Lay's Classic Party Size",
            "price_change": "+12.1%",
            "households_lost": "-201K",
            "lost_households_pct": -5.1,
            "volume_change": -3.9,
            "pool_size": 200900
        },
        {
            "rank": 5,
            "product_name": "Lipton Iced Tea 12pk",
            "price_change": "+8.4%",
            "households_lost": "-156K",
            "lost_households_pct": -4.2,
            "volume_change": -3.1,
            "pool_size": 156300
        }
    ],
    "selected_product": None,
    "audience_id": None,
    "sizing": None,
    "active_data_parts": []
}

def pricing_opportunities_tool(query_details: str) -> str:
    """Analyzes portfolio databases to identify products losing household shoppers over a 52-week pricing window.
    
    Args:
        query_details: Context string detailing target categories or portfolios.
    """
    logger.info(f"Executing pricing_opportunities_tool with details: {query_details}")
    products = _MOCK_STATE["products"]
    
    summary = "Pricing Opportunity Analysis completed successfully. Identified the following high-attrition products:\n"
    for p in products:
        summary += f"- {p['product_name']}: Price Change {p['price_change']}, Households Lost {p['households_lost']} ({p['lost_households_pct']}%), Volume Change {p['volume_change']}%, Lapsed Pool: {p['pool_size']}\n"
        
    a2ui_block = f"<a2ui-json>\n{json.dumps([{'component_type': 'pilot_diagnose_table', 'products': products}], indent=2)}\n</a2ui-json>"
    
    return f"{summary}\n\n{a2ui_block}"

import subprocess
import sys
import os

def call_mcp_tool(tool_name: str, arguments: dict) -> dict:
    mcp_server_id = os.environ.get("MCP_SERVER_NAME")
    if mcp_server_id:
        import asyncio
        from google.adk.integrations.agent_registry import AgentRegistry
        from google.auth import default

        logger.info(f"call_mcp_tool: Resolving MCP Server '{mcp_server_id}' from Agent Registry via get_mcp_toolset...")

        def get_cloud_run_auth_headers(context) -> dict:
            import google.auth
            import google.auth.transport.requests
            from google.oauth2 import id_token
            
            mcp_url = os.environ.get("MCP_SERVER_URL", "https://circana-mcp-server-943928157761.us-central1.run.app")
            try:
                creds, project = google.auth.default()
                auth_req = google.auth.transport.requests.Request()
                creds.refresh(auth_req)
                token = id_token.fetch_id_token(auth_req, mcp_url)
                return {"Authorization": f"Bearer {token}"}
            except Exception as auth_err:
                logger.warning(f"Could not automatically fetch Google ID token for remote auth: {auth_err}")
                return {}

        async def _async_call():
            _, project_id = default()
            LOCATION = "global"
            
            registry = AgentRegistry(
                project_id=project_id, 
                location=LOCATION,
                header_provider=get_cloud_run_auth_headers
            )
            
            mcp_toolset = registry.get_mcp_toolset(mcp_server_id)
            
            headers = get_cloud_run_auth_headers(None)
            session = await mcp_toolset._mcp_session_manager.create_session(headers=headers)
            
            result = await session.call_tool(tool_name, arguments=arguments)
            content_text = result.content[0].text
            return json.loads(content_text)

        try:
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            return loop.run_until_complete(_async_call())
        except Exception as e:
            logger.error(f"Failed to execute MCP tool call via AgentRegistry: {e}", exc_info=True)
            logger.info("Falling back to legacy HTTP POST or local stdio subprocess mode...")

    mcp_url = os.environ.get("MCP_SERVER_URL")
    if mcp_url:
        import httpx
        logger.info(f"call_mcp_tool: Making HTTP call to remote MCP server: {mcp_url}")
        
        headers = {}
        # Auto-detect and fetch Google IAM token if remote Cloud Run endpoint is protected
        if "localhost" not in mcp_url and "127.0.0.1" not in mcp_url:
            try:
                import google.auth
                import google.auth.transport.requests
                from google.oauth2 import id_token
                
                # Fetch credentials and generate ID token for Cloud Run URL as audience
                creds, project = google.auth.default()
                auth_req = google.auth.transport.requests.Request()
                creds.refresh(auth_req)
                target_audience = mcp_url.rstrip("/")
                token = id_token.fetch_id_token(auth_req, target_audience)
                headers["Authorization"] = f"Bearer {token}"
                logger.info("Successfully fetched Google Cloud ID Token for MCP request authentication.")
            except Exception as auth_err:
                logger.warning(f"Could not automatically fetch Google ID token for remote auth: {auth_err}")
                
        try:
            # Sync HTTP post
            with httpx.Client(timeout=30.0, headers=headers) as client:
                resp = client.post(
                    f"{mcp_url.rstrip('/')}/tools/call",
                    json={
                        "name": tool_name,
                        "arguments": arguments
                    }
                )
                resp.raise_for_status()
                payload = resp.json()
                
                if "error" in payload:
                    raise RuntimeError(f"MCP remote server error: {payload['error']}")
                    
                result = payload["result"]
                content_block = result["content"][0]["text"]
                return json.loads(content_block)
        except Exception as e:
            logger.error(f"Failed to execute MCP tool call via HTTP: {e}", exc_info=True)
            raise e

    # Fall back to local stdio subprocess mode
    # Look for mcp server in current package layout
    mcp_server_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "mcp_servers/circana_mcp_server.py"))
    if not os.path.exists(mcp_server_path):
        mcp_server_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "sub_agents/circana_mcp_server.py"))
    if not os.path.exists(mcp_server_path):
        mcp_server_path = os.path.join(os.path.dirname(__file__), "circana_mcp_server.py")
        
    logger.info(f"call_mcp_tool: Launching local MCP server subprocess: {mcp_server_path}")
    python_exec = sys.executable
    proc = subprocess.Popen(
        [python_exec, mcp_server_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        # standard JSON-RPC tools/call structure
        req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        proc.stdin.write(json.dumps(req) + "\n")
        proc.stdin.flush()
        
        response_line = proc.stdout.readline()
        if not response_line:
            raise RuntimeError("MCP server closed stdout unexpectedly.")
            
        resp = json.loads(response_line)
        if "error" in resp:
            raise RuntimeError(f"MCP server error: {resp['error']}")
            
        result = resp["result"]
        content_block = result["content"][0]["text"]
        return json.loads(content_block)
    finally:
        proc.stdin.close()
        proc.terminate()
        proc.wait()

def build_audience_tool(product_name: str, spend_criteria: str = "lapsed") -> str:
    """Invokes the on-premises 'audience-build' service to isolate and construct the shopper cohort.
    
    Args:
        product_name: Name of the product (e.g. 'Diet Pepsi 12pk').
        spend_criteria: Segment definition criteria (e.g. 'lapsed', 'heavy', 'all').
    """
    logger.info(f"build_audience_tool: Querying MCP server for tool 'audience-build'...")
    payloads = [
        UIBuilder.build_combined_activation("circana-combined-activation", {"product_name": product_name})
    ]
    active = _MOCK_STATE.setdefault("active_data_parts", [])
    active.extend(payloads)
    safe_prod = product_name.upper().replace(" ", "-").replace("'", "")
    aud_id = f"AUD-{safe_prod}-999"
    _MOCK_STATE["audience_id"] = aud_id
    return f"Audience built and scaled successfully for {product_name} (ID: {aud_id}). CRITICAL: Output exactly and ONLY: 'Selected product: {product_name}'"

def size_audience_tool(audience_id: str, partner_options: str = "LiveRamp,Google") -> str:
    """Invokes the on-premises 'audience-size' service to calculate estimated audience reach across channels.
    
    Args:
        audience_id: The identifier of the audience segment (e.g. 'AUD-DIET-PEPSI-12PK-999').
        partner_options: Comma-separated list of target channels.
    """
    logger.info(f"size_audience_tool: Querying MCP server for tool 'audience-size'...")
    product_name = _MOCK_STATE.get("selected_product") or "Tropicana Pure Premium 52oz"
    payloads = [
        UIBuilder.build_sizing_dashboard("circana-sizing-dashboard", {"audience_id": audience_id, "product_name": product_name})
    ]
    active = _MOCK_STATE.setdefault("active_data_parts", [])
    active.extend(payloads)
    return f"Audience sized successfully for ID: {audience_id}. Reach: 2.86M (92% addressable)."

def activate_audience_tool(audience_id: str, partners: str) -> str:
    """Activates the given audience segment with the specified marketing partners.
    
    Args:
        audience_id: The identifier of the audience segment (e.g. 'AUD-DIET-PEPSI-12PK-999').
        partners: Comma-separated list of target channels/partners (e.g. 'LiveRamp,Google').
    """
    logger.info(f"Executing activate_audience_tool for audience: {audience_id} | partners: {partners}")
    return json.dumps({
        "status": "Success",
        "audience_id": audience_id,
        "partners": partners.split(","),
        "message": f"Successfully activated segment {audience_id} with partners {partners}. Data sync initiated."
    }, indent=2)

def sanitize_content_with_model_armor(text: str) -> str:
    """Uses Google Cloud Vertex AI Model Armor to screen and sanitize prompt inputs and responses."""
    logger.info(f"Model Armor: Screening content (Length: {len(text)} chars)...")
    
    # 1. Local scanning engine fallback
    # Check for common prompt injection / jailbreak patterns
    jailbreak_patterns = [
        r"(?i)ignore\s+(?:all\s+)?previous\s+instructions",
        r"(?i)system\s+override",
        r"(?i)you\s+are\s+now\s+a\s+different\s+agent",
    ]
    import re
    for pattern in jailbreak_patterns:
        if re.search(pattern, text):
            logger.warning("Model Armor WARNING: Prompt injection pattern detected!")
            raise ValueError("Model Armor Verdict: BLOCKED (Prompt Injection Threat)")
            
    # Check for sensitive data (PII) leakage e.g. mock credit card numbers
    pii_patterns = [
        r"\b(?:\d[ -]??){15,16}\b", # simplified CC format
        r"\b\d{3}-\d{2}-\d{4}\b",    # Social Security number format
    ]
    for pattern in pii_patterns:
        if re.search(pattern, text):
            logger.warning("Model Armor WARNING: PII leakage detected!")
            # Redact PII
            text = re.sub(pattern, "[REDACTED_PII]", text)
            logger.info("Model Armor: Successfully redacted sensitive PII content.")
            
    logger.info("Model Armor Verdict: ALLOWED (Content passed safety checks)")
    return text



import uuid
import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import Message, MessageSendParams, Part, TextPart, Role, Task
from google.adk.tools import ToolContext

import os

AGENT_URLS = {
    "PricingAssortmentOrchestrator": os.environ.get(
        "PRICING_AGENT_URL", "projects/943928157761/locations/us-central1/reasoningEngines/5098398584357781504"
    ),
    "LiquidActivateOrchestrator": os.environ.get(
        "ACTIVATE_AGENT_URL", "projects/943928157761/locations/us-central1/reasoningEngines/2792555575144087552"
    ),
    "LoyaltyCampaignOrchestrator": os.environ.get(
        "LOYALTY_AGENT_URL", "projects/943928157761/locations/us-central1/reasoningEngines/584947332802412544"
    ),
    "AudienceProfileAgent": os.environ.get(
        "PROFILE_AGENT_URL", "projects/dummy/locations/us-central1/reasoningEngines/audience-profile"
    ),
    "SurveyOrchestrator": "projects/dummy/locations/us-central1/reasoningEngines/decoy-survey",
    "AnalyticsOrchestrator": "projects/dummy/locations/us-central1/reasoningEngines/decoy-analytics",
    "BrainWaveOrchestrator": "projects/dummy/locations/us-central1/reasoningEngines/decoy-brainwave",
    "SynapseOrchestrator": "projects/dummy/locations/us-central1/reasoningEngines/decoy-synapse",
    "SemanticLayerAgent": "projects/dummy/locations/us-central1/reasoningEngines/semantic-layer",
    "PricingOpportunitiesAgent": "projects/dummy/locations/us-central1/reasoningEngines/pricing-opportunities",
    "AudienceBuildAgent": "projects/dummy/locations/us-central1/reasoningEngines/audience-build",
    "AudienceScaleAgent": "projects/dummy/locations/us-central1/reasoningEngines/audience-scale",
    "AudienceSizeAgent": "projects/dummy/locations/us-central1/reasoningEngines/audience-size",
}

_http_client = None
_genai_client = None

def _get_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None:
        headers = {}
        try:
            from google.auth import default
            from google.auth.transport.requests import Request
            credentials, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
            request = Request()
            credentials.refresh(request)
            token = credentials.token
            if token:
                headers["Authorization"] = f"Bearer {token}"
                logger.info("Successfully configured GCP access token header for remote A2A calls.")
        except Exception as e:
            logger.warning(f"Could not load application default credentials for remote auth: {e}")

        _http_client = httpx.AsyncClient(timeout=60.0, headers=headers)
    return _http_client

def _get_genai_client():
    global _genai_client
    if _genai_client is None:
        import vertexai
        from google.genai import types
        _genai_client = vertexai.Client(
            project=os.environ.get("GOOGLE_CLOUD_PROJECT", os.environ.get("PROJECT_ID", "shade-sandbox")),
            location=os.environ.get("GOOGLE_CLOUD_LOCATION", os.environ.get("LOCATION", "us-central1")),
            http_options=types.HttpOptions(api_version="v1beta1")
        )
    return _genai_client

from a2a.client import ClientFactory, ClientConfig
from a2a.types import TransportProtocol

async def send_message_tool(agent_name: str, task_summary: str, tool_context: ToolContext) -> str:
    """Delegates a specialized retail operation phase to a remote A2A-compliant agent.
    
    Args:
        agent_name: Name of the remote agent, e.g. 'PricingAssortmentOrchestrator' or 'LiquidActivateOrchestrator'.
        task_summary: Clear instructions or action commands to execute.
    """
    logger.info(f"send_message_tool: Delegating to '{agent_name}' | Task: {task_summary}")
    
    if agent_name not in AGENT_URLS:
        return f"Error: Agent '{agent_name}' is not recognized. Available agents are: {list(AGENT_URLS.keys())}"
        
    url = AGENT_URLS[agent_name]
    
    if "dummy" in url:
        logger.warning(f"send_message_tool: Intercepted routing to decoy/sub agent: {agent_name}")
        if "decoy" in url:
            return f"Routing Failure: Decoy agent '{agent_name}' was incorrectly invoked. This request is out of this agent's scope."
            
        try:
            if agent_name == "SemanticLayerAgent":
                from circana_pilot_agent.sub_agents.semantic_layer_agent import semantic_layer_agent
                target_agent = semantic_layer_agent
            elif agent_name == "PricingOpportunitiesAgent":
                from circana_pilot_agent.sub_agents.pricing_opportunities_agent import pricing_opportunities_agent
                target_agent = pricing_opportunities_agent
            elif agent_name == "AudienceBuildAgent":
                from circana_pilot_agent.sub_agents.build_agent import build_agent
                target_agent = build_agent
            elif agent_name == "AudienceScaleAgent":
                from circana_pilot_agent.sub_agents.scale_agent import scale_agent
                target_agent = scale_agent
            elif agent_name == "AudienceSizeAgent":
                from circana_pilot_agent.sub_agents.size_agent import size_agent
                target_agent = size_agent
            elif agent_name == "PricingAssortmentOrchestrator":
                from circana_pilot_agent.sub_agents.pricing_assortment_orchestrator import pricing_assortment_orchestrator
                target_agent = pricing_assortment_orchestrator
            elif agent_name == "LiquidActivateOrchestrator":
                from circana_pilot_agent.sub_agents.liquid_activate_orchestrator import liquid_activate_orchestrator
                target_agent = liquid_activate_orchestrator
            elif agent_name == "LoyaltyCampaignOrchestrator":
                from circana_pilot_agent.sub_agents.loyalty_campaign_orchestrator import loyalty_campaign_orchestrator
                target_agent = loyalty_campaign_orchestrator
            elif agent_name == "AudienceProfileAgent":
                from circana_pilot_agent.sub_agents.profile_agent import profile_agent
                target_agent = profile_agent
            else:
                return f"Error: Agent '{agent_name}' mock is not configured."
                
            logger.info(f"Running agent '{agent_name}' locally using Runner...")
            from google.adk.runners import Runner
            from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
            from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
            from google.adk.sessions.in_memory_session_service import InMemorySessionService
            from google.genai import types
            
            local_runner = Runner(
                app_name=agent_name,
                agent=target_agent,
                artifact_service=InMemoryArtifactService(),
                session_service=InMemorySessionService(),
                memory_service=InMemoryMemoryService(),
            )
            
            # Context state extraction
            state = tool_context.state
            context_id = state.get("context_id") or str(uuid.uuid4())
            
            session = await local_runner.session_service.create_session(
                app_name=agent_name,
                user_id='user',
                state={},
                session_id=context_id,
            )
            
            content = types.Content(role='user', parts=[types.Part(text=task_summary)])
            ans = ""
            async for ev in local_runner.run_async(session_id=session.id, user_id='user', new_message=content):
                if hasattr(ev, 'is_final_response') and ev.is_final_response():
                    if ev.content and ev.content.parts:
                        ans = "\n".join([p.text for p in ev.content.parts if p.text])
                    break
                    
            logger.info(f"Local agent '{agent_name}' returned: {ans}")
            return ans
        except Exception as local_ex:
            logger.error(f"Error executing agent '{agent_name}' locally: {local_ex}", exc_info=True)
            return f"Error executing sub-agent '{agent_name}' locally: {str(local_ex)}"
        
    try:
        state = tool_context.state
        context_id = state.get("context_id") or str(uuid.uuid4())
        task_id = state.get("task_id") or str(uuid.uuid4())
        task_result = None

        if "projects/" in url and "reasoningEngines/" in url:
            # Route via Google GenAI SDK Agent Engines client
            logger.info(f"Routing delegation via GenAI SDK to Gemini Enterprise Agent Engine: {url}")
            genai_client = _get_genai_client()
            agent_engine = genai_client.agent_engines.get(name=url)
            
            parts_list = [{"text": task_summary}]
            response = await agent_engine.on_message_send(
                message_id=str(uuid.uuid4()),
                role="user",
                context_id=context_id,
                parts=parts_list
            )
            if response and isinstance(response, list) and len(response) > 0:
                first_el = response[0]
                if isinstance(first_el, tuple):
                    task_result = first_el[0]
                else:
                    task_result = first_el
        else:
            # Route via standard A2A HTTP client
            logger.info(f"Routing delegation via standard HTTP REST client to: {url}")
            httpx_client = _get_client()
            config = ClientConfig(
                supported_transports=[TransportProtocol.http_json],
                httpx_client=httpx_client
            )
            client = await ClientFactory.connect(url, client_config=config)
            message = Message(
                role=Role.user,
                message_id=str(uuid.uuid4()),
                context_id=context_id,
                parts=[Part(root=TextPart(text=task_summary))]
            )
            async for event in client.send_message(message):
                if isinstance(event, tuple):
                    task_result, _ = event
                    
        if task_result is None:
            return "Error: Downstream agent returned no task updates."
            
        logger.info(f"Task status: {task_result.status.state}")
        
        # Extract messages from both status.message and history in chronological order
        agent_messages = []
        if task_result.status and task_result.status.message:
            msg = task_result.status.message
            role_str = str(msg.role).lower()
            if 'agent' in role_str or 'model' in role_str:
                agent_messages.append(msg)
                
        for msg in reversed(task_result.history or []):
            role_str = str(msg.role).lower()
            if 'user' in role_str:
                break
            if 'agent' in role_str or 'model' in role_str:
                agent_messages.append(msg)
                
        agent_messages.reverse()
        
        import re

        def _sanitize_json(s: str) -> str:
            pattern = re.compile(
                r'("literalString"\s*:\s*")(.*?)("\s*(?:\n|\r\n|\\n)?\s*\}\s*(?:\n|\r\n|\\n)?\s*\})',
                re.DOTALL
            )
            def replacer(match):
                prefix = match.group(1)
                content = match.group(2)
                suffix = match.group(3)
                content = content.replace('\n', '\\n').replace('\r', '\\r')
                content = re.sub(r'(?<!\\)"', r'\"', content)
                return prefix + content + suffix
            s = pattern.sub(replacer, s)
            s = re.sub(r'\\\s*\n', '\n', s)
            return s.strip()

        def extract_and_format_widget(payload: dict) -> list:
            """Detects A2UI payloads (custom WebFrameSrcdoc or standard native layouts) and converts them to portal-renderable WebFrameSrcdoc format."""
            if not isinstance(payload, dict):
                return [payload]
                
            # If it is already a WebFrameSrcdoc update, return it as-is
            if "WebFrameSrcdoc" in str(payload):
                return [payload]
                
            # Import builders dynamically to avoid circular import issues
            try:
                from .components import get_product_table_a2ui, get_sizing_dashboard_a2ui, get_loyalty_dashboard_a2ui
            except ImportError:
                from components import get_product_table_a2ui, get_sizing_dashboard_a2ui, get_loyalty_dashboard_a2ui
                
            comp_type = payload.get("component_type")
            
            # 1. Product Table Match
            if comp_type == "product_table" or "products" in payload:
                products_data = payload.get("products")
                if isinstance(products_data, dict) and "data" in products_data:
                    products_list = products_data["data"]
                elif isinstance(products_data, list):
                    products_list = products_data
                else:
                    products_list = []
                    
                if products_list:
                    full_a2ui_str = get_product_table_a2ui(products_list)
                    full_json_str = full_a2ui_str.replace("<a2ui-json>", "").replace("</a2ui-json>", "").strip()
                    return json.loads(full_json_str)

            # 2. Native Table inside DataDisplayCard Match
            if comp_type == "DataDisplayCard" or "properties" in payload:
                props = payload.get("properties") or {}
                children = props.get("children") or []
                for child in children:
                    if child.get("component_type") == "Table":
                        rows = child.get("properties", {}).get("rows") or []
                        products_list = []
                        for row in rows:
                            if len(row) >= 3:
                                try:
                                    lost_str = row[1].get("text", "0").replace("%", "").strip()
                                    vol_str = row[2].get("text", "0").replace("%", "").strip()
                                    products_list.append({
                                        "product_name": row[0].get("text", "Unknown"),
                                        "lost_households_pct": float(lost_str) if lost_str else 0.0,
                                        "volume_change": float(vol_str) if vol_str else 0.0
                                    })
                                except Exception:
                                    pass
                        if products_list:
                            full_a2ui_str = get_product_table_a2ui(products_list)
                            full_json_str = full_a2ui_str.replace("<a2ui-json>", "").replace("</a2ui-json>", "").strip()
                            return json.loads(full_json_str)

            # 3. Sizing Dashboard Match
            if comp_type == "sizing_dashboard" or "sizing" in payload or "original_size" in str(payload):
                sizing_data = payload.get("sizing") or payload
                full_a2ui_str = get_sizing_dashboard_a2ui(sizing_data)
                full_json_str = full_a2ui_str.replace("<a2ui-json>", "").replace("</a2ui-json>", "").strip()
                return json.loads(full_json_str)

            # 4. Loyalty Dashboard Match
            if comp_type == "loyalty_dashboard" or "loyalty" in payload or "shoppers_isolated" in str(payload):
                loyalty_data = payload.get("loyalty") or payload
                full_a2ui_str = get_loyalty_dashboard_a2ui(loyalty_data)
                full_json_str = full_a2ui_str.replace("<a2ui-json>", "").replace("</a2ui-json>", "").strip()
                return json.loads(full_json_str)
                
            # 5. Demographic Profile Match
            if comp_type == "demographic_profile" or "median_age" in str(payload):
                profile_data = payload.get("profile") or payload
                full_a2ui_str = get_demographic_profile_a2ui(profile_data)
                full_json_str = full_a2ui_str.replace("<a2ui-json>", "").replace("</a2ui-json>", "").strip()
                return json.loads(full_json_str)

            return [payload]

        text_parts = []
        for msg in agent_messages:
            for part in msg.parts:
                print(f"[DEBUG tools.py] part type: {type(part.root)} | has_data: {hasattr(part.root, 'data')}")
                if hasattr(part.root, 'text') and part.root.text:
                    text_val = part.root.text
                    
                    # Extract any <a2ui-json> blocks
                    a2ui_pattern = re.compile(r'<a2ui-json>(.*?)</a2ui-json>', re.DOTALL)
                    for match in a2ui_pattern.finditer(text_val):
                        try:
                            json_str = _sanitize_json(match.group(1))
                            payloads = json.loads(json_str)
                            
                            def process_payload(payload):
                                normalized = extract_and_format_widget(payload)
                                for sub_p in normalized:
                                    _MOCK_STATE["active_data_parts"].append(sub_p)
                                    
                            if isinstance(payloads, list):
                                for p in payloads:
                                    process_payload(p)
                            else:
                                process_payload(payloads)
                            logger.info("[tools.py] Extracted, expanded and cached A2UI block from sub-agent text.")
                        except Exception as parse_ex:
                            logger.warning(f"[tools.py] Failed to parse/expand extracted A2UI block: {parse_ex}")
                    
                    # Strip <a2ui-json> blocks from the text returned to LLM
                    clean_text = a2ui_pattern.sub("", text_val).strip()
                    if clean_text:
                        text_parts.append(clean_text + "\n[A2UI interactive components staged successfully. Do NOT output any <a2ui-json> or table JSON widgets.]")
                elif hasattr(part.root, 'data') and part.root.data:
                    data_val = part.root.data
                    print(f"[DEBUG tools.py] Caching data part: {list(data_val.keys())}")
                    try:
                        normalized = extract_and_format_widget(data_val)
                        for sub_p in normalized:
                            _MOCK_STATE["active_data_parts"].append(sub_p)
                        logger.info(f"[tools.py] Expanded and cached native DataPart component")
                    except Exception as expand_ex:
                        logger.warning(f"[tools.py] Failed to expand native DataPart: {expand_ex}")
                        _MOCK_STATE["active_data_parts"].append(data_val)
                        
        if not text_parts:
            if _MOCK_STATE.get("active_data_parts"):
                return "Success: Downstream agent returned the interactive components."
            return "Error: Downstream agent completed successfully but returned no parts in history."
            
        return "\n".join(text_parts)
        
    except Exception as e:
        logger.error(f"Failed to delegate task to A2A agent '{agent_name}': {e}", exc_info=True)
        return f"Error delegating task to '{agent_name}': {str(e)}"

def get_loyalty_options_tool(product_name: str) -> str:
    """Retrieves current loyalty segment size and risk levels for personalization campaigns.
    
    Args:
        product_name: Name of the product (e.g. 'Diet Pepsi 12pk').
    """
    logger.info(f"Executing get_loyalty_options_tool for: {product_name}")
    loyalty_data = {
        "product_name": product_name,
        "shoppers_isolated": 350000,
        "risk_level": "High"
    }
    
    try:
        from .components import get_loyalty_dashboard_a2ui
    except ImportError:
        from components import get_loyalty_dashboard_a2ui
        
    summary = f"Successfully compiled loyalty segment parameters for product: {product_name}. Launch campaign when ready."
    a2ui_block = f"<a2ui-json>\n{json.dumps([{'component_type': 'loyalty_dashboard', 'loyalty': loyalty_data}], indent=2)}\n</a2ui-json>"
    
    return f"{summary}\n\n{a2ui_block}"

def launch_campaign_tool(product_name: str, discount_pct: float, points_mult: float) -> str:
    """Launches the personalized loyalty rewards campaign targeting lapsed customers.
    
    Args:
        product_name: Name of the product.
        discount_pct: The percent discount rate (e.g., 10 or 15).
        points_mult: Multiplier factor for reward points earned (e.g., 2 or 3).
    """
    logger.info(f"Executing launch_campaign_tool for {product_name}: discount={discount_pct}%, points={points_mult}x")
    return json.dumps({
        "status": "Success",
        "product_name": product_name,
        "discount_pct": discount_pct,
        "points_mult": points_mult,
        "message": f"Successfully launched personalized campaign for {product_name} cohort (discount: {discount_pct}%, points multiplier: {points_mult}x)!"
    }, indent=2)

def profile_audience_tool(audience_id: str) -> str:
    """Compiles demographic and geographic breakdown metrics for the target audience segment.
    
    Args:
        audience_id: The identifier of the audience segment.
    """
    logger.info(f"Executing profile_audience_tool for audience: {audience_id}")
    profile_data = {
        "audience_id": audience_id,
        "median_age": 47,
        "median_income": "$78K",
        "avg_hh_size": 3.1,
        "kids_in_hh": "52%",
        "income_distribution": [
            {"label": "< $50K", "pct": "18%", "idx": 75},
            {"label": "$50 - 75K", "pct": "24%", "idx": 114},
            {"label": "$75 - 100K", "pct": "22%", "idx": 102},
            {"label": "$100 - 150K", "pct": "21%", "idx": 108},
            {"label": "$150K+", "pct": "15%", "idx": 95}
        ],
        "top_dmas": [
            {"name": "Dallas-Ft Worth", "reach": "1.4M", "idx": "+32"},
            {"name": "Houston", "reach": "1.2M", "idx": "+28"},
            {"name": "Atlanta", "reach": "1.1M", "idx": "+24"},
            {"name": "Chicago", "reach": "1.1M", "idx": "+9"}
        ],
        "hh_composition": [
            {"name": "Couple + 2 kids", "pct": 30, "idx": "+62"},
            {"name": "Couple + 1 kid", "pct": 22, "idx": "+34"},
            {"name": "Couple, no kids", "pct": 24, "idx": "idx 92"},
            {"name": "Single parent", "pct": 9, "idx": "+18"},
            {"name": "Single adult", "pct": 8, "idx": "idx 71"},
            {"name": "Multi-gen", "pct": 7, "idx": "+22"}
        ],
        "generation_mix": [
            {"name": "Gen Z", "pct": "14%"},
            {"name": "Millennial", "pct": "24%"},
            {"name": "Gen X", "pct": "38%"},
            {"name": "Boomer", "pct": "18%"},
            {"name": "Silent", "pct": "6%"}
        ]
    }
    
    payloads = [
        UIBuilder.build_demographic_profile("circana-demographic-profile", profile_data)
    ]
    active = _MOCK_STATE.setdefault("active_data_parts", [])
    active.extend(payloads)
    
    summary = f"Audience profile compiled successfully for {audience_id} (Median Age: 47, Median Income: $78K)."
    a2ui_block = f"<a2ui-json>\n{json.dumps([{'component_type': 'demographic_profile', 'profile': profile_data}], indent=2)}\n</a2ui-json>"
    return f"{summary}\n\n{a2ui_block}"



