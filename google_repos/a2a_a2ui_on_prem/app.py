import os
import logging
import asyncio
import json
import queue
import threading
from flask import Flask, Response, request, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

from agents.client_agents import ResolutionAgentClient
from tools.mcp_adapter import MCPToolsAdapter
from agents.orchestrator import LiquidActivationOrchestrator
from generate_a2ui_payload import generate_a2ui_json

# Load environment configuration
load_dotenv()

# Initialize root logging configurations
logging.basicConfig(level=logging.INFO)
for logger_name in ["orchestrator", "client_agents", "mcp_adapter"]:
    l = logging.getLogger(logger_name)
    l.setLevel(logging.INFO)

app = Flask(__name__)
CORS(app)

@app.route("/api/run")
def run_orchestrator():
    query = request.args.get("query")
    model_id = request.args.get("model_id", "7920")

    if not query:
        return "data: " + json.dumps({"type": "result", "success": False, "error": "Query parameter is required."}) + "\n\n", 400

    log_queue = queue.Queue()

    class QueueLogHandler(logging.Handler):
        def emit(self, record):
            msg = record.getMessage()
            log_msg = self.format(record)
            log_queue.put({"type": "log", "message": log_msg})
            
            # Map HTTP request stages to single or parallel active agent arrays
            if "Executing Phase 1" in msg:
                log_queue.put({
                    "type": "status",
                    "agent": [
                        "Product Hierarchy Resolver Agent",
                        "Time Hierarchy Resolver Agent"
                    ],
                    "desc": [
                        "Calling: https://analytics-dev.iriworldwide.com/poc/agent/product/hierarchy/v1/invoke",
                        "Calling: https://analytics-dev.iriworldwide.com/poc/agent/time/hierarchy/v1/invoke"
                    ]
                })
            elif "Executing Phase 2" in msg:
                log_queue.put({
                    "type": "status",
                    "agent": [
                        "Product Entity Resolver Agent",
                        "Time Entity Resolver Agent"
                    ],
                    "desc": [
                        "Calling: https://analytics-dev.iriworldwide.com/poc/agent/product/entity/v1/invoke",
                        "Calling: https://analytics-dev.iriworldwide.com/poc/agent/time/entity/v1/invoke"
                    ]
                })
            elif "Querying MCP audience metadata" in msg:
                log_queue.put({
                    "type": "status",
                    "agent": "MCP Audience Metadata Service",
                    "desc": "Calling: https://analytics-dev.iriworldwide.com/poc/mcp/tools/ldservices/v1/tools/get_audience_metadata"
                })
            elif "Submitting sizing batch" in msg:
                log_queue.put({
                    "type": "status",
                    "agent": "MCP Tools Sizing Service",
                    "desc": "Calling: https://analytics-dev.iriworldwide.com/poc/mcp/tools/ldservices/v1/tools/create_size_batch"
                })
            elif "Starting polling loop" in msg or "Polling Attempt" in msg:
                log_queue.put({
                    "type": "status",
                    "agent": "Sizing Status Checking",
                    "desc": "Calling: https://analytics-dev.iriworldwide.com/poc/mcp/tools/ldservices/v1/tools/get_batch_status"
                })

    log_handler = QueueLogHandler()
    log_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))

    loggers = [
        logging.getLogger("orchestrator"),
        logging.getLogger("client_agents"),
        logging.getLogger("mcp_adapter")
    ]
    for logger in loggers:
        logger.addHandler(log_handler)

    def run_orchestrator_thread():
        try:
            # Load variables
            product_hierarchy_url = os.getenv("PRODUCT_HIERARCHY_URL")
            product_entity_url = os.getenv("PRODUCT_ENTITY_URL")
            time_hierarchy_url = os.getenv("TIME_HIERARCHY_URL")
            time_entity_url = os.getenv("TIME_ENTITY_URL")
            mcp_base_url = os.getenv("MCP_TOOLS_BASE_URL")
            client_id = os.getenv("CLIENT_ID")
            
            # Google GenAI Config Reference
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
            location = os.getenv("GOOGLE_CLOUD_LOCATION")
            model = os.getenv("GOOGLE_GENAI_MODEL")
            use_vertex = os.getenv("GOOGLE_GENAI_USE_VERTEXAI")
            
            logger = logging.getLogger("orchestrator")
            logger.info(f"GenAI environment initialized - Project: '{project_id}' | Location: '{location}' | Model: '{model}' | Use Vertex: '{use_vertex}'")

            # Initialize clients
            agent_client = ResolutionAgentClient(
                product_hierarchy_url=product_hierarchy_url,
                product_entity_url=product_entity_url,
                time_hierarchy_url=time_hierarchy_url,
                time_entity_url=time_entity_url
            )
            mcp_client = MCPToolsAdapter(base_url=mcp_base_url, client_id=client_id)
            orchestrator = LiquidActivationOrchestrator(client=agent_client, mcp_client=mcp_client)

            # Execute turn
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(orchestrator.run_turn(query=query, model_id=model_id))
            loop.close()

            # Parse variables for A2UI rendering
            batch_payload = result.get("batch", {})
            audiences = batch_payload.get("audiences", [])
            audience = audiences[0] if audiences else {}

            batch_name = batch_payload.get("name", "Orchestrator A2A Sizing Batch")
            audience_name = audience.get("name", "a2a_sizing_audience")
            
            products = audience.get("audienceProducts", [])
            product_name = products[0].get("productName", "Product") if products else "Product"

            times = audience.get("audienceTimes", [])
            time_name = times[0].get("name", "Time") if times else "Time"

            measures = audience.get("audienceMeasures", [])
            measure_name = "Dollars > $0"
            if measures:
                m = measures[0]
                measure_name = f"{m.get('measureType', 'Dollars')} {m.get('operator', '>')} ${m.get('value', '0')}"

            # Resolve consumer count
            raw_count = result.get("audiences", [{}])[0].get("estimateConsumerCount")
            count_str = "7.33M"
            if raw_count is not None:
                try:
                    count_val = int(raw_count)
                    count_str = f"{count_val / 1_000_000:.2f}M"
                except ValueError:
                    count_str = str(raw_count)

            # Generate A2UI JSON payload
            a2ui_json = generate_a2ui_json(
                batch_name=batch_name,
                audience_name=audience_name,
                product_name=product_name,
                time_name=time_name,
                measure_name=measure_name,
                consumer_count_millions=count_str
            )

            log_queue.put({
                "type": "result",
                "success": True,
                "batch_id": result.get("id"),
                "a2ui_json": a2ui_json
            })

        except Exception as e:
            app.logger.exception("Orchestration turn thread failed:")
            log_queue.put({
                "type": "result",
                "success": False,
                "error": str(e)
            })
        finally:
            for logger in loggers:
                logger.removeHandler(log_handler)
            # Signal finished
            log_queue.put(None)

    # Start thread
    threading.Thread(target=run_orchestrator_thread).start()

    def generate_events():
        while True:
            try:
                item = log_queue.get(timeout=240.0)
                if item is None:
                    break
                yield f"data: {json.dumps(item)}\n\n"
            except queue.Empty:
                break

    return Response(generate_events(), mimetype="text/event-stream")

@app.route("/")
def serve_index():
    return send_from_directory("static", "index.html")

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory("static", path)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
