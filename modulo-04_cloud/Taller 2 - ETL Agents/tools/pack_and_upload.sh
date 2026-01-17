#!/usr/bin/env bash
set -euo pipefail

ARTIFACTS_BUCKET="${1:-}"
if [[ -z "$ARTIFACTS_BUCKET" ]]; then
  echo "Uso: $0 <ARTIFACTS_BUCKET>" >&2
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Subiendo scripts Glue..."
aws s3 cp "$ROOT_DIR/labs/lab-01-glue-basics/src/glue_entity_raw_to_silver.py" \
  "s3://$ARTIFACTS_BUCKET/scripts/lab-01/glue_entity_raw_to_silver.py"

aws s3 cp "$ROOT_DIR/labs/lab-06-data-quality/src/glue_entity_raw_to_silver_with_quality.py" \
  "s3://$ARTIFACTS_BUCKET/scripts/lab-06/glue_entity_raw_to_silver_with_quality.py"

echo "Subiendo Lambdas (zip)..."
aws s3 cp "$ROOT_DIR/labs/lab-04-bedrock-agent-ops/dist/bedrock_agent_fulfillment.zip" \
  "s3://$ARTIFACTS_BUCKET/lambdas/lab-04/bedrock_agent_fulfillment.zip"

aws s3 cp "$ROOT_DIR/labs/lab-07-n8n-orchestration/dist/n8n_bridge_lambda.zip" \
  "s3://$ARTIFACTS_BUCKET/lambdas/lab-07/n8n_bridge_lambda.zip"

echo "Listo.\n"
