# Lab 07 - Integracion con n8n (Webhook, S3, Step Functions)

## Objetivo

Usar n8n como orquestador externo para:

- Recibir un archivo por Webhook
- Cargarlo a S3 (raw)
- Disparar el pipeline (Step Functions) via un "bridge" (Lambda Function URL)
- Consultar estado hasta terminar

## Recursos incluidos

- Docker Compose: `docker/docker-compose.yml`
- Workflow n8n (importable): `workflow/etl_webhook_to_s3_and_pipeline.json`
- Lambda bridge: `src/n8n_bridge_lambda.py` y zip en `dist/n8n_bridge_lambda.zip`
- CloudFormation: `infra/template.yaml`

## Pre-requisitos

- Lab 03 desplegado (State Machine)
- Lab 00 desplegado (bucket artifacts)
- Docker

## Paso 1. Desplegar Lambda bridge

1. Suba el zip:

```bash
aws s3 cp dist/n8n_bridge_lambda.zip s3://<ArtifactsBucketName>/lambdas/lab-07/n8n_bridge_lambda.zip
```

2. Despliegue `infra/template.yaml` con:

- ArtifactsBucketName
- StateMachineArn
- ApiKey (recomendado)

Guarde el Output `FunctionUrl`. Esa URL es el "base". Debe usar:

- `<FunctionUrl>start`
- `<FunctionUrl>status?executionArn=...`

Nota: CloudFormation devuelve una URL que normalmente termina en `/`. Use esa base.

## Paso 2. Levantar n8n local

```bash
cd docker
cp .env.example .env
# Edite .env y ponga N8N_ENCRYPTION_KEY

docker compose up -d
```

Abra n8n en `http://localhost:5678`.

## Paso 3. Importar el workflow

1. Importe `workflow/etl_webhook_to_s3_and_pipeline.json`.
2. Edite el nodo "Set Vars":
   - `data_bucket`: su DataBucketName
   - `bridge_base_url`: su FunctionUrl
   - `api_key`: su ApiKey (si la configuro)
3. Configure credenciales AWS para el nodo S3.

## Paso 4. Probar

Haga una llamada POST al webhook (ejemplo con curl):

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"dt":"2026-01-16","file_name":"orders.csv"}' \
  http://localhost:5678/webhook/etl-ingest
```

Para un escenario real, ajuste el workflow para recibir binarios y subirlos a S3.

## Entregables

- Evidencia del workflow corriendo
- Objeto cargado en `raw/`
- executionArn y status final

## Limpieza

Siga `CLEANUP.md`.
