# Lab 01 - Glue Basics (Raw CSV a Silver Parquet)

## Objetivo

Crear un Glue Job en PySpark que:

- Lea CSV desde `raw/`
- Limpie y tipifique columnas
- Escriba Parquet en `silver/` particionando por `source` y `dt`

## Recursos incluidos

- Script Glue: `src/glue_entity_raw_to_silver.py`
- CloudFormation: `infra/template.yaml`

## Pre-requisitos

- Lab 00 desplegado
- Dataset cargado en:
  - `s3://<DataBucket>/raw/source=synthetic/dt=2026-01-16/...`

## Paso 1. Subir el script al bucket de artifacts

Suba el script a:

- `s3://<ArtifactsBucket>/scripts/lab-01/glue_entity_raw_to_silver.py`

Ejemplo:

```bash
ARTIFACTS_BUCKET='<ArtifactsBucketName>'
aws s3 cp src/glue_entity_raw_to_silver.py s3://$ARTIFACTS_BUCKET/scripts/lab-01/glue_entity_raw_to_silver.py
```

## Paso 2. Desplegar el Glue Job

Despliegue `infra/template.yaml` con:

- DataBucketName = output del Lab 00
- ArtifactsBucketName = output del Lab 00
- GlueJobRoleArn = output del Lab 00

## Paso 3. Ejecutar el job para cada entidad

Lance el job tres veces cambiando `--ENTITY`:

```bash
JOB_NAME='<GlueJobName>'
aws glue start-job-run --job-name "$JOB_NAME" --arguments '{"--ENTITY":"customers"}'
aws glue start-job-run --job-name "$JOB_NAME" --arguments '{"--ENTITY":"orders"}'
aws glue start-job-run --job-name "$JOB_NAME" --arguments '{"--ENTITY":"payments"}'
```

## Paso 4. Validar

Revise en S3:

- `s3://<DataBucket>/silver/customers/source=synthetic/dt=2026-01-16/`
- `s3://<DataBucket>/silver/orders/source=synthetic/dt=2026-01-16/`
- `s3://<DataBucket>/silver/payments/source=synthetic/dt=2026-01-16/`

Opcional: registre tablas externas en Athena (se sugiere en Lab 03).

## Entregables

- Evidencia del job ejecutado (JobRunId)
- Evidencia de los archivos parquet en `silver/`

## Limpieza

Siga `CLEANUP.md`.
