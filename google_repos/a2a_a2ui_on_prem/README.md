# A2A Multi-Agent Orchestration & A2UI Emulator Dashboard

An advanced on-premises orchestration engine and developer sandbox designed to coordinate multiple specialized agent actions in parallel, process database entity mappings, submit analytical sizing queries to downstream engines, and render interactive widgets.

---

## 📽️ End-to-End Execution Tour
Watch the complete end-to-end execution of the multi-agent orchestration and UI rendering flow:

[![Watch Execution Tour](https://img.shields.io/badge/Play-Execution%20Tour%20Video-blue?style=for-the-badge&logo=googleplay)](https://github.com/elhadik/a2a_a2ui_on_prem/raw/main/static/a2a_execution_tour.mp4)

👉 **[Click here to watch the End-to-End Execution Tour Video](https://github.com/elhadik/a2a_a2ui_on_prem/raw/main/static/a2a_execution_tour.mp4)**

---

## 🚀 Key Architectural Features
1.  **Parallel Multi-Agent Execution**:
    *   **Phase 1 (Taxonomy mapping)**: Spawns parallel subagent instances (Product Hierarchy, Time Hierarchy) to parse taxonomy levels.
    *   **Phase 2 (Member mapping)**: Spawns parallel subagent instances (Product Entity, Time Entity) to map concepts to database member IDs.
2.  **Live Server-Sent Event (SSE) Log Trace**:
    *   Streams execution traces directly to the console panel.
    *   Dynamically maps HTTP request stages to active subagent indicators, showing target endpoints and statuses.
3.  **Sizing Batch Polling Loop**:
    *   Submits sized batch definitions to downstream APIs and polls status every 10 seconds for up to 3 minutes, handling cold starts and request latencies.
4.  **Declarative UI Panel (Collapsible/Manual Toggle)**:
    *   Starts collapsed by default to keep the log console full-width.
    *   Automatically slides open when an interactive card is successfully compiled.
    *   Can be manually toggled open/closed at any time using the subheader button.

---

## ⚙️ Environment Configuration
Configure your credentials and downstream endpoints in the `.env` file:

```ini
MODEL_ID=7920
GOOGLE_GENAI_USE_VERTEXAI=true
GOOGLE_CLOUD_PROJECT=shade-sandbox
GOOGLE_CLOUD_LOCATION=global
GOOGLE_GENAI_MODEL=gemini-3.5-flash

# Downstream Resolution Endpoints
PRODUCT_HIERARCHY_URL=https://analytics-dev.iriworldwide.com/poc/agent/product/hierarchy/v1/invoke
PRODUCT_ENTITY_URL=https://analytics-dev.iriworldwide.com/poc/agent/product/entity/v1/invoke
TIME_HIERARCHY_URL=https://analytics-dev.iriworldwide.com/poc/agent/time/hierarchy/v1/invoke
TIME_ENTITY_URL=https://analytics-dev.iriworldwide.com/poc/agent/time/entity/v1/invoke

# MCP Tools Endpoint
MCP_TOOLS_BASE_URL=https://analytics-dev.iriworldwide.com/poc/mcp/tools/ldservices
CLIENT_ID=e8d2abd2-ad45-4f49-9a48-a090349af1c7
```

---

## 🛠️ Setup & Execution

### 1. Install Dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Start the Backend Server
```bash
python app.py
```

### 3. Open Dashboard
Navigate to `http://localhost:8080` in your web browser.
*   Enter your query (e.g. `Create a verified audience sizing Dollar Sales > 0 for COCA COLA CO LOW CALORIE SOFT DRINKS in the latest 13 weeks`).
*   Click **Run A2A Turn** to watch the agents execute.
