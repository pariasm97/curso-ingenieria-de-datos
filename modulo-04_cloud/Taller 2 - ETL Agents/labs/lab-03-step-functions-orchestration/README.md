# Lab 03 - Orquestacion con AWS Step Functions

## Objetivo

Crear una State Machine que ejecute el ETL de `customers`, `orders` y `payments` en paralelo, usando integracion sincrona con Glue.

## Recursos incluidos

- Definicion ASL (referencial): `statemachine/definition.asl.json`
- CloudFormation: `infra/template.yaml`
- SQL Athena: `athena/create_tables.sql`

## Pre-requisitos

- Lab 00 desplegado
- Lab 01 desplegado y el Glue Job existente
- Dataset disponible en `raw/source=synthetic/dt=2026-01-16/`

## Paso 1. Desplegar la State Machine

Despliegue `infra/template.yaml` con:

- StepFunctionsRoleArn = output Lab 00
- GlueJobName = output Lab 01

## Paso 2. Ejecutar el pipeline

Inicie una ejecucion con el siguiente input (ajuste buckets):

```json
{
  "input_prefix": "s3://<DataBucketName>/raw/source=synthetic/dt=2026-01-16",
  "output_prefix": "s3://<DataBucketName>/silver",
  "source": "synthetic",
  "dt": "2026-01-16"
}
```

Puede iniciarlo desde consola o con AWS CLI:

```bash
aws stepfunctions start-execution \
  --state-machine-arn "<StateMachineArn>" \
  --input file://input.json
```

## Paso 3. Validar

- Revise la ejecucion en Step Functions y los logs en CloudWatch.
- Verifique `silver/` por cada entidad.

## Paso 4. Registrar tablas en Athena (opcional)

Ejecute `athena/create_tables.sql` en Athena, reemplazando:

- `<DATA_BUCKET>`
- `<GLUE_DB>` (output Lab 00)

Luego consulte:

```sql
SELECT dt, count(*) FROM <GLUE_DB>.orders_silver GROUP BY dt;
```

## Entregables

- executionArn de Step Functions
- Evidencia de outputs en `silver/`
- Consulta Athena con conteos

## Limpieza

Siga `CLEANUP.md`.
