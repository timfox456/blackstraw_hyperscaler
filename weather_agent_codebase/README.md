# GCP Hyperscaler Evaluation — A2A Weather + Host Agent

End-to-end harness for evaluating Vertex AI Agent Engine / Gemini Enterprise
using the existing `weather_agent` + `host_agent` ADK agents, with every
control from the Client Action Items report (`client_action_items_report.pdf`)
applied.

## Project layout

```
a2a_agent/
├─ agent.py                          # top-level re-export for Reasoning Engine
├─ deploy_agent_engine.py            # hardened deploy: SA + Firestore + OTel
├─ requirements.txt
├─ weather_agent/
│  ├─ agent.py                       # ADK weather agent (Reasoning Engine target)
│  └─ agent_rag.py                   # Standalone RAG-only weather agent
├─ host_agent/agent.py               # ADK orchestrator (A2A to weather agent)
└─ gcp/
   ├─ registration/                  # Section 1
   │  ├─ weather_agent.adkAgentDefinition.json
   │  ├─ weather_agent.AgentCard.json
   │  ├─ host_agent.adkAgentDefinition.json
   │  ├─ host_agent.a2aAgentDefinition.json
   │  └─ host_agent.AgentCard.json
   ├─ iam/                           # Section 2
   │  └─ setup_service_account.ps1
   ├─ services/                      # Section 3
   │  └─ firestore_services.py
   ├─ observability/                 # Section 6
   │  ├─ otel_setup.py               # Cloud Trace + Cloud Monitoring exporters
   │  └─ context_propagation.py      # W3C traceparent + gen_ai.conversation.id
   └─ retrieval/                     # RAG knowledge retrieval
      └─ weather_rag.py              # Vertex AI RAG corpus + retrieval tool
```

## Mapping to PDF action items

| PDF Section | What it requires | Where implemented |
|---|---|---|
| **1 — Agent Registry & Registration** | AgentCard + `adkAgentDefinition` / `a2aAgentDefinition` payloads; PATCH-don't-DELETE upgrade discipline | `gcp/registration/*.json`; `deploy_agent_engine.py` prints a ready-to-PATCH payload after deploy |
| **2 — Service Account Least Privilege** | Dedicated per-agent SA, AGENT_IDENTITY, minimal IAM roles | `gcp/iam/setup_service_account.ps1` creates SAs; `deploy_agent_engine.py` pins `service_account=...` |
| **3 — State & Persistent Memory** | Replace `InMemorySessionService` with `FirestoreSessionService`; periodic compaction | `gcp/services/firestore_services.py` (native first, custom fallback); wired into `AdkApp` via `session_service_builder` |
| **6 — Observability & Logging** | Emit OTel GenAI Semantic Convention spans/metrics so Gemini Enterprise dashboards (Overview / Evaluation / Models / Tools / Usage / Logs) populate | `gcp/observability/otel_setup.py` (Cloud Trace + Cloud Monitoring exporters + Resource attrs); `enable_tracing=True` on AdkApp; tool calls wrapped in `start_tool_span` |

## One-time setup

```powershell
# 1. Install deps
.\venv\Scripts\pip.exe install -r requirements.txt

# 2. Create dedicated SAs with least-privilege bindings (PDF Section 2)
gcloud auth login
.\gcp\iam\setup_service_account.ps1

# 3. Enable required APIs
gcloud services enable `
    aiplatform.googleapis.com `
    discoveryengine.googleapis.com `
    firestore.googleapis.com `
    cloudtrace.googleapis.com `
    monitoring.googleapis.com `
    logging.googleapis.com `
    --project=gemini-enterprise-app-499621

# 4. Create the (default) Firestore database in Native mode (PDF Section 3)
gcloud firestore databases create --location=us-central1 `
    --project=gemini-enterprise-app-499621
```

## Deploy

### Full hardened deploy (custom SA + Firestore)

```powershell
.\venv\Scripts\python.exe deploy_agent_engine.py --agent weather
.\venv\Scripts\python.exe deploy_agent_engine.py --agent host
```

### Deploy when corp Org Policy blocks Firestore and/or IAM bindings

If your account can't create a Firestore database or bind project-level IAM
on the dedicated service accounts (common in corp projects with restrictive
Org Policies), use these flags to fall back gracefully:

| Flag | Effect | Re-enable later |
|---|---|---|
| `--no-firestore` | Use default in-memory session/memory services instead of `FirestoreSessionService` (PDF Section 3). State is lost on container restart but everything else works. | Drop the flag once admin creates the `(default)` Firestore DB. |
| `--no-custom-sa` | Skip pinning the dedicated runtime SA; container runs under Vertex AI's default agent SA (PDF Section 2 "DEVELOPER_IDENTITY" path). | Drop the flag and pass `--service-account=weather-agent-runtime@...` once admin grants role bindings. |

```powershell
.\venv\Scripts\python.exe deploy_agent_engine.py --agent weather --no-firestore --no-custom-sa
.\venv\Scripts\python.exe deploy_agent_engine.py --agent host    --no-firestore --no-custom-sa
```

Each invocation will print the JSON payload to PATCH into the Gemini
Enterprise agent registry (don't DELETE + recreate — see PDF Section 1 about
the 30-day soft-delete cache locking the `authorizationId`).

## Register / update agents in Gemini Enterprise

Use `PATCH`, not `POST + DELETE`:

```bash
curl -X PATCH \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H 'Content-Type: application/json' \
  -d @gcp/registration/weather_agent.adkAgentDefinition.json \
  'https://discoveryengine.googleapis.com/v1alpha/projects/gemini-enterprise-app-499621/locations/global/collections/default_collection/engines/gemini-enterprise-app/assistants/default_assistant/agents/weather_agent_a2ui?updateMask=adkAgentDefinition'
```

## What the observability dashboards will show

Once deployed and the agents serve some traffic, the **Observability** tab
inside Gemini Enterprise (for each agent picked in the registry) will
populate these dashboards using the OTel signals emitted by
`gcp/observability/otel_setup.py`:

1. **Overview** — session volume, turns/session, error rates, token in/out, p50/p95/p99.
2. **Evaluation** — quality + safety indicators, hallucination rate, tool quality.
3. **Models** — per-model latency, call count, error rate, token quotas (tagged by `gen_ai.request.model`).
4. **Tools** — call count, error rate, p95 latency per tool (tagged by `gen_ai.tool.name` via `start_tool_span`).
5. **Usage** — CPU/memory + prompt processing stats.
6. **Logs** — filterable raw container stream (Cloud Logging).

The host -> weather A2A edge in the **multi-agent topology map** is rendered
from the `gen_ai.agent.downstream=weather_agent` attribute set on
`get_weather_from_remote`.

## Trace observability deep-dive

What's actually captured in each Cloud Trace span and how to find it.

### Persona switching (host -> weather handoff)

Per-agent spans are tagged with the resource attribute `gen_ai.agent.name`
(`host-agent` or `weather-agent`) set in `gcp/observability/otel_setup.py`.

To stitch the host and weather traces into a single distributed trace,
`gcp/observability/context_propagation.py` does two things on every A2A call:

1. **Injects the W3C `traceparent` / `tracestate` HTTP headers** on the
   outbound `:streamQuery` POST to the weather agent's Reasoning Engine.
   This is forward-compatible: once Reasoning Engine inbound extracts W3C
   context, host and weather spans share the same `trace_id` automatically.
2. **Sets a `gen_ai.conversation.id` correlation attribute on both sides
   right now.** The host generates the id, stamps it on its current span,
   and packs it into the ADK `user_id` field (`conv-{uuid}__{user}`). The
   weather agent's tool unwraps it from `ToolContext.session.user_id` and
   re-tags its own span with the same value. In Cloud Trace UI:

   ```
   attribute: gen_ai.conversation.id = <uuid>
   ```

   shows every span across both agents for that one A2A call.

The same attribute powers the **multi-agent topology map** (edge:
`host-agent -> weather-agent`, weighted by call count + p95 latency).

### Streaming

`enable_tracing=True` on `AdkApp` (set in `deploy_agent_engine.py`) tells the
ADK runner to emit one OTel span per `stream_query` call with these GenAI
semantic convention attributes:

| Attribute | What it tells you |
|---|---|
| `gen_ai.request.model` | e.g. `gemini-2.5-flash` |
| `gen_ai.usage.input_tokens` | prompt token count |
| `gen_ai.usage.output_tokens` | completion token count (totaled across stream) |
| `gen_ai.response.finish_reasons` | `STOP`, `MAX_TOKENS`, `SAFETY`, ... |

Per-chunk visibility is delivered as **span events** (not separate spans)
inside the parent `chat gemini-2.5-flash` span — open the span in Cloud
Trace UI and the timeline shows chunk-arrival timestamps. Useful for
computing **TTFT (time-to-first-token)** = `events[0].timestamp - span.start_time`.

### Attachments (multimodal parts)

ADK records each message `Part` as structured attributes on the LLM span
following the GenAI semconv:

- `gen_ai.input.messages` / `gen_ai.output.messages` — JSON-encoded array
  of `{role, parts: [{type, mime_type, content_ref?}]}`.
- Raw bytes are NOT in traces. Image / file / audio parts are staged in
  GCS by the runner and the trace records the GCS URI as `content_ref`.

> **Note:** the current agents declare `defaultInputModes: ["text/plain"]`
> in their AgentCards and accept only `location: str`. So attachment traces
> won't appear until you (a) add `"image/*"` to `defaultInputModes` in
> `gcp/registration/*.AgentCard.json` and (b) extend the tool signatures to
> accept `Part` arguments. Once you do, the existing OTel pipeline captures
> attachment metadata automatically — no further code change needed.

### Where the data lands

| Signal | Backend | UI |
|---|---|---|
| Spans (LLM + tool + A2A HTTP) | Cloud Trace | Trace Explorer, Gemini Enterprise Observability tab |
| Metrics (token usage, latency histograms, tool errors) | Cloud Monitoring | Metrics Explorer + the six Observability dashboards |
| Container logs | Cloud Logging | Logs Explorer + Observability -> Logs |
| Multi-agent topology | derived from spans | Gemini Enterprise Observability -> Topology |

### Forward-compatibility note

When Vertex AI Reasoning Engine starts honoring inbound W3C `traceparent`
extraction (already on the roadmap), no code change is required — the
`gcp.observability.context_propagation.inject_w3c_context_into_headers`
already injects the right headers, and ADK's auto-instrumentation on the
inbound side will pick them up. At that point the `gen_ai.conversation.id`
attribute becomes a redundant belt-and-suspenders cross-check rather than
the primary correlation mechanism.

## RAG retrieval (Vertex AI RAG Engine)

Adds a knowledge-retrieval surface to the eval so we can compare grounded
answers (RAG-backed) against the simulated `get_weather` tool output.

### Files

| File | What it does |
|---|---|
| `gcp/retrieval/weather_rag.py` | Creates (or reuses) a Vertex AI RAG corpus called `weather-knowledge-corpus` in `gemini-enterprise-app-499621 / us-central1`, seeds it with four in-memory weather knowledge docs (Chicago, Miami, NYC, general meteorology), and builds the `VertexAiRagRetrieval` ADK tool. |
| `weather_agent/agent_rag.py` | Standalone RAG-only agent (`name=weather_rag_agent`, `model=gemini-2.5-flash`) wired to the retrieval tool. Lives next to `weather_agent/agent.py` because of an ADK constraint: `VertexAiRagRetrieval` must be the only tool on its agent and cannot be combined with other tools. |

### Public API of `gcp/retrieval/weather_rag.py`

```python
from gcp.retrieval.weather_rag import (
    RAG_CORPUS_RESOURCE_NAME,         # str, populated after create_or_get_rag_corpus()
    create_or_get_rag_corpus,         # idempotent: returns corpus resource name
    build_rag_retrieval_tool,         # (corpus_resource_name) -> VertexAiRagRetrieval
)
```

`create_or_get_rag_corpus()` is idempotent — first call provisions the
corpus and uploads docs via `rag.upload_file` (using a temp dir so no
external files are needed). Subsequent calls just look up the existing
corpus by display name and return its resource name.

The retrieval tool is configured per the eval spec:

| Setting | Value |
|---|---|
| `name` | `retrieve_weather_knowledge` |
| `similarity_top_k` | `3` |
| `vector_distance_threshold` | `0.5` |

### Deploy the RAG agent

```powershell
.\venv\Scripts\python.exe -c "
import os, sys; sys.path.insert(0, os.getcwd())
import vertexai
from vertexai.preview import reasoning_engines
from gcp.observability.otel_setup import configure_otel
configure_otel(service_name='weather-rag-agent', project_id='gemini-enterprise-app-499621')
vertexai.init(project='gemini-enterprise-app-499621', location='us-central1', staging_bucket='gs://gemini-enterprise-app-499621-agent-stage')
from weather_agent.agent_rag import root_agent
app = reasoning_engines.AdkApp(agent=root_agent, enable_tracing=True)
re = reasoning_engines.ReasoningEngine.create(
    app,
    requirements=['google-adk>=2.0.0','google-cloud-aiplatform[agent_engines]>=1.91.0','opentelemetry-sdk>=1.27.0','opentelemetry-exporter-gcp-trace>=1.7.0','opentelemetry-exporter-gcp-monitoring>=1.7.0a0'],
    extra_packages=['./weather_agent','./gcp'],
    display_name='Weather RAG Agent',
)
print(re.resource_name)
"
```

The first deploy will trigger `create_or_get_rag_corpus()` at import time
(creating + seeding the corpus); subsequent deploys reuse it.

### Trace observability for RAG calls

The `VertexAiRagRetrieval` tool participates in the same OTel pipeline as
the rest of the weather agent's tools. In Cloud Trace you'll see a
`execute_tool retrieve_weather_knowledge` span carrying:

- `gen_ai.tool.name = retrieve_weather_knowledge`
- `gen_ai.system = vertex_ai`
- The retrieved chunks (truncated) as span events under GenAI semconv

Filter by `gen_ai.tool.name = "retrieve_weather_knowledge"` in Trace
Explorer to isolate RAG calls and measure p95 retrieval latency / hit
rate.

## Notes on the other PDF sections (not in scope for this delta)

- **4. Model Garden / Provisioned Throughput** — switching `model="gemini-2.5-flash"` to a PT endpoint is a single-line change in `weather_agent/agent.py` / `host_agent/agent.py` once a PT reservation exists.
- **5. Model Armor** — apply at the Apigee / Agent Gateway layer per PDF Section 5; no code change required because Model Armor is decoupled (model-agnostic) and applied at the gateway.
- **7. Workflows / HITL** — orchestrate via `SequentialAgent` / `ParallelAgent` in ADK; out of scope for this evaluation harness.
- **8. Prompt Templates** — load `instruction=` from Vertex AI Prompt Management via the Vertex SDK instead of inlining strings.
