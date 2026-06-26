# =============================================================================
# Least-privilege service account setup for the A2A weather + host agents.
# Implements PDF Section 2 (Service Account Security & Least Privilege).
#
# Run from PowerShell after `gcloud auth login`.
#
#   .\setup_service_account.ps1
#
# This script is idempotent: re-running it will not duplicate bindings.
# =============================================================================

$ErrorActionPreference = "Stop"

$PROJECT_ID   = "gemini-enterprise-app-499621"
$LOCATION     = "us-central1"

# One dedicated SA per agent (do NOT share VM/master SAs - PDF Section 2)
$WEATHER_SA   = "weather-agent-runtime"
$HOST_SA      = "host-agent-runtime"

$WEATHER_SA_EMAIL = "$WEATHER_SA@$PROJECT_ID.iam.gserviceaccount.com"
$HOST_SA_EMAIL    = "$HOST_SA@$PROJECT_ID.iam.gserviceaccount.com"

gcloud config set project $PROJECT_ID | Out-Null

function Ensure-SA($accountId, $displayName) {
    $email = "$accountId@$PROJECT_ID.iam.gserviceaccount.com"
    $exists = gcloud iam service-accounts list --filter="email=$email" --format="value(email)" 2>$null
    if (-not $exists) {
        Write-Host "Creating SA $email"
        gcloud iam service-accounts create $accountId `
            --display-name=$displayName `
            --description="Dedicated runtime identity for $displayName (least privilege per PDF Section 2)"
    } else {
        Write-Host "SA $email already exists - skipping create"
    }
}

function Grant-Role($saEmail, $role) {
    Write-Host "  - granting $role to $saEmail"
    gcloud projects add-iam-policy-binding $PROJECT_ID `
        --member="serviceAccount:$saEmail" `
        --role=$role `
        --condition=None `
        --quiet | Out-Null
}

# -----------------------------------------------------------------------------
# Weather agent SA: needs Vertex AI (LLM calls), Firestore (sessions/memory),
# OTel exporters (Cloud Trace / Cloud Monitoring / Cloud Logging).
# -----------------------------------------------------------------------------
Ensure-SA $WEATHER_SA "Weather Agent Runtime"
$weatherRoles = @(
    "roles/aiplatform.user",          # PDF Section 2: call LLMs (gemini-2.5-flash)
    "roles/datastore.user",           # PDF Section 2: Firestore session/memory reads+writes
    "roles/cloudtrace.agent",         # PDF Section 6: emit OTel spans to Cloud Trace
    "roles/monitoring.metricWriter",  # PDF Section 6: emit OTel metrics
    "roles/logging.logWriter"         # PDF Section 6: container/structured logs
)
foreach ($r in $weatherRoles) { Grant-Role $WEATHER_SA_EMAIL $r }

# -----------------------------------------------------------------------------
# Host orchestrator SA: same baseline + permission to invoke the weather
# agent's Reasoning Engine via A2A.
# -----------------------------------------------------------------------------
Ensure-SA $HOST_SA "Host Orchestrator Runtime"
$hostRoles = @(
    "roles/aiplatform.user",          # call LLMs + invoke remote Reasoning Engine
    "roles/datastore.user",
    "roles/cloudtrace.agent",
    "roles/monitoring.metricWriter",
    "roles/logging.logWriter"
)
foreach ($r in $hostRoles) { Grant-Role $HOST_SA_EMAIL $r }

# -----------------------------------------------------------------------------
# AGENT_IDENTITY (production setting per PDF Section 2): when deploying via
# Reasoning Engine, assign the dedicated SA so the container runs under a
# SPIFFE-attested principal (principal://agents.global...) rather than the
# deploying user's IAM context.
#
# Configure this at deploy time:
#   ReasoningEngine.create(..., service_account=$WEATHER_SA_EMAIL)
# -----------------------------------------------------------------------------
Write-Host ""
Write-Host "Done. Use these in deploy_agent_engine.py / gcloud deploys:"
Write-Host "  WEATHER_SA = $WEATHER_SA_EMAIL"
Write-Host "  HOST_SA    = $HOST_SA_EMAIL"
Write-Host ""
Write-Host "Both SAs run with AGENT_IDENTITY (least privilege). DEVELOPER_IDENTITY"
Write-Host "is only acceptable for local prototyping per PDF Section 2."
