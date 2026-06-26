# Agent Framework Comparison: LangGraph vs. Hyperscaler Frameworks

**Date:** June 2026 (updated June 24, 2026)  
**Requested by:** Pierre Abs (Circana), via Denesh Kumar Mani  
**Prepared by:** Tim Fox, Blackstraw team  
**Purpose:** Support Circana’s hyperscaler evaluation with a feature-level comparison of agent orchestration frameworks.

**Contexts covered:**

- **Structured attribution** — GM/CPG batch pipelines (deterministic match → LLM extraction → evaluation)
- **Emiri** — Circana’s analytics NL platform *and* Blackstraw’s user-attribute enrichment / negotiation integration
- **IRI Advantage LD** — hierarchical retail dimension API used alongside Emiri entity resolution

**Source documents:** `docs/emiri_payloads_and_response.md`, `docs/IRI_ADVANTAGE_API.md`

This document consolidates the general framework comparison and the Emiri-specific hyperscaler evaluation.

---

## Scope

Pierre asked for an analysis comparing **LangGraph** against hyperscaler agent frameworks:

- **Google ADK** (Agent Development Kit)
- **Microsoft Agent Framework (MAF)** — Pierre’s “MAF”
- **AWS Strands** (Strands Agents SDK)

Denesh also asked to include **Microsoft Semantic Kernel**. Semantic Kernel is included as the **legacy / maintenance-mode** predecessor to MAF, not as a recommended choice for greenfield work.

---

## Executive summary

### One-line positioning

| Framework | Positioning |
|---|---|
| **LangGraph** | Graph/state-machine runtime for **production-grade, auditable, long-running** agent workflows |
| **Google ADK** | Code-first, **Gemini/GCP-optimized** agent SDK with graph workflows + multi-agent (ADK 2.0) |
| **Microsoft Agent Framework (MAF)** | Microsoft’s **GA successor** to Semantic Kernel + AutoGen; enterprise .NET/Azure agent platform |
| **Semantic Kernel (SK)** | **Maintenance-mode** predecessor to MAF; use only for existing SK applications |
| **AWS Strands** | **Model-driven**, lightweight SDK; strong on Bedrock/AWS and fast agent delivery |

### Fit scores (by workload)

| Dimension | **LangGraph** | **Google ADK** | **Microsoft MAF** | **AWS Strands** |
|---|---|---|---|---|
| **Maturity (hands-on)** | Production-ready, widely adopted | Preview-era pain points in Circana demo; ADK 2.0 evolving | MAF 1.0 GA (Apr 2026); early production adoption | Strands 1.0 GA; AWS-internal first |
| **Vendor lock-in** | None — runs anywhere | High — optimized for Vertex AI / Agent Engine | High — tied to Azure AI Foundry | High — tied to Amazon Bedrock |
| **Blackstraw attribution batch** | ★★★★★ | ★★☆☆☆ | ★★☆☆☆ | ★★☆☆☆ |
| **Emiri API integration** (entity resolution, LD Advantage) | ★★★★★ | ★★☆☆☆ | ★★★☆☆ | ★★☆☆☆ |
| **Circana conversational Emiri** (Teams/DirectLine) | ★★★☆☆ | ★★★★☆ | ★★★★★ | ★★★☆☆ |
| **Negotiation engine** (entity resolution only) | ★★★★★ | ★★☆☆☆ | ★★★☆☆ | ★★☆☆☆ |

### Blackstraw recommendation (refined)

**Separate three concerns — do not pick one framework for all of them:**

| Layer | What it is | Recommendation |
|---|---|---|
| **1. Blackstraw batch pipelines** | UPC attribution, scrape enrichment, 50K+ product runs | **LangGraph** — explicit graph, checkpointing, audit trails |
| **2. Emiri / Advantage API integration** | HTTP orchestration to existing Circana services | **LangGraph tool nodes** (or plain Python + `requests`) — **integrate with Emiri, don’t replace it** |
| **3. Circana conversational Emiri** | Full NL query UI (Intent → Entity → Measures → Copilot) | **Circana-owned**; already **Azure OpenAI** (`azure-gpt-4o`). If rebuilt, **MAF** is the natural Microsoft path — but this is not Blackstraw’s batch scope |

**Key insight from Emiri docs:** Emiri’s *existing* architecture is already a **multi-stage, template-driven pipeline** with parallel entity-resolution branches — not an LLM-supervisor pattern. The negotiation use case **explicitly skips the Intent LLM** and calls entity resolution directly. Hyperscaler agent frameworks would add an unnecessary conversational orchestration layer on top of APIs that are already stage-based.

**Revisit ADK / MAF / Strands** for a *new* marketer-facing conversational portal — not for wrapping Blackstraw’s batch enrichment or Emiri API calls.

If Circana standardizes on one hyperscaler for **LLM runtime only**, pair LangGraph with that provider’s models (Azure OpenAI is already used by Emiri today) without rewriting orchestration into MAF/ADK/Strands supervisor trees.

---

## Consolidated feature matrix

**Legend:** ● strong / native · ◐ partial or emerging · ○ limited or indirect · — not a primary focus

| Dimension | **LangGraph** | **Google ADK** | **Microsoft MAF** | **Semantic Kernel** | **AWS Strands** |
|---|---|---|---|---|---|
| **Maintainer** | LangChain (open source) | Google (open source) | Microsoft (open source) | Microsoft (maintenance) | AWS (open source) |
| **GA / maturity (Jun 2026)** | ● v1+; widely used in production | ◐ ADK 2.0 recent; Circana demo hit preview gaps | ● MAF 1.0 GA (Apr 2026) | ◐ SK maintained; no new features | ● Strands 1.0 GA |
| **Core paradigm** | **Explicit graph** (nodes/edges/state) | Code-first agents + **Workflow graph** (2.0) | Agents + **explicit workflows** | Plugins + planners/processes | **Model-driven loop** (LLM orchestrates) |
| **Execution guarantee** | **Deterministic** — same input → same path | Non-deterministic — LLM-routed (supervisor pattern) | Non-deterministic — LLM-routed | Mixed (planner-driven) | Non-deterministic — tool-calling loop |
| **Orchestration topology** | Full graph (cycles, loops, branches) | Agent tree (supervisor → sub-agents) | Agent workflow (planner/executor) | Process framework / planners | Swarm, Graph, Agents-as-tools, Meta agents |
| **Multi-agent** | ● subgraphs, supervisor patterns | ● hierarchies, Task API, A2A | ● native multi-agent | ◐ multi-agent (legacy) | ● Swarm/Graph/A2A |
| **Parallelism** | ● native fan-out/fan-in | ◐ parallel via ThreadPoolExecutor | ◐ limited | ◐ varies | ◐ sequential tool calls (Graph mode differs) |
| **Batch processing** | ● map pipeline nodes to graph nodes | ○ conversational turns | ○ conversational | ○ | ○ single tool-call loops |
| **State management** | ● typed state (TypedDict), reducers | Session service (in-mem / Firestore) | ● session-based state (in-mem / Cosmos) | ◐ kernel memory/context | ◐ SessionManager (DynamoDB) |
| **Checkpointing / durable execution** | ● first-class (Postgres, etc.) | ◐ workflow state; Agent Engine gaps noted | ● long-running + HITL scenarios | ◐ less graph-native | ◐ session persistence; less graph-grade |
| **Human-in-the-loop** | ● `interrupt_before` / `interrupt_after` | ◐ custom (A2UI blocks, suspend execution) | ◐ custom (manual checkpoint) | ◐ possible, not graph-native | ◐ hooks/steering; tool interception |
| **Tool ecosystem** | LangChain tools + custom | `FunctionTool`, OpenAPI, Google integrations | Plugins → tools; MCP | SK plugins/functions | ● `@tool`, MCP, A2A |
| **MCP support** | ● native MCP client | ● native MCP + Agent Registry | ● MCP + A2A | ◐ evolving | ● native MCP |
| **A2A (agent-to-agent)** | ◐ community / custom | ● Task API, A2A | ● A2A + MCP | ○ | ● A2A in 1.0 |
| **Model agnosticism** | ● any LLM via LangChain | ● Gemini-first; others via custom | ● Azure OpenAI + multi-provider | ● multi-provider | ● Bedrock-first; many providers |
| **Vector store** | ● any (Chroma, Pinecone, FAISS, …) | Vertex AI Vector Search first-class | Azure AI Search first-class | ◐ via plugins | OpenSearch / Kendra first-class |
| **Observability** | ● LangSmith / LangFuse / OTel | Cloud Logging / Cloud Trace | ● Azure Monitor / OTel | ◐ OpenTelemetry | ● CloudWatch + X-Ray, hooks |
| **Per-node token attribution** | ● native token limits per node | ○ per-turn logs | ○ per-token accounting | ○ | Bedrock token logs |
| **Deployment** | Self-host, LangGraph Platform/Cloud, K8s | Cloud Run, GKE, Agent Runtime, Agent Engine | Azure Foundry, Functions, containers | Azure / self-host | Lambda, Fargate, Bedrock AgentCore |
| **Scale-to-zero** | ● LangGraph Platform | ◐ Cloud Run yes; Agent Engine unclear | ● Azure Functions | ◐ | ◐ unclear (Bedrock managed) |
| **Cloud affinity / lock-in** | Low | High on GCP managed path | High on Azure/Microsoft stack | Medium–high | High on AWS managed path |
| **Languages** | Python (primary), JS | Python, TS, Go, Java, Kotlin | .NET, Python, JS, Java | C#, Python, Java | Python, TypeScript |
| **Learning curve** | Steeper (graph DSL) | Moderate; improving with 2.0 | Moderate (.NET-friendly) | Moderate (legacy) | Lower for simple agents |
| **Best for** | Stateful pipelines, compliance, audit trails | Gemini/GCP conversational agents | New Microsoft/Azure agent apps | Existing SK codebases only | Bedrock/AWS conversational agents |
| **Weak for** | Simple one-shot tasks; ops overhead | Batch pipelines; non-GCP minimal coupling | Non-Microsoft stacks; batch pipelines | **Greenfield** (use MAF) | Deterministic batch without Graph discipline |

---

## Detailed feature matrices

### 1. Architecture and execution model

| Feature | LangGraph | Google ADK | Microsoft MAF | AWS Strands |
|---------|-----------|-----------|---------------|-------------|
| **Pattern** | Stateful graph (nodes + edges) | Agent tree (supervisor → sub-agents) | Agent workflow (planner/executor) | Agent loop (tool-calling loop) |
| **Execution guarantee** | Deterministic — same input → same path | Non-deterministic — LLM-routed | Non-deterministic — LLM-routed | Non-deterministic — LLM-routed |
| **State management** | User-defined state schema (TypedDict) | Session service (in-mem / Firestore) | Agent thread state (in-mem / Cosmos) | Agent session state (DynamoDB) |
| **Control flow** | Explicit edges, conditional routing, cycles | Prompt-based routing (system instructions) | Prompt-based routing | Tool-calling loop, single-agent |
| **Parallelism** | Native (fan-out/fan-in via graph) | Parallel via ThreadPoolExecutor | Limited | Sequential tool calls |
| **Human-in-the-loop** | Native `interrupt_before` / `interrupt_after` | Custom (parse A2UI blocks, suspend execution) | Custom (requires manual checkpoint) | Custom (tool-call interception) |
| **DAG / cycle support** | Full graph topology | Tree topology (supervisor → children) | Sequential / branching | Single loop (Graph mode adds structure) |
| **Batch processing** | Yes — map pipeline nodes to graph nodes | No — designed for conversational turns | No — designed for conversational | No — designed for single tool-call loops |

### 2. Vendor independence and portability

| Feature | LangGraph | Google ADK | Microsoft MAF | AWS Strands |
|---------|-----------|-----------|---------------|-------------|
| **LLM runtime** | Any (OpenAI, Anthropic, Gemini, local) | Gemini first-class; others via custom | Azure OpenAI first-class; others via custom | Bedrock first-class; others via custom |
| **Deployment target** | Anywhere (EC2, ECS, Cloud Run, local) | Vertex AI Agent Engine (optimized) | Azure AI Foundry | Amazon Bedrock |
| **Vector store** | Any (Chroma, Pinecone, FAISS, Weaviate) | Vertex AI Vector Search first-class | Azure AI Search first-class | OpenSearch / Kendra first-class |
| **Observability** | LangSmith / LangFuse / OTel | Cloud Logging / Cloud Trace | Azure Monitor / Application Insights | CloudWatch |
| **Framework lock-in** | Kotlin/Java/JS variants exist | Python-first (multi-lang in ADK 2.0) | Python + C# | Python + TypeScript |

### 3. Tool and function calling

| Feature | LangGraph | Google ADK | Microsoft MAF | AWS Strands |
|---------|-----------|-----------|---------------|-------------|
| **Tool definition** | `@tool` decorator (any callable) | `FunctionTool` (any callable) | `KernelFunction` / tools (any callable) | `@tool` decorator |
| **MCP support** | Native MCP client (any MCP server) | Native MCP client + Agent Registry resolution | MCP client | MCP client |
| **Human-in-the-loop tools** | Native `interrupt` nodes | Custom A2UI widget protocol | Custom | Custom |
| **Tool parallelism** | Yes (parallel tool calls) | Yes (LLM-driven) | Yes (LLM-driven) | Sequential |
| **Custom tool protocols** | Any (HTTP, gRPC, stdio) | A2A (JSON-RPC) + MCP | Agent Protocol | Bedrock tool schema |

### 4. State, memory, and context

| Feature | LangGraph | Google ADK | Microsoft MAF | AWS Strands |
|---------|-----------|-----------|---------------|-------------|
| **Session state** | User-defined (full control) | Session service (In-mem, Firestore) | Thread state (In-mem, Cosmos) | Session state (DynamoDB) |
| **Long-term memory** | Opt-in (external store) | Memory Service (Firestore-backed) | Agent state persistence | Session memory (DynamoDB) |
| **Cross-thread state** | Full (shared across graph instances) | Session-scoped (per conversation) | Thread-scoped (per conversation) | Session-scoped (per conversation) |
| **State schema** | TypedDict (formal, verified) | Dict[str, Any] (loose) | Dict[str, Any] (loose) | Dict[str, Any] (loose) |
| **State transitions** | Explicit (node → node) | Implicit (LLM decides) | Implicit (LLM decides) | Implicit (LLM decides) |

### 5. Deployment and operations

| Feature | LangGraph | Google ADK | Microsoft MAF | AWS Strands |
|---------|-----------|-----------|---------------|-------------|
| **Managed runtime** | LangGraph Cloud / LangGraph Platform | Vertex AI Agent Engine | Azure AI Foundry | Amazon Bedrock / AgentCore |
| **Self-hosted** | Yes (any Python host) | Yes (via ADK Runner local) | Yes (via self-host / containers) | Yes (via Strands SDK self-host) |
| **Container template** | `langgraph-api` Docker image | Custom Docker CMD | Azure Functions template | Bedrock agent runtime |
| **Scale-to-zero** | LangGraph Platform (yes) | Cloud Run yes; Agent Engine unclear | Azure Functions (yes) | Unclear (always warm?) |
| **Versioning / rollback** | Pin threads; git pin | Every code change = new engine ID | Revision per deployment | Alias per version |
| **CI/CD** | Standard Docker workflow | `agent_engines.create()` API | Bicep / Terraform templates | CloudFormation / CDK |

### 6. Observability and tracing

| Feature | LangGraph | Google ADK | Microsoft MAF | AWS Strands |
|---------|-----------|-----------|---------------|-------------|
| **Tracing** | LangSmith (first-party) / OpenTelemetry-native | Cloud Logging / Cloud Trace (GCP-native) | Azure Monitor / OpenTelemetry | CloudWatch + X-Ray |
| **Human-readable traces** | LangSmith UI (call tree visualization) | Cloud Trace (GCP console) | Azure Monitor / OTel backends | X-Ray console |
| **Cross-service trace** | Yes (OTel context propagation) | Unclear — A2A boundary may break trace context | Yes (OTel) | X-Ray cross-service |
| **Token attribution** | Per-node token counts | Per-turn token logs | Per-token accounting | Bedrock token logs |
| **Token-budget enforcement** | Native (token limits per node) | No native support | No native support | No native support |

### 7. Cost profile (Emiri batch workloads)

| Metric | LangGraph | Google ADK | Microsoft MAF | AWS Strands |
|--------|-----------|-----------|---------------|-------------|
| **Compute** | Self-host container (Cloud Run / ECS) ~$0.02/vCPU-hour | Agent Engine (per-deployment + per-hour) | Azure Functions consumption (~$0.02/vCPU-hour) | Bedrock per-request |
| **LLM** | Actual Gemini/OpenAI/Anthropic cost (usage-based) | Gemini cost (Vertex AI pay-per-token) | Azure OpenAI (pay-per-token) | Bedrock pay-per-token |
| **Idle cost** | Scale-to-zero container = $0 idle | Agent Engine idle cost unclear (per-engine-idle?) | Scale-to-zero function = $0 idle | Unclear (always warm?) |
| **50K-product batch run** | Container CPU × ~2 hours + 50K LLM calls | Engines (4 deployed) + 50K LLM calls + per-session fees | LLM + compute | LLM + Bedrock fees |
| **Total monthly (estimate)** | LLM cost + ~$20 compute | LLM + 4× engine/day idle + portal compute | LLM + compute | LLM + Bedrock fees |

---

## Orchestration philosophy

| | LangGraph | Google ADK | Microsoft MAF | AWS Strands |
|---|---|---|---|---|
| **Who controls the flow?** | Developer defines graph | Developer + workflow engine (2.0) / LLM supervisor | Developer defines workflows / LLM planner | **Model** drives loop; developer adds guardrails |
| **Determinism** | High — edges are explicit | High in Workflow mode; low in supervisor mode | High in workflow mode | Lower unless using **Graph** pattern |
| **Flexibility vs. predictability** | Best predictability | Good balance (workflow); poor for batch supervisor | Good enterprise balance | Best flexibility; needs guardrails for production |

**Takeaway:** For **attribution** and **Emiri** batch workloads (fixed phases: load → retrieve → extract → evaluate), LangGraph, ADK Workflow mode, MAF workflows, and Strands **Graph** mode align well. Pure model-driven / supervisor-routed patterns are better suited to exploratory or conversational agents than to regulated, auditable batch pipelines.

---

## Hyperscaler fit

| If Circana standardizes on… | Preferred framework | Notes |
|---|---|---|
| **GCP / Gemini** | Google ADK | Deepest integration; Agent Runtime; strong for conversational portal |
| **Azure / Microsoft 365** | Microsoft MAF (not SK for new work) | SK → MAF migration path exists |
| **AWS / Bedrock** | AWS Strands | AWS-preferred; used internally (Amazon Q, Glue, etc.) |
| **Multi-cloud / vendor-neutral orchestration** | LangGraph | Run the same graph on any model provider |

### Semantic Kernel vs. Microsoft Agent Framework

Microsoft’s position as of 2026:

- **MAF is the successor** to Semantic Kernel and AutoGen (GA April 2026).
- **Semantic Kernel is in maintenance mode** — critical and security fixes only; new features go to MAF.
- **Recommendation:** New projects should start on **MAF**. Existing SK projects should plan migration or expose plugins via MCP.

---

## Framework profiles

### LangGraph

- **What it is:** Low-level orchestration framework for stateful, long-running agents modeled as directed graphs (nodes = steps, edges = transitions).
- **Strengths:** Checkpointing, HITL interrupts, typed state, per-node tracing, strong production adoption, deep LangSmith observability.
- **Tradeoffs:** Graph DSL learning curve; operational overhead (Postgres checkpointer, etc.); overkill for simple linear tasks.
- **Blackstraw usage:** GM agentic attributor (`structured_attribution/methodologies/agentic-attributor/`) — deterministic match → parallel LLM extraction as a `StateGraph`.

### Google ADK (Agent Development Kit)

- **What it is:** Google’s open-source, code-first agent framework; optimized for Gemini and Google Cloud.
- **ADK 2.0 highlights:** Workflow Runtime (graph-based execution), Task API (structured A2A delegation), multi-agent via A2A.
- **Strengths:** Strong GCP integration, evaluation tooling, A2UI for interactive portals, multi-language support.
- **Tradeoffs:** Fast API evolution; strongest on GCP; **Circana hands-on demo found batch-pipeline gaps** (see below).

### Microsoft Agent Framework (MAF)

- **What it is:** Unified successor combining AutoGen’s agent abstractions with Semantic Kernel’s enterprise features plus explicit graph-based workflows.
- **Strengths:** GA with LTS commitment (Apr 2026), deep Azure/Microsoft ecosystem, MCP + A2A.
- **Tradeoffs:** Microsoft/Azure affinity; conversational-first patterns for many examples.

### Semantic Kernel (legacy)

- **What it is:** Model-agnostic SDK for plugins, planners, and multi-agent orchestration — predecessor to MAF.
- **When to use:** Extending existing SK applications only.

### AWS Strands (Strands Agents SDK)

- **What it is:** Open-source, model-driven agent SDK; AWS-preferred path for Bedrock.
- **Strands 1.0 highlights:** Swarm, Graph, Agents-as-tools, Meta agents, A2A, SessionManager, MCP, OpenTelemetry.
- **Strengths:** Low ceremony; strong AWS deployment story; model-agnostic beyond Bedrock.
- **Tradeoffs:** Model-driven default is less deterministic; Graph pattern needed for pipeline-style control.

---

## Emiri platform context (from internal docs)

Review of `docs/emiri_payloads_and_response.md` and `docs/IRI_ADVANTAGE_API.md` refines how we frame “Emiri” in this comparison.

### What Emiri actually is

Emiri is **not** a single batch job — it is Circana’s **natural-language analytics platform** with two distinct modes relevant to Blackstraw:

| Mode | Flow | LLM usage | Blackstraw relevance |
|---|---|---|---|
| **Full conversational Emiri** (1.0 prod / 2.0 demo) | Auth → Intent → Entity (Product ∥ Geography ∥ Other ∥ Filter) → Measures → `runCopilotAsync` → `fetchCopilotData` | Template-driven calls to `azure-gpt-4o` via `/llmadmin/api/llm/execution` | **Out of scope** for Blackstraw orchestration — Circana-owned product surface (Teams, DirectLine) |
| **Entity resolution only** (negotiation engine) | Auth → **`getEmiriEntityResponseProd`** directly (Intent step **skipped**) | `fast_entity.txt` / `entity_product_ee v3` templates on `gpt-4o` | **In scope** — Blackstraw calls this API to resolve SKU, brand, retailer, description |

The negotiation engine needs: **SKU, product description, retailer, brand, product name** — returned from entity resolution when properly configured.

### Emiri’s architecture already matches graph orchestration

The full Emiri entity response is internally **parallel fan-out**:

```
sentence + AS_MODEL (e.g. TSV_WB)
    ├── Filter entities   (~1.5s)
    ├── Geography entities (~0.4s)
    ├── Other entities    (~0.5s)
    └── Product entities  (~3.5s)  ← dominant latency
         → merged entities[] response
```

This is explicit staged execution with fixed templates — **not** “supervisor LLM picks the next agent.” LangGraph’s fan-out/fan-in maps this pattern directly. ADK/MAF/Strands would re-introduce non-deterministic routing on top of an API that is already deterministic.

The async Copilot path (`runCopilotAsync` → poll `fetchCopilotData` by `transactionID`) is a classic **async wait node** in a graph — again, not a conversational agent framework concern.

### Authentication and external APIs

Emiri integration involves **multiple auth schemes** (not framework-specific):

| Endpoint | Auth | Example |
|---|---|---|
| LLM execution (`/llmadmin/api/llm/execution`) | **Bearer token** (API secret) — basic auth does **not** work | Intent, Measures |
| LD Services (`getEmiriEntityResponseProd`) | LTPA cookie **or** Basic Auth (QA) | Entity resolution |
| Auth cache (`user_authentication`) | Basic Auth | Unify defaults, model IDs |
| **IRI Advantage LD** (`/client3-ld`) | Basic Auth + **session cookie** from `/security/login` | `getDescendantsAtLevelMembers` |

**IRI Advantage LD** is a separate REST API for hierarchical Product/Geography/Time dimensions. It is documented as **not yet integrated** into the negotiation orchestrator — recommended pattern is an **MCP or data-agent tool** with `requests.Session` cookie reuse.

LangGraph handles these as **HTTP tool nodes** with session state. Hyperscaler frameworks offer no advantage here; they add conversational routing overhead for what is fundamentally REST orchestration.

### Azure is already the Emiri LLM path

Emiri’s production LLM calls use **`azure-gpt-4o`** and **`gpt-4o`** via Circana’s `llmadmin` service — not Gemini, Bedrock, or a hyperscaler agent runtime. This means:

- **MAF** is relevant if Circana **rebuilds** the conversational Emiri surface on Microsoft Agent Framework — plausible given Azure entrenchment, but orthogonal to Blackstraw’s batch work.
- **ADK / Strands** are poor fits for Emiri *platform evolution* unless Circana pivots cloud strategy away from Azure for NL analytics.
- Blackstraw should use **Azure OpenAI** (or LiteLLM → Azure) for attribution LLM calls to align with Circana’s existing Emiri stack — **without** adopting MAF for orchestration.

### Implications for Pierre’s hyperscaler evaluation

| Question | Answer informed by Emiri docs |
|---|---|
| Should Blackstraw use MAF because Emiri is on Azure? | **No** — Emiri is API/template orchestration, not MAF. Azure alignment is at the **model provider** layer. |
| Should we replace Emiri entity resolution with our own agent? | **No** — call `getEmiriEntityResponseProd`; skip Intent for negotiation per team agreement. |
| Where do hyperscaler frameworks fit? | **New conversational portals** (e.g. marketer HITL review of attribution) — not Emiri API glue or batch enrichment. |
| How to integrate IRI Advantage? | LangGraph node or MCP tool; session-persistent HTTP client per `IRI_ADVANTAGE_API.md`. |

---

## Strong opinions and recommendations

### 1. Distinguish Blackstraw batch from Emiri platform integration

**Blackstraw batch** (attribution, scrape enrichment):

- Processes **50,000+ UPCs** per run
- Hybrid retrieval (ChromaDB + BM25) + constrained LLM extraction
- Outputs structured CSVs / evaluation artifacts
- No multi-turn conversation in the batch path

**Emiri integration** (negotiation engine):

- Calls **existing Circana APIs** — entity resolution, optionally IRI Advantage LD for hierarchy lookups
- Team agreed to **bypass IntentCall**; direct `getEmiriEntityResponseProd` with `AS_MODEL` + `sentence`
- Async Copilot polling where full NL analytics is needed
- Auth/session management across multiple Circana endpoints

Both map to LangGraph — but Emiri integration is **HTTP tool orchestration**, not rebuilding Emiri inside a hyperscaler agent framework.

| Phase | Blackstraw batch node | Emiri integration node |
|---|---|---|
| Load / preprocess | `load`, `preprocess` | `auth` (LTPA / Bearer / session login) |
| Retrieval / resolution | `retrieve` (Chroma + BM25) | `entity_resolve` (parallel Product/Geo/Other) |
| LLM extraction | `extract` (constrained picker) | *(optional — skipped for negotiation)* |
| Downstream data | `evaluate` | `advantage_ld_lookup`, `copilot_async` + poll |
| Output | CSV / metrics | Structured entity payload (SKU, brand, retailer, …) |

ADK, MAF, and Strands default to **LLM-routed execution** (“supervisor decides which sub-agent to call next”). That implies:

- Non-determinism (same input may take different paths)
- Harder unit testing of routing decisions
- Extra token cost for supervisor routing calls
- **Redundant layer** on top of Emiri’s already-staged API pipeline

### 2. Vendor independence matters during hyperscaler evaluation

Pierre is running a hyperscaler evaluation. The winning cloud is not yet decided. **LangGraph runs on any cloud and any LLM provider.** Committing to ADK, MAF, or Strands before that decision is premature.

LangGraph lets Blackstraw build the pipeline now, evaluate cloud providers in parallel, and migrate the LLM runtime without rewriting orchestration logic.

### 3. Structured attribution (GM / CPG)

For workloads with deterministic matching phases, parallel LLM extraction, and audit trails:

1. **Already in production patterns** — maps naturally to a graph
2. **Auditability** — per-attribute hit/miss and LLM reasoning benefit from per-node traces
3. **Deterministic + LLM hybrid** — graph orchestration does not force all control flow through an LLM
4. **Provider flexibility** — works with LiteLLM, Azure OpenAI, and other backends

### 4. When to prefer each hyperscaler framework

| Choose **Google ADK** if… | Choose **Microsoft MAF** if… | Choose **AWS Strands** if… |
|---|---|---|
| Gemini / Vertex is the mandated model path | **Rebuilding Circana’s conversational Emiri UI** on Azure | Bedrock is the mandated inference path |
| Building a **new conversational HITL portal** on GCP | Deep M365 / Foundry / Copilot integration for NL analytics | Fast path to AWS-native conversational agents |
| A2UI interactive widgets are a requirement | Greenfield on C# / enterprise Microsoft patterns | Team prefers minimal orchestration code |

**Not** a reason to choose MAF: “Emiri already uses Azure OpenAI” — that’s a **model provider** choice, not an orchestration framework choice.

### 5. What we would not recommend

- **Don’t start new Microsoft work on Semantic Kernel** — use MAF.
- **Don’t use ADK/MAF/Strands supervisor patterns for Blackstraw batch or Emiri API glue** — call Emiri’s staged APIs directly.
- **Don’t replace Emiri entity resolution with a custom hyperscaler agent** — use `getEmiriEntityResponseProd` per team agreement.
- **Don’t replace LangGraph with Strands model-driven loops** for attribution unless a **Graph** layer is added.
- **Don’t treat hyperscaler frameworks as drop-in replacements** — they optimize for conversational patterns, not Circana REST orchestration.

### 6. Suggested evaluation framing for Circana

Use a **three-layer decision**:

1. **Blackstraw orchestration** (batch attribution, Emiri API integration, Advantage LD tools)  
   → **LangGraph** (or plain Python for thin API wrappers)

2. **Circana conversational Emiri** (Intent → Entity → Copilot — existing product)  
   → Circana-owned; if rebuilt, **MAF** on Azure is the natural fit given current `azure-gpt-4o` usage

3. **Runtime layer** (models, hosting, security, billing)  
   → GCP vs. Azure vs. AWS — **Azure already chosen for Emiri LLM calls**

### Final recommendation

> **Build Blackstraw batch pipelines and Emiri API integration on LangGraph now.**  
> **Call existing Emiri entity resolution APIs — do not wrap them in hyperscaler agent frameworks.**  
> **Evaluate ADK / MAF / Strands only for a future conversational HITL portal** (e.g. marketer review of attribution), not for batch enrichment or negotiation API glue.  
> **Use Azure OpenAI for LLM calls** to align with Emiri’s existing model path, independent of MAF adoption.

---

## Blackstraw hands-on findings (Google ADK, Circana retail demo)

Relevant data from a detailed evaluation of Google ADK on a similar Circana pipeline (retail multi-agent demo):

| Finding | Implication |
|---|---|
| ADK optimized for **conversational HITL portals**, not batch pipelines | Poor fit for Emiri batch without workarounds |
| `InMemoryMemoryService` **does not survive worker restarts** | Repo explicitly warns about this; risky for production batch |
| **Agent Engine idle cost** across 4 engines unclear | Demo deploys 4 Reasoning Engines + MCP server; no scale-to-zero story documented |
| **A2A trace propagation unconfirmed** | Open question whether OTel context propagates across A2A boundaries |
| **Local dev required bypassing ADK** | Mock local services (Ollama + in-memory session) needed because ADK assumes Vertex AI Agent Engine for real LLM calls |

These findings reinforce the recommendation: hyperscaler conversational frameworks are not the right primary fit for Emiri’s batch pipeline. LangGraph (or plain orchestration via Ray + a vector store) better matches the requirements.

---

## Appendix: Minimal code comparison

### LangGraph (intentional routing)

```python
from langgraph.graph import StateGraph, START, END
from typing import TypedDict

class PipelineState(TypedDict):
    upcs: list[str]
    chunks: list[dict]
    attributes: list[dict]

graph = StateGraph(PipelineState)
graph.add_node("load", load_upcs)
graph.add_node("preprocess", preprocess)
graph.add_node("retrieve", hybrid_retrieve)
graph.add_node("extract", llm_extract)
graph.add_node("evaluate", compute_metrics)
graph.add_edge(START, "load")
graph.add_edge("load", "preprocess")
graph.add_edge("preprocess", "retrieve")
graph.add_edge("retrieve", "extract")
graph.add_edge("extract", "evaluate")
graph.add_edge("evaluate", END)

app = graph.compile()
result = app.invoke({"upcs": gm_webdata_upcs})
```

### Google ADK (LLM-routed supervisor)

```python
from google.adk.agents import Agent

supervisor = Agent(
    name="supervisor",
    model="gemini-2.0-flash",
    instruction="Call PricingAgent, then ActivateAgent... (instructions in prose)",
    sub_agents=[pricing_agent, activate_agent],
    tools=[send_message_tool],
)
# LLM decides routing — non-deterministic
```

### AWS Strands (tool-calling loop)

```python
from strands import Agent

agent = Agent(
    model="us.anthropic.claude-3-5-sonnet-20241022-v1:0",
    tools=[load_tool, retrieve_tool, extract_tool, evaluate_tool],
)
# Agent calls tools in loop until it decides to stop
```

### Microsoft MAF (planner/executor)

```python
from microsoft.agents.foundation import Agent

agent = Agent(
    name="emiri_supervisor",
    model_client=AzureChatAIRequestSettings(model="gpt-4o"),
    tools=[load_fn, retrieve_fn, extract_fn, evaluate_fn],
)
await agent.run("Process all UPCs and output CSV")
```

---

## Draft reply to Pierre (optional)

> We compared LangGraph against the hyperscaler agent frameworks (Google ADK, Microsoft Agent Framework, AWS Strands), with Semantic Kernel noted as Microsoft’s maintenance-mode predecessor to MAF.
>
> After reviewing Emiri’s API architecture (`emiri_payloads_and_response.md`, `IRI_ADVANTAGE_API.md`), we distinguish **three layers**: (1) Blackstraw batch attribution/enrichment, (2) integration with Circana’s existing Emiri and Advantage APIs, and (3) Circana’s conversational Emiri product (Intent → Entity → Copilot).
>
> **LangGraph** is the right fit for layers 1 and 2. Emiri’s entity resolution is already a staged, parallel API pipeline with template-driven LLM calls — not an LLM-supervisor pattern. The negotiation use case explicitly skips Intent and calls entity resolution directly. Wrapping these REST APIs in ADK/MAF/Strands adds non-deterministic routing without benefit.
>
> **MAF** becomes relevant for layer 3 only if Circana rebuilds the conversational Emiri surface — plausible given Emiri already uses Azure OpenAI (`azure-gpt-4o`), but that’s a model-provider alignment, not a reason to adopt MAF for Blackstraw orchestration.
>
> For batch workloads (50K+ UPCs) and Emiri API integration, we recommend **LangGraph + Azure OpenAI**. Evaluate hyperscaler frameworks separately for a future marketer-facing conversational portal.

---

## References

- [Google ADK](https://adk.dev/)
- [Google ADK on Cloud](https://docs.cloud.google.com/agent-builder/agent-development-kit/overview)
- [Microsoft Agent Framework overview](https://learn.microsoft.com/en-us/agent-framework/overview/)
- [Semantic Kernel and Microsoft Agent Framework (blog)](https://devblogs.microsoft.com/agent-framework/semantic-kernel-and-microsoft-agent-framework/)
- [AWS Strands Agents 1.0 announcement](https://aws.amazon.com/blogs/opensource/introducing-strands-agents-1-0-production-ready-multi-agent-orchestration-made-simple/)
- [Strands Agents documentation](https://strandsagents.com/)
- [LangGraph](https://github.com/langchain-ai/langgraph)

---

*Document version: 2.1 — June 2026 (added Emiri platform context from internal API docs)*
