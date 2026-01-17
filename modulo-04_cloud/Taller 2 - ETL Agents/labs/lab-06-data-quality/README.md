# Lab 06 - Calidad de datos (reporte y hard-fail)

## Objetivo

Agregar una capa minima de calidad de datos al ETL:

- Calcula metricas (nulos en campos requeridos, duplicados en llaves, valores negativos)
- Escribe un `report.json` en S3
- Falla el job si hay violaciones

## Recursos incluidos

- Script: `src/glue_entity_raw_to_silver_with_quality.py`
- CloudFormation: `infra/template.yaml`

## Pre-requisitos

- Lab 00 desplegado
- Datos en raw

## Paso 1. Subir el script al bucket de artifacts

```bash
ARTIFACTS_BUCKET='<ArtifactsBucketName>'
aws s3 cp src/glue_entity_raw_to_silver_with_quality.py s3://$ARTIFACTS_BUCKET/scripts/lab-06/glue_entity_raw_to_silver_with_quality.py
```

## Paso 2. Desplegar el Glue Job

Despliegue `infra/template.yaml` con los parametros del Lab 00.

## Paso 3. Ejecutar

Ejecute para una entidad:

```bash
aws glue start-job-run --job-name "<GlueJobName>" --arguments '{"--ENTITY":"orders"}'
```

## Paso 4. Validar

- Verifique salida silver (si paso calidad)
- Verifique el reporte:
  - `s3://<DataBucketName>/quality/orders/source=synthetic/dt=2026-01-16/report.json`

## Prueba de falla (opcional)

1. Suba un `orders.csv` con `order_id` duplicado.
2. Re-ejecute.
3. Observe que el job falla y el reporte explica el motivo.

## Entregables

- URL del reporte en S3
- Evidencia de job SUCCEEDED o FAILED segun escenario

## Limpieza

Siga `CLEANUP.md`.
