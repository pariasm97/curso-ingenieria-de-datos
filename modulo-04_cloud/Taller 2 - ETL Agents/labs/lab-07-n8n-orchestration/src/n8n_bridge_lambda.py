import json
import os
from datetime import datetime, timezone

import boto3

SFN = boto3.client("stepfunctions")

STATE_MACHINE_ARN = os.environ.get("STATE_MACHINE_ARN", "")
API_KEY = os.environ.get("API_KEY", "")


def _resp(status_code: int, body: dict):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "content-type,x-api-key",
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
        },
        "body": json.dumps(body, ensure_ascii=False),
    }


def _auth_ok(headers: dict) -> bool:
    if not API_KEY:
        return True
    if not headers:
        return False
    # headers puede venir con diferentes capitalizaciones
    for k, v in headers.items():
        if k.lower() == "x-api-key" and v == API_KEY:
            return True
    return False


def lambda_handler(event, context):
    method = (event.get("requestContext", {}).get("http", {}).get("method") or "").upper()
    path = event.get("rawPath") or event.get("path") or ""
    headers = event.get("headers") or {}

    if method == "OPTIONS":
        return _resp(200, {"ok": True})

    if not STATE_MACHINE_ARN:
        return _resp(500, {"error": "STATE_MACHINE_ARN no configurado"})

    if not _auth_ok(headers):
        return _resp(401, {"error": "No autorizado"})

    try:
        if path.endswith("/start") and method == "POST":
            body_str = event.get("body") or "{}"
            if event.get("isBase64Encoded"):
                # en este lab no se espera base64
                pass
            payload = json.loads(body_str)

            required = ["input_prefix", "output_prefix", "source", "dt"]
            missing = [k for k in required if not payload.get(k)]
            if missing:
                return _resp(400, {"error": f"Faltan campos: {', '.join(missing)}"})

            r = SFN.start_execution(stateMachineArn=STATE_MACHINE_ARN, input=json.dumps(payload))
            return _resp(
                200,
                {
                    "executionArn": r.get("executionArn"),
                    "startDate": r.get("startDate").astimezone(timezone.utc).isoformat() if r.get("startDate") else datetime.now(timezone.utc).isoformat(),
                },
            )

        if path.endswith("/status") and method == "GET":
            qs = event.get("queryStringParameters") or {}
            execution_arn = qs.get("executionArn")
            if not execution_arn:
                return _resp(400, {"error": "executionArn es requerido"})

            desc = SFN.describe_execution(executionArn=execution_arn)
            out = {"status": desc.get("status"), "executionArn": execution_arn}
            if desc.get("status") == "SUCCEEDED":
                out["output"] = desc.get("output")
            if desc.get("status") in ("FAILED", "TIMED_OUT", "ABORTED"):
                out["error"] = desc.get("cause") or desc.get("error")
            return _resp(200, out)

        return _resp(404, {"error": "Ruta no soportada. Use /start o /status"})

    except Exception as e:
        return _resp(500, {"error": str(e)})
