import sys
import json
import logging

# Set up logging to stderr so it doesn't corrupt stdout JSON-RPC stream
logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("circana_mcp_server")

def handle_list_tools():
    return {
        "tools": [
            {
                "name": "audience-build",
                "description": "Constructs a target shopper cohort segment from historical purchase data.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "product_name": {"type": "string", "description": "Name of the target product brand."},
                        "spend_criteria": {"type": "string", "description": "Segmentation criteria (e.g. lapsed, heavy)."}
                    },
                    "required": ["product_name"]
                }
            },
            {
                "name": "audience-size",
                "description": "Calculates target match sizing and reach metrics across activation channels.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "audience_id": {"type": "string", "description": "Audience ID returned by build-audience."},
                        "partner_options": {"type": "string", "description": "Comma-separated target channels."}
                    },
                    "required": ["audience_id"]
                }
            },
            {
                "name": "check-job-status",
                "description": "Checks status of an asynchronous MCP database query.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "job_id": {"type": "string", "description": "The Job ID to inspect."}
                    },
                    "required": ["job_id"]
                }
            },
            {
                "name": "audience-profile",
                "description": "Compiles demographic breakdown metrics for the target audience segment.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "audience_id": {"type": "string", "description": "The identifier of the audience segment."}
                    },
                    "required": ["audience_id"]
                }
            },
            {
                "name": "audience-activate",
                "description": "Validates compliance gates and activates the target audience segment across channels.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "audience_id": {"type": "string", "description": "The identifier of the audience segment."},
                        "partners": {"type": "string", "description": "Comma-separated target channels."}
                    },
                    "required": ["audience_id"]
                }
            }
        ]
    }

import os
import tempfile
import uuid

JOBS_FILE = os.path.join(tempfile.gettempdir(), "mcp_mock_jobs.json")

def _load_jobs() -> dict:
    if os.path.exists(JOBS_FILE):
        try:
            with open(JOBS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def _save_jobs(jobs: dict):
    try:
        with open(JOBS_FILE, "w") as f:
            json.dump(jobs, f)
    except Exception:
        pass

def handle_call_tool(name, arguments):
    logger.info(f"mcp_server: Calling tool {name} with args {arguments}")
    if name == "audience-build":
        product_name = arguments.get("product_name", "Selected Product")
        spend_criteria = arguments.get("spend_criteria", "lapsed")
        clean_name = product_name.upper().replace(' ', '-').replace("'", "")
        aud_id = f"AUD-{clean_name}-999"
        
        prod_lower = product_name.lower()
        if "pepsi" in prod_lower:
            shoppers = 350000
        elif "doritos" in prod_lower:
            shoppers = 280000
        elif "tomato" in prod_lower:
            shoppers = 410000
        elif "oreo" in prod_lower:
            shoppers = 190000
        elif "tea" in prod_lower:
            shoppers = 220000
        else:
            shoppers = 300000
            
        job_id = f"job_{uuid.uuid4().hex[:8]}"
        jobs = _load_jobs()
        jobs[job_id] = {
            "status": "Running",
            "progress": 0,
            "product_name": product_name,
            "spend_criteria": spend_criteria,
            "shoppers_isolated": shoppers,
            "aud_id": aud_id
        }
        _save_jobs(jobs)
        
        result = {
            "status": "Running",
            "job_id": job_id,
            "message": f"Query isolation request queued. Materializing shopper cohort database views for {product_name}..."
        }
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result, indent=2)
                }
            ]
        }
    elif name == "check-job-status":
        job_id = arguments.get("job_id")
        jobs = _load_jobs()
        if not job_id or job_id not in jobs:
            result = {
                "status": "Failed",
                "job_id": job_id or "unknown",
                "message": f"Job ID '{job_id}' not found in registry."
            }
        else:
            job = jobs[job_id]
            if job["status"] == "Running":
                job["progress"] += 40
                if job["progress"] >= 100:
                    job["status"] = "Completed"
                    job["result"] = {
                        "status": "Created",
                        "audience_id": job["aud_id"],
                        "product_name": job["product_name"],
                        "shoppers_isolated": job["shoppers_isolated"],
                        "message": f"Successfully materialized cohort for {job['product_name']} containing {job['shoppers_isolated']:,} shoppers."
                    }
                _save_jobs(jobs)
            result = {
                "job_id": job_id,
                "status": job["status"],
                "progress": min(job["progress"], 100),
                "message": f"Materializing database views ({min(job['progress'], 100)}% complete)...",
                "result": job.get("result")
            }
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result, indent=2)
                }
            ]
        }
    elif name == "audience-size":
        audience_id = arguments.get("audience_id", "AUD-DIET-PEPSI-999")
        partner_options = arguments.get("partner_options", "LiveRamp,Google")
        
        aud_id_upper = audience_id.upper()
        if "PEPSI" in aud_id_upper:
            p_name = "Diet Pepsi 12pk"
            original_size = 350000
            scaled_size = 1200000
            reach_pct = 85.0
        elif "DORITOS" in aud_id_upper:
            p_name = "Doritos Nacho Cheese 10oz"
            original_size = 280000
            scaled_size = 950000
            reach_pct = 78.0
        elif "TOMATO" in aud_id_upper:
            p_name = "Campbell's Tomato Soup 10.75oz"
            original_size = 410000
            scaled_size = 1400000
            reach_pct = 82.0
        elif "OREO" in aud_id_upper:
            p_name = "Oreo Double Stuf 15.35oz"
            original_size = 190000
            scaled_size = 650000
            reach_pct = 72.0
        elif "TEA" in aud_id_upper:
            p_name = "Lipton Iced Tea 64oz"
            original_size = 220000
            scaled_size = 780000
            reach_pct = 80.0
        else:
            p_name = "Selected Product"
            original_size = 300000
            scaled_size = 1000000
            reach_pct = 80.0
            
        result = {
            "audience_id": audience_id,
            "product_name": p_name,
            "original_size": original_size,
            "scaled_size": scaled_size,
            "reach_percentage": reach_pct,
            "partners": partner_options.split(",")
        }
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result, indent=2)
                }
            ]
        }
    else:
        raise ValueError(f"Unknown tool: {name}")

def main():
    logger.info("Circana MCP Tool Server started (listening on stdin).")
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            req = json.loads(line)
            req_id = req.get("id")
            method = req.get("method")
            params = req.get("params", {})
            
            # Initialization handshake
            if method == "initialize":
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": "circana-mcp-server",
                            "version": "1.0.0"
                        }
                    }
                }
            elif method == "tools/list":
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": handle_list_tools()
                }
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": handle_call_tool(tool_name, arguments)
                }
            else:
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
            
            # Print response to stdout
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            sys.stderr.flush()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--http", action="store_true", help="Run as HTTP Server")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="HTTP Server Host")
    parser.add_argument("--port", type=int, default=8080, help="HTTP Server Port")
    args = parser.parse_known_args()[0]
    
    if args.http:
        from fastapi import FastAPI, Request
        import uvicorn
        
        app = FastAPI(title="Circana MCP Server HTTP Mode")
        
        @app.get("/tools")
        def list_tools():
            return handle_list_tools()
            
        @app.post("/tools/call")
        async def call_tool(req: Request):
            body = await req.json()
            name = body.get("name")
            arguments = body.get("arguments", {})
            if not name and "params" in body:
                params = body["params"]
                name = params.get("name")
                arguments = params.get("arguments", {})
            
            logger.info(f"HTTP MCP: Calling tool {name} with args {arguments}")
            try:
                res = handle_call_tool(name, arguments)
                return {
                    "jsonrpc": "2.0",
                    "result": res
                }
            except Exception as e:
                logger.error(f"HTTP MCP Tool call error: {e}")
                return {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32603,
                        "message": str(e)
                    }
                }

        @app.post("/")
        async def handle_jsonrpc(req: Request):
            body = await req.json()
            method = body.get("method")
            req_id = body.get("id")
            params = body.get("params", {})
            
            logger.info(f"HTTP JSONRPC: method={method} | params={params}")
            
            if method == "initialize":
                result = {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "circana-mcp-server",
                        "version": "1.0.0"
                    }
                }
            elif method == "tools/list":
                result = handle_list_tools()
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                result = handle_call_tool(tool_name, arguments)
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
                
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": result
            }
                
        uvicorn.run(app, host=args.host, port=args.port)
    else:
        main()
