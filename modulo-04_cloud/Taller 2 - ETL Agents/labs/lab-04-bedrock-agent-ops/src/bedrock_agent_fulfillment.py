import json
import os
from datetime import datetime, timezone

import boto3

SFN = boto3.client("stepfunctions")

STATE_MACHINE_ARN = os.environ.get("STATE_MACHINE_ARN", "")


def _json_response(action_group: str, api_path: str, http_method: str, status_code: int, body_obj: dict):
    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": action_group,
            "apiPath": api_path,
            "httpMethod": http_method,
            "httpStatusCode": status_code,
            "responseBody": {
                "application/json": {
                    "body": json.dumps(body_obj, ensure_ascii=False)
                }
            },
        },
    }


def _get_query_param(params, name: str):
    # Bedrock Agents suele enviar parameters como lista de dicts
    if isinstance(params, list):
        for p in params:
            if p.get("name") == name:
                return p.get("value")
    if isinstance(params, dict):
        return params.get(name)
    return None


def lambda_handler(event, context):
    action_group = event.get("actionGroup", "")
    api_path = event.get("apiPath", "")
    http_method = event.get("httpMethod", "")

    if not STATE_MACHINE_ARN:
        return _json_response(action_group, api_path, http_method, 500, {"error": "STATE_MACHINE_ARN no configurado"})

    try:
        if api_path == "/pipeline/start" and http_method.upper() == "POST":
            rb = event.get("requestBody", {})
            # requestBody puede venir como {"content": {"application/json": {"properties": ...}}}
            # o como string. Normalizamos.
            payload = None
            if isinstance(rb, dict):
                content = rb.get("content") or {}
                app_json = content.get("application/json") or {}
                if isinstance(app_json, dict) and "body" in app_json:
                    payload = json.loads(app_json["body"]) if isinstance(app_json["body"], str) else app_json["body"]
                elif isinstance(app_json, dict):
                    payload = app_json
            elif isinstance(rb, str):
                payload = json.loads(rb)

            payload = payload or {}
            required = ["input_prefix", "output_prefix", "source", "dt"]
            missing = [k for k in required if not payload.get(k)]
            if missing:
                return _json_response(action_group, api_path, http_method, 400, {"error": f"Faltan campos: {', '.join(missing)}"})

            response = SFN.start_execution(
                stateMachineArn=STATE_MACHINE_ARN,
                input=json.dumps(payload),
            )
            return _json_response(
                action_group,
                api_path,
                http_method,
                200,
                {
                    "executionArn": response.get("executionArn"),
                    "startDate": response.get("startDate").astimezone(timezone.utc).isoformat() if response.get("startDate") else datetime.now(timezone.utc).isoformat(),
                },
            )

        if api_path == "/pipeline/status" and http_method.upper() == "GET":
            execution_arn = _get_query_param(event.get("parameters"), "executionArn")
            if not execution_arn:
                return _json_response(action_group, api_path, http_method, 400, {"error": "executionArn es requerido"})

            desc = SFN.describe_execution(executionArn=execution_arn)
            out = {
                "status": desc.get("status"),
                "executionArn": execution_arn,
            }
            if desc.get("status") == "SUCCEEDED":
                # output suele ser string json
                out["output"] = desc.get("output")
            if desc.get("status") in ("FAILED", "TIMED_OUT", "ABORTED"):
                out["error"] = desc.get("cause") or desc.get("error")

            return _json_response(action_group, api_path, http_method, 200, out)

        return _json_response(action_group, api_path, http_method, 404, {"error": "Ruta no soportada"})

    except Exception as e:
        return _json_response(action_group, api_path, http_method, 500, {"error": str(e)})
