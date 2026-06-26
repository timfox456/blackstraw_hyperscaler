# Circana GCP Deployment Guide

*How we deployed the Google-supplied Circana repos to GCP — context, commands, gotchas, and current live state.*
*Written to enable any engineer to pick up and continue this work in a new session.*

---

## 1. Environment Overview

### GCP Project

| Field | Value |
|-------|-------|
| **Project ID** | `gemini-enterprise-app-499621` |
| **Project Number** | `413407391500` |
| **Region** | `us-central1` |
| **Gemini Enterprise Console** | https://console.cloud.google.com/gemini-enterprise/locations/us/engines/gemini-enterprise-17818916_1781891684996/overview/dashboard?project=gemini-enterprise-app-499621 |

### Local Machine

| Field | Value |
|-------|-------|
| **Machine** | Blackstraw MacBook (macOS, Apple Silicon) |
| **Working directory** | `/Users/tim.fox/blackstraw/a2a_MCP_a2ui_agentengine_demo_session_longTermMemory` |
| **Python version** | 3.13.12 (venv pinned to 3.13 for local; deploy targets 3.10 in Docker) |
| **gcloud (standalone)** | `/Users/tim.fox/google-cloud-sdk/bin/gcloud` |
| **gcloud (homebrew)** | `/opt/homebrew/share/google-cloud-sdk/bin/gcloud` |
| **gcloud version** | 573.0.0 |

> **Note:** gcloud is not on the default `$PATH`. Always prefix commands:
> ```bash
> export PATH="/Users/tim.fox/google-cloud-sdk/bin:$PATH"
> ```
> Or add permanently to `~/.zshrc`.

### GCP Access

| Person | Email | Role on Project |
|--------|-------|-----------------|
| Tim Fox (Blackstraw) | tim.fox@blackstraw.ai | `roles/editor` + `roles/run.admin` + `roles/run.invoker` |
| Project Owner | anuranjan.mondal@blackstraw.ai | `roles/owner` |
| Project Owner | avinash.patel@blackstraw.ai | `roles/owner` |
| Project Owner | rishabh.mendiratta@blackstraw.ai | `roles/owner` |

> **IAM Note:** `roles/editor` is NOT sufficient alone. You also need:
> - `roles/run.admin` — to manage Cloud Run IAM policies and toggle public/private access
> - `roles/run.invoker` — to call authenticated Cloud Run services with your identity token
>
> Ask a project owner to grant these if missing.

---

## 2. Repos

| Repo | Path | Purpose |
|------|------|---------|
| **Cloud (ADK + Agent Engine)** | `/Users/tim.fox/blackstraw/a2a_MCP_a2ui_agentengine_demo_session_longTermMemory` | Supervisor + sub-agents on Vertex AI + MCP server + FastAPI portal |
| **On-prem (IRI orchestration)** | `/Users/tim.fox/blackstraw/a2a_a2ui_on_prem` | IRI entity resolution + audience sizing pipeline + Flask portal |

---

## 3. What Is Currently Live on GCP

### Cloud Run Services

| Service | URL | Auth |
|---------|-----|------|
| **Circana Portal** | https://circana-portal-c3i2rix2qq-uc.a.run.app | Public (allow-unauthenticated) |
| **MCP Server** | https://circana-mcp-server-c3i2rix2qq-uc.a.run.app | Requires `roles/run.invoker` |

### Vertex AI Reasoning Engines (Circana — currently active)

| Agent | Resource Name |
|-------|--------------|
| `pricing_assortment_orchestrator` | `projects/413407391500/locations/us-central1/reasoningEngines/7143683726067630080` |
| `liquid_activate_orchestrator` | `projects/413407391500/locations/us-central1/reasoningEngines/4518085143310630912` |
| `loyalty_campaign_orchestrator` | `projects/413407391500/locations/us-central1/reasoningEngines/5295519028985462784` |
| `audience_profile_agent` | `projects/413407391500/locations/us-central1/reasoningEngines/6121366610654527488` |

> **Note:** There are duplicate engine entries from previous deployment runs. The `.env` file contains the correct (most recently deployed) resource names above. Older duplicate engines are not referenced by `.env` and can be cleaned up.

---

## 4. Cloud Repo — Architecture

```
Browser
  │
  ▼
Cloud Run: circana-portal (web_app/server.py — FastAPI)
  │
  ├── send_message_tool ──► Vertex AI Reasoning Engine: pricing_assortment_orchestrator
  ├── send_message_tool ──► Vertex AI Reasoning Engine: liquid_activate_orchestrator
  ├── send_message_tool ──► Vertex AI Reasoning Engine: loyalty_campaign_orchestrator
  └── send_message_tool ──► Vertex AI Reasoning Engine: audience_profile_agent
                                          │
                                          └── call_mcp_tool ──► Cloud Run: circana-mcp-server
                                                                  (mock data — audience-build,
                                                                   audience-size, audience-profile,
                                                                   audience-activate, check-job-status)
```

### Key Files

| File | Purpose |
|------|---------|
| `agents/circana_pilot_agent/agent.py` | Supervisor agent definition + system prompt |
| `agents/circana_pilot_agent/executor.py` | `CircanaPilotExecutor` — bridges A2A to ADK Runner |
| `agents/circana_pilot_agent/tools.py` | `send_message_tool`, `call_mcp_tool`, mock `_MOCK_STATE` |
| `agents/circana_pilot_agent/components.py` | 9 A2UI HTML widget templates |
| `agents/circana_pilot_agent/mcp_servers/circana_mcp_server.py` | MCP server (runs on Cloud Run) |
| `agents/circana_pilot_agent/local_mocks/` | Local dev mock layer (Ollama, in-memory session, GCS, MCP) |
| `web_app/server.py` | FastAPI portal (sessions, chat, action callbacks) |
| `deploy.py` | Deploys 4 Reasoning Engines in parallel via `concurrent.futures` |
| `deploy_mcp.py` | Deploys MCP server to Cloud Run |
| `run_local.py` | Runs portal locally with `LOCAL_MODE=true` (no GCP) |
| `setup_gcp.sh` | One-time GCP setup: enables APIs, creates GCS bucket, sets IAM |
| `test_gcp.py` | Tests all 3 layers against live GCP services |
| `.env` | All config — GCP project, agent URLs, MCP URL |
| `pytest.ini` | Test config — markers: unit, integration, slow |
| `tests/unit/` | 73 unit tests (no GCP required) |
| `tests/integration/` | 14 integration tests (requires gcloud auth) |

---

## 5. Step-by-Step: How We Deployed Everything

### Prerequisites (do once)

```bash
# 1. Add gcloud to PATH (add to ~/.zshrc to make permanent)
export PATH="/Users/tim.fox/google-cloud-sdk/bin:$PATH"

# 2. Authenticate gcloud (browser-based, opens browser)
gcloud auth login

# 3. Set Application Default Credentials (needed for deploy.py / vertexai SDK)
gcloud auth application-default login

# 4. Set project
gcloud config set project gemini-enterprise-app-499621
```

### Step 1: Create Python virtualenv

```bash
cd /Users/tim.fox/blackstraw/a2a_MCP_a2ui_agentengine_demo_session_longTermMemory

# Create venv with Python 3.13 (use 3.13 for local; deploy.py targets Python 3.10 in cloud)
uv venv .venv --python 3.13
source .venv/bin/activate

# Install deps
uv pip install -r requirements.txt
```

### Step 2: One-time GCP setup (only needed on fresh project)

```bash
# Enables APIs, creates GCS staging bucket, grants IAM roles
source setup_gcp.sh
```

This script:
- Sets project to `gemini-enterprise-app-499621`
- Enables: `aiplatform`, `discoveryengine`, `run`, `storage`, `cloudbuild`, `iam`
- Creates GCS bucket: `gs://gemini-enterprise-app-499621-agent-stage`
- Grants IAM roles to the active gcloud user

> **Gotcha:** `setup_gcp.sh` calls `gcloud projects add-iam-policy-binding` which requires `resourcemanager.projects.setIamPolicy`. If you don't have this permission (Editor role doesn't include it), the IAM grants will fail silently. Have a Project Owner run it instead.

### Step 3: Deploy MCP server to Cloud Run

```bash
# From the repo root
python deploy_mcp.py
```

What it does:
1. Copies `Dockerfile.mcp` → `Dockerfile` (gcloud requires the file be named `Dockerfile`)
2. Runs `gcloud run deploy circana-mcp-server --source . --port 8080 --region us-central1 --no-allow-unauthenticated --clear-base-image --quiet`
3. Fetches the resulting service URL
4. Writes `MCP_SERVER_URL=<url>` back to `.env`
5. Cleans up the temporary `Dockerfile`

> **Gotcha encountered:** The original `deploy_mcp.py` called `sys.exit()` on any error, which closed the terminal. We rewrote it to use `return 1` instead. The rewrite is in the repo.

> **Gotcha encountered:** `gcloud run deploy` without `--clear-base-image` prompts interactively to select a base image. Added `--clear-base-image` flag to suppress this.

**Verify:**
```bash
curl -s -w "HTTP: %{http_code}" https://circana-mcp-server-c3i2rix2qq-uc.a.run.app/
# Expect HTTP 405 (POST only — service is up)

TOKEN=$(gcloud auth print-identity-token)
curl -s -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"audience-build","arguments":{"product_name":"Pepsi"}}}' \
     https://circana-mcp-server-c3i2rix2qq-uc.a.run.app/tools/call
# Expect JSON with status: "Completed", audience_id, shoppers_isolated
```

### Step 4: Deploy 4 sub-agents to Vertex AI

```bash
# From the repo root (deploy.py will cd into agents/ internally)
source .venv/bin/activate
python deploy.py
```

What it does:
1. `vertexai.init()` with `staging_bucket=gs://gemini-enterprise-app-499621-agent-stage`
2. Creates a `vertexai.Client` with API version `v1beta1`
3. Uses `concurrent.futures.ThreadPoolExecutor(max_workers=4)` to deploy all 4 agents in parallel
4. Each agent is packaged via `client.agent_engines.create(agent=A2aAgent(...), config=...)` with:
   - Python requirements (ADK 1.31, google-genai 1.73.1, a2a-sdk 0.3.26, etc.)
   - `extra_packages=["circana_pilot_agent"]` (the entire agent package)
   - `env_vars` including `MCP_SERVER_URL` from `.env`
5. Writes the 4 resource names back to `.env` as `PRICING_AGENT_URL`, `ACTIVATE_AGENT_URL`, `LOYALTY_AGENT_URL`, `PROFILE_AGENT_URL`

**Expected duration:** ~5 minutes (parallel)

> **Gotcha encountered:** Original `.env` had `GOOGLE_CLOUD_LOCATION=us` (Gemini Enterprise console uses `us`). `deploy.py` needs `us-central1` for Vertex AI APIs. We updated `.env` to `us-central1`.

> **Gotcha encountered:** `deploy.py` requires Application Default Credentials (`gcloud auth application-default login`), not just `gcloud auth login`. The SDK uses ADC for `vertexai.init()`.

**Verify:**
```bash
ACCESS_TOKEN=$(gcloud auth print-access-token)
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://us-central1-aiplatform.googleapis.com/v1beta1/projects/gemini-enterprise-app-499621/locations/us-central1/reasoningEngines" \
  | python3 -c "import sys,json; [print(e.get('displayName'), e.get('name')) for e in json.load(sys.stdin).get('reasoningEngines',[])]"
# Should show 4 Circana engines + other POC engines
```

### Step 5: Deploy the portal to Cloud Run

```bash
# Copy the portal Dockerfile to root (gcloud requires it named 'Dockerfile')
cp Dockerfile.portal Dockerfile

gcloud run deploy circana-portal \
  --source . \
  --region us-central1 \
  --project gemini-enterprise-app-499621 \
  --allow-unauthenticated \
  --clear-base-image \
  --quiet

# Clean up
rm Dockerfile
```

> **Note:** Portal is deployed with `--allow-unauthenticated` (public) for demo purposes.

**Verify:**
```bash
curl -s https://circana-portal-c3i2rix2qq-uc.a.run.app/api/sessions
# Expect: []

curl -s -X POST -H "Content-Type: application/json" \
  -d '{"message":"Identify pricing opportunities in soft drinks","session_id":"test-1"}' \
  https://circana-portal-c3i2rix2qq-uc.a.run.app/api/chat \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('Status:', d.get('status')); print('Widgets:', len(d.get('widgets',[])))"
# Expect: Status: Completed, Widgets: 2+
```

---

## 6. Running Tests

### Unit tests (no GCP required)

```bash
source .venv/bin/activate
export PATH="/Users/tim.fox/google-cloud-sdk/bin:$PATH"

python -m pytest tests/unit -v
# 73 tests, all should pass
```

### Integration tests (requires gcloud auth + live GCP)

```bash
source .venv/bin/activate
export PATH="/Users/tim.fox/google-cloud-sdk/bin:$PATH"

# Ensure ADC is valid (refresh if expired)
gcloud auth application-default login

python -m pytest tests/integration -v
# 14 tests
# - 6 MCP Cloud Run tests pass
# - 2 MCP tests are xfail (audience-profile, audience-activate not in deployed MCP version)
# - 5 Reasoning Engine tests pass (1 marked slow)
# - Portal E2E skips if portal not running on :8000
```

### Full test suite including live GCP test script

```bash
python test_gcp.py --layer all
# Tests: MCP endpoint, Reasoning Engines list, portal E2E
```

---

## 7. Local Development (No GCP)

```bash
source .venv/bin/activate

# Ensure Ollama is running with a model
brew install ollama           # if not installed
ollama pull llama3.2:latest
ollama serve &

# Set local mode
cp .env.local.example .env    # if .env doesn't exist, or edit .env to set LOCAL_MODE=true

# Run portal locally
python run_local.py
# Open http://localhost:8000
```

### LOCAL_MODE behaviour

When `LOCAL_MODE=true` in `.env`:

| Production component | Local replacement |
|---------------------|-------------------|
| Vertex AI Gemini | Ollama (`http://localhost:11434`) |
| Vertex AI Agent Engine | ADK `InMemorySessionService` + local `Runner` |
| Cloud Run MCP server | `local_mocks/local_mcp_server.py` (fake data) |
| GCS file storage | `local_mocks/local_gcs.py` (local filesystem) |
| `send_message_tool` → remote agents | Routes to local ADK Runner in-process |

---

## 8. On-Prem Repo — IRI Integration

### What it does

A standalone 6-file Python pipeline (~880 LOC) that:
1. Resolves product/time concepts against live IRI Liquid Data APIs
2. Queries audience metadata
3. Submits a sizing batch and polls until `status: "sized"`
4. Generates an A2UI HTML batch details card

### IRI Endpoints (all accessible without VPN from Blackstraw laptop)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `https://analytics-dev.iriworldwide.com/poc/agent/product/hierarchy/v1/invoke` | POST | Resolve product hierarchy ID |
| `https://analytics-dev.iriworldwide.com/poc/agent/time/hierarchy/v1/invoke` | POST | Resolve time hierarchy ID |
| `https://analytics-dev.iriworldwide.com/poc/agent/product/entity/v1/invoke` | POST | Resolve product member ID |
| `https://analytics-dev.iriworldwide.com/poc/agent/time/entity/v1/invoke` | POST | Resolve time member ID |
| `https://analytics-dev.iriworldwide.com/poc/mcp/tools/ldservices/v1/tools/get_audience_metadata` | GET | Get audience types + definition IDs |
| `https://analytics-dev.iriworldwide.com/poc/mcp/tools/ldservices/v1/tools/create_size_batch?type=Size` | POST | Submit sizing batch |
| `https://analytics-dev.iriworldwide.com/poc/mcp/tools/ldservices/v1/tools/get_batch_status` | GET | Poll batch status |

**Auth:** `X-Client-Id: e8d2abd2-ad45-4f49-9a48-a090349af1c7` header (in `.env` as `CLIENT_ID`)

### Running it

```bash
cd /Users/tim.fox/blackstraw/a2a_a2ui_on_prem
source .venv/bin/activate   # or: /Users/tim.fox/blackstraw/a2a_a2ui_on_prem/.venv/bin/activate

# CLI test (full pipeline, ~60-90s)
python run_activation_turn.py
# Expect: ORCHESTRATION TURN COMPLETED SUCCESSFULLY! + estimateConsumerCount: 7332992

# Flask portal (interactive UI)
python app.py
# Open http://localhost:8080
# Query: "Create a verified audience sizing Dollar Sales > 0 for COCA COLA CO LOW CALORIE SOFT DRINKS in the latest 13 weeks"
```

### Query format

```
Create a verified audience sizing <MEASURE> > 0 for <PRODUCT> in the <TIME>
```

Parser extracts:
- **Product** = text between `"for "` and `" in the"` or `" in "`
- **Time** = text after `"in the "` or `"latest "`
- **Measure** = keyword match in full query: `units`/`unit sales` → Units, `trips`/`product trips` → Trips, else → Dollars

**Validated working queries:**
```
Create a verified audience sizing Dollar Sales > 0 for COCA COLA CO LOW CALORIE SOFT DRINKS in the latest 13 weeks
Create a verified audience sizing Dollar Sales > 0 for PEPSI COLA in the latest 26 weeks
Create a verified audience sizing Unit Sales > 0 for COCA COLA CO LOW CALORIE SOFT DRINKS in the latest 13 weeks
```

### Known bug (fixed)

The IRI Product Entity agent is non-deterministic — the same query sometimes resolves to `Parent Company_1` level (has member IDs → works) and sometimes to `Brand_1` or `Category_1` level (empty member IDs → breaks with IRI error `AS-1180: Value of attribute ID cannot be empty`).

**Fix applied:** `agents/orchestrator.py` now filters out members with empty `id` fields and raises a clear `ValueError` immediately instead of burning 3 minutes of polling. The error message names the level that failed and suggests querying a more specific product.

---

## 9. Key Config Files

### Cloud repo `.env` (current state)

```ini
LOCAL_MODE=false

GOOGLE_CLOUD_PROJECT=gemini-enterprise-app-499621
GOOGLE_CLOUD_LOCATION=us-central1
PROJECT_ID=gemini-enterprise-app-499621
LOCATION=us-central1
VERTEX_AI_PROJECT=gemini-enterprise-app-499621
VERTEX_AI_LOCATION=us-central1
GOOGLE_GENAI_USE_VERTEXAI=true

STORAGE_BUCKET=gs://gemini-enterprise-app-499621-agent-stage

PRICING_AGENT_URL=projects/413407391500/locations/us-central1/reasoningEngines/7143683726067630080
ACTIVATE_AGENT_URL=projects/413407391500/locations/us-central1/reasoningEngines/4518085143310630912
LOYALTY_AGENT_URL=projects/413407391500/locations/us-central1/reasoningEngines/5295519028985462784
PROFILE_AGENT_URL=projects/413407391500/locations/us-central1/reasoningEngines/6121366610654527488

MCP_SERVER_URL=https://circana-mcp-server-c3i2rix2qq-uc.a.run.app
```

### On-prem `.env`

```ini
MODEL_ID=7920
GOOGLE_GENAI_USE_VERTEXAI=true
GOOGLE_CLOUD_PROJECT=shade-sandbox
GOOGLE_CLOUD_LOCATION=global
GOOGLE_GENAI_MODEL=gemini-3.5-flash

PRODUCT_HIERARCHY_URL=https://analytics-dev.iriworldwide.com/poc/agent/product/hierarchy/v1/invoke
PRODUCT_ENTITY_URL=https://analytics-dev.iriworldwide.com/poc/agent/product/entity/v1/invoke
TIME_HIERARCHY_URL=https://analytics-dev.iriworldwide.com/poc/agent/time/hierarchy/v1/invoke
TIME_ENTITY_URL=https://analytics-dev.iriworldwide.com/poc/agent/time/entity/v1/invoke

MCP_TOOLS_BASE_URL=https://analytics-dev.iriworldwide.com/poc/mcp/tools/ldservices
CLIENT_ID=e8d2abd2-ad45-4f49-9a48-a090349af1c7
```

---

## 10. Python Package Versions (critical — pinned)

These specific versions were tested and work together. Do not upgrade without testing:

| Package | Version | Why pinned |
|---------|---------|------------|
| `google-cloud-aiplatform[agent_engines,adk]` | `1.148.0` | Exact ADK + Agent Engine API |
| `google-adk` | `1.31.0` | ADK runner, session services |
| `google-genai` | `1.73.1` | GenAI client |
| `a2a-sdk` | `0.3.26` | A2A protocol types |
| `a2ui-agent-sdk` | `0.2.1` | A2UI schema manager |
| `fastapi` | `0.136.0` | Portal API (0.137.0 also in deploy.py requirements) |
| `uvicorn` | `0.44.0` | ASGI server |
| `pydantic` | `2.13.1` | Data validation |

---

## 11. Documents in This Repo

| File | Contents |
|------|---------|
| `GCP_Suitability_Assessment.md` | Full assessment of GCP suitability for Circana based on deployment experience |
| `Hyperscaler_Agent_Framework_Evaluation.md` | LangGraph vs ADK vs MAF vs Strands comparison for the Emiri pipeline |
| `DEPLOYMENT_GUIDE.md` | This file |
| `architecture/combined_architecture_design.md` | Original Google-provided architecture docs |

---

## 12. Common Commands Quick Reference

```bash
# PATH (always needed in a fresh terminal)
export PATH="/Users/tim.fox/google-cloud-sdk/bin:$PATH"

# Activate cloud repo venv
source /Users/tim.fox/blackstraw/a2a_MCP_a2ui_agentengine_demo_session_longTermMemory/.venv/bin/activate

# Check auth
gcloud auth list
gcloud auth application-default print-access-token | head -c 20

# Refresh ADC (expires ~60 min, needed for deploy.py)
gcloud auth application-default login

# List live services
gcloud run services list --project gemini-enterprise-app-499621 --region us-central1

# List Reasoning Engines
ACCESS_TOKEN=$(gcloud auth print-access-token)
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://us-central1-aiplatform.googleapis.com/v1beta1/projects/gemini-enterprise-app-499621/locations/us-central1/reasoningEngines" \
  | python3 -c "import sys,json; [print(e.get('displayName'), '|', e.get('name','').split('/')[-1]) for e in json.load(sys.stdin).get('reasoningEngines',[])]"

# Get identity token (for calling authenticated Cloud Run)
gcloud auth print-identity-token

# Redeploy MCP server
python deploy_mcp.py

# Redeploy all 4 sub-agents (~5 min)
python deploy.py

# Redeploy portal
cp Dockerfile.portal Dockerfile && gcloud run deploy circana-portal --source . --region us-central1 --project gemini-enterprise-app-499621 --allow-unauthenticated --clear-base-image --quiet && rm Dockerfile

# Run unit tests (no GCP)
python -m pytest tests/unit -v

# Run integration tests (needs GCP)
python -m pytest tests/integration -v

# Run full GCP test script
python test_gcp.py --layer all

# Run portal locally (LOCAL_MODE)
python run_local.py

# Run on-prem CLI pipeline
/Users/tim.fox/blackstraw/a2a_a2ui_on_prem/.venv/bin/python /Users/tim.fox/blackstraw/a2a_a2ui_on_prem/run_activation_turn.py

# Run on-prem Flask portal
/Users/tim.fox/blackstraw/a2a_a2ui_on_prem/.venv/bin/python /Users/tim.fox/blackstraw/a2a_a2ui_on_prem/app.py
# Open http://localhost:8080
```

---

## 13. Gotchas Encountered (Do Not Repeat)

| # | Gotcha | Fix |
|---|--------|-----|
| 1 | `gcloud` not on PATH | `export PATH="/Users/tim.fox/google-cloud-sdk/bin:$PATH"` |
| 2 | `deploy_mcp.py` called `sys.exit()` on error, closing terminal | Rewrote to `return 1` |
| 3 | `gcloud run deploy` prompted interactively for base image | Added `--clear-base-image` flag |
| 4 | `.env` had `LOCATION=us` — Vertex AI requires `us-central1` | Changed to `us-central1` |
| 5 | `deploy.py` needed ADC, not just `gcloud auth login` | Run `gcloud auth application-default login` separately |
| 6 | `roles/editor` cannot set IAM policy on Cloud Run services | Ask project owner for `roles/run.admin` + `roles/run.invoker` |
| 7 | `Dockerfile` must be named exactly `Dockerfile` (not `Dockerfile.mcp`) | `deploy_mcp.py` now copies `Dockerfile.mcp → Dockerfile` before deploying, cleans up after |
| 8 | IRI entity resolver returns empty member IDs non-deterministically | Fixed in `a2a_a2ui_on_prem/agents/orchestrator.py` — fails fast with clear error |
| 9 | ADC token expires ~60 min during long sessions | Re-run `gcloud auth application-default login` when `deploy.py` fails with auth errors |
| 10 | On-prem Flask app requires its own venv | Use explicit path: `/Users/tim.fox/blackstraw/a2a_a2ui_on_prem/.venv/bin/python` |

---

*Prepared by: Tim Fox, Blackstraw*
*Date: June 26, 2026*
*Session: Circana GCP suitability evaluation*