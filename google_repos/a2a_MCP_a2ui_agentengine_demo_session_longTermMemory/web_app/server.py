import sys
import os

# Disable mTLS client certificates to avoid pyOpenSSL context crashes on Google Linux workstations
os.environ["GOOGLE_API_USE_CLIENT_CERTIFICATE"] = "false"
os.environ["GOOGLE_API_USE_MTLS"] = "never"
sys.modules['OpenSSL'] = None
sys.modules['urllib3.contrib.pyopenssl'] = None

import uuid
import logging
import datetime
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables from parent directory .env
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "../.env")))

# Add agents/ directory to sys.path to resolve circana_pilot_agent
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../agents")))

from circana_pilot_agent.executor import CircanaPilotExecutor
from a2a.server.agent_execution import RequestContext
from a2a.server.events import EventQueue, EventConsumer
from a2a.types import Message, Role, TextPart, DataPart, Part

import vertexai
from google.genai import types
from google.api_core.exceptions import ResourceExhausted

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("web_app_server")

app = FastAPI(title="Circana Orchestrator Local Test Platform")

# Initialize Vertex AI & GenAI Client
project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", os.environ.get("PROJECT_ID", "shade-sandbox"))
location = os.environ.get("GOOGLE_CLOUD_LOCATION", os.environ.get("LOCATION", "us-central1"))
api_endpoint = f"{location}-aiplatform.googleapis.com"

vertexai.init(
    project=project_id,
    location=location,
    api_endpoint=api_endpoint
)

genai_client = vertexai.Client(
    project=project_id,
    location=location,
    http_options=types.HttpOptions(api_version="v1beta1")
)

agent_url = os.environ.get("PRICING_AGENT_URL")

class ChatRequest(BaseModel):
    message: str
    session_id: str
    attachments: Optional[List[str]] = None

class ActionRequest(BaseModel):
    action: Dict[str, Any]
    session_id: str

executor = CircanaPilotExecutor()

async def run_executor_turn(session_id: str, prompt_parts: List[Part]) -> Dict[str, Any]:
    from a2a.types import MessageSendParams
    task_id = str(uuid.uuid4())
    
    context = RequestContext(
        request=MessageSendParams(
            message=Message(
                message_id=str(uuid.uuid4()),
                role=Role.user,
                parts=prompt_parts
            )
        ),
        context_id=session_id,
        task_id=task_id
    )
    
    event_queue = EventQueue()
    
    # Run execution
    await executor.execute(context, event_queue)
    
    # Process events
    text_response = ""
    a2ui_widgets = []
    
    consumer = EventConsumer(event_queue)
    async for ev in consumer.consume_all():
        if ev.status and ev.status.state == 'completed' and ev.status.message:
            for part in ev.status.message.parts:
                if hasattr(part, 'root'):
                    root_val = part.root
                    if hasattr(root_val, 'text') and root_val.text:
                        text_response += root_val.text + "\n"
                    elif hasattr(root_val, 'data') and root_val.data:
                        a2ui_widgets.append(root_val.data)
                elif isinstance(part, dict):
                    if "text" in part:
                        text_response += part["text"] + "\n"
                    elif "data" in part:
                        a2ui_widgets.append(part["data"])
                    elif "root" in part:
                        root_part = part["root"]
                        if isinstance(root_part, dict):
                            if "text" in root_part:
                                text_response += root_part["text"] + "\n"
                            elif "data" in root_part:
                                a2ui_widgets.append(root_part["data"])
                        
    import re
    status = "Completed"
    job_id = None
    message = None
    
    if "status" in text_response and "job_id" in text_response:
        try:
            m = re.search(r'\{[^{}]*"status"\s*:\s*"Running"[^{}]*"job_id"\s*:\s*"([^"]+)"[^{}]*\}', text_response)
            if m:
                job_id = m.group(1)
                status = "Running"
                msg_m = re.search(r'"message"\s*:\s*"([^"]+)"', text_response)
                if msg_m:
                    message = msg_m.group(1)
        except Exception as pe:
            logger.error(f"Error parsing job details from response: {pe}")
            
    return {
        "text": text_response.strip(),
        "widgets": a2ui_widgets,
        "status": status,
        "job_id": job_id,
        "message": message
    }

@app.get("/api/sessions")
async def list_sessions():
    try:
        logger.info(f"Listing sessions for agent: {agent_url}")
        if not agent_url or "projects/" not in agent_url:
            return [
                {
                    "id": "local-session-1234",
                    "name": f"{agent_url}/sessions/local-session-1234",
                    "create_time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "user_id": "user"
                }
            ]
        sessions_page = genai_client.agent_engines.sessions.list(name=agent_url)
        sessions_list = []
        for s in sessions_page:
            session_id = s.name.split("/")[-1]
            sessions_list.append({
                "id": session_id,
                "name": s.name,
                "create_time": s.create_time.isoformat() if s.create_time else None,
                "user_id": s.user_id
            })
        # Sort sessions by create_time descending if available
        sessions_list.sort(key=lambda x: x["create_time"] or "", reverse=True)
        return sessions_list
    except Exception as e:
        logger.error(f"Error listing sessions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sessions")
async def create_session():
    try:
        logger.info(f"Creating session for agent: {agent_url}")
        if not agent_url or "projects/" not in agent_url:
            session_id = f"local-session-{str(uuid.uuid4())[:8]}"
            return {
                "id": session_id,
                "name": f"{agent_url}/sessions/{session_id}",
                "create_time": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
        operation = genai_client.agent_engines.sessions.create(
            name=agent_url,
            user_id="user"
        )
        session = operation.response
        session_id = session.name.split("/")[-1]
        return {
            "id": session_id,
            "name": session.name,
            "create_time": session.create_time.isoformat() if session.create_time else None
        }
    except Exception as e:
        logger.error(f"Error creating session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sessions/{session_id}")
async def get_session_history(session_id: str):
    try:
        if not agent_url or "projects/" not in agent_url:
            return []
        session_name = f"{agent_url}/sessions/{session_id}"
        logger.info(f"Fetching history events for session: {session_name}")
        events = genai_client.agent_engines.sessions.events.list(name=session_name)
        history = []
        for ev in events:
            role = "user" if ev.author == "user" else "assistant"
            text_parts = []
            widgets = []
            
            if ev.content and ev.content.parts:
                for part in ev.content.parts:
                    if hasattr(part, 'text') and part.text:
                        text_parts.append(part.text)
            
            # Extract widgets from custom_metadata if present
            if ev.event_metadata and ev.event_metadata.custom_metadata and "widgets" in ev.event_metadata.custom_metadata:
                widgets = ev.event_metadata.custom_metadata["widgets"]
                
            history.append({
                "role": role,
                "text": "\n".join(text_parts),
                "timestamp": ev.timestamp.isoformat() if ev.timestamp else None,
                "widgets": widgets
            })
        return history
    except Exception as e:
        logger.error(f"Error fetching session history for {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    try:
        if not agent_url or "projects/" not in agent_url:
            return {"status": "deleted"}
        session_name = f"{agent_url}/sessions/{session_id}"
        logger.info(f"Deleting session: {session_name}")
        genai_client.agent_engines.sessions.delete(name=session_name)
        return {"status": "deleted"}
    except Exception as e:
        logger.error(f"Error deleting session {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    try:
        logger.info(f"Received chat request for session {req.session_id}: {req.message}")
        
        prompt_parts = [Part(root=TextPart(text=req.message))]
        if req.attachments:
            for attachment_uri in req.attachments:
                prompt_parts.append(Part(root=TextPart(text=f"[User Attachment: {attachment_uri}]")))
                
        if not agent_url or "projects/" not in agent_url:
            result = await run_executor_turn(req.session_id, prompt_parts)
            return result
        session_name = f"{agent_url}/sessions/{req.session_id}"
        
        # 1. Append User Event
        try:
            genai_client.agent_engines.sessions.events.append(
                name=session_name,
                author="user",
                invocation_id=str(uuid.uuid4()),
                timestamp=datetime.datetime.now(datetime.timezone.utc),
                config={
                    "content": types.Content(
                        role="user",
                        parts=[types.Part(text=req.message)]
                    )
                }
            )
        except Exception as se:
            logger.error(f"Failed to append user message event to session: {se}")
            
        result = await run_executor_turn(req.session_id, prompt_parts)
        
        # 2. Append Agent Response Event
        try:
            genai_client.agent_engines.sessions.events.append(
                name=session_name,
                author="agent",
                invocation_id=str(uuid.uuid4()),
                timestamp=datetime.datetime.now(datetime.timezone.utc),
                config={
                    "content": types.Content(
                        role="model",
                        parts=[types.Part(text=result["text"])]
                    ),
                    "event_metadata": {
                        "custom_metadata": {
                            "widgets": result["widgets"]
                        }
                    }
                }
            )
        except Exception as se:
            logger.error(f"Failed to append agent response event to session: {se}")
            
        return result
    except ResourceExhausted as re:
        logger.error(f"Quota limits exceeded: {re}", exc_info=True)
        raise HTTPException(
            status_code=429,
            detail="⚠️ API Quota Exceeded: The system is receiving too many requests. Please wait a few seconds and try again."
        )
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/action")
async def action_endpoint(req: ActionRequest):
    try:
        logger.info(f"Received action request for session {req.session_id}: {req.action}")
        if not agent_url or "projects/" not in agent_url:
            result = await run_executor_turn(req.session_id, [Part(root=DataPart(data=req.action))])
            return result
        session_name = f"{agent_url}/sessions/{req.session_id}"
        
        # 1. Append Action click User Event
        try:
            click_desc = f"Clicked action: {req.action.get('actionId') or str(req.action)}"
            genai_client.agent_engines.sessions.events.append(
                name=session_name,
                author="user",
                invocation_id=str(uuid.uuid4()),
                timestamp=datetime.datetime.now(datetime.timezone.utc),
                config={
                    "content": types.Content(
                        role="user",
                        parts=[types.Part(text=click_desc)]
                    )
                }
            )
        except Exception as se:
            logger.error(f"Failed to append action click event to session: {se}")
            
        result = await run_executor_turn(req.session_id, [Part(root=DataPart(data=req.action))])
        
        # 2. Append Agent Response Event
        try:
            genai_client.agent_engines.sessions.events.append(
                name=session_name,
                author="agent",
                invocation_id=str(uuid.uuid4()),
                timestamp=datetime.datetime.now(datetime.timezone.utc),
                config={
                    "content": types.Content(
                        role="model",
                        parts=[types.Part(text=result["text"])]
                    ),
                    "event_metadata": {
                        "custom_metadata": {
                            "widgets": result["widgets"]
                        }
                    }
                }
            )
        except Exception as se:
            logger.error(f"Failed to append agent response event to session: {se}")
            
        return result
    except ResourceExhausted as re:
        logger.error(f"Quota limits exceeded: {re}", exc_info=True)
        raise HTTPException(
            status_code=429,
            detail="⚠️ API Quota Exceeded: The system is receiving too many requests. Please wait a few seconds and try again."
        )
    except Exception as e:
        logger.error(f"Error in action endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str):
    try:
        from circana_pilot_agent.tools import call_mcp_tool
        result = call_mcp_tool("check-job-status", {"job_id": job_id})
        return result
    except Exception as e:
        logger.error(f"Error checking status for job {job_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Fetch storage bucket name
storage = os.environ.get("STORAGE_BUCKET")

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        if not storage:
            raise HTTPException(status_code=500, detail="GCS storage bucket not configured (STORAGE_BUCKET environment variable must be set).")
            
        from google.cloud import storage as gcs_storage
        storage_client = gcs_storage.Client()
        bucket = storage_client.bucket(storage)
        
        blob_name = f"uploads/{uuid.uuid4()}_{file.filename}"
        blob = bucket.blob(blob_name)
        
        blob.upload_from_file(file.file, content_type=file.content_type)
        
        gcs_uri = f"gs://{storage}/{blob_name}"
        logger.info(f"Successfully uploaded {file.filename} to GCS: {gcs_uri}")
        
        return {
            "filename": file.filename,
            "gcs_uri": gcs_uri,
            "content_type": file.content_type
        }
    except Exception as e:
        logger.error(f"Failed to upload file to GCS: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Serve the static files from the static directory under the root URL
app.mount("/", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static"), html=True), name="static")

