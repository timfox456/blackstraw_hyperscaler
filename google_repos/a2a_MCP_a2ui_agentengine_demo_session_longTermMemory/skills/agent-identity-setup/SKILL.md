---
name: agent-identity-setup
description: Guides configuring native AGENT_IDENTITY for Reasoning Engines to secure access using SPIFFE cryptographic IDs.
---
# Agent Identity Setup Skill

This skill documents how to deploy AI agents on the Gemini Enterprise Agent Engine runtime using secure, native cryptographic identities instead of shared service account keys.

## Core Concepts
*   **AGENT_IDENTITY**: A purpose-built native IAM type that assigns unique, cryptographically attested SPIFFE IDs (`principal://agents.global.org...`) to reasoning engines.
*   **Access Control**: Simplifies IAM permissions. Instead of managing static credentials, the platform manages the identity lifecycle. Access tokens are scoped to the agent container.

## Configuration & Deployment
1.  **Deployment Script**:
    Add the `identity_type` parameter to the `_create_config` execution payload:
    ```python
    config = {
        "display_name": "pricing_assortment_orchestrator",
        "description": "Specialist pricing agent.",
        "agent_framework": "google-adk",
        "staging_bucket": "gs://your-staging-bucket",
        "identity_type": "AGENT_IDENTITY",  # Configure native Agent Identity
    }
    ```
2.  **SDK Client Registration**:
    Deploy using the Vertex AI / GenAI client SDK:
    ```python
    from vertexai.preview.reasoning_engines import ReasoningEngine
    
    engine = ReasoningEngine.create(
        reasoning_class=PricingAssortmentOrchestrator,
        config=config
    )
    ```

## Verification
*   Query the Vertex AI REST API to verify that the deployed resource contains:
	*   `"identityType": "AGENT_IDENTITY"`
	*   `"effectiveIdentity": "agents.global.org-.../reasoningEngines/...`
*   Verify sessions show up under **Sessions services** in the Google Cloud Console.

## Troubleshooting & Gotchas

> [!IMPORTANT]
> **1. FAILED_PRECONDITION / "unknown exception"**
> When using `AGENT_IDENTITY`, the reasoning engine container runs under its own restricted service account. If it tries to invoke LLMs (e.g. `gemini-2.5-flash`), the call will fail with a permission error, resulting in a generic `"unknown exception"` returned to the client.
> *   **To Fix**: Go to GCP Console IAM, and grant `Vertex AI User` role to the default Reasoning Engine service agent: `service-{PROJECT_NUMBER}@gcp-sa-aiplatform-re.iam.gserviceaccount.com`.
> *   **Alternative (Testing/Dev)**: Remove the `"identity_type"` key from the config entirely (or set it to `IDENTITY_TYPE_UNSPECIFIED`). This will use `DEVELOPER_IDENTITY` under the hood, running the engine with the deploying user's credentials which already have full permissions.

> [!WARNING]
> **2. Package Version Mismatch**
> Since the agent is serialized locally using `cloudpickle`, any version discrepancy between the local python virtual environment and the cloud requirements (especially for `pydantic`, `fastapi`, and `google-adk`) will fail to validate/unpickle inside the container, crashing on startup. Keep package versions in `deploy.py` synchronized with the local environment.

> [!TIP]
> **3. Extracting Remote Tracebacks**
> When a remote reasoning engine crashes, the GCP gateway conceals the traceback and returns a generic `400 Bad Request` containing `"unknown exception"`.
> *   To extract the true traceback, catch exceptions inside your agent executor (`sub_agents_executors.py`) and write the traceback into the returned message parts while setting the task state to `TaskState.completed` (final=True). This sends the traceback back as a successful payload that you can inspect directly on your local client.

