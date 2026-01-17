# Lab 00 - Bootstrap (S3, Glue DB, Athena, roles base)

## Objetivo

Dejar listo un entorno minimo para ejecutar los siguientes laboratorios:

- Buckets S3 para datos y artifacts
- Glue Database
- Athena Workgroup
- Roles IAM base (Glue, Step Functions, Lambda)

## Arquitectura minima

- S3 data bucket: `raw/`, `silver/`, `gold/`
- S3 artifacts bucket: scripts y resultados de Athena
- Glue Data Catalog (Database)
- Athena Workgroup con output a S3

## Pasos

### 1. Desplegar infraestructura

Desde CloudFormation, despliegue `infra/template.yaml` con parametros:

- StudentId: ejemplo `JEMV`
- Env: `dev`

Al finalizar, anote los Outputs:

- DataBucketName
- ArtifactsBucketName
- GlueDatabaseName
- AthenaWorkGroupName

### 2. Cargar dataset sintetico (opcional pero recomendado)

Se incluye un dataset pequeno en `data/`.

Subalo al bucket de datos en `raw/source=synthetic/dt=2026-01-16/`:

```bash
DATA_BUCKET='<DataBucketName>'
aws s3 cp data/customers.csv  s3://$DATA_BUCKET/raw/source=synthetic/dt=2026-01-16/customers.csv
aws s3 cp data/orders.csv     s3://$DATA_BUCKET/raw/source=synthetic/dt=2026-01-16/orders.csv
aws s3 cp data/payments.csv   s3://$DATA_BUCKET/raw/source=synthetic/dt=2026-01-16/payments.csv
```

### 3. Verificacion rapida

Liste el prefijo:

```bash
aws s3 ls s3://$DATA_BUCKET/raw/source=synthetic/dt=2026-01-16/
```

## Entregables

- Captura o evidencia del stack creado
- Evidencia de los archivos en el prefijo raw

## Limpieza

Siga `CLEANUP.md`.
