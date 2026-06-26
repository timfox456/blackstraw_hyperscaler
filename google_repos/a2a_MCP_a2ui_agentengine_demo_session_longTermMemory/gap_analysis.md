# Circana Multi-Agent MVP Gap Analysis

This document evaluates the current pilot implementation against the target product requirements (B1-B6) to identify remaining gaps and outline implementation strategies to close them.

---

## 📊 Gap Analysis Matrix

| Requirement | What We Have Implemented | What is Missing (The Gap) | How to Close the Gap |
| :--- | :--- | :--- | :--- |
| **B1 · Chat Host & MCP Apps** | <ul><li>**Applet rendering**: Pricing tables, Audience Sizing, and Loyalty personalization widgets.</li><li>**HITL checkpoint**: Suspension and resumption via `postMessage`.</li><li>**History & recall**: Load previous events from REST.</li><li>**Conversation management**: Create and delete sessions.</li><li>**Attachments & Voice**: Staging file uploads to GCS with badge chips, and speech recognition (STT) mic triggers + speech synthesis (TTS) reader.</li></ul> | <ul><li>**Streaming**: Chat responses return as single JSON blocks.</li></ul> | <ul><li>**Streaming**: Refactor the FastAPI chat endpoint to return a `StreamingResponse` using Server-Sent Events (SSE) to render text tokens in real time.</li></ul> |
| **B2 · Prompt Orchestration** | <ul><li>**Multi-part decomposition**: Coordinated hub-and-spoke flow.</li><li>**Structured step chaining**: Sequential execution.</li><li>**Mid-flow checkpoints**: Handled by A2UI callbacks.</li><li>**Long-running queries & GUI locks**: Asynchronous polling loop against `GET /api/jobs/{job_id}` showing progress checklist (0-100%) and disabling chat inputs.</li></ul> | <ul><li>**Plan transparency**: The user does not see what steps the orchestrator is planning next.</li></ul> | <ul><li>**Plan transparency**: Let the Supervisor output its planned execution steps as metadata, and display them as a progressive checklist in the UI (e.g., *"Sizing audience segment... [In Progress]"*).</li></ul> |
| **B3 · Supervisor Flow** | <ul><li>**Shared state**: Context parameters passed via local state dictionary.</li><li>**Routing precision**: Checked (decoy agents are never triggered).</li><li>**Guardrail block**: Model Armor blocks prompt injections.</li></ul> | <ul><li>**Native supervisor primitives**: LangGraph state machine orchestration.</li><li>**Per-step cost attribution**: Standard logs don't track token cost per step.</li><li>**Verifier agent**: Results are not double-checked before output.</li></ul> | <ul><li>**Native primitives**: Migrate the Python supervisor execution graph from custom loops to a native **LangGraph** structure.</li><li>**Cost attribution**: Extract `usage_metadata` from the GenAI API response after each turn, compute the dollar cost, and store it in Firestore for dashboard logging.</li><li>**Verifier**: Create a `VerificationAgent` that intercepts sub-agent outputs and runs validation checks (e.g., verifying math metrics).</li></ul> |
| **B4 · Memory** | <ul><li>**Short-term memory**: Chat history is preserved across turns.</li></ul> | <ul><li>**Memory inspection**: No view of what the agent "knows".</li><li>**Long-term memory**: Preferences (e.g. preferred partner) are lost on new chats.</li></ul> | <ul><li>**Memory inspection**: Render an A2UI sidebar widget called "Agent Profile Memory" displaying values stored in Firestore.</li><li>**Long-term memory**: After a session ends, run a background consolidation agent to extract facts (e.g., *"User prefers LiveRamp for activate activations"*) and save them to a user profile table to preload on new session startups.</li></ul> |
| **B5 · MCP Private Connectivity** | <ul><li>**Documented network model**: MCP server container deployed to Cloud Run.</li></ul> | <ul><li>**Private path verified**: Cloud Run is currently accessible over the internet (even if authenticated).</li></ul> | <ul><li>**Private path**: Enforce Cloud Run ingress control to `internal-only` and set up **Serverless VPC Access** / **VPC Service Controls** so Vertex AI Agent Engine communicates with the container entirely inside your private cloud network.</li></ul> |
| **B6 · Identity** | <ul><li>**Audit logs**: Trace IDs written to Cloud Logging.</li></ul> | <ul><li>**User identity at the tool**: The MCP tool queries the database using a master VM service account, not the logged-in user's identity.</li><li>**Entra federation**: Fake session user ID.</li></ul> | <ul><li>**User identity at the tool**: Pass the user's Microsoft Entra ID JWT in the `header_provider` of the A2A SDK. Have the MCP server validate this token and impersonate the user's GCP IAM role to query BigQuery on their behalf.</li></ul> |

---

## 🚀 Priority Next Steps

1. **Immediate Priority**: Refactor the FastAPI endpoint to stream response tokens (SSE) to the chat UI.
2. **Security & Ingress**: Verify the GCP VPC Service Controls layout for the MCP Cloud Run endpoints.
3. **Database Security**: Implement end-to-end user identity delegation instead of utilizing service accounts for BigQuery queries.

---
*Confidential - Circana Multi-Agent MVP | Date: 2026-06-14*
