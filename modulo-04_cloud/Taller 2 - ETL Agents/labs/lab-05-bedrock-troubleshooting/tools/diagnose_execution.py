import argparse
import json

import boto3


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--execution-arn", required=True)
    ap.add_argument("--max-events", type=int, default=100)
    args = ap.parse_args()

    sfn = boto3.client("stepfunctions")

    history = sfn.get_execution_history(
        executionArn=args.execution_arn,
        maxResults=args.max_events,
        reverseOrder=True,
    )

    # Buscamos el primer evento de tipo Failure
    failure_keys = {
        "ExecutionFailed",
        "TaskFailed",
        "TaskTimedOut",
        "ExecutionAborted",
        "ExecutionTimedOut",
    }

    for ev in history.get("events", []):
        if ev.get("type") in failure_keys:
            details_key = ev.get("type")[0].lower() + ev.get("type")[1:] + "EventDetails"
            details = ev.get(details_key, {})
            print(json.dumps({"event": ev.get("type"), "details": details}, indent=2, ensure_ascii=False))
            return

    print(json.dumps({"message": "No se encontro evento de falla en el rango consultado"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
