#!/usr/bin/env bash
set -euo pipefail

# Deploy this ADK agent to Vertex AI Agent Engine.
#
# Required env vars:
#   PROJECT_ID       (e.g. my-gcp-project)
#   REGION           (e.g. us-central1)
#   STAGING_BUCKET   (e.g. gs://my-bucket)
# Optional:
#   DISPLAY_NAME     (default: context-compaction-agent)
#   DESCRIPTION      (default: empty)
#   TRACE_TO_CLOUD   (default: true)  -> enables Cloud Trace
#   ENABLE_TELEMETRY (default: true)  -> populates Agent Engine observability dashboard
#   CAPTURE_MESSAGE_CONTENT (default: false) -> logs full prompts/responses (may include PII)

: "${PROJECT_ID:?Set PROJECT_ID}"
: "${REGION:?Set REGION}"
: "${STAGING_BUCKET:?Set STAGING_BUCKET (gs://...) }"

DISPLAY_NAME=${DISPLAY_NAME:-context-compaction-agent}
DESCRIPTION=${DESCRIPTION:-}
TRACE_TO_CLOUD=${TRACE_TO_CLOUD:-true}
ENABLE_TELEMETRY=${ENABLE_TELEMETRY:-true}
CAPTURE_MESSAGE_CONTENT=${CAPTURE_MESSAGE_CONTENT:-false}

# Sanity checks
command -v gcloud >/dev/null 2>&1 || { echo "gcloud not found"; exit 1; }
command -v adk >/dev/null 2>&1 || { echo "adk CLI not found (pip install google-adk)"; exit 1; }

# Ensure gcloud project is set (does not authenticate for you)
gcloud config set project "$PROJECT_ID" >/dev/null

# Create a temp env file for Agent Engine runtime env vars
ENV_FILE="$(mktemp -t adk-agent-engine-env.XXXXXX)"
trap 'rm -f "$ENV_FILE"' EXIT

# These env vars are read by the Agent Engine runtime for observability.
{
  echo "GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=${ENABLE_TELEMETRY}";
  echo "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=${CAPTURE_MESSAGE_CONTENT}";
} > "$ENV_FILE"

echo "Deploying ADK agent to Agent Engine..."
echo "  project:  $PROJECT_ID"
echo "  region:   $REGION"
echo "  staging:  $STAGING_BUCKET"
echo "  name:     $DISPLAY_NAME"
echo "  trace:    $TRACE_TO_CLOUD"
echo "  telemetry:$ENABLE_TELEMETRY"
echo "  capture:  $CAPTURE_MESSAGE_CONTENT"

TRACE_FLAG="--no-trace_to_cloud"
if [[ "$TRACE_TO_CLOUD" == "true" ]]; then
  TRACE_FLAG="--trace_to_cloud"
fi

adk deploy agent_engine \
  --project="$PROJECT_ID" \
  --region="$REGION" \
  --adk_app_object=app \
  --staging_bucket="$STAGING_BUCKET" \
  --display_name="$DISPLAY_NAME" \
  --description="$DESCRIPTION" \
  $TRACE_FLAG \
  --env_file="$ENV_FILE" \
  /Users/nagarjun/development/LAAS-proto-types/context_compaction/context_compaction_agent

