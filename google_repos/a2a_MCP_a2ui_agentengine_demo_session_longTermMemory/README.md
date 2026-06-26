# Retail Multi-Agent Orchestration Hub & Gemini Enterprise Agent Engine Integration

The **Retail Multi-Agent Orchestration Hub** is a premium, state-of-the-art pilot portal demonstrating a conversational AI interface coupled with an interactive sandbox canvas. The system coordinates retail pricing analytics, cohort construction, audience sizing, and marketing activations across a hybrid multi-agent network.

> [!TIP]
> **🚀 Live Web Portal URL**: [https://circana-portal-943928157761.us-central1.run.app](https://circana-portal-943928157761.us-central1.run.app)

---

## 🎥 Web Application Demo Walkthrough

Explore the E2E user flow of the Multi-Agent Portal, showing session initialization, tool execution, dynamic widget rendering, and safety blocks:

![Web App Demo Walkthrough](architecture/videos/portal_demo_v3.webp)

---

## 1. System Architecture & Topology

The application is built on the **Gemini Enterprise Agent Engine**, implementing a secure, stateful multi-agent hierarchy governed by Model Armor and integrated with custom tools via the Model Context Protocol (MCP):

![Circana Multi-Agent System Architecture](architecture/screenshots/system_architecture_googley.png)

### Core Architecture Components

1.  **FastAPI Portal App & HTTP Sessions:** Manages local user sessions, authenticates identity against Google/Entra Identity Providers, and maintains conversation states locally before dispatching payloads downstream.
2.  **Model Armor Safety Shield:** Acts as an inline firewall for the LLM. Every user prompt is scanned for prompt injection, hate speech, and jailbreak vectors. Every agent output is scanned to redact sensitive PII (Social Security or Credit Card numbers).
3.  **Gemini Enterprise Agent Engine:** Google Cloud's serverless container runtime that packages python-based agent orchestration frameworks and executes them securely under IAM policies.
4.  **Agent & MCP Registry:** Centralized registries that host global metadata configurations. The **Agent Registry** catalog allows the Supervisor to discover sub-agent microservice endpoints, and the **MCP Registry** publishes the schemas of tools hosted on external MCP servers.
5.  **A2A (Agent-to-Agent) Protocol:** Structured JSON message schema that allows the Supervisor to pass structured tasks and raw parameter definitions to sub-agents (and vice-versa) using A2A `DataPart` slots instead of raw unstructured text.
6.  **A2UI (Agent-to-User-Interface) Protocol:** Formats widget schemas (`<a2ui-json>`) returned by agents. The Supervisor intercepts these declarations and expands them into premium HTML widget sandboxes before streaming them to the client console.
7.  **Circana MCP Server on Cloud Run:** Host service built to run the Model Context Protocol in the cloud. It wraps our custom Audience Builder database APIs into standard MCP JSON-RPC schemas and exposes them safely via HTTPS.
8.  **Sessions & Memory Bank:** Manages session state preservation across chat turns. Integrates short-term session memory for conversation context with the **Gemini Enterprise Memory Bank** to extract and recall long-term user preferences and campaign history across browser reloads.
9.  **Agent Observability & Cloud Logging:** Emits execution telemetry, network latency, token consumption, and safety violations directly to **GCP Cloud Logging** to enable full tracing of A2A calls and tool usage per transaction step.
10. **Agent Identity (SPIFFE ID):** Native GCP IAM security protocol assigning cryptographically-attested SPIFFE IDs to each sub-agent for fine-grained authorization and auditing.
11. **Antigravity AI Coding Assistant:** Partner companion tool used to accelerate developer workspace setups, automatically packaging files, writing diagnostic tools, and configuring safety pipelines using project-level Agent Skills.

---

## 2. Master Sequence Flow

The following sequence diagram details how user inputs are processed, sanitized, delegated via A2A, checked for Human-in-the-Loop constraints, and projected onto the UI via A2UI widgets:

```mermaid
sequenceDiagram
    autonumber
    actor Marketer as Marketer
    participant Portal as FastAPI Portal App
    participant Armor as Model Armor Safety Shield
    participant Supervisor as Supervisor Agent (Agent Engine)
    participant SubAgent as Orchestrator Agent (Agent Engine)
    participant MCP as Circana MCP Server (Cloud Run)
    participant DB as Shopper DB / API

    %% Phase A: Initial Query & Pricing Analysis
    Marketer->>Portal: Input: "Identify soft drink pricing opportunities"
    Portal->>Armor: Validate Input & check Jailbreaks
    Note over Armor: Screens for prompt injections / jailbreaks
    Armor-->>Portal: Content Safety: ALLOWED
    Portal->>Supervisor: Execute Chat Turn
    Supervisor->>SubAgent: Delegate pricing analysis (A2A Protocol)
    SubAgent->>DB: Query attrition product catalog
    DB-->>SubAgent: Return product metrics JSON
    SubAgent-->>Supervisor: Return structured widget layout (<a2ui-json>)
    Supervisor-->>Portal: Stream text response + raw JSON widget data
    Note over Portal: Compiles raw JSON into HTML template with local CSS
    Portal-->>Marketer: Render Pricing Table Widget (HITL Checkpoint)

    %% Phase B: Human-in-the-Loop Callback & Audience Sizing
    Marketer->>Portal: Click "Select Cohort" for Diet Pepsi 12pk
    Note over Portal: Formulates semantic trigger: "Action: size Pepsi cohort"
    Portal->>Supervisor: Post Action Callback Event
    Supervisor->>SubAgent: Delegate audience construction & sizing (A2A)
    SubAgent->>MCP: Call tool: "audience-build"
    MCP->>DB: Materialize buyer segment
    DB-->>MCP: Segment materialized (AUD-PEPSI-999)
    MCP-->>SubAgent: Tool success payload
    SubAgent->>MCP: Call tool: "audience-size" (Params: AUD-PEPSI-999)
    MCP->>DB: Estimate audience size & reach
    DB-->>MCP: Return sizing numbers (1,200,000 households)
    MCP-->>SubAgent: Tool success payload
    SubAgent-->>Supervisor: Return structured sizing widget data
    Supervisor-->>Portal: Stream sizing metrics response
    Portal-->>Marketer: Render Interactive Cohort Sizing Dashboard

    %% Phase C: Activation Sync Export
    Marketer->>Portal: Check "LiveRamp" and click "Activate"
    Portal->>Supervisor: Post Activation Action Callback
    Supervisor->>SubAgent: Delegate activation export sync
    SubAgent->>DB: Execute export job to LiveRamp
    DB-->>SubAgent: Sync job initialized successfully
    SubAgent-->>Supervisor: Task complete success payload
    Supervisor-->>Portal: Stream sync confirmation text
    Portal-->>Marketer: Display final success message
```

---

## 3. Gemini Enterprise Agent Engine Component References & Citations

### 🛡️ Model Armor
*   **Definition:** A managed safety service designed to serve as a guardrail wrapper around LLM prompts and responses. It screens input strings for prompt injection, jailbreak attempts, and toxic content, and redacts sensitive Personally Identifiable Information (PII) before it reaches the model.
*   **System Integration:** Our supervisor uses Model Armor to sanitize user prompts inline. Any jailbreak string is immediately blocked, raising a validation exception.
*   **Official Citation:** 
    > *"Vertex AI Model Armor helps protect your generative AI models by scanning inputs and outputs for prompt injections, jailbreaks, PII, and unsafe content."* — [Google Cloud Vertex AI Model Armor Documentation](https://cloud.google.com/vertex-ai/generative-ai/docs/model-armor)
*   **Live Proof-of-Safety (Prompt Injection Blocked):**
    ![Model Armor Blocked Prompt](architecture/screenshots/safety_guardrail_block.png)

### 🗃️ Agent Registry & MCP tool registry
*   **Definition:** The centralized catalog in Gemini Enterprise Agent Engine where custom tools, endpoints, and Model Context Protocol (MCP) servers are registered, authorized, and made discoverable.
*   **System Integration:** The `circana-mcp-server` is registered under the global Agent Registry services with protocol bindings for `JSONRPC` over HTTP/SSE, publishing our custom cohort building tools.
*   **Official Citation:**
    > *"Agent Registry provides a unified catalog to discover, govern, and reuse tools, APIs, and Model Context Protocol servers across your enterprise AI applications."* — [Google Cloud Agent Platform Registry Documentation](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-registry)
*   **Live Proof-of-Registration (MCP Registry):**
    ![GCP MCP Server Registration](architecture/screenshots/gcp_mcp_server_registered.png)
*   **Live Proof-of-Registration (Agent Catalog):**
    ![GCP Agent Registry Catalog](architecture/screenshots/agent_registry_list.png)

### ⚙️ Gemini Enterprise Agent Engine
*   **Definition:** A managed runtime environment that packages Python code, dependencies, and parameters into a serialized execution graph (via Cloudpickle) and deploys it as an API endpoint.
*   **System Integration:** All three Circana sub-agents are deployed as Cloud Agent Engine endpoints under Python 3.13 containers:
    *   **Pricing Engine:** `projects/943928157761/locations/us-central1/reasoningEngines/5913690854400196608`
    *   **Activate Engine:** `projects/943928157761/locations/us-central1/reasoningEngines/3977143014630883328`
    *   **Loyalty Engine:** `projects/943928157761/locations/us-central1/reasoningEngines/4675200956873310208`
*   **Official Citation:**
    > *"Gemini Enterprise Agent Engine lets you deploy python-based orchestration frameworks (such as LangChain or custom agent models) to Google Cloud as fully-managed endpoints."* — [Google Cloud Gemini Enterprise Agent Engine Guide](https://cloud.google.com/vertex-ai/generative-ai/docs/reasoning-engine/overview)
*   **Live Proof-of-Deployment (Agent Engine Endpoints):**
    ![GCP Agent Engine Registered Endpoints](architecture/screenshots/agent_engine_registered.png)

### 🪪 GCP Agent Identity (SPIFFE ID)
*   **Definition:** A purpose-built, native IAM security protocol that assigns unique, cryptographically-attested SPIFFE identities to deployed AI agents. This avoids the use of shared, over-privileged master service account keys and enables granular audit logs.
*   **System Integration:** All Circana sub-agents are deployed with `"identity_type": "AGENT_IDENTITY"`, binding their runtime permissions strictly to their individual execution scopes.
*   **Official Citation:**
    > *"Agent Identity provides a strongly attested, SPIFFE-based cryptographic identity for each individual agent... This promotes a least-privilege approach to agent permissions, bounding access tokens to the agent runtime and ensuring non-repudiable auditing of agent actions."* — [Google Cloud Gemini Enterprise Agent Platform Security Guide](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-platform/security)


### 🌐 A2UI & Agent Interface Resources
* **A2UI Specification**: [https://a2ui.org/](https://a2ui.org/)
* **A2UI GitHub Repository**: [https://github.com/google/A2UI](https://github.com/google/A2UI)
* **A2UI Blog Post**: [Introducing A2UI: An open project for agent-driven interfaces](https://a2ui.org/)
* **A2UI Gemini Enterprise Sample**: `A2UI/samples/agent/adk/gemini_enterprise`
* **Shared A2UI Repositories & Demos**:
  * [https://github.com/elhadik/a2ui_ge_jira_screensplit](https://github.com/elhadik/a2ui_ge_jira_screensplit)
  * [https://github.com/elhadik/working_a2ui_poc](https://github.com/elhadik/working_a2ui_poc)
* **Google Cloud Documentation**: [Register and manage A2A agents](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-registry)
* **Vega-Lite Specification**: [https://vega.github.io/schema/vega-lite/v5.json](https://vega.github.io/schema/vega-lite/v5.json)


### 👥 Multi-Agent Teamwork Topology & Active Registry
The system utilizes a hub-and-spoke supervisor pattern. The root supervisor orchestrates the pipeline phases, parses A2UI layout responses, and coordinates state transitions.

```mermaid
graph TD
    User([User Interface / Session]) -->|1. Chat/Callback Event| Supervisor[CircanaPilotSupervisor]
    
    Supervisor -->|2a. Delegate Phase A| Pricing[PricingAssortmentOrchestrator]
    Supervisor -->|2b. Delegate Phase B/C| Activate[LiquidActivateOrchestrator]
    Supervisor -->|2c. Delegate Phase D| Loyalty[LoyaltyCampaignOrchestrator]
    Supervisor -->|2d. Delegate Profiling| Profile[AudienceProfileAgent]
    
    Pricing -->|Query Attrition| Tool1[pricing_opportunities_tool]
    Activate -->|Compute Sizing| Tool2[audience_sizing_tool]
    Activate -->|Sync Segment| Tool3[activate_segment_tool]
    Loyalty -->|Fetch Offer Config| Tool4[get_loyalty_options_tool]
    Loyalty -->|Launch Rewards| Tool5[launch_campaign_tool]
    Profile -->|Demographic Breakdown| Tool6[profile_audience_tool]
    
    style Supervisor fill:#f8fafc,stroke:#002f6c,stroke-width:2px;
    style Pricing fill:#e0f2fe,stroke:#0284c7,stroke-width:1px;
    style Activate fill:#ecfdf5,stroke:#059669,stroke-width:1px;
    style Loyalty fill:#fffbeb,stroke:#d97706,stroke-width:1px;
    style Profile fill:#f3e8ff,stroke:#9333ea,stroke-width:1px;
```

#### Active Registry Topology

| Agent Name | Role & Objective | Deployed Endpoint (Vertex AI) | Exposed Skills |
| :--- | :--- | :--- | :--- |
| **CircanaPilotSupervisor** | Root coordinator supervising the multi-agent pipeline and managing session state. | *Local web server executor* | Pipeline routing, callback execution, A2UI normalization. |
| **PricingAssortmentOrchestrator** | specialist agent identifying pricing opportunities and category buyer loss. | `projects/943928157761/`<br>`locations/us-central1/`<br>`reasoningEngines/`<br>`5913690854400196608` | Portfolio search, category shopper attrition mapping. |
| **LiquidActivateOrchestrator** | specialist agent coordinating cohort audience sizing and activation exports. | `projects/943928157761/`<br>`locations/us-central1/`<br>`reasoningEngines/`<br>`3977143014630883328` | Audience sizing, LiveRamp/Google Customer Match sync. |
| **LoyaltyCampaignOrchestrator** | specialist agent customizing personalization parameters and reward launches. | `projects/943928157761/`<br>`locations/us-central1/`<br>`reasoningEngines/`<br>`4675200956873310208` | Campaign personalization, loyalty rewards activation. |
| **AudienceProfileAgent** | specialist agent compiling demographic distribution and audience profile breakdown. | `http://localhost:8004` /<br>`projects/dummy/`<br>`locations/us-central1/`<br>`reasoningEngines/`<br>`audience-profile` | Audience demographic profiling, DMA heatmap analysis. |

> [!IMPORTANT]
> **Stateful Context Memory**: In the local development runner, session state is managed via `InMemoryMemoryService`. 
> While this works for single-process local debugging, deploying sub-agents to multi-worker or cloud environments requires migrating to **Firestore-based memory (`FirestoreMemoryService`)** to prevent containers from losing conversation context ("amnesia") between successive user prompts.

---

## 4. E2E Execution Flow & Interactive Dashboards

This walkthrough illustrates an interactive session across the supervisor and three specialized sub-agents, demonstrating how conversational requests translate into native A2UI data models.


### Step A: Category Pricing & Attrition Analysis (`Pricing Agent`)
*   **Agent Functionality**: Identifies category pricing opportunities, calculates lost households, and ranks product attrition where price increases drove volume loss.
*   **User Request**: `"Identify pricing opportunities with shopper attrition in the Soft Drinks category."`
*   **Agent Response & Action**: The `PricingAssortmentOrchestrator` queries historical store attrition data and projects an interactive product selection table into the browser canvas:

![Initial Product Select Table](architecture/screenshots/demo_pricing_table_v2.png)

---

### Step B: ProScore Lookalike Cohort Expansion (`Activate Agent`)
*   **Agent Functionality**: Constructs behavioral lookalikes (ProScore expansion) from verified panel seed buyers.
*   **User Request**: Selecting the `"Tropicana Pure Premium 52oz"` product row.
*   **Agent Response & Action**: The `LiquidActivateOrchestrator` expands the deterministic seed (412,400 households) via ProScore lookalikes to a complete activation-ready audience of 3.1M households.

![ProScore Lookalike Expansion Dashboard](architecture/screenshots/demo_proscore_expansion.png)

---

### Step C: Addressable Reach & Partner Sizing (`Activate Agent`)
*   **Agent Functionality**: Sizes estimated reach and addressable match rates across destination platforms (LiveRamp, Google DV360).
*   **User Request**: Confirming `"Yes, size it"`.
*   **Agent Response & Action**: Calculates an addressable match rate of **92%** (**2.86 Million Households**) and stages downstream activation options.

![Addressable Reach Sizing Dashboard](architecture/screenshots/demo_sizing_reach.png)

---

### Step D: Income Tier & DMA Geography Profiling (`Profile Agent`)
*   **Agent Functionality**: Compiles demographic distributions, income distribution indexes against US baseline, and top DMAs by reach.
*   **User Request**: Clicking `"View Demographic Profile"` / `"Profile it"`.
*   **Agent Response & Action**: The `AudienceProfileAgent` renders a comprehensive demographic dashboard highlighting Middle-Income concentration ($50-75K Index 114) and Southern DMA clusters (Dallas-Ft Worth +32 Index).

![Demographic Income & Geography Dashboard](architecture/screenshots/demo_profile_income.png)

---

### Step E: Household Composition & Generational Mix (`Profile Agent`)
*   **Agent Functionality**: Breaks down family household structures (kids in HH) and generation cohort distribution.
*   **User Request**: Scrolling profile metrics canvas.
*   **Agent Response & Action**: Highlights family concentration (`Couple + 2 kids` indexing +62) and primary decision-maker demographics (`Gen X` 38%).

![Demographic Composition Dashboard](architecture/screenshots/demo_profile_composition.png)

---

### Step F: Cross-Channel Export & Sync Confirmation (`Activate Agent`)
*   **Agent Functionality**: Packages matching deterministic panel segments and securely transmits identifiers to selected downstream activation endpoints.
*   **User Request**: Clicking `"Activate"` / `"Exporting cohort segment"`.
*   **Agent Response & Action**: Initiates real-time secure CRM onboarding to LiveRamp and Google DV360 Custom Match lists.

![Cross-Channel Sync Confirmation](architecture/screenshots/demo_export_sync.png)

---

## 5. Advanced Cloud Platform Integration Details

### A. MCP Cloud Run Deployment & Agent Registry Integration
The Circana Model Context Protocol (MCP) server is compiled as a Docker container (refer to [Dockerfile](file:///usr/local/google/home/elhadik/Circana_POC/Dockerfile)) running FastAPI in HTTP mode. The container is deployed to Google Cloud Run with access control secured by default (`--no-allow-unauthenticated`). 

To orchestrate tool calling securely, we utilize the **Gemini Enterprise Agent Engine Registry** client. During agent initialization, the agent dynamically fetches the registered tool descriptions and connection endpoints:
```python
from google.adk.integrations.agent_registry import AgentRegistry

registry = AgentRegistry(project_id=GOOGLE_CLOUD_PROJECT, location="global")
mcp_toolset = registry.get_mcp_toolset(MCP_SERVER_RESOURCE_NAME)
```
The ADK library automatically resolves the JSON-RPC SSE/Streamable HTTP bindings, manages connection pooling, and handles OIDC identity token generation for Cloud Run secure request routing via a custom `header_provider`.

---

### B. Gemini Enterprise Agent Engine & Graph Orchestration
We leverage the **Google GenAI ADK 2** framework to construct our multi-agent execution graph. Rather than relying on open-ended, non-deterministic agent routing, our topology enforces a strict **state-machine graph** via prompt instructions, structured payloads, and specialized node routing.

#### 1. Graph Structure & Node Definition
The orchestration graph is implemented as a hub-and-spoke tree:
* **Root Node (Supervisor)**: The `CircanaPilotSupervisor` agent (defined in [agent.py](file:///usr/local/google/home/elhadik/Circana_POC/agents/circana_pilot_agent/agent.py)) coordinates user session contexts, delegates tasks to specific leaf nodes, and projects UI widgets back to the portal.
* **Leaf Nodes (Sub-Agents)**: Remote `Agent` microservices deployed on the Gemini Enterprise Agent Engine (e.g., `PricingAssortmentOrchestrator`, `LiquidActivateOrchestrator`, and `LoyaltyCampaignOrchestrator`).

#### 2. Deterministic State Transitions
We map user interactions to a series of four distinct operational phases, preventing the supervisor from diverging or skipping steps:
* **Phase A (Pricing Analysis)** $\rightarrow$ **HITL Checkpoint** $\rightarrow$ **Phase B (Audience Sizing)** $\rightarrow$ **Phase C (Activation Sync)** $\rightarrow$ **Phase D (Loyalty Campaign)**

This state machine is enforced programmatically in the Supervisor's system instruction template (refer to [agent.py:L20-38](file:///usr/local/google/home/elhadik/Circana_POC/agents/circana_pilot_agent/agent.py#L20-38)):
1. **State Isolation**: Sub-agents only have access to tools that belong to their specific domain. For instance, the `PricingOpportunitiesAgent` cannot trigger audience activation.
2. **Context Passing (A2A)**: The root node passes parameters (such as the target cohort product or activation partners) down to the leaf nodes using structured A2A data slots, avoiding unstructured instruction drift.
3. **Execution Thread Locking**: The supervisor is instructed to halt execution and return control to the portal after completing each phase's A2UI component rendering, waiting for explicit user interaction before transitioning to the next phase.

#### 3. Dynamic Hybrid Routing vs. get_remote_a2a_agent
While standard Gemini Enterprise Agent Registry console examples recommend abstracting remote nodes using:
```python
remote_agent = registry.get_remote_a2a_agent(AGENT_NAME)
sub_agents=[remote_agent]
```
we programmatically route sub-agent communications through a custom `send_message_tool` tool instead. This dynamic approach guarantees:
* **Local Emulation Support**: When developing/testing locally, the supervisor routes requests to local mock ports (e.g. `http://localhost:8001`), whereas `get_remote_a2a_agent` would always force routing to cloud deployments.
* **Identity Header Propagation**: We can inject user Microsoft Entra ID context dynamically in A2A request headers per turn.

---

### C. Human-in-the-Loop (HITL) State Suspension & A2UI widgets
To provide a premium, application-like experience rather than a basic text chat, we leverage the **A2UI (Agent-to-User-Interface) Web Component** framework. 

#### 1. Rich Interactive Web Canvas
A2UI allows agents to project full-featured, stateful HTML/JS widgets directly into the user console interface:
* **Interactive Components**: Agents construct structured JSON configurations defining tables, charts, and control panels (badges, sliders, checkboxes).
* **Hover-over Tooltips**: Visual charts (such as the Reach Distribution graphs) render tooltips and details dynamically as the user hovers.
* **Interactive Elements**: Users can select checkable partners (e.g. checking "LiveRamp" or "Google Customer Match" in the sizing dashboard), toggle configurations, and edit pricing rows.
* **State Synchronization**: Actions taken in the sandboxed widget (clicks, toggles) immediately synchronize with the local session state.

#### 2. Suspension & Resumption Flow
This interaction is governed by state suspension and callback execution:
1. **Suspension**: When the Pricing Agent identifies cohort opportunities, it halts the execution graph and returns a structured `<a2ui-json>` schema block to the supervisor.
2. **Dynamic Rendering**: The frontend portal parses this block and renders a custom interactive sandbox.
3. **Resumption**: When the user performs an action (e.g., clicking a button inside the pricing table or clicking "Activate" after checking destination partners), the portal intercepts the click event and POSTs a resume callback request back to the `SupervisorAgent`, triggering the next node in the multi-agent graph.

---

### D. GCP Cloud Logging & Security Auditing
All session telemetries, tool executions, and safety screenings are logged natively to **GCP Cloud Logging**:
* **Execution Telemetry**: Trace IDs are propagated across the A2A network, matching Supervisor delegation steps with Cloud Run MCP container requests.
* **Cost Auditing**: Token consumption details and model latency are written per turn for exact cost computation.
* **Audit Traces**: Cloud Run request logs monitor endpoint access, rejecting unauthenticated requests automatically.
* **Observability Metrics**: The Vertex AI Agent Platform dashboard tracks queries per second, latency profiles, error rates, and container system resources:

  ![Agent Observability Dashboard Metrics](architecture/screenshots/agent_observability_metrics.png)

![GCP Cloud Run Request Logs](architecture/screenshots/cloud_run_mcp_logs.png)

---

### E. Stateful Sessions & Playground Testing
The Gemini Enterprise Agent Engine maintains conversational state natively across multi-turn interactions. Developers can monitor active sessions and inspect complete step-by-step chat logs and tool invocations:
* **Sessions Registry**: Active conversation sessions are tracked per reasoning engine:

  ![Agent Engine Sessions Registry](architecture/screenshots/agent_engine_sessions.png)

* **Playground Trace Inspection**: Complete interaction histories, tool calls, and state transitions can be audited in the Agent Playground:

  ![Agent Engine Playground Trace](architecture/screenshots/agent_engine_playground.png)

---

## 6. Setup & Deployment Guide from Scratch

This guide walks through deploying the entire Multi-Agent platform and MCP tool ecosystem from scratch on Google Cloud Platform.

### 📋 Prerequisites
1. **Google Cloud SDK**: Install the `gcloud` CLI. Authenticate your CLI and set up Application Default Credentials (ADC):
   ```bash
   gcloud auth login
   gcloud auth application-default login
   ```
2. **Project Configuration**: Ensure your target GCP project (e.g., `shade-sandbox`) is active, with Vertex AI, Cloud Run, and Cloud Storage APIs enabled.
3. **Environment Setup**: Ensure Python 3.13 is installed. Create and activate a virtual environment, then install requirements:
   ```bash
   python3.13 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

---

### 🚀 Step-by-Step Setup

#### Step 1: Deploy the MCP Tool Server to Cloud Run
The MCP server hosts the audience building database querying engines. It must be deployed first so the sub-agents can fetch its endpoint.

1. Ensure the `deploy_mcp.py` script is configured with your target GCP `project_id` and preferred deployment `region`.
2. Run the deployment script:
   ```bash
   python deploy_mcp.py
   ```
   *This command uploads the local MCP workspace, builds a container on Google Cloud Run, deploys it securely (disallowing public unauthenticated access), and updates your `.env` file with the generated `MCP_SERVER_URL`.*

---

#### Step 2: Deploy Orchestrator Sub-Agents to Vertex AI
Once the MCP server is live, the specialist sub-agents (Pricing, Activate, Loyalty) must be packaged and deployed as managed Reasoning Engine endpoints.

1. Set the staging GCS bucket variable in your environment or `.env` file:
   ```env
   STORAGE_BUCKET=gs://shade-agent-staging
   ```
2. Run the deployment script:
   ```bash
   python deploy.py
   ```
   *This script packages the local agent modules (under the `circana_pilot_agent` namespace), bundles dependencies (like `a2a-sdk` and `google-genai`), serializes the agent graphs, uploads them to your GCS staging bucket, creates Vertex AI Reasoning Engine resources, and automatically updates your local `.env` file with the new resource URLs (`PRICING_AGENT_URL`, `ACTIVATE_AGENT_URL`, `LOYALTY_AGENT_URL`).*

   > [!IMPORTANT]
   > **Packaging Directory Structure**: The `circana_pilot_agent` directory contains the sub-agent definitions, tools, and the `examples/` subdirectory. Packaging the entire `circana_pilot_agent` folder as an `extra_package` guarantees that relative file resource queries (like searching for A2UI schemas in `examples/0.8`) resolve correctly inside the cloud reasoning container.

---

#### Step 3: Run the Local Web Application (Development)
With all remote APIs and sub-agent endpoints successfully deployed and synchronized in your local `.env` file, start the local FastAPI web server:

1. Launch the web application using uvicorn:
   ```bash
   uvicorn web_app.server:app --host 0.0.0.0 --port 8000
   ```
2. Open your browser and navigate to `http://localhost:8000` to interact with the visual orchestrator portal.

---

#### Step 4: Deploy the Web Application to Cloud Run (Production)
For a fully public, production-grade cloud deployment, you can host the portal server on Google Cloud Run. This compiles the FastAPI application and static HTML frontend into a Docker container and serves it over a public HTTPS URL.

1. **Docker Configuration**: A dedicated [Dockerfile.portal](file:///usr/local/google/home/elhadik/Circana_POC/Dockerfile.portal) defines the runtime environment, dependencies, path variables, and launches the uvicorn worker exposing port `8080`.
2. **Source Optimization**: Ensure [.gcloudignore](file:///usr/local/google/home/elhadik/Circana_POC/.gcloudignore) is configured in your project root to exclude local virtual environments (`.venv/`) and media folders (`architecture/`) from the build context. This reduces source upload size from 400MB+ to under 2MB.
3. **Execution Command**: Since Google Cloud Run source builds expect the build spec to be named `Dockerfile` in the root folder, temporarily copy the portal Dockerfile and deploy:
   ```bash
   # 1. Copy portal config to temporary Dockerfile
   cp Dockerfile.portal Dockerfile

   # 2. Deploy to Cloud Run (automatically builds & registers container)
   gcloud run deploy circana-portal \
     --source . \
     --region us-central1 \
     --project shade-sandbox \
     --allow-unauthenticated

   # 3. Clean up the temporary Dockerfile
   rm Dockerfile
   ```
   *This command uploads the source assets, triggers a container build on Google Cloud Build, registers it in Artifact Registry, deploys the Cloud Run service, and outputs the public HTTPS Service URL (e.g. `https://circana-portal-943928157761.us-central1.run.app`).*

---

### 🧹 Step 5: Maintenance & Utilities
*   **Decoy/Stale Engine Cleanup**: To avoid resource leaks and clean up old/orphaned reasoning engine deployments:
    ```bash
    python scripts/delete_unused_engines.py
    ```
    *This utility fetches all active reasoning engine deployments, matches them against the current IDs declared in your `.env` configuration, and rate-limits the deletion of any unreferenced/orphaned engines in the GCP project.*

---

## 7. AI Agent Skills & Vibe Coding

To enable rapid iteration and "vibe coding" with AI assistants (such as **Antigravity**), this repository exposes project-specific instructions under the `skills/` folder:

*   **[a2a-multi-agent-orchestration](file:///usr/local/google/home/elhadik/Circana_POC/skills/a2a-multi-agent-orchestration/SKILL.md)**: Guides the construction of supervisor-specialist multi-agent execution graphs.
*   **[agent-identity-setup](file:///usr/local/google/home/elhadik/Circana_POC/skills/agent-identity-setup/SKILL.md)**: Guides configuring native `AGENT_IDENTITY` for Reasoning Engines to secure access using SPIFFE cryptographic IDs.
*   **[model-armor-integration](file:///usr/local/google/home/elhadik/Circana_POC/skills/model-armor-integration/SKILL.md)**: Guides implementing safety shields (Jailbreaks and PII redaction) inside Agent Runtime hooks.

### How AI Coding Agents Consume Skills
When pair-programming, AI agents like Antigravity parse the `SKILL.md` documents to understand local engineering conventions, API configurations, and deployment routines. This eliminates the need for the user to manually explain architecture patterns or write boilerplate instructions, accelerating feature development.

---

## 🤖 Google Antigravity Overview & Installation

**Google Antigravity** is a next-generation AI coding assistant designed to pair-program on local codebases. It reads your project structure, executes diagnostic commands, edits files, and automates builds directly from your terminal or IDE.

### 📥 How to Install
*   **CLI Companion Installation**:
    ```bash
    npm install -g @google/antigravity-cli
    ```
*   **IDE Extension**:
    Search for **Antigravity** in the Google Internal Extensions Marketplace or VS Code Extensions panel to enable inline code completion and sidebar agent chat workspace bindings.

---

## Operational Supplement: Unified Multi-Agent Engine & MCP Deployment Guide

This guide bridges the gap between the foundational README and the explicit requirements of enterprise cloud policies, focusing on Application Default Credentials (ADC), caching constraints, and precise directory resolution.

### Step 1: Repository Cloning & Core Pre-requisites
Execute these operations from your Linux Virtual Machine terminal to pull down the project and create a localized target environment shell.

```bash
# 1. Clone the master repository branch
git clone https://github.com/elhadik/a2a_MCP_a2ui_agentengine_demo_session_longTermMemory.git
cd a2a_MCP_a2ui_agentengine_demo_session_longTermMemory

# 2. Establish a clean, isolated Python virtual environment workspace
python3 -m venv venv
source venv/bin/activate

# 3. Write your ground-truth ecosystem environment properties matrix
cat << 'EOF' > .env
GCP_PROJECT_ID="symmetric-sonar-444512-p5"
GCP_REGION="us-central1"
VERTEX_AI_PROJECT="symmetric-sonar-444512-p5"
VERTEX_AI_LOCATION="us-central1"
STORAGE_BUCKET="gs://symmetric-sonar-444512-p5-agent-stage"
GOOGLE_GENAI_USE_VERTEXAI="true"
GOOGLE_CLOUD_PROJECT="symmetric-sonar-444512-p5"
GOOGLE_CLOUD_LOCATION="us-central1"
EOF
```

### Step 2: Enable Core Cloud APIs & Identity Provisioning
You must systematically initialize the underlying microservice fabrics on Google Cloud before applying role configurations.

```bash
# Enable required service micro-engines
gcloud services enable \
    aiplatform.googleapis.com \
    discoveryengine.googleapis.com \
    iam.googleapis.com \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    cloudbuild.googleapis.com
```

### Step 3: Comprehensive Cloud IAM Role Assignments
Enterprise policies intentionally disallow static API keys (`GEMINI_API_KEY`). The application must run entirely keyless via cross-service Identity and Access Management (IAM). Run this block to authorize your user profile, the backend compute engine, and the Vertex AI service agents:

```bash
# Set foundational variables
export PROJECT_ID="symmetric-sonar-444512-p5"
export ACTIVE_USER="admin@flupo.altostrat.com"
export PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")

# 1. Authorize your deployer profile to orchestrate architectures
gcloud projects add-iam-policy-binding $PROJECT_ID --member="user:$ACTIVE_USER" --role="roles/run.admin"
gcloud projects add-iam-policy-binding $PROJECT_ID --member="user:$ACTIVE_USER" --role="roles/storage.admin"
gcloud projects add-iam-policy-binding $PROJECT_ID --member="user:$ACTIVE_USER" --role="roles/iam.serviceAccountUser"

# 2. Authorize the Front-end Web Portal's identity to call Gemini keylessly (ADC)
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
    --role="roles/aiplatform.user"
```

### Step 4: Building & Deploying the MCP Backend Server
Why this step differs from the original README: Because the code file is located deep within a nested folder structure (`agents/circana_pilot_agent/mcp_servers/circana_mcp_server.py`), standard Cloud Buildpack guessers fail. We bypass this by creating an explicit `Dockerfile` that maps python package visibility tracking parameters (`PYTHONPATH`).

#### A. Create the Workspace Blueprint
Run this command block to drop the precise execution file into your root workspace:

```bash
cat << 'EOF' > Dockerfile
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app:/app/agents
COPY . /app/
RUN pip install --no-cache-dir fastapi uvicorn google-cloud-storage python-dotenv
EXPOSE 8080
CMD ["python", "agents/circana_pilot_agent/mcp_servers/circana_mcp_server.py", "--http", "--host", "0.0.0.0", "--port", "8080"]
EOF
```

#### B. Configure the Cached Deployer Script
Overwrite your `deploy_mcp.py` tracking script with this version. It passes empty strings (`--command ""` and `--args ""`) to clear sticky, broken command metadata caches out of Cloud Run's revision history:

```python
cat << 'EOF' > deploy_mcp.py
import os
import re
import subprocess
import sys

def deploy_mcp():
    project_id = "symmetric-sonar-444512-p5"
    region = "us-central1"
    service_name = "circana-mcp-server"
    
    print("Starting deployment of MCP Server to Google Cloud Run via Dockerfile...")
    
    cmd = [
        "gcloud", "run", "deploy", service_name,
        "--source", ".",
        "--region", region,
        "--project", project_id,
        "--no-allow-unauthenticated",
        "--command", "",
        "--args", ""
    ]
    
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        service_url = None
        for line in process.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
            if "Service URL:" in line:
                match = re.search(r"Service URL:\s*(https://[^\s]+)", line)
                if match:
                    service_url = match.group(1)
                    
        process.wait()
        if process.returncode != 0:
            sys.exit(process.returncode)
            
        print(f"\n✓ MCP Server deployed successfully! URL: {service_url}")
        
        env_path = ".env"
        env_content = ""
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                env_content = f.read()
                
        if "MCP_SERVER_URL=" in env_content:
            env_content = re.sub(r"MCP_SERVER_URL=[^\n]*", f"MCP_SERVER_URL={service_url}", env_content)
        else:
            env_content = env_content.strip() + f"\nMCP_SERVER_URL={service_url}\n"
            
        with open(env_path, "w") as f:
            f.write(env_content)
            
        print("✓ Updated .env file with remote MCP_SERVER_URL.")
        
    except Exception as e:
        sys.exit(1)

if __name__ == "__main__":
    deploy_mcp()
EOF
```

#### C. Run Build & Authorize Inter-Service Invocation
Execute the script, then grant the global Vertex AI system profile explicit permissions to bypass network perimeters and invoke your secure backend tools:

```bash
# 1. Compile and deploy via Cloud Build
python deploy_mcp.py

# 2. Authorize Vertex AI to call the newly created service
gcloud run services add-iam-policy-binding circana-mcp-server \
    --region=us-central1 \
    --project=$PROJECT_ID \
    --member="serviceAccount:service-$PROJECT_NUMBER@gcp-sa-aiplatform.iam.gserviceaccount.com" \
    --role="roles/run.invoker"
```

### Step 5: Registering the Vertex AI Sub-Agents
With the active tool URL written back into your local configuration context, you can register the reasoning brain components.

*Note: Temporary access tokens automatically drop after exactly 60 minutes. Re-prime your terminal session context parameters to prevent an unexpected access token refresh crash trace.*

```bash
# 1. Establish a fresh 60-minute access token block
export GOOGLE_OAUTH_ACCESS_TOKEN=$(gcloud auth print-access-token)

# 2. Trigger the master agents provisioning process
python deploy.py
```

### Step 6: Deploying the Asynchronous Web Portal
The final dashboard element is built using the provided layout file `Dockerfile.portal`.

*Note on package weight minimization: Make sure your root directory has a `.gcloudignore` file tracking your virtual directories (e.g., matching lines for `venv/` or `.git/`). This keeps Cloud Build from needlessly uploading heavy local compiler dependencies, keeping the deployment file small.*

```bash
# 1. Stage the designated portal configuration file
cp Dockerfile.portal Dockerfile

# 2. Launch the Web UI to Cloud Run bound to keyless enterprise parameters
gcloud run deploy circana-portal \
  --source . \
  --region us-central1 \
  --project symmetric-sonar-444512-p5 \
  --allow-unauthenticated \
  --command "" \
  --args "" \
  --set-env-vars GOOGLE_GENAI_USE_VERTEXAI="true",GOOGLE_CLOUD_PROJECT="symmetric-sonar-444512-p5",GOOGLE_CLOUD_LOCATION="us-central1"

# 3. Clean up the temporary root spec file
rm Dockerfile
```

### Step 7: Post-Install Verification & Testing
Once complete, open the public secure route path link returned by the `circana-portal` execution step in your web browser. Type a test prompt (e.g., `"Create a target marketing cohort for Pepsi products"`).

The web interface will securely fetch your keyless identity tokens, route intent parameters down to the active Vertex AI agents, and trigger the cloud container to parse your databases smoothly.


