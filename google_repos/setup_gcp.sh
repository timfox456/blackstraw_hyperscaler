#!/usr/bin/env bash
# One-time GCP setup: enables APIs, creates GCS bucket, sets IAM bindings.
# Usage: source setup_gcp.sh
# Run after: gcloud auth login && gcloud auth application-default login

set -e

export PATH="/Users/tim.fox/google-cloud-sdk/bin:$PATH"

PROJECT_ID="gemini-enterprise-app-499621"
REGION="us-central1"
BUCKET="gs://${PROJECT_ID}-agent-stage"
USER_EMAIL=$(gcloud auth list --filter=status:ACTIVE --format="value(account)")

echo "=========================================="
echo "Project:  $PROJECT_ID"
echo "Region:   $REGION"
echo "Bucket:   $BUCKET"
echo "User:     $USER_EMAIL"
echo "=========================================="

# 1. Set project
gcloud config set project "$PROJECT_ID"

# 2. Enable required APIs
echo "[1/5] Enabling APIs..."
gcloud services enable \
    aiplatform.googleapis.com \
    discoveryengine.googleapis.com \
    run.googleapis.com \
    storage.googleapis.com \
    cloudbuild.googleapis.com \
    iam.googleapis.com

# 3. Create staging bucket for agent deployment
echo "[2/5] Creating GCS bucket..."
if ! gsutil ls "$BUCKET" >/dev/null 2>&1; then
    gsutil mb -l "$REGION" "$BUCKET"
    echo "  Created: $BUCKET"
else
    echo "  Already exists: $BUCKET"
fi

# 4. Get project number for service account bindings
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")
SA_AIPLATFORM="service-${PROJECT_NUMBER}@gcp-sa-aiplatform.iam.gserviceaccount.com"
SA_COMPUTE="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

# 5. Grant IAM roles
echo "[3/5] Granting IAM roles to ${USER_EMAIL}..."
for ROLE in roles/run.admin roles/storage.admin roles/iam.serviceAccountUser roles/aiplatform.user; do
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="user:${USER_EMAIL}" \
        --role="$ROLE" --quiet 2>/dev/null || true
done

echo "[4/5] Authorizing Compute SA for keyless ADC..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SA_COMPUTE}" \
    --role="roles/aiplatform.user" --quiet 2>/dev/null || true

echo "[5/5] Authorizing Vertex AI SA to invoke Cloud Run (for MCP)..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SA_AIPLATFORM}" \
    --role="roles/run.invoker" --quiet 2>/dev/null || true

echo ""
echo "=========================================="
echo "✓ GCP setup complete."
echo "=========================================="
echo ""
echo "NEXT STEPS:"
echo "  1. Deploy MCP server:   python deploy_mcp.py"
echo "  2. Deploy sub-agents:   python deploy.py"
echo "  3. Run portal:          uvicorn web_app.server:app --port 8000"