"""Hardened deploy script for Vertex AI Reasoning Engine (Agent Engine).

Maps to the PDF action items as follows:

  - Section 1 (Registration)  : prints a ready-to-PATCH adkAgentDefinition
                                payload after deploy.
  - Section 2 (Service Account): pins the Reasoning Engine to a dedicated SA
                                (AGENT_IDENTITY) instead of DEVELOPER_IDENTITY.
  - Section 3 (State)          : wires a FirestoreSessionService +
                                FirestoreMemoryService into the AdkApp runner.
  - Section 6 (Observability)  : configures OpenTelemetry + Cloud Trace +
                                Cloud Monitoring exporters so spans/metrics
                                emit using GenAI semantic conventions inside
                                the deployed container via weather_agent/agent.py.

Run:
    python deploy_agent_engine.py
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import vertexai
from vertexai.preview import reasoning_engines

# Make sibling packages importable.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gcp.services.firestore_services import (
    build_firestore_memory_service,
    build_firestore_session_service,
)


PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "gemini-enterprise-app-499621")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
STAGING_BUCKET = os.environ.get(
    "GOOGLE_CLOUD_STAGING_BUCKET",
    f"gs://{PROJECT_ID}-agent-stage",
)


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument(
        "--agent",
        choices=["weather", "host"],
        default="weather",
        help="Which agent to deploy (weather_agent or host_agent).",
    )
    p.add_argument(
        "--service-account",
        default=None,
        help=(
            "Email of the dedicated runtime SA (PDF Section 2). "
            "Defaults to weather-agent-runtime@... or host-agent-runtime@..."
        ),
    )
    p.add_argument(
        "--display-name",
        default=None,
        help="Display name for the Reasoning Engine.",
    )
    p.add_argument(
        "--no-firestore",
        action="store_true",
        help=(
            "Skip wiring FirestoreSessionService / FirestoreMemoryService. "
            "Use this when the project's Org Policy blocks Firestore "
            "provisioning - the AdkApp will fall back to the default "
            "in-memory services and you can switch back later by re-running "
            "without this flag once the (default) Firestore DB exists."
        ),
    )
    p.add_argument(
        "--no-custom-sa",
        action="store_true",
        help=(
            "Do NOT pin a dedicated runtime service account. Falls back to "
            "Vertex AI's default agent SA (PDF Section 2 'DEVELOPER_IDENTITY'). "
            "Use this when project IAM admin hasn't bound roles on the "
            "dedicated SAs yet - re-deploy with --service-account=... once "
            "the admin grants roles/aiplatform.user, roles/datastore.user, "
            "roles/cloudtrace.agent, roles/monitoring.metricWriter, "
            "roles/logging.logWriter on the SA."
        ),
    )
    return p.parse_args()


def main():
    args = parse_args()

    # ------------------------------------------------------------------
    # Pick the right root_agent + defaults.
    # ------------------------------------------------------------------
    if args.agent == "weather":
        from weather_agent.agent import root_agent  # noqa: WPS433
        service_name = "weather-agent"
        default_sa = f"weather-agent-runtime@{PROJECT_ID}.iam.gserviceaccount.com"
        display_name = args.display_name or "Weather Forecast Agent"
        extra_packages = ["./weather_agent", "./gcp", "./agent.py"]
        description = "Weather agent (ADK) with Firestore session state + OTel."
    else:
        from host_agent.agent import root_agent  # noqa: WPS433
        service_name = "host-agent"
        default_sa = f"host-agent-runtime@{PROJECT_ID}.iam.gserviceaccount.com"
        display_name = args.display_name or "Weather Host Orchestrator"
        extra_packages = ["./host_agent", "./weather_agent", "./gcp", "./agent.py"]
        description = "Host orchestrator (ADK + A2A) with Firestore state + OTel."

    service_account = args.service_account or default_sa

    # ------------------------------------------------------------------
    # Vertex init
    # ------------------------------------------------------------------
    vertexai.init(
        project=PROJECT_ID,
        location=LOCATION,
        staging_bucket=STAGING_BUCKET,
    )

    # ------------------------------------------------------------------
    # Section 3: Firestore-backed Session + Memory services.
    # ------------------------------------------------------------------
    adk_app_kwargs = {
        "agent": root_agent,
        "enable_tracing": True,
    }

    if args.no_firestore:
        print(
            "[deploy] --no-firestore passed: using AdkApp default in-memory "
            "session/memory services. Re-run without this flag once the "
            "(default) Firestore DB is provisioned."
        )
    else:
        def session_service_builder():
            return build_firestore_session_service(project_id=PROJECT_ID)

        def memory_service_builder():
            return build_firestore_memory_service(project_id=PROJECT_ID)

        adk_app_kwargs["session_service_builder"] = session_service_builder
        adk_app_kwargs["memory_service_builder"] = memory_service_builder

    app = reasoning_engines.AdkApp(**adk_app_kwargs)

    # ------------------------------------------------------------------
    # Section 2: pin a dedicated, least-privilege SA (AGENT_IDENTITY).
    # ------------------------------------------------------------------
    requirements = [
        "google-adk>=2.0.0",
        "google-cloud-aiplatform[agent_engines]>=1.91.0",
        "opentelemetry-sdk>=1.27.0",
        "opentelemetry-exporter-gcp-trace>=1.7.0",
        "opentelemetry-exporter-gcp-monitoring>=1.7.0a0",
        "opentelemetry-instrumentation-requests>=0.48b0",
        "mcp>=1.0.0",
    ]
    if not args.no_firestore:
        requirements.append("google-cloud-firestore>=2.16.0")

    create_kwargs = dict(
        requirements=requirements,
        extra_packages=extra_packages,
        display_name=display_name,
        description=description,
    )
    if args.no_custom_sa:
        print(
            "[deploy] --no-custom-sa passed: falling back to Vertex AI's "
            "default agent SA (DEVELOPER_IDENTITY per PDF Section 2). "
            "Re-deploy with --service-account=... once the dedicated SA has "
            "the right role bindings."
        )
    else:
        create_kwargs["service_account"] = service_account

    print(f"[deploy] Deploying {args.agent} agent to Reasoning Engine...")
    print(f"[deploy]   project          = {PROJECT_ID}")
    print(f"[deploy]   location         = {LOCATION}")
    print(f"[deploy]   service_account  = {service_account}")
    print(f"[deploy]   staging_bucket   = {STAGING_BUCKET}")

    remote_agent = reasoning_engines.ReasoningEngine.create(app, **create_kwargs)

    print(f"\n[deploy] Deployed: {remote_agent.resource_name}\n")

    # ------------------------------------------------------------------
    # Section 1: print a ready-to-PATCH adkAgentDefinition payload.
    # ------------------------------------------------------------------
    registration_payload = {
        "name": (
            f"projects/{PROJECT_ID}/locations/global/collections/default_collection/"
            f"engines/gemini-enterprise-app/assistants/default_assistant/agents/"
            f"{args.agent}_agent_a2ui"
        ),
        "displayName": display_name,
        "description": description,
        "adkAgentDefinition": {"reasoningEngine": remote_agent.resource_name},
        "authorizationConfig": {"authorizationId": f"{args.agent}-agent-auth-v1"},
    }
    print("[deploy] Use this payload to register the agent in Gemini Enterprise:")
    print(json.dumps(registration_payload, indent=2))
    print(
        "\n[deploy] Register/update with PATCH (NEVER delete + recreate - PDF Section 1):\n"
        "  curl -X PATCH \\\n"
        "    -H \"Authorization: Bearer $(gcloud auth print-access-token)\" \\\n"
        "    -H 'Content-Type: application/json' \\\n"
        f"    -d @registration.json \\\n"
        f"    'https://discoveryengine.googleapis.com/v1alpha/{registration_payload['name']}?updateMask=adkAgentDefinition'"
    )


if __name__ == "__main__":
    main()
