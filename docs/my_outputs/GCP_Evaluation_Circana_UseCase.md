# GCP Evaluation for Circana's Use Case

**Date:** June 26, 2026

**Prepared by:** Tim Fox, Blackstraw (Circana engagement)

**Reviewed with:** Denesh Kumar Mani (engagement lead), Rishabh Mendiratta (parallel evaluator)

**Purpose:** Hands-on, evidence-based opinion on whether Google Cloud Platform can support Circana's agent workloads, produced for Circana's hyperscaler evaluation pilot. This document mirrors the **Hyperscaler Evaluation Pilot spreadsheet** (11 sections, 01–11) and provides **two advantages and two limitations per section for Google Cloud**, each grounded in direct hands-on experience deploying and exercising the Google-supplied POCs.


**Companion document:** `agent_framework_comparison` (v3.0) — the separate framework feature-matrix ask (LangGraph vs. ADK vs. MAF vs. Strands).

---

## 1. Executive Summary

### Bottom line

GCP's **Gemini Enterprise Agent Engine + ADK + A2UI/A2A** stack is a **strong, genuinely impressive platform for conversational, human-in-the-loop marketer-facing portals** — exactly the workload the two Google-supplied POCs demonstrate. For that workload class, the platform provides real, native primitives (Agent Engine runtime, A2UI widget protocol, A2A delegation, Agent Registry, SPIFFE agent identity, Model Armor, Cloud Trace) that would otherwise take months to build.

**A second piece of evidence sharpens this verdict:** the `weather_agent_codebase/` reference implementation (the codebase Rishabh actually exercised — see Section 2.5) demonstrates that many capabilities the **Circana POC** marks as Blocked or Weak are in fact **straightforwardly implementable on GCP** with documented patterns Google has already shipped — Firestore session/memory by default, per-agent dedicated SAs, W3C A2A trace propagation, per-tool span instrumentation with prompt-version lineage, native MCP via stdio, and Vertex AI RAG. The Circana POC's gaps in these areas are therefore best read as **implementation choices made by Google's pilot team**, not platform limits. Where the weather reference also leaves a gap (in-agent Model Armor wiring, end-user identity propagation, multimodal `stream_query`, batch scale), the gap is genuinely platform-level.

However, **the POCs and the reference codebase together do not exercise Circana's batch workloads** — batch attribution at the scale of hundreds of thousands to millions of UPCs, nor integration with Circana's existing **Emiri** entity-resolution APIs and **IRI Advantage LD** hierarchy API. Those workloads are deterministic, staged, API-orchestration pipelines — not conversational supervisor patterns — and the pilot provides **no evidence** that GCP's agent framework is the right home for them. The remaining true platform-level gaps relevant to Circana (real in-agent Model Armor, end-to-end user identity from Entra to MCP, multimodal binary attachments through `stream_query`, batch-scale cost and concurrency) are unsolved in either implementation.

**Recommendation:** Treat GCP as a **viable, leading candidate for the conversational HITL portal layer** of Circana's architecture (e.g., a marketer-facing attribution-review or audience-building portal) — and recognize that the Circana POC's current state understates GCP's portal-layer capability ceiling, because Google's own reference implementation does more. Treat the **batch attribution and Emiri/IRI API orchestration layers as unproven on GCP's agent framework** — they are better served by LangGraph (or plain Python) calling Azure OpenAI, independent of which cloud hosts the conversational surface. Do **not** let the POC's polished portal demo substitute for load/cost testing at Circana's real batch volumes.

### Scorecard at a glance

The **POC verdict** is what the Circana POC ships today. The **Platform verdict** factors in the weather-agent reference codebase (Section 2.5) — i.e., what is implementable on GCP today with documented patterns Google has shipped. Where they differ, the right input to "is GCP the right hyperscaler" is the **Platform verdict**.

| # | Section | POC verdict (Circana POC as deployed) | Platform verdict (weather-ref + POC) | Pilot coverage |
|---|---|---|---|---|
| 01 | Chat host & MCP apps | **Partial** — strong A2UI; streaming & MCP-in-trace gaps | **Partial** — A2UI strong; native `MCPToolset` stdio shown to work in weather ref; TTFT/chunk-streaming claim needs re-test (weather README contradicts Rishabh) | Partial |
| 02 | Complex prompt orchestration | **Partial** — orchestration visible; prompt versioning absent | **Partial** — prompt-version-as-span-attribute pattern shown in weather ref; no managed prompt registry → trace binding | Partial |
| 03 | Multi-agent supervisor flow | **Partial** — routing observable; MCP/A2A interop unproven | **Partial** — A2A trace propagation pattern demonstrated in weather ref (W3C + conversation_id); LLM-routed delegation still not a platform primitive | Partial |
| 04 | Memory across agent lifecycle | **Weak** — short-term only; long-term not implemented | **Partial** — Firestore session/memory is the default in weather ref; Gemini Memory Bank still not wired in either | Low (POC) / Partial (ref) |
| 05 | MCP private connectivity | **Weak** — MCP on public Cloud Run; private path not built | **Weak** — standard `MCPToolset` is not bespoke (weather ref); VPC SC / private path unbuilt in both | Low |
| 06 | End-to-end identity propagation | **Not met** — service-account identity, not user identity | **Partial** — per-agent dedicated SAs (AGENT_IDENTITY) demonstrated in weather ref; end-user identity (Entra → JWT → MCP) unbuilt in both | Blocked (POC) / Partial (ref) |
| 07 | Tracing & observability | **Strong** — best-in-class native tracing | **Strong** — confirmed by weather ref's OTel exporters + per-tool spans + multi-agent topology | High |
| 08 | Cost & resource isolation | **Partial** — project attribution works; per-step cost / batch-scale unknown | **Partial** — same; weather ref does not test batch either | Partial |
| 09 | Ontology & entity resolution | **Partial** — entity resolution works; ontology/RAG blocked by permissions | **Partial** — Vertex AI RAG corpus capability fully demonstrated in weather ref; ontology layer unbuilt in both | Partial |
| 10 | Governance & lineage | **Weak** — agent version ok; prompt/tool/skill/policy lineage weak | **Partial** — prompt/tool version-attribute pattern shown in weather ref; Model Armor punted to gateway even in ref; Agent Gateway unbuilt in both | Low (POC) / Partial (ref) |
| 11 | DevOps non-PROD→PROD | **Partial** — repeatable in principle, friction-laden in practice (10 documented gotchas, manual scripting, env drift) | **Partial** — weather ref's `--no-firestore` / `--no-custom-sa` flags show graceful-degradation discipline, but deployment is still manual scripting, not managed CI/CD | High |

### The single most important gap

**No batch-scale or cost-at-scale evidence.** The pilot deployed 4 always-on Reasoning Engines serving a single-user conversational portal with mock data. Circana's attribution runs process 50,000–1,000,000+ data points. Whether Agent Engine is cost-effective or even architecturally appropriate for batch fan-out at that volume is **unevaluated** and is the #1 open risk.

---

## 2. Methodology & Evidence Sources

This evaluation is grounded in direct hands-on experience from:

1. **Deploying both Google-supplied POCs** to Blackstraw's GCP project `gemini-enterprise-app-499621` (region `us-central1`):
   - `a2a_MCP_a2ui_agentengine_demo_session_longTermMemory` — the "cloud" POC: ADK supervisor + 4 sub-agents on Vertex AI Reasoning Engine + MCP server + FastAPI portal on Cloud Run.
   - `a2a_a2ui_on_prem` — the "on-prem" POC: IRI Liquid Data entity resolution + audience sizing pipeline + Flask portal.
   - Deployment steps, gotchas, and live resource IDs are documented in `docs/deployment/DEPLOYMENT_GUIDE.md`.
2. **Rishabh Mendiratta's parallel hands-on findings** — two reports in `docs/rishabh/`:
   - **Expanded report** (`GCP_Hyperscaler_Evaluation_Report_Expanded.docx.md`) — the grounded one: real trace IDs and specific pros/cons for ~7 criteria he tested hands-on. Used as primary evidence where it covers a section. **Important: Rishabh's hands-on testing was performed against the `weather_agent_codebase/` reference implementation (an ADK weather + host agent harness with deliberate hardening for Cloud Trace, Firestore, OTel, RAG, A2A trace propagation, and per-agent dedicated service accounts), not against the Circana POCs themselves.** See Section 2.5 for what this codebase implements and why it matters for interpreting his findings.
   - **Full report** (`GCP_Hyperscaler_Evaluation_Full_Report.docx.md`) — mirrors all 44 sub-criteria with real **Status / Pass Result / Trace ID** fields (hands-on data), but its **Pros/Cons are templated filler** (identical generic text per section). The Full report's statuses and trace IDs are used as evidence for sections the Expanded report doesn't cover; its templated Pros/Cons are not.
3. **The POC's own `gap_analysis.md`** — Google's own admitted gaps (B1–B6), which candidly document what the POC does vs. does not do.
4. **Reading the deployed POC source code** — `agent.py`, `tools.py`, `orchestrator.py`, `components.py`, `deploy.py`, `combined_architecture_design.md` — to verify README claims against actual implementation (several claims diverge from deployed code; these divergences are findings, not criticisms).
5. **Reading the `weather_agent_codebase/` reference implementation** — `weather_agent/agent.py`, `host_agent/agent.py`, `deploy_agent_engine.py`, `gcp/observability/otel_setup.py`, `gcp/observability/context_propagation.py`, `gcp/services/firestore_services.py`, `gcp/retrieval/weather_rag.py`. This is the codebase Rishabh exercised. It implements several capabilities the Circana POC chose not to (Firestore session/memory by default, per-agent dedicated runtime SAs, per-tool span instrumentation with `prompt.id`/`prompt.version` attributes, W3C `traceparent` + `gen_ai.conversation.id` correlation across A2A, native `MCPToolset` via stdio, Vertex AI RAG corpus + retrieval). It is treated here as the **GCP-platform-capability ceiling demonstrated by a hardened reference**, in contrast to the Circana POC which is the **floor of what Google chose to ship for the Circana engagement**.
6. **Circana use-case context** — `docs/emiri/IRI_ADVANTAGE_API.md`, `docs/emiri/LIQUID_DATA_REPORTS.md`, and the framework comparison's Emiri analysis.
7. **Meeting notes, June 26 2026** — `docs/meetings/meeting_20260626.md` — defining the evaluation ask and the hands-on grounding requirement.

**Evidence conventions in this document:**
- `[Trace: <id>]` = a Cloud Trace ID captured by Rishabh during hands-on testing of the **weather agent reference codebase** (see Section 2.5).
- `[POC: <file>:<line>]` = evidence in the deployed Circana POC source code.
- `[Weather: <file>:<line>]` = evidence in the `weather_agent_codebase/` reference implementation.
- `[Deploy: <topic>]` = evidence from the deployment guide (Tim's hands-on).
- `[Gap: B<n>]` = evidence from the Circana POC's own `gap_analysis.md`.
- `[Rishabh]` = Rishabh's Expanded report finding (weather-agent-codebase-based; see Section 2.5 for reading guidance).
- `[Inferred]` = an extrapolation not directly tested; clearly marked.

---

## 2.5. About the weather-agent reference codebase (how to read Rishabh's findings)

Rishabh's hands-on testing was performed against `weather_agent_codebase/`, a deliberately hardened ADK reference implementation that ships in this repo alongside the Circana POCs. This is the most important methodology fact in the document, because it means **Rishabh's results are evidence about what GCP can do when properly implemented, not evidence about what the Circana POC ships.** Many of his "Pass" results validate the platform; many of his "Blocked / Fail" results validate that even Google's reference implementation hasn't yet solved a given gap. Reading his Pass/Fail signals through this lens isolates "platform-capability gap" from "Circana POC implementation choice" — which is the most decision-relevant distinction for Circana.

### What the weather agent codebase implements that the Circana POC does not

| Capability | Weather agent | Circana POC |
|---|---|---|
| **Firestore session + memory by default** | `deploy_agent_engine.py` enables `FirestoreSessionService` + `FirestoreMemoryService` by default; `--no-firestore` is the escape hatch for corp Org Policy blocks. `gcp/services/firestore_services.py` ships native-first + custom-fallback implementations conforming to `BaseSessionService`/`BaseMemoryService`. | `InMemoryMemoryService` / `InMemorySessionService` in the local-execution fallback; cloud sub-agent memory not migrated. |
| **Per-agent dedicated runtime SAs (AGENT_IDENTITY)** | `deploy_agent_engine.py` pins `weather-agent-runtime@...` / `host-agent-runtime@...`; `setup_service_account.ps1` provisions with least-privilege role bindings. | Uses `google.auth.default()` — Vertex AI's default agent SA (DEVELOPER_IDENTITY). |
| **Per-tool span instrumentation** | Every tool body wrapped in `with start_tool_span("tool_name"):` setting `gen_ai.tool.name`, `gen_ai.operation.name`, plus prompt/version/conversation attributes. | Standard ADK `FunctionTool` wrapping with no custom span instrumentation. |
| **Prompt → trace linkage** | `PROMPT_ID` / `PROMPT_VERSION` module-level constants attached as span attributes on every tool call. | Prompts are inline Python strings with no version metadata. |
| **W3C `traceparent` + `gen_ai.conversation.id` propagation across A2A** | `gcp/observability/context_propagation.py` injects W3C headers and a belt-and-suspenders correlation id (stuffed into ADK `user_id`, unwrapped on the receiving side). Cross-agent traces are joinable today via attribute filter; native W3C single-trace-id is roadmap. | Two separate code paths (GenAI SDK for Reasoning Engine URLs, A2A SDK HTTP client for others); no trace-context propagation. |
| **OTel exporters to Cloud Trace + Cloud Monitoring** | `gcp/observability/otel_setup.py` wires `CloudTraceSpanExporter`, `CloudMonitoringMetricsExporter`, resource attributes (`service.name`, `gen_ai.agent.name`), and `RequestsInstrumentor` auto-instrumentation. | Relies on ADK default tracing only. |
| **Native MCP via stdio** | `MCPToolset(StdioConnectionParams(StdioServerParameters(command="npx", args=["-y", "@modelcontextprotocol/server-fetch"])))` — standard ADK pattern. | Custom 100-line tri-fallback HTTP adapter (`tools.py:87–188`). |
| **Vertex AI RAG corpus + retrieval tool** | `gcp/retrieval/weather_rag.py` provisions `weather-knowledge-corpus` via `rag.create_corpus(...RagManagedVertexVectorSearch())`, seeds with `rag.upload_file`, builds `VertexAiRagRetrieval(similarity_top_k=3, vector_distance_threshold=0.5)`. | `SemanticLayerAgent` is a `projects/dummy/...` placeholder URL. |
| **Multi-agent topology / `gen_ai.agent.downstream`** | Host agent tags spans with `gen_ai.agent.downstream=weather_agent`; Gemini Enterprise Observability renders the cross-agent edge. | Not instrumented. |

### What the weather agent does **not** solve (so the doc's gap-finding here is a true platform-level gap)

| Capability | Status in weather agent |
|---|---|
| **Real Vertex AI Model Armor in-agent** | The weather README explicitly punts: "Section 5 — apply at the Apigee / Agent Gateway layer per PDF Section 5; no code change required because Model Armor is decoupled (model-agnostic) and applied at the gateway." Even Google's reference impl does not wire Model Armor into the agent. |
| **End-user identity propagation (Entra → JWT → MCP)** | Weather impl uses dedicated per-agent SAs but does not propagate end-user identity. |
| **Multimodal binary attachments through `stream_query`** | `analyze_weather_image` accepts `image_description: str`, not bytes. README admits raw bytes are not in traces — only GCS `content_ref` URIs. |
| **Batch / cost-at-scale** | Weather agent is also single-user; no batch test, no scale-to-zero evidence. |
| **Deterministic graph routing as a platform primitive** | `host_agent.py` hardcodes `WEATHER_AGENT_RE_ID` and calls `:streamQuery` via raw `requests.post`. No more "platform-primitive" routing than the Circana POC. |

### How to read each section verdict in this document

Each section verdict now distinguishes two questions:

- **POC verdict** — what the deployed Circana POC actually demonstrates (Pass / Partial / Blocked / Fail).
- **Platform verdict** — what GCP-the-platform can do when the weather-agent-style hardening is applied.

The two often differ. The **platform verdict** is the right input to "is GCP the right hyperscaler for Circana"; the **POC verdict** is the right input to "is the Google-supplied Circana POC production-ready as-is." Both matter; conflating them is the failure mode this section is here to prevent.

### One direct contradiction worth re-testing

The weather README claims: "Per-chunk visibility is delivered as **span events** (not separate spans) inside the parent `chat gemini-2.5-flash` span — open the span in Cloud Trace UI and the timeline shows chunk-arrival timestamps. Useful for computing **TTFT (time-to-first-token)** = `events[0].timestamp - span.start_time`."

Rishabh reported: "Per chunk streaming events and TTFT metrics were unavailable."

These two statements are not compatible. One of them is wrong. The Circana POC's "no TTFT" verdict (Section 01.b) inherits from Rishabh's finding and is flagged below as needing re-test before being quoted.

---

## 3. Use-Case-Fit Analysis — Circana's Three Workload Layers

Circana's workloads are not monolithic. The right cloud decision differs by layer.

| Layer | What it is | Volume / pattern | LLM path today | GCP agent-framework fit |
|---|---|---|---|---|
| **1. Blackstraw batch attribution** | attribution, scrape enrichment, hybrid retrieval + constrained LLM extraction | **50K–1M+ UPCs** per run; deterministic phases; audit trails required | Azure OpenAI (`azure-gpt-4o`) via LiteLLM | **Unproven / poor** — POCs are conversational, not batch; Agent Engine is conversational-runtime-shaped |
| **2. Emiri / IRI Advantage API integration** | HTTP orchestration to Circana's existing staged APIs (entity resolution, LD hierarchy, Copilot async poll) | Per-request; parallel fan-out (Product ∥ Geography ∥ Other ∥ Filter); multiple auth schemes | `azure-gpt-4o` templates via Circana `llmadmin` | **Unproven / unnecessary** — these are REST calls, not agent-framework work; LangGraph tool nodes fit |
| **3. Conversational marketer portal** | NL query → intent → entity → measures → HITL review → activation | Single-user, multi-turn, interactive widgets | Azure OpenAI today; Gemini in the POC | **Strong fit** — this is exactly what the POCs demonstrate |

**The POCs only exercise Layer 3.** They do not touch Layer 1 or Layer 2. This is the central framing problem for the evaluation: a glowing portal demo does not validate GCP for batch attribution.

**Key architectural observation (from `docs/emiri/`):** Emiri's entity resolution is already a **staged, parallel, template-driven API pipeline** — not an LLM-supervisor pattern. The negotiation use case **explicitly skips the Intent LLM** and calls `getEmiriEntityResponseProd` directly. Wrapping these REST APIs in ADK's LLM-routed supervisor adds non-determinism and token cost without benefit. (This is developed fully in the companion framework comparison.)

---

## 4. Detailed Evaluation — Spreadsheet Sections 01–11

> Each sub-criterion lists **Status** (Pass / Partial Pass / Blocked / Not Exercised / Fail), the **evidence**, then exactly **two advantages** and **two limitations** on GCP, grounded in that evidence.

---

### Section 01 — Chat Host & MCP Apps

**Pass condition:** Native chat host renders our MCP applets without bespoke glue. Streaming and persona switching work out of the box.

#### 01.a MCP applet render visible in trace

**POC Status:** Blocked
**Platform Status:** Partial — re-test required (see contradiction below)
**Evidence:** `[Rishabh]` "MCP App Visible in Trace. Fail. Reasoning Engine containers lacked Node.js and public SSE infrastructure required by MCP deployment approaches." `[POC: tools.py:87-188]` `call_mcp_tool` does not run MCP inside the Reasoning Engine; it falls back to an HTTP POST to the separately-deployed Cloud Run MCP server (`/tools/call`), or a local stdio subprocess. The Agent Registry path (`get_mcp_toolset`) is attempted only when `MCP_SERVER_NAME` is set, and the code comments that it falls back to "legacy HTTP POST" on failure. `[Deploy: MCP server]` MCP server deployed as a standalone Cloud Run service (`circana-mcp-server`), not as an in-engine applet. **Contradicting evidence:** `[Weather: weather_agent/agent.py:190-198]` declares `MCPToolset(StdioConnectionParams(StdioServerParameters(command="npx", args=["-y", "@modelcontextprotocol/server-fetch"])))` — the **standard ADK pattern** using `npx`-based stdio MCP. `[Weather: deploy_agent_engine.py:163]` includes `mcp>=1.0.0` in the deployed `requirements`. Either (a) `npx` **is** available in the Reasoning Engine container and Rishabh's "lacked Node.js" finding is stale/wrong, or (b) the weather reference's `MCPToolset` declaration does not actually work in deployment — which would be a real platform bug. This needs re-test before being quoted to Circana.

**Advantages on GCP:**
1. MCP servers can be deployed as first-class Cloud Run containers and registered in the **Agent Registry** for discoverability — the `get_mcp_toolset` integration path exists and is documented (`[POC: tools.py:116-122]`).
2. **Standard ADK `MCPToolset` with stdio MCP servers is a clean one-call pattern** in Google's reference implementation (`[Weather: weather_agent/agent.py:190-198]`) — Cloud Run + ID-token auth is the right fallback for cases where stdio isn't appropriate.

**Limitations on GCP:**
1. MCP tool execution does **not** surface as native spans in the agent's trace when routed via the **Circana POC's HTTP fallback** — the path that POC actually uses (`[POC: tools.py:143-188]`). The weather reference's stdio `MCPToolset` is expected to surface natively, but this was not separately validated in Rishabh's tests.
2. **Whether MCP-via-npx-stdio works inside the Reasoning Engine container is unresolved.** Rishabh's hands-on tests reported it does not; Google's reference implementation declares it as the standard pattern. This contradiction is the single most important re-test before relying on native MCP on GCP.

#### 01.b Streaming visible in trace

**POC Status:** Partial Pass (portal returns single JSON blocks per `[Gap: B1]`)
**Platform Status:** Partial Pass — **direct contradiction between sources; re-test before quoting**
**Evidence:** `[Trace: c726b93cbb1ef459a762a2ab27cb6774]` `[Rishabh]` "Invocation, invoke_agent, call_llm, generate_content, and execute_tool spans were captured along with model metadata and token statistics. Per chunk streaming events and TTFT metrics were unavailable. Tracing required explicit enablement." `[Gap: B1]` Google's own gap analysis: "Streaming: Chat responses return as single JSON blocks" — the POC portal returns single JSON blocks, not token streams. Fix listed as "Refactor the FastAPI chat endpoint to return a StreamingResponse using SSE." **Contradicting evidence:** `[Weather: README.md "Streaming"]` claims "Per-chunk visibility is delivered as **span events** (not separate spans) inside the parent `chat gemini-2.5-flash` span — open the span in Cloud Trace UI and the timeline shows chunk-arrival timestamps. Useful for computing **TTFT (time-to-first-token)** = `events[0].timestamp - span.start_time`." If the weather README is correct, TTFT is computable as a derived metric from existing span events (just not as a separate span). If Rishabh's finding is correct, the README is aspirational. The verdict on this row should be revisited once one party is verified.

**Advantages on GCP:**
1. Native **GenAI semantic spans** (`invoke_agent`, `call_llm`, `generate_content`, `execute_tool`) are generated automatically once tracing is enabled, with model metadata and token accounting — a rich, hierarchical trace with no custom instrumentation (`[Rishabh]`).
2. The span hierarchy makes the agent execution flow easy to follow in Cloud Trace. If chunk-arrival span events are real (`[Weather: README]`), TTFT becomes a derived metric from a single LLM span — no separate-span-per-chunk required.

**Limitations on GCP:**
1. **The Circana POC portal doesn't stream at all** — it returns single JSON blocks per `[Gap: B1]`. SSE refactor is on the gap list but not done.
2. **Tracing is not enabled by default** — it requires explicit `enable_tracing` at deploy time (`[Weather: deploy_agent_engine.py:132]` sets `"enable_tracing": True` explicitly), and custom tools require additional instrumentation to appear as spans (`[Rishabh]`). A missed flag means zero observability.
3. **Chunk-level / TTFT visibility is contested** between Rishabh's hands-on (unavailable) and Google's reference README (computable via span events). This is the single most important streaming-related re-test before quoting verdicts on TTFT.

#### 01.c Attachments visible in trace

**Status:** Blocked
**Evidence:** `[Rishabh]` "stream_query does not support multimodal Content objects and Cloud Trace intentionally avoids storing binary payloads. GCS staging and custom metadata correlation would be required." `[POC README]` claims "Attachments & Voice: Staging file uploads to GCS with badge chips" — but this is UI-side staging, not trace-side attachment visibility.

**Advantages on GCP:**
1. **GCS** provides a natural staging store for attachment blobs, and attachment URLs/metadata can be attached to spans as custom attributes — the building blocks exist.
2. Cloud Trace's attribute model is flexible enough to carry attachment references (keys, sizes, content types) even when it won't store binaries.

**Limitations on GCP:**
1. `stream_query` **does not support multimodal `Content` objects**, so attachments cannot flow through the standard agent query path — this is a platform-level constraint, not a config gap (`[Rishabh]`).
2. **Cloud Trace intentionally avoids binary payload storage**, so end-to-end attachment visibility requires a custom GCS-staging + metadata-correlation pattern that is bespoke engineering — not native.

#### 01.d Persona switching visible in trace

**Status:** Pass
**Evidence:** `[Trace: e4fe9b4b3196cf7739ca0437e2e5fa5f]` `[Rishabh]` "Persona transitions appeared as execute_tool set_persona spans and generated independent reasoning steps. Conversation identifiers persisted across turns and token accumulation increased as session context grew."

**Advantages on GCP:**
1. Persona transitions are **independently observable** as `execute_tool` spans, and cross-turn context growth is visible in token accumulation — the platform models persona-as-tool cleanly (`[Rishabh]`).
2. Reasoning steps decompose into individual spans, so each persona change triggers its own traceable execution path.

**Limitations on GCP:**
1. Persona **semantics require application-level implementation** — GCP has no native "persona" concept; it's a tool-call pattern the developer designs (`[Rishabh]`).
2. No chunk-level streaming events (same gap as 01.b), so persona-switch latency is not directly measurable at the token level.

---

### Section 02 — Complex Prompt Orchestration

**Pass condition:** Multi-step prompt chain runs end-to-end against our MCPs. Each step traceable to a specific prompt version.

#### 02.a Multi-step prompt chain runs end-to-end against MCPs

**Status:** Blocked (against *our* MCPs); the POC chain works against the POC's own mock-MCP Cloud Run server.
**Evidence:** `[Rishabh]` "End-to-end MCP chain validation was not possible due to MCP infrastructure dependencies." `[POC: tools.py:12-64]` The MCP server's tools (`audience-build`, `audience-size`, `audience-activate`) return **mock data** from `_MOCK_STATE` — hardcoded product lists and fixed sizing numbers (e.g., "Reach: 2.86M (92% addressable)"). `[POC: tools.py:238-270]` `build_audience_tool` and `size_audience_tool` fabricate results without calling a real database. `[Deploy: on-prem POC]` The on-prem POC *does* call real IRI Liquid Data endpoints (`orchestrator.py`), but those are not "our MCPs" in the registry sense.

**Advantages on GCP:**
1. The **multi-step delegation chain itself works** — the supervisor calls `send_message_tool`, which routes via the GenAI SDK to Agent Engine (`on_message_send`), and sub-agents return structured A2UI payloads that the portal renders (`[POC: tools.py:481-505]`). The orchestration plumbing is functional.
2. The phase-based state-machine (Phase A pricing → HITL → Phase B sizing → Phase C activation) is enforceable through system-instruction discipline and tool scoping (`[POC: agent.py:20-41]`), and decoy agents are correctly intercepted (`[POC: tools.py:405-408]`).

**Limitations on GCP:**
1. The chain was **not validated against real Circana MCPs** — the POC's MCP tools return mock data, so "runs end-to-end against our MCPs" is unproven, not passed.
2. The orchestration is **LLM-instruction-routed**, not a deterministic graph — the supervisor follows prose phase instructions (`agent.py:20-41`), which means the same input could take a different path. For auditable batch pipelines this is a liability (see Section 3 of the companion framework comparison).

#### 02.b Each orchestration step visible in trace

**Status:** Pass
**Evidence:** `[Trace: 08b300d58ad7d89907a98551abbf9f55]` `[Rishabh]` "Parallel execution, aggregation, persona switching, and response generation appeared as distinct spans. The workflow generated fifteen spans and demonstrated that orchestration decisions could be reconstructed directly from Cloud Trace."

**Advantages on GCP:**
1. The **complete workflow is represented as a span tree** — parallel execution, aggregation, and response generation are all distinct, queryable spans (`[Rishabh]`).
2. Parallel execution is visible **without custom instrumentation**, and reasoning steps map directly to trace spans — reconstruction of orchestration decisions from the trace is practical.

**Limitations on GCP:**
1. **Trace complexity increases quickly** for larger workflows — at 15 spans for a 3-step demo, a real multi-agent batch run would produce span counts that make manual inspection difficult (`[Rishabh]`).
2. There is **no native prompt-version linkage** on these spans (see 02.c), so "each step visible" is true but "each step traceable to a prompt version" is not — half the pass condition is missing.

#### 02.c Each step traceable to a specific prompt version

**POC Status:** Fail — Circana POC's prompts are inline strings with no version metadata
**Platform Status:** Partial Pass — documented pattern adopted by Google's reference implementation
**Evidence:** `[Rishabh]` "Custom prompt identifiers were possible but no native prompt-to-trace linkage exists." `[Meeting notes]` Rishabh stated: "the create version API… doesn't version the prompts correctly" and "prompt management and cloud trace are pretty disconnected… you have to go in and manually do that." `[POC: agent.py:18-41]` The "prompt" is a hardcoded Python string (`ROLE_DESCRIPTION` + `WORKFLOW_DESCRIPTION` + `UI_DESCRIPTION`) assembled at agent creation — there is no prompt registry, no version ID, no prompt-to-trace binding. **Reference-implementation evidence:** `[Weather: weather_agent/agent.py:36-37]` declares module-level `PROMPT_ID = "7282778269173153792"` / `PROMPT_VERSION = "1"`, and `[Weather: weather_agent/agent.py:70-71, 96-97, 143-144, 169-170]` attach those as `prompt.id` / `prompt.version` span attributes on **every** tool call. This is exactly the discipline the spreadsheet asks for, applied consistently in Google's own reference implementation.

**Advantages on GCP:**
1. **The prompt-version-as-span-attribute pattern is demonstrated working in Google's reference implementation** (`[Weather: weather_agent/agent.py]`) — `prompt.id` and `prompt.version` attributes on every tool span give queryable prompt lineage with no managed-service dependency.
2. Reasoning Engine deployment IDs give agent-level versioning (see 10.a), which composes naturally with the per-span `prompt.id`/`prompt.version` pattern for an "engine X + prompt Y" lineage tuple.

**Limitations on GCP:**
1. **No managed Prompt Management → Cloud Trace linkage exists** — Vertex AI Prompt Management is not bound to the trace pipeline, and the `create version` API does not version prompts correctly per hands-on testing (`[Meeting notes]`, `[Rishabh]`). The capability gap is "no managed registry/binding"; the workable pattern is custom span attributes (as the weather ref shows).
2. The Circana POC does **not** apply this pattern — its prompts are inline Python strings with no version metadata at all (`[POC: agent.py:18-41]`), so even the manual-instrumentation discipline isn't applied. Adopting the weather-ref pattern is a one-file change.

---

### Section 03 — Multi-Agent Supervisor Flow

**Pass condition:** Supervisor delegates to parallel workers via platform primitives, not our code. Coordination state visible in the trace.

#### 03.a Supervisor routing visible in trace

**Status:** Partial Pass
**Evidence:** `[Rishabh]` "Routing decisions visible but downstream execution failed because missing IAM permissions." `[POC: tools.py:329-351]` Routing is implemented via an `AGENT_URLS` dict and an LLM-driven `send_message_tool` — the supervisor *decides* which agent to call based on its system instruction, then the tool looks up the URL. This is **custom-code routing dressed as a tool**, not a platform primitive. `[POC: agent.py:78-80]` The supervisor's only tools are `load_artifacts` and `FunctionTool(send_message_tool)`.

**Advantages on GCP:**
1. Routing decisions **are visible in the trace** as tool-call spans, and decoy-agent interception is verifiable (`[POC: tools.py:405-408]` returns a routing-failure message for decoys) — a nice guardrail pattern.
2. The Agent Registry / `get_remote_a2a_agent` path exists as a more platform-native routing option (the POC deliberately bypasses it for local-emulation support, `[POC README §5.B.3]`).

**Limitations on GCP:**
1. The deployed POC routes via a **custom `send_message_tool` with a hardcoded `AGENT_URLS` dict**, not a platform primitive — "supervisor delegates via platform primitives, not our code" is **not met** by the POC as deployed.
2. Routing is **LLM-instruction-driven** (prose phases in `agent.py:20-41`), so it is non-deterministic; the spreadsheet's "platform primitives" framing implies deterministic delegation, which ADK's supervisor mode does not provide natively.

#### 03.b Parallel worker delegation visible in trace

**Status:** Pass
**Evidence:** `[Trace: 08b300d58ad7d89907a98551abbf9f55]` `[Rishabh]` "Parallel execute_tool spans and aggregation events were fully observable." `[POC: deploy.py]` Deploys 4 engines in parallel via `ThreadPoolExecutor(max_workers=4)` (deployment parallelism). `[POC: orchestrator.py:109,131]` The on-prem POC uses `asyncio.gather` for genuine parallel hierarchy/entity resolution. `[POC: tools.py:469]` Runtime agent execution is streamed via `run_async`.

**Advantages on GCP:**
1. **Parallel `execute_tool` spans and aggregation events are fully observable** in Cloud Trace — the platform represents fan-out/fan-in natively in the span tree (`[Rishabh]`).
2. The on-prem POC's `asyncio.gather` pattern (`orchestrator.py`) shows that real parallel HTTP orchestration works alongside the agent runtime, and is traceable.

**Limitations on GCP:**
1. Runtime parallelism in the supervisor is **LLM-driven tool-call parallelism**, not graph-level fan-out — the LLM decides to call tools in parallel, which is less predictable than explicit graph fan-out (LangGraph's model).
2. There is **no native per-step cost attribution** in the standard logs (`[Gap: B3]`), so parallel-worker cost accounting requires custom extraction of `usage_metadata` per turn — bespoke work.

#### 03.c Coordination state visible in trace

**Status:** Partial Pass
**Evidence:** `[Rishabh]` "Session state observable but cross-trace relationships required custom correlation." `[POC: tools.py:12-64]` Coordination state in the deployed POC is a **module-level `_MOCK_STATE` dict** — shared mutable state holding `products`, `selected_product`, `audience_id`, `sizing`, `active_data_parts`. This is in-memory, non-persistent, and not a real coordination-state store.

**Advantages on GCP:**
1. **Session state is observable** through ADK's Session Service, and session IDs allow logical grouping of related interactions (`[Rishabh]`).
2. The platform's session/memory abstractions (Session Service, Memory Service) provide hooks to make coordination state inspectable if you migrate off in-memory implementations.

**Limitations on GCP:**
1. **Cross-trace relationships require custom correlation** — there is no native cross-trace conversation visualization, so reconstructing a multi-turn coordination narrative needs application-level work (`[Rishabh]`).
2. The deployed POC's coordination state is a **non-persistent `_MOCK_STATE` dict** (`tools.py:12-64`) — this would not survive a worker restart and is explicitly warned against in the README ("deploying sub-agents to multi-worker or cloud environments requires migrating to Firestore-based memory").

#### 03.d MCP and A2A interop visible in trace

**POC Status:** Blocked
**Platform Status:** Partial — A2A trace-context propagation pattern is demonstrated in Google's reference implementation
**Evidence:** `[Rishabh]` "MCP infrastructure unavailable for end-to-end validation." `[POC: tools.py:487-505]` A2A is routed via the GenAI SDK's `agent_engines.get(...).on_message_send(...)` for `projects/...reasoningEngines/...` URLs, or via the `a2a-sdk` HTTP client for other URLs. MCP is a separate HTTP path (`tools.py:143-188`). The two protocols are handled in different code branches with no shared trace context. **Reference-implementation evidence:** `[Weather: gcp/observability/context_propagation.py]` implements a belt-and-suspenders A2A trace-context propagation pattern: (1) `inject_w3c_context_into_headers` injects W3C `traceparent`/`tracestate` on outbound `:streamQuery` POSTs (forward-compatible for when Reasoning Engine inbound extracts W3C natively — already on the roadmap); (2) a `gen_ai.conversation.id` correlation attribute is generated host-side, packed into the ADK `user_id` field (`conv-{uuid}__{user}`), unwrapped by the receiving agent's tool from `ToolContext.session.user_id`, and re-stamped on its own span. Cloud Trace UI filter by that attribute reveals every span across both agents for one A2A call today. `[Weather: host_agent/agent.py:66-79]` shows the live integration.

**Advantages on GCP:**
1. **A2A trace-context propagation across agent boundaries is demonstrated working** in Google's reference implementation today via `gen_ai.conversation.id` correlation, with native W3C single-trace-id arriving when Reasoning Engine inbound extraction lands (`[Weather: gcp/observability/context_propagation.py]`, `[Weather: README "Persona switching"]`). The "unconfirmed open risk" framing earlier in this document was based on Circana POC code that does not implement the pattern, not on a platform limitation.
2. A2A's structured `DataPart` slots (vs. raw text) give cleaner delegation payloads that are more traceable than unstructured prompts; the multi-agent topology map renders the cross-agent edge from `gen_ai.agent.downstream` attributes (`[Weather: README "Trace observability deep-dive"]`).

**Limitations on GCP:**
1. **The Circana POC does not implement this trace-propagation pattern** — its A2A path (`[POC: tools.py:487-505]`) has no equivalent of the weather ref's `context_propagation.py`, so MCP↔A2A trace stitching in the deployed POC is fragmented. Adopting the weather-ref pattern is straightforward.
2. **Native end-to-end single-trace-ID across A2A still awaits a Reasoning Engine roadmap item** (W3C inbound extraction). Until then, cross-agent correlation is via a queryable attribute, not a unified trace tree — slightly less ergonomic in Cloud Trace UI.

---

### Section 04 — Memory Across the Agent Lifecycle

**Pass condition:** All five memory modes (short-term, long-term, compaction, dreaming, semantic layer) operate inside the pilot.

#### 04.a Short-term memory operates inside pilot

**POC Status:** Pass (functional) with cloud-amnesia risk on worker restart
**Platform Status:** Pass — Firestore is the default in Google's reference implementation
**Evidence:** `[Trace: 7da2763e804cc3b46736f1a6bc476abd]` `[Rishabh]` "Agent recalled earlier information and token growth confirmed context accumulation." `[POC: tools.py:444-446]` Local mode uses `InMemorySessionService` + `InMemoryMemoryService`. `[POC README]` "Stateful Context Memory: In the local development runner, session state is managed via InMemoryMemoryService… deploying sub-agents to multi-worker or cloud environments requires migrating to Firestore-based memory." **Reference-implementation evidence:** `[Weather: deploy_agent_engine.py:141-149]` enables `FirestoreSessionService` + `FirestoreMemoryService` **by default**; `--no-firestore` is the escape-hatch flag for projects where corp Org Policy blocks Firestore provisioning. `[Weather: gcp/services/firestore_services.py]` ships a native-first + custom-fallback implementation conforming to `BaseSessionService`/`BaseMemoryService` (`_CustomFirestoreSessionService` with `sessions/{app}/{user}/{sid}` Firestore document layout).

**Advantages on GCP:**
1. **Session context accumulation works natively** — the agent recalls earlier turns and token growth provides evidence of memory retention (`[Rishabh]`).
2. **Firestore session/memory is the default** in Google's reference implementation, not an aspirational migration — `deploy_agent_engine.py` wires it by default and degrades gracefully when Org Policy blocks Firestore. The platform-level migration from `InMemoryMemoryService` is a single-flag change with a working reference, not a research project.

**Limitations on GCP:**
1. **Cross-turn relationships require custom correlation** — each turn emits as an independent trace, so multi-turn memory visualization is not native (`[Rishabh]`).
2. The Circana POC uses **`InMemoryMemoryService`** in its local-execution fallback (`[POC: tools.py:444-446]`); the production-safe Firestore wiring is documented but **not adopted by the Circana POC**, despite being the default in Google's other reference implementation.

#### 04.b Long-term memory operates inside pilot

**POC Status:** Not Exercised in Circana POC (the repo name is misleading)
**Platform Status:** Partial — Firestore-backed long-term memory pattern shown in reference; Gemini Memory Bank still not wired
**Evidence:** `[Rishabh]` "No persistent memory store was configured." `[Gap: B4]` "Long-term memory: preferences (e.g. preferred partner) are lost on new chats." `[POC: tools.py:444-446]` Despite the repo name `..._session_longTermMemory`, the deployed code uses `InMemoryMemoryService`, not the Gemini Enterprise Memory Bank. `[POC README §1.8]` claims "Gemini Enterprise Memory Bank to extract and recall long-term user preferences" but the gap analysis contradicts this: long-term memory is a documented *gap*, not a feature. **Reference-implementation evidence:** `[Weather: gcp/services/firestore_services.py:159-198]` ships `_CustomFirestoreMemoryService.add_session_to_memory` — a documented compaction hook that summarizes session state and persists to `memories/{app}/{user}/{mid}` Firestore documents. This is not the managed Gemini Memory Bank, but it is a working durable long-term-memory pattern.

**Advantages on GCP:**
1. The **Gemini Enterprise Memory Bank** is a documented platform service for long-term, cross-session user preference extraction — the *managed capability exists* in the platform even though neither implementation wires it up.
2. **A durable Firestore-backed long-term memory pattern is demonstrated** in Google's reference implementation (`[Weather: gcp/services/firestore_services.py]`), with a compaction hook ready to consume — so a Circana team can ship long-term memory without waiting for Memory Bank integration.

**Limitations on GCP:**
1. **Neither the Circana POC nor the weather reference wires up the managed Gemini Memory Bank** — the integration discipline (extract preferences → consolidate → recall on session start) is left to the developer in both. Validating the managed Memory Bank end-to-end is an open re-test.
2. The Circana POC's repo name advertises long-term memory but the **deployed code does not implement it at all** — neither the managed Memory Bank nor the weather-ref's Firestore-backed pattern. A cautionary signal that README claims must be re-validated against deployed code.

#### 04.c Compaction visible as discrete trace event

**Status:** Not Exercised
**Evidence:** `[Rishabh]` "Compaction workflows were not implemented independently." `[Gap: B4]` mentions memory inspection and long-term consolidation but not compaction as a trace event.

**Advantages on GCP:**
1. Custom workflows can be made into first-class trace events via custom semantic attributes (see 04.d dreaming), so compaction *could* be rendered visible with engineering.
2. The span-attribute model is flexible enough to mark compaction events queryable.

**Limitations on GCP:**
1. **Compaction is not a native ADK capability** — it would require custom engineering and instrumentation, so "operates inside the pilot" is not met.
2. No evidence that GCP provides automatic context-window compaction with trace visibility — this would be build-work, not platform consumption.

#### 04.d Dreaming visible as discrete trace event

**Status:** Pass (with custom implementation)
**Evidence:** `[Trace: d84a15017ccd4ea3c3a25f2c88825e42]` `[Rishabh]` "Dreaming appeared as a dedicated execute_tool span with custom semantic attributes (consolidation type, turn count, summary length, prompt identifier, and prompt version)."

**Advantages on GCP:**
1. **Custom semantic attributes can be queried** in Cloud Trace, so custom workflows like dreaming become first-class trace events — the attribute model is genuinely extensible (`[Rishabh]`).
2. Prompt metadata can be attached manually to dreaming spans, showing that disciplined teams can build lineage on top of the platform.

**Limitations on GCP:**
1. **Dreaming is not a native ADK capability** — it requires custom engineering and instrumentation (`[Rishabh]`), so this pass is a credit to the implementer, not the platform.
2. The custom nature means there is **no consistency guarantee** across teams — every team would implement dreaming differently, with no platform-enforced contract.

#### 04.e Semantic layer integrates with retrieval

**POC Status:** Blocked — `SemanticLayerAgent` is a dummy placeholder
**Platform Status:** Partial — Vertex AI RAG capability fully demonstrated in reference implementation; blocked by IAM in pilot project
**Evidence:** `[Rishabh]` "RAG permissions unavailable and retrieval integration could not be validated." `[POC: tools.py:346]` `SemanticLayerAgent` is registered with a `projects/dummy/...` URL — it is a placeholder, not deployed. `[POC: sub_agents/semantic_layer_agent.py]` exists but routes to dummy endpoints. **Reference-implementation evidence:** `[Weather: gcp/retrieval/weather_rag.py:155-201]` `create_or_get_rag_corpus()` provisions a Vertex AI RAG corpus via `rag.create_corpus(display_name="weather-knowledge-corpus", backend_config=rag.RagVectorDbConfig(vector_db=rag.RagManagedVertexVectorSearch()))`, seeds it with `rag.upload_file`, and builds a configured `VertexAiRagRetrieval(similarity_top_k=3, vector_distance_threshold=0.5)` ADK tool. `[Weather: weather_agent/agent_rag.py]` wires it into a standalone RAG agent that participates in the same OTel pipeline as other tools.

**Advantages on GCP:**
1. **Vertex AI Vector Search + RAG corpora are demonstrated end-to-end** in Google's reference implementation (`[Weather: gcp/retrieval/weather_rag.py]`) — corpus provisioning, document seeding, ADK tool wiring, and OTel span emission all in one ~200-line module. The retrieval capability is not a maybe; it's shipping reference code.
2. RAG calls emit `gen_ai.tool.name = retrieve_weather_knowledge` + `gen_ai.system = vertex_ai` spans with truncated retrieved chunks as span events (`[Weather: README "Trace observability for RAG calls"]`), giving filterable p95 latency / hit-rate metrics in Trace Explorer.

**Limitations on GCP:**
1. **Blocked by `aiplatform.ragCorpora.query` IAM permissions in the Circana pilot project** — this is a project-IAM gap, not a capability gap (`[Rishabh]`). Once permissions are granted, the weather-ref pattern lifts and shifts.
2. The Circana POC's `SemanticLayerAgent` is a **dummy placeholder** (`tools.py:346`) with no real wiring — so even if RAG permissions were granted today, build work remains in the Circana POC. Adopting the weather-ref pattern is the shortest path.

---

### Section 05 — MCP Integration Over Private Connectivity

**Pass condition:** Platform calls an MCP inside Circana network over private connectivity. Documented setup, no bespoke vendor engineering required.

#### 05.a MCP called inside Circana network over private connectivity

**Status:** Blocked
**Evidence:** `[Rishabh]` "Private connectivity and MCP infrastructure unavailable." `[Deploy: MCP server]` The MCP server is deployed to Cloud Run with `--no-allow-unauthenticated` but is reachable over the **public internet** (authenticated). `[Gap: B5]` "Private path: Enforce Cloud Run ingress control to internal-only and set up Serverless VPC Access / VPC Service Controls so Vertex AI Agent Engine communicates with the container entirely inside your private cloud network." — not done. `[POC: combined_architecture_design.md §6]` lists three options (Transit VM proxy, PSC, Local mocking); the pilot used the local-mocking/public-authenticated path.

**Advantages on GCP:**
1. GCP offers the **right primitives** for private MCP connectivity — **Serverless VPC Access**, **VPC Service Controls**, and **Private Service Connect** — so the path to "inside Circana network" exists architecturally.
2. Cloud Run ingress can be locked to `internal-only`, and ID-token auth gives a defense-in-depth layer even before private networking is configured.

**Limitations on GCP:**
1. **The pilot did not implement private connectivity** — the MCP server is public-internet-authenticated, so "called inside Circana network over private connectivity" is **not met** (`[Gap: B5]`).
2. Setting up VPC Service Controls / Serverless VPC Access for Agent Engine → Cloud Run is **non-trivial networking engineering** — it is exactly the "bespoke vendor engineering" the spreadsheet asks to avoid (see 05.c).

#### 05.b Setup documented

**Status:** Partial Pass
**Evidence:** `[Deploy: DEPLOYMENT_GUIDE.md]` Tim's deployment guide thoroughly documents the MCP server deploy, Agent Engine deploy, portal deploy, IAM roles, gotchas, and config. `[Rishabh]` "Deployment and setup procedures were documented but not fully validated end to end." `[POC README §6]` Google's README documents setup from scratch.

**Advantages on GCP:**
1. **Deployment is well-documented** — both Google's README and Blackstraw's `DEPLOYMENT_GUIDE.md` provide step-by-step instructions with verification commands, enabling any engineer to reproduce the deployment.
2. The `setup_gcp.sh` one-time script automates API enablement, GCS bucket creation, and IAM grants — a reasonable starting scaffold.

**Limitations on GCP:**
1. Documentation covers the **public-authenticated path**, not the private-connectivity path that the spreadsheet requires — so setup is documented for the wrong deployment shape.
2. The documentation reveals **significant friction** (10 gotchas in `DEPLOYMENT_GUIDE.md §13`), including `gcloud` PATH issues, `sys.exit()` crashes, interactive base-image prompts, `LOCATION=us` vs `us-central1` mismatches, and ADC expiry — indicating the setup is not yet smooth.

#### 05.c No bespoke vendor engineering required

**POC Status:** Fail — Circana POC required significant bespoke engineering for its chosen pattern
**Platform Status:** Partial — standard `MCPToolset` pattern is not bespoke; private-path / identity-delegation are platform gaps
**Evidence:** `[Rishabh]` "Additional infrastructure and networking engineering were required." `[Deploy: §13]` 10 gotchas encountered. `[POC: tools.py:87-188]` `call_mcp_tool` is a 100-line custom adapter with three fallback strategies (Agent Registry → HTTP POST → local stdio subprocess) — bespoke glue. `[POC: deploy_mcp.py]` Required rewriting `sys.exit()` to `return 1`, adding `--clear-base-image`, and Dockerfile renaming. `[Gap: B5,B6]` Private path and identity delegation both require additional engineering. **Reference-implementation evidence:** `[Weather: weather_agent/agent.py:190-198]` uses the standard ADK pattern — a single `MCPToolset(StdioConnectionParams(StdioServerParameters(command="npx", args=...)))` declaration. No 100-line adapter, no tri-fallback chain. The Circana POC's bespoke glue is a property of its chosen approach, not a platform requirement.

**Advantages on GCP:**
1. The **standard ADK `MCPToolset` pattern is not bespoke glue** — Google's reference implementation shows MCP integration as a one-call declaration (`[Weather: weather_agent/agent.py:190-198]`). The Agent Registry + `get_mcp_toolset` is an additional discovery layer on top.
2. Cloud Run + ID-token auth is a relatively low-ceremony hosting model for MCP servers compared to building a custom container orchestrator.

**Limitations on GCP:**
1. **The Circana POC chose a non-standard pattern** (HTTP fallback with three strategies) and incurred the bespoke-engineering cost as a result. The 10 gotchas are real deployment friction. The standard pattern would have avoided most of them — but note the unresolved question from Section 01.a about whether the standard pattern actually works in the Reasoning Engine container.
2. **Private-path enforcement and end-to-end user-identity delegation are genuine platform gaps** — the gap analysis lists them as **Priority Next Steps** (`gap_analysis.md 🚀`), and even Google's reference implementation does not solve them. These are not implementation-choice gaps; they are real build-work required on top of any GCP deployment.

---

### Section 06 — End-to-End Identity Propagation

**Pass condition:** End-user identity reaches the MCP tool call. Visible in the trace. Works in both deployment patterns.

#### 06.a End-user identity reaches MCP tool call

**Two-part verdict:**
- **Per-agent AGENT_IDENTITY (dedicated runtime SA):** **POC Status:** Not adopted. **Platform Status:** Pass — demonstrated in reference impl.
- **End-user identity propagation (Entra → JWT → MCP):** **POC Status:** Blocked. **Platform Status:** Blocked — unbuilt in both implementations.

**Evidence:** `[Rishabh]` "Dependent on MCP and identity infrastructure." `[POC: tools.py:96-110]` `get_cloud_run_auth_headers` fetches a Google **ID token via `google.auth.default()`** — Vertex AI's default agent SA (DEVELOPER_IDENTITY pattern), not a dedicated per-agent runtime SA, and not the end-user's identity. `[Gap: B6]` "The MCP tool queries the database using a master VM service account, not the logged-in user's identity." `[POC: combined_architecture_design.md §7]` describes Entra ID federation with `offline_access` refresh tokens, but `gap_analysis.md` admits "Entra federation: Fake session user ID." **Reference-implementation evidence for per-agent AGENT_IDENTITY:** `[Weather: deploy_agent_engine.py:104,111,116,182]` pins a dedicated per-agent runtime SA via `create_kwargs["service_account"] = "weather-agent-runtime@..."` / `"host-agent-runtime@..."`; `[Weather: gcp/iam/setup_service_account.ps1]` provisions these SAs with least-privilege bindings (`roles/aiplatform.user`, `roles/datastore.user`, `roles/cloudtrace.agent`, `roles/monitoring.metricWriter`, `roles/logging.logWriter`). This is the PDF's AGENT_IDENTITY pattern, fully implemented. **End-user identity propagation:** neither the Circana POC nor the weather reference implements Entra → user JWT → MCP forwarding. The weather agent uses dedicated per-agent SAs but does not propagate end-user identity into the tool call.

**Advantages on GCP:**
1. **Per-agent AGENT_IDENTITY is demonstrably implementable** — Google's reference implementation pins a dedicated runtime SA per agent at deploy time with `--no-custom-sa` as the graceful-fallback flag for restrictive Org Policies (`[Weather: deploy_agent_engine.py:79-91,182]`). This gives each agent a cryptographically-attested identity for least-privilege auditing.
2. The A2A SDK's `header_provider` hook (`[POC: tools.py:119]`) is a documented injection point for forwarding user identity tokens — the *mechanism* to propagate user identity exists; the *content* (validated Entra JWT) is what's unbuilt.

**Limitations on GCP:**
1. **The Circana POC uses neither per-agent AGENT_IDENTITY nor user-identity propagation** — `google.auth.default()` produces a default Vertex AI agent SA token (`[POC: tools.py:96-110]`, `[Gap: B6]`). Adopting the weather-ref's per-agent SA pattern is straightforward; user-identity propagation is genuinely new build work.
2. **End-user identity propagation (Entra → JWT → MCP) is unbuilt in both implementations.** Entra ID federation is "fake session user ID" per `gap_analysis.md`, and the weather reference does not address it at all. This cross-IdP flow Circana would need (Microsoft Entra → GCP user-JWT → MCP server validates → impersonates user GCP IAM role) is the most significant unsolved identity gap.

#### 06.b Identity propagation visible in trace

**Status:** Blocked
**Evidence:** `[Rishabh]` "Dependent on MCP and identity infrastructure." No trace generated. Since 06.a is blocked, 06.b is too.

**Advantages on GCP:**
1. Cloud Trace's custom-attribute model *could* carry user-identity claims as span attributes if the `header_provider` forwarded them — the trace store is flexible enough.
2. Cloud Logging captures Cloud Run request logs with authenticated principals, giving an audit-trail *side channel* for identity even without in-trace visibility.

**Limitations on GCP:**
1. **No trace was generated** for identity propagation because the capability is not implemented — so visibility is unvalidated.
2. There is **no native identity-propagation trace feature** — it would be custom instrumentation, not a platform guarantee.

#### 06.c Works in both deployment patterns

**Status:** Blocked
**Evidence:** `[Rishabh]` "Could not be validated without MCP infrastructure." `[Deploy]` Two deployment patterns exist: (1) on-prem Flask POC, (2) cloud Agent Engine POC. Neither implements end-to-end user identity. `[POC: combined_architecture_design.md §3]` describes hybrid (GCP + on-prem Kubernetes) with federated token propagation, but this is design, not deployed code.

**Advantages on GCP:**
1. The **hybrid deployment design** (Agent Engine on GCP + on-prem agent pods, `[combined_architecture_design.md §3]`) anticipates both patterns and defines a federated-token-propagation model — the architecture is thought through.
2. A2A over HTTP/gRPC is pattern-agnostic, so the same delegation protocol *could* work in both on-prem and cloud patterns.

**Limitations on GCP:**
1. **Neither pattern implements end-to-end user identity** — the on-prem POC uses an `X-Client-Id` header for IRI (`[Deploy: on-prem .env]`), and the cloud POC uses service-account tokens — so "works in both" is unproven.
2. The hybrid design is **not deployed code** — it is architecture documentation, so validating it would require build work the pilot did not do.

---

### Section 07 — Tracing and Observability

**Pass condition:** Trace shows agents, MCP tools, skills, decisions, inputs, outputs, and errors needed to determine pass/fail.

#### 07.a Agent events visible in trace

**Status:** Pass
**Evidence:** `[Rishabh]` "Invocation, invoke_agent, call_llm, and execute_tool spans were visible." `[Trace: c726b93cbb1ef459a762a2ab27cb6774]` and related traces.

**Advantages on GCP:**
1. **Comprehensive native span vocabulary** for agent events (`invoke_agent`, `call_llm`, `generate_content`, `execute_tool`) is generated automatically — best-in-class native observability for conversational agents.
2. The hierarchical span tree makes agent execution flow easy to follow without custom instrumentation.

**Limitations on GCP:**
1. Tracing **requires explicit enablement** — it is not on by default, so a missed flag means zero observability (`[Rishabh]`).
2. Custom tools require **additional instrumentation** to appear as spans, so "agent events visible" is true for ADK-native events but incomplete for custom logic.

#### 07.b MCP tool events visible in trace

**Status:** Blocked
**Evidence:** `[Rishabh]` "MCP tool execution could not be validated." `[POC: tools.py:143-188]` MCP calls are HTTP POSTs to Cloud Run — they produce Cloud Run request logs, not agent-trace spans (no OTel context propagated over the HTTP POST in the fallback path).

**Advantages on GCP:**
1. MCP calls do produce **Cloud Run request logs** with latency and status, giving a side-channel observability path.
2. The Agent Registry `get_mcp_toolset` path *could* generate native spans if it worked end-to-end — the potential is there.

**Limitations on GCP:**
1. **MCP tool events did not surface in the agent trace** in the deployed POC — the HTTP-fallback path does not propagate trace context, so MCP calls are invisible in Cloud Trace.
2. Correlating Cloud Run logs with agent traces requires **manual timestamp/trace-ID correlation** — bespoke work that breaks the "single trace shows everything" ideal.

#### 07.c Skill events visible in trace

**POC Status:** Partial Pass — `AgentCard` skill metadata exists but no runtime span linkage
**Platform Status:** Partial Pass — per-tool span instrumentation pattern shown in reference impl
**Evidence:** `[Rishabh]` "Custom workflows appeared as execute_tool spans but no first-class skill abstraction existed." `[POC: agent.py:97-147]` `AgentCard` skills are **metadata** (id, name, description, tags, examples) for agent discovery — not runtime-traceable entities. **Reference-implementation evidence:** `[Weather: gcp/observability/otel_setup.py:153-157, 177-189]` ships a `start_tool_span(tool_name)` helper that emits an `execute_tool {tool_name}` span with `gen_ai.tool.name` + `gen_ai.operation.name` semantic-convention attributes. `[Weather: weather_agent/agent.py:60,86,132,160]` wraps every tool body with this helper, so each tool invocation is a queryable span with skill-like identity. Adding `skill.id` as a span attribute on top is a one-line discipline.

**Advantages on GCP:**
1. **Per-tool span instrumentation with GenAI semantic conventions is a clean, documented pattern** (`[Weather: gcp/observability/otel_setup.py]`) — `start_tool_span(...)` + `set_attribute("skill.id", ...)` gives skill-level lineage with no managed service required.
2. The **AgentCard skill metadata** model (`agent.py:97-147`) gives a clean catalog of agent capabilities for discovery; combining it with per-span `skill.id` closes the discovery + runtime-lineage loop.

**Limitations on GCP:**
1. **No first-class skill abstraction in the trace model** — skills are agent-card metadata; skill-to-span binding requires the manual discipline above (`[Rishabh]`).
2. The Circana POC does **not** apply this discipline — its `FunctionTool` wrappers use ADK defaults, so skill IDs are not on spans today. Adopting the weather-ref pattern is straightforward but unwired.

#### 07.d Inputs and outputs visible in trace

**Status:** Pass
**Evidence:** `[Rishabh]` "Model metadata and execution details were visible in spans." `[Trace: multiple]`.

**Advantages on GCP:**
1. **Model metadata and execution details are visible** in spans — inputs, outputs, model IDs, and token statistics are captured natively (`[Rishabh]`).
2. This gives strong debugging support for understanding *what* the agent did with *what* input.

**Limitations on GCP:**
1. Cloud Trace **avoids binary/large payloads**, so large inputs/outputs (e.g., big product tables) are truncated or omitted — visibility is text-bounded.
2. For multimodal inputs (attachments), visibility drops to metadata only (see 01.c).

#### 07.e Errors visible in trace

**Status:** Pass
**Evidence:** `[Rishabh]` "Permission denied and failed tool invocations surfaced in traces and logs." `[Deploy: §13]` IAM permission failures were a recurring theme and were visible.

**Advantages on GCP:**
1. **Permission-denied and failed tool invocations surface** in both traces and logs — errors are not swallowed, which is critical for debugging (`[Rishabh]`).
2. The dual trace + log surface gives redundant error visibility, useful for post-incident review.

**Limitations on GCP:**
1. Error visibility depends on the failing component emitting a span/log — custom tools that raise silently can still hide errors.
2. Cross-component error correlation (agent → MCP → DB) still requires manual work when trace context doesn't propagate (see 07.b).

---

### Section 08 — Project-Level Cost and Resource Isolation

**Pass condition:** Costs, resources, quotas, and usage are attributable at project level.

#### 08.a Costs attributable at project level

**Status:** Pass (at project level); **unknown at batch scale**
**Evidence:** `[Rishabh]` "Every span contained project identifiers, model information, and token usage statistics." `[Trace: invocation IDs e-bc5c6e03..., e-c2f633cc..., e-e2decf5d...]`. `[Meeting notes]` Tim: "we haven't actually run really at scale at all… how to observe both cost and scale in terms of the ability of these frameworks to scale to the hundreds of thousands to millions of rows." `[Gap: B3]` "Per-step cost attribution: standard logs don't track token cost per step."

**Advantages on GCP:**
1. **Project attribution is available natively** — every span carries project IDs, model info, and input/output/reasoning token counts, enabling conversation-level cost analysis (`[Rishabh]`).
2. **Reasoning-token visibility** is a notable plus — many platforms hide reasoning tokens; GCP surfaces them for cost accounting.

**Limitations on GCP:**
1. **Per-step token cost is not surfaced in default dashboards** — standard logs don't track cost per step, so building a per-step cost dashboard requires custom extraction of `usage_metadata` and Firestore logging (`[Gap: B3]`, `[Rishabh]`).
2. **Agent Engine idle cost is unclear** — the pilot deployed 4 always-on Reasoning Engines with no documented scale-to-zero story; at Circana's batch scale this is an open cost risk, not a measured data point (`[Meeting notes]`, `[Deploy]`).

#### 08.b Resources isolated at project level

**Status:** Pass
**Evidence:** `[Rishabh]` "Cloud Asset Inventory confirmed project-level isolation."

**Advantages on GCP:**
1. **Cloud Asset Inventory** confirms project-level resource isolation — the GCP project boundary is a clean isolation primitive.
2. Reasoning Engines, Cloud Run services, and GCS buckets are all project-scoped, giving clear resource attribution.

**Limitations on GCP:**
1. Project-level isolation is coarse — **multi-tenant workload isolation** (e.g., per-client or per-business-unit attribution) requires additional folder/org-policy engineering.
2. Shared services (e.g., a single MCP server serving multiple agents) blur project-boundary attribution unless deliberately separated.

#### 08.c Quotas visible at project level

**Status:** Pass
**Evidence:** `[Rishabh]` "Quotas and utilization metrics visible at project level."

**Advantages on GCP:**
1. **Quotas and utilization metrics are visible** at project level in the console — standard GCP capability, reliable.
2. The Vertex AI Agent Platform dashboard tracks QPS, latency, error rates, and container resources (`[POC README §5.D]`).

**Limitations on GCP:**
1. Quota visibility is project-level, not per-agent — a single agent hitting a quota can starve others in the same project.
2. Quota increases for batch workloads (concurrent Agent Engine calls at massive scale) are **untested** — the pilot never hit quota ceilings because it never ran at scale.

#### 08.d Usage reporting available at project level

**Status:** Pass
**Evidence:** `[Rishabh]` "Usage metrics and billing configuration visible."

**Advantages on GCP:**
1. **Usage metrics and billing configuration are visible** — standard GCP billing export to BigQuery is available for detailed analysis.
2. Token-usage statistics on spans enable conversation-level usage reporting.

**Limitations on GCP:**
1. Default dashboards don't surface **reasoning costs** — custom metrics may be required for complete reporting (`[Rishabh]`).
2. Usage reporting is geared to conversational-turn accounting, not batch-job accounting — mapping to "per-UPC attribution cost" would be custom.

---

### Section 09 — Ontology and Entity Resolution

**Pass condition:** Entities resolve consistently across prompts, tools, memory, and retrieval.

#### 09.a Entity IDs and names resolved consistently

**Status:** Pass (with a non-determinism caveat in the on-prem POC)
**Evidence:** `[Trace: 94782e61831fa9b956e3c6e21d10d65b]` `[Rishabh]` "Entity resolution persisted across turns." `[Deploy: §8]` "The IRI Product Entity agent is non-deterministic — the same query sometimes resolves to Parent Company_1 level (works) and sometimes to Brand_1 or Category_1 level (empty member IDs → breaks). Fix applied: filter empty ids and fail fast."

**Advantages on GCP:**
1. Entity resolution **persisted across turns** in the conversational agent — the session-bound entity context is stable (`[Rishabh]`).
2. The on-prem POC's `asyncio.gather` parallel entity resolution (`orchestrator.py:109,131`) demonstrates that parallel entity resolution integrates cleanly with the orchestration layer.

**Limitations on GCP:**
1. The IRI entity resolver is **non-deterministic** — the same query can resolve to different hierarchy levels, breaking downstream sizing (`[Deploy: §8]`). This is an IRI-side issue but it surfaces in the GCP-hosted orchestration.
2. Entity-resolution consistency across **prompts, tools, memory, and retrieval** is only validated for the conversational path — retrieval integration is blocked (09.d), so cross-surface consistency is unproven.

#### 09.b Disambiguation decisions visible

**Status:** Pass
**Evidence:** `[Trace: 94782e61831fa9b956e3c6e21d10d65b]` `[Rishabh]` "Clarification decisions visible through tool arguments and context."

**Advantages on GCP:**
1. **Disambiguation decisions are visible** through tool arguments and context in the trace — the platform represents clarifications as queryable spans.
2. Tool-argument visibility makes it easy to audit *why* an entity was resolved a given way.

**Limitations on GCP:**
1. Disambiguation visibility depends on the agent emitting a tool call — silent LLM-internal disambiguation is not captured.
2. Cross-turn disambiguation narratives require custom correlation (same gap as 03.c).

#### 09.c Ontology mappings visible

**Status:** Not Exercised
**Evidence:** `[Rishabh]` "No ontology layer was configured."

**Advantages on GCP:**
1. The **`SemanticLayerAgent`** is designed into the topology (`combined_architecture_design.md §2.A`) as a shared entity resolver — the ontology pattern is anticipated by the architecture.
2. Spanner is noted as a backing store for "domain ontology/grounding" (`combined_architecture_design.md §4`) — the building blocks exist.

**Limitations on GCP:**
1. **No ontology service or knowledge-graph layer was configured** in the pilot, so ontology mappings are entirely unvalidated (`[Rishabh]`).
2. The `SemanticLayerAgent` is a dummy placeholder (`tools.py:346`), so even the wiring is absent.

#### 09.d Retrieval uses resolved entity

**POC Status:** Blocked
**Platform Status:** Partial — RAG capability fully demonstrated in reference impl; pilot blocked by IAM
**Evidence:** `[Rishabh]` "Blocked by aiplatform.ragCorpora.query permissions and unavailable RAG infrastructure." `[Weather: gcp/retrieval/weather_rag.py]` shows the full provisioning + retrieval pattern working end-to-end against Vertex AI RAG corpora.

**Advantages on GCP:**
1. **Vertex AI Vector Search + RAG corpora are the platform-native retrieval path and are demonstrated end-to-end in the weather reference** — `create_or_get_rag_corpus()` + `build_rag_retrieval_tool()` together provide an idempotent corpus + tool, ready to plug into an agent.
2. The architecture designs the semantic layer to integrate with retrieval (`combined_architecture_design.md §4`), so the *intent* is present; the weather ref shows the implementation pattern.

**Limitations on GCP:**
1. **Blocked by RAG IAM permissions in the Circana pilot project** — a project-config gap, not a platform gap (`[Rishabh]`).
2. The dummy `SemanticLayerAgent` in the Circana POC (`tools.py:346`) means the resolved-entity → retrieval path is unwired in the deployed code, so even with permissions, the Circana POC requires build work. The weather-ref's `weather_rag.py` is a near-drop-in template.

---

### Section 10 — Governance and Agents/Tools Lineage

**Pass condition:** Agent, tool, prompt, skill, and policy versions are identifiable for each run.

#### 10.a Agent version identifiable

**Status:** Pass
**Evidence:** `[Rishabh]` "Reasoning Engine deployment identifiers were traceable." `[Deploy: §3]` Four engine resource names are documented (e.g., `projects/.../reasoningEngines/7143683726067630080`). `[Deploy: §13 gotcha]` Duplicate engines from previous runs exist — versioning is real but housekeeping is manual.

**Advantages on GCP:**
1. **Reasoning Engine deployment IDs are stable, traceable identifiers** — every agent version has a unique resource name, enabling agent-level lineage (`[Deploy]`).
2. Previous deployments remain available for rollback (see 11.d), so agent version history is preserved by the platform.

**Limitations on GCP:**
1. **Duplicate/orphaned engines accumulate** — the deployment guide notes "duplicate engine entries from previous deployment runs" requiring a cleanup script (`scripts/delete_unused_engines.py`), so version hygiene is manual.
2. Agent version is a deployment ID, not a semantic version — mapping "engine 7143683726067630080" to "attribution agent v2.3 with prompt v5" requires external registry discipline.

#### 10.b Tool version identifiable

**POC Status:** Fail — no tool-version metadata at all
**Platform Status:** Partial Pass — span-attribute pattern shown in reference impl (same shape as 02.c / 10.c)
**Evidence:** `[Rishabh]` "Tool metadata visible but no native tool version attribute exists." **Reference-implementation evidence:** the weather agent's `start_tool_span` helper (`[Weather: gcp/observability/otel_setup.py:153-157]`) plus per-tool `set_attribute("tool.version", "...")` lines would give tool-version-as-span-attribute lineage in the same shape as the prompt-version pattern. The weather ref applies the pattern for prompts (02.c, 10.c) but not explicitly for tool versions — the discipline is there, just not extended yet.

**Advantages on GCP:**
1. **Tool metadata is visible** in traces — tool names and arguments are captured natively, giving a foundation for tool lineage.
2. **Span-attribute discipline (the same pattern that works for `prompt.id`/`prompt.version`) extends naturally to `tool.version`** — Google's reference implementation shows the helper machinery; declaring tool versions is one constant per tool file.

**Limitations on GCP:**
1. **No managed tool-version registry → trace linkage exists** — tool lineage relies on the same custom-attribute pattern as prompts (`[Rishabh]`). MCP tools hosted on Cloud Run are versioned by Cloud Run revision, but Cloud Run revision → tool-span correlation requires custom binding.
2. Neither the Circana POC nor the weather reference explicitly attaches `tool.version` to spans — the pattern is unapplied, even though the helper exists.

#### 10.c Prompt version identifiable

**POC Status:** Fail — Circana POC's prompts are inline strings with no version metadata
**Platform Status:** Partial Pass — Google's reference impl applies the `prompt.id`/`prompt.version` span-attribute pattern on every tool call
**Evidence:** `[Rishabh]` "Prompt metadata could be manually instrumented only." `[Meeting notes]` Rishabh: "create version API doesn't version the prompts correctly." `[POC: agent.py:18-67]` Prompts are inline Python strings assembled at agent creation — no version ID, no registry. **Reference-implementation evidence:** `[Weather: weather_agent/agent.py:36-37]` declares `PROMPT_ID = "7282778269173153792"` / `PROMPT_VERSION = "1"`; `[Weather: weather_agent/agent.py:70-71, 96-97, 143-144, 169-170]` attach them as `prompt.id` / `prompt.version` span attributes on every tool call. This is the documented pattern, applied with discipline.

**Advantages on GCP:**
1. **Prompt-version-as-span-attribute is demonstrated working** in Google's reference implementation — `prompt.id`/`prompt.version` set on every span gives queryable prompt lineage today, no managed registry required.
2. The pattern composes with Reasoning Engine deployment IDs (agent-level version, 10.a), giving an "engine X + prompt Y" lineage tuple per trace.

**Limitations on GCP:**
1. **No managed Prompt Management → trace binding exists** — Vertex AI Prompt Management is disconnected from Cloud Trace, and the `create version` API does not version prompts correctly per hands-on testing (`[Meeting notes]`, `[Rishabh]`). The platform capability is "manual span attributes"; there is no managed equivalent yet.
2. The Circana POC does **not** apply the pattern — its prompts are inline strings with no version metadata at all (`[POC: agent.py:18-67]`). Adopting the weather-ref pattern is a one-file change.

#### 10.d Skill identifier visible

**Status:** Partial Pass
**Evidence:** `[Rishabh]` "Workflow identifiers visible but no native skill abstraction exists."

**Advantages on GCP:**
1. Workflow identifiers are visible in traces, so skill-like flows are identifiable at the workflow level.
2. The AgentCard skill metadata (`agent.py:97-147`) provides skill IDs for discovery.

**Limitations on GCP:**
1. **No native skill abstraction** in the trace model — skills are card metadata, not runtime-traceable entities (`[Rishabh]`).
2. Skill-to-run linkage requires custom instrumentation to attach skill IDs to spans.

#### 10.e Policy applied visible

**Status:** Fail
**Evidence:** `[Rishabh]` "Model Armor and Agent Gateway were not configured." `[POC: tools.py:287-317]` **Critical finding:** the deployed POC's `sanitize_content_with_model_armor` is a **local regex-based shim** — it checks for `ignore previous instructions`, `system override`, credit-card and SSN patterns with Python `re`, and raises `ValueError("Model Armor Verdict: BLOCKED")`. This is **not** the Vertex AI Model Armor service. `[POC README §3]` claims "Model Armor Safety Shield… screens for prompt injection, jailbreaks, PII" with a screenshot, but the code is a local regex fallback.

**Advantages on GCP:**
1. **Vertex AI Model Armor is a real managed service** for prompt-injection/jailbreak/PII scanning — the platform *has* the capability the spreadsheet asks for; the POC just didn't wire it up.
2. The `header_provider` / runtime-hook pattern is a documented integration point for inserting Model Armor into the request path.

**Limitations on GCP:**
1. **Model Armor was not configured** in the pilot — the deployed safety shield is a **local regex shim** (`tools.py:287-317`), not the real service, so "policy applied visible" is not just unmet, it is **misleadingly simulated** (`[Rishabh]`, `[POC: tools.py]`).
2. Agent Gateway was also not configured — so policy enforcement and its trace visibility are entirely unvalidated. This is one of the most important gaps for Circana's governance requirements.

---

### Section 11 — DevOps Practices Across Non-PROD and PROD

**Pass condition:** Pilot can be promoted from non-PROD to PROD with repeatable configuration and rollback path.

**Aggregate verdict:** **Partial Pass** — repeatable in principle, friction-laden in practice. Individual sub-criteria pass mechanically, but the 10 documented deployment gotchas, the manual scripting (not managed CI/CD), the orphaned-engine accumulation, and the env-var drift (`us` vs `us-central1`) collectively make this more "Partial" than "Strong" for a Circana audience evaluating production readiness.

#### 11.a Promotion path exists from non-PROD to PROD

**POC Status:** Partial Pass
**Platform Status:** Partial Pass — weather reference shows graceful-degradation flags but deployment is still manual scripting
**Evidence:** `[Rishabh]` "Promotion possible through repeatable deployments and registration updates." `[Deploy: §5]` `deploy.py` and `deploy_mcp.py` automate deployment; `.env` holds resource names. `[Deploy: §13 gotcha 4]` `LOCATION=us` vs `us-central1` mismatch shows environment config is error-prone. **Reference-implementation evidence:** `[Weather: deploy_agent_engine.py:69-91]` ships `--no-firestore` and `--no-custom-sa` graceful-degradation flags explicitly for "deploy when corp Org Policy blocks Firestore and/or IAM bindings" — recognition that real GCP projects have Org Policy friction, with a documented way to ship a partial-but-working deploy and re-enable features later.

**Advantages on GCP:**
1. **Promotion is achievable** through repeatable `deploy.py` runs and Agent Registry updates — the deployment scripts are parameterized by `.env`. The weather reference shows the disciplined version: explicit graceful-degradation flags for Org-Policy-blocked features, with a documented "re-enable later" path.
2. The `setup_gcp.sh` one-time script (Circana POC) and `setup_service_account.ps1` (weather ref) make bootstrapping a new environment straightforward.

**Limitations on GCP:**
1. Promotion is **manual scripting**, not a managed CI/CD pipeline — there is no native "promote engine to PROD" button in either implementation; it's redeploy-and-update-`.env`.
2. Environment config friction (the `us` vs `us-central1` gotcha) shows that environment parity is not enforced by the platform — it relies on operator discipline.

#### 11.b Configuration is repeatable

**Status:** Pass
**Evidence:** `[Rishabh]` "Deployments were deterministic and reusable." `[Deploy: §5]` `deploy.py` deploys 4 engines in parallel deterministically; `.env` captures all config.

**Advantages on GCP:**
1. **Deployments are deterministic and reusable** — the same `.env` + scripts reproduce the same deployment (`[Rishabh]`).
2. Pinned package versions (`DEPLOYMENT_GUIDE.md §10`) ensure dependency reproducibility.

**Limitations on GCP:**
1. Repeatability depends on **manually pinned versions and manual `.env` management** — drift is possible if pins aren't enforced.
2. The deploy scripts required **in-place fixes** (rewriting `sys.exit()`, adding `--clear-base-image`) to become repeatable — out-of-the-box repeatability was not frictionless.

#### 11.c Environment differences are controlled

**Status:** Pass
**Evidence:** `[Rishabh]` "Environment targeting achieved through configuration and environment variables." `[Deploy: §9]` `.env` files separate cloud vs on-prem config.

**Advantages on GCP:**
1. **Environment targeting via env vars** is clean and standard — `.env` files control project, location, URLs, and model IDs.
2. The `LOCAL_MODE=true` switch cleanly swaps all GCP dependencies for local mocks (`[Deploy: §7]`), which is excellent for dev/test parity.

**Limitations on GCP:**
1. Environment differences are controlled by **convention, not enforcement** — nothing prevents a wrong `.env` from pointing a "PROD" deploy at a dev project.
2. The `us` vs `us-central1` gotcha shows env-var mistakes are easy to make and hard to catch before deployment.

#### 11.d Rollback path exists

**Status:** Pass
**Evidence:** `[Rishabh]` "Previous deployments remained available and could be re-registered." `[Deploy: §3]` Previous Reasoning Engines remain deployed; `.env` can be pointed back to prior engine IDs.

**Advantages on GCP:**
1. **Previous deployments remain available** — old Reasoning Engines persist, so rollback is "point `.env` to the old engine ID and restart the portal" (`[Rishabh]`, `[Deploy]`).
2. Cloud Run revisions give the portal and MCP server revision-level rollback natively.

**Limitations on GCP:**
1. Rollback is **manual re-pointing**, not a managed rollback — the operator must know the previous engine ID and update `.env`.
2. Orphaned engines accumulate (see 10.a), so rollback options exist but the engine inventory gets noisy without cleanup discipline.

---

## 5. GCP Services Evaluated but Not Exercised (Extension Candidates)

These are platform capabilities the POCs *claim* or *design for* but did **not** wire up in deployed code. They are the most important areas to test before concluding GCP fits Circana.

| Service | POC status | What it would take to validate | Circana relevance |
|---|---|---|---|
| **Vertex AI Model Armor** (real service) | **Faked** — `tools.py:287-317` is a local regex shim, not the managed service | Wire the actual Model Armor API into the supervisor's pre/post hooks; verify jailbreak/PII blocks and trace visibility | **High** — governance/guardrails are a Circana ask (Denesh, meeting notes) |
| **Agent Gateway** | Not configured | Deploy and route agent traffic through it; verify policy enforcement and tracing | **High** — governance layer |
| **Vertex AI Vector Search / RAG corpora** | Blocked by `aiplatform.ragCorpora.query` permissions | Grant permissions; wire `SemanticLayerAgent` to real retrieval; validate entity→retrieval | **High** — semantic layer + retrieval grounding |
| **Gemini Enterprise Memory Bank** (long-term) | Not implemented (repo name notwithstanding) | Migrate `InMemoryMemoryService` → `FirestoreMemoryService` / Memory Bank; validate cross-session recall | **Medium** — portal personalization |
| **Firestore session/memory** | Documented, not deployed | Deploy Firestore-backed Session/Memory services; validate multi-worker survival | **High** — production-readiness |
| **VPC Service Controls / Serverless VPC Access** | Not configured (MCP is public-authenticated) | Lock Cloud Run to internal-only; configure VPC SC; validate Agent Engine → MCP over private path | **High** — private connectivity requirement |
| **SPIFFE Agent Identity** | Claimed in README, unverified in deployed code | Deploy engines with `identity_type: AGENT_IDENTITY`; verify attested identity in audit logs | **Medium** — least-privilege auditing |
| **Microsoft Entra ID federation** | "Fake session user ID" per gap analysis | Implement real OIDC federation via Discovery Engine authorization slots; validate user-token propagation to MCP | **High** — Circana is Entra/Active Directory shop |
| **Batch / high-volume fan-out on Agent Engine** | Not tested at all | Load test 50K–1M equivalent tasks through Agent Engine; measure cost, latency, quota | **Critical** — Circana's primary workload |

---

## 6. Extension to Circana's Use Case (Beyond the POC)

The POCs demonstrate a **conversational retail-activation portal**. Circana's real workloads are broader. This section extends the evaluation to the use cases the POCs did not cover.

### 6.1 Batch attribution at scale (50K–1M+ data poitns) — **UNPROVEN**

The POCs are single-user, conversational, mock-data demos. Circana's Blackstraw attribution runs process **50,000–1,000,000+ UPCs** per run through a deterministic pipeline: load → preprocess → hybrid retrieve (ChromaDB + BM25) → constrained LLM extraction → evaluate.

**GCP-relevant questions the pilot does not answer:**
- Is **Vertex AI Reasoning Engine** cost-effective for batch fan-out, or is it priced/architected for conversational always-on workloads? The pilot deployed 4 always-on engines with **no documented scale-to-zero story** and **no batch-run cost data** (`[Meeting notes]`, `[Deploy]`).
- Can Agent Engine handle **thousands of concurrent `stream_query` calls** for batch extraction, or will quota/concurrency limits bite? Untested.
- Does the **LLM-routed supervisor pattern** (ADK's default) introduce non-determinism and extra supervisor-token cost that batch pipelines don't want? Yes, per the framework comparison — batch pipelines want **deterministic graph execution**, not LLM-decided routing.

**[Inferred] position:** Agent Engine is conversational-runtime-shaped. For batch attribution, the better GCP pattern is likely **Cloud Run jobs / Batch + Vertex AI model calls** orchestrated by LangGraph (or plain Python), **not** Agent Engine. The pilot provides no evidence to confirm or refute this — it is the #1 gap to close before recommending GCP for Circana's primary workload.

### 6.2 Emiri API integration — **GCP agent framework adds no value here**

Emiri is Circana's NL analytics platform. The **negotiation engine** use case calls `getEmiriEntityResponseProd` directly (skipping Intent), which is internally a **parallel fan-out** (Product ∥ Geography ∥ Other ∥ Filter) with template-driven `azure-gpt-4o` calls — a staged REST pipeline, not an LLM-supervisor pattern (`docs/emiri/`).

**GCP fit:** ADK/Agent Engine would wrap an LLM-routed supervisor around APIs that are already deterministic and staged — adding non-determinism and token cost without benefit. The right pattern is **LangGraph tool nodes** (or plain `requests`) calling Emiri's APIs, with **Azure OpenAI** for the LLM (to align with Emiri's existing `azure-gpt-4o` path). This is cloud-agnostic and does not require GCP's agent framework.

**The POCs do not touch Emiri at all**, so the pilot offers no evidence for or against GCP for this layer. The framework comparison covers this in detail.

### 6.3 IRI Advantage LD hierarchy API — **partially exercised by the on-prem POC, but a different API**

The on-prem POC calls IRI **Liquid Data** endpoints at `analytics-dev.iriworldwide.com/poc/agent/...` with an `X-Client-Id` header. The **IRI Advantage LD** API (`docs/emiri/IRI_ADVANTAGE_API.md`) is a **different** service at `advantage.iriworldwide.com/client3-ld` with **Basic Auth + session-cookie reuse** (`/security/login` → cookie → `getDescendantsAtLevelMembers`).

**GCP fit:** The on-prem POC demonstrates that IRI HTTP orchestration works in Python with `asyncio.gather` parallelism and a polling loop. But it does **not** integrate the Advantage LD API (which uses a different auth scheme and is "not yet integrated into the main orchestrator" per `IRI_ADVANTAGE_API.md`). Integrating Advantage LD is **a LangGraph node or MCP tool** concern, not a GCP-agent-framework concern. GCP's MCP-on-Cloud-Run pattern could host such a tool, but the private-connectivity gap (Section 05) applies.

### 6.4 Where GCP genuinely shines (the conversational portal layer)

For a **marketer-facing HITL portal** — e.g., a "review attribution results, explore cohorts, approve activations" UI — the POCs show GCP is genuinely strong:
- **A2UI** is a real differentiator: agents project interactive HTML widgets (tables, charts, dashboards) into the chat canvas with `postMessage` callbacks for HITL — this is hard to build from scratch and GCP provides it natively (`[POC README §5.C]`, `[POC: components.py]`).
- **A2A** structured delegation with `DataPart` slots is cleaner than raw-text supervisor patterns.
- **Agent Engine + Agent Registry + SPIFFE identity + Cloud Trace** is a cohesive managed stack for conversational agents.
- **Cloud Trace's native GenAI spans** are best-in-class for conversational observability (Section 07).

**Recommendation:** If Circana wants a GCP-hosted conversational portal, the POC validates the platform's *capability* — but the production hardening work (real Model Armor, Firestore memory, private MCP, Entra federation, cost-at-scale) remains open.

---

## 7. Summary Scorecard

Each row now distinguishes **POC strengths/weaknesses** (what the Circana POC ships) from **platform strengths/weaknesses** (what GCP can do today with documented patterns Google has shipped — primarily the weather-agent reference codebase, Section 2.5). The two often differ. The platform column is the right input to "is GCP the right hyperscaler"; the POC column is the right input to "is the Google-supplied Circana POC production-ready as-is."

| # | Section | POC strengths | POC weaknesses | Platform-level strengths (weather-ref + POC) | True platform-level gaps |
|---|---|---|---|---|---|
| 01 | Chat host & MCP apps | A2UI widget rendering; native GenAI spans; persona-as-tool observable | MCP not visible in trace (HTTP fallback); 100-line custom adapter; portal doesn't stream | A2UI strong; standard `MCPToolset` stdio in weather ref; per-tool spans | No multimodal binary via `stream_query`; tracing not default; TTFT chunk-event claim needs re-test (weather README vs. Rishabh) |
| 02 | Prompt orchestration | Orchestration steps visible; phase-state-machine enforceable | No prompt-version metadata at all; mock MCPs only; LLM-routed (non-deterministic) | Prompt-version-as-span-attribute pattern shown in weather ref | No managed Prompt Management → trace binding |
| 03 | Supervisor flow | Parallel spans observable; decoy interception works | Custom AGENT_URLS routing; `_MOCK_STATE` coordination; no A2A trace context | A2A trace-context propagation (W3C + `gen_ai.conversation.id`) shown in weather ref | Native single-trace-id across A2A awaits Reasoning Engine roadmap |
| 04 | Memory | Short-term works; custom dreaming traceable | `InMemoryMemoryService` in deployed code; long-term not implemented; semantic layer is dummy | Firestore session/memory is default in weather ref; durable long-term Firestore pattern shown | Managed Gemini Memory Bank unwired in both; compaction not a native primitive |
| 05 | MCP private connectivity | Cloud Run IAM auth works | MCP is public-authenticated; 100-line custom adapter; 10 deployment gotchas | Standard `MCPToolset` is not bespoke; VPC SC / PSC primitives exist | Private MCP path unbuilt in both; standard pattern's actual viability in Reasoning Engine container is contested (Section 01.a) |
| 06 | Identity propagation | `header_provider` hook exists | Default Vertex SA, not per-agent SPIFFE; Entra federation fake | Per-agent dedicated runtime SAs (AGENT_IDENTITY) demonstrated in weather ref with least-privilege bindings | End-user identity propagation (Entra → JWT → MCP) unbuilt in both |
| 07 | Tracing & observability | Best-in-class native spans; errors surface in trace+log; I/O visible | MCP events not in POC's trace path; no per-tool span discipline | OTel pipeline + per-tool spans + multi-agent topology demonstrated in weather ref | Binary payloads truncated; tracing not default; TTFT contested |
| 08 | Cost & resource isolation | Project attribution native; reasoning-token visibility; quotas visible | Per-step cost not in default dashboards | Same as POC — weather ref does not test batch either | Agent Engine idle cost unknown; batch-scale cost untested |
| 09 | Ontology & entity resolution | Entity resolution persists in session; disambiguation visible | Ontology not configured; SemanticLayerAgent is dummy; IRI resolver non-deterministic | Vertex AI RAG corpus + retrieval tool fully demonstrated in weather ref | Ontology layer / knowledge graph unbuilt in both |
| 10 | Governance & lineage | Agent version (engine ID) traceable | Model Armor **faked** (regex shim); no prompt/tool version metadata; Agent Gateway not configured | Per-span `prompt.id`/`prompt.version` pattern shown in weather ref; per-tool span helper available | Real in-agent Model Armor punted to gateway even in weather ref; Agent Gateway unbuilt in both; no managed prompt/tool registry → trace binding |
| 11 | DevOps | Deterministic deployments; rollback via old engines; LOCAL_MODE parity; env-var targeting | Manual scripting not managed CI/CD; orphaned engines; env friction (`us` vs `us-central1`); 10 in-place fixes needed | Weather ref's `--no-firestore` / `--no-custom-sa` graceful-degradation flags show good ops discipline | Still manual scripting in both; no managed promotion pipeline |

---

## 8. Key Takeaways for Circana

1. **GCP is a strong candidate for the conversational HITL portal layer** — A2UI, A2A, Agent Engine, and Cloud Trace are a cohesive, genuinely impressive stack for marketer-facing interactive agents. The POCs prove the *capability*, and the weather reference codebase (Section 2.5) shows the platform ceiling is meaningfully higher than the Circana POC alone displays.
2. **GCP is unproven for Circana's batch workloads** — the #1 risk. No batch-scale, no cost-at-scale, no scale-to-zero evidence in either the Circana POC or the weather reference. Agent Engine is conversational-runtime-shaped. **Do not let the portal demo substitute for load/cost testing at 50K–1M UPCs.**
3. **Distinguish POC implementation gaps from platform gaps** (Section 2.5 + Section 7 scorecard). Most of the Circana POC's weaknesses — `InMemoryMemoryService` instead of Firestore, default service account instead of per-agent AGENT_IDENTITY, no prompt-version metadata, custom 100-line MCP adapter, no A2A trace propagation, no per-tool span discipline, dummy `SemanticLayerAgent` — are **implementation choices Google's pilot team made**, not platform limits. The weather-agent reference codebase implements all of these with documented patterns. Quoting Circana the POC's gaps as "platform gaps" would understate GCP.
4. **The true platform-level gaps that remain after weather-ref evidence** are: (a) real in-agent Model Armor (even the weather README punts to "apply at the Apigee/Agent Gateway layer"), (b) end-user identity propagation from Entra ID through to MCP tool calls, (c) multimodal binary attachments through `stream_query`, (d) batch / cost-at-scale, and (e) deterministic graph routing as a platform primitive. These are the gaps that should actually drive a hyperscaler decision — they apply to GCP-the-platform, not just to the Circana POC.
5. **Several "showcased" capabilities are faked or unwired in the deployed Circana POC** — most critically Model Armor (local regex shim, `tools.py:287-317`) and long-term memory (repo name says `longTermMemory`, code uses `InMemoryMemoryService`). README claims diverge from deployed code. This is not fraud — it's a pilot — but it means **capability claims must be re-validated against real services before being quoted to Circana.** The weather reference's own admissions (Model Armor punted to gateway, attachments are description strings not bytes) provide a useful sanity check on what the platform truly delivers in-agent vs. via decoupled infrastructure.
6. **Governance is the weakest area** (Section 10) — in-agent Model Armor wiring is missing in both implementations; Agent Gateway is unconfigured in both; prompt/tool/skill/policy lineage relies on the manual span-attribute pattern even in Google's reference. For Circana's governance asks (Denesh's meeting-notes criteria: "who is accessing my agents? guardrails? LLM interception?"), GCP requires deliberate build work on top of whatever the POC ships.
7. **Private connectivity and end-to-end user identity are real platform-build work** (Sections 05–06) — unbuilt in both the Circana POC and the weather reference. Both require deliberate engineering on top of any GCP deployment.
8. **The right architectural framing is three layers** (Section 3): LangGraph for batch + Emiri API orchestration (cloud-agnostic, Azure OpenAI for LLM); GCP for the conversational portal layer if Circana chooses GCP for that surface; runtime/models decided separately. **Don't pick one framework for all three.**
9. **The two highest-priority re-tests before quoting verdicts** are: (a) whether `MCPToolset` with `npx`-stdio actually works in the deployed Reasoning Engine container (Section 01.a — direct contradiction between weather reference's declared pattern and Rishabh's "lacks Node.js" finding), and (b) whether chunk-arrival span events / TTFT are computable as the weather README claims (Section 01.b — direct contradiction with Rishabh's "no TTFT" finding). One of each pair is wrong; the verdict shape on Sections 01.a and 01.b depends on which.

---

## Appendix A — Evidence Index

| Source | Path | Used for |
|---|---|---|
| Meeting notes | `docs/meetings/meeting_20260626.md` | Evaluation ask, methodology, batch-scale concern, prompt-mgmt finding |
| Rishabh Expanded report | `docs/rishabh/GCP_Hyperscaler_Evaluation_Report_Expanded.docx.md` | Grounded findings + trace IDs for ~7 criteria — tested against the **weather-agent reference codebase**, not the Circana POC (see Section 2.5) |
| Rishabh Full report | `docs/rishabh/GCP_Hyperscaler_Evaluation_Full_Report.docx.md` | Section structure (templated; not used as evidence) |
| Deployment guide | `docs/deployment/DEPLOYMENT_GUIDE.md` | Hands-on deployment findings, 10 gotchas, live resource IDs, IAM friction |
| **Weather agent reference codebase** | `weather_agent_codebase/` | Platform-capability ceiling: Firestore session/memory by default, per-agent dedicated SAs, per-tool span instrumentation with `prompt.id`/`prompt.version`, W3C + `gen_ai.conversation.id` propagation across A2A, native `MCPToolset` stdio, Vertex AI RAG corpus + retrieval tool |
| Weather agent README | `weather_agent_codebase/README.md` | TTFT-via-span-events claim, attachment-via-GCS-content_ref claim, multi-agent topology pattern, Model-Armor-at-the-gateway admission |
| Weather agent OTel setup | `weather_agent_codebase/gcp/observability/otel_setup.py` | Cloud Trace + Cloud Monitoring exporters; `start_tool_span` / `start_llm_span` GenAI semconv helpers |
| Weather A2A context propagation | `weather_agent_codebase/gcp/observability/context_propagation.py` | W3C `traceparent` injection + `gen_ai.conversation.id` belt-and-suspenders cross-agent correlation |
| Weather Firestore services | `weather_agent_codebase/gcp/services/firestore_services.py` | Native-first + custom-fallback `FirestoreSessionService` / `FirestoreMemoryService` with documented compaction hook |
| Weather RAG retrieval | `weather_agent_codebase/gcp/retrieval/weather_rag.py` | Vertex AI RAG corpus provisioning + `VertexAiRagRetrieval` ADK tool wiring |
| Weather deploy script | `weather_agent_codebase/deploy_agent_engine.py` | Default `enable_tracing=True`, Firestore-by-default with `--no-firestore` escape hatch, per-agent dedicated SA with `--no-custom-sa` escape hatch |
| Weather agent definition | `weather_agent_codebase/weather_agent/agent.py` | `PROMPT_ID`/`PROMPT_VERSION` on every span; `MCPToolset` via npx stdio; persona-as-tool; dreaming-as-tool |
| Weather host agent | `weather_agent_codebase/host_agent/agent.py` | W3C-headers + conversation-id outbound A2A pattern |
| POC gap analysis | `google_repos/.../gap_analysis.md` | Google's own admitted gaps B1–B6 |
| POC README | `google_repos/.../README.md` | Architecture claims, A2UI/A2A, Model Armor *claims*, deployment steps |
| POC combined architecture | `google_repos/.../architecture/combined_architecture_design.md` | Topology, hybrid deployment design, identity federation design |
| POC supervisor agent | `google_repos/.../agents/circana_pilot_agent/agent.py` | Prompt-as-inline-string, AgentCard skills, phase instructions |
| POC tools | `google_repos/.../agents/circana_pilot_agent/tools.py` | `_MOCK_STATE`, `call_mcp_tool` tri-fallback, regex Model Armor shim, `send_message_tool` routing, `AGENT_URLS` |
| On-prem orchestrator | `google_repos/a2a_a2ui_on_prem/agents/orchestrator.py` | `asyncio.gather` parallel resolution, polling loop, IRI integration |
| On-prem README | `google_repos/a2a_a2ui_on_prem/README.md` | On-prem POC architecture |
| IRI Advantage API | `docs/emiri/IRI_ADVANTAGE_API.md` | Advantage LD auth (Basic + session cookie), not-yet-integrated status |
| Liquid Data Reports | `docs/emiri/LIQUID_DATA_REPORTS.md` | LD services auth (LTPA), export workflow |
| Framework comparison | `langgraph_analysis/agent_framework_comparison.md` | Emiri architecture, three-layer framing, LangGraph rationale |

## Appendix B — Trace IDs Referenced (from Rishabh's hands-on testing)

| Trace ID | Section | What it shows |
|---|---|---|
| `c726b93cbb1ef459a762a2ab27cb6774` | 01.b, 07.a | Streaming spans (partial — no chunk-level) |
| `e4fe9b4b3196cf7739ca0437e2e5fa5f` | 01.d | Persona switching as `set_persona` spans |
| `08b300d58ad7d89907a98551abbf9f55` | 02.b, 03.b | Orchestration + parallel delegation (15 spans) |
| `7da2763e804cc3b46736f1a6bc476abd` | 04.a | Short-term memory / context accumulation |
| `d84a15017ccd4ea3c3a25f2c88825e42` | 04.d, 10.c | Dreaming as custom `execute_tool` span |
| `94782e61831fa9b956e3c6e21d10d65b` | 09.a, 09.b | Entity resolution + disambiguation |

---

*Document version: 1.1 — June 26, 2026. Grounded in hands-on deployment of the Google-supplied Circana POCs to Blackstraw's GCP environment, Rishabh Mendiratta's parallel hands-on testing against the `weather_agent_codebase/` reference implementation, the POCs' own gap analysis, and direct source-code review of both the Circana POCs and the weather reference codebase. Inferred/extrapolated points are marked `[Inferred]`. This document is the AI-synthesis/polish phase applied to already-grounded hands-on material, per the engagement methodology discussed with Denesh Kumar Mani.*

*v1.1 changelog: Added Section 2.5 disclosing that Rishabh's hands-on testing was performed against the weather-agent reference codebase, not the Circana POC. Split verdicts into POC-level and Platform-level columns throughout. Revised verdicts on Sections 01.a, 01.b, 02.c, 03.d, 04.a, 04.b, 04.e, 05.c, 06.a, 07.c, 09.d, 10.b, 10.c, 11 to reflect the platform-capability ceiling demonstrated by Google's reference implementation. Updated Sections 1, 7, and 8 (executive summary, scorecard, key takeaways) and Appendix A (added weather reference codebase as primary evidence source). Flagged two open contradictions between Rishabh's findings and the weather README (MCP-via-npx-stdio in Reasoning Engine, TTFT-via-span-events) as the highest-priority re-tests.*
